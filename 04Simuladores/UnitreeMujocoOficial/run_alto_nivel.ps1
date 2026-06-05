param(
    [string]$Interface = "Ethernet",
    [int]$DomainId = 1
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir
try {
    py -3.10 .\examples\alumnos_alto_nivel.py --domain $DomainId --interface $Interface
} finally {
    Pop-Location
}
