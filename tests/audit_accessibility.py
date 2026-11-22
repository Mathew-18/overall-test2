"""Check all site pages with Chromium, Playwright, and a local axe-core bundle.

Run: python3 tests/audit_accessibility.py --axe /path/to/axe.min.js
Use the official axe-core 4.10.3 npm bundle. The audit serves only the local
checkout, blocks external browser requests, and checks initially visible states.
"""

import argparse
import asyncio
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
from threading import Thread

from playwright.async_api import async_playwright


ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


async def audit(axe_path):
    pages = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))["pages"]
    handler = partial(QuietHandler, directory=str(ROOT))
    checks = []
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{server.server_port}/"
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(executable_path=shutil.which("chromium"))
            try:
                for width in (375, 1440):
                    context = await browser.new_context(viewport={"width": width, "height": 880},
                                                        reduced_motion="reduce")
                    await context.route("**/*", lambda route: route.continue_()
                                        if route.request.url.startswith(origin) else route.abort())
                    for path in pages:
                        page = await context.new_page()
                        try:
                            response = await page.goto(origin + path)
                            if response is None or response.status != 200:
                                raise RuntimeError(f"Could not serve {path}")
                            await page.evaluate("document.fonts.ready")
                            await page.add_script_tag(path=str(axe_path))
                            findings = await page.evaluate("""async () => {
                              const results = await axe.run(document, {runOnly: {
                                type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"]
                              }});
                              return results.violations.map(v => ({
                                rule: v.id, impact: v.impact, targets: v.nodes.map(n => n.target),
                                detail: v.nodes[0].failureSummary
                              }));
                            }""")
                            print(f"{width}px {path}: {len(findings)} rule violations", flush=True)
                            checks.append({"page": path, "width": width, "findings": findings})
                        finally:
                            await page.close()
                    await context.close()
            finally:
                await browser.close()
                server.shutdown()
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--axe", required=True, type=Path)
    parser.add_argument("--json", type=Path, help="Optional result file")
    args = parser.parse_args()
    results = asyncio.run(audit(args.axe.resolve(strict=True)))
    if args.json:
        args.json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    failures = [check for check in results if check["findings"]]
    if failures:
        print(json.dumps(failures, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
