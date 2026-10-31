# Agente Especialista em Mineração de Dados

Agente construído sobre o **GitHub Copilot** (VS Code) que atua como um especialista em mineração de dados: decide como um analista experiente decidiria e **executa as análises no Weka de verdade**, sem inventar resultados.

Trabalho da disciplina CTI0303 Ciência de Dados para Negócios – Mestrado Profissional PPgCTI/UFRN.

## Como funciona

O agente tem três camadas:

| Camada | Arquivo | Função |
|---|---|---|
| Conhecimento | `conhecimento/manual_decisoes.md` | 81 regras de decisão de especialista, destiladas do livro *Introduction to Data Mining* (Tan, Steinbach, Kumar, 1ª ed.) e reescritas com palavras próprias |
| Ferramentas | `ferramentas/weka_runner.py` | Executa o Weka 3.8.7 pela linha de comando (resumo da base e comparação com a linha de base) e grava cada saída em `resultados/` com o comando exato |
| Ferramentas | `ferramentas/significancia.py` | Compara dois classificadores com o teste t pareado corrigido (Nadeau e Bengio, o mesmo do Weka Experimenter), em 10 repetições da validação cruzada de 10 partes |
| Raciocínio | `.github/agents/especialista-mineracao.agent.md` | Define o papel, as regras inegociáveis, o fluxo de trabalho e o formato da resposta do agente |

O livro em si **não está no repositório**, por respeito aos direitos autorais. O agente usa o conhecimento incorporado no manual, sem citá-lo.

## Regras principais do agente

- Nenhum número inventado: toda métrica vem da saída real do Weka.
- Avaliação por validação cruzada estratificada de 10 partes, semente 1; relata só o bloco de validação, nunca o desempenho no treino.
- Sempre compara com a linha de base. Com matriz de custo, a linha de base é a mais barata entre "aprovar todos" e "recusar todos"; um modelo mais caro que ela é declarado **pior que não ter modelo**.
- Em classes desbalanceadas, **para e pergunta** ao usuário qual erro custa mais e quantas vezes mais, antes de modelar.
- Define **uma métrica principal** antes de ver os resultados; nunca recall ou precisão sozinhos.
- Não declara um modelo melhor que outro sem o teste de significância; diferenças não significativas são **empate técnico**, e entre empatados prefere o mais simples.

## Validação das ferramentas

- **`weka_runner.py`:** as matrizes de confusão geradas pelo script foram comparadas com as do Weka Explorer (interface gráfica), com a mesma base e a mesma configuração. **Resultados idênticos.**
- **`significancia.py`:** três testes de aceite. (a) Cada registro é testado exatamente uma vez por repetição (soma das partes = tamanho da base). (b) Um classificador comparado consigo mesmo dá diferença zero e "empate técnico". (c) Os valores de p foram recalculados de forma independente a partir dos valores de t, e conferem. A ferramenta é reprodutível: duas execuções com as mesmas sementes deram resultados idênticos.

## Como o agente foi desenvolvido: testar, achar o erro, corrigir a regra

O agente foi testado três vezes na mesma tarefa (base `credit-g.arff`, 1.000 clientes de crédito, 30% maus pagadores). Cada resposta foi conferida contra as saídas do Weka. Cada erro encontrado virou uma regra nova no manual, e a tarefa foi repetida.

| Aspecto | v1 | v2 | v3 |
|---|---|---|---|
| Perguntou o custo dos erros antes de modelar? | Sim | **Não** | **Sim** |
| Métrica principal | Indefinida | Recall (inadequada: "recusar todos" tem recall 1,0) | **Custo total** |
| Linha de base com custo (700) | Sim | Não | **Sim** |
| Modelo pior que a linha de base (IBk, custo 868) | Não apontado | Não apontado | **Descartado como "pior que não ter modelo"** |
| Diagnóstico de sobreajuste | Errado (usou o acerto de 100% do IBk no treino, que é garantido por construção) | Correto | Correto |
| Teste de significância | Não rodou | Rodou, na métrica errada | **Rodou no custo: melhor modelo contra a linha de base e contra o segundo melhor** |
| Conclusão | "NaiveBayes mais promissor" | Cautelosa, mas sobre recall | **NaiveBayes supera a linha de base (p < 0,001); empate técnico com RandomForest (p = 0,137); prefere-se o NaiveBayes por ser mais simples** |

