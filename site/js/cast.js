// cast.js: the cast of Zero to Shielded as SVG strings.
//
//   Maya         the learner (the viewer's stand-in). She pays. Gold accent.
//   Sam          her friend. He gets paid. Cool blue accent.
//   The Watcher  anyone looking at the public blockchain: a curious lens-eyed figure on
//                a short tower of blocks. Not a villain.
//
//   maya(opts) / sam(opts) / watcher(opts) -> "<svg ...>...</svg>"
//   opts = { size = 160, theme = "auto", label = false, pose = "stand", mood, id, lens }
//
// No dependencies and no DOM, so the same file runs in the site build (node) and in the
// browser. No style attributes and no <style>: presentation attributes only, because the
// site CSP forbids inline styles. Parts the stage animates are <g> elements with stable
// classes and a data-origin="x y" pivot in viewBox units (see CAST.classes). Pose tilts
// live on inner groups, so a transform the stage sets on a classed group never fights
// the drawing. Arms are named by picture side: cast-arm-l is the arm on the left of the
// picture (the character's own right arm).

const POSES = ["stand", "wave", "phone", "cheer", "point", "think", "write", "receive"];
const MOODS = ["neutral", "happy", "surprised", "thinking"];
const LENSES = ["none", "read", "scramble"];
const THEMES = ["dark", "light", "auto"];

const GOLD = "#F4B728";
const BLUE = "#7AA2FF";
const CREAM = "#F5F1E6";
const PAPER = "#FBF8F1";
const INK = "#141826";

// ---------- tiny SVG writer ----------

const r2 = (v) => Math.round(v * 100) / 100;
const pt = (p) => `${r2(p[0])} ${r2(p[1])}`;

function attrs(o) {
  let s = "";
  for (const k of Object.keys(o)) {
    const v = o[k];
    if (v === undefined || v === null || v === false || v === "") continue;
    s += ` ${k}="${typeof v === "number" ? r2(v) : v}"`;
  }
  return s;
}
const tag = (name, o, inner) => (inner === undefined ? `<${name}${attrs(o)}/>` : `<${name}${attrs(o)}>${inner}</${name}>`);
const g = (o, inner) => tag("g", o, inner);
const part = (cls, origin, inner) => tag("g", { class: cls, "data-origin": origin ? pt(origin) : undefined }, inner);
const path = (d, fill, extra) => tag("path", { d, fill, ...extra });
const ink = (d, stroke, width, extra) => tag("path", { d, fill: "none", stroke, "stroke-width": width, "stroke-linecap": "round", "stroke-linejoin": "round", ...extra });
const ell = (cx, cy, rx, ry, fill, extra) => tag("ellipse", { cx, cy, rx, ry, fill, ...extra });
const dot = (cx, cy, r, fill, extra) => tag("circle", { cx, cy, r, fill, ...extra });
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const MIRROR = "matrix(-1 0 0 1 200 0)"; // people are symmetric around x = 100

// quadratic curve helpers for limbs: a limb is shoulder S, bend C, wrist W
const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
const qAt = (a, c, b, t) => lerp(lerp(a, c, t), lerp(c, b, t), t);
function qSub(a, c, b, t0, t1) {
  const k0 = (1 - t0) * (1 - t1), k1 = (1 - t0) * t1 + t0 * (1 - t1), k2 = t0 * t1;
  const m = [k0 * a[0] + k1 * c[0] + k2 * b[0], k0 * a[1] + k1 * c[1] + k2 * b[1]];
  return `M${pt(qAt(a, c, b, t0))}Q${pt(m)} ${pt(qAt(a, c, b, t1))}`;
}
// rotation (degrees) that turns local +y toward the direction from -> to
const aim = (from, to) => (Math.atan2(-(to[0] - from[0]), to[1] - from[1]) * 180) / Math.PI;

// ---------- options ----------

let counter = 0;

function options(name, opts) {
  const o = opts && typeof opts === "object" ? opts : {};
  const size = Number.isFinite(Number(o.size)) && Number(o.size) > 0 ? Number(o.size) : 160;
  const pose = POSES.includes(o.pose) ? o.pose : "stand";
  const mood = MOODS.includes(o.mood) ? o.mood : pose === "cheer" ? "happy" : pose === "think" ? "thinking" : "neutral";
  const raw = o.id !== undefined && o.id !== null && String(o.id).trim() ? String(o.id).trim() : `zts-${name}-${++counter}`;
  return {
    size,
    theme: THEMES.includes(o.theme) ? o.theme : "auto",
    label: o.label,
    pose,
    mood,
    lens: LENSES.includes(o.lens) ? o.lens : "none",
    id: raw.replace(/[^A-Za-z0-9_-]/g, "-").replace(/^(?![A-Za-z])/, "c"),
    fine: size >= 80, // small renders drop hairline details and get bolder faces
  };
}

// What changes per theme. "auto" reads on both the ink field and cream: a faint light
// rim behind dark hair (invisible on cream) and a mid ground shadow.
function look(theme) {
  if (theme === "dark") return { shadow: "#02040A", shadowOp: 0.5, rim: "#FFF3D6", rimOp: 0.2, glow: 0.62 };
  if (theme === "light") return { shadow: "#2B2440", shadowOp: 0.13, rim: null, rimOp: 0, glow: 0.42 };
  return { shadow: "#090C18", shadowOp: 0.26, rim: "#FFF3D6", rimOp: 0.13, glow: 0.52 };
}

const POSE_WORDS = {
  stand: "", wave: "waving", phone: "holding up a phone", cheer: "cheering", point: "pointing",
  think: "thinking", write: "writing on paper", receive: "holding out both hands",
};

function svg(name, vb, o, defs, body) {
  const [w, h] = vb;
  let named = "";
  if (o.label) {
    named = typeof o.label === "string" ? o.label : CAST[name].name + (POSE_WORDS[o.pose] && !(name === "watcher" && o.pose === "phone") ? `, ${POSE_WORDS[o.pose]}` : "");
  }
  const a = {
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: `0 0 ${w} ${h}`,
    width: r2((o.size * w) / h),
    height: r2(o.size),
    class: `cast-figure cast-figure--${name}`,
    "data-cast": name,
    "data-pose": o.pose,
    "data-mood": o.mood,
    "data-theme": o.theme,
    "data-lens": name === "watcher" ? o.lens : undefined,
    role: named ? "img" : undefined,
    "aria-labelledby": named ? `${o.id}-title` : undefined,
  };
  const title = named ? `<title id="${o.id}-title">${esc(named)}</title>` : "";
  return tag("svg", a, `${title}<defs>${defs}</defs>${body}`);
}

// ---------- people (viewBox 0 0 200 320, ground at y 304) ----------

const P_VB = [200, 320];
const P_GROUND = 304;
const SHOULDER = { l: [70, 160], r: [130, 160] };
const P_ORIGIN = { body: [100, P_GROUND], head: [100, 132], eyes: [100, 99], mouth: [100, 118], armL: SHOULDER.l, armR: SHOULDER.r };

