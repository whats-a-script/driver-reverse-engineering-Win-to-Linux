/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Copyright (C) 2024 Experimental MT7927 Driver Project
 *
 * Main header file for MediaTek MT7927 (Filogic 380) Wi-Fi 7 driver
 *
 * This is an experimental, reverse-engineered driver. Register addresses,
 * firmware protocols, and hardware behavior are largely UNKNOWN and need
 * to be discovered through reverse engineering.
 */

#ifndef __MT7927_H
#define __MT7927_H

#include <linux/pci.h>
#include <linux/module.h>
#include <linux/interrupt.h>
#include <linux/workqueue.h>
#include <net/mac80211.h>

/* Driver version */
#define MT7927_DRIVER_VERSION "0.0.1-experimental"

/* PCI IDs for MT7927 (Filogic 380) */
#define MT7927_PCI_VENDOR_ID	0x14c3
#define MT7927_PCI_DEVICE_ID	0x7927

/*
 * Hardware constants
 * NOTE: These are educated guesses based on similar MediaTek chips.
 * Actual values need to be confirmed through reverse engineering.
 */
#define MT7927_MAX_TX_RINGS	4	/* TODO: Verify actual value */
#define MT7927_MAX_RX_RINGS	2	/* TODO: Verify actual value */
#define MT7927_TX_RING_SIZE	128	/* TODO: Verify actual value */
#define MT7927_RX_RING_SIZE	256	/* TODO: Verify actual value */

/*
 * DMA ring descriptor
 * TODO: Actual structure needs to be reverse-engineered from hardware/firmware
 */
struct mt7927_dma_desc {
	__le32 buf_addr;	/* Buffer physical address */
	__le32 ctrl;		/* Control flags */
	/* Additional fields TBD */
} __packed;

/*
 * TX/RX queue structure
 * Placeholder for DMA ring management
 */
struct mt7927_queue {
	struct mt7927_dma_desc *desc;	/* DMA descriptor ring */
	dma_addr_t desc_dma;		/* DMA handle for descriptors */
	void **buf;			/* Buffer pointers */
	u16 head;			/* Queue head index */
	u16 tail;			/* Queue tail index */
	u16 size;			/* Queue size */
	u8 hw_idx;			/* Hardware queue index */
};

/*
 * Main device structure
 * Contains per-device state for an MT7927 adapter
 */
struct mt7927_dev {
	struct pci_dev *pdev;			/* PCI device */
	struct device *dev;			/* Generic device */

	/* Memory-mapped I/O */
	void __iomem *regs;			/* Register base address */

	/* MAC80211 integration */
	struct ieee80211_hw *hw;		/* mac80211 hardware */

	/* TX/RX queues */
	struct mt7927_queue tx_q[MT7927_MAX_TX_RINGS];
	struct mt7927_queue rx_q[MT7927_MAX_RX_RINGS];

	/* Interrupts */
	int irq;				/* IRQ number */
	u32 irq_mask;				/* Current interrupt mask */

	/* Workqueue for deferred processing */
	struct workqueue_struct *wq;

	/* Device state */
	bool initialized;			/* Driver initialized */
	bool fw_loaded;				/* Firmware loaded */

	/* Firmware information */
	const struct firmware *fw;		/* Firmware blob */

	/* Statistics */
	u64 tx_packets;
	u64 rx_packets;
	u64 tx_errors;
	u64 rx_errors;
};

/*
 * Convert ieee80211_hw to mt7927_dev
 */
static inline struct mt7927_dev *mt7927_hw_dev(struct ieee80211_hw *hw)
{
	return (struct mt7927_dev *)hw->priv;
}

/*
 * Function prototypes - mt7927_main.c
 */
int mt7927_register_device(struct mt7927_dev *dev);
void mt7927_unregister_device(struct mt7927_dev *dev);

/*
 * Function prototypes - mt7927_pci.c
 */
int mt7927_pci_probe(struct pci_dev *pdev, const struct pci_device_id *id);
void mt7927_pci_remove(struct pci_dev *pdev);

/*
 * Hardware access helpers
 * TODO: Verify register access patterns for MT7927
 */
static inline u32 mt7927_rr(struct mt7927_dev *dev, u32 offset)
{
	return readl(dev->regs + offset);
}

static inline void mt7927_wr(struct mt7927_dev *dev, u32 offset, u32 val)
{
	writel(val, dev->regs + offset);
}

#endif /* __MT7927_H */
