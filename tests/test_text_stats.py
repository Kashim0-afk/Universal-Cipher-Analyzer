import pytest

from cipher_analyzer.frequencies import TABLES
from cipher_analyzer.stats import (
    RANDOM_IOC,
    chi_squared,
    index_of_coincidence,
    kasiski_factors,
)
from cipher_analyzer.text import fold_accents, letters


def test_fold_accents():
    assert fold_accents("È perché così, Straße, Œuvre") == "E perche cosi, Strasse, OEuvre"
    assert fold_accents("€ 日本") == "€ 日本"


def test_letters_folds_and_lowercases():
    assert letters("Città è 42 ß!") == "cittaess"
    assert letters("") == ""
    assert letters("12345 ?!") == ""


@pytest.mark.parametrize("lang", ["en", "it"])
def test_tables_are_complete_and_sum_to_100(lang):
    table = TABLES[lang]
    assert len(table) == 26
    assert sum(table.values()) == pytest.approx(100, abs=1.5)


def test_chi_squared_separates_languages(italian, english):
    it, en = letters(italian), letters(english)
    assert chi_squared(it, "it") < chi_squared(it, "en")
    assert chi_squared(en, "en") < chi_squared(en, "it")
    # The original scorer rated "zzzzqqqxxxjjj" almost like real English.
    assert chi_squared("zzzzqqqxxxjjj", "en") > 20 * chi_squared(en, "en")


def test_chi_squared_without_letters_is_infinite():
    assert chi_squared("", "en") == float("inf")


def test_index_of_coincidence(italian, english):
    assert index_of_coincidence(letters(italian)) > 0.065
    assert index_of_coincidence(letters(english)) > 0.058
    assert index_of_coincidence("abcdefghijklmnopqrstuvwxyz" * 4) < RANDOM_IOC
    assert index_of_coincidence("") == 0.0
    assert index_of_coincidence("a") == 0.0


def test_kasiski_finds_repeat_distance():
    factors = kasiski_factors("abcxxxxxxabc", max_period=10)
    assert factors[9] == 1
    assert factors[3] == 1
