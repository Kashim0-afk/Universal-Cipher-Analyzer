"""Reference letter frequencies (percent) for English and Italian.

Sources
-------
English
    Robert Lewand, *Cryptological Mathematics*, MAA, 2000, as reproduced in
    the Wikipedia article "Letter frequency" (table "Relative frequencies of
    letters in other languages", English column).

Italian
    Simon Singh, Stefano Galli, *Codici e Segreti*, Rizzoli, 1999, as
    reproduced in the same Wikipedia table (Italian column), with one
    correction: the table lists ``h`` as 0.136 %, which is a decimal slip.
    Counting the letters of "I promessi sposi" (Project Gutenberg eBook
    #45334, accents folded to the base letter) gives 1.36 %, and ``h`` is
    common in Italian ("che", "chi", "ho", "ha"). We use 1.36.

``scripts/corpus_frequencies.py`` recomputes the letter frequencies of any
UTF-8 text, so the tables can be checked against a corpus of your choice.
"""

from __future__ import annotations

from string import ascii_lowercase

ENGLISH: dict[str, float] = dict(
    zip(
        ascii_lowercase,
        (
            8.167, 1.492, 2.782, 4.253, 12.702, 2.228, 2.015, 6.094, 6.966,
            0.153, 0.772, 4.025, 2.406, 6.749, 7.507, 1.929, 0.095, 5.987,
            6.327, 9.056, 2.758, 0.978, 2.360, 0.150, 1.974, 0.074,
        ),
        strict=True,
    )
)  # fmt: skip

ITALIAN: dict[str, float] = dict(
    zip(
        ascii_lowercase,
        (
            11.745, 0.927, 4.501, 3.736, 11.792, 1.153, 1.644, 1.360, 10.143,
            0.011, 0.009, 6.510, 2.512, 6.883, 9.832, 3.056, 0.505, 6.367,
            4.981, 5.623, 2.813, 2.097, 0.033, 0.008, 0.020, 1.181,
        ),
        strict=True,
    )
)  # fmt: skip

TABLES: dict[str, dict[str, float]] = {"en": ENGLISH, "it": ITALIAN}
"""Language code -> letter -> expected frequency in percent."""

LANGUAGES: tuple[str, ...] = tuple(TABLES)
