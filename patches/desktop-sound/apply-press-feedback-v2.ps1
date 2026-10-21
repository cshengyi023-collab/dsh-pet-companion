# ============================================================
# 按压反馈 v2：整只宠物立刻压扁再回弹（比只压视频帧明显得多）
# 幂等；dsh-pet 升级后重跑本脚本。
# ============================================================
$ErrorActionPreference = 'Stop'
$helper = 'C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-pet\runtime\electron-helper'
$file = "$helper\sprite.js"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$src = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)

if ($src.Contains('[press-feedback-v2]')) {
  Write-Output '已打过 v2 按压补丁，跳过'
  exit 0
}

# 1) 把 v1 的按压片段换成 v2 调用
$old = @'
    // [press-feedback] 按下瞬间立刻 Q 弹压扁再回弹（与右下角挂件同款手感，不等点击动画首帧）
    try {
      const pressEl = this.front === 0 ? this.videoA : this.videoB;
      if (pressEl) this.startSquash(pressEl, 0.78);
    } catch (pressError) {}
'@
$new = @'
    // [press-feedback-v2] 按下瞬间整只宠物压扁再回弹（挂件同款手感）
    try { if (this.pressFeedback) this.pressFeedback(); } catch (pressError) {}
'@
if ($src.Contains($old)) {
  $src = $src.Replace($old, $new)
} elseif ($src.Contains('[press-feedback]')) {
  $src = $src -replace '(?s)\s*// \[press-feedback\].*?catch \(pressError\) \{\}', "`n" + $new
} else {
  # 没有 v1：直接插到左键判定之后
  $anchor = "    if (e.button !== 0) return;"
  if (-not $src.Contains($anchor)) { throw 'onPointerDown 锚点没找到' }
  $src = $src.Replace($anchor, $anchor + "`n" + $new)
}

# 2) 插入 pressFeedback 方法（放在 stopSquash 之前）
$methodAnchor = "  stopSquash() {"
if (-not $src.Contains($methodAnchor)) { throw 'stopSquash 锚点没找到' }
$method = @'
  /** [press-feedback-v2] 整只宠物按压：快速压扁 → 弹性回弹（与右下角挂件同款手感） */
  pressFeedback() {
    try {
      const el = this.el;
      if (!el) return;
      el.style.transformOrigin = 'bottom';
      el.style.transition = 'transform 90ms ease-out';
      el.style.transform = 'scale(0.94, 0.87)';
      clearTimeout(this.pressTimer);
      this.pressTimer = setTimeout(() => {
        el.style.transition = 'transform 190ms cubic-bezier(.3,1.6,.5,1)';
        el.style.transform = 'scale(1, 1)';
      }, 95);
    } catch (e) {}
  }

'@
$src = $src.Replace($methodAnchor, $method + $methodAnchor)

[System.IO.File]::WriteAllText($file, $src, $utf8)
$check = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
Write-Output ('含 v2 标记: ' + $check.Contains('[press-feedback-v2]'))
Write-Output ('含 pressFeedback 方法: ' + $check.Contains('pressFeedback() {'))
