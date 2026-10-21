/* ============================================================
 * dsh-pet 桌面 Helper 音效补丁 v2 —— 与「界面右下角小鲸鱼挂件」同款音效
 *   - press.mp3  / release.mp3 直接取自 dsh-whale-widget 的「小黄鸭」预设
 *     （assets/Ya1.mp3 / Ya2.mp3）——按下 / 松开各一声，和挂件手感一致。
 *   - 开关：右键她 →「音效：开/关」；状态存在本窗口 localStorage。
 *   - 备注：dsh-pet 插件升级会覆盖，重跑 apply-sound-patch.ps1 即可。
 * ============================================================ */
(function () {
  'use strict';
  var KEY = 'dsh-pet-helper:sound-enabled';
  var VOLUME = 0.85;
  var enabled = true;
  try {
    var saved = localStorage.getItem(KEY);
    if (saved === '0') enabled = false;
    if (saved === '1') enabled = true;
  } catch (e) {}

  var pressEl = null;
  var releaseEl = null;

  function make(name) {
    var a = new Audio('./sounds/' + name + '.mp3');
    a.preload = 'auto';
    a.volume = VOLUME;
    return a;
  }

  function playEl(el) {
    if (!el) return;
    try {
      el.currentTime = 0;
      var p = el.play();
      if (p && typeof p.catch === 'function') p.catch(function () {});
    } catch (e) {}
  }

  function getPress() {
    if (!pressEl) { try { pressEl = make('press'); } catch (e) { pressEl = null; } }
    return pressEl;
  }
  function getRelease() {
    if (!releaseEl) { try { releaseEl = make('release'); } catch (e) { releaseEl = null; } }
    return releaseEl;
  }

  // 预加载：第一次交互前把两个音效读进来（失败静默）
  try { getPress(); } catch (e) {}
  try { getRelease(); } catch (e) {}

  window.PetSound = {
    play: function () {
      if (!enabled) return;
      playEl(getPress());
    },
    release: function () {
      if (!enabled) return;
      playEl(getRelease());
    },
    enabled: function () { return enabled; },
    toggle: function () {
      enabled = !enabled;
      try { localStorage.setItem(KEY, enabled ? '1' : '0'); } catch (e) {}
      if (enabled) playEl(getPress());
      return enabled;
    },
    setEnabled: function (v) {
      enabled = !!v;
      try { localStorage.setItem(KEY, enabled ? '1' : '0'); } catch (e) {}
    }
  };
})();
