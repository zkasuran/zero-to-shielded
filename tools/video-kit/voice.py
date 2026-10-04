"""Narration.

Every cue is synthesised on its own and placed at an absolute offset, so a line
that runs long cannot push the rest of the video out of sync. Timings are derived
from the real audio durations rather than guessed, which is why the build measures
first and lays out second.

Two engines. `edge` is the default and costs nothing. `fish` calls the Fish Audio
API for a better read, which needs API credit on that account and a voice id:

    VOICE_ENGINE=fish FISH_VOICE=<reference_id> python3 build.py projects/x.json

The Fish token is read from FISH_TOKEN or ~/.cache/calle-video/fish.token, never
from a project file, and never printed. Cue files carry a digest of the engine, the
voice and the words, so an edited line is always re-read and an unchanged line is
never paid for twice.

`kokoro` runs Kokoro-82M locally on the CPU (no account, no network once the model is
cached). A project picks it with `"engine": "kokoro"` and a Kokoro voice such as
`"af_heart"`; it writes 24 kHz mono WAV cues and real per-word timings. A project
`lexicon` ({"written": "spoken"}) rewrites only the words sent to the engine, so a name
can be read with inline phonemes (`"Zodl": "[Zodl](/zˈɑdᵊl/)"`) while captions, the SRT
and timing.json keep the written line.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import shutil as _sh
EDGE = Path(os.environ.get("EDGE_TTS_BIN") or _sh.which("edge-tts") or "edge-tts")
VOICE = "en-US-AndrewNeural"
RATE = "+3%"

ENGINE = os.environ.get("VOICE_ENGINE", "edge")
FISH_ENDPOINT = "https://api.fish.audio/v1/tts"
FISH_TOKEN_FILE = Path.home() / ".cache" / "calle-video" / "fish.token"
FISH_MODEL = os.environ.get("FISH_MODEL", "s2.1-pro-free")
FISH_VOICE = os.environ.get("FISH_VOICE", "")

# GMI Cloud Inference Engine (MiniMax Speech 2.8 and friends). Async job queue:
# submit, poll, then download the audio URL. Token from GMI_TOKEN or the cache file.
GMI_BASE = "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey/requests"
GMI_TOKEN_FILE = Path.home() / ".cache" / "calle-video" / "gmi.token"
GMI_MODEL = os.environ.get("GMI_TTS_MODEL", "minimax-tts-speech-2.8-hd")
GMI_VOICE = os.environ.get("GMI_VOICE", "English_expressive_narrator")

# MiniMax T2A (Max plan, house default for submission builds). OpenAI-adjacent host, Bearer key from
# ~/Downloads/hackathon-hq/.minimax.env. Returns data.audio as a HEX string of an mp3.
MINIMAX_BASE = os.environ.get("MINIMAX_BASE", "https://api.minimax.io")
MINIMAX_ENV_FILE = Path(os.environ.get("MINIMAX_ENV_FILE", ".minimax.env"))
MINIMAX_TTS_MODEL = os.environ.get("MINIMAX_TTS_MODEL", "speech-02-hd")
MINIMAX_VOICE = os.environ.get("MINIMAX_VOICE", "English_expressive_narrator")

# Kokoro-82M, local. One pipeline per language per process, loaded on first use, because
# loading the model costs seconds and a build of cached cues should never pay for it.
KOKORO_REPO = os.environ.get("KOKORO_REPO", "hexgrad/Kokoro-82M")
KOKORO_MODEL = KOKORO_REPO.rsplit("/", 1)[-1]
KOKORO_VOICE = os.environ.get("KOKORO_VOICE", "af_heart")
KOKORO_SAMPLE_RATE = 24000
KOKORO_GAP = 0.12
"""Seconds of silence between the chunks Kokoro splits a long line into."""
KOKORO_FLOOR_DB = -50.0
KOKORO_KEEP = 0.05
"""Silence under the floor is trimmed from both ends of the read, keeping this much."""
_KOKORO_PIPELINES: dict[str, object] = {}

# Inline phoneme markup, `[word](/phonemes/)`. Only Kokoro reads it; every other engine is
# handed the bare word so a lexicon written for Kokoro cannot be read out as punctuation.
_PHONEME_LINK = re.compile(r"\[([^\]]+)\]\(/[^)]*/\)")


@dataclass
class Cue:
    text: str
    path: Path
    seconds: float
    start: float = 0.0
    words: list = None
    """Per-word (start, end, word) offsets inside this cue, when the engine reports them.

    edge-tts emits WordBoundary events, so a cue read by edge carries real word times and
    the karaoke caption style can track the read. Any engine that does not report them
    leaves this None and the caption layer falls back to the plain band.
    """


def speaker_settings(project: dict, entry) -> dict:
    """Resolve one cue's voice settings: project default, named speaker, then per-cue keys.

    A project sets one voice for the whole video, names a roster under `voices`, or overrides
    any field on a single cue. Later wins, so a cue can borrow a speaker and still change its
    rate. Every field here is part of the cache digest, or an edited voice would silently
    return yesterday's audio.
    """
    settings = {
        "voice": project.get("voice", VOICE),
        "rate": project.get("rate", RATE),
        "pitch": project.get("pitch", "+0Hz"),
        "volume": project.get("volume", "+0%"),
        # the project names its engine; VOICE_ENGINE (or edge) is only the default
        "engine": project.get("engine") or ENGINE,
    }
    if isinstance(entry, dict):
        named = entry.get("speaker")
        if named:
            roster = project.get("voices", {})
            if named not in roster:
                raise RuntimeError(f"cue names speaker {named!r}, which is not in the project's voices")
            settings.update(roster[named])
        for key in ("voice", "rate", "pitch", "volume", "engine"):
            if key in entry:
                settings[key] = entry[key]
    return settings


@functools.lru_cache(maxsize=32)
def _lexicon_pattern(keys: tuple[str, ...]) -> re.Pattern:
    # Longest first, so a phrase entry wins over a single word inside it. The lookarounds
    # make it whole-word without \b, which would refuse a key that starts or ends with
    # punctuation. One pass, so a replacement is never itself rewritten.
    ordered = sorted(keys, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(key) for key in ordered) + r")(?!\w)")


def spoken(text: str, lexicon: dict | None) -> str:
    """The words the engine reads: the written line with the project lexicon applied.

    Whole word or phrase, case sensitive, longest entry first. Only the engine sees the
    result. Captions, the SRT and timing.json keep the written line, so a pronunciation
    fix can never leak phoneme markup on screen.
    """
    if not lexicon:
        return text
    keys = tuple(key for key in lexicon if key)
    if not keys:
        return text
    return _lexicon_pattern(keys).sub(lambda match: str(lexicon[match.group(0)]), text)


def _percent(value, what: str) -> float:
    """An edge-style percentage ("-5%", "+3%") as a number, or a bare number as given."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "+0%").strip()
    match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)%", text)
    if not match:
        raise RuntimeError(f"kokoro: cannot read {what} {value!r}, want a percentage like -5%")
    return float(match.group(1))


