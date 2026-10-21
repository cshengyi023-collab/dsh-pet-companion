# -*- coding: utf-8 -*-
"""桌宠控制台 —— 一个带按钮的小窗口：说话 / 动作 / 试音 / 显示位置 / 读书。
不需要命令行知识，双击「桌宠控制台.cmd」即可打开。
试音：在左侧选人物，右侧自动合成并播放该人物的试读。
"""
import json
import os
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import filedialog, messagebox, ttk

BASE = "http://127.0.0.1:19387/dsh-pet-7340"
TTS = "http://127.0.0.1:19387/plugins/xiaomi-mimo-tts/synthesize"
PET = "main"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "试音缓存")
os.makedirs(CACHE, exist_ok=True)

SAMPLE = "你好呀，今天也要一起加油哦～"

WHALE = (
    "A bright, youthful female voice around 16-20. Sweet, soft and slightly nasal, with a lazy yet cheerful energy. "
    "Sentence endings often lift playfully. Sounds a bit tsundere on the surface, but warm, affectionate and mildly "
    "possessive underneath. Normally light and lively; turns earnest yet soft when serious. Speaks fairly quickly "
    "with natural pauses. Occasionally draws out a word when being stubborn, always with happy, playful energy."
)

# 预设人物（小米内置音色）
PRESET_VOICES = [
    ("冰糖", "活泼少女"), ("茉莉", "知性女声"), ("苏打", "阳光少年"), ("白桦", "成熟男声"),
    ("Mia", "Lively girl"), ("Chloe", "Witty grace"), ("Milo", "Sunny boy"), ("Dean", "Steady gentle"),
]
# 设计人物（音色设计预设）
DESIGN_VOICES = [
    ("萝莉·定稿", "二次元偏尖", "二次元动漫/游戏配音风格，8到12岁小女孩的萝莉音，音调偏高、声线尖细清脆，带夸张的二次元演技感；语速偏快、吐字干脆，尾音利落不拖长，不撒娇、不黏糊；带小恶魔式的坏笑，生气时音量拔高、语气冲。"),
    ("萝莉A·尖锐傲娇", "偏高偏尖", "二次元动漫/游戏配音风格，8到12岁小女孩的萝莉音，音调偏高、声线尖细清脆，带夸张的二次元演技感，不是温柔系；语速偏快，句尾常上扬，生气时音量拔高、带赌气的哼哼，撒娇带点坏心眼。"),
    ("萝莉B·小恶魔", "坏笑拖腔", "二次元游戏配音风，9到13岁小恶魔系萝莉音，高音偏尖、亮而利，带调皮坏笑和黏糊的拖腔，语速快；挑衅时一点不客气，故意拖长尾音，笑声清脆。"),
    ("小孩A·奶音4岁", "软糯奶音", "4到6岁小女孩，奶声奶气，声音软糯清亮，咬字略含糊，撒娇尾音上扬，语速偏快，情绪外露；生气时会拉长音、跺脚式地哼哼抗议。"),
    ("鲸鱼娘·旧版", "清甜灵动", WHALE),
    ("温柔陪伴", "张子苜", "年轻女性16-22岁,声线柔软细腻,低饱和带微微暖意,标准普通话,温柔亲密的邻家风格,语速偏慢,语调轻柔连贯,气息自然流畅,安静私密陪伴场景。"),
    ("邻家甜声", "陈念安", "年轻女性20-25岁,柔润清甜带撒娇感,普通话,清澈明亮的少女音,轻松温柔的亲近感,轻缓带温柔,中等偏快语速中等音量,生活分享场景。"),
    ("ASMR低语", "沈听澜", "女性18-20岁,轻柔耳语带微弱气息,普通话,声线细腻清晰,私密温柔感,安静平和带轻柔低语,语速缓慢音量很轻,私密低语场景。"),
    ("科技解说", "周砚川", "成年男性25-35岁,清晰利落中音、干净偏冷,标准普通话,精准干练的都市精英感,语速中等偏快、语调平稳,理性简洁、逻辑感强,现代资讯播报或商业讲解场景。"),
]
ANIMS = [
    "点击回应-元气挥手", "点击回应-害羞惊讶", "点击回应-开心跃动", "可爱宅舞", "优雅女仆舞",
    "东张西望", "原地小憩沉眠", "哈欠连天", "超大伸懒腰", "悠闲哼歌", "写代码", "吃白饭",
    "大口吃零食", "涮火锅", "玩水枪", "小提琴演奏", "蓝鲸现世", "打瞌睡被惊醒", "照镜子", "跑步",
]


