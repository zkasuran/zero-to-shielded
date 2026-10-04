// The transcript parser and the progress storage parser: both must survive junk.
import test from "node:test";
import assert from "node:assert/strict";
import { parseSrt, toParagraphs } from "../js/srt.js";
import { parseProgress, serializeProgress } from "../js/store.js";

const SAMPLE = `1
00:00:00,000 --> 00:00:02,500
By the end of this video you will have a wallet.

2
00:00:02,600 --> 00:00:05,000
Open Zodl and tap <i>Create New Wallet</i>.

3
00:00:09,000 --> 00:00:11,000
{\\an8}Write the words on paper.
`;

test("parses a normal SRT file", () => {
  const cues = parseSrt(SAMPLE);
  assert.equal(cues.length, 3);
  assert.deepEqual(cues[0], { start: 0, end: 2.5, text: "By the end of this video you will have a wallet." });
  assert.equal(cues[1].text, "Open Zodl and tap Create New Wallet.");
  assert.equal(cues[2].text, "Write the words on paper.");
});

test("survives BOM, CRLF, dots, missing numbers, no hours and junk blocks", () => {
  const messy = "\uFEFF1\r\n00:00:01.5 --> 00:00:03.250\r\nHello there.\r\n\r\njunk block\r\n\r\n00:04,000 --> 00:06,000\r\nNo hours and no number.\r\n\r\n3\r\n00:00:07,000 --> 00:00:06,000\r\nEnds before it starts.\r\n\r\n4\r\n00:00:08,000 --> 00:00:09,000\r\n\r\n";
  const cues = parseSrt(messy);
  assert.equal(cues.length, 2);
  assert.equal(cues[0].start, 1.5);
  assert.equal(cues[0].end, 3.25);
  assert.equal(cues[1].start, 4);
  assert.equal(cues[1].text, "No hours and no number.");
});

test("rejects non-strings and oversized input without throwing", () => {
  for (const bad of [null, undefined, 42, {}, [], "", "no cues here", "x".repeat(1_000_001)]) {
    assert.deepEqual(parseSrt(bad), []);
  }
});

test("groups cues into paragraphs on pauses", () => {
  const paras = toParagraphs(parseSrt(SAMPLE));
  assert.equal(paras.length, 2);
  assert.equal(paras[0].start, 0);
  assert.match(paras[0].text, /wallet\. Open Zodl/);
  assert.equal(paras[1].start, 9);
});

test("progress: valid data round trips, only known steps survive", () => {
  const done = new Set(["wallet", "shield", "receive"]);
  assert.deepEqual([...parseProgress(serializeProgress(done))], ["wallet", "shield", "receive"]);
  assert.deepEqual([...parseProgress('{"v":1,"done":["wallet","hack","zec",7,null,"zec"]}')], ["wallet", "zec"]);
});

test("progress: junk, wrong shapes and huge values give an empty set", () => {
  for (const raw of [null, undefined, "", "not json", "[]", "{}", '{"v":2,"done":["wallet"]}', '{"v":1,"done":"wallet"}', '{"v":1}', "null", "true", "1", '"x"', `{"v":1,"done":["${"a".repeat(5000)}"]}`]) {
    assert.equal(parseProgress(raw).size, 0, String(raw).slice(0, 30));
  }
});
