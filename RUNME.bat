@echo off
setlocal
title Smart Crop Rotation - Launcher
cd /d "%~dp0"

REM ============================================================
REM  Smart Crop Rotation - one-click launcher (Windows)
REM  Double-click this file to set up and start the app.
REM  Opens http://127.0.0.1:5000 automatically when ready.
REM ============================================================

echo.
echo  ==============================================
echo   Smart Crop Rotation - starting setup...
echo  ==============================================
echo.

REM ---- 1. Python check ----
where py >nul 2>nul
if %errorlevel%==0 (set PYLAUNCH=py) else (
  where python >nul 2>nul
  if %errorlevel%==0 (set PYLAUNCH=python) else (
    echo [ERROR] Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
  )
)

REM ---- 2. Create virtual environment if missing ----
if not exist venv\Scripts\python.exe (
  echo [1/4] Creating virtual environment...
  %PYLAUNCH% -m venv venv
  if errorlevel 1 (
    echo [ERROR] Could not create venv. 
    pause
    exit /b 1
  )
)

REM ---- 3. Install dependencies ----
echo [2/4] Installing dependencies (first run only)...
venv\Scripts\python.exe -m pip install --quiet --upgrade pip
venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed. Check internet connection.
  pause
  exit /b 1
)

REM ---- 4. Train model if missing ----
if not exist models\crop_model.pkl (
  echo [3/4] Training the machine-learning model...
  venv\Scripts\python.exe train_model.py
  if errorlevel 1 (
    echo [ERROR] Model training failed.
    pause
    exit /b 1
  )
) else (
  echo [3/4] Model already trained - skipping.
)

REM ---- 5. Start the app ----
echo [4/4] Starting the web app...
echo.
echo  Open this URL in your browser:  http://127.0.0.1:5000
echo  Press Ctrl+C in this window to stop the server.
echo.
start "" http://127.0.0.1:5000
venv\Scripts\python.exe app.py

pause
