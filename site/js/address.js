// address.js: tell what kind of Zcash address a string is, offline and synchronously.
//
// classify(str) -> { kind, shielded, valid, reason, network, label, encoding, prefix }
//
//   kind      "unified" (u1), "sapling" (zs1), "p2pkh" (t1), "p2sh" (t3), "tex" (tex1),
//             or for input that is not an address: "empty", "unknown", "phrase", "secret"
//   shielded  true (u1, zs1), false (t1, t3, tex1), null when unknown
//   valid     true only when the prefix, the checksum and the payload length all check out
//   reason    one plain sentence: why it failed, or what it is when it passed
//   network   "mainnet", "testnet" or null
//
// What is checked, per ZIP 316, ZIP 320, ZIP 173 and protocol spec section 5.6:
//   t1 / t3 / tm / t2   Base58Check: double SHA-256 checksum, 2 version bytes + 20 byte hash
//                       (0x1CB8 t1, 0x1CBD t3 on mainnet; 0x1D25 tm, 0x1CBA t2 on testnet)
//   zs1                 Bech32 (ZIP 173), HRP "zs" ("ztestsapling" on testnet), 43 byte payload
//   tex1                Bech32m, HRP "tex" ("textest"), 20 byte payload (ZIP 320)
//   u1                  Bech32m, HRP "u" ("utest"), at least 48 bytes, no length limit.
//                       A unified address is F4Jumbled. This module does NOT invert F4Jumble,
//                       so it does not list the receivers inside. Checksum + HRP only.
//
// Nothing here touches the network or storage. SHA-256 is implemented below so classify
// stays synchronous and runs the same in node tests and in the browser.

export const MAX_LEN = 512;

// ---------- SHA-256 (FIPS 180-4) ----------

const K = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]);

const ror = (x, n) => (x >>> n) | (x << (32 - n));

