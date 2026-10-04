// Site integrity: pages are in sync with their sources, the CSP is current, links
// resolve, copy follows the house rules and nothing on the site can take a phrase.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join, relative } from "node:path";
import { build, mediaSet } from "../tools/layout.mjs";
import { run as csp, htmlFiles } from "../tools/csp.mjs";
import { checkLinks } from "../tools/check-links.mjs";
import { audit } from "../tools/contrast.mjs";
import { STEPS, EPISODES } from "../js/episodes.js";

const SITE = join(dirname(fileURLToPath(import.meta.url)), "..");
const REPO = join(SITE, "..");
const pages = htmlFiles();
const read = (f) => readFileSync(f, "utf8");

test("every page is in sync with tools/layout.mjs (run: node tools/build.mjs)", () => {
  for (const { file, html } of build({ write: false })) {
    assert.equal(read(join(SITE, file)), html, `${file} is stale: run node site/tools/build.mjs`);
  }
});

test("the CSP meta on every page and in vercel.json is current", () => {
  const r = csp({ check: true });
  assert.deepEqual(r.stale, [], `stale: ${r.stale.join(", ")}`);
  assert.equal(r.hashes.length, 1, "exactly one inline script (the theme setter)");
  const vercel = JSON.parse(read(join(SITE, "vercel.json")));
  const all = vercel.headers.find((h) => h.source === "/(.*)").headers;
  const get = (k) => all.find((h) => h.key === k)?.value;
  assert.match(get("Content-Security-Policy"), /frame-ancestors 'none'$/);
  assert.match(get("Strict-Transport-Security"), /max-age=\d+/);
  assert.equal(get("X-Content-Type-Options"), "nosniff");
  assert.equal(get("Referrer-Policy"), "no-referrer");
  assert.equal(get("Permissions-Policy"), "camera=(), microphone=(), geolocation=(), payment=()");
  assert.equal(get("Cross-Origin-Opener-Policy"), "same-origin");
  assert.equal(vercel.cleanUrls, true);
  assert.equal(vercel.trailingSlash, true);
});

test("every internal link, import and url resolves", () => {
  const { count, broken } = checkLinks();
  assert.ok(count > 300);
  assert.deepEqual(broken, []);
});

test("every text colour is AA in both themes", () => {
  const bad = audit().filter((r) => r.ratio < 4.5);
  assert.deepEqual(bad, []);
});

test("voice gate is clean on every page", () => {
  const gate = join(REPO, "tools", "voice-gate.mjs");
  if (!existsSync(gate)) return;
  const r = spawnSync(process.execPath, [gate, ...pages], { encoding: "utf8" });
  assert.equal(r.status, 0, r.stdout + r.stderr);
});

test("no inline styles, no style blocks, no third-party scripts, one inline script", () => {
  for (const f of pages) {
    const html = read(f);
    const name = relative(SITE, f);
    assert.ok(!/\sstyle="/i.test(html), `${name}: style attribute`);
    assert.ok(!/<style[\s>]/i.test(html), `${name}: <style> block`);
    assert.ok(!/\son[a-z]+="/i.test(html), `${name}: inline event handler`);
    for (const m of html.matchAll(/<script[^>]*\ssrc="([^"]+)"/g)) assert.ok(!/^(https?:)?\/\//.test(m[1]), `${name}: external script ${m[1]}`);
    assert.equal((html.match(/<script>/g) || []).length, 1, `${name}: inline scripts`);
    assert.match(html, /<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'sha256-/);
  }
});

test("footer carries the AI line and the no tracking line on every page", () => {
  for (const f of pages) {
    const html = read(f);
    assert.ok(html.includes("Scripts, narration and editing were produced with AI assistance (Kiro). Narration is a synthesised voice."), relative(SITE, f));
    assert.ok(html.includes("No tracking. No cookies. No analytics."), relative(SITE, f));
  }
});

test("the checklist uses exactly the six bounty words, in order", () => {
  assert.deepEqual(STEPS.map((s) => s.label), ["Wallet setup", "Getting ZEC", "Shielding", "Unshielding", "Sending", "Receiving"]);
  const home = read(join(SITE, "index.html"));
  const labels = [...home.matchAll(/<span class="cl-label">([^<]+)<\/span>/g)].map((m) => m[1]);
  assert.deepEqual(labels, STEPS.map((s) => s.label));
});

test("episode pages: one per episode, titles from episodes.js, I did it where steps exist", () => {
  assert.equal(EPISODES.length, 6);
  for (const e of EPISODES) {
    const html = read(join(SITE, "episodes", e.id, "index.html"));
    assert.ok(html.includes(`>${e.title.replace(/&/g, "&amp;")}</h1>`), e.id);
    assert.equal(html.includes("data-did-it"), e.steps.length > 0, e.id);
    assert.ok(html.includes("CC BY-ND 4.0"), e.id);
  }
});

test("diagrams are labelled and nothing accepts a phrase", () => {
  for (const f of pages) {
    const html = read(f);
    const name = relative(SITE, f);
    const figures = [...html.matchAll(/<figure class="(?:chain|mini-chain|stage)[^"]*"[\s\S]*?<\/figure>/g)];
    for (const fig of figures) assert.match(fig[0], /Diagram/, `${name}: a diagram without its label`);
    assert.ok(!/type="password"/i.test(html), `${name}: password field`);
    assert.ok(!/<form[\s>]/i.test(html), `${name}: form`);
    const fields = (html.match(/<(input|textarea)\b/g) || []).length;
    if (name === join("tools", "address", "index.html")) assert.equal(fields, 1, "the address box is the only field");
    else assert.equal(fields, 0, `${name}: has an input`);
  }
});

test("capture hooks: sections, ids and data-step items exist where the kit expects them", () => {
  const expect = [
    ["index.html", "hero", 3], ["index.html", "checklist", 6], ["start/index.html", "checklist", 6],
    ["start/index.html", "path", 5], ["tools/address/index.html", "checker", 4], ["tools/chain/index.html", "chain", 8],
  ];
  for (const [file, id, n] of expect) {
    const html = read(join(SITE, file));
    const start = html.indexOf(`id="${id}" data-capture-section`);
    assert.ok(start > 0, `${file} #${id}`);
    const end = html.indexOf("</section>", start);
    const steps = (html.slice(start, end).match(/\sdata-step[\s>]/g) || []).length;
    assert.equal(steps, n, `${file} #${id} items`);
  }
});

test("media manifest: players only point at files that exist", () => {
  const media = mediaSet();
  for (const f of pages) {
    for (const m of read(f).matchAll(/(?:src|poster|data-srt)="[^"]*media\/([^"?]+)(?:\?v=[0-9a-f]{10})?"/g)) assert.ok(media.has(m[1]), `${relative(SITE, f)}: ${m[1]}`);
  }
  if (existsSync(join(SITE, "media"))) {
    for (const name of readdirSync(join(SITE, "media"))) {
      if (/^zts-e\d\.(mp4|jpg|srt)$/.test(name)) assert.ok(media.has(name));
    }
  }
});
