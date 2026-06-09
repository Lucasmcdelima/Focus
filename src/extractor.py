"""Extração de texto do PDF do Boletim Focus."""

import pdfplumber
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def extract_text(pdf_path: Path) -> str:
    """Extrai todo o texto do PDF, página a página, e retorna como string única."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                pages.append(text.strip())
    return "\n\n".join(pages)


def extract_and_save(pdf_path: Path, force: bool = False) -> Path:
    """Extrai o texto do PDF e salva em data/ com o mesmo nome base e extensão .txt.

    Retorna o caminho do arquivo de texto salvo.
    Pula se o .txt já existir (use force=True para sobrescrever).
    """
    txt_path = pdf_path.with_suffix(".txt")

    if txt_path.exists() and not force:
        print(f"[skip] {txt_path.name} já existe.")
        return txt_path

    print(f"[extract] {pdf_path.name}")
    text = extract_text(pdf_path)

    txt_path.write_text(text, encoding="utf-8")
    print(f"[ok] Texto salvo em {txt_path}")
    return txt_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        # tenta o PDF mais recente em data/
        pdfs = sorted(DATA_DIR.glob("focus_*.pdf"))
        if not pdfs:
            print("Nenhum PDF encontrado em data/. Execute downloader.py primeiro.")
            sys.exit(1)
        pdf_path = pdfs[-1]
    else:
        pdf_path = Path(sys.argv[1])

    extract_and_save(pdf_path)
