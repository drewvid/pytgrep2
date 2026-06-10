
all:

install:
	(cd tgrep2-andreasvc-refactored; make install)
	(cd tgrep2-bwaldon-refactored; make install)

test:
	python3 tests/run_tests.py

update:
	make -f Makefile.git update

