import io
import json

import pytest

from cipher_analyzer import caesar_encrypt
from cipher_analyzer.cli import main


def test_text_argument(capsys):
    assert main([caesar_encrypt("il gatto nero dorme sul divano mentre piove", 7)]) == 0
    out = capsys.readouterr().out
    assert "Best guess: Caesar, key 7, Italian" in out
    assert "il gatto nero dorme sul divano mentre piove" in out


def test_base64_output_is_printed(capsys):
    assert main(["SGVsbG8gV29ybGQ="]) == 0
    out = capsys.readouterr().out
    assert "Base64" in out
    assert "Hello World" in out


def test_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("Nggnpx ng qnja\n"))
    assert main([]) == 0
    assert "Attack at dawn" in capsys.readouterr().out


def test_file(tmp_path, capsys, english):
    path = tmp_path / "ct.txt"
    path.write_text(caesar_encrypt(english, 4), encoding="utf-8")
    assert main(["-f", str(path), "--top", "1"]) == 0
    out = capsys.readouterr().out
    assert "Caesar, key 4, English" in out
    assert "Other candidates" not in out


def test_json(capsys):
    assert main(["--json", "Uryyb Jbeyq, guvf vf n grfg"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["candidates"][0]["method"] == "rot13"
    assert data["candidates"][0]["plaintext"] == "Hello World, this is a test"


def test_no_letters_exit_code(capsys):
    assert main(["12345 67890"]) == 1
    assert "no letters to analyze" in capsys.readouterr().out


def test_json_without_letters(capsys):
    assert main(["--json", ""]) == 1
    assert json.loads(capsys.readouterr().out)["candidates"] == []


def test_missing_file(capsys, tmp_path):
    assert main(["-f", str(tmp_path / "nope.txt")]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_usage_errors():
    with pytest.raises(SystemExit) as exc:
        main(["--cipher", "enigma", "x"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit):
        main(["--top", "0", "x"])
