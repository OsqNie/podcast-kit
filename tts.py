#!/usr/bin/env python3
"""Turn an episode script (.txt) into one MP3 with the ElevenLabs API.

Usage:  python3 tts.py episodes/2026-10-15.txt
Voice and model come from show.json (voice_id, model_id); the API key comes from .env
(ELEVENLABS_API_KEY). Long scripts are split at paragraph breaks and joined into one MP3.
Standard library only.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
MAX_CHARS = 9500  # eleven_v4 accepts 10,000 characters per request


def load_env(path):
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def chunks(text, limit=MAX_CHARS):
    parts, cur = [], ""
    for para in text.split("\n\n"):
        if cur and len(cur) + len(para) + 2 > limit:
            parts.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        parts.append(cur)
    return parts


def synthesize(text, key, voice, model):
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": model}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs error {e.code}: {e.read().decode(errors='replace')}")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 tts.py <episode.txt>")
    script = pathlib.Path(sys.argv[1]).resolve()
    env = load_env(HERE / ".env")
    show = json.loads((HERE / "show.json").read_text(encoding="utf-8"))
    key = env.get("ELEVENLABS_API_KEY") or sys.exit("ELEVENLABS_API_KEY missing from .env")
    voice = env.get("VOICE_ID") or show.get("voice_id") or sys.exit("Set voice_id in show.json")
    model = env.get("MODEL_ID") or show.get("model_id", "eleven_v4")

    parts = chunks(script.read_text(encoding="utf-8").strip())
    audio = b"".join(synthesize(p, key, voice, model) for p in parts)  # MP3 frames concatenate cleanly
    out = script.with_suffix(".mp3")
    out.write_bytes(audio)
    print(f"OK {out.name}: {len(parts)} request(s), {sum(map(len, parts))} chars, {len(audio) // 1024} KB")


if __name__ == "__main__":
    main()
