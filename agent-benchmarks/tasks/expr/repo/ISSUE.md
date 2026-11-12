# Bug report

`evaluate(s)` should evaluate arithmetic expressions given as strings and return a number, but it gives wrong answers. Required behaviour:
- Numbers: integers and decimals (`3`, `0.5`, `.5`). Operators `+ - * / ^` and parentheses; whitespace anywhere.
- Precedence: `^` highest, then unary minus, then `* /`, then `+ -`. So `-2^2 == -4` and `2*-3 == -6`.
- `^` is RIGHT-associative: `2^3^2 == 512`. `+ - * /` are left-associative: `8/4/2 == 1`, `10-4-3 == 3`.
- Division is true division. Division by zero raises ZeroDivisionError.
- Malformed input (`2+`, `(1+2`, `1 2`, `` , `2**3`, `abc`) raises ValueError.
Do NOT use eval/exec/ast; write a real parser.
