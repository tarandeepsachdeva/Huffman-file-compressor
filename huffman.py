#!/usr/bin/env python3
"""
File Compression & Decompression Using Huffman Coding
Design & Analysis of Algorithms (DAA) Project

Huffman coding is a greedy algorithm that assigns variable-length prefix
codes to symbols based on their frequencies: more frequent symbols get
shorter codes. It minimizes expected code length among prefix codes,
i.e. it solves the optimal alphabetic-free prefix code problem.

Time complexity : O(n + k log k)   (n = input size, k = # distinct symbols)
Space complexity: O(k)
"""

import heapq
import sys
from collections import Counter
from pathlib import Path

MAGIC = b"HUFF"


# ---------------------------------------------------------------------------
# Huffman tree construction
# ---------------------------------------------------------------------------

class HuffmanNode:
    __slots__ = ("char", "freq", "left", "right", "code")

    def __init__(self, char, freq, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right
        self.code = ""

    def __lt__(self, other):
        # Tie-breaker keeps trees deterministic across runs
        return (self.freq, str(self.char)) < (other.freq, str(other.char))


def build_huffman_tree(freq: dict) -> HuffmanNode:
    """Greedy construction: repeatedly merge the two lowest-frequency nodes."""
    heap = [HuffmanNode(ch, f) for ch, f in freq.items()]
    heapq.heapify(heap)

    if len(heap) == 1:
        node = heapq.heappop(heap)
        node.code = "0"
        return node

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq, left, right)
        heapq.heappush(heap, merged)

    return heapq.heappop(heap)


def generate_codes(root: HuffmanNode, code: str = "", table: dict = None) -> dict:
    """Walk the tree once, appending 0/1, to produce the code table."""
    if table is None:
        table = {}
    if root.char is not None:
        table[root.char] = code
        return table
    generate_codes(root.left, code + "0", table)
    generate_codes(root.right, code + "1", table)
    return table


# ---------------------------------------------------------------------------
# Compression
# ---------------------------------------------------------------------------

def analyze(text: str) -> dict:
    """Frequency analysis of the input (part of the algorithm's output)."""
    counts = Counter(text)
    total = len(text)
    import math
    entropy_bits = -sum((c / total) * math.log2(c / total) for c in counts.values())
    return {
        "distinct_symbols": len(counts),
        "total_chars": total,
        "frequencies": dict(sorted(counts.items(), key=lambda x: -x[1])),
        "entropy_bits_per_char": entropy_bits,
    }


def compress_text(text: str) -> tuple:
    """Return (compressed_bits: str, code_table: dict)."""
    freq = Counter(text)
    if not freq:
        return "", {}

    root = build_huffman_tree(dict(freq))
    table = generate_codes(root)
    bitstring = "".join(table[ch] for ch in text)
    return bitstring, table


def bits_to_bytes(bitstring: str) -> bytes:
    """Pack a bitstring into bytes, padding the last byte with 0s."""
    pad = (-len(bitstring)) % 8
    bitstring += "0" * pad
    return int(bitstring, 2).to_bytes(len(bitstring) // 8, "big") if bitstring else b""


def bytes_to_bits(data: bytes) -> str:
    return "".join(f"{b:08b}" for b in data)


def serialize_table(table: dict) -> bytes:
    """Store the code table so the decompressor needs no side information."""
    import pickle
    return pickle.dumps(table)


def compress_bytes(raw: bytes) -> bytes:
    """Compress arbitrary bytes (used for binary files).
    Each byte value 0-255 is treated as a symbol."""
    freq = Counter(raw)
    root = build_huffman_tree(dict(freq))
    table = generate_codes(root)

    bitstring = "".join(table[b] for b in raw)

    packed = bits_to_bytes(bitstring)
    header = serialize_table(table)
    # magic(4) + header length(4) + table + padding-length(1) + payload
    pad_len = (-len(bitstring)) % 8
    return MAGIC + len(header).to_bytes(4, "big") + header + bytes([pad_len]) + packed


def decompress_bytes(data: bytes) -> bytes:
    if data[:4] != MAGIC:
        raise ValueError("Not a Huffman-compressed file (bad magic header). "
                         "Make sure you selected the .huff file, not the original.")
    header_len = int.from_bytes(data[4:8], "big")
    import pickle
    table = pickle.loads(data[8:8 + header_len])
    pad_len = data[8 + header_len]
    packed = data[9 + header_len:]

    # build reverse lookup: code -> byte value
    reverse = {v: k for k, v in table.items()}
    bits = bytes_to_bits(packed)
    if pad_len:
        bits = bits[:-pad_len]

    out = bytearray()
    code = ""
    for bit in bits:
        code += bit
        if code in reverse:
            out.append(reverse[code])
            code = ""
    return bytes(out)


def compress_file(input_path: str, output_path: str) -> dict:
    raw = Path(input_path).read_bytes()
    compressed = compress_bytes(raw)
    Path(output_path).write_bytes(compressed)
    return {
        "original_bytes": len(raw),
        "compressed_bytes": len(compressed),
        "ratio": len(compressed) / len(raw) if raw else 0.0,
        "saving_pct": (1 - len(compressed) / len(raw)) * 100 if raw else 0.0,
    }


def decompress_file(input_path: str, output_path: str) -> dict:
    data = Path(input_path).read_bytes()
    raw = decompress_bytes(data)
    Path(output_path).write_bytes(raw)
    return {"decompressed_bytes": len(raw)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    p = argparse.ArgumentParser(description="Huffman file compressor")
    p.add_argument("mode", choices=["compress", "decompress", "analyze"])
    p.add_argument("input")
    p.add_argument("output", nargs="?")
    args = p.parse_args()

    if args.mode == "analyze":
        text = Path(args.input).read_text(errors="replace")
        stats = analyze(text)
        stats["frequencies"] = dict(list(stats["frequencies"].items())[:20])
        print(stats)
        return

    if args.mode == "compress":
        stats = compress_file(args.input, args.output or args.input + ".huff")
        print(f"Compressed {stats['original_bytes']} -> {stats['compressed_bytes']} bytes "
              f"({stats['saving_pct']:.1f}% saved, ratio {stats['ratio']:.3f})")
    else:
        stats = decompress_file(args.input, args.output or args.input + ".out")
        print(f"Decompressed to {stats['decompressed_bytes']} bytes")


if __name__ == "__main__":
    main()
