# -*- coding: utf-8 -*-
"""陪伴服务 —— 本地定时陪伴（0 token）：
番茄钟 / 久坐提醒 / 喝水提醒 / 整点问候，全部通过桌宠气泡说话。
与语音插件独立：如果 TTS 的「播报来源 dsh-pet」开着，气泡还会被念出来。

用法：
  python companion.py             # 常驻运行（建议后台启动）
  python companion.py --test      # 立刻发一条测试气泡后退出
  python companion.py --status    # 看当前配置与下次触发时间
配置：companion.json（本目录，改完重启服务生效）
停止：停止陪伴.cmd（或结束对应 pythonw 进程）
"""
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "companion.json")
STATE_PATH = os.path.join(HERE, "companion-state.json")
PET_BASE = os.environ.get("PET_BASE", "http://127.0.0.1:19387/dsh-pet-7340")

DEFAULT_CONFIG = {
    "enabled": True,
    "quiet_hours": [0, 7],
    "items": {
        "pomodoro": {"on": False, "work_min": 25, "break_min": 5},
        "sit_reminder": {"on": True, "every_min": 45},
        "water": {"on": True, "every_min": 45},
        "hourly_greeting": {"on": False},
    },
}

MESSAGES = {
    "water": [
        "该喝水啦～我帮你盯着杯子呢。",
        "喝水时间到！一口也好，快去。",
        "喉咙干了会变笨的，喝口水吧～",
    ],
    "sit_reminder": [
        "坐好久了，起来伸个懒腰吧。",
        "腰要抗议了，站起来走两步～",
        "久坐提醒：动一动，扭扭脖子。",
    ],
    "pomodoro_work": [
        "番茄钟开始啦，专心这一轮～",
        "接下来 {m} 分钟，先别看手机。",
        "开工！我在这儿陪你到点。",
    ],
    "pomodoro_break": [
        "这一轮结束！休息 {m} 分钟。",
        "番茄完成～去倒杯水活动一下。",
        "暂停一下，眯一会也行。",
    ],
    "hourly": [
        "整点啦，进度怎么样？",
        "又过了一个小时，歇口气吧～",
        "报时：{h} 点整。",
    ],
}


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return default


def save(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def in_quiet_hours(cfg):
    q = cfg.get("quiet_hours") or []
    if len(q) == 2:
        start, end = int(q[0]), int(q[1])
        h = datetime.now().hour
        return start <= h < end if start <= end else (h >= start or h < end)
    return False


def say(text, duration=12000):
    body = json.dumps({"text": text, "duration": duration}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(PET_BASE + "/broadcast?pet=main", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = json.loads(resp.read().decode("utf-8", "replace")).get("ok")
            print(f"[{datetime.now():%H:%M:%S}] say -> {ok}: {text}")
    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] say failed: {e}")


def run():
    cfg = load(CONFIG_PATH, DEFAULT_CONFIG)
    state = load(STATE_PATH, {})
    if not os.path.exists(CONFIG_PATH):
        save(CONFIG_PATH, DEFAULT_CONFIG)
        cfg = DEFAULT_CONFIG
    enabled = cfg.get("enabled", True)
    items = cfg.get("items", {})
    print(f"陪伴服务启动 | enabled={enabled} | 配置: {CONFIG_PATH}")

    pomo_phase = state.get("pomodoro_phase", "work")
    pomo_until = state.get("pomodoro_until")

    while True:
        try:
            cfg = load(CONFIG_PATH, DEFAULT_CONFIG)  # 热加载配置
            if not cfg.get("enabled", True):
                time.sleep(20)
                continue
            items = cfg.get("items", {})
            now = datetime.now()
            quiet = in_quiet_hours(cfg)

            # 番茄钟
            p = items.get("pomodoro", {})
            if p.get("on"):
                if not pomo_until:
                    pomo_until = (now + timedelta(minutes=int(p.get("work_min", 25)))).isoformat()
                    pomo_phase = "work"
                    if not quiet:
                        say(random.choice(MESSAGES["pomodoro_work"]).format(m=p.get("work_min", 25)))
                elif now >= datetime.fromisoformat(pomo_until):
                    if pomo_phase == "work":
                        pomo_phase = "break"
                        mins = int(p.get("break_min", 5))
                        pomo_until = (now + timedelta(minutes=mins)).isoformat()
                        if not quiet:
                            say(random.choice(MESSAGES["pomodoro_break"]).format(m=mins))
                    else:
                        pomo_phase = "work"
                        mins = int(p.get("work_min", 25))
                        pomo_until = (now + timedelta(minutes=mins)).isoformat()
                        if not quiet:
                            say(random.choice(MESSAGES["pomodoro_work"]).format(m=mins))
                state["pomodoro_phase"] = pomo_phase
                state["pomodoro_until"] = pomo_until
            else:
                pomo_until = None
                pomo_phase = "work"
                state.pop("pomodoro_phase", None)
                state.pop("pomodoro_until", None)

            # 久坐 / 喝水
            for key in ("sit_reminder", "water"):
                it = items.get(key, {})
                if not it.get("on"):
                    state.pop(f"last_{key}", None)
                    continue
                every = max(1, int(it.get("every_min", 45))) * 60
                last = float(state.get(f"last_{key}", 0))
                if time.time() - last >= every:
                    state[f"last_{key}"] = time.time()
                    if not quiet:
                        say(random.choice(MESSAGES[key]))

            # 整点问候
            hg = items.get("hourly_greeting", {})
            if hg.get("on"):
                hm = now.strftime("%H:%M")
                if now.minute == 0 and state.get("last_hourly") != hm and not quiet:
                    state["last_hourly"] = hm
                    say(random.choice(MESSAGES["hourly"]).format(h=now.hour))

            save(STATE_PATH, state)
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] error: {e}")
        time.sleep(20)


def status():
    cfg = load(CONFIG_PATH, DEFAULT_CONFIG)
    state = load(STATE_PATH, {})
    print("配置:", json.dumps(cfg, ensure_ascii=False, indent=2))
    for key in ("sit_reminder", "water"):
        it = cfg.get("items", {}).get(key, {})
        if it.get("on"):
            last = float(state.get(f"last_{key}", 0))
            if last:
                nxt = datetime.fromtimestamp(last + int(it.get("every_min", 45)) * 60)
                print(f"{key}: 下次 {nxt:%H:%M}")
            else:
                print(f"{key}: 等待首轮")
    p = cfg.get("items", {}).get("pomodoro", {})
    if p.get("on"):
        until = state.get("pomodoro_until")
        print(f"番茄钟: {state.get('pomodoro_phase', 'work')} 到 {until or '未开始'}")


if __name__ == "__main__":
    if "--test" in sys.argv:
        say("陪伴服务测试：我在这儿呢。喝水、久坐、番茄钟，随时喊我。")
        sys.exit(0)
    if "--status" in sys.argv:
        status()
        sys.exit(0)
    run()
