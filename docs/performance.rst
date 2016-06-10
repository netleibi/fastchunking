===========
Performance
===========

Computation costs for `static chunking` are barely measurable: As chunking does
not depend on the actual message but only its length, computation costs are
essentially limited to a single :code:`xrange` call.

`Content-defined chunking`, however, is expensive: The algorithm has to compute
hash values for rolling hash window contents at `every` byte position of the
message that is to be chunked. To minimize costs, fastchunking works as follows:
    
    1. The message (fragment) is passed in its entirety to the C++ extension.
    2. Chunking is performed within the C++ extension.
    3. The resulting list of chunk boundaries is communicated back to Python and
       converted into a Python list.

Based on a 100 MiB random content, the author measured the following throughput
on an Intel Core i7-4600U in a single, non-representative test run:

    =========== ==========
    chunk size  throughput
    =========== ==========
    64 bytes    49 MiB/s
    128 bytes   57 MiB/s
    256 bytes   62 MiB/s
    512 bytes   63 MiB/s
    1024 bytes  67 MiB/s
    2048 bytes  68 MiB/s
    4096 bytes  70 MiB/s
    8192 bytes  71 MiB/s
    16384 bytes 71 MiB/s
    32768 bytes 71 MiB/s
    =========== ==========
