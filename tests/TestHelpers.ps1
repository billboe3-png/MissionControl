$script:MissionControlScriptsRoot = if ($script:MissionControlScriptsRoot) { $script:MissionControlScriptsRoot } else {
    Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts'
}

$libPath = Join-Path $script:MissionControlScriptsRoot 'lib'
$commandPath = Join-Path $script:MissionControlScriptsRoot 'commands'

foreach ($libFile in @(
    'Registry.ps1',
    'Bootstrap.ps1',
    'Config.ps1',
    'Output.ps1',
    'Logger.ps1',
    'Validation.ps1',
    'Helpers.ps1',
    'Docker.ps1',
    'Git.ps1',
    'Http.ps1',
    'Doctor.ps1',
    'Version.ps1'
)) {
    . (Join-Path $libPath $libFile)
}

foreach ($commandFile in (Get-ChildItem -LiteralPath $commandPath -Filter '*.ps1' | Sort-Object Name)) {
    . $commandFile.FullName
}
