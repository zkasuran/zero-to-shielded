#!/usr/bin/env python3
"""Build the click-to-copy thread page from docs/THREAD.md.

    python3 tools/thread-page.py [out_dir]     # default ~/Videos/zero-to-shielded-x

Writes THREAD.html next to the 4:5 episode files it names, so each card previews the exact
file to attach. One self-contained page: no network, no external fonts or scripts. Each post
has its text, the X character count (every URL counts 23), a Copy button and a Posted tick
saved in this browser. Re-run after any edit to docs/THREAD.md.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "Videos/zero-to-shielded-x"
X_MAX, URL_LEN = 280, 23

src = (ROOT / "docs/THREAD.md").read_text()
posts = []
for m in re.finditer(r"## (.+?)\n\n```text\n(.*?)\n```(.*?)(?=\n## |\Z)", src, re.S):
    name, text, rest = m.group(1), m.group(2), m.group(3)
    att = re.search(r"Attach `([^`]+)`", rest)
    xlen = len(re.sub(r"https?://\S+", "x" * URL_LEN, text))
    if xlen > X_MAX:
        sys.exit(f"{name}: {xlen} characters by X's count, over {X_MAX}")
    posts.append({"name": name, "text": text, "attach": att.group(1) if att else None, "x": xlen})
if len(posts) < 2:
    sys.exit("found no posts in docs/THREAD.md")


def link(text):
    out = html.escape(text)
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', out)


cards = []
for i, p in enumerate(posts):
    where = "Post this first" if i == 0 else f"Reply to post {i}"
    media = ""
    if p["attach"]:
        exists = (OUT / p["attach"]).is_file()
        media = (f'<figure class="media"><video src="{html.escape(p["attach"])}" controls preload="metadata" '
                 f'muted playsinline aria-label="Preview of {html.escape(p["attach"])}"></video>'
                 f'<figcaption>Attach <code>{html.escape(p["attach"])}</code>'
                 f'{"" if exists else " <strong class=warn>(file not found in this folder)</strong>"}</figcaption></figure>')
    else:
        media = '<p class="noattach">No video on this one.</p>'
    cards.append(f"""<li class="card" data-i="{i}">
  <div class="head"><span class="step">{i + 1}</span><div><h2>{html.escape(p["name"])}</h2><p class="where">{where}</p></div>
    <label class="done"><input type="checkbox" data-done> Posted</label></div>
  <div class="body">
    <div class="textcol">
      <pre class="text" id="t{i}">{link(p["text"])}</pre>
      <div class="row"><button type="button" class="copy" data-copy="{i}" aria-describedby="s{i}">Copy text</button>
        <span class="count" title="X counts every link as {URL_LEN}">{p["x"]} / {X_MAX}</span>
        <span class="status" id="s{i}" role="status" aria-live="polite"></span></div>
    </div>
    {media}
  </div>
