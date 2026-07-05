Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptsRoot = Join-Path $repoRoot 'scripts'
$script:MissionControlScriptsRoot = $scriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Output' {
    BeforeAll {
    }
    It 'returns a Help object for help output' {
        $context = New-McContext -ScriptRoot $scriptsRoot -Arguments @('help')
        $result = Invoke-McHelpCommand -Context $context
        $result.Type | Should Be 'Help'
        $result.Sections | Should Not BeNullOrEmpty
    }

    It 'returns a Version object for version output' {
        $context = New-McContext -ScriptRoot $scriptsRoot -Arguments @('version')
        $result = Invoke-McVersionCommand -Context $context
        $result.Type | Should Be 'Version'
        $result.Version | Should Not BeNullOrEmpty
    }

    It 'returns a Status object for status output' {
        $context = New-McContext -ScriptRoot $scriptsRoot -Arguments @('status')
        $result = Invoke-McStatusCommand -Context $context
        $result.Type | Should Be 'Status'
        $result.Items | Should Not BeNullOrEmpty
    }
}
