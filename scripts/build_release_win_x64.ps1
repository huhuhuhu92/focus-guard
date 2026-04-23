param(
    [string]$PythonExe = "",
    [switch]$InstallDeps,
    [switch]$Zip
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot "..")
Set-Location $projectRoot

function Get-PythonBits {
    param([string]$Exe)

    $output = & $Exe -c "import struct; print(struct.calcsize('P') * 8)" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $output) {
        throw "Failed to query Python bitness: $Exe"
    }
    $text = ($output | Select-Object -First 1).ToString().Trim()
    [int]$bits = 0
    if (-not [int]::TryParse($text, [ref]$bits)) {
        throw "Unexpected Python bitness output: '$text'"
    }
    return $bits
}

function Get-PEMeta {
    param([string]$Path)

    [byte[]]$bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 256) {
        throw "Invalid PE file (too small): $Path"
    }

    $peOffset = [BitConverter]::ToInt32($bytes, 0x3C)
    if ($peOffset -lt 0 -or $peOffset -gt ($bytes.Length - 128)) {
        throw "Invalid PE header offset: $Path"
    }

    $signature = [BitConverter]::ToUInt32($bytes, $peOffset)
    if ($signature -ne 0x00004550) {
        throw "Not a PE executable: $Path"
    }

    $machine = [BitConverter]::ToUInt16($bytes, $peOffset + 4)
    $optionalHeaderStart = $peOffset + 24
    $magic = [BitConverter]::ToUInt16($bytes, $optionalHeaderStart)

    $subsystemOffset = switch ($magic) {
        0x10B { $optionalHeaderStart + 68 } # PE32
        0x20B { $optionalHeaderStart + 68 } # PE32+
        default { throw "Unknown optional header magic: 0x$('{0:X}' -f $magic)" }
    }

    $subsystem = [BitConverter]::ToUInt16($bytes, $subsystemOffset)
    return [PSCustomObject]@{
        machine = $machine
        subsystem = $subsystem
        magic = $magic
    }
}

if (-not [Environment]::Is64BitOperatingSystem) {
    throw "Current OS is not 64-bit. Win x64 build requires 64-bit Windows."
}

if (-not $PythonExe) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd -or -not $pythonCmd.Source) {
        throw "Cannot find Python. Pass -PythonExe with a 64-bit Python path."
    }
    $PythonExe = $pythonCmd.Source
}

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

$pythonBits = Get-PythonBits -Exe $PythonExe
if ($pythonBits -ne 64) {
    throw "Python is not 64-bit ($pythonBits-bit): $PythonExe"
}

Write-Host "Using Python (x64): $PythonExe"

$buildScript = Join-Path $scriptRoot "build_exe.ps1"
if (-not (Test-Path $buildScript)) {
    throw "build_exe.ps1 not found under scripts/."
}

$buildArgs = @("-PythonExe", $PythonExe)
if ($InstallDeps) {
    $buildArgs += "-InstallDeps"
}

& $buildScript @buildArgs
if ($LASTEXITCODE -ne 0) {
    throw "EXE build failed."
}

$distFolder = Join-Path $projectRoot "dist\\FocusReminderDesktop"
$onefileExe = Join-Path $projectRoot "dist\\FocusReminderDesktop.exe"
$onedirExe = Join-Path $distFolder "FocusReminderDesktop.exe"

$exePath = if (Test-Path $onedirExe) { $onedirExe } elseif (Test-Path $onefileExe) { $onefileExe } else { $null }
if (-not $exePath) {
    throw "Build completed but EXE was not found."
}

$meta = Get-PEMeta -Path $exePath
if ($meta.machine -ne 0x8664) {
    throw "Output EXE is not x64 (machine=0x$('{0:X}' -f $meta.machine))."
}
if ($meta.subsystem -ne 2) {
    throw "Output EXE is not GUI subsystem (subsystem=$($meta.subsystem)); expected no console window."
}

Write-Host "Validated EXE: x64 + GUI subsystem (no terminal window)."

$releaseRoot = Join-Path $projectRoot "release\\win-x64"
Remove-Item -LiteralPath $releaseRoot -Recurse -Force -ErrorAction SilentlyContinue
if (Test-Path $releaseRoot) {
    throw "Cannot clean $releaseRoot. Close any running FocusReminderDesktop.exe and rerun."
}
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null

if (Test-Path $distFolder) {
    Copy-Item -Path (Join-Path $distFolder "*") -Destination $releaseRoot -Recurse -Force
} else {
    Copy-Item -LiteralPath $onefileExe -Destination $releaseRoot -Force
}

$readmePath = Join-Path $releaseRoot "README_RUN.txt"
Set-Content -Path $readmePath -Encoding UTF8 -Value @"
Focus Reminder Desktop (Win x64)

How to run:
1. Double click FocusReminderDesktop.exe
2. Keep the _internal folder next to FocusReminderDesktop.exe (if present).
3. No terminal window is expected.
4. The app runs in system tray; use tray menu to open settings/statistics.
"@

if ($Zip) {
    $zipName = "FocusReminderDesktop-win-x64-{0}.zip" -f (Get-Date -Format "yyyyMMdd-HHmmss")
    $zipPath = Join-Path $projectRoot ("release\\" + $zipName)
    Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path (Join-Path $releaseRoot "*") -DestinationPath $zipPath
    Write-Host "Zip package: $zipPath"
}

Write-Host "Release folder: $releaseRoot"
exit 0
