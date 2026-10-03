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
"""

from __future__ import annotations

import hashlib
import json
import os
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
        "engine": ENGINE,
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
          retries: int = 3) -> Cue:
    """Synthesise once per distinct line.

    The file name carries a digest of the engine, the voice, the rate, the pitch, the
    volume and the words, so editing any one of them always re-synthesises that line and
    an unchanged line is never paid for twice. Naming by segment position alone would
    happily hand back yesterday's audio for today's script, and leaving pitch or volume
    out of the digest would do the same for a re-voiced line.

    A network engine is retried with backoff, because a single 5xx part way through a
    build would otherwise throw away every cue already paid for.
    """
    active = engine or ENGINE
    if active == "minimax":
        engine_key = f"minimax:{MINIMAX_TTS_MODEL}:{MINIMAX_VOICE}"
    elif active == "gmi":
        engine_key = f"gmi:{GMI_MODEL}:{GMI_VOICE}"
    elif active == "fish":
        engine_key = f"fish:{FISH_MODEL}"
    else:
        engine_key = active
    stamp = hashlib.sha256(
        f"{engine_key}|{voice}|{rate}|{pitch}|{volume}|{text}".encode("utf-8")
    ).hexdigest()[:10]
    target = out.with_name(f"{out.stem}-{active}-{stamp}{out.suffix}")
    target.parent.mkdir(parents=True, exist_ok=True)
    marks_file = target.with_suffix(".words.json")

    words = None
    if not target.exists():
        last = None
        for attempt in range(retries):
            try:
                if active == "minimax":
                    _synth_minimax(text, target, voice)
                elif active == "fish":
                    _synth_fish(text, target, voice)
                elif active == "gmi":
                    _synth_gmi(text, target, voice)
                else:
                    words = _synth_edge(text, target, voice, rate, pitch, volume)
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
