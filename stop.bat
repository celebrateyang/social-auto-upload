@echo off
:: filepath: D:\code\social-auto-upload\stop.bat
chcp 65001 >nul
echo ========================================
echo   停止 Social Auto Upload 项目
echo ========================================
echo.

echo 正在停止 Python 后端服务...
taskkill /F /IM python.exe /T >nul 2>&1

echo 正在停止 Node.js 前端服务...
taskkill /F /IM node.exe /T >nul 2>&1

echo.
echo ✓ 所有服务已停止
echo.
pause