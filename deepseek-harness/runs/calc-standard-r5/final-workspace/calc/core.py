"""A small arithmetic expression evaluator.

The grammar implemented here (lowest to highest precedence) is::

    expression := term (("+" | "-") term)*
    term       := unary (("*" | "/" | "//" | "%") unary)*
    unary      := ("+" | "-") unary | power
    power      := atom ("**" unary)?
    atom       := NUMBER
                | IDENT
                | IDENT "(" arguments ")"
                | "(" expression ")"

``**`` is right-associative and binds tighter than unary minus, which is why
the right-hand side of ``**`` is parsed as a unary expression.
"""


class CalcError(ValueError):
    pass


# Token kinds.
_NUMBER = "NUMBER"
_IDENT = "IDENT"
_OP = "OP"
_LPAREN = "LPAREN"
_RPAREN = "RPAREN"
_COMMA = "COMMA"
_EOF = "EOF"

_TWO_CHAR_OPS = {"**", "//"}
_ONE_CHAR_OPS = {"+", "-", "*", "/", "%"}

# Functions and their allowed argument counts (min_args, max_args; None means
# unbounded).
_FUNCTIONS = {
    "min": (1, None),
    "max": (1, None),
    "abs": (1, 1),
}


class _Token:
    __slots__ = ("kind", "value")

    def __init__(self, kind, value=None):
        self.kind = kind
        self.value = value

    def __repr__(self):  # pragma: no cover - debugging aid only
        return "_Token(%r, %r)" % (self.kind, self.value)


def _is_digit(ch):
    return "0" <= ch <= "9"


def _is_ident_start(ch):
    return ch.isascii() and (ch.isalpha() or ch == "_")


def _is_ident_char(ch):
    return ch.isascii() and (ch.isalnum() or ch == "_")


def _tokenize(expr):
    tokens = []
    i = 0
    length = len(expr)
    while i < length:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue

        if _is_digit(ch) or (ch == "." and i + 1 < length and _is_digit(expr[i + 1])):
            start = i
            while i < length and _is_digit(expr[i]):
                i += 1
            if i < length and expr[i] == ".":
                i += 1
                while i < length and _is_digit(expr[i]):
                    i += 1
            text = expr[start:i]
            try:
                if "." in text:
                    tokens.append(_Token(_NUMBER, float(text)))
                else:
                    tokens.append(_Token(_NUMBER, int(text)))
            except (ValueError, OverflowError):
                raise CalcError("invalid number: %s" % text)
            continue

        if _is_ident_start(ch):
            start = i
            i += 1
            while i < length and _is_ident_char(expr[i]):
                i += 1
            tokens.append(_Token(_IDENT, expr[start:i]))
            continue

        two = expr[i:i + 2]
        if two in _TWO_CHAR_OPS:
            tokens.append(_Token(_OP, two))
            i += 2
            continue

        if ch in _ONE_CHAR_OPS:
            tokens.append(_Token(_OP, ch))
            i += 1
            continue

        if ch == "(":
            tokens.append(_Token(_LPAREN))
            i += 1
            continue

        if ch == ")":
            tokens.append(_Token(_RPAREN))
            i += 1
            continue

        if ch == ",":
            tokens.append(_Token(_COMMA))
            i += 1
            continue

        raise CalcError("unexpected character: %r" % ch)

    tokens.append(_Token(_EOF))
    return tokens


def _describe(token):
    if token.kind == _EOF:
        return "end of expression"
    if token.kind == _NUMBER:
        return repr(token.value)
    if token.kind == _IDENT:
        return repr(token.value)
    if token.kind == _OP:
        return repr(token.value)
    if token.kind == _LPAREN:
        return "'('"
    if token.kind == _RPAREN:
        return "')'"
    if token.kind == _COMMA:
        return "','"
    return repr(token.value)


class _Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.pos = 0
        self.env = env

    # -- token helpers ---------------------------------------------------
    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def match_op(self, *ops):
        token = self.peek()
        if token.kind == _OP and token.value in ops:
            self.pos += 1
            return token.value
        return None

    def expect(self, kind, message):
        token = self.peek()
        if token.kind != kind:
            raise CalcError(message)
        self.pos += 1
        return token

    # -- grammar ---------------------------------------------------------
    def parse(self):
        value = self.expression()
        token = self.peek()
        if token.kind != _EOF:
            if token.kind == _RPAREN:
                raise CalcError("unbalanced parentheses")
            raise CalcError("unexpected token: %s" % _describe(token))
        return value

    def expression(self):
        value = self.term()
        while True:
            op = self.match_op("+", "-")
            if op is None:
                return value
            right = self.term()
            if op == "+":
                value = value + right
            else:
                value = value - right

    def term(self):
        value = self.unary()
        while True:
            op = self.match_op("*", "/", "//", "%")
            if op is None:
                return value
            right = self.unary()
            if op == "*":
                value = value * right
            elif op == "/":
                if right == 0:
                    raise CalcError("division by zero")
                value = value / right
            elif op == "//":
                if right == 0:
                    raise CalcError("division by zero")
                value = value // right
            else:
                if right == 0:
                    raise CalcError("modulo by zero")
                value = value % right

    def unary(self):
        op = self.match_op("+", "-")
        if op is not None:
            value = self.unary()
            return value if op == "+" else -value
        return self.power()

    def power(self):
        base = self.atom()
        if self.match_op("**") is not None:
            exponent = self.unary()
            try:
                return base ** exponent
            except ZeroDivisionError:
                raise CalcError("division by zero")
            except OverflowError:
                raise CalcError("numeric overflow")
        return base

    def atom(self):
        token = self.peek()

        if token.kind == _NUMBER:
            self.pos += 1
            return token.value

        if token.kind == _IDENT:
            self.pos += 1
            name = token.value
            if self.peek().kind == _LPAREN:
                return self.call(name)
            if name not in self.env:
                raise CalcError("unknown variable: %s" % name)
            return self.env[name]

        if token.kind == _LPAREN:
            self.pos += 1
            value = self.expression()
            if self.peek().kind != _RPAREN:
                raise CalcError("unbalanced parentheses")
            self.pos += 1
            return value

        raise CalcError("unexpected token: %s" % _describe(token))

    def call(self, name):
        if name not in _FUNCTIONS:
            raise CalcError("unknown function: %s" % name)

        # Consume '(' and parse the argument list.
        self.pos += 1
        args = []
        if self.peek().kind != _RPAREN:
            args.append(self.expression())
            while self.peek().kind == _COMMA:
                self.pos += 1
                args.append(self.expression())
        self.expect(_RPAREN, "unbalanced parentheses")

        min_args, max_args = _FUNCTIONS[name]
        count = len(args)
        if count < min_args or (max_args is not None and count > max_args):
            if min_args == max_args:
                expected = "exactly %d argument%s" % (
                    min_args, "" if min_args == 1 else "s")
            elif max_args is None:
                expected = "at least %d argument%s" % (
                    min_args, "" if min_args == 1 else "s")
            else:
                expected = "%d to %d arguments" % (min_args, max_args)
            raise CalcError(
                "%s() takes %s (got %d)" % (name, expected, count))

        if name == "min":
            return min(args)
        if name == "max":
            return max(args)
        return abs(args[0])


def evaluate(expr, env=None):
    """Evaluate *expr*, optionally resolving identifiers from *env*."""
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")
    if env is None:
        env = {}

    tokens = _tokenize(expr)
    if len(tokens) == 1:  # only the EOF token
        raise CalcError("empty expression")

    return _Parser(tokens, env).parse()
