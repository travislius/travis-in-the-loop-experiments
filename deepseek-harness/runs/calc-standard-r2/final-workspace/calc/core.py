class CalcError(ValueError):
    pass


def _is_digit(ch):
    return "0" <= ch <= "9"


def _is_ident_start(ch):
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "_"


def _is_ident_part(ch):
    return _is_ident_start(ch) or _is_digit(ch)


def _tokenize(expr):
    """Turn an expression into (kind, value, position) tokens."""
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")

    tokens = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        if _is_digit(ch) or (ch == "." and i + 1 < n and _is_digit(expr[i + 1])):
            start = i
            has_dot = False

            if ch == ".":
                has_dot = True
                i += 1
                while i < n and _is_digit(expr[i]):
                    i += 1
            else:
                while i < n and _is_digit(expr[i]):
                    i += 1
                if i < n and expr[i] == ".":
                    has_dot = True
                    i += 1
                    while i < n and _is_digit(expr[i]):
                        i += 1

            text = expr[start:i]
            try:
                value = float(text) if has_dot else int(text)
            except ValueError:
                raise CalcError("invalid number %r" % (text,))
            tokens.append(("NUMBER", value, start))
            continue

        if _is_ident_start(ch):
            start = i
            i += 1
            while i < n and _is_ident_part(expr[i]):
                i += 1
            tokens.append(("IDENT", expr[start:i], start))
            continue

        if expr.startswith("**", i):
            tokens.append(("OP", "**", i))
            i += 2
            continue
        if expr.startswith("//", i):
            tokens.append(("OP", "//", i))
            i += 2
            continue
        if ch in "+-*/%":
            tokens.append(("OP", ch, i))
            i += 1
            continue

        if ch == "(":
            tokens.append(("LPAREN", ch, i))
            i += 1
            continue
        if ch == ")":
            tokens.append(("RPAREN", ch, i))
            i += 1
            continue
        if ch == ",":
            tokens.append(("COMMA", ch, i))
            i += 1
            continue

        raise CalcError("unexpected token %r" % (ch,))

    tokens.append(("EOF", None, n))
    return tokens


def _call_function(name, args):
    if name == "abs":
        if len(args) != 1:
            raise CalcError("abs() takes exactly one argument")
        return abs(args[0])

    if name == "min":
        if not args:
            raise CalcError("min() takes at least one argument")
        return min(args)

    if name == "max":
        if not args:
            raise CalcError("max() takes at least one argument")
        return max(args)

    raise CalcError("unknown function %r" % (name,))


class _Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.env = env if env is not None else {}
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.tokens[self.pos]
        if token[0] != "EOF":
            self.pos += 1
        return token

    def at_op(self, *values):
        token = self.peek()
        return token[0] == "OP" and token[1] in values

    def unexpected(self, token=None):
        if token is None:
            token = self.peek()
        kind, value, _ = token
        if kind == "EOF":
            return CalcError("unexpected end of input")
        return CalcError("unexpected token %r" % (value,))

    def parse(self):
        if self.peek()[0] == "EOF":
            raise CalcError("empty input")

        value = self.parse_expression()
        token = self.peek()
        if token[0] != "EOF":
            if token[0] == "RPAREN":
                raise CalcError("unbalanced parentheses")
            raise self.unexpected(token)
        return value

    def parse_expression(self):
        value = self.parse_term()

        while self.at_op("+", "-"):
            op = self.advance()[1]
            right = self.parse_term()
            if op == "+":
                value = value + right
            else:
                value = value - right

        return value

    def parse_term(self):
        value = self.parse_factor()

        while self.at_op("*", "/", "//", "%"):
            op = self.advance()[1]
            right = self.parse_factor()

            if op in ("/", "//", "%") and right == 0:
                if op == "%":
                    raise CalcError("modulo by zero")
                raise CalcError("division by zero")

            try:
                if op == "*":
                    value = value * right
                elif op == "/":
                    value = value / right
                elif op == "//":
                    value = value // right
                else:
                    value = value % right
            except ZeroDivisionError:
                raise CalcError("division or modulo by zero")

        return value

    def parse_factor(self):
        if self.at_op("+", "-"):
            op = self.advance()[1]
            value = self.parse_factor()
            return value if op == "+" else -value
        return self.parse_power()

    def parse_power(self):
        value = self.parse_primary()

        if self.at_op("**"):
            self.advance()
            exponent = self.parse_factor()
            try:
                value = value ** exponent
            except ZeroDivisionError:
                raise CalcError("zero cannot be raised to a negative power")

        return value

    def parse_primary(self):
        token = self.peek()
        kind, value, _ = token

        if kind == "NUMBER":
            self.advance()
            return value

        if kind == "IDENT":
            self.advance()
            if self.peek()[0] == "LPAREN":
                self.advance()
                args = []

                if self.peek()[0] != "RPAREN":
                    while True:
                        args.append(self.parse_expression())
                        if self.peek()[0] == "COMMA":
                            self.advance()
                            continue
                        break

                if self.peek()[0] != "RPAREN":
                    if self.peek()[0] == "EOF":
                        raise CalcError("unbalanced parentheses")
                    raise self.unexpected()

                self.advance()
                return _call_function(value, args)

            if value not in self.env:
                raise CalcError("unknown variable %r" % (value,))
            return self.env[value]

        if kind == "LPAREN":
            self.advance()
            value = self.parse_expression()
            if self.peek()[0] != "RPAREN":
                if self.peek()[0] == "EOF":
                    raise CalcError("unbalanced parentheses")
                raise self.unexpected()
            self.advance()
            return value

        if kind == "EOF":
            raise CalcError("unexpected end of input")

        if kind == "RPAREN":
            raise CalcError("unbalanced parentheses")

        raise self.unexpected(token)


def evaluate(expr, env=None):
    parser = _Parser(_tokenize(expr), env)
    return parser.parse()
