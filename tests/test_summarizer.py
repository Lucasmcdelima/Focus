"""Testes para src/summarizer.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from summarizer import _output_path, summarize


def _fake_response(text: str):
    """Cria um mock de anthropic.Anthropic().messages.create()."""
    block = MagicMock()
    block.text = text

    usage = MagicMock()
    usage.input_tokens = 100
    usage.output_tokens = 50
    usage.cache_read_input_tokens = 0
    usage.cache_creation_input_tokens = 100

    response = MagicMock()
    response.content = [block]
    response.usage = usage
    return response


def test_output_path():
    txt = Path("data/focus_2025-01-27.txt")
    md = _output_path(txt)
    assert md.name == "focus_2025-01-27.md"
    assert "output" in str(md)


def test_summarize_creates_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr("summarizer.OUTPUT_DIR", tmp_path)

    txt = tmp_path / "focus_2025-01-27.txt"
    txt.write_text("IPCA mediana 4,5%\nSelic mediana 13,0%", encoding="utf-8")

    fake_md = "# Boletim Focus — 2025-01-27\n\n## Destaques\n- IPCA: 4,5%"
    fake_resp = _fake_response(fake_md)

    with patch("summarizer.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = fake_resp
        md_path = summarize(txt)

    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "Boletim Focus" in content


def test_summarize_skips_existing(tmp_path, monkeypatch):
    monkeypatch.setattr("summarizer.OUTPUT_DIR", tmp_path)

    txt = tmp_path / "focus_2025-01-27.txt"
    txt.write_text("conteúdo", encoding="utf-8")

    md = tmp_path / "focus_2025-01-27.md"
    md.write_text("# já existe", encoding="utf-8")

    with patch("summarizer.anthropic.Anthropic") as MockClient:
        summarize(txt, force=False)
        MockClient.assert_not_called()


def test_summarize_uses_correct_model(tmp_path, monkeypatch):
    monkeypatch.setattr("summarizer.OUTPUT_DIR", tmp_path)

    txt = tmp_path / "focus_2025-01-27.txt"
    txt.write_text("texto do focus", encoding="utf-8")

    fake_resp = _fake_response("# Resumo")

    with patch("summarizer.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = fake_resp
        summarize(txt)

    call_kwargs = MockClient.return_value.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-6"


def test_summarize_uses_cache_control(tmp_path, monkeypatch):
    monkeypatch.setattr("summarizer.OUTPUT_DIR", tmp_path)

    txt = tmp_path / "focus_2025-01-27.txt"
    txt.write_text("texto do focus", encoding="utf-8")

    fake_resp = _fake_response("# Resumo")

    with patch("summarizer.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = fake_resp
        summarize(txt)

    call_kwargs = MockClient.return_value.messages.create.call_args.kwargs
    system = call_kwargs["system"]
    assert isinstance(system, list)
    assert system[0]["cache_control"] == {"type": "ephemeral"}
