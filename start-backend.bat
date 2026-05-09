@echo off
cd /d "%~dp0"
echo Starting backend services via Docker Compose...
docker compose up --build gateway-service auth-service simulation-service config-service admin-service mongo redis
pause
