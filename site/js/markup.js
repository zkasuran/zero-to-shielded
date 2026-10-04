// markup.js: HTML for the parts that repeat across pages. Pure functions that return
// strings, used by tools/layout.mjs at build time (so pages work and capture without
// waiting for JS) and by the browser when it needs to re-render. No style attributes.

import { EPISODES, STEPS, formatTime } from "./episodes.js";
import { icon, brandMark } from "./icons.js";
import { classify, KINDS, shorten } from "./address.js";
import { CHECKER_EXAMPLES } from "./examples.js";

export const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// "/media/zts-e1.mp4" -> "zts-e1.mp4"
export const mediaName = (p) => String(p || "").replace(/^\/?media\//, "");

const YT_ID = /^[A-Za-z0-9_-]{11}$/;

// ---------- progress checklist ----------

export function checklistMarkup({ variant = "full" } = {}) {
  const steps = STEPS.map((s, i) => {
    const ep = EPISODES.find((e) => e.id === s.episode);
    return `<li class="cl-step" data-step data-step-id="${s.id}">
<button class="cl-toggle" type="button" aria-pressed="false" data-cl-toggle="${s.id}">
<span class="cl-box" aria-hidden="true"><span class="cl-n tnum">${i + 1}</span>${icon("check", "cl-tick")}</span>
<span class="cl-label">${esc(s.label)}</span>
</button>
<a class="cl-ep" href="/episodes/${ep.id}/">Episode ${ep.number}</a>
</li>`;
  }).join("\n");
  return `<div class="checklist checklist--${variant} is-k0" data-checklist-root>
<div class="cl-status">
<div class="cl-progress">
<p class="cl-count"><span class="cl-num tnum" aria-hidden="true"></span><span class="cl-of" aria-hidden="true">of 6 steps done</span><span class="sr-only" data-cl-live aria-live="polite"></span></p>
<div class="cl-bar" aria-hidden="true"><span class="cl-fill"></span></div>
</div>
<div class="cl-done" aria-hidden="true">
<span class="cl-badge">${brandMark("cl-mark")}</span>
<p class="cl-done-text"><strong>You're shielded.</strong> <span>All six steps done. You made your first private payment.</span></p>
</div>
</div>
<ol class="cl-steps">
${steps}
</ol>
<div class="cl-foot"><p class="small soft cl-note" data-cl-note>Saved in this browser only.</p><button class="btn btn--ghost btn--sm cl-reset" type="button" data-cl-reset>${icon("reset")}Clear ticks</button></div>
</div>`;
}

// ---------- episode cards ----------

export function episodeCard(e, media = new Set()) {
  const poster = media.has(mediaName(e.poster));
  const art = poster
    ? `<img src="${e.poster}" alt="" loading="lazy" decoding="async" width="640" height="360">`
    : `<span class="ep-art-num" aria-hidden="true">${e.number}</span><span class="ep-art-mark" aria-hidden="true">${brandMark("ep-art-shield")}</span>`;
  return `<li class="ep-item"><a class="ep-card" href="/episodes/${e.id}/" data-ep="${e.id}">
<span class="ep-art${poster ? " has-img" : ""}">${art}<span class="ep-play" aria-hidden="true">${icon("play")}</span></span>
<span class="ep-body">
<span class="ep-kicker"><span class="ep-badge ep-badge--sm vt-num-${e.id}">E${e.number}</span><span class="ep-len tnum">${icon("clock")}${esc(e.length)}</span><span class="ep-done chip chip--gold" data-ep-done hidden>${icon("check")}Done</span></span>
<span class="ep-name vt-title-${e.id}">${esc(e.title)}</span>
</span>
</a></li>`;
}

export function episodeCards(media) {
  return `<ol class="ep-row" role="list">\n${EPISODES.map((e) => episodeCard(e, media)).join("\n")}\n</ol>`;
}

// ---------- player ----------
// Order of preference: YouTube (nocookie, loaded on click), the self-hosted mp4, then
// the poster or a drawn title card. Nothing third party loads until you press play.

export function playerMarkup(e, media = new Set(), { hero = false } = {}) {
  const has = (p) => media.has(mediaName(p));
  const poster = has(e.poster) ? e.poster : null;
  const srt = has(e.srt) ? ` data-srt="${e.srt}"` : "";
  const cls = `player${hero ? " player--hero" : ""}`;
  const label = `Episode ${e.number}: ${e.title}`;

  if (e.youtubeId && YT_ID.test(e.youtubeId)) {
    const thumb = poster || `https://i.ytimg.com/vi/${e.youtubeId}/hqdefault.jpg`;
    return `<div class="${cls}" data-player="${e.id}" data-mode="youtube" data-youtube="${e.youtubeId}"${srt}>
<button class="player-facade" type="button" data-yt-play aria-label="Play ${esc(label)}. Loads the player from youtube-nocookie.com.">
<img src="${thumb}" alt="" width="1280" height="720" decoding="async">
<span class="player-play" aria-hidden="true">${icon("play")}</span>
<span class="player-note">Plays from youtube-nocookie.com</span>
</button>
</div>`;
  }
  if (has(e.mp4)) {
    return `<div class="${cls}" data-player="${e.id}" data-mode="video"${srt}>
<video class="player-video" controls preload="metadata" playsinline${poster ? ` poster="${poster}"` : ""} src="${e.mp4}" aria-label="${esc(label)}"></video>
</div>`;
  }
  const tag = hero ? "a" : "div";
  const href = hero ? ` href="/episodes/${e.id}/" aria-label="Open episode ${e.number}: ${esc(e.title)}"` : "";
  const art = poster
    ? `<img class="pp-img" src="${poster}" alt="" width="1280" height="720" decoding="async">`
    : `<span class="pp-glow" aria-hidden="true"></span><span class="pp-num" aria-hidden="true">${e.number}</span>
<span class="pp-text"><span class="pp-kicker">Episode ${e.number} · about ${esc(e.length)}</span><span class="pp-title">${esc(e.short)}</span></span>`;
  return `<div class="${cls}" data-player="${e.id}" data-mode="poster"${srt}>
<${tag} class="pp${poster ? " pp--img" : ""}"${href}>
${art}
<span class="player-play" aria-hidden="true">${icon("play")}</span>
<span class="pp-status chip">${icon("film")}Video coming soon</span>
</${tag}>
</div>`;
}

// ---------- chapters ----------

export function chapterItems(e, { enabled = false } = {}) {
  return e.chapters.map((c) =>
    `<li><button class="chapter" type="button" data-t="${c.t}"${enabled ? "" : " disabled"}><span class="chapter-t tnum">${formatTime(c.t)}</span><span class="chapter-title">${esc(c.title)}</span></button></li>`).join("\n");
}

// ---------- address checker demo rows ----------

export function verdictChip(r) {
  if (!r.valid && r.kind !== "unified" && r.kind !== "sapling" && !KINDS[r.kind]) {
    return `<span class="chip chip--danger">${icon("alert")}Not an address</span>`;
  }
  if (r.shielded === true) return `<span class="chip chip--gold">${icon("lock")}Shielded</span>`;
  if (r.shielded === false) return `<span class="chip chip--clear">${icon("eye")}Transparent</span>`;
  return `<span class="chip chip--danger">${icon("alert")}Not an address</span>`;
}

export function kindsMarkup() {
  const order = ["unified", "sapling", "p2pkh", "p2sh", "tex"];
  return `<ul class="kinds reveal-stagger">\n${order.map((k) => {
    const m = KINDS[k];
    const chip = m.shielded
      ? `<span class="chip chip--gold">${icon("lock")}Shielded</span>`
      : `<span class="chip chip--clear">${icon("eye")}Transparent</span>`;
    return `<li class="kind kind--${m.shielded ? "gold" : "clear"}">
<div class="kind-top"><span class="kind-prefix">${m.prefix}</span>${chip}</div>
<h3 class="h3">${esc(m.label)}</h3>
<p>${esc(m.explain)}</p>
${m.limit ? `<p class="kind-limit small">${esc(m.limit)}</p>` : ""}
<p class="kind-enc small soft">Checksum: ${esc(m.encoding)}</p>
</li>`;
  }).join("\n")}\n</ul>`;
}

export function checkerExamples() {
  return CHECKER_EXAMPLES.map((x) => {
    const r = classify(x.addr);
    if (!r.valid) throw new Error(`example ${x.id} does not validate: ${r.reason}`);
    const meta = KINDS[r.kind];
    return `<div class="ck-row ck-example" data-step data-example="${x.id}">
<div class="ck-ex-main">
<span class="ck-ex-tag">Example</span>
<code class="ck-addr" title="${x.addr}">${esc(shorten(x.addr, x.addr.length > 60 ? 16 : 40, 10))}</code>
</div>
<div class="ck-ex-result">
<span class="ck-kind">${esc(meta.label)}</span>
${verdictChip(r)}
<span class="ck-sum">${icon("check")}Checksum OK</span>
</div>
<button class="btn btn--sm ck-try" type="button" data-try="${x.addr}">Check it${icon("arrow")}</button>
</div>`;
  }).join("\n");
}
