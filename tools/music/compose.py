#!/usr/bin/env python3
"""
Original background music for Zero to Shielded, rendered from code.

Every sound is synthesised here with numpy: wavetable oscillators built by additive
synthesis (band-limited by construction), two-operator FM, additive bells, a sine sub
bass and filtered-noise drums. No samples, no third-party audio, no AI music model.
ffmpeg is called only to measure EBU R128 loudness. Every random choice comes from a
named, fixed-seed stream, so two runs write byte-identical files.

    python3 tools/music/compose.py               render music/*.wav and music/levels.json
    python3 tools/music/compose.py --only bed    render one piece (bed, trailer, preview)
    python3 tools/music/compose.py --stems       also print per-layer loudness

Validate the files with tools/music/check.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np

SR = 48_000
BPM = 92.0
BEAT_S = 60.0 / BPM
BED_BARS = 48
BED_N = round(BED_BARS * 4 * BEAT_S * SR)  # 6_010_435 samples, 125.217 s
TRAILER_N = 34 * SR
PREVIEW_S = 12.0
TARGET_LUFS = -14.0
TP_CEILING = -1.3  # limiter ceiling (dBTP); the files must measure <= -1.0
SEED = 20261004
TWO_PI = 2.0 * np.pi

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "music"

T_START = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T_START:6.1f}s] {msg}", flush=True)


# ---------------------------------------------------------------- small helpers


def rng_for(name: str) -> np.random.Generator:
    """One independent fixed-seed stream per part: editing one part never shifts another."""
    digest = hashlib.sha256(f"zts-music:{SEED}:{name}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def midi_hz(m: float) -> float:
    return 440.0 * 2.0 ** ((m - 69.0) / 12.0)


def undb(d):
    return 10.0 ** (np.asarray(d, dtype=float) / 20.0)


def ramp_up(n: int) -> np.ndarray:
    """Raised cosine from exactly 0 towards 1."""
    return 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / max(n, 1))


def ramp_down(n: int) -> np.ndarray:
    """Raised cosine from just below 1 to exactly 0."""
    return 0.5 + 0.5 * np.cos(np.pi * np.arange(1, n + 1) / max(n, 1))


def pan_gains(p: float) -> tuple[float, float]:
    a = (float(np.clip(p, -1.0, 1.0)) + 1.0) * np.pi / 4.0
    return float(np.cos(a)), float(np.sin(a))


def fast_len(n: int) -> int:
    """Smallest 2^a 3^b 5^c >= n (numpy has no next_fast_len)."""
    best = 1 << max(0, int(n - 1).bit_length())
    p5 = 1
    while p5 < best:
        p35 = p5
        while p35 < best:
            v = p35
            while v < n:
                v *= 2
            best = min(best, v)
            p35 *= 3
        p5 *= 5
    return best


def lp2(f, fc, q=0.707):
    """Magnitude of a two-pole low-pass (12 dB per octave)."""
    r = np.asarray(f, dtype=float) / fc
    return 1.0 / np.sqrt((1.0 - r * r) ** 2 + (r / q) ** 2)


def hp2(f, fc, q=0.707):
    """Magnitude of a two-pole high-pass (12 dB per octave), zero at DC."""
    r = np.asarray(f, dtype=float) / fc
    return r * r / np.sqrt((1.0 - r * r) ** 2 + (r / q) ** 2)


class Track:
    """A buffer. Circular tracks wrap anything that runs past the end back to the start,
    which is how note releases and reverb tails cross the loop point."""

    def __init__(self, n: int, circular: bool, channels: int = 2):
        self.n = n
        self.circular = circular
        self.buf = np.zeros((channels, n))

    def add(self, start: float, sig: np.ndarray) -> None:
        sig = np.atleast_2d(sig)
        if sig.shape[0] != self.buf.shape[0]:
            sig = np.broadcast_to(sig, (self.buf.shape[0], sig.shape[1]))
        start = int(round(start))
        m = sig.shape[1]
        if self.circular:
            assert m <= self.n
            start %= self.n
            k = min(m, self.n - start)
            self.buf[:, start:start + k] += sig[:, :k]
            if k < m:
                self.buf[:, :m - k] += sig[:, k:]
        else:
            if start < 0:
                sig, m, start = sig[:, -start:], m + start, 0
            k = min(m, self.n - start)
            if k > 0:
                self.buf[:, start:start + k] += sig[:, :k]


# ---------------------------------------------------------------- oscillators

TABLE = 8192
PARTIAL_CAP = 8000.0  # no oscillator partial above this, so nothing can alias at 48 kHz
_TABLES: dict[tuple[str, int], np.ndarray] = {}


def wavetable(kind: str, f0: float) -> np.ndarray:
    """One cycle of a saw or triangle built by additive synthesis, partials <= 8 kHz."""
    kmax = max(1, int(PARTIAL_CAP // f0))
    key = (kind, kmax)
    if key not in _TABLES:
        k = np.arange(1, kmax + 1, dtype=float)
        if kind == "saw":
            amp = 1.0 / k
        else:  # triangle: odd partials, 1/k^2, alternating sign
            amp = np.where(k % 2 == 1, 1.0 / k ** 2, 0.0) * np.where(k % 4 == 3, -1.0, 1.0)
        edge = np.clip((k - 0.7 * kmax) / (0.3 * kmax + 1.0), 0.0, 1.0)
        amp = amp * (0.5 + 0.5 * np.cos(np.pi * edge))  # soft spectral edge
        spec = np.zeros(TABLE // 2 + 1, dtype=complex)
        spec[1:kmax + 1] = -0.5j * TABLE * amp  # rfft of sin(k x) is -i N/2 at bin k
        tab = np.fft.irfft(spec, n=TABLE)
        _TABLES[key] = np.append(tab, tab[0])  # guard sample for interpolation
    return _TABLES[key]


def osc(tab: np.ndarray, freq, n: int, phase0: float = 0.0) -> np.ndarray:
    """Read a band-limited table at freq (Hz, scalar or per sample), linear interpolation."""
    inc = np.broadcast_to(np.asarray(freq, dtype=float) / SR, (n,))
    ph = np.empty(n)
    ph[0] = 0.0
    np.cumsum(inc[:-1], out=ph[1:])
    ph += phase0
    ph %= 1.0
    pos = ph * TABLE
    i = np.minimum(pos.astype(np.int64), TABLE - 1)
    frac = pos - i
    a = tab[i]
    return a + frac * (tab[i + 1] - a)


PAD_STACK = (  # (wave, detune cents, gain, pan)
    ("saw", -7.0, 0.50, -0.8),
    ("saw", 7.0, 0.50, 0.8),
    ("saw", 0.0, 0.30, 0.0),
    ("tri", 0.0, 0.75, 0.0),
)


def pad_note(rng, midi, dur, vel, attack, release):
    """Detuned saw and triangle stack, slow drift on every voice, wide stereo."""
    f0 = midi_hz(midi)
    nd = max(1, int(dur * SR))
    n = nd + int(release * SR)
    t = np.arange(n) / SR
    out = np.zeros((2, n))
    for kind, cents, gain, pan in PAD_STACK:
        wob = rng.uniform(1.0, 2.5) * np.sin(TWO_PI * rng.uniform(0.06, 0.17) * t + rng.uniform(0, TWO_PI))
        sig = osc(wavetable(kind, f0), f0 * 2.0 ** ((cents + wob) / 1200.0), n, rng.uniform())
        gl, gr = pan_gains(pan)
        out[0] += (gain * gl) * sig
        out[1] += (gain * gr) * sig
    env = np.ones(n)
    na = min(int(attack * SR), n)
    env[:na] = ramp_up(na)
    tail = np.exp(-np.arange(n - nd) / (release * SR / 5.0))
    k = max(1, (n - nd) // 4)
    tail[-k:] *= ramp_down(k)
    env[nd:] *= tail
    return out * (env * vel)


def ep_note(midi, dur, vel, pan):
    """Soft two-operator FM electric piano (1:1), index falls fast, short 3rd-partial tine."""
    f0 = midi_hz(midi)
    nd = max(1, int(dur * SR))
    n = nd + int(0.45 * SR)
    t = np.arange(n) / SR
    index = (0.25 + 1.45 * vel) * np.exp(-t / 0.22) + 0.12
    w = TWO_PI * f0 * t
    sig = np.sin(w + index * np.sin(w)) + (0.06 * vel) * np.exp(-t / 0.045) * np.sin(3.0 * w)
    env = (0.3 + 0.7 * np.exp(-t / 0.55)) * np.exp(-t / 3.0)
    na = int(0.004 * SR)
    env[:na] *= ramp_up(na)
    rel = np.exp(-np.arange(n - nd) / (0.08 * SR))
    k = (n - nd) // 3
    rel[-k:] *= ramp_down(k)
    env[nd:] *= rel
    mono = sig * env * vel ** 1.4
    gl, gr = pan_gains(pan)
    return np.vstack([gl * mono, gr * mono])


BELL_PARTIALS = ((1.0, 1.0, 1.0), (2.0, 0.28, 0.55), (3.0, 0.10, 0.40), (4.16, 0.08, 0.30), (5.43, 0.035, 0.22))


def bell_note(rng, midi, vel, length=3.4, attack=0.004, reverse=False):
    """Additive bell: five partials, upper ones die first, nothing above 7.5 kHz."""
    f0 = midi_hz(midi)
    n = int(length * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for ratio, amp, decay in BELL_PARTIALS:
        if f0 * ratio > 7500.0:
            continue
        sig += amp * np.exp(-t / (1.4 * decay)) * np.sin(TWO_PI * f0 * ratio * t + rng.uniform(0, TWO_PI))
    na = int(attack * SR)
    sig[:na] *= ramp_up(na)
    k = n // 5
    sig[-k:] *= ramp_down(k)
    if reverse:
        sig = sig[::-1].copy()
    return sig * vel


def bass_note(midi, dur, vel, release=0.16):
    """Round sub: sine plus a little 2nd harmonic, soft attack."""
    f0 = midi_hz(midi)
    nd = max(1, int(dur * SR))
    n = nd + int(release * SR)
    t = np.arange(n) / SR
    w = TWO_PI * f0 * t
    sig = np.sin(w) + 0.2 * np.sin(2.0 * w)
    env = 0.85 + 0.15 * np.exp(-t / 0.5)
    na = int(0.03 * SR)
    env[:na] *= ramp_up(na)
    env[nd:] *= ramp_down(n - nd)
    return sig * env * vel


def kick(vel):
    """Soft kick: sine with a short pitch drop, 4 ms attack so there is no click."""
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 46.0 + 60.0 * np.exp(-t / 0.028)
    ph = TWO_PI * np.cumsum(f) / SR
    ph -= ph[0]
    env = np.exp(-t / 0.15)
    na = int(0.004 * SR)
    env[:na] *= ramp_up(na)
    k = int(0.08 * SR)
    env[-k:] *= ramp_down(k)
    return np.sin(ph) * env * vel


def noise_bank(rng, lo, hi, seconds=4.0):
    n = int(seconds * SR)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    y = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) * hp2(f, lo) * lp2(f, hi), n)
    return y / np.sqrt(np.mean(y * y))


def noise_hit(rng, bank, vel, length, attack, decay):
    n = int(length * SR)
    s = int(rng.integers(0, len(bank) - n))
    t = np.arange(n) / SR
    env = np.exp(-t / decay)
    na = int(attack * SR)
    env[:na] *= ramp_up(na)
    k = n // 4
    env[-k:] *= ramp_down(k)
    return bank[s:s + n] * env * vel


# ---------------------------------------------------------------- processing


def eq(x, gain_fn, circular, pad=SR):
    """Zero-phase FFT EQ. Circular signals are wrap-padded so the loop stays continuous."""
    c, n = x.shape
    if circular:
        xe = np.concatenate([x[:, -pad:], x, x[:, :pad]], axis=1)
    else:
        xe = np.pad(x, ((0, 0), (pad, pad)))
    size = fast_len(xe.shape[1])
    f = np.fft.rfftfreq(size, 1.0 / SR)
    y = np.fft.irfft(np.fft.rfft(xe, n=size, axis=1) * gain_fn(f), n=size, axis=1)
    return y[:, pad:pad + n]


def speech_dip(f, lo=1500.0, hi=4000.0, depth_db=-4.0, shoulder=0.5):
    """-4 dB across 1.5 to 4 kHz, raised-cosine shoulders half an octave wide."""
    lf = np.log2(np.maximum(f, 1.0))
    below = np.clip((np.log2(lo) - lf) / shoulder, 0.0, 1.0)
    above = np.clip((lf - np.log2(hi)) / shoulder, 0.0, 1.0)
    return undb(depth_db * (0.5 + 0.5 * np.cos(np.pi * np.maximum(below, above))))


def master_eq(f):
    """Gentle 12 dB per octave low-pass at 9 kHz and a 28 Hz high-pass (kills DC)."""
    return hp2(f, 28.0) * lp2(f, 9000.0)


STFT_HOP = 527  # divides BED_N (5 x 17 x 31 x 2281) so the frame grid wraps exactly
STFT_N = 4 * STFT_HOP  # 75 % overlap, sqrt-Hann analysis and synthesis


def moving_lowpass(x, cutoff_at, circular, q=0.8):
    """Two-pole low-pass whose cutoff follows cutoff_at(seconds), by weighted overlap-add."""
    c, n = x.shape
    hop, nfft = STFT_HOP, STFT_N
    if circular:
        assert n % hop == 0
        xe = np.concatenate([x, x[:, :nfft]], axis=1)
        offset, frames = 0, n // hop
    else:
        xe = np.concatenate([np.zeros((c, nfft)), x, np.zeros((c, nfft + hop))], axis=1)
        offset, frames = nfft, (n + nfft) // hop + 1
    ye = np.zeros((c, xe.shape[1]))
    win = np.sqrt(0.5 - 0.5 * np.cos(TWO_PI * np.arange(nfft) / nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / SR)
    j = np.arange(nfft)
    for m0 in range(0, frames, 512):
        ms = np.arange(m0, min(frames, m0 + 512))
        idx = ms[:, None] * hop + j[None, :]
        centre = (ms * hop + nfft / 2 - offset) / SR
        h = lp2(f[None, :], np.asarray(cutoff_at(centre), dtype=float)[:, None], q)
        for ch in range(c):
            seg = np.fft.irfft(np.fft.rfft(xe[ch][idx] * win, axis=1) * h, n=nfft, axis=1) * win
            for k, m in enumerate(ms):
                ye[ch, m * hop:m * hop + nfft] += seg[k]
    ye *= 0.5  # sum of Hann windows at 75 % overlap is 2
    if circular:
        y = ye[:, :n].copy()
        y[:, :nfft] += ye[:, n:n + nfft]
        return y
    return ye[:, offset:offset + n]


REVERB_BANDS = ((0.0, 250.0, 2.4, 1.0), (250.0, 1000.0, 2.2, 1.0), (1000.0, 3000.0, 1.9, 1.0),
                (3000.0, 6000.0, 1.4, 0.8), (6000.0, 1e9, 0.8, 0.5))  # (lo, hi, RT60 s, level)


def reverb_ir(seconds=3.0, predelay=0.018):
    """Synthetic stereo hall: band-split noise, each band decays at its own RT60 (2.2 s mids)."""
    rng = rng_for("reverb-ir")
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = np.fft.rfftfreq(n, 1.0 / SR)
    lf = np.log2(np.maximum(f, 1.0))

    def step(c):  # 0 below c, 1 above, raised cosine over +-1/6 octave
        if c <= 0.0:
            return np.ones_like(lf)
        if c >= 1e8:
            return np.zeros_like(lf)
        return 0.5 + 0.5 * np.sin(np.pi / 2.0 * np.clip((lf - np.log2(c)) * 6.0, -1.0, 1.0))

    ir = np.zeros((2, n))
    for ch in range(2):
        spec = np.fft.rfft(rng.standard_normal(n))
        for lo, hi, rt60, level in REVERB_BANDS:
            mask = step(lo) * (1.0 - step(hi)) * level
            ir[ch] += np.fft.irfft(spec * mask, n) * np.exp(-6.9078 * t / rt60)
    nd = int(predelay * SR)
    ir = np.concatenate([np.zeros((2, nd)), ir[:, :n - nd]], axis=1)
    no = int(0.012 * SR)
    ir[:, nd:nd + no] *= ramp_up(no)  # soft onset, no hard first reflection
    k = int(0.3 * SR)
    ir[:, -k:] *= ramp_down(k)
    return ir / np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))  # unit energy per channel


def convolve(x, ir, circular):
    """FFT convolution. Circular mode folds the tail back onto the start (wrapped tails)."""
    n, m = x.shape[1], ir.shape[1]
    size = fast_len(n + m - 1)
    y = np.fft.irfft(np.fft.rfft(x, n=size, axis=1) * np.fft.rfft(ir, n=size, axis=1), n=size, axis=1)
    out = y[:, :n].copy()
    if circular:
        out[:, :m - 1] += y[:, n:n + m - 1]
    return out


def band_power_db(x, lo, hi):
    size = fast_len(x.shape[1])
    p = np.sum(np.abs(np.fft.rfft(x, n=size, axis=1)) ** 2, axis=0)
    f = np.fft.rfftfreq(size, 1.0 / SR)
    return 10.0 * np.log10(np.sum(p[(f >= lo) & (f < hi)]) + 1e-30)


# ---------------------------------------------------------------- loudness, limiter, files


def parse_ebur128(text: str) -> dict:
    s = text[text.rfind("Summary:"):]

    def grab(pattern):
        m = re.search(pattern, s, re.S)
        return float(m.group(1)) if m else float("nan")

    return {
        "I": grab(r"I:\s+(-?[\d.]+|-inf) LUFS"),
        "LRA": grab(r"LRA:\s+(-?[\d.]+) LU"),
        "TP": grab(r"True peak:\s+Peak:\s+(-?[\d.]+|-inf) dBFS"),
        "SP": grab(r"Sample peak:\s+Peak:\s+(-?[\d.]+|-inf) dBFS"),
    }


def loudness(x: np.ndarray) -> dict:
    """EBU R128 via ffmpeg ebur128, fed float32 on stdin (no temp files)."""
    data = np.ascontiguousarray(x.T, dtype="<f4").tobytes()
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[0]),
           "-i", "pipe:0", "-af", "ebur128=peak=true+sample:framelog=quiet", "-f", "null", "-"]
    res = subprocess.run(cmd, input=data, capture_output=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode("utf-8", "replace")[-600:])
    return parse_ebur128(res.stderr.decode("utf-8", "replace"))


def true_peak_track(x, circular, over=4, chunk=1 << 16, pad=1024):
    """Per-sample inter-sample peak estimate (4x band-limited upsampling, stereo linked)."""
    c, n = x.shape
    if circular:
        xe = np.concatenate([x[:, -pad:], x, x[:, :pad]], axis=1)
    else:
        xe = np.pad(x, ((0, 0), (pad, pad)))
    out = np.zeros(n)
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        seg = xe[:, s:e + 2 * pad]
        size = fast_len(seg.shape[1])
        up = np.fft.irfft(np.fft.rfft(seg, n=size, axis=1), n=size * over, axis=1) * over
        up = np.abs(up[:, pad * over:(pad + e - s) * over])
        out[s:e] = up.max(axis=0).reshape(e - s, over).max(axis=1)
    return out


LIM_BLOCK = 85  # divides BED_N and TRAILER_N, so the gain grid wraps exactly on the loop


def limiter_gain(tp, ceiling_db, circular, knee_db=3.0, look=3, release_s=0.15):
    """Soft-knee look-ahead limiter gain (linear, per sample) from a true-peak track.

    Static curve: unity below ceiling - knee, then an exponential knee that approaches
    the ceiling and never crosses it. Instant attack per 1.8 ms block, exponential
    release, then a +-(look+1) block minimum and a +-look block Hann smoother, which
    keeps the smoothed gain at or below the requirement on every block."""
    n = len(tp)
    assert n % LIM_BLOCK == 0
    nb = n // LIM_BLOCK
    lvl = 20.0 * np.log10(np.maximum(tp.reshape(nb, LIM_BLOCK).max(axis=1), 1e-9))
    start = ceiling_db - knee_db
    over = lvl - start
    need = np.where(over > 0.0, start + knee_db * (1.0 - np.exp(-over / knee_db)), lvl) - lvl
    a = float(np.exp(-LIM_BLOCK / (release_s * SR)))
    seq = np.concatenate([need, need]) if circular else need
    g = np.empty(len(seq))
    cur = 0.0
    for i, v in enumerate(seq.tolist()):
        cur = min(v, cur * a)
        g[i] = cur
    g = g[nb:] if circular else g
    w = look + 1
    ge = np.concatenate([g[-w:], g, g[:w]]) if circular else np.concatenate([np.full(w, g[0]), g, np.full(w, g[-1])])
    h = np.lib.stride_tricks.sliding_window_view(ge, 2 * w + 1).min(axis=1)
    kern = np.hanning(2 * look + 3)[1:-1]
    kern /= kern.sum()
    he = np.concatenate([h[-look:], h, h[:look]]) if circular else np.concatenate([np.full(look, h[0]), h, np.full(look, h[-1])])
    sm = np.convolve(he, kern, mode="valid")
    centres = (np.arange(nb) + 0.5) * LIM_BLOCK
    xs = np.arange(n)
    if circular:
        gs = np.interp(xs, np.concatenate([[centres[-1] - n], centres, [centres[0] + n]]),
                       np.concatenate([[sm[-1]], sm, [sm[0]]]))
    else:
        gs = np.interp(xs, centres, sm)
    return undb(gs), float(-need.min())


def master(x, circular, label):
    """Gain to -14 LUFS, then the soft-knee true-peak limiter; iterate on ffmpeg's numbers."""
    tp = true_peak_track(x, circular)
    m = loudness(x)
    gain_db = TARGET_LUFS - m["I"]
    ceiling = TP_CEILING
    y = x
    for it in range(8):
        g = float(undb(gain_db))
        lim, max_gr = limiter_gain(tp * g, ceiling, circular)
        y = x * (g * lim)
        m = loudness(y)
        log(f"{label}: pass {it + 1} gain {gain_db:+.2f} dB, ceiling {ceiling:.2f}, max GR {max_gr:.2f} dB "
            f"-> I {m['I']:.1f} LUFS, TP {m['TP']:.1f} dBTP, LRA {m['LRA']:.1f} LU")
        ok_i = abs(m["I"] - TARGET_LUFS) < 0.05
        ok_tp = m["TP"] <= TP_CEILING + 0.15
        if ok_i and ok_tp:
            break
        gain_db += TARGET_LUFS - m["I"]
        if not ok_tp:
            ceiling -= m["TP"] - TP_CEILING
    m["gain_db"] = round(gain_db, 3)
    m["max_gain_reduction_db"] = round(max_gr, 3)
    return y, m


