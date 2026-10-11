#!/usr/bin/env python3
"""Schätzt Wort-Zeitstempel für einen Voiceover ohne ASR.

Satzgrenzen werden proportional zur Zeichenzahl verteilt und auf erkannte Sprechpausen
(ffmpeg silencedetect) gezogen; Wörter innerhalb eines Satzes proportional verteilt.
Nutzung: python3 scripts/align.py <script.txt> <voiceover.mp3> <out.json>
"""
import json, re, subprocess, sys

script, audio, out = sys.argv[1:4]
paras = [p.strip() for p in open(script).read().split("\n\n") if p.strip()]

def silences(noise="-38dB", d="0.18"):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    s = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r)]
    e = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r)]
    return list(zip(s, e))

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
                           capture_output=True, text=True).stdout)
sil = silences()
start = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
end = sil[-1][0] if sil and sil[-1][1] > dur - 0.05 else dur
pauses = [(s, e) for s, e in sil if s > start + 0.1 and e < end - 0.1]

# Sätze mit Absatz-Index
sents = []
for pi, p in enumerate(paras):
    for s in re.split(r"(?<=[.!?])\s+", p):
        if s.strip():
            sents.append((pi, s.strip()))
weights = [len(s) + 6 for _, s in sents]  # +6: Satzpause
total = sum(weights)
speech = end - start
bounds = [start]
acc = 0
for w in weights[:-1]:
    acc += w
    t = start + speech * acc / total
    near = [p for p in pauses if abs((p[0] + p[1]) / 2 - t) < 1.6]
    if near:
        p = min(near, key=lambda p: abs((p[0] + p[1]) / 2 - t))
        t = (p[0] + p[1]) / 2
        pauses.remove(p)
    bounds.append(max(t, bounds[-1] + 0.3))
bounds.append(end)

words, sentences = [], []
for i, (pi, s) in enumerate(sents):
    t0, t1 = bounds[i], bounds[i + 1]
    # Pausen innerhalb des Satzintervalls abziehen (Ende/Anfang der Lücke)
    t0s = next((e for a, e in sil if abs((a + e) / 2 - t0) < 0.01), t0)
    t1s = next((a for a, e in sil if abs((a + e) / 2 - t1) < 0.01), t1)
    ws = s.split()
    wl = [len(w) + 1 for w in ws]
    tot = sum(wl); c = 0
    for w, l in zip(ws, wl):
        ws_t = t0s + (t1s - t0s) * c / tot
        c += l
        words.append({"text": w, "start": round(ws_t, 3), "end": round(t0s + (t1s - t0s) * c / tot, 3), "para": pi})
    sentences.append({"text": s, "start": round(t0s, 3), "end": round(t1s, 3), "para": pi})

scenes = []
for pi in range(len(paras)):
    ss = [s for s in sentences if s["para"] == pi]
    scenes.append({"scene": pi + 1, "start": ss[0]["start"], "end": ss[-1]["end"]})
json.dump({"duration": dur, "scenes": scenes, "sentences": sentences, "words": words}, open(out, "w"), ensure_ascii=False, indent=1)
for sc in scenes:
    print(sc)