export function sha256(input) {
  const msg = input instanceof Uint8Array ? input : new TextEncoder().encode(String(input));
  const len = msg.length;
  const total = ((len + 9 + 63) >>> 6) << 6;
  const buf = new Uint8Array(total);
  buf.set(msg);
  buf[len] = 0x80;
  const view = new DataView(buf.buffer);
  view.setUint32(total - 8, Math.floor(len / 0x20000000) >>> 0);
  view.setUint32(total - 4, (len * 8) >>> 0);

  const H = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const W = new Uint32Array(64);
  for (let off = 0; off < total; off += 64) {
    for (let i = 0; i < 16; i++) W[i] = view.getUint32(off + i * 4);
    for (let i = 16; i < 64; i++) {
      const a = W[i - 15], b = W[i - 2];
      const s0 = ror(a, 7) ^ ror(a, 18) ^ (a >>> 3);
      const s1 = ror(b, 17) ^ ror(b, 19) ^ (b >>> 10);
      W[i] = (W[i - 16] + s0 + W[i - 7] + s1) >>> 0;
    }
    let a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
    for (let i = 0; i < 64; i++) {
      const S1 = ror(e, 6) ^ ror(e, 11) ^ ror(e, 25);
      const ch = (e & f) ^ (~e & g);
      const t1 = (h + S1 + ch + K[i] + W[i]) >>> 0;
      const S0 = ror(a, 2) ^ ror(a, 13) ^ ror(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const t2 = (S0 + maj) >>> 0;
      h = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
    }
    H[0] = (H[0] + a) >>> 0; H[1] = (H[1] + b) >>> 0; H[2] = (H[2] + c) >>> 0; H[3] = (H[3] + d) >>> 0;
    H[4] = (H[4] + e) >>> 0; H[5] = (H[5] + f) >>> 0; H[6] = (H[6] + g) >>> 0; H[7] = (H[7] + h) >>> 0;
  }
  const out = new Uint8Array(32);
  const ov = new DataView(out.buffer);
  for (let i = 0; i < 8; i++) ov.setUint32(i * 4, H[i]);
  return out;
}

export function toHex(bytes) {
  let s = "";
  for (const b of bytes) s += b.toString(16).padStart(2, "0");
  return s;
}

// ---------- Base58 / Base58Check ----------

const B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const B58_MAP = new Map([...B58].map((c, i) => [c, i]));

export function base58Decode(str) {
  const bytes = [];
  for (const ch of str) {
    const v = B58_MAP.get(ch);
    if (v === undefined) return null;
    let carry = v;
    for (let j = 0; j < bytes.length; j++) {
      carry += bytes[j] * 58;
      bytes[j] = carry & 0xff;
      carry >>= 8;
    }
    while (carry > 0) { bytes.push(carry & 0xff); carry >>= 8; }
  }
  for (const ch of str) { if (ch === "1") bytes.push(0); else break; }
  return Uint8Array.from(bytes.reverse());
}

export function base58Encode(bytes) {
  const digits = [];
  for (const byte of bytes) {
    let carry = byte;
    for (let j = 0; j < digits.length; j++) {
      carry += digits[j] << 8;
      digits[j] = carry % 58;
      carry = (carry / 58) | 0;
    }
    while (carry > 0) { digits.push(carry % 58); carry = (carry / 58) | 0; }
  }
  let out = "";
  for (const byte of bytes) { if (byte === 0) out += "1"; else break; }
  for (let i = digits.length - 1; i >= 0; i--) out += B58[digits[i]];
  return out;
}

function checksum4(payload) {
  return sha256(sha256(payload)).subarray(0, 4);
}

export function base58CheckEncode(payload) {
  const all = new Uint8Array(payload.length + 4);
  all.set(payload);
  all.set(checksum4(payload), payload.length);
  return base58Encode(all);
}

// -> { ok, payload, reason, badChar }
export function base58CheckDecode(str) {
  for (const ch of str) {
    if (!B58_MAP.has(ch)) return { ok: false, reason: "char", badChar: ch };
  }
  const raw = base58Decode(str);
  if (!raw || raw.length < 5) return { ok: false, reason: "short" };
  const payload = raw.subarray(0, raw.length - 4);
  const given = raw.subarray(raw.length - 4);
  const want = checksum4(payload);
  for (let i = 0; i < 4; i++) if (given[i] !== want[i]) return { ok: false, reason: "checksum", payload };
  return { ok: true, payload: Uint8Array.from(payload) };
}

// ---------- Bech32 / Bech32m (BIP 173, BIP 350, ZIP 173) ----------

const CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l";
const CHARSET_MAP = new Map([...CHARSET].map((c, i) => [c, i]));
const GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];
export const BECH32_CONST = 1;
export const BECH32M_CONST = 0x2bc830a3;

function polymod(values) {
  let chk = 1;
  for (const v of values) {
    const top = chk >>> 25;
    chk = ((chk & 0x1ffffff) << 5) ^ v;
    for (let i = 0; i < 5; i++) if ((top >>> i) & 1) chk ^= GEN[i];
  }
  return chk >>> 0;
}

function hrpExpand(hrp) {
  const out = [];
  for (let i = 0; i < hrp.length; i++) out.push(hrp.charCodeAt(i) >> 5);
  out.push(0);
  for (let i = 0; i < hrp.length; i++) out.push(hrp.charCodeAt(i) & 31);
  return out;
}

export function convertBits(data, from, to, pad) {
  let acc = 0, bits = 0;
  const out = [];
  const maxv = (1 << to) - 1;
  for (const value of data) {
    if (value < 0 || value >> from) return null;
    acc = (acc << from) | value;
    bits += from;
    while (bits >= to) {
      bits -= to;
      out.push((acc >> bits) & maxv);
    }
    acc &= (1 << bits) - 1;
  }
  if (pad) {
    if (bits > 0) out.push((acc << (to - bits)) & maxv);
  } else if (bits >= from || ((acc << (to - bits)) & maxv)) {
    return null;
  }
  return out;
}