def write_wav24(path: Path, x: np.ndarray) -> None:
    q = np.ascontiguousarray(np.clip(np.round(x.T * 8388608.0), -8388608, 8388607).astype("<i4"))
    raw = q.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()  # interleaved little-endian 24-bit
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[0])
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(raw)


def read_wav24(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    assert width == 3 and rate == SR, (width, rate)
    b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
    v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
    v = np.where(v >= 1 << 23, v - (1 << 24), v)
    return v.reshape(-1, ch).T / 8388608.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- the music

CHORDS = {
    # name: (bass, voicing set 1, voicing set 2 (second half), pitch classes for the arpeggio)
    "Dmaj9": (38, (50, 54, 57, 61, 64), (50, 57, 64, 66, 73), (2, 6, 9, 1, 4)),
    "Bm11": (35, (47, 54, 57, 62, 64), (47, 57, 64, 66, 74), (11, 2, 6, 9, 4)),
    "Gmaj9": (31, (43, 54, 57, 59, 62), (43, 59, 66, 69, 74), (7, 11, 2, 6, 9)),
    "A6sus4": (33, (45, 54, 57, 62, 64), (45, 57, 64, 66, 74), (9, 2, 4, 6)),
    "A": (33, (45, 52, 57, 61, 64), (45, 57, 61, 64, 73), (9, 1, 4)),
    "Dmaj9-final": (38, (50, 57, 64, 66, 69, 73), (50, 57, 64, 66, 69, 73), (2, 6, 9, 1, 4)),
}
CYCLE = ((("Dmaj9", 0, 4),), (("Bm11", 0, 4),), (("Gmaj9", 0, 4),), (("A6sus4", 0, 2), ("A", 2, 2)))
PAD_VEL = (0.55, 0.8, 0.85, 0.85, 0.8, 0.7)

EP_PATTERNS = {  # eighth-note slots in a bar, 1 = play
    "sparse": ((1, 0, 0, 0, 1, 0, 0, 0), (1, 0, 0, 1, 0, 0, 0, 0), (0, 0, 1, 0, 0, 0, 1, 0), (1, 0, 0, 0, 0, 1, 0, 0)),
    "light": ((1, 0, 1, 0, 0, 1, 0, 0), (1, 0, 0, 1, 0, 0, 1, 0), (1, 0, 0, 0, 1, 0, 1, 0), (0, 1, 0, 0, 1, 0, 0, 1)),
    "medium": ((1, 0, 1, 0, 0, 1, 0, 0), (1, 0, 0, 1, 0, 1, 0, 0), (0, 1, 0, 1, 0, 0, 1, 0),
               (1, 0, 1, 1, 0, 0, 1, 0), (1, 0, 0, 1, 0, 1, 1, 0), (1, 0, 1, 0, 1, 0, 0, 1)),
    "full": ((1, 0, 1, 1, 0, 1, 0, 1), (1, 1, 0, 1, 0, 1, 1, 0), (1, 0, 1, 0, 1, 1, 0, 1)),
}
REG1, REG2 = (64, 81), (66, 85)  # arpeggio registers, first and second half
BELL_FIGURES = {"rise": (81, 86, 90), "fall": (90, 88, 86), "rise2": (83, 86, 88), "final": (86, 90, 93)}
SWING = 0.53  # off-beat eighths land at 53 % of the beat: a lazy, human lilt
# Faders set by measurement (--stems prints each layer's LUFS before the mix): the
# targets are pad -20, EP -22.5, bass -24.5, kick -27, bells -28, hats + shaker -33.
# The master stage then lifts the whole mix to -14 LUFS.
FADERS_DB = {"pad": -22.6, "ep": -9.8, "bell": -15.7, "bass": -18.6, "kick": -12.5, "hats": -20.5}
SEND_MELODIC, SEND_HATS, SEND_KICK = 0.22, 0.12, 0.04  # reverb wet share per bus


def swung(u: float) -> float:
    """Map a position inside the beat (0..1) onto the swung grid."""
    return u * 2.0 * SWING if u < 0.5 else SWING + (u - 0.5) * 2.0 * (1.0 - SWING)


class Piece:
    def __init__(self, name, n, circular, spb, t0):
        self.name, self.n, self.circular = name, n, circular
        self.spb, self.t0 = spb, t0  # samples per beat, sample index of beat 0
        self.segs: list[tuple[float, float, str, int]] = []
        self.reattack: set[float] = set()
        self.pad_end = 0.0
        self.final_release = None
        self.cutoff = None
        self.ep_plan: list = []
        self.ep_extra: list = []
        self.bells: list = []
        self.reverse_bells: list = []
        self.bass_plan: list = []
        self.kicks: list = []
        self.hats: list = []
        self.shakers: list = []
        self.ride: tuple | None = None  # (seconds, dB) knots for a whole-mix fader ride

    def pos(self, beat: float, jitter_s: float = 0.0) -> float:
        return self.t0 + beat * self.spb + jitter_s * SR

    def chord_at(self, beat: float):
        for seg in self.segs:
            if seg[0] <= beat < seg[0] + seg[1]:
                return seg
        return self.segs[-1]


def jitter(rng, ms=8.0, sd=4.0):
    return float(np.clip(rng.normal(0.0, sd), -ms, ms)) / 1000.0


def render_pad(p: Piece):
    rng = rng_for(f"{p.name}:pad")
    tr = Track(p.n, p.circular)
    cur: dict[int, list] = {}
    notes = []
    for beat, _beats, name, vset in p.segs:
        voicing = CHORDS[name][vset]  # vset 1 or 2 indexes the voicing set
        re_hit = beat in p.reattack
        for v in range(6):
            pitch = voicing[v] if v < len(voicing) else None
            c = cur.get(v)
            if c is not None and (re_hit or c[0] != pitch):
                notes.append((v, c[0], c[1], beat, c[2]))
                del cur[v]
            if pitch is not None and v not in cur:
                cur[v] = [pitch, beat, "phrase" if re_hit else "move"]
    for v, c in cur.items():
        notes.append((v, c[0], c[1], p.pad_end, c[2]))
    for v, midi, b0, b1, kind in notes:
        lead = 0.25 if kind == "phrase" else 0.08
        attack = 0.9 if kind == "phrase" else 0.45
        release = p.final_release if (p.final_release and b1 == p.pad_end) else 2.0
        start = p.pos(b0) - lead * SR
        dur = (b1 - b0) * p.spb / SR + lead
        if start < 0 and not p.circular:  # the trailer opens on this chord at t = 0
            dur += start / SR
            start, attack = 0.0, 2.2
        tr.add(start, pad_note(rng, midi, dur, PAD_VEL[v], attack, release))
    return tr.buf


def render_ep(p: Piece):
    rng = rng_for(f"{p.name}:ep")
    tr = Track(p.n, p.circular)
    last = None
    count = 0
    for bar, density, (lo, hi), octave in p.ep_plan:
        pats = EP_PATTERNS[density]
        pat = pats[int(rng.integers(len(pats)))]
        for slot in range(8):
            if not pat[slot]:
                continue
            grid = bar * 4 + slot * 0.5
            beat = bar * 4 + int(slot // 2) + swung((slot % 2) * 0.5)
            seg = p.chord_at(grid)
            pool = [m for m in range(lo, hi + 1) if m % 12 in CHORDS[seg[2]][3]]
            i = len(pool) // 2 if last is None else int(np.argmin([abs(m - last) for m in pool]))
            frac = i / max(1, len(pool) - 1)
            steps = np.array([-2, -1, 1, 2])
            prob = np.array([0.15, 0.35, 0.35, 0.15]) * np.where(steps < 0, 0.6 + frac, 1.6 - frac)
            i = int(np.clip(i + rng.choice(steps, p=prob / prob.sum()), 0, len(pool) - 1))
            midi = pool[i]
            last = midi
            base = 0.80 if slot == 0 else (0.68 if slot % 2 == 0 else 0.56)
            vel = float(np.clip(base * (1.0 + rng.normal(0.0, 0.08)), 0.3, 0.95))
            ring = (seg[0] + seg[1] - beat) * p.spb / SR + 0.12  # pedal lifts at the chord change
            dur = float(np.clip(ring, 0.3, 1.6))
            pan = float(np.clip(rng.normal(0.0, 0.22), -0.45, 0.45))
            tr.add(p.pos(beat, jitter(rng)), ep_note(midi, dur, vel, pan))
            count += 1
            if octave and midi + 12 <= 88:
                tr.add(p.pos(beat, jitter(rng, 4, 2)), ep_note(midi + 12, dur, vel * 0.45, -pan))
    for beat, midi, dur, vel in p.ep_extra:  # e.g. the trailer's final rolled chord
        tr.add(p.pos(beat, jitter(rng, 3, 1.5)), ep_note(midi, dur, vel, float(rng.uniform(-0.3, 0.3))))
        count += 1
    return tr.buf, count


def render_bells(p: Piece):
    rng = rng_for(f"{p.name}:bells")
    tr = Track(p.n, p.circular)
    for beat, fig, vel in p.bells:
        for i, midi in enumerate(BELL_FIGURES[fig]):
            v = vel * (1.0 - 0.18 * i) * (1.0 + rng.normal(0.0, 0.05))
            gl, gr = pan_gains((-0.35, 0.05, 0.4)[i])
            s = bell_note(rng, midi, v)
            tr.add(p.pos(beat + 0.25 * i, jitter(rng, 5, 2.5)), np.vstack([gl * s, gr * s]))
    for end_beat, midi, vel, length in p.reverse_bells:  # swell that ends on a downbeat
        s = bell_note(rng, midi, vel, length=length, attack=0.08, reverse=True)
        tr.add(p.pos(end_beat) - len(s), s)
    return tr.buf


def render_bass(p: Piece):
    tr = Track(p.n, p.circular)
    for beat, beats, vel, release in p.bass_plan:
        root = CHORDS[p.chord_at(beat)[2]][0]
        tr.add(p.pos(beat), bass_note(root, beats * p.spb / SR + 0.02, vel, release))
    return tr.buf


def render_drums(p: Piece):
    rng = rng_for(f"{p.name}:drums")
    hat_bank = noise_bank(rng, 4000.0, 8000.0)  # brushes: dark, above the speech band
    shk_bank = noise_bank(rng, 5000.0, 9000.0)
    kicks, hats = Track(p.n, p.circular), Track(p.n, p.circular)
    pump = Track(p.n, p.circular, channels=1)
    shape = pump_shape()
    for beat, vel in p.kicks:
        at = p.pos(beat, jitter(rng, 4, 2))
        kicks.add(at, kick(vel * (1.0 + rng.normal(0.0, 0.04))))
        pump.add(at, shape * min(1.0, vel / 0.9))
    for beat, vel in p.hats:
        s = noise_hit(rng, hat_bank, vel * (1.0 + rng.normal(0.0, 0.1)), 0.25, 0.008, 0.06)
        gl, gr = pan_gains(0.25)
        hats.add(p.pos(beat, jitter(rng, 6, 3)), np.vstack([gl * s, gr * s]))
    for beat, vel in p.shakers:
        s = noise_hit(rng, shk_bank, vel * (1.0 + rng.normal(0.0, 0.12)), 0.14, 0.006, 0.035)
        gl, gr = pan_gains(-0.3)
        hats.add(p.pos(beat, jitter(rng, 6, 3)), np.vstack([gl * s, gr * s]))
    return kicks.buf, hats.buf, pump.buf[0]


def pump_shape(attack=0.012, recover=0.13, length=0.6):
    """Unit sidechain dip: 12 ms down, exponential recovery."""
    n = int(length * SR)
    t = np.arange(n) / SR
    s = np.exp(-np.maximum(t - attack, 0.0) / recover)
    na = int(attack * SR)
    s[:na] = ramp_up(na)
    k = n // 4
    s[-k:] *= ramp_down(k)
    return s


def bed_piece() -> Piece:
    p = Piece("bed", BED_N, True, BED_N / (BED_BARS * 4), 0.0)
    for bar in range(BED_BARS):
        vset = 2 if 24 <= bar < 44 else 1  # second half voicings, back home for the last 4 bars
        for name, b0, nb in CYCLE[bar % 4]:
            p.segs.append((bar * 4 + b0, nb, name, vset))
    p.reattack = {0, 32, 64, 96, 128, 160, 176}  # bars 1, 9, 17, 25, 33, 41, 45
    p.pad_end = BED_BARS * 4
    lfo = BED_N / 6 / SR  # one filter sweep per 8 bars, six per loop: periodic on the loop
    p.cutoff = lambda t: 1800.0 * 2.0 ** (0.3 * np.sin(TWO_PI * np.asarray(t) / lfo))
    for bar in range(BED_BARS):
        dens = "sparse" if bar < 4 or bar >= 44 else ("light" if bar < 8 else "medium")
        p.ep_plan.append((bar, dens, REG2 if 24 <= bar < 44 else REG1, False))
    for i, (bar, fig) in enumerate(((0, "rise"), (8, "fall"), (16, "rise2"), (24, "rise"), (32, "fall"), (40, "rise2"))):
        p.bells.append((bar * 4, fig, 0.5 if i % 2 == 0 else 0.42))
    for bar in range(BED_BARS):
        p.bass_plan.append((bar * 4, 4, 0.8 if bar < 4 or bar >= 44 else 0.9, 0.16))
    for bar in range(4, 44):  # drums in at bar 5, out for the last 4 bars
        p.kicks += [(bar * 4, 0.9), (bar * 4 + 2, 0.78)]
        if bar % 8 == 7:
            p.kicks.append((bar * 4 + 3 + SWING, 0.4))  # soft pickup into each new phrase
        for beat in range(4):
            p.hats.append((bar * 4 + beat + SWING, 0.42 if bar < 8 else 0.55))
        if bar >= 8:
            for beat in range(4):
                for k, v in enumerate((0.40, 0.25, 0.62, 0.28)):
                    p.shakers.append((bar * 4 + beat + swung(k / 4), v))
    return p


def trailer_piece() -> Piece:
    spb = BEAT_S * SR
    t0 = (20.0 - 32 * BEAT_S) * SR  # bar 9 (the lift) lands exactly on 20.0 s
    p = Piece("trailer", TRAILER_N, False, spb, t0)
    for bar in range(8):
        for name, b0, nb in CYCLE[bar % 4]:
            p.segs.append((bar * 4 + b0, nb, name, 1))
    p.segs += [(32, 4, "Dmaj9", 2), (36, 4, "Bm11", 2), (40, 2, "Gmaj9", 2), (42, 1, "A6sus4", 2),
               (43, 1, "A", 2), (44, 6, "Dmaj9-final", 2)]
    p.reattack = {0, 16, 32, 44}
    p.pad_end, p.final_release = 47, 3.2  # final chord holds 3 beats, then a 3.2 s release
    knots_t = np.array([0.0, 7.0, 18.3, 20.0, 27.8, 30.0, 34.0])
    knots_f = np.log2([700.0, 1800.0, 1800.0, 2600.0, 2400.0, 1600.0, 1000.0])
    p.cutoff = lambda t: 2.0 ** (np.interp(np.asarray(t), knots_t, knots_f) + 0.12 * np.sin(TWO_PI * 0.1 * np.asarray(t)))
    for bar, dens in ((1, "sparse"), (2, "light"), (3, "light"), (4, "medium"), (5, "medium"), (6, "medium"), (7, "light")):
        p.ep_plan.append((bar, dens, REG1, False))
    for bar in (8, 9, 10):
        p.ep_plan.append((bar, "full", REG2, True))  # the lift: busier and doubled an octave up
    p.ep_extra = [(44 + 0.14 * i, m, 2.2, 0.62 - 0.04 * i) for i, m in enumerate((62, 66, 69, 73, 76))]
    p.bells = [(16, "rise", 0.5), (32, "rise2", 0.6), (44, "final", 0.55)]
    p.reverse_bells = [(32, 86, 0.45, 2.0)]
    p.bass_plan = [(bar * 4, 4, 0.7 if bar == 2 else 0.9, 0.16) for bar in range(2, 11)]
    p.bass_plan.append((44, 3, 0.9, 1.2))
    for bar in range(3, 11):
        p.kicks.append((bar * 4, 0.9))
        if bar != 7:  # a breath on beat 3 just before the lift
            p.kicks.append((bar * 4 + 2, 0.78))
        for beat in range(4):
            if bar == 7 and beat >= 2:
                for k in range(4):  # quiet sixteenth hats rising into the lift
                    p.hats.append((bar * 4 + beat + swung(k / 4), 0.3 + 0.06 * ((beat - 2) * 4 + k)))
            else:
                p.hats.append((bar * 4 + beat + SWING, 0.55))
    p.kicks.append((44, 0.7))
    # fader ride: the pad intro sits well under the groove, a short breath before 20 s,
    # then the lift steps up about 2 dB with the brighter voicings and doubled keys
    p.ride = ((0.0, -7.0), (4.35, -5.0), (6.9, -1.5), (9.5, 0.0), (18.3, 0.0), (19.6, -0.8), (20.0, 2.0),
              (27.8, 2.0), (30.0, 1.0), (34.0, 1.0))
    for bar in range(2, 11):
        scale = 0.5 if bar == 2 else 1.0
        for beat in range(4):
            for k, v in enumerate((0.40, 0.25, 0.62, 0.28)):
                p.shakers.append((bar * 4 + beat + swung(k / 4), v * scale))
    return p


IR_CACHE: list[np.ndarray] = []


def render(p: Piece, stems_report: bool = False) -> tuple[np.ndarray, dict]:
    log(f"{p.name}: synthesising layers")
    pad = render_pad(p)
    pad = moving_lowpass(pad, p.cutoff, p.circular)
    ep, ep_count = render_ep(p)
    bell = render_bells(p)
    bass = render_bass(p)
    kicks, hats, pump_db = render_drums(p)
    bass *= undb(-5.0 * pump_db)  # sidechain-style pump from the kick
    pad *= undb(-1.5 * pump_db)
    stems = {"pad": pad, "ep": ep, "bell": bell, "bass": bass, "kick": kicks, "hats": hats}
    for k in stems:
        stems[k] = stems[k] * undb(FADERS_DB[k])
    info: dict = {"ep_notes": ep_count, "kick_hits": len(p.kicks), "hat_hits": len(p.hats),
                  "shaker_hits": len(p.shakers), "bell_figures": len(p.bells)}
    info["stems_lufs"] = {k: loudness(v)["I"] for k, v in stems.items()}
    if stems_report:
        log(f"{p.name}: stem loudness {info['stems_lufs']}")
    log(f"{p.name}: speech-band dip, reverb, master EQ")
    melodic_raw = stems["pad"] + stems["ep"] + stems["bell"]
    melodic = eq(melodic_raw, speech_dip, p.circular)
    info["dip_db"] = round(band_power_db(melodic, 1500, 4000) - band_power_db(melodic_raw, 1500, 4000), 2)
    if not IR_CACHE:
        IR_CACHE.append(reverb_ir())
    send = SEND_MELODIC * melodic + SEND_HATS * stems["hats"] + SEND_KICK * stems["kick"]
    wet = convolve(send, IR_CACHE[0], p.circular)
    mix = ((1 - SEND_MELODIC) * melodic + (1 - SEND_HATS) * stems["hats"] + (1 - SEND_KICK) * stems["kick"]
           + stems["bass"] + wet)
    mix = eq(mix, master_eq, p.circular)
    if p.ride:
        kt, kd = zip(*p.ride, strict=True)
        mix *= undb(np.interp(np.arange(p.n) / SR, kt, kd))
    if not p.circular:  # trailer: exact silence at both ends
        n_in, n_out = int(0.01 * SR), int(1.2 * SR)
        mix[:, :n_in] *= ramp_up(n_in)
        mix[:, -n_out:] *= ramp_down(n_out)
    return mix, info


# ---------------------------------------------------------------- preview


def speech_like(seconds: float) -> np.ndarray:
    """Speech stand-in: 300 Hz to 3 kHz noise bursts in syllable, word and phrase rhythm."""
    rng = rng_for("preview:speech")
    n = int(seconds * SR)
    env = np.zeros(n)
    t = 0.4
    while t < seconds - 0.8:
        for _ in range(int(rng.integers(3, 7))):  # words per phrase
            for _ in range(int(rng.integers(1, 4))):  # syllables per word
                d = rng.uniform(0.10, 0.22)
                i0, m = int(t * SR), int(d * SR)
                if i0 + m >= n:
                    break
                k = np.arange(m) / m
                env[i0:i0 + m] = np.maximum(env[i0:i0 + m], rng.uniform(0.55, 1.0) * np.sin(np.pi * k) ** 0.6)
                t += d + rng.uniform(0.015, 0.05)
            t += rng.uniform(0.06, 0.14)  # gap between words
        t += rng.uniform(0.35, 0.65)  # breath between phrases
    f = np.fft.rfftfreq(n, 1.0 / SR)
    shape = hp2(f, 300.0) * lp2(f, 3000.0) / np.sqrt(1.0 + (f / 700.0) ** 2)
    noise = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) * shape, n)
    return noise * env


