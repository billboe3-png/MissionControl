# Restore Mission Control PostgreSQL database from backup
# Usage: .\scripts\restore-db.ps1 <backup_file.sql.gz>

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

if (-not (Test-Path $BackupFile)) {
    Write-Host "File not found: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "WARNING: This will REPLACE the entire mission_control database!" -ForegroundColor Yellow
$confirm = Read-Host "Type 'yes' to continue"
if ($confirm -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Gray
    exit 0
}

Write-Host "Dropping and recreating database..." -ForegroundColor Cyan
docker compose exec -T postgres psql -U mission_control -d postgres -c "DROP DATABASE IF EXISTS mission_control;"
docker compose exec -T postgres psql -U mission_control -d postgres -c "CREATE DATABASE mission_control OWNER mission_control;"

Write-Host "Restoring from $BackupFile..." -ForegroundColor Cyan
Get-Content $BackupFile | gunzip | docker compose exec -T postgres psql -U mission_control -d mission_control --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "Restore complete." -ForegroundColor Green
} else {
    Write-Host "Restore FAILED" -ForegroundColor Red
    exit 1
}
