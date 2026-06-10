Note: I've only tried building this using the gcc C compiler on my ~2019 MacBook.

To compile locally (from the root directory):

```
gcc tgrep2.c drutils.c hash.c svd.c -o tgrep2
```

To run: 

```
./tgrep2
```

Verify it's working:

```
./tgrep2 -c corpus.t2c "TOP"
```

