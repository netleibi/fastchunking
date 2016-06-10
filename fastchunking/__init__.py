"""Fast and easy-to-use string chunking algorithms.

`fastchunking` provides two public classes meant to be used by end users.

* :class:`.SC`: Static chunking strategy.

* :class:`.RabinKarpCDC`: Rabin-Karp-based content-defined chunking strategy.

See below for details.
"""
import abc
import fastchunking._rabinkarprh as _rabinkarprh

__version__ = '0.0.1'


class BaseChunkingStrategy(object):

    """Abstract base class for chunking strategies."""
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.window_size = 1

    @abc.abstractmethod
    def create_chunker(self, chunk_size):
        """Abstract interface for chunker creation."""
        raise NotImplementedError

    def create_multilevel_chunker(self, chunk_sizes):
        """Create a multi-level chunker performing chunking with different
        chunk sizes.

        Args:
            chunk_sizes (list): List of target chunk sizes.

                Warning:
                    For performance reasons, behavior is only defined if chunk sizes
                    are passed in order, i.e., from lowest to highest value.

        Returns:
            BaseMultiLevelChunker: A multi-level chunker object.
        """
        return DefaultMultiLevelChunker(chunk_sizes, self.create_chunker)


class BaseChunker(object):

    """Abstract class specifying the interface of chunkers."""
    __metaclass__ = abc.ABCMeta

    def next_chunk_boundaries(self, buf, prepend_bytes=0):
        """Computes the next chunk boundaries within `buf`.

        Note:
            If called more than once, output depends on `all` previous calls of this
            function: The chunking algorithm is applied to the concatenation of all
            `buf` values.

        Args:
            buf (string): The message that is to be chunked.
            prepend_bytes (Optional[int]): Optional number of zero bytes that should be
                input to the chunking algorithm before `buf`.

        Returns:
            list: List of chunk boundary positions relative to `buf`.
        """
        raise NotImplementedError


class BaseMultiLevelChunker(BaseChunker):

    """Abstract class specifying the interface of multi-level chunkers."""
    __metaclass__ = abc.ABCMeta

    def next_chunk_boundaries(self, buf, prepend_bytes=0):
        """Computes the next chunk boundaries within `buf`.

        See :meth:`.BaseChunker.next_chunk_boundaries`.
        """
        return [boundary for (boundary, _) in
                self.next_chunk_boundaries_levels(buf, prepend_bytes)]

    def next_chunk_boundaries_levels(self, buf, prepend_bytes=0):
        """Computes the next chunk boundaries within `buf`.

        Similar to :meth:`.next_chunk_boundaries`, but information about which
        chunker led to a respective boundary is included in the returned value.

        Args:
            buf (string): The message that is to be chunked.
            prepend_bytes (Optional[int]): Optional number of zero bytes that
                should be input to the chunking algorithm before `buf`.

        Returns:
            list: List of tuples (boundary, level), where boundary is a boundary
            position relative to `buf` and level is the index of the chunker
            (i.e., the index of its chunk size specified during
            instantiation) that yielded the boundary.

            If multiple chunkers yield the same boundary, it is returned
            only once, along with the highest matching chunker index.
        """
        raise NotImplementedError


class DefaultMultiLevelChunker(BaseMultiLevelChunker):

    """Default multi-level chunker implementation, turning a standard chunker
    into a multi-level chunker.

    Multi-level chunkers perform chunking using multiple chunkers of type
    :class:`.BaseChunker` with different chunk sizes in parallel.
    """

    def __init__(self, chunk_sizes, chunker_create_fn):
        # create a chunker for each chunk size
        self._chunkers = [
            chunker_create_fn(chunk_size) for chunk_size in chunk_sizes]

    def next_chunk_boundaries_levels(self, buf, prepend_bytes=0):
        """Computes the next chunk boundaries within `buf`.

        Similar to :meth:`.next_chunk_boundaries`, but information about which
        chunker led to a respective boundary is included in the returned value.

        Args:
            buf (string): The message that is to be chunked.
            prepend_bytes (Optional[int]): Optional number of zero bytes that
                should be input to the chunking algorithm before `buf`.

        Returns:
            list: List of tuples (boundary, level), where boundary is a boundary
            position relative to `buf` and level is the index of the chunker
            (i.e., the index of its chunk size specified during
            instantiation) that yielded the boundary.

            If multiple chunkers yield the same boundary, it is returned
            only once, along with the highest matching chunker index.
        """
        boundaries = {}
        for level_index, chunker in enumerate(self._chunkers):
            boundaries.update(dict(
                [(boundary, level_index) for boundary in
                 chunker.next_chunk_boundaries(buf, prepend_bytes)]))
        return sorted(boundaries.items())


