# Запуск с правами администратора (если нет - перезапуск с ними)
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Start-Process powershell "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "Stop"

$pythonVersion = "3.13.3"
$pythonInstaller = "python-$pythonVersion-amd64.exe"
$downloadUrl = "https://www.python.org/ftp/python/$pythonVersion/$pythonInstaller"
$installDir = "$env:ProgramFiles\Python$($pythonVersion.Replace('.', ''))"
$pythonExe = "$installDir\python.exe"

Write-Host "`nInstalling Python $pythonVersion and dependencies..."

if (-Not (Test-Path $pythonExe)) {
    Write-Host "`nPython installer found at: $PSScriptRoot\$pythonInstaller"
    if (-Not (Test-Path "$PSScriptRoot\$pythonInstaller")) {
        Write-Host "Downloading Python installer..."
        Invoke-WebRequest -Uri $downloadUrl -OutFile "$PSScriptRoot\$pythonInstaller"
    }
    Write-Host "Installing Python silently..."
    Start-Process -Wait -FilePath "$PSScriptRoot\$pythonInstaller" -ArgumentList @(
        "/quiet",
        "InstallAllUsers=1",
        "PrependPath=1",
        "Include_pip=1",
        "TargetDir=$installDir"
    )
} else {
    Write-Host "`nPython is already installed at: $installDir"
}

if (-Not (Test-Path $pythonExe)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonExe = $pythonCommand.Source
    } else {
        Write-Host "Error: Python executable not found after installation."
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

$envPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
if ($envPath -notlike "*$installDir*") {
    Write-Host "Updating system PATH..."
    $newPath = "$envPath;$installDir;$installDir\Scripts"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
}

$requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
if (-Not (Test-Path $requirementsPath)) {
    Write-Host "`nError: requirements.txt not found at $requirementsPath"
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "`nInstalling dependencies..."
& "$pythonExe" -m pip install --upgrade pip
& "$pythonExe" -m pip install -r $requirementsPath

Write-Host "`nInstallation completed."
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
