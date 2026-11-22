"""Build head markup and crawler files for a static site at any deployment prefix."""

from html import escape
import json
from pathlib import Path, PurePosixPath
import posixpath
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BRAND = "DH Construction"


def site_root(base_url):
    base = urlsplit(base_url)
    if base.scheme not in {"http", "https"} or not base.hostname or base.query or base.fragment:
        raise ValueError("Expected an absolute HTTP(S) site root without a query or fragment")
    return base_url.rstrip("/") + "/"


def page_url(page, base_url):
    path = PurePosixPath(page)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".html":
        raise ValueError("Expected a site-relative HTML path")
    suffix = "" if str(path) == "index.html" else quote(str(path))
    return site_root(base_url) + suffix


def head(page, title, description, base_url, preview=True):
    """Return escaped, per-page head contents. Assets load from the local site."""
    root = site_root(base_url)
    canonical = page_url(page, root)
    icon = posixpath.relpath("assets/brand/favicon.png", str(PurePosixPath(page).parent))
    share_image = root + "assets/brand/social.jpg"
    text = escape(description, quote=True)
    title = escape(title, quote=True)
    url = escape(canonical, quote=True)
    share = escape(share_image, quote=True)
    directives = "noindex, follow" if preview else "index, follow"
    contact = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))["contact"]
    organization = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": root + "#organization",
        "name": BRAND,
        "url": root,
        "logo": root + "assets/brand/logo.webp",
        "telephone": contact["phone"],
        "email": contact["email"],
    }
    data = json.dumps(organization, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{text}">
<meta name="robots" content="{directives}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/png" sizes="64x64" href="{escape(icon, quote=True)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="en_IN">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{text}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{share}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{BRAND} logo">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{text}">
<meta name="twitter:image" content="{share}">
<meta name="twitter:image:alt" content="{BRAND} logo">
<script type="application/ld+json">{data}</script>'''


def discovery_files(pages, base_url, preview=True):
    """Return complete UTF-8 sitemap and robots contents without writing files."""
    root = site_root(base_url)
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for page in pages:
        loc = ET.SubElement(ET.SubElement(sitemap, "url"), "loc")
        loc.text = page_url(page, root)
    ET.indent(sitemap, space="  ")
    xml = ET.tostring(sitemap, encoding="unicode", xml_declaration=True) + "\n"
    # Let crawlers read the preview pages' noindex directive. A project Pages
    # subdirectory cannot override the robots.txt at its host's root.
    robots = "User-agent: *\nAllow: /\n"
    if not preview:
        robots += f"\nSitemap: {root}sitemap.xml\n"
    return {"robots.txt": robots, "sitemap.xml": xml}
