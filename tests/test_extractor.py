"""Testes para src/extractor.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extractor import extract_and_save, extract_text


def _fake_pdf(pages: list[str]):
    """Cria um mock de pdfplumber que retorna as páginas fornecidas."""
    mock_pages = []
    for text in pages:
        page = MagicMock()
        page.extract_text.return_value = text
        mock_pages.append(page)

    pdf_ctx = MagicMock()
    pdf_ctx.__enter__ = MagicMock(return_value=MagicMock(pages=mock_pages))
    pdf_ctx.__exit__ = MagicMock(return_value=False)
    return pdf_ctx


def test_extract_text_joins_pages():
    fake = _fake_pdf(["Página 1", "Página 2", "Página 3"])
    with patch("extractor.pdfplumber.open", return_value=fake):
        result = extract_text(Path("dummy.pdf"))
    assert "Página 1" in result
    assert "Página 2" in result
    assert "Página 3" in result
    # páginas separadas por linha em branco
    assert "\n\n" in result


def test_extract_text_ignores_empty_pages():
    fake = _fake_pdf(["Conteúdo", None, "Mais conteúdo"])
    with patch("extractor.pdfplumber.open", return_value=fake):
        result = extract_text(Path("dummy.pdf"))
    assert "Conteúdo" in result
    assert "Mais conteúdo" in result


def test_extract_and_save_creates_txt(tmp_path):
    pdf = tmp_path / "focus_2025-01-27.pdf"
    pdf.write_bytes(b"dummy")

    fake = _fake_pdf(["Texto de teste do Focus"])
    with patch("extractor.pdfplumber.open", return_value=fake):
        txt_path = extract_and_save(pdf)

    assert txt_path == tmp_path / "focus_2025-01-27.txt"
    assert txt_path.exists()
    assert "Texto de teste do Focus" in txt_path.read_text(encoding="utf-8")


def test_extract_and_save_skips_existing(tmp_path):
    pdf = tmp_path / "focus_2025-01-27.pdf"
    pdf.write_bytes(b"dummy")
    txt = tmp_path / "focus_2025-01-27.txt"
    txt.write_text("já existe", encoding="utf-8")

    with patch("extractor.pdfplumber.open") as mock_open:
        result = extract_and_save(pdf, force=False)

    mock_open.assert_not_called()
    assert result == txt
