# Boletim Focus — BCB

## Objetivo

Baixar o Boletim Focus do Banco Central do Brasil toda segunda-feira, extrair o texto e gerar um resumo executivo em markdown.

## Fonte

- Página oficial: https://www.bcb.gov.br/publicacoes/focus
- Padrão de URL do PDF: `https://www.bcb.gov.br/content/focus/focus/R{AAAAMMDD}.pdf`
  - Exemplo: `https://www.bcb.gov.br/content/focus/focus/R20250131.pdf`

## Convenções de nomenclatura

- Arquivos nomeados com a data de publicação: `focus_AAAA-MM-DD`
  - PDF baixado: `data/focus_AAAA-MM-DD.pdf`
  - Texto extraído: `data/focus_AAAA-MM-DD.txt`
  - Resumo gerado: `output/focus/focus_AAAA-MM-DD.md`

## Estrutura de pastas

```
.
├── src/                  # código-fonte principal
├── tests/                # testes automatizados
├── data/                 # PDFs e textos extraídos (não versionar PDFs)
├── output/
│   └── focus/            # resumos executivos em markdown
└── .github/
    └── workflows/        # pipelines de CI/CD e automação semanal
```

## Lógica de download

- O BCB publica o Focus toda **segunda-feira**.
- Quando a segunda-feira é feriado, a publicação ocorre na **terça-feira** (ou dia útil seguinte).
- O download deve tentar a data alvo e, em caso de 404, **retroceder dia a dia** até encontrar o PDF.
- Janela de retrocesso sugerida: até 4 dias corridos.

## Regras de extração e resumo

- **Nunca inventar números.** Toda mediana, projeção ou estatística citada no resumo deve estar presente no texto extraído do PDF.
- Toda mediana citada deve ser rastreável à fonte (seção e página, quando possível).
- O resumo deve ser objetivo e estruturado em markdown.

## Dependências esperadas

- `requests` ou `httpx` — download do PDF
- `pdfplumber` ou `pypdf` — extração de texto
- `anthropic` — geração do resumo via Claude API (etapa futura)

## Automação

- O workflow semanal deve rodar toda **segunda-feira** (cron: `0 12 * * 1`).
- Em caso de falha no download, retentar na terça (ou via rerun manual).
