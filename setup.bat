@echo off
setlocal EnableExtensions EnableDelayedExpansion
if not exist logs mkdir logs

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY_CMD=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PY_CMD=python"
  ) else (
    echo Python was not found on PATH.
    pause
    exit /b 1
  )
)

if not exist .venv (
  %PY_CMD% -m venv .venv >> logs\setup.log 2>&1
)

.venv\Scripts\python.exe -m pip install --upgrade pip >> logs\setup.log 2>&1
.venv\Scripts\python.exe -m pip install -r requirements.txt >> logs\setup.log 2>&1
.venv\Scripts\python.exe -m playwright install chromium >> logs\setup.log 2>&1

if not exist .env copy /Y .env.example .env >nul

echo Setup complete.
echo Add your OPENAI_API_KEY to .env before running.
pause
