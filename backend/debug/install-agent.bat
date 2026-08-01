@echo off
setlocal enabledelayedexpansion

:: Mission Control Agent Installer for Windows
:: Usage: install-agent.bat <AgentId> <ApiKey> [ServerUrl] [InstallDir]
if "%~1"=="" (
    echo ERROR: Agent ID required
    echo Usage: %~nx0 ^<AgentId^> ^<ApiKey^> [ServerUrl] [InstallDir]
    pause
    exit /b 1
)
if "%~2"=="" (
    echo ERROR: API key required
    echo Usage: %~nx0 ^<AgentId^> ^<ApiKey^> [ServerUrl] [InstallDir]
    pause
    exit /b 1
)

set AGENT_ID=%~1
set API_KEY=%~2
set SERVER_URL=%~3
if "%SERVER_URL%"=="" set SERVER_URL=https://missioncontrol.optichosting.co.za
set INSTALL_DIR=%~4
if "%INSTALL_DIR%"=="" set INSTALL_DIR=C:\MissionControlAgent

echo.
echo ========================================
echo  Mission Control Agent Installer
echo ========================================
echo.
echo  Agent ID : %AGENT_ID%
echo  Server   : %SERVER_URL%
echo  Install  : %INSTALL_DIR%
echo.

set PYTHON=C:\Users\robert\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PYTHON%" set PYTHON=py -3

echo [1/5] Preparing directories...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\agent" mkdir "%INSTALL_DIR%\agent"
echo   Done.

echo [2/5] Downloading agent package...
set ZIP_PATH=%INSTALL_DIR%\agent-bundle.zip
curl.exe -sSf -k -X POST -H "Content-Type: application/json" -H "X-Agent-API-Key: %API_KEY%" -d "{\"agent_id\":%AGENT_ID%}" -o "%ZIP_PATH%" "%SERVER_URL%/api/v1/agents/%AGENT_ID%/bundles/download"
if not exist "%ZIP_PATH%" (
    echo ERROR: Download failed. Check network, server URL, and API key.
    pause
    exit /b 1
)
for %%A in ("%ZIP_PATH%") do set SIZE=%%~zA
echo   Downloaded: !SIZE! bytes
if !SIZE! LSS 1000 (
    echo ERROR: Downloaded file too small. Check auth/network.
    pause
    exit /b 1
)

echo [3/5] Installing files...
powershell -Command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%INSTALL_DIR%' -Force"
if not exist "%INSTALL_DIR%\agent\agent.py" (
    echo   Fixing bundle structure...
    powershell -Command "$root='%INSTALL_DIR%'; $pkg=Join-Path $root 'agent'; Get-ChildItem $root -Filter *.py | Move-Item -Destination $pkg -Force; Get-ChildItem $root -Directory | Where-Object { $_.Name -ne 'agent' -and $_.Name -ne 'logs' } | Move-Item -Destination $pkg -Force"
)
del /f "%ZIP_PATH%" >nul 2>&1
echo   Done.

echo [4/5] Writing configuration...
set CONFIG_PATH=%INSTALL_DIR%\config.yaml
(
echo server_url: %SERVER_URL%
echo agent_id: %AGENT_ID%
echo api_key: %API_KEY%
echo heartbeat_interval: 30
echo log_file: %INSTALL_DIR%\logs\agent.log
echo verify_ssl: false
) > "%CONFIG_PATH%"
echo   Config: %CONFIG_PATH%

echo [5/5] Registering scheduled task...
set BAT_PATH=%INSTALL_DIR%\run-agent.bat
(
echo @echo off
echo cd /d %INSTALL_DIR%
echo "%PYTHON%" -m agent --config "%CONFIG_PATH%" --log-file "%INSTALL_DIR%\logs\agent.log"
) > "%BAT_PATH%"

schtasks /Delete /TN "MissionControlAgent" /F >nul 2>&1
schtasks /Create /TN "MissionControlAgent" /TR "cmd /c \"%BAT_PATH%\"" /SC ONSTART /RU SYSTEM /F
if errorlevel 1 (
    echo ERROR: Failed to create scheduled task. Run this script as Administrator.
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
schtasks /Run /TN "MissionControlAgent" >nul 2>&1

echo.
echo ========================================
echo  Installation complete
echo ========================================
echo.
echo  Verify with:
echo    schtasks /Query /TN "MissionControlAgent" /FO LIST /V
echo    type "%INSTALL_DIR%\logs\agent.log" ^| findstr /C:"heartbeat" /C:"Registered"
echo.
pause
