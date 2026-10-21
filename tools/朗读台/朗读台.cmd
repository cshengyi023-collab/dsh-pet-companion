@echo off
chcp 65001 >nul
title 朗读台 · 鲸鱼娘
setlocal
set "PY=C:\Users\chenshengyi\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" (
  echo 找不到内置 Python：%PY%
  pause
  exit /b 1
)
echo ============================================
echo   朗读台 —— 用鲸鱼娘的声音读书 / 读讲义
echo   （把你的 txt / md 文件拖进这个窗口，回车）
echo ============================================
echo.
set /p TARGET=文件路径：
if "%TARGET%"=="" goto :end
"%PY%" "%~dp0readaloud.py" "%TARGET%" --play
echo.
:end
pause
