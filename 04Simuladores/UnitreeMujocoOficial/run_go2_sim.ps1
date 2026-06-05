param(
    [string]$Interface = "Ethernet",
    [int]$DomainId = 1,
    [switch]$UseJoystick,
    [switch]$SetupOnly
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoDir = Join-Path $scriptDir "unitree_mujoco"
$repoUrl = "https://github.com/unitreerobotics/unitree_mujoco.git"

function Require-Command($Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "No se encontro '$Name' en PATH."
    }
}

Require-Command git
Require-Command py

if (-not (Test-Path $repoDir)) {
    Write-Host "[INFO] Clonando unitree_mujoco oficial..."
    git clone --depth 1 $repoUrl $repoDir
} else {
    Write-Host "[INFO] unitree_mujoco ya existe. No se vuelve a clonar."
}

$configPath = Join-Path $repoDir "simulate_python\config.py"
if (-not (Test-Path $configPath)) {
    throw "No se encontro config.py en $configPath"
}

$joystickValue = if ($UseJoystick) { "1" } else { "0" }
$config = Get-Content -LiteralPath $configPath -Raw
$config = $config -replace 'ROBOT\s*=\s*".*?"', 'ROBOT = "go2"'
$config = $config -replace 'DOMAIN_ID\s*=\s*\d+', "DOMAIN_ID = $DomainId"
$config = $config -replace 'INTERFACE\s*=\s*".*?"', "INTERFACE = `"$Interface`""
$config = $config -replace 'USE_JOYSTICK\s*=\s*\d+', "USE_JOYSTICK = $joystickValue"
$config = $config -replace 'PRINT_SCENE_INFORMATION\s*=\s*(True|False)', 'PRINT_SCENE_INFORMATION = False'
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
Write-Host "     Robot     : go2"
Write-Host "     Domain ID : $DomainId"
Write-Host "     Interface : $Interface"
Write-Host "     Joystick  : $joystickValue"

if ($SetupOnly) {
    exit 0
}

Push-Location (Join-Path $repoDir "simulate_python")
try {
    py -3.10 .\unitree_mujoco.py
} finally {
    Pop-Location
}