def kokoro_speed(rate) -> float:
    """The kit's rate string as a Kokoro speed: "-5%" is 0.95, "+3%" is 1.03.

    A bare number is taken as the speed itself, for a project written for Kokoro.
    """
    if isinstance(rate, (int, float)):
        return float(rate)
    return max(0.5, min(2.0, 1.0 + _percent(rate, "rate") / 100.0))


def _kokoro_pipeline(lang: str):
    pipeline = _KOKORO_PIPELINES.get(lang)
    if pipeline is None:
        import warnings

        with warnings.catch_warnings():
            # torch warns about dropout and weight_norm on every load; neither is ours
            warnings.simplefilter("ignore")
            try:
                from huggingface_hub.utils import logging as hf_logging

                hf_logging.set_verbosity_error()
            except Exception:  # noqa: BLE001 - a quieter log is a nicety, not a requirement
                pass
            from kokoro import KPipeline

            pipeline = KPipeline(lang_code=lang, repo_id=KOKORO_REPO)
        _KOKORO_PIPELINES[lang] = pipeline
    return pipeline


def _voiced_span(samples, keep: int) -> tuple[int, int]:
    """First and last sample above the floor, widened by `keep` samples each side."""
    import numpy as np

    loud = np.flatnonzero(np.abs(samples) > 10 ** (KOKORO_FLOOR_DB / 20))
    if not loud.size:
        return 0, 0
    return max(0, int(loud[0]) - keep), min(samples.size, int(loud[-1]) + 1 + keep)


