"""A small QR Code encoder (ISO/IEC 18004) using only the standard library.

It encodes text as bytes at error correction level M in versions 1 to 10 (up to 213 bytes), which is
enough for a repository URL, and renders the symbol as an inline SVG. site/build.py uses it so the
published slideshow carries a QR code that always matches the repository in site/site.toml, without
adding a dependency to the Pages build.
"""
from __future__ import annotations

# Level M, versions 1 to 10: error correction codewords per block and number of blocks (ISO/IEC 18004 table 9).
ECC_PER_BLOCK = (10, 16, 26, 18, 24, 16, 18, 22, 22, 26)
BLOCKS = (1, 1, 1, 2, 2, 4, 4, 4, 5, 5)
FORMAT_LEVEL_M = 0
PAD_BYTES = (0xEC, 0x11)
MASKS = (
    lambda x, y: (x + y) % 2 == 0,
    lambda x, y: y % 2 == 0,
    lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0,
    lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: x * y % 2 + x * y % 3 == 0,
    lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
)


def raw_codewords(version: int) -> int:
    """All codewords (data plus error correction) that fit in a symbol of this version."""
    modules = (16 * version + 128) * version + 64
    if version >= 2:
        count = version // 7 + 2
        modules -= (25 * count - 10) * count - 55
        if version >= 7:
            modules -= 36
    return modules // 8


def gf_multiply(x: int, y: int) -> int:
    """Multiply in GF(256) modulo x^8 + x^4 + x^3 + x^2 + 1."""
    product = 0
    for bit in range(7, -1, -1):
        product = (product << 1) ^ ((product >> 7) * 0x11D)
        product ^= ((y >> bit) & 1) * x
    return product


def rs_divisor(degree: int) -> list[int]:
    coefficients = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for i in range(degree):
            coefficients[i] = gf_multiply(coefficients[i], root)
            if i + 1 < degree:
                coefficients[i] ^= coefficients[i + 1]
        root = gf_multiply(root, 2)
    return coefficients


def rs_remainder(data: list[int], divisor: list[int]) -> list[int]:
    remainder = [0] * len(divisor)
    for byte in data:
        factor = byte ^ remainder.pop(0)
        remainder.append(0)
        for i, coefficient in enumerate(divisor):
            remainder[i] ^= gf_multiply(coefficient, factor)
    return remainder


