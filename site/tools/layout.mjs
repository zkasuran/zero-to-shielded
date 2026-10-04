#!/usr/bin/env node
// layout.mjs: keep the shared head, header and footer identical on every page.
//
// Each page marks regions with <!-- @head --> ... <!-- /@head --> (and @meta, @header,
// @footer). This tool rewrites those regions from one source, marks the current page in
// the menu, writes the six episode pages from js/episodes.js and turns root links
// ("/tools/") into relative ones ("../../tools/") so the site works at a domain root
// (Vercel) and under a sub path (GitHub Pages) alike. 404.html keeps root links because
// it is served at any depth. Run from anywhere: `node site/tools/layout.mjs`.

import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const SITE = join(dirname(fileURLToPath(import.meta.url)), "..");
const SITE_URL = "https://zero-to-shielded.vercel.app";

const { EPISODES, STEPS, formatTime } = await import(pathToFileURL(join(SITE, "js/episodes.js")).href);
const { icon, brandMark } = await import(pathToFileURL(join(SITE, "js/icons.js")).href);
const M = await import(pathToFileURL(join(SITE, "js/markup.js")).href);
const { policy, hashOf } = await import(pathToFileURL(join(SITE, "tools/csp.mjs")).href);

// The cast (Maya, Sam, the Watcher) comes from js/cast.js, written by the lead. Until
// that file exists each slot gets a plain initial so the layout holds. Style attributes
// in the returned SVG are turned into presentation attributes, because the CSP allows
// no inline styles.
const CAST_FILE = join(SITE, "js/cast.js");
let CAST = null;
if (existsSync(CAST_FILE)) {
  try {
    const mod = await import(pathToFileURL(CAST_FILE).href);
    CAST = mod && typeof mod.maya !== "function" && mod.default ? mod.default : mod;
  } catch (err) {
    console.warn(`layout: js/cast.js could not be loaded in node (${err.message}); using initials`);
  }
}
const CAST_NAMES = { maya: "Maya", sam: "Sam", watcher: "The Watcher" };

function presentational(svg) {
  return String(svg)
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/\son\w+="[^"]*"/gi, "")
    .replace(/\sstyle="([^"]*)"/gi, (m, css) => css.split(";").map((d) => d.trim()).filter(Boolean).map((d) => {
      const i = d.indexOf(":");
      if (i < 0) return "";
      const k = d.slice(0, i).trim().toLowerCase();
      const v = d.slice(i + 1).trim().replace(/"/g, "'");
      return /^[a-z-]+$/.test(k) ? ` ${k}="${v}"` : "";
    }).join(""));
}

export function castMarkup(name, size = "md") {
  const label = CAST_NAMES[name] || name;
  const cls = `cast cast--${size} cast--${name}`;
  const fn = CAST && typeof CAST[name] === "function" ? CAST[name] : null;
  if (fn) {
    try {
      const svg = fn({ size: size === "lg" ? 96 : size === "sm" ? 44 : 64, theme: "auto", label: false });
      if (typeof svg === "string" && svg.includes("<svg")) {
        return `<span class="${cls}" role="img" aria-label="${label}">${presentational(svg).replace(/<svg\b/, '<svg aria-hidden="true" focusable="false"')}</span>`;
      }
    } catch (err) {
      console.warn(`layout: cast.${name}() failed: ${err.message}`);
    }
  }
  const inner = name === "watcher" ? icon("eye") : esc(label[0]);
  return `<span class="${cls}" role="img" aria-label="${label}"><span class="avatar avatar--${name}" aria-hidden="true">${inner}</span></span>`;
}

// Which media files exist decides what each player shows (see README-DEPLOY.md).
export function mediaSet() {
  const dir = join(SITE, "media");
  if (!existsSync(dir)) return new Set();
  return new Set(readdirSync(dir).filter((f) => /^zts-e\d\.(mp4|jpg|srt)$/.test(f)));
}

// Sets data-theme before first paint. Its sha256 goes into the CSP (tools/csp.mjs).
// ?theme=dark|light forces a theme without saving it. ?capture=1 marks the page for the
// video kit: no view transitions, no motion, final states only.
export const THEME_SCRIPT = `(function(){var d=document.documentElement,q,t,s=null;try{q=new URLSearchParams(location.search)}catch(e){q=new URLSearchParams("")}t=q.get("theme");if(t==="dark"||t==="light"){d.setAttribute("data-theme-forced","")}else{try{s=localStorage.getItem("zts-theme")}catch(e){}t=(s==="dark"||s==="light")?s:((window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches)?"light":"dark")}d.setAttribute("data-theme",t);if(q.get("capture")==="1"){d.setAttribute("data-capture","");addEventListener("pagereveal",function(e){if(e.viewTransition){e.viewTransition.skipTransition()}})}})();`;

