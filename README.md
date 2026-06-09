# Boletim Focus — BCB

Pipeline que baixa o Boletim Focus do Banco Central do Brasil, extrai o
texto do PDF e — numa automação agendada — aciona um agente de IA que lê
esse texto e gera um resumo executivo em markdown.

> Os scripts Python cuidam exclusivamente de baixar e extrair. O resumo é
> gerado pelo Claude lendo o `.txt` produzido. Nenhum número é inventado:
> o agente só cita medianas e projeções que estejam literalmente no documento.

---

## Estrutura

```
.
├── src/
│   ├── baixar_focus.py    # baixa o PDF do BCB; retrocede até 7 dias para cobrir feriados
│   ├── extrair_texto.py   # extrai texto do PDF página a página com pdfplumber
│   ├── downloader.py      # baixador usado pelo pipeline agendado
│   ├── extractor.py       # extrator usado pelo pipeline agendado
│   ├── summarizer.py      # gera o resumo via Claude API (claude-sonnet-4-6)
│   └── pipeline.py        # orquestra download + extração + resumo
│
├── tests/
│   ├── test_baixar_focus.py   # 5 testes offline + 1 marcado @network
│   ├── test_downloader.py
│   ├── test_extractor.py
│   └── test_summarizer.py
│
├── data/                  # PDFs baixados e arquivos .txt extraídos
├── output/focus/          # resumos em markdown (focus_AAAA-MM-DD.md)
│
├── .github/workflows/
│   └── focus.yml          # roda testes em todo push/PR; pipeline toda segunda-feira
│
├── demo.py                # baixa + extrai localmente em duas linhas
├── requirements.txt       # requests==2.32.3, pdfplumber==0.11.4, pytest==8.3.3
└── pytest.ini             # define o marker `network` e aponta testpaths = tests
```

---

## Como rodar localmente

```bash
python -m pip install -r requirements.txt
python demo.py
```

A flag `--abrir` abre o `.txt` gerado no navegador ao final:

```bash
python demo.py --abrir
```

O script encontra o boletim mais recente automaticamente: começa pela
última segunda-feira e recua um dia por tentativa (até sete) para cobrir
feriados.

---

## Testes

```bash
# todos os testes offline (padrão recomendado)
pytest

# equivalente explícito — exclui qualquer teste que faça chamada de rede
pytest -m "not network"

# apenas o teste de download real contra o BCB (requer internet)
pytest -m network -v
```

O marker `network` está declarado em `pytest.ini`. Testes sem essa marca
são puramente offline e podem rodar em qualquer ambiente, incluindo CI.

---

## Pipeline em duas etapas

O BCB bloqueia requisições vindas de IPs de provedores de nuvem (AWS,
GitHub etc.), o que impede o download direto dentro de um GitHub Action.
Por isso o fluxo foi dividido:

**Etapa 1 — download local**

Rode `python demo.py` na sua máquina e faça commit do `.txt` gerado:

```bash
python demo.py
git add data/
git commit -m "chore: Focus $(date +%Y-%m-%d)"
git push
```

**Etapa 2 — resumo no GitHub Action**

O workflow `focus.yml` roda toda segunda-feira às 14 h UTC. Ele lê o
`.txt` já commitado, chama `src/pipeline.py` (que aciona o Claude via
`ANTHROPIC_API_KEY`) e commita o `.md` gerado em `output/focus/`.

Em todo `push` e `pull_request` o mesmo workflow roda apenas o job de
testes — sem tocar no BCB nem consumir créditos da API.

Para disparar o pipeline manualmente: **Actions → Boletim Focus →
Run workflow** (é possível passar uma data específica ou forçar
reprocessamento).
