#!/bin/bash

qemu-system-arm -M lm3s6965evb --kernel main.bin --serial stdio