def duck_gain(key, threshold=0.02, ratio=8.0, attack=0.04, release=0.6, knee_db=9.0, block=48):
    """Simple RMS sidechain ducker with the kit's settings (threshold 0.02, ratio 8, 40/600 ms)."""
    nb = len(key) // block
    p = (key[:nb * block].reshape(nb, block) ** 2).mean(axis=1)
    aa, ar = np.exp(-block / (attack * SR)), np.exp(-block / (release * SR))
    env = np.empty(nb)
    e = 0.0
    for i, v in enumerate(p.tolist()):
        c = aa if v > e else ar
        e = c * e + (1.0 - c) * v
        env[i] = e
    over = 10.0 * np.log10(env + 1e-20) - 20.0 * np.log10(threshold)
    gr = np.where(over <= -knee_db / 2, 0.0,
                  np.where(over >= knee_db / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee_db / 2) ** 2 / (2 * knee_db)))
    centres = (np.arange(nb) + 0.5) * block
    return undb(-np.interp(np.arange(len(key)), centres, gr))


def render_preview(bed: np.ndarray) -> tuple[np.ndarray, dict]:
    n = int(PREVIEW_S * SR)
    start = round(16 * 4 * BED_N / (BED_BARS * 4))  # bar 17: full groove, the busiest texture
    music = bed[:, start:start + n] * undb(-21.0)
    speech = speech_like(PREVIEW_S)
    # edge-tts en-US-AndrewNeural at -5 % measured -19.9 LUFS, so the stand-in sits at -20 LUFS
    speech *= undb(-20.0 - loudness(np.vstack([speech, speech]))["I"])
    speech2 = np.vstack([speech, speech])
    gain = duck_gain(speech)
    ducked = music * gain
    mix = speech2 + ducked
    norm = float(undb(-16.0 - loudness(mix)["I"]))  # the kit normalises the final mix to -16 LUFS
    mix, speech2, ducked, music = mix * norm, speech2 * norm, ducked * norm, music * norm
    k = int(0.3 * SR)
    mix[:, :k] *= ramp_up(k)
    mix[:, -k:] *= ramp_down(k)
    ls, lm, lu = loudness(speech2)["I"], loudness(ducked)["I"], loudness(music)["I"]
    info = {
        "bed_excerpt_start_s": round(start / SR, 3),
        "speech_lufs": ls,
        "music_ducked_lufs": lm,
        "music_unducked_lufs": lu,
        "speech_to_music_lu": round(ls - lm, 1),
        "speech_to_music_unducked_lu": round(ls - lu, 1),
        "max_duck_db": round(float(-20 * np.log10(gain.min())), 1),
    }
    return mix, info


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=("bed", "trailer", "preview"), action="append")
    ap.add_argument("--stems", action="store_true", help="print per-layer loudness (mix calibration)")
    args = ap.parse_args()
    want = set(args.only or ("bed", "trailer", "preview"))
    OUT.mkdir(parents=True, exist_ok=True)
    levels_path = OUT / "levels.json"
    levels = json.loads(levels_path.read_text()) if levels_path.exists() else {}
    bed = None
    if "bed" in want:
        mix, info = render(bed_piece(), args.stems)
        bed, m = master(mix, True, "bed")
        write_wav24(OUT / "zts-bed.wav", bed)
        levels["bed"] = {**m, **info, "frames": BED_N, "seconds": round(BED_N / SR, 4), "bars": BED_BARS, "bpm": BPM}
        log(f"wrote music/zts-bed.wav ({BED_N} frames, {BED_N / SR:.3f} s)")
    if "trailer" in want:
        mix, info = render(trailer_piece(), args.stems)
        trailer, m = master(mix, False, "trailer")
        write_wav24(OUT / "zts-trailer.wav", trailer)
        levels["trailer"] = {**m, **info, "frames": TRAILER_N, "seconds": TRAILER_N / SR}
        log(f"wrote music/zts-trailer.wav ({TRAILER_N / SR:.1f} s)")
    if "preview" in want:
        if bed is None:
            bed = read_wav24(OUT / "zts-bed.wav")
        mix, info = render_preview(bed)
        write_wav24(OUT / "preview-ducked.wav", mix)
        info.update(loudness(mix))
        levels["preview"] = info
        log(f"wrote music/preview-ducked.wav, speech to music {info['speech_to_music_lu']} LU")
    levels["sha256"] = {p.name: sha256(p) for p in sorted(OUT.glob("*.wav"))}
    levels_path.write_text(json.dumps(levels, indent=2) + "\n")
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
