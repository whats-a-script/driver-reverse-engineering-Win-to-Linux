/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Copyright (C) 2024 Experimental MT7927 Driver Project
 *
 * Register definitions for MediaTek MT7927 (Filogic 380)
 *
 * IMPORTANT: Most of these register addresses are UNKNOWN and need to be
 * reverse-engineered. Do NOT use these values without verification!
 *
 * The values here are placeholders based on patterns from other MediaTek
 * chips (mt7921, mt7922, etc.) and may be completely incorrect for MT7927.
 */

#ifndef __MT7927_REGS_H
#define __MT7927_REGS_H

/*
 * Base addresses for register blocks
 * TODO: These need to be discovered through reverse engineering
 */
#define MT7927_TOP_BASE			0x00000000
#define MT7927_MCU_BASE			0x00080000
#define MT7927_WFDMA_BASE		0x00024000
#define MT7927_MAC_BASE			0x00020000

/*
 * Chip ID and version registers
 * NOTE: Location unknown - these are guesses
 */
#define MT7927_TOP_MISC			0x00000000	/* TODO: Verify */
#define MT7927_CHIP_ID			0x00000000	/* TODO: Verify */
#define MT7927_HW_VER			0x00000004	/* TODO: Verify */
#define MT7927_FW_VER			0x00000008	/* TODO: Verify */

/*
 * Interrupt registers
 * TODO: Actual addresses need to be reverse-engineered
 */
#define MT7927_INT_STATUS		0x00000000	/* TODO: Verify */
#define MT7927_INT_MASK			0x00000004	/* TODO: Verify */

/* Interrupt bits - TODO: Verify these exist and their bit positions */
#define MT7927_INT_TX_DONE		BIT(0)		/* TX completion */
#define MT7927_INT_RX_DONE		BIT(1)		/* RX packet ready */
#define MT7927_INT_MCU_CMD		BIT(2)		/* MCU command */
#define MT7927_INT_ALL			0xFFFFFFFF	/* All interrupts */

/*
 * DMA engine registers (WFDMA)
 * TODO: Need to discover actual register layout
 */
#define MT7927_WFDMA_GLO_CFG		0x00000000	/* TODO: Verify */
#define MT7927_WFDMA_RST		0x00000004	/* TODO: Verify */

/*
 * TX queue registers
 * TODO: Discover actual TX queue control registers
 */
#define MT7927_TX_RING_BASE(n)		(0x00000000 + (n) * 0x10)  /* TODO: Verify */
#define MT7927_TX_RING_CNT(n)		(0x00000004 + (n) * 0x10)  /* TODO: Verify */
#define MT7927_TX_RING_CIDX(n)		(0x00000008 + (n) * 0x10)  /* TODO: Verify */
#define MT7927_TX_RING_DIDX(n)		(0x0000000C + (n) * 0x10)  /* TODO: Verify */

/*
 * RX queue registers
 * TODO: Discover actual RX queue control registers
 */
#define MT7927_RX_RING_BASE(n)		(0x00000000 + (n) * 0x10)  /* TODO: Verify */
#define MT7927_RX_RING_CNT(n)		(0x00000004 + (n) * 0x10)  /* TODO: Verify */
#define MT7927_RX_RING_CIDX(n)		(0x00000008 + (n) * 0x10)  /* TODO: Verify */
#define MT7927_RX_RING_DIDX(n)		(0x0000000C + (n) * 0x10)  /* TODO: Verify */

/*
 * MCU communication registers
 * TODO: Discover MCU mailbox/command interface
 */
#define MT7927_MCU_CMD			0x00000000	/* TODO: Verify */
#define MT7927_MCU_STATUS		0x00000004	/* TODO: Verify */

/*
 * MAC configuration registers
 * TODO: Discover MAC layer register layout
 */
#define MT7927_MAC_ADDR_0		0x00000000	/* TODO: Verify */
#define MT7927_MAC_ADDR_1		0x00000004	/* TODO: Verify */

/*
 * PHY configuration registers
 * TODO: Discover PHY configuration interface
 */
#define MT7927_PHY_CTRL			0x00000000	/* TODO: Verify */

/*
 * Power management registers
 * TODO: Discover power management interface
 */
#define MT7927_PM_CTRL			0x00000000	/* TODO: Verify */

/*
 * Firmware loading
 * TODO: Discover firmware download protocol and registers
 */
#define MT7927_FW_DL_ADDR		0x00000000	/* TODO: Verify */
#define MT7927_FW_DL_CTRL		0x00000004	/* TODO: Verify */

#endif /* __MT7927_REGS_H */
