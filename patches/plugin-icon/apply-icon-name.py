# -*- coding: utf-8 -*-
"""给 dsh-pet 换插件图标 + 改插件列表显示名（幂等，可重复运行）。
- 图标：assets/plugin-icon.png（由 make_icon.py 生成，≤256KiB）
- 显示名：DSH 从插件包 locale/<lang>.json 的 meta.title 读取（见 dsh-app-boot readPluginMeta），
  需要同时给 package.json exports 加 "./locale/*.json"，否则 Node ESM 解析不到。
用法（由 DSH profile 外的 Python 执行）：
  python apply-icon-name.py
"""
import json, os, shutil, sys

PET = r"C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-pet"
HERE = os.path.dirname(os.path.abspath(__file__))
ICON_SRC = os.path.join(HERE, "plugin-icon.png")

TITLE_ZH = "蓝色大肥鱼 · 桌宠"
TITLE_EN = "Blue Whale Pet"
DESC_ZH = "住在你桌面上的蓝色大肥鱼：会自己溜达、能被拖来甩去，也能听我指挥说句话、做动作。"
DESC_EN = "A chubby blue whale pet living on your desktop: roams, gets dragged around, and obeys scripted commands."

def write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

# 1) 图标
assert os.path.exists(ICON_SRC), f"icon missing: {ICON_SRC}"
size = os.path.getsize(ICON_SRC)
assert size <= 256 * 1024, f"icon too large: {size}"
os.makedirs(os.path.join(PET, "assets"), exist_ok=True)
shutil.copyfile(ICON_SRC, os.path.join(PET, "assets", "plugin-icon.png"))
print("icon ->", os.path.join(PET, "assets", "plugin-icon.png"), size, "bytes")

# 2) 本地化显示名
loc = os.path.join(PET, "locale")
os.makedirs(loc, exist_ok=True)
write_json(os.path.join(loc, "en.json"), {
    "meta": {"title": TITLE_EN, "description": DESC_EN}
})
write_json(os.path.join(loc, "zh.json"), {
    "meta": {"title": TITLE_ZH, "description": DESC_ZH}
})
print("locale ->", loc)

# 3) package.json：icon 指向新图 + 允许解析 ./locale/*.json
pkg_path = os.path.join(PET, "package.json")
with open(pkg_path, encoding="utf-8") as f:
    pkg = json.load(f)

pkg["icon"] = "assets/plugin-icon.png"
exports = pkg.setdefault("exports", {})
exports["./locale/*.json"] = "./locale/*.json"

files = pkg.get("files")
if isinstance(files, list):
    for extra in ("assets/plugin-icon.png", "locale"):
        if extra not in files:
            files.append(extra)

with open(pkg_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(pkg, f, ensure_ascii=False, indent=2)
    f.write("\n")

# 4) 校验
with open(pkg_path, encoding="utf-8") as f:
    pkg2 = json.load(f)
print("package icon:", pkg2["icon"])
print("exports has locale:", "./locale/*.json" in pkg2["exports"])
print("locale files:", sorted(os.listdir(loc)))
print("title zh:", json.load(open(os.path.join(loc, "zh.json"), encoding="utf-8"))["meta"]["title"])
print("OK")
