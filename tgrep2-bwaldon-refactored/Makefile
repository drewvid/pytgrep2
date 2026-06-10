
all:

tgrep2:
	gcc tgrep2.c drutils.c hash.c svd.c -o tgrep2 -lm

test:
	./tgrep2 -i "NP << mindfulness"	

install: tgrep2
	cp tgrep2 ../bin/tgrep2-bwaldon

clean:
	rm -f *.o tgrep2
