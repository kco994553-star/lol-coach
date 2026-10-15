[CmdletBinding()]
param(
    [switch]$InstallPython,
    [switch]$CreateShortcut,
    [switch]$StartAtLogin,
    [switch]$NoBrowser,
    [ValidateRange(0,65535)][int]$Port = 8765,
    [string]$DataDir = (Join-Path $env:LOCALAPPDATA 'LoL-Coach-PC\private'),
    [string]$LcuLockfile,
    [string]$LcuCertificateSha256
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ProjectRoot = $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

function Find-CoachPython {
    $Candidates = @()
    foreach ($Name in @('py.exe','python.exe','python3.exe')) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue
        if ($Command) { $Candidates += $Command.Source }
    }
    $PythonHome = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if (Test-Path -LiteralPath $PythonHome) {
        $Candidates += @(Get-ChildItem -LiteralPath $PythonHome -Filter python.exe -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    }
    foreach ($Candidate in $Candidates) {
        try {
            $CheckArgs = @('-c', 'import sys; assert sys.version_info >= (3,11); print(sys.executable)')
            if ([IO.Path]::GetFileName($Candidate) -eq 'py.exe') { $CheckArgs = @('-3') + $CheckArgs }
            $Resolved = & $Candidate @CheckArgs 2>$null
            if ($LASTEXITCODE -eq 0 -and $Resolved -and (Test-Path -LiteralPath ([string]$Resolved))) { return ([string]$Resolved).Trim() }
        } catch { }
    }
    return $null
}

$Python = Find-CoachPython
if (-not $Python) {
    if (-not $InstallPython) { throw 'Python 3.11+ is required. Run Start-LoL-Coach.cmd or add -InstallPython to install Python for this Windows user.' }
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) { throw 'winget is unavailable. Install Python 3.13 from python.org, then run this launcher again.' }
    Write-Host 'Installing Python 3.13 for the current Windows user...'
    & winget.exe install --exact --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'Python installation did not complete. Install Python 3.13 and run the launcher again.' }
    $Python = Find-CoachPython
    if (-not $Python) { throw 'Python was installed but cannot be found yet. Close this window and run the launcher again.' }
}

$Venv = Join-Path $ProjectRoot '.venv-pc'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host 'Creating the project-local Python environment...'
    & $Python -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment.' }
}
$Requirements = @((Join-Path $ProjectRoot 'requirements-r3.txt'), (Join-Path $ProjectRoot 'requirements-private-cache.txt'))
$DependencyKey = ($Requirements | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash }) -join ':'
$Stamp = Join-Path $Venv 'pc-dependencies.sha256'
if (-not (Test-Path -LiteralPath $Stamp) -or (Get-Content -LiteralPath $Stamp -Raw).Trim() -ne $DependencyKey) {
    Write-Host 'Installing pinned project dependencies in .venv-pc...'
    & $VenvPython -m pip --disable-pip-version-check install -r $Requirements[0] -r $Requirements[1]
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check the internet connection and run again.' }
    Set-Content -LiteralPath $Stamp -Value $DependencyKey -Encoding ASCII
}

New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
$Identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $DataDir '/inheritance:r' '/grant:r' "${Identity}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not protect the local private data directory.' }

if ($CreateShortcut -or $StartAtLogin) {
    $Shell = New-Object -ComObject WScript.Shell
    $Locations = @()
    if ($CreateShortcut) { $Locations += [Environment]::GetFolderPath('Desktop') }
    if ($StartAtLogin) { $Locations += [Environment]::GetFolderPath('Startup') }
    foreach ($Location in $Locations) {
        $Shortcut = $Shell.CreateShortcut((Join-Path $Location 'LoL Coach PC.lnk'))
        $Shortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        $ShortcutArguments = '-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $ProjectRoot 'Start-LoL-Coach.ps1') + '" -Port ' + $Port + ' -DataDir "' + $DataDir + '"'
        if ($LcuLockfile) { $ShortcutArguments += ' -LcuLockfile "' + $LcuLockfile + '"' }
        if ($LcuCertificateSha256) { $ShortcutArguments += ' -LcuCertificateSha256 "' + $LcuCertificateSha256 + '"' }
        $Shortcut.Arguments = $ShortcutArguments
        $Shortcut.WorkingDirectory = $ProjectRoot
        $Shortcut.Description = 'Local pre-game LoL Coach; keep the launcher window open'
        $Shortcut.Save()
    }
}
$ServerArguments = @((Join-Path $ProjectRoot 'scripts\launch_pc.py'), '--port', [string]$Port, '--data-dir', $DataDir)
if ($NoBrowser) { $ServerArguments += '--no-browser' }
if ($LcuLockfile) { $ServerArguments += @('--lcu-lockfile', $LcuLockfile) }
if ($LcuCertificateSha256) { $ServerArguments += @('--lcu-certificate-sha256', $LcuCertificateSha256) }
& $VenvPython @ServerArguments
if ($LASTEXITCODE -ne 0) { throw 'The local app stopped. Check whether it is already running or choose another port.' }