def jreq(method, url, body=None, timeout=180):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def pet_say(text, duration=10000):
    return jreq("POST", f"{BASE}/broadcast?pet={PET}", {"text": text, "duration": duration})


def pet_anim(name):
    return jreq("POST", f"{BASE}/anim?pet={PET}", {"name": name})


def get_state():
    st, body = jreq("GET", f"{BASE}/state")
    return json.loads(body) if st == 200 else None


def set_display(mode):
    st, body = jreq("GET", f"{BASE}/config")
    cfg = json.loads(body)
    entry = cfg["main"]
    keep = ["name", "id", "size", "balanceEnabled", "display", "position",
            "whisperEnabled", "workStatusEnabled", "fixedEnabled"]
    pets = []
    for p in entry["pets"]:
        q = {k: p[k] for k in keep if k in p}
        if q.get("id") == PET:
            q["display"] = mode
        pets.append(q)
    return jreq("PUT", f"{BASE}/config", {"pets": pets})


def synth(text, preset=None, design=None):
    body = {"text": text, "format": "mp3"}
    if preset:
        body["model"] = "mimo-v2.5-tts"
        body["voice"] = preset
    elif design:
        body["model"] = "mimo-v2.5-tts-voicedesign"
        body["voiceDesignPrompt"] = design
    st, data = jreq("POST", TTS, body)
    if st != 200 or b"ID3" not in data[:3] and not data[:1] == b"\xff":
        raise RuntimeError(f"合成失败 HTTP {st}: {data[:200]!r}")
    return data


_mci_lock = threading.Lock()


def play_mp3(path):
    """用 Windows MCI 播放 mp3（后台线程，阻塞到播完）。"""
    with _mci_lock:
        import ctypes
        mci = ctypes.windll.winmm.mciSendStringW
        alias = "petconsole"
        mci(f'close {alias}', None, 0, 0)
        err = mci(f'open "{path}" type mpegvideo alias {alias}', None, 0, 0)
        if err:
            raise RuntimeError(f"播放失败 MCI {err}")
        try:
            mci(f'play {alias} wait', None, 0, 0)
        finally:
            mci(f'close {alias}', None, 0, 0)


