Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptsRoot = Join-Path $repoRoot 'scripts'
$script:MissionControlScriptsRoot = $scriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Validation' {
    Context 'Assert-McArgumentCount' {
        It 'passes when argument count meets minimum' {
            $arguments = @('command', 'arg1', 'arg2')
            { Assert-McArgumentCount -Arguments $arguments -Minimum 2 -Usage 'test' } | Should Not Throw
        }

        It 'throws when argument count is below minimum' {
            $arguments = @('command')
            { Assert-McArgumentCount -Arguments $arguments -Minimum 2 -Usage 'test command' } | Should Throw "Invalid arguments. Usage: test command"
        }

        It 'throws with correct usage message' {
            $arguments = @('command')
            { Assert-McArgumentCount -Arguments $arguments -Minimum 3 -Usage 'mc test <args>' } | Should Throw 'mc test <args>'
        }
    }

    Context 'Assert-McValidSubcommand' {
        It 'passes when subcommand is in allowed list' {
            $context = [pscustomobject]@{
                CommandArguments = @('docker', 'up')
            }
            { Assert-McValidSubcommand -Context $context -AllowedSubcommands @('up', 'down', 'logs') } | Should Not Throw
        }

        It 'throws when subcommand is missing' {
            $context = [pscustomobject]@{
                CommandArguments = @('docker')
            }
            { Assert-McValidSubcommand -Context $context -AllowedSubcommands @('up', 'down', 'logs') } | Should Throw "Missing subcommand. Allowed: up, down, logs"
        }

        It 'throws when subcommand is not in allowed list' {
            $context = [pscustomobject]@{
                CommandArguments = @('docker', 'banana')
            }
            { Assert-McValidSubcommand -Context $context -AllowedSubcommands @('up', 'down', 'logs') } | Should Throw "Unknown subcommand 'banana'. Allowed: up, down, logs"
        }

        It 'is case-insensitive for subcommand matching' {
            $context = [pscustomobject]@{
                CommandArguments = @('docker', 'UP')
            }
            { Assert-McValidSubcommand -Context $context -AllowedSubcommands @('up', 'down', 'logs') } | Should Not Throw
        }
    }
}
