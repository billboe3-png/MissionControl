Set-StrictMode -Version Latest

Describe 'Registry' {
    BeforeAll {
        $repoRoot = Split-Path -Parent $PSScriptRoot
        $scriptsRoot = Join-Path $repoRoot 'scripts'
        $scriptPath = Join-Path $scriptsRoot 'mc.ps1'
        . $scriptPath
    }
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
}
