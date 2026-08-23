$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Core
$ProgressPreference = 'SilentlyContinue'
$apiKey = 'mc_agent_aee5599672def0e225d8aa73a2d1f1ef2bf5b03e33355a5e241d40697d6163f9'
$base = 'https://missioncontrol.optichosting.co.za/api/v1/agents/1/plugins'
$local = 'C:\MissionControlAgent\agent'
$plugins = @('veeam','windows','hyperv','docker','zabbix','active_directory','microsoft_365','proxmox','windows_docker','linux')
$site = python -c "import site,json; print(site.getsitepackages()[1])"
$sys = Join-Path $site 'agent'
foreach ($p in $plugins) {
  $url = "$base/$p"
  $tmp = [IO.Path]::GetTempFileName()
  curl.exe -sSf -k -H "X-Agent-API-Key: $apiKey" -o $tmp $url
  if (-not (Test-Path $tmp)) { continue }
  $content = [IO.File]::ReadAllText($tmp)
  if (-not $content) { Remove-Item $tmp -Force; continue }
  $name = '{0}_plugin.py' -f $p
  $targets = @(Join-Path $local (Join-Path 'plugins' $name))
  if ($p -in @('windows','hyperv','docker','zabbix','active_directory','microsoft_365','proxmox','windows_docker','linux')) {
    $targets += Join-Path $sys (Join-Path 'plugins' $name)
  } else {
    $targets += Join-Path $sys $name
  }
  foreach ($t in $targets) {
    $dir = Split-Path $t
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [IO.File]::WriteAllText($t, $content)
  }
  Remove-Item $tmp -Force
}
$initLocal = Join-Path $local '__init__.py'
$initSys = Join-Path $sys '__init__.py'
$ver = "`r`n__version__ = `"3.0.0-rc1`"`r`n"
if (Test-Path $initLocal) {
  $c = Get-Content $initLocal -Raw
  $c = $c -replace '(?m)^__version__\s*=\s*.*$',''
  Set-Content -Path $initLocal -Value $c -NoNewline
  Add-Content -Path $initLocal -Value $ver
}
if (Test-Path $initSys) {
  $c = Get-Content $initSys -Raw
  $c = $c -replace '(?m)^__version__\s*=\s*.*$',''
  Set-Content -Path $initSys -Value $c -NoNewline
  Add-Content -Path $initSys -Value $ver
}
schtasks /End /TN 'MissionControlAgent'
Start-Sleep -Seconds 5
schtasks /Run /TN 'MissionControlAgent'
