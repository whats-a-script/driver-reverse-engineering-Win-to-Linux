# Windows → Linux Mapping (MT79xx/MT7927)

| Windows Driver Concept | Linux Equivalent | Notes / Required Behavior |
| --- | --- | --- |
| `DriverEntry` registering `WDF_DRIVER_CONFIG` and `EvtDeviceAdd` | `module_init` + `pci_register_driver` (`probe` hook) | Initializes PCI resources; Linux probe should map BARs, set DMA mask, but skip firmware load until approved. |
| `EvtDevicePrepareHardware` / `NdisMSetMiniportAttributes` | `mt7927_pci_probe` (mt76-style) | Configure BAR windows, allocate DMA rings, set IRQs; defer radio bring-up until firmware running. |
| `NdisMiniportInitializeEx` firmware download sequence | `mt7927_mcu_init` / firmware loader stub | Windows pushes ROM patch then RAM firmware; Linux stub should implement same order with checksum/ack handshakes. |
| `OID_DOT11_RESET_REQUEST` / IOCTL dispatch | `cfg80211_ops` (e.g., `disconnect`, `scan`, `set_channel`) | Map OID handlers to cfg80211/mac80211 commands; enforce capability flags. |
| `MiniportSendNetBufferLists` (TX) | `ieee80211_tx` → mt76 TX path | Map TX descriptors; ensure Windows scatter/gather maps to mt76 `mt76_txwi` preparation. |
| `MiniportReturnNetBufferLists` (RX completion) | `mt76_rx_complete` feeding mac80211 | DMA RX ring recycling mirrors Windows NBL return logic. |
| `InterruptServiceRoutine` + `InterruptDpc` | `irq_handler_t` + NAPI poll | Windows top/bottom halves correspond to Linux hardirq handler clearing status then scheduling NAPI. |
| `WdfDeviceIoControl` custom IOCTLs (registry/config) | `debugfs`/`nl80211` vendor commands | Translate non-standard IOCTLs into vendor NL ops or debugfs knobs; document any hardware writes separately. |

Identified Firmware Load Sequence (from Windows driver expectations)
1. Read CHIP_ID and power/clock registers.
2. Apply ROM patch pointer, then download RAM firmware chunks with checksum/ack.
3. Issue `FW_START`/`PATCH_FINISH`, wait for MCU `READY` heartbeat.
4. Configure DMA rings (RX/TX) while radio disabled.
5. Enable interrupts; confirm quiet status before continuing.

Next Mapping TODOs
- Confirm IOCTL IDs and firmware filenames from Windows binaries (needs SYS/INF input).
- Align descriptor formats with DMA probe findings.
- Validate interrupt bits against BAR/MMIO traces.
