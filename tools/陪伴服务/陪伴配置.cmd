@echo off
chcp 65001 >nul
title 陪伴服务 · 配置
setlocal
set "PY=C:\Users\chenshengyi\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%~dp0companion.json" "%PY%" -c "import sys; sys.path.insert(0, r'%~dp0'); import companion, json; companion.save(companion.CONFIG_PATH, companion.DEFAULT_CONFIG)"
start "" notepad "%~dp0companion.json"
echo 改完保存后，重启陪伴服务即可生效。
timeout /t 3 >nul