def _kokoro_words(tokens) -> list[tuple[float, float, str]]:
    """Tokens joined back into written words, with chunk-relative times.

    Kokoro splits punctuation into its own tokens and marks the space after each one, so
    tokens are glued until a token carries whitespace: "Zodl" + "," reads "Zodl,". A word
    with no timed token is skipped, and so is a group that is only punctuation.
    """
    words: list[tuple[float, float, str]] = []
    label, start, end = "", None, None
    for token in tokens:
        label += token.text or ""
        if token.start_ts is not None and token.end_ts is not None:
            start = float(token.start_ts) if start is None else start
            end = float(token.end_ts)
        if token.whitespace:
            if start is not None and any(ch.isalnum() for ch in label):
                words.append((start, max(start, end), label.strip()))
            label, start, end = "", None, None
    if start is not None and any(ch.isalnum() for ch in label):
        words.append((start, max(start, end), label.strip()))
    return words


def _synth_kokoro(text: str, out: Path, voice: str, rate: str,
                  pitch: str = "+0Hz", volume: str = "+0%") -> list:
    """Synthesise with Kokoro-82M on this machine and return per-word timings.

    Kokoro yields one result per chunk of a long line. Each chunk is trimmed to its voiced
    span (keeping 0.05 s) and the chunks are joined with a 0.12 s breath, so the read has a
    natural pause where the model split it and no dead air at either end. Word times are
    moved by the same offsets, so they stay on the audio that is actually written. Kokoro
    has no pitch control: pitch is still part of the cue digest but does not change the read.
    """
    import numpy as np
    import soundfile

    if not voice or voice.endswith("Neural"):
        # an edge voice left as the project default is not a Kokoro voice
        voice = KOKORO_VOICE
    lang = voice[0] if len(voice) > 2 and voice[2] == "_" else "a"
    pipeline = _kokoro_pipeline(lang)
    gain = max(0.0, 1.0 + _percent(volume, "volume") / 100.0)
    rate_hz = KOKORO_SAMPLE_RATE
    keep = round(KOKORO_KEEP * rate_hz)
    gap = np.zeros(round(KOKORO_GAP * rate_hz), dtype=np.float32)

    pieces: list = []
    words: list[tuple[float, float, str]] = []
    written = 0
    for result in pipeline(text, voice=voice, speed=kokoro_speed(rate)):
        audio = getattr(result, "audio", None)
        if audio is None:
            continue
        samples = np.asarray(audio.detach().cpu().numpy() if hasattr(audio, "detach") else audio,
                             dtype=np.float32).reshape(-1)
        low, high = _voiced_span(samples, keep)
        if high <= low:
            continue
        if pieces:
            pieces.append(gap)
            written += gap.size
        # chunk time zero lands here in the written file, after the trim and the gaps
        origin = (written - low) / rate_hz
        chunk_end = (written + high - low) / rate_hz
        for start, end, word in _kokoro_words(getattr(result, "tokens", None) or []):
            start = min(max(origin + start, written / rate_hz), chunk_end)
            end = min(max(origin + end, start), chunk_end)
            words.append((round(start, 3), round(end, 3), word))
        pieces.append(samples[low:high])
        written += high - low
    if not pieces:
        raise RuntimeError(f"kokoro returned no audio for {text[:48]!r}")
    signal = np.concatenate(pieces) * gain
    np.clip(signal, -1.0, 1.0, out=signal)
    # written aside then moved, so an interrupted read never leaves a cue the cache trusts
    partial = out.with_name(out.name + ".partial.wav")
    soundfile.write(str(partial), signal, rate_hz, subtype="PCM_16")
    os.replace(partial, out)
    return words


