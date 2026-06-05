param(
    [string]$RunDir = "runs/ppo_go2_walk_v1",
    [int]$Seconds = 12,
    [int]$Poll = 30,
    [switch]$Once,
    [switch]$Deterministic
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir
try {
    $args = @(
        ".\scripts\watch_checkpoints.py",
        "--run-dir", $RunDir,
        "--seconds", "$Seconds",
        "--poll", "$Poll"
    )
    if ($Once) {
        $args += "--once"
    }
    if ($Deterministic) {
        $args += "--deterministic"
    }
    py -3.10 @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
