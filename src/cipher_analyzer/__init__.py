"""Classical cipher analysis for Italian and English text.

Caesar/ROT13, Atbash and Vigenère cryptanalysis with chi-squared scoring and
index of coincidence, plus Base64/hex decoding.
"""

from .analysis import (
    Analysis,
    Candidate,
    analyze,
    crack_atbash,
    crack_caesar,
    crack_vigenere,
    decode_base64,
    decode_hex,
    guess_key_lengths,
    language_scores,
)
from .ciphers import (
    atbash,
    caesar_decrypt,
    caesar_encrypt,
    rot13,
    vigenere_decrypt,
    vigenere_encrypt,
)
from .text import fold_accents

__version__ = "2.0.0"

__all__ = [
    "Analysis",
    "Candidate",
    "__version__",
    "analyze",
    "atbash",
    "caesar_decrypt",
    "caesar_encrypt",
    "crack_atbash",
    "crack_caesar",
    "crack_vigenere",
    "decode_base64",
    "decode_hex",
    "fold_accents",
    "guess_key_lengths",
    "language_scores",
    "rot13",
    "vigenere_decrypt",
    "vigenere_encrypt",
]
