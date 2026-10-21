@echo off
chcp 65001 >nul
title 陪伴服务 · 开机自启
setlocal
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
copy /Y "%~dp0启动陪伴.vbs" "%STARTUP%\DSH陪伴服务.vbs" >nul
if errorlevel 1 (
  echo 写入启动文件夹失败。
) else (
  echo 已登记开机自启：%STARTUP%\DSH陪伴服务.vbs
  echo 取消自启：删掉这个文件即可。
)
timeout /t 4 >nul
