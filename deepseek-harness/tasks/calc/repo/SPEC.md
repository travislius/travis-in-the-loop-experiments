
# calc — specification
Implement `evaluate(expr: str, env: dict | None = None) -> int | float` in `calc/core.py`.

1. Numbers: integers (`42`) and decimals (`3.5`, `.5`). Integer-only arithmetic stays `int`.
2. Operators, lowest to highest precedence: `+ -`, then `* / // %`, then unary `-`/`+`, then `**`.
   - `**` is right-associative and binds tighter than unary minus: `-2**2 == -4`, `2**-1 == 0.5`, `2**3**2 == 512`.
   - `/` is true division (always float). `//` and `%` follow Python semantics.
3. Parentheses. Whitespace is insignificant.
4. Variables: identifiers `[A-Za-z_][A-Za-z0-9_]*` looked up in `env`.
5. Functions: `min(a, b, ...)`, `max(a, b, ...)` (1+ args), `abs(x)`. Nested calls allowed.
6. Errors: raise `calc.core.CalcError` (subclass of ValueError) with a message for:
   unknown variable, unknown function, wrong arg count for abs, division/modulo by zero,
   unbalanced parentheses, empty input, any unexpected token.
7. Do NOT use Python `eval`, `exec`, `compile` or the `ast` module.
