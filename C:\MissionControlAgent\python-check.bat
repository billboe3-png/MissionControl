@echo off
cd /d C:\MissionControlAgent
"C:\Users\robert\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" -c "import sys; print('Python:', sys.executable); print('Version:', sys.version)" > "C:\MissionControlAgent\python-check.log" 2>&1
echo Exit: %ERRORLEVEL% >> "C:\MissionControlAgent\python-check.log"
