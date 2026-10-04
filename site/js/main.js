// main.js: loaded on every page. Page modules (js/pages/*.js) add their own parts.
import { initTheme } from "./theme.js";
import { initNav } from "./nav.js";
import { initReveals, initMagnetic, initSpotlight, shimmer } from "./fx.js";
import { installCapture } from "./capture.js";
import { mountChecklists } from "./checklist.js";
import { CAPTURE } from "./env.js";

installCapture();
initTheme();
initNav();
mountChecklists();
initReveals();
initMagnetic();
initSpotlight();
shimmer([...document.querySelectorAll("[data-shimmer]")]);

// Cross-document view transitions: skip them in capture mode, and keep the header out
// of the old snapshot when the menu is open so it does not animate half open.
addEventListener("pageswap", (e) => {
  if (!e.viewTransition) return;
  if (CAPTURE) e.viewTransition.skipTransition();
  document.documentElement.classList.remove("menu-open");
});
