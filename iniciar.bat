@echo off
title DISCO DOWNLOAD
echo.
echo  ============================================
echo    DISCO DOWNLOAD - Arrancando la pista...
echo  ============================================
echo.
echo  Abre tu navegador en: http://localhost:5555
echo  Para parar el servidor pulsa Ctrl+C
echo.
cd /d "%~dp0"
uv run --with flask --with librosa --with mutagen ytweb.py
pause
