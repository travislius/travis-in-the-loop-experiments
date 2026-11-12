# Bug report

`compare(a, b)` for semantic versions is wrong for pre-releases and build metadata. It must follow SemVer 2.0.0 precedence: return -1, 0 or 1. Examples: 1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta < 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0; build metadata is ignored (1.0.0+build.5 == 1.0.0); 1.10.0 > 1.9.0. Fix it.