class SC(BaseChunkingStrategy):

    """Static chunking strategy.

    Generates fixed-size chunks.
    """

    def create_chunker(self, chunk_size):
        """Create a chunker performing static chunking (SC) with a specific
        chunk size.

        Args:
            chunk_size (int): Target chunk size.

        Returns:
            BaseChunker: A chunker object.
        """
        return SC._Chunker(chunk_size)

    class _Chunker(BaseChunker):

        """Static chunker instance."""

        def __init__(self, chunk_size):
            self._chunk_size = chunk_size
            self._next_chunk_boundary = self._chunk_size

        def next_chunk_boundaries(self, buf, prepend_bytes=0):
            # consider prepend_bytes
            self._next_chunk_boundary = (
                (self._next_chunk_boundary - prepend_bytes) % self._chunk_size)
            if self._next_chunk_boundary == 0:
                self._next_chunk_boundary = self._chunk_size

            # determine chunk boundaries
            buf_length = len(buf)
            chunk_boundaries = xrange(
                self._next_chunk_boundary, buf_length + 1, self._chunk_size)

            # update next chunk boundary position
            self._next_chunk_boundary = (
                self._next_chunk_boundary - buf_length) % self._chunk_size
            if self._next_chunk_boundary == 0:
                self._next_chunk_boundary = self._chunk_size

            return list(chunk_boundaries)


class RabinKarpCDC(BaseChunkingStrategy):

    """Content-defined chunking strategy based on Rabin Karp.

    Generates variable-size chunks.
    """

    def __init__(self, window_size, seed):
        super(RabinKarpCDC, self).__init__()
        self.window_size = window_size
        self._seed = seed

    def create_chunker(self, chunk_size):
        """Create a chunker performing content-defined chunking (CDC) using
        Rabin Karp's rolling hash scheme with a specific, expected chunk size.

        Args:
            chunk_size (int): (Expected) target chunk size.

        Returns:
            BaseChunker: A chunker object.
        """
        rolling_hash = _rabinkarprh.RabinKarpHash(self.window_size, self._seed)
        rolling_hash.set_threshold(1.0 / chunk_size)
        return RabinKarpCDC._Chunker(rolling_hash)

    def create_multilevel_chunker(self, chunk_sizes):
        """Create a multi-level chunker performing content-defined chunking
        (CDC) using Rabin Karp's rolling hash scheme with different specific,
        expected chunk sizes.

        Args:
            chunk_sizes (list): List of (expected) target chunk sizes.

                Warning:
                    For performance reasons, behavior is only defined if chunk sizes
                    are passed in order, i.e., from lowest to highest value.

        Returns:
            BaseMultiLevelChunker: A multi-level chunker object.
        """
        rolling_hash = _rabinkarprh.RabinKarpMultiThresholdHash(
            self.window_size, self._seed, [1.0 / chunk_size for chunk_size in chunk_sizes])
        return RabinKarpCDC._MultiLevelChunker(rolling_hash)

    class _Chunker(BaseChunker):

        def __init__(self, rolling_hash):
            self._rolling_hash = rolling_hash

        def next_chunk_boundaries(self, buf, prepend_bytes=0):
            return list(self._rolling_hash.next_chunk_boundaries(buf, prepend_bytes))

    class _MultiLevelChunker(BaseMultiLevelChunker):

        def __init__(self, rolling_hash):
            self._rolling_hash = rolling_hash

        def next_chunk_boundaries_levels(self, buf, prepend_bytes=0):
            i = iter(list(
                self._rolling_hash.next_chunk_boundaries_with_thresholds(buf, prepend_bytes)))
            return zip(i, i)
