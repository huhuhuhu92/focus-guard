param(
    [string]$PythonExe = "",
    [switch]$RunGuiSmoke,
    [switch]$RunPackaging
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot "..")
Set-Location $projectRoot

$results = New-Object System.Collections.Generic.List[object]
$startedAt = Get-Date

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

    function Test-AcceptanceDeps {
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
        if (Test-AcceptanceDeps -Exe $candidate) {
            return $candidate
        }
    }

    return $candidates[0]
}

function Add-Result {
    param(
        [string]$Step,
        [string]$Status,
        [bool]$Required,
        [double]$Seconds,
        [string]$Detail
    )

    $results.Add([PSCustomObject]@{
            step     = $Step
            status   = $Status
            required = $Required
            seconds  = [math]::Round($Seconds, 2)
            detail   = $Detail
        })
}

function Invoke-Step {
    param(
        [string]$Name,
        [ScriptBlock]$Action,
        [bool]$Required = $true
    )

    Write-Host "==> $Name"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        & $Action
        $sw.Stop()
        Add-Result -Step $Name -Status "PASS" -Required $Required -Seconds $sw.Elapsed.TotalSeconds -Detail ""
        Write-Host "    PASS" -ForegroundColor Green
        return $true
    }
    catch {
        $sw.Stop()
        $detail = $_.Exception.Message
        if ($Required) {
            Add-Result -Step $Name -Status "FAIL" -Required $Required -Seconds $sw.Elapsed.TotalSeconds -Detail $detail
            Write-Host "    FAIL: $detail" -ForegroundColor Red
            return $false
        }
        Add-Result -Step $Name -Status "WARN" -Required $Required -Seconds $sw.Elapsed.TotalSeconds -Detail $detail
        Write-Host "    WARN: $detail" -ForegroundColor Yellow
        return $true
    }
}

function Invoke-PythonSnippet {
    param([string]$Code)
    $Code | & $PythonExe -
    if ($LASTEXITCODE -ne 0) {
        throw "python snippet exited with code $LASTEXITCODE"
    }
}

$PythonExe = Resolve-PythonExecutable -Preferred $PythonExe

$ok = $true

$ok = (Invoke-Step -Name "Python environment info" -Required $true -Action {
        & $PythonExe -c "import sys, platform; print('python_exe=', sys.executable); print('python_version=', platform.python_version())"
        if ($LASTEXITCODE -ne 0) { throw "python not available" }
        & $PythonExe -m pip -V
        if ($LASTEXITCODE -ne 0) { throw "pip not available in selected interpreter" }
    }) -and $ok

$ok = (Invoke-Step -Name "Source compile check" -Required $true -Action {
        & $PythonExe -m compileall focus_reminder tests
        if ($LASTEXITCODE -ne 0) { throw "compileall failed" }
    }) -and $ok

$ok = (Invoke-Step -Name "Unit tests" -Required $true -Action {
        & $PythonExe -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { throw "unit tests failed" }
    }) -and $ok

$ok = (Invoke-Step -Name "Config file validation" -Required $true -Action {
        Invoke-PythonSnippet @'
import json
from pathlib import Path

cfg_path = Path("focus_reminder/data/config.json")
if not cfg_path.exists():
    raise SystemExit("config.json not found")

required_keys = {
    "idle_threshold_seconds",
    "pre_reminder_seconds",
    "enable_pre_reminder",
    "cooldown_seconds",
    "dismiss_mode",
    "enable_history",
    "monitor_enabled",
}
data = json.loads(cfg_path.read_text(encoding="utf-8"))
missing = sorted(required_keys - set(data.keys()))
if missing:
    raise SystemExit(f"config missing keys: {missing}")
print("config_ok")
'@
    }) -and $ok

