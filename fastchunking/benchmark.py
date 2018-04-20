import os
import time
import timeit

import fastchunking

if __name__ == '__main__':
    print("Benchmarking RabinKarpChunking creation time...")
    NUMBER = 10000
    total_time = timeit.timeit('fastchunking.RabinKarpCDC(48, 0).create_chunker(128)',
                               setup='import fastchunking', number=NUMBER)
    print("average creation time: {:f}s\n".format(total_time / NUMBER))

    print("Benchmarking RabinKarpChunking chunking throughput...")
    SIZE = 100 * 1024 * 1024  # 100 MiB
    for chunk_size in (2 ** i for i in range(6, 16)):
        chunker = fastchunking.RabinKarpCDC(48, 0).create_chunker(chunk_size)
        content = os.urandom(SIZE)
        t = time.time()
        list(chunker.next_chunk_boundaries(content, 0))

        msg = "chunking throughput (chunk size = {chunk_size:5d} bytes): {throughput:7.2f} MiB/s"
        t = time.time() - t
        print(msg.format(chunk_size=chunk_size, throughput=SIZE / 1024 / 1024 / t if t else float('inf')))
