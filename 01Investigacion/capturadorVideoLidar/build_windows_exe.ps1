$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ProjectRoot "..\..")
$VenvDir = Join-Path $ProjectRoot ".venv-win"
$SdkPath = Join-Path $RepoRoot "00SDK\unitree_sdk2_python"

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

if (!(Test-Path $VenvDir)) {
    $pythonCmd = @(Get-PythonCommand)
    if ($pythonCmd.Length -gt 1) {
        Invoke-Native $pythonCmd[0] @($pythonCmd[1..($pythonCmd.Length - 1)]) -m venv $VenvDir
    } else {
        Invoke-Native $pythonCmd[0] -m venv $VenvDir
    }
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
if (-not $env:CYCLONEDDS_HOME -and -not $env:CMAKE_PREFIX_PATH) {
    Write-Warning "cyclonedds puede requerir CycloneDDS nativo para Windows. Si pip falla, definir CYCLONEDDS_HOME o CMAKE_PREFIX_PATH."
}

Invoke-Native $PythonExe -m pip install --upgrade pip
Invoke-Native $PythonExe -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
Invoke-Native $PythonExe -m pip install -e $SdkPath

Invoke-Native $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name CapturadorVideoLidar `
    --paths $SdkPath `
    --collect-all unitree_sdk2py `
    --collect-all cyclonedds `
    --collect-all cv2 `
    (Join-Path $ProjectRoot "main.py")

$DistDir = Join-Path $ProjectRoot "dist\CapturadorVideoLidar"
$ZipPath = Join-Path $ProjectRoot "dist\CapturadorVideoLidar-win64.zip"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}
Compress-Archive -Path (Join-Path $DistDir "*") -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "Build listo:"
Write-Host "  $DistDir\CapturadorVideoLidar.exe"
Write-Host "  $ZipPath"
