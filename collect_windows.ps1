<#
    collect_windows.ps1
    Purpose : Collect Windows driver metadata for ANY peripheral device.
    Output  : <OutputRoot>\<DeviceName>\
    Safe    : Read-only. No system modifications.

    Usage:
        .\collect_windows.ps1                                      # list all devices, pick first
        .\collect_windows.ps1 -DeviceName "my_device"             # custom output folder
        .\collect_windows.ps1 -VendorId 0x14C3 -DeviceId 0x7927  # target by PCI/USB IDs
        .\collect_windows.ps1 -DeviceClass "Net"                   # filter by class
        .\collect_windows.ps1 -DeviceClass "USB" -VendorId 0x0BDA  # USB Realtek
#>

param(
    [string]$DeviceName  = "",    # output folder name (auto-derived if empty)
    [string]$VendorId    = "",    # PCI VEN / USB VID  e.g. "0x14C3"
    [string]$DeviceId    = "",    # PCI DEV / USB PID  e.g. "0x7927"
    [string]$DeviceClass = ""     # Windows class filter: Net, MEDIA, HIDClass, Bluetooth, …
)

$OutputRoot = "C:\Users\Tron\OneDrive\Documents\GitHub\linuxwifi7\TP-link-wifi-MT7927-reverse-engineer\pulled drivers"

# Classes that are PCI/system infrastructure — never interesting as target devices
$SkipClasses = @("System","Computer","Processor","Volume","DiskDrive","CDROM",
                 "DiskDrive","HDC","SCSIAdapter","1394","PCMCIA","PrintQueue","Monitor")

# ---------------------------------------------------------------
# Helper: normalise a hex ID string → uppercase no-prefix
# ---------------------------------------------------------------
function NormHex([string]$h) {
    return $h.ToUpper().Replace("0X","").TrimStart("0")
}

# ---------------------------------------------------------------
# 1. Enumerate candidate devices
# ---------------------------------------------------------------
Write-Host "Scanning for peripheral devices..."

$AllDevices = Get-PnpDevice -ErrorAction SilentlyContinue |
    Where-Object {
        ($_.InstanceId -match "^PCI\\" -or $_.InstanceId -match "^USB\\") -and
        $_.Status -ne "Unknown"
    }

# Apply class filter if provided
if ($DeviceClass -ne "") {
    $AllDevices = $AllDevices | Where-Object { $_.Class -match $DeviceClass }
}

# Remove infrastructure classes
$Candidates = $AllDevices | Where-Object {
    $_.Class -notin $SkipClasses -and
    $_.FriendlyName -notmatch "Root Hub|Host Controller|ISA Bridge|PCI Bridge|Host Bridge|ACPI|System|BIOS"
}

# Apply PCI VEN / USB VID filter
if ($VendorId -ne "") {
    $VenHex = NormHex $VendorId
    $Candidates = $Candidates | Where-Object {
        $_.InstanceId -match "VEN_$VenHex" -or $_.InstanceId -match "VID_$VenHex"
    }
}

# Apply PCI DEV / USB PID filter
if ($DeviceId -ne "") {
    $DevHex = NormHex $DeviceId
    $Candidates = $Candidates | Where-Object {
        $_.InstanceId -match "DEV_$DevHex" -or $_.InstanceId -match "PID_$DevHex"
    }
}

if (-not $Candidates) {
    Write-Host "ERROR: No matching devices found."
    Write-Host "       Try removing filters, or use -VendorId / -DeviceId / -DeviceClass."
    exit 1
}

# Show found devices
Write-Host ""
Write-Host "Found devices:"
$i = 1
foreach ($d in $Candidates) {
    Write-Host "  [$i] $($d.FriendlyName)  [$($d.Class)]  $($d.InstanceId)"
    $i++
}
Write-Host ""

# Pick the first one
$Target = $Candidates | Select-Object -First 1
Write-Host "Using: $($Target.FriendlyName)"
Write-Host "ID   : $($Target.InstanceId)"

# Detect bus type
$IsBus_USB = $Target.InstanceId -match "^USB\\"
$IsBus_PCI = $Target.InstanceId -match "^PCI\\"
$BusType   = if ($IsBus_USB) { "USB" } else { "PCI" }
Write-Host "Bus  : $BusType"

# Derive output folder name from IDs if not given
if ($DeviceName -eq "") {
    $IId = $Target.InstanceId.ToUpper()
    if ($IsBus_PCI) {
        $Ven = if ($IId -match "VEN_([0-9A-F]+)") { $Matches[1].ToLower() } else { "unkn" }
        $Dev = if ($IId -match "DEV_([0-9A-F]+)") { $Matches[1].ToLower() } else { "0000" }
        $DeviceName = "ven${Ven}_dev${Dev}"
    } else {
        $Vid = if ($IId -match "VID_([0-9A-F]+)") { $Matches[1].ToLower() } else { "unkn" }
        $Pid = if ($IId -match "PID_([0-9A-F]+)") { $Matches[1].ToLower() } else { "0000" }
        $DeviceName = "usb_vid${Vid}_pid${Pid}"
    }
}

$OutputDir = Join-Path $OutputRoot $DeviceName
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Write-Host "Output folder: $OutputDir"
Write-Host ""

# ---------------------------------------------------------------
# 2. PCI or USB device information
# ---------------------------------------------------------------
Write-Host "[1/7] Device info..."
$Candidates | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\pci_device.json"

# ---------------------------------------------------------------
# 3. Driver package (Win32_PnPSignedDriver)
# ---------------------------------------------------------------
Write-Host "[2/7] Driver package..."
$FriendlyFragment = ($Target.FriendlyName -split " ")[0..2] -join " "
$DriverInfo = Get-WmiObject Win32_PnPSignedDriver -ErrorAction SilentlyContinue |
    Where-Object { $_.DeviceName -match [regex]::Escape(($Target.FriendlyName.Substring(0, [Math]::Min(12,$Target.FriendlyName.Length)))) }