const PEOPLE = {
  maya: {
    skin: ["#B87752", "#9A5C3B", "#CF9169"],
    blush: "#E2685A",
    lip: "#57212A",
    hair: ["#2F1D22", "#1E1216", "#5A3A3A"],
    top: ["#F4B728", "#D6930C", "#FFD263"], // jacket, the gold accent
    inner: [CREAM, "#E0D7C5"],
    pants: ["#2D7570", "#215955", "#3F918A"],
    shoe: [CREAM, "#CFC3AE", GOLD],
    sleeve: "long",
  },
  sam: {
    skin: ["#EDBE97", "#D8A079", "#F8D4B6"],
    blush: "#EE8A78",
    lip: "#66292B",
    hair: ["#3A2621", "#281915", "#70503F"],
    top: ["#DD6F54", "#C0563E", "#F08C70"], // overshirt
    inner: [BLUE, "#5F86EA"], // tee, the cool blue accent
    pants: ["#76784B", "#5E6038", "#8E9062"],
    shoe: [CREAM, "#CFC3AE", BLUE],
    sleeve: "rolled",
  },
};

const FACE = {
  maya: "M100 57.5C120.5 57.5 135 73 135 95C135 117 120 132.5 100 132.5C80 132.5 65 117 65 95C65 73 79.5 57.5 100 57.5Z",
  sam: "M100 57C121.5 57 135.5 72.5 135.5 93.5C135.5 112.5 128 126.5 113 131C106 133.2 94 133.2 87 131C72 126.5 64.5 112.5 64.5 93.5C64.5 72.5 78.5 57 100 57Z",
};

const TORSO = "M100 143.5C86 143.5 70 146 64 156C59 163 58 172 59 186L61 226C61.5 232 64 235 70 235H130C136 235 138.5 232 139 226L141 186C142 172 141 163 136 156C130 146 114 143.5 100 143.5Z";

// arm per pose: c = bend control point, w = wrist, hand = shape, rot = fixed hand angle,
// flip = mirror the hand, prop = what the hand holds. Left first unless rFirst.
const ARMS = {
  stand: { l: { c: [57, 190], w: [58, 224], hand: "rest" }, r: { c: [143, 190], w: [142, 224], hand: "rest" } },
  wave: { l: { c: [57, 190], w: [58, 224], hand: "rest" }, r: { c: [172, 168], w: [161, 117], hand: "open", flip: true } },
  phone: { l: { c: [57, 190], w: [58, 224], hand: "rest" }, r: { c: [168, 188], w: [160, 146], hand: "none", prop: "phone" } },
  cheer: { l: { c: [44, 150], w: [43, 96], hand: "fist" }, r: { c: [156, 150], w: [157, 96], hand: "fist" } },
  point: { l: { c: [38, 194], w: [69, 207], hand: "fist" }, r: { c: [160, 164], w: [175, 141], hand: "point" } },
  think: { l: { c: [56, 214], w: [89, 141], hand: "chin" }, r: { c: [140, 208], w: [87, 197], hand: "rest", flip: true }, rFirst: true },
  write: { l: { c: [52, 204], w: [73, 205], hand: "hold", prop: "paper" }, r: { c: [150, 204], w: [117, 192], hand: "fist", prop: "pen" } },
  receive: { l: { c: [56, 214], w: [79, 199], hand: "palm", rot: 0, scale: 1.35 }, r: { c: [144, 214], w: [121, 199], hand: "palm", rot: 0, scale: 1.35 } },
};
const LOOK = { stand: [0, 0], wave: [1, 0], phone: [2.6, -1.4], cheer: [0, -1.2], point: [2.6, -0.6], think: [-1.8, -2.2], write: [0.4, 2.4], receive: [0, 2.2] };
const TILT = { stand: 0, wave: 3, phone: 5, cheer: -3, point: 2, think: -6, write: 4, receive: 0 };

function hand(kind, K, fine) {
  const [k, ks, kl] = K;
  const fold = (d) => (fine ? ink(d, ks, 1.5, { opacity: 0.8 }) : "");
  switch (kind) {
    case "fist":
      return dot(0, 9.4, 8.4, k) + ell(5.6, 7, 3.2, 4.4, k) + fold("M-4.6 12.6Q0 15 4.4 12.8") + ell(-3, 6, 3.2, 2.2, kl, { opacity: 0.45 });
    case "point":
      return ink("M1.8 12V24.5", k, 5) + dot(0, 9.2, 8.2, k) + ell(5.6, 7, 3.2, 4.4, k) + fold("M-4.6 12.4Q-1.6 14.4 1 13.6") + ell(-3, 6, 3.2, 2.2, kl, { opacity: 0.45 });
    case "chin":
      return ink("M1.6 12V21.5", k, 5) + dot(0, 9, 8, k) + ell(5.4, 6.8, 3, 4.2, k) + fold("M-4.4 12.2Q-1.6 14.2 0.8 13.4");
    case "open":
      // fingers together, a little spread at the tips, thumb out
      return ink("M5.4 6.6L11.4 2.8", k, 4.8) + ell(0, 8, 7.6, 7.4, k)
        + path("M-6.9 9.5L-7.6 18C-7.6 21.8 -4 23.4 0 23.4C4 23.4 7.6 21.8 7.6 18L6.9 9.5Z", k)
        + (fine ? ink("M-2.5 14.4L-2.8 21.6M2.5 14.4L2.8 21.6", ks, 1.25, { opacity: 0.75 }) : "")
        + ell(-2.6, 6, 3.2, 2.4, kl, { opacity: 0.4 });
    case "hold":
      return ell(0, 9, 7.8, 8, k) + ink("M5 4.5L8.6 12.5", k, 4.6) + fold("M-4.2 12Q-0.6 14 3 12.6");
    case "palm":
      return path("M-11.4 -0.6C-11.4 7.6 -5.6 11 0.4 11C6.6 11 11.6 7.2 11.6 0.6C6 3.4 -5.4 3.4 -11.4 -0.6Z", k)
        + path("M-10.8 -0.8C-5 2.4 5.8 2.6 11.2 0.2C8.6 -3.4 -7.6 -4 -10.8 -0.8Z", kl)
        + ell(-10.6, -1.8, 3.1, 4.3, k, { transform: "rotate(-18 -10.6 -1.8)" })
        + fold("M-3 7.6Q1 8.8 5 7.2");
    case "rest":
    default:
      return path("M-6.8 4C-7.6 11 -4.6 17.6 0.4 17.6C5.6 17.6 7.8 12 7 5.4C6.6 2.2 4 0.6 0 0.6C-3.8 0.6 -6.4 1.8 -6.8 4Z", k)
        + path("M5 4.6C8.8 5.8 10.2 9.8 8.8 12.6C7.8 14.4 5.4 13.6 5 11.4Z", k)
        + (fine ? path("M-6.5 6.4C-6.8 12 -4 16.4 0 17.2C-3 14.4 -4.4 10.4 -4.2 5.6Z", ks, { opacity: 0.55 }) : "");
  }
}

