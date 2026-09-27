"""Cryptanalysis: find the cipher, the key and the language of a ciphertext.

Every candidate decryption is scored with chi-squared against the English
and Italian reference frequencies (see :mod:`cipher_analyzer.frequencies`).
The language is decided on the *decrypted* text, never on the ciphertext.
"""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from string import ascii_lowercase

from .ciphers import atbash, caesar_decrypt, vigenere_decrypt
from .frequencies import LANGUAGES
from .stats import (
    average_column_ioc,
    chi_squared_counts,
    index_of_coincidence,
    kasiski_factors,
    letter_counts,
)
from .text import ASCII_LETTERS, letters

CIPHERS = ("auto", "caesar", "rot13", "atbash", "vigenere", "base64", "hex")

MIN_VIGENERE_LETTERS = 60
"""Below this many letters Vigenère is not attempted in ``auto`` mode."""

MIN_COLUMN_LETTERS = 8
"""A key length is only tried if every column gets at least this many letters."""

IOC_THRESHOLD = 0.05
"""Average column IoC that makes a key length worth trying."""

KEY_LETTER_PENALTY = 4.0
"""Chi-squared cost of each key letter when ranking Vigenère solutions.

Every key letter is a free parameter: a longer key always fits the letter
frequencies a little better, even when it is wrong. Without a cost, a
150-letter text encrypted with ``roma`` is "solved" with a 12-letter key.
"""

KEY_AGREEMENT = 0.5
"""See :func:`_divisor_keys`."""

VIGENERE_IOC_LIMIT = 0.058
"""Ciphertext IoC above this looks monoalphabetic (EN ~0.066, IT ~0.075)."""

VIGENERE_GAIN = 0.6
"""In ``auto`` mode Vigenère must reach a (penalized) chi-squared below
``VIGENERE_GAIN`` times the best monoalphabetic one; see :func:`_vigenere_wins`.
"""


@dataclass(frozen=True)
class Candidate:
    """One possible decryption."""

    method: str
    """``plaintext``, ``caesar``, ``rot13``, ``atbash``, ``vigenere``, ``base64`` or ``hex``."""
    key: str | None
    language: str | None
    """Best-fitting language of :attr:`plaintext`, or ``None`` if it has no letters."""
    score: float
    """Chi-squared of :attr:`plaintext` against :attr:`language` (lower is better)."""
    plaintext: str
    language_scores: dict[str, float] = field(default_factory=dict, compare=False)
    """Chi-squared against every language considered."""


@dataclass(frozen=True)
class Analysis:
    """Result of :func:`analyze`."""

    text: str
    letters: int
    ioc: float
    candidates: list[Candidate]
    notes: list[str] = field(default_factory=list)

    @property
    def best(self) -> Candidate | None:
        return self.candidates[0] if self.candidates else None


def language_scores(text: str, langs: Iterable[str] = LANGUAGES) -> dict[str, float]:
    """Chi-squared of ``text`` against each language (accents folded)."""
    counts = letter_counts(letters(text))
    return {lang: chi_squared_counts(counts, lang) for lang in langs}


def _candidate(method: str, key: str | None, plaintext: str, langs: tuple[str, ...]) -> Candidate:
    scores = language_scores(plaintext, langs)
    lang = min(scores, key=scores.__getitem__)
    if scores[lang] == float("inf"):
        return Candidate(method, key, None, float("inf"), plaintext, scores)
    return Candidate(method, key, lang, scores[lang], plaintext, scores)


def _langs(lang: str) -> tuple[str, ...]:
    if lang == "auto":
        return LANGUAGES
    if lang not in LANGUAGES:
        raise ValueError(f"unknown language {lang!r}; choose from {', '.join(LANGUAGES)}")
    return (lang,)


# --------------------------------------------------------------------------
# Encodings (not ciphers: no key, just a different representation)
# --------------------------------------------------------------------------


def _printable(s: str) -> bool:
    return bool(s) and all(c.isprintable() or c in "\n\r\t" for c in s)


