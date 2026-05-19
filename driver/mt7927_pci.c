// SPDX-License-Identifier: GPL-2.0-only
/*
 * Copyright (C) 2024 Experimental MT7927 Driver Project
 *
 * PCIe interface for MediaTek MT7927 (Filogic 380) Wi-Fi 7 driver
 *
 * This implements the PCI device binding, resource allocation, and
 * basic hardware initialization for the MT7927 chipset.
 */

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/interrupt.h>

#include "mt7927.h"
#include "mt7927_regs.h"

/*
 * PCI device ID table
 * This binds the driver to MT7927 devices
 */
static const struct pci_device_id mt7927_pci_id_table[] = {
	{
		PCI_DEVICE(MT7927_PCI_VENDOR_ID, MT7927_PCI_DEVICE_ID)
	},
	{ } /* Terminator */
};
MODULE_DEVICE_TABLE(pci, mt7927_pci_id_table);

/*
 * Interrupt handler
 * TODO: Implement proper interrupt handling once register layout is known
 */
static irqreturn_t mt7927_interrupt_handler(int irq __maybe_unused, void *dev_id __maybe_unused)
{
	/*
	 * TODO: Implement interrupt handling:
	 * - Read interrupt status
	 * - Handle TX completion
	 * - Handle RX packets
	 * - Handle MCU events
	 * - Clear interrupt status
	 */

	return IRQ_HANDLED;
}

/*
 * Enable/disable PCI device
 */
static int mt7927_pci_enable_device(struct pci_dev *pdev)
{
	int ret;

	ret = pci_enable_device(pdev);
	if (ret) {
		dev_err(&pdev->dev, "Failed to enable PCI device: %d\n", ret);
		return ret;
	}

	pci_set_master(pdev);

	return 0;
}

/*
 * Set up DMA mask
 * MT7927 likely supports 64-bit DMA based on modern PCIe standards
 */
static int mt7927_pci_set_dma_mask(struct pci_dev *pdev)
{
	int ret;

	/* Try 64-bit DMA first */
	ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
	if (ret) {
		/* Fallback to 32-bit DMA */
		dev_info(&pdev->dev, "64-bit DMA not available, using 32-bit\n");
		ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
		if (ret) {
			dev_err(&pdev->dev, "Failed to set DMA mask: %d\n", ret);
			return ret;
		}
	}

	return 0;
}

/*
 * Map PCI BAR to kernel virtual address
 * Maps BAR0 for device registers and BAR2 for additional memory regions
 */
static int mt7927_pci_map_bars(struct mt7927_dev *dev)
{
	struct pci_dev *pdev = dev->pdev;
	int ret;

	/* Request PCI regions */
	ret = pci_request_regions(pdev, KBUILD_MODNAME);
	if (ret) {
		dev_err(dev->dev, "Failed to request PCI regions: %d\n", ret);
		return ret;
	}

	/*
	 * Map BAR0 - contains device registers
	 */
	dev->regs = pci_iomap(pdev, 0, 0);
	if (!dev->regs) {
		dev_err(dev->dev, "Failed to map BAR0\n");
		pci_release_regions(pdev);
		return -ENOMEM;
	}

	dev_info(dev->dev, "Mapped BAR0 to %p\n", dev->regs);

	/*
	 * Map BAR2 - additional memory region
	 * Used for extended functionality (DMA, firmware, etc.)
	 */
	dev->bar2 = pci_iomap(pdev, 2, 0);
	if (!dev->bar2) {
		dev_err(dev->dev, "Failed to map BAR2\n");
		pci_iounmap(pdev, dev->regs);
		dev->regs = NULL;
		pci_release_regions(pdev);
		return -ENOMEM;
	}

	dev_info(dev->dev, "Mapped BAR2 to %p\n", dev->bar2);
	return 0;
}

/*
 * Unmap PCI BARs
 */
static void mt7927_pci_unmap_bars(struct mt7927_dev *dev)
{
	struct pci_dev *pdev = dev->pdev;

	if (dev->bar2) {
		pci_iounmap(pdev, dev->bar2);
		dev->bar2 = NULL;
	}

	if (dev->regs) {
		pci_iounmap(pdev, dev->regs);
		dev->regs = NULL;
	}

	pci_release_regions(pdev);
}

/*
 * Read hardware chip ID
 * TODO: Discover actual chip ID register location
 */
static int mt7927_read_chip_id(struct mt7927_dev *dev)
{
	u32 chip_id;

	/*
	 * This is a placeholder. We don't know the actual register address
	 * for reading the chip ID. Need to reverse engineer this.
	 */
	chip_id = 0x7927; /* Hardcoded for now */

	dev_info(dev->dev, "Chip ID: 0x%04x (PLACEHOLDER - not read from hardware)\n",
		 chip_id);

	/*
	 * TODO: Once we know the register address:
	 * chip_id = mt7927_rr(dev, MT7927_CHIP_ID);
	 * Validate that it matches expected value
	 */

	return 0;
}

/*
 * PCI probe function
 * Called when a MT7927 device is detected
 */
