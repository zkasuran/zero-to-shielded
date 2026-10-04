// fx.js: the motion layer. Every effect moves only transform and opacity (or canvas),
// pauses when off screen, and collapses to a plain fade or the final state under
// prefers-reduced-motion and under ?capture=1.

import { CAPTURE, reducedMotion, finePointer } from "./env.js";

const root = document.documentElement;

// ---------- seeded random, so captures are identical run to run ----------

export function rng(seed = 1) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

const GLYPHS = "░▒▓█▚▞▙▟▛▜▄▀▌▐";
export function glyphs(n, seed = 7) {
  const r = rng(seed);
  let out = "";
  for (let i = 0; i < n; i++) out += GLYPHS[Math.floor(r() * GLYPHS.length)];
  return out;
}

// ---------- reveal on scroll ----------
// Browsers with scroll-driven animations use pure CSS (animation-timeline: view()).
// The rest get an IntersectionObserver that adds .is-in. Capture mode shows all.

export function initReveals() {
  if (CAPTURE) return;
  const css = typeof CSS !== "undefined" && CSS.supports && CSS.supports("animation-timeline: view()");
  if (css) return;
  const els = document.querySelectorAll(".reveal, .reveal-stagger > *, [data-draw]");
  if (!els.length || !("IntersectionObserver" in window)) return;
  root.classList.add("io-reveal");
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
    }
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  els.forEach((el) => io.observe(el));
}

// ---------- magnetic primary buttons ----------

export function initMagnetic() {
  if (CAPTURE || reducedMotion() || !finePointer()) return;
  document.querySelectorAll("[data-magnetic]").forEach((el) => {
    let raf = 0;
    const move = (e) => {
      const r = el.getBoundingClientRect();
      const dx = e.clientX - (r.left + r.width / 2);
      const dy = e.clientY - (r.top + r.height / 2);
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        el.style.setProperty("--mx", `${(dx * 0.22).toFixed(2)}px`);
        el.style.setProperty("--my", `${(dy * 0.32).toFixed(2)}px`);
      });
    };
    const leave = () => {
      cancelAnimationFrame(raf);
      el.style.setProperty("--mx", "0px");
      el.style.setProperty("--my", "0px");
    };
    el.classList.add("is-magnetic");
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerleave", leave);
  });
}

// ---------- cursor spotlight ----------
// A blurred gold disc follows the pointer inside cards. It moves by transform only.

export function initSpotlight(selector = ".tool-card, .ep-card, .need-card, .support-card, .kind, .mistake") {
  if (CAPTURE || reducedMotion() || !finePointer()) return;
  document.querySelectorAll(selector).forEach((card) => {
    const spot = document.createElement("span");
    spot.className = "spot";
    spot.setAttribute("aria-hidden", "true");
    card.classList.add("has-spot");
    if (getComputedStyle(card).position === "static") card.classList.add("is-relative");
    card.prepend(spot);
    let raf = 0;
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        spot.style.setProperty("--sx", `${(e.clientX - r.left).toFixed(1)}px`);
        spot.style.setProperty("--sy", `${(e.clientY - r.top).toFixed(1)}px`);
      });
    });
  });
}

// ---------- text decrypt / encrypt ----------
// Resolves glyphs into the real text left to right (decrypt), or the reverse.
// Uses a monospace face so the width never jumps.

const running = new WeakMap();

export function scrambleTo(el, finalText, { duration = 900, seed = 3, mode = "decrypt" } = {}) {
  const prev = running.get(el);
  if (prev) cancelAnimationFrame(prev);
  const target = String(finalText);
  if (reducedMotion()) {
    el.textContent = target;
    return Promise.resolve();
  }
  const r = rng(seed + target.length);
  const start = performance.now();
  return new Promise((resolve) => {
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const settled = Math.floor(p * target.length);
      let s = "";
      for (let i = 0; i < target.length; i++) {
        const ch = target[i];
        const keep = mode === "decrypt" ? i < settled : i >= target.length - settled;
        if (ch === " ") s += " ";
        else if (keep) s += mode === "decrypt" ? ch : GLYPHS[Math.floor(r() * GLYPHS.length)];
        else s += mode === "decrypt" ? GLYPHS[Math.floor(r() * GLYPHS.length)] : ch;
      }
      el.textContent = s;
      if (p < 1) running.set(el, requestAnimationFrame(tick));
      else { running.delete(el); resolve(); }
    };
    running.set(el, requestAnimationFrame(tick));
  });
}

