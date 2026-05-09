@echo off
cd /d "%~dp0"
echo Starting all services via Docker Compose...
docker compose up --build
pause
