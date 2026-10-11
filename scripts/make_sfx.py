#!/usr/bin/env python3
"""Erzeugt die Soundeffekte (v2): weich, stereo, mit kurzem Raumhall.

Nutzung: python3 scripts/make_sfx.py  → schreibt assets/sfx/*.wav (48 kHz, 16 bit, stereo)
"""
import pathlib, wave
import numpy as np

SR = 48000
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "sfx"
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(x, a=0.005, r=0.2):
    n = len(x)
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    e *= np.exp(-np.arange(n) / (r * SR))
    return x * e


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def highpass(x, fc):
    return x - lowpass(x, fc)


def reverb(st, size=0.9, mix=0.22, decay=1.2):
    n = int(SR * size)
    ir_l = rng.standard_normal(n) * np.exp(-np.arange(n) / (decay * SR / 6))
    ir_r = rng.standard_normal(n) * np.exp(-np.arange(n) / (decay * SR / 6))
    ir_l, ir_r = lowpass(ir_l, 5000), lowpass(ir_r, 5000)
    ir_l /= np.sqrt((ir_l ** 2).sum()); ir_r /= np.sqrt((ir_r ** 2).sum())
    pad = np.zeros((st.shape[0] + n, 2))
    pad[: st.shape[0]] = st
    wet_l = np.zeros(pad.shape[0]); wet_r = np.zeros(pad.shape[0])
    cl = np.convolve(st[:, 0], ir_l); cr = np.convolve(st[:, 1], ir_r)
    wet_l[: len(cl)] = cl[: pad.shape[0]]; wet_r[: len(cr)] = cr[: pad.shape[0]]
    pad[:, 0] = pad[:, 0] * (1 - mix) + wet_l * mix
    pad[:, 1] = pad[:, 1] * (1 - mix) + wet_r * mix
    return pad


def stereo(x, pan=0.0, width=0.0):
    l = x * np.sqrt((1 - pan) / 2) * 1.41
    r = x * np.sqrt((1 + pan) / 2) * 1.41
    if width:
        d = int(width * SR / 1000)
        r = np.concatenate([np.zeros(d), r])[: len(x)]
    return np.stack([l, r], axis=1)


def save(name, st, peak=0.7):
    st = st / (np.abs(st).max() + 1e-9) * peak
    fade = min(len(st), int(0.01 * SR))
    st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


