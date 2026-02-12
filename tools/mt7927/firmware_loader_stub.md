# MT7927 Firmware Loader Stub (Pseudocode)

> **Rule:** No proprietary firmware binaries are stored or committed. This document
> only captures control flow and handshake checkpoints.

## Boot Handshake Checklist
- [ ] Assert PCIe link up and read CHIP_ID via `mmio_dump.py`
- [ ] Enable clocks/reset deassert sequence (MAC, WF subsys)
- [ ] Poll MCU mailbox for `READY` bit
- [ ] Upload ROM patch pointer only (no binary here)
- [ ] Send `DOWNLOAD_CFG` with target region (DLM/ILM)
- [ ] Stream firmware image in chunks with checksum per chunk
- [ ] Send `PATCH_FINISH` / `FW_START` command
- [ ] Poll `READY` / `ALIVE` heartbeat
- [ ] Configure DMA rings (RX/TX) in reset state
- [ ] Enable interrupts and verify ISR is silent for 1s

## Pseudocode Skeleton
```c
int mt7927_fw_boot(struct mt7927_dev *dev, const struct fw_image *fw) {
    // 1) Safe pre-checks
    if (!mt7927_chip_id_ok(dev)) return -ENODEV;
    mt7927_reset_mac(dev);

    // 2) Handshake with MCU
    if (!mt7927_mcu_ready(dev)) return -EAGAIN;

    // 3) Firmware download (abstracted)
    for_each_chunk(fw) {
        send_dl_cfg(dev, chunk);
        send_dl_data(dev, chunk);
        send_dl_chk(dev, chunk);
    }

    // 4) Start firmware
    send_fw_start(dev);
    if (!mt7927_wait_alive(dev)) return -ETIMEDOUT;

    // 5) Prepare DMA rings (still disabled)
    mt7927_dma_setup(dev);
    return 0;
}
```

## Safety Defaults
- Default mode is **read-only**: scripts should only observe unless `--unsafe` is passed.
- All writes must be logged with timestamp, command, and rollback notes.
- If any step faults, record incident and re-assert reset to rollback.
