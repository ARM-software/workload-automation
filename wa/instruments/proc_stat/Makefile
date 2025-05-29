# CROSS_COMPILE=aarch64-linux-gnu- make
#
CC=gcc

ifdef DEBUG
	CFLAGS=-static -lc -g
else
	CFLAGS=-static -lc -O2
endif

cpu_poller: cpu_poller.c
	$(CROSS_COMPILE)$(CC) $(CFLAGS) proc_stat_poller.c -o proc_stat_poller

release:
	mkdir -p bin/arm64
	aarch64-linux-gnu-$(CC) $(CFLAGS) proc_stat_poller.c -o bin/arm64/proc_stat_poller
	mkdir -p bin/armeabi
	arm-linux-gnueabi-$(CC) $(CFLAGS) proc_stat_poller.c -o bin/armeabi/proc_stat_poller

clean:
	rm -rf proc_stat_poller bin/*

.PHONY: clean