export const PAGES = [
  { file: "index.html", path: "/" },
  { file: "start/index.html", path: "/start/" },
  { file: "episodes/index.html", path: "/episodes/" },
  ...EPISODES.map((e) => ({ file: `episodes/${e.id}/index.html`, path: `/episodes/${e.id}/`, episode: e.id })),
  { file: "tools/address/index.html", path: "/tools/address/" },
  { file: "tools/chain/index.html", path: "/tools/chain/" },
  { file: "learn/phrase-guard/index.html", path: "/learn/phrase-guard/" },
  { file: "help/index.html", path: "/help/" },
  { file: "404.html", path: "/404.html", rootLinks: true, noindex: true },
];

const NAV = [
  {
    id: "start", label: "Start", match: "/start/",
    links: [
      { href: "/start/#path", title: "The 5-step path", desc: "Watch, do it, tick it. In order.", ico: icon("path") },
      { href: "/start/#need", title: "What you need", desc: "A phone, 15 minutes, a pen and paper.", ico: icon("list") },
    ],
    foot: { text: "New here?", href: "/episodes/e1/", label: "Start episode 1" },
  },
  {
    id: "episodes", label: "Episodes", match: "/episodes/", wide: true,
    links: EPISODES.map((e) => ({
      href: `/episodes/${e.id}/`, title: e.short, desc: `Episode ${e.number}, about ${e.length}`, num: `E${e.number}`,
    })),
    foot: { text: "Five videos and a trailer", href: "/episodes/", label: "All episodes" },
  },
  {
    id: "tools", label: "Tools", match: "/tools/",
    links: [
      { href: "/tools/address/", title: "Address checker", desc: "Paste an address. See if it is shielded.", ico: icon("search") },
      { href: "/tools/chain/", title: "What the blockchain sees", desc: "A diagram of one private payment.", ico: icon("eye") },
    ],
  },
  {
    id: "learn", label: "Learn", match: "/learn/",
    links: [
      { href: "/learn/phrase-guard/", title: "Phrase Guard", desc: "Six quick scam checks. Safe or scam?", ico: icon("shieldCheck") },
    ],
  },
  {
    id: "help", label: "Help", match: "/help/",
    links: [
      { href: "/help/#glossary", title: "Glossary", desc: "Every word, in plain English.", ico: icon("book") },
      { href: "/help/#mistakes", title: "Common mistakes", desc: "Four slips and how to avoid them.", ico: icon("alert") },
      { href: "/help/#support", title: "Get support", desc: "Official Zodl help only.", ico: icon("help") },
    ],
  },
];

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function head() {
  return [
    `<meta charset="utf-8">`,
    `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`,
    `<meta http-equiv="Content-Security-Policy" content="${policy(new Set([hashOf(THEME_SCRIPT)]))}">`,
    `<meta name="referrer" content="no-referrer">`,
    `<meta name="color-scheme" content="dark light">`,
    `<meta name="theme-color" content="#0B0F1A" media="(prefers-color-scheme: dark)">`,
    `<meta name="theme-color" content="#FBF8F1" media="(prefers-color-scheme: light)">`,
    `<script>${THEME_SCRIPT}</script>`,
    `<link rel="preload" href="/fonts/InterVariable.woff2" as="font" type="font/woff2" crossorigin>`,
    `<link rel="stylesheet" href="/css/site.css">`,
    `<link rel="icon" href="/favicon.svg" type="image/svg+xml">`,
    `<link rel="modulepreload" href="/js/main.js">`,
  ].join("\n");
}

function meta(page, title, description) {
  const url = SITE_URL + (page.path === "/404.html" ? "/" : page.path);
  const lines = [
    `<link rel="canonical" href="${url}">`,
    `<meta property="og:type" content="website">`,
    `<meta property="og:site_name" content="Zero to Shielded">`,
    `<meta property="og:title" content="${esc(title)}">`,
    `<meta property="og:description" content="${esc(description)}">`,
    `<meta property="og:url" content="${url}">`,
    `<meta property="og:image" content="${SITE_URL}/img/og.png">`,
    `<meta property="og:image:width" content="1200">`,
    `<meta property="og:image:height" content="630">`,
    `<meta property="og:image:alt" content="Zero to Shielded: your first private Zcash payment in 15 minutes.">`,
    `<meta name="twitter:card" content="summary_large_image">`,
  ];
  if (page.noindex) lines.unshift(`<meta name="robots" content="noindex">`);
  return lines.join("\n");
}

