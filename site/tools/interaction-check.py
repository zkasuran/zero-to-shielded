#!/usr/bin/env python3
"""End-to-end behaviour checks in headless Chromium (server on the site folder).
  python3 site/tools/interaction-check.py [--base http://127.0.0.1:8765]
Covers: I did it on E1 to E4 until "You're shielded", ticks on home, corrupt and blocked
storage, theme toggle, keyboard menu, Phrase Guard, Address detective, the chain flip,
the capture hook. Exit 1 on the first failed expectation or any console error."""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://127.0.0.1:8765"
errors, results = [], []


def expect(cond, what):
    results.append(("ok  " if cond else "FAIL") + " " + what)
    if not cond:
        raise SystemExit("\n".join(results) + f"\nFAILED: {what}")


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1360, "height": 900})
    pg = ctx.new_page()
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(str(e)))

    # I did it, episode by episode
    for ep, n in (("e1", 1), ("e2", 2), ("e3", 4), ("e4", 6)):
        pg.goto(f"{BASE}/episodes/{ep}/", wait_until="load")
        pg.click("[data-did-it]")
        pg.wait_for_timeout(120)
        stored = pg.evaluate("JSON.parse(localStorage.getItem('zts-progress')).done.length")
        expect(stored == n, f"{ep}: I did it stores {n} ticks")
        expect(pg.get_attribute("[data-did-it]", "aria-pressed") == "true", f"{ep}: button shows Done")
        if ep == "e4":
            expect(pg.evaluate("document.querySelector('[data-checklist-root]').classList.contains('is-complete')"), "e4: checklist shows You're shielded")
            expect(pg.locator(".burst").count() == 1, "e4: gold shield burst plays")
    pg.wait_for_timeout(1700)
    expect(pg.locator(".burst").count() == 0, "burst cleans itself up")

    pg.goto(f"{BASE}/", wait_until="load")
    expect(pg.evaluate("document.querySelector('#checklist [data-checklist-root]').classList.contains('is-k6')"), "home: all six ticked")
    expect(pg.locator(".ep-card [data-ep-done]:not([hidden])").count() == 4, "home: E1 to E4 cards say Done")
    pg.click('#checklist [data-cl-toggle="zec"]')
    expect(pg.evaluate("JSON.parse(localStorage.getItem('zts-progress')).done.includes('zec')") is False, "home: untick one step")
    pg.click("#checklist [data-cl-reset]")
    expect(pg.evaluate("JSON.parse(localStorage.getItem('zts-progress')).done.length") == 0, "home: clear ticks")

    # corrupt storage
    pg.evaluate("localStorage.setItem('zts-progress', '{not json')")
    pg.reload(wait_until="load")
    expect(pg.evaluate("document.querySelector('#checklist [data-checklist-root]').classList.contains('is-k0')"), "corrupt storage: page starts empty, no crash")
    pg.evaluate("localStorage.setItem('zts-progress', JSON.stringify({v:1, done:['wallet','evil','zec']}))")
    pg.reload(wait_until="load")
    expect(pg.evaluate("document.querySelector('#checklist [data-checklist-root]').classList.contains('is-k2')"), "unknown step ids are dropped")

    # blocked storage (quota or private mode)
    blocked = ctx.new_page()
    blocked.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    blocked.add_init_script("Storage.prototype.setItem = function () { throw new DOMException('full', 'QuotaExceededError'); };")
    blocked.goto(f"{BASE}/start/", wait_until="load")
    blocked.click('#checklist [data-cl-toggle="send"]')
    expect(blocked.evaluate("document.querySelector('#checklist [data-step-id=send]').classList.contains('is-done')"), "blocked storage: tick still shows")
    expect("not saving" in blocked.inner_text("#checklist [data-cl-note]"), "blocked storage: says it is not saving")
    blocked.close()

    # theme toggle
    pg.goto(f"{BASE}/", wait_until="load")
    before = pg.get_attribute("html", "data-theme")
    pg.click("[data-theme-toggle]")
    pg.wait_for_timeout(800)
    after = pg.get_attribute("html", "data-theme")
    expect(before != after and pg.evaluate("localStorage.getItem('zts-theme')") == after, f"theme toggle {before} -> {after}, saved")
    pg.goto(f"{BASE}/?theme={before}", wait_until="load")
    expect(pg.get_attribute("html", "data-theme") == before and pg.evaluate("localStorage.getItem('zts-theme')") == after, "?theme= forces without saving")

    # keyboard menu
    pg.goto(f"{BASE}/", wait_until="load")
    pg.keyboard.press("Tab")
    pg.keyboard.press("Tab")
    pg.keyboard.press("Tab")
    expect(pg.evaluate("document.querySelector('[data-nav-item=start]').classList.contains('is-open')"), "Tab onto Start opens its submenu")
    pg.keyboard.press("ArrowDown")
    expect(pg.evaluate("document.activeElement.closest('.nav-panel') !== null"), "ArrowDown moves into the submenu")
    pg.keyboard.press("Escape")
    expect(pg.evaluate("!document.querySelector('.nav-item.is-open') && document.activeElement.classList.contains('nav-trigger')"), "Escape closes and returns focus")
    pg.click('[data-nav-item="help"] .nav-trigger')
    expect(pg.evaluate("document.querySelector('[data-nav-item=help]').classList.contains('is-open')"), "click opens Help")
    pg.mouse.click(700, 600)
    expect(pg.evaluate("!document.querySelector('.nav-item.is-open')"), "click outside closes")

    # phrase guard, all right
    pg.goto(f"{BASE}/learn/phrase-guard/", wait_until="load")
    for ans in ["scam", "scam", "safe", "scam", "safe", "scam"]:
        pg.click(f'[data-g-pick="{ans}"]')
        pg.click("[data-g-next]")
    expect(pg.inner_text("[data-g-final]") == "6", "Phrase Guard: 6 of 6")
    expect(pg.locator(".burst").count() == 1, "Phrase Guard: burst on a perfect score")

    # address detective
    pg.goto(f"{BASE}/tools/address/", wait_until="load")
    for _ in range(6):
        addr = pg.get_attribute("[data-det-addr]", "title")
        pick = "shielded" if addr.startswith(("u1", "zs1")) else "transparent"
        pg.click(f'[data-det-pick="{pick}"]')
        pg.click("[data-det-next]")
    expect(pg.inner_text("[data-det-addr]").startswith("6 of 6"), "detective: 6 of 6")
    expect(pg.inner_text("[data-det-best]") == "6", "detective: best streak 6 saved")

    # chain flip
    pg.goto(f"{BASE}/tools/chain/", wait_until="load")
    pg.click('[data-mode-btn="shielded"]')
    pg.wait_for_timeout(1400)
    w = pg.inner_text('[data-w="amount"]')
    note = pg.inner_text('[data-p="note"]')
    expect("ZEC" not in w and note == "Thanks for lunch!", f"chain: Watcher sees '{w}', Sam reads '{note}'")
    pg.click('[data-mode-btn="transparent"]')
    pg.wait_for_timeout(1200)
    expect(pg.inner_text('[data-w="amount"]') == "0.50 ZEC", "chain: back to transparent")

    # capture hook only with ?capture=1
    pg.goto(f"{BASE}/", wait_until="load")
    expect(pg.evaluate("typeof window.setReveal") == "undefined", "no setReveal without ?capture=1")
    pg.goto(f"{BASE}/?capture=1", wait_until="load")
    saved_before = pg.evaluate("localStorage.getItem('zts-progress')")
    pg.evaluate("window.setReveal(3, '#checklist')")
    expect(pg.evaluate("document.querySelectorAll('#checklist .cl-step.is-done').length") == 3, "setReveal(3) ticks three steps")
    expect(pg.evaluate("localStorage.getItem('zts-progress')") == saved_before, "setReveal saves nothing")
    pg.evaluate("window.setReveal(1, '#hero')")
    expect(pg.evaluate("[...document.querySelectorAll('#hero [data-step]')].map(e => getComputedStyle(e).opacity).join()") == "1,0,0", "setReveal(1) on #hero shows only the headline")

    b.close()

print("\n".join(results))
if errors:
    print("console errors:", errors)
    sys.exit(1)
print(f"interaction-check: {len(results)} checks passed, no console errors")
