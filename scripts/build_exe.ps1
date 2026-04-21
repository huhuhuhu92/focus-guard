param(
    [string]$PythonExe = "",
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot "..")
Set-Location $projectRoot

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

if ($InstallDeps) {
    & $resolvedPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed."
    }
}

& $resolvedPython -m PyInstaller --noconfirm --clean focus_reminder/infrastructure/packaging/pyinstaller.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$exeCandidates = @(
    (Join-Path $projectRoot "dist\\FocusReminderDesktop\\FocusReminderDesktop.exe"),
    (Join-Path $projectRoot "dist\\FocusReminderDesktop.exe")
)

$exePath = $null
foreach ($candidate in $exeCandidates) {
    if (Test-Path $candidate) {
        $exePath = $candidate
        break
    }
}

if (-not $exePath) {
    throw "Build completed but exe not found. Checked: $($exeCandidates -join '; ')"
}

Write-Host "Build OK: $exePath"
exit 0