function header(page) {
  const items = NAV.map((cat) => {
    const current = page.path.startsWith(cat.match);
    const links = cat.links.map((l) => {
      const here = l.href === page.path ? ` aria-current="page"` : "";
      const lead = l.num ? `<span class="nl-icon">${l.num}</span>` : `<span class="nl-icon">${l.ico}</span>`;
      return `<li><a href="${l.href}"${here}>${lead}<span class="nl-title">${esc(l.title)}</span><span class="nl-desc">${esc(l.desc)}</span></a></li>`;
    }).join("\n");
    const foot = cat.foot
      ? `<div class="nav-foot"><span>${esc(cat.foot.text)}</span><a class="link-arrow" href="${cat.foot.href}">${esc(cat.foot.label)}${icon("arrow")}</a></div>`
      : "";
    return `<li class="nav-item" data-nav-item="${cat.id}">
<button class="nav-trigger${current ? " is-current" : ""}" type="button" aria-expanded="false" aria-controls="nav-${cat.id}">${cat.label}${icon("chevron")}</button>
<div class="nav-panel${cat.wide ? " nav-panel--wide" : ""}" id="nav-${cat.id}">
<div class="nav-card">
<ul class="nav-links">
${links}
</ul>
${foot}
</div>
</div>
</li>`;
  }).join("\n");

  return `<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
<div class="wrap header-bar">
<a class="brand" href="/"${page.path === "/" ? ` aria-current="page"` : ""}>${brandMark()}<span class="brand-name">Zero to Shielded</span></a>
<nav class="nav" id="site-nav" aria-label="Main">
<ul class="nav-list">
${items}
</ul>
</nav>
<div class="header-actions">
<button class="icon-btn theme-toggle" type="button" data-theme-toggle aria-label="Change theme">${icon("sun", "i-sun")}${icon("moon", "i-moon")}</button>
<button class="icon-btn menu-toggle" type="button" data-menu-toggle aria-expanded="false" aria-controls="site-nav" aria-label="Open menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true" focusable="false"><path class="bar bar-1" d="M4.5 7h15"/><path class="bar bar-2" d="M4.5 12h15"/><path class="bar bar-3" d="M4.5 17h15"/></svg></button>
</div>
</div>
</header>`;
}

function footer(page) {
  const col = (title, links) => `<div><h2>${title}</h2><ul>${links.map((l) =>
    `<li><a href="${l.href}"${l.href === page.path ? ` aria-current="page"` : ""}${l.ext ? ` rel="noopener noreferrer"` : ""}>${esc(l.label)}</a></li>`).join("")}</ul></div>`;
  return `<footer class="site-footer">
<div class="wrap">
<div class="footer-grid">
<div class="footer-brand">
<a class="brand" href="/">${brandMark()}<span class="brand-name">Zero to Shielded</span></a>
<p>Five short videos and a few small tools. They take you from no wallet to your first shielded Zcash payment with Zodl.</p>
</div>
<nav class="footer-nav" aria-label="Footer">
${col("Start", [{ href: "/start/", label: "The 5-step path" }, { href: "/start/#need", label: "What you need" }, { href: "/#checklist", label: "Your checklist" }])}
${col("Episodes", EPISODES.map((e) => ({ href: `/episodes/${e.id}/`, label: `E${e.number} ${e.short}` })))}
${col("Tools", [{ href: "/tools/address/", label: "Address checker" }, { href: "/tools/chain/", label: "What the blockchain sees" }, { href: "/learn/phrase-guard/", label: "Phrase Guard" }])}
${col("Help", [{ href: "/help/#glossary", label: "Glossary" }, { href: "/help/#mistakes", label: "Common mistakes" }, { href: "/help/#support", label: "Get support" }, { href: "https://support.zodl.com/", label: "Zodl support", ext: true }])}
</nav>
</div>
<div class="footer-legal">
<p class="no-track">${icon("shieldCheck")}No tracking. No cookies. No analytics.</p>
<p>Scripts, narration and editing were produced with AI assistance (Kiro). Narration is a synthesised voice.</p>
<p>An independent guide for the ZECATHON. It is not made by Zodl. Code under LicenseRef-zkasuran-SAND-1.0. Videos under CC BY-ND 4.0.</p>
</div>
</div>
</footer>`;
}

// ---------- episode pages ----------

function stepNames(ids) {
  return ids.map((id) => STEPS.find((s) => s.id === id).label);
}

