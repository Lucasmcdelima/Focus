"""Envio do resumo HTML do Boletim Focus por e-mail via SMTP do Gmail."""

import argparse
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from html.parser import HTMLParser

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "focus"

# Credenciais lidas exclusivamente de variáveis de ambiente — nunca no código.
ENV_USER = "FOCUS_SMTP_USER"
ENV_PASSWORD = "FOCUS_SMTP_APP_PASSWORD"
ENV_DEST = "FOCUS_EMAIL_DEST"
ENV_BCC = "FOCUS_EMAIL_BCC"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def encontrar_html_mais_recente() -> Path:
    """Retorna o focus_*.html mais recente em output/focus/.

    Levanta FileNotFoundError se nenhum arquivo for encontrado.
    """
    candidatos = sorted(OUTPUT_DIR.glob("focus_*.html"))
    if not candidatos:
        raise FileNotFoundError(
            f"Nenhum arquivo focus_*.html encontrado em {OUTPUT_DIR}. "
            "Execute o pipeline para gerar o resumo HTML primeiro."
        )
    # sorted() em caminhos que seguem o padrão focus_AAAA-MM-DD.html
    # já ordena cronologicamente por nome.
    return candidatos[-1]


def _data_do_nome(html_path: Path) -> str:
    """Extrai 'AAAA-MM-DD' do nome focus_AAAA-MM-DD.html."""
    # stem = "focus_AAAA-MM-DD"
    return html_path.stem.replace("focus_", "")


def _html_para_texto(html: str) -> str:
    """Converte HTML simples em texto plano para o fallback da mensagem."""

    class _Stripper(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self._partes: list[str] = []

        def handle_data(self, data: str) -> None:
            stripped = data.strip()
            if stripped:
                self._partes.append(stripped)

        def get_text(self) -> str:
            return "\n".join(self._partes)

    stripper = _Stripper()
    stripper.feed(html)
    return stripper.get_text()


# ---------------------------------------------------------------------------
# Montagem da mensagem
# ---------------------------------------------------------------------------

def montar_mensagem(
    html_path: Path,
    remetente: str,
    destinatarios: list[str],
    bcc: list[str],
    assunto: str | None = None,
) -> EmailMessage:
    """Monta o e-mail multipart/alternative com corpo HTML e fallback texto."""
    data_str = _data_do_nome(html_path)
    assunto_final = assunto or f"Resumo Focus — {data_str}"

    html_body = html_path.read_text(encoding="utf-8")
    texto_body = _html_para_texto(html_body)

    msg = EmailMessage()
    msg["Subject"] = assunto_final
    msg["From"] = remetente
    msg["To"] = ", ".join(destinatarios)
    if bcc:
        # send_message() usa o cabeçalho BCC para entregar, mas o remove antes de enviar.
        msg["BCC"] = ", ".join(bcc)

    msg.set_content(texto_body)  # fallback texto plano
    msg.add_alternative(html_body, subtype="html")  # corpo principal HTML

    return msg


# ---------------------------------------------------------------------------
# Envio
# ---------------------------------------------------------------------------

def enviar(msg: EmailMessage, usuario: str, senha: str) -> None:
    """Conecta ao Gmail via SSL e envia a mensagem.

    Os destinatários (To, BCC) são lidos diretamente dos cabeçalhos de msg pelo
    send_message(), que também remove o BCC antes de entregar.
    """
    print(f"[email] Conectando em {SMTP_HOST}:{SMTP_PORT}…")
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.login(usuario, senha)
        smtp.send_message(msg)

    rcpts = ", ".join(filter(None, [msg["To"], msg["BCC"]]))
    print(f"[ok] E-mail enviado para: {rcpts}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Envia o resumo HTML do Boletim Focus por e-mail via Gmail SMTP."
    )
    parser.add_argument(
        "--html",
        metavar="ARQUIVO",
        help="Caminho do .html a enviar (padrão: focus_*.html mais recente em output/focus/)",
    )
    parser.add_argument(
        "--dest",
        metavar="EMAIL[,EMAIL…]",
        help=(
            "Destinatários separados por vírgula "
            f"(padrão: variável de ambiente {ENV_DEST})"
        ),
    )
    parser.add_argument(
        "--assunto",
        metavar="TEXTO",
        help='Assunto do e-mail (padrão: "Resumo Focus — AAAA-MM-DD")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Monta e exibe a mensagem sem enviar — não exige credenciais SMTP. "
            "Útil para testar a montagem do e-mail."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # --- Resolve o arquivo HTML ---
    if args.html:
        html_path = Path(args.html)
        if not html_path.exists():
            print(f"[erro] Arquivo não encontrado: {html_path}", file=sys.stderr)
            sys.exit(1)
    else:
        html_path = encontrar_html_mais_recente()

    print(f"[info] Arquivo: {html_path}")

    # --- Resolve os destinatários ---
    dest_raw = args.dest or os.environ.get(ENV_DEST, "")
    destinatarios = [e.strip() for e in dest_raw.split(",") if e.strip()]
    if not destinatarios:
        print(
            f"[erro] Nenhum destinatário informado. Use --dest ou defina {ENV_DEST}.",
            file=sys.stderr,
        )
        sys.exit(1)

    bcc_raw = os.environ.get(ENV_BCC, "")
    bcc = [e.strip() for e in bcc_raw.split(",") if e.strip()]

    # --- Dry-run: monta e exibe sem enviar (não exige credenciais) ---
    if args.dry_run:
        remetente_fake = os.environ.get(ENV_USER, "remetente@exemplo.com")
        msg = montar_mensagem(html_path, remetente_fake, destinatarios, bcc, args.assunto)
        print("\n--- Cabeçalhos ---")
        for chave in ("From", "To", "BCC", "Subject"):
            if msg[chave]:
                print(f"{chave}: {msg[chave]}")
        print("\n--- Corpo (texto plano) ---")
        parte_texto = msg.get_body(preferencelist=("plain",))
        if parte_texto:
            print(parte_texto.get_content())
        print("--- fim dry-run ---")
        return

    # --- Envio real: lê credenciais das variáveis de ambiente ---
    usuario = os.environ.get(ENV_USER, "").strip()
    senha = os.environ.get(ENV_PASSWORD, "").strip()

    if not usuario:
        print(f"[erro] Variável {ENV_USER!r} não definida.", file=sys.stderr)
        sys.exit(1)
    if not senha:
        print(f"[erro] Variável {ENV_PASSWORD!r} não definida.", file=sys.stderr)
        sys.exit(1)

    msg = montar_mensagem(html_path, usuario, destinatarios, bcc, args.assunto)
    enviar(msg, usuario, senha)


if __name__ == "__main__":
    main()
