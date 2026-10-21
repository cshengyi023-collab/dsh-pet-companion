# -*- coding: utf-8 -*-
"""桌宠控制台（接管用）—— 任何 DSH 会话的 Agent 都可以运行这个脚本指挥桌宠。

用法：
  python petctl.py state                     # 看当前状态（气泡/余额/显示位置）
  python petctl.py say "文本" [毫秒]          # 让她说一句（气泡）
  python petctl.py whisper                    # 让她自己生成一句碎碎念（会花 LLM token）
  python petctl.py chat "你好"                # 和她聊天（她的 LLM，花 token）
  python petctl.py anim "东张西望"            # 点播动画
  python petctl.py display desktop|web|both|none   # 切换显示位置（桌面/网页/都显示/都不显示）
  别名: wave shy dance spin work sleep eat magic whale roam run stretch
环境变量：PET_BASE（默认 http://127.0.0.1:19387/dsh-pet-7340）、PET_ID（默认 main）
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("PET_BASE", "http://127.0.0.1:19387/dsh-pet-7340")
PET = os.environ.get("PET_ID", "main")


def req(method, path, body=None, timeout=120):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def read_config():
    status, txt = req("GET", "/config")
    if status != 200:
        raise SystemExit(f"读配置失败 {status}: {txt[:200]}")
    return json.loads(txt)


def save_display(display):
    cfg = read_config()
    entry = cfg.get("main")
    if not entry or "pets" not in entry:
        raise SystemExit("配置结构不认识（没有 main.pets）")
    pets = []
    keep = ["name", "id", "size", "balanceEnabled", "display", "position",
            "whisperEnabled", "workStatusEnabled", "fixedEnabled"]
    for p in entry["pets"]:
        q = {k: p[k] for k in keep if k in p}
        if q.get("id") == PET:
            q["display"] = display
        pets.append(q)
    status, txt = req("PUT", "/config", {"pets": pets})
    if status != 200:
        raise SystemExit(f"改显示位置失败 {status}: {txt[:300]}")
    print(f"已把宠物 {PET} 的显示位置改为：{display}（桌面侧会自动重载）")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "state"
    alias = {
        "wave": "点击回应-元气挥手", "shy": "点击回应-害羞惊讶", "dance": "可爱宅舞",
        "spin": "小幅度原地360度旋转展示", "work": "写代码", "sleep": "原地小憩沉眠",
        "eat": "吃白饭", "magic": "扑克魔术", "whale": "蓝鲸现世",
        "roam": "螃蟹走路", "run": "原地左转奔跑", "stretch": "超大伸懒腰",
    }
    if cmd == "state":
        status, txt = req("GET", "/state")
        if status != 200:
            raise SystemExit(f"读状态失败 {status}")
        s = json.loads(txt)
        pets = s.get("pets", {})
        for pid, leaf in pets.items():
            say = leaf.get("say", {}).get("data") or {}
            anim = leaf.get("anim", {}).get("data") or {}
            print(f"[{pid}] 气泡: {say.get('text', '（无）')}")
            if anim:
                print(f"       动画: {anim.get('name') or anim.get('url')}")
        bal = s.get("sections", {}).get("balance", {}).get("data") or {}
        if bal.get("ok"):
            d = bal.get("data") or {}
            print(f"余额: {d.get('currency','?')} {d.get('total','?')}（{bal.get('provider')}）")
        ws = s.get("sections", {}).get("workStatus", {}).get("data") or {}
        print(f"工作状态: {ws.get('state') or '空闲'}")
        try:
            cfg = read_config()
            for p in cfg.get("main", {}).get("pets", []):
                if p.get("id") == PET:
                    print(f"显示位置: {p.get('display')}")
        except Exception:
            pass
        return

    if cmd == "say":
        text = sys.argv[2] if len(sys.argv) > 2 else "你好呀"
        dur = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
        print(req("POST", f"/broadcast?pet={PET}", {"text": text, "duration": dur})[1])
        return
    if cmd == "whisper":
        print(req("POST", f"/whisper?pet={PET}")[1])
        return
    if cmd == "chat":
        text = sys.argv[2] if len(sys.argv) > 2 else "你好呀"
        print(req("POST", f"/chat?pet={PET}", {"text": text})[1])
        return
    if cmd == "anim":
        name = sys.argv[2] if len(sys.argv) > 2 else alias.get(cmd)
        if not name:
            raise SystemExit("要一个动画名")
        print(req("POST", f"/anim?pet={PET}", {"name": name})[1])
        return
    if cmd == "display":
        if len(sys.argv) < 3:
            raise SystemExit("display 需要参数：desktop / web / both / none")
        save_display(sys.argv[2])
        return
    if cmd in alias:
        print(req("POST", f"/anim?pet={PET}", {"name": alias[cmd]})[1])
        return
    print(__doc__)


if __name__ == "__main__":
    main()
