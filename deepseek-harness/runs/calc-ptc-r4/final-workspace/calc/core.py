class CalcError(ValueError):
    pass


_ASCII_DIGITS = "0123456789"
_ASCII_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_WHITESPACE = " \t\r\n\f\v"
_IDENT_START = _ASCII_LETTERS + "_"
_IDENT_CHARS = _IDENT_START + _ASCII_DIGITS


def _is_digit(ch):
    return ch in _ASCII_DIGITS


def _is_ident_start(ch):
    return ch in _IDENT_START


def _is_ident_char(ch):
    return ch in _IDENT_CHARS


def _apply(op, left, right):
    """Apply an arithmetic operator, translating zero-division to CalcError."""
    try:
        if op == "/":
            return left / right
        if op == "//":
            return left // right
        if op == "%":
            return left % right
    except ZeroDivisionError:
        raise CalcError("division or modulo by zero") from None
    raise CalcError("unknown operator %r" % (op,))  # pragma: no cover


def _power(base, exponent):
    try:
        return base ** exponent
    except ZeroDivisionError:
        raise CalcError("zero cannot be raised to a negative power") from None


class _Parser:
    def __init__(self, text, env):
        self.text = text
        self.pos = 0
        self.env = env

    # -- helpers ---------------------------------------------------------
    def _skip_ws(self):
        text = self.text
        n = len(text)
        while self.pos < n and text[self.pos] in _WHITESPACE:
            self.pos += 1

    def _number(self):
        text = self.text
        n = len(text)
        start = self.pos
        is_float = False
        while self.pos < n and _is_digit(text[self.pos]):
            self.pos += 1
        if self.pos < n and text[self.pos] == ".":
            is_float = True
            self.pos += 1
            while self.pos < n and _is_digit(text[self.pos]):
                self.pos += 1
        literal = text[start:self.pos]
        if is_float:
            return float(literal)
        return int(literal)

    def _name(self):
        text = self.text
        n = len(text)
        start = self.pos
        self.pos += 1
        while self.pos < n and _is_ident_char(text[self.pos]):
            self.pos += 1
        name = text[start:self.pos]

        self._skip_ws()
        if self.pos < n and text[self.pos] == "(":
            return self._call(name)
        if name in self.env:
            return self.env[name]
        raise CalcError("unknown variable %r" % (name,))

    def _call(self, name):
        text = self.text
        n = len(text)
        # Consume '('.
        self.pos += 1
        args = []
        self._skip_ws()
        if self.pos < n and text[self.pos] == ")":
            self.pos += 1
        else:
            while True:
                args.append(self._expr())
                self._skip_ws()
                if self.pos < n and text[self.pos] == ",":
                    self.pos += 1
                    continue
                if self.pos < n and text[self.pos] == ")":
                    self.pos += 1
                    break
                if self.pos >= n:
                    raise CalcError("unbalanced parentheses: expected ')'")
                raise CalcError("unexpected token %r" % (text[self.pos],))
        return self._invoke(name, args)

    def _invoke(self, name, args):
        if name == "abs":
            if len(args) != 1:
                raise CalcError("abs() takes exactly 1 argument (%d given)" % len(args))
            return abs(args[0])
        if name == "min":
            if not args:
                raise CalcError("min() takes at least 1 argument (0 given)")
            return min(args)
        if name == "max":
            if not args:
                raise CalcError("max() takes at least 1 argument (0 given)")
            return max(args)
        raise CalcError("unknown function %r" % (name,))

    # -- grammar ---------------------------------------------------------
    def parse(self):
        self._skip_ws()
        if self.pos >= len(self.text):
            raise CalcError("empty expression")
        value = self._expr()
        self._skip_ws()
        if self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == ")":
                raise CalcError("unbalanced parentheses: unexpected ')'")
            raise CalcError("unexpected token %r" % (ch,))
        return value

    def _expr(self):
        value = self._term()
        while True:
            self._skip_ws()
            if self.pos >= len(self.text):
                return value
            ch = self.text[self.pos]
            if ch == "+":
                self.pos += 1
                value = value + self._term()
            elif ch == "-":
                self.pos += 1
                value = value - self._term()
            else:
                return value

    def _term(self):
        value = self._unary()
        while True:
            self._skip_ws()
            if self.pos >= len(self.text):
                return value
            text = self.text
            if text.startswith("//", self.pos):
                self.pos += 2
                right = self._unary()
                value = _apply("//", value, right)
            elif text.startswith("**", self.pos):
                # '**' is consumed by _power; reaching it here means a
                # malformed expression, which the caller reports.
                return value
            elif text[self.pos] == "*":
                self.pos += 1
                value = value * self._unary()
            elif text[self.pos] == "/":
                self.pos += 1
                right = self._unary()
                value = _apply("/", value, right)
            elif text[self.pos] == "%":
                self.pos += 1
                right = self._unary()
                value = _apply("%", value, right)
            else:
                return value

    def _unary(self):
        self._skip_ws()
        if self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == "+":
                self.pos += 1
                return +self._unary()
            if ch == "-":
                self.pos += 1
                return -self._unary()
        return self._power()

    def _power(self):
        base = self._atom()
        self._skip_ws()
        if self.text.startswith("**", self.pos):
            self.pos += 2
            exponent = self._unary()
            return _power(base, exponent)
        return base

    def _atom(self):
        self._skip_ws()
        text = self.text
        n = len(text)
        if self.pos >= n:
            raise CalcError("unexpected end of expression")
        ch = text[self.pos]
        if _is_digit(ch):
            return self._number()
        if ch == "." and self.pos + 1 < n and _is_digit(text[self.pos + 1]):
            return self._number()
        if ch == "(":
            self.pos += 1
            value = self._expr()
            self._skip_ws()
            if self.pos >= n or text[self.pos] != ")":
                raise CalcError("unbalanced parentheses: expected ')'")
            self.pos += 1
            return value
        if ch == ")":
            raise CalcError("unbalanced parentheses: unexpected ')'")
        if _is_ident_start(ch):
            return self._name()
        raise CalcError("unexpected token %r" % (ch,))


def evaluate(expr, env=None):
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")
    if env is None:
        env = {}
    return _Parser(expr, env).parse()
