# AstraForge v1.2 — Build Script
# Run from the repo root:  .\tools\AstraForge\build.ps1
# Requires: pip install pyinstaller

$ErrorActionPreference = "Stop"
$Root   = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ToolDir = Join-Path $Root "tools\AstraForge"
$Dist   = Join-Path $Root "dist"
$Build  = Join-Path $Root "build"

Write-Host "==> Installing / upgrading PyInstaller..." -ForegroundColor Cyan
pip install --upgrade pyinstaller

Set-Location $ToolDir

Write-Host "`n==> Building GUI EXE (AstraForge.exe)..." -ForegroundColor Cyan
python -m PyInstaller AstraForgeGUI.spec --distpath "$Dist" --workpath "$Build" --noconfirm

Write-Host "`n==> Building CLI EXE (AstraForgeCLI.exe)..." -ForegroundColor Cyan
python -m PyInstaller AstraForgeCLI.spec --distpath "$Dist" --workpath "$Build" --noconfirm

Write-Host "`n==> Build complete." -ForegroundColor Green
Write-Host "    GUI : $Dist\AstraForge.exe"
Write-Host "    CLI : $Dist\AstraForgeCLI.exe"
Write-Host ""
Write-Host "Next step: open installer.iss in Inno Setup Compiler to produce AstraForge_Setup.exe"
