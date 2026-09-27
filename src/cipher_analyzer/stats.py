"""Statistics used by the cryptanalysis: chi-squared, index of coincidence, Kasiski.

All functions take a string of lowercase ASCII letters (see
:func:`cipher_analyzer.text.letters`).
"""

from __future__ import annotations

from collections import Counter
from itertools import pairwise
from string import ascii_lowercase

from .frequencies import TABLES

MIN_EXPECTED_PERCENT = 0.05
"""Floor applied to reference frequencies inside chi-squared.

Italian lists ``k`` at 0.009 %: without a floor, one ``k`` in a 20-letter
text would add ~5500 to the score and swamp everything else. With the floor
a rare letter still costs a lot, but a single loanword cannot decide alone.
"""

RANDOM_IOC = 1 / 26
"""Index of coincidence of uniformly random letters (~0.0385)."""


def letter_counts(s: str) -> list[int]:
    """Counts of ``a``..``z`` in ``s``."""
    c = Counter(s)
    return [c.get(ch, 0) for ch in ascii_lowercase]


def chi_squared_counts(counts: list[int], lang: str) -> float:
    """Pearson chi-squared of observed ``counts`` against language ``lang``.

    Lower means closer to the language. Returns ``inf`` for zero letters.
    """
    n = sum(counts)
    if n == 0:
        return float("inf")
    table = TABLES[lang]
    total = 0.0
    for observed, ch in zip(counts, ascii_lowercase, strict=True):
        expected = n * max(table[ch], MIN_EXPECTED_PERCENT) / 100
        total += (observed - expected) ** 2 / expected
    return total


def chi_squared(s: str, lang: str) -> float:
    """Chi-squared of the letter string ``s`` against language ``lang``."""
    return chi_squared_counts(letter_counts(s), lang)


def index_of_coincidence(s: str) -> float:
    """Probability that two letters drawn from ``s`` are equal.

    English text is around 0.066, Italian around 0.075, random letters
    0.0385. A monoalphabetic cipher (Caesar, Atbash) keeps the value of the
    plaintext; Vigenère pushes it towards the random value.
    """
    n = len(s)
    if n < 2:
        return 0.0
    return sum(k * (k - 1) for k in letter_counts(s)) / (n * (n - 1))


def average_column_ioc(s: str, period: int) -> float:
    """Mean IoC of the ``period`` columns ``s[0::p], s[1::p], ...``."""
    cols = [s[i::period] for i in range(period)]
    return sum(index_of_coincidence(c) for c in cols) / period


def kasiski_factors(s: str, seq_len: int = 3, max_period: int = 20) -> Counter[int]:
    """Kasiski examination.

    For every sequence of ``seq_len`` letters that repeats, take the
    distances between occurrences and count how many of them each period
    ``2..max_period`` divides. The true key length (and its divisors) tends
    to get the highest counts.
    """
    positions: dict[str, list[int]] = {}
    for i in range(len(s) - seq_len + 1):
        positions.setdefault(s[i : i + seq_len], []).append(i)
    factors: Counter[int] = Counter()
    for pos in positions.values():
        for a, b in pairwise(pos):
            distance = b - a
            for p in range(2, max_period + 1):
                if distance % p == 0:
                    factors[p] += 1
    return factors
