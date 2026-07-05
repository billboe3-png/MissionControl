Set-StrictMode -Version Latest

$script:RepoRoot = Split-Path -Parent $PSScriptRoot
$script:ScriptsRoot = Join-Path $script:RepoRoot 'scripts'
$script:MissionControlScriptsRoot = $script:ScriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Config' {
    BeforeAll {
        $configDirectory = Join-Path $script:RepoRoot '.config'
        New-Item -ItemType Directory -Path $configDirectory -Force | Out-Null

        $configPath = Join-Path $configDirectory 'test-config.json'
        '{"output":"json","log":true,"noColor":true}' | Set-Content -LiteralPath $configPath -Encoding UTF8

        $invalidConfigPath = Join-Path $configDirectory 'invalid-config.json'
        '{"output":"xml"}' | Set-Content -LiteralPath $invalidConfigPath -Encoding UTF8
    }

    AfterAll {
        Remove-Item -LiteralPath (Join-Path $script:RepoRoot '.config') -Recurse -Force -ErrorAction SilentlyContinue
    }

    It 'loads a configuration file' {
        $config = Load-McConfig -ConfigPath '.config/test-config.json' -ProjectRoot $script:RepoRoot
        $config.output | Should Be 'json'
        $config.log | Should Be $true
        $config.noColor | Should Be $true
    }

    It 'applies config precedence over defaults' {
        $options = [pscustomobject]@{
            Help = $false
            Verbose = $false
            Quiet = $false
            Debug = $false
            Output = 'console'
            NoColor = $false
            Log = $false
            Config = '.config/test-config.json'
            Explicit = [pscustomobject]@{
                Output = $false
                NoColor = $false
                Log = $false
                Config = $false
            }
        }

        $merged = Merge-McConfigOptions -Options $options -Config (Load-McConfig -ConfigPath '.config/test-config.json' -ProjectRoot $script:RepoRoot)
        $merged.Output | Should Be 'json'
        $merged.Log | Should Be $true
        $merged.NoColor | Should Be $true
    }

    It 'throws for invalid configuration values' {
        { Load-McConfig -ConfigPath '.config/invalid-config.json' -ProjectRoot $script:RepoRoot } | Should Throw 'output'
    }
}
