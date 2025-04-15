import argparse
import gzip
import m3u8
import os
import platform
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

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


def custom_load(uri):
    return m3u8.load(
        uri=uri,
        headers={"Referer": "https://www.onsen.ag/"},
    )


def save_js_str(uri):
    with urllib.request.urlopen(uri) as res:
        if res.info().get("Content-Encoding") == "gzip":
            res_content = gzip.decompress(res.read()).decode(res.headers.get_content_charset(failobj="utf-8"))
        else:
            res_content = res.read().decode(res.headers.get_content_charset(failobj="utf-8"))
    p = OnsenHTMLParser()
    p.feed(res_content)
    return p.saved_filepath


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
            variant_m3u8.playlists, key=lambda pl: pl.stream_info.bandwidth or 0
        )

        # choice best quality chunklist
        chunklist_uri = (
            best_chunk.absolute_uri if best_chunk.absolute_uri is not None else ""
        )
        # assume given uri is uri
        if urllib.parse.urlsplit(chunklist_uri).scheme:
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
