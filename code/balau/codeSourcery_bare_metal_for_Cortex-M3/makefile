corm3 : main.c lm3s6965.ld reset.S syscalls.c
	arm-none-eabi-gcc -mthumb -march=armv7 -mfix-cortex-m3-ldrd -c main.c -o main.o
	arm-none-eabi-gcc -mthumb -march=armv7 -mfix-cortex-m3-ldrd -c reset.S -o reset.o
	arm-none-eabi-gcc -mthumb -march=armv7 -mfix-cortex-m3-ldrd -c syscalls.c -o syscalls.o
	arm-none-eabi-gcc -mthumb -march=armv7 -mfix-cortex-m3-ldrd -T lm3s6965.ld main.o reset.o syscalls.o -o main.elf
#	arm-none-eabi-gcc -mthumb -march=armv7 -mfix-cortex-m3-ldrd -T lm3s6965.ld main.c reset.S syscalls.c -o main.elf
	arm-none-eabi-objcopy -O binary main.elf main.bin
