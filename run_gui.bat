@echo off
title Running OmniVoice GUI...
cd /d "%~dp0"
echo Starting OmniVoice GUI local voice cloning tool...
set "PY_EXE=.venv\Scripts\python.exe"
set "PY_CMD=py -3.11"
set "PYTORCH_INDEX=https://download.pytorch.org/whl/cu128"

if not exist "%PY_EXE%" (
    echo Local .venv was not found. Creating it on this machine...
    %PY_CMD% -m venv .venv 2>nul
    if errorlevel 1 (
        set "PY_CMD=python"
        python -m venv .venv
    )
    if errorlevel 1 goto failed
)

"%PY_EXE%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo Python 3.10 or newer is required. Python 3.11 is recommended.
    goto failed
)

"%PY_EXE%" -c "import static_ffmpeg; static_ffmpeg.add_paths(); import torch, torchaudio, numpy, soundfile, sounddevice, customtkinter; from transformers import HiggsAudioV2TokenizerModel; from omnivoice import OmniVoice" >nul 2>nul
if errorlevel 1 (
    echo Installing or repairing project dependencies...
    "%PY_EXE%" -m pip install --upgrade pip
    if errorlevel 1 goto failed
    "%PY_EXE%" -m pip install -e . --extra-index-url "%PYTORCH_INDEX%"
    if errorlevel 1 goto failed
)

"%PY_EXE%" -c "import static_ffmpeg; static_ffmpeg.add_paths(); import torch, torchaudio, numpy, soundfile, sounddevice, customtkinter; from transformers import HiggsAudioV2TokenizerModel; from omnivoice import OmniVoice" >nul 2>nul
if errorlevel 1 (
    echo Dependency check still failed after installation.
    goto failed
)

"%PY_EXE%" gui.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo Failed to start OmniVoice GUI.
echo If this is the first run on a new computer, make sure Python 3.11 is installed
echo and run this file again with internet access. The first run must download
echo Python packages and the Hugging Face models.
pause