export function bech32Encode(hrp, data5, variant = "bech32") {
  const c = variant === "bech32m" ? BECH32M_CONST : BECH32_CONST;
  const mod = polymod([...hrpExpand(hrp), ...data5, 0, 0, 0, 0, 0, 0]) ^ c;
  const chk = [];
  for (let p = 0; p < 6; p++) chk.push((mod >>> (5 * (5 - p))) & 31);
  return `${hrp}1${[...data5, ...chk].map((d) => CHARSET[d]).join("")}`;
}

// Expects lower case. -> { ok, hrp, words, variant, reason, badChar }
// `limit` is BIP 173's 90 character cap. Zcash unified addresses ignore it (ZIP 316),
// so classify() checks payload lengths per kind instead and passes no limit.
export function bech32Decode(str, limit = Infinity) {
  if (str.length > limit) return { ok: false, reason: "long" };
  const pos = str.lastIndexOf("1");
  if (pos < 1) return { ok: false, reason: "separator" };
  const hrp = str.slice(0, pos);
  const part = str.slice(pos + 1);
  if (hrp.length > 83) return { ok: false, reason: "hrp" };
  for (let i = 0; i < hrp.length; i++) {
    const c = hrp.charCodeAt(i);
    if (c < 33 || c > 126) return { ok: false, reason: "hrp" };
  }
  if (part.length < 6) return { ok: false, reason: "short", hrp };
  const values = [];
  for (const ch of part) {
    const v = CHARSET_MAP.get(ch);
    if (v === undefined) return { ok: false, reason: "char", badChar: ch, hrp };
    values.push(v);
  }
  const pm = polymod([...hrpExpand(hrp), ...values]);
  const variant = pm === BECH32_CONST ? "bech32" : pm === BECH32M_CONST ? "bech32m" : null;
  if (!variant) return { ok: false, reason: "checksum", hrp };
  return { ok: true, hrp, words: values.slice(0, -6), variant };
}

// ---------- kinds ----------

// Plain-language copy per kind. Sources: docs/FACTS.md F27, F28, F30, F39 to F46.
export const KINDS = {
  unified: {
    label: "Unified address",
    prefix: "u1",
    encoding: "Bech32m",
    shielded: true,
    verdict: "Shielded",
    explain: "A u1 address is a unified address. It bundles one or more receivers. A receiver is one way to get paid. The address Zodl shows as Zcash Shielded Address starts with u1 and holds only shielded receivers. An address made by another wallet may also hold a transparent receiver.",
    limit: "This checker checks the prefix and the checksum. It does not open the address to list the receivers inside.",
  },
  sapling: {
    label: "Sapling address",
    prefix: "zs1",
    encoding: "Bech32",
    shielded: true,
    verdict: "Shielded",
    explain: "Older Sapling addresses start with zs1. Sapling is a shielded pool, so payments to this address are shielded. Your Zodl shielded address starts with u1 instead.",
    limit: "",
  },
  p2pkh: {
    label: "Transparent address",
    prefix: "t1",
    encoding: "Base58Check",
    shielded: false,
    verdict: "Transparent",
    explain: "It starts with t1 and works like a Bitcoin address. Anyone can see what is sent to it. Paying it from your shielded balance is unshielding: the amount and this address are public and you cannot add a note.",
    limit: "",
  },
  p2sh: {
    label: "Transparent address (P2SH)",
    prefix: "t3",
    encoding: "Base58Check",
    shielded: false,
    verdict: "Transparent",
    explain: "Transparent addresses start with t1 or t3. This one starts with t3. Anyone can see what is sent to it, like Bitcoin.",
    limit: "",
  },
  tex: {
    label: "TEX address",
    prefix: "tex1",
    encoding: "Bech32m",
    shielded: false,
    verdict: "Transparent",
    explain: "A TEX address starts with tex1. It is a form of a t1 address that can only be paid from transparent funds. Some exchanges use tex1 addresses for deposits. When you pay one from Zodl, Zodl does the two steps for you. The amount and the address are public.",
    limit: "",
  },
};