// Keeps glyph strings gently changing while they are on screen ("the Watcher sees noise").
export function shimmer(els) {
  if (CAPTURE || reducedMotion() || !els.length) return () => {};
  const live = new Set();
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) e.isIntersecting ? live.add(e.target) : live.delete(e.target);
  });
  els.forEach((el) => io.observe(el));
  const r = rng(11);
  let last = 0;
  let raf = 0;
  const loop = (now) => {
    raf = requestAnimationFrame(loop);
    if (now - last < 110 || document.hidden) return;
    last = now;
    for (const el of live) {
      if (el.dataset.locked === "1") continue;
      const chars = [...el.textContent];
      if (!chars.length) continue;
      const i = Math.floor(r() * chars.length);
      if (chars[i] !== " ") chars[i] = GLYPHS[Math.floor(r() * GLYPHS.length)];
      el.textContent = chars.join("");
    }
  };
  raf = requestAnimationFrame(loop);
  return () => { cancelAnimationFrame(raf); io.disconnect(); };
}

// ---------- gold shield burst ----------

export function burst(host, { count = 90 } = {}) {
  if (!host || CAPTURE) return;
  if (reducedMotion()) {
    host.classList.add("is-celebrating");
    setTimeout(() => host.classList.remove("is-celebrating"), 1200);
    return;
  }
  const canvas = document.createElement("canvas");
  canvas.className = "burst";
  canvas.setAttribute("aria-hidden", "true");
  host.appendChild(canvas);
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = Math.max(1, rect.width * dpr);
  canvas.height = Math.max(1, rect.height * dpr);
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  const origin = host.querySelector(".cl-badge") || host;
  const o = origin.getBoundingClientRect();
  const cx = o.left + o.width / 2 - rect.left;
  const cy = o.top + o.height / 2 - rect.top;
  const r = rng(Date.now() & 0xffff);
  const gold = ["#F4B728", "#FFD877", "#FFE9A8", "#E9A90F"];
  const parts = Array.from({ length: count }, (_, i) => {
    const a = (i / count) * Math.PI * 2 + r() * 0.4;
    const sp = 2.2 + r() * 5.2;
    return { x: cx, y: cy, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 1.2, s: 1.6 + r() * 3.4, c: gold[i % gold.length], rot: r() * 6.28, vr: (r() - 0.5) * 0.3, shape: i % 3 };
  });
  host.classList.add("is-celebrating");
  const start = performance.now();
  const life = 1500;
  const frame = (now) => {
    const t = now - start;
    ctx.clearRect(0, 0, rect.width, rect.height);
    // expanding ring
    const p = Math.min(1, t / 700);
    ctx.globalAlpha = (1 - p) * 0.7;
    ctx.strokeStyle = "#F4B728";
    ctx.lineWidth = 3 * (1 - p) + 0.5;
    ctx.beginPath();
    ctx.arc(cx, cy, 20 + p * 220, 0, Math.PI * 2);
    ctx.stroke();
    for (const q of parts) {
      q.vy += 0.09;
      q.vx *= 0.985;
      q.vy *= 0.985;
      q.x += q.vx;
      q.y += q.vy;
      q.rot += q.vr;
      ctx.globalAlpha = Math.max(0, 1 - t / life);
      ctx.fillStyle = q.c;
      ctx.save();
      ctx.translate(q.x, q.y);
      ctx.rotate(q.rot);
      if (q.shape === 0) { ctx.beginPath(); ctx.arc(0, 0, q.s, 0, Math.PI * 2); ctx.fill(); }
      else if (q.shape === 1) ctx.fillRect(-q.s, -q.s / 2, q.s * 2, q.s);
      else {
        // tiny shield
        const k = q.s * 1.3;
        ctx.beginPath();
        ctx.moveTo(0, -k); ctx.lineTo(k, -k * 0.6); ctx.lineTo(k * 0.8, k * 0.3); ctx.lineTo(0, k); ctx.lineTo(-k * 0.8, k * 0.3); ctx.lineTo(-k, -k * 0.6);
        ctx.closePath(); ctx.fill();
      }
      ctx.restore();
    }
    if (t < life) requestAnimationFrame(frame);
    else { canvas.remove(); host.classList.remove("is-celebrating"); }
  };
  requestAnimationFrame(frame);
}
