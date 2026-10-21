$ErrorActionPreference = 'Continue'
$pkg = 'C:\Users\chenshengyi\.dsh\profiles\desktop\package.json'
$txt = [System.IO.File]::ReadAllText($pkg, [System.Text.Encoding]::UTF8)
$fixed = [regex]::Replace($txt, '"dsh-whale-startup"\s*:\s*"[^"]*"', '"dsh-whale-startup": "link:D:/ai工作库/dsh-whale-startup"')
[System.IO.File]::WriteAllText($pkg, $fixed, (New-Object System.Text.UTF8Encoding($false)))
Write-Output '=== after ==='
[System.IO.File]::ReadAllText($pkg, [System.Text.Encoding]::UTF8)
Write-Output '=== junction check ==='
Get-Item 'C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-whale-startup' -Force -ErrorAction SilentlyContinue | Select-Object Name,LinkType,Target
