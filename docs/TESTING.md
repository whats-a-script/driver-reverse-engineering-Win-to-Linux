# Testing Guide for MT7927 Driver

This document describes how to test the MT7927 driver on a system with the hardware.

## Prerequisites

### Required Packages
```bash
# Ubuntu/Debian
sudo apt-get install linux-headers-$(uname -r) build-essential

# Ensure mac80211 is available (usually built-in or as module)
# Check if mac80211 is available:
ls /lib/modules/$(uname -r)/kernel/net/mac80211/
# Or check if it's built into the kernel:
zcat /proc/config.gz | grep MAC80211
```

### Required Hardware
- MediaTek MT7927 (Filogic 380) based Wi-Fi adapter
- Known working: TP-Link Archer TXE70E
- PCI ID: 14C3:7927

## Building the Driver

```bash
cd driver
make clean
make
```

This should produce `mt7927.ko` kernel module.

## Pre-Installation Checks

### 1. Verify Hardware is Detected

```bash
# Check if device is present
lspci -nn | grep 14c3:7927

# Example output:
# 03:00.0 Network controller [0280]: MEDIATEK Corp. Device [14c3:7927]
```

### 2. Check Current Driver (if any)

```bash
# See what driver is currently bound
lspci -k -s 03:00.0  # Replace 03:00.0 with your device's bus address

# Unbind existing driver if needed
echo "0000:03:00.0" | sudo tee /sys/bus/pci/drivers/<current_driver>/unbind
```

### 3. Dump PCI Configuration Space

Before loading the experimental driver, capture the device state:

```bash
# Dump PCI config space
sudo lspci -xxx -s 03:00.0 > pci_config_before.txt

# Verbose device info
sudo lspci -vvv -s 03:00.0 > pci_info.txt
```

## Loading the Driver

### Option 1: Manual Load (Recommended for Testing)

```bash
# Load dependencies first
sudo modprobe mac80211
sudo modprobe cfg80211

# Load our driver
sudo insmod mt7927.ko

# Check if it loaded
lsmod | grep mt7927

# Check kernel messages
sudo dmesg | tail -50
```

Expected output in dmesg:
```
[  123.456789] MT7927: MediaTek MT7927 (Filogic 380) Wi-Fi 7 driver v0.0.1-experimental
[  123.456790] MT7927: This is an EXPERIMENTAL driver for reverse engineering
[  123.456791] MT7927: PCI ID: 14c3:7927
[  123.456792] mt7927 0000:03:00.0: MT7927 device detected (PCI ID 14c3:7927)
[  123.456793] mt7927 0000:03:00.0: Driver version: 0.0.1-experimental
[  123.456794] mt7927 0000:03:00.0: Using IRQ 123
[  123.456795] mt7927 0000:03:00.0: Mapped BAR0 to ffffffffc0xxxxxx
[  123.456796] mt7927 0000:03:00.0: Chip ID: 0x7927 (PLACEHOLDER - not read from hardware)
[  123.456797] mt7927 0000:03:00.0: Registering with mac80211
[  123.456798] mt7927 0000:03:00.0: Registered with mac80211 successfully
[  123.456799] mt7927 0000:03:00.0: MT7927 device initialized successfully
[  123.456800] mt7927 0000:03:00.0: NOTE: This is an experimental driver - hardware is not yet functional
```

### Option 2: Persistent Installation (NOT RECOMMENDED)

```bash
# Install the module (requires root)
cd driver
sudo make install

# Load at boot (add to /etc/modules)
echo "mt7927" | sudo tee -a /etc/modules
```

## Verifying Driver Status

### Check Module Information
```bash
modinfo mt7927
lsmod | grep mt7927
```

### Check Device Binding
```bash
# Check if driver is bound to device
ls -l /sys/bus/pci/drivers/mt7927/
lspci -k -s 03:00.0
```

### Check Wireless Interface
```bash
# List network interfaces (NOTE: Currently won't create interface - stub only)
ip link show
iw dev
```

## Unloading the Driver

```bash
# Unload the driver
sudo rmmod mt7927

# Check kernel messages
sudo dmesg | tail -20
```

Expected output:
```
[  456.789012] mt7927 0000:03:00.0: Removing MT7927 device
[  456.789013] mt7927 0000:03:00.0: Unregistering from mac80211
[  456.789014] mt7927 0000:03:00.0: MT7927 device removed
[  456.789015] MT7927: Driver unloaded
```

## Testing Scenarios

### Test 1: Module Load/Unload
**Purpose**: Verify driver initializes and cleans up properly

```bash
# Load
sudo insmod mt7927.ko
sleep 2
sudo dmesg | tail -20 > test1_load.txt

# Unload
sudo rmmod mt7927
sleep 1
sudo dmesg | tail -20 > test1_unload.txt
```

**Success Criteria**:
- Module loads without errors
- Device is detected and bound
- Module unloads cleanly
- No kernel panics or oops

