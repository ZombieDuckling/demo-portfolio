#!/usr/bin/env python3
"""Validate the static demo portfolio before it is deployed.

The check intentionally uses only the Python standard library so GitHub Actions
and local contributors can run it without installing project dependencies.
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = sorted(ROOT.glob("*.html")) + sorted((ROOT / "demos").glob("*.html"))
REQUIRED_INDEX_LINKS = {
    "demos/claymorphic-spatial-ui.html",
    "demos/neumorphic-orbital-ui.html",
}


class StaticPortfolioParser(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.title_text = ""
        self._in_title = False
        self.links: list[tuple[int, str, str]] = []
        self.scripts = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value for key, value in attrs if value is not None}
        if tag == "title":
            self._in_title = True
        if tag == "script":
            self.scripts += 1
        for attr in ("href", "src"):
            value = attrs_dict.get(attr)
            if value:
                self.links.append((self.getpos()[0], attr, value))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_text += data


def is_external_or_special(link: str) -> bool:
    parsed = urlparse(link)
    return bool(parsed.scheme or parsed.netloc) or link.startswith(("#", "mailto:", "tel:", "data:"))


def resolve_local_link(source: Path, link: str) -> Path:
    without_fragment = link.split("#", 1)[0].split("?", 1)[0]
    return (source.parent / unquote(without_fragment)).resolve()


def assert_inside_root(path: Path) -> bool:
    try:
        path.relative_to(ROOT)
        return True
    except ValueError:
        return False


def validate_html(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    parser = StaticPortfolioParser(path)
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # pragma: no cover - defensive parse guard
        errors.append(f"{path.relative_to(ROOT)}: HTML parser failed: {exc}")
        return errors

    rel = path.relative_to(ROOT)
    if not re.search(r"<html\b[^>]*\blang=", text, re.IGNORECASE):
        errors.append(f"{rel}: missing <html lang=...>")
    if not re.search(r'<meta\s+name=["\']viewport["\']', text, re.IGNORECASE):
        errors.append(f"{rel}: missing responsive viewport meta tag")
    if not parser.title_text.strip():
        errors.append(f"{rel}: missing non-empty <title>")

    for line, attr, link in parser.links:
        if is_external_or_special(link):
            continue
        target = resolve_local_link(path, link)
        if not assert_inside_root(target):
            errors.append(f"{rel}:{line}: {attr} escapes repository root: {link}")
        elif not target.exists():
            errors.append(f"{rel}:{line}: missing local {attr} target: {link}")

    return errors


def main() -> int:
    errors: list[str] = []
    if not HTML_FILES:
        errors.append("No HTML files found to validate")

    for path in HTML_FILES:
        errors.extend(validate_html(path))

    index = ROOT / "index.html"
    if index.exists():
        index_text = index.read_text(encoding="utf-8")
        for link in sorted(REQUIRED_INDEX_LINKS):
            if link not in index_text:
                errors.append(f"index.html: missing launch link for {link}")

    if errors:
        print("Static portfolio validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(HTML_FILES)} HTML files and required demo links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
