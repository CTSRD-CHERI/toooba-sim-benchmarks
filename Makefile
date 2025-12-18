all:
	cd Toooba-mibench2; sh buildAll.sh; mv *.bin ../; cd ../
	cd Toooba-olden; sh buildAll.sh; mv *.bin ../; cd ../