function phoneProp(o, L) {
  const glow = dot(0, -2, 40, `url(#${o.id}-glow)`, { opacity: L.glow });
  const bodyShape = tag("rect", { x: -15.5, y: -28, width: 31, height: 56, rx: 6.5, fill: "#1B2135" })
    + tag("rect", { x: -15.5, y: -28, width: 31, height: 56, rx: 6.5, fill: "none", stroke: "#4A5577", "stroke-width": 1.2, opacity: 0.9 });
  const screen = part("cast-screen", [0, -1],
    tag("rect", { x: -12.5, y: -24.5, width: 25, height: 47, rx: 4, fill: `url(#${o.id}-screen)` })
    + part("cast-shield", [0, -2],
      path("M0 -10.5L8 -7.2V-1.4C8 4.6 4.4 8.2 0 10.4C-4.4 8.2 -8 4.6 -8 -1.4V-7.2Z", GOLD)
      + path("M0 -10.5V10.4C-4.4 8.2 -8 4.6 -8 -1.4V-7.2Z", "#FFD263")));
  const glint = ink("M-9 -20.5H-3", "#FFFFFF", 1.6, { opacity: 0.55 });
  return { glow, phone: bodyShape + screen + glint };
}

function personArm(side, spec, P, o, L) {
  const S = SHOULDER[side];
  const { c: C, w: W } = spec;
  const K = P.skin;
  const d = `M${pt(S)}Q${pt(C)} ${pt(W)}`;
  const dx = W[0] - C[0], dy = W[1] - C[1], len = Math.hypot(dx, dy) || 1;
  const H = [W[0] + (dx / len) * 1.5, W[1] + (dy / len) * 1.5];
  const ang = spec.rot !== undefined ? spec.rot : aim(C, W);
  const mirror = (side === "r") !== !!spec.flip;
  const k = spec.scale || 1.1;
  const handG = (kind, at, angle) => g({ transform: `translate(${pt(at)}) rotate(${r2(angle)}) scale(${mirror ? -k : k} ${k})` }, hand(kind, K, o.fine));
  const sideName = side === "l" ? "l" : "r";
  const H5 = [W[0] + (dx / len) * 4.5, W[1] + (dy / len) * 4.5]; // hand base sits inside the cuff

  // the arm's shadow falls on the torso only (light from the upper left)
  let s = g({ "clip-path": `url(#${o.id}-torso)` }, ink(d, P.top[1], 18, { transform: "translate(3 3)", opacity: 0.75 }));
  let front = "";
  let handPart = "";

  if (spec.prop === "phone") {
    const at = [W[0] + 2, W[1] - 35];
    const ph = phoneProp(o, L);
    const local = (inner) => g({ transform: `translate(${pt(at)}) rotate(6)` }, inner);
    // palm behind the phone, finger tips curl over its right edge, thumb on the front
    const behind = local(ell(1, 31, 12.5, 10.5, K[0]) + (o.fine ? ell(-3, 34, 7, 5, K[1], { opacity: 0.35 }) : ""));
    const grip = local([10, 17, 24].map((y) => ell(15.2, y, 3.7, 3.4, K[0])).join("")
      + ink("M-12.4 27.5L-11.4 14.5", K[0], 6.6)
      + (o.fine ? ink("M-13.2 23.6L-12.6 17", K[2], 1.6, { opacity: 0.7 }) + [13.4, 20.4].map((y) => ink(`M12.6 ${y}H16.6`, K[1], 1.2, { opacity: 0.7 })).join("") : ""));
    handPart = part(`cast-hand-${sideName}`, W, behind + part("cast-prop cast-phone", at, local(ph.glow + ph.phone)) + grip);
  } else if (spec.prop === "paper") {
    const at = [97, 199];
    const lines = [-8, 0, 8].map((y, i) => tag("rect", { x: -18, y: y - 2, width: i === 2 ? 18 : 33, height: 4, rx: 2, fill: "#C9C0AE", opacity: 0.85 })).join("");
    const paper = g({ transform: `translate(${pt(at)}) rotate(-6)` },
      tag("rect", { x: -25, y: -19, width: 50, height: 38, rx: 3, fill: "#E3DACB" })
      + tag("rect", { x: -25, y: -19, width: 50, height: 36, rx: 3, fill: PAPER })
      + lines);
    handPart = part("cast-prop cast-paper", at, paper) + part(`cast-hand-${sideName}`, W, handG("hold", H5, -84));
  } else if (spec.prop === "pen") {
    const tip = [104.5, 206.5];
    const pen = ink(`M${pt(tip)}L125 178`, "#2A3150", 5.2) + ink("M106.3 204L104.5 206.5", "#141826", 3) + ink("M119.5 185.6L125 178", GOLD, 5.4)
      + (o.fine ? ink("M110 199L117 189.5", "#4A5577", 1.4, { opacity: 0.8 }) : "");
    handPart = part("cast-prop cast-pen", tip, pen) + part(`cast-hand-${sideName}`, W, handG("fist", H5, 40));
  } else if (spec.hand !== "none") {
    handPart = part(`cast-hand-${sideName}`, W, handG(spec.hand, spec.hand === "palm" ? H : H5, ang));
  }

  if (P.sleeve === "long") {
    front += ink(d, P.top[0], 17);
    front += ink(qSub(S, C, W, 0.1, 0.72), P.top[2], 4.4, { transform: "translate(-2.6 -1.4)", opacity: 0.85 });
    // ribbed cuff: a flat band that ends round at the wrist
    front += ink(qSub(S, C, W, 0.86, 1), P.top[1], 17.4, { "stroke-linecap": "butt" }) + dot(W[0], W[1], 8.7, P.top[1]);
    if (o.fine) front += ink(qSub(S, C, W, 0.855, 0.875), P.top[2], 17.4, { "stroke-linecap": "butt", opacity: 0.55 });
  } else {
    front += ink(qSub(S, C, W, 0.4, 1), K[0], 13);
    if (o.fine) front += ink(qSub(S, C, W, 0.62, 0.96), K[2], 3, { transform: "translate(-2 -1)", opacity: 0.6 });
    front += ink(qSub(S, C, W, 0, 0.5), P.top[0], 17);
    front += ink(qSub(S, C, W, 0.1, 0.4), P.top[2], 4.4, { transform: "translate(-2.6 -1.4)", opacity: 0.85 });
    front += ink(qSub(S, C, W, 0.44, 0.55), P.top[2], 19);
    if (o.fine) front += ink(qSub(S, C, W, 0.47, 0.52), P.top[1], 19.4, { opacity: 0.5 });
  }
  s += handPart + front;
  return part(`cast-arm-${sideName}`, S, s);
}

