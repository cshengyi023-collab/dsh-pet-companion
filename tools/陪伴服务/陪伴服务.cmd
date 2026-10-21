@echo off
chcp 65001 >nul
title 陪伴服务 · 启动
setlocal
wscript "%~dp0启动陪伴.vbs"
echo 陪伴服务已在后台启动（番茄钟/久坐/喝水/整点问候，按 companion.json 的开关）。
echo 停止：双击「停止陪伴.cmd」；开机自启：双击「开机自启.cmd」。
timeout /t 3 >nul
