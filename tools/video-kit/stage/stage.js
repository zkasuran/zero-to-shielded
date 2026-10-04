// stage.js: the browser side of the video kit's `stage` segments.
//
// A stage page imports this module, registers scenes with Stage.scene(id, build) and the
// engine does the rest: it reads window.STAGE_INPUT (or URL params for a manual preview),
// builds the requested scene once, then renders any frame on demand through
// window.stageSeek(t). Every frame is a pure function of t: tweens, camera, cursor,
// typing, scrambles, video and iframe state are all computed from t alone, so frames can
// be captured in any order and in parallel pages. Real time never drives anything:
// CSS transitions are switched off and CSS/WAAPI animations are paused and seeked to t.
//
// Generic on purpose: no series colours or components here except the default caption
// look. Series styling lives in the episode library (episodes/stage/lib/).

const W = 1920;
const H = 1080;
const CX = W / 2;
const CY = H / 2;

// ---------------------------------------------------------------- math and easing

export const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
export const lerp = (a, b, p) => a + (b - a) * p;
export const smooth = (a, b, v) => {
  const p = clamp((v - a) / (b - a || 1e-9));
  return p * p * (3 - 2 * p);
};

const springK = 9.5;
const springNorm = 1 - (1 + springK) * Math.exp(-springK);

export const ease = {
  linear: (p) => p,
  inQuad: (p) => p * p,
  outQuad: (p) => 1 - (1 - p) * (1 - p),
  inCubic: (p) => p * p * p,
  outCubic: (p) => 1 - Math.pow(1 - p, 3),
  inOutCubic: (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
  outQuart: (p) => 1 - Math.pow(1 - p, 4),
  inOutQuart: (p) => (p < 0.5 ? 8 * p * p * p * p : 1 - Math.pow(-2 * p + 2, 4) / 2),
  outQuint: (p) => 1 - Math.pow(1 - p, 5),
  inOutQuint: (p) => (p < 0.5 ? 16 * Math.pow(p, 5) : 1 - Math.pow(-2 * p + 2, 5) / 2),
  inOutSine: (p) => -(Math.cos(Math.PI * p) - 1) / 2,
  outBack: (p) => {
    const c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2);
  },
  outExpo: (p) => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p)),
  inOutExpo: (p) =>
    p <= 0 ? 0 : p >= 1 ? 1 : p < 0.5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2,
  outElastic: (p) => {
    if (p <= 0) return 0;
    if (p >= 1) return 1;
    return Math.pow(2, -10 * p) * Math.sin((p * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1;
  },
  // critically damped spring, normalised so it lands exactly on 1 at p = 1
  spring: (p) => (p >= 1 ? 1 : (1 - (1 + springK * p) * Math.exp(-springK * p)) / springNorm),
};

export function easeFn(e) {
  if (typeof e === "function") return e;
  return ease[e] || ease.outCubic;
}

// ---------------------------------------------------------------- seeded randomness

// mulberry32: a small, fast seeded generator. Same seed, same sequence, every page.
export function rng(seed = 1) {
  let a = (Number(seed) >>> 0) || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// hash(...ints) -> [0, 1). Stateless, so it is safe to call from any frame in any order.
export function hash(...n) {
  let h = 2166136261 >>> 0;
  for (const v of n) {
    h ^= (Math.floor(v) | 0) >>> 0;
    h = Math.imul(h, 16777619) >>> 0;
    h ^= h >>> 13;
    h = Math.imul(h, 0x5bd1e995) >>> 0;
    h ^= h >>> 15;
  }
  return (h >>> 0) / 4294967296;
}

// ---------------------------------------------------------------- small helpers

const TRANSFORM_PROPS = ["x", "y", "scale", "scaleX", "scaleY", "rotate"];
const BASE = { opacity: 1, x: 0, y: 0, scale: 1, scaleX: 1, scaleY: 1, rotate: 0, blur: 0 };
const KNOWN = new Set(["opacity", "blur", ...TRANSFORM_PROPS]);

const num = (v, d = 3) => {
  const k = Math.pow(10, d);
  return Math.round(v * k) / k;
};

function raf2() {
  return new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(() => res())));
}

