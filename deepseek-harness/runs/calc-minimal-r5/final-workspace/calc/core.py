"""A small arithmetic expression evaluator."""


class CalcError(ValueError):
    """Raised for invalid expressions or expression evaluation errors."""


_NUMBER = "NUMBER"
_IDENT = "IDENT"
_OP = "OP"
_LPAREN = "LPAREN"
_RPAREN = "RPAREN"
_COMMA = "COMMA"
_EOF = "EOF"


class _Token:
    __slots__ = ("kind", "value", "pos")

    def __init__(self, kind, value, pos):
        self.kind = kind
        self.value = value
        self.pos = pos


def _tokenize(expr):
    """Turn *expr* into a list of tokens, ending with an EOF token."""
    tokens = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        if ch.isdigit() or (ch == "." and i + 1 < n and expr[i + 1].isdigit()):
            start = i
            if ch == ".":
                i += 1
                while i < n and expr[i].isdigit():
                    i += 1
                tokens.append(_Token(_NUMBER, float(expr[start:i]), start))
            else:
                while i < n and expr[i].isdigit():
                    i += 1
                if i < n and expr[i] == ".":
                    i += 1
                    while i < n and expr[i].isdigit():
                        i += 1
                    tokens.append(
                        _Token(_NUMBER, float(expr[start:i]), start)
                    )
                else:
                    tokens.append(
                        _Token(_NUMBER, int(expr[start:i]), start)
                    )
            continue

        if ch.isalpha() or ch == "_":
            start = i
            i += 1
            while i < n and (expr[i].isalnum() or expr[i] == "_"):
                i += 1
            tokens.append(_Token(_IDENT, expr[start:i], start))
            continue

        if ch == "/" and i + 1 < n and expr[i + 1] == "/":
            tokens.append(_Token(_OP, "//", i))
            i += 2
            continue
        if ch == "*" and i + 1 < n and expr[i + 1] == "*":
            tokens.append(_Token(_OP, "**", i))
            i += 2
            continue
