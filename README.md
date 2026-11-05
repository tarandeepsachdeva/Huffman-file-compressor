# File Compression & Decompression Using Huffman Coding

A Design & Analysis of Algorithms (DAA) project implementing lossless
file compression with Huffman codes in Python.

## Files

| File | Purpose |
|------|---------|
| `huffman.py` | Core algorithm + CLI (`compress`, `decompress`, `analyze`) |
| `demo.py` | Frequency analysis, code table, compression stats, round-trip check |

## Usage

```bash
python3 demo.py                                  # run the demo
python3 huffman.py analyze input.txt             # frequency/entropy stats
python3 huffman.py compress input.txt out.huff   # compress a file
python3 huffman.py decompress out.huff out.txt   # decompress back
```

## Algorithm

1. **Frequency analysis** — count occurrences of every symbol (byte value
   0–255 for files, characters for text).
2. **Tree construction (greedy)** — build a min-heap of leaf nodes keyed by
   frequency. Repeatedly extract the two lowest-frequency nodes, merge them
   into a new node whose frequency is their sum, and reinsert. Stop when one
   node remains — that is the Huffman tree. Cost: `O(k log k)` for `k`
   distinct symbols.
3. **Code assignment** — traverse the tree once (`O(k)`); left edge = `0`,
   right edge = `1`. Each leaf's path from the root is its prefix code.
   Property: no code is a prefix of another, so decoding is unambiguous.
4. **Encoding** — replace each symbol by its code and pack the bitstring
   into bytes. Cost: `O(n)` for input length `n`.
5. **Decoding** — rebuild a reverse map `code -> symbol` and scan the
   bitstream, accumulating bits until a code matches. Cost: `O(n')` where
   `n'` is the compressed length.

Overall time complexity: `O(n + k log k)`; space: `O(k)`.

## Why it is optimal

Huffman coding produces the minimum expected code length
`L = Σ pᵢ·len(cᵢ)` among all prefix codes. Intuition: if two symbols `a`,
`b` are the two least frequent and `len(a) < len(b)`, swapping their codes
strictly reduces `L` — so in an optimal code the two least frequent
symbols must sit at the same (maximum) depth, which is exactly what the
merge step guarantees inductively. This is the standard exchange argument.

## Analysis / observations

- Compression is best when the symbol distribution is **skewed**. On
  uniform data Huffman codes approach `log₂(k)` bits/symbol — no better
  than fixed-length coding, plus header overhead.
- The compressed file stores the code table (pickle) + padding length, so
  decompression needs no external side information.
- Huffman is optimal *per-symbol* but cannot exploit multi-symbol context;
  that is the motivation for arithmetic coding / LZ77+Huffman (DEFLATE).
- Real-world compressors (gzip, zlib) use Huffman coding on LZ77 output.

## Limitations

- Header overhead makes tiny files larger after compression.
- No adaptation: the table is built once per file.
- Python bit-by-bit encoding is slow for very large files.
