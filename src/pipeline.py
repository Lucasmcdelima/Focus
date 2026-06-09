"""Orquestra download e extração do Boletim Focus."""

import argparse
from datetime import date
from pathlib import Path

from downloader import download_focus
from extractor import extract_and_save
from summarizer import summarize


def run(
    starting: date | None = None,
    force: bool = False,
    skip_summary: bool = False,
) -> tuple[Path, Path, Path | None]:
    """Executa download, extração e (opcionalmente) resumo.

    Retorna (pdf_path, txt_path, md_path).
    md_path é None quando skip_summary=True.
    """
    pdf_path = download_focus(starting=starting, force=force)
    txt_path = extract_and_save(pdf_path, force=force)
    md_path = None if skip_summary else summarize(txt_path, force=force)
    return pdf_path, txt_path, md_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline Focus BCB")
    parser.add_argument(
        "--date",
        metavar="AAAA-MM-DD",
        help="Data de referência (padrão: hoje)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescreve arquivos já existentes",
    )
    parser.add_argument(
        "--skip-summary",
        action="store_true",
        help="Pula a geração do resumo com a API do Claude",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    starting = date.fromisoformat(args.date) if args.date else None
    pdf_path, txt_path, md_path = run(
        starting=starting, force=args.force, skip_summary=args.skip_summary
    )
    print(f"\nPronto!\n  PDF   : {pdf_path}\n  Texto : {txt_path}")
    if md_path:
        print(f"  Resumo: {md_path}")
