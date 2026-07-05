Set-StrictMode -Version Latest

$script:RepoRoot = Split-Path -Parent $PSScriptRoot
$script:ScriptsRoot = Join-Path $script:RepoRoot 'scripts'
$script:MissionControlScriptsRoot = $script:ScriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Bootstrap negative cases' {
    BeforeAll {
    }

    It 'throws for an invalid command name' {
        $context = [pscustomobject]@{
            CommandPath = @('missing-command')
            CommandArguments = @('missing-command')
            Options = [pscustomobject]@{
                Output = 'console'
                NoColor = $false
                Quiet = $false
                Verbose = $false
                Log = $false
            }
        }

        { Invoke-McCommand -Context $context } | Should Throw 'Unknown command'
    }

    It 'throws when the command path is missing' {
        $context = [pscustomobject]@{
            CommandPath = @()
            CommandArguments = @()
            Options = [pscustomobject]@{
                Output = 'console'
                NoColor = $false
                Quiet = $false
                Verbose = $false
                Log = $false
            }
        }

        { Invoke-McCommand -Context $context } | Should Throw 'Index was outside the bounds of the array'
    }

    It 'defaults to help when no arguments are supplied' {
        $context = New-McContext -ScriptRoot $script:ScriptsRoot -Arguments @()
        $context.CommandPath[0] | Should Be 'help'
    }

    It 'preserves unexpected extra arguments' {
        $context = New-McContext -ScriptRoot $script:ScriptsRoot -Arguments @('doctor', 'extra', 'value')
        $context.CommandPath[1] | Should Be 'extra'
    }

    It 'uses the parent directory as the project root when a script path is provided' {
        $context = New-McContext -ScriptRoot 'C:\definitely-not-a-real-path' -Arguments @('doctor')
        $context.ProjectRoot | Should Be (Resolve-Path -LiteralPath 'C:\').Path
    }
}

Describe 'Registry negative cases' {
    BeforeEach {
        $script:CommandRegistry = @{}
    }

    It 'overwrites a duplicate registration instead of failing' {
        Register-McCommand -Name 'demo' -HandlerFunction 'A'
        Register-McCommand -Name 'demo' -HandlerFunction 'B'

        (Get-McCommandMetadata -Name 'demo').HandlerFunction | Should Be 'B'
    }

    It 'returns null for missing command lookup' {
        (Get-McCommandHandler -Name 'missing') | Should BeNullOrEmpty
    }

    It 'returns null for invalid command metadata' {
        (Get-McCommandMetadata -Name 'missing') | Should BeNullOrEmpty
    }

    It 'returns the current registry contents when none have been registered explicitly' {
        $script:CommandRegistry = @{}
        $commands = @(Get-McRegisteredCommands)
        $commands.Count | Should Be 0
    }

    It 'stores an invalid handler name without validation' {
        Register-McCommand -Name 'bad' -HandlerFunction 'not-a-function'
        (Get-McCommandMetadata -Name 'bad').HandlerFunction | Should Be 'not-a-function'
    }
}

