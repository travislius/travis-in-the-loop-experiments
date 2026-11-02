"""A small arithmetic expression evaluator.

The grammar mirrors Python's precedence rules:

    expression   := additive
    additive     := multiplicative (('+' | '-') multiplicative)*
    multiplicative := unary (('*' | '/' | '//' | '%') unary)*
    unary        := ('+' | '-') unary | power
    power        := primary ('**' unary)?
    primary      := NUMBER
                  | IDENT '(' arglist ')'
                  | IDENT
                  | '(' expression ')'
    arglist      := expression (',' expression)*

Because ``unary`` recurses through ``power`` and ``power`` recurses through
``unary`` on its right-hand side, ``**`` is right-associative and binds more
tightly than a leading unary sign (``-2**2 == -4``, ``2**3**2 == 512``).
"""


class CalcError(ValueError):
    """Raised for any invalid expression."""


# Token kinds.
_NUMBER = "NUMBER"
_IDENT = "IDENT"
_OP = "OP"
_LPAREN = "LPAREN"
_RPAREN = "RPAREN"
_COMMA = "COMMA"

_DIGITS = "0123456789"
_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _is_digit(ch):
    return ch in _DIGITS


def _is_ident_start(ch):
    return ch in _LETTERS or ch == "_"


def _is_ident_char(ch):
    return ch in _LETTERS or ch in _DIGITS or ch == "_"


def _tokenize(text):
    """Split *text* into ``(kind, value)`` tokens, ignoring whitespace."""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]

        if ch.isspace():
            i += 1
            continue

        # Number: digits with an optional fractional part, or ".digits".
        if _is_digit(ch) or (ch == "." and i + 1 < n and _is_digit(text[i + 1])):
            start = i
            while i < n and _is_digit(text[i]):
                i += 1
            if i < n and text[i] == ".":
                i += 1
                while i < n and _is_digit(text[i]):
                    i += 1
            tokens.append((_NUMBER, text[start:i]))
            continue

        # Identifier.
        if _is_ident_start(ch):
            start = i
            i += 1
            while i < n and _is_ident_char(text[i]):
                i += 1
            tokens.append((_IDENT, text[start:i]))
            continue

        # Two-character operators come before their one-character prefixes.
        if text.startswith("**", i):
            tokens.append((_OP, "**"))
            i += 2
            continue
        if text.startswith("//", i):
            tokens.append((_OP, "//"))
            i += 2
            continue
        if ch in "+-*/%":
            tokens.append((_OP, ch))
            i += 1
            continue
        if ch == "(":
            tokens.append((_LPAREN, ch))
            i += 1
            continue
        if ch == ")":
            tokens.append((_RPAREN, ch))
            i += 1
            continue
        if ch == ",":
            tokens.append((_COMMA, ch))
            i += 1
            continue

        raise CalcError("unexpected character: %r" % (ch,))

    return tokens


def _number_value(literal):
    if "." in literal:
        return float(literal)
    return int(literal)


class _Parser(object):
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.env = env
        self.pos = 0

    # -- token helpers --------------------------------------------------

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def _peek_kind(self):
        return self._peek()[0]

    def _peek_op(self):
        kind, value = self._peek()
        if kind == _OP:
            return value
        return None

    def _advance(self):
        token = self._peek()
        self.pos += 1
        return token

    def _unexpected(self):
        kind, value = self._peek()
        if kind is None:
            raise CalcError("unexpected end of expression")
        raise CalcError("unexpected token: %r" % (value,))

    # -- grammar --------------------------------------------------------

    def parse(self):
        return self._additive()

    def _additive(self):
        value = self._multiplicative()
        while True:
            op = self._peek_op()
            if op == "+" or op == "-":
                self._advance()
                right = self._multiplicative()
                if op == "+":
                    value = value + right
                else:
                    value = value - right
            else:
                return value

    def _multiplicative(self):
        value = self._unary()
        while True:
            op = self._peek_op()
            if op in ("*", "/", "//", "%"):
                self._advance()
                right = self._unary()
                value = self._binary(op, value, right)
            else:
                return value

    def _unary(self):
        op = self._peek_op()
        if op == "+":
            self._advance()
            return +self._unary()
        if op == "-":
            self._advance()
            return -self._unary()
        return self._power()

    def _power(self):
        base = self._primary()
        if self._peek_op() == "**":
            self._advance()
            exponent = self._unary()
            return self._power_value(base, exponent)
        return base

    def _primary(self):
        kind, value = self._peek()

        if kind == _NUMBER:
            self._advance()
            return _number_value(value)

        if kind == _IDENT:
            self._advance()
            if self._peek_kind() == _LPAREN:
                self._advance()
                arguments = self._arguments()
                return self._call(value, arguments)
            if value not in self.env:
                raise CalcError("unknown variable: %s" % (value,))
            return self.env[value]

        if kind == _LPAREN:
            self._advance()
            result = self._additive()
            if self._peek_kind() != _RPAREN:
                raise CalcError("unbalanced parentheses: expected ')'")
            self._advance()
            return result

        self._unexpected()

    def _arguments(self):
        """Parse a call's argument list; the opening '(' was consumed."""
        arguments = []
        if self._peek_kind() == _RPAREN:
            self._advance()
            return arguments

        arguments.append(self._additive())
        while self._peek_kind() == _COMMA:
            self._advance()
            arguments.append(self._additive())

        if self._peek_kind() != _RPAREN:
            if self._peek_kind() is None:
                raise CalcError("unbalanced parentheses: expected ')'")
            raise CalcError("expected ',' or ')' in function call")
        self._advance()
        return arguments

    # -- operations -----------------------------------------------------

    def _binary(self, op, left, right):
        try:
            if op == "*":
                return left * right
            if op == "/":
                return left / right
            if op == "//":
                return left // right
            return left % right
        except ZeroDivisionError:
            if op == "%":
                raise CalcError("modulo by zero")
            raise CalcError("division by zero")

    def _power_value(self, base, exponent):
        try:
            result = base ** exponent
        except ZeroDivisionError:
            raise CalcError("zero cannot be raised to a negative power")
        if isinstance(result, complex):
            raise CalcError("power operation produced a complex number")
        return result

    def _call(self, name, arguments):
        if name == "abs":
            if len(arguments) != 1:
                raise CalcError("abs() takes exactly 1 argument")
            return abs(arguments[0])
        if name == "min":
            if not arguments:
                raise CalcError("min() requires at least 1 argument")
            return min(arguments)
        if name == "max":
            if not arguments:
                raise CalcError("max() requires at least 1 argument")
            return max(arguments)
        raise CalcError("unknown function: %s" % (name,))


def evaluate(expr, env=None):
    """Evaluate the arithmetic expression *expr*.

    Variables are looked up in *env* (an empty mapping when omitted).  The
    result is an ``int`` whenever the computation involves integers only
    (except for ``/``, which always produces a ``float``).
    """
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")

    if env is None:
        env = {}

    tokens = _tokenize(expr)
    if not tokens:
        raise CalcError("empty expression")

    parser = _Parser(tokens, env)
    result = parser.parse()

    if parser.pos != len(tokens):
        kind, value = tokens[parser.pos]
        if kind == _RPAREN:
            raise CalcError("unbalanced parentheses: unexpected ')'")
        raise CalcError("unexpected token: %r" % (value,))

    return result
