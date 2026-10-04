// Address checker tests. Valid vectors are real, published test data (sources and
// commits in vectors.json and bech32-vectors.json). Every valid vector is then changed
// in small ways (one character, case mix, cut short, wrong prefix, wrong checksum type)
// and each changed copy must fail.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash, randomBytes } from "node:crypto";
import {
  classify, sha256, toHex, base58Decode, base58Encode, base58CheckDecode, base58CheckEncode,
  bech32Decode, bech32Encode, convertBits, MAX_LEN, KINDS,
} from "../js/address.js";
import { CHECKER_EXAMPLES, DETECTIVE } from "../js/examples.js";

const V = JSON.parse(readFileSync(new URL("./vectors.json", import.meta.url), "utf8"));
const BIP = JSON.parse(readFileSync(new URL("./bech32-vectors.json", import.meta.url), "utf8"));

const CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l";
const B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

// Change the character at index i to another character from the same alphabet.
function swapAt(s, i, alphabet) {
  const c = s[i];
  const next = alphabet[(alphabet.indexOf(c) + 7) % alphabet.length];
  return s.slice(0, i) + next + s.slice(i + 1);
}

const mainnetUA = V.unified.filter((u) => u.network === "mainnet").map((u) => u.addr);
const mainnetT1 = [...V.tex.map((t) => t.t1), ...V.transparent.filter((t) => t.network === "mainnet" && t.kind === "p2pkh").map((t) => t.addr), V.zip320_example.t1];
const mainnetT3 = V.transparent.filter((t) => t.network === "mainnet" && t.kind === "p2sh").map((t) => t.addr);
const mainnetTex = [...V.tex.map((t) => t.tex), V.zip320_example.tex];
const mainnetSapling = V.sapling.filter((s) => s.network === "mainnet").map((s) => s.addr);

// ---------- SHA-256 ----------

