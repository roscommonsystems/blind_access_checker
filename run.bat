@echo off
if not exist .venv\Scripts\python.exe (
  call setup.bat
)
.venv\Scripts\python.exe app.py
pause