function personEyes(P, o) {
  const big = o.fine ? 1 : 1.25;
  const dark = "#1E161B";
  const [lx, ly] = o.mood === "thinking" ? [-1.8, -2.2] : LOOK[o.pose];
  if (o.mood === "happy") {
    return [87, 113].map((x) => ink(`M${x - 5.4} 101Q${x} ${94.6} ${x + 5.4} 101`, dark, 3.2 * big)).join("");
  }
  const rx = (o.mood === "surprised" ? 4.7 : 4.1) * big;
  const ry = (o.mood === "surprised" ? 6 : 5.1) * big;
  return [87, 113].map((x) => ell(x + lx, 99 + ly, rx, ry, dark)
    + (o.fine ? dot(x + lx + 1.5, 99 + ly - 2, o.mood === "surprised" ? 1.8 : 1.45, "#FFFFFF", { opacity: 0.92 }) : "")).join("");
}

function personBrows(P, o) {
  if (!o.fine) return "";
  const c = P.hair[0];
  const B = {
    neutral: ["M80 88Q86.5 84.4 93 86.6", "M107 86.6Q113.5 84.4 120 88"],
    happy: ["M80 86.2Q86.5 82.4 93 84.8", "M107 84.8Q113.5 82.4 120 86.2"],
    surprised: ["M79.6 82.6Q86.5 77.4 93 80.6", "M107 80.6Q113.5 77.4 120.4 82.6"],
    thinking: ["M80 83.4Q86.5 78.8 93 82.2", "M107 87.4Q113.5 86.2 120 88.4"],
  }[o.mood];
  return part("cast-brows", [100, 85], ink(B[0], c, 3.1) + ink(B[1], c, 3.1));
}

function personMouth(P, o) {
  const w = o.fine ? 2.8 : 3.6;
  switch (o.mood) {
    case "happy":
      return path("M90.5 114.4Q100 116.6 109.5 114.4Q108.6 126.4 100 126.4Q91.4 126.4 90.5 114.4Z", P.lip)
        + path("M93.6 121.8Q100 118.6 106.4 121.8Q104 125.6 100 125.6Q96 125.6 93.6 121.8Z", "#E8786A")
        + (o.fine ? path("M92 115.3Q100 117.2 108 115.3L107.6 117.6Q100 119.2 92.4 117.6Z", "#FFFFFF", { opacity: 0.92 }) : "");
    case "surprised":
      return ell(100, 119.6, 4.4, 5.4, P.lip) + ell(100, 121.8, 2.6, 2.2, "#E8786A");
    case "thinking":
      return ink("M94.6 119.8Q99.6 118 106.6 117", P.lip, w);
    default:
      return ink("M92.6 116.6Q100 122.6 107.4 116.6", P.lip, w);
  }
}

// hair: back layer (behind the face) and cap layer (over the forehead)
function mayaHair(P, o, L) {
  const [h, hs, hl] = P.hair;
  const bumps = [];
  for (let i = 0; i < 9; i++) {
    const a = ((-200 + i * 27.5) * Math.PI) / 180;
    bumps.push([100 + Math.cos(a) * 16.5, 35 + Math.sin(a) * 15.5]);
  }
  const puffShapes = (fill, extra) => dot(100, 35, 19, fill, extra) + bumps.map((b) => dot(b[0], b[1], 8.2, fill, extra)).join("");
  const curls = [[61.4, 95, 4.6], [60.9, 86, 4.8], [63.4, 77, 4.8], [68.6, 69, 4.6], [138.6, 95, 4.6], [139.1, 86, 4.8], [136.6, 77, 4.8], [131.4, 69, 4.6]];
  const cap = "M62.5 101C59.5 76 76 52.5 100 52.5C124 52.5 140.5 76 137.5 101C135 90 132 81 126 76C116 68.4 101 66 86 66.6C77 70 68 82 62.5 101Z";
  const capShapes = (fill, extra) => path(cap, fill, extra) + curls.map((c) => dot(c[0], c[1], c[2], fill, extra)).join("");
  const rim = L.rim ? g({ opacity: L.rimOp, stroke: L.rim, "stroke-width": 3.4, fill: L.rim }, puffShapes(L.rim) + capShapes(L.rim)) : "";

  let back = rim + puffShapes(h);
  back += ell(100, 50, 17, 7, hs, { opacity: 0.9 });
  if (o.fine) {
    back += ink("M86.5 29.5Q89.5 22.5 97 21.6", hl, 3, { opacity: 0.85 })
      + ink("M84 41.5Q83.4 35.6 87 32.4", hl, 2.6, { opacity: 0.7 })
      + ink("M101.5 25.6Q107 23.8 111.4 27.4", hl, 2.4, { opacity: 0.6 })
      + ink("M110 44Q115.6 41.6 116.4 35.6", hs, 2.6, { opacity: 0.9 });
  }
  let front = capShapes(h);
  front += path("M126 76C132 81 135 90 137.5 101L139.4 92C139 84 136.6 76 131 70Z", hs, { opacity: 0.8 });
  if (o.fine) {
    front += ink("M90 60.4C102 56.6 116 58.6 126.4 66.4", hl, 3, { opacity: 0.8 })
      + ink("M84 62.6C76.4 66.6 70 75 66.4 86", hl, 2.6, { opacity: 0.7 })
      + ink("M66.5 95.6Q63.8 101.8 67.4 105.4", hs, 2.2, { opacity: 0.9 });
  }
  // gold hair tie where the puff meets the head
  front += ell(100, 53.6, 13, 4.5, GOLD) + ell(100, 55, 12, 2.8, "#D6930C", { opacity: 0.55 }) + (o.fine ? ink("M91 52.4Q96 50.8 101.5 51", "#FFE08A", 1.6) : "");
  return { back, front, cap };
}

function samHair(P, o, L) {
  const [h, hs, hl] = P.hair;
  // short, soft side-swept fringe: parted on the picture left, swept across to the right
  const cap = "M63.8 102C60.4 82 65.2 63.6 79 54.4C91 46.4 107.6 43.6 121.6 47.6C135 51.4 141.8 63.6 139.8 81.4L137.4 102C136.2 95.4 135 90.6 133.4 86.6C126.8 82.4 117.2 81.2 108 79C99.8 77 91 74 82.4 72.8C76.4 79.6 69.4 89.6 63.8 102Z";
  const tuft = "M82.4 72.8C88 66.6 96 63.2 104.4 63.2C98.6 66.4 94.6 70.4 92.6 75.2Z";
  const burns = "M64.4 97.6H68.6V107.6Q66 108.4 64.9 106.2Z";
  const shapes = (fill, extra) => path(cap, fill, extra) + path(burns, fill, extra) + path(burns, fill, { ...extra, transform: MIRROR });
  const rim = L.rim ? g({ opacity: L.rimOp, stroke: L.rim, "stroke-width": 3.4, fill: L.rim }, shapes(L.rim)) : "";
  let front = rim + shapes(h);
  front += path("M133.4 86.6C135 90.6 136.2 95.4 137.4 102L139.8 81.4C140.4 75 139.6 69.4 137.4 64.6C136.6 72.6 135.2 80 133.4 86.6Z", hs, { opacity: 0.9 });
  front += path(tuft, hs, { opacity: 0.75 });
  if (o.fine) {
    front += ink("M80.6 58.4C92 50.6 108 48 123 52.4", hl, 3.2, { opacity: 0.85 })
      + ink("M96.6 61.4C108 59.6 120 62.6 129.6 70.6", hl, 2.4, { opacity: 0.55 })
      + ink("M108 79C114.6 75.8 121.6 75.6 128 78.4", hs, 2, { opacity: 0.8 });
  }
  return { back: "", front, cap };
}

