.PHONY : all clean install drutils tgrep2

all: drutils tgrep2

drutils:
	$(MAKE) -C DRUtils

tgrep2:
	$(MAKE) -C src-tgrep2

clean:
	$(MAKE) -C DRUtils clean
	$(MAKE) -C src-tgrep2 clean

install:
	$(MAKE) -C src-tgrep2 install
