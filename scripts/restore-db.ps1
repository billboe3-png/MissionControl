# Restore Mission Control PostgreSQL database from backup
# Usage: .\scripts\restore-db.ps1 <backup_file.sql.gz>

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$ProjectName = $env:COMPOSE_PROJECT_NAME,
    [string]$Database = $env:POSTGRES_DB,
    [string]$Username = $env:POSTGRES_USER
)

if (-not $ProjectName) {
    Write-Host "ERROR: Set COMPOSE_PROJECT_NAME or pass -ProjectName (missioncontrol-live | missioncontrol-dev)" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $BackupFile)) {
    Write-Host "File not found: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "WARNING: This will REPLACE the entire $Database database in project $ProjectName!" -ForegroundColor Yellow
$confirm = Read-Host "Type 'yes' to continue"
if ($confirm -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Gray
    exit 0
}

Write-Host "Dropping and recreating database..." -ForegroundColor Cyan
docker compose `
  --project-name "$ProjectName" `
  exec -T postgres psql -U "$Username" -d postgres -c "DROP DATABASE IF EXISTS $Database;"
docker compose `
  --project-name "$ProjectName" `
  exec -T postgres psql -U "$Username" -d postgres -c "CREATE DATABASE $Database OWNER $Username;"

Write-Host "Restoring from $BackupFile..." -ForegroundColor Cyan
Get-Content $BackupFile | gunzip | docker compose `
  --project-name "$ProjectName" `
  exec -T postgres psql -U "$Username" -d "$Database" --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "Restore complete." -ForegroundColor Green
} else {
    Write-Host "Restore FAILED" -ForegroundColor Red
    exit 1
}
