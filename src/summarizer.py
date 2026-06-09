"""Geração de resumo executivo do Boletim Focus via Claude API."""

import anthropic
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "focus"

SYSTEM_PROMPT = """\
Você é um analista econômico especialista no Boletim Focus do Banco Central do Brasil.

Sua tarefa é gerar um **resumo executivo em markdown** a partir do texto extraído do PDF.

## Regras invioláveis

- **NUNCA invente números.** Todo número, mediana, projeção ou estatística deve estar \
literalmente presente no texto fornecido.
- **Toda mediana citada deve ser rastreável ao texto-fonte.** Antes de incluir qualquer valor, \
confirme que ele existe no texto. Se não estiver, omita — não estime, não arredonde, não infira.
- Não faça afirmações sobre o mercado ou a economia além do que o texto contém.

## Estrutura obrigatória do resumo

```
# Boletim Focus — AAAA-MM-DD

## Destaques
- (3 a 5 bullets com as principais expectativas do mercado)

## Indicadores Principais
| Indicador | Mediana | Período |
|-----------|---------|---------|
| IPCA | … | … |
| PIB | … | … |
| Selic (fim de ano) | … | … |
| Câmbio (USD/BRL) | … | … |

(inclua apenas indicadores cujas medianas estejam explicitamente no texto)

## Análise por Indicador
### IPCA
…
### PIB
…
### Selic
…
### Câmbio
…

---
*Fonte: Banco Central do Brasil — Boletim Focus*
```

Use linguagem objetiva, técnica e impessoal. Não inclua seções para indicadores ausentes no texto.\
"""


def _output_path(txt_path: Path) -> Path:
    stem = txt_path.stem  # "focus_AAAA-MM-DD"
    return OUTPUT_DIR / f"{stem}.md"


def summarize(txt_path: Path, force: bool = False) -> Path:
    """Gera resumo executivo em markdown e salva em output/focus/.

    Retorna o caminho do arquivo markdown gerado.
    Pula se o arquivo já existir (use force=True para sobrescrever).
    """
    md_path = _output_path(txt_path)

    if md_path.exists() and not force:
        print(f"[skip] {md_path.name} já existe.")
        return md_path

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[summarize] {txt_path.name}")
    text = txt_path.read_text(encoding="utf-8")
    date_str = txt_path.stem.replace("focus_", "")

    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Data de referência: {date_str}\n\n"
                    f"Texto do Boletim Focus:\n\n{text}"
                ),
            }
        ],
    )

    summary = response.content[0].text
    md_path.write_text(summary, encoding="utf-8")

    usage = response.usage
    print(f"[ok] Resumo salvo em {md_path}")
    print(
        f"     Tokens — input: {usage.input_tokens}, output: {usage.output_tokens}, "
        f"cache_read: {usage.cache_read_input_tokens}, "
        f"cache_write: {usage.cache_creation_input_tokens}"
    )

    return md_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        txts = sorted(DATA_DIR.glob("focus_*.txt"))
        if not txts:
            print("Nenhum .txt encontrado em data/. Execute o pipeline primeiro.")
            sys.exit(1)
        txt_path = txts[-1]
    else:
        txt_path = Path(sys.argv[1])

    summarize(txt_path)