def sweep_noise(d, f0, f1, q=1.6):
    """Gefiltertes Rauschen mit wanderndem Bandpass (Whoosh)."""
    x = rng.standard_normal(int(SR * d))
    out = np.zeros_like(x)
    lp1 = lp2 = 0.0
    for i in range(len(x)):
        fc = f0 * (f1 / f0) ** (i / len(x))
        a = np.exp(-2 * np.pi * fc / SR)
        lp1 = (1 - a) * x[i] + a * lp1
        lp2 = (1 - a) * lp1 + a * lp2
        out[i] = lp1 - lp2 * (1 / q)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # whoosh: weicher Luftzug, wandert von links nach rechts
    d = 0.9; x = sweep_noise(d, 300, 2400)
    shape = np.sin(np.pi * np.clip(t(d) / d, 0, 1)) ** 2
    x = highpass(x * shape, 120)
    pan = np.linspace(-0.7, 0.7, len(x))
    st = np.stack([x * np.sqrt((1 - pan) / 2), x * np.sqrt((1 + pan) / 2)], axis=1)
    save("whoosh", reverb(st, 0.8, 0.25), 0.6)

    # swoosh-soft: Szenenübergang, sehr leise und breit
    d = 0.7; x = sweep_noise(d, 700, 3500)
    x = highpass(x * np.sin(np.pi * t(d) / d) ** 3, 300)
    save("swoosh-soft", reverb(stereo(x, 0, 12), 0.7, 0.3), 0.45)

    # pop: weicher Blasen-Ton mit Tonhöhenanstieg
    d = 0.22; tt = t(d)
    f = 420 + 380 * (1 - np.exp(-tt * 40))
    x = env(np.sin(2 * np.pi * np.cumsum(f) / SR), 0.002, 0.045)
    x += 0.15 * env(np.sin(2 * np.pi * 2 * np.cumsum(f) / SR), 0.002, 0.03)
    save("pop", reverb(stereo(lowpass(x, 4000)), 0.5, 0.18), 0.55)

    # click: UI-Klick mit etwas Körper
    d = 0.08; tt = t(d)
    x = env(np.sin(2 * np.pi * 1800 * tt), 0.0005, 0.008) + 0.5 * env(np.sin(2 * np.pi * 320 * tt), 0.0005, 0.02)
    save("click", reverb(stereo(x), 0.3, 0.12), 0.5)

    # tick: zarter Glas-Tick
    d = 0.25; tt = t(d)
    x = env(np.sin(2 * np.pi * 2637 * tt) + 0.4 * np.sin(2 * np.pi * 3951 * tt), 0.001, 0.05)
    save("tick", reverb(stereo(x), 0.6, 0.3), 0.35)

    # dock: weiches Einrasten (tiefer Körper + gläserner Oberton)
    d = 0.6; tt = t(d)
    body = env(np.sin(2 * np.pi * (110 + 60 * np.exp(-tt * 30)) * tt), 0.002, 0.09)
    glass = 0.35 * env(np.sin(2 * np.pi * 1760 * tt) + 0.5 * np.sin(2 * np.pi * 2640 * tt), 0.002, 0.14)
    save("dock", reverb(stereo(body + glass, 0, 6), 0.8, 0.22), 0.65)

    # lock: zweistufiges, sattes Einrasten
    d = 0.5; tt = t(d)
    c1 = env(np.sin(2 * np.pi * 2200 * tt) * 0.6 + rng.standard_normal(len(tt)) * 0.15, 0.0005, 0.006)
    c2 = np.zeros_like(tt); s = int(0.09 * SR)
    c2[s:] = env(np.sin(2 * np.pi * 150 * tt[: len(tt) - s]) + 0.4 * np.sin(2 * np.pi * 1900 * tt[: len(tt) - s]), 0.0005, 0.05)
    save("lock", reverb(stereo(lowpass(c1 + c2, 6000)), 0.5, 0.18), 0.6)

    # ping: freundliche Benachrichtigung (zwei Töne)
    d = 0.9; tt = t(d)
    x = env(np.sin(2 * np.pi * 1318.5 * tt), 0.002, 0.18)
    x2 = np.zeros_like(tt); s = int(0.09 * SR)
    x2[s:] = env(np.sin(2 * np.pi * 1975.5 * tt[: len(tt) - s]), 0.002, 0.25)
    save("ping", reverb(stereo(x + 0.8 * x2, 0.25, 4), 0.9, 0.3), 0.4)

    # hum: Server fährt hoch (warm, ansteigend)
    d = 2.0; tt = t(d)
    f = 55 + 55 * np.clip(tt / 1.3, 0, 1)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR) + 0.2 * np.sin(2 * np.pi * np.cumsum(3 * f) / SR)
    x *= np.clip(tt / 0.5, 0, 1) * np.clip((d - tt) / 0.6, 0, 1)
    x += 0.08 * lowpass(rng.standard_normal(len(tt)), 900) * np.clip(tt / 1.0, 0, 1) * np.clip((d - tt) / 0.6, 0, 1)
    save("hum", reverb(stereo(lowpass(x, 1200), 0, 8), 0.8, 0.2), 0.5)

    # pulse: Herzschlag des Datenpunkts
    d = 0.8; tt = t(d)
    def thump(o):
        y = np.zeros_like(tt); s = int(o * SR)
        y[s:] = env(np.sin(2 * np.pi * 62 * tt[: len(tt) - s]), 0.004, 0.07)
        return y
    save("pulse", reverb(stereo(lowpass(thump(0) + 0.7 * thump(0.24), 300)), 0.6, 0.15), 0.7)

    # typing: dezentes Tippen, leicht variiert
    d = 1.6; x = np.zeros(int(SR * d))
    for k, o in enumerate(np.arange(0.02, d - 0.05, 0.075) + rng.uniform(-0.012, 0.012, len(np.arange(0.02, d - 0.05, 0.075)))):
        s = int(o * SR); n = int(0.03 * SR)
        f = 2600 + rng.uniform(-300, 300)
        x[s:s + n] += env(np.sin(2 * np.pi * f * t(0.03)) * 0.6 + rng.standard_normal(n) * 0.25, 0.0005, 0.006) * rng.uniform(0.6, 1)
    save("typing", reverb(stereo(highpass(x, 800), -0.15), 0.4, 0.15), 0.3)

    # riser: luftiger Anstieg vor dem Outro
    d = 1.6; x = sweep_noise(d, 400, 6000)
    x = highpass(x * (t(d) / d) ** 2.2, 250)
    tone = 0.25 * np.sin(2 * np.pi * np.cumsum(220 * (1 + t(d) / d)) / SR) * (t(d) / d) ** 2
    save("riser", reverb(stereo(x + tone, 0, 10), 0.9, 0.3), 0.5)

    # boom: weicher, tiefer Einstieg
    d = 2.2; tt = t(d)
    x = env(np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 6)) * tt), 0.004, 0.55)
    x += 0.2 * env(lowpass(rng.standard_normal(len(tt)), 400), 0.002, 0.2)
    save("boom", reverb(stereo(lowpass(x, 400), 0, 10), 1.2, 0.3), 0.8)

    # success: Freigabe, aufsteigende Terz
    d = 0.9; tt = t(d)
    a = env(np.sin(2 * np.pi * 987.8 * tt), 0.002, 0.12)
    b = np.zeros_like(tt); s = int(0.11 * SR)
    b[s:] = env(np.sin(2 * np.pi * 1318.5 * tt[: len(tt) - s]) + 0.3 * np.sin(2 * np.pi * 2637 * tt[: len(tt) - s]), 0.002, 0.25)
    save("success", reverb(stereo(a + b, 0.1, 5), 0.9, 0.28), 0.45)

    # chime: Logo-Outro, warmer Akkord mit Glanz
    d = 3.2; tt = t(d)
    x = sum(g * np.sin(2 * np.pi * f * tt) * np.exp(-tt * dec) for f, g, dec in
            [(261.6, 0.5, 1.2), (329.6, 0.4, 1.3), (392.0, 0.4, 1.4), (523.3, 0.35, 1.6), (1046.5, 0.15, 2.4), (1568, 0.08, 3)])
    x *= np.clip(tt / 0.01, 0, 1)
    save("chime", reverb(stereo(x, 0, 14), 1.6, 0.4, 2.0), 0.55)

    print("SFX v2 geschrieben:", sorted(p.name for p in OUT.glob("*.wav")))


if __name__ == "__main__":
    main()
