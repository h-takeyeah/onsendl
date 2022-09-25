import os
from html.parser import HTMLParser
from tempfile import mkstemp


class OnsenHTMLParser(HTMLParser):
    def __init__(self, *, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.inside_script_tag = False
        self.fp, self.fpath = mkstemp()

    def handle_starttag(self, tag, _):
        if tag == "script":
            self.inside_script_tag = True

    def handle_data(self, data: str):
        if self.inside_script_tag == True and data[:20].lower().startswith(
            "window.__nuxt__"
        ):
            self.writeline(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.inside_script_tag = True

    def feed(self, data):
        try:
            super().feed(data)
        finally:
            os.close(self.fp)
        return self.fpath

    def writeline(self, data):
        with open(self.fpath, "a", encoding="utf8") as f:
            f.write(data)
