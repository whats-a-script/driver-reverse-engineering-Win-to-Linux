<#
    collect_windows.ps1
    Purpose: Collect all Windows-side driver metadata for MT7927 (or any PCI Wi-Fi device)
    Output: C:\Users\Tron\OneDrive\Documents\GitHub\linuxwifi7\TP-link-wifi-MT7927-reverse-engineer\pulled drivers\<device_name>\
    Safe: Read-only, no system modifications
#>

param(
    [string]$DeviceName = "mt7927"
)

# Absolute output root (your chosen path)
$OutputRoot = "C:\Users\Tron\OneDrive\Documents\GitHub\linuxwifi7\TP-link-wifi-MT7927-reverse-engineer\pulled drivers"

# Final output directory
$OutputDir = Join-Path $OutputRoot $DeviceName
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Write-Host "Collecting Windows driver data for device: $DeviceName"
Write-Host "Output directory: $OutputDir"

# -------------------------------
# 1. PCI DEVICE INFORMATION
# -------------------------------
Write-Host "Collecting PCI device information..."

$Pnp = Get-PnpDevice | Where-Object { $_.InstanceId -match "PCI" }

$Wifi = $Pnp | Where-Object {
    $_.FriendlyName -match "MediaTek" -or
    $_.FriendlyName -match "Wi-Fi" -or
    $_.InstanceId -match "VEN_14C3"
}

$Wifi | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\pci_device.json"

# -------------------------------
# 2. DRIVER PACKAGE INFORMATION
# -------------------------------
Write-Host "Collecting driver package information..."

$DriverInfo = Get-WmiObject Win32_PnPSignedDriver |
    Where-Object { $_.DeviceName -match "MediaTek" -or $_.DeviceName -match "Wi-Fi" }

$DriverInfo | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\driver_package.json"

# -------------------------------
# 3. DRIVER FILES (INF, SYS, CAT)
# -------------------------------
Write-Host "Collecting driver file paths..."

$DriverFiles = $DriverInfo | Select-Object DeviceName, DriverVersion, InfName, DriverProviderName, DriverDate, Driver, Manufacturer

$DriverFiles | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\driver_files.json"

# Copy INF/SYS/CAT if possible
foreach ($d in $DriverInfo) {
    if ($d.Driver -and (Test-Path $d.Driver)) {
        try {
            Copy-Item $d.Driver -Destination $OutputDir -Force
        } catch {
            Write-Host "Warning: Could not copy $($d.Driver)"
        }
    }
}

# -------------------------------
# 4. REGISTRY METADATA
# -------------------------------
Write-Host "Collecting registry metadata..."

$RegPaths = @(
    "HKLM:\SYSTEM\CurrentControlSet\Services",
    "HKLM:\SYSTEM\CurrentControlSet\Control\Class"
)

$RegDump = foreach ($path in $RegPaths) {
    Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "MT7927" -or $_.Name -match "MediaTek" } |
        ForEach-Object {
            Get-ItemProperty $_.PsPath -ErrorAction SilentlyContinue
        }
}

$RegDump | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\registry.json"

# -------------------------------
# 5. NETSH WLAN DRIVER INFO
# -------------------------------
Write-Host "Collecting WLAN driver info..."

$Wlan = netsh wlan show drivers
$Wlan | Out-File "$OutputDir\netsh_wlan_drivers.txt"

# -------------------------------
# 6. SYSTEM INFORMATION SNAPSHOT
# -------------------------------
Write-Host "Collecting system info..."

systeminfo | Out-File "$OutputDir\systeminfo.txt"

Get-ComputerInfo | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\computerinfo.json"

# -------------------------------
# 7. PCI CONFIGURATION (OPTIONAL)
# -------------------------------
Write-Host "Collecting PCI config (optional)..."

try {
    pnputil /enum-devices /connected > "$OutputDir\pnputil_devices.txt"
} catch {}

Write-Host "Windows driver data collection complete."