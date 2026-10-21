# -*- coding: utf-8 -*-
"""让「气泡播报」也支持音色设计（用户选的音色）：
原实现里播报路径强行用预设模型 mimo-v2.5-tts，导致选什么音色设计都没用；
这里在非实时模型（voicedesign）时改走非流式完整音频 + <audio> 播放。
幂等；插件升级后重跑。"""
import os, shutil

CLIENT = r"C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-xiaomi-tts\lib\client.js"
MARK = "[voicedesign-announce]"

with open(CLIENT, encoding="utf-8") as f:
    src = f.read()

if MARK in src:
    print("already patched; skip")
    raise SystemExit(0)

bak = CLIENT + ".orig-voicedesign"
if not os.path.exists(bak):
    shutil.copyfile(CLIENT, bak)
    print("backup ->", bak)

old = '''\t\t\t\tawait streamPcmAudio(normalized, controller.signal, async (pcm) => {
\t\t\t\t\tif (this.disposed || controller.signal.aborted || generation !== this.generation) return;
\t\t\t\t\trecording.append(pcm);
\t\t\t\t\tawait this.audio.enqueue(pcm);
\t\t\t\t}, ttsSelection({
\t\t\t\t\t...settings,
\t\t\t\t\tmodel: "mimo-v2.5-tts"
\t\t\t\t}));'''

new = '''\t\t\t\t// [voicedesign-announce] 音色设计（非实时模型）不支持 PCM 流式：
\t\t\t\t// 改走非流式完整音频 + <audio> 播放，这样气泡播报也能用上用户选的音色。
\t\t\t\tif (!supportsRealtimeTts(settings)) {
\t\t\t\t\tconst response = await fetch(hostRoute(TTS_ROUTE), {
\t\t\t\t\t\tmethod: "POST",
\t\t\t\t\t\theaders: { "content-type": "application/json" },
\t\t\t\t\t\tbody: JSON.stringify({ ...ttsSelection(settings), text: normalized, format: "mp3" }),
\t\t\t\t\t\tsignal: controller.signal
\t\t\t\t\t});
\t\t\t\t\tif (!response.ok) throw new Error("complete-audio-" + response.status);
\t\t\t\t\tconst blob = await response.blob();
\t\t\t\t\tif (this.disposed || controller.signal.aborted || generation !== this.generation) return;
\t\t\t\t\tconst url = URL.createObjectURL(blob);
\t\t\t\t\tthis.completeUrl = url;
\t\t\t\t\tconst audio = new Audio(url);
\t\t\t\t\taudio.volume = Math.max(0, Math.min(1, settings.voiceVolume));
\t\t\t\t\taudio.playbackRate = Math.max(.5, Math.min(2, settings.voiceRate || 1));
\t\t\t\t\tthis.completeAudio = audio;
\t\t\t\t\tawait new Promise((resolve, reject) => {
\t\t\t\t\t\tconst cleanup = () => {
\t\t\t\t\t\t\tif (this.completeAudio === audio) this.completeAudio = null;
\t\t\t\t\t\t\tif (this.completeUrl === url) this.completeUrl = null;
\t\t\t\t\t\t\ttry { URL.revokeObjectURL(url); } catch (error) {}
\t\t\t\t\t\t};
\t\t\t\t\t\taudio.onended = () => { cleanup(); resolve(); };
\t\t\t\t\t\taudio.onerror = () => { cleanup(); reject(new Error("complete-audio-playback")); };
\t\t\t\t\t\tcontroller.signal.addEventListener("abort", () => { try { audio.pause(); } catch (error) {} cleanup(); resolve(); }, { once: true });
\t\t\t\t\t\tconst p = audio.play();
\t\t\t\t\t\tif (p && typeof p.catch === "function") p.catch((error) => { cleanup(); reject(error); });
\t\t\t\t\t});
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t\tawait streamPcmAudio(normalized, controller.signal, async (pcm) => {
\t\t\t\t\tif (this.disposed || controller.signal.aborted || generation !== this.generation) return;
\t\t\t\t\trecording.append(pcm);
\t\t\t\t\tawait this.audio.enqueue(pcm);
\t\t\t\t}, ttsSelection({
\t\t\t\t\t...settings,
\t\t\t\t\tmodel: "mimo-v2.5-tts"
\t\t\t\t}));'''

if old not in src:
    raise SystemExit("锚点没找到（版本可能变了）")
src = src.replace(old, new, 1)

# stop() 里补上完整音频的停止
old_stop = '''\t\t\tthis.generation += 1;
\t\t\tthis.request?.abort();
\t\t\tthis.request = null;
\t\t\tthis.audio.stop();'''
new_stop = '''\t\t\tthis.generation += 1;
\t\t\tthis.request?.abort();
\t\t\tthis.request = null;
\t\t\tthis.audio.stop();
\t\t\ttry {
\t\t\t\tif (this.completeAudio) { this.completeAudio.pause(); this.completeAudio = null; }
\t\t\t\tif (this.completeUrl) { URL.revokeObjectURL(this.completeUrl); this.completeUrl = null; }
\t\t\t} catch (error) {}'''
if old_stop not in src:
    raise SystemExit("stop() 锚点没找到")
src = src.replace(old_stop, new_stop, 1)

with open(CLIENT, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("patched voicedesign announcement playback")