</li>""")

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zero to Shielded: X thread, click to copy</title>
<style>
:root {{ color-scheme: dark; --bg:#0B0F1A; --card:#151C30; --line:#26304d; --text:#F5F1E6; --soft:#B9B3A3; --gold:#F4B728; --ink:#141826; --ok:#7ee0a1; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:16px/1.5 system-ui, -apple-system, "Segoe UI", Inter, sans-serif; }}
main {{ max-width: 1040px; margin: 0 auto; padding: 32px 20px 80px; }}
h1 {{ font-size: 30px; margin: 0 0 6px; }} h1 span {{ color: var(--gold); }}
.lede {{ color: var(--soft); margin: 0 0 8px; }}
.steps {{ color: var(--soft); margin: 0 0 24px; padding-left: 20px; }}
.progress {{ font-weight: 700; color: var(--gold); margin: 0 0 18px; }}
ol.cards {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 16px; }}
.card {{ background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 18px; }}
.card.is-done {{ opacity: .55; }}
.head {{ display: flex; align-items: center; gap: 14px; }}
.step {{ flex: none; width: 36px; height: 36px; border-radius: 50%; background: var(--gold); color: var(--ink); font-weight: 800; display: grid; place-items: center; }}
.head h2 {{ font-size: 18px; margin: 0; }} .where {{ margin: 0; color: var(--soft); font-size: 14px; }}
.done {{ margin-left: auto; display: flex; align-items: center; gap: 8px; color: var(--soft); cursor: pointer; }}
.done input {{ width: 20px; height: 20px; accent-color: var(--gold); }}
.body {{ display: grid; grid-template-columns: 1fr 220px; gap: 18px; margin-top: 14px; }}
@media (max-width: 760px) {{ .body {{ grid-template-columns: 1fr; }} }}
.text {{ white-space: pre-wrap; word-break: break-word; margin: 0; padding: 14px; background: #0f1526; border: 1px solid var(--line); border-radius: 12px; font: 16px/1.5 system-ui, sans-serif; }}
.text a {{ color: var(--gold); }}
.row {{ display: flex; align-items: center; gap: 14px; margin-top: 10px; flex-wrap: wrap; }}
button.copy {{ font: inherit; font-weight: 800; color: var(--ink); background: var(--gold); border: 0; border-radius: 999px; padding: 10px 20px; cursor: pointer; }}
button.copy:hover {{ background: #F8C244; }}
button:focus-visible, input:focus-visible, a:focus-visible {{ outline: 3px solid var(--gold); outline-offset: 3px; }}
.count {{ color: var(--soft); font-variant-numeric: tabular-nums; }}
.status {{ color: var(--ok); font-weight: 700; }}
.media {{ margin: 0; }} .media video {{ width: 100%; aspect-ratio: 4 / 5; background: #000; border-radius: 12px; }}
.media figcaption {{ font-size: 14px; color: var(--soft); margin-top: 6px; }}
code {{ color: var(--text); }} .warn {{ color: #FF9A8B; }}
.noattach {{ color: var(--soft); align-self: center; }}
</style></head>
<body><main>
<h1>Zero to Shielded <span>X thread</span></h1>
<p class="lede">{len(posts)} posts. Copy each one, paste it into X, attach the video shown beside it, post, then tick Posted.</p>
<ol class="steps">
  <li>Post 1 goes up on its own. Every other post is a reply to the one just before it, so the thread stays in order.</li>
  <li>Upload each video file into the post itself (not a link), so it plays in the feed.</li>
</ol>
<p class="progress" id="progress" aria-live="polite"></p>
<ol class="cards">
{chr(10).join(cards)}
</ol>
</main>
<script>
const POSTS = {json.dumps([p["text"] for p in posts])};
const KEY = "zts-thread-posted";
const load = () => {{ try {{ return new Set(JSON.parse(localStorage.getItem(KEY) || "[]")); }} catch {{ return new Set(); }} }};
const save = (s) => {{ try {{ localStorage.setItem(KEY, JSON.stringify([...s])); }} catch {{}} }};
async function copy(text) {{
  try {{ await navigator.clipboard.writeText(text); return true; }} catch {{
    const ta = document.createElement("textarea"); ta.value = text; ta.setAttribute("readonly", "");
    ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select();
    const ok = document.execCommand("copy"); ta.remove(); return ok;
  }}
}}
document.querySelectorAll("[data-copy]").forEach((b) => b.addEventListener("click", async () => {{
  const i = Number(b.dataset.copy), s = document.getElementById("s" + i);
  s.textContent = (await copy(POSTS[i])) ? "Copied" : "Copy failed: select the text by hand";
  setTimeout(() => (s.textContent = ""), 2500);
}}));
const paint = () => {{
  const done = load(); let n = 0;
  document.querySelectorAll(".card").forEach((c) => {{
    const on = done.has(c.dataset.i); c.classList.toggle("is-done", on); c.querySelector("[data-done]").checked = on; n += on;
  }});
  document.getElementById("progress").textContent = n === POSTS.length ? "All posted." : `${{n}} of ${{POSTS.length}} posted`;
}};
document.querySelectorAll("[data-done]").forEach((cb) => cb.addEventListener("change", () => {{
  const done = load(), i = cb.closest(".card").dataset.i; cb.checked ? done.add(i) : done.delete(i); save(done); paint();
}}));
paint();
</script>
</body></html>
"""
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "THREAD.html").write_text(page)
print(f"wrote {OUT / 'THREAD.html'}: {len(posts)} posts, longest {max(p['x'] for p in posts)} by X's count")
