"""Run with python3 tests/browser_navigation.py (Playwright and Chromium)."""
import json
import os
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
MOBILE_BREAKPOINT = 991


class SiteHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def check_page(page, width):
    header = page.locator(".dh-header")
    toggle = header.locator(".dh-toggle")
    menu = header.locator("#dh-menu")
    summary = header.locator(".dh-services summary")
    service_links = header.locator("#dh-service-links")
    first_link = service_links.locator("a").first

    expect(menu.locator("a[aria-current='page']")).to_have_count(1)
    expect(menu.locator("[data-dh-active] .dh-indicator")).to_have_count(1)
    if width <= MOBILE_BREAKPOINT:
        expect(menu).to_be_hidden()
        toggle.tap()
        expect(toggle).to_have_attribute("aria-expanded", "true")
        summary.tap()
        expect(summary).to_have_attribute("aria-expanded", "true")
        expect(first_link).to_be_visible()
        summary.tap()
        expect(first_link).to_be_hidden()
    else:
        expect(toggle).to_be_hidden()
        expect(menu).to_be_visible()

    summary.focus()
    page.keyboard.press("ArrowDown")
    expect(first_link).to_be_focused()
    if width > MOBILE_BREAKPOINT:
        header_box = header.bounding_box()
        panel_box = service_links.bounding_box()
        assert panel_box["y"] >= header_box["y"] + header_box["height"] - 1, panel_box
    else:
        assert menu.evaluate("e => e.getBoundingClientRect().bottom <= innerHeight + 1")

    page.keyboard.press("Escape")
    expect(summary).to_be_focused()
    expect(summary).to_have_attribute("aria-expanded", "false")
    page.keyboard.press("Enter")
    expect(first_link).to_be_visible()
    page.keyboard.press("Tab")
    expect(first_link).to_be_focused()
    page.keyboard.press("Escape")
    if width <= MOBILE_BREAKPOINT:
        page.keyboard.press("Escape")
        expect(menu).to_be_hidden()
        expect(toggle).to_be_focused()


def run(browser, origin):
    catalog = json.loads((ROOT / "data/site.json").read_text())
    paths = list(catalog["navigation"].values()) + list(catalog["services"].values())
    for width in (320, 375, 768, 991, 992, 1440):
        context = browser.new_context(viewport={"width": width, "height": 800},
                                      has_touch=width <= MOBILE_BREAKPOINT)
        context.route("**/*", lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
        page = context.new_page()
        for path in paths:
            page.goto(origin + path, wait_until="domcontentloaded")
            try:
                check_page(page, width)
            except Exception as error:
                raise AssertionError(f"Navigation failed at {width}px on {path}") from error
        context.close()
        print(f"Navigation at {width}px passed on {len(paths)} pages.", flush=True)

    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto(origin + catalog["navigation"]["Home"], wait_until="domcontentloaded")
    page.locator("[data-dh-nav='about']").click()
    expect(page.locator("[data-dh-nav='about']")).to_have_attribute("aria-current", "page")
    summary = page.locator(".dh-services summary")
    summary.click()
    page.locator(".dh-logo").focus()
    expect(summary).to_have_attribute("aria-expanded", "false")
    summary.focus()
    page.set_viewport_size({"width": 390, "height": 760})
    expect(page.locator(".dh-toggle")).to_be_focused()
    page.locator(".dh-toggle").click()
    summary.click()
    service = page.locator("#dh-service-links a").nth(1)
    service_path = next(iter(catalog["services"].values()))
    service.click()
    expect(page).to_have_url(origin + service_path)
    expect(page.locator(".dh-toggle")).to_have_attribute("aria-expanded", "false")
    expect(page.locator("[data-dh-nav='services'] .dh-indicator")).to_have_count(1)
    page.locator(".dh-toggle").focus()
    page.set_viewport_size({"width": 1280, "height": 800})
    expect(page.locator("[data-dh-nav='services']")).to_be_focused()
    context.close()
    print("Cross-page selection, resize focus and service navigation passed.")

    for javascript in (True, False):
        context = browser.new_context(java_script_enabled=javascript, reduced_motion="reduce",
                                      viewport={"width": 375, "height": 680})
        page = context.new_page()
        page.goto(origin + catalog["navigation"]["Home"], wait_until="domcontentloaded")
        if javascript:
            page.locator(".dh-toggle").click()
        page.locator(".dh-services summary").click()
        disclosure = page.locator("#dh-service-links")
        expect(disclosure).to_be_visible()
        assert disclosure.evaluate("e => getComputedStyle(e).animationName") == "none"
        context.close()
    print("Reduced motion and navigation without JavaScript passed.")


if __name__ == "__main__":
    handler = partial(SiteHandler, directory=str(ROOT))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server, sync_playwright() as playwright:
        Thread(target=server.serve_forever, daemon=True).start()
        browser_path = os.environ.get("CHROMIUM_PATH") or shutil.which("chromium")
        browser = playwright.chromium.launch(executable_path=browser_path)
        try:
            run(browser, f"http://127.0.0.1:{server.server_port}/")
        finally:
            browser.close()
            server.shutdown()
