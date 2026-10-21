@echo off
chcp 65001 >nul
title 陪伴服务 · 停止
setlocal
set "TASK=DSH桌宠陪伴"
schtasks /End /TN "%TASK%" >nul 2>&1
powershell -NoProfile -Command "Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*dsh-primary-runtime*' } | ForEach-Object { try { $_.Kill(); Write-Host ('已停止 PID ' + $_.Id) } catch {} }"
echo 陪伴服务已停止（计划任务保留，下次登录仍会自启；想彻底删掉运行：schtasks /Delete /TN "%TASK%" /F）。
timeout /t 3 >nul
