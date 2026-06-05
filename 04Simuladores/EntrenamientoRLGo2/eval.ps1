param(
    [string]$RunDir = "runs/ppo_go2_walk",
    [int]$Seconds = 20
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir
try {
    py -3.10 .\scripts\eval_policy.py --run-dir $RunDir --seconds $Seconds --deterministic
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
