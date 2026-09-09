# Starts everything needed for local development.
#
# PowerShell, not bash: Maven's bash launcher fails on this machine because the install
# path contains an apostrophe (D:\Aditya's\JavaLibs\...), which breaks the classworlds
# classpath. The Maven Wrapper avoids the issue entirely, and these scripts use it.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

Write-Host '== CycloVision: starting local stack ==' -ForegroundColor Cyan

# --- 1. PostgreSQL + PostGIS -------------------------------------------------------
Write-Host "`n[1/4] PostgreSQL + PostGIS" -ForegroundColor Yellow
Set-Location $root
docker compose up -d postgres
if ($LASTEXITCODE -ne 0) { throw 'docker compose failed. Is Docker Desktop running?' }

Write-Host '      waiting for the database to accept connections...'
$ready = $false
foreach ($attempt in 1..30) {
    docker exec cyclovision-postgres pg_isready -U cyclovision -d cyclovision *> $null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $ready) { throw 'Postgres did not become ready within 30 seconds.' }
Write-Host '      ready' -ForegroundColor Green

# --- 2. Backend ---------------------------------------------------------------------
# Flyway applies V1-V3 on startup, so this is also what creates the schema.
Write-Host "`n[2/4] Spring Boot backend on :8090" -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\backend'; .\mvnw.cmd spring-boot:run"
)

# --- 3. AI service ------------------------------------------------------------------
Write-Host "`n[3/4] FastAPI AI service on :8000" -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\ai-service'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
)

# --- 4. Frontend --------------------------------------------------------------------
Write-Host "`n[4/4] Vite dev server on :5173" -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host "`n== Started ==" -ForegroundColor Cyan
Write-Host '  app       http://localhost:5173'
Write-Host '  api       http://localhost:8090/api/health'
Write-Host '  api docs  http://localhost:8090/swagger-ui.html'
Write-Host '  ai docs   http://localhost:8000/docs'
Write-Host "`nRun scripts\demo-check.ps1 once everything has settled." -ForegroundColor DarkGray
