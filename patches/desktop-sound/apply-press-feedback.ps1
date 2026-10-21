# ============================================================
# 给桌面版桌宠加「按压 Q 弹」反馈（幂等，可重复运行）
# 与右下角小鲸鱼挂件同款手感：按下瞬间立刻压扁再回弹，不用等点击动画首帧。
# 备注：dsh-pet 升级会覆盖 sprite.js，届时重跑本脚本。
# ============================================================
$ErrorActionPreference = 'Stop'
$helper = 'C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-pet\runtime\electron-helper'
$file = "$helper\sprite.js"
$utf8 = New-Object System.Text.UTF8Encoding($false)
if (-not (Test-Path $file)) { throw "找不到 sprite.js：$file" }

$src = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
$marker = '[press-feedback]'

if ($src.Contains($marker)) {
  Write-Output '已打过按压补丁，跳过'
  exit 0
}

$bak = "$file.orig-press"
if (-not (Test-Path $bak)) {
  [System.IO.File]::WriteAllText($bak, $src, $utf8)
  Write-Output "已备份：$bak"
}

$anchor = "    if (e.button !== 0) return;"
if (-not $src.Contains($anchor)) { throw 'onPointerDown 锚点没找到（版本可能变了）' }

$insert = @'
    // [press-feedback] 按下瞬间立刻 Q 弹压扁再回弹（与右下角挂件同款手感，不等点击动画首帧）
    try {
      const pressEl = this.front === 0 ? this.videoA : this.videoB;
      if (pressEl) this.startSquash(pressEl, 0.78);
    } catch (pressError) {}
'@

$patched = $src.Replace($anchor, $anchor + "`n" + $insert)
[System.IO.File]::WriteAllText($file, $patched, $utf8)
Write-Output '已插入按压反馈'
$check = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
Write-Output ('校验 press-feedback: ' + $check.Contains($marker))