def decode_base64(text: str) -> str | None:
    """Strict Base64 decode to UTF-8 text, or ``None``.

    Whitespace is ignored; length must be a multiple of 4 and the result
    must be printable UTF-8. Plain words such as ``"ciao"`` are valid Base64
    alphabet-wise but decode to binary garbage, so they are rejected.
    """
    s = "".join(text.split())
    if len(s) < 4 or len(s) % 4:
        return None
    try:
        decoded = base64.b64decode(s, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    return decoded if _printable(decoded) else None


_HEX_RE = re.compile(r"(?:0x)?([0-9a-fA-F]+)")


def decode_hex(text: str) -> str | None:
    """Hex (optionally spaced, optional ``0x`` prefix) to UTF-8 text, or ``None``."""
    s = "".join(text.split())
    m = _HEX_RE.fullmatch(s)
    if not m or len(m.group(1)) < 4 or len(m.group(1)) % 2:
        return None
    try:
        decoded = bytes.fromhex(m.group(1)).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    return decoded if _printable(decoded) else None


# --------------------------------------------------------------------------
# Monoalphabetic ciphers
# --------------------------------------------------------------------------


def crack_caesar(text: str, lang: str = "auto") -> list[Candidate]:
    """All 26 Caesar shifts, best first. Shift 0 is reported as ``plaintext``,
    shift 13 as ``rot13``."""
    langs = _langs(lang)
    out = []
    for k in range(26):
        method = {0: "plaintext", 13: "rot13"}.get(k, "caesar")
        out.append(_candidate(method, None if k == 0 else str(k), caesar_decrypt(text, k), langs))
    return sorted(out, key=lambda c: c.score)


def crack_atbash(text: str, lang: str = "auto") -> Candidate:
    """Atbash has no key: decrypt and score."""
    return _candidate("atbash", None, atbash(text), _langs(lang))


# --------------------------------------------------------------------------
# Vigenère
# --------------------------------------------------------------------------


def _cipher_letters(text: str) -> str:
    """The letters Vigenère actually shifted (ASCII only, no folding)."""
    return "".join(c.lower() for c in text if c in ASCII_LETTERS)


def guess_key_lengths(text: str, max_len: int = 20, top: int = 6) -> list[int]:
    """Plausible Vigenère key lengths (2..``max_len``), most likely first.

    With the right length every column is a plain Caesar, so the average
    column index of coincidence rises to the language value (~0.07); wrong
    lengths mix alphabets and stay near 0.04-0.05. Returned: every length
    whose IoC reaches :data:`IOC_THRESHOLD` (at least the ``top`` best by
    IoC), plus the two strongest Kasiski periods. Lengths that leave fewer
    than :data:`MIN_COLUMN_LETTERS` letters per column are skipped.

    IoC alone cannot choose among the survivors: multiples of the right
    length score just as high, and short columns make the IoC noisy.
    :func:`crack_vigenere` settles it with chi-squared.
    """
    s = _cipher_letters(text)
    max_len = min(max_len, len(s) // MIN_COLUMN_LETTERS)
    if max_len < 2:
        return []
    iocs = {p: average_column_ioc(s, p) for p in range(2, max_len + 1)}
    by_ioc = sorted(iocs, key=lambda p: -iocs[p])
    ranked = [p for p in by_ioc if iocs[p] >= IOC_THRESHOLD] or by_ioc[:top]
    for p in by_ioc[:top] + [p for p, _ in kasiski_factors(s, max_period=max_len).most_common(2)]:
        if p not in ranked:
            ranked.append(p)
    return ranked


def _solve_key(s: str, period: int, lang: str) -> str:
    """For each column pick the shift whose decryption best fits ``lang``."""
    key = []
    for i in range(period):
        counts = letter_counts(s[i::period])
        # Decrypting with shift k turns ciphertext letter (p + k) into p.
        best = min(
            range(26),
            key=lambda k: chi_squared_counts(counts[k:] + counts[:k], lang),
        )
        key.append(ascii_lowercase[best])
    return "".join(key)


def _minimal_period(key: str) -> str:
    """``"romaroma"`` -> ``"roma"``."""
    for p in range(1, len(key)):
        if len(key) % p == 0 and key[:p] * (len(key) // p) == key:
            return key[:p]
    return key


def _divisor_keys(s: str, key: str, lang: str) -> list[str]:
    """Shorter keys worth trying when ``key`` may be the true key repeated.

    Solving at twice the true length gives the key twice, except that
    columns with half the letters occasionally pick a wrong shift
    (``"pyqgunjython"`` instead of ``"python"``). For every divisor ``d`` of
    the length, the key solved at ``d`` is proposed if, repeated, it matches
    at least :data:`KEY_AGREEMENT` of the letters. The proposals compete with
    the long key on score; they are not forced.
    """
    n = len(key)
    out = []
    for d in range(2, n):
        if n % d:
            continue
        short = _minimal_period(_solve_key(s, d, lang))
        same = sum(a == b for a, b in zip(key, short * (n // len(short)), strict=True))
        if same >= KEY_AGREEMENT * n:
            out.append(short)
    return out


def crack_vigenere(text: str, lang: str = "auto", max_len: int = 20) -> list[Candidate]:
    """Vigenère cryptanalysis: candidate key lengths by IoC/Kasiski, then each
    key letter by chi-squared on its column. Returns candidates, best first
    (empty if the text is too short).

    Keys found at a multiple of the true length also propose their shorter
    versions (see :func:`_divisor_keys`); solutions are ranked by chi-squared plus
    :data:`KEY_LETTER_PENALTY` per key letter.
    """
    langs = _langs(lang)
    s = _cipher_letters(text)
    seen: dict[str, Candidate] = {}
    for period in guess_key_lengths(text, max_len):
        for lg in langs:
            key = _minimal_period(_solve_key(s, period, lg))
            for k in [key, *_divisor_keys(s, key, lg)]:
                if len(k) < 2 or k in seen:
                    continue  # a one-letter key is just Caesar
                seen[k] = _candidate("vigenere", k, vigenere_decrypt(text, k), langs)
    if not seen:
        return []
    return sorted(seen.values(), key=_penalized)


def _penalized(c: Candidate) -> float:
    """Chi-squared plus :data:`KEY_LETTER_PENALTY` per key letter."""
    return c.score + KEY_LETTER_PENALTY * len(c.key or "")


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def analyze(
    text: str,
    cipher: str = "auto",
    lang: str = "auto",
    top: int = 5,
) -> Analysis:
    """Analyze ``text`` and return ranked candidate decryptions.

    ``cipher`` restricts the search (see :data:`CIPHERS`); ``lang`` is
    ``"auto"``, ``"en"`` or ``"it"``. Never raises on odd input: an empty string
    or text without letters gives an :class:`Analysis` with a note.
    """
    if cipher not in CIPHERS:
        raise ValueError(f"unknown cipher {cipher!r}; choose from {', '.join(CIPHERS)}")
    langs = _langs(lang)
    s = letters(text)
    notes: list[str] = []
    candidates: list[Candidate] = []

    if cipher in ("auto", "hex"):
        decoded = decode_hex(text)
        if decoded is not None:
            candidates.append(_candidate("hex", None, decoded, langs))
    if cipher in ("auto", "base64") and not candidates:
        decoded = decode_base64(text)
        if decoded is not None:
            candidates.append(_candidate("base64", None, decoded, langs))
    if cipher in ("hex", "base64") and not candidates:
        notes.append(f"input is not valid {cipher} for UTF-8 text")

    if not s:
        if not candidates:
            notes.append("no letters to analyze")
        return Analysis(text, 0, 0.0, candidates[:top], notes)

    ioc = index_of_coincidence(_cipher_letters(text))
    if cipher in ("hex", "base64") or candidates:
        # A clean Base64/hex decode to readable text is conclusive: running
        # letter statistics on the encoded form would only add noise.
        return Analysis(text, len(s), ioc, candidates[:top], notes)

    classical: list[Candidate] = []
    if cipher in ("auto", "caesar"):
        classical += crack_caesar(text, lang)
    elif cipher == "rot13":
        classical += [c for c in crack_caesar(text, lang) if c.method == "rot13"]
    if cipher in ("auto", "atbash"):
        classical.append(crack_atbash(text, lang))
    classical.sort(key=lambda c: c.score)

    if cipher == "vigenere" or (cipher == "auto" and len(s) >= MIN_VIGENERE_LETTERS):
        vig = crack_vigenere(text, lang)
        if cipher == "vigenere":
            classical = vig
            if not vig:
                notes.append(
                    f"text too short for Vigenère: need at least "
                    f"{2 * MIN_COLUMN_LETTERS} letters, got {len(s)}"
                )
        elif vig and _vigenere_wins(vig[0], classical[0], ioc):
            classical = vig[:1] + classical + vig[1:]
        else:
            classical += vig
    elif cipher == "auto":
        notes.append(f"Vigenère skipped: fewer than {MIN_VIGENERE_LETTERS} letters")

    if len(s) < 20:
        notes.append(f"only {len(s)} letters: frequency analysis is unreliable on very short texts")
    candidates += classical
    return Analysis(text, len(s), ioc, candidates[:top], notes)


def _vigenere_wins(vig: Candidate, mono: Candidate, ioc: float) -> bool:
    """Decide between the best Vigenère and the best monoalphabetic solution.

    Both scores include :data:`KEY_LETTER_PENALTY` per key letter (a Caesar
    shift counts as one), and Vigenère must also win by the margin
    :data:`VIGENERE_GAIN` on a ciphertext whose IoC is not monoalphabetic.
    """
    mono_cost = mono.score + KEY_LETTER_PENALTY
    return ioc < VIGENERE_IOC_LIMIT and _penalized(vig) < VIGENERE_GAIN * mono_cost
