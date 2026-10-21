/**
 * dsh-pet-companion —— 浏览器半侧（v0.2）
 *
 * 左下角的「小鲸鲸陪伴」面板：
 *   🍅 专注：SVG 进度环番茄钟 + 任务名 + 今日统计 + 结束提示音 + 宠物冒泡
 *   🗒 待办：本地待办清单，可一键设为当前专注任务
 *   💧 提醒：喝水 / 久坐本地定时提醒（0 token）
 *   📚 讲解 / ✏️ 辅导：借桌宠的模型通道（≈1 次模型调用），带历史与复制
 *   🎮 游戏陪伴 / 🎤 语音聊天：开关先记住，能力在后续版本接入
 *
 * 纯 DOM + 作用域样式；所有开关/统计存 localStorage；插件设置页可控制面板显隐与各功能开关。
 */
window.__ModuleLoader__.load({
  id: "dsh-pet-companion",
  factory: (require) => {
    var module = { exports: {} };
    var exports = module.exports;
    Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });

    const NS = "dsh-pet-companion";
    const STORE_KEY = "dsh-pet-companion:v2";
    const LEGACY_KEY = "dsh-pet-companion:v1";
    const VERSION = "v0.2";

    const FEATURE_ROWS = [
      ["pomodoro", "专注计时", "进度环番茄钟，也支持正计时和自定义倒计时；今日统计；结束时她冒泡并响提示音。"],
      ["todo", "待办便签", "本地待办清单，可设为当前专注任务。"],
      ["remind", "喝水和久坐提醒", "本地定时提醒（0 token），到点她冒泡。"],
      ["lesson", "课程讲解", "输入主题，按课堂方式讲解。借桌宠模型通道，≈1 次模型调用。"],
      ["tutor", "作业辅导", "贴题目，一步步讲思路。≈1 次模型调用。"],
      ["game", "游戏陪伴", "后续版本接入前台窗口检测后启用。"],
      ["voice", "语音聊天", "后续版本接入麦克风与识别后启用。"],
    ];

    const DEFAULT_SETTINGS = {
      mode: "pill",
      tab: "pomodoro",
      workMin: 25,
      breakMin: 5,
      longBreakMin: 15,
      sessionsBeforeLong: 4,
      autoContinue: true,
      chime: true,
      task: "",
      focusMode: "pomodoro",
      countdownMin: 10,
      petDisplay: "both",
      minimizeHide: false,
      features: { pomodoro: true, todo: true, remind: true, lesson: true, tutor: true, game: true, voice: true },
      reminders: { enabled: false, waterMin: 45, sitMin: 45 },
      todos: [],
      history: { lesson: [], tutor: [] },
      stats: { date: "", sessions: 0, focusMin: 0, days: {} },
    };

    let root = null;
    let styleEl = null;
    let activeDispose = null;

    // ---------- 设置存储 ----------
    function todayKey() {
      const d = new Date();
      return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
    }

    function normalizeStats(stats) {
      const base = { date: "", sessions: 0, focusMin: 0, days: {} };
      const merged = { ...base, ...(stats && typeof stats === "object" ? stats : {}) };
      const today = todayKey();
      if (merged.date !== today) {
        if (merged.date) merged.days[merged.date] = { sessions: merged.sessions, focusMin: merged.focusMin };
        merged.date = today;
        merged.sessions = 0;
        merged.focusMin = 0;
      }
      return merged;
    }

    function readSettings() {
      try {
        let raw = localStorage.getItem(STORE_KEY);
        if (!raw) raw = localStorage.getItem(LEGACY_KEY);
        const parsed = raw ? JSON.parse(raw) : null;
        const merged = { ...DEFAULT_SETTINGS, ...(parsed && typeof parsed === "object" ? parsed : {}) };
        merged.features = { ...DEFAULT_SETTINGS.features, ...(merged.features || {}) };
        merged.reminders = { ...DEFAULT_SETTINGS.reminders, ...(merged.reminders || {}) };
        merged.history = { lesson: [], tutor: [], ...(merged.history || {}) };
        merged.stats = normalizeStats(merged.stats);
        if (!Array.isArray(merged.todos)) merged.todos = [];
        // 低调模式迁移：老版本默认是展开的大面板；升级后第一次先收成小胶囊
        if (!parsed || parsed.subtleMigrated !== true) merged.mode = "pill";
        return merged;
      } catch {
        return { ...DEFAULT_SETTINGS, stats: normalizeStats(null) };
      }
    }

    function writeSettings(patch) {
      try {
        const next = { ...readSettings(), ...patch };
        localStorage.setItem(STORE_KEY, JSON.stringify(next));
        window.dispatchEvent(new CustomEvent("dsh-pet-companion:settings", { detail: next }));
        return next;
      } catch {
        return readSettings();
      }
    }

    // ---------- 桌宠 API ----------
    const PET_BASES = (() => {
      const list = [];
      try {
        if (location && /^https?:$/.test(location.protocol) && location.origin) list.push(location.origin);
      } catch (error) {}
      list.push("http://127.0.0.1:19387");
      return [...new Set(list)];
    })();

    async function petFetch(path, options) {
      let lastError = null;
      for (const base of PET_BASES) {
        try {
          const res = await fetch(base + path, options);
          if (res.ok || res.status === 404) return res;
          lastError = new Error("HTTP " + res.status);
        } catch (error) {
          lastError = error;
        }
      }
      throw lastError || new Error("桌宠接口不可达");
    }

    async function petJson(path, options) {
      const res = await petFetch(path, options);
      const text = await res.text();
      try {
        return JSON.parse(text);
      } catch {
        return { raw: text };
      }
    }

    async function petSay(text, durationMs = 12000) {
      return petJson("/dsh-pet-7340/broadcast?pet=main", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text, duration: durationMs }),
      }).catch(() => null);
    }

    async function petState() {
      try {
        const res = await petFetch("/dsh-pet-7340/state", { cache: "no-store" });
        if (res.status === 404) return null;
        return await res.json();
      } catch (error) {
        return null;
      }
    }

    async function petGenerate(prompt, onStatus) {
      const before = await petState();
      const beforeCounter = before?.pets?.main?.say?.counter ?? 0;
      const res = await petJson("/dsh-pet-7340/chat?pet=main", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: prompt }),
      });
      if (res && res.reason) throw new Error(res.reason + (res.message ? "：" + res.message : ""));
      const deadline = Date.now() + 30000;
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, 800));
        const state = await petState();
        const say = state?.pets?.main?.say;
        if (say && (say.counter ?? 0) > beforeCounter) {
          const text = say.data?.text;
          if (typeof text === "string" && text.trim()) return text.trim();
        }
        if (onStatus) onStatus("等待回复…");
      }
      throw new Error("等待超时（她可能没连上模型）");
    }

    // ---------- 桌宠显示控制 ----------
    const KEEP_PET_FIELDS = ["name", "id", "size", "balanceEnabled", "display", "position", "whisperEnabled", "workStatusEnabled", "fixedEnabled"];

    async function petGetPets() {
      const cfg = await petJson("/dsh-pet-7340/config", { cache: "no-store" });
      const pets = cfg && cfg.main && cfg.main.pets;
      if (!Array.isArray(pets)) throw new Error("读取桌宠配置失败");
      return pets;
    }

    function narrowPet(p) {
      const q = {};
      for (const k of KEEP_PET_FIELDS) if (k in p) q[k] = p[k];
      return q;
    }

    async function petGetDisplay() {
      const pets = await petGetPets();
      const mine = pets.find((p) => (p.id || "main") === "main");
      return mine ? mine.display : null;
    }

    async function petSetDisplay(display) {
      const pets = await petGetPets();
      const out = pets.map((p) => {
        const q = narrowPet(p);
        if ((q.id || "main") === "main") q.display = display;
        return q;
      });
      const res = await petFetch("/dsh-pet-7340/config", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ pets: out }),
      });
      if (!res.ok) throw new Error("修改桌宠显示失败 HTTP " + res.status);
      return display;
    }

    // ---------- 小工具 ----------
    function el(tag, attrs, children) {
      const node = document.createElement(tag);
      if (attrs) {
        for (const [k, v] of Object.entries(attrs)) {
          if (k === "class") node.className = v;
          else if (k === "text") node.textContent = v;
          else if (k === "html") node.innerHTML = v;
          else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2).toLowerCase(), v);
          else if (v !== undefined && v !== null && v !== false) node.setAttribute(k, v === true ? "" : v);
        }
      }
      for (const child of children || []) if (child) node.appendChild(child);
      return node;
    }

    function fmtClock(ms) {
      const total = Math.max(0, Math.round(ms / 1000));
      const m = Math.floor(total / 60);
      const s = total % 60;
      return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    }

    let audioCtx = null;
    function playChime(kind) {
      try {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (!Ctx) return;
        if (!audioCtx) audioCtx = new Ctx();
        const notes = kind === "break" ? [523.25, 659.25, 783.99] : [783.99, 659.25, 523.25];
        notes.forEach((freq, i) => {
          const osc = audioCtx.createOscillator();
          const gain = audioCtx.createGain();
          osc.type = "sine";
          osc.frequency.value = freq;
          const t0 = audioCtx.currentTime + i * 0.16;
          gain.gain.setValueAtTime(0.0001, t0);
          gain.gain.exponentialRampToValueAtTime(0.18, t0 + 0.02);
          gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.32);
          osc.connect(gain).connect(audioCtx.destination);
          osc.start(t0);
          osc.stop(t0 + 0.34);
        });
      } catch (error) {}
    }

    // ---------- 样式 ----------
    const CSS = `
      .pc-root { position: fixed; left: 14px; bottom: 14px; z-index: 2147482000; font: 12px/1.5 -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; color: #e6f0fb; opacity: .97; }
      .pc-card { width: 288px; max-height: min(60vh, 520px); display: flex; flex-direction: column; border-radius: 13px; overflow: hidden;
        background: linear-gradient(180deg, rgba(19,32,55,.94), rgba(11,18,33,.95)); border: 1px solid rgba(120,180,240,.16);
        box-shadow: 0 8px 24px rgba(0,12,36,.34); backdrop-filter: blur(10px); }
      .pc-head { display: flex; align-items: center; gap: 6px; padding: 6px 9px; user-select: none;
        background: rgba(80,150,235,.1); border-bottom: 1px solid rgba(120,180,240,.1); }
      .pc-dot { width: 6px; height: 6px; border-radius: 50%; background: #6fd3ff; box-shadow: 0 0 6px rgba(111,211,255,.8); flex: none; opacity: .8; }
      .pc-title { font-weight: 600; letter-spacing: .3px; flex: 1; font-size: 11.5px; opacity: .9; }
      .pc-badge { font-size: 9.5px; opacity: .45; border: 1px solid rgba(160,210,255,.25); border-radius: 999px; padding: 0 5px; white-space: nowrap; }
      .pc-hbtn { width: 18px; height: 18px; line-height: 17px; text-align: center; border-radius: 6px; cursor: pointer; opacity: .7;
        border: 1px solid transparent; font-size: 11px; flex: none; }
      .pc-hbtn:hover { opacity: 1; background: rgba(130,200,255,.22); border-color: rgba(140,210,255,.4); }
      .pc-mini { display: none; align-items: center; gap: 6px; padding: 4px 9px; border-radius: 999px; cursor: pointer;
        background: rgba(18,30,52,.9); border: 1px solid rgba(120,180,240,.2); box-shadow: 0 4px 12px rgba(0,12,36,.28);
        font-size: 11px; opacity: .9; }
      .pc-mini:hover { border-color: rgba(150,210,255,.5); opacity: 1; }
      .pc-mini-timer { font-variant-numeric: tabular-nums; opacity: .7; }
      .pc-dotbtn { display: none; width: 26px; height: 26px; border-radius: 50%; cursor: pointer; align-items: center; justify-content: center;
        background: rgba(18,30,52,.85); border: 1px solid rgba(120,180,240,.22); box-shadow: 0 4px 12px rgba(0,12,36,.28); font-size: 12px; opacity: .82; }
      .pc-dotbtn:hover { border-color: rgba(150,210,255,.6); opacity: 1; }
      .pc-root[data-mode="open"] .pc-mini, .pc-root[data-mode="open"] .pc-dotbtn { display: none; }
      .pc-root[data-mode="pill"] .pc-card, .pc-root[data-mode="pill"] .pc-dotbtn { display: none; }
      .pc-root[data-mode="pill"] .pc-mini { display: flex; }
      .pc-root[data-mode="dot"] .pc-card, .pc-root[data-mode="dot"] .pc-mini { display: none; }
      .pc-root[data-mode="dot"] .pc-dotbtn { display: flex; }
      .pc-tabs { display: flex; gap: 3px; padding: 6px 7px 0; flex-wrap: wrap; }
      .pc-tab { border: 1px solid transparent; background: rgba(120,180,255,.05); color: #c6ddf6; border-radius: 7px;
        padding: 3px 7px; cursor: pointer; font-size: 11.5px; line-height: 1.3; opacity: .85; }
      .pc-tab:hover { background: rgba(120,180,255,.13); opacity: 1; }
      .pc-tab.is-on { background: rgba(110,190,250,.16); border-color: rgba(130,200,250,.35); color: #eef7ff; opacity: 1; }
      .pc-body { padding: 9px 10px 10px; overflow: auto; }
      .pc-body h4 { margin: 1px 0 7px; font-size: 12px; font-weight: 600; color: #dcebff; display: flex; align-items: center; gap: 6px; }
      .pc-chip { font-size: 10px; opacity: .6; font-weight: 400; border: 1px solid rgba(160,210,255,.3); border-radius: 999px; padding: 0 5px; }
      .pc-row { display: flex; gap: 5px; align-items: center; margin: 5px 0; }
      .pc-row label { opacity: .8; }
      .pc-input, textarea.pc-input { width: 100%; box-sizing: border-box; background: rgba(8,18,34,.72); border: 1px solid rgba(120,180,255,.24);
        color: #eaf3ff; border-radius: 7px; padding: 5px 7px; font: inherit; resize: vertical; }
      .pc-input:focus, textarea.pc-input:focus { outline: none; border-color: rgba(140,210,255,.7); }
      .pc-num { width: 48px; text-align: center; }
      .pc-btn { border: 1px solid rgba(120,190,240,.3); background: rgba(80,160,235,.1); color: #e4f0fc; border-radius: 7px;
        padding: 4px 9px; cursor: pointer; font: inherit; opacity: .92; }
      .pc-btn:hover { background: rgba(90,170,240,.2); opacity: 1; }
      .pc-btn:disabled { opacity: .45; cursor: default; }
      .pc-btn.pc-primary { background: rgba(85,170,240,.24); border-color: rgba(140,205,245,.45); font-weight: 600; }
      .pc-btn.pc-ghost { background: transparent; border-color: rgba(140,190,240,.25); }
      .pc-btn.pc-mini { padding: 2px 7px; font-size: 11px; }
      .pc-hint { opacity: .6; font-size: 11px; margin-top: 5px; }
      .pc-hint.err { color: #ff9d9d; opacity: .95; }
      .pc-foot { padding: 5px 9px 7px; font-size: 10px; opacity: .48; border-top: 1px solid rgba(120,190,255,.1); }
      /* 专注 */
      .pc-pomo { display: flex; align-items: center; gap: 11px; margin: 2px 0 6px; }
      .pc-ring-wrap { position: relative; width: 92px; height: 92px; flex: none; }
      .pc-ring { width: 92px; height: 92px; transform: rotate(-90deg); opacity: .9; }
      .pc-ring-bg { fill: none; stroke: rgba(130,190,255,.1); stroke-width: 6; }
      .pc-ring-fg { fill: none; stroke: url(#pc-ring-grad); stroke-width: 6; stroke-linecap: round; transition: stroke-dashoffset .28s linear; opacity: .85; }
      .pc-ring-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
      .pc-clock { font-variant-numeric: tabular-nums; font-size: 22px; font-weight: 600; letter-spacing: .5px; color: #cfe9ff; line-height: 1.1; }
      .pc-phase { font-size: 10.5px; opacity: .65; margin-top: 1px; }
      .pc-pomo-side { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
      .pc-task-input { width: 100%; box-sizing: border-box; background: rgba(8,18,34,.72); border: 1px solid rgba(120,180,255,.22);
        color: #eaf3ff; border-radius: 7px; padding: 4px 7px; font: inherit; font-size: 11.5px; }
      .pc-presets { display: flex; gap: 4px; }
      .pc-preset { flex: 1; border: 1px solid rgba(130,190,245,.22); background: rgba(120,180,255,.06); color: #cfe4ff;
        border-radius: 7px; padding: 3px 0; cursor: pointer; font-size: 11px; text-align: center; }
      .pc-preset:hover { background: rgba(120,180,255,.16); }
      .pc-preset.is-on { background: rgba(110,200,255,.24); border-color: rgba(140,210,255,.55); color: #fff; }
      .pc-stats { display: flex; gap: 6px; margin-top: 8px; }
      .pc-stat { flex: 1; background: rgba(70,130,200,.07); border: 1px solid rgba(130,190,245,.1); border-radius: 8px; padding: 5px 7px; }
      .pc-stat b { display: block; font-size: 13px; color: #cfe6fb; font-weight: 600; }
      .pc-stat span { font-size: 10px; opacity: .5; }
      .pc-actions { display: flex; gap: 5px; margin-top: 8px; }
      .pc-actions .pc-btn.pc-primary { flex: 1; }
      /* 待办 */
      .pc-todo { display: flex; gap: 5px; align-items: center; padding: 4px 5px; border-radius: 7px; margin: 3px 0; }
      .pc-todo:hover { background: rgba(120,180,255,.08); }
      .pc-todo input[type="checkbox"] { accent-color: #6fd3ff; flex: none; }
      .pc-todo-text { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .pc-todo.done .pc-todo-text { opacity: .45; text-decoration: line-through; }
      .pc-todo-x { cursor: pointer; opacity: .45; padding: 0 3px; flex: none; }
      .pc-todo-x:hover { opacity: 1; color: #ff9d9d; }
      /* 输出 */
      .pc-out { margin-top: 7px; padding: 7px 8px; border-radius: 8px; background: rgba(6,15,30,.72); border: 1px solid rgba(120,180,255,.16);
        white-space: pre-wrap; word-break: break-word; max-height: 200px; overflow: auto; display: none; }
      .pc-out.is-on { display: block; }
      .pc-hist { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 7px; }
      .pc-hist-chip { font-size: 10.5px; border: 1px solid rgba(130,190,245,.22); background: rgba(120,180,255,.06);
        border-radius: 999px; padding: 1px 7px; cursor: pointer; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .pc-hist-chip:hover { background: rgba(120,180,255,.18); }
      /* 开关 */
      .pc-switch { position: relative; width: 34px; height: 18px; flex: none; }
      .pc-switch input { opacity: 0; width: 0; height: 0; }
      .pc-slider { position: absolute; inset: 0; border-radius: 999px; background: rgba(120,160,210,.35); cursor: pointer; transition: .18s; }
      .pc-slider::before { content: ""; position: absolute; width: 14px; height: 14px; left: 2px; top: 2px; border-radius: 50%; background: #eaf3ff; transition: .18s; }
      .pc-switch input:checked + .pc-slider { background: rgba(110,210,255,.75); }
      .pc-switch input:checked + .pc-slider::before { transform: translateX(16px); }
      .pc-note { background: rgba(120,180,255,.07); border: 1px dashed rgba(130,190,245,.25); border-radius: 8px; padding: 6px 8px; font-size: 11px; opacity: .8; margin-top: 7px; }
    `;

    function installStyles() {
      if (styleEl) return;
      styleEl = document.createElement("style");
      styleEl.id = "dsh-pet-companion-style";
      styleEl.textContent = CSS;
      document.head.appendChild(styleEl);
    }
    function removeStyles() {
      if (styleEl && styleEl.parentNode) styleEl.parentNode.removeChild(styleEl);
      styleEl = null;
    }

    function makeSwitch(checked, onChange) {
      const wrap = el("span", { class: "pc-switch" });
      const input = el("input", { type: "checkbox" });
      input.checked = !!checked;
      input.addEventListener("change", () => onChange(input.checked));
      wrap.appendChild(input);
      wrap.appendChild(el("span", { class: "pc-slider" }));
      return wrap;
    }

    // ---------- 面板 ----------
    function mountPanel(ctx) {
      const settings = readSettings();
      root = el("div", { class: "pc-root", "data-mode": "open" });
      const card = el("div", { class: "pc-card" });
      root.appendChild(card);

      const head = el("div", { class: "pc-head" });
      head.appendChild(el("span", { class: "pc-dot" }));
      head.appendChild(el("span", { class: "pc-title", text: "小鲸鲸陪伴" }));
      head.appendChild(el("span", { class: "pc-badge", text: VERSION }));
      const minBtn = el("span", { class: "pc-hbtn", title: "收起成小胶囊", text: "—" });
      const closeBtn = el("span", { class: "pc-hbtn", title: "隐藏（点小圆点恢复）", text: "✕" });
      head.appendChild(minBtn);
      head.appendChild(closeBtn);
      card.appendChild(head);

      const tabs = el("div", { class: "pc-tabs" });
      const body = el("div", { class: "pc-body" });
      card.appendChild(tabs);
      card.appendChild(body);
      const foot = el("div", { class: "pc-foot", text: "本地功能 0 token · 带「≈1 次模型调用」的才花 · Alt+P 隐藏/展开" });
      card.appendChild(foot);
      document.body.appendChild(root);

      const views = {};
      let current = settings.tab || "pomodoro";
      const featureOn = (key) => !settings.features || settings.features[key] !== false;
      const tabsDef = [
        ["pomodoro", "🍅 专注"],
        ["todo", "🗒 待办"],
        ["remind", "💧 提醒"],
        ["lesson", "📚 讲解"],
        ["tutor", "✏️ 辅导"],
        ["pet", "🐟 桌宠"],
      ];
      const visibleTabs = () => tabsDef.filter(([key]) => featureOn(key));

      function renderTabs() {
        tabs.textContent = "";
        const list = visibleTabs();
        if (list.length === 0) {
          tabs.appendChild(el("span", { class: "pc-hint", text: "所有功能都已关闭，可在 设置 → 小鲸鲸陪伴 重新打开。" }));
          return;
        }
        if (!list.some(([key]) => key === current)) current = list[0][0];
        for (const [key, label] of list) {
          const btn = el("button", { class: "pc-tab" + (key === current ? " is-on" : ""), text: label });
          btn.addEventListener("click", () => {
            current = key;
            writeSettings({ tab: key });
            renderTabs();
            renderBody();
          });
          tabs.appendChild(btn);
        }
      }

      function renderBody() {
        body.textContent = "";
        const view = views[current];
        if (!view || !featureOn(current)) {
          body.appendChild(el("div", { class: "pc-hint", text: "这个功能已在设置里关闭。" }));
          return;
        }
        body.appendChild(view());
      }

      // ---------- 专注：番茄钟 / 正计时 / 自定义倒计时 ----------
      const focus = {
        mode: ["pomodoro", "stopwatch", "countdown"].includes(settings.focusMode) ? settings.focusMode : "pomodoro",
        pomo: { phase: "work", remain: (settings.workMin || 25) * 60 * 1000 },
        stopwatch: { elapsed: 0 },
        countdown: { total: (settings.countdownMin || 10) * 60 * 1000, remain: (settings.countdownMin || 10) * 60 * 1000 },
      };
      let timer = null;
      let running = false;
      let lastTick = 0;
      let clockEl = null;
      let ringEl = null;
      let pillTimer = null;
      const lastOut = {};

      function fmtLong(ms) {
        const total = Math.max(0, Math.round(ms / 1000));
        const h = Math.floor(total / 3600);
        const m = Math.floor((total % 3600) / 60);
        const s = total % 60;
        const mm = String(m).padStart(2, "0");
        const ss = String(s).padStart(2, "0");
        return h > 0 ? h + ":" + mm + ":" + ss : mm + ":" + ss;
      }
      function focusTotal() {
        if (focus.mode === "pomodoro") return (focus.pomo.phase === "work" ? settings.workMin : settings.breakMin) * 60000;
        if (focus.mode === "countdown") return focus.countdown.total;
        return 3600000;
      }
      function focusValue() {
        if (focus.mode === "pomodoro") return Math.max(0, focus.pomo.remain);
        if (focus.mode === "countdown") return Math.max(0, focus.countdown.remain);
        return Math.max(0, focus.stopwatch.elapsed);
      }
      function focusRatio() {
        if (focus.mode === "stopwatch") return Math.min(1, focus.stopwatch.elapsed / 3600000);
        const total = focusTotal();
        return total > 0 ? Math.max(0, Math.min(1, focusValue() / total)) : 0;
      }
      function paintFocus() {
        const value = focusValue();
        const text = focus.mode === "stopwatch" ? fmtLong(value) : fmtClock(value);
        if (clockEl) clockEl.textContent = text;
        if (ringEl) {
          const r = 45;
          const c = 2 * Math.PI * r;
          const ratio = focusRatio();
          ringEl.style.strokeDasharray = String(c);
          ringEl.style.strokeDashoffset = String(c * (1 - ratio));
        }
        if (pillTimer) pillTimer.textContent = fmtLong(value);
      }
      function stopTimer() {
        if (timer) clearInterval(timer);
        timer = null;
        running = false;
      }
      function startTimer() {
        stopTimer();
        running = true;
        lastTick = Date.now();
        timer = setInterval(() => {
          const now = Date.now();
          const delta = now - lastTick;
          lastTick = now;
          if (focus.mode === "pomodoro") {
            focus.pomo.remain -= delta;
            if (focus.pomo.remain <= 0) {
              focus.pomo.remain = 0;
              completePhase();
            }
          } else if (focus.mode === "countdown") {
            focus.countdown.remain -= delta;
            if (focus.countdown.remain <= 0) {
              focus.countdown.remain = 0;
              completeCountdown();
            }
          } else {
            focus.stopwatch.elapsed += delta;
          }
          paintFocus();
        }, 250);
      }
      function addStats(minutes, asSession) {
        const stats = normalizeStats(settings.stats);
        stats.focusMin += Math.max(0, Math.round(minutes));
        if (asSession) stats.sessions += 1;
        settings.stats = stats;
        writeSettings({ stats });
      }
      function completePhase() {
        const finished = focus.pomo.phase;
        stopTimer();
        if (finished === "work") {
          addStats(settings.workMin || 25, true);
          const task = (settings.task || "").trim();
          petSay("番茄完成！" + (task ? "「" + task + "」" : "这次") + "专心了 " + (settings.workMin || 25) + " 分钟，休息一下吧～");
          if (settings.chime) playChime("break");
          focus.pomo.phase = "break";
          focus.pomo.remain = (settings.breakMin || 5) * 60000;
        } else {
          petSay("休息结束，下一轮开始啦！");
          if (settings.chime) playChime("work");
          focus.pomo.phase = "work";
          focus.pomo.remain = (settings.workMin || 25) * 60000;
        }
        if (settings.autoContinue) startTimer();
        else paintFocus();
        renderBody();
      }
      function completeCountdown() {
        stopTimer();
        const mins = Math.max(1, Math.round(focus.countdown.total / 60000));
        addStats(mins, true);
        const task = (settings.task || "").trim();
        petSay("倒计时结束啦！" + (task ? "「" + task + "」" : "") + "这次专注了 " + mins + " 分钟。");
        if (settings.chime) playChime("break");
        focus.countdown.remain = focus.countdown.total;
        paintFocus();
        renderBody();
      }
      function logStopwatch() {
        const mins = Math.floor(focus.stopwatch.elapsed / 60000);
        if (mins >= 1) {
          addStats(mins, false);
          petSay("记下啦：这次专注了 " + mins + " 分钟。");
          focus.stopwatch.elapsed = 0;
        }
        stopTimer();
        paintFocus();
        renderBody();
      }

      views.pomodoro = () => {
        const wrap = el("div");
        const stats = normalizeStats(settings.stats);
        // 模式切换：番茄钟 / 正计时 / 自定义倒计时
        const modes = [
          ["pomodoro", "🍅 番茄钟"],
          ["stopwatch", "⏱ 正计时"],
          ["countdown", "⏲ 倒计时"],
        ];
        const modeRow = el("div", { class: "pc-presets" });
        for (const [value, label] of modes) {
          const btn = el("div", { class: "pc-preset" + (focus.mode === value ? " is-on" : ""), text: label });
          btn.addEventListener("click", () => {
            stopTimer();
            focus.mode = value;
            writeSettings({ focusMode: value });
            if (value === "pomodoro") {
              focus.pomo.phase = "work";
              focus.pomo.remain = (settings.workMin || 25) * 60000;
            } else if (value === "countdown") {
              focus.countdown.total = (settings.countdownMin || 10) * 60000;
              focus.countdown.remain = focus.countdown.total;
            }
            renderBody();
          });
          modeRow.appendChild(btn);
        }
        wrap.appendChild(modeRow);

        const ringSvg = (() => {
          const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
          svg.setAttribute("class", "pc-ring");
          svg.setAttribute("viewBox", "0 0 104 104");
          svg.innerHTML =
            '<defs><linearGradient id="pc-ring-grad" x1="0" y1="0" x2="1" y2="1">' +
            '<stop offset="0%" stop-color="#8fe3ff"/><stop offset="100%" stop-color="#6f9dff"/></linearGradient></defs>' +
            '<circle class="pc-ring-bg" cx="52" cy="52" r="45"></circle>';
          const fg = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          fg.setAttribute("class", "pc-ring-fg");
          fg.setAttribute("cx", "52");
          fg.setAttribute("cy", "52");
          fg.setAttribute("r", "45");
          svg.appendChild(fg);
          ringEl = fg;
          return svg;
        })();
        const phaseText =
          focus.mode === "pomodoro" ? (focus.pomo.phase === "work" ? "专注中" : "休息中") : focus.mode === "stopwatch" ? "正计时" : "倒计时";
        const center = el("div", { class: "pc-ring-center" }, [
          (clockEl = el("div", { class: "pc-clock", text: focus.mode === "stopwatch" ? fmtLong(focus.stopwatch.elapsed) : fmtClock(focusValue()) })),
          el("div", { class: "pc-phase", text: phaseText }),
        ]);
        const side = el("div", { class: "pc-pomo-side" });
        const taskInput = el("input", { class: "pc-task-input", placeholder: "这次专注做什么？（可留空）", value: settings.task || "" });
        taskInput.addEventListener("input", () => {
          settings.task = taskInput.value;
          writeSettings({ task: taskInput.value });
        });
        side.appendChild(taskInput);

        if (focus.mode === "pomodoro") {
          const presets = el("div", { class: "pc-presets" });
          [[25, 5], [45, 10], [60, 15]].forEach(([w, b]) => {
            const on = settings.workMin === w && settings.breakMin === b;
            const btn = el("div", { class: "pc-preset" + (on ? " is-on" : ""), text: w + "/" + b });
            btn.addEventListener("click", () => {
              settings.workMin = w;
              settings.breakMin = b;
              writeSettings({ workMin: w, breakMin: b });
              focus.pomo.phase = "work";
              focus.pomo.remain = w * 60000;
              stopTimer();
              renderBody();
            });
            presets.appendChild(btn);
          });
          side.appendChild(presets);
          // 自定义时长
          const customRow = el("div", { class: "pc-row" });
          const workInput = el("input", { class: "pc-input pc-num", type: "number", min: "1", max: "180", value: String(settings.workMin || 25) });
          const breakInput = el("input", { class: "pc-input pc-num", type: "number", min: "1", max: "60", value: String(settings.breakMin || 5) });
          const applyCustom = () => {
            const w = Math.max(1, Math.min(180, Number(workInput.value) || 25));
            const b = Math.max(1, Math.min(60, Number(breakInput.value) || 5));
            workInput.value = String(w);
            breakInput.value = String(b);
            settings.workMin = w;
            settings.breakMin = b;
            writeSettings({ workMin: w, breakMin: b });
            focus.pomo.phase = "work";
            focus.pomo.remain = w * 60000;
            stopTimer();
            renderBody();
          };
          workInput.addEventListener("change", applyCustom);
          breakInput.addEventListener("change", applyCustom);
          customRow.appendChild(el("label", { text: "专注" }));
          customRow.appendChild(workInput);
          customRow.appendChild(el("label", { text: "分 / 休息" }));
          customRow.appendChild(breakInput);
          customRow.appendChild(el("label", { text: "分" }));
          side.appendChild(customRow);
        } else if (focus.mode === "countdown") {
          const cdRow = el("div", { class: "pc-row" });
          const minInput = el("input", { class: "pc-input pc-num", type: "number", min: "1", max: "600", value: String(settings.countdownMin || 10) });
          const applyCd = () => {
            const m = Math.max(1, Math.min(600, Number(minInput.value) || 10));
            minInput.value = String(m);
            settings.countdownMin = m;
            writeSettings({ countdownMin: m });
            stopTimer();
            focus.countdown.total = m * 60000;
            focus.countdown.remain = m * 60000;
            renderBody();
          };
          minInput.addEventListener("change", applyCd);
          cdRow.appendChild(el("label", { text: "计时" }));
          cdRow.appendChild(minInput);
          cdRow.appendChild(el("label", { text: "分钟" }));
          side.appendChild(cdRow);
          side.appendChild(el("div", { class: "pc-hint", text: "任意分钟数，到点提示并记入专注统计。" }));
        } else {
          side.appendChild(el("div", { class: "pc-hint", text: "自由计时：暂停后可以「记入统计」，清空重新开始。" }));
        }
        wrap.appendChild(el("div", { class: "pc-pomo" }, [el("div", { class: "pc-ring-wrap" }, [ringSvg, center]), side]));

        const actions = el("div", { class: "pc-actions" });
        const startBtn = el("button", { class: "pc-btn pc-primary", text: running ? "暂停" : "开始" });
        startBtn.addEventListener("click", () => {
          if (running) {
            stopTimer();
            startBtn.textContent = "继续";
            renderBody();
            return;
          }
          if (focus.mode === "pomodoro" && focus.pomo.remain <= 0) focus.pomo.remain = focusTotal();
          if (focus.mode === "countdown" && focus.countdown.remain <= 0) focus.countdown.remain = focus.countdown.total;
          startTimer();
          startBtn.textContent = "暂停";
        });
        actions.appendChild(startBtn);
        const resetBtn = el("button", { class: "pc-btn", text: "重置" });
        resetBtn.addEventListener("click", () => {
          stopTimer();
          if (focus.mode === "pomodoro") {
            focus.pomo.phase = "work";
            focus.pomo.remain = (settings.workMin || 25) * 60000;
          } else if (focus.mode === "countdown") {
            focus.countdown.remain = focus.countdown.total;
          } else {
            focus.stopwatch.elapsed = 0;
          }
          renderBody();
        });
        actions.appendChild(resetBtn);
        if (focus.mode === "pomodoro") {
          const skipBtn = el("button", { class: "pc-btn pc-ghost", text: "跳过" });
          skipBtn.addEventListener("click", () => {
            focus.pomo.remain = 0;
            completePhase();
          });
          actions.appendChild(skipBtn);
        } else if (focus.mode === "countdown") {
          const doneBtn = el("button", { class: "pc-btn pc-ghost", text: "结束" });
          doneBtn.addEventListener("click", () => {
            const mins = Math.floor((focus.countdown.total - focus.countdown.remain) / 60000);
            if (mins >= 1) {
              addStats(mins, true);
              petSay("结束啦，这次专注了 " + mins + " 分钟。");
            }
            stopTimer();
            focus.countdown.remain = focus.countdown.total;
            renderBody();
          });
          actions.appendChild(doneBtn);
        } else {
          const logBtn = el("button", { class: "pc-btn pc-ghost", text: "记入统计" });
          logBtn.disabled = running || focus.stopwatch.elapsed < 60000;
          logBtn.addEventListener("click", logStopwatch);
          actions.appendChild(logBtn);
        }
        wrap.appendChild(actions);

        const statsRow = el("div", { class: "pc-stats" });
        statsRow.appendChild(el("div", { class: "pc-stat" }, [el("b", { text: String(stats.sessions) }), el("span", { text: "今日完成" })]));
        statsRow.appendChild(el("div", { class: "pc-stat" }, [el("b", { text: String(stats.focusMin) }), el("span", { text: "今日专注（分）" })]));
        const streakDays = Object.keys(stats.days || {}).length + (stats.sessions > 0 ? 1 : 0);
        statsRow.appendChild(el("div", { class: "pc-stat" }, [el("b", { text: String(Math.max(streakDays, stats.sessions > 0 ? 1 : 0)) }), el("span", { text: "有记录天数" })]));
        wrap.appendChild(statsRow);
        wrap.appendChild(el("div", { class: "pc-hint", text: "结束时她会冒泡提醒；开着语音播报的话还会念出来。" }));
        paintFocus();
        return wrap;
      };

      // ---------- 待办 ----------
      views.todo = () => {
        const wrap = el("div");
        wrap.appendChild(el("h4", null, ["待办便签", el("span", { class: "pc-chip", text: "0 token" })]));
        const input = el("input", { class: "pc-input", placeholder: "加一条待办，回车保存" });
        const add = () => {
          const text = input.value.trim();
          if (!text) return;
          const todos = [...(settings.todos || []), { id: String(Date.now()), text, done: false }];
          settings.todos = todos;
          writeSettings({ todos });
          input.value = "";
          renderBody();
        };
        input.addEventListener("keydown", (event) => {
          if (event.key === "Enter") add();
        });
        wrap.appendChild(el("div", { class: "pc-row" }, [input, el("button", { class: "pc-btn", text: "添加", onclick: add })]));
        const list = (settings.todos || []).slice().sort((a, b) => Number(a.done) - Number(b.done));
        if (list.length === 0) {
          wrap.appendChild(el("div", { class: "pc-note", text: "还没有待办。先把「今天要做什么」写下来，专注时她会帮你盯着。" }));
        }
        for (const item of list) {
          const row = el("div", { class: "pc-todo" + (item.done ? " done" : "") });
          const cb = el("input", { type: "checkbox" });
          cb.checked = !!item.done;
          cb.addEventListener("change", () => {
            const todos = settings.todos.map((x) => (x.id === item.id ? { ...x, done: cb.checked } : x));
            settings.todos = todos;
            writeSettings({ todos });
            renderBody();
          });
          row.appendChild(cb);
          row.appendChild(el("span", { class: "pc-todo-text", text: item.text, title: item.text }));
          const focusBtn = el("span", { class: "pc-hint", style: "cursor:pointer;margin:0 2px;opacity:.6", text: "专注", title: "设为当前专注任务" });
          focusBtn.addEventListener("click", () => {
            settings.task = item.text;
            pomo.phase = "work";
            pomo.remain = (settings.workMin || 25) * 60 * 1000;
            stopTimer();
            pomo.running = false;
            writeSettings({ task: item.text, tab: "pomodoro" });
            current = "pomodoro";
            renderTabs();
            renderBody();
          });
          row.appendChild(focusBtn);
          const del = el("span", { class: "pc-todo-x", text: "✕", title: "删除" });
          del.addEventListener("click", () => {
            const todos = settings.todos.filter((x) => x.id !== item.id);
            settings.todos = todos;
            writeSettings({ todos });
            renderBody();
          });
          row.appendChild(del);
          wrap.appendChild(row);
        }
        const doneCount = (settings.todos || []).filter((x) => x.done).length;
        if (doneCount > 0) {
          wrap.appendChild(el("div", { class: "pc-row" }, [
            el("span", { class: "pc-hint", text: "已完成 " + doneCount + " 条" }),
            el("button", {
              class: "pc-btn pc-ghost pc-mini",
              text: "清理已完成",
              onclick: () => {
                const todos = settings.todos.filter((x) => !x.done);
                settings.todos = todos;
                writeSettings({ todos });
                renderBody();
              },
            }),
          ]));
        }
        return wrap;
      };

      // ---------- 提醒（喝水 / 久坐） ----------
      let remindTimer = null;
      let lastWater = Date.now();
      let lastSit = Date.now();
      function scheduleReminders() {
        if (remindTimer) clearInterval(remindTimer);
        remindTimer = null;
        if (!settings.reminders || !settings.reminders.enabled) return;
        lastWater = Date.now();
        lastSit = Date.now();
        remindTimer = setInterval(() => {
          const now = Date.now();
          const waterMs = Math.max(5, settings.reminders.waterMin || 45) * 60000;
          const sitMs = Math.max(5, settings.reminders.sitMin || 45) * 60000;
          if (now - lastWater >= waterMs) {
            lastWater = now;
            petSay("该喝水啦～杯子就在手边，咕咚咕咚。");
            if (settings.chime) playChime("break");
          }
          if (now - lastSit >= sitMs) {
            lastSit = now;
            petSay("坐太久啦，站起来走两步，伸个懒腰～");
            if (settings.chime) playChime("break");
          }
        }, 15000);
      }
      views.remind = () => {
        const wrap = el("div");
        wrap.appendChild(el("h4", null, ["喝水 / 久坐提醒", el("span", { class: "pc-chip", text: "0 token" })]));
        const row = el("div", { class: "pc-row" });
        row.appendChild(el("label", { text: "开启提醒" }));
        row.appendChild(makeSwitch(!!settings.reminders.enabled, (v) => {
          settings.reminders = { ...settings.reminders, enabled: v };
          writeSettings({ reminders: settings.reminders });
          scheduleReminders();
          renderBody();
        }));
        wrap.appendChild(row);
        const nums = el("div", { class: "pc-row" });
        nums.appendChild(el("label", { text: "喝水每" }));
        const waterInput = el("input", { class: "pc-input pc-num", type: "number", min: "5", max: "240", value: String(settings.reminders.waterMin || 45) });
        waterInput.addEventListener("change", () => {
          settings.reminders = { ...settings.reminders, waterMin: Math.max(5, Math.min(240, Number(waterInput.value) || 45)) };
          writeSettings({ reminders: settings.reminders });
          scheduleReminders();
        });
        nums.appendChild(waterInput);
        nums.appendChild(el("label", { text: "分钟 · 久坐每" }));
        const sitInput = el("input", { class: "pc-input pc-num", type: "number", min: "5", max: "240", value: String(settings.reminders.sitMin || 45) });
        sitInput.addEventListener("change", () => {
          settings.reminders = { ...settings.reminders, sitMin: Math.max(5, Math.min(240, Number(sitInput.value) || 45)) };
          writeSettings({ reminders: settings.reminders });
          scheduleReminders();
        });
        nums.appendChild(sitInput);
        nums.appendChild(el("label", { text: "分钟" }));
        wrap.appendChild(nums);
        wrap.appendChild(el("div", { class: "pc-row" }, [
          el("button", {
            class: "pc-btn",
            text: "现在试一下",
            onclick: () => {
              petSay("该喝水啦～杯子就在手边，咕咚咕咚。");
              if (settings.chime) playChime("break");
            },
          }),
          el("span", { class: "pc-hint", text: "提醒只在本页面开着的标签页里计时；关掉后不提醒。" }),
        ]));
        return wrap;
      };

      // ---------- 讲解 / 辅导 ----------
      function makeAskView(key, title, placeholder, template, hint) {
        return () => {
          const wrap = el("div");
          wrap.appendChild(el("h4", null, [title, el("span", { class: "pc-chip", text: "≈1 次模型调用" })]));
          const input = el("textarea", { class: "pc-input", rows: "3", placeholder });
          wrap.appendChild(input);
          const out = el("div", { class: "pc-out" });
          const status = el("div", { class: "pc-hint" });
          const previous = lastOut[key];
          if (previous && previous.a) {
            out.textContent = previous.a;
            out.classList.add("is-on");
            input.value = previous.q || "";
          }
          const actions = el("div", { class: "pc-row" });
          const askBtn = el("button", { class: "pc-btn pc-primary", text: "开始" });
          askBtn.addEventListener("click", async () => {
            const value = input.value.trim();
            if (!value) {
              status.textContent = "先输入内容～";
              return;
            }
            askBtn.disabled = true;
            status.textContent = "思考中…（这一步会花 token）";
            out.classList.remove("is-on");
            try {
              const text = await petGenerate(template(value), (msg) => {
                status.textContent = msg;
              });
              status.textContent = "完成（已存进历史）";
              lastOut[key] = { q: value, a: text };
              const history = { ...settings.history, [key]: [{ q: value, a: text, at: Date.now() }, ...(settings.history[key] || [])].slice(0, 8) };
              settings.history = history;
              writeSettings({ history });
              renderBody();
            } catch (error) {
              status.textContent = "失败：" + (error && error.message ? error.message : String(error)) + "（需要桌宠在运行）";
              status.classList.add("err");
            } finally {
              askBtn.disabled = false;
            }
          });
          const copyBtn = el("button", { class: "pc-btn pc-ghost pc-mini", text: "复制结果" });
          copyBtn.addEventListener("click", async () => {
            const text = out.textContent || "";
            if (!text) return;
            try {
              await navigator.clipboard.writeText(text);
              status.textContent = "已复制";
            } catch (error) {
              status.textContent = "复制失败（可以手动选中）";
            }
          });
          actions.appendChild(askBtn);
          actions.appendChild(copyBtn);
          wrap.appendChild(actions);
          wrap.appendChild(status);
          wrap.appendChild(out);
          const hist = settings.history[key] || [];
          if (hist.length > 0) {
            wrap.appendChild(el("div", { class: "pc-hint", text: "最近记录（点一下回看）：" }));
            const chips = el("div", { class: "pc-hist" });
            for (const item of hist.slice(0, 6)) {
              const chip = el("span", { class: "pc-hist-chip", text: item.q.slice(0, 14), title: item.q });
              chip.addEventListener("click", () => {
                input.value = item.q;
                out.textContent = item.a;
                out.classList.add("is-on");
                status.textContent = "回看历史";
                lastOut[key] = { q: item.q, a: item.a };
              });
              chips.appendChild(chip);
            }
            wrap.appendChild(chips);
          }
          wrap.appendChild(el("div", { class: "pc-hint", text: hint }));
          return wrap;
        };
      }

      views.lesson = makeAskView(
        "lesson",
        "课程讲解",
        "想听什么？例如：什么是梯度下降 / 光合作用是怎么回事",
        (topic) =>
          `【认真模式】请暂时放下小鲸鲸的卖萌/撒娇人设，用清晰、可靠的老师语气回答。像上课一样给我讲解：${topic}。要求：先一句话说这是什么，再分 3-4 个要点按顺序讲清楚，用生活化比喻，最后给我一个自测问题。口语化，控制在 400 字以内。`,
        "讲解由桌宠的聊天模型生成；她不在时会提示。",
      );

      views.tutor = makeAskView(
        "tutor",
        "作业辅导",
        "把题目贴在这里（数学 / 物理 / 语文都可以）",
        (question) =>
          `【认真模式】请暂时放下小鲸鲸的卖萌/撒娇人设，用耐心、清晰的辅导语气回答。请辅导我完成这道作业题：${question}\n要求：先指出题目在考什么，再一步一步讲思路（为什么这么做），最后给答案；如果我可能卡住的地方，单独提醒一句。不要只给答案。`,
        "她会一步步讲思路，而不是只报答案。",
      );

      // ---------- 桌宠显示 ----------
      views.pet = () => {
        const wrap = el("div");
        wrap.appendChild(el("h4", null, ["桌宠显示", el("span", { class: "pc-chip", text: "本地控制" })]));
        const status = el("div", { class: "pc-hint", text: "" });
        const displayRow = el("div", { class: "pc-presets" });
        const choices = [
          ["both", "都显示"],
          ["desktop", "仅桌面"],
          ["web", "仅 DSH 页面"],
          ["none", "都隐藏"],
        ];
        const markCurrent = (value) => {
          Array.from(displayRow.children).forEach((child) => {
            child.classList.toggle("is-on", child.getAttribute("data-value") === value);
          });
        };
        petGetDisplay()
          .then((cur) => {
            markCurrent(cur || settings.petDisplay || "both");
            if (cur) settings.petDisplay = cur;
          })
          .catch(() => status.textContent = "桌宠没在运行，读不到当前显示状态");
        for (const [value, label] of choices) {
          const btn = el("div", { class: "pc-preset", "data-value": value, text: label });
          btn.addEventListener("click", () => {
            markCurrent(value);
            settings.petDisplay = value;
            writeSettings({ petDisplay: value });
            status.textContent = "正在切换…";
            petSetDisplay(value)
              .then(() => {
                status.textContent = value === "none" ? "桌宠已隐藏；可以从这里随时叫回来。" : "已切换（桌面侧会即时重载）";
              })
              .catch((error) => {
                status.textContent = "切换失败：" + (error && error.message ? error.message : String(error));
              });
          });
          displayRow.appendChild(btn);
        }
        wrap.appendChild(displayRow);
        wrap.appendChild(el("div", { class: "pc-hint", text: "显示位置：桌面 / DSH 页面（网页端需刷新页面才更新）" }));
        wrap.appendChild(status);

        const minimizeRow = el("div", { class: "pc-row" });
        minimizeRow.appendChild(el("label", { text: "DSH 最小化时隐藏桌宠" }));
        minimizeRow.appendChild(makeSwitch(!!settings.minimizeHide, (v) => {
          settings.minimizeHide = v;
          writeSettings({ minimizeHide: v });
        }));
        wrap.appendChild(el("div", { class: "pc-note", text: "开启后：最小化 DSH 时自动把桌面宠物收起来，恢复窗口时再放回来。最近一次切换的显示状态会记住。" }));
        wrap.appendChild(minimizeRow);

        wrap.appendChild(el("div", { class: "pc-foot", text: "后续版本：陪玩游戏 / 语音聊天（设置里可以先放开关位置）" }));
        return wrap;
      };

      // ---------- 游戏 / 语音 ----------
      views.game = () => {
        const wrap = el("div");
        wrap.appendChild(el("h4", null, ["游戏陪伴", el("span", { class: "pc-chip", text: "未接入" })]));
        const row = el("div", { class: "pc-row" });
        row.appendChild(el("label", { text: "启用陪玩评论（先记住）" }));
        row.appendChild(makeSwitch(!!settings.features.game, (v) => {
          settings.features = { ...settings.features, game: v };
          writeSettings({ features: settings.features });
          renderTabs();
          renderBody();
        }));
        wrap.appendChild(row);
        wrap.appendChild(el("div", { class: "pc-note", text: "接入后：读取当前前台窗口（只读标题、不截图），在你玩游戏时低频冒一句评论。每次 ≈1 次模型调用，可设日预算；全屏游戏时默认闭嘴。" }));
        return wrap;
      };

      views.voice = () => {
        const wrap = el("div");
        wrap.appendChild(el("h4", null, ["语音聊天", el("span", { class: "pc-chip", text: "未接入" })]));
        const row = el("div", { class: "pc-row" });
        row.appendChild(el("label", { text: "启用麦克风聊天（先记住）" }));
        row.appendChild(makeSwitch(!!settings.features.voice, (v) => {
          settings.features = { ...settings.features, voice: v };
          writeSettings({ features: settings.features });
          renderTabs();
          renderBody();
        }));
        wrap.appendChild(row);
        wrap.appendChild(el("div", { class: "pc-note", text: "接入后：按住说话 → 本地/云端语音识别 → 她回答（≈1 次模型调用）→ 语音播报。需要麦克风权限，优先本地识别、不上传录音。" }));
        return wrap;
      };

      // ---------- 显示模式 ----------
      const mini = el("div", { class: "pc-mini", title: "展开小鲸鲸陪伴" }, [
        el("span", { text: "🍅 小鲸鲸" }),
        (pillTimer = el("span", { class: "pc-mini-timer", text: fmtLong(focusValue()) })),
      ]);
      const dotBtn = el("div", { class: "pc-dotbtn", title: "展开小鲸鲸陪伴", text: "鲸" });
      root.appendChild(mini);
      root.appendChild(dotBtn);

      let mode = ["open", "pill", "dot"].includes(settings.mode) ? settings.mode : "open";
      function applyMode() {
        root.setAttribute("data-mode", mode);
      }
      function setMode(next) {
        mode = next;
        writeSettings({ mode });
        applyMode();
      }
      minBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        setMode("pill");
      });
      closeBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        setMode("dot");
      });
      mini.addEventListener("click", () => setMode("open"));
      dotBtn.addEventListener("click", () => setMode("open"));
      applyMode();

      if (settings.panelEnabled === false) root.style.display = "none";
      // 第一次以低调模式启动：记下标记，之后尊重用户自己选的面板形态
      if (!settings.subtleMigrated) writeSettings({ subtleMigrated: true, mode });
      const onExternalSettings = (event) => {
        const next = (event && event.detail) || readSettings();
        settings.features = next.features || settings.features;
        settings.panelEnabled = next.panelEnabled !== false;
        settings.minimizeHide = next.minimizeHide === true;
        settings.petDisplay = next.petDisplay || settings.petDisplay;
        root.style.display = settings.panelEnabled ? "" : "none";
        if (next.mode && ["open", "pill", "dot"].includes(next.mode) && next.mode !== mode) {
          mode = next.mode;
          applyMode();
        }
        renderTabs();
        renderBody();
      };
      window.addEventListener("dsh-pet-companion:settings", onExternalSettings);

      // Alt+P：隐藏 / 展开
      const onKeydown = (event) => {
        if (event.altKey && (event.key === "p" || event.key === "P")) {
          event.preventDefault();
          setMode(mode === "dot" ? "open" : "dot");
        }
      };
      window.addEventListener("keydown", onKeydown);

      // DSH 最小化时自动隐藏桌面宠物（Page Visibility 只在窗口最小化/切走时变 hidden）
      let displayBeforeMinimize = null;
      let minimizeBusy = false;
      const onVisibilityChange = async () => {
        if (!settings.minimizeHide || minimizeBusy) return;
        minimizeBusy = true;
        try {
          if (document.hidden) {
            const current = await petGetDisplay();
            if (current === "both" || current === "desktop") {
              displayBeforeMinimize = current;
              await petSetDisplay("web");
            }
          } else if (displayBeforeMinimize) {
            const target = displayBeforeMinimize;
            displayBeforeMinimize = null;
            await petSetDisplay(target);
          }
        } catch (error) {
          /* 桌宠不在运行时静默 */
        } finally {
          minimizeBusy = false;
        }
      };
      document.addEventListener("visibilitychange", onVisibilityChange);

      renderTabs();
      renderBody();
      scheduleReminders();

      const dispose = () => {
        stopTimer();
        if (remindTimer) clearInterval(remindTimer);
        window.removeEventListener("dsh-pet-companion:settings", onExternalSettings);
        window.removeEventListener("keydown", onKeydown);
        document.removeEventListener("visibilitychange", onVisibilityChange);
        if (root && root.parentNode) root.parentNode.removeChild(root);
        root = null;
      };
      activeDispose = dispose;
      return dispose;
    }

    // ---------- 设置页 ----------
    function installSettingsSection(ctx, react) {
      const h = react.createElement;
      const ROW = { display: "flex", alignItems: "center", gap: "12px", padding: "10px 0", borderBottom: "1px solid rgba(128,128,128,.16)" };
      const TITLE = { fontWeight: 600, fontSize: "13px" };
      const DESC = { opacity: 0.66, fontSize: "12px", marginTop: "2px" };

      function Toggle({ on, label, onClick }) {
        return h(
          "button",
          {
            type: "button",
            role: "switch",
            "aria-checked": on ? "true" : "false",
            "aria-label": label,
            onClick,
            style: {
              minWidth: "52px",
              padding: "4px 10px",
              borderRadius: "999px",
              border: "1px solid rgba(128,160,200,.35)",
              cursor: "pointer",
              fontSize: "12px",
              background: on ? "rgba(90,180,255,.45)" : "rgba(128,128,128,.22)",
              color: "inherit",
            },
          },
          on ? "开" : "关",
        );
      }

      function SettingsPage() {
        const [settings, setSettings] = react.useState(readSettings());
        react.useEffect(() => {
          const onChange = (event) => setSettings(event && event.detail ? event.detail : readSettings());
          window.addEventListener("dsh-pet-companion:settings", onChange);
          return () => window.removeEventListener("dsh-pet-companion:settings", onChange);
        }, []);
        const apply = (patch) => setSettings(writeSettings(patch));
        const [petDisplay, setPetDisplayState] = react.useState(null);
        const [petMsg, setPetMsg] = react.useState("");
        react.useEffect(() => {
          let alive = true;
          petGetDisplay()
            .then((value) => {
              if (alive) setPetDisplayState(value || "both");
            })
            .catch(() => {
              if (alive) setPetMsg("桌宠没在运行，读不到当前显示状态");
            });
          return () => {
            alive = false;
          };
        }, []);
        const changeDisplay = (value) => {
          setPetDisplayState(value);
          setPetMsg("正在切换…");
          petSetDisplay(value)
            .then(() => setPetMsg("已切换（桌面侧会即时重载；网页端需刷新页面）"))
            .catch((error) => setPetMsg("切换失败：" + (error && error.message ? error.message : String(error))));
        };
        const features = settings.features || DEFAULT_SETTINGS.features;
        const isOn = (key) => features[key] !== false;
        const rows = [
          [
            "显示陪伴面板",
            "关掉后左下角面板完全隐藏，随时可以在这里打开；也可以按 Alt+P 快速隐藏/展开。",
            settings.panelEnabled !== false,
            () => apply({ panelEnabled: !(settings.panelEnabled !== false) }),
          ],
        ];
        for (const [key, title, desc] of FEATURE_ROWS) {
          rows.push([title, desc, isOn(key), () => apply({ features: { ...features, [key]: !isOn(key) } })]);
        }
        return h(
          "div",
          { style: { padding: "2px 0", maxWidth: "760px" } },
          h("h2", { style: { fontSize: "16px", margin: "0 0 6px" } }, "小鲸鲸陪伴"),
          h(
            "p",
            { style: { opacity: 0.7, fontSize: "12.5px", margin: "0 0 6px" } },
            "面板默认收成左下角的小胶囊（只显示番茄倒计时），点一下才展开，尽量不挡视线。本地功能（番茄钟 / 待办 / 提醒）0 token；讲解和辅导借桌宠的模型通道，标了「≈1 次模型调用」的才花。",
          ),
          ...rows.map(([title, desc, on, onToggle]) =>
            h(
              "div",
              { key: title, style: ROW },
              h("div", { style: { flex: 1 } }, h("div", { style: TITLE }, title), h("div", { style: DESC }, desc)),
              h(Toggle, { on, label: title, onClick: onToggle }),
            ),
          ),
          h("div", { style: { marginTop: "16px", marginBottom: "2px", fontWeight: 600, fontSize: "13px" } }, "桌宠显示"),
          h(
            "div",
            { style: ROW },
            h("div", { style: { flex: 1 } }, h("div", { style: TITLE }, "显示位置"), h("div", { style: DESC }, "桌面 = 独立小窗；DSH 页面 = 界面内嵌。改这里会立刻写入桌宠配置。")),
            h(
              "div",
              { style: { display: "flex", gap: "6px", flexWrap: "wrap" } },
              [
                ["both", "都显示"],
                ["desktop", "仅桌面"],
                ["web", "仅页面"],
                ["none", "隐藏"],
              ].map(([value, label]) =>
                h(
                  "button",
                  {
                    key: value,
                    type: "button",
                    "aria-pressed": (petDisplay || "") === value ? "true" : "false",
                    onClick: () => changeDisplay(value),
                    style: {
                      padding: "3px 9px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      fontSize: "12px",
                      border: "1px solid rgba(128,160,200,.35)",
                      background: (petDisplay || "") === value ? "rgba(90,180,255,.4)" : "transparent",
                      color: "inherit",
                    },
                  },
                  label,
                ),
              ),
            ),
          ),
          h(
            "div",
            { style: { ...ROW, borderBottom: "none" } },
            h("div", { style: { flex: 1 } }, h("div", { style: TITLE }, "DSH 最小化时隐藏桌宠"), h("div", { style: DESC }, "开启后：最小化窗口时自动收起桌面宠物，恢复窗口时再放回来。")),
            h(Toggle, {
              on: settings.minimizeHide === true,
              label: "DSH 最小化时隐藏桌宠",
              onClick: () => apply({ minimizeHide: !settings.minimizeHide }),
            }),
          ),
          petMsg ? h("div", { style: { opacity: 0.6, fontSize: "11.5px", marginTop: "4px" } }, petMsg) : null,
          h(
            "div",
            { style: { ...ROW, borderBottom: "none" } },
            h("div", { style: { flex: 1 } }, h("div", { style: TITLE }, "面板形态"), h("div", { style: DESC }, "完整面板 / 小胶囊 / 小圆点；默认是「胶囊」，最不惹眼。")),            h(
              "div",
              { style: { display: "flex", gap: "6px" } },
              [
                ["open", "完整"],
                ["pill", "胶囊"],
                ["dot", "圆点"],
              ].map(([value, label]) =>
                h(
                  "button",
                  {
                    key: value,
                    type: "button",
                    "aria-pressed": (settings.mode || "open") === value ? "true" : "false",
                    onClick: () => apply({ mode: value }),
                    style: {
                      padding: "3px 9px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      fontSize: "12px",
                      border: "1px solid rgba(128,160,200,.35)",
                      background: (settings.mode || "open") === value ? "rgba(90,180,255,.4)" : "transparent",
                      color: "inherit",
                    },
                  },
                  label,
                ),
              ),
            ),
          ),
          h(
            "div",
            { style: { ...ROW, borderBottom: "none" } },
            h("div", { style: { flex: 1 } }, h("div", { style: TITLE }, "今日专注"), h("div", { style: DESC }, "本地统计，清零不影响历史。" )),
            h(
              "button",
              {
                type: "button",
                onClick: () => apply({ stats: { date: todayKey(), sessions: 0, focusMin: 0, days: settings.stats?.days || {} } }),
                style: { padding: "3px 9px", borderRadius: "8px", cursor: "pointer", fontSize: "12px", border: "1px solid rgba(128,160,200,.35)", background: "transparent", color: "inherit" },
              },
              "清零今日",
            ),
          ),
          h(
            "p",
            { style: { opacity: 0.5, fontSize: "11.5px", marginTop: "8px" } },
            "插件：dsh-pet-companion v0.4 · 桌宠/语音插件不在时，讲解/辅导会提示降级，本地功能独立可用。",
          ),
        );
      }

      const seats = [
        ["settings.section", { name: "settings.section", id: "pet-companion", order: 52, label: () => "小鲸鲸陪伴" }, () => h(SettingsPage)],
        ["settings.plugins.tab", { name: "settings.plugins.tab", id: NS, order: 56, label: () => "小鲸鲸陪伴" }, () => h(SettingsPage)],
        [
          "plugins.bundle.config",
          { name: "plugins.bundle.config", key: NS },
          (owner) => (owner && owner.view === "summary" ? h("span", null, "陪伴面板 · 番茄钟 / 待办 / 提醒 / 讲解 / 辅导") : h(SettingsPage)),
        ],
      ];
      for (const [seat, descriptor, component] of seats) {
        try {
          ctx.slots.inject(seat, () => {
            try {
              return ctx.slots.register(descriptor, component);
            } catch (error) {
              console.warn("[dsh-pet-companion] settings seat unavailable:", seat, error);
              return () => {};
            }
          });
        } catch (error) {
          console.warn("[dsh-pet-companion] settings inject failed:", seat, error);
        }
      }
    }

    function apply(ctx) {
      installStyles();
      try {
        mountPanel(ctx);
      } catch (error) {
        console.warn("[dsh-pet-companion] mount failed:", error);
      }
      let react = null;
      try {
        react = require("react");
      } catch (error) {
        react = null;
      }
      if (react) {
        try {
          installSettingsSection(ctx, react);
        } catch (error) {
          console.warn("[dsh-pet-companion] settings section unavailable:", error);
        }
      }
      ctx.effect(() => {
        return () => {
          if (activeDispose) activeDispose();
          activeDispose = null;
          removeStyles();
        };
      }, "dsh-pet-companion: panel");
    }

    exports.apply = apply;
    exports.inject = ["slots"];
    exports.name = "pet-companion";
    return module.exports;
  },
});
