#!/usr/bin/env python3
"""Headless Chromium gate for the site: zero console errors, zero CSP violations.

Usage (server must be running on the site folder):
  python3 -m http.server 8765 --directory site &
  python3 site/tools/browser-check.py [--base http://127.0.0.1:8080] [--shots DIR] [--only /path/]

Every page is opened at 390x844 and 1360x900, in dark and light (forced with ?theme=),
with prefers-reduced-motion both on and off for one width. Console errors, warnings
that mention CSP, page errors, failed requests and securitypolicyviolation events all
count as failures. Exit 1 on any failure.
"""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGES = [
    "/", "/start/", "/episodes/", "/episodes/e0/", "/episodes/e1/", "/episodes/e2/", "/episodes/e3/",
    "/episodes/e4/", "/episodes/e5/", "/tools/address/", "/tools/chain/", "/learn/phrase-guard/", "/help/",
    "/404.html",
]
SIZES = [(390, 844), (1360, 900)]
THEMES = ["dark", "light"]

LISTEN = """
window.__csp = [];
document.addEventListener('securitypolicyviolation', (e) => {
  window.__csp.push({ directive: e.violatedDirective, blocked: e.blockedURI, sample: e.sample, line: e.lineNumber, src: e.sourceFile });
});
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8765")
    ap.add_argument("--shots", default=None)
    ap.add_argument("--only", action="append")
    ap.add_argument("--capture", action="store_true", help="also load every page with ?capture=1")
    args = ap.parse_args()
    pages = args.only or PAGES
    shots = Path(args.shots) if args.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)

    failures = []
    runs = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for (w, h) in SIZES:
            for theme in THEMES:
                for motion in (["no-preference", "reduce"] if w == 1360 else ["no-preference"]):
                    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1,
                                              reduced_motion=motion)
                    ctx.add_init_script(LISTEN)
                    page = ctx.new_page()
                    current = []
                    page.on("console", lambda m: current.append((m.type, m.text)))
                    page.on("pageerror", lambda e: current.append(("pageerror", str(e))))
                    page.on("requestfailed", lambda r: current.append(("requestfailed", f"{r.url} {r.failure}")))
                    page.on("response", lambda r: current.append(("http", f"{r.status} {r.url}")) if r.status >= 400 else None)
                    for path in pages:
                        variants = [f"?theme={theme}"] + ([f"?theme={theme}&capture=1"] if args.capture else [])
                        for q in variants:
                            url = f"{args.base}{path}{q}"
                            current.clear()
                            page.goto(url, wait_until="load")
                            page.wait_for_timeout(500)
                            # scroll through so scroll-driven and lazy parts run
                            page.evaluate("""async () => { const H = document.documentElement.scrollHeight;
                                for (let y = 0; y < H; y += Math.round(innerHeight * 0.8)) { scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
                                scrollTo(0, 0); }""")
                            page.wait_for_timeout(250)
                            csp = page.evaluate("window.__csp || []")
                            bad = [m for m in current if m[0] in ("error", "pageerror", "requestfailed", "http")
                                   or (m[0] == "warning" and ("Content Security" in m[1] or "CSP" in m[1]))]
                            for m in bad:
                                failures.append(f"{w}x{h} {theme} {motion} {path}{q}: {m[0]}: {m[1][:300]}")
                            for v in csp:
                                failures.append(f"{w}x{h} {theme} {motion} {path}{q}: CSP {json.dumps(v)[:300]}")
                            runs += 1
                    ctx.close()
        browser.close()
    print(f"browser-check: {runs} page loads")
    if failures:
        print(f"browser-check: {len(failures)} problem(s)")
        for f in failures:
            print("  " + f)
        return 1
    print("browser-check: zero console errors, zero CSP violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