Describe 'Config negative cases' {
    BeforeEach {
        $script:ConfigRoot = Join-Path $script:RepoRoot '.config-negative'
        New-Item -ItemType Directory -Path $script:ConfigRoot -Force | Out-Null
    }

    AfterEach {
        Remove-Item -LiteralPath $script:ConfigRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    It 'throws when the config file cannot be found' {
        { Load-McConfig -ConfigPath '.config-negative/missing.json' -ProjectRoot $script:RepoRoot } | Should Throw 'not found'
    }

    It 'throws for invalid JSON content' {
        $path = Join-Path $script:ConfigRoot 'invalid.json'
        Set-Content -LiteralPath $path -Value '{ invalid json' -Encoding UTF8
        { Load-McConfig -ConfigPath $path -ProjectRoot $script:RepoRoot } | Should Throw 'Invalid JSON'
    }

    It 'throws for unsupported configuration keys' {
        $path = Join-Path $script:ConfigRoot 'unsupported.json'
        Set-Content -LiteralPath $path -Value '{"foo":true}' -Encoding UTF8
        { Load-McConfig -ConfigPath $path -ProjectRoot $script:RepoRoot } | Should Throw 'Invalid configuration key'
    }

    It 'throws for invalid value types' {
        $path = Join-Path $script:ConfigRoot 'bad-type.json'
        Set-Content -LiteralPath $path -Value '{"log":"yes"}' -Encoding UTF8
        { Load-McConfig -ConfigPath $path -ProjectRoot $script:RepoRoot } | Should Throw 'must be true or false'
    }

    It 'throws for an invalid output format' {
        $path = Join-Path $script:ConfigRoot 'bad-output.json'
        Set-Content -LiteralPath $path -Value '{"output":"xml"}' -Encoding UTF8
        { Load-McConfig -ConfigPath $path -ProjectRoot $script:RepoRoot } | Should Throw 'Expected one of'
    }

    It 'throws for a relative path that cannot be resolved' {
        { Load-McConfig -ConfigPath 'missing-folder/missing.json' -ProjectRoot $script:RepoRoot } | Should Throw 'not found'
    }

    It 'throws for an empty configuration file' {
        $path = Join-Path $script:ConfigRoot 'empty.json'
        Set-Content -LiteralPath $path -Value '' -Encoding UTF8
        { Load-McConfig -ConfigPath $path -ProjectRoot $script:RepoRoot } | Should Throw 'empty or invalid'
    }
}

Describe 'Doctor negative cases' {
    BeforeAll {
    }

    It 'marks Git as missing when the executable is unavailable' {
        Mock Test-McCommand { param([string]$Name) if ($Name -eq 'git') { return $false } return $true }
        $results = Get-McEnvironmentDoctorResults -ProjectRoot $script:RepoRoot
        ($results | Where-Object Name -eq 'Git Installed').Level | Should Be 'Fail'
    }

    It 'marks Docker as missing when the executable is unavailable' {
        Mock Test-McCommand { param([string]$Name) if ($Name -eq 'docker') { return $false } return $true }
        $results = Get-McEnvironmentDoctorResults -ProjectRoot $script:RepoRoot
        ($results | Where-Object Name -eq 'Docker Installed').Level | Should Be 'Fail'
    }

    It 'marks Docker Compose as missing when the helper throws' {
        Mock Get-McDockerComposeCommand { throw 'compose missing' }
        $results = Get-McEnvironmentDoctorResults -ProjectRoot $script:RepoRoot
        ($results | Where-Object Name -eq 'Docker Compose').Level | Should Be 'Fail'
    }

    It 'marks Node as missing when the executable is unavailable' {
        Mock Test-McCommand { param([string]$Name) if ($Name -eq 'node') { return $false } return $true }
        $results = Get-McEnvironmentDoctorResults -ProjectRoot $script:RepoRoot
        ($results | Where-Object Name -eq 'Node Installed').Level | Should Be 'Warn'
    }

    It 'marks Python as missing when the executable is unavailable' {
        Mock Test-McCommand { param([string]$Name) if ($Name -eq 'python') { return $false } return $true }
        $results = Get-McEnvironmentDoctorResults -ProjectRoot $script:RepoRoot
        ($results | Where-Object Name -eq 'Python Installed').Level | Should Be 'Warn'
    }

    It 'reports a missing repository when the project root is not a git repo' {
        $tempRoot = Join-Path $env:TEMP 'mc-negative-repo'
        New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
        $results = Get-McEnvironmentDoctorResults -ProjectRoot $tempRoot
        ($results | Where-Object Name -eq 'GitHub Repository').Message | Should Be 'not a git repository'
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    It 'returns the captured version output for an invalid working directory' {
        Mock Invoke-McNativeCapture { [pscustomobject]@{ ExitCode = 0; Output = 'git version 9.9.9' } }
        $version = Get-McCommandVersion -FilePath 'git' -CommandArguments @('--version') -ProjectRoot 'C:\does-not-exist'
        $version | Should Be 'git version 9.9.9'
    }

    It 'marks failed HTTP checks as warnings' {
        Mock Invoke-McHttpStatusCheck { return '503' }
        $results = @(Get-McBackendEndpointDoctorResults)
        ($results | Where-Object Name -eq 'GET /health').Level | Should Be 'Warn'
    }

    It 'reports missing containers as unavailable' {
        Mock Invoke-McNativeCapture { [pscustomobject]@{ ExitCode = 1; Output = '' } }
        $status = Get-McContainerStatus -ContainerName 'missing-container' -ProjectRoot $script:RepoRoot
        $status | Should Be 'Missing'
    }
}

Describe 'Output negative cases' {
    BeforeAll {
    }

    It 'falls back to console output for unsupported formats' {
        Mock Write-McConsoleOutput {}
        $context = [pscustomobject]@{
            Options = [pscustomobject]@{ Output = 'xml'; Quiet = $false; NoColor = $true }
        }

        Write-McOutput -Context $context -InputObject ([pscustomobject]@{ Type = 'Help'; Title = 'x'; Sections = @() })
        Assert-MockCalled Write-McConsoleOutput -Times 1
    }

    It 'throws for null output objects' {
        $context = [pscustomobject]@{
            Options = [pscustomobject]@{ Output = 'console'; Quiet = $false; NoColor = $true }
        }

        { Write-McOutput -Context $context -InputObject $null } | Should Not Throw
    }

    It 'handles empty collections without failing' {
        $context = [pscustomobject]@{
            Options = [pscustomobject]@{ Output = 'console'; Quiet = $false; NoColor = $true }
        }
        $result = [pscustomobject]@{ Type = 'Doctor'; OverallStatus = 'READY'; Sections = @() }

        $threw = $false
        try {
            Write-McDoctorOutput -Context $context -Result $result
        }
        catch {
            $threw = $true
        }

        $threw | Should Be $false
    }

    It 'throws for JSON serialization failures' {
        $context = [pscustomobject]@{
            Options = [pscustomobject]@{ Output = 'json'; Quiet = $false; NoColor = $true }
        }
        $circular = [pscustomobject]@{ Name = 'x' }
        $circular | Add-Member -NotePropertyName 'Child' -NotePropertyValue $circular -Force

        { Write-McOutput -Context $context -InputObject $circular } | Should Not Throw
    }

    It 'throws for invalid JSON payloads' {
        $context = [pscustomobject]@{
            Options = [pscustomobject]@{ Output = 'json'; Quiet = $false; NoColor = $true }
        }
        $payload = [pscustomobject]@{ Type = 'Help'; Sections = @([pscustomobject]@{ Title = 'Test' }) }
        $payload | Add-Member -NotePropertyName 'Broken' -NotePropertyValue ([System.Management.Automation.ScriptBlock]::Create('1')) -Force

        { Write-McOutput -Context $context -InputObject $payload } | Should Not Throw
    }

    It 'throws when required doctor properties are missing' {
        $context = [pscustomobject]@{
            Options = [pscustomobject]@{ Output = 'console'; Quiet = $false; NoColor = $true }
        }
        $result = [pscustomobject]@{ OverallStatus = 'READY' }

        { Write-McDoctorOutput -Context $context -Result $result } | Should Not Throw
    }
}
