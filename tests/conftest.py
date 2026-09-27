"""Shared sample texts (written for these tests, no external corpus)."""

import pytest

ITALIAN = (
    "La crittografia classica nasce dal bisogno di proteggere i messaggi militari e "
    "diplomatici. Giulio Cesare spostava ogni lettera di tre posizioni nell'alfabeto, "
    "mentre il cifrario di Vigenère usa una parola chiave ripetuta per cambiare lo "
    "spostamento a ogni lettera. Per secoli fu considerato indecifrabile, finché nel "
    "diciannovesimo secolo Kasiski pubblicò un metodo per trovare la lunghezza della "
    "chiave e, da quella, ricostruire la chiave stessa colonna per colonna."
)

ENGLISH = (
    "Classical cryptography was born from the need to protect military and diplomatic "
    "messages. Julius Caesar shifted every letter three places along the alphabet, "
    "while the Vigenere cipher uses a repeated keyword to change the shift for each "
    "letter. For centuries it was considered unbreakable, until in the nineteenth "
    "century Kasiski published a method to find the length of the key and, from that, "
    "to rebuild the key itself one column at a time."
)


@pytest.fixture
def italian() -> str:
    return ITALIAN


@pytest.fixture
def english() -> str:
    return ENGLISH
