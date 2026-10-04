// env.js: what kind of visit this is. Read once, used everywhere.
const root = document.documentElement;

// ?capture=1: the video kit is screenshotting. Final states only, no motion.
export const CAPTURE = root.hasAttribute("data-capture");

export const reducedMotion = () =>
  CAPTURE || (typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches);

export const finePointer = () =>
  typeof matchMedia === "function" && matchMedia("(hover: hover) and (pointer: fine)").matches;

// The site root, from this module's own URL (/js/env.js -> /). Works at a domain root
// and under a sub path, so links built in JS match the relative links in the HTML.
export const SITE_ROOT = new URL("../", import.meta.url);
export const siteUrl = (path) => new URL(String(path).replace(/^\//, ""), SITE_ROOT).href;

export const theme = () => (root.dataset.theme === "light" ? "light" : "dark");
