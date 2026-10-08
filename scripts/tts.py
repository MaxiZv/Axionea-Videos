#!/usr/bin/env python3
"""Erzeugt den Voiceover mit ElevenLabs inkl. Zeitstempeln je Zeichen.

Nutzung: python3 scripts/tts.py audio/script.txt audio/voiceover
Liest ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID / ELEVENLABS_MODEL aus .env oder der Umgebung.
Schreibt <out>.mp3 und <out>.alignment.json.
"""
import base64, json, os, pathlib, subprocess, sys

root = pathlib.Path(__file__).resolve().parent.parent
env = dict(os.environ)
envfile = root / ".env"
if envfile.exists():
    for line in envfile.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip())

text = pathlib.Path(sys.argv[1]).read_text().strip()
out = pathlib.Path(sys.argv[2])
voice = env.get("ELEVENLABS_VOICE_ID", "Dm2pqleCzqJpMQgIh5nm")
body = json.dumps({"text": text, "model_id": env.get("ELEVENLABS_MODEL", "eleven_v4"), "language_code": "de"})
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"
res = subprocess.run(
    ["curl", "-sS", "--fail-with-body", "-m", "180", "-X", "POST", url,
     "-H", f"xi-api-key: {env['ELEVENLABS_API_KEY']}", "-H", "Content-Type: application/json", "-d", body],
    capture_output=True, text=True)
if res.returncode != 0:
    sys.exit(f"ElevenLabs-Aufruf fehlgeschlagen: {res.stderr.strip()} {res.stdout[:500]}")
data = json.loads(res.stdout)
out.parent.mkdir(parents=True, exist_ok=True)
out.with_suffix(".mp3").write_bytes(base64.b64decode(data["audio_base64"]))
out.with_suffix(".alignment.json").write_text(json.dumps(data.get("alignment"), ensure_ascii=False))
print(f"OK: {out.with_suffix('.mp3')}")
