"""Source parity tests use lxml only during development."""
from collections import Counter
import json
from pathlib import Path
import re
import unittest
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = json.loads((ROOT / "review/original-inventory.json").read_text(encoding="utf-8"))
SITE = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))


def normalized(text):
    return " ".join(text.split())


class OriginalPages(unittest.TestCase):
    def test_original_content_and_images_in_order(self):
        for path, record in ORIGINAL.items():
            with self.subTest(path=path):
                doc = html.parse(str(ROOT / path), html.HTMLParser(encoding="utf-8"))
                sections = doc.xpath("//main/section")
                self.assertEqual(len(sections), len(record["sections"]))
                for expected, section in zip(record["sections"], sections):
                    self.assertEqual(section.get("id"), expected["id"])
                    self.assertEqual(section.get("class"), expected["classes"])
                    self.assertEqual(section.xpath(".//img/@src"), expected["images"])
                    self.assertEqual(section.xpath(".//*[@data-aos]/@data-aos"), expected["reveals"])
                    headings = [normalized(x.text_content()) for x in section.xpath(".//h1|.//h2|.//h3|.//h4|.//h5|.//h6")]
                    self.assertEqual(headings, expected["headings"])
                    actual = iter(normalized(x) for x in section.xpath(".//text()[not(ancestor::script or ancestor::style)]") if x.strip())
                    for text in expected["texts"]:
                        self.assertTrue(any(candidate == text for candidate in actual), f"{path} #{section.get('id')}: lost or moved {text}")
                self.assertEqual(len(doc.xpath("//main")), 1)
                self.assertEqual(len(doc.xpath("//main//h1")), 1)
                self.assertEqual(len(doc.xpath("//head/title")), 1)
                self.assertEqual(len(doc.xpath('//link[@rel="canonical"]')), 1)
                self.assertIn("noindex", doc.xpath('//meta[@name="robots"]/@content')[0])
                self.assertEqual(len(doc.xpath('//*[@data-whatsapp][contains(@class,"dh-guide")]')), 1)
                self.assertTrue(all(url == SITE["contact"]["whatsapp"] for url in doc.xpath('//*[@data-whatsapp]/@data-whatsapp')))
                styles = " ".join(doc.xpath("//style/text()")) + (ROOT/"assets/css/enhancements.css").read_text()
                for key in record["keyframes"]:
                    self.assertRegex(styles, r"@keyframes\s+" + re.escape(key) + r"\b")
                self.assertEqual(doc.xpath("//main//canvas/@id"), record["canvases"])
                self.assertEqual(doc.xpath('//*[@data-target]/@data-target|//*[@data-count]/@data-count'), record["counters"])
                self.assertEqual([(e.getparent().get("class"),e.get("alt")) for e in doc.xpath("//main//img")], [tuple(item) for item in record["photo_placements"]])

    def test_all_form_controls_are_labelled(self):
        count=0
        for path in ORIGINAL:
            doc=html.parse(str(ROOT/path),html.HTMLParser(encoding="utf-8"))
            forms=doc.xpath("//main//form")
            count+=len(forms)
            for form in forms:
                for field in form.xpath('.//*[@data-label]'):
                    self.assertTrue(form.xpath('.//label[@for=$key]',key=field.get("id")))
        self.assertEqual(count,8)
