#!/usr/bin/env python3
"""
Validate the rendered music without listening to it.

    python3 tools/music/check.py [--scratch DIR] [--report FILE]

Reads music/*.wav from disk and checks: format and length, EBU R128 loudness and true
peak (ffmpeg ebur128, the same command the episode gates use), clipping and DC, band
energy, the bed's loop joint, hiss and aliasing, silent stretches, the trailer tail,
and the speech-to-music ratio of the ducked preview (also re-measured through the
video kit's own ffmpeg ducking chain). Exits 1 if any hard check fails.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose as C  # noqa: E402

SR = C.SR
OUT = C.OUT
BANDS = (("sub", 20, 60), ("low", 60, 250), ("low-mid", 250, 1500), ("speech 1.5-4k", 1500, 4000), ("high", 4000, 20000))
LINES: list[str] = []
FAILS: list[str] = []


def say(s: str = "") -> None:
    print(s, flush=True)
    LINES.append(s)


def gate(ok: bool, what: str) -> str:
    if not ok:
        FAILS.append(what)
    return "ok" if ok else "FAIL"


def ebur128_file(path: Path) -> tuple[dict, np.ndarray]:
    """Exactly `ffmpeg -i f.wav -af ebur128=peak=true -f null -`, plus the per-frame log."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True, check=True)
    summary = C.parse_ebur128(res.stderr)
    frames = np.array([(float(t), float(m), float(s)) for t, m, s in
                       re.findall(r"t:\s*([\d.]+)\s+TARGET:.*?M:\s*(-?[\d.]+|-inf)\s+S:\s*(-?[\d.]+|-inf)", res.stderr)])
    return summary, frames


def ffprobe(path: Path) -> dict:
    entries = "stream=codec_name,sample_rate,channels,bits_per_sample:format=duration"
    res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries, "-of", "json", str(path)],
                         capture_output=True, text=True, check=True)
    d = json.loads(res.stdout)
    s = d["streams"][0]
    return {"codec": s["codec_name"], "rate": int(s["sample_rate"]), "channels": s["channels"],
            "bits": s.get("bits_per_sample"), "duration": float(d["format"]["duration"])}


