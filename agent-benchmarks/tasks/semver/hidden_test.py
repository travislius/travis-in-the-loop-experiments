from semver import compare as c
CHAIN=["1.0.0-alpha","1.0.0-alpha.1","1.0.0-alpha.beta","1.0.0-beta","1.0.0-beta.2","1.0.0-beta.11","1.0.0-rc.1","1.0.0"]
def test_chain():
    for i in range(len(CHAIN)-1):
        assert c(CHAIN[i],CHAIN[i+1])==-1 and c(CHAIN[i+1],CHAIN[i])==1
def test_build(): assert c("1.0.0+build.5","1.0.0")==0
def test_minor(): assert c("1.10.0","1.9.0")==1
def test_eq(): assert c("2.3.4","2.3.4")==0
