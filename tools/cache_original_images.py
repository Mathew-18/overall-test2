"""Cache the original public images in an extracted review copy, preserving each source URL."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from html import unescape
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "assets" / "original-media"
MAX_BYTES = 24 * 1024 * 1024
ALLOWED_HOSTS = {"images.unsplash.com", "picsum.photos"}
IMAGE = re.compile(r'<img\b[^>]*>', re.I)
SOURCE = re.compile(r'\ssrc="([^"]+)"', re.I)


def image_ext(raw):
    if raw.startswith(b"\xff\xd8\xff"): return ".jpg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"): return ".png"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP": return ".webp"
    if raw.startswith((b"GIF87a", b"GIF89a")): return ".gif"
    raise ValueError("Response is not a recognized image")


def cache(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
        raise ValueError("Unexpected source host")
    key = hashlib.sha256(url.encode()).hexdigest()
    for path in STORE.glob(key + ".*"):
        if image_ext(path.read_bytes()) == path.suffix:
            return path
    req = Request(url, headers={"Accept": "image/jpeg,image/png,image/webp,image/gif"})
    with urlopen(req, timeout=30) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Image exceeds size limit")
    path = STORE / (key + image_ext(raw))
    with NamedTemporaryFile(dir=STORE, delete=False) as tmp:
        tmp.write(raw)
    os.replace(tmp.name, path)
    return path


def cache_one(url):
    try:
        return url, cache(url), None
    except (OSError, ValueError) as exc:
        return url, None, str(exc)


def add_local_sources(page, local):
    def replace(match):
        tag = match.group()
        src = SOURCE.search(tag)
        url = unescape(src.group(1)) if src else None
        if url not in local or " srcset=" in tag:
            return tag
        relative = Path(os.path.relpath(local[url], page.parent)).as_posix()
        return tag[:-1] + f' srcset="{relative}">'
    original = page.read_text(encoding="utf-8")
    updated = IMAGE.sub(replace, original)
    if original != updated:
        page.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true",
                        help="Download the exact referenced image bytes and use them in this copy")
    args = parser.parse_args()
    inventory = json.loads((ROOT / "review/original-inventory.json").read_text(encoding="utf-8"))
    urls = sorted({url for p in inventory.values() for section in p["sections"] for url in section["images"]})
    if not args.download:
        print(f"{len(urls)} original URLs. Use --download in an extracted test copy to cache them.")
        return 0
    STORE.mkdir(exist_ok=True)
    local = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for url, path, error in pool.map(cache_one, urls):
            if error:
                print(f"Unavailable: {url} ({error})")
            else:
                local[url] = path
    for page in inventory:
        add_local_sources(ROOT / page, local)
    print(f"Cached {len(local)} of {len(urls)} original images. Original src addresses are preserved.")
    return int(len(local) != len(urls))


if __name__ == "__main__":
    raise SystemExit(main())
