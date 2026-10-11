/* Gemeinsame Bausteine für die Axionea-Videos. Erwartet window.T aus timing.js. */
(function () {
  const T = window.T;

  window.AX = {
    // Zeitpunkte
    S: (n) => T.scenes[n - 1].start,
    E: (n) => T.scenes[n - 1].end,
    SE: (n, i) => T.sentences.filter((s) => s.para === n - 1)[i].start,
    W: (text, occ = 0) => {
      const hits = T.words.filter((w) => w.text === text);
      if (!hits[occ]) throw new Error("Wort nicht gefunden: " + text);
      return hits[occ].start;
    },

    // Untertitel: Gruppen erscheinen Wort für Wort, Schlüsselbegriffe in Sapphire
    captions(tl, opts = {}) {
      const skip = opts.skipScenes || [];
      const host = document.getElementById("captions");
      T.captions.forEach((g, gi) => {
        if (skip.includes(g.para + 1)) return;
        const el = document.createElement("div");
        el.className = "cap-group" + (g.dark ? " dark" : "");
        el.id = "cap-" + gi;
        g.words.forEach((w, wi) => {
          const s = document.createElement("span");
          s.className = "cap-word" + (w.k ? " key" : "");
          s.id = `cap-${gi}-${wi}`;
          s.textContent = w.t;
          el.appendChild(s);
        });
        host.appendChild(el);
        tl.set(el, { opacity: 1 }, g.start);
        g.words.forEach((w, wi) => {
          tl.fromTo(`#cap-${gi}-${wi}`, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.22, ease: "power2.out" }, Math.max(g.start, w.s - 0.04));
        });
        tl.to(el, { opacity: 0, duration: 0.08, ease: "none" }, g.end - 0.08);
      });
    },

    // Logo baut sich aus zwei Teilen auf, danach die Wortmarke
    logo(tl, t0, ids) {
      tl.fromTo(ids.left, { x: -260, y: -160, opacity: 0, rotation: -8 }, { x: 0, y: 0, opacity: 1, rotation: 0, duration: 0.55, ease: "power3.out" }, t0);
      tl.fromTo(ids.right, { x: 260, y: 160, opacity: 0, rotation: 8 }, { x: 0, y: 0, opacity: 1, rotation: 0, duration: 0.55, ease: "power3.out" }, t0);
      tl.fromTo(ids.glow, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1.25, duration: 0.35, ease: "power2.out" }, t0 + 0.5);
      tl.to(ids.glow, { opacity: 0, scale: 1.6, duration: 0.9, ease: "power2.in" }, t0 + 0.85);
      tl.fromTo(ids.mark + " span", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, stagger: 0.05, ease: "power3.out" }, t0 + 0.7);
    },
  };
})();
