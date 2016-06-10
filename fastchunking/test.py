import os
import sys
import unittest

sys.path.insert(0, os.path.abspath('..'))
import fastchunking


class StaticChunkingTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(StaticChunkingTests, self).__init__(*args, **kwargs)
        self.chunking_strategy = fastchunking.SC()

    def test_chunk_size_1(self):
        chunker = self.chunking_strategy.create_chunker(chunk_size=1)
        self.assertEqual(
            list(chunker.next_chunk_boundaries('0' * 3)), [1, 2, 3])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 1)), [1])

    def test_chunk_size_2(self):
        chunker = self.chunking_strategy.create_chunker(chunk_size=2)
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 4)), [2, 4])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 1)), [])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 1)), [1])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 3)), [2])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 3)), [1, 3])

    def test_chunk_size_3(self):
        chunker = self.chunking_strategy.create_chunker(chunk_size=3)
        self.assertEqual(
            list(chunker.next_chunk_boundaries('0' * 9)), [3, 6, 9])
        self.assertEqual(
            list(chunker.next_chunk_boundaries('0' * 10)), [3, 6, 9])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 2)), [2])
        self.assertEqual(
            list(chunker.next_chunk_boundaries('0' * 11)), [3, 6, 9])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 1)), [1])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 0)), [])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 0)), [])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 0)), [])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 3)), [3])

    def test_chunk_size_4(self):
        chunker = self.chunking_strategy.create_chunker(chunk_size=4)
        self.assertEqual(
            list(chunker.next_chunk_boundaries('0' * 12)), [4, 8, 12])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 2)), [])
        self.assertEqual(
            list(chunker.next_chunk_boundaries('0' * 12)), [2, 6, 10])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 1)), [])
        self.assertEqual(
            list(chunker.next_chunk_boundaries('0' * 12)), [1, 5, 9])
        self.assertEqual(list(chunker.next_chunk_boundaries('0' * 1)), [1])

    def test_multilevel(self):
        chunker = self.chunking_strategy.create_multilevel_chunker(
            [5, 10])
        self.assertEqual(list(chunker.next_chunk_boundaries_levels(
            '0' * 20)), [(5, 0), (10, 1), (15, 0), (20, 1)])
        self.assertEqual(list(chunker.next_chunk_boundaries_levels(
            '0' * 21)), [(5, 0), (10, 1), (15, 0), (20, 1)])
        self.assertEqual(list(chunker.next_chunk_boundaries_levels(
            '0' * 22)), [(4, 0), (9, 1), (14, 0), (19, 1)])
        self.assertEqual(list(chunker.next_chunk_boundaries_levels(
            '0' * 22)), [(2, 0), (7, 1), (12, 0), (17, 1), (22, 0)])

    def test_multilevel_without_levels(self):
        chunker = self.chunking_strategy.create_multilevel_chunker(
            [5, 10])
        self.assertEqual(list(chunker.next_chunk_boundaries(
            '0' * 20)), [5, 10, 15, 20])
        self.assertEqual(list(chunker.next_chunk_boundaries(
            '0' * 21)), [5, 10, 15, 20])
        self.assertEqual(list(chunker.next_chunk_boundaries(
            '0' * 22)), [4, 9, 14, 19])
        self.assertEqual(list(chunker.next_chunk_boundaries(
            '0' * 22)), [2, 7, 12, 17, 22])

    def test_prepending(self):
        for _ in range(1024):
            content = os.urandom(1024)

            chunker = self.chunking_strategy.create_chunker(
                chunk_size=64)
            boundaries = chunker.next_chunk_boundaries('\0' + content)

            prepend_chunker = self.chunking_strategy.create_chunker(
                chunk_size=64)
            prepend_boundaries = prepend_chunker.next_chunk_boundaries(
                content, 1)

            self.assertEqual(
                boundaries, map(lambda x: x + 1, prepend_boundaries))


class RabinKarpTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(RabinKarpTests, self).__init__(*args, **kwargs)
        self.chunking_strategy = fastchunking.RabinKarpCDC(48, 0)

    def test_deterministic_chunking(self):
        content = os.urandom(1024 * 1024)

        chunker = self.chunking_strategy.create_chunker(chunk_size=128)
        boundaries = chunker.next_chunk_boundaries(content)

        chunker2 = self.chunking_strategy.create_chunker(chunk_size=128)
        boundaries2 = chunker2.next_chunk_boundaries(content)

        self.assertEqual(boundaries, boundaries2)

    def test_consistent_chunking(self):
        chunker = self.chunking_strategy.create_chunker(chunk_size=128)

        part_len = 10 * 1024
        content = os.urandom(part_len)
        boundaries = chunker.next_chunk_boundaries(content + content)

        for boundary in boundaries:
            if boundary < part_len:
                self.assertIn(boundary + part_len, boundaries)

    def test_prepending(self):
        for _ in range(1024):
            content = os.urandom(1024)

            chunker = self.chunking_strategy.create_chunker(
                chunk_size=64)
            boundaries = chunker.next_chunk_boundaries('\0' + content)

            prepend_chunker = self.chunking_strategy.create_chunker(
                chunk_size=64)
            prepend_boundaries = prepend_chunker.next_chunk_boundaries(
                content, 1)

            self.assertEqual(
                boundaries, map(lambda x: x + 1, prepend_boundaries))

    def test_sample_data_1(self):
        content = 'Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.'

        chunker = self.chunking_strategy.create_chunker(chunk_size=128)
        boundaries = chunker.next_chunk_boundaries(content)

        self.assertEqual(boundaries, [91, 121, 387, 417])

    def test_sample_data_2(self):
        content = 'Lorem ipsum dolor sit amet, dictas definitiones ea nam, per at fugit voluptaria. Brute luptatum recusabo ne per, mei modo consul indoctum ex. Quem accusamus an sea. Graece oportere dignissim eos et, an diam voluptatibus est. Dictas aperiam est at, nibh tritani has ex, his decore aliquid ut. Ius ei iusto ludus clita, ea per inermis probatus forensibus. Eum ex ludus nullam persequeris, mel gubergren reprehendunt ad, ne mel regione disputationi. Aliquando forensibus sit ne, sea et graece causae fabulas. Vel eu pericula intellegat rationibus, in qui exerci adversarium. Ea nec feugiat placerat, eos dicat invidunt maluisset ea. Graece convenire.'

        chunker = self.chunking_strategy.create_chunker(chunk_size=16)
        boundaries = chunker.next_chunk_boundaries(content)

        self.assertEqual(boundaries, [56, 98, 119, 182, 198, 204, 214, 245, 270, 282, 287, 312, 313, 315, 317, 328, 331,
                                      345, 367, 377, 397, 410, 417, 418, 437, 443, 459, 466, 474, 475, 492, 497, 501, 522, 532, 545, 577, 597, 598, 606])

    def test_multilevel(self):
        content = 'Lorem ipsum dolor sit amet, dictas definitiones ea nam, per at fugit voluptaria. Brute luptatum recusabo ne per, mei modo consul indoctum ex. Quem accusamus an sea. Graece oportere dignissim eos et, an diam voluptatibus est. Dictas aperiam est at, nibh tritani has ex, his decore aliquid ut. Ius ei iusto ludus clita, ea per inermis probatus forensibus. Eum ex ludus nullam persequeris, mel gubergren reprehendunt ad, ne mel regione disputationi. Aliquando forensibus sit ne, sea et graece causae fabulas. Vel eu pericula intellegat rationibus, in qui exerci adversarium. Ea nec feugiat placerat, eos dicat invidunt maluisset ea. Graece convenire.'

        chunker = self.chunking_strategy.create_multilevel_chunker(
            [16, 32, 64])
        boundaries_with_levels = chunker.next_chunk_boundaries_levels(
            content)

        self.assertEqual(boundaries_with_levels, [(56L, 0L), (98L, 1L), (106L, 0L), (136L, 0L), (182L, 1L), (196L, 0L), (198L, 2L), (204L, 1L), (206L, 0L), (213L, 0L), (227L, 0L), (245L, 2L), (270L, 1L), (282L, 0L), (287L, 0L), (312L, 1L), (313L, 1L), (315L, 1L), (317L, 0L), (328L, 0L), (
            331L, 0L), (345L, 0L), (367L, 0L), (377L, 2L), (383L, 1L), (391L, 0L), (408L, 0L), (410L, 2L), (437L, 0L), (443L, 0L), (459L, 1L), (463L, 0L), (466L, 2L), (474L, 1L), (492L, 2L), (497L, 2L), (501L, 1L), (522L, 2L), (532L, 1L), (545L, 1L), (577L, 0L), (597L, 0L), (598L, 2L), (606L, 0L)])


class AbstractTests(unittest.TestCase):

    def test_chunking_strategy(self):
        class Test(fastchunking.BaseChunkingStrategy):

            def create_chunker(self, *args, **kwargs):
                return super(Test, self).create_chunker(*args, **kwargs)

        self.assertRaises(NotImplementedError, Test().create_chunker, 4096)
        self.assertRaises(
            NotImplementedError, Test().create_multilevel_chunker, [4096])

    def test_chunker(self):
        class Test(fastchunking.BaseChunker):

            def next_chunk_boundaries(self, *args, **kwargs):
                return super(Test, self).next_chunk_boundaries(*args, **kwargs)

        self.assertRaises(
            NotImplementedError, Test().next_chunk_boundaries, '0')

if __name__ == "__main__":
    unittest.main()