const BECH32_KINDS = {
  u: { kind: "unified", network: "mainnet", variant: "bech32m" },
  utest: { kind: "unified", network: "testnet", variant: "bech32m" },
  zs: { kind: "sapling", network: "mainnet", variant: "bech32" },
  ztestsapling: { kind: "sapling", network: "testnet", variant: "bech32" },
  tex: { kind: "tex", network: "mainnet", variant: "bech32m" },
  textest: { kind: "tex", network: "testnet", variant: "bech32m" },
};

const BASE58_VERSIONS = [
  { v: [0x1c, 0xb8], kind: "p2pkh", network: "mainnet" },
  { v: [0x1c, 0xbd], kind: "p2sh", network: "mainnet" },
  { v: [0x1d, 0x25], kind: "p2pkh", network: "testnet" },
  { v: [0x1c, 0xba], kind: "p2sh", network: "testnet" },
];

const PREFIXES = "Your Zodl shielded address starts with u1. Transparent addresses start with t1 or t3. TEX addresses start with tex1. Older Sapling addresses start with zs1.";

const REASONS = {
  empty: "Paste an address to check it.",
  long: `That is too long to be a Zcash address. This checker reads at most ${MAX_LEN} characters.`,
  phrase: "This looks like a list of words, not an address. Never paste your recovery phrase into any website. This page has cleared it.",
  secret: "This looks like a secret key, not an address. Never paste a key into any website. This page has cleared it.",
  mixed: "This mixes capital and small letters. A real u1, zs1 or tex1 address uses one case only, so it may have been changed.",
  checksum: "The checksum does not match. A character is wrong or missing. Copy the address again.",
  variant: "The checksum type is wrong for this prefix. Copy the address again.",
  length: "The address has the wrong length for its kind. It may be cut short.",
  padding: "The address does not end cleanly. It may be cut short or changed.",
  short: "This is too short to be a Zcash address.",
  unknown: `This does not start like a Zcash address. ${PREFIXES}`,
  draft: "This looks like a newer unified address format that is still a draft. This checker reads u1 addresses.",
  version: "The checksum is fine but this is not a Zcash transparent address.",
};

function result(kind, valid, reason, network = null, extra = {}) {
  const meta = KINDS[kind];
  return {
    kind,
    shielded: meta ? meta.shielded : null,
    valid,
    reason,
    network,
    label: meta ? meta.label : null,
    encoding: meta ? meta.encoding : null,
    prefix: meta ? meta.prefix : null,
    ...extra,
  };
}

const WHITESPACE = /[\s\u200b-\u200d\u2060\ufeff]+/g;

export function normalize(input) {
  const text = typeof input === "string" ? input : "";
  return text.replace(WHITESPACE, "");
}

function looksLikePhrase(raw) {
  // numbered lists ("1. apple 2. river") count as words: drop the numbers first
  const tokens = raw.trim().split(/[\s,;.):]+/).filter((t) => t && !/^\d{1,2}$/.test(t));
  const words = tokens.filter((t) => /^[a-z]{3,8}$/i.test(t));
  return words.length >= 12 && words.length >= tokens.length * 0.6;
}

function looksLikeSecret(compact) {
  const lower = compact.toLowerCase();
  if (lower.startsWith("secret-extended-key-")) return true;
  if (/^[5KLc9][1-9A-HJ-NP-Za-km-z]{50,51}$/.test(compact)) {
    const d = base58CheckDecode(compact);
    if (d.ok && (d.payload[0] === 0x80 || d.payload[0] === 0xef) && (d.payload.length === 33 || d.payload.length === 34)) return true;
  }
  return false;
}

