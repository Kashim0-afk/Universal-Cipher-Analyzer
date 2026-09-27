"""Encryption and decryption for the supported classical ciphers.

Only ASCII letters are transformed; case is preserved and every other
character is copied through unchanged.
"""

from __future__ import annotations

from string import ascii_lowercase

from .text import ASCII_LETTERS

__all__ = [
    "atbash",
    "caesar_decrypt",
    "caesar_encrypt",
    "rot13",
    "vigenere_decrypt",
    "vigenere_encrypt",
]


def _shift_char(c: str, k: int) -> str:
    base = ord("A") if c.isupper() else ord("a")
    return chr((ord(c) - base + k) % 26 + base)


def caesar_encrypt(text: str, shift: int) -> str:
    """Shift every ASCII letter forward by ``shift`` positions."""
    return "".join(_shift_char(c, shift) if c in ASCII_LETTERS else c for c in text)


def caesar_decrypt(text: str, shift: int) -> str:
    """Inverse of :func:`caesar_encrypt`."""
    return caesar_encrypt(text, -shift)


def rot13(text: str) -> str:
    """ROT13 is Caesar with shift 13; it is its own inverse."""
    return caesar_encrypt(text, 13)


def atbash(text: str) -> str:
    """Map a<->z, b<->y, ...; Atbash is its own inverse."""
    out = []
    for c in text:
        if c in ASCII_LETTERS:
            base = ord("A") if c.isupper() else ord("a")
            out.append(chr(base + 25 - (ord(c) - base)))
        else:
            out.append(c)
    return "".join(out)


def _key_shifts(key: str) -> list[int]:
    shifts = [ascii_lowercase.index(c) for c in key.lower() if c in ascii_lowercase]
    if not shifts:
        raise ValueError("Vigenère key must contain at least one ASCII letter")
    return shifts


def _vigenere(text: str, key: str, sign: int) -> str:
    shifts = _key_shifts(key)
    out = []
    j = 0
    for c in text:
        if c in ASCII_LETTERS:
            out.append(_shift_char(c, sign * shifts[j % len(shifts)]))
            j += 1
        else:
            out.append(c)
    return "".join(out)


def vigenere_encrypt(text: str, key: str) -> str:
    """Vigenère encryption. The key advances only on ASCII letters."""
    return _vigenere(text, key, +1)


def vigenere_decrypt(text: str, key: str) -> str:
    """Inverse of :func:`vigenere_encrypt`."""
    return _vigenere(text, key, -1)