def probe_seconds(path: Path) -> float:
    done = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(done.stdout.strip())


def _fish_token() -> str:
    token = os.environ.get("FISH_TOKEN", "")
    if not token and FISH_TOKEN_FILE.exists():
        token = FISH_TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError(
            f"no Fish Audio token. Put it in {FISH_TOKEN_FILE} with mode 0600 or set FISH_TOKEN."
        )
    return token


def _synth_fish(text: str, out: Path, voice: str) -> None:
    # The `voice` param carries the edge voice by default (names end in "Neural"),
    # which is not a Fish reference. Use an explicit Fish voice id from FISH_VOICE
    # or a non-edge project voice; otherwise send none and let s2.1-pro-free use
    # its default voice.
    reference = FISH_VOICE or (voice if voice and not voice.endswith("Neural") else "")
    payload = {"text": text, "format": "mp3", "mp3_bitrate": 128}
    if reference:
        payload["reference_id"] = reference
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        FISH_ENDPOINT,
        data=body,
        headers={
            "authorization": f"Bearer {_fish_token()}",
            "content-type": "application/json",
            "model": FISH_MODEL,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            audio = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        try:
            detail = json.loads(detail).get("message", detail)
        except json.JSONDecodeError:
            pass
        raise RuntimeError(f"Fish Audio returned {error.code}: {detail}") from None
    if len(audio) < 1024:
        raise RuntimeError(f"Fish Audio returned {len(audio)} bytes, which is not audio")
    out.write_bytes(audio)


def _gmi_token() -> str:
    token = os.environ.get("GMI_TOKEN", "")
    if not token and GMI_TOKEN_FILE.exists():
        token = GMI_TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError(f"no GMI token. Put it in {GMI_TOKEN_FILE} (mode 600) or set GMI_TOKEN.")
    return token


def _gmi_call(url: str, data: dict | None = None, method: str = "GET") -> dict:
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(
        url, data=body, method=method,
        headers={"Authorization": f"Bearer {_gmi_token()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def _synth_gmi(text: str, out: Path, voice: str) -> None:
    """MiniMax Speech on the GMI Inference Engine: submit, poll, download."""
    reference = GMI_VOICE or (voice if voice and not voice.endswith("Neural") else "English_expressive_narrator")
    payload = {
        "model": GMI_MODEL,
        "payload": {
            "text": text, "voice_id": reference, "speed": "1", "vol": "1", "pitch": "0",
            "emotion": "auto", "language_boost": "auto", "format": "mp3",
            "audio_sample_rate": "32000", "bitrate": "128000", "channel": "1",
        },
    }
    try:
        submitted = _gmi_call(GMI_BASE, payload, "POST")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GMI submit {error.code}: {error.read().decode('utf-8','replace')[:200]}") from None
    rid = submitted.get("request_id") or submitted.get("id")
    if not rid:
        raise RuntimeError(f"GMI submit had no request_id: {json.dumps(submitted)[:200]}")
    audio_url = None
    for _ in range(75):
        time.sleep(4)
        state = _gmi_call(f"{GMI_BASE}/{rid}")
        status = state.get("status")
        if status == "success":
            audio_url = (state.get("outcome") or {}).get("audio_url")
            break
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"GMI job {status}: {json.dumps(state)[:200]}")
    if not audio_url:
        raise RuntimeError("GMI job did not reach success in time")
    with urllib.request.urlopen(audio_url, timeout=90) as response:
        audio = response.read()
    if len(audio) < 1024:
        raise RuntimeError(f"GMI returned {len(audio)} bytes, which is not audio")
    out.write_bytes(audio)


def _minimax_key() -> str:
    key = os.environ.get("MINIMAX_API_KEY", "")
    if not key and MINIMAX_ENV_FILE.exists():
        for line in MINIMAX_ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("MINIMAX_API_KEY="):
                key = line.split("=", 1)[1].strip()
                break
    if not key:
        raise RuntimeError(f"no MiniMax key. Set MINIMAX_API_KEY or put it in {MINIMAX_ENV_FILE} (mode 600).")
    return key


def _synth_minimax(text: str, out: Path, voice: str) -> None:
    """MiniMax T2A: one request, decode the hex-encoded mp3 in data.audio."""
    voice_id = MINIMAX_VOICE or (voice if voice and not voice.endswith("Neural") else "English_expressive_narrator")
    payload = {
        "model": MINIMAX_TTS_MODEL,
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice_id, "speed": 1.0, "vol": 1.0, "pitch": 0},
        "audio_setting": {"format": "mp3", "sample_rate": 32000, "bitrate": 128000, "channel": 1},
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{MINIMAX_BASE}/v1/t2a_v2",
        data=body,
        headers={"Authorization": f"Bearer {_minimax_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"MiniMax T2A {error.code}: {error.read().decode('utf-8', 'replace')[:200]}") from None
    base = result.get("base_resp") or {}
    if base.get("status_code") not in (0, None):
        raise RuntimeError(f"MiniMax T2A status {base.get('status_code')}: {base.get('status_msg')}")
    audio_hex = (result.get("data") or {}).get("audio")
    if not audio_hex:
        raise RuntimeError(f"MiniMax T2A returned no audio: {json.dumps(result)[:200]}")
    audio = bytes.fromhex(audio_hex)
    if len(audio) < 1024:
        raise RuntimeError(f"MiniMax T2A returned {len(audio)} bytes, which is not audio")
    out.write_bytes(audio)


def _synth_edge(text: str, out: Path, voice: str, rate: str,
                pitch: str = "+0Hz", volume: str = "+0%") -> list | None:
    """Synthesise with edge-tts and capture word timings when the library is importable.

    The CLI cannot report WordBoundary events, so the Python API is tried first and the
    CLI is the fallback. Both produce the same audio, the API just also hands back the
    per-word offsets the karaoke caption style needs.
    """
    words = _synth_edge_api(text, out, voice, rate, pitch, volume)
    if words is not None:
        return words
    if not EDGE.exists():
        raise RuntimeError(f"edge-tts not found at {EDGE}")
    command = [str(EDGE), "--voice", voice, f"--rate={rate}", "--text", text, "--write-media", str(out)]
    # The equals form matters: a negative value like -4Hz passed as a separate argument is
    # read by argparse as a flag, so `--pitch -4Hz` fails with a usage error.
    if pitch and pitch != "+0Hz":
        command += [f"--pitch={pitch}"]
    if volume and volume != "+0%":
        command += [f"--volume={volume}"]
    done = subprocess.run(command, capture_output=True, text=True, check=False)
    if done.returncode != 0 or not out.exists():
        raise RuntimeError(f"edge-tts failed for {out.name}: {done.stderr.strip()[:200]}")
    return None


def _synth_edge_api(text: str, out: Path, voice: str, rate: str, pitch: str, volume: str):
    """The Python API path, which is the only way to get per-word timings.

    edge-tts reports WordBoundary events over its streaming API, but only when it is asked
    for them: the library defaults to `boundary='SentenceBoundary'` and one cue per
    sentence is no use to a karaoke caption. The CLI cannot pass them on either
    (`--write-subtitles` is sentence level too), so this needs the library. It lives in the
    venv that owns the edge-tts binary rather than in this interpreter, so the work runs as
    a short script under that venv's python. Returns the word list, or None when that path
    fails, in which case the caller falls back to the CLI and captions stay on the band.
    """
    script = (
        "import asyncio, json, sys, edge_tts\n"
        "text, voice, rate, pitch, volume, media, marks = sys.argv[1:8]\n"
        "async def run():\n"
        "    kw = {'rate': rate, 'boundary': 'WordBoundary'}\n"
        "    if pitch != '+0Hz': kw['pitch'] = pitch\n"
        "    if volume != '+0%': kw['volume'] = volume\n"
        "    c = edge_tts.Communicate(text, voice, **kw)\n"
        "    audio = bytearray(); words = []\n"
        "    async for chunk in c.stream():\n"
        "        if chunk['type'] == 'audio': audio.extend(chunk['data'])\n"
        "        elif chunk['type'] == 'WordBoundary':\n"
        "            s = chunk['offset'] / 1e7\n"
        "            words.append((s, s + chunk['duration'] / 1e7, chunk['text']))\n"
        "    open(media, 'wb').write(bytes(audio))\n"
        "    open(marks, 'w').write(json.dumps(words))\n"
        "asyncio.run(run())\n"
    )
    marks_path = out.with_suffix(".words.json")
    python = EDGE.with_name("python")
    if not python.exists():
        import sys as _sys
        python = Path(_sys.executable)
    done = subprocess.run(
        [str(python), "-c", script, text, voice, rate, pitch, volume, str(out), str(marks_path)],
        capture_output=True, text=True, check=False, timeout=120,
    )
    if done.returncode != 0 or not out.exists() or out.stat().st_size < 1024:
        return None
    try:
        return [tuple(w) for w in json.loads(marks_path.read_text(encoding="utf-8"))]
    except (OSError, ValueError):
        return None



def synth(text: str, out: Path, voice: str = VOICE, rate: str = RATE,
          pitch: str = "+0Hz", volume: str = "+0%", engine: str | None = None,
          retries: int = 3, say: str | None = None) -> Cue:
    """Synthesise once per distinct line.

    The file name carries a digest of the engine, the voice, the rate, the pitch, the
    volume and the words, so editing any one of them always re-synthesises that line and
    an unchanged line is never paid for twice. Naming by segment position alone would
    happily hand back yesterday's audio for today's script, and leaving pitch or volume
    out of the digest would do the same for a re-voiced line.

    `text` is the written line and is what the Cue carries into captions, the SRT and
    timing.json. `say` is what the engine reads (the line after the project lexicon), and
    it is what the digest covers, because it is what the audio is made of. With no `say`
    the two are the same line and the digest is unchanged from before `say` existed.

    A network engine is retried with backoff, because a single 5xx part way through a
    build would otherwise throw away every cue already paid for.
    """
    active = engine or ENGINE
    words_out = text if say is None else say
    if active != "kokoro":
        words_out = _PHONEME_LINK.sub(r"\1", words_out)
    if active == "minimax":
        engine_key = f"minimax:{MINIMAX_TTS_MODEL}:{MINIMAX_VOICE}"
    elif active == "gmi":
        engine_key = f"gmi:{GMI_MODEL}:{GMI_VOICE}"
    elif active == "fish":
        engine_key = f"fish:{FISH_MODEL}"
    elif active == "kokoro":
        engine_key = f"kokoro:{KOKORO_MODEL}"
    else:
        engine_key = active
    stamp = hashlib.sha256(
        f"{engine_key}|{voice}|{rate}|{pitch}|{volume}|{words_out}".encode("utf-8")
    ).hexdigest()[:10]
    # Kokoro hands back raw samples, so its cues are written as WAV rather than re-encoded
    suffix = ".wav" if active == "kokoro" else out.suffix
    target = out.with_name(f"{out.stem}-{active}-{stamp}{suffix}")
    target.parent.mkdir(parents=True, exist_ok=True)
    marks_file = target.with_suffix(".words.json")

    words = None
    if not target.exists():
        last = None
        for attempt in range(retries):
            try:
                if active == "minimax":
                    _synth_minimax(words_out, target, voice)
                elif active == "fish":
                    _synth_fish(words_out, target, voice)
                elif active == "gmi":
                    _synth_gmi(words_out, target, voice)
                elif active == "kokoro":
                    words = _synth_kokoro(words_out, target, voice, rate, pitch, volume)
                else:
                    words = _synth_edge(words_out, target, voice, rate, pitch, volume)
                break
            except Exception as error:  # noqa: BLE001 - retried below, re-raised on the last
                last = error
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"TTS failed for cue {text[:48]!r} after {retries} tries via {active}: {error}"
                    ) from None
                time.sleep(2 ** attempt)
        if words:
            marks_file.write_text(json.dumps(words), encoding="utf-8")
    elif marks_file.exists():
        words = json.loads(marks_file.read_text(encoding="utf-8"))

    return Cue(text=text, path=target, seconds=probe_seconds(target), words=words)


def silence(seconds: float, out: Path) -> Cue:
    """A measured pause, so a script can breathe without a hand-edited gap.

    Rendered as a real silent file rather than a gap in the layout, so it goes through the
    same measure-then-place path as every spoken cue and cannot drift.
    """
    target = out.with_name(f"{out.stem}-pause-{seconds:.2f}{out.suffix}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        done = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi",
             "-i", "anullsrc=r=48000:cl=mono", "-t", f"{seconds:.3f}", str(target)],
            capture_output=True, text=True, check=False,
        )
        if done.returncode != 0:
            raise RuntimeError(f"pause render failed: {done.stderr.strip()[:200]}")
    return Cue(text="", path=target, seconds=probe_seconds(target))


def track(cues: list[Cue], total: float, out: Path, music: Path | None = None) -> Path:
    """
    One silent bed plus every cue delayed to its start, normalised to -16 LUFS.

    With a music path, the bed loops under the narration, fades in and out, and is
    sidechain ducked whenever the voice speaks. The voice channel is never
    attenuated: the music moves out of its way instead.
    """
    if not cues:
        raise RuntimeError("no narration cues")
    command = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    filters = []
    labels = ["[0:a]"]
    for index, cue in enumerate(cues, start=1):
        command += ["-i", str(cue.path)]
        delay = max(0, round(cue.start * 1000))
        filters.append(f"[{index}:a]aresample=48000,adelay={delay}|{delay}[a{index}]")
        labels.append(f"[a{index}]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first[speech]")

    if music is None:
        filters.append("[speech]loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.79:level=disabled[out]")
    else:
        index = len(cues) + 1
        command += ["-stream_loop", "-1", "-i", str(music)]
        fade_out = max(total - 3.0, 0.5)
        filters.append(
            f"[{index}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"atrim=duration={total:.3f},asetpts=N/SR/TB,volume=-21dB,"
            f"afade=t=in:d=1.5,afade=t=out:st={fade_out:.3f}:d=3.0[bed]"
        )
        filters.append("[speech]asplit=2[voice][key]")
        filters.append("[bed][key]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=600[ducked]")
        filters.append("[voice][ducked]amix=inputs=2:normalize=0:duration=first[mixed]")
        filters.append("[mixed]alimiter=limit=0.94,loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.79:level=disabled[out]")

    command += [
        "-filter_complex", ";".join(filters),
        "-map", "[out]", "-ac", "2", "-ar", "48000", str(out),
    ]
    done = subprocess.run(command, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"narration mix failed: {done.stderr.strip()[:400]}")
    return out
