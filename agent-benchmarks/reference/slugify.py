import re, unicodedata
def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")
