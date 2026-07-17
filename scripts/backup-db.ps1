# Backup Mission Control PostgreSQL database
# Usage: .\scripts\backup-db.ps1 [output_dir]

param(
    [string]$OutputDir = "backups"
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outPath = Join-Path $OutputDir "missioncontrol_$timestamp.sql.gz"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "Backing up Mission Control database..." -ForegroundColor Cyan

docker compose exec -T postgres pg_dump -U mission_control -d mission_control --no-owner --no-privileges | gzip > $outPath

if ($LASTEXITCODE -eq 0) {
    $size = (Get-Item $outPath).Length / 1KB
    Write-Host "Backup saved: $outPath ($([math]::Round($size, 1)) KB)" -ForegroundColor Green
} else {
    Write-Host "Backup FAILED" -ForegroundColor Red
    exit 1
}
