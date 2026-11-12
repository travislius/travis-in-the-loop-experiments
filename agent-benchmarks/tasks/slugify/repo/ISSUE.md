# Bug report

`slugify()` produces bad slugs: `slugify('  Hello,   World!  ')` returns `'-hello-world-'` instead of `'hello-world'`, and accented letters like `'Crème Brûlée'` are dropped instead of becoming `'creme-brulee'`. Fix it.
