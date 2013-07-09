PROJ_NAME=hello-world

PLATFORM=stm32f0

ARMBIN=/usr/local/arm-bin/
PATH:=	$(PATH):$(ARMBIN)
VPATH = .:stm32f0
CC=arm-none-eabi-gcc
LD=arm-none-eabi-ld
LDSCRIPT_INC=ldscripts
LINKERFILE=stm32f0.ld

CRT0=startup_$(PLATFORM)xx.o

CFLAGS += -g -std=c99 -Os # -Wall -Werror -Wextra
CFLAGS += -mlittle-endian -mcpu=cortex-m0  -march=armv6-m -mthumb
CFLAGS += -ffunction-sections -fdata-sections
CFLAGS += -Wl,--gc-sections -Wl,-Map=$(PROJ_NAME).map
CFLAGS += -nodefaultlibs
CFLAGS += -I$(PLATFORM)

all:	hello-world.hex hello-world.bin

OBJS=	hello-world.o uart.o
OBJS+=	system_stm32f0xx.o

system_stm32f0xx.o:	system_stm32f0xx.c

hello-world.elf:	$(CRT0) $(OBJS)
	$(CC) $(CFLAGS) -L $(LDSCRIPT_INC) -T $(LINKERFILE) -o hello-world.elf $(CRT0) $(OBJS)

hello-world.hex:	hello-world.elf
	arm-none-eabi-objcopy -O ihex hello-world.elf hello-world.hex

hello-world.bin:	hello-world.elf
	arm-none-eabi-objcopy -O binary hello-world.elf hello-world.bin

$(CRT0): stm32f0/startup_$(PLATFORM)xx.s
	$(CC) $(CFLAGS) -c stm32f0/startup_$(PLATFORM)xx.s

.S.o:
	$(CC) $(ASFLAGS) -c $?

.s.o:
	$(CC) $(ASFLAGS) -c $?

.c.o:
	$(CC) $(CFLAGS) -c $?

.c.s:
	$(CC) $(CFLAGS) -S $?

clean:
	rm -f *.o *.elf *.bin *.hex *.map