def data_codewords(data: bytes, version: int) -> list[int]:
    capacity = raw_codewords(version) - ECC_PER_BLOCK[version - 1] * BLOCKS[version - 1]
    bits = "0100" + format(len(data), "08b" if version <= 9 else "016b")
    bits += "".join(format(byte, "08b") for byte in data)
    bits += "0" * min(4, capacity * 8 - len(bits))
    bits += "0" * (-len(bits) % 8)
    words = [int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)]
    while len(words) < capacity:
        words.append(PAD_BYTES[(len(words) - len(bits) // 8) % 2])
    return words


def interleave(words: list[int], version: int) -> list[int]:
    count, ecc_length = BLOCKS[version - 1], ECC_PER_BLOCK[version - 1]
    raw = raw_codewords(version)
    short_blocks, short_length = count - raw % count, raw // count
    divisor = rs_divisor(ecc_length)
    blocks, start = [], 0
    for i in range(count):
        length = short_length - ecc_length + (0 if i < short_blocks else 1)
        block = words[start:start + length]
        start += length
        ecc = rs_remainder(block, divisor)
        if i < short_blocks:
            block.append(0)  # keeps the blocks the same length; skipped when interleaving
        blocks.append(block + ecc)
    result = []
    for i in range(len(blocks[0])):
        for j, block in enumerate(blocks):
            if i != short_length - ecc_length or j >= short_blocks:
                result.append(block[i])
    return result


class Symbol:
    def __init__(self, version: int, codewords: list[int]):
        self.version, self.size = version, version * 4 + 17
        self.modules = [[False] * self.size for _ in range(self.size)]
        self.reserved = [[False] * self.size for _ in range(self.size)]
        self.draw_function_patterns()
        self.place(codewords)

    def put(self, x: int, y: int, dark: bool) -> None:
        self.modules[y][x] = dark
        self.reserved[y][x] = True

    def alignment_positions(self) -> list[int]:
        if self.version == 1:
            return []
        count = self.version // 7 + 2
        step = (self.version * 4 + count * 2 + 1) // (count * 2 - 2) * 2
        return [6] + [self.size - 7 - i * step for i in range(count - 2, -1, -1)]

    def draw_function_patterns(self) -> None:
        for i in range(self.size):
            self.put(6, i, i % 2 == 0)
            self.put(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (self.size - 4, 3), (3, self.size - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    if 0 <= cx + dx < self.size and 0 <= cy + dy < self.size:
                        self.put(cx + dx, cy + dy, max(abs(dx), abs(dy)) not in (2, 4))
        positions = self.alignment_positions()
        for i, cx in enumerate(positions):
            for j, cy in enumerate(positions):
                if (i, j) in ((0, 0), (0, len(positions) - 1), (len(positions) - 1, 0)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.put(cx + dx, cy + dy, max(abs(dx), abs(dy)) != 1)
        self.draw_format(0)
        if self.version >= 7:
            remainder = self.version
            for _ in range(12):
                remainder = (remainder << 1) ^ ((remainder >> 11) * 0x1F25)
            bits = self.version << 12 | remainder
            for i in range(18):
                a, b = self.size - 11 + i % 3, i // 3
                self.put(a, b, bool((bits >> i) & 1))
                self.put(b, a, bool((bits >> i) & 1))

    def draw_format(self, mask: int) -> None:
        data = FORMAT_LEVEL_M << 3 | mask
        remainder = data
        for _ in range(10):
            remainder = (remainder << 1) ^ ((remainder >> 9) * 0x537)
        bits = (data << 10 | remainder) ^ 0x5412
        bit = lambda i: bool((bits >> i) & 1)  # noqa: E731
        for i in range(6):
            self.put(8, i, bit(i))
        self.put(8, 7, bit(6))
        self.put(8, 8, bit(7))
        self.put(7, 8, bit(8))
        for i in range(9, 15):
            self.put(14 - i, 8, bit(i))
        for i in range(8):
            self.put(self.size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.put(8, self.size - 15 + i, bit(i))
        self.put(8, self.size - 8, True)

    def place(self, codewords: list[int]) -> None:
        index, right = 0, self.size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vertical in range(self.size):
                for offset in range(2):
                    x = right - offset
                    y = self.size - 1 - vertical if ((right + 1) & 2) == 0 else vertical
                    if not self.reserved[y][x] and index < len(codewords) * 8:
                        self.modules[y][x] = bool((codewords[index >> 3] >> (7 - (index & 7))) & 1)
                        index += 1
            right -= 2

    def apply_mask(self, mask: int) -> None:
        rule = MASKS[mask]
        for y in range(self.size):
            for x in range(self.size):
                if not self.reserved[y][x] and rule(x, y):
                    self.modules[y][x] = not self.modules[y][x]

    def penalty(self) -> int:
        lines = ["".join("1" if dark else "0" for dark in row) for row in self.modules]
        lines += ["".join(lines[y][x] for y in range(self.size)) for x in range(self.size)]
        score = 0
        for line in lines:
            run = 1
            for i in range(1, self.size + 1):
                if i < self.size and line[i] == line[i - 1]:
                    run += 1
                    continue
                score += run - 2 if run >= 5 else 0
                run = 1
            for pattern in ("10111010000", "00001011101"):
                score += 40 * sum(line.startswith(pattern, i) for i in range(self.size - 10))
        for y in range(self.size - 1):
            for x in range(self.size - 1):
                if self.modules[y][x] == self.modules[y][x + 1] == self.modules[y + 1][x] == self.modules[y + 1][x + 1]:
                    score += 3
        dark = sum(row.count(True) for row in self.modules)
        total = self.size * self.size
        return score + 10 * (-(-abs(dark * 20 - total * 10) // total) - 1)


def encode(text: str) -> list[list[bool]]:
    """The QR Code for text as rows of modules (True is dark), without the quiet zone."""
    data = text.encode("utf-8")
    for version in range(1, 11):
        capacity = raw_codewords(version) - ECC_PER_BLOCK[version - 1] * BLOCKS[version - 1]
        if 4 + (8 if version <= 9 else 16) + 8 * len(data) <= capacity * 8:
            break
    else:
        raise ValueError(f"{len(data)} bytes do not fit a version 10 QR Code at level M")
    symbol = Symbol(version, interleave(data_codewords(data, version), version))
    best, lowest = 0, None
    for mask in range(8):
        symbol.apply_mask(mask)
        symbol.draw_format(mask)
        score = symbol.penalty()
        symbol.apply_mask(mask)
        if lowest is None or score < lowest:
            best, lowest = mask, score
    symbol.apply_mask(best)
    symbol.draw_format(best)
    return symbol.modules


def to_svg(modules: list[list[bool]], css_class: str = "qr-code", border: int = 4) -> str:
    """The symbol as an inline SVG: black modules on white, inside the four-module quiet zone the standard requires."""
    size = len(modules)
    runs = []
    for y, row in enumerate(modules):
        x = 0
        while x < size:
            if not row[x]:
                x += 1
                continue
            start = x
            while x < size and row[x]:
                x += 1
            runs.append(f"M{start + border} {y + border}h{x - start}v1h-{x - start}z")
    side = size + 2 * border
    return (f'<svg class="{css_class}" viewBox="0 0 {side} {side}" shape-rendering="crispEdges" '
            f'aria-hidden="true" focusable="false"><rect width="{side}" height="{side}" fill="#fff"/>'
            f'<path d="{"".join(runs)}" fill="#000"/></svg>')
