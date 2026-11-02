class CalcError(ValueError):
    pass


class _Token:
    __slots__ = ("kind", "value", "pos")

    def __init__(self, kind, value, pos):
        self.kind = kind
        self.value = value
        self.pos = pos


def _tokenize(expr):
    """Turn an expression into a list of tokens, raising CalcError on bad input."""
    tokens = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        # Integer or decimal literal.  A decimal point must be followed by at
        # least one digit; the part before it may be empty (e.g. ".5").
        if ("0" <= ch <= "9") or (
            ch == "." and i + 1 < n and "0" <= expr[i + 1] <= "9"
        ):
            start = i
            if ch == ".":
                i += 1
                while i < n and "0" <= expr[i] <= "9":
                    i += 1
                kind = "number"
            else:
                while i < n and "0" <= expr[i] <= "9":
                    i += 1
                if i < n and expr[i] == ".":
                    i += 1
                    if i >= n or not ("0" <= expr[i] <= "9"):
                        raise CalcError("unexpected token '.' at position %d" % (i - 1))
                    while i < n and "0" <= expr[i] <= "9":
                        i += 1
                kind = "number"
            text = expr[start:i]
            value = int(text) if "." not in text else float(text)
            tokens.append(_Token(kind, value, start))
            continue

        if ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ch == "_":
            start = i
            i += 1
            while i < n:
                c = expr[i]
                if (
                    ("A" <= c <= "Z")
                    or ("a" <= c <= "z")
                    or ("0" <= c <= "9")
                    or c == "_"
                ):
                    i += 1
                else:
                    break
            tokens.append(_Token("identifier", expr[start:i], start))
            continue

        # Longest-match operators first.
        if expr.startswith("**", i):
            tokens.append(_Token("op", "**", i))
            i += 2
        elif expr.startswith("//", i):
            tokens.append(_Token("op", "//", i))
            i += 2
        elif ch in "+-*/%":
            tokens.append(_Token("op", ch, i))
            i += 1
        elif ch == "(":
            tokens.append(_Token("lparen", ch, i))
            i += 1
        elif ch == ")":
            tokens.append(_Token("rparen", ch, i))
            i += 1
        elif ch == ",":
            tokens.append(_Token("comma", ch, i))
            i += 1
        else:
            raise CalcError("unexpected token %r at position %d" % (ch, i))

    tokens.append(_Token("eof", None, n))
    return tokens


class _Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.env = env
        self.pos = 0
        self.paren_depth = 0

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def unexpected(self, token=None):
        if token is None:
            token = self.current()
        if token.kind == "eof":
            if self.paren_depth:
                raise CalcError("unbalanced parentheses")
            raise CalcError("unexpected end of input")
        raise CalcError(
            "unexpected token %r at position %d" % (token.value, token.pos)
        )

    def expect(self, kind, value=None):
        token = self.current()
        if token.kind != kind or (value is not None and token.value != value):
            self.unexpected(token)
        return self.advance()

    def parse(self):
        if self.current().kind == "eof":
            raise CalcError("empty input")
        value = self.parse_additive()
        if self.current().kind != "eof":
            if self.current().kind == "rparen":
                raise CalcError("unbalanced parentheses")
            self.unexpected()
        return value

    def parse_additive(self):
        value = self.parse_multiplicative()
        while self.current().kind == "op" and self.current().value in ("+", "-"):
            op = self.advance().value
            right = self.parse_multiplicative()
            if op == "+":
                value = value + right
            else:
                value = value - right
        return value

    def parse_multiplicative(self):
        value = self.parse_unary()
        while self.current().kind == "op" and self.current().value in (
            "*",
            "/",
            "//",
            "%",
        ):
            op = self.advance().value
            right = self.parse_unary()
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
                if op == "%":
                    raise CalcError("modulo by zero")
                raise CalcError("division by zero")
        return value

    def parse_unary(self):
        token = self.current()
        if token.kind == "op" and token.value == "+":
            self.advance()
            return +self.parse_unary()
        if token.kind == "op" and token.value == "-":
            self.advance()
            return -self.parse_unary()
        return self.parse_power()

    def parse_power(self):
        value = self.parse_primary()
        if self.current().kind == "op" and self.current().value == "**":
            self.advance()
            # The right side is a unary expression: this makes "**"
            # right-associative and permits a signed exponent.
            exponent = self.parse_unary()
            try:
                value = value ** exponent
            except ZeroDivisionError:
                raise CalcError("zero cannot be raised to a negative power")
        return value

    def parse_primary(self):
        token = self.current()

        if token.kind == "number":
            self.advance()
            return token.value

        if token.kind == "identifier":
            name = self.advance().value
            if self.current().kind == "lparen":
                return self.parse_call(name)
            if name not in self.env:
                raise CalcError("unknown variable %r" % name)
            return self.env[name]

        if token.kind == "lparen":
            self.advance()
            self.paren_depth += 1
            value = self.parse_additive()
            if self.current().kind != "rparen":
                self.unexpected()
            self.advance()
            self.paren_depth -= 1
            return value

        if token.kind == "rparen":
            raise CalcError("unbalanced parentheses")

        self.unexpected(token)

    def parse_call(self, name):
        # The opening parenthesis is the current token.
        self.expect("lparen")
        self.paren_depth += 1

        if name not in ("min", "max", "abs"):
            raise CalcError("unknown function %r" % name)

        args = []
        if self.current().kind != "rparen":
            args.append(self.parse_additive())
            while self.current().kind == "comma":
                self.advance()
                if self.current().kind == "rparen":
                    raise CalcError("unexpected token ')'")
                args.append(self.parse_additive())

        if self.current().kind != "rparen":
            self.unexpected()
        self.advance()
        self.paren_depth -= 1

        if name == "abs":
            if len(args) != 1:
                raise CalcError("abs() takes exactly one argument")
            return abs(args[0])
        if not args:
            raise CalcError("%s() requires at least one argument" % name)
        if name == "min":
            return min(args)
        return max(args)


def evaluate(expr, env=None):
    """Evaluate a calculator expression according to SPEC.md."""
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")
    if env is None:
        env = {}
    tokens = _tokenize(expr)
    return _Parser(tokens, env).parse()
