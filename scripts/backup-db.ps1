# Backup Mission Control PostgreSQL database
# Usage: .\scripts\backup-db.ps1 [output_dir]

param(
    [string]$OutputDir = "backups",
    [string]$ProjectName = $env:COMPOSE_PROJECT_NAME,
    [string]$Database = $env:POSTGRES_DB,
    [string]$Username = $env:POSTGRES_USER
)

if (-not $ProjectName) {
    Write-Host "ERROR: Set COMPOSE_PROJECT_NAME or pass -ProjectName (missioncontrol-live | missioncontrol-dev)" -ForegroundColor Red
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outPath = Join-Path $OutputDir "missioncontrol_${ProjectName}_${timestamp}.sql.gz"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "Backing up Mission Control database..." -ForegroundColor Cyan
Write-Host "  Project : $ProjectName" -ForegroundColor DarkGray
Write-Host "  Database: $Database" -ForegroundColor DarkGray

docker compose `
  --project-name "$ProjectName" `
  exec -T postgres pg_dump -U "$Username" -d "$Database" --no-owner --no-privileges | gzip > $outPath

if ($LASTEXITCODE -eq 0) {
    $size = (Get-Item $outPath).Length / 1KB
    Write-Host "Backup saved: $outPath ($([math]::Round($size, 1)) KB)" -ForegroundColor Green
} else {
    Write-Host "Backup FAILED" -ForegroundColor Red
    exit 1
}
