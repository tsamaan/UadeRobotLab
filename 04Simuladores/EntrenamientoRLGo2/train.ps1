param(
    [int]$Timesteps = 200000,
    [string]$RunName = "ppo_go2_walk"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir
try {
    py -3.10 .\scripts\train_ppo.py --timesteps $Timesteps --run-name $RunName
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
