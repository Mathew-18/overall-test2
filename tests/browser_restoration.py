"""Run against the extracted static site with Chromium and Python Playwright."""
import argparse
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import shutil
from threading import Thread
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
PAGES=json.loads((ROOT/"data/site.json").read_text())["pages"]
WIDTHS=(320,360,390,430,768,992,1024,1280,1440,1920,844)

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass

def interact(page, counts):
    for q in page.locator(".faq-q").all():
        before=q.get_attribute("aria-expanded")
        q.press("Enter")
        expect(q).to_have_attribute("aria-expanded", "false" if before=="true" else "true")
        counts["faq questions"]+=1
    filters=page.locator(".gal-btn,.filter-btn").all()
    for b in filters:
        b.press("Enter")
        active=b.get_attribute("data-filter") or b.get_attribute("data-f")
        page.wait_for_function("""f => [...document.querySelectorAll('.proj-item,.gal-col,.gal-item[data-cat]')].every(el=>{
            const category = el.dataset.cat || el.dataset.c;
            return !!el.getClientRects().length === (f==='all'||category===f);
        })""",arg=active,timeout=3500)
        expect(b).to_have_attribute("aria-pressed","true")
        counts["filter selections"]+=1
    if filters:
        filters[0].press("Enter")
    for tile in page.locator("[data-photo-view],.proj-card-foot a[aria-haspopup]").all():
        tile.press("Enter")
        view=page.locator("dialog[open]")
        expect(view).to_have_count(1)
        if tile.get_attribute("data-photo-view") is not None:
            assert view.locator("img").get_attribute("src")==tile.locator("img").evaluate("img => img.currentSrc || img.src")
        else:
            assert view.locator("a").get_attribute("href")==tile.get_attribute("href")
        page.keyboard.press("Escape")
        expect(tile).to_be_focused()
        counts["viewers opened and dismissed"]+=1
    area=page.locator("#estArea")
    if area.count():
        for text,expected in [("50.9","5,864"),("-5","₹0"),("","₹0")]:
            area.fill(text)
            assert expected in page.locator("#estPrice").inner_text()
        for option in page.locator(".est-opt").all():
            option.press("Space")
            expect(option).to_have_attribute("aria-pressed","true")
            counts["calculator choices"]+=1
        area.fill("100")
        assert "21,150" in page.locator("#estPrice").inner_text()
    counters=page.locator("main [data-count],main .counter[data-target]")
    for counter in counters.all():
        counter.scroll_into_view_if_needed()
        page.wait_for_function("el => Number(el.textContent.replaceAll(',','').trim())===Number(el.dataset.count || el.dataset.target)",arg=counter.element_handle(),timeout=4500)
        counts["animated counter targets"]+=1

def run(out):
    counts=Counter()
    results=[]
    failures=[]
    with ThreadingHTTPServer(("127.0.0.1",0),partial(Handler,directory=ROOT.parent)) as server,sync_playwright() as engine:
        Thread(target=server.serve_forever,daemon=True).start()
        origin=f"http://127.0.0.1:{server.server_port}/"
        base=origin+ROOT.name+"/"
        browser=engine.chromium.launch(executable_path=shutil.which("chromium"))
        for width in WIDTHS:
            height=390 if width==844 else (844 if width<992 else 900)
            ctx=browser.new_context(viewport={"width":width,"height":height},has_touch=width<992,reduced_motion="reduce" if width in (320,1440) else "no-preference")
            ctx.route("**/*",lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
            page=ctx.new_page()
            page.set_default_timeout(4500)
            for path in PAGES:
                errs=[]
                def on_error(exc): errs.append(str(exc))
                def track(msg):
                    if msg.type=="error" and msg.location.get("url","").startswith(origin):errs.append(msg.text)
                def bad(res):
                    if res.url.startswith(origin) and res.status>=400:errs.append(f"{res.status}: {res.url}")
                page.on("pageerror",on_error);page.on("console",track);page.on("response",bad)
                try:
                    assert page.goto(base+path,wait_until="domcontentloaded").status==200
                    page.evaluate("document.fonts.ready")
                    state=page.evaluate("""() => {
                      const box=s=>document.querySelector(s).getBoundingClientRect();
                      return {width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,
                        sections:document.querySelectorAll('main>section').length,
                        headingClear:box('main h1').top >= box('header').bottom-1,
                        fonts:[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family),
                        clipped:[...document.querySelectorAll('main h1,main h2,main p,main .fc-custom,main button,footer a')].filter(e=>{
                          const r=e.getBoundingClientRect();return r.width && e.offsetWidth>0 && !e.closest('table,.comp-wrap') && (r.left < -2 || r.right>innerWidth+2)
                        }).map(el=>el.textContent.trim().slice(0,45)).slice(0,4)
                      }}""")
                    assert state["width"]<=width+1 and state["headingClear"],state
                    assert "Poppins" in state["fonts"] and "Playfair Display" in state["fonts"],state
                    # Entrance transforms can begin off the edge. Check final heading/content boxes in reduced motion.
                    if width in (320,1440):assert not state["clipped"],state
                    assert page.locator("header [aria-current=page]").evaluate("a=>a.href")==base+path
                    if width in (390,1440) and out:
                        page.screenshot(path=out/f"{Path(path).stem}-{width}.png",animations="disabled")
                    if width==1440:interact(page,counts)
                    if width==1280:
                        for counter in page.locator("[data-count],.counter[data-target],#stats .stat-num").all():
                            counter.scroll_into_view_if_needed()
                            if counter.get_attribute("data-count") or counter.get_attribute("data-target"):
                                page.wait_for_function("el => Number(el.textContent.replaceAll(',', '').trim())===Number(el.dataset.count || el.dataset.target)",arg=counter.element_handle(),timeout=5000)
                            else:
                                page.wait_for_function("el => Number(el.firstChild.textContent)>0",arg=counter.element_handle())
                            counts["motion-enabled counter checks"]+=1
                    if width==390 and path=="index.html" and out:
                        page.get_by_role("button",name="Open project assistant").click()
                        page.locator("#dh-guide-panel").evaluate("el => Promise.all(el.getAnimations().map(a=>a.finished))")
                        page.screenshot(path=out/"assistant-390.png")
                    assert not errs, list(map(str,errs))
                    results.append({"path":path,"width":width,"height":height,"document_height":state["height"]})
                except Exception as e:failures.append([path,width,str(e)[:900]])
                finally:
                    page.remove_listener("pageerror",on_error);page.remove_listener("console",track);page.remove_listener("response",bad)
            print(width,len(results),len(failures),flush=True)
            ctx.close()
        browser.close();server.shutdown()
    report={"passed_layout_profiles":len(results),"interactions":dict(counts),"failures":failures,"profiles":results}
    if out:(out.parent/"browser-results.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="profiles"},indent=2))
    return bool(failures)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--artifacts",type=Path);args=p.parse_args()
    if args.artifacts:args.artifacts.mkdir(parents=True,exist_ok=True)
    raise SystemExit(run(args.artifacts))
