# Preflight. Run this immediately before demonstrating, every time.
#
# It checks the things that actually break on stage: a service that did not come up, a
# database with no storms in it, a demo storm with no precomputed frames, and whether the
# leakage guard still holds.
#
# Exit code 0 means safe to present.

$ErrorActionPreference = 'Continue'

$failures = @()
$warnings = @()

function Test-Endpoint {
    param([string]$Name, [string]$Url)
    try {
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec 5
        Write-Host "  OK   $Name" -ForegroundColor Green
        return $response
    } catch {
        Write-Host "  FAIL $Name -> $Url" -ForegroundColor Red
        $script:failures += "$Name unreachable at $Url"
        return $null
    }
}

Write-Host '== CycloVision preflight ==' -ForegroundColor Cyan

# --- Services ----------------------------------------------------------------------
Write-Host "`nServices" -ForegroundColor Yellow
$aiHealth = Test-Endpoint 'AI service' 'http://localhost:8000/health'
$apiHealth = Test-Endpoint 'Backend' 'http://localhost:8090/api/health'
Test-Endpoint 'Frontend' 'http://localhost:5173' | Out-Null

# --- Model bundle -------------------------------------------------------------------
Write-Host "`nModel bundle" -ForegroundColor Yellow
if ($aiHealth) {
    $trained = @($aiHealth.models | Where-Object { $_.isTrained })
    Write-Host "  $($aiHealth.models.Count) components registered, $($trained.Count) trained"
    if ($trained.Count -eq 0) {
        # Correct for Phase 0, and the UI says so. Stated out loud so nobody walks on
        # stage expecting forecast numbers that do not exist yet.
        $warnings += 'No trained models. Forecast values will be absent and every output is stamped DEMO_DATA.'
    }
}

# --- Data ---------------------------------------------------------------------------
Write-Host "`nData" -ForegroundColor Yellow
$storms = $null
try {
    $storms = Invoke-RestMethod -Uri 'http://localhost:8090/api/storms' -TimeoutSec 5
} catch {
    $failures += 'GET /api/storms failed'
}

if ($null -ne $storms) {
    $count = @($storms).Count
    Write-Host "  $count storms in the database"
    if ($count -eq 0) {
        $warnings += 'No storms loaded. Phase 1 imports IBTrACS and joins HURSAT frames.'
    }

    $demo = @($storms | Where-Object { $_.isDemo })
    foreach ($storm in $demo) {
        # The leakage guard, checked from outside as well as in the database.
        if ($storm.split -ne 'test') {
            $failures += "Demo storm $($storm.name) is in the '$($storm.split)' split. Verification results would be meaningless."
        }

        try {
            $detail = Invoke-RestMethod -Uri "http://localhost:8090/api/storms/$($storm.sid)" -TimeoutSec 10
            $analysed = @($detail.frames | Where-Object { $_.hasAnalysis }).Count
            Write-Host "  $($storm.name): $($detail.frames.Count) frames, $analysed analysed, $($detail.framesWithImagery) with imagery"
            if ($detail.frames.Count -eq 0) {
                $failures += "Demo storm $($storm.name) has no frames; the timeline will be empty."
            } elseif ($analysed -eq 0) {
                $warnings += "Demo storm $($storm.name) has no precomputed analysis. Run ml/precompute/precompute_frames.py."
            }
        } catch {
            $failures += "Could not load detail for demo storm $($storm.name)"
        }
    }
}

# --- Degradation --------------------------------------------------------------------
Write-Host "`nDegradation" -ForegroundColor Yellow
if ($apiHealth) {
    if ($apiHealth.demoMode) {
        Write-Host '  DEMO_MODE is ON: forecasts come from stored scenarios, stamped DEMO_DATA' -ForegroundColor DarkYellow
    } else {
        Write-Host '  DEMO_MODE is off: forecasts go to the live AI service'
    }
    Write-Host "  backend $($apiHealth.status) - ai $($apiHealth.aiService.status) - db $($apiHealth.database)"
    if ($apiHealth.database -ne 'UP') { $failures += 'Backend cannot reach the database.' }
}

# --- Verdict -------------------------------------------------------------------------
Write-Host "`n== Result ==" -ForegroundColor Cyan
foreach ($warning in $warnings) { Write-Host "  WARN $warning" -ForegroundColor Yellow }
foreach ($failure in $failures) { Write-Host "  FAIL $failure" -ForegroundColor Red }

if ($failures.Count -gt 0) {
    Write-Host "`nNot safe to present: $($failures.Count) failure(s)." -ForegroundColor Red
    exit 1
}

Write-Host "`nSafe to present." -ForegroundColor Green
if ($warnings.Count -gt 0) {
    Write-Host 'Note the warnings above so nothing on stage is a surprise.' -ForegroundColor DarkGray
}
exit 0
