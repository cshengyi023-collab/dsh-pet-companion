# ============================================================
# 给 dsh-pet 的桌面 Helper 打「摸她出声」补丁（v2：与右下角小鲸鱼挂件同款音效）
#   1) 复制音效文件：dsh-whale-widget 的小黄鸭预设 → helper/sounds/{press,release}.mp3
#   2) 复制 sound.js（按下/松开各播一声，带开关）
#   3) index.html 加载 sound.js（在 sprite.js 之前）
#   4) sprite.js：pointerdown 播放按下音；pointerup 播放松开音；右键菜单「音效：开/关」
# 幂等，可重复运行。dsh-pet 升级/重装后重跑一次即可。
# ============================================================
$ErrorActionPreference = 'Stop'
$helper  = 'C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-pet\runtime\electron-helper'
$widget  = 'C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-whale-widget\assets'
$patch   = 'D:\ai工作库\dsh-pet-control\desktop-sound'
$utf8    = New-Object System.Text.UTF8Encoding($false)

if (-not (Test-Path "$helper\sprite.js")) { throw "找不到 dsh-pet 桌面 Helper：$helper" }
if (-not (Test-Path "$widget\Ya1.mp3"))   { throw "找不到挂件音效：$widget\Ya1.mp3" }

Write-Output '=== 1) 音效文件（小黄鸭预设）==='
New-Item -ItemType Directory -Force -Path "$helper\sounds" | Out-Null
Copy-Item "$widget\Ya1.mp3" "$helper\sounds\press.mp3" -Force
Copy-Item "$widget\Ya2.mp3" "$helper\sounds\release.mp3" -Force
Write-Output ('press.mp3  : ' + (Get-Item "$helper\sounds\press.mp3").Length + ' B')
Write-Output ('release.mp3: ' + (Get-Item "$helper\sounds\release.mp3").Length + ' B')

Write-Output '=== 2) sound.js ==='
[System.IO.File]::WriteAllText("$helper\sound.js", [System.IO.File]::ReadAllText("$patch\sound.js", [System.Text.Encoding]::UTF8), $utf8)
Write-Output ('sound.js: ' + (Test-Path "$helper\sound.js"))

Write-Output '=== 3) index.html ==='
$html = [System.IO.File]::ReadAllText("$helper\index.html", [System.Text.Encoding]::UTF8)
if ($html -match 'sound\.js') {
  Write-Output '已引用 sound.js'
} else {
  $anchor = '    <script src="./constants.js"></script>'
  if ($html -notmatch [regex]::Escape($anchor)) { throw 'index.html 锚点没找到（版本可能变了）' }
  $html = $html.Replace($anchor, $anchor + "`n    <script src=`"./sound.js`"></script>")
  [System.IO.File]::WriteAllText("$helper\index.html", $html, $utf8)
  Write-Output '已插入 sound.js 引用'
}

Write-Output '=== 4) sprite.js ==='
$sprite = [System.IO.File]::ReadAllText("$helper\sprite.js", [System.Text.Encoding]::UTF8)

# 4a) 按下音
if ($sprite -notmatch 'PetSound && window\.PetSound\.play') {
  $anchorDown = "    this.hit.addEventListener('pointerdown', (e) => this.onPointerDown(e), { signal: ac.signal });"
  if ($sprite -notmatch [regex]::Escape($anchorDown)) { throw 'sprite.js 锚点 pointerdown 没找到' }
  $sprite = $sprite.Replace($anchorDown, $anchorDown + "`n    this.hit.addEventListener('pointerdown', () => { try { window.PetSound && window.PetSound.play(); } catch (e) {} }, { signal: ac.signal });")
  Write-Output '已插入：pointerdown 按下音'
} else { Write-Output '按下音已存在' }

# 4b) 松开音
if ($sprite -notmatch 'window\.PetSound\.release') {
  $anchorUp = "    window.addEventListener('pointerup', (e) => this.onPointerUp(e), { signal: ac.signal });"
  if ($sprite -notmatch [regex]::Escape($anchorUp)) { throw 'sprite.js 锚点 pointerup 没找到' }
  $sprite = $sprite.Replace($anchorUp, $anchorUp + "`n    window.addEventListener('pointerup', () => { try { window.PetSound && window.PetSound.release(); } catch (e) {} }, { signal: ac.signal });")
  Write-Output '已插入：pointerup 松开音'
} else { Write-Output '松开音已存在' }

# 4c) 右键菜单开关
if ($sprite -notmatch 'sound-toggle') {
  $anchorTool = "      { label: '回到初始位置', action: 'home' },"
  if ($sprite -notmatch [regex]::Escape($anchorTool)) { throw 'sprite.js 锚点 菜单项 没找到' }
  $sprite = $sprite.Replace($anchorTool, "      { label: '音效：' + (window.PetSound && window.PetSound.enabled() ? '开' : '关'), action: 'sound-toggle' },`n" + $anchorTool)
  $anchorHome = "    if (leaf.action === 'home') {"
  if ($sprite -notmatch [regex]::Escape($anchorHome)) { throw 'sprite.js 锚点 home 分支 没找到' }
  $sprite = $sprite.Replace($anchorHome, "    if (leaf.action === 'sound-toggle') {`n      if (window.PetSound) window.PetSound.toggle();`n      return;`n    }`n" + $anchorHome)
  Write-Output '已插入：右键菜单开关'
} else { Write-Output '菜单开关已存在' }

[System.IO.File]::WriteAllText("$helper\sprite.js", $sprite, $utf8)

Write-Output '=== 5) 校验 ==='
$s = [System.IO.File]::ReadAllText("$helper\sprite.js", [System.Text.Encoding]::UTF8)
@(
  @{ n = '按下音钩子'; ok = ($s -match 'PetSound && window\.PetSound\.play') },
  @{ n = '松开音钩子'; ok = ($s -match 'window\.PetSound\.release') },
  @{ n = '菜单开关';   ok = ($s -match 'sound-toggle') },
  @{ n = '音效文件';   ok = ((Test-Path "$helper\sounds\press.mp3") -and (Test-Path "$helper\sounds\release.mp3")) }
) | ForEach-Object { Write-Output (' - ' + $_.n + ': ' + $_.ok) }