$ok = (Invoke-Step -Name "SQLite schema and R/W check" -Required $true -Action {
        Invoke-PythonSnippet @'
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

db_path = Path("focus_reminder/data/focus_reminder.db")
db_path.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS reminder_events (
        id TEXT PRIMARY KEY,
        level TEXT NOT NULL,
        triggered_at TEXT NOT NULL,
        idle_seconds INTEGER NOT NULL,
        media_state TEXT NOT NULL,
        dismiss_mode TEXT NOT NULL,
        dismiss_reason TEXT,
        popup_duration_ms INTEGER,
        foreground_app TEXT,
        foreground_title TEXT
    )
    """
)
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS app_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """
)
conn.commit()

tables = {row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
missing = {"reminder_events", "app_meta"} - tables
if missing:
    raise SystemExit(f"sqlite missing tables: {sorted(missing)}")

probe_id = f"probe-{uuid.uuid4()}"
cur.execute(
    """
    INSERT INTO reminder_events (
        id, level, triggered_at, idle_seconds, media_state, dismiss_mode,
        dismiss_reason, popup_duration_ms, foreground_app, foreground_title
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        probe_id,
        "pre_reminder",
        datetime.now().isoformat(timespec="seconds"),
        120,
        "none",
        "activity",
        "auto",
        0,
        "acceptance-script",
        "acceptance-script",
    ),
)
conn.commit()

count = cur.execute("SELECT COUNT(*) FROM reminder_events WHERE id = ?", (probe_id,)).fetchone()[0]
if count != 1:
    raise SystemExit("probe event insert verification failed")

cur.execute("DELETE FROM reminder_events WHERE id = ?", (probe_id,))
conn.commit()
conn.close()
print("sqlite_ok")
'@
    }) -and $ok

$ok = (Invoke-Step -Name "Dependency import check" -Required $true -Action {
        & $PythonExe -c "from PySide6 import QtCore, QtWidgets, QtCharts; import pynput, psutil, win32api; print('deps_ok', QtCore.__version__, QtCharts.__name__)"
        if ($LASTEXITCODE -ne 0) { throw "required imports failed" }
    }) -and $ok

if ($RunGuiSmoke) {
    $ok = (Invoke-Step -Name "GUI smoke check (optional)" -Required $false -Action {
            Invoke-PythonSnippet @'
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from focus_reminder.app.bootstrap import AppBootstrap

app = QApplication([])
bootstrap = AppBootstrap(app)
bootstrap.start()
QTimer.singleShot(1500, app.quit)
app.exec()
bootstrap.shutdown()
print("gui_smoke_ok")
'@
        }) -and $ok
}

if ($RunPackaging) {
    $ok = (Invoke-Step -Name "PyInstaller packaging (optional)" -Required $false -Action {
            & $PythonExe -m PyInstaller --noconfirm --clean focus_reminder/infrastructure/packaging/pyinstaller.spec
            if ($LASTEXITCODE -ne 0) { throw "pyinstaller failed" }
            $exeCandidates = @(
                (Join-Path $projectRoot "dist/FocusReminderDesktop/FocusReminderDesktop.exe"),
                (Join-Path $projectRoot "dist/FocusReminderDesktop.exe")
            )
            $exePath = $null
            foreach ($candidate in $exeCandidates) {
                if (Test-Path $candidate) {
                    $exePath = $candidate
                    break
                }
            }
            if (-not $exePath) {
                throw "packaging finished but exe not found. checked: $($exeCandidates -join '; ')"
            }
            Write-Host "packaging output: $exePath"
        }) -and $ok
}

$endedAt = Get-Date
$failedCount = @($results | Where-Object { $_.status -eq "FAIL" }).Count
$warnCount = @($results | Where-Object { $_.status -eq "WARN" }).Count

Write-Host ""
Write-Host "========== Acceptance Result =========="
$results | Format-Table -AutoSize
Write-Host ""
Write-Host "Started at: $startedAt"
Write-Host "Ended at: $endedAt"
Write-Host "FAIL: $failedCount, WARN: $warnCount"

$report = [PSCustomObject]@{
    started_at = $startedAt.ToString("s")
    ended_at   = $endedAt.ToString("s")
    failed     = $failedCount
    warning    = $warnCount
    results    = $results
}
$reportPath = Join-Path $projectRoot "acceptance_report.json"
$report | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $reportPath
Write-Host "Report file: $reportPath"

if ($failedCount -gt 0 -or -not $ok) {
    exit 1
}

exit 0
