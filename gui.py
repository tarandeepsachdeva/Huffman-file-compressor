#!/usr/bin/env python3
"""Tkinter GUI for Huffman file compression / decompression."""
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from huffman import analyze, compress_file, decompress_file


class HuffmanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Huffman File Compressor")
        self.geometry("640x480")
        self.minsize(520, 400)

        self._build_widgets()

    # ---------------- UI ----------------
    def _build_widgets(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Input file:").grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.input_var).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(top, text="Browse…", command=self.pick_input).grid(row=0, column=2)

        ttk.Label(top, text="Output file:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.output_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.output_var).grid(row=1, column=1, sticky="we", padx=6, pady=(8, 0))
        ttk.Button(top, text="Browse…", command=self.pick_output).grid(row=1, column=2, pady=(8, 0))

        top.columnconfigure(1, weight=1)

        btns = ttk.Frame(self, padding=(10, 4))
        btns.pack(fill="x")
        ttk.Button(btns, text="Analyze", command=lambda: self.run("analyze")).pack(side="left", padx=4)
        ttk.Button(btns, text="Compress", command=lambda: self.run("compress")).pack(side="left", padx=4)
        ttk.Button(btns, text="Decompress", command=lambda: self.run("decompress")).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear log", command=self.clear_log).pack(side="right", padx=4)

        self.log = tk.Text(self, wrap="word", state="disabled", font=("Menlo", 11))
        scroll = ttk.Scrollbar(self, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ---------------- helpers ----------------
    def pick_input(self):
        path = filedialog.askopenfilename()
        if path:
            self.input_var.set(path)
            if not self.output_var.get():
                self.output_var.set(path + ".huff")

    def pick_output(self):
        path = filedialog.asksaveasfilename()
        if path:
            self.output_var.set(path)

    def log_msg(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _validate(self):
        src, dst = self.input_var.get().strip(), self.output_var.get().strip()
        if not src or not Path(src).is_file():
            messagebox.showerror("Error", "Please choose a valid input file.")
            return None
        if not dst:
            messagebox.showerror("Error", "Please choose an output file.")
            return None
        return src, dst

    # ---------------- actions ----------------
    def run(self, mode):
        paths = self._validate()
        if not paths:
            return
        src, dst = paths
        threading.Thread(target=self._worker, args=(mode, src, dst), daemon=True).start()

    def _worker(self, mode, src, dst):
        try:
            if mode == "analyze":
                try:
                    text = Path(src).read_text(errors="replace")
                    stats = analyze(text)
                    self._log(f"--- Analysis of {src} ---")
                    self._log(f"distinct symbols : {stats['distinct_symbols']}")
                    self._log(f"total chars      : {stats['total_chars']}")
                    self._log(f"entropy          : {stats['entropy_bits_per_char']:.3f} bits/char")
                    self._log("top frequencies  : " + str(list(stats["frequencies"].items())[:15]))
                except UnicodeDecodeError:
                    self._log("Binary file — showing byte-value histogram instead:")
                    data = Path(src).read_bytes()
                    from collections import Counter
                    top = Counter(data).most_common(15)
                    self._log(f"size             : {len(data)} bytes")
                    self._log(f"distinct bytes   : {len(set(data))}")
                    self._log("top bytes        : " + str(top))

            elif mode == "compress":
                s = compress_file(src, dst)
                self._log(f"Compressed {src}")
                self._log(f"  {s['original_bytes']} -> {s['compressed_bytes']} bytes")
                self._log(f"  saved {s['saving_pct']:.1f}%  (ratio {s['ratio']:.3f})")
                self._log(f"  output: {dst}")

            else:
                s = decompress_file(src, dst)
                self._log(f"Decompressed {src}")
                self._log(f"  {s['decompressed_bytes']} bytes")
                self._log(f"  output: {dst}")

            self._log("Done.")
        except Exception as e:
            msg = str(e)
            self._log(f"ERROR: {msg}")
            self._ui(lambda: messagebox.showerror("Error", msg))

    # tkinter isn't thread-safe — marshal UI updates to main thread
    def _log(self, msg):
        self._ui(lambda: self.log_msg(msg))

    def _ui(self, fn):
        self.after(0, fn)


if __name__ == "__main__":
    HuffmanApp().mainloop()
