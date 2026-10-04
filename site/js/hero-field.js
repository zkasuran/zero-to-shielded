// hero-field.js: the hero background. Slate dots drift in from the left (transparent:
// anyone can see them), cross a line and turn gold (shielded), then slip behind the
// player. Canvas only, about 120 dots, paused off screen and in background tabs,
// drawn once and frozen under reduced motion and in capture mode.

import { CAPTURE, reducedMotion } from "./env.js";
import { rng } from "./fx.js";

function hexToRgb(hex, fallback) {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(hex).trim());
  if (!m) return fallback;
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function sprite(rgb, size) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  const grd = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grd.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.9)`);
  grd.addColorStop(0.25, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.35)`);
  grd.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
  g.fillStyle = grd;
  g.fillRect(0, 0, size, size);
  return c;
}

export function heroField(canvas, hero) {
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const still = CAPTURE || reducedMotion();
  const rand = rng(20261004);
  let w = 0, h = 0, dpr = 1, line = 0;
  let parts = [];
  let colors = null;
  let glow = null;
  let raf = 0;
  let last = 0;
  let onScreen = true;
  const pointer = { x: -1e4, y: -1e4 };

  function readColors() {
    const cs = getComputedStyle(document.documentElement);
    const dark = document.documentElement.dataset.theme !== "light";
    colors = {
      dark,
      gold: hexToRgb(cs.getPropertyValue("--gold"), [244, 183, 40]),
      clear: hexToRgb(cs.getPropertyValue("--clear"), [122, 162, 255]),
    };
    glow = sprite(colors.gold, 48);
  }

  function boundary() {
    const player = hero.querySelector(".hero-player");
    const hr = hero.getBoundingClientRect();
    if (player && innerWidth >= 960) {
      const pr = player.getBoundingClientRect();
      return Math.max(w * 0.3, pr.left - hr.left - 28);
    }
    return w * 0.52;
  }

  function spawn(p, fresh) {
    p.z = 0.35 + rand() * 0.65;
    p.x = fresh ? -20 - rand() * w * 0.25 : -0.15 * w + rand() * w * 1.15;
    p.by = rand() * h;
    p.amp = 4 + rand() * 16;
    p.freq = 0.25 + rand() * 0.6;
    p.ph = rand() * Math.PI * 2;
    p.v = (22 + rand() * 46) * (0.6 + p.z * 0.6);
    p.r = 0.7 + rand() * 1.7;
    p.flash = 0;
    p.crossed = p.x > line;
    p.ox = 0; p.oy = 0;
  }

  function layout() {
    const r = canvas.getBoundingClientRect();
    w = Math.max(1, r.width);
    h = Math.max(1, r.height);
    dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    line = boundary();
    const n = Math.round(Math.min(150, Math.max(40, (w * h) / (w < 700 ? 11000 : 8200))));
    parts = Array.from({ length: n }, () => { const p = {}; spawn(p, false); return p; });
  }

  function draw(t, dt) {
    ctx.clearRect(0, 0, w, h);
    // one column of text over the field on phones: keep the dots quieter there
    const soft = w < 700 ? 0.55 : 1;
    const { gold, clear, dark } = colors;
    const band = 70;
    for (const p of parts) {
      if (dt) {
        p.x += p.v * dt;
        if (!p.crossed && p.x > line) { p.crossed = true; p.flash = 1; }
        p.flash = Math.max(0, p.flash - dt * 1.6);
        if (p.x > w + 30) spawn(p, true);
        // gentle push away from the pointer
        const dx = p.x - pointer.x, dy = p.by - pointer.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 120 * 120) {
          const f = (1 - Math.sqrt(d2) / 120) * 26;
          const d = Math.sqrt(d2) || 1;
          p.ox += ((dx / d) * f - p.ox) * 0.12;
          p.oy += ((dy / d) * f - p.oy) * 0.12;
        } else {
          p.ox *= 0.94; p.oy *= 0.94;
        }
      }
      const y = p.by + Math.sin(t * p.freq + p.ph) * p.amp + p.oy;
      const x = p.x + p.ox;
      // 0 = transparent (slate), 1 = shielded (gold)
      const k = Math.min(1, Math.max(0, (x - (line - band)) / band));
      const c = [0, 1, 2].map((i) => Math.round(clear[i] + (gold[i] - clear[i]) * k));
      const a = (dark ? 0.22 + 0.5 * p.z : 0.2 + 0.45 * p.z) * (0.55 + 0.45 * k) * soft;
      const rad = p.r * (0.8 + p.z * 0.7) * (1 + k * 0.35);
      if (k > 0.6) {
        const gs = rad * (7 + p.flash * 10);
        ctx.globalAlpha = ((dark ? 0.42 : 0.5) * k * (0.5 + p.z * 0.5) + p.flash * 0.5) * soft;
        ctx.drawImage(glow, x - gs / 2, y - gs / 2, gs, gs);
      }
      ctx.globalAlpha = Math.min(1, a + p.flash * 0.4);
      ctx.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`;
      ctx.beginPath();
      ctx.arc(x, y, rad, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  function loop(now) {
    raf = requestAnimationFrame(loop);
    const dt = last ? Math.min(0.05, (now - last) / 1000) : 0;
    last = now;
    draw(now / 1000, dt);
  }

  function start() {
    if (still || raf || !onScreen || document.hidden) return;
    last = 0;
    raf = requestAnimationFrame(loop);
  }
  function stop() {
    cancelAnimationFrame(raf);
    raf = 0;
  }

  readColors();
  layout();
  draw(0, 0);
  canvas.classList.add("is-ready");
  if (still) {
    new ResizeObserver(() => { layout(); draw(0, 0); }).observe(canvas);
    document.addEventListener("zts:theme", () => { readColors(); draw(0, 0); });
    return;
  }

  let resizeRaf = 0;
  new ResizeObserver(() => {
    cancelAnimationFrame(resizeRaf);
    resizeRaf = requestAnimationFrame(() => { layout(); draw(0, 0); });
  }).observe(canvas);
  new IntersectionObserver((entries) => {
    onScreen = entries[0].isIntersecting;
    onScreen ? start() : stop();
  }).observe(hero);
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));
  document.addEventListener("zts:theme", () => readColors());
  hero.addEventListener("pointermove", (e) => {
    const r = canvas.getBoundingClientRect();
    pointer.x = e.clientX - r.left;
    pointer.y = e.clientY - r.top;
  });
  hero.addEventListener("pointerleave", () => { pointer.x = -1e4; pointer.y = -1e4; });
  start();
}
