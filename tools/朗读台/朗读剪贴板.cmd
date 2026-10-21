@echo off
chcp 65001 >nul
title 朗读剪贴板 · 鲸鱼娘
setlocal
set "PY=C:\Users\chenshengyi\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
echo 正在用鲸鱼娘的声音朗读剪贴板内容……
"%PY%" "%~dp0..\朗读台\readaloud.py" --clipboard --play