test("sha256 matches FIPS 180-4 examples", () => {
  assert.equal(toHex(sha256("")), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  assert.equal(toHex(sha256("abc")), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  assert.equal(toHex(sha256("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq")), "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");
  assert.equal(toHex(sha256("a".repeat(1000000))), "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
});

test("sha256 agrees with node:crypto on 300 random inputs, every length 0..299", () => {
  for (let n = 0; n < 300; n++) {
    const buf = randomBytes(n);
    assert.equal(toHex(sha256(new Uint8Array(buf))), createHash("sha256").update(buf).digest("hex"), `length ${n}`);
  }
});

// ---------- Base58 / Bech32 primitives ----------

test("base58 round trips, keeps leading zero bytes, rejects 0 O I l", () => {
  for (let n = 0; n < 60; n++) {
    const bytes = new Uint8Array(randomBytes(n % 30));
    if (n % 5 === 0 && bytes.length) bytes[0] = 0;
    assert.deepEqual([...base58Decode(base58Encode(bytes))], [...bytes]);
  }
  for (const bad of ["0", "O", "I", "l"]) assert.equal(base58Decode(`t1${bad}abc`), null);
  const payload = new Uint8Array([0x1c, 0xb8, ...randomBytes(20)]);
  assert.equal(base58CheckDecode(base58CheckEncode(payload)).ok, true);
});

test("BIP 173 Bech32 and BIP 350 Bech32m vectors", () => {
  for (const s of BIP.bech32_valid) {
    const d = bech32Decode(s.toLowerCase(), 90);
    assert.equal(d.ok, true, s);
    assert.equal(d.variant, "bech32", s);
  }
  for (const s of BIP.bech32m_valid) {
    const d = bech32Decode(s.toLowerCase(), 90);
    assert.equal(d.ok, true, s);
    assert.equal(d.variant, "bech32m", s);
  }
  // Invalid rows fail. The "checksum calculated with uppercase form of HRP" rows fail as
  // checksum errors once lowered, which is how classify() reads input.
  for (const { s, why } of [...BIP.bech32_invalid, ...BIP.bech32m_invalid]) {
    assert.equal(bech32Decode(s.toLowerCase(), 90).ok, false, `${s}: ${why}`);
  }
  // no string is valid as both variants (BIP 350)
  for (const s of BIP.bech32_valid) assert.notEqual(bech32Decode(s.toLowerCase()).variant, "bech32m");
});

test("bech32Encode and convertBits round trip both variants", () => {
  for (const variant of ["bech32", "bech32m"]) {
    const bytes = [...randomBytes(32)];
    const words = convertBits(bytes, 8, 5, true);
    const s = bech32Encode("zs", words, variant);
    const d = bech32Decode(s);
    assert.equal(d.ok, true);
    assert.equal(d.variant, variant);
    assert.deepEqual(convertBits(d.words, 5, 8, false), bytes);
  }
});

// ---------- real Zcash vectors: all valid on mainnet ----------

test("all 60 unified address vectors (zcash-test-vectors) are valid mainnet u1", () => {
  assert.equal(mainnetUA.length, 60);
  for (const a of mainnetUA) {
    const r = classify(a);
    assert.equal(r.valid, true, `${a}: ${r.reason}`);
    assert.equal(r.kind, "unified");
    assert.equal(r.network, "mainnet");
    assert.equal(r.shielded, true);
    assert.equal(r.encoding, "Bech32m");
  }
});

test("ZIP 320 vectors: every t1 and its tex1 decode to the same 20 byte key hash", () => {
  assert.equal(V.tex.length, 15);
  for (const t of V.tex) {
    const a = classify(t.t1);
    const b = classify(t.tex);
    assert.equal(a.valid, true, t.t1);
    assert.equal(a.kind, "p2pkh");
    assert.equal(a.network, "mainnet");
    assert.equal(a.shielded, false);
    assert.equal(b.valid, true, t.tex);
    assert.equal(b.kind, "tex");
    assert.equal(b.shielded, false);
    assert.equal(toHex(a.bytes), t.p2pkh);
    assert.equal(toHex(b.bytes), t.p2pkh);
  }
});

test("ZIP 320 example pair from zips.z.cash/zip-0320 is one key in two forms", () => {
  const { t1, tex } = V.zip320_example;
  assert.equal(t1, "t1VmmGiyjVNeCjxDZzg7vZmd99WyzVby9yC");
  assert.equal(tex, "tex1s2rt77ggv6q989lr49rkgzmh5slsksa9khdgte");
  const a = classify(t1);
  const b = classify(tex);
  assert.equal(a.valid && b.valid, true);
  assert.equal(a.kind, "p2pkh");
  assert.equal(b.kind, "tex");
  assert.deepEqual([...a.bytes], [...b.bytes]);
  // and the conversion itself, as in the ZIP's reference code
  assert.equal(bech32Encode("tex", convertBits([...a.bytes], 8, 5, true), "bech32m"), tex);
});

test("zcash base58_keys_valid: t1/t3 mainnet and tm/t2 testnet, hash matches the script", () => {
  for (const t of V.transparent) {
    const r = classify(t.addr);
    assert.equal(r.valid, true, t.addr);
    assert.equal(r.kind, t.kind, t.addr);
    assert.equal(r.network, t.network, t.addr);
    assert.equal(r.shielded, false);
    const hash = t.kind === "p2pkh" ? t.script.slice(6, 46) : t.script.slice(4, 44);
    assert.equal(toHex(r.bytes), hash, t.addr);
  }
  assert.ok(mainnetT3.length >= 7);
  assert.ok(V.transparent.some((t) => t.network === "testnet" && t.addr.startsWith("tm")));
  assert.ok(V.transparent.some((t) => t.network === "testnet" && t.addr.startsWith("t2")));
});

test("Sapling vectors (librustzcash): zs1 mainnet valid and shielded, testnet recognised", () => {
  for (const s of V.sapling) {
    const r = classify(s.addr);
    assert.equal(r.valid, true, s.addr);
    assert.equal(r.kind, "sapling");
    assert.equal(r.network, s.network);
    assert.equal(r.shielded, true);
    if (s.bytes) assert.equal(toHex(r.bytes), s.bytes);
  }
  assert.equal(mainnetSapling.length, 2);
});

test("testnet unified and TEX prefixes are recognised as testnet", () => {
  const ua = bech32Decode(mainnetUA[0]);
  const re = bech32Encode("utest", ua.words, "bech32m");
  assert.deepEqual([classify(re).valid, classify(re).network, classify(re).kind], [true, "testnet", "unified"]);
  const tx = bech32Decode(mainnetTex[0]);
  const tt = bech32Encode("textest", tx.words, "bech32m");
  assert.deepEqual([classify(tt).valid, classify(tt).network, classify(tt).kind], [true, "testnet", "tex"]);
});

// ---------- tampered copies must fail ----------

const bech32All = [...mainnetUA, ...mainnetTex, ...mainnetSapling];
const base58All = [...mainnetT1, ...mainnetT3];

test("one character changed: every Bech32 vector fails, at many positions", () => {
  for (const a of bech32All) {
    const sep = a.lastIndexOf("1");
    for (let i = sep + 1; i < a.length; i += 3) {
      const bad = swapAt(a, i, CHARSET);
      assert.equal(classify(bad).valid, false, `${a} @${i}`);
    }
  }
});

test("one character changed: every Base58Check vector fails, at every position after the prefix", () => {
  for (const a of base58All) {
    for (let i = 2; i < a.length; i++) {
      const bad = swapAt(a, i, B58);
      const r = classify(bad);
      assert.equal(r.valid, false, `${a} @${i}`);
    }
  }
});

test("mixed case fails, all upper case passes (Bech32), any case change fails (Base58)", () => {
  for (const a of bech32All) {
    const i = a.length - 3;
    const mixed = a.slice(0, i) + a[i].toUpperCase() + a.slice(i + 1);
    if (mixed === a) continue;
    const r = classify(mixed);
    assert.equal(r.valid, false, mixed);
    assert.match(r.reason, /capital and small/);
    assert.equal(classify(a.toUpperCase()).valid, true, a);
  }
  for (const a of base58All) {
    const i = [...a].findIndex((c, k) => k > 2 && /[a-km-z]/.test(c));
    const flipped = a.slice(0, i) + a[i].toUpperCase() + a.slice(i + 1);
    assert.equal(classify(flipped).valid, false, flipped);
  }
});

test("truncated addresses fail", () => {
  for (const a of [...bech32All, ...base58All]) {
    assert.equal(classify(a.slice(0, -1)).valid, false, a);
    assert.equal(classify(a.slice(0, -6)).valid, false, a);
    assert.equal(classify(a.slice(0, Math.floor(a.length / 2))).valid, false, a);
  }
});

test("wrong prefix (HRP) fails even with the data part intact", () => {
  for (const a of bech32All) {
    const data = a.slice(a.lastIndexOf("1"));
    for (const hrp of ["zs", "u", "tex", "ztestsapling", "utest", "bc", "x"]) {
      if (a.startsWith(hrp + "1")) continue;
      assert.equal(classify(hrp + data).valid, false, `${hrp}${data.slice(0, 12)}`);
    }
  }
  for (const a of base58All) {
    assert.equal(classify("t2" + a.slice(2)).valid, false);
    assert.equal(classify("T1" + a.slice(2)).valid, false);
  }
});

test("right prefix, wrong checksum type: Bech32m Sapling and Bech32 TEX or u1 fail", () => {
  for (const a of mainnetSapling) {
    const d = bech32Decode(a);
    const r = classify(bech32Encode("zs", d.words, "bech32m"));
    assert.equal(r.valid, false);
    assert.match(r.reason, /checksum type/);
  }
  for (const a of [...mainnetTex, ...mainnetUA.slice(0, 10)]) {
    const d = bech32Decode(a);
    const r = classify(bech32Encode(d.hrp, d.words, "bech32"));
    assert.equal(r.valid, false, a);
  }
});

test("right checksum, wrong payload length fails for zs1, tex1 and u1", () => {
  const enc = (hrp, n, v) => bech32Encode(hrp, convertBits([...randomBytes(n)], 8, 5, true), v);
  assert.equal(classify(enc("zs", 42, "bech32")).valid, false);
  assert.equal(classify(enc("zs", 44, "bech32")).valid, false);
  assert.equal(classify(enc("tex", 21, "bech32m")).valid, false);
  assert.equal(classify(enc("tex", 19, "bech32m")).valid, false);
  assert.equal(classify(enc("u", 47, "bech32m")).valid, false);
  assert.equal(classify(enc("u", 48, "bech32m")).valid, true);
  const payload = new Uint8Array([0x1c, 0xb8, ...randomBytes(21)]);
  assert.equal(classify(base58CheckEncode(payload)).valid, false);
});

// ---------- normalising and limits ----------

test("whitespace, line breaks and zero-width characters inside are removed", () => {
  const a = mainnetUA[6];
  const spaced = `  ${a.slice(0, 40)} \n ${a.slice(40, 90)}\t${a.slice(90)}\u200b `;
  assert.equal(classify(spaced).valid, true);
  assert.equal(classify(`\n${mainnetT1[0]}\r\n`).valid, true);
});

test(`input longer than ${MAX_LEN} characters is refused with a reason`, () => {
  const r = classify(mainnetUA[0] + "q".repeat(MAX_LEN));
  assert.equal(r.valid, false);
  assert.match(r.reason, /too long/);
  const huge = classify("x".repeat(100000));
  assert.equal(huge.valid, false);
});

test("a recovery phrase or a key is flagged and marked to clear, never treated as an address", () => {
  const phrase = "abandon ability able about above absent absorb abstract absurd abuse access accident acoustic acquire across act";
  const r = classify(phrase);
  assert.equal(r.kind, "phrase");
  assert.equal(r.valid, false);
  assert.equal(r.clear, true);
  assert.equal(classify("1. apple 2. river 3. stone 4. cloud 5. tiger 6. maple 7. ocean 8. pencil 9. garden 10. silver 11. window 12. rocket").kind, "phrase");
  const wif = base58CheckEncode(new Uint8Array([0x80, ...randomBytes(32), 0x01]));
  assert.equal(classify(wif).kind, "secret");
  assert.equal(classify("secret-extended-key-main1qqqqqqqqqqqqqq").kind, "secret");
});

test("every failure has a plain reason and every result has the same shape", () => {
  const junk = ["", "   ", "hello", "u1", "t1", "zs1", "tex1", "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", "zu1abcdef", "t1VmmGiyjVNeCjxDZzg7vZmd99WyzVby9y0", "u1" + "b".repeat(80), null, undefined, 42, {}, []];
  for (let n = 0; n < 400; n++) junk.push(randomBytes(n % 120).toString("latin1"));
  for (const j of junk) {
    const r = classify(j);
    assert.deepEqual(Object.keys(r).slice(0, 5), ["kind", "shielded", "valid", "reason", "network"]);
    assert.equal(typeof r.reason, "string");
    assert.ok(r.reason.length > 10);
    if (!r.valid) assert.ok(!/undefined|null|NaN/.test(r.reason), r.reason);
  }
  assert.match(classify("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4").reason, /does not start like a Zcash address/);
  assert.match(classify("t1VmmGiyjVNeCjxDZzg7vZmd99WyzVby9y0").reason, /"0" cannot appear/);
});

test("each kind has copy for the page", () => {
  for (const k of ["unified", "sapling", "p2pkh", "p2sh", "tex"]) {
    assert.ok(KINDS[k].label && KINDS[k].explain && KINDS[k].prefix && KINDS[k].encoding);
  }
  assert.match(KINDS.unified.limit, /does not open the address/);
});

// ---------- the examples the site shows come from the vectors ----------

test("checker examples (u1, t1, tex1) are mainnet vectors and validate", () => {
  const all = new Set([...mainnetUA, ...mainnetT1, ...mainnetTex]);
  assert.deepEqual(CHECKER_EXAMPLES.map((x) => x.id), ["u1", "t1", "tex1"]);
  for (const x of CHECKER_EXAMPLES) {
    assert.ok(all.has(x.addr), x.addr);
    assert.ok(x.addr.startsWith(x.id), x.addr);
    assert.equal(classify(x.addr).valid, true);
  }
  const u = V.unified.find((v) => v.addr === CHECKER_EXAMPLES[0].addr);
  assert.deepEqual(u.receivers, ["sapling", "orchard"]);
});

test("address detective answers match the checker", () => {
  const all = new Set([...mainnetUA, ...mainnetT1, ...mainnetT3, ...mainnetTex, ...mainnetSapling]);
  assert.equal(DETECTIVE.length, 6);
  for (const d of DETECTIVE) {
    assert.ok(all.has(d.addr), d.addr);
    const r = classify(d.addr);
    assert.equal(r.valid, true);
    assert.equal(r.shielded ? "shielded" : "transparent", d.answer, d.addr);
    if (r.kind === "unified") {
      const v = V.unified.find((u) => u.addr === d.addr);
      assert.ok(!v.receivers.includes("p2pkh") && !v.receivers.includes("p2sh"), "detective u1 must hold no transparent receiver");
    }
  }
});
