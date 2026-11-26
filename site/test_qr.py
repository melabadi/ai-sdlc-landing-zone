"""QR encoder checks: python -m unittest discover -s site -p "test_*.py".

The expected symbol was produced by an independent implementation (the python-qrcode package) and decoded
back to the text with OpenCV when the encoder was written; the multi-block versions were compared with
python-qrcode module by module.
"""
import unittest

import qr

URL = "https://github.com/melabadi/ai-sdlc-landing-zone"
# Version 4, level M, mask picked by the penalty rules. '#' is a dark module.
EXPECTED = (
    "#######..#..##..#####..#..#######",
    "#.....#...##.#####..#.....#.....#",
    "#.###.#.##...#.#.##.##....#.###.#",
    "#.###.#.###.#.###...#.#...#.###.#",
    "#.###.#.##..##.#.##..#.#..#.###.#",
    "#.....#.##..#..##...#.....#.....#",
    "#######.#.#.#.#.#.#.#.#.#.#######",
    "........#####.##..#..#...........",
    "#.#####...#.##.#.#.....#..#####..",
    "##.###..#.#.....#.###..#..##.##.#",
    "#.....#.####...##.#.#.#.###.#.##.",
    "##.....#.#....#.#...###.#.#.###..",
    "..######.#..#.....##..####.###.#.",
    "#.#....###..#.###...#..##.#..#.##",
    "#...#.###.#.###...##..#..##...##.",
    "##.###.#....#.#.#..###.#.###.##..",
    ".##.###.###......#.#..#.##.##...#",
    "..##.#.##..#.....####..#..##.##.#",
    "##..#.##.##..#####..#.#.##.##.##.",
    "#..###.###....##.#####.....######",
    ".###..######..#.#..##.#.##.###...",
    "#.####.#..##.#.#..#..#.#..#...#.#",
    "#.#.#.#.###...#####.#...##.#.#.#.",
    "#.#.##..#####..#..#..###.##.#.#..",
    "#..##.#.#.##.#.#.#....#######....",
    "........#.##.##.#.##.#.##...#.###",
    "#######...#...##..#.#####.#.#.##.",
    "#.....#.#.##.####...#####...####.",
    "#.###.#.####.###..##.#..######.##",
    "#.###.#.##..#..##...#..###..##.##",
    "#.###.#.###..#....##..#...##.##..",
    "#.....#..#.#..#.#..####...#.###..",
    "#######.#....#...#.#..####.#...#.",
)


class QrTests(unittest.TestCase):
    def test_repository_url_symbol_is_unchanged(self):
        rows = tuple("".join("#" if dark else "." for dark in row) for row in qr.encode(URL))
        self.assertEqual(EXPECTED, rows)

    def test_versions_with_several_blocks_and_version_info_stay_square_and_scale_up(self):
        for length, version in ((14, 1), (48, 4), (122, 7), (203, 10)):
            with self.subTest(length=length):
                modules = qr.encode("a" * length)
                self.assertEqual(version * 4 + 17, len(modules))
                self.assertTrue(all(len(row) == len(modules) for row in modules))

    def test_text_that_does_not_fit_is_refused(self):
        with self.assertRaises(ValueError):
            qr.encode("a" * 214)

    def test_svg_keeps_the_quiet_zone(self):
        svg = qr.to_svg(qr.encode(URL))
        self.assertIn('viewBox="0 0 41 41"', svg)
        self.assertIn('M4 4h7', svg)  # the first row of the top-left finder pattern, four modules in


if __name__ == "__main__":
    unittest.main()
