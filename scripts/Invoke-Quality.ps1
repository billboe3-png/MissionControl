<#
.SYNOPSIS
Quality gate script for Mission Control CLI validation.
.DESCRIPTION
Runs Pester tests, CLI smoke tests, and formatting/lint checks.
Returns non-zero exit code if any check fails.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptsRoot = Join-Path $repoRoot 'scripts'

Write-Host "=== Mission Control Quality Gate ===" -ForegroundColor Cyan
Write-Host ""

# 1. Pester Tests
Write-Host "Step 1: Running Pester tests..." -ForegroundColor Cyan
$testFiles = @(
    'Bootstrap.Tests.ps1',
    'Registry.Tests.ps1',
    'Logger.Tests.ps1',
    'Helpers.Tests.ps1',
    'Validation.Tests.ps1'
)
$testPaths = $testFiles | ForEach-Object { Join-Path $repoRoot "tests\$_" }
$pesterResult = Invoke-Pester -Path $testPaths -PassThru
if ($pesterResult.FailedCount -gt 0) {
    Write-Host "Pester tests FAILED: $($pesterResult.FailedCount) failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Quality Gate FAILED" -ForegroundColor Red
    exit 1
}
Write-Host "Pester tests PASSED: $($pesterResult.PassedCount) passed" -ForegroundColor Green
Write-Host ""

# 2. CLI Smoke Tests
Write-Host "Step 2: Running CLI smoke tests..." -ForegroundColor Cyan

$smokeTests = @(
    @{ Command = 'help'; Description = 'mc help' },
    @{ Command = 'version'; Description = 'mc version' },
    @{ Command = 'status'; Description = 'mc status' },
    @{ Command = 'doctor'; Args = @('--output', 'json'); Description = 'mc doctor --output json' }
)

$smokeFailed = $false
foreach ($test in $smokeTests) {
    Write-Host "  Running: $($test.Description)..." -ForegroundColor Gray
    $testArgs = if ($test.Args) { $test.Args } else { @() }
    $commandArgs = @($test.Command) + $testArgs
    $scriptPath = Join-Path $scriptsRoot 'mc.ps1'
    $allArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$scriptPath`"") + $commandArgs
    $process = Start-Process -FilePath 'pwsh' -ArgumentList $allArgs -Wait -PassThru -NoNewWindow -WorkingDirectory $repoRoot
    
    if ($process.ExitCode -ne 0) {
        Write-Host "  FAILED: $($test.Description) (exit code: $($process.ExitCode))" -ForegroundColor Red
        $smokeFailed = $true
    }
    else {
        Write-Host "  PASSED: $($test.Description)" -ForegroundColor Green
    }
}

if ($smokeFailed) {
    Write-Host ""
    Write-Host "CLI smoke tests FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Quality Gate FAILED" -ForegroundColor Red
    exit 1
}
Write-Host "CLI smoke tests PASSED" -ForegroundColor Green
Write-Host ""

# 3. Formatting/Lint Placeholder
Write-Host "Step 3: Formatting/Lint checks..." -ForegroundColor Cyan
Write-Host "  (Placeholder for future linting implementation)" -ForegroundColor Yellow
Write-Host "  SKIPPED" -ForegroundColor Gray
Write-Host ""

# Success
Write-Host "=== Quality Gate PASSED ===" -ForegroundColor Green
exit 0
