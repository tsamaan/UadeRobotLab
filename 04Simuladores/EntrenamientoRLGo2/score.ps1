param(
    [string]$RunDir = "runs/ppo_go2_flat_v3_rear_fix_test",
    [string]$Checkpoint = "latest",
    [int]$Steps = 600,
    [switch]$Deterministic
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir
try {
    $args = @(
        ".\scripts\score_policy.py",
        "--run-dir", $RunDir,
        "--checkpoint", $Checkpoint,
        "--steps", "$Steps"
    )
    if ($Deterministic) {
        $args += "--deterministic"
    }
    py -3.10 @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
