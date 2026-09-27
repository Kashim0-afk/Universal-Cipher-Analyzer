import base64
import time

import pytest

from cipher_analyzer import (
    analyze,
    atbash,
    caesar_encrypt,
    crack_caesar,
    crack_vigenere,
    decode_base64,
    decode_hex,
    guess_key_lengths,
    language_scores,
    vigenere_encrypt,
)

# ---- Caesar: includes the cases the original tool got wrong ----------------


@pytest.mark.parametrize(
    ("plaintext", "key", "lang"),
    [
        ("il gatto nero dorme sul divano mentre piove", 7, "it"),
        ("ciao come stai", 5, "it"),
        ("the quick brown fox jumps over the lazy dog", 3, "en"),
        ("meet me near the old bridge after sunset", 11, "en"),
    ],
)
def test_caesar_short_sentences(plaintext, key, lang):
    best = analyze(caesar_encrypt(plaintext, key)).best
    assert best is not None
    assert (best.method, best.key, best.language) == ("caesar", str(key), lang)
    assert best.plaintext == plaintext


def test_rot13_is_labelled():
    best = analyze(caesar_encrypt("Attack at dawn", 13)).best
    assert (best.method, best.key, best.plaintext) == ("rot13", "13", "Attack at dawn")


@pytest.mark.parametrize("key", range(1, 26))
def test_caesar_every_key_both_languages(key, italian, english):
    for text, lang in ((italian, "it"), (english, "en")):
        best = analyze(caesar_encrypt(text, key)).best
        assert best.plaintext == text
        assert best.language == lang


def test_crack_caesar_returns_all_shifts_sorted():
    cands = crack_caesar(caesar_encrypt("buongiorno a tutti quanti", 4))
    assert len(cands) == 26
    assert cands[0].key == "4"
    assert [c.score for c in cands] == sorted(c.score for c in cands)


def test_plaintext_is_recognised(italian):
    best = analyze(italian).best
    assert (best.method, best.key, best.language) == ("plaintext", None, "it")


def test_very_short_text_comes_with_a_warning():
    result = analyze(caesar_encrypt("hello", 1))
    assert any("unreliable" in n for n in result.notes)


# ---- Accents and ß ---------------------------------------------------------


def test_accents_survive_caesar():
    plaintext = "Perché la città è così bella? Già, però è piena di turisti."
    best = analyze(caesar_encrypt(plaintext, 9)).best
    assert best.plaintext == plaintext
    assert best.language == "it"


def test_eszett_does_not_crash_and_is_preserved():
    plaintext = "the old man walked down the Straße to buy fresh bread and milk"
    for ct in (caesar_encrypt(plaintext, 6), vigenere_encrypt(plaintext, "key")):
        result = analyze(ct)
        assert result.best is not None
        assert "ß" in result.best.plaintext
    assert analyze(caesar_encrypt(plaintext, 6)).best.plaintext == plaintext


def test_accented_letters_count_for_scoring_only():
    assert language_scores("perché è così") == language_scores("perche e cosi")
    best = analyze(caesar_encrypt("Perché la città è così bella quando piove?", 2)).best
    assert best.plaintext == "Perché la città è così bella quando piove?"


# ---- Atbash ----------------------------------------------------------------


def test_atbash_detected(italian, english):
    for text, lang in ((italian, "it"), (english, "en")):
        best = analyze(atbash(text)).best
        assert (best.method, best.language, best.plaintext) == ("atbash", lang, text)


# ---- Vigenère --------------------------------------------------------------


@pytest.mark.parametrize("key", ["roma", "lemon", "segreto"])
def test_vigenere_auto_detected(key, italian, english):
    for text, lang in ((italian, "it"), (english, "en")):
        best = analyze(vigenere_encrypt(text, key)).best
        assert (best.method, best.key, best.language) == ("vigenere", key, lang)
        assert best.plaintext == text


@pytest.mark.parametrize("key", ["roma", "lemon"])
def test_vigenere_about_200_letters(key, italian, english):
    for text in (italian[:250], english[:250]):
        best = crack_vigenere(vigenere_encrypt(text, key))[0]
        assert best.key == key


def test_key_length_guess_contains_true_length(english):
    assert 5 in guess_key_lengths(vigenere_encrypt(english, "lemon"))


def test_vigenere_on_short_text_is_refused_not_crashing():
    result = analyze(vigenere_encrypt("ciao come stai", "roma"), cipher="vigenere")
    assert result.best is None
    assert any("too short" in n for n in result.notes)


def test_vigenere_is_fast(english):
    ct = vigenere_encrypt(english * 3, "cryptography")
    start = time.perf_counter()
    best = analyze(ct).best
    assert time.perf_counter() - start < 2.0
    assert best.key == "cryptography"


def test_caesar_text_is_not_reported_as_vigenere(english):
    assert analyze(caesar_encrypt(english, 21)).best.method == "caesar"


# ---- Encodings -------------------------------------------------------------


def test_base64_is_decoded_and_shown():
    result = analyze("SGVsbG8gV29ybGQ=")
    assert [(c.method, c.plaintext) for c in result.candidates] == [("base64", "Hello World")]


def test_base64_utf8_italian():
    encoded = base64.b64encode("Perché non è qui?".encode()).decode()
    best = analyze(encoded).best
    assert (best.method, best.plaintext) == ("base64", "Perché non è qui?")


@pytest.mark.parametrize("text", ["ciao", "test", "abc", "SGVsbG8", "not base64!"])
def test_base64_rejects_non_text(text):
    assert decode_base64(text) is None


def test_hex_is_decoded():
    assert decode_hex("63 69 61 6f") == "ciao"
    assert decode_hex("0x6369616f") == "ciao"
    assert analyze("48656c6c6f").best.method == "hex"
    assert decode_hex("cafe") is None  # valid hex, not text
    assert decode_hex("abc") is None


def test_forced_encoding_on_wrong_input():
    result = analyze("hello world", cipher="base64")
    assert result.best is None
    assert result.notes == ["input is not valid base64 for UTF-8 text"]


# ---- Robustness ------------------------------------------------------------


@pytest.mark.parametrize("text", ["", "   \n", "12345 67890", "?!.,;:", "€€ 42 ☺"])
def test_input_without_letters(text):
    result = analyze(text)
    assert result.best is None
    assert result.letters == 0
    assert "no letters to analyze" in result.notes


def test_language_can_be_forced():
    best = analyze(caesar_encrypt("ciao come stai", 5), lang="en").best
    assert best.language == "en"
    assert set(best.language_scores) == {"en"}


def test_bad_arguments_raise():
    with pytest.raises(ValueError):
        analyze("x", cipher="enigma")
    with pytest.raises(ValueError):
        analyze("x", lang="fr")


def test_top_limits_candidates(english):
    assert len(analyze(caesar_encrypt(english, 3), top=2).candidates) == 2
