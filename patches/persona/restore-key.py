import re
PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"
BAK = PATCH + ".bak-xiaojingjing"
bak = open(BAK, encoding="utf-8").read()
m = re.search(r'apiKey:\s*["\u0027]?([A-Za-z0-9_\-]{8,})["\u0027]?', bak)
if not m:
    # 试其他备份
    import glob
    for b in sorted(glob.glob(PATCH + ".bak*")):
        t = open(b, encoding="utf-8").read()
        m = re.search(r'apiKey:\s*["\u0027]?([A-Za-z0-9_\-]{8,})["\u0027]?', t)
        if m:
            print("key found in", b)
            break
if not m:
    raise SystemExit("未找到 key，请让用户重新粘贴")
key = m.group(1)
t = open(PATCH, encoding="utf-8").read()
t2 = t.replace('apiKey: ""', 'apiKey: "%s"' % key)
open(PATCH, "w", encoding="utf-8", newline="\n").write(t2)
print("key restored, length:", len(key))