function timeout(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

function withTimeout(p, ms, label) {
  let id;
  const guard = new Promise((res) => {
    id = setTimeout(() => {
      console.warn(`[stage] ${label} timed out after ${ms} ms, continuing`);
      res();
    }, ms);
  });
  return Promise.race([Promise.resolve(p).finally(() => clearTimeout(id)), guard]);
}

// ---------------------------------------------------------------- keyed tracks

// keys([{at, dur, ease, ...values}], base) -> (t) => state
// The first key is the starting state (its dur is a move from `base` if given). Every
// later key moves from wherever the track is at that key's `at` to the key's values over
// `dur` seconds, so overlapping keys stay continuous. Values a key leaves out hold.
// `zoom` is interpolated in log space so zooms feel even.
export function track(list, base = {}) {
  const ks = (list || [])
    .map((k, i) => ({ ...k, at: Number(k.at) || 0, dur: Math.max(0, k.dur ?? 0.8), _i: i, _e: easeFn(k.ease || "inOutCubic") }))
    .sort((a, b) => a.at - b.at || a._i - b._i);
  const names = new Set(Object.keys(base));
  for (const k of ks) for (const n of Object.keys(k)) if (!["at", "dur", "ease", "_i", "_e"].includes(n) && typeof k[n] === "number") names.add(n);
  const starts = [];
  const mixv = (n, a, b, p) => (n === "zoom" && a > 0 && b > 0 ? Math.exp(lerp(Math.log(a), Math.log(b), p)) : lerp(a, b, p));
  const fill = (o, src) => {
    for (const n of names) if (typeof src[n] === "number") o[n] = src[n];
    return o;
  };
  // the first key is a static starting state; every later key is a move
  function startOf(k) {
    if (starts[k]) return starts[k];
    const s = k === 0 ? fill(fill({}, base), ks[0] || {}) : stateAt(ks[k].at, k - 1);
    starts[k] = s;
    return s;
  }
  function stateAt(t, upto) {
    let k = -1;
    for (let i = 0; i <= upto; i++) if (ks[i].at <= t) k = i;
    if (k <= 0) return ks.length ? { ...startOf(0) } : { ...base };
    const from = startOf(k);
    const key = ks[k];
    const p = key.dur > 0 ? key._e(clamp((t - key.at) / key.dur)) : 1;
    const out = {};
    for (const n of names) {
      const a = from[n];
      const b = typeof key[n] === "number" ? key[n] : a;
      out[n] = a === undefined ? b : mixv(n, a, b, p);
    }
    return out;
  }
  const fn = (t) => stateAt(t, ks.length - 1);
  fn.keys = ks;
  return fn;
}

// ---------------------------------------------------------------- captions

function splitPieces(words, maxChars) {
  // words: [{text, start, end}] -> [[word, ...], ...]. A small dynamic program picks the
  // breaks: pieces near an even length, at most maxChars (a few over costs a lot), ending
  // on a sentence or a comma where possible, never a short orphan.
  const n = words.length;
  const lens = words.map((w) => w.text.length);
  const total = lens.reduce((s, l) => s + l + 1, 0) - 1;
  if (total <= maxChars || n < 2) return [words];
  const target = total / Math.ceil(total / maxChars);
  const best = new Array(n + 1).fill(Infinity);
  const from = new Array(n + 1).fill(0);
  best[0] = 0;
  for (let i = 1; i <= n; i++) {
    let L = -1;
    for (let j = i - 1; j >= 0; j--) {
      L += lens[j] + 1;
      if (L > maxChars + 6 && i - j > 1) break;
      const last = words[i - 1].text;
      const next = i < n ? words[i].text.toLowerCase() : "";
      let c = 50;
      c += L < target ? Math.pow((target - L) / 7, 2) : Math.pow((L - target) / 9, 2);
      if (L > maxChars) c += (L - maxChars) * 25;
      if (i < n) {
        if (/[.!?]$/.test(last)) c += 0;
        else if (/[,;:]$/.test(last)) c += 18;
        else if (/^(and|or|but|then|so|if|when|because|before|after)$/.test(next)) c += 40;
        else c += 80;
        if (/^(the|a|an|to|of|in|on|at|for|your|my|is|and|or|with|from)$/i.test(last)) c += 60;
      }
      if (L < 14) c += 70;
      if (best[j] + c < best[i]) {
        best[i] = best[j] + c;
        from[i] = j;
      }
    }
  }
  const pieces = [];
  for (let i = n; i > 0; i = from[i]) pieces.unshift(words.slice(from[i], i));
  return pieces;
}

function wordsFor(cue) {
  if (cue._words) return cue._words;
  cue._words = computeWords(cue);
  return cue._words;
}

function computeWords(cue) {
  if (Array.isArray(cue.words) && cue.words.length) {
    // the kit sends [[start, end, text], ...]; {start, end, text} objects work too
    const ws = cue.words
      .map((w) => (Array.isArray(w) ? { start: Number(w[0]), end: Number(w[1]), text: String(w[2] ?? "") } : { start: Number(w.start), end: Number(w.end), text: String(w.text ?? "") }))
      .filter((w) => w.text.trim() && isFinite(w.start));
    if (ws.length) return ws;
  }
  // proportional timing by characters, punctuation adds a little pause weight
  const raw = String(cue.text || "").split(/\s+/).filter(Boolean);
  const weight = (w) => w.length + 1 + (/[.!?]$/.test(w) ? 3 : /[,;:]$/.test(w) ? 1.5 : 0);
  const sum = raw.reduce((s, w) => s + weight(w), 0) || 1;
  const span = Math.max(0.01, cue.end - cue.start);
  let acc = 0;
  return raw.map((w) => {
    const a = cue.start + (acc / sum) * span;
    acc += weight(w);
    const b = cue.start + (acc / sum) * span;
    return { text: w, start: a, end: b };
  });
}

// ---------------------------------------------------------------- the scene object

class Scene {
  constructor(input, host) {
    this.input = input;
    this.id = input.scene;
    this.seconds = Number(input.seconds) || 8;
    this.fps = Number(input.fps) || 30;
    this.params = input.params || {};
    this.offset = Number(input.offset) || 0;
    this.cues = (input.cues || []).map((c) => ({ ...c, start: Number(c.start), end: Number(c.end), text: String(c.text || "") }));
    this.t = 0;
    this.W = W;
    this.H = H;
    this.host = host;
    this._recs = new Map();
    this._order = 0;
    this._hooks = [];
    this._defer = [];
    this._layers = [];
    this._cam = null;

    this.viewport = host;
    this.root = this.layer(1, { cls: "stage-root", above: true });
    this.overlay = document.createElement("div");
    this.overlay.className = "stage-overlay";
    host.appendChild(this.overlay);
    this.top = document.createElement("div");
    this.top.className = "stage-top";
    host.appendChild(this.top);
  }

  // ----- cues
  cue(i) {
    const c = this._cueAt(i);
    return c ? c.start : 0;
  }
  cueEnd(i) {
    const c = this._cueAt(i);
    return c ? c.end : this.seconds;
  }
  // word(i, phrase, nth): start time of a word or phrase inside cue i, from the cue's word
  // timings when the kit supplies them, else the same proportional estimate the captions
  // use. Sync visuals to what is said: S.word(1, "Swap"). wordSpan() returns {start, end}.
  word(i, phrase, nth = 0) {
    return this.wordSpan(i, phrase, nth).start;
  }
  wordSpan(i, phrase, nth = 0) {
    const c = this._cueAt(i);
    if (!c) return { start: 0, end: 0 };
    const ws = wordsFor(c);
    const norm = (s) => String(s).toLowerCase().replace(/[^\p{L}\p{N}']/gu, "");
    const want = String(phrase).split(/\s+/).map(norm).filter(Boolean);
    let seen = 0;
    for (let k = 0; k + want.length <= ws.length; k++) {
      let ok = true;
      for (let j = 0; j < want.length; j++) if (norm(ws[k + j].text) !== want[j]) { ok = false; break; }
      if (ok && seen++ === nth) return { start: ws[k].start, end: ws[k + want.length - 1].end };
    }
    console.warn(`[stage] "${phrase}" not found in cue ${i}`);
    return { start: c.start, end: c.end };
  }

  track(keys, base) {
    return track(keys, base);
  }

  _cueAt(i) {
    const n = this.cues.length;
    if (!n) return null;
    let k = i < 0 ? n + i : i;
    if (k < 0 || k >= n) {
      console.warn(`[stage] cue ${i} does not exist (${n} cues), clamped`);
      k = clamp(k, 0, n - 1);
    }
    return this.cues[k];
  }

  // ----- DOM
  el(tag = "div", opts = {}, parent) {
    if (typeof opts === "string") opts = { class: opts };
    const isSvg = /^(svg|path|circle|rect|g|line|polyline|polygon|defs|linearGradient|radialGradient|stop|ellipse|text|use|clipPath|mask|filter)$/.test(tag);
    const e = isSvg ? document.createElementNS("http://www.w3.org/2000/svg", tag) : document.createElement(tag);
    if (opts.class) e.setAttribute("class", opts.class);
    if (opts.text != null) e.textContent = opts.text;
    if (opts.html != null) e.innerHTML = opts.html;
    if (opts.attrs) for (const [k, v] of Object.entries(opts.attrs)) e.setAttribute(k, v);
    if (opts.style) {
      if (typeof opts.style === "string") e.style.cssText += opts.style;
      else for (const [k, v] of Object.entries(opts.style)) k.startsWith("--") ? e.style.setProperty(k, v) : (e.style[k] = v);
    }
    if (opts.tf) {
      // a base transform (centring, for example) that tweens compose after
      e.dataset.tf = opts.tf;
      e.style.transform = opts.tf;
    }
    (parent === null ? null : parent || this.root)?.appendChild(e);
    return e;
  }

  // Scene-space rect of an element, measured at build time (before any frame transform).
  rectOf(el) {
    const r = el.getBoundingClientRect();
    const o = this.root.getBoundingClientRect();
    const z = o.width / W || 1;
    const x = (r.left - o.left) / z;
    const y = (r.top - o.top) / z;
    const w = r.width / z;
    const h = r.height / z;
    return { x, y, w, h, cx: x + w / 2, cy: y + h / 2, right: x + w, bottom: y + h };
  }

  // ----- tweens
  _rec(el) {
    let r = this._recs.get(el);
    if (!r) {
      r = { el, list: [], props: new Set(), byProp: null, last: {} };
      this._recs.set(el, r);
    }
    return r;
  }

  tween(el, spec = {}) {
    if (!el) return null;
    if (Array.isArray(el) || el instanceof NodeList) {
      return [...el].map((e, i) => this.tween(e, { ...spec, at: (spec.at || 0) + i * (spec.stagger || 0) }));
    }
    const r = this._rec(el);
    const tw = {
      at: Number(spec.at) || 0,
      dur: Math.max(0, spec.dur ?? 0.6),
      e: easeFn(spec.ease || "outCubic"),
      from: spec.from || {},
      to: spec.to || {},
      order: this._order++,
      cache: {},
    };
    r.list.push(tw);
    for (const k of Object.keys(tw.from)) r.props.add(k);
    for (const k of Object.keys(tw.to)) r.props.add(k);
    r.byProp = null;
    return tw;
  }

  // set(el, values, at = -Infinity): a hard cut to values at time `at`
  set(el, values, at = -1e9) {
    return this.tween(el, { at, dur: 0, to: values });
  }

  // enter: from `from` to the resting values (identity for transform props)
  enter(el, { at = 0, dur = 0.8, ease: e = "outExpo", from = { opacity: 0, y: 28, blur: 8 }, stagger = 0 } = {}) {
    const to = {};
    for (const k of Object.keys(from)) to[k] = k in BASE ? BASE[k] : 1;
    return this.tween(el, { at, dur, ease: e, from, to, stagger });
  }

  // exit: from wherever the element is at `at` to `to`
  exit(el, { at, dur = 0.45, ease: e = "inCubic", to = { opacity: 0, y: -18, blur: 6 }, stagger = 0 } = {}) {
    if (at == null || !isFinite(at)) return null;
    return this.tween(el, { at, dur, ease: e, to, stagger });
  }

  _index(r) {
    r.byProp = {};
    const sorted = [...r.list].sort((a, b) => a.at - b.at || a.order - b.order);
    for (const p of r.props) r.byProp[p] = sorted.filter((tw) => p in tw.from || p in tw.to);
  }

  _fromVal(list, k, p) {
    const tw = list[k];
    if (p in tw.from) return tw.from[p];
    if (p in tw.cache) return tw.cache[p];
    let v;
    if (k === 0) v = p in BASE ? BASE[p] : 0;
    else {
      const prev = list[k - 1];
      const a = this._fromVal(list, k - 1, p);
      const b = p in prev.to ? prev.to[p] : a;
      const q = prev.dur > 0 ? prev.e(clamp((tw.at - prev.at) / prev.dur)) : 1;
      v = a + (b - a) * q;
    }
    tw.cache[p] = v;
    return v;
  }

  // value of property p of element el at time t (pure)
  valueOf(el, p, t = this.t) {
    const r = this._recs.get(el);
    if (!r || !r.props.has(p)) return p in BASE ? BASE[p] : undefined;
    if (!r.byProp) this._index(r);
    return this._val(r, p, t);
  }

  _val(r, p, t) {
    const list = r.byProp[p];
    let k = -1;
    for (let i = 0; i < list.length; i++) {
      if (list[i].at <= t) k = i;
      else break;
    }
    if (k < 0) {
      const f = list[0];
      return p in f.from ? f.from[p] : p in BASE ? BASE[p] : 0;
    }
    const tw = list[k];
    const a = this._fromVal(list, k, p);
    const b = p in tw.to ? tw.to[p] : a;
    const q = tw.dur > 0 ? tw.e(clamp((t - tw.at) / tw.dur)) : 1;
    return a + (b - a) * q;
  }

  _applyTweens(t) {
    for (const r of this._recs.values()) {
      if (!r.byProp) this._index(r);
      const v = {};
      for (const p of r.props) v[p] = this._val(r, p, t);
      const st = r.el.style;
      const last = r.last;
      let hasTf = false;
      for (const p of TRANSFORM_PROPS) if (p in v) hasTf = true;
      if (hasTf) {
        const base = r.el.dataset.tf ? r.el.dataset.tf + " " : "";
        const x = v.x ?? 0, y = v.y ?? 0, rot = v.rotate ?? 0;
        const s = v.scale ?? 1;
        const sx = s * (v.scaleX ?? 1), sy = s * (v.scaleY ?? 1);
        let tf = base;
        if (x || y) tf += `translate(${num(x, 2)}px,${num(y, 2)}px) `;
        if (rot) tf += `rotate(${num(rot, 3)}deg) `;
        if (sx !== 1 || sy !== 1) tf += `scale(${num(sx, 4)},${num(sy, 4)})`;
        tf = tf.trim() || "none";
        if (last.tf !== tf) {
          st.transform = tf === "none" && !base ? "" : tf;
          last.tf = tf;
        }
      }
      if ("opacity" in v) {
        const o = String(num(clamp(v.opacity), 4));
        if (last.op !== o) {
          st.opacity = o;
          last.op = o;
        }
      }
      if ("blur" in v) {
        const b = Math.max(0, v.blur);
        const base = r.el.dataset.filter || "";
        const f = b > 0.05 ? `${base} blur(${num(b, 2)}px)`.trim() : base;
        if (last.f !== f) {
          st.filter = f;
          last.f = f;
        }
      }
      for (const p of r.props) {
        if (KNOWN.has(p)) continue;
        if (p.startsWith("--")) {
          const s = String(num(v[p], 4));
          if (last[p] !== s) {
            st.setProperty(p, s);
            last[p] = s;
          }
        }
      }
    }
  }

  // ----- per-frame hooks
  on(fn) {
    this._hooks.push(fn);
    return fn;
  }

  // ----- deferred work that stageReady waits for (async loads inside components)
  defer(p) {
    this._defer.push(Promise.resolve(p).catch((e) => console.warn("[stage] deferred task failed", e)));
    return p;
  }

  // ----- camera and depth layers
  camera(keys) {
    const ks = (keys || []).map((k) => this._camKey(k));
    this._cam = track(ks, { x: CX, y: CY, zoom: 1 });
    return this._cam;
  }

  _camKey(k) {
    const out = { ...k };
    let rect = k.fit || null;
    if (k.el) rect = this.rectOf(k.el);
    if (rect) {
      const pad = k.pad ?? 80;
      const zw = (W - 2 * pad) / Math.max(1, rect.w);
      const zh = (900 - 2 * pad) / Math.max(1, rect.h);
      const z = Math.min(k.maxZoom ?? 2.4, zw, zh);
      out.x = (rect.cx ?? rect.x + rect.w / 2) + (k.dx || 0);
      out.y = (rect.cy ?? rect.y + rect.h / 2) + (k.dy || 0);
      if (k.zoom == null) out.zoom = Math.max(k.minZoom ?? 1, z);
    }
    delete out.el;
    delete out.fit;
    return out;
  }

  camAt(t = this.t) {
    return this._cam ? this._cam(t) : { x: CX, y: CY, zoom: 1 };
  }

  // scene point -> screen point at time t for a layer of the given depth
  project(x, y, t = this.t, depth = 1) {
    const c = this.camAt(t);
    const z = 1 + (c.zoom - 1) * depth;
    const cx = CX + (c.x - CX) * depth;
    const cy = CY + (c.y - CY) * depth;
    return { x: CX + (x - cx) * z, y: CY + (y - cy) * z, zoom: z };
  }

  // layer(depth): a 1920x1080 layer that follows the camera by `depth` (0 = fixed, 1 = full
  // camera). Use 0.1 to 0.4 for parallax backgrounds, > 1 for near foreground.
  layer(depth = 0.25, { cls = "", above = false, bleed = 0 } = {}) {
    const d = document.createElement("div");
    d.className = `stage-layer ${cls}`.trim();
    if (bleed) {
      // oversized so zoom outs and pans never show an edge; origin stays at the viewport corner
      Object.assign(d.style, { left: `${-bleed}px`, top: `${-bleed}px`, width: `${W + 2 * bleed}px`, height: `${H + 2 * bleed}px`, transformOrigin: `${bleed}px ${bleed}px` });
    }
    d._depth = depth;
    if (above || !this.root) this.host.insertBefore(d, this.overlay || null);
    else this.host.insertBefore(d, this.root);
    this._layers.push(d);
    return d;
  }

  _applyCamera(t) {
    const c = this.camAt(t);
    for (const l of this._layers) {
      const d = l._depth;
      const z = 1 + (c.zoom - 1) * d;
      const x = CX + (c.x - CX) * d;
      const y = CY + (c.y - CY) * d;
      const tf =
        Math.abs(z - 1) < 1e-5 && Math.abs(x - CX) < 1e-3 && Math.abs(y - CY) < 1e-3
          ? ""
          : `translate(${num(CX, 2)}px,${num(CY, 2)}px) scale(${num(z, 5)}) translate(${num(-x, 2)}px,${num(-y, 2)}px)`;
      if (l._tf !== tf) {
        l.style.transform = tf;
        l._tf = tf;
      }
    }
  }

  // ----- cursor
  // points: [{at, x, y, click, dur, ease, arc}] in scene px (or {el} for an element centre).
  // opts: {hide, size, trail}. The cursor lives in the overlay, so it keeps its size when
  // the camera zooms (it grows a little, like a recording). Its position follows the
  // camera projection of the scene point.
  cursor(points, opts = {}) {
    const size = opts.size ?? 1;
    const pts = (points || [])
      .map((p) => {
        const q = { ...p };
        if (p.el) {
          const r = this.rectOf(p.el);
          q.x = r.x + r.w * (p.ax ?? 0.5) + (p.dx || 0);
          q.y = r.y + r.h * (p.ay ?? 0.5) + (p.dy || 0);
        }
        return q;
      })
      .sort((a, b) => a.at - b.at);
    if (!pts.length) return null;
    const svg = `<svg viewBox="-3 -3 30 38" width="${36 * size}" height="${45.6 * size}" aria-hidden="true"><path d="M1 1 L1 25.5 L7 19.8 L11.2 29.4 L15.6 27.5 L11.5 18.2 L19.4 18.2 Z" fill="#101114" stroke="#ffffff" stroke-width="2.1" stroke-linejoin="round"/></svg>`;
    const tip = 4.8 * size; // the arrow tip sits on the point
    const mk = (cls) => {
      const d = this.el("div", { class: `stage-cursor ${cls}`, html: svg }, this.overlay);
      d.style.transformOrigin = "0 0";
      d.firstChild.style.transform = `translate(${-tip}px,${-tip}px)`;
      return d;
    };
    const ghosts = opts.trail === false ? [] : [mk("is-ghost"), mk("is-ghost"), mk("is-ghost")];
    const cur = mk("is-main");
    const clicks = pts.filter((p) => p.click);
    const ripples = clicks.map(() => this.el("div", { class: "stage-ripple" }, this.overlay));
    const hide = opts.hide ?? null;

    const posAt = (t) => {
      // returns scene point at t
      if (t <= pts[0].at) return { x: pts[0].x, y: pts[0].y };
      for (let i = 1; i < pts.length; i++) {
        const a = pts[i - 1], b = pts[i];
        if (t >= b.at) continue;
        const gap = b.at - a.at;
        const dur = b.dur ?? clamp(gap * 0.82, 0.25, 1.1);
        const leave = Math.max(a.at + (a.click ? 0.14 : 0), b.at - dur);
        if (t <= leave) return { x: a.x, y: a.y };
        const p = easeFn(b.ease || "inOutCubic")(clamp((t - leave) / Math.max(0.01, b.at - leave)));
        // a gentle arc: control point pushed sideways from the midpoint
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        const dx = b.x - a.x, dy = b.y - a.y;
        const arc = b.arc ?? 0.12;
        const qx = mx - dy * arc, qy = my + dx * arc;
        const u = 1 - p;
        return { x: u * u * a.x + 2 * u * p * qx + p * p * b.x, y: u * u * a.y + 2 * u * p * qy + p * p * b.y };
      }
      const z = pts[pts.length - 1];
      return { x: z.x, y: z.y };
    };

    this.on((t) => {
      const appear = smooth(pts[0].at - 0.05, pts[0].at + 0.25, t);
      const gone = hide != null ? 1 - smooth(hide, hide + 0.3, t) : 1;
      const vis = appear * gone;
      // press: dip on each click
      let press = 0;
      for (const c of clicks) {
        const d = t - c.at;
        if (d > -0.08 && d < 0.3) press = Math.max(press, d < 0 ? (d + 0.08) / 0.08 : 1 - smooth(0.04, 0.3, d));
      }
      const s = this.project(0, 0, t);
      const grow = 1 + (s.zoom - 1) * 0.35;
      const scale = grow * (1 - 0.16 * press) * lerp(0.85, 1, appear);
      const p = posAt(t);
      const sp = this.project(p.x, p.y, t);
      const set = (node, x, y, o, sc) => {
        const tf = `translate(${num(x, 2)}px,${num(y, 2)}px) scale(${num(sc, 4)})`;
        if (node._tf !== tf) { node.style.transform = tf; node._tf = tf; }
        const os = String(num(o, 3));
        if (node._o !== os) { node.style.opacity = os; node._o = os; }
      };
      set(cur, sp.x, sp.y, vis, scale);
      // motion trail: ghosts where the cursor was a few milliseconds ago, only when fast
      const dt = 1 / 60;
      ghosts.forEach((g, i) => {
        const q = posAt(t - dt * (i + 1) * 1.4);
        const gp = this.project(q.x, q.y, t);
        const speed = Math.hypot(gp.x - sp.x, gp.y - sp.y) / (dt * (i + 1) * 1.4);
        const k = clamp((speed - 500) / 2600) * 0.32 * (1 - i / 3.4);
        set(g, gp.x, gp.y, vis * k, scale);
      });
      clicks.forEach((c, i) => {
        const d = t - c.at;
        const r = ripples[i];
        const on = d >= 0 && d < 0.7;
        const q = this.project(c.x, c.y, t);
        const pr = on ? ease.outCubic(clamp(d / 0.7)) : 0;
        set(r, q.x, q.y, on ? (1 - pr) * 0.9 : 0, (0.25 + pr * 1.35) * grow);
      });
    });
    return { el: cur, at: posAt, points: pts };
  }

  // ----- typing (chars shown is a pure function of t)
  type(el, text, opts = {}) {
    const at = opts.at ?? 0;
    const cps = opts.cps ?? 22;
    const seed = opts.seed ?? 7;
    const str = String(text);
    const times = [];
    let acc = 0;
    for (let i = 0; i < str.length; i++) {
      const ch = str[i];
      let d = (1 / cps) * (0.62 + 0.76 * hash(seed, i));
      if (ch === " ") d *= 1.25;
      if (/[.,!?]/.test(str[i - 1] || "")) d *= 2.2;
      acc += opts.jitter === false ? 1 / cps : d;
      times.push(at + acc);
    }
    const isInput = el.tagName === "INPUT" || el.tagName === "TEXTAREA";
    let textNode = null, caret = null;
    if (!isInput) {
      el.textContent = "";
      textNode = document.createTextNode("");
      el.appendChild(textNode);
      if (opts.caret !== false) {
        caret = document.createElement("span");
        caret.className = "stage-caret";
        el.appendChild(caret);
      }
    } else {
      el.style.caretColor = "transparent";
    }
    let last = null;
    this.on((t) => {
      let n = 0;
      while (n < times.length && times[n] <= t) n++;
      const v = str.slice(0, n);
      if (v !== last) {
        if (isInput) {
          el.value = v;
          if (opts.events) el.dispatchEvent(new Event("input", { bubbles: true }));
        } else textNode.data = v;
        last = v;
      }
      if (caret) {
        const typing = t >= at && n < times.length;
        const end = opts.until ?? Infinity;
        const blink = typing ? 1 : (Math.floor((t - at) / 0.53) % 2 === 0 ? 1 : 0);
        const o = t < at - 0.4 || t > end ? 0 : blink;
        const os = String(o);
        if (caret._o !== os) { caret.style.opacity = os; caret._o = os; }
      }
    });
    return { done: times[times.length - 1] ?? at };
  }

  // ----- deterministic glyph scramble
  // mode "decrypt": glyphs before `at`, letters lock in between at and until, text after.
  // mode "encrypt": text before `at`, glyphs take over until `until`, glyphs after.
  // mode "noise":  glyphs forever, never resolves.
  scramble(el, opts = {}) {
    const text = String(opts.text ?? el.textContent ?? "");
    const at = opts.at ?? 0;
    const until = opts.until ?? at + 1.2;
    const seed = opts.seed ?? 11;
    const rate = opts.rate ?? 16;
    const mode = opts.mode || "decrypt";
    const glyphs = opts.glyphs || "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghkmnpqrstuvwxyz0123456789#%&*+=?<>/~";
    const keep = opts.keepSpaces !== false;
    const order = text.split("").map((_, i) => (opts.order === "random" ? hash(seed, i, 99) : i / Math.max(1, text.length - 1)));
    const spans = !!opts.spans;
    let nodes = null;
    if (spans) {
      el.textContent = "";
      nodes = text.split("").map(() => {
        const s = document.createElement("span");
        el.appendChild(s);
        return s;
      });
    }
    let last = null;
    const glyph = (i, t) => {
      const step = Math.floor(t * rate + hash(seed, i, 5) * 3);
      return glyphs[Math.floor(hash(seed, i, step) * glyphs.length)];
    };
    this.on((t) => {
      let out = "";
      const flags = [];
      for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        if (keep && ch === " ") { out += " "; flags.push(0); continue; }
        const lock = lerp(at, until, order[i]);
        let plain;
        if (mode === "noise") plain = false;
        else if (mode === "encrypt") plain = t < lock;
        else plain = t >= lock;
        out += plain ? ch : glyph(i, t);
        flags.push(plain ? 0 : 1);
      }
      if (out === last) return;
      last = out;
      if (!spans) el.textContent = out;
      else nodes.forEach((s, i) => {
        if (s.textContent !== out[i]) s.textContent = out[i];
        const g = flags[i] === 1;
        if (s._g !== g) { s.classList.toggle("is-glyph", g); s._g = g; }
      });
    });
    return el;
  }

  // ----- footage
  video(el, opts = {}) {
    const at = opts.at ?? 0;
    const from = opts.from ?? 0;
    el.muted = true;
    el.playsInline = true;
    el.preload = "auto";
    el.pause();
    const ready = new Promise((res) => {
      if (el.readyState >= 2) return res();
      el.addEventListener("loadeddata", () => res(), { once: true });
      el.addEventListener("error", () => res(), { once: true });
    });
    this.defer(withTimeout(ready, 15000, "video load"));
    this.on((t) => {
      const end = opts.to ?? (isFinite(el.duration) ? el.duration : from + 1e6);
      const target = clamp(from + (t - at), from, Math.max(from, end - 0.001));
      if (Math.abs(el.currentTime - target) < 0.0005 && !el.seeking) return null;
      return withTimeout(
        new Promise((res) => {
          el.addEventListener("seeked", () => res(), { once: true });
          el.currentTime = target;
        }),
        5000,
        "video seek",
      );
    });
    return el;
  }

  // ----- a same-origin iframe (the real companion site)
  site(iframe, opts = {}) {
    const S = this;
    const h = {
      iframe,
      get win() { return iframe.contentWindow; },
      get doc() { return iframe.contentDocument; },
      _scroll: null,
      _reveals: [],
      _box: null,
      ready: null,
    };
    h.ready = withTimeout(
      new Promise((res) => {
        const done = async () => {
          try {
            const d = iframe.contentDocument;
            if (d && d.fonts) await withTimeout(d.fonts.ready, 6000, "iframe fonts");
            // kill real-time motion inside the page too. A constructed sheet, because the
            // site's CSP (style-src 'self') refuses an injected <style>.
            const css = "*,*::before,*::after{transition:none!important;caret-color:transparent!important;scroll-behavior:auto!important}";
            try {
              const sheet = new iframe.contentWindow.CSSStyleSheet();
              sheet.replaceSync(css);
              d.adoptedStyleSheets = [...d.adoptedStyleSheets, sheet];
            } catch (e) {
              console.warn("[stage] could not freeze iframe transitions", e);
            }
            h.box();
          } catch (e) {
            console.warn("[stage] iframe is not same-origin or failed to load", e);
          }
          res();
        };
        const loaded = () => {
          try {
            const d = iframe.contentDocument;
            return d && d.readyState === "complete" && d.location.href !== "about:blank";
          } catch {
            return false;
          }
        };
        if (loaded()) done();
        else iframe.addEventListener("load", () => done(), { once: true });
      }),
      opts.timeout ?? 15000,
      "iframe load",
    );
    this.defer(h.ready);

    // box: where the iframe viewport sits in scene px and its scale (measured lazily)
    h.box = () => {
      if (h._box) return h._box;
      const r = S.rectOf(iframe);
      const s = r.w / (iframe.offsetWidth || r.w);
      h._box = { x: r.x, y: r.y, s };
      return h._box;
    };
    h.docTop = (sel) => {
      const el = typeof sel === "string" ? h.doc.querySelector(sel) : sel;
      if (!el) return 0;
      return el.getBoundingClientRect().top + h.win.scrollY;
    };
    // scroll([{at, y} | {at, to: selector, offset}, ...]) pure in t
    h.scroll = (keys) => {
      const ks = keys.map((k) => {
        const q = { ...k };
        if (k.to != null) q.y = h.docTop(k.to) + (k.offset || 0);
        delete q.to;
        return q;
      });
      h._scroll = track(ks, { y: 0 });
      return h;
    };
    h.scrollAt = (t) => (h._scroll ? Math.max(0, h._scroll(t).y) : 0);
    // reveal(k | [{at, k}], scope): setReveal(k, scope) as a step function of t
    h.reveal = (keys, scope) => {
      const ks = typeof keys === "number" ? [{ at: -1e9, k: keys }] : [...keys].sort((a, b) => a.at - b.at);
      h._reveals.push({ ks, scope });
      return h;
    };
    h.rect = (sel, { at = S.t } = {}) => {
      const el = typeof sel === "string" ? h.doc.querySelector(sel) : sel;
      if (!el) {
        console.warn(`[stage] site.rect: ${sel} not found`);
        return { x: 0, y: 0, w: 0, h: 0, cx: 0, cy: 0 };
      }
      const r = el.getBoundingClientRect();
      const sy = h.win.scrollY;
      const b = h.box();
      const top = r.top + sy - h.scrollAt(at);
      const x = b.x + r.left * b.s;
      const y = b.y + top * b.s;
      const w = r.width * b.s;
      const hh = r.height * b.s;
      return { x, y, w, h: hh, cx: x + w / 2, cy: y + hh / 2, right: x + w, bottom: y + hh };
    };
    h.point = (sel, { at = S.t, ax = 0.5, ay = 0.5, dx = 0, dy = 0 } = {}) => {
      const r = h.rect(sel, { at });
      return { x: r.x + r.w * ax + dx, y: r.y + r.h * ay + dy };
    };
    const lastK = new Map();
    let lastZ = null;
    this.on((t) => {
      const win = h.win;
      if (!win) return;
      // Chromium keeps a composited layer's first raster scale once its scale starts to
      // change outside an animation, so after a zoom the page would look sharper or softer
      // depending on which frames were seeked before. Rebuilding the iframe's layers when
      // the camera zoom changes makes every frame raster as if it were the first.
      const z = Math.round(this.camAt(t).zoom * 1e4);
      if (lastZ !== null && z !== lastZ && opts.reraster !== false) {
        iframe.style.display = "none";
        void iframe.offsetWidth;
        iframe.style.display = "";
        void iframe.offsetWidth;
      }
      lastZ = z;
      if (h._scroll) {
        const y = Math.round(h.scrollAt(t));
        if (Math.round(win.scrollY) !== y) win.scrollTo({ top: y, left: 0, behavior: "instant" });
      }
      for (const rv of h._reveals) {
        let k = rv.ks[0].k;
        for (const key of rv.ks) if (key.at <= t) k = key.k;
        const id = rv.scope || "*";
        if (lastK.get(id) !== k && typeof win.setReveal === "function") {
          win.setReveal(k, rv.scope);
          lastK.set(id, k);
        }
      }
      // CSS or WAAPI animations inside the page follow t as well
      try {
        for (const a of h.doc.getAnimations()) {
          a.pause();
          a.currentTime = t * 1000;
        }
      } catch { /* not same origin */ }
    });
    return h;
  }

  // ----- captions inside the frame
  captions(opts = {}) {
    const maxChars = opts.maxChars ?? 52;
    const fade = opts.fade ?? 0.14;
    const box = this.el("div", { class: "stage-captions" }, this.top);
    if (opts.y != null) box.style.top = `${opts.y}px`;
    const pill = this.el("div", { class: "stage-caption" }, box);
    if (opts.size) pill.style.fontSize = `${opts.size}px`;
    if (opts.color) pill.style.color = opts.color;
    if (opts.highlight) pill.style.setProperty("--stage-hl", opts.highlight);
    const plan = this.cues.map((c) => {
      const words = wordsFor(c);
      const pieces = splitPieces(words, maxChars).map((ws) => ({ words: ws, start: ws[0].start }));
      pieces.forEach((p, i) => {
        p.start = i === 0 ? c.start : p.start;
        p.end = i + 1 < pieces.length ? pieces[i + 1].words[0].start : c.end;
      });
      return { cue: c, pieces };
    });
    let shown = null;
    let spans = [];
    let lastNow = -2;
    this.on((t) => {
      const cur = plan.find((p) => t >= p.cue.start && t < p.cue.end);
      if (!cur) {
        if (box._o !== "0") { box.style.opacity = "0"; box._o = "0"; }
        return;
      }
      let piece = cur.pieces[0];
      for (const p of cur.pieces) if (t >= p.start) piece = p;
      if (shown !== piece) {
        pill.textContent = "";
        spans = piece.words.map((w, i) => {
          const s = document.createElement("span");
          s.className = "stage-w";
          s.textContent = w.text;
          pill.appendChild(s);
          if (i < piece.words.length - 1) pill.appendChild(document.createTextNode(" "));
          return s;
        });
        shown = piece;
        lastNow = -2;
      }
      let now = -1;
      piece.words.forEach((w, i) => { if (t >= w.start) now = i; });
      if (now >= 0 && t >= piece.words[now].end && now === piece.words.length - 1 && t > piece.words[now].end + 0.25) now = -1;
      if (now !== lastNow) {
        spans.forEach((s, i) => s.classList.toggle("is-now", i === now));
        lastNow = now;
      }
      // opacity only. No backdrop-filter on the pill either: Chromium's backdrop blur over
      // a changing page depended on the frames seeked before (measured), so it is not pure
      const o = Math.min(1, (t - cur.cue.start) / fade, (cur.cue.end - t) / fade);
      const os = String(num(clamp(o), 3));
      if (box._o !== os) {
        box.style.opacity = os;
        box._o = os;
      }
    });
    return box;
  }

  // ----- the frame
  async _render(t) {
    this.t = t;
    this._applyTweens(t);
    this._applyCamera(t);
    const waits = [];
    for (const fn of this._hooks) {
      const r = fn(t, this);
      if (r && typeof r.then === "function") waits.push(r);
    }
    // CSS and WAAPI animations on the stage page follow t (as if started at t = 0)
    for (const a of document.getAnimations()) {
      try {
        a.pause();
        a.currentTime = t * 1000;
      } catch { /* ignore */ }
    }
    if (waits.length) await Promise.all(waits);
  }
}

// ---------------------------------------------------------------- boot

const scenes = new Map();
let current = null;
let booted = null;
let queue = Promise.resolve();
let resolveReady, rejectReady;

const readyPromise = new Promise((res, rej) => {
  resolveReady = res;
  rejectReady = rej;
});
readyPromise.catch(() => {});
window.stageReady = readyPromise;

const BASE_CSS = `
html.stage-page, html.stage-page body { margin: 0; padding: 0; background: #000; overflow: hidden; }
html.stage-page *, html.stage-page *::before, html.stage-page *::after { transition: none !important; }
#stage { position: absolute; left: 0; top: 0; width: ${W}px; height: ${H}px; overflow: hidden; transform-origin: 0 0; contain: strict; }
.stage-layer { position: absolute; left: 0; top: 0; width: ${W}px; height: ${H}px; transform-origin: 0 0; }
.stage-root { overflow: visible; }
.stage-overlay, .stage-top { position: absolute; inset: 0; pointer-events: none; }
.stage-cursor { position: absolute; left: 0; top: 0; width: 0; height: 0; opacity: 0; z-index: 30; }
.stage-cursor svg { display: block; overflow: visible; filter: drop-shadow(0 6px 9px rgba(0,0,0,.42)) drop-shadow(0 1px 1.5px rgba(0,0,0,.5)); }
.stage-cursor.is-ghost svg { filter: none; }
.stage-ripple { position: absolute; left: 0; top: 0; width: 0; height: 0; opacity: 0; z-index: 29; }
.stage-ripple::before { content: ""; position: absolute; left: -46px; top: -46px; width: 92px; height: 92px; border-radius: 50%;
  border: 3px solid var(--stage-ripple, #F4B728); background: radial-gradient(circle, rgba(244,183,40,.28), rgba(244,183,40,0) 70%); box-sizing: border-box; }
.stage-caret { display: inline-block; width: .08em; height: 1em; margin-left: .04em; vertical-align: -0.12em; background: currentColor; border-radius: 2px; }
.stage-captions { position: absolute; left: 0; right: 0; top: 941px; height: 108px; display: flex; align-items: center; justify-content: center; opacity: 0; z-index: 50; }
.stage-caption { max-width: 1560px; padding: 11px 30px 13px; border-radius: 22px; text-align: center;
  font: 600 44px/1.22 "Inter", system-ui, sans-serif; letter-spacing: -0.012em; color: var(--stage-cap, #F5F1E6);
  background: rgba(9, 12, 22, .8);
  box-shadow: 0 0 0 1px rgba(245,241,230,.07), 0 0 34px 6px rgba(4,6,12,.4), 0 12px 32px -10px rgba(0,0,0,.55);
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; text-wrap: balance; }
.stage-w.is-now { color: var(--stage-hl, #F4B728); }
.stage-error { position: absolute; inset: 0; display: grid; place-items: center; color: #ffb4b4; font: 600 32px/1.4 system-ui; padding: 120px; text-align: center; white-space: pre-wrap; }
`;

function readInput() {
  if (window.STAGE_INPUT && typeof window.STAGE_INPUT === "object") return { ...window.STAGE_INPUT, preview: false };
  const q = new URLSearchParams(location.search);
  const id = q.get("scene") || [...scenes.keys()][0];
  const meta = scenes.get(id)?.meta || {};
  const seconds = Number(q.get("seconds")) || meta.seconds || 8;
  const texts = meta.narration || [];
  const n = q.has("cues") ? Math.max(0, Number(q.get("cues")) || 0) : texts.length || 2;
  const L = n ? seconds / n : seconds;
  const cues = [];
  for (let i = 0; i < n; i++) {
    cues.push({ start: num(i * L + 0.2, 3), end: num((i + 1) * L - 0.2, 3), text: texts[i] || `Cue ${i + 1} of ${n}, sample caption text for the preview` });
  }
  let params = meta.params || {};
  try { if (q.get("params")) params = { ...params, ...JSON.parse(q.get("params")) }; } catch { /* ignore */ }
  return { scene: id, seconds, fps: Number(q.get("fps")) || 30, cues, params, offset: Number(q.get("offset")) || 0, preview: true };
}

async function loadFonts() {
  if (!document.fonts) return;
  const faces = [...document.fonts];
  await Promise.all(faces.map((f) => f.load().catch(() => null)));
  await document.fonts.ready;
}

const pageWaits = [];

async function boot() {
  if (booted) return booted;
  booted = (async () => {
    const st = document.createElement("style");
    st.textContent = BASE_CSS;
    document.head.prepend(st);
    document.documentElement.classList.add("stage-page");
    await withTimeout(Promise.all(pageWaits), 10000, "page waits");
    const input = readInput();
    let host = document.getElementById("stage");
    if (!host) {
      host = document.createElement("div");
      host.id = "stage";
      document.body.appendChild(host);
    }
    host.innerHTML = "";
    const entry = scenes.get(input.scene);
    if (!entry) {
      const msg = `stage: scene "${input.scene}" is not registered. Known: ${[...scenes.keys()].join(", ")}`;
      host.innerHTML = `<div class="stage-error"></div>`;
      host.firstChild.textContent = msg;
      throw new Error(msg);
    }
    await withTimeout(loadFonts(), 8000, "fonts");
    const S = new Scene(input, host);
    current = S;
    Stage.S = S;
    await entry.build(S);
    await Promise.all(S._defer);
    await withTimeout(loadFonts(), 8000, "fonts");
    // images still decoding
    await Promise.all([...host.querySelectorAll("img")].map((im) => (im.decode ? im.decode().catch(() => null) : null)));
    await S._render(0);
    await raf2();
    if (input.preview) previewMode(S);
    return S;
  })();
  booted.then(() => resolveReady(true), (e) => { console.error(e); rejectReady(e); });
  return booted;
}

async function seek(t) {
  const S = await booted;
  if (document.fonts) await document.fonts.ready;
  const tt = clamp(Number(t) || 0, 0, S.seconds);
  await S._render(tt);
  await raf2();
  return tt;
}

window.stageSeek = (t) => {
  const p = queue.then(() => seek(t));
  queue = p.catch(() => {});
  return p;
};

// Manual preview: fit the 1920x1080 stage into the window, ?t=2.5 shows one frame,
// ?play=1 loops in real time (preview only; capture never uses wall clock time).
function previewMode(S) {
  const host = S.host;
  const fit = () => {
    const k = Math.min(innerWidth / W, innerHeight / H);
    host.style.transform = k < 1 ? `scale(${k})` : "";
  };
  fit();
  addEventListener("resize", fit);
  const q = new URLSearchParams(location.search);
  if (q.has("t")) window.stageSeek(Number(q.get("t")) || 0);
  if (q.get("play") === "1") {
    const t0 = performance.now();
    const loop = async () => {
      const t = ((performance.now() - t0) / 1000) % S.seconds;
      await window.stageSeek(t);
      document.title = `${S.id} ${t.toFixed(2)}s`;
      requestAnimationFrame(loop);
    };
    loop();
  }
}

export const Stage = {
  S: null,
  // scene(id, build, meta): build(S) may be async. meta.narration and meta.seconds feed the
  // manual preview when there is no STAGE_INPUT.
  scene(id, build, meta = {}) {
    scenes.set(id, { build, meta });
    return Stage;
  },
  scenes: () => [...scenes.keys()],
  // wait(promise): boot waits for it before building (a stylesheet a library injects, say)
  wait(p) {
    pageWaits.push(Promise.resolve(p).catch(() => null));
    return p;
  },
  boot,
  ease,
  track,
  rng,
  hash,
  clamp,
  lerp,
  smooth,
};

// Boot after every module on the page has registered its scenes.
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => setTimeout(boot, 0), { once: true });
} else {
  setTimeout(boot, 0);
}

export default Stage;