function personHead(name, P, o, L) {
  const K = P.skin;
  const face = FACE[name];
  const hair = name === "maya" ? mayaHair(P, o, L) : samHair(P, o, L);
  const ears = (extra) => g(extra, ell(64.6, 101, 5.6, 8, K[0]) + ell(65.6, 101.6, 2.6, 4.4, K[1], { opacity: 0.8 }));
  let s = hair.back;
  s += ears({}) + ears({ transform: MIRROR });
  if (name === "maya" && o.fine) s += dot(64, 109.6, 2.4, GOLD) + dot(136, 109.6, 2.4, GOLD);
  // face: shade tone, lit area shifted to the light, soft highlight, hair shadow
  s += g({ "clip-path": `url(#${o.id}-face)` },
    path(face, K[1]) + ell(94, 90, 36.5, 40, K[0])
    + (o.fine ? ell(86, 79, 12, 6, K[2], { opacity: 0.5, transform: "rotate(-14 86 79)" }) : "")
    // the hair casts a soft shadow just under its edge
    + (o.fine ? path(hair.cap, K[1], { opacity: 0.5, transform: "translate(1.4 3.4)" }) : ""));
  s += ell(80, 112, 6.6, 3.9, P.blush, { opacity: o.mood === "happy" ? 0.6 : 0.36 }) + ell(120, 112, 6.6, 3.9, P.blush, { opacity: o.mood === "happy" ? 0.6 : 0.36 });
  if (name === "sam" && o.fine) {
    s += [[77.5, 107.6], [81.6, 110.4], [76.2, 111.6], [122.5, 107.6], [118.4, 110.4], [123.8, 111.6]].map((p) => dot(p[0], p[1], 0.95, K[1])).join("");
  }
  s += name === "sam" ? ell(100, 108.6, 4, 2.9, K[1]) : ell(100, 108.6, 3.4, 2.5, K[1]);
  if (o.fine) s += ell(98.6, 107.6, 1.4, 0.9, K[2], { opacity: 0.6 });
  s += hair.front;
  s += part("cast-eyes", P_ORIGIN.eyes, personEyes(P, o));
  s += personBrows(P, o);
  s += part("cast-mouth", P_ORIGIN.mouth, personMouth(P, o));
  const tilt = TILT[o.pose] + (name === "sam" && o.pose === "stand" ? 2 : 0);
  return part("cast-head", P_ORIGIN.head, tilt ? g({ transform: `rotate(${tilt} 100 132)` }, s) : s);
}

function personTorso(name, P, o) {
  const [t, ts, tl] = P.top;
  const K = P.skin;
  let s = path("M91 116H109V147.5Q100 152.5 91 147.5Z", K[1]); // neck
  s += path(TORSO, t);
  s += path("M122 146.4C133 149 140 158 141 175V186L139 226C138.5 232 136 235 130 235H117C125 218 128 190 122 146.4Z", ts, { opacity: 0.9 });
  s += ink("M66 159Q72 150.4 84 147.4", tl, 3.6, { opacity: 0.8 });
  if (name === "maya") {
    s += path("M88.6 143H111.4L108.6 235H91.4Z", P.inner[0]);
    s += path("M104.4 143H111.4L108.6 235H103.6C105.8 206 106 172 104.4 143Z", P.inner[1]);
    s += path("M91 142.4C92 151 96 155.4 100 155.4C104 155.4 108 151 109 142.4Z", K[1]);
    s += ink("M89 146L92 233.6", ts, 2.6) + ink("M111 146L108 233.6", ts, 2.6);
    s += ink("M82 152Q85.6 143.6 91.6 142", tl, 5.2) + ink("M118 152Q114.4 143.6 108.4 142", tl, 5.2);
    if (o.fine) s += ink("M62 228.6H138", ts, 1.6, { opacity: 0.7 }) + ink("M88.8 147.6L91.6 233", tl, 1.2, { opacity: 0.8 });
  } else {
    s += path("M89 143H111L109.4 235H90.6Z", P.inner[0]);
    s += path("M104.6 143H111L109.4 235H104C106 206 106.2 172 104.6 143Z", P.inner[1]);
    s += path("M92 142.4C93 147.6 96 149.6 100 149.6C104 149.6 107 147.6 108 142.4Z", K[1]);
    s += ink("M92.4 145.2Q100 152.6 107.6 145.2", P.inner[1], 2.4);
    s += ink("M89.4 146L91 233.6", ts, 2.6) + ink("M110.6 146L109 233.6", ts, 2.6);
    s += path("M90.6 141L79.6 148.4C82 152.4 86.6 156.6 92.6 160.4Z", tl) + path("M109.4 141L120.4 148.4C118 152.4 113.4 156.6 107.4 160.4Z", tl);
    if (o.fine) s += path("M116.6 170.4H130V181.6Q130 184.2 127.4 184.2H119.2Q116.6 184.2 116.6 181.6Z", ts) + ink("M116.6 174H130", t, 1.4, { opacity: 0.7 });
  }
  return s;
}

function personLegs(P, o) {
  const [p, ps, pl] = P.pants;
  const [sh, sole, accent] = P.shoe;
  let s = path("M72.5 226H127.5V250H72.5Z", p);
  s += path("M72.5 232H99L97 292.5Q97 295.5 94 295.5H80Q77 295.5 76.8 292.5Z", p);
  s += path("M101 232H127.5L123.2 292.5Q123 295.5 120 295.5H106Q103 295.5 103 292.5Z", p);
  s += path("M90.5 238H99L97 292.5Q97 295.5 94 295.5H90.8C93 272 92.6 254 90.5 238Z", ps);
  s += path("M118.5 238H127.5L123.2 292.5Q123 295.5 120 295.5H117C120.5 272 120.6 254 118.5 238Z", ps);
  s += ink("M99.6 250.6L100.4 292", ps, 1.6, { opacity: 0.8 });
  s += ink("M78.6 240Q79.4 266 80.6 289", pl, 3, { opacity: 0.7 }) + ink("M106 246Q105.6 268 106.4 289", pl, 2.6, { opacity: 0.55 });
  const shoe = path("M99 304H70.6Q67.6 304 68 301C69 294 75 289.6 85 289.6C93 289.6 99 292.4 99 298.6Z", sh)
    + path("M99 300.6H68.2C68 302.8 69 304 70.6 304H99Z", sole)
    + ink("M70 299.4H98.4", accent, o.fine ? 2.2 : 3, { "stroke-linecap": "butt" })
    + (o.fine ? ink("M80.6 291.6L84 294.2M85.4 290.8L88.6 293.6", sole, 1.5) : "");
  s += shoe + g({ transform: MIRROR }, shoe);
  return s;
}

