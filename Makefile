
all:

install:
	mkdir -p bin
	(cd tgrep2-andreasvc-refactored; make; make install)
	(cd tgrep2-bwaldon-refactored; make; make install)

test:
	python3 tests/run_tests.py
