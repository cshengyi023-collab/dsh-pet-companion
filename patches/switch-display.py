import json, urllib.request

BASE = 'http://127.0.0.1:19387/dsh-pet-7340'

def req(method, path, data=None):
    body = json.dumps(data).encode('utf-8') if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, method=method,
                               headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=15) as resp:
        return resp.status, resp.read().decode('utf-8', 'replace')

# 1. 读配置
_, txt = req('GET', '/config')
cfg = json.loads(txt)
entry = cfg['main']['pets'][0]
print('current display =', entry.get('display'))
print('pet keys:', sorted(entry.keys())[:30])

# 2. 只改 display 为 desktop，其余字段原样回写
keep = ['name', 'id', 'size', 'balanceEnabled', 'display', 'position',
        'whisperEnabled', 'workStatusEnabled', 'fixedEnabled']
pet = {k: entry[k] for k in keep if k in entry}
pet['display'] = 'desktop'
status, txt = req('PUT', '/config', {'pets': [pet]})
print('PUT status:', status, txt[:200])

# 3. 验证
_, txt = req('GET', '/config')
cfg = json.loads(txt)
print('after display =', cfg['main']['pets'][0].get('display'))

# 4. 试一次说话 + 动作（0.3.7 支持 broadcast / anim）
print('say:', req('POST', '/broadcast?pet=main', {
    'text': '我从屏幕边边溜到桌面上啦～现在就趴在你旁边。',
    'duration': 12000,
})[1][:200])
print('wave:', req('POST', '/anim?pet=main', {'name': '点击回应-元气挥手'})[1][:200])
