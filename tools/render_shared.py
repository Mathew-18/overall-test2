"""Generate checked-in shared regions. Run with --check to detect stale HTML."""
import argparse
from html import escape
import json
import os
from pathlib import Path
from string import Template
from metadata import head, discovery_files

ROOT = Path(__file__).resolve().parents[1]


def replace_region(source, name, markup):
    start = f"<!-- shared:{name} -->"
    end = f"<!-- /shared:{name} -->"
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError(f"Expected one marker pair for {name}")
    before, rest = source.split(start)
    _, after = rest.split(end)
    return before + start + "\n" + markup.strip() + "\n    " + end + after


def render(page, site, templates, base_url, preview):
    def url(path):
        target, separator, fragment = path.partition("#")
        relative = os.path.relpath(ROOT / target, (ROOT / page).parent).replace(os.sep, "/")
        return escape(relative + separator + fragment, quote=True)

    def link(label, path, state=""):
        return f'<a href="{url(path)}"{state}>{escape(label)}</a>'

    def item_list(routes, active=False):
        items = []
        for label, path in routes.items():
            current = ' aria-current="page"' if active and page == path else ""
            items.append(f"          <li>{link(label, path, current)}</li>")
        return "\n".join(items)

    nav = site["navigation"]
    services = site["services"]
    navigation = []
    for label, path in nav.items():
        current = ' aria-current="page"' if page == path else ""
        if label == "Services":
            active = ' data-dh-active' if page == path or page in services.values() else ""
            service_links = {"All Services": path, **services}
            navigation.append(f'''      <li class="dh-service-item">
        <details class="dh-services">
          <summary class="dh-nav-link" data-dh-nav="services"{active} aria-controls="dh-service-links">
            Services <span class="dh-chevron" aria-hidden="true"></span>
          </summary>
          <ul id="dh-service-links">
{item_list(service_links, active=True)}
          </ul>
        </details>
      </li>''')
        else:
            active = ' data-dh-active' if current else ""
            state = f' class="dh-nav-link" data-dh-nav="{label.lower()}"{active}{current}'
            navigation.append(f"      <li>{link(label, path, state)}</li>")

    info = site["pages"][page]
    section_links = info.get("sections", {})
    shortcuts = ""
    if section_links:
        items = "\n".join(f'      <li><a href="#{escape(anchor)}">{escape(label)}</a></li>'
                          for anchor, label in section_links.items())
        shortcuts = f'''  <details class="dh-shortcuts">
    <summary>On this page</summary>
    <ul>
{items}
    </ul>
  </details>'''
    profiles = []
    for name, profile in site["social_profiles"].items():
        icon = f'<i class="bi bi-{name.lower()}" aria-hidden="true"></i>'
        if profile:
            element = f'<a href="{escape(profile)}" aria-label="{escape(name)}">{icon}</a>'
        else:
            label = escape(f"{name} profile unavailable")
            element = f'<span role="img" aria-label="{label}" title="{label}">{icon}</span>'
        profiles.append(f"        <li>{element}</li>")

    fields = {key: escape(value) for key, value in site["contact"].items()}
    fields.update(
        home=url(nav["Home"]), logo=url(site["logo"]), optimized_logo=url("assets/brand/logo.webp"), navigation="\n".join(navigation),
        profiles="\n".join(profiles), company=item_list(nav), services=item_list(services), shortcuts=shortcuts,
        footer_id=f' id="{escape(info["footer_id"])}"' if "footer_id" in info else "",
        description=escape(info["description"]), copyright=escape(info["copyright"]),
        specialties=item_list(info["specialties"]), location=escape(info["location"]),
        hours=f'\n      <p>{escape(info["hours"])}</p>' if "hours" in info else "",
    )
    path = ROOT / page
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    source = raw.decode().replace("\r\n", "\n")
    assets = f'<link rel="stylesheet" href="{url("assets/css/site.css")}">\n    <script defer src="{url("assets/js/site.js")}"></script>'
    for name in ("enquiries", "enhancements"):
        assets += f'\n    <link rel="stylesheet" href="{url(f"assets/css/{name}.css")}">'
        assets += f'\n    <script defer src="{url(f"assets/js/{name}.js")}"></script>'
    meta = info["meta"]
    source = replace_region(source, "metadata", head(page, meta["title"], meta["description"], base_url, preview))
    source = replace_region(source, "assets", assets)
    for name, template in templates.items():
        source = replace_region(source, name, template.substitute(fields))
    return source.replace("\n", newline).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--base-url", default="https://mathew-18.github.io/DH_Construction_Phase1_Test/")
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    if args.production and args.base_url == parser.get_default("base_url"):
        parser.error("Supply the approved production --base-url when requesting an indexable build")
    site = json.loads((ROOT / "data/site.json").read_text())
    templates = {name: Template((ROOT / f"templates/{name}.html").read_text())
                 for name in ("header", "footer", "assistant")}
    changes = {}
    for page in (*site["navigation"].values(), *site["services"].values()):
        output = render(page, site, templates, args.base_url, not args.production)
        path = ROOT / page
        if output != path.read_bytes():
            changes[path] = output
    for name, content in discovery_files(site["pages"], args.base_url, not args.production).items():
        path = ROOT / name
        output = content.encode("utf-8")
        if not path.exists() or path.read_bytes() != output:
            changes[path] = output
    for path, output in changes.items():
        print(path.relative_to(ROOT))
        if not args.check:
            path.write_bytes(output)
    return int(args.check and bool(changes))


if __name__ == "__main__":
    raise SystemExit(main())
