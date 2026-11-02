"""A small arithmetic expression evaluator.

This module implements the language described in SPEC.md with a hand-written
tokenizer and recursive-descent parser.
"""

import re


class CalcError(ValueError):
    """Raised when an expression cannot be tokenized, parsed, or evaluated."""


# A number is either digits with an optional fractional part (including a
# trailing dot), or a leading dot followed by digits.
_NUMBER_PATTERN = r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)"
_IDENT_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"

_NUMBER = "number"
_IDENT = "ident"
_OP = "op"
_EOF = "eof"


def _tokenize(text):
    """Return a list of (kind, value) tokens ending with an EOF token."""
    tokens = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]

        if ch.isspace():
            i += 1
            continue

        if "0" <= ch <= "9" or (
            ch == "." and i + 1 < length and "0" <= text[i + 1] <= "9"
        ):
            match = re.match(_NUMBER_PATTERN, text[i:])
            lexeme = match.group(0)
            if "." in lexeme:
                value = float(lexeme)
            else:
                value = int(lexeme)
            tokens.append((_NUMBER, value))
            i += len(lexeme)
            continue

        if ch == "_" or "A" <= ch <= "Z" or "a" <= ch <= "z":
            match = re.match(_IDENT_PATTERN, text[i:])
            lexeme = match.group(0)
            tokens.append((_IDENT, lexeme))
            i += len(lexeme)
            continue

        two = text[i : i + 2]
        if two == "**" or two == "//":
            tokens.append((_OP, two))
            i += 2
            continue

        if ch in "+-*/%(),":
            tokens.append((_OP, ch))
            i += 1
            continue

        raise CalcError("unexpected token %r" % ch)

    tokens.append((_EOF, None))
    return tokens


class _Parser:
    def __init__(self, tokens, env):
        self._tokens = tokens
        self._pos = 0
        self._env = env
        self._depth = 0

    # -- token helpers -------------------------------------------------
    def _peek(self):
        return self._tokens[self._pos]

    def _advance(self):
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    @staticmethod
    def _is_op(token, *ops):
        return token[0] == _OP and token[1] in ops

    # -- grammar -------------------------------------------------------
    def parse(self):
        if self._peek()[0] == _EOF:
            raise CalcError("empty input")

        value = self._expression()
        token = self._peek()
        if token[0] != _EOF:
            if self._is_op(token, ")"):
                raise CalcError("unbalanced parentheses: unexpected ')'")
            raise CalcError("unexpected token %r" % (token[1],))
        return value

    # expression := term (('+' | '-') term)*
    def _expression(self):
        value = self._term()
        while True:
            token = self._peek()
            if not self._is_op(token, "+", "-"):
                return value
            op = self._advance()[1]
            right = self._term()
            value = self._binary(op, value, right)

    # term := unary (('*' | '/' | '//' | '%') unary)*
    def _term(self):
        value = self._unary()
        while True:
            token = self._peek()
            if not self._is_op(token, "*", "/", "//", "%"):
                return value
            op = self._advance()[1]
            right = self._unary()
            value = self._binary(op, value, right)

    # unary := ('+' | '-') unary | power
    def _unary(self):
        token = self._peek()
        if self._is_op(token, "+", "-"):
            op = self._advance()[1]
            operand = self._unary()
            return -operand if op == "-" else +operand
        return self._power()

    # power := atom ('**' unary)?
    #
    # Parsing the right operand as a unary expression makes power
    # right-associative and lets it accept unary signs on the exponent, which
    # yields Python's precedence: -2**2 == -4 and 2**3**2 == 512.
    def _power(self):
        base = self._atom()
        token = self._peek()
        if self._is_op(token, "**"):
            self._advance()
            exponent = self._unary()
            return self._binary("**", base, exponent)
        return base

    def _atom(self):
        token = self._peek()
        kind, value = token

        if kind == _NUMBER:
            self._advance()
            return value

        if kind == _IDENT:
            self._advance()
            name = value
            if self._is_op(self._peek(), "("):
                return self._call(name)
            return self._lookup(name)

        if self._is_op(token, "("):
            self._advance()
            self._depth += 1
            value = self._expression()
            if self._is_op(self._peek(), ")"):
                self._advance()
                self._depth -= 1
                return value
            raise CalcError("unbalanced parentheses: expected ')'")

        if self._is_op(token, ")"):
            raise CalcError("unbalanced parentheses: unexpected ')'")

        if kind == _EOF:
            if self._depth:
                raise CalcError("unbalanced parentheses: expected ')'")
            raise CalcError("unexpected token: end of input")

        raise CalcError("unexpected token %r" % (value,))

    def _call(self, name):
        self._advance()  # consume '('
        self._depth += 1
        args = []

        token = self._peek()
        if self._is_op(token, ")"):
            self._advance()
            self._depth -= 1
        else:
            args.append(self._expression())
            while True:
                token = self._peek()
                if self._is_op(token, ","):
                    self._advance()
                    args.append(self._expression())
                elif self._is_op(token, ")"):
                    self._advance()
                    self._depth -= 1
                    break
                elif token[0] == _EOF:
                    raise CalcError("unbalanced parentheses: expected ')'")
                else:
                    raise CalcError("unexpected token %r" % (token[1],))

        if name == "abs":
            if len(args) != 1:
                raise CalcError(
                    "wrong number of arguments for abs(): "
                    "takes exactly 1 argument (%d given)" % len(args)
                )
            return abs(args[0])
        if name == "min":
            if not args:
                raise CalcError(
                    "wrong number of arguments for min(): "
                    "requires at least 1 argument (0 given)"
                )
            return min(args)
        if name == "max":
            if not args:
                raise CalcError(
                    "wrong number of arguments for max(): "
                    "requires at least 1 argument (0 given)"
                )
            return max(args)

        raise CalcError("unknown function %r" % name)

    def _lookup(self, name):
        if name not in self._env:
            raise CalcError("unknown variable %r" % name)
        return self._env[name]

    @staticmethod
    def _binary(op, left, right):
        try:
            if op == "+":
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                return left / right
            if op == "//":
                return left // right
            if op == "%":
                return left % right
            if op == "**":
                return left ** right
        except ZeroDivisionError:
            if op == "%":
                raise CalcError("modulo by zero") from None
            raise CalcError("division by zero") from None

        raise CalcError("unexpected token %r" % (op,))


def evaluate(expr, env=None):
    """Evaluate an arithmetic expression and return an int or float.

    env is an optional mapping from variable names to numeric values.
    CalcError is raised for malformed expressions and semantic errors.
    """
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")

    tokens = _tokenize(expr)
    parser = _Parser(tokens, {} if env is None else env)
    return parser.parse()
