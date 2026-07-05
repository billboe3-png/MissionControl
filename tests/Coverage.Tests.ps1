Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptsRoot = Join-Path $repoRoot 'scripts'
$script:MissionControlScriptsRoot = $scriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Coverage completion' {
    BeforeAll {
    }

    It 'covers verbose, quiet, debug, no-color, log, and config option parsing' {
        $configDirectory = Join-Path $repoRoot '.config'
        New-Item -ItemType Directory -Path $configDirectory -Force | Out-Null
        $configPath = Join-Path $configDirectory 'mc.json'
        '{"output":"json","log":true,"noColor":true}' | Set-Content -LiteralPath $configPath -Encoding UTF8

        $context = New-McContext -ScriptRoot $scriptsRoot -Arguments @('--verbose', '--quiet', '--debug', '--no-color', '--log', '--output', 'json', '--config', $configPath)
        $context.Options.Verbose | Should Be $true
        $context.Options.Quiet | Should Be $true
        $context.Options.Debug | Should Be $true
        $context.Options.NoColor | Should Be $true
        $context.Options.Log | Should Be $true
        $context.Options.Output | Should Be 'json'
    }

    It 'throws when --output is missing its value' {
        { Split-McArguments -Arguments @('--output') } | Should Throw 'Missing value for --output'
    }

    It 'throws when --output uses an invalid value' {
        { Split-McArguments -Arguments @('--output', 'xml') } | Should Throw 'Unsupported output format'
    }

    It 'throws when --config is missing its value' {
        { Split-McArguments -Arguments @('--config') } | Should Throw 'Missing value for --config'
    }

    It 'dispatches the resolved handler for a command path' {
        Register-McCommand -Name 'sample' -HandlerFunction 'Invoke-McStatusCommand'
        $context = [pscustomobject]@{
            ProjectRoot = $repoRoot
            CommandPath = @('sample')
            CommandArguments = @()
            Options = [pscustomobject]@{ Output = 'console'; Quiet = $false; NoColor = $true; Log = $false; Verbose = $false }
        }
        $result = Invoke-McCommand -Context $context
        $result.Type | Should Be 'Status'
    }

    It 'validates argument counts and executable requirements' {
        { Assert-McArgumentCount -Arguments @('a') -Minimum 2 -Usage 'mc test' } | Should Throw 'Invalid arguments'
        { Assert-McExecutable -Name 'this-command-should-not-exist' } | Should Throw 'not found on PATH'
    }

    It 'validates git repository roots' {
        $tempRoot = Join-Path $env:TEMP 'mc-coverage-repo'
        New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
        { Assert-McGitRepository -ProjectRoot $tempRoot } | Should Throw 'not a Git repository'
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    It 'initializes and writes logs for info, debug, error, and quiet modes' {
        $context = [pscustomobject]@{
            ProjectRoot = $repoRoot
            Options = [pscustomobject]@{ Log = $true; Quiet = $false; Verbose = $false; NoColor = $true }
            LogFile = $null
        }
        Initialize-McLogger -Context $context
        $context.LogFile | Should Not BeNullOrEmpty
        Write-McLog -Context $context -Level INFO -Message 'info message'
        Write-McLog -Context $context -Level DEBUG -Message 'debug message'
        Write-McLog -Context $context -Level ERROR -Message 'error message'
        $context.Options.Quiet = $true
        Write-McLog -Context $context -Level INFO -Message 'quiet message'
        (Get-Content -LiteralPath $context.LogFile | Select-Object -Last 4) | Should Not BeNullOrEmpty
    }

    It 'covers helper placeholder and color output helpers' {
        $result = New-McPlaceholderResult -Name 'demo'
        $result.Type | Should Be 'Placeholder'
        { Invoke-McPlaceholder -Name 'demo' } | Should Not Throw
        Write-McColorLine -Context ([pscustomobject]@{ Options = [pscustomobject]@{ NoColor = $true } }) -Message 'hello' -Color Green
    }

    It 'covers docker compose detection and status helpers' {
        Mock Get-Command { param([string]$Name) if ($Name -eq 'docker') { return 'docker' } return $null }
        Mock Invoke-McNativeCommand {}
        Mock Invoke-McNativeCapture { [pscustomobject]@{ ExitCode = 0; Output = 'ok' } }
        $compose = Get-McDockerComposeCommand
        $compose.FilePath | Should Be 'docker'
        Invoke-McDockerCompose -ProjectRoot $repoRoot -ComposeArguments @('ps')
        Invoke-McDockerComposeCapture -ProjectRoot $repoRoot -ComposeArguments @('ps')
        Get-McDockerComposeStatus | Should Be 'docker available'
    }

    It 'covers git status and commit paths' {
        Mock Assert-McExecutable {}
        Mock Assert-McGitRepository {}
        Mock Invoke-McNativeCommand {}
        Invoke-McGitStatus -ProjectRoot $repoRoot
        { Invoke-McGitCommit -ProjectRoot $repoRoot -Message 'ab' } | Should Throw 'Commit message must be at least 3 characters'
        { Invoke-McGitCommit -ProjectRoot $repoRoot -Message 'valid message' -WhatIf:$false } | Should Not Throw
    }

    It 'covers output rendering for console, json, json-pretty, help, status, doctor, action, error, and raw' {
        $context = [pscustomobject]@{
            Options = [pscustomobject]@{ Output = 'console'; Quiet = $false; NoColor = $true }
        }
        Write-McOutput -Context $context -InputObject ([pscustomobject]@{ Type = 'Help'; Title = 'x'; Sections = @([pscustomobject]@{ Title = 't'; Color = 'Cyan'; Lines = @('line') }) })
        $context.Options.Output = 'json'
        Write-McOutput -Context $context -InputObject ([pscustomobject]@{ Type = 'Status'; Items = @() })
        $context.Options.Output = 'json-pretty'
        Write-McOutput -Context $context -InputObject ([pscustomobject]@{ Type = 'Version'; Version = '1.0'; Message = 'm' })
        Write-McConsoleOutput -Context $context -InputObject ([pscustomobject]@{ Type = 'Raw'; Output = 'raw' })
        Write-McConsoleOutput -Context $context -InputObject ([pscustomobject]@{ Type = 'Error'; Error = 'oops' })
        Write-McHelpOutput -Context $context -Result ([pscustomobject]@{ Title = 't'; Sections = @([pscustomobject]@{ Title = 's'; Color = 'Cyan'; Lines = @('l') }) })
        Write-McStatusOutput -Context $context -Result ([pscustomobject]@{ Items = @([pscustomobject]@{ Name = 'a'; Value = 'b' }) })
        Write-McDoctorOutput -Context $context -Result ([pscustomobject]@{ OverallStatus = 'READY'; Sections = @([pscustomobject]@{ Name = 's'; Checks = @([pscustomobject]@{ Level = 'Pass'; Name = 'n'; Message = 'm' }) }) })
        Write-McActionOutput -Context $context -Result ([pscustomobject]@{ Messages = @([pscustomobject]@{ Level = 'SUCCESS'; Message = 'done' }); Output = 'out' })
    }

    It 'covers doctor branch states and version detection' {
        Mock Test-McCommand { param([string]$Name) if ($Name -eq 'docker') { return $true } return $false }
        Mock Invoke-McNativeCapture {
            param([string]$FilePath, [string[]]$CommandArguments, [string]$WorkingDirectory)
            if ($CommandArguments -contains 'info') { return [pscustomobject]@{ ExitCode = 0; Output = '' } }
            if ($CommandArguments[0] -eq 'inspect') { return [pscustomobject]@{ ExitCode = 0; Output = 'running|healthy' } }
            return [pscustomobject]@{ ExitCode = 0; Output = '1.2.3' }
        }
        Get-McContainerStatus -ContainerName 'x' -ProjectRoot $repoRoot | Should Be 'Healthy'
        Mock Invoke-McNativeCapture {
            param([string]$FilePath, [string[]]$CommandArguments, [string]$WorkingDirectory)
            if ($CommandArguments[0] -eq 'inspect') { return [pscustomobject]@{ ExitCode = 0; Output = 'running|unhealthy' } }
            return [pscustomobject]@{ ExitCode = 0; Output = '1.2.3' }
        }
        Get-McContainerStatus -ContainerName 'x' -ProjectRoot $repoRoot | Should Be 'Unhealthy'
        Mock Invoke-McNativeCapture { [pscustomobject]@{ ExitCode = 0; Output = 'restarting' } }
        Get-McContainerStatus -ContainerName 'x' -ProjectRoot $repoRoot | Should Be 'Restarting'
        Mock Invoke-McNativeCapture { [pscustomobject]@{ ExitCode = 1; Output = '' } }
        Get-McContainerStatus -ContainerName 'x' -ProjectRoot $repoRoot | Should Be 'Missing'
    }
}
