$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ProjectRoot "..\..")
$VenvDir = Join-Path $ProjectRoot ".venv-win"
$SdkPath = Join-Path $RepoRoot "00SDK\unitree_sdk2_python"
$BuildDir = Join-Path $ProjectRoot "build"
$DistBase = Join-Path $ProjectRoot "dist"

function Get-PythonCommand {
    if ($env:PYTHON_EXE -and (Test-Path $env:PYTHON_EXE)) {
        return @($env:PYTHON_EXE)
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @("py", "-3.12")
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @("python")
    }

    throw "No encontre Python. Para construir el exe hace falta Python solo en esta PC de build."
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo el comando: $Command $($Arguments -join ' ')"
    }
}

function Compress-WithRetry {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$DestinationPath
    )

    $lastError = $null
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Compress-Archive -Path $SourcePath -DestinationPath $DestinationPath -Force
            return
        } catch {
            $lastError = $_
            Start-Sleep -Seconds 2
        }
    }

    throw $lastError
}

if (!(Test-Path $VenvDir)) {
    $pythonCmd = @(Get-PythonCommand)
    if ($pythonCmd.Length -gt 1) {
        Invoke-Native $pythonCmd[0] @($pythonCmd[1..($pythonCmd.Length - 1)]) -m venv $VenvDir
    } else {
        Invoke-Native $pythonCmd[0] -m venv $VenvDir
    }
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

Invoke-Native $PythonExe -m pip install --upgrade pip
Invoke-Native $PythonExe -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if (Test-Path $SdkPath) {
    Invoke-Native $PythonExe -m pip install --no-deps --editable $SdkPath
}

Invoke-Native $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name CapturadorVideoLidar `
    --distpath $DistBase `
    --workpath $BuildDir `
    --specpath $ProjectRoot `
    --paths $SdkPath `
    --collect-all unitree_sdk2py `
    --collect-all cyclonedds `
    --collect-all cv2 `
    (Join-Path $ProjectRoot "main.py")

$DistDir = Join-Path $ProjectRoot "dist\CapturadorVideoLidar"
$Ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($Ffmpeg) {
    Copy-Item -Path $Ffmpeg.Source -Destination (Join-Path $DistDir "ffmpeg.exe") -Force
    Write-Host "ffmpeg incluido en el paquete."
} else {
    Write-Warning "No encontre ffmpeg en PATH. El exe guardara H264 crudo, pero no convertira a MP4 automaticamente."
}

$ZipPath = Join-Path $ProjectRoot "dist\CapturadorVideoLidar-win64.zip"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}
Compress-WithRetry -SourcePath (Join-Path $DistDir "*") -DestinationPath $ZipPath

Write-Host ""
Write-Host "Build listo:"
Write-Host "  $DistDir\CapturadorVideoLidar.exe"
Write-Host "  $ZipPath"
