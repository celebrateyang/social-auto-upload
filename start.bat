@echo off
REM filepath: d:\code\social-auto-upload\start.bat
chcp 65001 >nul
title Social Auto Upload

echo ========================================
echo   Starting Social Auto Upload Project
echo ========================================
echo.

:: Set paths
set MINICONDA_ROOT=e:\softafter\miniconda
set PROJECT_DIR=D:\code\social-auto-upload
set CONDA_ENV_PATH=E:\app_cache\conda-envs\social-auto-upload

:: Change to project directory
cd /d "%PROJECT_DIR%"

:: Check if conda environment exists
if not exist "%CONDA_ENV_PATH%\python.exe" (
    echo Error: Cannot find Python in conda environment
    echo Path: %CONDA_ENV_PATH%\python.exe
    pause
    exit /b 1
)

:: Add conda environment to PATH
set PATH=%CONDA_ENV_PATH%;%CONDA_ENV_PATH%\Scripts;%CONDA_ENV_PATH%\Library\bin;%PATH%

echo [1/3] Environment ready
echo.

:: Start backend in background
echo [2/3] Starting backend service...
start /b python sau_backend.py
echo Backend service started
echo.

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend in foreground
echo [3/3] Starting frontend service...
cd sau_frontend
echo.
echo ========================================
echo   Services Started
echo   Backend: http://localhost:5409
echo   Frontend: http://localhost:5173
echo ========================================
echo.
npm run dev