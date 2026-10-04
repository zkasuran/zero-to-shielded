// pages/chain.js: the "flip the same payment" stage. A switch (and, on wide screens,
// the scroll position) moves one diagram between transparent and shielded. The Watcher's
// values encrypt into glyphs; Maya and Sam's note decrypts into words.

import { scrambleTo, glyphs, shimmer, rng } from "../fx.js";
import { CAPTURE, reducedMotion } from "../env.js";

const stage = document.querySelector("[data-stage]");
if (stage) initStage(stage);

const PUBLIC = { sender: "t1Kx9…8Rn", receiver: "t1Q4m…2Lw", amount: "0.50 ZEC", note: "No note on t1" };
const PAIR = {
  transparent: { sender: "Maya", receiver: "Sam", amount: "0.50 ZEC", note: "No note on t1" },
  shielded: { sender: "Maya", receiver: "Sam", amount: "0.50 ZEC", note: "Thanks for lunch!" },
};
const CAPTIONS = {
  transparent: "Transparent: the Watcher reads everything Maya and Sam read.",
  shielded: "Shielded: the Watcher sees only noise. Maya and Sam still read every detail.",
};
const TAGS = { transparent: "0.50 ZEC, public", shielded: "encrypted" };

function encrypt(el, final, duration = 700) {
  if (reducedMotion()) { el.textContent = final; return; }
  const from = el.textContent;
  const len = Math.max(from.length, final.length);
  const r = rng(final.length * 31 + 7);
  const t0 = performance.now();
  const G = "░▒▓█▚▞▙▟▛▜";
  const tick = (now) => {
    const p = Math.min(1, (now - t0) / duration);
    const n = Math.floor(p * len);
    let s = "";
    for (let i = 0; i < len; i++) {
      if (i < n) s += final[i] || "";
      else if (i < n + 3) s += G[Math.floor(r() * G.length)];
      else s += from[i] || "";
    }
    el.textContent = s;
    if (p < 1) requestAnimationFrame(tick);
    else el.textContent = final;
  };
  requestAnimationFrame(tick);
}

function initStage(root) {
  const buttons = [...root.querySelectorAll("[data-mode-btn]")];
  const watch = Object.fromEntries([...root.querySelectorAll("[data-w]")].map((d) => [d.dataset.w, d]));
  const pair = Object.fromEntries([...root.querySelectorAll("[data-p]")].map((d) => [d.dataset.p, d]));
  const caption = root.querySelector("[data-stage-caption]");
  const tag = root.querySelector("[data-flow-tag]");
  let mode = root.dataset.mode || "transparent";

  Object.values(watch).forEach((d) => (d.dataset.locked = "1"));
  shimmer(Object.values(watch));

  function set(next, focus = null) {
    root.classList.toggle("focus-pair", focus === "pair");
    if (next === mode) return;
    mode = next;
    root.dataset.mode = mode;
    buttons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.modeBtn === mode)));
    Object.entries(watch).forEach(([k, d], i) => {
      if (mode === "shielded") {
        encrypt(d, glyphs(Math.max(6, PUBLIC[k].length), 40 + i), 520 + i * 120);
        setTimeout(() => (d.dataset.locked = "0"), 900);
      } else {
        d.dataset.locked = "1";
        scrambleTo(d, PUBLIC[k], { duration: 520 + i * 90, seed: 9 + i });
      }
    });
    Object.entries(pair).forEach(([k, d]) => {
      const want = PAIR[mode][k];
      if (d.textContent !== want) scrambleTo(d, want, { duration: 900, seed: 21 });
    });
    if (caption) caption.textContent = CAPTIONS[mode];
    if (tag) tag.textContent = TAGS[mode];
  }

  buttons.forEach((b) => b.addEventListener("click", () => set(b.dataset.modeBtn)));

  // Arrow keys move the switch, like a radio group.
  root.querySelector(".seg")?.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const next = mode === "transparent" ? "shielded" : "transparent";
    set(next);
    root.querySelector(`[data-mode-btn="${next}"]`)?.focus();
  });

  // Scrollytelling on wide screens: the step in the middle of the screen drives the stage.
  const wide = matchMedia("(min-width: 960px)");
  if (CAPTURE || !("IntersectionObserver" in window)) return;
  const steps = [...document.querySelectorAll("[data-xstep]")];
  const io = new IntersectionObserver((entries) => {
    if (!wide.matches) return;
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      steps.forEach((s) => s.classList.toggle("is-active", s === e.target));
      const which = e.target.dataset.xstep;
      set(which === "transparent" ? "transparent" : "shielded", which === "pair" ? "pair" : null);
    }
  }, { rootMargin: "-45% 0px -45% 0px" });
  steps.forEach((s) => io.observe(s));
}
