"""Download do PDF mais recente do Boletim Focus — Banco Central do Brasil."""

from datetime import date, timedelta
from pathlib import Path

import urllib3
import requests

# O BCB usa certificado intermediário não presente no bundle padrão do requests;
# desabilitamos a verificação SSL e suprimimos o aviso resultante.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
SSL_VERIFY = False

# User-Agent de navegador para reduzir chances de bloqueio pelo servidor do BCB
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

# Padrão de URL oficial do Focus; a data vai no formato AAAAMMDD (sem hífens)
URL_TEMPLATE = "https://www.bcb.gov.br/content/focus/focus/R{data}.pdf"

# Número máximo de dias a recuar quando o PDF do dia não está disponível
MAX_TENTATIVAS = 7


def ultima_segunda(hoje: date) -> date:
    """Retorna a segunda-feira mais recente estritamente anterior a *hoje*.

    Se *hoje* já é segunda-feira, retrocede para a segunda da semana passada.

    Exemplos:
        hoje = seg 02/06 → retorna seg 26/05
        hoje = ter 03/06 → retorna seg 02/06
        hoje = dom 01/06 → retorna seg 26/05
    """
    # weekday(): 0 = segunda, 1 = terça, ..., 6 = domingo.
    # Quando hoje é segunda (0) recuamos uma semana inteira (7 dias);
    # nos demais casos recuamos tantos dias quantos forem necessários
    # para chegar à segunda imediatamente anterior.
    dias_a_recuar = 7 if hoje.weekday() == 0 else hoje.weekday()
    return hoje - timedelta(days=dias_a_recuar)


def baixar(dest: Path) -> tuple[date, Path]:
    """Baixa o PDF mais recente do Focus para a pasta *dest*.

    Parte da última segunda-feira e recua um dia por tentativa, cobrindo
    feriados, até MAX_TENTATIVAS. Antes de salvar, valida que a resposta
    começa com a assinatura de PDF ``%PDF``.

    Retorna:
        Tupla (data_da_publicacao, caminho_do_arquivo).

    Levanta:
        RuntimeError se nenhuma das tentativas produzir um PDF válido.
    """
    dest.mkdir(parents=True, exist_ok=True)

    # Ponto de partida: última segunda estritamente antes de hoje
    data_tentativa = ultima_segunda(date.today())

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        url = URL_TEMPLATE.format(data=data_tentativa.strftime("%Y%m%d"))
        print(f"  [{tentativa}/{MAX_TENTATIVAS}] GET {url}")

        try:
            resposta = requests.get(url, headers=HEADERS, timeout=30, verify=SSL_VERIFY)
        except requests.RequestException as exc:
            # Falha de rede — registra e tenta o dia anterior
            print(f"    erro de rede: {exc}")
            data_tentativa -= timedelta(days=1)
            continue

        if resposta.status_code != 200:
            # Arquivo inexistente nessa data — tenta o dia anterior
            print(f"    HTTP {resposta.status_code}")
            data_tentativa -= timedelta(days=1)
            continue

        # Valida a assinatura de PDF nos primeiros bytes
        if not resposta.content.startswith(b"%PDF"):
            print("    resposta não reconhecida como PDF (assinatura %PDF ausente)")
            data_tentativa -= timedelta(days=1)
            continue

        # PDF válido — persiste na pasta de destino com nome padronizado
        nome_arquivo = f"focus_{data_tentativa.strftime('%Y-%m-%d')}.pdf"
        caminho = dest / nome_arquivo
        caminho.write_bytes(resposta.content)
        print(f"    salvo em {caminho}")
        return data_tentativa, caminho

    raise RuntimeError(
        f"PDF do Focus não encontrado após {MAX_TENTATIVAS} tentativas "
        f"(início: {ultima_segunda(date.today()).isoformat()})."
    )


def main() -> None:
    """Baixa o Focus mais recente para data/ e exibe caminho e tamanho."""
    pasta_destino = Path(__file__).parent.parent / "data"

    print("Buscando o Boletim Focus mais recente...\n")
    data_pub, caminho = baixar(pasta_destino)

    tamanho_kb = caminho.stat().st_size / 1024
    print(f"\nPublicação : {data_pub.isoformat()}")
    print(f"Arquivo    : {caminho}")
    print(f"Tamanho    : {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
