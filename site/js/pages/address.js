// pages/address.js: the live address checker and the Address detective game.
// Everything runs here, in the page. Nothing you paste is stored or sent anywhere:
// no fetch, no storage, no logging. What you paste is only ever set as text, never HTML.

import { classify, KINDS, shorten } from "../address.js";
import { DETECTIVE } from "../examples.js";
import { icon } from "../icons.js";
import { scrambleTo, burst } from "../fx.js";
import { getItem, setItem } from "../store.js";
import { reducedMotion } from "../env.js";

const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};
const svg = (name) => {
  const t = document.createElement("template");
  t.innerHTML = icon(name);
  return t.content.firstChild;
};

// ---------- checker ----------

const box = document.querySelector("[data-addr]");
const out = document.querySelector("[data-result]");
const clearBtn = document.querySelector("[data-clear]");
const pasteBtn = document.querySelector("[data-paste]");

const NET = { mainnet: "Mainnet", testnet: "Testnet" };
const GUESS = { unified: "a unified address (u1)", sapling: "a Sapling address (zs1)", p2pkh: "a transparent address (t1)", p2sh: "a transparent address (t3)", tex: "a TEX address (tex1)" };

function fit() {
  if (!box) return;
  box.style.setProperty("height", "auto");
  box.style.setProperty("height", `${Math.min(box.scrollHeight + 2, 240)}px`);
}

function render(r) {
  out.replaceChildren();
  out.className = "ck-result";
  if (r.kind === "empty") { out.hidden = true; return; }
  out.hidden = false;
  const tone = r.valid ? (r.shielded ? "is-shielded" : "is-transparent") : "is-invalid";
  out.classList.add(tone);

  const head = el("div", "ck-verdict");
  const ico = el("span", "ck-verdict-ico");
  ico.appendChild(svg(r.valid ? (r.shielded ? "lock" : "eye") : (r.kind === "phrase" || r.kind === "secret") ? "shield" : "alert"));
  const words = el("div", "ck-verdict-words");
  const title = el("p", "ck-verdict-title");
  const verdict = r.valid ? (r.shielded ? "Shielded" : "Transparent") : r.kind === "phrase" || r.kind === "secret" ? "Stop. Cleared." : "Not valid";
  const sub = el("p", "ck-verdict-sub");
  if (r.valid) sub.textContent = `${KINDS[r.kind].label} · ${NET[r.network] || ""} · ${KINDS[r.kind].encoding} checksum OK`;
  else if (GUESS[r.kind]) sub.textContent = `Looks like ${GUESS[r.kind]}, but it does not check out`;
  else sub.textContent = r.kind === "phrase" ? "That was not an address" : r.kind === "secret" ? "That was not an address" : "Not a Zcash address";
  words.append(title, sub);
  head.append(ico, words);
  out.appendChild(head);

  if (r.valid) {
    out.appendChild(el("p", "ck-explain", KINDS[r.kind].explain));
    if (r.network === "testnet") out.appendChild(el("p", "ck-reason", r.reason));
    if (KINDS[r.kind].limit) out.appendChild(el("p", "ck-limit small", KINDS[r.kind].limit));
    const checks = el("ul", "ck-checks");
    for (const t of [`Starts with ${KINDS[r.kind].prefix}`, `${KINDS[r.kind].encoding} checksum`, "Right length"]) {
      const li = el("li");
      li.append(svg("check"), document.createTextNode(t));
      checks.appendChild(li);
    }
    out.appendChild(checks);
  } else {
    out.appendChild(el("p", "ck-reason", r.reason));
  }

  if (r.valid && r.shielded && !reducedMotion()) scrambleTo(title, verdict, { duration: 520, seed: 5 });
  else title.textContent = verdict;
}

function check(now = false) {
  const value = box.value;
  clearBtn.hidden = value.length === 0;
  const r = classify(value);
  if (r.clear) {
    // a phrase or a key was pasted: wipe it at once
    box.value = "";
    clearBtn.hidden = true;
    fit();
  }
  render(r);
  if (!now) fit();
}

if (box && out) {
  let t = 0;
  box.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => check(), 90);
    fit();
  });
  box.addEventListener("paste", () => setTimeout(() => check(true), 0));
  box.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); check(true); }
  });
  clearBtn.addEventListener("click", () => {
    box.value = "";
    check(true);
    fit();
    box.focus();
  });
  if (navigator.clipboard && typeof navigator.clipboard.readText === "function") {
    pasteBtn.hidden = false;
    pasteBtn.addEventListener("click", async () => {
      try {
        const text = await navigator.clipboard.readText();
        box.value = text.slice(0, 4096);
        check(true);
        fit();
      } catch {
        box.focus();
      }
    });
  }
  document.querySelectorAll("[data-try]").forEach((b) => {
    b.addEventListener("click", () => {
      box.value = b.dataset.try;
      check(true);
      fit();
      box.scrollIntoView({ block: "center", behavior: reducedMotion() ? "auto" : "smooth" });
      box.focus({ preventScroll: true });
    });
  });
  if (box.value) check(true);
}

