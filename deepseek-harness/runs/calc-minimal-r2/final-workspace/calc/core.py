"""A small arithmetic expression evaluator.

The implementation is a hand-written tokenizer and recursive-descent parser.
It deliberately does not use Python's ``eval``/``exec``/``compile`` or the
``ast`` module.
"""


class CalcError(ValueError):
    """Raised for malformed expressions and evaluation errors."""


class _Token:
    __slots__ = ("kind", "value", "pos")

    def __init__(self, kind, value, pos):
        self.kind = kind
        self.value = value
        self.pos = pos

    def __repr__(self):
        return "_Token(%r, %r, %r)" % (self.kind, self.value, self.pos)


_NUMBER_CHARS = set("0123456789.")
_IDENT_START = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_")
_IDENT_CONT = _IDENT_START | set("0123456789")


def _tokenize(expr):
    tokens = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue

        # A decimal may begin with a dot, but a lone dot is not a number.
        if ch.isdigit() or (ch == "." and i + 1 < n and expr[i + 1].isdigit()):
            start = i
            saw_dot = False
            while i < n and (expr[i].isdigit() or expr[i] == "."):
                if expr[i] == ".":
                    if saw_dot:
                        # Let the parser report the second dot as an
                        # unexpected token via the tokens already produced.
                        break
                    saw_dot = True
                i += 1
            text = expr[start:i]
            try:
                value = float(text) if saw_dot else int(text)
            except ValueError:
                raise CalcError("invalid number at position %d" % start)
            tokens.append(_Token("number", value, start))
            continue

        if ch in _IDENT_START:
            start = i
            i += 1
            while i < n and expr[i] in _IDENT_CONT:
                i += 1
            tokens.append(_Token("ident", expr[start:i], start))
            continue

        if expr.startswith("**", i):
            tokens.append(_Token("op", "**", i))
            i += 2
            continue
        if expr.startswith("//", i):
            tokens.append(_Token("op", "//", i))
            i += 2
            continue
        if ch in "+-*/%":
            tokens.append(_Token("op", ch, i))
            i += 1
            continue
        if ch == "(":
            tokens.append(_Token("lparen", ch, i))
            i += 1
            continue
        if ch == ")":
            tokens.append(_Token("rparen", ch, i))
            i += 1
            continue
        if ch == ",":
            tokens.append(_Token("comma", ch, i))
            i += 1
            continue

        raise CalcError("unexpected token %r at position %d" % (ch, i))

    tokens.append(_Token("eof", None, n))
    return tokens


class _Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.env = env
        self.index = 0

    @property
    def current(self):
        return self.tokens[self.index]

    def advance(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _is_op(self, value):
        tok = self.current
        return tok.kind == "op" and tok.value == value

    def parse(self):
        if self.current.kind == "eof":
            raise CalcError("empty input")

        result = self.parse_additive()
        if self.current.kind != "eof":
            tok = self.current
            if tok.kind == "rparen":
                raise CalcError("unbalanced parentheses at position %d" % tok.pos)
            raise CalcError("unexpected token at position %d" % tok.pos)
        return result

    def parse_additive(self):
        value = self.parse_multiplicative()
        while self.current.kind == "op" and self.current.value in ("+", "-"):
            op = self.advance().value
            rhs = self.parse_multiplicative()
            if op == "+":
                value = value + rhs
            else:
                value = value - rhs
        return value

    def parse_multiplicative(self):
        value = self.parse_unary()
        while self.current.kind == "op" and self.current.value in (
            "*",
            "/",
            "//",
            "%",
        ):
            op = self.advance().value
            rhs = self.parse_unary()
            try:
                if op == "*":
                    value = value * rhs
                elif op == "/":
                    value = value / rhs
                elif op == "//":
                    value = value // rhs
                else:
                    value = value % rhs
            except ZeroDivisionError:
                if op == "/":
                    raise CalcError("division by zero")
                raise CalcError("modulo by zero")
            except (ArithmeticError, TypeError, ValueError) as exc:
                raise CalcError("arithmetic error: %s" % exc)
        return value

    def parse_unary(self):
        if self._is_op("+"):
            self.advance()
            return self.parse_unary()
        if self._is_op("-"):
            self.advance()
            return -self.parse_unary()
        return self.parse_power()

    def parse_power(self):
        value = self.parse_primary()
        if self._is_op("**"):
            self.advance()
            # The right operand is a unary expression.  This makes **
            # right-associative and permits forms such as 2**-1.
            rhs = self.parse_unary()
            try:
                value = value ** rhs
            except ZeroDivisionError:
                raise CalcError("zero cannot be raised to a negative power")
            except (ArithmeticError, TypeError, ValueError) as exc:
                raise CalcError("arithmetic error: %s" % exc)
        return value

    def parse_primary(self):
        tok = self.current
        if tok.kind == "number":
            self.advance()
            return tok.value

        if tok.kind == "ident":
            name = tok.value
            self.advance()
            if self.current.kind == "lparen":
                return self.parse_call(name)
            if name not in self.env:
                raise CalcError("unknown variable %r" % name)
            return self.env[name]

        if tok.kind == "lparen":
            self.advance()
            if self.current.kind == "rparen":
                raise CalcError("unexpected token at position %d" % self.current.pos)
            if self.current.kind == "eof":
                raise CalcError("unbalanced parentheses")
            value = self.parse_additive()
            if self.current.kind != "rparen":
                raise CalcError("unbalanced parentheses")
            self.advance()
            return value

        if tok.kind == "eof":
            raise CalcError("unexpected end of expression")
        raise CalcError("unexpected token at position %d" % tok.pos)

    def parse_call(self, name):
        # Current token is the opening parenthesis.
        self.advance()
        args = []

        if self.current.kind == "rparen":
            self.advance()
        else:
            while True:
                if self.current.kind == "eof":
                    raise CalcError("unbalanced parentheses")
                args.append(self.parse_additive())
                if self.current.kind == "comma":
                    self.advance()
                    if self.current.kind in ("rparen", "eof"):
                        raise CalcError("unexpected token at position %d" % self.current.pos)
                    continue
                if self.current.kind == "rparen":
                    self.advance()
                    break
                if self.current.kind == "eof":
                    raise CalcError("unbalanced parentheses")
                raise CalcError("unexpected token at position %d" % self.current.pos)

        if name == "abs":
            if len(args) != 1:
                raise CalcError("abs() takes exactly 1 argument")
            return abs(args[0])
        if name == "min":
            if len(args) < 1:
                raise CalcError("min() requires at least 1 argument")
            return min(args)
        if name == "max":
            if len(args) < 1:
                raise CalcError("max() requires at least 1 argument")
            return max(args)

        raise CalcError("unknown function %r" % name)


def evaluate(expr, env=None):
    """Evaluate *expr* using *env* for variable lookup.

    ``env`` defaults to an empty mapping.  Only the grammar described in the
    project specification is supported; malformed expressions raise
    :class:`CalcError`.
    """
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")
    if env is None:
        env = {}
    tokens = _tokenize(expr)
    return _Parser(tokens, env).parse()
