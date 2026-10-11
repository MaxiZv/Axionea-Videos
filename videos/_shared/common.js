/* Gemeinsame Bausteine für die Axionea-Videos (v2). Erwartet window.T aus timing.js. */
(function () {
  const T = window.T;
  const XF = 0.6; // Überblendung zwischen Szenen in Sekunden

  const AX = {
    XF,
    S: (n) => T.scenes[n - 1].start,
    E: (n) => T.scenes[n - 1].end,
    SE: (n, i) => T.sentences.filter((s) => s.para === n - 1)[i].start,
    W: (text, occ = 0) => {
      const hits = T.words.filter((w) => w.text === text);
      if (!hits[occ]) throw new Error("Wort nicht gefunden: " + text);
      return hits[occ].start;
    },

    // Apple-artiges Einblenden: weich, mit Unschärfe und leichter Tiefe
    reveal(tl, sel, t, o = {}) {
      tl.fromTo(sel,
        { opacity: 0, y: o.y ?? 46, scale: o.scale ?? 0.97, filter: `blur(${o.blur ?? 16}px)` },
        { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: o.d ?? 1.0, ease: o.ease ?? "expo.out", stagger: o.stagger ?? 0 }, t);
    },
    // Zeilen-Reveal für Überschriften (Wort für Wort aus einer Maske)
    words(tl, sel, t, o = {}) {
      const el = document.querySelector(sel);
      const parts = el.textContent.trim().split(/\s+/);
      el.innerHTML = parts.map((p, i) => `<span class="rw" style="display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:0.08em"><span id="${el.id}-w${i}" style="display:inline-block">${p}</span></span>`).join(" ");
      tl.fromTo(parts.map((_, i) => `#${el.id}-w${i}`), { yPercent: 110, opacity: 0 }, { yPercent: 0, opacity: 1, duration: o.d ?? 0.9, ease: "expo.out", stagger: o.stagger ?? 0.06 }, t);
    },

    // Szenen: Überblendung, langsame Kamerafahrt und schwebende Farbflächen
    scenes(tl) {
      T.scenes.forEach((s) => {
        const cam = document.querySelector(`#s${s.n} .cam`);
        if (!cam) return;
        if (s.n > 1) tl.fromTo(cam, { opacity: 0 }, { opacity: 1, duration: XF, ease: "power2.inOut" }, s.start);
        const dur = s.end - s.start + XF;
        tl.fromTo(`#s${s.n} .stage`, { scale: 1.0 }, { scale: 1.035, duration: dur, ease: "none" }, s.start);
        const bg = document.querySelector(`#s${s.n} .bgimg`);
        if (bg) tl.fromTo(bg, { x: 0, y: 0, scale: 1 }, { x: s.n % 2 ? -60 : 60, y: s.n % 2 ? 30 : -30, scale: 1.04, duration: dur, ease: "sine.inOut" }, s.start);
      });
    },

    // Logo oben links: hell/dunkel je nach Szene, vor dem Outro ausblenden
    brand(tl, outroScene) {
      tl.set("#brand-dark", { opacity: T.scenes[0].dark ? 1 : 0 }, 0);
      tl.set("#brand-light", { opacity: T.scenes[0].dark ? 0 : 1 }, 0);
      tl.fromTo("#brand", { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.8, ease: "expo.out" }, 0.3);
      T.scenes.forEach((s, i) => {
        if (i === 0 || s.n === outroScene) return;
        const prev = T.scenes[i - 1];
        if (prev.dark !== s.dark) {
          tl.to("#brand-dark", { opacity: s.dark ? 1 : 0, duration: XF }, s.start);
          tl.to("#brand-light", { opacity: s.dark ? 0 : 1, duration: XF }, s.start);
        }
      });
      tl.to("#brand", { opacity: 0, duration: 0.4 }, AX.S(outroScene));
    },

    // Untertitel: ganze Satzteile, ruhig ein- und ausgeblendet; gesprochene Wörter werden kräftig
    captions(tl, opts = {}) {
      const skip = opts.skipScenes || [];
      const host = document.getElementById("captions");
      T.captions.forEach((g, gi) => {
        if (skip.includes(g.para + 1)) return;
        const el = document.createElement("div");
        el.className = "cap-group" + (g.dark ? " dark" : "");
        el.id = "cap-" + gi;
        const inner = document.createElement("div");
        inner.className = "cap-inner";
        g.words.forEach((w, wi) => {
          const s = document.createElement("span");
          s.className = "cap-word";
          s.id = `cap-${gi}-${wi}`;
          s.textContent = w.t;
          inner.appendChild(s);
        });
        el.appendChild(inner);
        host.appendChild(el);
        tl.fromTo(el, { opacity: 0, y: 14, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, ease: "power2.out" }, g.start);
        const strong = g.dark ? "#ffffff" : "#0f172a";
        const key = g.dark ? "#7fb0ff" : "#0f52ba";
        g.words.forEach((w, wi) => {
          tl.to(`#cap-${gi}-${wi}`, { color: w.k ? key : strong, duration: 0.25, ease: "power1.out" }, Math.max(g.start, w.s - 0.05));
        });
        tl.to(el, { opacity: 0, filter: "blur(6px)", duration: 0.25, ease: "power2.in" }, g.end - 0.25);
      });
    },

    // Logo-Outro: zwei Teile rasten ein, Glanz, dann der Schriftzug
    logo(tl, t0, ids) {
      tl.fromTo(ids.left, { x: -220, y: -140, opacity: 0, rotation: -10, filter: "blur(12px)" }, { x: 0, y: 0, opacity: 1, rotation: 0, filter: "blur(0px)", duration: 0.75, ease: "expo.out" }, t0 - 0.2);
      tl.fromTo(ids.right, { x: 220, y: 140, opacity: 0, rotation: 10, filter: "blur(12px)" }, { x: 0, y: 0, opacity: 1, rotation: 0, filter: "blur(0px)", duration: 0.75, ease: "expo.out" }, t0 - 0.2);
      tl.fromTo(ids.glow, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1.25, duration: 0.4, ease: "power2.out" }, t0 + 0.35);
      tl.to(ids.glow, { opacity: 0, scale: 1.7, duration: 1.0, ease: "power2.in" }, t0 + 0.75);
      tl.fromTo(ids.mark + " span", { opacity: 0, y: 40, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.7, stagger: 0.05, ease: "expo.out" }, t0 + 0.5);
    },
  };
  window.AX = AX;
})();
