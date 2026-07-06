Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptsRoot = Join-Path $repoRoot 'scripts'
$script:MissionControlScriptsRoot = $scriptsRoot
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')

Describe 'Logger' {
    Context 'Initialize-McLogger' {
        It 'creates log directory if it does not exist' {
            $tempProjectRoot = Join-Path $env:TEMP "mc-test-project-$(Get-Random)"
            $tempLogDir = Join-Path $tempProjectRoot 'logs'
            
            try {
                New-Item -ItemType Directory -Path $tempProjectRoot -Force | Out-Null
                
                $context = [pscustomobject]@{
                    ProjectRoot = $tempProjectRoot
                    Options     = [pscustomobject]@{ Log = $false }
                    LogFile     = $null
                }
                
                Initialize-McLogger -Context $context
                
                $context.LogFile | Should Not BeNullOrEmpty
                Test-Path -LiteralPath $tempLogDir | Should Be $true
            }
            finally {
                Remove-Item -LiteralPath $tempProjectRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
        }

        It 'sets LogFile path to logs/mc.log' {
            $tempProjectRoot = Join-Path $env:TEMP "mc-test-project-$(Get-Random)"
            
            try {
                New-Item -ItemType Directory -Path $tempProjectRoot -Force | Out-Null
                
                $context = [pscustomobject]@{
                    ProjectRoot = $tempProjectRoot
                    Options     = [pscustomobject]@{ Log = $false }
                    LogFile     = $null
                }
                
                Initialize-McLogger -Context $context
                
                $expectedPath = Join-Path $tempProjectRoot 'logs\mc.log'
                $context.LogFile | Should Be $expectedPath
            }
            finally {
                Remove-Item -LiteralPath $tempProjectRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    Context 'Write-McLog' {
        It 'writes log entry to file when logging is enabled' {
            $tempProjectRoot = Join-Path $env:TEMP "mc-test-project-$(Get-Random)"
            
            try {
                New-Item -ItemType Directory -Path $tempProjectRoot -Force | Out-Null
                New-Item -ItemType Directory -Path (Join-Path $tempProjectRoot 'logs') -Force | Out-Null
                
                $logFile = Join-Path $tempProjectRoot 'logs\mc.log'
                
                $context = [pscustomobject]@{
                    ProjectRoot = $tempProjectRoot
                    Options     = [pscustomobject]@{ Log = $true; Quiet = $true; Verbose = $false }
                    LogFile     = $logFile
                }
                
                Write-McLog -Context $context -Level 'INFO' -Message 'Test message'
                
                Test-Path -LiteralPath $logFile | Should Be $true
                $content = Get-Content -LiteralPath $logFile -Raw
                $content | Should Match 'Test message'
                $content | Should Match '\[INFO\]'
            }
            finally {
                Remove-Item -LiteralPath $tempProjectRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
        }

        It 'writes ERROR level logs even when logging is disabled' {
            $tempProjectRoot = Join-Path $env:TEMP "mc-test-project-$(Get-Random)"
            
            try {
                New-Item -ItemType Directory -Path $tempProjectRoot -Force | Out-Null
                New-Item -ItemType Directory -Path (Join-Path $tempProjectRoot 'logs') -Force | Out-Null
                
                $logFile = Join-Path $tempProjectRoot 'logs\mc.log'
                
                $context = [pscustomobject]@{
                    ProjectRoot = $tempProjectRoot
                    Options     = [pscustomobject]@{ Log = $false; Quiet = $true; Verbose = $false }
                    LogFile     = $logFile
                }
                
                Write-McLog -Context $context -Level 'ERROR' -Message 'Error message'
                
                $content = Get-Content -LiteralPath $logFile -Raw
                $content | Should Match 'Error message'
                $content | Should Match '\[ERROR\]'
            }
            finally {
                Remove-Item -LiteralPath $tempProjectRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
        }

        It 'writes DEBUG level logs even when logging is disabled' {
            $tempProjectRoot = Join-Path $env:TEMP "mc-test-project-$(Get-Random)"
            
            try {
                New-Item -ItemType Directory -Path $tempProjectRoot -Force | Out-Null
                New-Item -ItemType Directory -Path (Join-Path $tempProjectRoot 'logs') -Force | Out-Null
                
                $logFile = Join-Path $tempProjectRoot 'logs\mc.log'
                
                $context = [pscustomobject]@{
                    ProjectRoot = $tempProjectRoot
                    Options     = [pscustomobject]@{ Log = $false; Quiet = $true; Verbose = $false }
                    LogFile     = $logFile
                }
                
                Write-McLog -Context $context -Level 'DEBUG' -Message 'Debug message'
                
                $content = Get-Content -LiteralPath $logFile -Raw
                $content | Should Match 'Debug message'
                $content | Should Match '\[DEBUG\]'
            }
            finally {
                Remove-Item -LiteralPath $tempProjectRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
        }

        It 'includes timestamp in log entry' {
            $tempProjectRoot = Join-Path $env:TEMP "mc-test-project-$(Get-Random)"
            
            try {
                New-Item -ItemType Directory -Path $tempProjectRoot -Force | Out-Null
                New-Item -ItemType Directory -Path (Join-Path $tempProjectRoot 'logs') -Force | Out-Null
                
                $logFile = Join-Path $tempProjectRoot 'logs\mc.log'
                
                $context = [pscustomobject]@{
                    ProjectRoot = $tempProjectRoot
                    Options     = [pscustomobject]@{ Log = $true; Quiet = $true; Verbose = $false }
                    LogFile     = $logFile
                }
                
                Write-McLog -Context $context -Level 'INFO' -Message 'Test message'
                
                $content = Get-Content -LiteralPath $logFile -Raw
                $content | Should Match '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
            }
            finally {
                Remove-Item -LiteralPath $tempProjectRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
        }

        It 'supports all log levels' {
            $tempProjectRoot = Join-Path $env:TEMP "mc-test-project-$(Get-Random)"
            
            try {
                New-Item -ItemType Directory -Path $tempProjectRoot -Force | Out-Null
                New-Item -ItemType Directory -Path (Join-Path $tempProjectRoot 'logs') -Force | Out-Null
                
                $logFile = Join-Path $tempProjectRoot 'logs\mc.log'
                
                $context = [pscustomobject]@{
                    ProjectRoot = $tempProjectRoot
                    Options     = [pscustomobject]@{ Log = $true; Quiet = $true; Verbose = $false }
                    LogFile     = $logFile
                }
                
                $levels = @('INFO', 'WARN', 'ERROR', 'DEBUG', 'SUCCESS')
                foreach ($level in $levels) {
                    Write-McLog -Context $context -Level $level -Message "$level message"
                }
                
                $content = Get-Content -LiteralPath $logFile -Raw
                foreach ($level in $levels) {
                    $content | Should Match "\[$level\]"
                }
            }
            finally {
                Remove-Item -LiteralPath $tempProjectRoot -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
}
