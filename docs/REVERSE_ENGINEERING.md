# Reverse Engineering Notes - MediaTek MT7927

This document contains notes, findings, and methodologies for reverse engineering the MediaTek MT7927 (Filogic 380) Wi-Fi 7 chipset.

## Hardware Information

### PCI Device Details
- **Vendor ID**: 0x14C3 (MediaTek Inc.)
- **Device ID**: 0x7927
- **Subsystem Vendor**: TBD (depends on manufacturer)
- **Subsystem Device**: TBD
- **Class**: Network controller (0x0280)
- **Revision**: Unknown

### Physical Characteristics
- **Interface**: PCIe (generation unknown, likely Gen 3 or Gen 4)
- **Form Factor**: M.2 or PCIe card (device dependent)
- **Antennas**: External (typically 2-4 for tri-band operation)

### Known Compatible Devices
1. **TP-Link Archer TXE70E**
   - PCIe Wi-Fi 7 adapter
   - Tri-band (2.4/5/6 GHz)
   - Windows driver available

## Reverse Engineering Methodology

### Phase 1: Information Gathering ✓

#### 1.1 PCI Configuration Space Analysis
```bash
# Dump PCI configuration space (if hardware available)
lspci -vvv -d 14c3:7927

# Dump PCI config space to file
sudo lspci -xxx -d 14c3:7927 > pci_config.txt
```

**Expected Information**:
- BAR (Base Address Register) layout
- Interrupt configuration
- Capabilities (MSI, MSI-X, etc.)
- Power management features

#### 1.2 Driver Analysis
- [ ] Extract Windows driver from manufacturer
- [ ] Identify driver version and date
- [ ] Extract firmware blob(s) from driver package
- [ ] Identify any configuration files or INI files

**Tools**:
- 7-Zip or similar for extraction
- `binwalk` for finding embedded firmware
- `strings` for finding text strings

#### 1.3 Related Chipset Study
Study similar MediaTek chips with existing Linux drivers:
- **MT7921** (Wi-Fi 6E, PCIe) - Most similar
- **MT7922** (Wi-Fi 6E, USB/SDIO)
- **MT7915** (Wi-Fi 6, PCIe)

Compare register layouts, initialization sequences, and firmware protocols.

### Phase 2: Static Analysis (In Progress)

#### 2.1 Windows Driver Analysis
**Tools**: Ghidra, IDA Pro, Binary Ninja

**Tasks**:
- [ ] Load driver .sys file into disassembler
- [ ] Identify PCI probe/initialization functions
- [ ] Find register read/write functions
- [ ] Map out register addresses used
- [ ] Identify firmware loading code
- [ ] Document initialization sequence

**Key Functions to Find**:
- DriverEntry (driver initialization)
- AddDevice (device probe)
- PCI config space access
- Memory-mapped I/O access
- Interrupt handlers
- Firmware download routines

#### 2.2 Firmware Analysis
- [ ] Extract firmware binary from Windows driver
- [ ] Determine firmware format (encrypted? compressed?)
- [ ] Identify firmware header structure
- [ ] Look for signature or checksum validation
- [ ] Search for command/response structures

**Tools**:
- `binwalk` - Firmware analysis
- `hexdump` - Binary inspection
- Ghidra/IDA - Binary analysis

### Phase 3: Dynamic Analysis (TODO)

#### 3.1 Windows Driver Tracing
Capture actual hardware behavior under Windows:

**Option A: PCIe Bus Sniffer** (Hardware)
- Requires expensive PCIe analyzer hardware
- Captures all PCIe transactions
- Most accurate but costly

**Option B: Driver Tracing** (Software)
Tools to trace Windows driver behavior:
- **PCILeech** - DMA-based PCIe tracing
- **WinDbg** - Kernel debugging with breakpoints
- **API Monitor** - Capture driver I/O
- **Wireshark** - Capture network traffic

**Steps**:
1. Install driver in Windows (VM recommended)
2. Set up tracing tool
3. Perform operations (connect, scan, transmit)
4. Capture register accesses
5. Document sequences

#### 3.2 Register Discovery
- [ ] Map register addresses to functions
- [ ] Identify bit fields in control registers
- [ ] Document read-only vs read-write registers
- [ ] Find interrupt status/mask registers
- [ ] Locate DMA descriptor registers

#### 3.3 Firmware Protocol Analysis
- [ ] Capture firmware download sequence
- [ ] Identify command structure
- [ ] Document response format
- [ ] Map command IDs to functions

### Phase 4: Implementation (TODO)

Once register maps and protocols are understood:

1. **Update Register Definitions** (`mt7927_regs.h`)
   - Replace placeholder addresses with real ones
   - Document each register's purpose
   - Add bit field definitions

2. **Implement Hardware Initialization**
   - Device reset sequence
   - Clock/power configuration
   - Firmware download
   - MAC/PHY initialization

3. **Implement DMA Engine**
   - Descriptor format
   - TX/RX ring setup
   - Pointer management
   - Completion handling

4. **Implement Interrupt Handling**
   - Status register reading
   - Interrupt demultiplexing
   - Work queue scheduling

5. **Implement TX/RX**
   - Packet preparation
   - Descriptor filling
   - DMA management
   - Completion processing

## Findings Log

