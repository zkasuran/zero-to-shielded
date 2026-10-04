#!/usr/bin/env node
// build.mjs: the one command to run after editing a page, js/episodes.js or site/media/.
//   node site/tools/build.mjs
// 1. layout.mjs writes the shared head, header, footer and data regions on every page
// 2. csp.mjs hashes the inline script and writes the CSP into every page and vercel.json
// There is no bundler and no dependency: the output is the files you deploy.

import { pathToFileURL } from "node:url";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const { build } = await import(pathToFileURL(join(here, "layout.mjs")).href);
const { run } = await import(pathToFileURL(join(here, "csp.mjs")).href);

const pages = build();
const csp = run();
console.log(`build: ${pages.length} pages written, CSP ${csp.hashes.length} hash(es), ${csp.stale.length} file(s) updated by csp`);
