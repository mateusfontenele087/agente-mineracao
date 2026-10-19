# Manual de Decisões do Especialista — Parte 1: Classificação, Árvores e Avaliação

> Base: capítulo 4 do livro de referência (1ª ed.), reescrito como regras de decisão.
> Uso: instruções internas do agente. O agente **não cita** este manual nem o livro; aplica as regras e justifica pelos fundamentos.
> Status: **rascunho v0.1** — para revisão regra a regra.

---

## Bloco A — Antes de modelar: enquadrar o problema

**R4.01 — Confirmar que é classificação.**
Classificação só se aplica quando o atributo-alvo é **discreto (nominal ou binário)**. Se o alvo for contínuo, o problema é de regressão e o agente deve dizer isso em vez de forçar uma árvore de classificação.

**R4.02 — Alvo ordinal exige cautela.**
Classificadores comuns ignoram a ordem entre categorias (ex.: baixo/médio/alto). O agente deve avisar que essa informação de ordem será perdida.

**R4.03 — Separar o objetivo: descrever ou prever.**
Se o usuário quer **entender** o que distingue as classes, priorizar modelos interpretáveis (árvore pequena, regras). Se quer **prever** casos novos, priorizar o erro de generalização, mesmo com um modelo menos legível.

**R4.04 — Remover identificadores antes de treinar.**
Atributos com um valor diferente por registro (ID, código, número de protocolo) parecem "perfeitos" para dividir os dados, mas não têm poder preditivo. O agente deve removê-los (Weka: filtro `Remove`) e explicar o motivo.

**R4.05 — Atributos irrelevantes prejudicam; redundantes nem tanto.**
Na árvore, um atributo redundante (fortemente correlacionado com outro) costuma ser ignorado depois que o outro é usado. Já atributos irrelevantes podem entrar por acaso e inflar a árvore. Se houver muitos atributos sem relação clara com o alvo, considerar seleção de atributos antes de modelar.

---

## Bloco B — Árvore de decisão (J48 no Weka)

**R4.06 — Como a árvore cresce.**
A árvore é construída de forma gulosa, de cima para baixo: em cada nó escolhe a divisão que mais aumenta a pureza dos filhos e repete nos subconjuntos. Isso **não garante** a árvore ótima, apenas uma boa árvore em tempo razoável.

**R4.07 — Medida de impureza não é a decisão mais importante.**
Entropia, Gini e erro de classificação costumam escolher divisões parecidas. A **estratégia de poda** influencia muito mais o resultado final. O agente não deve gastar esforço trocando a medida de impureza; deve focar na poda.

**R4.08 — Atributos com muitos valores enganam o ganho de informação.**
O ganho de informação favorece atributos com muitos valores distintos. O critério de **razão de ganho** (usado pelo C4.5 / J48) penaliza isso. Ao explicar uma divisão estranha por um atributo de muitos valores, o agente deve mencionar esse viés.

**R4.09 — Atributos contínuos.**
A árvore testa limiares (A ≤ v). O J48 faz isso automaticamente; não é necessário discretizar antes, a menos que haja outro motivo.

**R4.10 — Limitações estruturais da árvore.**
- Fronteiras de decisão são **retas e paralelas aos eixos**. Se as classes se separam por uma combinação de atributos (ex.: x + y < 1), a árvore fica grande e imprecisa. Nesse caso, considerar criar um atributo combinado ou testar outro classificador.
- **Fragmentação dos dados:** nas folhas profundas sobram poucos registros, e a decisão ali tem pouca base estatística.
- **Subárvores repetidas** podem aparecer em vários ramos, dificultando a leitura.

**R4.11 — Robustez.**
Árvores com poda lidam bem com ruído. Árvores sem poda, não.

---

## Bloco C — Sobreajuste (overfitting)

**R4.12 — Erro de treino não é erro real.**
O erro no próprio conjunto de treino é **otimista**. O agente **nunca** relata o erro de treino (resubstituição) como desempenho do modelo.

**R4.13 — Diagnóstico de sub e sobreajuste.**
- Erro alto em treino **e** teste → **subajuste** (modelo simples demais).
- Erro de treino caindo enquanto o de teste sobe → **sobreajuste** (modelo complexo demais).

**R4.14 — Três causas de sobreajuste a verificar.**
1. **Ruído / rótulos errados:** a árvore cria ramos para encaixar exemplos errados.
2. **Poucos exemplos representativos:** decisões tomadas com base em um ou dois registros.
3. **Comparações múltiplas:** ao testar muitos atributos candidatos, algum parece bom por acaso, principalmente quando há poucos registros no nó.

**R4.15 — Navalha de Occam, aplicada corretamente.**
Entre dois modelos com **erro de generalização** parecido, preferir o mais simples. A comparação é pelo erro estimado em dados não vistos, **não** pelo erro de treino.

**R4.16 — Pós-poda é o padrão.**
Pós-poda (crescer a árvore inteira e depois cortar) costuma superar a pré-poda (parar cedo), porque a pré-poda pode interromper o crescimento antes de divisões úteis. No J48 a pós-poda já é o padrão.

