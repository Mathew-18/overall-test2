"""Run with python3 -m unittest discover -s tests."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import unittest
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "data/site.json").read_text())


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.tags = Counter()
        self.ids = set()
        self.references = []
        self.header_links = []
        self.footer_links = []
        self.nav_controls = []
        self.region = None
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags[tag] += 1
        if tag in ("header", "footer"):
            self.region = tag
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.references.append(attrs[key])
        if self.region == "header" and "data-dh-nav" in attrs:
            self.nav_controls.append((tag, attrs))
        if tag == "a" and self.region:
            getattr(self, self.region + "_links").append(attrs)

    def handle_endtag(self, tag):
        if tag == self.region:
            self.region = None

    def target(self, ref):
        path = unquote(urlsplit(ref).path)
        return (self.path.parent / path).resolve() if path else self.path


class SharedSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {ROOT / path: Page(ROOT / path) for path in SITE["pages"]}

    def test_catalog_and_landmarks(self):
        actual = set(ROOT.glob("*.html")) | {p for folder in ("about", "Projects", "services", "Contact")
                                             for p in (ROOT / folder).glob("*.html")}
        self.assertEqual(set(self.pages), actual)
        self.assertEqual(len(actual), 11)
        for page in self.pages.values():
            with self.subTest(page=page.path.name):
                self.assertEqual((page.tags["header"], page.tags["footer"]), (1, 1))

    def test_navigation_and_current_page(self):
        routes = [ROOT / path for path in SITE["navigation"].values()]
        services = [ROOT / path for path in SITE["services"].values()]
        self.assertEqual(len(services), 6)
        for page in self.pages.values():
            with self.subTest(page=page.path.name):
                current = [a for a in page.header_links if a.get("aria-current") == "page"]
                self.assertEqual([page.target(a["href"]) for a in current], [page.path])
                menu = [page.target(a["href"]) for a in page.header_links if not urlsplit(a["href"]).scheme]
                self.assertEqual(menu, [routes[0], *routes[:3], *services, *routes[3:]])
                self.assertEqual([a["data-dh-nav"] for _, a in page.nav_controls],
                                 [label.lower() for label in SITE["navigation"]])
                active = [a["data-dh-nav"] for _, a in page.nav_controls if "data-dh-active" in a]
                expected = "services" if page.path in services else next(
                    label.lower() for label, path in SITE["navigation"].items() if ROOT / path == page.path
                )
                self.assertEqual(active, [expected])
                tag, disclosure = page.nav_controls[2]
                self.assertEqual(tag, "summary")
                self.assertIn(disclosure.get("aria-controls"), page.ids)
                footer = {page.target(a["href"]) for a in page.footer_links}
                self.assertTrue(set(routes + services) <= footer)

    def test_local_assets_and_fragments(self):
        for page in self.pages.values():
            for ref in page.references:
                url = urlsplit(ref)
                if url.scheme or url.netloc:
                    continue
                with self.subTest(page=page.path.name, ref=ref):
                    self.assertNotEqual(ref, "#")
                    target = page.target(ref)
                    self.assertTrue(target.is_file())
                    if url.fragment:
                        self.assertIn(unquote(url.fragment), self.pages[target].ids)

    def test_generated_files_are_current(self):
        subprocess.run([sys.executable, ROOT / "tools/render_shared.py", "--check"], check=True)


if __name__ == "__main__":
    unittest.main()
