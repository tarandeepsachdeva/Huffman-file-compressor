#!/usr/bin/env python3
"""Demo: frequency analysis, Huffman encoding, compression stats, round-trip."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from huffman import analyze, compress_text, decompress_bytes, compress_bytes

SAMPLE = """Huffman coding is a greedy algorithm for constructing optimal
prefix codes. It assigns shorter binary codes to more frequent symbols
and longer codes to rarer ones, minimizing the expected code length.
This demo shows the frequency analysis, code table, encoded bitstring,
and verifies lossless round-trip compression."""


def decode_text(bitstring: str, table: dict) -> str:
    reverse = {v: k for k, v in table.items()}
    out, code = [], ""
    for bit in bitstring:
        code += bit
        if code in reverse:
            out.append(reverse[code])
            code = ""
    return "".join(out)


def main():
    # 1. Frequency analysis
    stats = analyze(SAMPLE)
    print("=== Frequency analysis ===")
    print(f"distinct symbols : {stats['distinct_symbols']}")
    print(f"total chars      : {stats['total_chars']}")
    print(f"entropy          : {stats['entropy_bits_per_char']:.3f} bits/char")
    print("top frequencies  :", list(stats["frequencies"].items())[:8])

    # 2. Build codes
    bitstring, table = compress_text(SAMPLE)
    print("\n=== Huffman code table ===")
    for ch, code in sorted(table.items(), key=lambda x: (len(x[1]), x[1])):
        print(f"  {repr(ch):8} -> {code}")

    # 3. Compression statistics
    orig_bits = stats["total_chars"] * 8
    huff_bits = len(bitstring)
    print("\n=== Compression stats ===")
    print(f"fixed-length    : {orig_bits} bits")
    print(f"Huffman         : {huff_bits} bits")
    print(f"bits/char       : {huff_bits / stats['total_chars']:.3f}")
    print(f"saving          : {(1 - huff_bits / orig_bits) * 100:.1f}%")

    # 4. Round-trip check
    assert decode_text(bitstring, table) == SAMPLE
    packed = compress_bytes(SAMPLE.encode())
    assert decompress_bytes(packed) == SAMPLE.encode()
    print("\nRound-trip verified: decoded output == original.")


if __name__ == "__main__":
    main()
