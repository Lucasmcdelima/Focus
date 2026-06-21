# Roteiro semanal — Resumo do Boletim Focus

Execute os passos abaixo em ordem. Interrompa imediatamente se qualquer
condição de parada for atingida e informe qual foi.

---

## Passo 1 — Localizar o arquivo de texto mais recente

Procure todos os arquivos que correspondam ao padrão `data/focus_*.txt`.

- Se não existir nenhum, **pare sem commitar o HTML** com a mensagem:
  > "Nenhum arquivo focus_*.txt encontrado em data/. Execute o pipeline de
  > download antes de rodar esta automação."

Selecione o arquivo com a data mais recente no nome.

---

## Passo 2 — Verificar o frescor do arquivo

Extraia a data do nome do arquivo (`focus_AAAA-MM-DD.txt`) e calcule a
diferença em relação à data de hoje.

| Diferença | Ação |
|---|---|
| 0 a 3 dias | Prosseguir normalmente. |
| 4 a 7 dias | Prosseguir, mas adicionar ao final do resumo gerado a nota: `> ⚠️ Texto com N dias — confirme se há edição mais recente.` |
| Mais de 7 dias | **Pare sem commitar o HTML** com a mensagem: `"Arquivo com mais de 7 dias (data: AAAA-MM-DD). Atualize o texto antes de gerar o resumo."` |

---

## Passo 3 — Sanity check do conteúdo

Leia o arquivo selecionado e verifique:

1. O texto tem **pelo menos 2 000 caracteres**.
2. O texto contém as três palavras-chave: **IPCA**, **Selic** e **PIB**
   (a presença dessas palavras confirma que o layout do documento não
   mudou e que os principais indicadores estão presentes).

Se qualquer uma dessas condições falhar, **pare sem commitar o HTML** com a mensagem:
> "Sanity check falhou em `<nome_do_arquivo>`: `<descrição do problema>`.
> O layout do documento pode ter mudado."

---

## Passo 4 — Gerar o resumo

Leia o texto completo e produza um documento markdown com as seções abaixo.

**Regra inviolável:** nunca invente números. Toda mediana, projeção ou
estatística citada deve estar literalmente presente no texto. Se um valor
não aparecer no texto, omita-o.

### Seção 1 — Resumo executivo (até 200 palavras)

Comece pelas medianas principais do mercado para o período de referência
(IPCA, Selic, PIB, câmbio — somente os que estiverem no texto). Em
seguida, descreva em linguagem direta o que o mercado espera para os
próximos meses. Encerre com uma frase sobre o tom geral das expectativas
(convergindo, estáveis, ou se deteriorando).

### Seção 2 — Três principais revisões da semana

Liste exatamente três revisões que se destacam no texto — movimentos
de alta ou baixa nas expectativas em relação à semana anterior, se o
texto trouxer essa comparação.

Para cada revisão, inclua:
- O indicador e os valores (de X% para Y%, por exemplo).
- Uma hipótese de motivo, introduzida com "Possível motivo:".
  A hipótese deve ser plausível e baseada no contexto macroeconômico
  implícito no texto; deixe claro que é uma inferência, não um fato
  afirmado pelo documento.

Se o texto não trouxer comparações com a semana anterior para três
indicadores distintos, liste apenas os que houver e explique a ausência.

---

## Passo 5 — Salvar o resultado

Salve o documento gerado em:

```
output/focus/focus_AAAA-MM-DD.md
```

onde `AAAA-MM-DD` é a data extraída do nome do arquivo de texto de entrada.

Crie o diretório `output/focus/` se ele não existir.

Confirme a gravação informando o caminho completo e o número de palavras
do documento gerado.

---

## Passo 6 — Publicar o HTML

Publique o HTML: `git add output/focus/focus_AAAA-MM-DD.html`, commit e
`git push` para `main`. É esse push que dispara o Action de envio
(`focus-enviar.yml`), que manda o e-mail via SMTP — você não cria rascunho
nem dispara nada à mão. Destinatário, remetente e senha ficam nos Secrets.

Se o `git push` falhar, **pare sem retentar** e informe o erro completo.
