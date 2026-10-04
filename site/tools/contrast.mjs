#!/usr/bin/env node
// contrast.mjs: WCAG 2.x contrast for every text colour token on every surface it sits
// on, in both themes, read straight from css/site.css so it cannot drift.
//   node site/tools/contrast.mjs        (exit 1 if any pair is under 4.5:1)

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const CSS = join(dirname(fileURLToPath(import.meta.url)), "..", "css", "site.css");

function block(css, selector) {
  const i = css.indexOf(selector);
  if (i < 0) throw new Error(`no ${selector} block in site.css`);
  const open = css.indexOf("{", i);
  return css.slice(open + 1, css.indexOf("}", open));
}

function parseColor(v) {
  v = v.trim();
  let m = /^#([0-9a-f]{6})$/i.exec(v);
  if (m) { const n = parseInt(m[1], 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255, 1]; }
  m = /^rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*(?:\/\s*([\d.]+))?\s*\)$/i.exec(v);
  if (m) return [Number(m[1]), Number(m[2]), Number(m[3]), m[4] === undefined ? 1 : Number(m[4])];
  return null;
}

function tokens(text) {
  const out = {};
  for (const m of text.matchAll(/--([\w-]+):\s*([^;]+);/g)) {
    const c = parseColor(m[2]);
    if (c) out[m[1]] = c;
  }
  return out;
}

const over = (fg, bg) => [0, 1, 2].map((i) => Math.round(fg[i] * fg[3] + bg[i] * (1 - fg[3]))).concat(1);
function lum([r, g, b]) {
  const f = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
export const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };

export function audit() {
  const css = readFileSync(CSS, "utf8");
  const themes = {
    dark: tokens(block(css, ':root[data-theme="dark"] {')),
    light: tokens(block(css, ':root[data-theme="light"] {')),
  };
  const rows = [];
  for (const [name, t] of Object.entries(themes)) {
    const solid = ["bg", "bg-2", "surface", "surface-2", "surface-3"].map((k) => [k, t[k]]);
    const tints = ["gold-soft", "clear-soft", "danger-soft"].map((k) => [`${k} on surface-2`, over(t[k], t["surface-2"])]);
    const grounds = [...solid, ...tints];
    for (const fg of ["text", "text-soft", "gold-text", "clear", "danger"]) {
      for (const [bgName, bg] of grounds) rows.push({ theme: name, fg, bg: bgName, ratio: ratio(t[fg], bg) });
    }
    rows.push({ theme: name, fg: "on-gold", bg: "gold", ratio: ratio(t["on-gold"], t.gold) });
  }
  // the player and the episode art are dark in both themes, with fixed colours
  for (const bg of ["#0B0F1A", "#141D36"]) {
    for (const fg of ["#F5F1E6", "#F4B728"]) rows.push({ theme: "player", fg, bg, ratio: ratio(parseColor(fg), parseColor(bg)) });
  }
  return rows;
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  const rows = audit();
  const bad = rows.filter((r) => r.ratio < 4.5);
  const worst = {};
  for (const r of rows) {
    const k = `${r.theme} ${r.fg}`;
    if (!worst[k] || r.ratio < worst[k].ratio) worst[k] = r;
  }
  for (const r of Object.values(worst)) console.log(`${r.theme.padEnd(6)} ${r.fg.padEnd(10)} lowest ${r.ratio.toFixed(2)}:1 on ${r.bg}`);
  if (bad.length) {
    console.error(`contrast: ${bad.length} pair(s) under 4.5:1`);
    bad.forEach((r) => console.error(`  ${r.theme} ${r.fg} on ${r.bg}: ${r.ratio.toFixed(2)}`));
    process.exit(1);
  }
  console.log(`contrast: ${rows.length} pairs, all AA (4.5:1 or more)`);
}