function episodePage(e) {
  const i = EPISODES.indexOf(e);
  const next = EPISODES[i + 1] || null;
  const prev = EPISODES[i - 1] || null;
  const names = stepNames(e.steps);
  const ticks = names.length
    ? `<span class="chip chip--gold">${icon("check")}Ticks ${names.map(esc).join(" and ")}</span>`
    : "";
  const didIt = names.length
    ? `<button class="btn btn--primary btn--lg" type="button" data-did-it="${e.id}" aria-pressed="false">${icon("check")}<span data-did-label>I did it</span><span class="btn-shine" aria-hidden="true"></span></button>`
    : "";
  const nextBtn = next
    ? `<a class="btn btn--lg${names.length ? "" : " btn--primary"}" href="/episodes/${next.id}/">Next episode${icon("arrow")}</a>`
    : `<a class="btn btn--lg" href="/tools/address/">Try the address checker${icon("arrow")}</a>`;
  const title = `${e.title} · Zero to Shielded`;
  const desc = e.summary.split(". ").slice(0, 2).join(". ").replace(/\.?$/, ".");

  return `<!doctype html>
<html lang="en" data-theme="dark">
<head>
<!-- @head -->
<!-- /@head -->
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<!-- @meta -->
<!-- /@meta -->
</head>
<body data-page="episode">
<!-- @header -->
<!-- /@header -->
<main id="main" tabindex="-1" data-episode="${e.id}">
<section class="section ep-hero">
<div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/episodes/">Episodes</a><span aria-hidden="true">/</span><span aria-current="page">Episode ${e.number}</span></nav>
<div class="ep-head">
<span class="ep-badge vt-num-${e.id}" aria-hidden="true">E${e.number}</span>
<div>
<p class="eyebrow">Episode ${e.number} · about ${e.length}</p>
<h1 class="h1 ep-title vt-title-${e.id}">${esc(e.title)}</h1>
</div>
</div>
<p class="lede ep-summary">${esc(e.summary)}</p>
<div class="ep-meta">${ticks}<span class="chip">${icon("sparkle")}${esc(e.outcome)}</span></div>
</div>
</section>
<section class="section section--tight ep-watch" aria-label="Video and chapters">
<div class="wrap ep-grid">
<div class="ep-main">
<!-- @player:${e.id} -->
<!-- /@player -->
<div class="ep-actions">
${didIt}
${nextBtn}
<p class="ep-did-note small soft" data-did-note aria-live="polite"></p>
</div>
<p class="credits small soft">Scripts, narration and editing were produced with AI assistance (Kiro). Narration is a synthesised voice. The video is licensed <a href="https://creativecommons.org/licenses/by-nd/4.0/" rel="noopener noreferrer">CC BY-ND 4.0</a>.</p>
</div>
<aside class="ep-side card" aria-labelledby="chapters-title">
<div class="ep-side-head"><h2 class="h3" id="chapters-title">Chapters</h2><span class="chip" data-chapter-note>Draft times</span></div>
<ol class="chapters" data-chapters="${e.id}">
<!-- @chapters:${e.id} -->
<!-- /@chapters -->
</ol>
<p class="small soft chapters-hint" data-chapter-hint>Chapter buttons jump the video once it is live.</p>
</aside>
</div>
</section>
${names.length || e.id === "e5" ? `<section class="section" id="progress" aria-labelledby="progress-title">
<div class="wrap">
<div class="section-head"><div><h2 class="h2" id="progress-title">Your progress</h2><p>Tick each step when you have done it in the app. Your ticks stay in this browser only.</p></div></div>
<div data-checklist>
<!-- @checklist:compact -->
<!-- /@checklist -->
</div>
</div>
</section>` : ""}
<section class="section" id="transcript" aria-labelledby="transcript-title" hidden>
<div class="wrap">
<div class="transcript card">
<div class="transcript-head"><h2 class="h2" id="transcript-title">Transcript</h2><p class="soft small">From the captions file. Tap a time to jump there.</p></div>
<div class="transcript-body" data-transcript="${e.id}"></div>
</div>
</div>
</section>
<section class="section section--tight">
<div class="wrap ep-pager">
${prev ? `<a class="pager-link" href="/episodes/${prev.id}/">${icon("back")}<span><span class="small soft">Previous</span><span class="pager-title">E${prev.number} ${esc(prev.short)}</span></span></a>` : `<span></span>`}
${next ? `<a class="pager-link pager-link--next" href="/episodes/${next.id}/"><span><span class="small soft">Next</span><span class="pager-title">E${next.number} ${esc(next.short)}</span></span>${icon("arrow")}</a>` : `<a class="pager-link pager-link--next" href="/start/"><span><span class="small soft">Done?</span><span class="pager-title">Back to the 5-step path</span></span>${icon("arrow")}</a>`}
</div>
</section>
</main>
<!-- @footer -->
<!-- /@footer -->
<script type="module" src="/js/main.js"></script>
<script type="module" src="/js/pages/episode.js"></script>
</body>
</html>
`;
}

