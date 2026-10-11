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
OUTRO_TAIL = 4.8  # Sekunden nach der letzten Silbe (Logo-Klang klingt vollständig aus)

CONFIG = {
    "01-axionea-imagefilm": {
        "keys": ["sensiblen", "Daten", "Routine", "Stunden", "Wissen", "Axionea", "KI-Agentur", "beraten,", "bauen", "betreuen", "Beratung:", "Workshops", "IT,", "Betrieb.",
                 "Deutschland", "Cloud", "lokal", "eigenen", "Hardware", "Assistenten",
                 "Automatisierungen", "Wissensdatenbanken", "Software", "jede", "Branche",
                 "rechnet", "messen", "letzte", "Wort", "Sicherheit", "KI"],
        "dark_scenes": [1, 8],
        "music_start_scene": 2,
        # (Szene, Offset ab Szenenstart oder Wort, Effekt, Pegel dB)
        "cues": [
            ("t", 0.0, "boom", -8), ("t", 0.5, "pulse", -10),
            ("t", 2.9, "tick", -10), ("t", 3.5, "tick", -11), ("t", 4.1, "tick", -11),
            ("scene", 2, 0.0, "swoosh-soft", -14),
            ("word", "Anfragen", -0.1, "ping", -17), ("word", "Dokumente", -0.1, "ping", -18),
            ("word", "Angebote", -0.1, "ping", -18), ("word", "wertvolles", 0.4, "whoosh", -18),
            ("scene", 3, 0.0, "swoosh-soft", -14), ("scene", 3, 1.6, "dock", -12),
            ("word", "beraten,", -0.15, "pop", -17), ("word", "bauen", -0.15, "pop", -17), ("word", "betreuen", -0.15, "pop", -17),
            ("scene", 4, 0.0, "swoosh-soft", -14),
            ("word", "Cloud,", 0.2, "whoosh", -15), ("word", "Cloud,", 1.35, "dock", -13),
            ("word", "lokal,", -0.3, "dock", -15),
            ("word", "empfehlen", 0.0, "tick", -13), ("word", "passende", 0.0, "tick", -13),
            ("word", "richten", 0.0, "tick", -13), ("word", "schulen", 0.0, "tick", -13),
            ("word", "Betrieb.", -0.3, "hum", -15),
            ("scene", 5, 0.0, "swoosh-soft", -14),
            ("sent", 5, 0, 1.6, "pop", -15), ("sent", 5, 0, 2.3, "typing", -21),
            ("sent", 5, 1, -0.1, "pop", -15), ("sent", 5, 2, -0.1, "pop", -15),
            ("sent", 5, 3, -0.1, "pop", -15), ("sent", 5, 3, 0.5, "whoosh", -17),
            ("sent", 5, 3, 2.0, "swoosh-soft", -14),
            ("scene", 6, 0.0, "swoosh-soft", -14),
            ("word", "Steuerkanzlei,", -0.15, "pop", -16), ("word", "Patentanwalt,", -0.15, "pop", -16),
            ("word", "Ingenieurbüro", -0.15, "pop", -16), ("word", "Finanzmakler:", -0.15, "pop", -16),
            ("word", "jede", -0.3, "whoosh", -15),
            ("scene", 7, 0.0, "swoosh-soft", -14), ("word", "Beratung:", -0.1, "tick", -13),
            ("word", "Workshops", -0.1, "tick", -13), ("word", "Start", -0.1, "tick", -13),
            ("word", "letzte", 0.0, "click", -10), ("word", "letzte", 0.12, "success", -13),
            ("scene", 8, -0.3, "riser", -17), ("scene", 8, 0.95, "dock", -9),
            ("scene", 8, 2.6, "chime", -12),
        ],
    },
    "02-axionea-core-kanzlei": {
        "keys": ["Wissen", "Routine", "Posteingang", "Termine", "Mandantenanfragen", "Mandantendaten",
                 "Axionea", "Core.", "Fünf", "Bausteine", "System.", "Deutschland.", "DATEV",
                 "Automatisierungsplattform", "Wissensbasis", "KI-Modelle", "Verbrauch.",
                 "Chatfenster", "Erstentwurf", "prüft", "frei.", "Check", "messen", "Hardware", "IT,", "Betrieb", "Workshops", "lokal", "KI-Tools",
                 "Cloud.", "Kanzlei."],
        "dark_scenes": [1, 8],
        "music_start_scene": 2,
        "cues": [
            ("t", 0.0, "boom", -9), ("t", 0.3, "pulse", -11), ("word", "Aber", 0.2, "whoosh", -16),
            ("scene", 2, 0.0, "swoosh-soft", -14),
            ("word", "Posteingang,", -0.15, "ping", -17), ("word", "Termine,", -0.15, "ping", -18),
            ("word", "Mandantenanfragen,", -0.15, "ping", -18), ("word", "dieselben", 0.0, "tick", -15),
            ("sent", 2, 1, 0.0, "whoosh", -17), ("word", "keine", -0.1, "lock", -11),
            ("scene", 3, -1.0, "riser", -19), ("scene", 3, 0.3, "dock", -11),
            ("word", "Erstens:", 0.05, "dock", -11), ("word", "Zweitens:", 0.05, "dock", -11),
            ("word", "Drittens:", 0.05, "dock", -11), ("word", "Viertens:", 0.05, "dock", -11),
            ("word", "Fünftens:", 0.05, "dock", -11),
            ("scene", 5, 0.0, "swoosh-soft", -14), ("word", "Erstentwurf,", -0.6, "typing", -21),
            ("word", "gibt", 0.0, "click", -10), ("word", "gibt", 0.12, "success", -13),
            ("scene", 6, 0.0, "swoosh-soft", -14), ("word", "empfehlen", 0.0, "tick", -13),
            ("word", "passende", 0.0, "tick", -13), ("word", "richten", 0.0, "tick", -13),
            ("word", "richten", 0.3, "hum", -16), ("word", "schulen", -0.1, "pop", -15),
            ("word", "übernehmen", -0.1, "pop", -15),
            ("scene", 7, 0.0, "swoosh-soft", -14), ("word", "Check,", -0.1, "tick", -13),
            ("word", "Workshops", -0.1, "tick", -13), ("word", "messen", -0.1, "tick", -13),
            ("scene", 8, -0.8, "riser", -17), ("word", "Axionea.", 0.0, "dock", -9),
            ("word", "Axionea.", 1.6, "chime", -12),
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
        nxt_len = len(txt) + 1 + len(nxt["text"]) if nxt else 0
        if (nxt is None or end_sent or len(cur) >= 8 or nxt_len > 46 or (soft and len(cur) >= 4)
                or (nxt and nxt["para"] != w["para"])):
            groups.append(cur)
            cur = []
    out = []
    for gi, g in enumerate(groups):
        start = g[0]["start"]
        nxt_start = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else g[-1]["end"] + 0.6
        end = min(nxt_start - 0.08, g[-1]["end"] + 0.9)
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

    # Gesamtdauer und letzte Szene in index.html an das Audio anpassen
    html_p = vdir / "index.html"
    if html_p.exists():
        html = html_p.read_text()
        html = re.sub(r'(data-composition-id="[^"]+" data-start="0" data-width="1920" data-height="1080" data-duration=")[0-9.]+', rf"\g<1>{total}", html)
        html = re.sub(r'(<audio id="soundtrack" src="shared/soundtrack.wav" data-start="0" data-duration=")[0-9.]+', rf"\g<1>{total}", html)
        for s in data["scenes"]:
            dur = round(s["end"] - s["start"] + (0 if s["n"] == len(data["scenes"]) else 0.6), 3)
            html = re.sub(rf'<section id="s{s["n"]}" class="clip scene" data-start="[0-9.]+" data-duration="[0-9.]+"',
                          f'<section id="s{s["n"]}" class="clip scene" data-start="{s["start"]}" data-duration="{dur}"', html)
        html_p.write_text(html)

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
                   f"atrim=0:{total},afade=t=out:st={total - 1.2}:d=1.2,loudnorm=I=-12:TP=-1:LRA=11,aresample=48000[out]")
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
