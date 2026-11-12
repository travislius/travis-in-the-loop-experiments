import pytest
from pathglob import match as m
@pytest.mark.parametrize("p,s,ok",[
 ("*.py","a.py",True),("*.py","src/a.py",False),("src/*.py","src/a.py",True),
 ("a/**/b","a/b",True),("a/**/b","a/x/y/b",True),("a/**/b","a/xb",False),
 ("a/**","a/x/y",True),("a/**","a",False),("**/b","b",True),("**/b","x/y/b",True),("**/b","xb",False),
 ("?.txt","a.txt",True),("?.txt","/.txt",False),("?.txt","ab.txt",False),
 ("[a-c]x","bx",True),("[!a-c]x","bx",False),("[!a-c]x","dx",True),("[a-c]x","/x",False),
 (r"\*.md","*.md",True),(r"\*.md","a.md",False),("A*","abc",False),
 ("docs/**/*.md","docs/x/y/z.md",True),("docs/**/*.md","docs/z.md",True),("docs/**/*.md","docs/z.mdx",False),
])
def test_cases(p,s,ok): assert m(p,s)==ok