// ---------- region rewriting ----------

function replaceRegion(html, name, body, file) {
  const re = new RegExp(`<!-- @${name} -->[\\s\\S]*?<!-- /@${name} -->`);
  if (!re.test(html)) throw new Error(`${file}: missing <!-- @${name} --> region`);
  return html.replace(re, `<!-- @${name} -->\n${body}\n<!-- /@${name} -->`);
}

// Optional data regions: <!-- @name:arg --> ... <!-- /@name -->
function fillData(html, media) {
  const byId = (id) => {
    const e = EPISODES.find((x) => x.id === id);
    if (!e) throw new Error(`unknown episode ${id}`);
    return e;
  };
  const fill = {
    checklist: (arg) => M.checklistMarkup({ variant: arg || "full" }),
    cards: () => M.episodeCards(media),
    player: (arg) => M.playerMarkup(byId(arg), media),
    "hero-player": (arg) => M.playerMarkup(byId(arg || "e1"), media, { hero: true }),
    chapters: (arg) => M.chapterItems(byId(arg), { enabled: false }),
    examples: () => M.checkerExamples(),
    kinds: () => M.kindsMarkup(),
    cast: (arg) => { const [who, size] = String(arg || "maya").split("-"); return castMarkup(who, size || "md"); },
  };
  return html.replace(/<!-- @([a-z-]+)(?::([\w-]+))? -->[\s\S]*?<!-- \/@\1 -->/g, (m, name, arg) => {
    if (!fill[name]) return m;
    return `<!-- @${name}${arg ? ":" + arg : ""} -->\n${fill[name](arg)}\n<!-- /@${name} -->`;
  });
}

// Media is cached for a day (vercel.json), so a changed poster or captions file needs a new
// URL: append ?v=<first 10 hex of its sha256>. Re-run the build after replacing any media file.
function versionMedia(html) {
  return html.replace(/\b(src|poster|data-srt)="([^"?]*media\/(zts-e\d\.(?:jpg|srt|mp4)))(?:\?v=[0-9a-f]+)?"/g, (m, attr, url, name) => {
    const f = join(SITE, "media", name);
    if (!existsSync(f)) return m;
    const v = createHash("sha256").update(readFileSync(f)).digest("hex").slice(0, 10);
    return `${attr}="${url}?v=${v}"`;
  });
}

function relativize(html, file) {
  const depth = file.split("/").length - 1;
  const prefix = depth === 0 ? "./" : "../".repeat(depth);
  return html.replace(/\b(href|src|poster)="\/(?!\/)([^"]*)"/g, (m, attr, rest) => `${attr}="${prefix}${rest}"`);
}

export function build({ write = true } = {}) {
  const out = [];
  const media = mediaSet();
  const rendered = new Map();
  for (const e of EPISODES) {
    rendered.set(`episodes/${e.id}/index.html`, episodePage(e));
  }
  for (const page of PAGES) {
    const file = join(SITE, page.file);
    if (!rendered.has(page.file) && !existsSync(file)) { console.warn(`layout: skip missing ${page.file}`); continue; }
    let html = rendered.get(page.file) ?? readFileSync(file, "utf8");
    const title = (html.match(/<title>([^<]*)<\/title>/) || [, "Zero to Shielded"])[1].replace(/&amp;/g, "&");
    const description = (html.match(/<meta name="description" content="([^"]*)">/) || [, ""])[1].replace(/&amp;/g, "&").replace(/&quot;/g, '"');
    html = replaceRegion(html, "head", head(), page.file);
    html = replaceRegion(html, "meta", meta(page, title, description), page.file);
    html = replaceRegion(html, "header", header(page), page.file);
    html = replaceRegion(html, "footer", footer(page), page.file);
    html = fillData(html, media);
    if (!page.rootLinks) html = relativize(html, page.file);
    html = versionMedia(html);
    if (write) { mkdirSync(dirname(file), { recursive: true }); writeFileSync(file, html); }
    out.push({ file: page.file, html });
  }
  return out;
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  const done = build();
  console.log(`layout: ${done.length} pages`);
}
