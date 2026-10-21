import json, struct, os, sys, re

P = r"C:\Users\chenshengyi\AppData\Local\Programs\DeepSeek Harness\resources\app.asar"
data = open(P, "rb").read()
start = 16
txt = data[start:].decode("utf-8", "ignore")
obj, end = json.JSONDecoder().raw_decode(txt)
base = start + end
outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(outdir, exist_ok=True)

targets = []
def walk(node, prefix):
    for name, ent in node.get("files", {}).items():
        p = prefix + "/" + name if prefix else name
        if "files" in ent:
            walk(ent, p)
        else:
            if any(k in p for k in ("dsh-app-boot/lib/index.js",
                                    "dsh-plugin-manager/lib/index.js",
                                    "dsh-plugin-manager/lib/client.js")):
                targets.append((p, int(ent["offset"]), ent["size"]))
walk(obj, "")

for p, off, size in targets:
    dest = os.path.join(outdir, p.replace("/", "__"))
    open(dest, "wb").write(data[base + off: base + off + size])
    print("wrote", os.path.basename(dest), size)
