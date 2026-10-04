// series.js: the Zero to Shielded design library for stage pages.
//
// Every episode page imports this and the engine, then registers scenes:
//
//   import * as Z from "./lib/series.js";
//   Z.scene("e1-create", (S) => { ... }, { label: "Diagram, not the app" });
//
// Z.scene installs the series field (ink, gold drift, grain), the in-frame captions and
// the honesty label before your build runs. Components take S and options, return their
// element (or a handle) and carry their own enter and exit motion, timed by `at` and
// `until` (scene seconds). `until` defaults to the end of the segment; pass null to keep.
//
// Honesty rules baked in: nothing here draws an app screen. Buttons are text chips,
// addresses show only their prefix, phrase slots are numbered blurred bars, the phone is
// an outline with an abstract glow.

import { Stage, ease, rng, hash, clamp, lerp, smooth } from "../../../tools/video-kit/stage/stage.js";

export { Stage, ease, rng, hash, clamp, lerp, smooth };

export const C = {
  gold: "#F4B728", goldHi: "#FFE39A", goldDeep: "#8A5C00", cream: "#F5F1E6", soft: "#B9B3A3",
  blue: "#7AA2FF", ink: "#07090F", ink2: "#1E2642", onGold: "#1B1304",
};

// Make sure the stylesheet is on the page and loaded before the engine builds.
(() => {
  const href = new URL("./series.css", import.meta.url).href;
  let link = [...document.querySelectorAll('link[rel="stylesheet"]')].find((l) => l.href === href);
  if (!link) {
    link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
  if (!link.sheet) Stage.wait(new Promise((res) => { link.addEventListener("load", res, { once: true }); link.addEventListener("error", res, { once: true }); }));
})();

// ---------------------------------------------------------------- icons (inline SVG)

const I = {
  info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9.2"/><path d="M12 11v5.4"/><circle cx="12" cy="7.6" r=".6" fill="currentColor"/></svg>`,
  lock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.6l4.4 4.4L19 7.4"/></svg>`,
  cycle: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19.5 12a7.5 7.5 0 0 1-12.8 5.3"/><path d="M4.5 12a7.5 7.5 0 0 1 12.8-5.3"/><path d="M17.6 3.2v3.6H14"/><path d="M6.4 20.8v-3.6H10"/></svg>`,
  globe: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.6 2.6 3.8 5.6 3.8 9s-1.2 6.4-3.8 9c-2.6-2.6-3.8-5.6-3.8-9S9.4 5.6 12 3z"/></svg>`,
  alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3.5l9 16H3z"/><path d="M12 10v4.4"/><circle cx="12" cy="17.2" r=".5" fill="currentColor"/></svg>`,
  arrow: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>`,
};
export const icons = I;

// the series mark: the site's own shield outline (not a brand logo)
const SHIELD_PATH = "M16 2.6l10.6 4v7.6c0 6.6-4.4 11.8-10.6 13.9C9.8 26 5.4 20.8 5.4 14.2V6.6z";
let uid = 0;
function shieldSvg({ check = true, tone = "gold" } = {}) {
  const id = `zs${++uid}`;
  const stops = tone === "blue"
    ? ["#E1EAFF", "#9DB8FF", "#7AA2FF", "#3F63C4"]
    : tone === "deep"
      ? ["#E8C25A", "#B98300", "#8A5C00", "#5E3E00"]
      : ["#FFF0BE", "#FFD45E", "#F4B728", "#B57D00"];
  return `<svg class="zts-shield" viewBox="4 1.6 24 28.4" aria-hidden="true">
<defs><linearGradient id="${id}g" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="${stops[0]}"/><stop offset=".3" stop-color="${stops[1]}"/><stop offset=".62" stop-color="${stops[2]}"/><stop offset="1" stop-color="${stops[3]}"/></linearGradient>
<linearGradient id="${id}h" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<path d="${SHIELD_PATH}" fill="url(#${id}g)"/>
<path d="${SHIELD_PATH}" fill="none" stroke="url(#${id}h)" stroke-width=".7" transform="translate(16 15.6) scale(.86) translate(-16 -15.6)"/>
${check ? `<path d="M11 15.6l3.4 3.4 6.6-6.8" fill="none" stroke="${tone === "blue" ? "#0E1D45" : "#2A1B00"}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>` : ""}
</svg>`;
}

// ---------------------------------------------------------------- layout helpers

// place(el, x, y, anchor): absolute position in scene px; anchor "center" | "top" | "left" | "topleft"
export function place(el, x, y, anchor = "center") {
  if (x == null || y == null) return el;
  el.classList.add("zts-abs");
  el.style.left = `${x}px`;
  el.style.top = `${y}px`;
  const tf = { center: "translate(-50%,-50%)", top: "translate(-50%,0)", left: "translate(0,-50%)", bottom: "translate(-50%,-100%)", topleft: "" }[anchor] ?? "translate(-50%,-50%)";
  if (tf) {
    el.dataset.tf = tf;
    el.style.transform = tf;
  }
  return el;
}

const untilOf = (S, until) => (until === undefined ? S.seconds : until);

// appear(S, el, {at, until, from, exit}): the series enter and exit motion
export function appear(S, el, { at = 0, until, from = { opacity: 0, y: 34, blur: 10 }, exit = { opacity: 0, y: -22, blur: 8 }, dur = 0.9, exitDur = 0.45, ease: e = "outExpo" } = {}) {
  if (at != null) S.enter(el, { at, dur, ease: e, from });
  const u = untilOf(S, until);
  if (u != null && isFinite(u)) S.exit(el, { at: Math.max(at ?? 0, u - exitDur), dur: exitDur, to: exit, ease: "inCubic" });
  return el;
}

// words(S, parent, text, {at, stagger}): one span per word, each rises in after the last
export function words(S, parent, text, { at = 0, stagger = 0.06, dur = 0.9, from = { opacity: 0, y: 38, blur: 10 }, ease: e = "outExpo" } = {}) {
  const spans = [];
  String(text).split(/\s+/).filter(Boolean).forEach((w, i, all) => {
    const s = S.el("span", { class: "zts-word", text: w }, parent);
    spans.push(s);
    if (i < all.length - 1) parent.appendChild(document.createTextNode(" "));
  });
  if (at != null) spans.forEach((s, i) => S.enter(s, { at: at + i * stagger, dur, ease: e, from }));
  return spans;
}

// ---------------------------------------------------------------- the field

function glowSprite(rgb, size = 64) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  const grd = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grd.addColorStop(0, `rgba(${rgb},1)`);
  grd.addColorStop(0.18, `rgba(${rgb},.75)`);
  grd.addColorStop(0.42, `rgba(${rgb},.18)`);
  grd.addColorStop(1, `rgba(${rgb},0)`);
  g.fillStyle = grd;
  g.fillRect(0, 0, size, size);
  return c;
}

function noiseTile(seed, size = 160) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  const img = g.createImageData(size, size);
  const R = rng(seed);
  for (let i = 0; i < size * size; i++) {
    // sparse: about 45% of the cells carry a speck, so frames stay cheap to encode
    const on = R() < 0.45;
    const v = R() < 0.5 ? 0 : 255;
    img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v;
    img.data[i * 4 + 3] = on ? 8 + Math.floor(R() * 22) : 0;
  }
  g.putImageData(img, 0, 0);
  return c;
}

// field(S): radial ink, two slow glows, one canvas of drifting gold motes plus film grain.
// Everything is driven by global time (S.offset + t), so a cut between two segments of
// the same episode does not jump.
export function field(S, { motes = 120, grain = true, seed = 20261004, depth = 0.12 } = {}) {
  // params.grain (0..1, default 1) and params.motes are production knobs for the kit
  if (S.params.grain != null) grain = Number(S.params.grain);
  if (S.params.motes != null) motes = Number(S.params.motes);
  const grainK = grain === true ? 1 : Number(grain) || 0;
  const bleed = 140;
  const layer = S.layer(depth, { cls: "zts-field", bleed });
  const FW = 1920 + 2 * bleed, FH = 1080 + 2 * bleed;
  const g1 = S.el("div", { class: "zts-field-glow", style: { width: "1300px", height: "1300px", willChange: "transform" } }, layer);
  const g2 = S.el("div", { class: "zts-field-glow is-blue", style: { width: "1400px", height: "1400px", willChange: "transform" } }, layer);
  const cv = S.el("canvas", {}, layer);
  const k = Math.min(1, window.devicePixelRatio || 1);
  cv.width = Math.round(FW * k);
  cv.height = Math.round(FH * k);
  const ctx = cv.getContext("2d");
  const gold = glowSprite("255,206,96");
  const pale = glowSprite("255,236,190");
  const R = rng(seed);
  const parts = [];
  for (let i = 0; i < motes; i++) {
    const z = Math.pow(R(), 1.6) * 0.85 + 0.15;
    parts.push({
      x: R() * FW, y: R() * FH, z,
      r: 2.2 + z * 7.5 + R() * 2.5,
      vx: (3 + R() * 7) * (0.4 + z), vy: -(4 + R() * 9) * (0.4 + z),
      ph: R() * Math.PI * 2, f: 0.1 + R() * 0.25, amp: 8 + R() * 22, tw: 0.4 + R() * 1.1,
      pale: R() < 0.28,
    });
  }
  const bokeh = [];
  for (let i = 0; i < 9; i++) bokeh.push({ x: R() * FW, y: R() * FH, r: 40 + R() * 70, vx: 2 + R() * 4, vy: -(1.5 + R() * 3), a: 0.025 + R() * 0.04, ph: R() * 6.28 });
  // grain is drawn at half resolution and scaled up softly: it reads as film grain, it
  // survives video compression better than single pixel noise and it keeps PNGs light
  const tile = grainK > 0 ? noiseTile(seed + 1) : null;
  const pattern = tile ? ctx.createPattern(tile, "repeat") : null;
  if (pattern) pattern.setTransform(new DOMMatrix().scale(2, 2));
  const vig = S.layer(0, { cls: "zts-vignette-layer" });
  S.el("div", { class: "zts-vignette" }, vig);
  const wrap = (v, m) => ((v % m) + m) % m;
  let last = null;
  S.on((t) => {
    const g = S.offset + t;
    const cam = S.camAt(t);
    // glows: slow orbits
    const t1 = `translate(${(-200 + Math.sin(g * 0.05) * 90).toFixed(1)}px,${(-260 + Math.cos(g * 0.043) * 60).toFixed(1)}px)`;
    const t2 = `translate(${(FW - 1300 + Math.cos(g * 0.037) * 110).toFixed(1)}px,${(FH - 1000 + Math.sin(g * 0.031) * 80).toFixed(1)}px)`;
    if (g1._tf !== t1) { g1.style.transform = t1; g1._tf = t1; }
    if (g2._tf !== t2) { g2.style.transform = t2; g2._tf = t2; }
    const key = `${g.toFixed(4)}|${cam.x.toFixed(2)}|${cam.y.toFixed(2)}|${cam.zoom.toFixed(4)}`;
    if (key === last) return;
    last = key;
    ctx.setTransform(k, 0, 0, k, 0, 0);
    ctx.clearRect(0, 0, FW, FH);
    // near motes move a little more with the camera than the layer itself: depth
    const px = -(cam.x - 960) * 0.18, py = -(cam.y - 540) * 0.18;
    const zs = (cam.zoom - 1) * 0.25;
    ctx.globalCompositeOperation = "lighter";
    for (const b of bokeh) {
      const x = wrap(b.x + b.vx * g, FW + 300) - 150;
      const y = wrap(b.y + b.vy * g, FH + 300) - 150;
      ctx.globalAlpha = b.a * (0.7 + 0.3 * Math.sin(g * 0.3 + b.ph));
      ctx.drawImage(gold, x - b.r, y - b.r, b.r * 2, b.r * 2);
    }
    for (const p of parts) {
      let x = wrap(p.x + p.vx * g + Math.sin(g * p.f + p.ph) * p.amp, FW + 60) - 30;
      let y = wrap(p.y + p.vy * g, FH + 60) - 30;
      x += px * p.z; y += py * p.z;
      const sc = 1 + zs * p.z;
      x = FW / 2 + (x - FW / 2) * sc; y = FH / 2 + (y - FH / 2) * sc;
      const tw = 0.55 + 0.45 * Math.sin(g * p.tw + p.ph * 3);
      ctx.globalAlpha = clamp((0.16 + 0.6 * p.z) * tw, 0, 1);
      const r = p.r * sc;
      ctx.drawImage(p.pale ? pale : gold, x - r, y - r, r * 2, r * 2);
    }
    ctx.globalCompositeOperation = "source-over";
    if (pattern) {
      // grain changes 24 times a second, position picked by hash: pure in time
      const fi = Math.floor(g * 24);
      const ox = Math.floor(hash(fi, 17) * 160) * 2, oy = Math.floor(hash(fi, 29) * 160) * 2;
      ctx.globalAlpha = 0.6 * grainK;
      ctx.translate(-ox, -oy);
      ctx.fillStyle = pattern;
      ctx.fillRect(ox, oy, FW, FH);
    }
    ctx.globalAlpha = 1;
  });
  return layer;
}

// ---------------------------------------------------------------- scene wrapper

// look(S, {label, captions}): field + captions + honesty label
export function look(S, { label: text, captions = true, motes, grain, seed } = {}) {
  field(S, { motes, grain, seed });
  if (captions) S.captions();
  if (text) label(S, text);
}

// scene(id, build, meta): Stage.scene with the series look installed first.
// meta: {label, narration (preview captions), seconds (preview length), look: {...}}
export function scene(id, build, meta = {}) {
  return Stage.scene(id, async (S) => {
    look(S, { label: meta.label, ...(meta.look || {}) });
    await build(S);
  }, meta);
}

// ---------------------------------------------------------------- honesty label

// label(S, text): pinned top left for the whole scene, never animated, never zoomed
export function label(S, text) {
  const el = S.el("div", { class: "zts-label", html: "<i></i><span></span>" }, S.overlay);
  el.lastChild.textContent = text;
  return el;
}

// ---------------------------------------------------------------- headline, note

export function headline(S, { kicker, text, at = 0.2, until, x = 960, y = 210, size = "h2", align = "center", width = 1400, stagger = 0.05 } = {}) {
  const el = S.el("div", { class: `zts-headline${align === "left" ? " is-left" : ""}`, style: { width: `${width}px` } });
  place(el, x, y, align === "left" ? "left" : "center");
  if (kicker) {
    const k = S.el("div", { class: "zts-kicker", text: kicker }, el);
    S.enter(k, { at, dur: 0.8, from: { opacity: 0, y: 14, blur: 6 } });
  }
  const h = S.el("div", { class: size === "h1" ? "zts-h1" : "zts-h2" }, el);
  words(S, h, text, { at: at + (kicker ? 0.12 : 0), stagger });
  const u = untilOf(S, until);
  if (u != null && isFinite(u)) S.exit(el, { at: u - 0.45, to: { opacity: 0, y: -18, blur: 8 } });
  return el;
}

export function note(S, text, { at = 0.4, until, x, y, parent, anchor = "center" } = {}) {
  const el = S.el("div", { class: "zts-note", text }, parent);
  place(el, x, y, anchor);
  appear(S, el, { at, until, from: { opacity: 0, y: 14, blur: 6 }, dur: 0.7 });
  return el;
}

// ---------------------------------------------------------------- chips

// chip(S, text, {kind: "gold"|"blue"|"ghost"|"banner"|"step", tap, at, until, x, y, icon, size, strike, parent})
// Shorthand flags work too: {gold: true}, {blue: true}, {ghost: true}.
export function chip(S, text, opts = {}) {
  const kind = opts.kind || (opts.blue ? "blue" : opts.ghost ? "ghost" : opts.banner ? "banner" : "gold");
  const size = opts.size ? ` zts-chip--${opts.size}` : "";
  const el = S.el("div", { class: `zts-chip zts-chip--${kind}${size}` }, opts.parent);
  S.el("div", { class: "zts-chip-bg" }, el);
  if (kind === "step") S.el("div", { class: "zts-chip-lit" }, el);
  const fx = S.el("div", { class: "zts-chip-fx", style: "position:absolute;inset:0;border-radius:inherit;overflow:hidden;z-index:-1" }, el);
  const ripple = S.el("div", { class: "zts-chip-ripple" }, fx);
  const ring = S.el("div", { class: "zts-chip-ring" }, el);
  const ico = opts.icon ?? (kind === "banner" ? "alert" : null);
  if (ico) S.el("span", { class: "zts-chip-ico", html: I[ico] || ico }, el);
  const label = S.el("span", { class: "zts-chip-text", text }, el);
  // hidden until a tap() or pulse() drives them: a tween's `from` value applies before it
  // starts, so without this the ring and ripple would show at 0.9 from the first frame
  S.set(ripple, { opacity: 0 });
  S.set(ring, { opacity: 0 });
  el._ripple = ripple;
  el._ring = ring;
  el._label = label;
  place(el, opts.x, opts.y, opts.anchor);
  if (opts.at != null) appear(S, el, { at: opts.at, until: opts.until, from: { opacity: 0, y: 22, scale: 0.9, blur: 6 }, dur: 0.75 });
  const taps = opts.tap == null ? [] : [].concat(opts.tap);
  for (const t of taps) tap(S, el, t);
  if (opts.strike != null) strike(S, el, opts.strike);
  return el;
}

// tap(S, chipEl, at): press, ripple and a ring pulse exactly at `at`
export function tap(S, el, at) {
  S.tween(el, { at: at - 0.07, dur: 0.07, ease: "outQuad", to: { scale: 0.93 } });
  S.tween(el, { at: at + 0.02, dur: 0.5, ease: "outBack", to: { scale: 1 } });
  if (el._ripple) S.tween(el._ripple, { at, dur: 0.75, ease: "outCubic", from: { opacity: 0.95, scale: 0.15 }, to: { opacity: 0, scale: 3.6 } });
  if (el._ring) S.tween(el._ring, { at: at + 0.02, dur: 0.7, ease: "outCubic", from: { opacity: 0.9, scale: 1 }, to: { opacity: 0, scale: 1.22 } });
}

// pulse(S, chipEl, at): a ring and a small lift, for "this one" as the narration names it
export function pulse(S, el, at) {
  S.tween(el, { at, dur: 0.22, ease: "outCubic", to: { scale: 1.07 } });
  S.tween(el, { at: at + 0.22, dur: 0.6, ease: "outBack", to: { scale: 1 } });
  if (el._ring) S.tween(el._ring, { at, dur: 0.8, ease: "outCubic", from: { opacity: 0.95, scale: 1 }, to: { opacity: 0, scale: 1.28 } });
}

// strike(S, chipEl, at): a line draws through the chip and it dims (for "not needed" items)
export function strike(S, el, at) {
  const line = S.el("div", { class: "zts-strike" }, el);
  S.tween(line, { at, dur: 0.45, ease: "inOutCubic", from: { "--strike": 0 }, to: { "--strike": 1 } });
  S.tween(el._label || el, { at: at + 0.1, dur: 0.4, to: { opacity: 0.5 } });
  return line;
}

// ---------------------------------------------------------------- step flow

const ARROW_ROW = `<svg class="zts-flow-arrow" viewBox="0 0 96 28"><path pathLength="1" d="M4 14 H86"/><path class="head" d="M76 5 L88 14 L76 23"/></svg>`;
const ARROW_COL = `<svg class="zts-flow-arrow" viewBox="0 0 28 70"><path pathLength="1" d="M14 4 V60"/><path class="head" d="M5 50 L14 62 L23 50"/></svg>`;

// stepFlow(S, {steps, at, gap, times, x, y, dir, mode, keep, until})
// steps: "Open Zodl" | {label, kind, note, tap} | {group: ["Receive", ...], title, kind}
// mode "build": each step arrives as it lights. mode "light": all steps show at `at`,
// then light one by one. keep: leave earlier steps lit. Returns {el, chips, steps, times}.
export function stepFlow(S, { steps = [], at = 0.4, gap = 1.0, times, x = 960, y = 440, dir = "row", mode = "build", keep = false, until, tapAll = false, size } = {}) {
  const el = S.el("div", { class: `zts-flow${dir === "col" ? " is-col" : ""}` });
  place(el, x, y);
  const T = steps.map((_, i) => (times && times[i] != null ? times[i] : at + i * gap));
  const out = { el, chips: [], steps: [], arrows: [], times: T };
  steps.forEach((raw, i) => {
    const st = typeof raw === "string" ? { label: raw } : raw;
    const ti = T[i];
    if (i > 0) {
      const a = S.el("div", { html: dir === "col" ? ARROW_COL : ARROW_ROW, style: "display:flex" }, el).firstChild;
      const draw = mode === "light" ? at : ti - 0.42;
      S.tween(a, { at: draw, dur: 0.42, ease: "inOutCubic", from: { "--draw": 0, "--head": 0 }, to: { "--draw": 1 } });
      S.tween(a, { at: draw + 0.3, dur: 0.2, to: { "--head": 1 } });
      if (mode === "light") S.tween(a, { at: ti - 0.3, dur: 0.3, from: { opacity: 0.45 }, to: { opacity: 1 } });
      out.arrows.push(a);
    }
    const wrap = S.el("div", { class: "zts-flow-step" }, el);
    out.steps.push(wrap);
    if (st.group) {
      const g = S.el("div", { class: "zts-group" }, wrap);
      if (st.title) S.el("div", { class: "zts-group-title", text: st.title }, g);
      const chips = st.group.map((name, j) => chip(S, name, { kind: st.kind || "gold", parent: g, size: st.size || size, at: (mode === "light" ? at : ti) + 0.08 + j * 0.09, until }));
      appear(S, g, { at: (mode === "light" ? at : ti) - 0.05, until, from: { opacity: 0, scale: 0.96, blur: 8 }, dur: 0.8 });
      out.chips.push(chips);
    } else {
      const lit = st.kind == null || st.kind === "step";
      const c = chip(S, st.label, { kind: lit ? "step" : st.kind, parent: wrap, size: st.size || size, icon: st.icon });
      const enterAt = mode === "light" ? at + i * 0.08 : ti - 0.12;
      appear(S, c, { at: enterAt, until, from: { opacity: 0, y: 18, scale: 0.9, blur: 6 }, dur: 0.75 });
      if (lit) {
        S.tween(c, { at: ti, dur: 0.22, ease: "outCubic", from: { "--lit": 0 }, to: { "--lit": 1 } });
        if (!st.tap) {
          // a small pop as it lights (a tap already gives the tapped chip its own motion)
          S.tween(c, { at: ti, dur: 0.16, ease: "outCubic", to: { scale: 1.05 } });
          S.tween(c, { at: ti + 0.16, dur: 0.5, ease: "outBack", to: { scale: 1 } });
        }
        if (!keep && i < steps.length - 1 && T[i + 1] != null) {
          c.classList.add("is-done");
          S.tween(c, { at: T[i + 1], dur: 0.26, ease: "outCubic", to: { "--lit": 0 } });
          S.tween(c, { at: T[i + 1], dur: 0.26, ease: "outCubic", from: { "--done": 0 }, to: { "--done": 1 } });
        }
      }
      if (st.tap || (tapAll && st.tap !== false)) tap(S, c, typeof st.tap === "number" ? st.tap : ti + 0.22);
      if (st.note) {
        const n = S.el("div", { class: "zts-flow-note", text: st.note }, wrap);
        appear(S, n, { at: st.noteAt ?? ti + 0.5, until, from: { opacity: 0, y: 10 }, dur: 0.6 });
      }
      out.chips.push(c);
    }
  });
  return out;
}

// ---------------------------------------------------------------- cards

// defCard(S, {term, text, at, until, x, y, kind, icon})
export function defCard(S, { term, text, at = 0.3, until, x = 960, y = 640, kind = "gold", icon = true, width } = {}) {
  const el = S.el("div", { class: `zts-card zts-def${kind === "blue" ? " is-blue" : ""}` });
  if (width) el.style.width = `${width}px`;
  place(el, x, y);
  if (icon) {
    const ic = S.el("div", { html: kind === "blue" ? shieldSvg({ check: false, tone: "blue" }) : shieldSvg({ check: true }), style: "flex:none" }, el).firstChild;
    ic.classList.add("zts-def-ico");
    S.enter(ic, { at: at + 0.2, dur: 0.9, ease: "outBack", from: { opacity: 0, scale: 0.6, rotate: -8 } });
  }
  S.el("div", { class: "zts-def-bar" }, el);
  const body = S.el("div", {}, el);
  const tEl = S.el("div", { class: "zts-def-term", text: term }, body);
  const xEl = S.el("div", { class: "zts-def-text" }, body);
  words(S, xEl, text, { at: at + 0.3, stagger: 0.028, dur: 0.8, from: { opacity: 0, y: 16, blur: 6 } });
  S.enter(tEl, { at: at + 0.15, dur: 0.8, from: { opacity: 0, x: -16, blur: 6 } });
  appear(S, el, { at, until, from: { opacity: 0, y: 46, scale: 0.97, blur: 12 }, dur: 1.0 });
  return el;
}

// addressCard(S, {title, prefix, badge, kind, at, until, x, y, note, refresh: [t...], seed})
// Shows only the prefix and a blurred tail of bars: never a full address, never characters.
export function addressCard(S, { title = "Zcash Shielded Address", prefix = "u1", badge = "Private", kind = "shielded", at = 0.3, until, x = 960, y = 460, note, refresh = [], seed = 3, spin = false } = {}) {
  const el = S.el("div", { class: `zts-card zts-addr is-${kind}` });
  place(el, x, y);
  const head = S.el("div", { class: "zts-addr-head" }, el);
  S.el("div", { class: "zts-addr-title", text: title }, head);
  if (badge) S.el("div", { class: `zts-badge is-${kind}`, html: `${kind === "shielded" ? I.lock : ""}<span></span>` }, head).lastChild.textContent = badge;
  const badgeEl = head.lastChild;
  if (badgeEl && badgeEl.querySelector("svg")) Object.assign(badgeEl.querySelector("svg").style, { width: "20px", height: "20px" });
  const line = S.el("div", { class: "zts-addr-line" }, el);
  S.el("div", { class: "zts-addr-prefix", text: prefix }, line);
  const tail = S.el("div", { class: "zts-addr-tail" }, line);
  const R = rng(seed);
  const bars = [];
  for (let i = 0; i < 6; i++) {
    const w = 40 + R() * 46;
    const b = S.el("span", { style: { width: `${w.toFixed(0)}px`, transformOrigin: "0 50%" } }, tail);
    bars.push(b);
  }
  refresh.forEach((rt, k) => {
    bars.forEach((b, i) => {
      const s = 0.55 + hash(seed, k, i) * 0.9;
      S.tween(b, { at: rt + i * 0.03, dur: 0.5, ease: "inOutCubic", to: { scaleX: s, opacity: 0.6 + hash(seed, k, i, 3) * 0.4 } });
    });
  });
  let spinEl = null;
  if (note) {
    const n = S.el("div", { class: "zts-addr-note", html: `${I.cycle}<span></span>` }, el);
    n.lastChild.textContent = note;
    spinEl = n.firstChild;
    S.enter(n, { at: at + 0.6, dur: 0.7, from: { opacity: 0, y: 10 } });
  }
  if (spinEl && (spin || refresh.length)) {
    spinEl.style.transformOrigin = "50% 50%";
    const times = refresh.length ? refresh : [];
    S.on((t) => {
      let r = 0;
      if (spin) r = t * 40;
      for (const rt of times) r += 360 * ease.inOutCubic(clamp((t - rt) / 0.8));
      const tf = `rotate(${r.toFixed(2)}deg)`;
      if (spinEl._tf !== tf) { spinEl.style.transform = tf; spinEl._tf = tf; }
    });
  }
  appear(S, el, { at, until, from: { opacity: 0, y: 40, scale: 0.97, blur: 10 }, dur: 1.0 });
  return el;
}

// ---------------------------------------------------------------- objects

// coin(S, kind, {size, text, label, at, until, x, y, parent}): gold = shielded, blue = transparent
export function coin(S, kind = "gold", { size = 132, text = "ZEC", label, at, until, x, y, parent } = {}) {
  const el = S.el("div", { class: `zts-coin is-${kind === "blue" || kind === "transparent" ? "blue" : "gold"}`, text, style: { "--d": `${size}px` } }, parent);
  if (label) S.el("div", { class: "zts-coin-label", text: label }, el);
  place(el, x, y);
  if (at != null) appear(S, el, { at, until, from: { opacity: 0, scale: 0.6, y: 20, blur: 6 }, dur: 0.8, ease: "outBack" });
  return el;
}

// shield(S, {size, check, tone, at, until, x, y, parent, glow})
export function shield(S, { size = 140, check = true, tone = "gold", at, until, x, y, parent, glow = true } = {}) {
  const el = S.el("div", { html: shieldSvg({ check, tone }), style: { width: `${size}px`, height: `${size * 1.18}px` } }, parent);
  const svg = el.firstChild;
  svg.style.width = "100%";
  svg.style.height = "100%";
  if (glow) el.dataset.filter = `drop-shadow(0 ${(size * 0.12).toFixed(0)}px ${(size * 0.22).toFixed(0)}px rgba(244,183,40,.35))`;
  el.style.filter = el.dataset.filter || "";
  place(el, x, y);
  if (at != null) appear(S, el, { at, until, from: { opacity: 0, scale: 0.5, rotate: -10, blur: 8 }, dur: 1.0, ease: "outBack" });
  return el;
}

// envelope(S, {at, until, x, y, open, lines, parent}): sealed gold letter; `open` time
// lifts the flap and slides the letter out, its lines decrypt (scramble) as it rises
export function envelope(S, { at, until, x, y, open, lines = [], parent, seed = 5 } = {}) {
  const el = S.el("div", { class: "zts-env" }, parent);
  S.el("div", { class: "zts-env-back" }, el);
  const letter = S.el("div", { class: "zts-env-letter" }, el);
  const rows = lines.map((ln, i) => {
    const r = S.el("div", { class: "zts-post-line zts-scramble", style: "border-color:rgba(138,92,0,.2);font-size:32px" }, letter);
    if (open != null) S.scramble(r, { text: ln, at: open + 0.55 + i * 0.12, until: open + 1.35 + i * 0.12, seed: seed + i, mode: "decrypt", spans: true });
    else r.textContent = ln;
    return r;
  });
  S.el("div", { class: "zts-env-front" }, el);
  const flap = S.el("div", { class: "zts-env-flap" }, el);
  const seal = S.el("div", { class: "zts-env-seal", html: shieldSvg({ check: false, tone: "deep" }) }, el);
  place(el, x, y);
  if (open != null) {
    S.tween(el, { at: open, dur: 0.8, ease: "inOutCubic", from: { "--open": 0 }, to: { "--open": 1 } });
    S.tween(el, { at: open + 0.45, dur: 0.9, ease: "outExpo", from: { "--rise": 0 }, to: { "--rise": 1 } });
    // the flap passes behind the letter once it is past upright
    S.on((t) => {
      const back = t >= open + 0.4;
      if (flap._b !== back) { flap.style.zIndex = back ? "0" : "3"; letter.style.zIndex = back ? "2" : "1"; flap._b = back; }
    });
  }
  if (at != null) appear(S, el, { at, until, from: { opacity: 0, y: 40, rotate: 4, blur: 10 }, dur: 1.0 });
  el._letter = letter;
  el._rows = rows;
  el._seal = seal;
  return el;
}

// postcard(S, {lines, tag, stamp, at, until, x, y, parent}): blue, every line readable
export function postcard(S, { lines = [], tag = "Postcard", stamp = "t1", at, until, x, y, parent } = {}) {
  const el = S.el("div", { class: "zts-post" }, parent);
  if (tag) S.el("div", { class: "zts-post-tag", text: tag }, el);
  const box = S.el("div", { class: "zts-post-lines" }, el);
  const rows = lines.map((ln) => {
    const r = S.el("div", { class: "zts-post-line" }, box);
    const m = /^(From|To)\s+(.*)$/.exec(ln);
    if (m) { S.el("em", { text: m[1] }, r); r.appendChild(document.createTextNode(m[2])); }
    else r.textContent = ln;
    return r;
  });
  if (stamp) S.el("div", { class: "zts-post-stamp", text: stamp }, el);
  place(el, x, y);
  if (at != null) appear(S, el, { at, until, from: { opacity: 0, y: 40, rotate: -4, blur: 10 }, dur: 1.0 });
  el._rows = rows;
  return el;
}

// phraseCard(S, {at, until, x, y, slots, write: {at, dur}, title, seed})
// 24 numbered slots, each a blurred bar. No word ever appears, real or fake.
export function phraseCard(S, { at = 0.3, until, x = 960, y = 450, slots = 24, write, title = "Recovery phrase", seed = 9, parent } = {}) {
  const el = S.el("div", { class: "zts-paper" }, parent);
  const head = S.el("div", { class: "zts-paper-head" }, el);
  S.el("div", { class: "zts-paper-title", text: title }, head);
  S.el("div", { class: "zts-paper-count", text: `${slots} words` }, head);
  const grid = S.el("div", { class: "zts-slots" }, el);
  const R = rng(seed);
  const bars = [];
  for (let i = 0; i < slots; i++) {
    const s = S.el("div", { class: "zts-slot" }, grid);
    S.el("b", { text: String(i + 1) }, s);
    const bar = S.el("span", { style: { width: `${(80 + R() * 120).toFixed(0)}px` } }, s);
    bars.push(bar);
  }
  if (write) {
    const per = (write.dur ?? 4) / slots;
    bars.forEach((b, i) => S.tween(b, { at: write.at + i * per, dur: per * 1.4, ease: "inOutSine", from: { "--w": 0 }, to: { "--w": 1 } }));
  }
  place(el, x, y);
  if (at != null) appear(S, el, { at, until, from: { opacity: 0, y: 50, rotate: -2, blur: 12 }, dur: 1.0 });
  el._bars = bars;
  return el;
}

// phone(S, {at, until, x, y, glyph, tone, glow}): a plain phone outline with an abstract
// glowing screen. Never an app screen.
export function phone(S, { at, until, x, y, glyph = "shield", tone = "gold", glow = 1, parent, scale } = {}) {
  const el = S.el("div", { class: "zts-phone" }, parent);
  const scr = S.el("div", { class: `zts-phone-screen${tone === "blue" ? " is-blue" : ""}`, style: { "--glow": String(glow) } }, el);
  S.el("div", { class: "zts-phone-pill" }, scr);
  if (glyph === "shield") S.el("div", { html: shieldSvg({ check: true }) }, scr);
  place(el, x, y);
  if (scale) S.set(el, { scale });
  if (at != null) appear(S, el, { at, until, from: { opacity: 0, y: 60, blur: 10 }, dur: 1.0 });
  el._screen = scr;
  return el;
}

// ---------------------------------------------------------------- burst

// burst(S, {at, x, y, seed, count, power, ring}): a seeded gold particle burst on one
// shared canvas inside the camera layer. Pure in t.
export function burst(S, { at, x = 960, y = 460, seed = 1, count = 80, power = 1, ring = true, life = 1.5 } = {}) {
  if (!S._burst) {
    const cv = S.el("canvas", { class: "zts-burst" });
    const k = Math.min(2, window.devicePixelRatio || 1);
    cv.width = 1920 * k;
    cv.height = 1080 * k;
    const ctx = cv.getContext("2d");
    const spr = glowSprite("255,214,110", 48);
    const list = [];
    let dirty = true;
    S._burst = list;
    S.on((t) => {
      const live = list.filter((b) => t >= b.at && t <= b.at + b.life + 0.1);
      if (!live.length && !dirty) return;
      ctx.setTransform(k, 0, 0, k, 0, 0);
      ctx.clearRect(0, 0, 1920, 1080);
      dirty = live.length > 0;
      ctx.globalCompositeOperation = "lighter";
      for (const b of live) {
        const tau = t - b.at;
        if (b.ring) {
          const p = clamp(tau / 0.9);
          if (p < 1) {
            ctx.globalAlpha = (1 - p) * 0.7;
            ctx.strokeStyle = "rgba(255,214,110,1)";
            ctx.lineWidth = 6 * (1 - p) + 1;
            ctx.beginPath();
            ctx.arc(b.x, b.y, 30 + ease.outExpo(p) * 260 * b.power, 0, Math.PI * 2);
            ctx.stroke();
          }
        }
        for (const q of b.parts) {
          if (tau > q.life) continue;
          const dk = q.drag;
          const dist = (q.v * (1 - Math.exp(-dk * tau))) / dk;
          const px = b.x + Math.cos(q.a) * dist;
          const py = b.y + Math.sin(q.a) * dist + 0.5 * 260 * tau * tau;
          const fade = Math.pow(1 - tau / q.life, 1.5);
          const sp = q.v * Math.exp(-dk * tau);
          ctx.globalAlpha = fade;
          const r = q.r * (0.6 + 0.4 * fade);
          ctx.drawImage(spr, px - r * 3, py - r * 3, r * 6, r * 6);
          if (q.streak && sp > 120) {
            ctx.globalAlpha = fade * 0.55;
            ctx.strokeStyle = q.pale ? "#FFF3D0" : "#FFD25E";
            ctx.lineWidth = Math.max(1, r * 0.7);
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(px - Math.cos(q.a) * sp * 0.045, py - Math.sin(q.a) * sp * 0.045);
            ctx.stroke();
          }
        }
      }
      ctx.globalCompositeOperation = "source-over";
      ctx.globalAlpha = 1;
    });
  }
  const R = rng(seed * 7919 + 13);
  const parts = [];
  for (let i = 0; i < count; i++) {
    parts.push({
      a: R() * Math.PI * 2, v: (300 + R() * 900) * power, drag: 2.4 + R() * 2.2,
      r: 2 + R() * 4.5, life: life * (0.55 + R() * 0.45), streak: R() < 0.6, pale: R() < 0.35,
    });
  }
  S._burst.push({ at, x, y, parts, ring, power, life });
}

// ---------------------------------------------------------------- lens

// lens(S, {r, zoom, keys: [{at, x, y, dur, ease}], layers: [el], at, until})
// A magnifier. Each layer is an absolutely placed element in scene px (the "what the lens
// sees" version of whatever is under it); the lens shows it, magnified, through a circle.
export function lens(S, { r = 140, zoom = 1.25, keys = [], layers = [], at = 0, until } = {}) {
  const T = S.track(keys, { x: 960, y: 460 });
  const ring = S.el("div", { class: "zts-lens-ring" });
  const body = S.el("div", { style: `position:absolute;left:0;top:0;--r:${r}` }, ring);
  S.el("div", { class: "handle" }, body);
  S.el("div", { class: "rim" }, body);
  for (const l of layers) l.classList.add("zts-lens-layer");
  const u = untilOf(S, until);
  const visAt = (t) => smooth(at, at + 0.5, t) * (u != null && isFinite(u) ? 1 - smooth(u - 0.4, u, t) : 1);
  S.on((t) => {
    const p = T(t);
    const v = visAt(t);
    const tf = `translate(${p.x.toFixed(2)}px,${p.y.toFixed(2)}px)`;
    if (ring._tf !== tf) { ring.style.transform = tf; ring._tf = tf; }
    const btf = `scale(${(0.7 + 0.3 * ease.outBack(v)).toFixed(4)})`;
    if (body._tf !== btf) { body.style.transform = btf; body._tf = btf; }
    const o = v.toFixed(3);
    if (ring._o !== o) { ring.style.opacity = o; ring._o = o; }
    for (const l of layers) {
      const ox = l.offsetLeft, oy = l.offsetTop;
      const lx = p.x - ox, ly = p.y - oy;
      const rr = (r * (0.7 + 0.3 * v)) / zoom;
      const cp = v > 0.01 ? `circle(${rr.toFixed(2)}px at ${lx.toFixed(2)}px ${ly.toFixed(2)}px)` : "circle(0px at 0 0)";
      if (l._cp !== cp) { l.style.clipPath = cp; l._cp = cp; }
      const ltf = `translate(${lx.toFixed(2)}px,${ly.toFixed(2)}px) scale(${zoom}) translate(${(-lx).toFixed(2)}px,${(-ly).toFixed(2)}px)`;
      if (l._tf !== ltf) { l.style.transform = ltf; l.style.transformOrigin = "0 0"; l._tf = ltf; }
    }
  });
  return { el: ring, at: T };
}

// ---------------------------------------------------------------- browser window (real site)

// browserWindow(S, {url, src, at, until, x, y, scale, vw, vh})
// A Screen Studio style window around a same-origin iframe of the real companion site,
// rendered at vw x vh CSS px and scaled to fit. Returns a handle:
//   {el, iframe, site (S.site helper), ready, rect(sel, {at}), point(sel, {at}), box}
export function browserWindow(S, { url = "zero-to-shielded.vercel.app", src = "/", at = 0.1, until, x = 960, y = 468, scale = 0.8, vw = 1440, vh = 900, theme = "dark" } = {}) {
  const w = Math.round(vw * scale), h = Math.round(vh * scale);
  const el = S.el("div", { class: "zts-window", style: { width: `${w}px`, height: `${h + 56}px` } });
  place(el, x, y);
  const bar = S.el("div", { class: "zts-window-bar" }, el);
  S.el("div", { class: "zts-window-dots", html: "<i></i><i></i><i></i>" }, bar);
  const m = /^([^/]+)(\/.*)?$/.exec(url.replace(/^https?:\/\//, ""));
  const host = m ? m[1] : url;
  const path = m && m[2] && m[2] !== "/" ? m[2] : "";
  const u = S.el("div", { class: "zts-window-url", html: `${I.lock}<span></span><b></b>` }, bar);
  u.children[1].textContent = host;
  u.children[2].textContent = path;
  const view = S.el("div", { class: "zts-window-view", style: { width: `${w}px`, height: `${h}px` } }, el);
  const full = new URL(src, location.origin);
  if (!full.searchParams.has("capture")) full.searchParams.set("capture", "1");
  if (!full.searchParams.has("theme")) full.searchParams.set("theme", theme);
  const iframe = S.el("iframe", { attrs: { src: full.pathname + full.search + full.hash, width: String(vw), height: String(vh), scrolling: "no", tabindex: "-1", "aria-hidden": "true" }, style: { width: `${vw}px`, height: `${vh}px`, transform: `scale(${scale})` } }, view);
  const site = S.site(iframe);
  if (at != null) appear(S, el, { at, until, from: { opacity: 0, y: 70, scale: 0.94, blur: 12 }, dur: 1.1 });
  return {
    el, iframe, site, ready: site.ready, scale,
    rect: (sel, o) => site.rect(sel, o),
    point: (sel, o) => site.point(sel, o),
  };
}

// ---------------------------------------------------------------- cast

let castMod = null;
// Probe first: the kit treats a failed .js request as fatal. cast.js is optional here.
// "/js/cast.js/" reaches the same file on the kit's server (empty segments are dropped)
// but does not end in .js, so a miss is only a warning.
const loadCast = () => (castMod ??= fetch("/js/cast.js/", { cache: "no-store" })
  .then((r) => (r.ok && /javascript/.test(r.headers.get("content-type") || "") ? import("/js/cast.js") : null))
  .catch(() => null)
  .then((m) => {
    if (!m) console.warn("[series] /js/cast.js not available, using fallback figures");
    return m;
  }));

function fallbackFigure(who) {
  const tone = who === "sam" ? ["#7AA2FF", "#3F5FB8"] : who === "watcher" ? ["#B9B3A3", "#6E6A60"] : ["#F4B728", "#B57D00"];
  if (who === "watcher") {
    return `<svg viewBox="0 0 220 360" aria-hidden="true"><defs><linearGradient id="fw1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3A4366"/><stop offset="1" stop-color="#1A2038"/></linearGradient></defs>
<rect x="40" y="250" width="140" height="34" rx="8" fill="#2A3150" stroke="rgba(245,241,230,.25)" stroke-width="2"/><rect x="52" y="286" width="116" height="34" rx="8" fill="#232A46" stroke="rgba(245,241,230,.2)" stroke-width="2"/><rect x="64" y="322" width="92" height="34" rx="8" fill="#1D2340" stroke="rgba(245,241,230,.18)" stroke-width="2"/>
<path d="M70 248 C70 190 150 190 150 248 Z" fill="url(#fw1)" stroke="rgba(245,241,230,.3)" stroke-width="2"/><circle cx="110" cy="150" r="44" fill="url(#fw1)" stroke="rgba(245,241,230,.3)" stroke-width="2"/>
<circle cx="110" cy="150" r="24" fill="#0B0F1A" stroke="#F5F1E6" stroke-width="5"/><circle cx="102" cy="142" r="7" fill="rgba(255,255,255,.55)"/></svg>`;
  }
  return `<svg viewBox="0 0 220 360" aria-hidden="true"><defs><linearGradient id="ff${who}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${tone[0]}"/><stop offset="1" stop-color="${tone[1]}"/></linearGradient></defs>
<path d="M30 352 C30 250 70 214 110 214 C150 214 190 250 190 352 Z" fill="url(#ff${who})" opacity=".92"/>
<circle cx="110" cy="146" r="56" fill="url(#ff${who})"/><path d="M76 120 a40 40 0 0 1 68 0" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="5" stroke-linecap="round"/></svg>`;
}

// castFigure(S, who, {size, pose, mood, at, until, x, y, name, parent})
// Uses /js/cast.js (maya, sam, watcher) when it is there; otherwise a simple silhouette.
export function castFigure(S, who, { size = 340, pose, mood, at, until, x, y, name, parent } = {}) {
  const el = S.el("div", { class: "zts-figure", style: { width: `${size}px` } }, parent);
  el.dataset.who = who;
  S.defer(loadCast().then((m) => {
    let svg = null;
    const fn = m && (m[who] || (m.default && m.default[who]));
    if (typeof fn === "function") {
      try { svg = fn({ size, theme: "dark", label: false, pose, mood }); } catch (e) { console.warn(`[series] cast.${who}() failed`, e); }
    }
    el.insertAdjacentHTML("afterbegin", typeof svg === "string" && svg.includes("<svg") ? svg : fallbackFigure(who));
    el.dataset.source = typeof svg === "string" && svg.includes("<svg") ? "cast" : "fallback";
  }));
  if (name) S.el("div", { class: "zts-figure-name", text: name }, el);
  place(el, x, y);
  if (at != null) appear(S, el, { at, until, from: { opacity: 0, y: 40, blur: 10 }, dur: 1.0 });
  return el;
}

// ---------------------------------------------------------------- opening and end cards

// openingCard(S, {n, title, at, until}): the same card in every episode (about 4 s)
export function openingCard(S, { n = 1, title = "", at = 0, until } = {}) {
  const root = S.el("div", { class: "zts-open" });
  const row = S.el("div", { class: "zts-open-row" }, root);
  const numWrap = S.el("div", { class: "zts-open-num-wrap" }, row);
  const glow = S.el("div", { class: "zts-open-num-glow" }, numWrap);
  const shadow = S.el("div", { class: "zts-open-num-shadow" }, numWrap);
  const num = S.el("div", { class: "zts-open-num", text: String(n) }, numWrap);
  const text = S.el("div", { class: "zts-open-text" }, row);
  const kicker = S.el("div", { class: "zts-kicker", text: `Zero to Shielded · Episode ${n}` }, text);
  const h = S.el("div", { class: "zts-open-title" }, text);
  const ws = words(S, h, title, { at: at + 0.55, stagger: 0.075, dur: 1.0, from: { opacity: 0, y: 46, blur: 12 } });
  const rule = S.el("div", { class: "zts-open-rule" }, text);
  const aka = S.el("div", { class: "zts-open-aka", html: `${I.info}<span><b>Zodl</b> was called <b>Zashi</b> in older guides</span>` }, text);

  S.enter(glow, { at, dur: 1.8, ease: "outCubic", from: { opacity: 0, scale: 0.55 } });
  S.enter(shadow, { at: at + 0.2, dur: 1.2, ease: "outCubic", from: { opacity: 0, scaleX: 0.6 } });
  S.enter(num, { at: at + 0.05, dur: 1.25, ease: "outExpo", from: { opacity: 0, y: 90, scale: 0.86, blur: 18 } });
  S.tween(num, { at: at + 0.6, dur: 1.5, ease: "inOutCubic", from: { "--sweep": -0.3 }, to: { "--sweep": 1.35 } });
  S.enter(kicker, { at: at + 0.35, dur: 0.9, from: { opacity: 0, x: -26, blur: 6 } });
  S.tween(rule, { at: at + 1.0, dur: 0.9, ease: "outExpo", from: { scaleX: 0, opacity: 0 }, to: { scaleX: 1, opacity: 1 } });
  S.enter(aka, { at: at + 1.2, dur: 0.9, from: { opacity: 0, y: 16, blur: 6 } });
  // slow parallax drift while it holds: numeral and text move apart a touch
  const hold = Math.max(1, untilOf(S, until) ?? S.seconds);
  S.tween(numWrap, { at, dur: hold, ease: "inOutSine", from: { x: 10, y: 6 }, to: { x: -14, y: -8 } });
  S.tween(text, { at, dur: hold, ease: "inOutSine", from: { x: -6 }, to: { x: 10 } });
  const u = untilOf(S, until);
  if (u != null && isFinite(u)) S.exit(row, { at: u - 0.5, dur: 0.5, to: { opacity: 0, scale: 0.97, y: -24, blur: 10 } });
  return { el: root, num, title: h, words: ws, kicker };
}

// endCard(S, {next, url, ticks, note, more, at, until}): next step and the site URL
export function endCard(S, { next = "", url = "zero-to-shielded.vercel.app", ticks = [], note, more, at = 0.15, until = null } = {}) {
  const root = S.el("div", { class: "zts-end" });
  const sh = S.el("div", { html: shieldSvg({ check: true }) }, root).firstChild;
  sh.parentNode.style.cssText = "display:contents";
  S.enter(sh, { at, dur: 1.1, ease: "outBack", from: { opacity: 0, scale: 0.4, rotate: -12, blur: 8 } });
  if (ticks.length) {
    const row = S.el("div", { class: "zts-end-ticks" }, root);
    ticks.forEach((tk, i) => chip(S, tk, { kind: "ghost", size: "sm", icon: "check", parent: row, at: at + 0.25 + i * 0.12, until }));
    row.querySelectorAll(".zts-chip-ico").forEach((e) => (e.style.color = C.gold));
  }
  let kick = "Next";
  let line = String(next);
  const m = /^Next:\s*(.*)$/i.exec(line);
  if (m) line = m[1];
  if (line) {
    const k = S.el("div", { class: "zts-kicker", text: kick }, root);
    S.enter(k, { at: at + 0.3, dur: 0.8, from: { opacity: 0, y: 12, blur: 6 } });
    const big = S.el("div", { class: "zts-end-next" }, root);
    words(S, big, line, { at: at + 0.42, stagger: 0.07, dur: 1.0, from: { opacity: 0, y: 44, blur: 12 } });
  }
  const pill = S.el("div", { class: "zts-end-url", html: `${I.globe}<span></span><u></u>` }, root);
  pill.children[1].textContent = url;
  pill.firstChild.style.color = C.gold;
  S.enter(pill, { at: at + 0.85, dur: 1.0, from: { opacity: 0, y: 34, scale: 0.96, blur: 10 } });
  S.tween(pill.children[2], { at: at + 1.35, dur: 1.0, ease: "outExpo", from: { "--draw": 0 }, to: { "--draw": 1 } });
  if (more) {
    const mo = S.el("div", { class: "zts-end-more", text: more }, root);
    S.enter(mo, { at: at + 1.1, dur: 0.9, from: { opacity: 0, y: 16, blur: 6 } });
  }
  if (note) {
    const n = S.el("div", { class: "zts-end-note", text: note }, root);
    S.enter(n, { at: at + 1.3, dur: 0.9, from: { opacity: 0, y: 16, blur: 6 } });
  }
  const u = until;
  if (u != null && isFinite(u)) S.exit(root, { at: u - 0.5, dur: 0.5, to: { opacity: 0, y: -20, blur: 8 } });
  return { el: root, url: pill };
}
