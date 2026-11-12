from textutil import slugify
def test_basic(): assert slugify("  Hello,   World!  ") == "hello-world"
def test_accents(): assert slugify("Crème Brûlée") == "creme-brulee"
def test_numbers(): assert slugify("Top 10 Tips") == "top-10-tips"
def test_empty(): assert slugify("!!!") == ""
def test_dashes(): assert slugify("a--b") == "a-b"
