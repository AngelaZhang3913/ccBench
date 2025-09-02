obj-m += bbr_test.o

# Disable objtool for older kernels
EXTRA_CFLAGS += -fno-stack-protector
ccflags-y := -Wno-unused-function

KDIR := /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) CONFIG_STACK_VALIDATION= modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
