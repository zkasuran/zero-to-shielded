// theme.js: the light/dark toggle. The inline head script already set data-theme before
// first paint; this only handles the button, saving the choice and the reveal.
import { getItem, setItem } from "./store.js";
import { reducedMotion, CAPTURE } from "./env.js";

const KEY = "zts-theme";
const root = document.documentElement;

function label(btn) {
  const dark = root.dataset.theme !== "light";
  const text = dark ? "Switch to light theme" : "Switch to dark theme";
  btn.setAttribute("aria-label", text);
  btn.setAttribute("title", text);
}

function syncThemeColor() {
  const bg = root.dataset.theme === "light" ? "#FBF8F1" : "#0B0F1A";
  document.querySelectorAll('meta[name="theme-color"]').forEach((m) => m.setAttribute("content", bg));
}

function apply(next, btn) {
  root.dataset.theme = next;
  if (btn) label(btn);
  syncThemeColor();
  document.dispatchEvent(new CustomEvent("zts:theme", { detail: { theme: next } }));
}

export function initTheme() {
  const btn = document.querySelector("[data-theme-toggle]");
  const forced = root.hasAttribute("data-theme-forced");
  if (forced || getItem(KEY)) syncThemeColor();
  if (!btn) return;
  label(btn);

  btn.addEventListener("click", () => {
    const next = root.dataset.theme === "light" ? "dark" : "light";
    if (!forced) setItem(KEY, next);
    if (!document.startViewTransition || reducedMotion() || CAPTURE) { apply(next, btn); return; }
    const r = btn.getBoundingClientRect();
    const x = r.left + r.width / 2;
    const y = r.top + r.height / 2;
    const end = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    root.classList.add("vt-theme");
    let t;
    try { t = document.startViewTransition(() => apply(next, btn)); } catch { root.classList.remove("vt-theme"); apply(next, btn); return; }
    t.ready.then(() => {
      root.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${end}px at ${x}px ${y}px)`] },
        { duration: 620, easing: "cubic-bezier(.65,0,.35,1)", pseudoElement: "::view-transition-new(root)" },
      );
    }).catch(() => {});
    t.finished.finally(() => root.classList.remove("vt-theme"));
  });

  // Follow the system setting until the visitor picks one.
  if (!forced && typeof matchMedia === "function") {
    matchMedia("(prefers-color-scheme: light)").addEventListener("change", (e) => {
      if (getItem(KEY)) return;
      apply(e.matches ? "light" : "dark", btn);
    });
  }
}
