"""Measure how often ``analyze`` recovers the plaintext, by text length.

Takes random passages from two public-domain books, encrypts them and counts
correct answers. Needs an Italian and an English UTF-8 text, for example
Project Gutenberg #45334 ("I promessi sposi") and #1342 ("Pride and
Prejudice"):

    python scripts/benchmark.py pg45334.txt pg1342.txt

A Caesar trial is correct if the best candidate is the exact plaintext; a
Vigenère trial if the best candidate is Vigenère with the exact key (keys of
2 to 7 letters). The numbers in the README come from this script.
"""

from __future__ import annotations

import random
import sys

from cipher_analyzer import analyze, caesar_encrypt, vigenere_encrypt

KEYS = ["zx", "abc", "key", "roma", "lemon", "crypto", "python", "segreto"]
LENGTHS = [15, 20, 30, 60, 100, 150, 250, 400]
TRIALS = 50


def passage(src: str, n_letters: int, rng: random.Random) -> str:
    start = rng.randrange(len(src) - 20 * n_letters)
    out, count = [], 0
    for c in src[start:]:
        out.append(c)
        count += c.isascii() and c.isalpha()
        if count >= n_letters:
            break
    return " ".join("".join(out).split())


def main(paths: list[str]) -> int:
    if len(paths) != 2:
        print(__doc__)
        return 2
    books = {}
    for lang, path in zip(("it", "en"), paths, strict=True):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        books[lang] = text[len(text) // 20 : -len(text) // 10]  # skip licence boilerplate
    rng = random.Random(2026)
    print(f"{'letters':>7} {'lang':>4} {'caesar':>7} {'vigenere':>9}")
    for n in LENGTHS:
        for lang, src in books.items():
            ok_c = ok_v = 0
            for _ in range(TRIALS):
                pt = passage(src, n, rng)
                best = analyze(caesar_encrypt(pt, rng.randrange(1, 26))).best
                ok_c += best is not None and best.plaintext == pt
                key = rng.choice(KEYS)
                best = analyze(vigenere_encrypt(pt, key)).best
                ok_v += best is not None and best.method == "vigenere" and best.key == key
            print(f"{n:>7} {lang:>4} {ok_c / TRIALS:>7.0%} {ok_v / TRIALS:>9.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