### Date: 2024-01-XX - Initial Setup
- Created driver skeleton
- PCI IDs confirmed: 14C3:7927
- Driver compiles successfully
- No hardware testing yet

### Date: TBD - PCI Configuration
*(Future entries will go here)*

## Register Map (Work in Progress)

| Address | Name | Access | Purpose | Status |
|---------|------|--------|---------|--------|
| TBD | CHIP_ID | RO | Chip identification | Unknown |
| TBD | HW_VER | RO | Hardware version | Unknown |
| TBD | FW_VER | RO | Firmware version | Unknown |
| TBD | INT_STATUS | RO | Interrupt status | Unknown |
| TBD | INT_MASK | RW | Interrupt mask | Unknown |

*(This table will be populated as registers are discovered)*

## Firmware Format (Work in Progress)

### Firmware File
- **Expected Name**: Unknown (possibly `WIFI_RAM_CODE_MT7927.bin` or similar)
- **Size**: Unknown
- **Format**: Unknown (likely custom format)

### Structure (Hypothesis)
Based on other MT76xx firmware:
```
+------------------+
| Header           |  (Magic, version, size, checksum)
+------------------+
| Section 1        |  (Code/data segment)
+------------------+
| Section 2        |  (Code/data segment)
+------------------+
| ...              |
+------------------+
```

## DMA Descriptor Format (Work in Progress)

### TX Descriptor (Hypothesis)
```c
struct mt7927_tx_desc {
    __le32 buf_addr_lo;     /* Buffer address [31:0] */
    __le32 buf_addr_hi;     /* Buffer address [63:32] */
    __le16 buf_len;         /* Buffer length */
    __le16 flags;           /* Control flags */
    /* Additional fields TBD */
};
```

### RX Descriptor (Hypothesis)
```c
struct mt7927_rx_desc {
    __le32 buf_addr_lo;     /* Buffer address [31:0] */
    __le32 buf_addr_hi;     /* Buffer address [63:32] */
    __le16 buf_len;         /* Buffer length */
    __le16 flags;           /* Status flags */
    /* Additional fields TBD */
};
```

## Command/Event Protocol (Work in Progress)

### MCU Command Format (Hypothesis)
```c
struct mt7927_mcu_cmd {
    __le16 cmd_id;          /* Command identifier */
    __le16 seq;             /* Sequence number */
    __le32 len;             /* Payload length */
    u8 data[];              /* Command payload */
};
```

## Known Issues and Challenges

### Technical Challenges
1. **No Hardware Available for Testing**
   - Cannot verify register addresses
   - Cannot test initialization sequences
   - Must rely on static analysis initially

2. **Firmware Not Public**
   - Must extract from Windows driver
   - May be encrypted or obfuscated
   - Download protocol unknown

3. **Limited Documentation**
   - No public datasheet
   - No reference manual
   - Must infer from similar chips

### Legal Considerations
- Windows driver is copyrighted - cannot copy code
- Firmware may be copyrighted - cannot redistribute
- Must implement clean-room driver
- Reverse engineering for interoperability generally legal

## Tools and Resources

### Essential Tools
- **Ghidra** - Free disassembler/decompiler
- **lspci** - PCI device information
- **hexdump** - Binary file inspection
- **binwalk** - Firmware analysis

### Optional Tools
- **IDA Pro** - Commercial disassembler
- **Wireshark** - Network traffic analysis
- **WinDbg** - Windows kernel debugging
- **PCILeech** - PCIe DMA analysis

### Reference Documentation
- [MT76 Driver Source](https://github.com/torvalds/linux/tree/master/drivers/net/wireless/mediatek/mt76)
- [Linux mac80211 Documentation](https://wireless.wiki.kernel.org/)
- [PCI Local Bus Specification](https://pcisig.com/)
- [IEEE 802.11 Standards](https://www.ieee802.org/11/)

## Next Steps

### Immediate (Priority 1)
1. Obtain TP-Link Archer TXE70E or similar device
2. Dump PCI configuration space
3. Extract Windows driver package
4. Extract firmware binary

### Short Term (Priority 2)
1. Analyze Windows driver with Ghidra
2. Map register addresses
3. Document initialization sequence
4. Understand firmware format

### Medium Term (Priority 3)
1. Implement register definitions
2. Implement firmware loading
3. Implement basic initialization
4. Test on real hardware

### Long Term (Priority 4)
1. Implement full TX/RX paths
2. Add power management
3. Optimize performance
4. Submit to upstream Linux kernel

## Contributing Findings

If you discover something about the MT7927 hardware:

1. Document your findings clearly
2. Include evidence (register dumps, traces, etc.)
3. Update this document or add new ones
4. Share via GitHub pull request

**Template for New Findings**:
```markdown
### Date: YYYY-MM-DD - Finding Title

**Component**: (e.g., Interrupt Controller, DMA Engine)

**Method**: (How you discovered this)

**Finding**:
(Detailed description)

**Evidence**:
(Register dumps, traces, code snippets)

**Confidence**: (Low/Medium/High)
```

## Acknowledgments

Thanks to:
- Linux mt76 driver developers for reference implementation
- Ghidra project for reverse engineering tools
- Linux wireless community for documentation and support

---

**Document Version**: 0.1  
**Last Updated**: January 2024  
**Status**: Early documentation phase
