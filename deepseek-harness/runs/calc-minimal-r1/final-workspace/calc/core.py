"""A small arithmetic expression evaluator.

The implementation uses a hand-written tokenizer and recursive-descent parser,
without relying on Python's dynamic code-execution facilities.
"""


class CalcError(ValueError):
    """Raised for invalid expressions and evaluation errors."""


# Token kinds.  The exact kind strings are private to this module.
_NUMBER = "NUMBER"
_IDENT = "IDENT"
_OP = "OP"
_EOF = "EOF"

_PUNCTUATION = set("+-*/%(),")


def _is_ident_start(ch):
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "_"


def _is_ident_part(ch):
    return _is_ident_start(ch) or ("0" <= ch <= "9")


def _token_description(token):
    """Return a human-readable description of a token for error messages."""
    kind, value, _pos = token
    if kind == _EOF:
        return "end of input"
    if kind == _NUMBER:
        return repr(value)
    return repr(value)


def _tokenize(expr):
    """Turn *expr* into a list of ``(kind, value, position)`` tuples.

    Only the number syntax described by the specification is accepted:
    integers, decimals with a fractional part, and decimals beginning with a
    dot.  A trailing decimal point (for example ``3.``) is treated as a
    decimal as well, which is consistent with Python's float literal syntax.
    """
    tokens = []
    i = 0
    length = len(expr)

    while i < length:
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        # A number can be either digits followed by an optional fraction, or
        # a dot followed by digits.  Keep the original spelling only to decide
        # whether the result should be an int or a float.
        if ("0" <= ch <= "9") or (ch == "." and i + 1 < length and "0" <= expr[i + 1] <= "9"):
            start = i
            is_float = False
            if ch == ".":
                is_float = True
                i += 1
                while i < length and "0" <= expr[i] <= "9":
                    i += 1
            else:
                while i < length and "0" <= expr[i] <= "9":
                    i += 1
                if i < length and expr[i] == ".":
                    is_float = True
                    i += 1
                    # The fractional part may be empty, as in Python's ``3.``.
                    while i < length and "0" <= expr[i] <= "9":
                        i += 1

            text = expr[start:i]
            try:
                value = float(text) if is_float else int(text)
            except ValueError:
                raise CalcError("unexpected token %r" % (text,)) from None
            tokens.append((_NUMBER, value, start))
            continue

        if _is_ident_start(ch):
            start = i
            i += 1
            while i < length and _is_ident_part(expr[i]):
                i += 1
            tokens.append((_IDENT, expr[start:i], start))
            continue

        if ch in _PUNCTUATION:
            if ch == "*" and i + 1 < length and expr[i + 1] == "*":
                tokens.append((_OP, "**", i))
                i += 2
            elif ch == "/" and i + 1 < length and expr[i + 1] == "/":
                tokens.append((_OP, "//", i))
                i += 2
            else:
                tokens.append((_OP, ch, i))
                i += 1
            continue

        raise CalcError("unexpected token %r at position %d" % (ch, i))

    tokens.append((_EOF, None, length))
    return tokens


