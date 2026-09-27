# Universal Cipher Analyzer

[![CI](https://github.com/Kashim0-afk/Universal-Cipher-Analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/Kashim0-afk/Universal-Cipher-Analyzer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A small command-line tool and Python library that breaks classical ciphers on
Italian and English text. It is a learning project about frequency analysis,
not a general-purpose codebreaker: "universal" in the name is historical.

What it does:

- **Caesar / ROT13**: tries all 26 shifts.
- **Atbash**: a↔z, b↔y, ...
- **Vigenère**: real cryptanalysis, not a dictionary of keys. The key length
  comes from the index of coincidence and the Kasiski examination; each key
  letter is the Caesar shift that makes its column fit the language best
  (chi-squared).
- **Base64 and hex**: strict decoding to UTF-8 text, and the decoded text is
  printed.
- **Automatic detection**: with no options it tries everything and ranks the
  results.
- **Language (IT/EN)**: every candidate plaintext is scored against both
  languages and the language is chosen on the *decrypted* text.

No dependencies outside the standard library.

## How the scoring works

For each candidate plaintext the tool counts the 26 letters and computes
Pearson's chi-squared against reference frequencies:

- English: Lewand, *Cryptological Mathematics* (2000);
- Italian: Singh and Galli, *Codici e Segreti* (1999), with `h` corrected
  from 0.136 % to 1.36 % (a decimal slip in the published table, checked
  against the letters of *I promessi sposi*).

Both are the tables reproduced on Wikipedia, "Letter frequency". Sources and
the correction are documented in
[`src/cipher_analyzer/frequencies.py`](src/cipher_analyzer/frequencies.py).
Lower chi-squared means closer to the language.

Accented letters and `ß` are never altered by the ciphers: they are copied
through unchanged, so `perché` stays `perché` in the output. For scoring only,
they are folded to ASCII (`è` counts as `e`, `ß` as `ss`).

Vigenère adds free parameters (one per key letter), and more parameters always
fit the frequencies a bit better. The ranking therefore adds a fixed cost per
key letter, and in automatic mode Vigenère must beat the best single-alphabet
answer by a clear margin on a ciphertext whose index of coincidence is low.

## Limits

Frequency analysis needs text. Measured with
[`scripts/benchmark.py`](scripts/benchmark.py) (50 random passages per row
from *I promessi sposi* and *Pride and Prejudice*; Vigenère keys of 2 to 7
letters):

| Letters | Caesar IT | Caesar EN | Vigenère IT | Vigenère EN |
|--------:|----------:|----------:|------------:|------------:|
| 15      | 98 %      | 90 %      | –           | –           |
| 30      | 100 %     | 94 %      | –           | –           |
| 60      | 100 %     | 100 %     | 64 %        | 34 %        |
| 100     | 100 %     | 100 %     | 86 %        | 66 %        |
| 150     | 100 %     | 100 %     | 90 %        | 76 %        |
| 250     | 100 %     | 100 %     | 100 %       | 98 %        |

- Under ~20 letters any answer is a guess; the tool prints a warning. "hello"
  or "Uryyb Jbeyq" are too short.
- Vigenère is not attempted automatically below 60 letters, and each key
  length needs at least 8 letters per column. As a rule of thumb, give it
  30 or more letters per key letter.
- Only English and Italian, only the 26 ASCII letters. General substitution
  ciphers, transposition, XOR and modern ciphers are not supported.
- Base64/hex are recognised only when they decode to printable UTF-8 text.

## Installation

Python 3.10 or newer.

```bash
git clone https://github.com/Kashim0-afk/Universal-Cipher-Analyzer
cd Universal-Cipher-Analyzer
pip install -e .
```

This installs the `cipher-analyzer` command (`python -m cipher_analyzer` works
too). For development: `pip install -e ".[dev]"`, then `pytest` and
`ruff check .`.

## Usage

```text
cipher-analyzer [TEXT] [-f FILE] [-c {auto,caesar,rot13,atbash,vigenere,base64,hex}]
                [-l {auto,en,it}] [-n TOP] [--json]
```

Without `TEXT` or `--file` it reads standard input. Exit status is 0 when a
candidate is found, 1 when there is nothing to analyze, 2 on usage errors.

### Examples (real output)

Caesar, Italian (the original version of this tool got this one wrong):

```text
$ cipher-analyzer "ps nhaav ulyv kvytl zbs kpchuv tluayl wpvcl"
Input: 36 letters, index of coincidence 0.059
Note: Vigenère skipped: fewer than 60 letters

Best guess: Caesar, key 7, Italian (chi-squared 10.8)

  il gatto nero dorme sul divano mentre piove

Other candidates (lower chi-squared = closer to the language):
  2. rot13     key=13       en chi2=  146.5  cf aunni hyli xilgy mof xcpuhi gyhnly jcipy
  3. plaintext key=-        en chi2=  154.2  ps nhaav ulyv kvytl zbs kpchuv tluayl wpvcl
  4. caesar    key=9        en chi2=  185.2  gj eyrrm lcpm bmpkc qsj bgtylm kclrpc ngmtc
  5. caesar    key=18       en chi2=  232.0  xa vpiid ctgd sdgbt hja sxkpcd btcigt exdkt
```

Vigenère, key `roma`, 211 letters (note that `è` passes through untouched):

```text
$ cipher-analyzer -n 2 "Co orzhfoxfmfzo olrgeito zajqq drz nijcsnf ru picfexuqrv w yejgmgxw yicwfaiw q dzdxodofitw. Silzuo Tseais epfgfamo agew xekhqrr ru tis bojwlifbu, mvbfrv wx cztdaiwa dz Jugvbède lgm ueo baicxa tvuams digsfuko bei qmmswmrv za sgcetraqnkc m oxbu lvhfeio."
Input: 211 letters, index of coincidence 0.042

Best guess: Vigenère, key 'roma', Italian (chi-squared 28.3)

  La crittografia classica nasce dal bisogno di proteggere i messaggi militari e diplomatici. Giulio Cesare spostava ogni lettera di tre posizioni, mentre il cifrario di Vigenère usa una parola chiave ripetuta per cambiare lo spostamento a ogni lettera.

Other candidates (lower chi-squared = closer to the language):
  2. caesar    key=12       en chi2=  791.2  Qc cfnvtcltatnc czfuswhc noxee rfn bwxqgbt fi dwqtsliefj ...
```

Atbash, English:

```text
$ cipher-analyzer -n 1 "Nvvg nv zg gsv low yirwtv zugvi hfmhvg"
Input: 31 letters, index of coincidence 0.077
Note: Vigenère skipped: fewer than 60 letters

Best guess: Atbash, English (chi-squared 13.6)

  Meet me at the old bridge after sunset
```

Base64 (UTF-8 with accents):

```text
$ cipher-analyzer "UGVyY2jDqSBub24gw6ggcXVpPw=="
Input decodes cleanly as base64.

Best guess: Base64 (encoding), Italian (chi-squared 27.9)

  Perché non è qui?
```

Input without letters does not crash:

```text
$ cipher-analyzer "12345 67890"
Input: 0 letters, index of coincidence 0.000
Note: no letters to analyze
No candidate decryption found.
```

`--json` prints the same candidates as JSON, with the chi-squared for each
language.

### As a library

```python
from cipher_analyzer import analyze

with open("secret.txt", encoding="utf-8") as fh:
    result = analyze(fh.read())
for c in result.candidates:
    print(c.method, c.key, c.language, round(c.score, 1), c.plaintext[:40])
```

## Project layout

```text
src/cipher_analyzer/
    frequencies.py   reference tables and their sources
    text.py          accent folding, letter extraction
    stats.py         chi-squared, index of coincidence, Kasiski
    ciphers.py       encrypt/decrypt (Caesar, ROT13, Atbash, Vigenère)
    analysis.py      cryptanalysis and automatic detection
    cli.py           command-line interface
tests/               pytest suite
scripts/             benchmark and corpus frequency counter
```

## In italiano

Strumento didattico da riga di comando che rompe Cesare/ROT13, Atbash e
Vigenère su testi italiani e inglesi e decodifica Base64/hex. La lingua si
sceglie sul testo decifrato con il chi-quadro sulle frequenze delle lettere;
per Vigenère la lunghezza della chiave si stima con l'indice di coincidenza e
Kasiski. Su testi brevi (meno di ~20 lettere per Cesare, meno di qualche
centinaio per Vigenère) i risultati non sono affidabili: vedi la tabella nella
sezione *Limits*.

## License

MIT, see [LICENSE](LICENSE).