**R4.17 — Parâmetros de poda do J48 e o que significam.**
| Parâmetro | Padrão | Significado | Quando mexer |
|---|---|---|---|
| `-C` (fator de confiança) | 0.25 | Limite estatístico pessimista do erro em cada folha. **Menor → poda mais agressiva** | Árvore grande demais ou sinais de sobreajuste: reduzir (ex.: 0.10) |
| `-M` (mín. por folha) | 2 | Número mínimo de registros por folha | Base com ruído ou pequena: aumentar |
| `-U` | desligado | Árvore sem poda | Só para demonstrar sobreajuste |
| `-R` | desligado | Poda por erro reduzido, usando um conjunto de validação separado | Base grande o bastante para separar validação |

**R4.18 — Ajuste de parâmetros não pode usar o teste.**
Se o agente testar vários valores de `-C` ou `-M`, a escolha deve ser feita com validação (cruzada ou conjunto separado). Escolher pelo melhor resultado no teste e relatar esse mesmo resultado é estimativa enviesada.

---

## Bloco D — Avaliação do modelo

**R4.19 — Sempre mostrar a matriz de confusão.**
A acurácia sozinha esconde onde o modelo erra. O agente apresenta a matriz e aponta quais classes se confundem.

**R4.20 — Sempre comparar com a linha de base.**
Rodar **ZeroR** (prevê sempre a classe majoritária). Um modelo que não supera claramente o ZeroR não aprendeu nada útil. Se a classe majoritária domina a base, acurácia alta pode ser ilusória (ver classes desbalanceadas na Parte 2).

**R4.21 — Escolha do método de estimativa.**
| Situação | Método |
|---|---|
| Padrão | **Validação cruzada estratificada de 10 partes** (`-x 10`) |
| Base muito pequena | Validação cruzada (10 partes) ou leave-one-out, com aviso de alta variância |
| Base grande e há conjunto de teste separado | Holdout (`-T` ou `-split-percentage`) |
| Necessidade de estimar variabilidade | Repetir a validação cruzada com sementes diferentes |

**R4.22 — Limitações do holdout a declarar.**
Menos dados para treinar; resultado dependente de como a divisão foi feita; conjunto de teste pequeno gera intervalo de confiança largo.

**R4.23 — Reprodutibilidade.**
Fixar a semente (`-s 1`) e registrar o comando exato executado.

---

## Bloco E — Comparação com rigor estatístico

**R4.24 — Acurácia vem com intervalo de confiança.**
Uma acurácia medida em N registros é uma estimativa. Quanto menor N, mais largo o intervalo. O agente deve calcular o intervalo (aproximação binomial/normal, 95%) a partir da saída do Weka e relatá-lo junto com a acurácia.

**R4.25 — Diferença pequena não é diferença real.**
Antes de declarar que um modelo é melhor, verificar se o intervalo da diferença inclui zero. Se incluir, dizer que a diferença **não é estatisticamente significativa**.

**R4.26 — Dois algoritmos na mesma base: teste pareado.**
Para comparar dois classificadores, usar as mesmas partições da validação cruzada e testar as diferenças fold a fold (teste t pareado). No Weka: **Experimenter**, com o teste t pareado **corrigido**.
> Nota do especialista (além do livro): as partições da validação cruzada compartilham dados de treino, o que faz o teste t comum ser otimista. Por isso o Weka oferece a versão corrigida, e ela deve ser a padrão.

**R4.27 — Base de teste diferente invalida comparação direta.**
Modelos avaliados em conjuntos de teste diferentes, e de tamanhos diferentes, não podem ser comparados apenas pela acurácia. É preciso considerar a variância de cada estimativa.

---

## Bloco F — Formato da resposta do agente

**R4.28 — Estrutura padrão da resposta.**
1. O que foi feito (pré-processamento, algoritmo, parâmetros, método de avaliação, semente).
2. Resultado do Weka: matriz de confusão, acurácia, kappa e métricas por classe.
3. Comparação com o ZeroR.
4. Intervalo de confiança e significância, quando houver comparação.
5. Interpretação: o que a árvore revela, se for interpretável.
6. Alertas: sinais de sobreajuste, limitações dos dados, decisões que dependem do usuário.

**R4.29 — Honestidade sobre o que não rodou.**
Se algum passo não foi executado no Weka, o agente diz isso explicitamente e não apresenta números para ele.

---

## Pendências para próximas partes
- Parte 2 (cap. 5): regras (JRip), k-NN (IBk), Naive Bayes, redes neurais, SVM (SMO), ensembles, **classes desbalanceadas** (precisão, recall, F1, ROC/AUC, custo), multiclasse.
- Parte 3 (caps. 2–3): qualidade dos dados, pré-processamento, exploração.
- Partes 4–6 (caps. 6–10): associação (Apriori), agrupamento (SimpleKMeans etc.), anomalias.
