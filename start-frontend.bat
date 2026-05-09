@echo off
cd /d "%~dp0"
echo Starting frontend container via Docker Compose...
docker compose up --build frontend
pause
