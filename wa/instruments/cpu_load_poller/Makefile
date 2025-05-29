# CROSS_COMPILE=aarch64-linux-gnu- make
#
CC=gcc

ifdef DEBUG
	CFLAGS=-static -lc -g
else
	CFLAGS=-static -lc -O2
endif

cpu_poller: cpu_poller.c
	$(CROSS_COMPILE)$(CC) $(CFLAGS) cpu_load_poller.c -o cpu_load_poller

release:
	mkdir -p bin/arm64
	aarch64-linux-gnu-$(CC) $(CFLAGS) cpu_load_poller.c -o bin/arm64/cpu_load_poller
	mkdir -p bin/armeabi
	arm-linux-gnueabi-$(CC) $(CFLAGS) cpu_load_poller.c -o bin/armeabi/cpu_load_poller

clean:
	rm -rf cpu_load_poller bin/*

.PHONY: clean