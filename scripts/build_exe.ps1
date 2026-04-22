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

    function Add-Candidate {
        param(
            [System.Collections.Generic.List[string]]$List,
            [string]$PathValue
        )
        if (-not $PathValue) {
            return
        }
        if (-not (Test-Path $PathValue)) {
            return
        }
        $resolved = (Resolve-Path $PathValue).Path
        if (-not $List.Contains($resolved)) {
            $List.Add($resolved)
        }
    }

    function Test-PackagingDeps {
        param([string]$Exe)
        $outFile = [System.IO.Path]::GetTempFileName()
        $errFile = [System.IO.Path]::GetTempFileName()
        $probeFile = [System.IO.Path]::GetTempFileName()
        try {
            Set-Content -Path $probeFile -Encoding UTF8 -Value @'
from PySide6 import QtCore, QtWidgets, QtCharts
import pynput
import psutil
import win32api
import PyInstaller
'@
            $probe = Start-Process -FilePath $Exe `
                -ArgumentList @($probeFile) `
                -NoNewWindow -Wait -PassThru `
                -RedirectStandardOutput $outFile `
                -RedirectStandardError $errFile
            return $probe.ExitCode -eq 0
        }
        finally {
            Remove-Item -ErrorAction SilentlyContinue $outFile
            Remove-Item -ErrorAction SilentlyContinue $errFile
            Remove-Item -ErrorAction SilentlyContinue $probeFile
        }
    }

    $candidates = New-Object System.Collections.Generic.List[string]

    if ($Preferred) {
        Add-Candidate -List $candidates -PathValue $Preferred
    }

    $projectVenv = Join-Path $projectRoot ".venv\Scripts\python.exe"
    Add-Candidate -List $candidates -PathValue $projectVenv

    if ($env:VIRTUAL_ENV) {
        $venvPython = Join-Path $env:VIRTUAL_ENV "Scripts\\python.exe"
        Add-Candidate -List $candidates -PathValue $venvPython
    }

    if ($env:CONDA_PREFIX) {
        $condaPython = Join-Path $env:CONDA_PREFIX "python.exe"
        Add-Candidate -List $candidates -PathValue $condaPython
    }

    $condaCmd = Get-Command conda -ErrorAction SilentlyContinue
    if ($condaCmd -and $condaCmd.Source) {
        try {
            $condaJson = & $condaCmd.Source env list --json 2>$null
            if ($LASTEXITCODE -eq 0 -and $condaJson) {
                $condaData = $condaJson | ConvertFrom-Json
                if ($condaData.envs) {
                    foreach ($envPath in $condaData.envs) {
                        $envPython = Join-Path $envPath "python.exe"
                        Add-Candidate -List $candidates -PathValue $envPython
                    }
                }
            }
        }
        catch {
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd -and $pythonCmd.Source -and (Test-Path $pythonCmd.Source)) {
        Add-Candidate -List $candidates -PathValue $pythonCmd.Source
    }

    if ($candidates.Count -eq 0) {
        throw "Cannot find python executable. Activate a conda/venv env or pass -PythonExe."
    }

    foreach ($candidate in $candidates) {
        if (Test-PackagingDeps -Exe $candidate) {
            return [PSCustomObject]@{
                path = $candidate
                ready = $true
            }
        }
    }

    return [PSCustomObject]@{
        path = $candidates[0]
        ready = $false
    }
}

$selected = Resolve-PythonExecutable -Preferred $PythonExe
$resolvedPython = $selected.path

if (-not $selected.ready -and -not $InstallDeps) {
    throw "No Python env with packaging dependencies was found. Use -InstallDeps, or pass -PythonExe <env python>."
}

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
