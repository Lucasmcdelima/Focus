"""Pipeline local: baixa o Boletim Focus e extrai o texto."""

import argparse
import sys
import webbrowser
from pathlib import Path

# Adiciona src/ ao path para que os módulos sejam encontrados sem instalação
sys.path.insert(0, str(Path(__file__).parent / "src"))

from baixar_focus import baixar
from extrair_texto import extrair

# Pasta onde o PDF e o .txt serão armazenados
PASTA_DATA = Path(__file__).parent / "data"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa o Focus e extrai o texto em sequência."
    )
    # Flag opcional: abre o .txt no navegador ao final
    parser.add_argument(
        "--abrir",
        action="store_true",
        help="Abre o arquivo .txt gerado no navegador padrão.",
    )
    args = parser.parse_args()

    # ── Passo 1: baixa o PDF ─────────────────────────────────────────────────
    data_pub, pdf_path = baixar(PASTA_DATA)
    tamanho_kb = pdf_path.stat().st_size / 1024
    print(f"[1/2] PDF baixado: {pdf_path.name} ({tamanho_kb:.1f} KB)")

    # ── Passo 2: extrai o texto ──────────────────────────────────────────────
    txt_path = extrair(pdf_path)
    print(f"[2/2] Texto extraído: {txt_path}")

    # Abre o .txt no navegador, se solicitado
    if args.abrir:
        webbrowser.open(txt_path.as_uri())


if __name__ == "__main__":
    main()
