// 冒烟测试：用 jsdom 挂载 dsh-pet-companion 面板，点一遍所有标签，抓运行时错误。
//
// 运行：
//   cd tests
//   npm i jsdom        # 或 pnpm add jsdom
//   node smoke.mjs
//
// 退出码非 0 表示有错误（面板挂载失败 / 标签渲染抛异常 / 交互异常）。
import fs from "node:fs";
import { JSDOM } from "jsdom";

const bundlePath = process.env.COMPANION_BUNDLE
  ? process.env.COMPANION_BUNDLE
  : new URL("../lib/client.js", import.meta.url);
const code = fs.readFileSync(bundlePath, "utf8");

const dom = new JSDOM("<!doctype html><html><head></head><body></body></html>", {
  url: "http://127.0.0.1:19387/",
  pretendToBeVisual: true,
});
const { window } = dom;

const problems = [];
const origError = console.error;
console.error = (...a) => {
  problems.push(a.map(String).join(" "));
  origError(...a);
};

globalThis.window = window;
globalThis.document = window.document;
globalThis.localStorage = window.localStorage;
globalThis.CustomEvent = window.CustomEvent;
globalThis.fetch = async () => ({ ok: false, status: 404, text: async () => "{}", json: async () => ({}) });
window.fetch = globalThis.fetch;
globalThis.AudioContext = function () {};

let exportsObj = null;
window.__ModuleLoader__ = {
  load({ id, factory }) {
    exportsObj = factory((name) => {
      throw new Error("react not needed for panel test: " + name);
    });
  },
};

const run = (codeText) => {
  const fn = new Function(
    "window", "document", "localStorage", "CustomEvent", "fetch", "navigator", "location", "AudioContext", "console",
    codeText,
  );
  fn(window, window.document, window.localStorage, window.CustomEvent, globalThis.fetch, window.navigator, window.location, globalThis.AudioContext, console);
};

try {
  run(code);
} catch (error) {
  console.log("BUNDLE LOAD ERROR:", error && error.stack);
  process.exit(1);
}

const ctx = {
  slots: { inject() {}, register() { return () => {}; } },
  effect(fn) { try { fn(); } catch (e) { problems.push("effect: " + e.message); } },
};

try {
  exportsObj.apply(ctx);
} catch (error) {
  problems.push("apply: " + (error && error.message));
}

const $ = (sel) => window.document.querySelector(sel);
const $$ = (sel) => [...window.document.querySelectorAll(sel)];
const click = (el) => el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

if (!window.document.querySelector(".pc-root")) {
  problems.push("panel not mounted");
}
console.log("panel mounted:", !!window.document.querySelector(".pc-root"));
console.log("clock:", ($(".pc-clock") || {}).textContent);

// 开始 / 暂停
const startBtn = $$(".pc-btn").find((b) => /开始/.test(b.textContent || ""));
if (startBtn) {
  click(startBtn);
  await sleep(1200);
  const clock = ($(".pc-clock") || {}).textContent;
  console.log("clock after start:", clock);
  if (clock === "25:00" || !clock) problems.push("timer did not tick");
  const pauseBtn = $$(".pc-btn").find((b) => /暂停/.test(b.textContent || ""));
  if (pauseBtn) click(pauseBtn);
  else problems.push("pause button missing");
} else {
  problems.push("start button missing");
}

// 所有标签都要能渲染
for (const label of ["待办", "提醒", "讲解", "辅导", "桌宠", "专注"]) {
  const tab = $$(".pc-tab").find((b) => (b.textContent || "").includes(label));
  if (!tab) {
    problems.push("tab missing: " + label);
    continue;
  }
  try {
    click(tab);
    const text = (($(".pc-body") || {}).textContent || "").trim();
    if (!text) problems.push("tab rendered empty: " + label);
    console.log("tab", label, "ok:", text.slice(0, 24).replace(/\s+/g, " "));
  } catch (error) {
    problems.push("tab " + label + " threw: " + (error && error.message));
  }
}

// 三种专注模式切换
for (const label of ["正计时", "倒计时", "番茄钟"]) {
  const chip = $$(".pc-preset").find((c) => /正计时|倒计时|番茄钟/.test(c.textContent || "") && (c.textContent || "").includes(label));
  if (chip) click(chip);
  else problems.push("mode chip missing: " + label);
}
console.log("mode switch done, clock:", ($(".pc-clock") || {}).textContent);

// 胶囊 / 圆点
const minBtn = window.document.querySelector(".pc-hbtn");
if (minBtn) click(minBtn);
console.log("mode after minimize:", ($(".pc-root") || {}).getAttribute("data-mode"));

console.log("=== problems ===");
problems.forEach((p) => console.log("PROBLEM:", p.slice(0, 300)));
console.log(problems.length === 0 ? "SMOKE TEST PASSED" : "SMOKE TEST FAILED");
process.exit(problems.length === 0 ? 0 : 1);
