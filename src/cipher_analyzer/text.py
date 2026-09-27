"""Text helpers: accent folding and letter extraction.

The ciphers in this package only transform the 52 ASCII letters. Everything
else (digits, punctuation, accented letters, ``ß``) is copied through
unchanged, so the output never loses characters.

Accent folding is used only for *scoring*: ``"perché"`` counts as
``p e r c h e`` when letter frequencies are compared, while the text shown
to the user keeps its accents.
"""

from __future__ import annotations

import unicodedata
from string import ascii_letters, ascii_lowercase

# Letters that NFKD does not decompose into "base letter + combining mark".
_SPECIAL = str.maketrans(
    {
        "ß": "ss",
        "ẞ": "SS",
        "æ": "ae",
        "Æ": "AE",
        "œ": "oe",
        "Œ": "OE",
        "ø": "o",
        "Ø": "O",
        "đ": "d",
        "Đ": "D",
        "ł": "l",
        "Ł": "L",
    }
)

ASCII_LETTERS = frozenset(ascii_letters)
LOWERCASE = frozenset(ascii_lowercase)


def fold_accents(text: str) -> str:
    """Return ``text`` with accented Latin letters replaced by ASCII ones.

    ``"È perché ß"`` becomes ``"E perche ss"``. Characters that have no
    ASCII equivalent (``"€"``, ``"日"``) are kept as they are.
    """
    decomposed = unicodedata.normalize("NFKD", text.translate(_SPECIAL))
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def letters(text: str) -> str:
    """Lowercase ASCII letters of ``text`` after accent folding, in order."""
    return "".join(c for c in fold_accents(text).lower() if c in LOWERCASE)
