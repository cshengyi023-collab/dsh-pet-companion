# ============================================================
# 修复：按压动画残留 transform 导致「悬浮标签/菜单偏离」的问题
# 原因：pressFeedback() 结束时把 transform 留成了 scale(1,1)（非 none），
#       而被 transform 的祖先会成为 position:fixed 子元素的包含块——
#       .pet-tooltip 是 position:fixed，于是悬浮标签按宠物容器坐标定位，偏到很远。
# 修法：动画结束后把 transform/transition/transformOrigin 全部清空。
# 幂等；dsh-pet 升级后重跑。
# ============================================================
$ErrorActionPreference = 'Stop'
$helper = 'C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-pet\runtime\electron-helper'
$file = "$helper\sprite.js"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$src = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)

if ($src.Contains('[press-feedback-v3]')) { Write-Output '已修过（v3），跳过'; exit 0 }

$old = @'
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

$new = @'
  /** [press-feedback-v3] 整只宠物按压：快速压扁 → 弹性回弹；结束后必须清空 transform，
   *  否则被 transform 的容器会变成 position:fixed 的 tooltip/菜单的包含块，导致悬浮标签偏移。 */
  pressFeedback() {
    try {
      const el = this.el;
      if (!el) return;
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      el.style.transformOrigin = 'bottom';
      el.style.transition = 'transform 90ms ease-out';
      el.style.transform = 'scale(0.94, 0.87)';
      clearTimeout(this.pressTimer);
      this.pressTimer = setTimeout(() => {
        el.style.transition = 'transform 190ms cubic-bezier(.3,1.6,.5,1)';
        el.style.transform = 'scale(1, 1)';
        clearTimeout(this.pressCleanup);
        this.pressCleanup = setTimeout(() => {
          el.style.transform = '';
          el.style.transition = '';
          el.style.transformOrigin = '';
        }, 210);
      }, 95);
    } catch (e) {}
  }
'@

if (-not $src.Contains($old)) { throw 'pressFeedback v2 代码没找到（版本可能变了）' }
$src = $src.Replace($old, $new)
[System.IO.File]::WriteAllText($file, $src, $utf8)
$check = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
Write-Output ('含 v3 标记: ' + $check.Contains('[press-feedback-v3]'))
