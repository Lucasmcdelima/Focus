"""Testes para src/baixar_focus.py."""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

# Adiciona src/ ao path, como no demo.py
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from baixar_focus import baixar, ultima_segunda


# ── Testes offline: ultima_segunda ────────────────────────────────────────────


def test_ultima_segunda_quinta():
    # 05/06/2025 é quinta-feira; a segunda anterior é 02/06/2025
    resultado = ultima_segunda(date(2025, 6, 5))
    assert resultado == date(2025, 6, 2)
    assert resultado.weekday() == 0


def test_ultima_segunda_terca():
    # 03/06/2025 é terça-feira; a segunda anterior é 02/06/2025
    resultado = ultima_segunda(date(2025, 6, 3))
    assert resultado == date(2025, 6, 2)
    assert resultado.weekday() == 0


def test_ultima_segunda_quando_hoje_e_segunda():
    # 02/06/2025 é segunda; deve recuar uma semana inteira → 26/05/2025
    resultado = ultima_segunda(date(2025, 6, 2))
    assert resultado == date(2025, 5, 26)
    assert resultado.weekday() == 0
    # garante que o retorno é ESTRITAMENTE anterior à data dada
    assert resultado < date(2025, 6, 2)


def test_ultima_segunda_domingo():
    # 01/06/2025 é domingo; a segunda anterior é 26/05/2025
    resultado = ultima_segunda(date(2025, 6, 1))
    assert resultado == date(2025, 5, 26)
    assert resultado.weekday() == 0


def test_ultima_segunda_varredura_60_dias():
    # Para qualquer dia nos próximos 60 dias o retorno deve ser sempre uma
    # segunda-feira estritamente anterior à data de entrada.
    hoje = date.today()
    for delta in range(60):
        dia = hoje + timedelta(days=delta)
        resultado = ultima_segunda(dia)
        assert resultado.weekday() == 0, (
            f"{dia.isoformat()}: retornou {resultado.isoformat()} (não é segunda)"
        )
        assert resultado < dia, (
            f"{dia.isoformat()}: retorno {resultado.isoformat()} não é estritamente anterior"
        )


# ── Teste com rede: download real ─────────────────────────────────────────────


@pytest.mark.network
def test_baixar_download_real(tmp_path):
    """Faz o download real do Focus e valida o arquivo recebido."""
    data_pub, caminho = baixar(tmp_path)

    # arquivo foi criado em disco
    assert caminho.exists(), "arquivo não foi criado"

    # começa com a assinatura de PDF
    assert caminho.read_bytes()[:4] == b"%PDF", "arquivo não começa com %PDF"

    # tamanho mínimo razoável para um Boletim Focus
    assert caminho.stat().st_size > 50 * 1024, "arquivo menor que 50 KB"

    # nome do arquivo bate com a data de publicação
    assert caminho.name == f"focus_{data_pub.strftime('%Y-%m-%d')}.pdf"

    # data dentro da janela esperada: não no futuro, não mais de 14 dias atrás
    hoje = date.today()
    assert data_pub <= hoje, "data de publicação está no futuro"
    assert data_pub >= hoje - timedelta(days=14), (
        "data de publicação está mais de 14 dias no passado"
    )
