@echo off
chcp 65001 >nul
title 桌宠控制台
set "PYW=C:\Users\chenshengyi\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\pythonw.exe"
if not exist "%PYW%" set "PYW=C:\Users\chenshengyi\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
start "" "%PYW%" "%~dp0桌宠控制台.pyw"