int mt7927_pci_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
	struct mt7927_dev *dev;
	int ret;

	dev_info(&pdev->dev, "MT7927 device detected (PCI ID %04x:%04x)\n",
		 pdev->vendor, pdev->device);
	dev_info(&pdev->dev, "Driver version: %s\n", MT7927_DRIVER_VERSION);

	/* Allocate device structure */
	dev = devm_kzalloc(&pdev->dev, sizeof(*dev), GFP_KERNEL);
	if (!dev)
		return -ENOMEM;

	dev->pdev = pdev;
	dev->dev = &pdev->dev;
	pci_set_drvdata(pdev, dev);

	/* Enable PCI device */
	ret = mt7927_pci_enable_device(pdev);
	if (ret)
		return ret;

	/* Set up DMA */
	ret = mt7927_pci_set_dma_mask(pdev);
	if (ret)
		goto err_disable_device;

	/* Map register space */
	ret = mt7927_pci_map_bars(dev);
	if (ret)
		goto err_disable_device;

	/* Read chip ID to verify hardware */
	ret = mt7927_read_chip_id(dev);
	if (ret)
		goto err_unmap_bars;

	/* Enable MSI for better interrupt performance */
	ret = pci_enable_msi(pdev);
	if (ret) {
		dev_warn(dev->dev, "Failed to enable MSI: %d, falling back to legacy interrupts\n", ret);
		/* Continue with legacy interrupts - not a fatal error */
	} else {
		dev_info(dev->dev, "MSI enabled successfully\n");
	}

	/* Request IRQ */
	ret = devm_request_irq(&pdev->dev, pdev->irq, mt7927_interrupt_handler,
			       IRQF_SHARED, KBUILD_MODNAME, dev);
	if (ret) {
		dev_err(dev->dev, "Failed to request IRQ %d: %d\n",
			pdev->irq, ret);
		goto err_unmap_bars;
	}
	dev->irq = pdev->irq;
	dev_info(dev->dev, "Using IRQ %d\n", dev->irq);

	/*
	 * TODO: Initialize hardware components in sequence:
	 * 1. Reset device
	 * 2. Load firmware
	 * 3. Initialize MAC layer
	 * 4. Initialize PHY layer
	 * 5. Set up DMA rings
	 * 6. Enable interrupts
	 */

	/* Register with mac80211 */
	ret = mt7927_register_device(dev);
	if (ret) {
		dev_err(dev->dev, "Failed to register with mac80211: %d\n", ret);
		goto err_unmap_bars;
	}

	dev->initialized = true;
	dev_info(dev->dev, "MT7927 device initialized successfully\n");
	dev_info(dev->dev, "NOTE: This is an experimental driver - hardware is not yet functional\n");

	return 0;

err_unmap_bars:
	pci_disable_msi(pdev);
	mt7927_pci_unmap_bars(dev);
err_disable_device:
	pci_disable_device(pdev);
	return ret;
}

/*
 * PCI remove function
 * Called when device is removed or driver is unloaded
 */
void mt7927_pci_remove(struct pci_dev *pdev)
{
	struct mt7927_dev *dev = pci_get_drvdata(pdev);

	dev_info(&pdev->dev, "Removing MT7927 device\n");

	if (!dev)
		return;

	/* Mark as not initialized */
	dev->initialized = false;

	/* Unregister from mac80211 */
	mt7927_unregister_device(dev);

	/*
	 * TODO: Shutdown hardware in reverse order:
	 * 1. Disable interrupts
	 * 2. Stop DMA
	 * 3. Power down MAC/PHY
	 * 4. Release firmware
	 */

	/* IRQ is freed automatically by devm */

	/* Disable MSI if it was enabled */
	pci_disable_msi(pdev);

	/* Unmap register space */
	mt7927_pci_unmap_bars(dev);

	/* Disable PCI device */
	pci_disable_device(pdev);

	dev_info(&pdev->dev, "MT7927 device removed\n");
}

/*
 * PCI driver structure
 */
static struct pci_driver mt7927_pci_driver = {
	.name		= KBUILD_MODNAME,
	.id_table	= mt7927_pci_id_table,
	.probe		= mt7927_pci_probe,
	.remove		= mt7927_pci_remove,
};

/*
 * Module initialization
 */
static int __init mt7927_pci_init(void)
{
	int ret;

	pr_info("MT7927: MediaTek MT7927 (Filogic 380) Wi-Fi 7 driver v%s\n",
		MT7927_DRIVER_VERSION);
	pr_info("MT7927: This is an EXPERIMENTAL driver for reverse engineering\n");
	pr_info("MT7927: PCI ID: %04x:%04x\n",
		MT7927_PCI_VENDOR_ID, MT7927_PCI_DEVICE_ID);

	ret = pci_register_driver(&mt7927_pci_driver);
	if (ret) {
		pr_err("MT7927: Failed to register PCI driver: %d\n", ret);
		return ret;
	}

	return 0;
}
module_init(mt7927_pci_init);

/*
 * Module cleanup
 */
static void __exit mt7927_pci_exit(void)
{
	pci_unregister_driver(&mt7927_pci_driver);
	pr_info("MT7927: Driver unloaded\n");
}
module_exit(mt7927_pci_exit);

MODULE_AUTHOR("Experimental MT7927 Driver Project");
MODULE_DESCRIPTION("MediaTek MT7927 (Filogic 380) Wi-Fi 7 PCIe Driver");
MODULE_LICENSE("GPL");
MODULE_VERSION(MT7927_DRIVER_VERSION);
