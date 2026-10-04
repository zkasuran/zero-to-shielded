// Entry point so `node --test site/test/` works on Node 22 and later, which treat a
// directory argument as a module path (package.json "main") instead of searching it.
import "./address.test.mjs";
import "./srt-store.test.mjs";
import "./site.test.mjs";