if (-not $DriverInfo) {
    # Fallback: match any driver with a word from the friendly name
    $Words = $Target.FriendlyName -split "\s+" | Where-Object { $_.Length -gt 4 }
    foreach ($Word in $Words) {
        $DriverInfo = Get-WmiObject Win32_PnPSignedDriver -ErrorAction SilentlyContinue |
            Where-Object { $_.DeviceName -match $Word }
        if ($DriverInfo) { break }
    }
}

$DriverInfo | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\driver_package.json"

# ---------------------------------------------------------------
# 4. Driver files (condensed)
# ---------------------------------------------------------------
Write-Host "[3/7] Driver file list..."
$DriverFiles = $DriverInfo | Select-Object DeviceName, DriverVersion, InfName,
                                            DriverProviderName, DriverDate,
                                            Driver, Manufacturer
$DriverFiles | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\driver_files.json"

foreach ($d in $DriverInfo) {
    if ($d.Driver -and (Test-Path $d.Driver -ErrorAction SilentlyContinue)) {
        try { Copy-Item $d.Driver -Destination $OutputDir -Force }
        catch { Write-Host "  Warning: could not copy $($d.Driver)" }
    }
}

# ---------------------------------------------------------------
# 5. Registry metadata
# ---------------------------------------------------------------
Write-Host "[4/7] Registry..."
$RegPaths = @(
    "HKLM:\SYSTEM\CurrentControlSet\Services",
    "HKLM:\SYSTEM\CurrentControlSet\Control\Class"
)
$Words2 = $Target.FriendlyName -split "\s+" | Where-Object { $_.Length -gt 4 }
$RegDump = foreach ($path in $RegPaths) {
    Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $n = $_.Name; $Words2 | Where-Object { $n -match $_ } } |
        ForEach-Object { Get-ItemProperty $_.PsPath -ErrorAction SilentlyContinue }
}
$RegDump | ConvertTo-Json -Depth 6 | Out-File "$OutputDir\registry.json"

# ---------------------------------------------------------------
# 6. WiFi capabilities (netsh) — only for WiFi devices
# ---------------------------------------------------------------
$IsWifi = $Target.FriendlyName -match "Wi-Fi|WiFi|Wireless|WLAN|802\.11" -or
          $Target.Class -match "Net"
if ($IsWifi) {
    Write-Host "[5/7] WiFi capabilities (netsh)..."
    netsh wlan show drivers 2>&1 | Out-File "$OutputDir\netsh_wlan_drivers.txt"
} else {
    Write-Host "[5/7] Skipping netsh (not a WiFi device)."
    "" | Out-File "$OutputDir\netsh_wlan_drivers.txt"
}

# ---------------------------------------------------------------
# 7. System information
# ---------------------------------------------------------------
Write-Host "[6/7] System info..."
systeminfo | Out-File "$OutputDir\systeminfo.txt"
Get-ComputerInfo -ErrorAction SilentlyContinue |
    ConvertTo-Json -Depth 6 | Out-File "$OutputDir\computerinfo.json"

# ---------------------------------------------------------------
# 8. Device-class-specific extras
# ---------------------------------------------------------------
Write-Host "[7/7] Device-specific extras..."

# USB: device descriptor
if ($IsBus_USB) {
    try {
        $UsbDev = Get-WmiObject Win32_USBHub -ErrorAction SilentlyContinue
        $UsbDev | ConvertTo-Json -Depth 4 | Out-File "$OutputDir\usb_hubs.json"
    } catch {}
    # pnputil for USB info
    pnputil /enum-devices /deviceid "$($Target.InstanceId)" 2>&1 |
        Out-File "$OutputDir\pnputil_devices.txt"
}

# PCI: pnputil enum
if ($IsBus_PCI) {
    try { pnputil /enum-devices /connected 2>&1 | Out-File "$OutputDir\pnputil_devices.txt" }
    catch {}
}

# Audio: list audio endpoints
if ($Target.Class -match "MEDIA|Audio") {
    Get-WmiObject Win32_SoundDevice -ErrorAction SilentlyContinue |
        ConvertTo-Json -Depth 4 | Out-File "$OutputDir\audio_devices.json"
}

# Bluetooth: list BT devices
if ($Target.Class -match "Bluetooth") {
    Get-WmiObject Win32_PnPEntity -ErrorAction SilentlyContinue |
        Where-Object { $_.PNPClass -match "Bluetooth" } |
        ConvertTo-Json -Depth 4 | Out-File "$OutputDir\bluetooth_devices.json"
}

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
$VenOut = if ($Target.InstanceId -match "(VEN_|VID_)([0-9A-Fa-f]+)") { "0x$($Matches[2])" } else { "" }
$DevOut = if ($Target.InstanceId -match "(DEV_|PID_)([0-9A-Fa-f]+)") { "0x$($Matches[2])" } else { "" }

Write-Host ""
Write-Host "Collection complete."
Write-Host "Device  : $($Target.FriendlyName)  [$($Target.Class)]"
Write-Host "Bus     : $BusType  $VenOut : $DevOut"
Write-Host "Output  : $OutputDir"
Write-Host ""
Write-Host "Next — run AstraForge:"
Write-Host "  python tools\AstraForge\AstraForge.py windows"
if ($VenOut) {
    Write-Host "  python tools\AstraForge\AstraForge.py windows --vendor-id $VenOut --device-id $DevOut"
}
Write-Host "  python tools\AstraForge\AstraForge.py generate"
