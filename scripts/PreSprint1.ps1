<#
=========================================================================
 Mission Control - Pre Sprint 1 Setup
 Version : 1.0.0
 Author  : Robert Barnes
 Purpose : Prepare the Mission Control repository for Sprint 1
=========================================================================

This script:

- Verifies you are in the MissionControl repository
- Creates documentation folders
- Creates prompt files
- Creates template files
- Creates a logs folder
- Creates or updates README.md
- Creates or updates .gitignore
- Displays repository status

This script is safe to run multiple times.
#>

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Ensure-Folder {
    param([string]$Path)

    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "[Created] Folder $Path" -ForegroundColor Green
    }
    else {
        Write-Host "[Exists ] Folder $Path" -ForegroundColor DarkGray
    }
}

function Ensure-File {
    param(
        [string]$Path,
        [string]$Content = ""
    )

    if (!(Test-Path $Path)) {
        Set-Content -Path $Path -Value $Content -Encoding UTF8
        Write-Host "[Created] File $Path" -ForegroundColor Green
    }
    else {
        Write-Host "[Exists ] File $Path" -ForegroundColor DarkGray
    }
}

Write-Section "Mission Control - Pre Sprint 1"

# -------------------------------------------------------------
# Validate repository
# -------------------------------------------------------------

if (!(Test-Path ".git")) {
    Write-Host ""
    Write-Host "ERROR: This is not the MissionControl repository." -ForegroundColor Red
    Write-Host "Run this script from C:\Projects\MissionControl" -ForegroundColor Yellow
    exit 1
}

# -------------------------------------------------------------
# Create folders
# -------------------------------------------------------------

Write-Section "Creating Folder Structure"

$Folders = @(
    "logs",

    "docs",
    "docs\adr",
    "docs\api",
    "docs\architecture",
    "docs\assets",
    "docs\database",
    "docs\planning",
    "docs\prompts",
    "docs\standards",
    "docs\templates"
)

foreach ($Folder in $Folders) {
    Ensure-Folder $Folder
}

# -------------------------------------------------------------
# Create Prompt Files
# -------------------------------------------------------------

Write-Section "Creating Prompt Files"

$PromptFiles = @(
    "docs\prompts\001-project-foundation.md",
    "docs\prompts\002-authentication.md",
    "docs\prompts\003-dashboard.md",
    "docs\prompts\004-projects.md",
    "docs\prompts\005-tasks.md",
    "docs\prompts\006-notes.md",
    "docs\prompts\007-focus-mode.md",
    "docs\prompts\008-resume-me.md",
    "docs\prompts\009-parking-lot.md",
    "docs\prompts\010-integrations.md"
)

foreach ($File in $PromptFiles) {
    Ensure-File $File
}

# -------------------------------------------------------------
# README
# -------------------------------------------------------------

Write-Section "Creating README"

$Readme = @"
# Mission Control

Mission Control is a personal productivity platform for senior IT professionals.

## Vision

One dashboard.

One workflow.

One place to manage everything.

## Planned Modules

- Dashboard
- Tasks
- Projects
- Notes
- Focus Mode
- Resume Me
- Parking Lot
- Microsoft 365
- Google Workspace
- Ticket System
- Zabbix
- AI Assistant

Current Status

Sprint 1 - Foundation
"@

Set-Content README.md $Readme -Encoding UTF8

# -------------------------------------------------------------
# .gitignore
# -------------------------------------------------------------

Write-Section "Creating .gitignore"

$GitIgnore = @"
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Node
node_modules/

# Environment
.env

# Logs
logs/
*.log

# VS Code
.vscode/settings.json

# Docker
*.pid

# Operating System
Thumbs.db
.DS_Store
"@

Set-Content .gitignore $GitIgnore -Encoding UTF8

# -------------------------------------------------------------
# ADR README
# -------------------------------------------------------------

Ensure-File "docs\adr\README.md" @"
# Architecture Decision Records

Create one file per architectural decision.

Example:

ADR-001-Modular-Monolith.md
ADR-002-JWT.md
ADR-003-PostgreSQL.md
"@

# -------------------------------------------------------------
# Meeting Template
# -------------------------------------------------------------

Ensure-File "docs\templates\meeting-template.md" @"
# Meeting Notes

Date:

Attendees:

Objectives:

Discussion:

Decisions:

Action Items:
"@

# -------------------------------------------------------------
# Prompt Template
# -------------------------------------------------------------

Ensure-File "docs\templates\prompt-template.md" @"
# Sprint Prompt

## Objective

## Requirements

## Deliverables

## Acceptance Criteria

## Constraints

## Definition of Done
"@

# -------------------------------------------------------------
# Repository Status
# -------------------------------------------------------------

Write-Section "Repository Status"

git status

Write-Host ""
Write-Host "Mission Control repository is ready for Sprint 1." -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Populate docs\prompts\001-project-foundation.md"
Write-Host "2. Open the project in Codex"
Write-Host "3. Ask Codex to implement Sprint 1"
Write-Host ""