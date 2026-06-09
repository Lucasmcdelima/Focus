"""Extração de texto de PDFs do Boletim Focus."""

import argparse
import sys
from pathlib import Path

import pdfplumber

# Pasta padrão onde os PDFs são armazenados pelo baixar_focus.py
PASTA_DATA = Path(__file__).parent.parent / "data"


def extrair(pdf_path: Path) -> Path:
    """Extrai o texto de *pdf_path* e salva como .txt no mesmo diretório.

    Cada página é extraída individualmente e as páginas são unidas com
    uma linha em branco entre elas. O arquivo de saída usa a mesma
    base de nome do PDF, apenas com a extensão trocada para .txt.

    Retorna o caminho do arquivo .txt gerado.
    """
    txt_path = pdf_path.with_suffix(".txt")

    paginas: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            # extract_text retorna None para páginas sem texto detectável
            texto = pagina.extract_text(x_tolerance=2, y_tolerance=2)
            if texto:
                paginas.append(texto.strip())

    # Página em branco entre seções para preservar a estrutura visual
    conteudo = "\n\n".join(paginas)

    txt_path.write_text(conteudo, encoding="utf-8")
    return txt_path


def _pdf_mais_recente() -> Path | None:
    """Retorna o focus_*.pdf mais recente em PASTA_DATA, ou None."""
    candidatos = sorted(PASTA_DATA.glob("focus_*.pdf"))
    return candidatos[-1] if candidatos else None


def main() -> None:
    """Ponto de entrada: extrai texto de um PDF do Focus e salva como .txt."""
    parser = argparse.ArgumentParser(
        description="Extrai o texto de um PDF do Boletim Focus."
    )
    parser.add_argument(
        "--pdf",
        metavar="CAMINHO",
        help="PDF a processar. Omita para usar o mais recente em data/.",
    )
    args = parser.parse_args()

    # Resolve qual PDF usar
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"Erro: arquivo não encontrado: {pdf_path}", file=sys.stderr)
            sys.exit(1)
    else:
        pdf_path = _pdf_mais_recente()
        if pdf_path is None:
            # Nenhum PDF disponível — orienta o usuário
            print(
                "Nenhum PDF encontrado em data/.\n"
                "Baixe o Focus primeiro executando:\n"
                "    python src/baixar_focus.py",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Usando PDF mais recente: {pdf_path.name}")

    txt_path = extrair(pdf_path)

    tamanho_kb = txt_path.stat().st_size / 1024
    print(f"Texto salvo : {txt_path}")
    print(f"Tamanho     : {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
