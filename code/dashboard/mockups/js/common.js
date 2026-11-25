/* Shared helpers: strings, language switching, icons and page controls.
   Mockup only. Nothing here talks to the live console. */
(function () {
  const params = new URLSearchParams(location.search);
  const UI = (window.UI = {
    lang: params.get("lang") === "zh" ? "zh" : "en",
    state: params.get("state") || document.body.dataset.state || "ready",
    still: params.has("still"),
    AGENTS: ["coord", "a1", "a2", "guard"],
  });

  UI.esc = (v) => String(v).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  UI.money = (n, digits) =>
    new Intl.NumberFormat(UI.lang === "zh" ? "zh-CN" : "en-US", {
      style: "currency", currency: "USD", currencyDisplay: "narrowSymbol",
      minimumFractionDigits: digits || 0, maximumFractionDigits: digits || 0,
    }).format(n);

  /* t(id, params). A value "@a1" resolves to an agent name, "@ui_x" to
     another string. A missing id falls back to English, then to the id. */
  UI.t = (key, p, lang) => {
    const l = lang || UI.lang;
    let s = (window.STRINGS[l] && window.STRINGS[l][key]) || window.STRINGS.en[key] || key;
    return s.replace(/\{(\w+)\}/g, (_, name) => {
      let v = p && p[name];
      if (v === undefined) return "";
      if (typeof v === "string" && v[0] === "@") {
        const ref = v.slice(1);
        return UI.t(UI.AGENTS.includes(ref) ? "ui_agent_" + ref : ref, null, l);
      }
      if (name === "amount" || name === "cap") return UI.money(v);
      return v;
    });
  };
  UI.h = (key, p, lang) => UI.esc(UI.t(key, p, lang));

  const PATHS = {
    check: '<path d="M4 13l5 5L20 6"/>',
    cross: '<path d="M5 5l14 14M19 5L5 19"/>',
    stop: '<path d="M8 3h8l5 5v8l-5 5H8l-5-5V8zM7 12h10"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>',
    pause: '<path d="M8 4v16M16 4v16"/>',
    mic: '<path d="M9 4h6v10H9zM5 11v1a7 7 0 0 0 14 0v-1M12 19v3"/>',
    micoff: '<path d="M9 4h6v10H9zM5 11v1a7 7 0 0 0 14 0v-1M12 19v3M3 3l18 18"/>',
    net: '<path d="M3 9a14 14 0 0 1 18 0M7 14a8 8 0 0 1 10 0M12 19h0M3 3l18 18"/>',
    plug: '<path d="M8 3v5M16 3v5M6 8h12v4a6 6 0 0 1-12 0zM12 18v4M3 21L21 3"/>',
    warn: '<path d="M12 3l10 18H2zM12 10v5M12 18h0"/>',
  };
  UI.icon = (name) => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${PATHS[name] || ""}</svg>`;
  UI.FAULT_ICON = { api: "plug", net: "net", mic: "micoff", models: "warn", vault: "warn", cost: "stop" };

  UI.langBadge = (extra) =>
    `<div class="lang ${extra || ""}" aria-label="EN / 中文">` +
    ["en", "zh"].map((l) => `<span class="${UI.lang === l ? "on" : ""}">${UI.h("ui_lang_" + l)}</span>`).join("") +
    "</div>";

  UI.meter = (n) => {
    let bars = "";
    for (let i = 0; i < n; i++) {
      const hi = (0.25 + 0.75 * Math.abs(Math.sin(i * 1.7 + 0.6))).toFixed(2);
      bars += `<i style="--hi:${hi};--lo:${(hi * 0.3).toFixed(2)};animation-delay:-${(i * 67) % 420}ms"></i>`;
    }
    return `<div class="meter" role="img" aria-label="${UI.h("ui_mic_level")}">${bars}</div>`;
  };

  /* Shrink any [data-fit] element until it fits its box. Keeps long
     translations from overflowing without per-string CSS. */
  UI.fit = () => {
    document.querySelectorAll("[data-fit]").forEach((el) => {
      el.style.fontSize = "";
      let size = parseFloat(getComputedStyle(el).fontSize);
      const min = Number(el.dataset.fit) || 24;
      while (size > min && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + size * 0.25)) {
        size -= 2;
        el.style.fontSize = size + "px";
      }
    });
  };

  UI.start = (render) => {
    let prompt = Number(params.get("prompt") || 0) % 3;
    const root = document.getElementById("screen");
    const paint = () => {
      document.documentElement.lang = UI.lang;
      let s = window.STATES[UI.state];
      /* Fail safe: an unknown or broken snapshot shows "offline", never a
         stale or half drawn live screen. */
      try {
        if (!s) throw new Error("unknown state " + UI.state);
        root.innerHTML = render(s, prompt);
      } catch (err) {
        console.warn(err);
        root.innerHTML = render(window.STATES["api-down"], prompt);
      }
      root.className = s && s.confirmRed ? "confirm-red" : "";
      UI.fit();
    };
    if (UI.still) document.documentElement.classList.add("still");
    paint();
    document.fonts.ready.then(UI.fit);
    if (!UI.still) {
      setInterval(() => {
        prompt = (prompt + 1) % 3;
        const el = document.querySelector("[data-prompt]");
        if (!el) return;
        el.textContent = UI.t("ui_at_prompt_" + (prompt + 1));
        el.classList.remove("enter");
        void el.offsetWidth;
        el.classList.add("enter");
      }, 6000);
    }
    document.addEventListener("keydown", (e) => {
      const ids = Object.keys(window.STATES);
      const at = ids.indexOf(UI.state);
      if (e.key === "l" || e.key === "L") UI.lang = UI.lang === "en" ? "zh" : "en";
      else if (e.key === "ArrowRight") UI.state = ids[(at + 1) % ids.length];
      else if (e.key === "ArrowLeft") UI.state = ids[(at - 1 + ids.length) % ids.length];
      else return;
      paint();
    });
    UI.paint = paint;
  };
})();
