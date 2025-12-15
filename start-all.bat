@echo off
cd /d "%~dp0"
echo Запуск обоих серверов...
start "Backend Server" cmd /k "call venv\Scripts\activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul
start "Frontend Server" cmd /k "npm run dev"
echo Серверы запущены в отдельных окнах!
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
pause

