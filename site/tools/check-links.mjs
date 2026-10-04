#!/usr/bin/env node
// check-links.mjs: every internal link, script, stylesheet, image and module import in
// site/ must point at a file that exists, and every #fragment at an id on that page.
//   node site/tools/check-links.mjs     (exit 1 and a list when something is broken)

import { readFileSync, existsSync, statSync, readdirSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SITE = resolve(join(dirname(fileURLToPath(import.meta.url)), ".."));

function walk(dir, ext, out = []) {
  for (const name of readdirSync(dir)) {
    if (name.startsWith(".") || name === "node_modules") continue;
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, ext, out);
    else if (ext.some((e) => name.endsWith(e))) out.push(p);
  }
  return out;
}

const idCache = new Map();
function idsOf(file) {
  if (!idCache.has(file)) {
    const html = readFileSync(file, "utf8");
    idCache.set(file, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])));
  }
  return idCache.get(file);
}

function targetFile(fromFile, url, rootRelative) {
  const clean = url.split("#")[0].split("?")[0];
  let p;
  if (clean === "") p = fromFile;
  else if (clean.startsWith("/")) p = join(SITE, clean);
  else p = resolve(dirname(fromFile), clean);
  if (clean.endsWith("/") || (existsSync(p) && statSync(p).isDirectory())) p = join(p, "index.html");
  return p;
}

const SKIP = /^(https?:|mailto:|tel:|data:|javascript:|blob:)/i;

export function checkLinks() {
  const broken = [];
  let count = 0;
  for (const file of walk(SITE, [".html"])) {
    if (relative(SITE, file).startsWith(`tools${sep}partials`)) continue;
    const html = readFileSync(file, "utf8");
    for (const m of html.matchAll(/\s(href|src|poster|data-srt)="([^"]*)"/g)) {
      const url = m[2];
      if (!url || SKIP.test(url)) continue;
      count++;
      const target = targetFile(file, url);
      if (!target.startsWith(SITE) || !existsSync(target)) {
        broken.push(`${relative(SITE, file)}: ${m[1]}="${url}" -> missing ${relative(SITE, target)}`);
        continue;
      }
      const hash = url.includes("#") ? url.split("#")[1] : "";
      if (hash && target.endsWith(".html") && !idsOf(target).has(hash)) {
        broken.push(`${relative(SITE, file)}: ${url} -> no id="${hash}" in ${relative(SITE, target)}`);
      }
    }
  }
  for (const file of walk(join(SITE, "js"), [".js"])) {
    const src = readFileSync(file, "utf8");
    for (const m of src.matchAll(/(?:import\s[^'"]*?from\s*|import\s*\(\s*|^import\s*)["'](\.{1,2}\/[^"']+)["']/gm)) {
      count++;
      const target = resolve(dirname(file), m[1]);
      if (!existsSync(target)) broken.push(`${relative(SITE, file)}: import "${m[1]}" -> missing`);
    }
  }
  for (const file of walk(join(SITE, "css"), [".css"])) {
    const src = readFileSync(file, "utf8");
    for (const m of src.matchAll(/url\(["']?([^"')]+)["']?\)/g)) {
      if (SKIP.test(m[1])) continue;
      count++;
      const target = resolve(dirname(file), m[1]);
      if (!existsSync(target)) broken.push(`${relative(SITE, file)}: url(${m[1]}) -> missing`);
    }
  }
  return { count, broken };
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  const { count, broken } = checkLinks();
  if (broken.length) {
    console.error(`check-links: ${broken.length} broken of ${count}`);
    broken.forEach((b) => console.error(`  ${b}`));
    process.exit(1);
  }
  console.log(`check-links: ${count} internal links, imports and urls, all resolve`);
}
