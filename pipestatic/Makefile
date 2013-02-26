CC=gcc
DEPS = stats.h

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

test_stats: stats.o test_stats.o
	gcc -o test_stats stats.o test_stats.o -I. -lpthread

clean:
	rm -f *.o test_stats
