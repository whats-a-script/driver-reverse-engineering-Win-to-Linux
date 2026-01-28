# SPDX-License-Identifier: GPL-2.0-only
#
# Makefile for MediaTek MT7927 (Filogic 380) Wi-Fi 7 driver
#
# This is an out-of-tree driver for the MT7927 chipset.
# Build against current kernel headers.
#

obj-m += mt7927.o

mt7927-objs := \
	mt7927_main.o \
	mt7927_pci.o

# Kernel build directory
KDIR ?= /lib/modules/$(shell uname -r)/build

# Current directory
PWD := $(shell pwd)

# Build flags
ccflags-y := -Wall -Wextra

# Default target: build the module
all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

# Clean build artifacts
clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# Install the module (requires root)
install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a

# Help target
help:
	@echo "Available targets:"
	@echo "  all     - Build the mt7927 kernel module (default)"
	@echo "  clean   - Remove build artifacts"
	@echo "  install - Install the module (requires root)"
	@echo ""
	@echo "Usage: make [target]"

.PHONY: all clean install help
