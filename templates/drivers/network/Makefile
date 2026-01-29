# Makefile for kernel module

# Module name - change this for your driver
MODULE_NAME := example_net

# Source files
obj-m := $(MODULE_NAME).o
$(MODULE_NAME)-objs := network_driver_template.o

# Kernel build directory
KDIR ?= /lib/modules/$(shell uname -r)/build

# Current directory
PWD := $(shell pwd)

# Default target: build the module
all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

# Clean build artifacts
clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# Install module
install: all
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a

# Uninstall module
uninstall:
	rm -f /lib/modules/$(shell uname -r)/extra/$(MODULE_NAME).ko
	depmod -a

# Load module
load:
	sudo insmod $(MODULE_NAME).ko

# Unload module
unload:
	sudo rmmod $(MODULE_NAME)

# Reload module (unload + load)
reload: unload load

# Show kernel log
dmesg:
	dmesg | tail -20

# Help
help:
	@echo "Available targets:"
	@echo "  all       - Build the kernel module (default)"
	@echo "  clean     - Remove build artifacts"
	@echo "  install   - Install module to system"
	@echo "  uninstall - Remove module from system"
	@echo "  load      - Load module into kernel"
	@echo "  unload    - Unload module from kernel"
	@echo "  reload    - Unload and reload module"
	@echo "  dmesg     - Show recent kernel messages"

.PHONY: all clean install uninstall load unload reload dmesg help
