// capture.js: the hook the video kit drives (tools/video-kit/web.py).
//
// With ?capture=1 the page exposes window.setReveal(k, scope). Inside the section named
// by scope, items carry data-step. setReveal shows the first k of them. It only toggles
// classes (opacity), never layout, because the kit measures item boxes once at full
// reveal and reuses them for every state. Sections can register their own behaviour
// (the checklist ticks its first k steps instead of hiding the rest).

import { CAPTURE } from "./env.js";

const handlers = new Map();

export function registerReveal(sectionId, fn) {
  handlers.set(sectionId, fn);
}

function hideAfter(k, section) {
  section.querySelectorAll("[data-step]").forEach((el, i) => el.classList.toggle("step-off", i >= k));
}

export function installCapture() {
  if (!CAPTURE) return;
  window.setReveal = (k, scope) => {
    const n = Math.max(0, Math.floor(Number(k) || 0));
    const sections = scope
      ? [document.querySelector(scope)].filter(Boolean)
      : [...document.querySelectorAll("[data-capture-section]")];
    for (const section of sections) {
      const fn = handlers.get(section.id) || hideAfter;
      fn(n, section);
    }
    return true;
  };
}
