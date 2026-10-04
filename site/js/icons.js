// Small stroke icons drawn for this site (24 x 24). Shared by the page build tool
// (node) and the browser, so every icon in static and rendered markup is the same.
// No style attributes: colour comes from currentColor, sizes from CSS.

const P = {
  play: '<path d="M8 5.6v12.8a.6.6 0 0 0 .9.5l10.2-6.4a.6.6 0 0 0 0-1L8.9 5.1a.6.6 0 0 0-.9.5z" fill="currentColor" stroke="none"/>',
  check: '<path d="M5 12.6l4.4 4.4L19 7.4"/>',
  chevron: '<path d="M6.5 9.5L12 15l5.5-5.5"/>',
  arrow: '<path d="M5 12h13.5M13 6.5l5.5 5.5-5.5 5.5"/>',
  back: '<path d="M19 12H5.5M11 6.5L5.5 12l5.5 5.5"/>',
  sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.8v2.1M12 19.1v2.1M2.8 12h2.1M19.1 12h2.1M5.5 5.5l1.5 1.5M17 17l1.5 1.5M5.5 18.5L7 17M17 7l1.5-1.5"/>',
  moon: '<path d="M19.6 14.6A8.2 8.2 0 0 1 9.4 4.4a8.2 8.2 0 1 0 10.2 10.2z"/>',
  lock: '<rect x="4.8" y="10.6" width="14.4" height="10" rx="2.6"/><path d="M8.2 10.6V7.8a3.8 3.8 0 0 1 7.6 0v2.8"/>',
  eye: '<path d="M2.6 12S6 5.6 12 5.6 21.4 12 21.4 12 18 18.4 12 18.4 2.6 12 2.6 12z"/><circle cx="12" cy="12" r="2.9"/>',
  shield: '<path d="M12 2.9l7.4 2.8v5.6c0 4.8-3.1 8.5-7.4 9.9-4.3-1.4-7.4-5.1-7.4-9.9V5.7z"/>',
  shieldCheck: '<path d="M12 2.9l7.4 2.8v5.6c0 4.8-3.1 8.5-7.4 9.9-4.3-1.4-7.4-5.1-7.4-9.9V5.7z"/><path d="M8.6 12.1l2.4 2.4 4.6-4.8"/>',
  search: '<circle cx="10.8" cy="10.8" r="6.3"/><path d="M15.5 15.5l4.7 4.7"/>',
  book: '<path d="M4.6 5.6a2.4 2.4 0 0 1 2.4-2.4h12.4v14.6H7a2.4 2.4 0 0 0-2.4 2.4z"/><path d="M4.6 20.2a2.4 2.4 0 0 0 2.4 2.4h12.4v-4.8"/>',
  alert: '<path d="M12 3.6l9.4 16.2H2.6z"/><path d="M12 9.6v4.6M12 17.2v.2"/>',
  chat: '<path d="M4.4 5.6h15.2v10.2H11l-4.6 3.8v-3.8h-2z"/>',
  path: '<circle cx="5.6" cy="18.4" r="2.2"/><circle cx="18.4" cy="5.6" r="2.2"/><path d="M7.6 17.4c5.6-1.6 1.8-7.2 7.2-9.8"/>',
  list: '<path d="M10 6.5h10M10 12h10M10 17.5h10"/><path d="M3.8 6.4l1.4 1.4 2.4-2.6M3.8 11.9l1.4 1.4 2.4-2.6M3.8 17.4l1.4 1.4 2.4-2.6"/>',
  phone: '<rect x="6.6" y="2.8" width="10.8" height="18.4" rx="2.8"/><path d="M10.6 18h2.8"/>',
  clock: '<circle cx="12" cy="12" r="8.6"/><path d="M12 7.4V12l3 2"/>',
  pen: '<path d="M14.6 4.6l4.8 4.8L9 19.8l-5.4.6.6-5.4z"/><path d="M12.8 6.4l4.8 4.8"/>',
  external: '<path d="M14 4.4h5.6V10M19.4 4.6L11 13"/><path d="M18 14.2v4.2a1.6 1.6 0 0 1-1.6 1.6H5.6A1.6 1.6 0 0 1 4 18.4V7.6A1.6 1.6 0 0 1 5.6 6h4.2"/>',
  close: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
  reset: '<path d="M4.6 12a7.4 7.4 0 1 0 2.2-5.2"/><path d="M4.4 4.4v4.2h4.2"/>',
  clipboard: '<rect x="5.4" y="4.6" width="13.2" height="16.4" rx="2.4"/><path d="M9.2 4.6V3.4h5.6v1.2"/><path d="M8.8 10h6.4M8.8 13.6h6.4M8.8 17.2h3.6"/>',
  mail: '<rect x="3.4" y="5.4" width="17.2" height="13.2" rx="2.4"/><path d="M4 7l8 6 8-6"/>',
  at: '<circle cx="12" cy="12" r="3.6"/><path d="M15.6 12v1.4a2.6 2.6 0 0 0 5.2 0V12a8.8 8.8 0 1 0-3.4 6.9"/>',
  help: '<circle cx="12" cy="12" r="8.6"/><path d="M9.6 9.4a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.1-2.4 3.6M12 16.8v.2"/>',
  sparkle: '<path d="M12 3.4l1.9 5.6 5.7 1.9-5.7 1.9L12 18.4l-1.9-5.6-5.7-1.9 5.7-1.9z"/>',
  film: '<rect x="3.4" y="5" width="17.2" height="14" rx="2.6"/><path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor"/>',
  key: '<circle cx="8" cy="15.6" r="4"/><path d="M10.9 12.8l8.5-8.5M16.4 7.3l2.4 2.4M14.2 9.5l1.8 1.8"/>',
  scam: '<circle cx="12" cy="12" r="8.6"/><path d="M6 6l12 12"/>',
  trophy: '<path d="M8 4.4h8v5.2a4 4 0 0 1-8 0z"/><path d="M8 6.2H4.8a3 3 0 0 0 3.4 3.6M16 6.2h3.2a3 3 0 0 1-3.4 3.6M12 13.6v3.6M8.6 20.4h6.8M9.6 17.2h4.8v3.2H9.6z"/>',
  flame: '<path d="M12 21.4c-3.8 0-6.6-2.6-6.6-6.2 0-3.4 2.4-5.2 3.6-7.8.6 1.6 1.4 2.6 2.4 3.2.2-2.6 1.4-5.2 3.6-7.2.2 3.4 4.2 6.2 4.2 11.2 0 3.8-3.2 6.8-7.2 6.8z"/>',
};

export function icon(name, cls = "") {
  const body = P[name];
  if (!body) return "";
  const c = cls ? ` class="${cls}"` : "";
  return `<svg${c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${body}</svg>`;
}

// The site mark: a gold shield with a tick. Deliberately not the Zcash or Zodl logo.
export function brandMark(cls = "brand-mark") {
  return `<svg class="${cls}" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><path class="bm-fill" d="M16 2.6l10.6 4v7.6c0 6.6-4.4 11.8-10.6 13.9C9.8 26 5.4 20.8 5.4 14.2V6.6z"/><path class="bm-ink" d="M11 15.6l3.4 3.4 6.6-6.8" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

export const ICON_NAMES = Object.keys(P);
