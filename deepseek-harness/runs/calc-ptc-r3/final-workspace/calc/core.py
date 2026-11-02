"""A small arithmetic expression evaluator.

Implements the grammar and semantics described in SPEC.md without using
Python's eval, exec, compile, or the ast module.
"""

import re


class CalcError(ValueError):
    """Raised for any invalid expression or evaluation error."""


# Tokenizer.  Whitespace is insignificant and simply skipped.  Numbers are
# ASCII integers or decimals (3.5, .5); names follow the identifier rule from
# the spec.  Multi-character operators must be tried before their
# single-character prefixes.
_TOKEN_RE = re.compile(
    r"""
      (?P<ws>\s+)
    | (?P<number>(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+))
    | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<op>\*\*|//|[+\-*/%(),])
    """,
    re.VERBOSE,
)

_FUNCTIONS = ("min", "max", "abs")


def _tokenize(expr):
    """Turn expr into a list of (kind, text) tokens.

    For operator tokens the kind is the operator text itself.
    """
    tokens = []
    pos = 0
    length = len(expr)
    while pos < length:
        match = _TOKEN_RE.match(expr, pos)
        if match is None:
            raise CalcError("unexpected character %r" % (expr[pos],))
        pos = match.end()
        kind = match.lastgroup
        text = match.group()
        if kind == "ws":
            continue
        if kind == "op":
            tokens.append((text, text))
        else:
            tokens.append((kind, text))
    return tokens


class _Parser:
    def __init__(self, tokens, env):
        self.tokens = tokens
        self.pos = 0
        self.env = env if env is not None else {}

    # -- token helpers ---------------------------------------------------
    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def advance(self):
        token = self.peek()
        self.pos += 1
        return token

    def expect(self, op):
        kind, text = self.peek()
        if kind != op:
            if kind is None:
                raise CalcError("unbalanced parentheses")
            raise CalcError("unexpected token %r" % (text,))
        self.pos += 1

    # -- grammar ---------------------------------------------------------
    def parse(self):
        if not self.tokens:
            raise CalcError("empty input")
        value = self.parse_expression()
        if self.pos != len(self.tokens):
            kind, text = self.peek()
            raise CalcError("unexpected token %r" % (text,))
        return value

    def parse_expression(self):
        # Lowest precedence: addition and subtraction, left-associative.
        value = self.parse_term()
        while True:
            kind, _text = self.peek()
            if kind == "+":
                self.pos += 1
                value = value + self.parse_term()
            elif kind == "-":
                self.pos += 1
                value = value - self.parse_term()
            else:
                return value

    def parse_term(self):
        # Multiplicative operators, left-associative.
        value = self.parse_unary()
        while True:
            kind, _text = self.peek()
            if kind == "*":
                self.pos += 1
                value = value * self.parse_unary()
            elif kind == "/":
                self.pos += 1
                rhs = self.parse_unary()
                try:
                    value = value / rhs
                except ZeroDivisionError:
                    raise CalcError("division by zero")
            elif kind == "//":
                self.pos += 1
                rhs = self.parse_unary()
                try:
                    value = value // rhs
                except ZeroDivisionError:
                    raise CalcError("integer division by zero")
            elif kind == "%":
                self.pos += 1
                rhs = self.parse_unary()
                try:
                    value = value % rhs
                except ZeroDivisionError:
                    raise CalcError("modulo by zero")
            else:
                return value

    def parse_unary(self):
        # Unary plus/minus bind less tightly than exponentiation, so they are
        # handled here, above parse_power in the call chain.
        kind, _text = self.peek()
        if kind == "+":
            self.pos += 1
            return +self.parse_unary()
        if kind == "-":
            self.pos += 1
            return -self.parse_unary()
        return self.parse_power()

    def parse_power(self):
        # Exponentiation is right-associative and its right operand may itself
        # be a unary expression (2**-1).  Its left operand is an atom, so
        # -2**2 parses as -(2**2).
        base = self.parse_atom()
        if self.peek()[0] == "**":
            self.pos += 1
            exponent = self.parse_unary()
            try:
                return base ** exponent
            except ZeroDivisionError:
                raise CalcError("division by zero in exponentiation")
        return base

    def parse_atom(self):
        kind, text = self.peek()
        if kind == "number":
            self.pos += 1
            if "." in text:
                return float(text)
            return int(text)
        if kind == "name":
            self.pos += 1
            if self.peek()[0] == "(":
                if text not in _FUNCTIONS:
                    raise CalcError("unknown function %r" % (text,))
                return self.parse_call(text)
            if text not in self.env:
                raise CalcError("unknown variable %r" % (text,))
            return self.env[text]
        if kind == "(":
            self.pos += 1
            value = self.parse_expression()
            self.expect(")")
            return value
        if kind is None:
            raise CalcError("unexpected end of input")
        raise CalcError("unexpected token %r" % (text,))

    def parse_call(self, name):
        # The current token is the opening parenthesis.
        self.expect("(")
        args = []
        if self.peek()[0] != ")":
            while True:
                args.append(self.parse_expression())
                if self.peek()[0] == ",":
                    self.pos += 1
                    continue
                break
        self.expect(")")
        return self._apply(name, args)

    @staticmethod
    def _apply(name, args):
        if name == "abs":
            if len(args) != 1:
                raise CalcError("abs() takes exactly one argument")
            return abs(args[0])
        if len(args) < 1:
            raise CalcError("%s() takes at least one argument" % (name,))
        if name == "min":
            return min(args)
        return max(args)


def evaluate(expr, env=None):
    """Evaluate the arithmetic expression expr.

    Variables are resolved from env.  Returns an int when the whole
    computation is integer-valued (except for true division, which always
    returns a float).  Raises CalcError on any invalid input.
    """
    parser = _Parser(_tokenize(expr), env)
    return parser.parse()