class App:
    def __init__(self, root):
        self.root = root
        root.title("桌宠控制台 · 蓝色大肥鱼")
        root.geometry("560x520")
        root.attributes("-topmost", True)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.nb = nb

        # ---- 说话 ----
        tab = ttk.Frame(nb)
        nb.add(tab, text="💬 说话")
        self.say_var = tk.StringVar(value="我在这儿呢～")
        ttk.Entry(tab, textvariable=self.say_var).pack(fill="x", padx=10, pady=(12, 6))
        row = ttk.Frame(tab)
        row.pack(fill="x", padx=10)
        ttk.Button(row, text="让她说这句", command=self.do_say).pack(side="left")
        ttk.Button(row, text="碎碎念一句", command=self.do_whisper).pack(side="left", padx=6)
        quick = ttk.Frame(tab)
        quick.pack(fill="x", padx=10, pady=8)
        for text in ["你好呀", "我回来了", "该喝水啦", "加油！", "陪我聊会儿"]:
            ttk.Button(quick, text=text, command=lambda t=text: self.send_say(t)).pack(side="left", padx=2)

        # ---- 动作 ----
        tab = ttk.Frame(nb)
        nb.add(tab, text="🎬 动作")
        self.anim_var = tk.StringVar(value=ANIMS[0])
        ttk.Combobox(tab, textvariable=self.anim_var, values=ANIMS, state="readonly").pack(fill="x", padx=10, pady=(12, 6))
        ttk.Button(tab, text="播放这个动作", command=self.do_anim).pack(anchor="w", padx=10)
        grid = ttk.Frame(tab)
        grid.pack(fill="x", padx=10, pady=8)
        for i, name in enumerate(["点击回应-元气挥手", "点击回应-害羞惊讶", "可爱宅舞", "原地小憩沉眠",
                                  "超大伸懒腰", "东张西望", "写代码", "蓝鲸现世"]):
            ttk.Button(grid, text=name.replace("点击回应-", ""), command=lambda n=name: self.send_anim(n)).grid(row=i // 4, column=i % 4, padx=2, pady=2, sticky="ew")
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        # ---- 试音 ----
        tab = ttk.Frame(nb)
        nb.add(tab, text="🎧 试音")
        left = ttk.Frame(tab)
        left.pack(side="left", fill="both", expand=False, padx=(10, 4), pady=10)
        ttk.Label(left, text="预设人物").pack(anchor="w")
        self.voice_list = tk.Listbox(left, height=8, width=14, exportselection=False)
        for name, summary in PRESET_VOICES:
            self.voice_list.insert("end", f"{name}（{summary}）")
        self.voice_list.pack()
        ttk.Label(left, text="设计人物").pack(anchor="w", pady=(8, 0))
        self.design_list = tk.Listbox(left, height=7, width=14, exportselection=False)
        for name, summary, _ in DESIGN_VOICES:
            self.design_list.insert("end", f"{name}（{summary}）")
        self.design_list.pack()
        right = ttk.Frame(tab)
        right.pack(side="left", fill="both", expand=True, padx=4, pady=10)
        ttk.Label(right, text="选一个人物，自动播放试读").pack(anchor="w")
        self.preview_msg = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.preview_msg, foreground="#666").pack(anchor="w", pady=4)
        ttk.Button(right, text="重播上一次", command=self.replay_preview).pack(anchor="w", pady=4)
        ttk.Button(right, text="打开试音缓存文件夹", command=self.open_cache).pack(anchor="w")
        self.voice_list.bind("<<ListboxSelect>>", lambda e: self.select_voice("preset"))
        self.design_list.bind("<<ListboxSelect>>", lambda e: self.select_voice("design"))
        self.last_preview = None

        # ---- 设置 ----
        tab = ttk.Frame(nb)
        nb.add(tab, text="⚙ 设置")
        ttk.Label(tab, text="显示位置").pack(anchor="w", padx=10, pady=(12, 4))
        row = ttk.Frame(tab)
        row.pack(fill="x", padx=10)
        for label, mode in [("仅桌面", "desktop"), ("仅 DSH 界面", "web"), ("都显示", "both"), ("都不显示", "none")]:
            ttk.Button(row, text=label, command=lambda m=mode: self.do_display(m)).pack(side="left", padx=2)
        ttk.Button(tab, text="打开朗读台（读书/授课）", command=self.open_reader).pack(anchor="w", padx=10, pady=(16, 4))
        ttk.Button(tab, text="打开陪伴服务配置", command=self.open_companion).pack(anchor="w", padx=10, pady=4)
        ttk.Button(tab, text="刷新状态", command=self.refresh_status).pack(anchor="w", padx=10, pady=4)

        # ---- 状态栏 ----
        self.status = tk.StringVar(value="就绪")
        ttk.Label(root, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", side="bottom")
        self.refresh_status()

    # ---- 通用 ----
    def run_bg(self, fn, ok_msg=None):
        def worker():
            try:
                fn()
                if ok_msg:
                    self.root.after(0, lambda: self.status.set(ok_msg))
            except Exception as e:
                self.root.after(0, lambda: self.status.set(f"失败：{e}"))
        threading.Thread(target=worker, daemon=True).start()

    def refresh_status(self):
        def work():
            st = get_state()
            if not st:
                self.root.after(0, lambda: self.status.set("连不上 DSH（桌宠未运行？）"))
                return
            p = st.get("pets", {}).get(PET, {})
            bubble = ((p.get("say") or {}).get("data") or {}).get("text") or "（无气泡）"
            bal = (st.get("sections", {}).get("balance", {}) or {}).get("data") or {}
            money = ""
            if bal.get("ok"):
                d = bal.get("data") or {}
                money = f" | 余额 {d.get('currency', '')}{d.get('total', '')}"
            self.root.after(0, lambda: self.status.set(f"她：{bubble}{money}"))
        threading.Thread(target=work, daemon=True).start()

    # ---- 说话/动作 ----
    def send_say(self, text):
        self.run_bg(lambda: pet_say(text), f"已让她说：{text}")

    def do_say(self):
        self.send_say(self.say_var.get().strip() or "你好呀")

    def do_whisper(self):
        def work():
            st, body = jreq("POST", f"{BASE}/whisper?pet={PET}")
            data = json.loads(body) if body.startswith(b"{") else {}
            self.root.after(0, lambda: self.status.set(f"碎碎念：{data.get('text', body[:80])}"))
        threading.Thread(target=work, daemon=True).start()

    def send_anim(self, name):
        self.run_bg(lambda: pet_anim(name), f"已播放：{name}")

    def do_anim(self):
        self.send_anim(self.anim_var.get())

    # ---- 试音 ----
    def select_voice(self, kind):
        if kind == "preset":
            idx = self.voice_list.curselection()
            if not idx:
                return
            self.design_list.selection_clear(0, "end")
            name, summary = PRESET_VOICES[idx[0]]
            self.preview(f"{name}-{summary}", preset=name)
        else:
            idx = self.design_list.curselection()
            if not idx:
                return
            self.voice_list.selection_clear(0, "end")
            name, summary, prompt = DESIGN_VOICES[idx[0]]
            self.preview(f"{name}-{summary}", design=prompt)

    def preview(self, key, preset=None, design=None):
        cache_path = os.path.join(CACHE, f"{key}.mp3")
        self.last_preview = cache_path
        self.preview_msg.set(f"正在准备：{key} …")

        def work():
            try:
                if not os.path.exists(cache_path):
                    data = synth(SAMPLE, preset=preset, design=design)
                    with open(cache_path, "wb") as f:
                        f.write(data)
                self.root.after(0, lambda: self.preview_msg.set(f"试读：{key}（{SAMPLE}）"))
                play_mp3(cache_path)
            except Exception as e:
                self.root.after(0, lambda: self.preview_msg.set(f"试音失败：{e}"))
        threading.Thread(target=work, daemon=True).start()

    def replay_preview(self):
        if self.last_preview and os.path.exists(self.last_preview):
            threading.Thread(target=lambda: play_mp3(self.last_preview), daemon=True).start()

    def open_cache(self):
        os.startfile(CACHE)

    # ---- 设置 ----
    def do_display(self, mode):
        def work():
            st, body = set_display(mode)
            msg = "已切换（网页端如未变化请按 Ctrl+R 刷新）" if st == 200 else f"失败：{body[:120]}"
            self.root.after(0, lambda: self.status.set(msg))
        threading.Thread(target=work, daemon=True).start()

    def open_reader(self):
        os.startfile(r"D:\ai工作库\朗读台\朗读台.cmd")

    def open_companion(self):
        os.startfile(r"D:\ai工作库\陪伴服务\陪伴配置.cmd")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
