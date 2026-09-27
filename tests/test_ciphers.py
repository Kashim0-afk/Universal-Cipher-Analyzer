import pytest

from cipher_analyzer import (
    atbash,
    caesar_decrypt,
    caesar_encrypt,
    rot13,
    vigenere_decrypt,
    vigenere_encrypt,
)


def test_caesar_known_vector():
    assert caesar_encrypt("Attack at Dawn!", 3) == "Dwwdfn dw Gdzq!"


@pytest.mark.parametrize("k", range(-30, 30, 7))
def test_caesar_roundtrip(k, italian):
    assert caesar_decrypt(caesar_encrypt(italian, k), k) == italian


def test_non_ascii_letters_are_untouched():
    # The original script shifted "è" into a-z and crashed on "ß".
    assert caesar_encrypt("è perché ß Straße", 3) == "è shufké ß Vwudßh"
    assert vigenere_encrypt("ßè", "key") == "ßè"
    assert atbash("àß") == "àß"


def test_rot13_is_involution(english):
    assert rot13("Hello") == "Uryyb"
    assert rot13(rot13(english)) == english


def test_atbash_known_vector_and_involution(italian):
    assert atbash("abc XYZ") == "zyx CBA"
    assert atbash(atbash(italian)) == italian


def test_vigenere_known_vector():
    # Classic textbook example.
    assert vigenere_encrypt("ATTACKATDAWN", "LEMON") == "LXFOPVEFRNHR"


def test_vigenere_key_advances_only_on_ascii_letters():
    assert vigenere_encrypt("a-a è a", "ab") == "a-b è a"


@pytest.mark.parametrize("key", ["roma", "LEMON", "k e y"])
def test_vigenere_roundtrip(key, english):
    assert vigenere_decrypt(vigenere_encrypt(english, key), key) == english


@pytest.mark.parametrize("key", ["", "123", "èé"])
def test_vigenere_rejects_keys_without_letters(key):
    with pytest.raises(ValueError):
        vigenere_encrypt("text", key)
