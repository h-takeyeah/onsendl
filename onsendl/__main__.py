import argparse
import gzip
import m3u8
import os
import platform
import re
import subprocess
import sys
import urllib.request
import urllib.parse
from pathlib import Path
import m3u8.httpclient as m3u8http

from onsendl.html_parser import OnsenHTMLParser

PSYSTEM = platform.system().lower()
PWD = Path(".").resolve()
INVALID_CHARS_DICT = str.maketrans(
    {
        # fmt: off
        k: "_" for k in [
            " ", "\u3000", "\\", "/", ":", ";", "*",
            "?", '"', "<", ">", "|", "%", "\u2019", "!",
        ]
    }
)


class OnsenHTTPClient(m3u8http.DefaultHTTPClient):
    def download(
        self,
        uri,
        timeout=None,
        headers={},
        verify_ssl=True,
    ):
        proxy_handler = urllib.request.ProxyHandler(self.proxies)
        https_handler = m3u8http.HTTPSHandler(verify_ssl=verify_ssl)
        opener = urllib.request.build_opener(proxy_handler, https_handler)
        opener.addheaders = headers.items()
        resource = opener.open(uri, timeout=timeout)
        base_uri = m3u8http._parsed_url(resource.geturl())
        bytes_content = resource.read()
        # assert isinstance(bytes_content, bytes)
        try:
            bytes_content = gzip.decompress(bytes_content)
        except gzip.BadGzipFile:
            pass
        content = bytes_content.decode(
            resource.headers.get_content_charset(failobj="utf-8")
        )
        return content, base_uri


def custom_load(uri):
    return m3u8.load(
        uri=uri,
        headers={"Referer": "https://www.onsen.ag/"},
        http_client=OnsenHTTPClient(),
    )


def save_js_str(uri):
    res_content, _ = OnsenHTTPClient().download(uri)
    p = OnsenHTMLParser()
    return p.feed(res_content)


def download_chunks(uri, title):
    filepath = PWD.joinpath(title + ".aac")
    completed = subprocess.run(
        # fmt: off
        args=[
            "ffmpeg", "-n", "-stats", "-loglevel", "warning",
            "-headers", "Referer: https://www.onsen.ag/\r\n",
            "-i", uri, "-c", "copy", filepath,
        ]
    )
    try:
        completed.check_returncode()
    except subprocess.CalledProcessError:
        return None
    else:
        return filepath


def main():
    rc = 0
    parser = argparse.ArgumentParser()
    parser.add_argument("program_url", type=str, help="url of onsen.ag radio program")
    # parser.add_argument("all", action="store_true", default=True, help="download all available epsiodes")
    args = parser.parse_args()
    program_url = args.program_url
    # dl_all = args.all

    def is_onsen_url(u: str):
        u = u.rstrip("/")
        p_result = urllib.parse.urlparse(u)
        path = p_result.path.strip("/").split("/")
        return (
            p_result.scheme in ("http", "https")
            and len(path) == 2
            and path[0] == "program"
        )

    if not is_onsen_url(program_url):
        raise ValueError("onsen url format is https://www.onsen.ag/program/<title>")

    filepath = save_js_str(program_url)

    ptn = re.compile(
        r"^https.+{title}.+\.m3u8$".format(title=program_url.rstrip("/").split("/")[-1])
    )
    episodes = []
    with open(filepath, encoding="utf8") as f:
        for token in f.read().split(","):
            token = token.replace("\n", "").strip('"')
            token = token.encode().decode("unicode-escape")
            if ptn.match(token):
                episodes.append(token)
    os.remove(filepath)

    for pl_uri in episodes:
        variant_m3u8 = custom_load(pl_uri)
        # assert variant_m3u8.is_variant
        best_chunk = max(
            variant_m3u8.playlists, key=lambda pl: pl.stream_info.bandwidth
        )

        # choice best quality chunklist
        chunklist_uri = (
            best_chunk.absolute_uri if best_chunk.absolute_uri is not None else ""
        )
        if m3u8.is_url(chunklist_uri):
            ep_unique_id = (
                urllib.parse.urlparse(chunklist_uri).path.strip("/").split("/")[-2]
            )
            ep_unique_id = ep_unique_id.translate(INVALID_CHARS_DICT)
            ep_unique_id = ep_unique_id.removesuffix(".mp4")
            print(f"start downloading {ep_unique_id}")
            saved_at = download_chunks(chunklist_uri, ep_unique_id)
            if saved_at is None:
                rc = 1
                print("download failed")
            else:
                print(f"saved at {saved_at}")

    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