class _Parser:
    """Recursive-descent parser for the expression grammar."""

    def __init__(self, tokens, env):
        self.tokens = tokens
        self.env = env
        self.pos = 0
        # Used only to give a more accurate error message for a missing
        # closing parenthesis.
        self.paren_depth = 0

    @property
    def current(self):
        return self.tokens[self.pos]

    def _advance(self):
        token = self.current
        if token[0] != _EOF:
            self.pos += 1
        return token

    def _unexpected(self, expected=None):
        token = self.current
        if token[0] == _EOF and self.paren_depth > 0:
            raise CalcError("unbalanced parentheses: missing ')'")
        if expected:
            raise CalcError(
                "unexpected token %s (expected %s)"
                % (_token_description(token), expected)
            )
        raise CalcError("unexpected token %s" % (_token_description(token),))

    def parse(self):
        if self.current[0] == _EOF:
            raise CalcError("empty input")

        value = self._parse_additive()

        if self.current[0] != _EOF:
            if self.current[0] == _OP and self.current[1] == ")":
                raise CalcError("unbalanced parentheses: unexpected ')'")
            self._unexpected()

        return value

    def _parse_additive(self):
        value = self._parse_multiplicative()
        while self.current[0] == _OP and self.current[1] in ("+", "-"):
            op = self._advance()[1]
            right = self._parse_multiplicative()
            value = _apply_binary(op, value, right)
        return value

    def _parse_multiplicative(self):
        value = self._parse_unary()
        while self.current[0] == _OP and self.current[1] in ("*", "/", "//", "%"):
            op = self._advance()[1]
            right = self._parse_unary()
            value = _apply_binary(op, value, right)
        return value

    def _parse_unary(self):
        if self.current[0] == _OP and self.current[1] in ("+", "-"):
            op = self._advance()[1]
            operand = self._parse_unary()
            return _apply_unary(op, operand)
        return self._parse_power()

    def _parse_power(self):
        left = self._parse_primary()
        if self.current[0] == _OP and self.current[1] == "**":
            self._advance()
            # Parsing the right operand at the unary level makes **
            # right-associative while still allowing 2**-1.
            right = self._parse_unary()
            return _apply_binary("**", left, right)
        return left

    def _parse_primary(self):
        token = self.current

        if token[0] == _NUMBER:
            self._advance()
            return token[1]

        if token[0] == _IDENT:
            name = self._advance()[1]
            if self.current[0] == _OP and self.current[1] == "(":
                return self._parse_call(name)
            return self._lookup_variable(name)

        if token[0] == _OP and token[1] == "(":
            self._advance()
            self.paren_depth += 1
            try:
                value = self._parse_additive()
                if not (self.current[0] == _OP and self.current[1] == ")"):
                    if self.current[0] == _EOF:
                        raise CalcError("unbalanced parentheses: missing ')'")
                    self._unexpected("')'")
                self._advance()  # consume ')'
                return value
            finally:
                self.paren_depth -= 1

        if token[0] == _OP and token[1] == ")":
            raise CalcError("unbalanced parentheses: unexpected ')'")

        self._unexpected()

    def _lookup_variable(self, name):
        if self.env is None or name not in self.env:
            raise CalcError("unknown variable %r" % (name,))
        value = self.env[name]
        return _require_number(value, "variable %r" % (name,))

    def _parse_call(self, name):
        # Only the three functions named by the specification exist.
        if name not in ("min", "max", "abs"):
            raise CalcError("unknown function %r" % (name,))

        self._advance()  # consume '('
        self.paren_depth += 1
        try:
            args = []
            if self.current[0] == _OP and self.current[1] == ")":
                self._advance()
            else:
                while True:
                    args.append(self._parse_additive())
                    if self.current[0] == _OP and self.current[1] == ",":
                        self._advance()
                        continue
                    if self.current[0] == _OP and self.current[1] == ")":
                        self._advance()
                        break
                    if self.current[0] == _EOF:
                        raise CalcError("unbalanced parentheses: missing ')'")
                    self._unexpected("',' or ')'")

            if name == "abs":
                if len(args) != 1:
                    raise CalcError(
                        "wrong number of arguments for abs: expected 1, got %d"
                        % len(args)
                    )
            elif len(args) < 1:
                raise CalcError(
                    "wrong number of arguments for %s: expected at least 1, got 0"
                    % name
                )

            return _apply_function(name, args)
        finally:
            self.paren_depth -= 1


def _require_number(value, description):
    if isinstance(value, bool):
        # bool is an int subclass; arithmetic with it is well-defined and
        # Python-compatible, so let it through.
        return value
    if isinstance(value, (int, float)):
        return value
    raise CalcError("%s is not a number" % (description,))


def _apply_unary(op, value):
    value = _require_number(value, "operand")
    try:
        if op == "+":
            return +value
        return -value
    except (TypeError, ValueError, OverflowError) as exc:
        raise CalcError("invalid operand for unary %s: %s" % (op, exc)) from None


def _apply_binary(op, left, right):
    left = _require_number(left, "left operand")
    right = _require_number(right, "right operand")
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
        raise CalcError("unexpected operator %r" % (op,))
    except ZeroDivisionError:
        if op == "%":
            raise CalcError("modulo by zero") from None
        if op == "/" or op == "//":
            raise CalcError("division by zero") from None
        # This can occur for zero raised to a negative power.
        raise CalcError("division by zero: zero cannot be raised to a negative power") from None
    except (TypeError, ValueError, OverflowError) as exc:
        raise CalcError("invalid operands for %s: %s" % (op, exc)) from None


def _apply_function(name, args):
    for arg in args:
        _require_number(arg, "function argument")
    try:
        if name == "abs":
            return abs(args[0])
        if name == "min":
            return min(args)
        if name == "max":
            return max(args)
        raise CalcError("unknown function %r" % (name,))
    except (TypeError, ValueError, OverflowError) as exc:
        raise CalcError("invalid arguments for %s: %s" % (name, exc)) from None


def evaluate(expr, env=None):
    """Evaluate the arithmetic expression *expr*.

    ``env`` optionally maps variable names to numeric values.  Invalid
    expressions raise :class:`CalcError`, a subclass of :class:`ValueError`.
    """
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")

    tokens = _tokenize(expr)
    parser = _Parser(tokens, env)
    return _require_number(parser.parse(), "expression result")
