"""Exercise the built static pages with synthetic enquiries. No external requests.

Run with Python Playwright and Chromium: python3 tests/enquiries_browser.py
Optionally pass --base http://127.0.0.1:PORT for an already-running instance.
"""

import argparse
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
from threading import Thread
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
WHATSAPP = json.loads((ROOT / "data/site.json").read_text())["contact"]["whatsapp"]
PAGES = [
    "index.html", "Contact/contact.html", "services/Buliding_Construction.html",
    "services/Building_rennovation.html", "services/interior_designs.html",
    "services/Infrastructure.html", "services/Glass.html", "services/falseceling.html",
]
VALUES = {
    "tel": "+91 90000 00000", "number": "125.5", "email": "reader@example.invalid",
    "text": "QA & + / தமிழ்", "textarea": "Synthetic request & + / தமிழ்",
}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def serve(base):
    if base:
        if urlsplit(base).hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("--base must be local")
        yield base.rstrip("/")
        return
    with ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=ROOT)) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            worker.join()


def isolated_page(browser, base, path, viewport, reduce=False):
    page = browser.new_page(viewport=viewport, reduced_motion="reduce" if reduce else "no-preference")
    page.set_default_timeout(5000)
    page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(base + "/") else route.abort())
    page.add_init_script("""window.drafts = [];
        window.open = (url, target, features) => {
          window.drafts.push({url, target, features});
          if (window.simulateRestrictedPopup) throw new DOMException("Popup blocked", "SecurityError");
          return null;
        };""")
    page.goto(base + "/" + path, wait_until="domcontentloaded")
    return page


def draft(page, expected_count):
    records = page.evaluate("window.drafts")
    assert len(records) == expected_count, records
    record = records[-1]
    assert record["target"] == "_blank" and "noopener" in record["features"]
    url = record["url"]
    assert url.split("?")[0] == WHATSAPP
    return url, parse_qs(urlsplit(url).query)["text"][0]


def verify_form(page):
    form = page.locator(".dh-enquiry")
    expect(form).to_have_count(1)
    button = form.locator('[type="submit"]')
    button.click()
    assert form.locator(":invalid").count() > 0
    controls = form.locator("[data-label]").all()
    for control in controls:
        kind = control.evaluate("el => el.type")
        assert control.evaluate("el => el.labels.length > 0")
        if kind == "select-one":
            control.select_option(index=1)
        else:
            control.fill(VALUES[kind])
    button.click()
    assert page.evaluate("window.drafts.length") == 0
    form.get_by_role("checkbox").check()
    telephone = form.locator('input[type="tel"]')
    telephone.fill("12345wrong")
    button.click()
    assert page.evaluate("window.drafts.length") == 0
    telephone.fill(VALUES["tel"])
    email = form.locator('input[type="email"]')
    if email.count():
        email.fill("invalid")
        button.click()
        assert page.evaluate("window.drafts.length") == 0
        email.fill("")
    # Browsers may return null even for a successful noopener popup. Every visitor
    # also gets an ordinary link to the same populated draft, including on SecurityError.
    page.evaluate("window.simulateRestrictedPopup = true")
    button.click()
    form.evaluate("f => f.requestSubmit()")
    url, text = draft(page, 1)
    for control in controls:
        if control.input_value():
            assert f"{control.get_attribute('data-label')}: {control.input_value()}" in text
    expect(button).to_be_disabled()
    expect(form.get_by_role("status")).to_contain_text("If WhatsApp did not open")
    expect(form.get_by_role("status").get_by_role("link")).to_have_attribute("href", url)
    return len(controls)


