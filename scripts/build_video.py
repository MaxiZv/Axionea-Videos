#!/usr/bin/env python3
"""Bereitet ein Video-Projekt für HyperFrames vor.

- kopiert videos/_shared nach videos/<v>/shared
- erzeugt videos/<v>/timing.js (Szenen, Sätze, Wörter, Untertitel-Gruppen, Beats)
- mischt den Soundtrack (Stimme -14 LUFS, Musik -36 LUFS, Effekte, Mix -12 LUFS) nach
  videos/<v>/shared/soundtrack.wav

Nutzung: python3 scripts/build_video.py 01-axionea-imagefilm
"""
import json, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SFX = ROOT / "assets" / "sfx"
MUSIC = ROOT / "assets" / "music" / "royalty-free-music.mp3"
OUTRO_TAIL = 3.2  # Sekunden nach der letzten Silbe

CONFIG = {
    "01-axionea-imagefilm": {
        "keys": ["sensiblen", "Daten", "Routine", "Stunden", "Wissen", "Axionea", "KI-Agentur",
                 "Deutschland", "Cloud", "lokal", "eigenen", "Hardware", "Assistenten",
                 "Automatisierungen", "Wissensdatenbanken", "Software", "jede", "Branche",
                 "rechnet", "messen", "letzte", "Wort", "Sicherheit", "KI"],
        "dark_scenes": [1, 8],
        "music_start_scene": 2,
        # (Szene, Offset ab Szenenstart oder Wort, Effekt, Pegel dB)
        "cues": [
            ("t", 0.0, "boom", -6), ("t", 0.5, "pulse", -8), ("t", 2.9, "click", -10),
            ("t", 3.5, "click", -12), ("t", 4.1, "click", -12),
            ("scene", 2, -0.25, "swoosh-soft", -10),
            ("word", "Anfragen", 0.0, "ping", -12), ("word", "Dokumente", 0.0, "ping", -13),
            ("word", "Angebote", 0.0, "ping", -13), ("word", "wertvolles", 0.4, "whoosh", -16),
            ("scene", 3, -0.25, "swoosh-soft", -10), ("scene", 3, 1.0, "lock", -8),
            ("scene", 4, -1.3, "riser", -16), ("scene", 4, 0.0, "dock", -8),
            ("word", "Cloud,", 0.0, "whoosh", -12), ("word", "lokal,", 0.0, "dock", -10),
            ("sent", 4, 2, 0.5, "tick", -10), ("sent", 4, 2, 0.9, "tick", -10),
            ("sent", 4, 2, 1.3, "tick", -10), ("sent", 4, 2, 2.0, "hum", -12),
            ("scene", 5, -0.25, "swoosh-soft", -10),
            ("sent", 5, 0, 1.6, "pop", -10), ("sent", 5, 0, 2.2, "typing", -16),
            ("sent", 5, 1, 0.0, "pop", -10), ("sent", 5, 2, 0.0, "pop", -10),
            ("sent", 5, 3, 0.0, "pop", -10), ("sent", 5, 3, 2.0, "swoosh-soft", -10),
            ("scene", 6, -0.25, "swoosh-soft", -10),
            ("word", "Steuerkanzlei,", 0.0, "pop", -12), ("word", "Patentanwalt,", 0.0, "pop", -12),
            ("word", "Ingenieurbüro", 0.0, "pop", -12), ("word", "Finanzmakler:", 0.0, "pop", -12),
            ("word", "jede", 0.0, "whoosh", -12),
            ("scene", 7, -0.25, "swoosh-soft", -10), ("word", "starten", 0.0, "tick", -10),
            ("word", "messen", 0.0, "tick", -10), ("word", "bleiben", 0.0, "tick", -10),
            ("word", "letzte", 0.0, "click", -8), ("word", "letzte", 0.15, "success", -10),
            ("scene", 8, -1.2, "riser", -14), ("scene", 8, 0.55, "dock", -6),
            ("scene", 8, 2.6, "chime", -10),
        ],
    },
    "02-axionea-core-kanzlei": {
        "keys": ["Wissen", "Routine", "Posteingang", "Termine", "Mandantenanfragen", "Mandantendaten",
                 "Axionea", "Core.", "Fünf", "Bausteine", "System.", "Deutschland.", "DATEV",
                 "Automatisierungsplattform", "Wissensbasis", "KI-Modelle", "Verbrauch.",
                 "Chatfenster", "Erstentwurf", "prüft", "frei.", "Check", "messen", "Sicherheitsanforderungen",
                 "Cloud.", "Kanzlei."],
        "dark_scenes": [1, 7],
        "music_start_scene": 2,
        "cues": [
            ("t", 0.0, "boom", -8), ("t", 0.3, "pulse", -8), ("word", "Aber", 0.2, "whoosh", -12),
            ("scene", 2, -0.25, "swoosh-soft", -10),
            ("word", "Posteingang,", 0.0, "ping", -12), ("word", "Termine,", 0.0, "ping", -13),
            ("word", "Mandantenanfragen,", 0.0, "ping", -13), ("word", "dieselben", 0.0, "tick", -12),
            ("word", "keine", 0.0, "lock", -8),
            ("scene", 3, -1.2, "riser", -16), ("scene", 3, 0.0, "dock", -8),
            ("word", "Erstens:", 0.0, "dock", -8), ("word", "Zweitens:", 0.0, "dock", -8),
            ("word", "Drittens:", 0.0, "dock", -8), ("word", "Viertens:", 0.0, "dock", -8),
            ("word", "Fünftens:", 0.0, "dock", -8),
            ("scene", 5, -0.25, "swoosh-soft", -10), ("word", "Erstentwurf,", -0.6, "typing", -16),
            ("word", "gibt", 0.0, "click", -8), ("word", "gibt", 0.15, "success", -10),
            ("scene", 6, -0.25, "swoosh-soft", -10), ("word", "Check,", 0.0, "tick", -10),
            ("word", "setzen", 0.0, "tick", -10), ("word", "messen", 0.0, "tick", -10),
            ("word", "Kanzleien", 0.0, "whoosh", -12),
            ("scene", 7, -1.2, "riser", -14), ("word", "Axionea.", 0.0, "dock", -6),
            ("word", "Axionea.", 1.6, "chime", -10),
        ],
    },
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Fehler: {' '.join(cmd[:6])} …\n{r.stderr[-2000:]}")
    return r


def caption_groups(words, keys):
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        txt = " ".join(x["text"] for x in cur)
        end_sent = re.search(r"[.!?]$", w["text"]) is not None
        soft = re.search(r"[,:]$", w["text"]) is not None
        if (nxt is None or end_sent or len(cur) >= 4 or len(txt) >= 24 or (soft and len(cur) >= 2)
                or (nxt and nxt["para"] != w["para"])):
            groups.append(cur)
            cur = []
    out = []
    for gi, g in enumerate(groups):
        start = g[0]["start"]
        nxt_start = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else g[-1]["end"] + 0.6
        end = min(nxt_start - 0.1, g[-1]["end"] + 0.6)
        out.append({"start": round(start - 0.05, 3), "end": round(end, 3), "para": g[0]["para"],
                    "words": [{"t": x["text"], "s": x["start"],
                               "k": x["text"].strip(".,:;!?") in [k.strip(".,:;!?") for k in keys]} for x in g]})
    return out


def main(v):
    cfg = CONFIG[v]
    vdir = ROOT / "videos" / v
    tim = json.loads((vdir / "audio" / "timing.json").read_text())
    shared = vdir / "shared"
    if shared.exists():
        shutil.rmtree(shared)
    shutil.copytree(ROOT / "videos" / "_shared", shared)

    voice_end = tim["scenes"][-1]["end"]
    total = round(voice_end + OUTRO_TAIL, 2)
    scenes = tim["scenes"]
    # Szenengrenzen: jede Szene beginnt in der Pause vor ihrem ersten Wort
    starts = [0.0] + [round((scenes[i - 1]["end"] + scenes[i]["start"]) / 2, 3) for i in range(1, len(scenes))]
    ends = starts[1:] + [total]

    def word_t(text, occurrence=0):
        hits = [w for w in tim["words"] if w["text"] == text]
        if len(hits) <= occurrence:
            sys.exit(f"Wort nicht gefunden: {text}")
        return hits[occurrence]["start"]

    def sent_t(scene, idx):
        ss = [s for s in tim["sentences"] if s["para"] == scene - 1]
        return ss[idx]["start"]

    cues = []
    for c in cfg["cues"]:
        if c[0] == "t":
            t, name, db = c[1], c[2], c[3]
        elif c[0] == "scene":
            t, name, db = starts[c[1] - 1] + c[2], c[3], c[4]
        elif c[0] == "word":
            t, name, db = word_t(c[1]) + c[2], c[3], c[4]
        elif c[0] == "sent":
            t, name, db = sent_t(c[1], c[2]) + c[3], c[4], c[5]
        cues.append({"t": round(max(0, t), 3), "sfx": name, "db": db})

    data = {
        "total": total,
        "voiceEnd": voice_end,
        "scenes": [{"n": i + 1, "start": starts[i], "end": ends[i], "speechStart": scenes[i]["start"],
                    "speechEnd": scenes[i]["end"], "dark": (i + 1) in cfg["dark_scenes"]} for i in range(len(scenes))],
        "sentences": tim["sentences"],
        "words": tim["words"],
        "captions": caption_groups(tim["words"], cfg["keys"]),
        "cues": cues,
    }
    for g in data["captions"]:
        g["dark"] = (g["para"] + 1) in cfg["dark_scenes"]
    (vdir / "timing.js").write_text("window.T = " + json.dumps(data, ensure_ascii=False) + ";\n")

    # Soundtrack mischen
    music_start = starts[cfg["music_start_scene"] - 1]
    inputs = ["-i", str(vdir / "audio" / "voiceover.mp3"), "-i", str(MUSIC)]
    filters = [
        "[0:a]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=11,aformat=channel_layouts=stereo[voice]",
        f"[1:a]aresample=48000,loudnorm=I=-24:TP=-2:LRA=11,volume=-12dB,aformat=channel_layouts=stereo,atrim=0:{total - music_start},"
        f"afade=t=in:st=0:d=2.5,afade=t=out:st={max(0, total - music_start - 3.5)}:d=3.5,"
        f"adelay={int(music_start * 1000)}|{int(music_start * 1000)}[music]",
    ]
    labels = ["[voice]", "[music]"]
    for i, c in enumerate(cues):
        inputs += ["-i", str(SFX / f"{c['sfx']}.wav")]
        ms = int(c["t"] * 1000)
        filters.append(f"[{i + 2}:a]aresample=48000,aformat=channel_layouts=stereo,volume={c['db']}dB,"
                       f"adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,"
                   f"atrim=0:{total},loudnorm=I=-12:TP=-1:LRA=11,aresample=48000[out]")
    out = shared / "soundtrack.wav"
    run(["ffmpeg", "-hide_banner", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
         "-ac", "2", "-ar", "48000", str(out)])
    meas = run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "loudnorm=print_format=summary", "-f", "null", "-"]).stderr
    lufs = re.search(r"Input Integrated:\s+(-?[0-9.]+)", meas)
    print(f"{v}: Dauer {total}s, {len(cues)} Effekte, Mix {lufs.group(1) if lufs else '?'} LUFS")
    for s in data["scenes"]:
        print(f"  Szene {s['n']}: {s['start']:.2f}–{s['end']:.2f}")


if __name__ == "__main__":
    main(sys.argv[1])