function person(name, opts) {
  const o = options(name, opts);
  const P = PEOPLE[name];
  const L = look(o.theme);
  const A = ARMS[o.pose];
  let defs = tag("clipPath", { id: `${o.id}-face` }, path(FACE[name]))
    + tag("clipPath", { id: `${o.id}-torso` }, path(TORSO));
  if (o.pose === "phone") {
    defs += tag("radialGradient", { id: `${o.id}-glow` },
      tag("stop", { offset: 0, "stop-color": "#FFE7A3", "stop-opacity": 0.9 })
      + tag("stop", { offset: 0.45, "stop-color": GOLD, "stop-opacity": 0.32 })
      + tag("stop", { offset: 1, "stop-color": GOLD, "stop-opacity": 0 }));
    defs += tag("linearGradient", { id: `${o.id}-screen`, x1: 0, y1: 0, x2: 0.35, y2: 1 },
      tag("stop", { offset: 0, "stop-color": "#FFFBEF" }) + tag("stop", { offset: 1, "stop-color": "#FBE2A2" }));
  }
  const shadow = part("cast-shadow", [100, P_GROUND], ell(100, P_GROUND + 0.5, 44, 5.6, L.shadow, { opacity: L.shadowOp }));
  const armL = personArm("l", A.l, P, o, L);
  const armR = personArm("r", A.r, P, o, L);
  const body = personLegs(P, o) + personTorso(name, P, o) + personHead(name, P, o, L) + (A.rFirst ? armR + armL : armL + armR);
  return svg(name, P_VB, o, defs, shadow + part("cast-body", P_ORIGIN.body, body));
}

// ---------- the Watcher (viewBox 0 0 220 300, ground at y 285) ----------

const W_VB = [220, 300];
const W_GROUND = 285;
const LENS = { cx: 110, cy: 121, r: 28, rim: 37 };
const W_ORIGIN = { body: [110, 188], head: [110, 188], eyes: [LENS.cx, LENS.cy], mouth: [110, 170], lens: [LENS.cx, LENS.cy], armL: [64, 142], armR: [156, 142] };
const WC = {
  body: ["#73C5B4", "#56A898", "#A0DDCF"],
  brow: "#3B8576",
  rim: ["#EFE9DA", "#CBC2AE", "#FFFFFF"],
  barrel: "#192036",
  iris: ["#33427E", "#5468B0"],
  pupil: "#0E1325",
  mouth: "#21324A",
  blush: "#FF8C98",
  block: ["#5D6BA0", "#7D8AC2", "#46517F", "#8E9AD2"],
};
const W_BODY = "M110 70C137 70 157 94 158.6 127C160.2 161 138 187 110 187C82 187 59.8 161 61.4 127C63 94 83 70 110 70Z";
const W_ARMS = {
  stand: { l: { c: [53, 150], w: [52, 166] }, r: { c: [167, 150], w: [168, 166] } },
  wave: { l: { c: [53, 150], w: [52, 166] }, r: { c: [178, 140], w: [176, 112], hand: "open" } },
  cheer: { l: { c: [44, 132], w: [44, 108] }, r: { c: [176, 132], w: [176, 108] } },
  point: { l: { c: [53, 150], w: [52, 166] }, r: { c: [176, 140], w: [188, 130], hand: "point" } },
  think: { l: { c: [53, 150], w: [52, 166] }, r: { c: [164, 160], w: [146, 153] } },
  write: { l: { c: [52, 166], w: [70, 170], prop: "pad" }, r: { c: [168, 172], w: [130, 170], prop: "pencil" } },
  receive: { l: { c: [52, 162], w: [68, 166], hand: "palm" }, r: { c: [168, 162], w: [152, 166], hand: "palm" } },
};
W_ARMS.phone = W_ARMS.stand; // the Watcher has no wallet, so "phone" falls back to "stand"
const W_LOOK = { stand: [0, 0], wave: [2, -1], phone: [0, 0], cheer: [0, -3], point: [5, -2], think: [-4, -5], write: [-3, 5], receive: [0, 5] };

function block(x, y, w, h, i, fine) {
  const d = 8;
  const C = WC.block;
  let s = path(`M${x} ${y}L${x + d} ${y - d}H${x + w + d}L${x + w} ${y}Z`, C[1]);
  s += path(`M${x + w} ${y}L${x + w + d} ${y - d}V${y + h - d}L${x + w} ${y + h}Z`, C[2]);
  s += tag("rect", { x, y, width: w, height: h, fill: C[0] });
  s += tag("rect", { x: x + 9, y: y + 8.5, width: w * 0.42, height: 4.2, rx: 2.1, fill: C[3], opacity: 0.6 });
  s += tag("rect", { x: x + 9, y: y + 16.5, width: w * (i === 1 ? 0.3 : 0.24), height: 4.2, rx: 2.1, fill: C[3], opacity: 0.45 });
  if (fine) s += ink(`M${x + 1} ${y + 0.6}L${x + d + 1} ${y - d + 0.6}H${x + w + d - 1}`, "#A9B4E4", 1.3, { opacity: 0.55 });
  return s;
}

function watcherHand(kind, fine) {
  const [b, bs, bl] = WC.body;
  if (kind === "open") return ink("M-4 6L-6 15M0 7V16.5M4 6L6 15", b, 3.6) + dot(0, 5, 7, b) + (fine ? ell(-2, 3, 2.6, 1.8, bl, { opacity: 0.7 }) : "");
  if (kind === "point") return ink("M1 7V18", b, 4.4) + dot(0, 5, 6.8, b) + (fine ? ell(-2, 3, 2.6, 1.8, bl, { opacity: 0.7 }) : "");
  if (kind === "palm") return ell(0, 2, 9, 5.6, b) + ell(0, 0.4, 6.4, 2.6, bl, { opacity: 0.9 });
  return dot(0, 5, 7, b) + (fine ? ell(-2.2, 3, 2.6, 1.8, bl, { opacity: 0.7 }) : "") + (fine ? ink("M-3 8.6Q0 10.2 3 8.6", bs, 1.3, { opacity: 0.8 }) : "");
}