export function classify(input) {
  const raw = typeof input === "string" ? input : "";
  if (raw.length > MAX_LEN * 8) return result("unknown", false, REASONS.long);
  const s = normalize(raw);
  if (!s) return result("empty", false, REASONS.empty);
  if (s.length > MAX_LEN) return result("unknown", false, REASONS.long);
  if (looksLikePhrase(raw)) return result("phrase", false, REASONS.phrase, null, { clear: true });
  if (looksLikeSecret(s)) return result("secret", false, REASONS.secret, null, { clear: true });

  const lower = s.toLowerCase();
  const sep = lower.lastIndexOf("1");
  const hrp = sep > 0 ? lower.slice(0, sep) : "";

  if (BECH32_KINDS[hrp]) {
    const want = BECH32_KINDS[hrp];
    if (s !== lower && s !== s.toUpperCase()) return result(want.kind, false, REASONS.mixed, want.network);
    const d = bech32Decode(lower);
    if (!d.ok) {
      if (d.reason === "char") return result(want.kind, false, `"${d.badChar}" cannot appear in this kind of address. Check for a typo.`, want.network);
      if (d.reason === "short") return result(want.kind, false, REASONS.short, want.network);
      return result(want.kind, false, REASONS.checksum, want.network);
    }
    if (d.variant !== want.variant) return result(want.kind, false, REASONS.variant, want.network);
    const bytes = convertBits(d.words, 5, 8, false);
    if (!bytes) return result(want.kind, false, REASONS.padding, want.network);
    if (want.kind === "sapling" && bytes.length !== 43) return result(want.kind, false, REASONS.length, want.network);
    if (want.kind === "tex" && bytes.length !== 20) return result(want.kind, false, REASONS.length, want.network);
    if (want.kind === "unified" && bytes.length < 48) return result(want.kind, false, REASONS.length, want.network);
    return result(want.kind, true, passReason(want.kind, want.network), want.network, { bytes: Uint8Array.from(bytes) });
  }

  if (/^(zu|tu|zutest|tutest)1/.test(lower)) return result("unknown", false, REASONS.draft);

  if (/^t[13m2]/.test(s)) {
    const d = base58CheckDecode(s);
    const guess = s[1] === "1" || s[1] === "m" ? "p2pkh" : "p2sh";
    const net = s[1] === "1" || s[1] === "3" ? "mainnet" : "testnet";
    if (!d.ok) {
      if (d.reason === "char") return result(guess, false, `"${d.badChar}" cannot appear in a transparent address. Check for a typo.`, net);
      if (d.reason === "short") return result(guess, false, REASONS.short, net);
      return result(guess, false, REASONS.checksum, net);
    }
    if (d.payload.length !== 22) return result(guess, false, REASONS.length, net);
    const hit = BASE58_VERSIONS.find((x) => x.v[0] === d.payload[0] && x.v[1] === d.payload[1]);
    if (!hit) return result("unknown", false, REASONS.version);
    return result(hit.kind, true, passReason(hit.kind, hit.network), hit.network, { bytes: d.payload.slice(2) });
  }

  return result("unknown", false, s.length < 8 ? REASONS.short : REASONS.unknown);
}

const NOUNS = {
  unified: "unified address",
  sapling: "Sapling address",
  p2pkh: "transparent address",
  p2sh: "transparent P2SH address",
  tex: "TEX address",
};

function passReason(kind, network) {
  const meta = KINDS[kind];
  const what = meta.shielded ? "shielded" : "transparent";
  if (network === "testnet") return `A valid ${NOUNS[kind]} for the test network. Testnet addresses are for testing only.`;
  return `A valid ${NOUNS[kind]}. It is ${what}.`;
}

// Short display form: keep the prefix and the tail readable.
export function shorten(addr, head = 14, tail = 10) {
  const s = String(addr);
  return s.length <= head + tail + 1 ? s : `${s.slice(0, head)}…${s.slice(-tail)}`;
}
