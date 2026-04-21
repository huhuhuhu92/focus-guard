param(
    [string]$PythonExe = "D:\\condaData\\envs_dirs\\my_project_py311\\python.exe"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot "..")
Set-Location $projectRoot

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

Write-Host "Using Python: $PythonExe"
& $PythonExe -m focus_reminder.app.main
exit $LASTEXITCODE