function watcherArm(side, spec, o) {
  const S = W_ORIGIN[side === "l" ? "armL" : "armR"];
  const { c: C, w: W } = spec;
  const [b, bs, bl] = WC.body;
  const d = `M${pt(S)}Q${pt(C)} ${pt(W)}`;
  const mirror = side === "r";
  const ang = spec.hand === "palm" ? 0 : aim(C, W);
  const at = (p, a, inner) => g({ transform: `translate(${pt(p)}) rotate(${r2(a)})${mirror && spec.hand !== "palm" ? " scale(-1 1)" : ""}` }, inner);
  let s = ink(d, bs, 14, { transform: "translate(1.4 1.8)", opacity: 0.6 }) + ink(d, b, 13);
  if (o.fine) s += ink(qSub(S, C, W, 0.15, 0.75), bl, 3, { transform: "translate(-1.6 -1.2)", opacity: 0.7 });
  let hp = "";
  if (spec.prop === "pad") {
    const c = [84, 168];
    hp = part("cast-prop cast-paper", c, g({ transform: `translate(${pt(c)}) rotate(-8)` },
      tag("rect", { x: -15, y: -12, width: 30, height: 24, rx: 2.5, fill: "#E3DACB" })
      + tag("rect", { x: -15, y: -12, width: 30, height: 22.6, rx: 2.5, fill: PAPER })
      + [-5, 1, 7].map((y, i) => tag("rect", { x: -10, y: y - 1.5, width: i === 2 ? 10 : 20, height: 3, rx: 1.5, fill: "#C9C0AE" })).join("")))
      + part("cast-hand-l", W, at(W, -70, watcherHand("fist", o.fine)));
  } else if (spec.prop === "pencil") {
    const tip = [97.5, 175.5];
    hp = part("cast-prop cast-pen", tip, ink(`M${pt(tip)}L114 160`, "#2A3150", 4.2) + ink("M110.4 163.6L114 160", GOLD, 4.4) + ink("M99 174L97.5 175.5", INK, 2.4))
      + part("cast-hand-r", W, at(W, 50, watcherHand("fist", o.fine)));
  } else {
    hp = part(`cast-hand-${side}`, W, at(W, ang, watcherHand(spec.hand || "fist", o.fine)));
  }
  return part(`cast-arm-${side}`, S, s + hp);
}

function watcherEye(o) {
  const { cx, cy, r } = LENS;
  const [lx, ly] = W_LOOK[o.pose];
  const sur = o.mood === "surprised";
  let s = dot(cx, cy, r, `url(#${o.id}-glass)`);
  if (o.lens === "none") {
    const ix = cx + lx, iy = cy + ly + (o.mood === "thinking" ? -1 : 0);
    s += dot(ix, iy, sur ? 13 : 15, WC.iris[0]);
    if (o.fine) s += dot(ix, iy, sur ? 10.5 : 12, "none", { stroke: WC.iris[1], "stroke-width": 2.2, opacity: 0.6 });
    s += dot(ix, iy, sur ? 6.2 : 8, WC.pupil);
    s += dot(ix - 5.5, iy - 6, sur ? 4.6 : 4.2, "#FFFFFF") + dot(ix + 5.4, iy + 5.2, 1.9, "#FFFFFF", { opacity: 0.9 });
    // lids, clipped to the glass: a smiling lower lid, a thoughtful tilted upper lid
    if (o.mood === "happy") {
      s += g({ "clip-path": `url(#${o.id}-lens)` }, ell(cx, cy + 27, 38, 17, WC.body[0]) + ink(`M${cx - 30} ${cy + 13}Q${cx} ${cy + 6} ${cx + 30} ${cy + 13}`, WC.body[1], 2.4));
    } else if (o.mood === "thinking") {
      s += g({ "clip-path": `url(#${o.id}-lens)` }, path(`M${cx - 32} ${cy - 32}H${cx + 32}V${cy - 9}L${cx - 32} ${cy - 17}Z`, WC.body[0]) + ink(`M${cx - 32} ${cy - 17}L${cx + 32} ${cy - 9}`, WC.body[1], 2.4));
    }
  } else if (o.lens === "read") {
    s += dot(cx, cy, r, `url(#${o.id}-read)`);
    s += part("cast-lens-content", [cx, cy], [[-10, 34], [0, 28], [10, 20]].map(([y, w]) => tag("rect", { x: cx - 17, y: cy + y - 2.6, width: w, height: 5.2, rx: 2.6, fill: "#F2F6FF", opacity: 0.95 })).join(""));
  } else {
    s += dot(cx, cy, r, `url(#${o.id}-scramble)`);
    const cells = [
      [-17, -13, 6, 4], [-9, -13, 4, 4], [-3, -13, 7, 4], [6, -13, 5, 4], [13, -12, 4, 3],
      [-21, -5, 5, 4], [-14, -5, 8, 4], [-4, -5, 4, 4], [2, -5, 6, 4], [10, -5, 7, 4], [19, -4, 3, 3],
      [-20, 3, 7, 4], [-11, 3, 4, 4], [-5, 3, 6, 4], [3, 3, 4, 4], [9, 3, 8, 4], [19, 3, 3, 4],
      [-16, 11, 4, 4], [-10, 11, 7, 4], [-1, 11, 5, 4], [6, 11, 6, 4], [14, 11, 4, 3],
      [-9, 18, 6, 3], [-1, 18, 4, 3], [5, 18, 6, 3],
    ];
    s += part("cast-lens-content", [cx, cy], cells.map(([x, y, w, h], i) => tag("rect", { x: cx + x, y: cy + y, width: w, height: h, rx: 1, fill: i % 3 === 1 ? "#FFF2C4" : "#8A5C00", opacity: i % 3 === 1 ? 0.85 : 0.5 })).join(""));
  }
  // glass glint on top of whatever the lens shows
  s += ink(`M${cx - 19} ${cy - 6}A20 20 0 0 1 ${cx - 7} ${cy - 19}`, "#FFFFFF", 3.6, { opacity: o.lens === "none" ? 0.5 : 0.7 });
  return s;
}

