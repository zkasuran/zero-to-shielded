// store.js: progress ticks in localStorage, read defensively.
// Storage can be missing, full, blocked (private mode, sandboxed iframes) or hold junk
// from an older version. None of that may break the page: parse, validate the shape,
// keep only known step ids, and fall back to memory for this visit.
// The pure parts (parseProgress, serializeProgress) are tested in node.

import { STEPS } from "./episodes.js";

export const PROGRESS_KEY = "zts-progress";
const IDS = STEPS.map((s) => s.id);
const VALID = new Set(IDS);
const MAX_RAW = 4096;

export function parseProgress(raw) {
  if (typeof raw !== "string" || raw.length === 0 || raw.length > MAX_RAW) return new Set();
  let data;
  try { data = JSON.parse(raw); } catch { return new Set(); }
  if (!data || typeof data !== "object" || Array.isArray(data)) return new Set();
  if (data.v !== 1 || !Array.isArray(data.done)) return new Set();
  const out = new Set();
  for (const id of data.done.slice(0, 32)) if (typeof id === "string" && VALID.has(id)) out.add(id);
  return out;
}

export function serializeProgress(done) {
  return JSON.stringify({ v: 1, done: IDS.filter((id) => done.has(id)) });
}

let memory = null;
let persistent = true;

function storage() {
  try { return typeof window !== "undefined" ? window.localStorage : null; } catch { return null; }
}

export function storageWorks() {
  return persistent;
}

export function readProgress() {
  if (memory) return new Set(memory);
  const s = storage();
  if (!s) { persistent = false; return new Set(); }
  try { return parseProgress(s.getItem(PROGRESS_KEY)); } catch { persistent = false; return new Set(); }
}

export function writeProgress(done) {
  const prev = readProgress();
  const next = new Set([...done].filter((id) => VALID.has(id)));
  memory = new Set(next);
  let ok = false;
  const s = storage();
  if (s) {
    try { s.setItem(PROGRESS_KEY, serializeProgress(next)); ok = true; memory = null; } catch { ok = false; }
  }
  persistent = ok;
  document.dispatchEvent(new CustomEvent("zts:progress", { detail: { done: [...next], prev: [...prev], saved: ok } }));
  return ok;
}

export function onProgress(fn) {
  document.addEventListener("zts:progress", (e) => fn(new Set(e.detail.done), new Set(e.detail.prev), e.detail));
  // other tabs
  window.addEventListener("storage", (e) => {
    if (e.key !== PROGRESS_KEY && e.key !== null) return;
    const next = readProgress();
    fn(next, next, { saved: true, external: true });
  });
}

// Small generic helpers for other keys (theme, best streak). Never throw.
export function getItem(key) {
  const s = storage();
  try { return s ? s.getItem(key) : null; } catch { return null; }
}
export function setItem(key, value) {
  const s = storage();
  try { if (s) { s.setItem(key, value); return true; } } catch { /* quota or blocked */ }
  return false;
}
