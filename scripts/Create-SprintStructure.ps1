<#
=========================================================================
 Mission Control - Sprint Structure Generator
 Version : 1.0.0
 Author  : Robert Barnes

 Creates the documentation, backend, frontend and CI structure
 required for the next development sprint.

 Safe to run multiple times.
=========================================================================#
>

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Title)

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Ensure-Folder {
    param([string]$Path)

    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
        Write-Host "[Created] $Path" -ForegroundColor Green
    }
    else {
        Write-Host "[Exists ] $Path" -ForegroundColor DarkGray
    }
}

function Ensure-File {
    param(
        [string]$Path,
        [string]$Content = ""
    )

    if (!(Test-Path $Path)) {
        Set-Content -Path $Path -Value $Content -Encoding UTF8
        Write-Host "[Created] $Path" -ForegroundColor Green
    }
    else {
        Write-Host "[Exists ] $Path" -ForegroundColor DarkGray
    }
}

Write-Header "Mission Control - Creating Sprint Structure"

if (!(Test-Path ".git")) {
    Write-Host "Run this script from the MissionControl root folder." -ForegroundColor Red
    exit 1
}

# ============================================================
# Documentation
# ============================================================

Write-Header "Documentation"

$DocFolders = @(
    "docs/prompts",
    "docs/specifications",
    "docs/reviews",
    "docs/decisions",
    "docs/changelogs",
    "docs/sprints"
)

foreach ($folder in $DocFolders) {
    Ensure-Folder $folder
}

Ensure-File "docs/prompts/002-foundation-hardening.md"
Ensure-File "docs/specifications/Sprint-001.md"
Ensure-File "docs/reviews/Sprint-001-Review.md"
Ensure-File "docs/sprints/Sprint-001.md"

# ============================================================
# Backend
# ============================================================

Write-Header "Backend"

$BackendFolders = @(
    "backend/app/api/v1",
    "backend/app/api/v1/endpoints",
    "backend/app/core",
    "backend/app/db",
    "backend/app/middleware",
    "backend/app/repositories",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/workers",
    "backend/tests"
)

foreach ($folder in $BackendFolders) {
    Ensure-Folder $folder
}

$BackendInitFiles = @(
    "backend/app/api/v1/__init__.py",
    "backend/app/api/v1/endpoints/__init__.py",
    "backend/app/middleware/__init__.py",
    "backend/app/repositories/__init__.py",
    "backend/app/workers/__init__.py"
)

foreach ($file in $BackendInitFiles) {
    Ensure-File $file
}

Ensure-File "backend/app/core/logging.py"
Ensure-File "backend/app/core/security.py"
Ensure-File "backend/app/db/base.py"
Ensure-File "backend/app/db/session.py"

# ============================================================
# Frontend
# ============================================================

Write-Header "Frontend"

$FrontendFolders = @(
    "frontend/src/assets",
    "frontend/src/components",
    "frontend/src/layouts",
    "frontend/src/pages",
    "frontend/src/hooks",
    "frontend/src/contexts",
    "frontend/src/services",
    "frontend/src/types",
    "frontend/src/utils"
)

foreach ($folder in $FrontendFolders) {
    Ensure-Folder $folder
}

Ensure-File "frontend/src/components/.gitkeep"
Ensure-File "frontend/src/layouts/.gitkeep"
Ensure-File "frontend/src/pages/.gitkeep"
Ensure-File "frontend/src/hooks/.gitkeep"
Ensure-File "frontend/src/contexts/.gitkeep"
Ensure-File "frontend/src/services/.gitkeep"
Ensure-File "frontend/src/types/.gitkeep"
Ensure-File "frontend/src/utils/.gitkeep"

# ============================================================
# GitHub
# ============================================================

Write-Header "GitHub"

Ensure-Folder ".github/workflows"

Ensure-File ".github/workflows/ci.yml"

# ============================================================
# Docker
# ============================================================

Write-Header "Docker"

$DockerFolders = @(
    "docker/backend",
    "docker/frontend",
    "docker/postgres",
    "docker/redis",
    "docker/nginx"
)

foreach ($folder in $DockerFolders) {
    Ensure-Folder $folder
}

# ============================================================
# Templates
# ============================================================

Write-Header "Sprint Templates"

Ensure-File "docs/sprints/SPRINT_TEMPLATE.md" @"
# Sprint

## Objective

## Scope

## Deliverables

## Acceptance Criteria

## Risks

## Testing Checklist

## Review Notes

## Status
"@

Ensure-File "docs/reviews/REVIEW_TEMPLATE.md" @"
# Review

## Summary

## Architecture

## Security

## Code Quality

## Testing

## Recommendations

## Approved
"@

Ensure-File "docs/specifications/SPECIFICATION_TEMPLATE.md" @"
# Specification

## Overview

## Functional Requirements

## Technical Requirements

## Constraints

## Acceptance Criteria
"@

Write-Header "Repository Status"

git status

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Mission Control Sprint Structure Created"
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host " 1. Populate docs/prompts/002-foundation-hardening.md"
Write-Host " 2. Ask Codex to implement Sprint 1B"
Write-Host " 3. Review the changes"
Write-Host " 4. Test the application"
Write-Host ""