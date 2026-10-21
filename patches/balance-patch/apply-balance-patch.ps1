# ============================================================
# 修复 dsh-pet「账号余额显示 0」补丁（幂等，可重复运行）
#
# 问题：dsh-pet 0.3.7 的 deepseek-account 余额实现只取「充值钱包数组的第 0 个」，
#       而 DSH 账号接口返回的钱包顺序不固定（用户这里是 USD 0.00 排在最前，
#       真实余额在 CNY 钱包里，还有赠金钱包单独一组），于是桌宠永远显示 0。
# 修复：对齐 DSH 官方「账号与余额」卡片的判定口径——
#       充值钱包 + 赠金钱包一起看，优先取「有余额的钱包」的币种（CNY 优先），
#       同币种求和后再算 total / toppedUp / granted。
#
# 用法：powershell -ExecutionPolicy Bypass -File apply-balance-patch.ps1
# 备注：dsh-pet 升级会覆盖 lib/index.js，届时重跑本脚本；改完必须**完全重启 DSH 应用**。
# ============================================================
$ErrorActionPreference = 'Stop'
$file = 'C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-pet\lib\index.js'
$utf8 = New-Object System.Text.UTF8Encoding($false)

if (-not (Test-Path $file)) { throw "找不到 dsh-pet host 文件：$file" }
$src = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)

$marker = '账号没有可用余额钱包'
$anchorStart = '	const wallets = Array.isArray(snapshot.value) ? snapshot.value : [];'
$anchorEnd   = '	const granted = bonus ? money(bonus.balance, "bonus balance") : "0.00";'

if ($src.Contains($marker)) {
  Write-Output '已打过余额补丁，跳过'
  exit 0
}
if (-not $src.Contains($anchorStart)) { throw '锚点（钱包数组）没找到：版本可能变了' }
if (-not $src.Contains($anchorEnd)) { throw '锚点（granted）没找到：版本可能变了' }

# 备份一次原始文件
$bak = "$file.orig-balance-patch"
if (-not (Test-Path $bak)) { [System.IO.File]::WriteAllText($bak, $src, $utf8); Write-Output "已备份原始文件：$bak" }

$newBlock = @'
	// [balance-patch] 对齐 DSH 账号卡片口径：充值钱包 + 赠金钱包一起看，优先有余额的钱包（CNY 优先）。
	const normRaw = Array.isArray(snapshot.value) ? snapshot.value : [];
	const bonusRaw = Array.isArray(snapshot.bonusWallets) ? snapshot.bonusWallets : [];
	const usable = (list) => list.filter((w) => w && Number.isFinite(Number(w.balance)));
	const normWallets = usable(normRaw);
	const bonusWallets = usable(bonusRaw);
	if (normWallets.length === 0 && bonusWallets.length === 0) throw new Error("dsh-pet: 账号没有可用余额钱包");
	const curOf = (w) => { const c = String((w && w.currency) || "CNY").toUpperCase(); return c || "CNY"; };
	const allWallets = normWallets.concat(bonusWallets);
	const nonzero = allWallets.filter((w) => Number(w.balance) > 0);
	const pick = nonzero.find((w) => curOf(w) === "CNY") || nonzero[0] || allWallets.find((w) => curOf(w) === "CNY") || allWallets[0];
	const currency = curOf(pick);
	const sumOf = (list) => list.filter((w) => curOf(w) === currency).reduce((s, w) => s + Number(w.balance), 0);
	const toppedUp = sumOf(normWallets).toFixed(2);
	const granted = sumOf(bonusWallets).toFixed(2);
'@

# 定位并替换锚点之间的整段
$startIdx = $src.IndexOf($anchorStart)
$endIdx = $src.IndexOf($anchorEnd, $startIdx)
if ($startIdx -lt 0 -or $endIdx -lt 0) { throw '替换区间定位失败' }
$endIdx = $endIdx + $anchorEnd.Length
$patched = $src.Substring(0, $startIdx) + $newBlock.TrimEnd("`r`n") + $src.Substring($endIdx)

[System.IO.File]::WriteAllText($file, $patched, $utf8)
Write-Output '=== 已写入补丁，校验 ==='
$after = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
Write-Output ('含新逻辑: ' + $after.Contains($marker))
Write-Output ('文件大小: ' + [math]::Round($after.Length/1KB,1) + ' KB')
