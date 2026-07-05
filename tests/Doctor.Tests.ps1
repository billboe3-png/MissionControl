Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptsRoot = Join-Path $repoRoot 'scripts'
$script:MissionControlScriptsRoot = $scriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Doctor' {
    BeforeAll {
    }
    It 'returns a doctor object' {
        $context = New-McContext -ScriptRoot $scriptsRoot -Arguments @('doctor')
        $result = Invoke-McDoctorCommand -Context $context

        $result.Type | Should Be 'Doctor'
        $result.OverallStatus | Should Not BeNullOrEmpty
        $result.Sections | Should Not BeNullOrEmpty
    }

    It 'returns valid JSON when output is json' {
        $context = New-McContext -ScriptRoot $scriptsRoot -Arguments @('doctor', '--output', 'json')
        $result = Invoke-McDoctorCommand -Context $context
        $json = $result | ConvertTo-Json -Depth 10
        { $json | ConvertFrom-Json | Out-Null } | Should Not Throw
    }
}
