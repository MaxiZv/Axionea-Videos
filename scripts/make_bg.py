#!/usr/bin/env python3
"""Rendert die weichen Farbflächen-Hintergründe je Szene als PNG (statt CSS-Blur).

Nutzung: python3 scripts/make_bg.py <video>  → videos/<video>/bg/s<N>.png (2112x1188)
"""
import pathlib, struct, sys, zlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H, PADX, PADY = 2112, 1188, 96, 54  # Rand für die Kamerafahrt

C = {"sapphire": (26, 106, 232), "cyan": (6, 182, 212), "amber": (245, 158, 11), "indigo": (74, 85, 210),
     "violet": (124, 92, 255), "emerald": (16, 185, 129)}
LIGHT, DARK = (247, 249, 252), (0, 9, 38)

# (Farbe, x, y, Breite, Höhe, Deckkraft) in 1920x1080-Koordinaten
SCENES = {
    "01-axionea-imagefilm": {
        1: (DARK, [("sapphire", 1150, -200, 900, 700, 0.55), ("indigo", -200, 600, 800, 600, 0.4), ("amber", 200, 300, 300, 300, 0.18)]),
        2: (LIGHT, [("amber", 1300, -150, 700, 600, 0.38), ("sapphire", -250, 600, 800, 600, 0.3)]),
        3: (LIGHT, [("sapphire", 100, 150, 700, 600, 0.35), ("cyan", 1300, 500, 700, 500, 0.25)]),
        4: (LIGHT, [("cyan", -100, 100, 800, 700, 0.3), ("indigo", 1200, 300, 800, 700, 0.3)]),
        5: (LIGHT, [("sapphire", -200, 0, 700, 600, 0.25), ("amber", 1400, 0, 600, 500, 0.22), ("emerald", 100, 700, 600, 500, 0.2), ("cyan", 1300, 700, 700, 500, 0.22)]),
        6: (LIGHT, [("violet", -100, -100, 700, 600, 0.2), ("cyan", 1300, 100, 700, 600, 0.25), ("amber", 700, 750, 700, 400, 0.2)]),
        7: (LIGHT, [("emerald", -100, 0, 700, 500, 0.22), ("indigo", 1300, 0, 700, 500, 0.25), ("sapphire", 600, 700, 800, 500, 0.2)]),
        8: (DARK, [("sapphire", 560, 0, 800, 700, 0.5), ("cyan", 1300, 600, 600, 500, 0.2), ("amber", 0, 650, 600, 500, 0.15)]),
    },
    "02-axionea-core-kanzlei": {
        1: (DARK, [("sapphire", 1100, -200, 900, 700, 0.55), ("violet", -200, 550, 800, 600, 0.3), ("cyan", 700, 600, 500, 400, 0.15)]),
        2: (LIGHT, [("amber", 1300, -150, 700, 600, 0.3), ("sapphire", -250, 600, 800, 600, 0.3), ("violet", 700, 800, 600, 400, 0.15)]),
        3: (LIGHT, [("sapphire", 560, 120, 800, 700, 0.35), ("cyan", 1400, 600, 600, 500, 0.2), ("indigo", -100, 500, 600, 500, 0.2)]),
        4: (LIGHT, [("sapphire", 560, 150, 800, 600, 0.3), ("emerald", -100, 600, 700, 500, 0.2), ("amber", 1400, 600, 600, 500, 0.2), ("violet", 1400, -100, 600, 500, 0.2), ("cyan", -100, -100, 600, 500, 0.2)]),
        5: (LIGHT, [("sapphire", 300, 0, 800, 600, 0.25), ("emerald", 1200, 600, 700, 500, 0.25)]),
        6: (LIGHT, [("indigo", -100, 300, 800, 700, 0.3), ("cyan", 1200, 300, 800, 700, 0.3)]),
        7: (DARK, [("sapphire", 560, 0, 800, 700, 0.5), ("cyan", 1300, 600, 600, 500, 0.2), ("amber", 0, 650, 600, 500, 0.15)]),
    },
}


def png(path, rgb):
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    path.write_bytes(data)


def render(base, blobs, dark):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.ones((H, W, 3), np.float32) * np.array(base, np.float32)
    for name, x, y, w, h, op in blobs:
        cx, cy = x + w / 2 + PADX, y + h / 2 + PADY
        sx, sy = w / 2.2, h / 2.2
        a = op * np.exp(-(((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2)) * (1.0 if dark else 0.85)
        img = img * (1 - a[..., None]) + np.array(C[name], np.float32) * a[..., None]
    # feines Punktraster
    grid = ((xx % 28 < 2) & (yy % 28 < 2))
    dot = np.array((255, 255, 255) if dark else (15, 23, 42), np.float32)
    g = 0.05 if dark else 0.05
    img[grid] = img[grid] * (1 - g) + dot * g
    # leichtes Rauschen gegen Banding
    img += np.random.default_rng(3).normal(0, 1.2, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


def main(v):
    out = ROOT / "videos" / v / "bg"
    out.mkdir(parents=True, exist_ok=True)
    for n, (base, blobs) in SCENES[v].items():
        png(out / f"s{n}.png", render(base, blobs, base == DARK))
    print(f"{v}: {len(SCENES[v])} Hintergründe")


if __name__ == "__main__":
    main(sys.argv[1])
