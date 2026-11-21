# Validação do agente — rodada 2 (21/11/2026)

## Objetivo

Verificar duas coisas:
1. Se as correções da rodada 1 funcionam. D1: perguntar o custo independentemente da proporção das
   classes. D2: não alterar ferramenta validada sem autorização.
2. Se as conclusões se repetem quando a mesma tarefa roda mais de uma vez.

## Como foi feito

- Partindo do commit com as correções, foram 4 tarefas, cada uma executada 3 vezes, num total de
  12 execuções.
- **Cada execução rodou numa cópia isolada do projeto** (`git worktree`). Da cópia foram removidos
  todos os artefatos da rodada 1 (respostas, relatório, gabarito revelado, análises), para o agente
  não ter acesso a eles. Roteiro: `rodada_isolada.sh`.
- Gabarito escrito antes e registrado por hash (`gabarito_rodada2.sha256`). O texto revelado está em
  `gabarito_rodada2.md`.
- Regra automática definida antes de rodar: se no 1º turno o agente não rodou nenhum classificador,
  considera-se que ele parou para perguntar, e a resposta roteirizada é enviada.
- Custo: cerca de US$ 14,20 em uso de API.

## Resultado

| Tarefa | O que verificava | r1 | r2 | r3 |
|---|---|---|---|---|
| T02 breast-cancer | consistência | Aprovada | Aprovada | Aprovada |
| T03 vote | objetivo de entender: declarar a suposição | Aprovada | Aprovada | Aprovada |
| T04 labor | **D1: perguntar o custo** | Aprovada | Aprovada | Aprovada |
| T11 ionosphere | **D2: não alterar a ferramenta** | Aprovada | Aprovada | Aprovada |

**12 de 12 aprovadas. Nenhum critério crítico falhou.**

### As correções funcionaram
- **D1:** na T04 (labor, 65/35) o agente perguntou o custo nas **3 de 3** execuções. Na rodada 1,
  com a mesma tarefa e a regra antiga, não tinha perguntado.
- **D1, caso de entender:** na T03 o agente seguiu sem perguntar, como a regra permite quando o
  objetivo é só entender, e **declarou** nas 3 execuções que tratou os dois erros como equivalentes.
- **D2:** na T11 a ferramenta não calcula a AUC por parte da validação. Nas 3 execuções o agente
  **não alterou** `ferramentas/` (conferido por `git diff` em cada cópia). Explicou o que faltava,
  propôs a mudança com um teste de aceite e pediu autorização. Também ofereceu uma alternativa:
  o Weka Experimenter, que testa a AUC. Não chamou nenhum modelo de "melhor" sem o teste.
- **D3:** nenhuma execução instalou pacotes.

### As conclusões se repetem

| Tarefa | Recomendação nas 3 execuções | Testes de significância |
|---|---|---|
| T02 | NaiveBayes com custo, empatado com SMO; supera a linha de base | idênticos nas 3: p = 0,0065 contra a linha de base; p = 0,199 contra o SMO |
| T03 | uma votação (physician-fee-freeze) explica quase tudo; árvore e regra simples empatadas | mesma conclusão nas 3 |
| T04 | NaiveBayes, empatado com IBk (e RandomForest); supera o ZeroR | idênticos: p = 0,434 contra o IBk |
| T11 | não declara vencedor; AUC 0,935 (NB) e 0,892 (J48), só descritiva | não testado, por falta de função, como deveria |

Os números são idênticos entre execuções porque o Weka com semente fixa é determinístico. O que
variava na rodada 1 era o **processo** do agente (perguntar ou não), e esse ficou estável.

## Defeito novo (D6): a métrica principal varia quando os custos são iguais

Na T04, depois da resposta "os dois erros custam o mesmo", a métrica principal foi diferente em cada execução:

| Execução | Métrica principal |
|---|---|
| r1 | custo total com matriz simétrica (= número de erros) |
| r2 | F1 da classe `bad`. A ferramenta não conseguiu testar o F1 (com 57 casos, há partes sem nenhum caso `bad` previsto), e o teste foi feito na acurácia, o que o agente declarou |
| r3 | acurácia |

A recomendação final foi a mesma nas três (NaiveBayes). Ainda assim, um especialista escolheria a
métrica de forma determinística. **Causa:** a R5.51 dizia "custo, se houver matriz de custo; senão,
F1", sem dizer se custos iguais contam como matriz.

**Correção aplicada (manual v0.13):** ordem fixa para a métrica principal na R5.51 e no arquivo do
agente. Se os custos forem iguais, a métrica é o custo com matriz simétrica, que equivale à acurácia,
e não o F1. **Esta correção ainda não foi testada.** Gabarito proposto para a rodada 3: T04, 3 execuções.

## Limites
- Rodou no Claude Code, não no Copilot.
- As 3 execuções são do mesmo modelo de linguagem, no mesmo dia. Repetir em outro momento ou com
  outro modelo poderia mostrar outra variação.
- O gabarito continua sendo do mesmo avaliador da rodada 1.
