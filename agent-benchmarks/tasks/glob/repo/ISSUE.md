# Bug report

`match(pattern, path)` decides whether a slash-separated relative path matches a glob pattern, like .gitignore-style tooling. It currently uses fnmatch, which is wrong. Required semantics:
- `?` matches exactly one character except `/`.
- `*` matches any run of characters (including empty) except `/`.
- `**` as a whole path segment matches zero or more whole segments: `a/**/b` matches `a/b`, `a/x/b`, `a/x/y/b`; a trailing `a/**` matches everything under `a/` (but not `a` itself); a leading `**/b` matches `b` and `x/y/b`.
- `[abc]`, ranges `[a-z]`, and negation `[!a-z]` match one character (never `/`).
- A backslash escapes the next character: `\*` matches a literal `*`.
- Matching is case-sensitive and must match the whole path.
Use only the standard library.
