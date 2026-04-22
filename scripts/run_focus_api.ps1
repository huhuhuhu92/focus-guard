param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot "..")
Set-Location $projectRoot

Write-Host "Tip: This script starts API service only (no desktop UI)." -ForegroundColor Yellow
Write-Host "For desktop app, use: .\scripts\run_focus_reminder.ps1" -ForegroundColor Yellow

function Resolve-PythonExecutable {
    param([string]$Preferred)

    if ($Preferred -and (Test-Path $Preferred)) {
        return (Resolve-Path $Preferred).Path
    }

    $candidates = New-Object System.Collections.Generic.List[string]

    if ($env:VIRTUAL_ENV) {
        $venvPython = Join-Path $env:VIRTUAL_ENV "Scripts\\python.exe"
        if (Test-Path $venvPython) { $candidates.Add($venvPython) }
    }

    if ($env:CONDA_PREFIX) {
        $condaPython = Join-Path $env:CONDA_PREFIX "python.exe"
        if (Test-Path $condaPython) { $candidates.Add($condaPython) }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd -and $pythonCmd.Source -and (Test-Path $pythonCmd.Source)) {
        $candidates.Add($pythonCmd.Source)
    }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw "Cannot find a usable python executable. Activate a conda/venv env or pass -PythonExe."
}

$resolvedPython = Resolve-PythonExecutable -Preferred $PythonExe
Write-Host "Using Python: $resolvedPython"
& $resolvedPython -m focus_reminder.api.main
exit $LASTEXITCODE