### Test 2: Multiple Load/Unload Cycles
**Purpose**: Check for memory leaks and cleanup issues

```bash
for i in {1..10}; do
    echo "Iteration $i"
    sudo insmod mt7927.ko
    sleep 1
    sudo rmmod mt7927
    sleep 1
done
```

**Success Criteria**:
- All cycles complete successfully
- No increase in memory usage (check /proc/meminfo)
- No warnings in dmesg

### Test 3: Register Access (Requires Implementation)
**Purpose**: Test if we can read/write device registers

This test is not yet implemented as register addresses are unknown.

## Capturing Debug Information

### Full System Information
```bash
# Create debug info bundle
mkdir -p mt7927_debug
cd mt7927_debug

# Kernel version
uname -a > kernel_version.txt

# Module info
modinfo ../driver/mt7927.ko > module_info.txt

# PCI device info
lspci -nn > pci_devices.txt
sudo lspci -vvv -s 03:00.0 > device_verbose.txt
sudo lspci -xxx -s 03:00.0 > device_config.txt

# Kernel messages
sudo dmesg > dmesg.txt

# Loaded modules
lsmod > lsmod.txt

# Create tarball
cd ..
tar czf mt7927_debug.tar.gz mt7927_debug/
```

## Troubleshooting

### Module Won't Load - Symbol Errors
```
mt7927: Unknown symbol ieee80211_alloc_hw_nm (err -2)
```

**Solution**: Load dependencies first
```bash
sudo modprobe cfg80211
sudo modprobe mac80211
```

### Module Won't Load - Version Mismatch
```
mt7927: version magic '6.11.0-xxx' should be '6.11.0-yyy'
```

**Solution**: Rebuild against correct kernel headers
```bash
cd driver
make clean
make
```

### Device Not Detected
```
No output from: lspci -nn | grep 14c3:7927
```

**Possible Causes**:
- Hardware not installed properly
- PCIe slot disabled in BIOS
- Hardware failure

**Solutions**:
- Reseat the card
- Check BIOS settings
- Try different PCIe slot

### Kernel Panic or Oops

If the system crashes when loading the driver:

1. Boot into safe mode or use another kernel
2. Don't load the driver again until investigating
3. Capture crash dump if available (check /var/crash/)
4. Report the issue with full crash log

### No Wireless Interface Created

This is EXPECTED in the current version. The driver only detects the hardware and binds to it - it does not yet initialize the hardware or create network interfaces.

To verify the driver is working:
```bash
# Driver should be bound to device
lspci -k -s 03:00.0 | grep "Kernel driver in use"
# Should show: Kernel driver in use: mt7927
```

## Safety Precautions

### ⚠️ IMPORTANT WARNINGS

1. **Backup Your System** before loading this driver
2. **Hardware Risk**: This driver may damage hardware (unlikely but possible)
3. **System Stability**: May cause kernel panics or system crashes
4. **Data Loss**: Could potentially cause data corruption
5. **No Warranty**: Use entirely at your own risk

### Recommended Testing Environment

- **Virtual Machine**: If possible, pass through the PCIe device to a VM
- **Test System**: Use a non-critical system
- **Backup**: Have full system backup
- **Serial Console**: Set up serial console for debugging if system becomes unresponsive

### Emergency Recovery

If system won't boot after installing the driver:

1. Boot from recovery media
2. Mount root filesystem
3. Remove the driver:
   ```bash
   rm /lib/modules/$(uname -r)/extra/mt7927.ko
   depmod -a
   ```
4. Remove from /etc/modules if added
5. Reboot

## Reporting Issues

When reporting issues, please include:

1. Hardware model and PCI ID
2. Kernel version (uname -a)
3. Complete dmesg output
4. Steps to reproduce
5. PCI configuration space dump
6. Any crash dumps or oops messages

Create an issue on GitHub with this information.

## Contributing Test Results

Your testing helps the project! If you test on real hardware:

1. Document your findings in docs/REVERSE_ENGINEERING.md
2. Include register dumps if you capture any
3. Share any working initialization sequences
4. Report both successes and failures

## Current Limitations

As of v0.0.1-experimental:

- ❌ Does NOT initialize hardware
- ❌ Does NOT create wireless interface  
- ❌ Does NOT transmit or receive packets
- ❌ Does NOT load firmware
- ✅ Does detect device
- ✅ Does bind to PCI device
- ✅ Does allocate resources (IRQ, BARs)

The driver is currently a skeleton for reverse engineering and development.

## Next Steps for Testing

Once reverse engineering progresses:

1. Test firmware loading
2. Test register access
3. Test interrupt handling
4. Test DMA ring setup
5. Test TX/RX paths
6. Test mode changes (STA, AP, Monitor)
7. Performance testing
8. Stress testing

---

**Last Updated**: January 2024  
**Tested Kernel Versions**: None yet (awaiting hardware testing)  
**Known Working Hardware**: None confirmed yet