def welch(x: np.ndarray, nfft: int = 16384) -> tuple[np.ndarray, np.ndarray]:
    """Average power spectrum (both channels summed), Hann frames, 50 % overlap."""
    hop = nfft // 2
    win = np.hanning(nfft)
    n = (x.shape[1] - nfft) // hop + 1
    acc = np.zeros(nfft // 2 + 1)
    for ch in range(x.shape[0]):
        for s in range(0, n, 256):
            idx = (np.arange(s, min(n, s + 256)) * hop)[:, None] + np.arange(nfft)[None, :]
            acc += np.sum(np.abs(np.fft.rfft(x[ch][idx] * win, axis=1)) ** 2, axis=0)
    return np.fft.rfftfreq(nfft, 1.0 / SR), acc / (n * x.shape[0])


def band_table(name: str, x: np.ndarray) -> dict:
    f, p = welch(x)
    total = p[(f >= 20) & (f < 20000)].sum()
    rows = {}
    for label, lo, hi in BANDS:
        e = p[(f >= lo) & (f < hi)].sum()
        rows[label] = (100.0 * e / total, 10 * np.log10(e / total), 10 * np.log10(e / total / np.log2(hi / lo)))
    ref = rows["low-mid"][2]
    say(f"\n{name}: band energy (both channels, whole file)")
    say("| band | range | share | level re total | per octave re low-mid |")
    say("|---|---|---:|---:|---:|")
    for label, lo, hi in BANDS:
        share, lvl, dens = rows[label]
        say(f"| {label} | {lo}-{hi} Hz | {share:.2f} % | {lvl:+.1f} dB | {dens - ref:+.1f} dB/oct |")
    return rows


def flatness(p: np.ndarray) -> float:
    p = np.maximum(p, 1e-30)
    return float(np.exp(np.mean(np.log(p))) / np.mean(p))


def noise_report(name: str, x: np.ndarray, quiet: np.ndarray | None) -> None:
    f, p = welch(x)
    total = p[(f >= 20) & (f < 20000)].sum()
    above12 = 10 * np.log10(p[f >= 12000].sum() / total)
    above16 = 10 * np.log10(p[f >= 16000].sum() / total)
    white = C.rng_for("check:white").standard_normal((2, 20 * SR))
    fw, pw = welch(white)
    say(f"\n{name}: hiss and aliasing")
    say(f"- energy above 12 kHz: {above12:.1f} dB re total, above 16 kHz: {above16:.1f} dB; all of it is the brushed hat "
        f"and shaker (no harsh highs gate: below -30 dB) {gate(above12 < -30, name + ' HF energy')}")
    m, mw = (f >= 1000) & (f < 8000), (fw >= 1000) & (fw < 8000)
    fq, pq = welch(quiet)
    say(f"- spectral flatness 1-8 kHz: whole file {flatness(p[m]):.4f}, drumless stretch {flatness(pq[m]):.4f} "
        f"(white noise reference {flatness(pw[mw]):.3f}, pure tones near 0) {gate(flatness(pq[m]) < 0.05, name + ' tonal')}")
    m8 = (f >= 8000) & (f < 16000)
    say(f"- spectral flatness 8-16 kHz, whole file: {flatness(p[m8]):.3f} (noise-like by design: brushes)")
    floor = 10 * np.log10(np.median(pq[(fq >= 10000) & (fq < 20000)]) / pq.max())
    hf = 10 * np.log10(pq[fq >= 9000].sum() / pq[(fq >= 20) & (fq < 20000)].sum())
    say(f"- drumless stretch (no hat, no shaker): median 10-20 kHz power {floor:.1f} dB below the spectral peak, "
        f"energy above 9 kHz {hf:.1f} dB re total: no hiss floor {gate(floor < -80 and hf < -60, name + ' noise floor')}")


def alias_selftest() -> None:
    """Render each oscillator alone at its highest pitch; any partial that is not a
    multiple of the fundamental (or a designed bell ratio) would be aliasing."""
    say("\noscillator self-test (2 s tones, 1 Hz bins, Blackman-Harris window)")
    say("| source | f0 | partials expected up to | largest unexpected component | energy above 8.5 kHz |")
    say("|---|---:|---:|---:|---:|")
    n = 2 * SR
    tests = []
    for kind, midi in (("saw", 74), ("tri", 74), ("saw", 31)):
        f0 = C.midi_hz(midi)
        tests.append((f"pad {kind} table, MIDI {midi}", f0, C.osc(C.wavetable(kind, f0), f0, n, 0.1), [f0 * k for k in range(1, 400)]))
    f0 = C.midi_hz(88)
    ep = C.ep_note(88, 1.8, 0.95, 0.0)[0][:n]
    tests.append(("EP FM, MIDI 88, velocity 0.95", f0, np.pad(ep, (0, n - len(ep))), [f0 * k for k in range(1, 40)]))
    f0 = C.midi_hz(93)
    b = C.bell_note(np.random.default_rng(1), 93, 1.0, length=2.0)
    tests.append(("bell, MIDI 93", f0, b, [f0 * r for r, _, _ in C.BELL_PARTIALS]))
    f0 = C.midi_hz(38)
    tests.append(("sub bass, MIDI 38", f0, C.bass_note(38, 1.9, 1.0)[:n], [f0, 2 * f0]))
    win = blackman_harris(SR)
    for label, f0, sig, partials in tests:
        seg = sig[int(0.5 * SR):int(1.5 * SR)] * win
        spec = np.abs(np.fft.rfft(seg)) ** 2
        f = np.fft.rfftfreq(SR, 1.0 / SR)
        near = np.zeros_like(f, dtype=bool)
        for q in partials:
            if q < SR / 2:
                near |= np.abs(f - q) <= 12.0
        worst = 10 * np.log10(spec[~near].max() / spec.max())
        hf = 10 * np.log10(spec[f > 8500].sum() / spec.sum() + 1e-30)
        top = max(q for q in partials if q < 8000.0 or q == partials[0])
        say(f"| {label} | {f0:.1f} Hz | {top:.0f} Hz | {worst:.1f} dB | {hf:.1f} dB |")
        gate(worst < -80 and hf < -90, f"alias test {label}")


def blackman_harris(n: int) -> np.ndarray:
    k = np.arange(n) / n
    return 0.35875 - 0.48829 * np.cos(2 * np.pi * k) + 0.14128 * np.cos(4 * np.pi * k) - 0.01168 * np.cos(6 * np.pi * k)


def loop_joint(x: np.ndarray) -> None:
    n = x.shape[1]
    xx = np.concatenate([x, x], axis=1)  # the bed twice, end to end
    d1 = np.abs(np.diff(x, axis=1, append=x[:, :1]))  # includes the wrap-around step
    d2 = np.abs(x[:, 2:] - 2 * x[:, 1:-1] + x[:, :-2])
    jump = np.abs(xx[:, n] - xx[:, n - 1])
    curv = np.abs(xx[:, n + 1] - 2 * xx[:, n] + xx[:, n - 1])
    say("\nbed loop joint (file rendered twice end to end, joint between sample N-1 and N)")
    for ch, name in enumerate(("L", "R")):
        rank = 100.0 * np.mean(d1[ch] < jump[ch])
        say(f"- {name}: jump {jump[ch]:.6f} FS ({20 * np.log10(jump[ch] + 1e-12):.1f} dBFS); file max step {d1[ch].max():.6f}, "
            f"99.9th pct {np.percentile(d1[ch], 99.9):.6f}, joint ranks at the {rank:.1f}th percentile; "
            f"2nd difference {curv[ch]:.2e} vs file 99.9th pct {np.percentile(d2[ch], 99.9):.2e}")
        gate(jump[ch] <= np.percentile(d1[ch], 99.9) and curv[ch] <= np.percentile(d2[ch], 99.9), f"loop joint {name}")
    w = int(0.05 * SR)

    def step_db(at: int) -> tuple[float, float, float]:
        pre = 20 * np.log10(np.sqrt(np.mean(xx[:, at - w:at] ** 2)))
        post = 20 * np.log10(np.sqrt(np.mean(xx[:, at:at + w] ** 2)))
        return pre, post, post - pre

    pre, post, d = step_db(n)
    bar = n / C.BED_BARS
    others = [step_db(round(b * bar))[2] for b in (8, 16, 24, 32, 40, 44)]  # the other phrase downbeats
    say(f"- RMS 50 ms before the joint {pre:.1f} dBFS, after {post:.1f} dBFS ({d:+.2f} dB, the bar 1 downbeat); "
        f"the same step at the other phrase downbeats (bars 9, 17, 25, 33, 41, 45): {min(others):+.2f} to {max(others):+.2f} dB "
        f"{gate(min(others) - 1.0 <= d <= max(others) + 1.0, 'loop level step like any phrase start')}")
    med = 20 * np.log10(np.median(np.sqrt(np.mean(x[:, :(n // w) * w].reshape(2, -1, w) ** 2, axis=(0, 2)))))
    say(f"- the 50 ms just before the joint sits {pre - med:+.1f} dB from the file's median 50 ms RMS ({med:.1f} dBFS): "
        f"the drumless bars breathe, there is no gap {gate(pre - med > -6.0, 'no gap before the joint')}")
    # click detector: energy above 10 kHz in 5 ms windows; a click would spike at the joint
    hp = C.eq(xx[:, n - SR:n + SR], lambda f: (f > 10000).astype(float), False)
    e = np.sum(hp ** 2, axis=0)
    win = int(0.005 * SR)
    frames = e[:(len(e) // win) * win].reshape(-1, win).sum(axis=1)
    centre = frames[len(frames) // 2 - 1:len(frames) // 2 + 1].max()
    say(f"- energy above 10 kHz in the 5 ms windows at the joint: {10 * np.log10(centre / np.median(frames)):+.1f} dB "
        f"re the median 5 ms window of the surrounding 2 s (a click would read +20 dB or more) "
        f"{gate(centre <= 4 * np.median(frames) + 1e-30, 'loop click energy')}")
    rms = np.sqrt(np.mean(xx[:, n - 4 * SR:n + 4 * SR].reshape(2, -1, SR // 10) ** 2, axis=(0, 2)))
    say(f"- 100 ms RMS across the 8 s around the joint: min {20 * np.log10(rms.min()):.1f} dBFS, "
        f"max {20 * np.log10(rms.max()):.1f} dBFS (no gap)")
    # drums enter at bar 5 and leave after bar 44: brush band (5-9 kHz) energy per bar
    hb = C.eq(x, lambda f: ((f >= 5000) & (f < 9000)).astype(float), True)
    per_bar = np.array([np.sum(hb[:, round(b * bar):round((b + 1) * bar)] ** 2) for b in range(C.BED_BARS)])
    rel = 10 * np.log10(per_bar / per_bar.max() + 1e-30)
    fmt = lambda bars: " ".join(f"{b + 1}:{rel[b]:.0f}" for b in bars)  # noqa: E731
    gap = rel[4:44].min() - max(rel[:4].max(), rel[44:].max())
    say(f"- brush band (5-9 kHz) energy per bar, dB re loudest bar: {fmt(range(0, 9))} ... {fmt(range(40, 48))}; "
        f"every drum bar is at least {gap:.1f} dB above every drumless bar "
        f"{gate(gap >= 10.0, 'drums only in bars 5-44')}")
    # the real path: ffmpeg's own looping demuxer, as the video kit runs it
    res = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-stream_loop", "1", "-i", str(OUT / "zts-bed.wav"),
                          "-af", "aformat=sample_fmts=flt:sample_rates=48000:channel_layouts=stereo,asetpts=N/SR/TB",
                          "-f", "f32le", "-"], capture_output=True, check=True)
    looped = np.frombuffer(res.stdout, "<f4").reshape(-1, 2).T.astype(float)
    same = looped.shape[1] == 2 * n and float(np.abs(looped - xx).max()) < 1e-7
    say(f"- ffmpeg -stream_loop decode (the kit's path): {looped.shape[1]} frames = 2 x {n}, "
        f"max difference from the file twice end to end {np.abs(looped - xx[:, :looped.shape[1]]).max():.1e} "
        f"{gate(same, 'ffmpeg loop path identical')}")


def transient_report(name: str, x: np.ndarray, m: dict) -> None:
    """Onset steps: 5 ms RMS against the 50 ms before it. A hard hit reads 20 dB or more."""
    mono = np.sqrt(np.mean(x ** 2, axis=0))
    w = int(0.005 * SR)
    e = np.sqrt(np.mean(mono[:(len(mono) // w) * w].reshape(-1, w) ** 2, axis=1)) + 1e-9
    prev = np.convolve(e, np.ones(10) / 10, mode="full")[:len(e)]
    step = 20 * np.log10(e[10:] / prev[9:-1])
    say(f"- {name}: peak to loudness ratio {m['TP'] - m['I']:.1f} dB; largest onset step (5 ms vs the 50 ms before) "
        f"{step.max():.1f} dB, 99th percentile {np.percentile(step, 99):.1f} dB {gate(step.max() < 15.0, name + ' soft transients')}")


def silence_report(name: str, x: np.ndarray, frames: np.ndarray, t_from: float, t_to: float) -> None:
    sel = (frames[:, 0] >= t_from) & (frames[:, 0] <= t_to)
    m, s = frames[sel, 1], frames[sel, 2]
    sec = x[:, int(t_from * SR):int(t_to * SR)]
    k = sec.shape[1] // SR
    rms = 20 * np.log10(np.sqrt(np.mean(sec[:, :k * SR].reshape(2, k, SR) ** 2, axis=(0, 2))) + 1e-12)
    s_ok = s[frames[sel, 0] >= t_from + 3.0] if t_from < 3.0 else s
    say(f"- {name} {t_from:.1f}-{t_to:.1f} s: momentary loudness min {m.min():.1f} / max {m.max():.1f} LUFS, "
        f"short-term min {s_ok.min():.1f} / max {s_ok.max():.1f} LUFS, quietest 1 s RMS {rms.min():.1f} dBFS "
        f"{gate(m.min() > -40.0 and rms.min() > -50.0, name + ' no silent section')}")


def kit_chain_ratio(scratch: Path, levels: dict) -> None:
    """Re-run the preview stems through the video kit's own ffmpeg ducking chain."""
    bed = C.read_wav24(OUT / "zts-bed.wav")
    start = round(16 * 4 * C.BED_N / (C.BED_BARS * 4))
    n = int(C.PREVIEW_S * SR)
    speech = C.speech_like(C.PREVIEW_S)
    # A TTS cue is mono. ffmpeg upmixes mono to stereo at -3 dB per side, so a mono cue at
    # -18 LUFS arrives as the same -18 LUFS stereo voice the numpy preview uses.
    speech *= C.undb(-20.0 - C.loudness(speech[None, :])["I"])
    scratch.mkdir(parents=True, exist_ok=True)
    sp, bd = scratch / "kit-speech.wav", scratch / "kit-bed.wav"
    C.write_wav24(sp, speech[None, :])
    C.write_wav24(bd, bed[:, start:start + n])
    graph = (f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=duration={C.PREVIEW_S:.3f},"
             "asetpts=N/SR/TB,volume=-21dB[bed];"
             "[0:a]aformat=channel_layouts=stereo,asplit=2[voice][key];"
             "[bed][key]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=600[ducked]")
    C.write_wav24(bd, bed[:, start:start + n])
    for level in (-20.0, -26.0):  # edge-tts AndrewNeural -5 % measured -19.9 LUFS; a quieter engine reads ~-26
        C.write_wav24(sp, speech[None, :] * C.undb(level + 20.0))
        out = {}
        for label, pick in (("voice", "[voice]"), ("ducked", "[ducked]")):
            target = scratch / f"kit-{label}.wav"
            g = graph + (";[ducked]anullsink" if label == "voice" else ";[voice]anullsink")
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(sp), "-i", str(bd),
                            "-filter_complex", g, "-map", pick, "-c:a", "pcm_f32le", str(target)], check=True)
            out[label] = ebur128_file(target)[0]["I"]
        say(f"- kit's own ffmpeg chain (volume=-21dB, sidechaincompress 0.02/8/40/600), raw voice {level:.0f} LUFS mono: "
            f"voice {out['voice']:.1f} LUFS, ducked bed {out['ducked']:.1f} LUFS, ratio {out['voice'] - out['ducked']:.1f} LU")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    levels = json.loads((OUT / "levels.json").read_text())
    files = {"bed": OUT / "zts-bed.wav", "trailer": OUT / "zts-trailer.wav", "preview": OUT / "preview-ducked.wav"}
    data = {}
    say("files")
    say("| file | codec | rate | ch | bits | frames | duration | sha256 matches levels.json |")
    say("|---|---|---:|---:|---:|---:|---:|---|")
    for key, path in files.items():
        x = C.read_wav24(path)
        data[key] = x
        info = ffprobe(path)
        same = C.sha256(path) == levels["sha256"].get(path.name)
        say(f"| {path.name} | {info['codec']} | {info['rate']} | {info['channels']} | {info['bits']} | {x.shape[1]} | "
            f"{x.shape[1] / SR:.3f} s | {'yes' if same else 'NO'} |")
        gate(info["rate"] == SR and info["channels"] == 2 and info["codec"] == "pcm_s24le", f"{key} format")
    gate(data["bed"].shape[1] == C.BED_N, "bed is exactly 48 bars at 92 BPM")
    say(f"bed: 48 bars x 4 beats x 60/92 s = {48 * 4 * 60 / 92:.4f} s = {48 * 4 * 60 / 92 * SR:.2f} samples, "
        f"file has {data['bed'].shape[1]} (rounded to the nearest sample)")

    say("\nloudness (ffmpeg -i f.wav -af ebur128=peak=true -f null -)")
    say("| file | integrated | LRA | true peak | sample peak | clipped samples | DC L / R |")
    say("|---|---:|---:|---:|---:|---:|---|")
    frames = {}
    for key, path in files.items():
        x = data[key]
        m, fr = ebur128_file(path)
        frames[key] = fr
        sp = 20 * np.log10(np.abs(x).max())
        clipped = int(np.sum(np.abs(x) >= 1.0 - 2.0 ** -22))
        dc = [20 * np.log10(abs(float(np.mean(x[c]))) + 1e-12) for c in range(2)]
        say(f"| {path.name} | {m['I']:.1f} LUFS | {m['LRA']:.1f} LU | {m['TP']:.1f} dBTP | {sp:.2f} dBFS | {clipped} | "
            f"{dc[0]:.0f} / {dc[1]:.0f} dBFS |")
        if key != "preview":
            gate(abs(m["I"] - C.TARGET_LUFS) <= 1.0, f"{key} loudness")
            gate(m["TP"] <= -1.0, f"{key} true peak")
        gate(clipped == 0 and max(dc) < -80, f"{key} clipping or DC")
        frames[key + "-summary"] = m
    say("\ntransients")
    for key in ("bed", "trailer"):
        transient_report(key, data[key], frames[key + "-summary"])

    rows = band_table("bed", data["bed"])
    band_table("trailer", data["trailer"])
    speech = C.speech_like(C.PREVIEW_S)
    band_table("speech stand-in used in the preview (for contrast)", np.vstack([speech, speech]))
    say(f"\nmelodic bus 1.5-4 kHz energy after the dip vs before: bed {levels['bed']['dip_db']:+.2f} dB, "
        f"trailer {levels['trailer']['dip_db']:+.2f} dB")
    lighter = rows["speech 1.5-4k"][2] - rows["low-mid"][2]
    say(f"bed: the 1.5-4 kHz band carries {rows['speech 1.5-4k'][0]:.2f} % of the energy, {lighter:+.1f} dB per octave "
        f"against 250-1500 Hz {gate(lighter < -6.0, 'speech band lighter')}")

    loop_joint(data["bed"])

    bed = data["bed"]
    bar = C.BED_N / C.BED_BARS
    quiet = np.concatenate([bed[:, int(44 * bar):], bed[:, :int(4 * bar)]], axis=1)  # bars 45-48 then 1-4
    noise_report("bed", bed, quiet)
    tr = data["trailer"]
    noise_report("trailer", tr, tr[:, int(0.5 * SR):int(4.2 * SR)])  # before the shaker enters at 4.35 s
    alias_selftest()

    say("\nno silent sections")
    silence_report("bed", bed, frames["bed"], 0.5, C.BED_N / SR)
    silence_report("trailer", tr, frames["trailer"], 1.0, 31.0)
    say("\ntrailer ending")
    for a, b in ((30.0, 31.0), (31.0, 32.0), (32.0, 33.0), (33.0, 33.5), (33.5, 34.0)):
        seg = tr[:, int(a * SR):int(b * SR)]
        say(f"- {a:.1f}-{b:.1f} s RMS {20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12):.1f} dBFS, "
            f"peak {20 * np.log10(np.abs(seg).max() + 1e-12):.1f} dBFS")
    e = np.sqrt(np.mean(tr[:, :(tr.shape[1] // 2400) * 2400].reshape(2, -1, 2400) ** 2, axis=(0, 2)))
    last = (np.nonzero(20 * np.log10(e + 1e-12) > -60.0)[0].max() + 1) * 2400 / SR
    say(f"- last 50 ms window above -60 dBFS ends at {last:.2f} s; final samples {tr[0, -1]:.1e} / {tr[1, -1]:.1e} "
        f"{gate(last <= 34.0 and abs(tr[:, -1]).max() == 0.0, 'trailer tail decayed')}")
    tp_ = C.trailer_piece()
    say(f"- events: drums enter at {tp_.pos(12) / SR:.2f} s, the lift lands at {tp_.pos(32) / SR:.2f} s, "
        f"the final Dmaj9 lands at {tp_.pos(44) / SR:.2f} s and releases at {tp_.pos(47) / SR:.2f} s")
    fr = frames["trailer"]
    pts = (1.5, 4.0, 6.5, 8.0, 12.0, 16.0, 19.0, 20.5, 23.0, 26.0, 28.5, 30.5, 32.0)
    say("- loudness shape (momentary, 400 ms): " + ", ".join(
        f"{t:g} s {fr[np.argmin(np.abs(fr[:, 0] - t)), 1]:.1f}" for t in pts) + " LUFS")
    m_at = lambda a, b: float(np.mean(fr[(fr[:, 0] >= a) & (fr[:, 0] < b), 1]))  # noqa: E731
    build, groove, lift = m_at(1.5, 4.3), m_at(9.6, 18.2), m_at(20.4, 27.8)
    say(f"- mean momentary: pad intro 1.5-4.3 s {build:.1f}, groove 9.6-18.2 s {groove:.1f}, lift 20.4-27.8 s {lift:.1f} LUFS "
        f"{gate(build < groove - 4.0 and lift >= groove + 1.0, 'trailer builds then lifts')}")

    say("\npreview (12 s, bed at -21 dB under a speech-like signal, ducked, mix normalised to -16 LUFS)")
    pv = levels["preview"]
    say(f"- excerpt from bed {pv['bed_excerpt_start_s']} s (bar 17, full groove); speech {pv['speech_lufs']:.1f} LUFS, "
        f"ducked bed {pv['music_ducked_lufs']:.1f} LUFS, bed without ducking {pv['music_unducked_lufs']:.1f} LUFS; "
        f"speech to music {pv['speech_to_music_lu']:.1f} LU ducked, {pv['speech_to_music_unducked_lu']:.1f} LU without ducking; "
        f"deepest duck {pv['max_duck_db']} dB")
    scratch = args.scratch or Path(tempfile.mkdtemp(prefix="zts-music-"))
    kit_chain_ratio(scratch, levels)

    say("\nresult: " + ("ALL CHECKS PASS" if not FAILS else "FAILED: " + ", ".join(FAILS)))
    if args.report:
        args.report.write_text("\n".join(LINES) + "\n")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
