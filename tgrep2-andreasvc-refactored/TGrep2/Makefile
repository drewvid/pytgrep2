# Edit this line to point to the directory containing the drutils.h file:
UTIL_DIR= ../DRUtils

UTIL_LIB= ${UTIL_DIR}/libdrutils.a
CC= gcc -O4 -Wall

.PHONY: clean install 

tgrep2: tgrep2.c Makefile
	${CC} -o ../$@ -I${UTIL_DIR} tgrep2.c ${UTIL_LIB} -lm

install: tgrep2
	cp ../tgrep2 ../../bin/tgrep2-andreasvc 

clean:
	rm -f *.o ../tgrep2

