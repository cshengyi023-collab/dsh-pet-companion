# -*- coding: utf-8 -*-
"""朗读台 —— 用「鲸鱼娘」音色把书/讲义/任意文本读给你听。

原理：调用本机 DSH 里 dsh-xiaomi-tts 插件的非流式合成接口
  POST http://127.0.0.1:19387/plugins/xiaomi-mimo-tts/synthesize
  body: { text, model: "mimo-v2.5-tts-voicedesign", voiceDesignPrompt, speechInstruction, format: "mp3" }
逐段合成后拼成一个 mp3，输出到本目录 output/。

用法：
  python readaloud.py "D:\\books\\三体.txt"            # 合成
  python readaloud.py "D:\\books\\三体.txt" --play     # 合成后自动打开
  python readaloud.py --text "今天讲机器学习中的梯度下降。" --play
  python readaloud.py "讲义.md" --max-chars 260 --out "D:\\out.mp3"

合规提示：只朗读你有权使用的内容（自己的文档、公版书、已获授权的教材）。
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:19387/plugins/xiaomi-mimo-tts"
# 「小鲸鲸」定稿：二次元偏尖萝莉音（不要拖腔、不要嗲）
WHALE_PROMPT = (
    "二次元动漫/游戏配音风格，8到12岁小女孩的萝莉音，音调偏高、声线尖细清脆，带夸张的二次元演技感；"
    "语速偏快、吐字干脆，尾音利落不拖长，不撒娇、不黏糊；带小恶魔式的坏笑，"
    "生气时音量拔高、语气冲。"
)
VOICE_INSTRUCTION = "用二次元萝莉的语气自然朗读，吐字干脆、尾音利落，情绪跟着内容走。"


def read_text(path: str) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"读不了这个文件（编码未知）：{path}")


def clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"```.*?```", "\n", text, flags=re.S)      # 代码块跳过
    text = re.sub(r"`([^`]*)`", r"\1", text)                  # 行内代码去反引号
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # 图片
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # 链接留文字
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)  # 标题符号
    text = re.sub(r"[*_~>]{1,}", "", text)                    # 强调符号
    return text


def split_chunks(text: str, max_chars: int):
    text = re.sub(r"\n{2,}", "\n", text).strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[。！？!?；;：:])|\n", text)
    chunks, buf = [], ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(buf) + len(s) <= max_chars:
            buf += s
        else:
            if buf:
                chunks.append(buf)
            while len(s) > max_chars:  # 超长单句硬切
                chunks.append(s[:max_chars])
                s = s[max_chars:]
            buf = s
    if buf:
        chunks.append(buf)
    return chunks


def strip_id3(data: bytes) -> bytes:
    if data[:3] == b"ID3" and len(data) > 10:
        size = (data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14 | (data[8] & 0x7F) << 7 | (data[9] & 0x7F)
        footer = 10 if (data[5] & 0x10) else 0
        return data[10 + size + footer:]
    return data


def synthesize(chunk: str, timeout: int = 180) -> bytes:
    body = json.dumps({
        "text": chunk,
        "model": "mimo-v2.5-tts-voicedesign",
        "voiceDesignPrompt": WHALE_PROMPT,
        "speechInstruction": VOICE_INSTRUCTION,
        "format": "mp3",
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/synthesize", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ctype = resp.headers.get("content-type", "")
        data = resp.read()
    if "audio" not in ctype:
        raise RuntimeError("合成失败：" + data.decode("utf-8", "replace")[:300])
    return data


def read_clipboard() -> str:
    """用 Win32 API 直接读剪贴板文字（不 spawn 子进程，沙盒里也能用）。"""
    import ctypes

    CF_UNICODETEXT = 13
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_bool
    user32.IsClipboardFormatAvailable.argtypes = [ctypes.c_uint]
    user32.IsClipboardFormatAvailable.restype = ctypes.c_bool
    user32.GetClipboardData.argtypes = [ctypes.c_uint]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = ctypes.c_bool
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_bool

    if not user32.OpenClipboard(None):
        raise SystemExit("打不开剪贴板（可能被其他程序占用）")
    try:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            raise SystemExit("剪贴板里不是文字。")
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            raise SystemExit("读取剪贴板失败。")
        ptr = kernel32.GlobalLock(handle)
        try:
            text = ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()

    text = text or ""
    if not text.strip():
        raise SystemExit("剪贴板是空的。")
    return text


def main():
    ap = argparse.ArgumentParser(description="用鲸鱼娘音色朗读文本")
    ap.add_argument("file", nargs="?", help="要朗读的 txt/md 文件")
    ap.add_argument("--text", help="直接朗读这段文字")
    ap.add_argument("--clipboard", action="store_true", help="朗读当前剪贴板内容")
    ap.add_argument("--out", help="输出 mp3 路径")
    ap.add_argument("--max-chars", type=int, default=280, help="每段合成字符数（默认 280）")
    ap.add_argument("--play", action="store_true", help="合成后自动打开播放")
    args = ap.parse_args()

    if args.clipboard:
        raw, stem = read_clipboard(), "剪贴板"
    elif args.text:
        raw, stem = args.text, "朗读"
    elif args.file:
        raw = read_text(args.file)
        stem = os.path.splitext(os.path.basename(args.file))[0]
    else:
        raise SystemExit("用法：python readaloud.py <文件>  或  --text \"...\"  或  --clipboard")

    text = clean(raw)
    chunks = split_chunks(text, args.max_chars)
    if not chunks:
        raise SystemExit("没有可朗读的文字。")
    print(f"共 {len(chunks)} 段，开始合成（音色：鲸鱼娘 / 音色设计）…")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = args.out or os.path.join(out_dir, f"{stem}_鲸鱼娘.mp3")

    parts, t0 = [], time.time()
    for i, chunk in enumerate(chunks, 1):
        try:
            audio = strip_id3(synthesize(chunk))
        except urllib.error.HTTPError as e:
            raise SystemExit(f"第 {i} 段失败：HTTP {e.code} {e.read()[:300]!r}")
        except Exception as e:
            raise SystemExit(f"第 {i} 段失败：{e}")
        parts.append(audio)
        print(f"  [{i}/{len(chunks)}] {len(chunk)} 字 -> {len(audio)//1024} KB")

    with open(out_path, "wb") as f:
        f.write(b"".join(parts))
    print(f"完成：{out_path}（{os.path.getsize(out_path)//1024} KB，用时 {time.time()-t0:.1f}s）")

    if args.play:
        os.startfile(out_path)  # noqa: S606  (Windows 用默认播放器打开)


if __name__ == "__main__":
    main()
