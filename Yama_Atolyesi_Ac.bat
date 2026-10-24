@echo off
chcp 65001 >nul
cd /d "%~dp0"
start "" py -3.12 "%~dp0Yama_Atolyesi.py"