// ---------- address detective ----------

const game = document.querySelector("[data-detective]");
if (game) detective(game);

function detective(root) {
  const $ = (s) => root.querySelector(s);
  const addrEl = $("[data-det-addr]");
  const roundEl = $("[data-det-round]");
  const streakEl = $("[data-det-streak]");
  const bestEl = $("[data-det-best]");
  const feedback = $("[data-det-feedback]");
  const next = $("[data-det-next]");
  const picks = [...root.querySelectorAll("[data-det-pick]")];
  const dots = [...root.querySelectorAll(".det-progress span")];
  const stage = $("[data-det-stage]");
  let order = [];
  let i = 0;
  let streak = 0;
  let score = 0;
  let best = Math.max(0, Math.min(99, parseInt(getItem("zts-detective-best") || "0", 10) || 0));
  bestEl.textContent = String(best);

  const PREFIX = /^(u1|zs1|tex1|t1|t3)/;
  function show() {
    const item = order[i];
    addrEl.replaceChildren();
    const short = shorten(item.addr, item.addr.length > 60 ? 18 : 40, 8);
    const m = PREFIX.exec(short);
    const pre = el("span", "det-prefix", m ? m[1] : "");
    addrEl.append(pre, document.createTextNode(short.slice(m ? m[1].length : 0)));
    addrEl.setAttribute("title", item.addr);
    roundEl.textContent = String(i + 1);
    feedback.replaceChildren();
    feedback.className = "det-feedback";
    picks.forEach((p) => { p.disabled = false; p.classList.remove("is-right", "is-wrong"); });
    next.hidden = true;
    stage.classList.remove("is-right", "is-wrong");
    stage.classList.add("is-new");
    requestAnimationFrame(() => stage.classList.remove("is-new"));
  }

  function start() {
    order = DETECTIVE.map((x) => ({ ...x, k: Math.random() })).sort((a, b) => a.k - b.k);
    i = 0; streak = 0; score = 0;
    streakEl.textContent = "0";
    dots.forEach((d) => d.classList.remove("is-right", "is-wrong"));
    root.classList.remove("is-over");
    next.textContent = "Next address";
    show();
  }

  const NOUN = { unified: "a unified address", sapling: "a Sapling address", p2pkh: "a transparent address", p2sh: "a transparent address", tex: "a TEX address" };
  function why(item) {
    const r = classify(item.addr);
    const k = KINDS[r.kind];
    if (!k) return "";
    return `It starts with ${k.prefix}, so it is ${NOUN[r.kind]}. ${r.shielded ? "It is shielded." : "It is transparent: anyone can see what is sent to it."}`;
  }

  picks.forEach((p) => p.addEventListener("click", () => {
    const item = order[i];
    const right = p.dataset.detPick === item.answer;
    picks.forEach((x) => (x.disabled = true));
    p.classList.add(right ? "is-right" : "is-wrong");
    stage.classList.add(right ? "is-right" : "is-wrong");
    dots[i].classList.add(right ? "is-right" : "is-wrong");
    if (right) {
      streak += 1;
      score += 1;
      if (streak > best) { best = streak; setItem("zts-detective-best", String(best)); bestEl.textContent = String(best); }
    } else {
      streak = 0;
    }
    streakEl.textContent = String(streak);
    feedback.replaceChildren();
    feedback.className = `det-feedback ${right ? "is-right" : "is-wrong"}`;
    const lead = el("strong", null, right ? "Right. " : "Not quite. ");
    feedback.append(lead, document.createTextNode(why(item)));
    const last = i === order.length - 1;
    next.textContent = last ? "See your score" : "Next address";
    next.hidden = false;
    next.focus({ preventScroll: true });
  }));

  next.addEventListener("click", () => {
    if (root.classList.contains("is-over")) { start(); return; }
    if (i < order.length - 1) { i += 1; show(); return; }
    // the end
    root.classList.add("is-over");
    addrEl.replaceChildren(el("span", "det-score", `${score} of ${order.length}`));
    feedback.className = "det-feedback";
    feedback.textContent = score === order.length
      ? "Perfect. You can tell shielded from transparent at a glance."
      : "Good work. The trick: u1 and zs1 are shielded. t1, t3 and tex1 are transparent.";
    picks.forEach((x) => (x.disabled = true));
    next.textContent = "Play again";
    next.hidden = false;
    if (score === order.length) burst(root, { count: 70 });
  });

  start();
}
