"""
Source parser and text normalizer.
Extracts clean text and structural headings from HTML and PDF documents while
stripping navigation/footer boilerplate and standardizing whitespace.
"""

import io
import re
import unicodedata
from html.parser import HTMLParser
from typing import List, Optional, Tuple


class TextExtractorHTMLParser(HTMLParser):
    """Simple, dependency-free HTML parser that ignores script/style and extracts clean text."""

    def __init__(self):
        super().__init__()
        self._pieces: List[str] = []
        self._ignore = False
        self._title: Optional[str] = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "nav", "footer", "header", "noscript"):
            self._ignore = True
        elif tag_lower == "title":
            self._in_title = True
        elif tag_lower in ("h1", "h2", "h3", "h4", "p", "div", "li", "tr"):
            self._pieces.append("\n")

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "nav", "footer", "header", "noscript"):
            self._ignore = False
        elif tag_lower == "title":
            self._in_title = False
        elif tag_lower in ("h1", "h2", "h3", "h4", "p", "div", "li", "tr"):
            self._pieces.append("\n")

    def handle_data(self, data: str):
        if self._in_title and not self._title:
            self._title = data.strip()
        elif not self._ignore:
            self._pieces.append(data)

    def get_text(self) -> Tuple[str, Optional[str]]:
        return "".join(self._pieces), self._title


class SourceParser:
    """Parses and normalizes source content from HTML and PDF formats."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalizes unicode, strips control characters, and collapses repetitive whitespace
        while preserving paragraph and section breaks.
        """
        # Normalize Unicode characters (e.g. smart quotes, non-breaking spaces)
        text = unicodedata.normalize("NFKC", text)

        # Replace non-breaking spaces and tabs with standard space
        text = text.replace("\xa0", " ").replace("\t", " ")

        # Remove control characters except standard newlines
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Collapse 3 or more newlines into double newline (paragraph boundary)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Collapse horizontal whitespace
        lines = [re.sub(r" {2,}", " ", line).strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    @classmethod
    def parse_html(cls, html_bytes: bytes, encoding: str = "utf-8") -> Tuple[str, Optional[str]]:
        """
        Parses raw HTML bytes, returning (clean_text, page_title).
        """
        try:
            html_str = html_bytes.decode(encoding, errors="replace")
        except Exception:
            html_str = html_bytes.decode("latin-1", errors="replace")

        parser = TextExtractorHTMLParser()
        parser.feed(html_str)
        raw_text, title = parser.get_text()
        return cls.normalize_text(raw_text), title

    @classmethod
    def parse_pdf(cls, pdf_bytes: bytes) -> List[Tuple[int, str]]:
        """
        Extracts text from a PDF, returning a list of (page_number, page_text).
        Gracefully falls back if pypdf is not installed.
        """
        pages: List[Tuple[int, str]] = []
        try:
            import pypdf  # type: ignore

            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for idx, page in enumerate(reader.pages, start=1):
                extracted = page.extract_text() or ""
                normalized = cls.normalize_text(extracted)
                if normalized:
                    pages.append((idx, normalized))
        except ImportError:
            # Fallback for environments without pypdf
            normalized = cls.normalize_text(pdf_bytes.decode("utf-8", errors="ignore"))
            pages.append((1, normalized))
        except Exception as exc:
            # If PDF parsing fails, return empty or raw extract
            normalized = cls.normalize_text(pdf_bytes.decode("utf-8", errors="ignore"))
            if normalized:
                pages.append((1, normalized))

        return pages

