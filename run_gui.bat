@echo off
title Running OmniVoice GUI...
cd /d "%~dp0"
echo Starting OmniVoice GUI local voice cloning tool...
set "PY_EXE=.venv\Scripts\python.exe"

if not exist "%PY_EXE%" (
    echo Local .venv was not found. Creating it on this machine...
    py -3.11 -m venv --system-site-packages .venv 2>nul
    if errorlevel 1 (
        python -m venv --system-site-packages .venv
    )
    if errorlevel 1 goto failed

    echo Installing GUI runtime packages...
    "%PY_EXE%" -m pip install --upgrade pip
    if errorlevel 1 goto failed
    "%PY_EXE%" -m pip install sounddevice customtkinter static-ffmpeg "transformers>=5.3.0"
    if errorlevel 1 goto failed
)

"%PY_EXE%" -c "import sounddevice, customtkinter, static_ffmpeg; from transformers import HiggsAudioV2TokenizerModel" >nul 2>nul
if errorlevel 1 (
    echo Repairing missing or outdated runtime packages...
    "%PY_EXE%" -m pip install sounddevice customtkinter static-ffmpeg "transformers>=5.3.0"
    if errorlevel 1 goto failed
)

"%PY_EXE%" gui.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo Failed to start OmniVoice GUI.
echo If this is the first run on a new computer, make sure Python 3.11 is installed
echo and run this file again with internet access.
pause
