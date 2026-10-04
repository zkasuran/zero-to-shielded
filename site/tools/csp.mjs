#!/usr/bin/env node
// csp.mjs: one Content-Security-Policy for every page and for vercel.json, with the
// sha256 of every inline script computed from the files themselves so it never drifts.
//
//   node site/tools/csp.mjs           rewrite the meta tag on every page and vercel.json
//   node site/tools/csp.mjs --check   exit 1 if any page or vercel.json is out of date
//
// The meta policy cannot carry frame-ancestors (browsers ignore it there), so only the
// header sent by Vercel adds it. See SECURITY.md.

import { readFileSync, writeFileSync, readdirSync, statSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join, relative } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SITE = join(dirname(fileURLToPath(import.meta.url)), "..");

export function inlineScripts(html) {
  const out = [];
  const re = /<script(\s[^>]*)?>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const attrs = m[1] || "";
    if (/\ssrc\s*=/.test(attrs)) continue;
    out.push(m[2]);
  }
  return out;
}

export const hashOf = (text) => `'sha256-${createHash("sha256").update(text, "utf8").digest("base64")}'`;

export function policy(hashes) {
  return [
    "default-src 'none'",
    `script-src 'self' ${[...hashes].sort().join(" ")}`.trim(),
    "style-src 'self'",
    "img-src 'self' data: https://i.ytimg.com",
    "media-src 'self'",
    "font-src 'self'",
    "connect-src 'self'",
    "frame-src https://www.youtube-nocookie.com",
    "base-uri 'none'",
    "form-action 'none'",
    "object-src 'none'",
  ].join("; ");
}

export function headerPolicy(hashes) {
  return `${policy(hashes)}; frame-ancestors 'none'`;
}

export function htmlFiles(dir = SITE) {
  const out = [];
  for (const name of readdirSync(dir)) {
    if (name.startsWith(".") || name === "node_modules") continue;
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) {
      if (relative(SITE, p) === "tools/partials") continue;
      out.push(...htmlFiles(p));
    } else if (name.endsWith(".html")) out.push(p);
  }
  return out.sort();
}

const META_RE = /<meta http-equiv="Content-Security-Policy" content="[^"]*">/;

export function run({ check = false } = {}) {
  const files = htmlFiles();
  const hashes = new Set();
  for (const f of files) for (const s of inlineScripts(readFileSync(f, "utf8"))) hashes.add(hashOf(s));
  const meta = `<meta http-equiv="Content-Security-Policy" content="${policy(hashes)}">`;
  const stale = [];
  for (const f of files) {
    const html = readFileSync(f, "utf8");
    if (!META_RE.test(html)) { stale.push(`${relative(SITE, f)} (no CSP meta)`); continue; }
    const next = html.replace(META_RE, meta);
    if (next !== html) {
      stale.push(relative(SITE, f));
      if (!check) writeFileSync(f, next);
    }
  }
  const vpath = join(SITE, "vercel.json");
  const vercel = JSON.parse(readFileSync(vpath, "utf8"));
  const all = vercel.headers.find((h) => h.source === "/(.*)");
  const entry = all && all.headers.find((h) => h.key === "Content-Security-Policy");
  if (!entry) throw new Error("vercel.json: no Content-Security-Policy header on /(.*)");
  const want = headerPolicy(hashes);
  if (entry.value !== want) {
    stale.push("vercel.json");
    entry.value = want;
    if (!check) writeFileSync(vpath, `${JSON.stringify(vercel, null, 2)}\n`);
  }
  return { files: files.length, hashes: [...hashes], stale, policy: policy(hashes) };
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  const check = process.argv.includes("--check");
  const r = run({ check });
  if (check && r.stale.length) {
    console.error(`csp: out of date: ${r.stale.join(", ")}\nRun: node site/tools/csp.mjs`);
    process.exit(1);
  }
  console.log(`csp: ${r.files} pages, ${r.hashes.length} inline script hash(es)${r.stale.length && !check ? `, updated ${r.stale.length}` : ", in sync"}`);
}
