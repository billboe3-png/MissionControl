Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptsRoot = Join-Path $repoRoot 'scripts'
$script:MissionControlScriptsRoot = $scriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Helpers' {
    Context 'New-McPlaceholderResult' {
        It 'creates a placeholder result object' {
            $result = New-McPlaceholderResult -Name 'test'
            $result | Should Not BeNullOrEmpty
            $result.Type | Should Be 'Placeholder'
            $result.Message | Should Match 'test'
            $result.Message | Should Match 'future sprint'
        }

        It 'includes command name in message' {
            $result = New-McPlaceholderResult -Name 'build'
            $result.Message | Should Match 'build'
        }
    }

    Context 'Invoke-McNativeCapture' {
        It 'captures output from native command' {
            $tempDir = Join-Path $env:TEMP "mc-test-$(Get-Random)"
            New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
            
            try {
                $result = Invoke-McNativeCapture -FilePath 'cmd' -CommandArguments @('/c', 'echo', 'test content') -WorkingDirectory $tempDir
                
                $result | Should Not BeNullOrEmpty
                $result.ExitCode | Should Be 0
                $result.Output | Should Match 'test content'
            }
            finally {
                Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
            }
        }

        It 'returns non-zero exit code on failure' {
            $tempDir = Join-Path $env:TEMP "mc-test-$(Get-Random)"
            New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
            
            try {
                $result = Invoke-McNativeCapture -FilePath 'cmd' -CommandArguments @('/c', 'exit', '1') -WorkingDirectory $tempDir
                
                $result | Should Not BeNullOrEmpty
                $result.ExitCode | Should Not Be 0
            }
            finally {
                Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    Context 'Get-McProjectRoot' {
        It 'resolves project root from scripts directory' {
            $scriptsRoot = Join-Path $repoRoot 'scripts'
            $projectRoot = Get-McProjectRoot -ScriptRoot $scriptsRoot
            
            $projectRoot | Should Be $repoRoot
        }
    }
}
