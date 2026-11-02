"""A small expression evaluator.

The grammar implemented here follows SPEC.md, from lowest to highest
precedence::

    expression := term (("+" | "-") term)*
    term       := unary (("*" | "/" | "//" | "%") unary)*
    unary      := ("+" | "-") unary | power
    power      := primary ("**" unary)?
    primary    := NUMBER | IDENTIFIER | IDENTIFIER "(" arguments ")" | "(" expression ")"

``power`` is right-associative because its exponent is parsed as a ``unary``
(which itself eventually reaches ``power``), and it binds tighter than unary
minus because ``unary`` delegates to ``power`` only when it has no sign.
"""

import re

_NUMBER_RE = re.compile(r"(?:\d+\.\d*|\.\d+|\d+)")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Two-character operators must be tested before their one-character prefixes.
_TWO_CHAR_OPS = ("//", "**")
_ONE_CHAR_OPS = ("+", "-", "*", "/", "%")


class CalcError(ValueError):
    pass


class _Parser:
    def __init__(self, text, env):
        self.text = text
        self.pos = 0
        self.env = env

    # -- helpers ---------------------------------------------------------
    def error(self, message):
        raise CalcError(message)

    def skip_ws(self):
        text = self.text
        while self.pos < len(text) and text[self.pos].isspace():
            self.pos += 1

    def peek(self):
        """Return the next non-whitespace character, or '' at end of input."""
        self.skip_ws()
        if self.pos < len(self.text):
            return self.text[self.pos]
        return ""

    def at_end(self):
        return self.pos >= len(self.text)

    # -- grammar ---------------------------------------------------------
    def parse(self):
        self.skip_ws()
        if self.at_end():
            self.error("empty expression")
        value = self.expression()
        self.skip_ws()
        if not self.at_end():
            self.error("unexpected token: %r" % (self.text[self.pos],))
        return value

    def expression(self):
        left = self.term()
        while True:
            ch = self.peek()
            if ch == "+":
                self.pos += 1
                left = left + self.term()
            elif ch == "-":
                self.pos += 1
                left = left - self.term()
            else:
                return left

    def term(self):
        left = self.unary()
        while True:
            self.skip_ws()
            rest = self.text[self.pos:]
            if rest.startswith("//"):
                self.pos += 2
                right = self.unary()
                try:
                    left = left // right
                except ZeroDivisionError:
                    self.error("integer division by zero")
            elif rest.startswith("**"):
                # A well-formed power consumed its own '**'; anything left is
                # an unexpected token.
                return left
            elif rest.startswith("*"):
                self.pos += 1
                left = left * self.unary()
            elif rest.startswith("/"):
                self.pos += 1
                right = self.unary()
                try:
                    left = left / right
                except ZeroDivisionError:
                    self.error("division by zero")
            elif rest.startswith("%"):
                self.pos += 1
                right = self.unary()
                try:
                    left = left % right
                except ZeroDivisionError:
                    self.error("modulo by zero")
            else:
                return left

    def unary(self):
        ch = self.peek()
        if ch == "-":
            self.pos += 1
            return -self.unary()
        if ch == "+":
            self.pos += 1
            return +self.unary()
        return self.power()

    def power(self):
        base = self.primary()
        self.skip_ws()
        if self.text.startswith("**", self.pos):
            self.pos += 2
            exponent = self.unary()
            try:
                value = base ** exponent
            except ZeroDivisionError:
                self.error("division by zero")
            except OverflowError:
                self.error("numeric overflow")
            if isinstance(value, complex):
                self.error("result is not a real number")
            return value
        return base

    def primary(self):
        ch = self.peek()
        if ch == "":
            self.error("unexpected end of expression")
        if ch == "(":
            self.pos += 1
            value = self.expression()
            self.skip_ws()
            if self.at_end() or self.text[self.pos] != ")":
                self.error("unbalanced parentheses: missing ')'")
            self.pos += 1
            return value
        if ch == ")":
            self.error("unbalanced parentheses: unexpected ')'")

        match = _NUMBER_RE.match(self.text, self.pos)
        if match:
            token = match.group(0)
            self.pos = match.end()
            if "." in token:
                return float(token)
            return int(token)

        match = _IDENT_RE.match(self.text, self.pos)
        if match:
            name = match.group(0)
            self.pos = match.end()
            self.skip_ws()
            if not self.at_end() and self.text[self.pos] == "(":
                return self.call(name)
            return self.lookup(name)

        self.error("unexpected token: %r" % (ch,))

    # -- identifiers and calls ------------------------------------------
    def lookup(self, name):
        if name in self.env:
            return self.env[name]
        self.error("unknown variable: %s" % (name,))

    def call(self, name):
        # self.pos is at the opening parenthesis.
        self.pos += 1
        args = []
        self.skip_ws()
        if not self.at_end() and self.text[self.pos] == ")":
            self.pos += 1
        else:
            while True:
                args.append(self.expression())
                self.skip_ws()
                if self.at_end():
                    self.error("unbalanced parentheses: missing ')'")
                ch = self.text[self.pos]
                if ch == ",":
                    self.pos += 1
                    continue
                if ch == ")":
                    self.pos += 1
                    break
                self.error("unexpected token: %r" % (ch,))

        if name == "abs":
            if len(args) != 1:
                self.error("abs() takes exactly 1 argument")
            return abs(args[0])
        if name == "min":
            if not args:
                self.error("min() takes at least 1 argument")
            return min(args)
        if name == "max":
            if not args:
                self.error("max() takes at least 1 argument")
            return max(args)
        self.error("unknown function: %s" % (name,))


def evaluate(expr, env=None):
    """Evaluate *expr* using variables from *env* and return an int or float.

    Raises ``CalcError`` (a ``ValueError``) for malformed or invalid
    expressions.
    """
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")
    parser = _Parser(expr, {} if env is None else env)
    return parser.parse()
