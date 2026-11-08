@echo off
title Test Real-Time OTP Email Delivery
echo ==========================================================
echo Testing Real-Time OTP Delivery to SRU Inboxes
echo ==========================================================

REM Detect python executable
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PY=python
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PY=py
    ) else (
        if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
            set PY="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        ) else (
            echo [ERROR] Python not found.
            pause
            exit /b 1
        )
    )
)

set RECIPIENT=%1
if "%RECIPIENT%"=="" set RECIPIENT=2303a51751@sru.edu.in

echo Using Python: %PY%
echo Testing recipient: %RECIPIENT%
echo.
%PY% test_email.py %RECIPIENT%
echo.
pause

