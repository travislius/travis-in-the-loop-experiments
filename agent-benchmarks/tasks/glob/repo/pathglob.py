import fnmatch
def match(pattern, path):
    return fnmatch.fnmatch(path, pattern)
