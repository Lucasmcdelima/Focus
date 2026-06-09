"""Testes para src/downloader.py."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from downloader import MAX_BACKTRACK_DAYS, _pdf_path, _pdf_url, find_latest_focus


def test_pdf_url_format():
    d = date(2025, 1, 27)
    assert _pdf_url(d) == "https://www.bcb.gov.br/content/focus/focus/R20250127.pdf"


def test_pdf_path_format(tmp_path, monkeypatch):
    monkeypatch.setattr("downloader.DATA_DIR", tmp_path)
    d = date(2025, 1, 27)
    assert _pdf_path(d) == tmp_path / "focus_2025-01-27.pdf"


def _mock_head(status_codes: list[int]):
    """Retorna um mock de requests.head que responde com os status fornecidos em sequência."""
    responses = [MagicMock(status_code=code) for code in status_codes]
    mock = MagicMock(side_effect=responses)
    return mock


def test_find_latest_focus_first_day():
    """Encontra o PDF no próprio dia de referência."""
    with patch("downloader.requests.head", _mock_head([200])):
        found_date, url = find_latest_focus(date(2025, 1, 27))
    assert found_date == date(2025, 1, 27)
    assert "R20250127.pdf" in url


def test_find_latest_focus_backtrack():
    """Retrocede dias até achar o PDF (simula segunda feriado)."""
    # 404, 404, 200 — acha no 3º dia
    with patch("downloader.requests.head", _mock_head([404, 404, 200])):
        found_date, _ = find_latest_focus(date(2025, 1, 27))
    assert found_date == date(2025, 1, 25)


def test_find_latest_focus_not_found():
    """Levanta RuntimeError quando nenhum PDF é encontrado."""
    codes = [404] * (MAX_BACKTRACK_DAYS + 1)
    with patch("downloader.requests.head", _mock_head(codes)):
        with pytest.raises(RuntimeError, match="PDF do Focus não encontrado"):
            find_latest_focus(date(2025, 1, 27))


def test_download_focus_skips_existing(tmp_path, monkeypatch):
    """Não baixa se o arquivo já existe e force=False."""
    monkeypatch.setattr("downloader.DATA_DIR", tmp_path)

    # Cria o arquivo previamente
    existing = tmp_path / "focus_2025-01-27.pdf"
    existing.write_bytes(b"%PDF-dummy")

    with patch("downloader.find_latest_focus", return_value=(date(2025, 1, 27), "http://x")):
        with patch("downloader.requests.get") as mock_get:
            from downloader import download_focus
            result = download_focus(date(2025, 1, 27), force=False)

    mock_get.assert_not_called()
    assert result == existing
