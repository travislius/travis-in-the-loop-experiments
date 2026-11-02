"""Arithmetic expression evaluator (see SPEC.md).

The module exposes :func:`evaluate`, which parses and evaluates a small
arithmetic language with numbers, variables, parentheses, the operators
`+ - * / // % **` and the functions `min`, `max` and `abs`.

No Python `eval`/`exec`/`compile` (nor the `ast` module) is used: the
expression is tokenised and parsed by hand.
"""


class CalcError(ValueError):
    """Raised for any invalid expression or evaluation error."""


_NAME_START = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
)
_NAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"
)


def _is_digit(ch):
    return "0" <= ch <= "9"


def _tokenize(text):
    """Turn *text* into a list of (kind, value) tokens ending with ("end", None)."""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if _is_digit(ch) or (ch == "." and i + 1 < n and _is_digit(text[i + 1])):
            j = i
            while j < n and _is_digit(text[j]):
                j += 1
            is_float = False
            if j < n and text[j] == ".":
                is_float = True
                j += 1
                while j < n and _is_digit(text[j]):
                    j += 1
            literal = text[i:j]
            tokens.append(("number", float(literal) if is_float else int(literal)))
            i = j
            continue
        if ch in _NAME_START:
            j = i + 1
            while j < n and text[j] in _NAME_CHARS:
                j += 1
            tokens.append(("name", text[i:j]))
            i = j
            continue
        pair = text[i:i + 2]
        if pair == "**" or pair == "//":
            tokens.append(("op", pair))
            i += 2
            continue
        if ch in "+-*/%(),":
            tokens.append(("op", ch))
            i += 1
            continue
        raise CalcError("unexpected character: %r" % (ch,))
    tokens.append(("end", None))
    return tokens


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

    def at_op(self, *ops):
        kind, value = self.peek()
        return kind == "op" and value in ops

    def eat_op(self, *ops):
        if self.at_op(*ops):
            return self.advance()[1]
        return None

    # -- grammar ---------------------------------------------------------
    def parse(self):
        value = self.parse_additive()
        kind, token = self.peek()
        if kind != "end":
            raise CalcError("unexpected token: %r" % (token,))
        return value

    def parse_additive(self):
        value = self.parse_multiplicative()
        while True:
            op = self.eat_op("+", "-")
            if op is None:
                return value
            value = _binary(op, value, self.parse_multiplicative())

    def parse_multiplicative(self):
        value = self.parse_unary()
        while True:
            op = self.eat_op("*", "/", "//", "%")
            if op is None:
                return value
            value = _binary(op, value, self.parse_unary())

    def parse_unary(self):
        if self.at_op("+", "-"):
            op = self.advance()[1]
            operand = self.parse_unary()
            return operand if op == "+" else -operand
        return self.parse_power()

    def parse_power(self):
        base = self.parse_atom()
        if self.eat_op("**") is not None:
            exponent = self.parse_unary()
            return _binary("**", base, exponent)
        return base

    def parse_atom(self):
        kind, value = self.peek()
        if kind == "number":
            self.advance()
            return value
        if kind == "name":
            self.advance()
            if self.at_op("("):
                return self.parse_call(value)
            return self._variable(value)
        if kind == "op" and value == "(":
            self.advance()
            inner = self.parse_additive()
            if self.eat_op(")") is None:
                raise CalcError("unbalanced parentheses: expected ')'")
            return inner
        if kind == "end":
            raise CalcError("unexpected end of expression")
        raise CalcError("unexpected token: %r" % (value,))

    def _variable(self, name):
        try:
            return self.env[name]
        except KeyError:
            raise CalcError("unknown variable: %s" % (name,)) from None

    def parse_call(self, name):
        self.eat_op("(")
        args = []
        if self.at_op(")"):
            self.advance()
        else:
            while True:
                args.append(self.parse_additive())
                if self.eat_op(",") is not None:
                    continue
                if self.eat_op(")") is not None:
                    break
                raise CalcError(
                    "unbalanced parentheses: expected ')' in call to %s" % (name,)
                )
        return _call(name, args)


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
    except OverflowError:
        raise CalcError("numeric overflow") from None
    raise CalcError("unexpected operator: %r" % (op,))


def _call(name, args):
    if name == "abs":
        if len(args) != 1:
            raise CalcError(
                "abs() takes exactly 1 argument (%d given)" % (len(args),)
            )
        return abs(args[0])
    if name == "min":
        if not args:
            raise CalcError("min() requires at least 1 argument")
        return min(args)
    if name == "max":
        if not args:
            raise CalcError("max() requires at least 1 argument")
        return max(args)
    raise CalcError("unknown function: %s" % (name,))


def evaluate(expr, env=None):
    """Evaluate *expr* and return an int or float.

    *env* is an optional mapping of variable names to values.
    Any problem raises :class:`CalcError`.
    """
    if not isinstance(expr, str):
        raise CalcError("expression must be a string")
    tokens = _tokenize(expr)
    if len(tokens) == 1:  # only the "end" token: empty or blank input
        raise CalcError("empty expression")
    parser = _Parser(tokens, {} if env is None else env)
    result = parser.parse()
    if isinstance(result, complex):
        raise CalcError("result is not a real number")
    return result
