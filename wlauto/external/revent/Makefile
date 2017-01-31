# CROSS_COMPILE=aarch64-linux-gnu- make
#
CC=gcc
LIBFLAGS= -lm

ifdef DEBUG
	CFLAGS=-static -lc -g
else
	CFLAGS=-static -lc -O2
endif

revent: revent.c
	$(CROSS_COMPILE)$(CC) $(CFLAGS) revent.c -o revent $(LIBFLAGS)

clean:
	rm -rf revent

.PHONY: clean
