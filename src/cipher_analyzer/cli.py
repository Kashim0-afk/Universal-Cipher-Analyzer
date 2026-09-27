"""Command-line interface: ``cipher-analyzer`` / ``python -m cipher_analyzer``."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict

from . import __version__
from .analysis import CIPHERS, Analysis, Candidate, analyze

LANG_NAMES = {"en": "English", "it": "Italian"}
METHOD_NAMES = {
    "plaintext": "no cipher (text is already readable)",
    "caesar": "Caesar",
    "rot13": "ROT13 (Caesar, shift 13)",
    "atbash": "Atbash",
    "vigenere": "Vigenère",
    "base64": "Base64 (encoding)",
    "hex": "hex (encoding)",
}
PREVIEW = 60


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cipher-analyzer",
        description=(
            "Detect and break classical ciphers (Caesar/ROT13, Atbash, Vigenère) "
            "and decode Base64/hex. Candidates are scored with chi-squared against "
            "English and Italian letter frequencies."
        ),
        epilog="Reads TEXT, or --file, or standard input when neither is given.",
    )
    p.add_argument("text", nargs="?", help="ciphertext (quote it)")
    p.add_argument("-f", "--file", help="read the ciphertext from a UTF-8 file")
    p.add_argument(
        "-c",
        "--cipher",
        choices=CIPHERS,
        default="auto",
        help="restrict the search (default: auto)",
    )
    p.add_argument(
        "-l", "--lang", choices=("auto", "en", "it"), default="auto", help="plaintext language"
    )
    p.add_argument("-n", "--top", type=int, default=5, help="candidates to show (default: 5)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None and args.file is not None:
        raise SystemExit("cipher-analyzer: error: give TEXT or --file, not both")
    if args.file is not None:
        with open(args.file, encoding="utf-8") as fh:
            return fh.read()
    if args.text is not None:
        return args.text
    return sys.stdin.read()


def _score(c: Candidate) -> str:
    return "n/a" if c.language is None else f"{c.score:.1f}"


def _describe(c: Candidate) -> str:
    parts = [METHOD_NAMES.get(c.method, c.method)]
    if c.key is not None:
        parts.append(f"key {c.key!r}" if c.method == "vigenere" else f"key {c.key}")
    if c.language is not None:
        parts.append(LANG_NAMES.get(c.language, c.language))
    return ", ".join(parts)


def _one_line(s: str) -> str:
    s = " ".join(s.split())
    return s if len(s) <= PREVIEW else s[: PREVIEW - 3] + "..."


def format_report(result: Analysis) -> str:
    best = result.best
    if best is not None and best.method in ("base64", "hex"):
        lines = [f"Input decodes cleanly as {best.method}."]
    else:
        lines = [f"Input: {result.letters} letters, index of coincidence {result.ioc:.3f}"]
    for note in result.notes:
        lines.append(f"Note: {note}")
    if best is None:
        lines.append("No candidate decryption found.")
        return "\n".join(lines)
    lines += [
        "",
        f"Best guess: {_describe(best)} (chi-squared {_score(best)})",
        "",
        *("  " + line for line in best.plaintext.strip("\n").splitlines()),
    ]
    if len(result.candidates) > 1:
        lines += ["", "Other candidates (lower chi-squared = closer to the language):"]
        for i, c in enumerate(result.candidates[1:], start=2):
            key = c.key if c.key is not None else "-"
            lang = c.language or "-"
            lines.append(
                f"  {i}. {c.method:<9} key={key:<8} {lang:<2} "
                f"chi2={_score(c):>7}  {_one_line(c.plaintext)}"
            )
    return "\n".join(lines)


def _to_json(result: Analysis) -> str:
    def clean(x: float) -> float | None:
        return None if x == float("inf") else round(x, 3)

    data = {
        "letters": result.letters,
        "ioc": round(result.ioc, 5),
        "notes": result.notes,
        "candidates": [
            {
                **asdict(c),
                "score": clean(c.score),
                "language_scores": {k: clean(v) for k, v in c.language_scores.items()},
            }
            for c in result.candidates
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Exit status: 0 if a candidate was found, 1 if not, 2 on usage errors."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    args = build_parser().parse_args(argv)
    if args.top < 1:
        raise SystemExit("cipher-analyzer: error: --top must be at least 1")
    try:
        text = _read_input(args)
    except OSError as exc:
        print(f"cipher-analyzer: error: cannot read {args.file}: {exc.strerror}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print(f"cipher-analyzer: error: {args.file} is not UTF-8 text", file=sys.stderr)
        return 2
    result = analyze(text, args.cipher, args.lang, args.top)
    print(_to_json(result) if args.json else format_report(result))
    return 0 if result.best is not None else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
