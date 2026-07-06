Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptsRoot = Join-Path $repoRoot 'scripts'
$script:MissionControlScriptsRoot = $scriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Registry' {
    It 'contains expected commands' {
        $commands = Get-McRegisteredCommands
        $commands -contains 'doctor' | Should Be $true
        $commands -contains 'help' | Should Be $true
        $commands -contains 'status' | Should Be $true
        $commands -contains 'version' | Should Be $true
    }

    It 'returns metadata for registered commands' {
        $metadata = Get-McCommandMetadata -Name 'doctor'
        $metadata | Should Not BeNullOrEmpty
        $metadata.HandlerFunction | Should Be 'Invoke-McDoctorCommand'
    }

    It 'returns handler function name for registered commands' {
        $handler = Get-McCommandHandler -Name 'help'
        $handler | Should Be 'Invoke-McHelpCommand'
    }

    It 'returns null for unregistered commands' {
        $handler = Get-McCommandHandler -Name 'nonexistent'
        $handler | Should BeNullOrEmpty
    }
}
