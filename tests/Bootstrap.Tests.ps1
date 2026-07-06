Set-StrictMode -Version Latest

$script:RepoRoot = Split-Path -Parent $PSScriptRoot
$script:ScriptsRoot = Join-Path $script:RepoRoot 'scripts'
$script:MissionControlScriptsRoot = $script:ScriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Bootstrap' {
    BeforeAll {
        $configDirectory = Join-Path $script:RepoRoot '.config'
        New-Item -ItemType Directory -Path $configDirectory -Force | Out-Null
        $configPath = Join-Path $configDirectory 'mc.json'
        '{"output":"json","log":true,"noColor":true}' | Set-Content -LiteralPath $configPath -Encoding UTF8
    }
    It 'creates a context with parsed options' {
        $configPath = Join-Path $script:RepoRoot '.config/mc.json'
        $context = New-McContext -ScriptRoot $script:ScriptsRoot -Arguments @('doctor', '--output', 'json', '--config', $configPath)

        $context | Should Not BeNullOrEmpty
        $context.CommandPath[0] | Should Be 'doctor'
        $context.Options.Output | Should Be 'json'
        $context.ConfigPath | Should Be $configPath
    }

    It 'treats help as a command path when no command is provided' {
        $context = New-McContext -ScriptRoot $script:ScriptsRoot -Arguments @('--help')
        $context.CommandPath[0] | Should Be 'help'
        $context.Options.Help | Should Be $true
    }

    It 'dispatches command to registered handler' {
        $context = New-McContext -ScriptRoot $script:ScriptsRoot -Arguments @('version')
        $result = Invoke-McCommand -Context $context
        $result | Should Not BeNullOrEmpty
        $result.Type | Should Be 'Version'
    }

    It 'throws for unknown command' {
        $context = New-McContext -ScriptRoot $script:ScriptsRoot -Arguments @('nonexistent')
        { Invoke-McCommand -Context $context } | Should Throw "Unknown command 'nonexistent'"
    }
}
