// pages/episode.js: player, chapter seek, transcript from the captions file, "I did it".
import { episodeById, STEPS, formatTime } from "../episodes.js";
import { makePlayer } from "../player.js";
import { parseSrt, toParagraphs } from "../srt.js";
import { readProgress, writeProgress, onProgress } from "../store.js";
import { siteUrl } from "../env.js";

const main = document.querySelector("main[data-episode]");
const ep = main ? episodeById(main.dataset.episode) : null;

if (ep) {
  const player = makePlayer(main.querySelector("[data-player]"));
  setupChapters(player);
  setupDidIt();
  loadTranscript(player);
}

function setupChapters(player) {
  const list = main.querySelector("[data-chapters]");
  const hint = main.querySelector("[data-chapter-hint]");
  const note = main.querySelector("[data-chapter-note]");
  if (note) note.hidden = !ep.chaptersDraft;
  if (!list) return;
  const buttons = [...list.querySelectorAll(".chapter")];
  if (!player || !player.canSeek) return;
  buttons.forEach((b) => {
    b.disabled = false;
    b.addEventListener("click", () => {
      player.seek(Number(b.dataset.t) || 0);
      mark(Number(b.dataset.t) || 0);
    });
  });
  if (hint) hint.textContent = player.mode === "youtube" ? "Tap a chapter to start the video there." : "Tap a chapter to jump there.";
  const mark = (t) => {
    let current = null;
    for (const b of buttons) if (Number(b.dataset.t) <= t + 0.25) current = b;
    buttons.forEach((b) => b.classList.toggle("is-current", b === current));
  };
  player.onTime(mark);
}

function setupDidIt() {
  const btn = main.querySelector("[data-did-it]");
  if (!btn) return;
  const label = btn.querySelector("[data-did-label]");
  const note = main.querySelector("[data-did-note]");
  const names = ep.steps.map((id) => STEPS.find((s) => s.id === id).label).join(" and ");
  const paint = (done) => {
    const all = ep.steps.every((s) => done.has(s));
    btn.setAttribute("aria-pressed", String(all));
    btn.classList.toggle("is-done", all);
    if (label) label.textContent = all ? "Done" : "I did it";
  };
  paint(readProgress());
  btn.addEventListener("click", () => {
    const done = readProgress();
    const all = ep.steps.every((s) => done.has(s));
    ep.steps.forEach((s) => (all ? done.delete(s) : done.add(s)));
    const saved = writeProgress(done);
    if (note) {
      note.textContent = all
        ? `Unticked ${names}.`
        : `Ticked ${names}.${saved ? "" : " Your browser is not saving it after this visit."}`;
    }
  });
  onProgress((done) => paint(done));
}

async function loadTranscript(player) {
  const section = document.querySelector("#transcript");
  const host = section && section.querySelector("[data-transcript]");
  const srt = main.querySelector("[data-player]")?.dataset.srt;
  if (!section || !host || !srt) return;
  let text = "";
  try {
    const res = await fetch(siteUrl(srt), { credentials: "same-origin" });
    if (!res.ok) return;
    text = await res.text();
  } catch {
    return;
  }
  const paras = toParagraphs(parseSrt(text));
  if (!paras.length) return;
  const frag = document.createDocumentFragment();
  for (const p of paras) {
    const row = document.createElement("p");
    row.className = "tp";
    row.dataset.t = String(p.start);
    const t = document.createElement("button");
    t.type = "button";
    t.className = "tp-t";
    t.textContent = formatTime(p.start);
    t.setAttribute("aria-label", `Jump to ${formatTime(p.start)}`);
    if (player && player.canSeek) t.addEventListener("click", () => player.seek(p.start));
    else t.disabled = true;
    const span = document.createElement("span");
    span.textContent = p.text;
    row.append(t, span);
    frag.appendChild(row);
  }
  host.replaceChildren(frag);
  section.hidden = false;
  if (player && player.mode === "video") {
    const rows = [...host.querySelectorAll(".tp")];
    player.onTime((now) => {
      let cur = null;
      for (const r of rows) if (Number(r.dataset.t) <= now + 0.2) cur = r;
      rows.forEach((r) => r.classList.toggle("is-current", r === cur));
    });
  }
}
