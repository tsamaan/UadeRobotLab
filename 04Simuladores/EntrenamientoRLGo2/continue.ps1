param(
    [string]$SourceRun = "runs/ppo_go2_flat_v1",
    [string]$SourceCheckpoint = "",
    [int]$Timesteps = 1000000,
    [string]$RunName = "ppo_go2_flat_v2",
    [int]$Seed = 1,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir
try {
    $args = @(
        ".\scripts\continue_ppo.py",
        "--source-run", $SourceRun,
        "--timesteps", "$Timesteps",
        "--run-name", $RunName,
        "--seed", "$Seed"
    )
    if ($SourceCheckpoint -ne "") {
        $args += @("--source-checkpoint", $SourceCheckpoint)
    }
    if ($CheckOnly) {
        $args += "--check-only"
    }
    py -3.10 @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
