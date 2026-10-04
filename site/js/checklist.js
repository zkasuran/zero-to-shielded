// checklist.js: the six-step progress card. Same markup on home, /start/ and episode
// pages (rendered at build time by tools/layout.mjs). Every instance on a page paints
// from the same stored set, so ticking one ticks them all, also across tabs.

import { STEPS } from "./episodes.js";
import { readProgress, writeProgress, onProgress, storageWorks } from "./store.js";
import { burst } from "./fx.js";
import { registerReveal } from "./capture.js";

const K_CLASSES = ["is-k0", "is-k1", "is-k2", "is-k3", "is-k4", "is-k5", "is-k6"];

function paint(root, done) {
  const k = STEPS.filter((s) => done.has(s.id)).length;
  root.classList.remove(...K_CLASSES);
  root.classList.add(`is-k${k}`);
  root.classList.toggle("is-complete", k === STEPS.length);
  root.querySelectorAll(".cl-step").forEach((li) => {
    const on = done.has(li.dataset.stepId);
    li.classList.toggle("is-done", on);
    const btn = li.querySelector("[data-cl-toggle]");
    if (btn) btn.setAttribute("aria-pressed", String(on));
  });
  const doneBox = root.querySelector(".cl-done");
  if (doneBox) doneBox.setAttribute("aria-hidden", String(k !== STEPS.length));
  const live = root.querySelector("[data-cl-live]");
  if (live) live.textContent = k === STEPS.length ? "All 6 steps done. You're shielded." : `${k} of 6 steps done`;
}

// Capture preview: first k steps ticked, nothing saved.
export function preview(root, k) {
  const done = new Set(STEPS.slice(0, Math.min(k, STEPS.length)).map((s) => s.id));
  paint(root, done);
}

export function mountChecklists() {
  const roots = [...document.querySelectorAll("[data-checklist-root]")];
  registerReveal("checklist", (k, section) => {
    const r = section.querySelector("[data-checklist-root]");
    if (r) preview(r, k);
  });
  if (!roots.length) return;

  let done = readProgress();
  const paintAll = () => roots.forEach((r) => paint(r, done));
  paintAll();

  const note = () => {
    if (storageWorks()) return;
    roots.forEach((r) => {
      const n = r.querySelector("[data-cl-note]");
      if (n) n.textContent = "Your browser is not saving ticks, so they last until you close this tab.";
    });
  };
  note();

  for (const root of roots) {
    root.addEventListener("click", (e) => {
      const t = e.target.closest("[data-cl-toggle]");
      if (t) {
        const next = new Set(done);
        const id = t.dataset.clToggle;
        next.has(id) ? next.delete(id) : next.add(id);
        writeProgress(next);
        return;
      }
      if (e.target.closest("[data-cl-reset]")) writeProgress(new Set());
    });
  }

  onProgress((next, prev, info) => {
    done = next;
    paintAll();
    note();
    if (!info.external && next.size === STEPS.length && prev.size < STEPS.length) {
      const target = roots.find((r) => r.getBoundingClientRect().bottom > 0 && r.getBoundingClientRect().top < innerHeight) || roots[0];
      burst(target);
    }
  });
}
