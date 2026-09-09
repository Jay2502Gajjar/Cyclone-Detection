# Stops the database. The three dev servers run in their own windows; close those.
#
# The volume is kept: dropping it would mean re-running the whole ingest, which is hours
# of work in later phases. Pass -Purge only when you genuinely want a clean schema.

param([switch]$Purge)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($Purge) {
    Write-Host 'Removing the database AND its volume. All ingested data will be lost.' -ForegroundColor Red
    docker compose down -v
} else {
    docker compose down
    Write-Host 'Database stopped. The pgdata volume is preserved.' -ForegroundColor Green
}
