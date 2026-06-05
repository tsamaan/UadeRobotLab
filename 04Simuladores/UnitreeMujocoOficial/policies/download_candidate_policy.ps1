$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$modelsDir = Join-Path $scriptDir "models"
New-Item -ItemType Directory -Force $modelsDir | Out-Null

$url = "https://huggingface.co/cagataydev/sac-unitree-go2-mujoco/resolve/main/best/best_model.zip"
$out = Join-Path $modelsDir "best_model.zip"

curl.exe -k -L $url -o $out

if (-not (Test-Path $out) -or (Get-Item $out).Length -eq 0) {
    throw "No se pudo descargar el modelo."
}

Write-Host "[OK] Modelo descargado en $out"
