all:
	cd Toooba-mibench2; sh buildAll.sh; mv *.bin ../
	cd Toooba-olden; sh buildAll.sh; mv *.bin ../
	cd cva6-olden; PORT_DIR=cva6-metal make compile; mv coremark ../coremark.bin
