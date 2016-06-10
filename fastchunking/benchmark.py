import timeit
import os
import time

import fastchunking

if __name__ == '__main__':
    print "Benchmarking RabinKarpChunking creation time..."
    NUMBER = 10000
    total_time = timeit.timeit(
        "fastchunking.RabinKarpCDC(48, 0).create_chunker(128)",
        setup="import fastchunking",
        number=NUMBER)
    print "average creation time: {:f}s\n".format(total_time / NUMBER)

    print "Benchmarking RabinKarpChunking chunking throughput..."
    SIZE = 100 * 1024 * 1024  # 100 MiB
    for chunksize in [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]:
        chunker = fastchunking.RabinKarpCDC(
            48, 0).create_chunker(chunksize)
        content = os.urandom(SIZE)
        t = time.time()
        chunker.next_chunk_boundaries(content, 0)
        print "chunking throughput (chunksize = {} bytes): {} MiB/s".format(
            chunksize, SIZE / 1024 / 1024 / (time.time() - t))
