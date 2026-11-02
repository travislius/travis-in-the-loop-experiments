"""A small, safe arithmetic expression evaluator.

The parser is a hand-written recursive-descent parser.  It deliberately does
not use Python's ``eval``, ``exec``, ``compile`` or ``ast`` modules.
"""


class CalcError(ValueError):
    pass


_NUMBER = "NUMBER"
_NAME = "NAME"
_OP = "OP"
_EOF = "EOF"


def _is_identifier_start(ch):
    return ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ch == "_"


def _is_identifier_part(ch):
    return _is_identifier_start(ch) or ("0" <= ch <= "9")


def _tokenize(expr):
    tokens = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        # A decimal may start with a digit (1, 3.5, 3.) or with a dot
        # followed by at least one digit (.5).
        if ("0" <= ch <= "9") or (ch == "." and i + 1 < n and
                                   "0" <= expr[i + 1] <= "9"):
            start = i
            if ch == ".":
                i += 1
                while i < n and "0" <= expr[i] <= "9":
                    i += 1
            else:
                while i < n and "0" <= expr[i] <= "9":
                    i += 1
                if i < n and expr[i] == ".":
                    i += 1
                    while i < n and "0" <= expr[i] <= "9":
                        i += 1
            text = expr[start:i]
            value = float(text) if "." in text else int(text)
            tokens.append((_NUMBER, value, start))
            continue

        if _is_identifier_start(ch):
            start = i
            i += 1
            while i < n and _is_identifier_part(expr[i]):
                i += 1
            tokens.append((_NAME, expr[start:i], start))
            continue

        if expr.startswith("**", i):
            tokens.append((_OP, "**", i))
            i += 2
            continue
        if expr.startswith("//", i):
            tokens.append((_OP, "//", i))
            i += 2
            continue
        if ch in "+-*/%(),":
            tokens.append((_OP, ch, i))
            i += 1
            continue

        raise CalcError("Unexpected character {!r} at position {}".format(ch, i))

    tokens.append((_EOF, None, n))
    return tokens


class _Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.env = env
        self.pos = 0

    @property
    def current(self):
        return self.tokens[self.pos]

    def _advance(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _match_op(self, value):
        if self.current[0] == _OP and self.current[1] == value:
            self.pos += 1
            return True
        return False

    def _unexpected(self):
        kind, value, position = self.current
        if kind == _EOF:
            return CalcError("Unexpected end of expression")
        return CalcError("Unexpected token {!r} at position {}".format(value, position))

    def parse(self):
        if self.current[0] == _EOF:
            raise CalcError("Empty input")

        value = self.parse_additive()
        if self.current[0] != _EOF:
            raise self._unexpected()
        return value

    def parse_additive(self):
        value = self.parse_multiplicative()
        while self.current[0] == _OP and self.current[1] in ("+", "-"):
            op = self._advance()[1]
            right = self.parse_multiplicative()
            try:
                if op == "+":
                    value = value + right
                else:
                    value = value - right
            except (TypeError, ValueError, OverflowError) as exc:
                raise CalcError("Invalid operands for {}: {}".format(op, exc))
        return value

    def parse_multiplicative(self):
        value = self.parse_unary()
        while self.current[0] == _OP and self.current[1] in ("*", "/", "//", "%"):
            op = self._advance()[1]
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
                if op in ("/", "//"):
                    raise CalcError("Division by zero")
                raise CalcError("Modulo by zero")
            except (TypeError, ValueError, OverflowError) as exc:
                raise CalcError("Invalid operands for {}: {}".format(op, exc))
        return value

    def parse_unary(self):
        if self._match_op("+"):
            return +self.parse_unary()
        if self._match_op("-"):
            try:
                return -self.parse_unary()
            except (TypeError, ValueError, OverflowError) as exc:
                raise CalcError("Invalid operand for unary minus: {}".format(exc))
        return self.parse_power()

    def parse_power(self):
        base = self.parse_primary()
        if self._match_op("**"):
            exponent = self.parse_unary()
            try:
                return base ** exponent
            except ZeroDivisionError:
                raise CalcError("Division by zero")
            except (TypeError, ValueError, OverflowError) as exc:
                raise CalcError("Invalid exponentiation: {}".format(exc))
        return base

    def parse_primary(self):
        token = self.current

        if token[0] == _NUMBER:
            self._advance()
            return token[1]

        if token[0] == _NAME:
            name = self._advance()[1]
            if self._match_op("("):
                args = self._parse_arguments()
                return self._call_function(name, args)
            if self.env is None or name not in self.env:
                raise CalcError("Unknown variable: {}".format(name))
            return self.env[name]

        if self._match_op("("):
            value = self.parse_additive()
            if not self._match_op(")"):
                if self.current[0] == _EOF:
                    raise CalcError("Unbalanced parentheses")
                raise self._unexpected()
            return value

        raise self._unexpected()

    def _parse_arguments(self):
        args = []
        if self._match_op(")"):
            return args

        while True:
            args.append(self.parse_additive())
            if self._match_op(","):
                continue
            if self._match_op(")"):
                return args
            if self.current[0] == _EOF:
                raise CalcError("Unbalanced parentheses")
            raise self._unexpected()

    def _call_function(self, name, args):
        if name == "abs":
            if len(args) != 1:
                raise CalcError("abs() takes exactly 1 argument")
            try:
                return abs(args[0])
            except (TypeError, ValueError, OverflowError) as exc:
                raise CalcError("Invalid argument to abs(): {}".format(exc))

        if name == "min":
            if len(args) < 1:
                raise CalcError("min() requires at least 1 argument")
            try:
                return min(args)
            except (TypeError, ValueError) as exc:
                raise CalcError("Invalid arguments to min(): {}".format(exc))

        if name == "max":
            if len(args) < 1:
                raise CalcError("max() requires at least 1 argument")
            try:
                return max(args)
            except (TypeError, ValueError) as exc:
                raise CalcError("Invalid arguments to max(): {}".format(exc))

        raise CalcError("Unknown function: {}".format(name))


def evaluate(expr, env=None):
    """Evaluate *expr* using an optional mapping of variable names to values."""
    if not isinstance(expr, str):
        raise CalcError("Expression must be a string")
    parser = _Parser(_tokenize(expr), env)
    return parser.parse()
