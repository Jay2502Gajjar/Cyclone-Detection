# Runs every test suite in the repository.
#
# Three languages, one command. The backend suite is deliberately database-free so it
# runs anywhere; the migration test that needs real PostgreSQL is opt-in and only runs
# when -WithDatabase is passed and the container is up.

param([switch]$WithDatabase)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$failures = @()

Write-Host '== Backend (JUnit) ==' -ForegroundColor Cyan
Set-Location "$root\backend"
if ($WithDatabase) {
    .\mvnw.cmd -B test '-Dcyclovision.db.it=true'
} else {
    .\mvnw.cmd -B test
}
if ($LASTEXITCODE -ne 0) { $failures += 'backend' }

Write-Host "`n== AI service (pytest) ==" -ForegroundColor Cyan
Set-Location "$root\ai-service"
.\.venv\Scripts\python.exe -m pytest
if ($LASTEXITCODE -ne 0) { $failures += 'ai-service' }

Write-Host "`n== Frontend (tsc + oxlint) ==" -ForegroundColor Cyan
Set-Location "$root\frontend"
npm run build
if ($LASTEXITCODE -ne 0) { $failures += 'frontend build' }
npm run lint
if ($LASTEXITCODE -ne 0) { $failures += 'frontend lint' }

Set-Location $root
Write-Host "`n== Result ==" -ForegroundColor Cyan
if ($failures.Count -gt 0) {
    Write-Host "Failed: $($failures -join ', ')" -ForegroundColor Red
    exit 1
}
Write-Host 'All suites passed.' -ForegroundColor Green
if (-not $WithDatabase) {
    Write-Host 'The PostGIS migration test was skipped. Run with -WithDatabase after docker compose up -d postgres.' -ForegroundColor DarkGray
}
exit 0