def verify_guide(page):
    guide = page.locator(".dh-guide")
    launch = guide.get_by_role("button", name="Open project assistant")
    panel = guide.get_by_role("dialog")
    guide.get_by_role("button", name="Dismiss welcome").click()
    expect(launch).to_be_focused()
    launch.press("Enter")
    field = guide.locator("#dh-guide-answer")
    expect(field).to_be_focused()
    go = guide.get_by_role("button", name="Continue", exact=True)
    go.click()
    assert field.evaluate("el => !el.validity.valid")
    field.fill("Plumbing")
    go.press("Enter")
    field.fill("Commercial")
    guide.get_by_role("button", name="Back", exact=True).press("Enter")
    expect(field).to_have_value("Plumbing")
    go.press("Enter")
    expect(field).to_have_value("Commercial")
    go.press("Enter")
    field.fill("Locality & station")
    guide.get_by_role("button", name="Minimize assistant").click()
    expect(panel).to_be_hidden()
    expect(launch).to_be_focused()
    launch.press("Enter")
    expect(field).to_have_value("Locality & station")
    field.press("Enter")
    field.fill("Sample + தமிழ்")
    go.press("Enter")
    guide.get_by_role("button", name="Skip budget").click()
    field.fill("Within three months")
    go.press("Enter")
    field.fill("QA & test")
    field.press("Enter")
    field.fill("12")
    field.press("Enter")
    assert field.evaluate("el => !el.validity.valid")
    field.fill(VALUES["tel"])
    field.press("Enter")
    expect(guide.get_by_role("heading", name="Review your enquiry")).to_be_focused()
    send = guide.get_by_role("button", name="Submit via WhatsApp")
    expect(send).to_be_disabled()
    guide.get_by_role("checkbox").check()
    guide.get_by_role("button", name="Edit location").click()
    field.fill("Updated & area")
    field.press("Enter")
    expect(send).to_be_disabled()
    guide.get_by_role("checkbox").check()
    send.press("Enter")
    send.evaluate("b => b.click()")
    expect(send).to_be_disabled()
    url, message = draft(page, 1)
    for answer in ["Plumbing", "Commercial", "Updated & area", "Sample + தமிழ்", "Within three months", "QA & test", VALUES["tel"]]:
        assert answer in message
    expect(guide.get_by_role("status").get_by_role("link")).to_have_attribute("href", url)
    rect = panel.bounding_box()
    assert 0 <= rect["x"] and rect["x"] + rect["width"] <= page.viewport_size["width"] + 1
    assert 0 <= rect["y"] and rect["y"] + rect["height"] <= page.viewport_size["height"] + 1
    guide.get_by_role("button", name="Close and clear enquiry").click()
    expect(panel).to_be_hidden()
    launch.press("Enter")
    expect(field).to_have_value("")
    field.press("Escape")
    expect(panel).to_be_hidden()
    expect(launch).to_be_focused()


def verify_free_text_and_budget(page):
    guide = page.locator(".dh-guide")
    guide.locator(".dh-invite").click()
    field = guide.locator("#dh-guide-answer")
    guide.get_by_role("button", name="Home Renovation", exact=True).click()
    for answer in ["Shop & workshop", "Chennai", "Repair & refinish", "Around ₹3–4 lakh", "After the monsoon", "Test visitor", "+91 90000 00000"]:
        field.fill(answer)
        guide.locator('form button[type="submit"]').click()
    review = guide.get_by_role("heading", name="Review your enquiry")
    expect(review).to_be_focused()
    guide.get_by_role("checkbox").check()
    guide.get_by_role("button", name="Submit via WhatsApp").click()
    _, message = draft(page, 1)
    for answer in ["Home Renovation", "Shop & workshop", "Chennai", "Repair & refinish", "Around ₹3–4 lakh", "After the monsoon", "Test visitor", "+91 90000 00000"]:
        assert answer in message
    expect(guide.get_by_role("status")).to_contain_text("Press Send")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base")
    args = parser.parse_args()
    total = 0
    with serve(args.base) as base, sync_playwright() as engine:
        browser = engine.chromium.launch(executable_path=shutil.which("chromium") or shutil.which("google-chrome"))
        for path in PAGES:
            page = isolated_page(browser, base, path, {"width": 1280, "height": 800})
            total += verify_form(page)
            page.close()
            print("Form passed:", path, flush=True)
        for width, height, reduce in [(320, 568, False), (844, 390, False), (1024, 768, True)]:
            page = isolated_page(browser, base, "index.html", {"width": width, "height": height}, reduce)
            verify_guide(page)
            page.close()
            print(f"Assistant passed: {width} × {height}, reduced motion={reduce}", flush=True)
        page = isolated_page(browser, base, "Contact/contact.html", {"width": 390, "height": 844}, True)
        verify_free_text_and_budget(page)
        page.close()
        print("Assistant passed: welcome invitation, suggested reply, custom answers, optional budget, and single WhatsApp handoff.")
        browser.close()
    print(f"Verified {len(PAGES)} forms, {total} fields, and three guided enquiry profiles.")


if __name__ == "__main__":
    main()
