@echo off
cd /d "%~dp0"
py start.py
if errorlevel 1 python start.py

