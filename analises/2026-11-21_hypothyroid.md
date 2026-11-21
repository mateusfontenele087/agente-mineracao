# Triagem de hipotireoidismo — hypothyroid.arff — 21/11/2026

## Decisões combinadas com o usuário

- **Classe positiva:** `hypothyroid`, que junta os tipos compensado (194), primário (95) e secundário (2). Os outros 3.481 registros são `negative` (92,3%).
- **Custo:** deixar passar um doente (falso negativo) custa 10 vezes mais que um alarme falso (falso positivo). Matriz na ordem (`negative`, `hypothyroid`), com linhas = real e colunas = previsto: `[0 1; 10 0]`.
- **Métrica principal, definida antes de rodar os modelos:** custo total = FP + 10 × FN. Menor é melhor.
- **Linhas de base de custo:** prever tudo como negativo custa 291 × 10 = **2.910**; prever tudo como hipotireoidismo custa 3.481 × 1 = 3.481. A linha de base é **2.910**.

## Preparação

O script [2026-11-21_preparar_hypothyroid.py](2026-11-21_preparar_hypothyroid.py) gera três bases novas. A original não foi alterada.

| Passo | Motivo |
|---|---|
| Classe binária | É a pergunta da triagem: tem ou não tem hipotireoidismo. O tipo secundário tem só 2 casos, e nenhum modelo aprende uma classe assim. |
| Remover `TBG` e `TBG measured` | `TBG` está 100% ausente; `TBG measured` é constante. |
| Remover os outros 5 atributos `... measured` | Indicam se o exame foi **pedido**, não como está a tireoide. O TSH só falta em negativos (369 de 3.481), então o modelo aprenderia a decisão do médico. |
| Remover `hypopituitary` | Tem um único caso `t`. |
| `age = 455` vira `?` | Valor impossível. Não há outra informação para corrigir, então fica como ausente. |

Bases geradas:
- `dados/hypothyroid_bin.arff`: **análise principal** (3.772 registros, 291 positivos).
- `dados/hypothyroid_bin_sem_dup.arff`: cenário sem as 61 linhas duplicadas, todas negativas (3.711 registros).
- `dados/hypothyroid_bin_com_tsh.arff`: cenário só com quem tem TSH medido (3.403 registros).

Perfil da base original: [resultados/20261121_132621_perfil_hypothyroid.txt](../resultados/20261121_132621_perfil_hypothyroid.txt).

## Candidatos

Configuração de avaliação: validação cruzada estratificada de 10 partes, semente 1. Todos os candidatos rodaram dentro de `weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 10.0 0.0]"`, que repondera os dados de treino em cada parte. A exceção é o RF `-M`, que escolhe a classe de menor custo esperado. Foram testadas **7 configurações** ao todo, além do ZeroR. Por isso o melhor resultado tende a ser um pouco otimista.

Comando-modelo:
`python3 ferramentas/weka_runner.py comparar hypothyroid_bin.arff weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 10.0 0.0]" -W weka.classifiers.trees.J48 -- -C 0.25 -M 2`

| Modelo | Acurácia (IC 95%) | Kappa | Recall hip. | Precisão hip. | F1 hip. | AUC | Custo | Matriz (VN FP / FN VP) | Saída |
|---|---|---|---|---|---|---|---|---|---|
| ZeroR | 92,29% ± 0,85 | 0,000 | 0,000 | — | — | 0,498 | **2.910** | 3481 0 / 291 0 | |
| **J48** (C 0,25, M 2) | **99,42% ± 0,24** | 0,960 | 0,976 | 0,950 | 0,963 | 0,987 | **85** | 3466 15 / 7 284 | [arquivo](../resultados/20261121_132759_513069_classificador.txt) |
| RandomForest `-M` | 98,36% ± 0,41 | 0,894 | 0,993 | 0,828 | 0,903 | 0,988 | **80** | 3421 60 / 2 289 | [arquivo](../resultados/20261121_132918_922873_classificador.txt) |
| JRip | 99,20% ± 0,28 | 0,945 | 0,973 | 0,928 | 0,950 | 0,984 | 102 | 3459 22 / 8 283 | [arquivo](../resultados/20261121_132759_778624_classificador.txt) |
| RandomForest (reponderado) | 96,58% ± 0,58 | 0,707 | 0,581 | 0,960 | 0,724 | 0,986 | 1.227 | 3474 7 / 122 169 | [arquivo](../resultados/20261121_132759_660323_classificador.txt) |
| NaiveBayes `-K` | 91,54% ± 0,89 | 0,524 | 0,722 | 0,469 | 0,568 | 0,924 | 1.048 | 3243 238 / 81 210 | [arquivo](../resultados/20261121_132759_934708_classificador.txt) |
| NaiveBayes | 90,93% ± 0,92 | 0,442 | 0,567 | 0,433 | 0,491 | 0,887 | 1.476 | 3265 216 / 126 165 | [arquivo](../resultados/20261121_132759_442976_classificador.txt) |
| IBk (`-K 15 -X`, escolheu k = 1) | 89,10% ± 0,99 | 0,241 | 0,302 | 0,297 | 0,300 | 0,617 | 2.238 | 3273 208 / 203 88 | [arquivo](../resultados/20261121_132759_427038_classificador.txt) |

