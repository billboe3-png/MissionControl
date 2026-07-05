Set-StrictMode -Version Latest
. .\scripts\mc.ps1
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
try {
    Invoke-McCommand -Context $context
    'NOERROR'
}
catch {
    $_.Exception.Message
}
