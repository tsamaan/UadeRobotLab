param(
    [string]$Interface = "",
    [int]$DomainId = 1,
    [switch]$UseJoystick,
    [switch]$UseElasticBand,
    [switch]$NoElasticBand,
    [switch]$NoPoseHold,
    [int]$ApiPort = 8765,
    [switch]$SetupOnly
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoDir = Join-Path $scriptDir "unitree_mujoco"
$repoUrl = "https://github.com/unitreerobotics/unitree_mujoco.git"
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
$useVenvPython = Test-Path $venvPython

function Require-Command($Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "No se encontro '$Name' en PATH."
    }
}

function Invoke-SimPython($Arguments) {
    if ($script:useVenvPython) {
        & $script:venvPython @Arguments
    } else {
        & py -3.10 @Arguments
    }
}

function Test-PythonImport($ModuleName) {
    Invoke-SimPython @("-c", "import $ModuleName") *> $null
    return ($LASTEXITCODE -eq 0)
}

function Get-SimulatorInterface($RequestedInterface) {
    if ($RequestedInterface.Trim().Length -gt 0) {
        return $RequestedInterface
    }

    $preferredNames = @("Ethernet", "Wi-Fi", "vEthernet (Default Switch)")
    $adapters = @(Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq "Up" })

    foreach ($name in $preferredNames) {
        $adapter = $adapters | Where-Object { $_.Name -eq $name } | Select-Object -First 1
        if ($adapter) {
            return $adapter.Name
        }
    }

    $firstUpAdapter = $adapters | Select-Object -First 1
    if ($firstUpAdapter) {
        return $firstUpAdapter.Name
    }

    throw "No se encontro una interfaz de red activa. Conectate a Ethernet/Wi-Fi o pasa -Interface con el nombre de la placa."
}

function Set-PythonAssignment($Content, $Name, $Value) {
    $pattern = "(?m)^$Name\s*=.*$"
    $line = "$Name = $Value"
    if ($Content -match $pattern) {
        return ($Content -replace $pattern, $line)
    }
    return ($Content.TrimEnd() + "`r`n" + $line + "`r`n")
}

Require-Command git

if (-not $useVenvPython) {
    Require-Command py
}

if (-not (Test-PythonImport "mujoco")) {
    throw "Falta el paquete Python 'mujoco'. Instalalo con: py -3.10 -m pip install mujoco"
}

if (-not (Test-PythonImport "pygame")) {
    throw "Falta el paquete Python 'pygame'. Instalalo con: py -3.10 -m pip install pygame"
}

if (-not (Test-PythonImport "unitree_sdk2py")) {
    throw "Falta 'unitree_sdk2py'. Instala unitree_sdk2_python siguiendo el README oficial de Unitree."
}

if (-not (Test-Path $repoDir)) {
    Write-Host "[INFO] Clonando unitree_mujoco oficial..."
    git clone --depth 1 $repoUrl $repoDir
} else {
    Write-Host "[INFO] unitree_mujoco ya existe. No se vuelve a clonar."
}

$resolvedInterface = Get-SimulatorInterface $Interface
if ($UseElasticBand -and $NoElasticBand) {
    throw "Usa -UseElasticBand o -NoElasticBand, no ambos."
}
$elasticBandValue = if ($UseElasticBand) { "True" } else { "False" }
$poseHoldValue = if ($NoPoseHold) { "False" } else { "True" }
$joystickValue = if ($UseJoystick) { "1" } else { "0" }

$configPath = Join-Path $repoDir "simulate_python\config.py"
if (-not (Test-Path $configPath)) {
    throw "No se encontro config.py en $configPath"
}

