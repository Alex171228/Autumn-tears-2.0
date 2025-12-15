@echo off
cd /d "%~dp0"
call venv\Scripts\activate
echo Запуск Backend сервера (FastAPI)...
uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause

