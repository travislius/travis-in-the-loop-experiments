class CalcError(ValueError):
    pass


_NUMBER = "number"
_NAME = "name"
_OP = "operator"
_END = "end"


def _is_digit(ch):
    return "0" <= ch <= "9"


def _is_name_start(ch):
    return ch == "_" or "a" <= ch <= "z" or "A" <= ch <= "Z"


def _is_name_continue(ch):
    return _is_name_start(ch) or _is_digit(ch)


def _tokenize(text):
    tokens = []
    i = 0
    length = len(text)

    while i < length:
        ch = text[i]

        if ch.isspace():
            i += 1
            continue

        if _is_digit(ch) or (
            ch == "." and i + 1 < length and _is_digit(text[i + 1])
        ):
            start = i
            if ch == ".":
                i += 1
                while i < length and _is_digit(text[i]):
                    i += 1
            else:
                while i < length and _is_digit(text[i]):
                    i += 1
                if i < length and text[i] == ".":
                    i += 1
                    while i < length and _is_digit(text[i]):
                        i += 1
            raw = text[start:i]
            value = float(raw) if "." in raw else int(raw)
            tokens.append((_NUMBER, value, start))
            continue

        if _is_name_start(ch):
            start = i
            i += 1
            while i < length and _is_name_continue(text[i]):
                i += 1
            tokens.append((_NAME, text[start:i], start))
            continue

        if ch == "*" and i + 1 < length and text[i + 1] == "*":
            tokens.append((_OP, "**", i))
            i += 2
            continue

        if ch == "/" and i + 1 < length and text[i + 1] == "/":
            tokens.append((_OP, "//", i))
            i += 2
            continue

        if ch in "+-*/%(),":
            tokens.append((_OP, ch, i))
            i += 1
            continue

        raise CalcError("unexpected token {!r} at position {}".format(ch, i))

    tokens.append((_END, None, length))
    return tokens


class _Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.env = env
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos]

    def _match_operator(self, *operators):
        token = self._peek()
        if token[0] == _OP and token[1] in operators:
            self.pos += 1
            return token[1]
        return None

    def _unexpected(self, token=None):
        if token is None:
            token = self._peek()
        if token[0] == _END:
            return CalcError("unexpected end of input")
        return CalcError(
            "unexpected token {!r} at position {}".format(token[1], token[2])
        )

    def parse(self):
        if self._peek()[0] == _END:
            raise CalcError("empty input")

        value = self._expression()

        token = self._peek()
        if token[0] != _END:
            if token[0] == _OP and token[1] == ")":
                raise CalcError("unbalanced parentheses")
            raise self._unexpected(token)
        return value

    def _expression(self):
        value = self._term()

        while True:
            operator = self._match_operator("+", "-")
            if operator is None:
                break
            right = self._term()
            if operator == "+":
                value = value + right
            else:
                value = value - right

        return value

    def _term(self):
        value = self._unary()

        while True:
            operator = self._match_operator("*", "/", "//", "%")
            if operator is None:
                break
            right = self._unary()
            value = self._apply_binary(operator, value, right)

        return value

    def _unary(self):
        operator = self._match_operator("+", "-")
        if operator is not None:
            value = self._unary()
            return value if operator == "+" else -value
        return self._power()

    def _power(self):
        base = self._primary()
        if self._match_operator("**") is not None:
            # Parsing the exponent as a unary expression makes ** right-associative
            # while still allowing a signed exponent (2 ** -1).
            exponent = self._unary()
            try:
                result = base ** exponent
            except (ZeroDivisionError, OverflowError) as exc:
                raise CalcError(str(exc)) from None
            if isinstance(result, complex):
                raise CalcError("result is not a real number")
            return result
        return base

    def _apply_binary(self, operator, left, right):
        if operator == "*":
            return left * right

        if operator == "/":
            if right == 0:
                raise CalcError("division by zero")
            return left / right

        if operator == "//":
            if right == 0:
                raise CalcError("division by zero")
            return left // right

        if operator == "%":
            if right == 0:
                raise CalcError("modulo by zero")
            return left % right

        raise self._unexpected()

    def _primary(self):
        token = self._peek()

        if token[0] == _NUMBER:
            self.pos += 1
            return token[1]

        if token[0] == _NAME:
            self.pos += 1
            name = token[1]
            if self._match_operator("(") is not None:
                return self._call(name)
            if name in self.env:
                return self.env[name]
            raise CalcError("unknown variable: {}".format(name))

        if token[0] == _OP and token[1] == "(":
            self.pos += 1
            value = self._expression()
            if self._match_operator(")") is None:
                raise CalcError("unbalanced parentheses")
            return value

        if token[0] == _OP and token[1] == ")":
            raise CalcError("unbalanced parentheses")

        raise self._unexpected(token)

    def _call(self, name):
        if name not in ("min", "max", "abs"):
            raise CalcError("unknown function: {}".format(name))

        arguments = []
        if self._match_operator(")") is None:
            while True:
                arguments.append(self._expression())

                if self._match_operator(",") is not None:
                    continue
                if self._match_operator(")") is not None:
                    break

                token = self._peek()
                if token[0] == _END:
                    raise CalcError("unbalanced parentheses")
                raise self._unexpected(token)

        if name == "abs":
            if len(arguments) != 1:
                raise CalcError(
                    "abs() takes exactly 1 argument (got {})".format(
                        len(arguments)
                    )
                )
            return abs(arguments[0])

        if not arguments:
            raise CalcError(
                "{}() requires at least 1 argument".format(name)
            )
        if name == "min":
            return min(arguments)
        return max(arguments)


def evaluate(expr, env=None):
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")

    if env is None:
        env = {}

    parser = _Parser(_tokenize(expr), env)
    return parser.parse()