$config = Get-Content -LiteralPath $configPath -Raw
$config = $config -replace 'ROBOT\s*=\s*".*?"', 'ROBOT = "g1"'
$config = $config -replace 'DOMAIN_ID\s*=\s*\d+', "DOMAIN_ID = $DomainId"
$config = $config -replace 'INTERFACE\s*=\s*".*?"', "INTERFACE = `"$resolvedInterface`""
$config = $config -replace 'USE_JOYSTICK\s*=\s*\d+', "USE_JOYSTICK = $joystickValue"
$config = $config -replace 'PRINT_SCENE_INFORMATION\s*=\s*(True|False)', 'PRINT_SCENE_INFORMATION = False'
$config = $config -replace 'ENABLE_ELASTIC_BAND\s*=\s*(True|False)', "ENABLE_ELASTIC_BAND = $elasticBandValue"
$config = Set-PythonAssignment $config "HOLD_INITIAL_POSE" $poseHoldValue
$config = Set-PythonAssignment $config "POSE_HOLD_KP" "100.0"
$config = Set-PythonAssignment $config "POSE_HOLD_KD" "10.0"
$config = Set-PythonAssignment $config "ELASTIC_BAND_POINT" "[0.0, 0.0, 1.4]"
$config = Set-PythonAssignment $config "ELASTIC_BAND_STIFFNESS" "600.0"
$config = Set-PythonAssignment $config "ELASTIC_BAND_DAMPING" "100.0"
$config = Set-PythonAssignment $config "ELASTIC_BAND_LENGTH" "0.0"
$config = Set-PythonAssignment $config "ELASTIC_BAND_ENABLE_AT_START" "True"
$config = Set-PythonAssignment $config "STUDENT_API_HOST" '"127.0.0.1"'
$config = Set-PythonAssignment $config "STUDENT_API_PORT" "$ApiPort"
Set-Content -LiteralPath $configPath -Value $config -Encoding UTF8

$bridgePath = Join-Path $repoDir "simulate_python\unitree_sdk2py_bridge.py"
$bridge = Get-Content -LiteralPath $bridgePath -Raw
if ($bridge -notmatch "class RecurrentThread:\r?\n\s+def __init__\(self, interval, target, name=") {
    $oldImport = "from unitree_sdk2py.utils.thread import RecurrentThread"
    $fallbackThread = @'
try:
    from unitree_sdk2py.utils.thread import RecurrentThread
except Exception:
    import threading
    import time

    class RecurrentThread:
        def __init__(self, interval, target, name=""):
            self.interval = interval
            self.target = target
            self.name = name
            self._running = False
            self._thread = None

        def Start(self):
            self._running = True
            self._thread = threading.Thread(target=self._run, name=self.name, daemon=True)
            self._thread.start()

        def Stop(self):
            self._running = False

        def _run(self):
            while self._running:
                start = time.perf_counter()
                self.target()
                sleep_time = self.interval - (time.perf_counter() - start)
                if sleep_time > 0:
                    time.sleep(sleep_time)
'@
    $bridge = $bridge.Replace($oldImport, $fallbackThread)
    Set-Content -LiteralPath $bridgePath -Value $bridge -Encoding UTF8
    Write-Host "[OK] Parche Windows aplicado a unitree_sdk2py_bridge.py"
}

Write-Host "[OK] Configuracion lista:"
Write-Host "     Robot        : g1"
Write-Host "     Domain ID    : $DomainId"
Write-Host "     Interface    : $resolvedInterface"
Write-Host "     Joystick     : $joystickValue"
Write-Host "     Elastic band : $elasticBandValue"
Write-Host "     Pose hold    : $poseHoldValue"
Write-Host "     API          : 127.0.0.1:$ApiPort"
if ($useVenvPython) {
    Write-Host "     Python       : .venv"
} else {
    Write-Host "     Python       : py -3.10"
}

if ($SetupOnly) {
    Push-Location $scriptDir
    try {
        Invoke-SimPython @(".\g1_teacher_sim.py", "--check-model")
        Invoke-SimPython @(".\g1_teacher_sim.py", "--check-stability")
    } finally {
        Pop-Location
    }
    Write-Host "[OK] SetupOnly finalizado. No se abre la ventana de MuJoCo."
    exit 0
}

Write-Host "[INFO] Abriendo MuJoCo con G1. Cerrar la ventana corta el simulador."
Write-Host "[INFO] El robot queda estabilizado por motores/base docente, sin banda elastica."
Write-Host "[INFO] Los alumnos pueden usar g1_student_api.py mientras esta ventana este abierta."

Push-Location $scriptDir
try {
    Invoke-SimPython @(".\g1_teacher_sim.py")
} finally {
    Pop-Location
}