Correções no manual que saíram desses testes: R5.48 (duas linhas de base com custo), R5.49 (quando o acerto no treino não diz nada), R5.50 (empate técnico), R5.51 (uma métrica principal, nunca recall sozinho; correção de Bonferroni para as demais) e R5.52 (quais pares testar). As três respostas estão em `analises/`, **sem edição**, e as saídas correspondentes do Weka em `resultados/`.

**Limite conhecido:** as regras foram ajustadas olhando para a mesma base em que foram testadas. O desempenho do agente em bases diferentes ainda precisa ser verificado.

## Resultado da versão 3 — `credit-g.arff`

Matriz de custo informada pelo usuário: aprovar um mau pagador custa 5; recusar um bom pagador custa 1. Validação cruzada estratificada de 10 partes, semente 1.

| Modelo | Acurácia | Recall `bad` | Precisão `bad` | F1 `bad` | AUC | Custo total |
|---|---:|---:|---:|---:|---:|---:|
| Linha de base: aprovar todos (ZeroR) | 70,0% | 0,000 | — | — | 0,500 | 1.500 |
| Linha de base: recusar todos | 30,0% | 1,000 | 0,300 | 0,462 | 0,500 | **700** |
| J48 | 60,6% | 0,780 | 0,416 | 0,543 | 0,655 | 658 |
| **NaiveBayes** | 69,0% | 0,817 | 0,490 | 0,613 | 0,787 | **530** |
| IBk | 72,0% | 0,510 | 0,535 | 0,522 | 0,660 | 868 |
| SMO | 61,9% | 0,837 | 0,431 | 0,569 | 0,681 | 577 |
| RandomForest | 70,1% | 0,787 | 0,501 | 0,612 | 0,795 | 555 |

Todos os classificadores rodaram dentro do `CostSensitiveClassifier` do Weka com essa matriz. Teste de significância no custo (10 × 10 validações cruzadas): NaiveBayes contra "recusar todos", p = 0,000028; NaiveBayes contra RandomForest, p = 0,137 (empate técnico).

## Primeiro teste — `weather.nominal.arff`

Base de 14 registros, objetivo de **entender** os fatores associados a `play`. O J48 acertou 7 de 14 (50%) e o ZeroR, 9 de 14 (64,3%), com intervalos de confiança largos e sobrepostos (26,8%–73,2% e 38,8%–83,7%). Conclusão do agente: a árvore descreve os 14 casos, mas a base é pequena demais para regras confiáveis de previsão.

## Como executar

Requisitos: Java 8+, Weka 3.8.7, Python 3 com SciPy (Anaconda), VS Code com GitHub Copilot.

1. Ajuste o caminho do `weka.jar` no topo de `ferramentas/weka_runner.py`.
2. No chat do Copilot, selecione o agente **especialista-mineracao**.
3. Peça, por exemplo: *"Analise a base credit-g.arff. Quero prever quais clientes são maus pagadores."*

Uso direto das ferramentas:

```
python ferramentas/weka_runner.py resumo credit-g.arff
python ferramentas/weka_runner.py comparar credit-g.arff weka.classifiers.trees.J48 -C 0.25 -M 2
python ferramentas/significancia.py credit-g.arff --a weka.classifiers.bayes.NaiveBayes --b weka.classifiers.trees.RandomForest --custo "0 1; 5 0" --positiva bad --repeticoes 10
```

## Estado do projeto

- [x] Manual de decisões – Parte 1 (classificação, árvores, avaliação)
- [x] Manual de decisões – Parte 2 (técnicas alternativas, classes desbalanceadas, escolha entre algoritmos)
- [x] Camada Weka validada contra a interface gráfica
- [x] Ferramenta de teste de significância validada
- [x] Agente testado e corrigido em três rodadas na `credit-g`
- [ ] Teste em bases diferentes (ex.: `diabetes.arff`)
- [ ] Manual – Parte 3 (qualidade dos dados, pré-processamento, exploração)
- [ ] Manual – Partes 4 a 6 (associação, agrupamento, anomalias)
