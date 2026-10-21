# -*- coding: utf-8 -*-
"""两件事（幂等）：
A) 给 dsh-xiaomi-tts 的 API Key 输入框加「显示/隐藏密钥」眼睛按钮（输入时能核对，不再只能看到圆点）
B) 合并 cordis.patch.yml 里重复的 xiaomi-mimo-tts 配置条目（保留用户已保存的 key / 偏好 + 气泡播报配置）
"""
import os, re, shutil, sys

PROFILE = r"C:\Users\chenshengyi\.dsh\profiles\desktop"
PATCH = os.path.join(PROFILE, "cordis.patch.yml")
CLIENT = os.path.join(PROFILE, "node_modules", "dsh-xiaomi-tts", "lib", "client.js")

# ============ A) 眼睛按钮补丁 ============
MARKER = "[key-reveal]"

def patch_client():
    bak = CLIENT + ".orig-key-reveal"
    # 有备份就以备份为准（幂等 + 可从半失败状态恢复）
    if os.path.exists(bak):
        with open(bak, encoding="utf-8") as f:
            src = f.read()
        print("A) restored from backup:", bak)
    else:
        with open(CLIENT, encoding="utf-8") as f:
            src = f.read()
        shutil.copyfile(CLIENT, bak)
        print("A) backup ->", bak)
    if MARKER in src:
        print("A) client.js: backup already patched ?! skip")
        return

    # 1) 增加 revealed 状态
    state_anchor = "\tconst [bubbleKey, setBubbleKey] = (0, react.useState)(() => randomCopyKey(API_KEY_IDLE_COPY_KEYS));"
    if src.count(state_anchor) != 1:
        raise SystemExit("anchor(state) not unique: %d" % src.count(state_anchor))
    src = src.replace(state_anchor, state_anchor + "\n\tconst [revealed, setRevealed] = (0, react.useState)(false);")

    # 2) 容器加 position:relative，眼睛按钮绝对定位才稳
    container_anchor = '\t\t\t\tclassName: "xmimo-tts-api-key-input",'
    if src.count(container_anchor) != 1:
        raise SystemExit("anchor(container) not unique: %d" % src.count(container_anchor))
    src = src.replace(container_anchor, container_anchor + '\n\t\t\t\tstyle: { position: "relative" },')

    # 3) 输入框类型可切换 + 右侧留出按钮空间
    type_anchor = '\t\t\t\t\t\ttype: "password",'
    if src.count(type_anchor) != 1:
        raise SystemExit("anchor(type) not unique: %d" % src.count(type_anchor))
    src = src.replace(type_anchor, '\t\t\t\t\t\ttype: revealed ? "text" : "password",')

    style_anchor = '\t\t\t\t\t\tstyle: { padding: "0 var(--xmimo-ui-space-4)" }\n\t\t\t\t\t}),'
    if src.count(style_anchor) != 1:
        raise SystemExit("anchor(style) not unique: %d" % src.count(style_anchor))

    eye_jsx = '''\t\t\t\t\t\tstyle: { padding: "0 var(--xmimo-ui-space-4)", paddingRight: "34px" }
\t\t\t\t\t}),
\t\t\t\t\t/* [key-reveal] 显示/隐藏 API Key —— 本补丁由 dsh-pet-control/key-reveal 维护 */
\t\t\t\t\t(0, react_jsx_runtime.jsx)("button", {
\t\t\t\t\t\ttype: "button",
\t\t\t\t\t\t"aria-label": revealed ? "隐藏 API Key" : "显示 API Key",
\t\t\t\t\t\ttitle: revealed ? "隐藏 API Key" : "显示 API Key",
\t\t\t\t\t\t"aria-pressed": revealed,
\t\t\t\t\t\tdisabled: !writable,
\t\t\t\t\t\tonClick: (event) => {
\t\t\t\t\t\t\tevent.preventDefault();
\t\t\t\t\t\t\tevent.stopPropagation();
\t\t\t\t\t\t\tsetRevealed((current) => !current);
\t\t\t\t\t\t},
\t\t\t\t\t\tstyle: { position: "absolute", right: "8px", top: "50%", transform: "translateY(-50%)", display: "inline-flex", alignItems: "center", justifyContent: "center", width: "26px", height: "26px", padding: "0", border: "none", borderRadius: "6px", background: "transparent", color: "inherit", cursor: "pointer", opacity: 0.72 },
\t\t\t\t\t\tchildren: (0, react_jsx_runtime.jsx)("svg", {
\t\t\t\t\t\t\twidth: "16",
\t\t\t\t\t\t\theight: "16",
\t\t\t\t\t\t\tviewBox: "0 0 24 24",
\t\t\t\t\t\t\tfill: "none",
\t\t\t\t\t\t\tstroke: "currentColor",
\t\t\t\t\t\t\tstrokeWidth: "1.8",
\t\t\t\t\t\t\tstrokeLinecap: "round",
\t\t\t\t\t\t\tstrokeLinejoin: "round",
\t\t\t\t\t\t\t"aria-hidden": "true",
\t\t\t\t\t\t\tchildren: revealed
\t\t\t\t\t\t\t\t? (0, react_jsx_runtime.jsx)("path", { d: "M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24M1 1l22 22" })
\t\t\t\t\t\t\t\t: (0, react_jsx_runtime.jsxs)(react_jsx_runtime.Fragment, { children: [
\t\t\t\t\t\t\t\t\t(0, react_jsx_runtime.jsx)("path", { d: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" }),
\t\t\t\t\t\t\t\t\t(0, react_jsx_runtime.jsx)("circle", { cx: "12", cy: "12", r: "3" })
\t\t\t\t\t\t\t\t] })
\t\t\t\t\t\t})
\t\t\t\t\t}),'''
    src = src.replace(style_anchor, eye_jsx)

    with open(CLIENT, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("A) client.js patched (eye toggle)")

# ============ B) 合并重复的 xiaomi-mimo-tts 配置 ============
def consolidate_patch():
    with open(PATCH, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")

    idx1 = next((i for i, l in enumerate(lines) if l.strip() == "- id: xiaomi-mimo-tts"), None)
    idx2 = next((i for i, l in enumerate(lines) if l.strip() == "- id: preset-whale-girl"), None)
    if idx1 is None:
        print("B) no xiaomi entry, skip")
        return
    # 取最后一个 apiKey 值（用户已保存的那个）
    keys = re.findall(r"^\s*apiKey:\s*(\S.*)$", text, re.M)
    key = keys[-1].strip().strip('"').strip("'") if keys else ""
    if not key or key.startswith("<"):
        key = ""
    # 如果已经有唯一一条合并好的条目，跳过
    if text.count("- id: xiaomi-mimo-tts") == 1 and "# [tts-consolidated]" in text:
        print("B) patch already consolidated, skip")
        return

    bak = PATCH + ".bak-consolidate"
    if not os.path.exists(bak):
        shutil.copyfile(PATCH, bak)
        print("B) backup ->", bak)

    head = "\n".join(lines[:idx1]).rstrip("\n") + "\n"

    if idx2 is not None:
        # preset-whale-girl 条目（保留用户启用状态），到下一个 top-level 条目/注释前
        end = len(lines)
        for j in range(idx2 + 1, len(lines)):
            if lines[j].startswith("- ") or lines[j].startswith("#"):
                end = j
                break
        preset_block = "\n".join(lines[idx2:end]).rstrip("\n") + "\n"
    else:
        preset_block = ""

    WHALE = ("A bright, youthful female voice around 16-20. Sweet, soft and slightly nasal, with a lazy yet cheerful energy. "
             "Sentence endings often lift playfully. Sounds a bit tsundere on the surface, but warm, affectionate and mildly "
             "possessive underneath. Normally light and lively; turns earnest yet soft when serious. Speaks fairly quickly "
             "with natural pauses. Occasionally draws out a word when being stubborn, always with happy, playful energy.")

    merged = f"""# [tts-consolidated] 语音朗读配置（合并了多份重复条目；由 dsh-pet-control/key-reveal 维护）
# 说明：announcementSources 里的 dsh-pet 负责把桌宠气泡念出来；没有可用 key 时自动退回浏览器本地语音。
- id: xiaomi-mimo-tts
  name: dsh-xiaomi-tts
  config:
    enabled: true
    provider: xiaomi
    apiKey: "{key}"
    baseURL: "https://api.xiaomimimo.com/v1"
    model: mimo-v2.5-tts-voicedesign
    voice: "茉莉"
    voiceDesignPrompt: "{WHALE}"
    voiceDesignCustomPrompt: "{WHALE}"
    presetStylePrompt: "使用清晰、自然、准确的声音朗读，语速适中，停顿自然，语气平和克制，避免夸张表达。"
    instruction: "用自然的四川话口音说这段话，保持日常聊天的感觉。"
    format: pcm
    announcementSources:
      - dsh-pet
      - question-titles
    localSpeechMode: auto
    localVoiceURI: "Microsoft Kangkang - Chinese (Simplified, PRC)"
    autoPlay: false
    readScope: smart
    voiceVolume: 1
    voiceRate: 1
    soundEnabled: true
    soundVolume: 0.36
    soundPack: soft
    taskSounds: true
    clickSounds: true
    maxTextLength: 12000
    requestTimeoutMs: 120000
    maxMp3AudioBytes: 33554432
    maxWavAudioBytes: 134217728
    maxPausedPcmBytes: 33554432
"""

    new_text = head + merged + "\n" + preset_block
    with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    print("B) patch consolidated; apiKey preserved:", bool(key), "| preset block kept:", bool(preset_block))

if __name__ == "__main__":
    patch_client()
    consolidate_patch()
    print("DONE")
