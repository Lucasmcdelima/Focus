"""Download do Boletim Focus do Banco Central do Brasil."""

import requests
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BCB_URL = "https://www.bcb.gov.br/content/focus/focus/R{date}.pdf"
MAX_BACKTRACK_DAYS = 4


def _pdf_url(target: date) -> str:
    return BCB_URL.format(date=target.strftime("%Y%m%d"))


def _pdf_path(target: date) -> Path:
    return DATA_DIR / f"focus_{target.strftime('%Y-%m-%d')}.pdf"


def find_latest_focus(starting: date | None = None) -> tuple[date, str]:
    """Retorna (data_publicacao, url) do PDF mais recente a partir de `starting`.

    Retrocede dia a dia até MAX_BACKTRACK_DAYS caso receba 404.
    Levanta RuntimeError se não encontrar nenhum PDF no período.
    """
    if starting is None:
        starting = date.today()

    for days_back in range(MAX_BACKTRACK_DAYS + 1):
        target = starting - timedelta(days=days_back)
        url = _pdf_url(target)
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            return target, url

    raise RuntimeError(
        f"PDF do Focus não encontrado nos últimos {MAX_BACKTRACK_DAYS} dias "
        f"a partir de {starting.isoformat()}."
    )


def download_focus(starting: date | None = None, force: bool = False) -> Path:
    """Baixa o PDF do Focus e salva em data/.

    Retorna o caminho do arquivo salvo.
    Pula o download se o arquivo já existir (use force=True para sobrescrever).
    """
    pub_date, url = find_latest_focus(starting)
    dest = _pdf_path(pub_date)

    if dest.exists() and not force:
        print(f"[skip] {dest.name} já existe.")
        return dest

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[download] {url}")
    response = requests.get(url, timeout=60, stream=True)
    response.raise_for_status()

    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"[ok] Salvo em {dest}")
    return dest


if __name__ == "__main__":
    download_focus()
