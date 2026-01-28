# Quick Start Guide - MT7927 Driver Development

This is a quick reference for developers working on the MT7927 driver.

## Project Overview

**Goal**: Create an open-source Linux driver for MediaTek MT7927 Wi-Fi 7 chipset  
**Status**: Skeleton phase - hardware reverse engineering needed  
**License**: GPL-2.0-only  

## Quick Commands

### Build
```bash
cd driver
make                # Build driver
make clean         # Clean build artifacts
sudo make install  # Install module (not recommended)
```

### Test (if hardware available)
```bash
sudo modprobe mac80211           # Load dependency
sudo insmod driver/mt7927.ko     # Load driver
sudo dmesg | tail -30            # Check kernel log
sudo rmmod mt7927                # Unload driver
```

### Development
```bash
# Check coding style
scripts/checkpatch.pl --no-tree --file driver/mt7927_*.c

# Build documentation (if sphinx installed)
make -C docs html
```

## File Structure

```
driver/
├── mt7927.h           - Main structures and device state
├── mt7927_regs.h      - Register definitions (mostly TODO)
├── mt7927_pci.c       - PCI probe/remove, hardware init
├── mt7927_main.c      - mac80211 integration, callbacks
├── Makefile           - Build system
└── Kconfig            - Kernel configuration

docs/
├── REVERSE_ENGINEERING.md - RE methodology and findings
├── TESTING.md             - Hardware testing guide
└── CONTRIBUTING.md        - Contribution guidelines
```

## Key Data Structures

### Device State
```c
struct mt7927_dev {
    struct pci_dev *pdev;      // PCI device
    void __iomem *regs;        // Register base
    struct ieee80211_hw *hw;   // mac80211 hardware
    // ... see mt7927.h for full structure
};
```

### DMA Queues
```c
struct mt7927_queue {
    struct mt7927_dma_desc *desc;  // DMA descriptors
    dma_addr_t desc_dma;           // DMA handle
    // ... see mt7927.h
};
```

## Implementation Phases

### Phase 1: Skeleton ✅ (Current)
- [x] PCI device detection
- [x] Resource allocation
- [x] mac80211 registration (stub)
- [x] Build system
- [x] Documentation

### Phase 2: Register Discovery (TODO)
- [ ] Identify register addresses
- [ ] Map interrupt controller
- [ ] Find DMA engine registers
- [ ] Document bit fields

### Phase 3: Initialization (TODO)
- [ ] Device reset sequence
- [ ] Firmware loading protocol
- [ ] MAC initialization
- [ ] PHY initialization

### Phase 4: Data Path (TODO)
- [ ] DMA ring setup
- [ ] TX path implementation
- [ ] RX path implementation
- [ ] Interrupt handling

### Phase 5: Advanced Features (TODO)
- [ ] Power management
- [ ] Hardware encryption
- [ ] Advanced PHY features
- [ ] Performance optimization

## Common Tasks

### Adding New Register Definition
```c
// In mt7927_regs.h
#define MT7927_NEW_REG    0x12345678  /* Brief description */

// Document in REVERSE_ENGINEERING.md
// Update inline comments with confidence level
```

### Implementing Hardware Function
```c
static int mt7927_new_function(struct mt7927_dev *dev)
{
    /*
     * TODO: Explain what this function should do
     * Document any assumptions
     * Note confidence level
     */
    
    /* Implementation */
    
    return 0;
}
```

### Adding mac80211 Callback
```c
// In mt7927_main.c
static void mt7927_new_callback(struct ieee80211_hw *hw, ...)
{
    struct mt7927_dev *dev = mt7927_hw_dev(hw);
    
    /* Implementation */
}

// Add to mt7927_ops structure
static const struct ieee80211_ops mt7927_ops = {
    // ...
    .new_callback = mt7927_new_callback,
};
```

## Debugging

### Enable Debug Messages
```c
// Add to driver (temporarily for debugging)
#define DEBUG
#include <linux/printk.h>

pr_debug("Debug message: value=%d\n", val);
dev_dbg(dev->dev, "Device debug: %s\n", msg);
```

### Kernel Log Levels
```bash
# Set log level to show all messages
sudo dmesg -n 8

# Filter driver messages
sudo dmesg | grep mt7927
```

### GDB Kernel Debugging
```bash
# Load module with debug symbols
sudo insmod driver/mt7927.ko

# Attach with gdb (requires kernel debugging enabled)
sudo gdb vmlinux
(gdb) target remote /dev/mem
```

## Reverse Engineering Tips

### Analyzing Windows Driver
1. Extract driver .sys file from installer
2. Load in Ghidra/IDA Pro
3. Find PCI device ID references
4. Trace register accesses
5. Document sequences

### Register Discovery
1. Dump PCI config: `lspci -xxx -s XX:XX.X`
2. Monitor under Windows: PCILeech, WinDbg
3. Compare with similar chips (MT7921)
4. Test on real hardware carefully

### Firmware Analysis
1. Extract from Windows driver
2. Check header/magic bytes
3. Look for version strings
4. Compare with MT7921 firmware
5. Document format

## Testing Checklist

Before committing:
- [ ] Code compiles without warnings
- [ ] Follows kernel coding style
- [ ] Documentation updated
- [ ] TODO/FIXME added for unknowns
- [ ] Commit message is clear

Before loading on hardware:
- [ ] Backup system
- [ ] Review register writes
- [ ] Have recovery plan
- [ ] Document system state
- [ ] Start with read-only operations

## Useful Resources

### Linux Kernel
- [Kernel Documentation](https://www.kernel.org/doc/html/latest/)
- [mac80211 Documentation](https://wireless.wiki.kernel.org/en/developers/documentation/mac80211)
- [PCI Driver HOWTO](https://www.kernel.org/doc/html/latest/PCI/pci.html)

### Reference Drivers
- [mt76 driver](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/net/wireless/mediatek/mt76)
- [mt7921 (most similar)](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/net/wireless/mediatek/mt76/mt7921)

### Tools
- **Ghidra**: Free reverse engineering tool
- **lspci**: PCI device information
- **WinDbg**: Windows kernel debugging
- **Wireshark**: Network protocol analysis

## Getting Help

- **Code Questions**: Add comment in code review
- **Bug Reports**: Open GitHub issue
- **General Questions**: GitHub Discussions
- **Documentation**: Check docs/ directory

## Common Pitfalls

1. **Don't Guess Register Addresses**
   - Always mark unknown addresses as TODO
   - Document confidence level
   - Test on real hardware before committing

2. **Don't Copy Proprietary Code**
   - Clean-room implementation only
   - Reference public documentation
   - Acknowledge reverse engineering sources

3. **Don't Forget Error Handling**
   - Check all return values
   - Clean up on error paths
   - Use goto for cleanup when appropriate

4. **Don't Break ABI**
   - Keep structures extensible
   - Use reserved fields for future use
   - Version your structures

## Next Steps

1. **Get Hardware**: Obtain MT7927-based device
2. **Dump Config**: Capture PCI configuration space
3. **Extract Firmware**: Get firmware from Windows driver
4. **Analyze Driver**: Reverse engineer Windows driver
5. **Implement**: Add functionality as discovered

## Safety Warnings

⚠️ **This is experimental code**
- May damage hardware (unlikely but possible)
- May crash system
- May corrupt data
- Use at your own risk

Always:
- Test in safe environment
- Have backups
- Document everything
- Start conservatively

---

**Version**: 0.0.1-experimental  
**Last Updated**: January 2024  
**Status**: Skeleton complete, awaiting reverse engineering
