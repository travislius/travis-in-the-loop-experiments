class CalcError(ValueError):
    pass


_FUNCTION_ARITY = {
    "abs": (1, 1),
    "min": (1, None),
    "max": (1, None),
}


def _is_digit(ch):
    return "0" <= ch <= "9"


def _is_ident_start(ch):
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "_"


def _is_ident_part(ch):
    return _is_ident_start(ch) or _is_digit(ch)


def _tokenize(text):
    """Turn *text* into (kind, value, position) tokens."""
    tokens = []
    i = 0
    length = len(text)

    while i < length:
        ch = text[i]

        if ch.isspace():
            i += 1
            continue

        # Numbers: 42, 3.5, .5, and (like Python) 5.
        if _is_digit(ch) or (
            ch == "." and i + 1 < length and _is_digit(text[i + 1])
        ):
            start = i
            if ch == ".":
                i += 1
                while i < length and _is_digit(text[i]):
                    i += 1
                value = float(text[start:i])
            else:
                while i < length and _is_digit(text[i]):
                    i += 1
                if i < length and text[i] == ".":
                    i += 1
                    while i < length and _is_digit(text[i]):
                        i += 1
                    value = float(text[start:i])
                else:
                    value = int(text[start:i])
            tokens.append(("number", value, start))
            continue

        if _is_ident_start(ch):
            start = i
            i += 1
            while i < length and _is_ident_part(text[i]):
                i += 1
            tokens.append(("ident", text[start:i], start))
            continue

        if text.startswith("**", i) or text.startswith("//", i):
            tokens.append(("op", text[i:i + 2], i))
            i += 2
            continue

        if ch in "+-*/%(),":
            tokens.append(("op", ch, i))
            i += 1
            continue

        raise CalcError(
            "unexpected character {!r} at position {}".format(ch, i)
        )

    return tokens


def _apply_binary(op, left, right):
    try:
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
        if op == "//":
            return left // right
        if op == "%":
            return left % right
        if op == "**":
            return left ** right
    except ZeroDivisionError:
        if op == "%":
            raise CalcError("modulo by zero")
        raise CalcError("division by zero")

    # The parser never produces any other operator.
    raise CalcError("unexpected operator {!r}".format(op))


class _Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.env = env
        self.pos = 0

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _peek_op(self, op):
        token = self._peek()
        return token is not None and token[0] == "op" and token[1] == op

    def _describe_unexpected(self):
        token = self._peek()
        if token is None:
            return "unexpected end of expression"
        kind, value, position = token
        if kind == "op" and value == ")":
            return "unbalanced parentheses"
        return "unexpected token {} at position {}".format(
            repr(value), position
        )

    def parse(self):
        if not self.tokens:
            raise CalcError("empty input")

        value = self._parse_expression()

        if self._peek() is not None:
            raise CalcError(self._describe_unexpected())

        return value

    # expression -> term (('+' | '-') term)*
    def _parse_inner_expression(self):
        try:
            return self._parse_expression()
        except CalcError as exc:
            # An expression ending while a '(' is still open is an
            # unbalanced-parentheses error rather than a generic EOF error.
            if str(exc) == "unexpected end of expression":
                raise CalcError("unbalanced parentheses")
            raise

    def _parse_expression(self):
        value = self._parse_term()

        while True:
            token = self._peek()
            if token is None or token[0] != "op" or token[1] not in "+-":
                break
            op = token[1]
            self.pos += 1
            right = self._parse_term()
            value = _apply_binary(op, value, right)

        return value

    # term -> unary (('*' | '/' | '//' | '%') unary)*
    def _parse_term(self):
        value = self._parse_unary()

        while True:
            token = self._peek()
            if (
                token is None
                or token[0] != "op"
                or token[1] not in ("*", "/", "//", "%")
            ):
                break
            op = token[1]
            # Distinguish '//' from '/'; the tokenizer already made it one token.
            self.pos += 1
            right = self._parse_unary()
            value = _apply_binary(op, value, right)

        return value

    # unary -> ('+' | '-') unary | power
    def _parse_unary(self):
        token = self._peek()
        if token is not None and token[0] == "op" and token[1] in "+-":
            op = token[1]
            self.pos += 1
            operand = self._parse_unary()
            if op == "-":
                return -operand
            return +operand

        return self._parse_power()

    # power -> atom ['**' unary]      (right-associative, tighter than unary)
    def _parse_power(self):
        value = self._parse_atom()

        if self._peek_op("**"):
            self.pos += 1
            exponent = self._parse_unary()
            value = _apply_binary("**", value, exponent)

        return value

    def _parse_atom(self):
        token = self._peek()
        if token is None:
            raise CalcError("unexpected end of expression")

        kind, value, position = token

        if kind == "number":
            self.pos += 1
            return value

        if kind == "ident":
            self.pos += 1

            if self._peek_op("("):
                self.pos += 1
                args = []

                if not self._peek_op(")"):
                    args.append(self._parse_inner_expression())
                    while self._peek_op(","):
                        self.pos += 1
                        args.append(self._parse_inner_expression())

                if not self._peek_op(")"):
                    raise CalcError("unbalanced parentheses")
                self.pos += 1

                return self._call(value, args)

            if value in self.env:
                return self.env[value]

            raise CalcError("unknown variable {!r}".format(value))

        if kind == "op" and value == "(":
            self.pos += 1
            inner = self._parse_inner_expression()

            if not self._peek_op(")"):
                raise CalcError("unbalanced parentheses")
            self.pos += 1

            return inner

        raise CalcError(self._describe_unexpected())

    def _call(self, name, args):
        if name not in _FUNCTION_ARITY:
            raise CalcError("unknown function {!r}".format(name))

        minimum, maximum = _FUNCTION_ARITY[name]

        if len(args) < minimum or (maximum is not None and len(args) > maximum):
            if name == "abs":
                raise CalcError("abs() takes exactly 1 argument")
            raise CalcError("{}() requires at least 1 argument".format(name))

        if name == "abs":
            return abs(args[0])
        if name == "min":
            return min(args)
        return max(args)


def evaluate(expr, env=None):
    if env is None:
        env = {}

    tokens = _tokenize(expr)
    return _Parser(tokens, env).parse()
