// srt.js: a defensive SubRip parser for the episode transcripts.
// Captions files come from the video kit, but the parser assumes nothing: BOM, CRLF,
// missing cue numbers, dots instead of commas, no hours, stray markup, junk blocks and
// huge files are all handled. Pure, so node tests cover it.

const MAX_BYTES = 1_000_000;
const MAX_CUES = 3000;
const TIME = /^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})[,.](\d{1,3})\s*-->\s*(?:(\d{1,2}):)?(\d{1,2}):(\d{2})[,.](\d{1,3})/;

function seconds(h, m, s, ms) {
  return (Number(h) || 0) * 3600 + Number(m) * 60 + Number(s) + Number(String(ms).padEnd(3, "0")) / 1000;
}

function clean(text) {
  return text
    .replace(/\{\\[^}]*\}/g, "")
    .replace(/<[^>]*>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseSrt(input) {
  if (typeof input !== "string" || !input || input.length > MAX_BYTES) return [];
  const text = input.replace(/^\uFEFF/, "").replace(/\r\n?/g, "\n");
  const cues = [];
  for (const block of text.split(/\n[ \t]*\n/)) {
    const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
    const at = lines.findIndex((l) => TIME.test(l));
    if (at < 0) continue;
    const m = lines[at].match(TIME);
    const start = seconds(m[1], m[2], m[3], m[4]);
    const end = seconds(m[5], m[6], m[7], m[8]);
    if (!Number.isFinite(start) || !Number.isFinite(end) || end < start || Number(m[3]) > 59 || Number(m[7]) > 59) continue;
    const body = clean(lines.slice(at + 1).join(" "));
    if (!body) continue;
    cues.push({ start, end, text: body });
    if (cues.length >= MAX_CUES) break;
  }
  return cues.sort((a, b) => a.start - b.start);
}

// Group cues into readable paragraphs: break on a pause, or once a paragraph is long
// enough and a sentence ends.
export function toParagraphs(cues, { gap = 2.2, soft = 220, hard = 520 } = {}) {
  const out = [];
  let cur = null;
  let lastEnd = -Infinity;
  for (const c of cues) {
    const len = cur ? cur.text.length : 0;
    const sentenceEnded = cur && /[.!?]["')\]]?$/.test(cur.text);
    if (!cur || c.start - lastEnd > gap || len > hard || (len > soft && sentenceEnded)) {
      cur = { start: c.start, text: c.text };
      out.push(cur);
    } else {
      cur.text += ` ${c.text}`;
    }
    lastEnd = c.end;
  }
  return out;
}
