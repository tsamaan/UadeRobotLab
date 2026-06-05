param(
    [string]$Interface = "Ethernet",
    [int]$DomainId = 1,
    [string]$Model = "models/best_model.zip",
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir
try {
    $args = @(".\policies\rl_policy_runner.py", "--domain", "$DomainId", "--interface", "$Interface", "--model", "$Model")
    if ($Check) {
        $args += "--check"
    }
    py -3.10 @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
