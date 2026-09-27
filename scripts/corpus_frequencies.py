"""Print the letter frequencies (percent) of UTF-8 text files.

Accents are folded to the base letter, as the analyzer does when scoring.

    python scripts/corpus_frequencies.py pg45334.txt
"""

from __future__ import annotations

import sys
from collections import Counter
from string import ascii_lowercase

from cipher_analyzer.text import letters


def main(paths: list[str]) -> int:
    if not paths:
        print(__doc__)
        return 2
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            counts = Counter(letters(fh.read()))
        n = sum(counts.values()) or 1
        print(f"{path}: {n} letters")
        print("  " + "  ".join(f"{c}:{100 * counts[c] / n:.2f}" for c in ascii_lowercase))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