export function watcher(opts) {
  const o = options("watcher", opts);
  const L = look(o.theme);
  const A = W_ARMS[o.pose];
  const [b, bs, bl] = WC.body;
  const { cx, cy, r, rim } = LENS;
  let defs = tag("clipPath", { id: `${o.id}-body` }, path(W_BODY))
    + tag("clipPath", { id: `${o.id}-lens` }, dot(cx, cy, r))
    + tag("radialGradient", { id: `${o.id}-glass`, cx: 0.4, cy: 0.36, r: 0.7 },
      tag("stop", { offset: 0, "stop-color": "#FFFFFF" }) + tag("stop", { offset: 1, "stop-color": "#DCE4F7" }));
  if (o.lens === "read") {
    defs += tag("radialGradient", { id: `${o.id}-read`, cx: 0.4, cy: 0.36, r: 0.75 },
      tag("stop", { offset: 0, "stop-color": "#B5CBFF" }) + tag("stop", { offset: 1, "stop-color": "#668EF0" }));
  }
  if (o.lens === "scramble") {
    defs += tag("radialGradient", { id: `${o.id}-scramble`, cx: 0.4, cy: 0.36, r: 0.75 },
      tag("stop", { offset: 0, "stop-color": "#FFD978" }) + tag("stop", { offset: 1, "stop-color": "#E59E12" }));
  }

  const shadow = part("cast-shadow", [110, W_GROUND], ell(112, W_GROUND + 0.5, 62, 5.6, L.shadow, { opacity: L.shadowOp }));
  const blocks = part("cast-blocks", [110, W_GROUND], block(52, 256, 108, 29, 0, o.fine) + block(62, 224, 88, 29, 1, o.fine) + block(72, 192, 68, 29, 2, o.fine));

  const feet = ell(96, 188.4, 11.5, 5.6, bs) + ell(124, 188.4, 11.5, 5.6, bs);
  let shape = g({ "clip-path": `url(#${o.id}-body)` },
    path(W_BODY, bs) + ell(104.5, 122, 52, 63, b)
    + (o.fine ? ell(84, 94, 15, 9, bl, { opacity: 0.55, transform: "rotate(-34 84 94)" }) : ""));
  const antenna = part("cast-antenna", [110, 72], ink("M110 73Q106.6 60 112.6 50", WC.brow, 3.6) + dot(113.4, 46.6, 6.2, "#FF9E7D") + ell(115.6, 49, 3, 2, "#E9785A", { opacity: 0.8 }) + (o.fine ? dot(111.6, 44.6, 2, "#FFFFFF", { opacity: 0.9 }) : ""));

  const ticks = o.fine ? Array.from({ length: 20 }, (_, i) => {
    const a = (i / 20) * Math.PI * 2;
    return ink(`M${pt([cx + Math.cos(a) * 34.4, cy + Math.sin(a) * 34.4])}L${pt([cx + Math.cos(a) * 36.4, cy + Math.sin(a) * 36.4])}`, WC.rim[1], 1.3);
  }).join("") : "";
  const lens = part("cast-lens", [cx, cy],
    dot(cx + 1.2, cy + 2.4, rim, bs, { opacity: 0.7 })
    + dot(cx, cy, rim, WC.rim[0])
    + ink(`M${cx + 26} ${cy + 26}A${rim - 1.5} ${rim - 1.5} 0 0 1 ${cx - 26} ${cy + 26}`, WC.rim[1], 3, { opacity: 0.9 })
    + ticks
    + dot(cx, cy, r + 3.6, WC.barrel)
    + part("cast-eyes", W_ORIGIN.eyes, watcherEye(o))
    + (o.fine ? ink(`M${cx - 27} ${cy - 20}A${rim - 3} ${rim - 3} 0 0 1 ${cx - 8} ${cy - 33}`, WC.rim[2], 2, { opacity: 0.8 }) : ""));

  const B = {
    neutral: `M95 78Q110 72.4 125 78`,
    happy: `M95 76Q110 69.6 125 76`,
    surprised: `M95.4 72.4Q110 64.4 124.6 72.4`,
    thinking: `M95 75Q110 70.4 125 80`,
  }[o.mood];
  const brow = part("cast-brows", [110, 76], ink(B, WC.brow, 4.2));
  const mouthD = {
    neutral: ink("M101.4 167.6Q110 174 118.6 167.6", WC.mouth, o.fine ? 3.2 : 4),
    happy: path("M100 166.4Q110 168.6 120 166.4Q119 178.4 110 178.4Q101 178.4 100 166.4Z", WC.mouth) + path("M103.4 174Q110 170.6 116.6 174Q114 177.6 110 177.6Q106 177.6 103.4 174Z", "#E8786A"),
    surprised: ell(110, 171, 4.6, 5.6, WC.mouth) + ell(110, 173.2, 2.6, 2.2, "#E8786A"),
    thinking: ink("M103.6 171.6Q109 169.4 117.4 169", WC.mouth, o.fine ? 3.2 : 4),
  }[o.mood];
  const blushOp = o.mood === "happy" ? 0.78 : 0.6;
  const cheeks = ell(80, 165, 7.4, 4.4, WC.blush, { opacity: blushOp }) + ell(140, 165, 7.4, 4.4, WC.blush, { opacity: blushOp });
  const head = part("cast-head", W_ORIGIN.head, antenna + shape + cheeks + brow + lens + part("cast-mouth", W_ORIGIN.mouth, mouthD));
  const armL = watcherArm("l", A.l, o);
  const armR = watcherArm("r", A.r, o);
  const body = part("cast-body", W_ORIGIN.body, feet + head + armL + armR);
  return svg("watcher", W_VB, o, defs, shadow + blocks + body);
}

export function maya(opts) { return person("maya", opts); }
export function sam(opts) { return person("sam", opts); }

// ---------- metadata ----------

const PEOPLE_ORIGINS = {
  "cast-body": pt(P_ORIGIN.body), "cast-head": pt(P_ORIGIN.head), "cast-eyes": pt(P_ORIGIN.eyes),
  "cast-mouth": pt(P_ORIGIN.mouth), "cast-arm-l": pt(P_ORIGIN.armL), "cast-arm-r": pt(P_ORIGIN.armR),
};

export const CAST = {
  poses: POSES,
  moods: MOODS,
  lenses: LENSES,
  themes: THEMES,
  classes: ["cast-body", "cast-head", "cast-eyes", "cast-mouth", "cast-arm-l", "cast-arm-r", "cast-prop", "cast-lens"],
  maya: {
    name: "Maya",
    role: "The learner. She pays.",
    viewBox: "0 0 200 320",
    width: 200,
    height: 320,
    baseline: P_GROUND,
    accent: GOLD,
    poses: POSES,
    origins: PEOPLE_ORIGINS,
  },
  sam: {
    name: "Sam",
    role: "Her friend. He gets paid.",
    viewBox: "0 0 200 320",
    width: 200,
    height: 320,
    baseline: P_GROUND,
    accent: BLUE,
    poses: POSES,
    origins: PEOPLE_ORIGINS,
  },
  watcher: {
    name: "The Watcher",
    role: "Anyone looking at the public blockchain.",
    viewBox: "0 0 220 300",
    width: 220,
    height: 300,
    baseline: W_GROUND,
    accent: WC.body[0],
    poses: POSES.filter((p) => p !== "phone"),
    lens: { ...LENS },
    origins: {
      "cast-body": pt(W_ORIGIN.body), "cast-head": pt(W_ORIGIN.head), "cast-eyes": pt(W_ORIGIN.eyes),
      "cast-mouth": pt(W_ORIGIN.mouth), "cast-arm-l": pt(W_ORIGIN.armL), "cast-arm-r": pt(W_ORIGIN.armR),
      "cast-lens": pt(W_ORIGIN.lens),
    },
  },
};

export default { maya, sam, watcher, CAST };