O IC 95% da acurácia usa a aproximação normal, calculada a partir da acurácia do Weka com n = 3.772.

Todos os modelos custam menos que a linha de base de 2.910. Nenhum foi descartado como "pior que não ter modelo".

## Significância (teste t pareado corrigido, 10 × 10 partes, só no custo)

Foram feitas 3 comparações com `ferramentas/significancia.py --sem-envelope`:

| Comparação | Custo médio por parte (A × B) | p | Conclusão | Relatório |
|---|---|---|---|---|
| RF `-M` × ZeroR | 7,29 × 291,0 | < 0,001 | RF `-M` melhor | [arquivo](../resultados/20261121_133938_778565_significancia.txt) |
| J48 × ZeroR | 5,87 × 291,0 | < 0,001 | J48 melhor | [arquivo](../resultados/20261121_134501_367064_significancia.txt) |
| RF `-M` × J48 | 7,29 × 5,87 | 0,454 | **empate técnico** | [arquivo](../resultados/20261121_134614_700694_significancia.txt) |

**Escolha: J48.** No custo, ele empata com o RandomForest `-M`. É mais simples e pode ser lido e auditado por quem vai usar a triagem.

## Interpretação da árvore (J48, base principal)

O caminho principal da árvore é:

- **TSH ≤ 6:** em geral **negativo**. A exceção é TT4 ≤ 49 com `referral source = other` (folha pequena, ver alertas).
- **TSH > 6, sem tiroxina, sem bócio, sem cirurgia de tireoide e TT4 ≤ 144:** **hipotireoidismo**. Esta folha cobre a grande maioria dos positivos.
- **TSH > 6 e já em uso de tiroxina:** só é hipotireoidismo se **FTI ≤ 62**. Com FTI acima disso, o tratamento parece estar controlando o quadro.
- **TSH > 6 e já operado da tireoide:** hipotireoidismo se TT4 ≤ 69.

As regras do JRip contam a mesma história. A primeira regra é TSH ≥ 6,1, sem tiroxina, sem cirurgia e TT4 ≤ 148.

Os pesos que aparecem nas folhas estão reponderados pelo custo. Não são contagens de pacientes.

## Sensibilidade (J48, mesma configuração)

| Base | Custo J48 (linha de base) | Recall | Precisão | Matriz | Saída |
|---|---|---|---|---|---|
| Principal | 85 (2.910) | 0,976 | 0,950 | 3466 15 / 7 284 | [arquivo](../resultados/20261121_132759_513069_classificador.txt) |
| Sem duplicatas | 64 (2.910) | 0,983 | 0,953 | 3406 14 / 5 286 | [arquivo](../resultados/20261121_134621_408892_classificador.txt) |
| Só com TSH medido | 47 (2.910) | 0,990 | 0,944 | 3095 17 / 3 288 | [arquivo](../resultados/20261121_134621_406402_classificador.txt) |

A conclusão não muda em nenhum cenário. As duplicatas não inflaram o resultado, e o desempenho não dependia da ausência do TSH.

## Alertas

1. **Sobreajuste:** não há sinal. O J48 acerta 99,68% no treino e 99,42% na validação, com 16 folhas.
2. **Folha suspeita:** "TSH ≤ 6, TT4 ≤ 49 e `referral source = other` → hipotireoidismo" depende da **origem do encaminhamento**, que é um atributo administrativo. Tem pouca base (cerca de 15 casos reponderados). Para uso real, convém revisar com um especialista clínico ou testar a árvore sem `referral source`.
3. **Os 7 falsos negativos** são os doentes que a triagem deixaria passar. Valem uma revisão caso a caso.
4. **Dados de 1987, de um único centro australiano.** Faixas de referência e práticas de exame mudaram. Antes de qualquer uso, o modelo precisa ser validado em dados atuais da população-alvo.
5. **Quem já toma tiroxina** (464 pacientes) foi mantido. A árvore trata esse grupo num ramo próprio.
6. **Não executado:** IBk com seleção de atributos (o IBk ficou muito atrás, provavelmente pelos atributos binários irrelevantes e pelos ausentes na distância); NaiveBayes `-D`; J48 com `-M` do `CostSensitiveClassifier`; teste do JRip contra o J48.
7. **Ferramenta alterada:** `ferramentas/significancia.py` ganhou a opção `--sem-envelope`. Com ela, a matriz de custo serve só para calcular o custo, e cada modelo roda exatamente como foi configurado. Sem a opção, o comportamento antigo continua igual.
