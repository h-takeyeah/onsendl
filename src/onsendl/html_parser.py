from html.parser import HTMLParser
from tempfile import NamedTemporaryFile


class OnsenHTMLParser(HTMLParser):
    def __init__(self, *, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.inside_script_tag = False
        self.f = NamedTemporaryFile(mode="w", prefix="onsenhtmlparserout--", delete=False)

    def handle_starttag(self, tag, _): # pyright: ignore[reportIncompatibleMethodOverride]
        if tag == "script":
            self.inside_script_tag = True

    def handle_data(self, data: str):
        if self.inside_script_tag and data[:20].lower().startswith(
            "window.__nuxt__"
        ):
            self.f.write(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.inside_script_tag = False

    def feed(self, data):
        try:
            super().feed(data)
        finally:
            self.f.close()

    @property
    def saved_filepath(self):
        return self.f.name
