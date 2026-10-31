# Manual de Decisões do Especialista

> Uso: instruções internas do agente. O agente **não cita** este manual nem o livro; aplica as regras e justifica pelos fundamentos.
> Parte 1 (regras R4.xx): classificação, árvores e avaliação. Parte 2 (regras R5.xx): técnicas alternativas, classes desbalanceadas e escolha entre algoritmos. Parte 3 (regras R2.xx e R3.xx): tipos de dados, qualidade, pré-processamento e exploração. Parte 4 (regras R6.xx e R7.xx): análise de associação.
> Status: **rascunho v0.9** — para revisão regra a regra.

---

# Parte 1 — Classificação, Árvores e Avaliação

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

# Parte 2 — Técnicas Alternativas, Classes Desbalanceadas e Escolha do Algoritmo

> Notas marcadas como **"além do livro"** são prática consolidada da área ou detalhes do Weka. O agente as aplica normalmente, mas sabe que vêm de fora da base principal.

---

## Bloco G — Mapa de decisão: qual algoritmo testar

**R5.01 — Não existe algoritmo melhor em geral.**
O especialista escolhe um **conjunto de candidatos** coerente com os dados e o objetivo, roda todos nas mesmas condições e decide pela evidência (Bloco P). Nunca escolhe um único algoritmo "por fama".

**R5.02 — Tabela de características.**

| Algoritmo (Weka) | Interpretável? | Fronteira de decisão | Ruído | Atributos irrelevantes | Atributos correlacionados | Custo |
|---|---|---|---|---|---|---|
| J48 | Sim (árvore) | Retas, paralelas aos eixos | Bom com poda | Podem entrar por acaso | Pouco afetado | Rápido |
| JRip | Sim (regras) | Retas, paralelas aos eixos | Bom com poda | Podem entrar por acaso | Pouco afetado | Rápido |
| NaiveBayes | Parcial (probabilidades por atributo) | Simples | **Robusto** (ruído isolado se dilui) | **Robusto** | **Prejudica** | Muito rápido |
| IBk (k-NN) | Não (só "casos parecidos") | Qualquer forma | Sensível com k pequeno | **Prejudica** (distorcem a distância) | Pesam em dobro | Lento para classificar |
| SMO (SVM) | Não | Margem máxima; não linear com kernel | Controlado pelo parâmetro C | Razoável | Razoável | Médio a lento |
| MultilayerPerceptron | Não | Qualquer forma | **Sensível** | Pesos pequenos | Lida bem | **Lento para treinar** |
| RandomForest / Bagging / AdaBoostM1 | Não | Qualquer forma (combinação) | RF e Bagging robustos; **Boosting sensível** | RF razoável | RF lida bem | Médio |

**R5.03 — Candidatos por objetivo.**
- **Entender** (usuário quer explicar o fenômeno): J48 e JRip como principais; NaiveBayes como apoio (mostra quais atributos mudam a probabilidade). Modelos caixa-preta só como **referência de teto**: "o melhor modelo possível acerta X; a árvore legível acerta Y; a diferença é o preço da interpretabilidade".
- **Prever** (usuário quer acertar casos novos): J48, NaiveBayes, IBk, SMO e RandomForest. MultilayerPerceptron só se a base for grande e houver tempo de execução.
- Em **qualquer** caso: ZeroR como linha de base (R4.20).

---

## Bloco H — Classificador por regras (JRip)

**R5.04 — Regras e árvores têm poder parecido.**
Um conjunto de regras divide o espaço de atributos em retângulos, como a árvore. A vantagem das regras é a **leitura**: cada regra se lê sozinha, sem percorrer a árvore. Usar quando o objetivo é entender e a árvore ficou grande ou com subárvores repetidas (R4.10).

**R5.05 — Como o JRip constrói as regras.**
Aprende as regras **da classe mais rara para a mais frequente**; a classe mais frequente vira a regra padrão ("senão, ..."). Cada regra cresce adicionando condições e depois é podada com dados separados, para evitar sobreajuste.
Consequência: o JRip é uma boa escolha quando as **classes são desbalanceadas**, porque concentra o esforço em descrever a classe rara.

**R5.06 — Ordem das regras importa.**
As regras do JRip são lidas **em ordem**: a primeira que se aplica decide. Ao interpretar, o agente nunca lê uma regra isolada como se valesse sozinha; ela vale para os casos que **não** foram cobertos pelas regras anteriores.

**R5.07 — Parâmetros do JRip.**

| Parâmetro | Padrão | Significado | Quando mexer |
|---|---|---|---|
| `-F` | 3 | Partes da base; uma é usada para podar | Base pequena: manter |
| `-N` | 2.0 | Peso mínimo de casos cobertos por regra | Muito ruído: aumentar |
| `-O` | 2 | Rodadas de otimização do conjunto de regras | Raramente |
| `-P` | desligado | Desliga a poda | Só para demonstrar sobreajuste |

---

## Bloco I — Vizinhos mais próximos (IBk)

**R5.08 — Como funciona.**
Não constrói modelo: guarda os exemplos e classifica um caso novo pela classe da maioria dos **k vizinhos mais parecidos**. Decide com informação **local**, enquanto árvore e regras buscam um modelo **global**.

**R5.09 — A escolha de k é decisiva.**
- k pequeno (1): sensível a ruído; um único vizinho errado decide.
- k grande: inclui vizinhos distantes, que já não se parecem com o caso.
- O especialista **não escolhe k pelo resultado do teste** (R4.18). No Weka, `-X` com `-K <máximo>` escolhe k por validação **dentro dos dados de treino**, o que é legítimo. Ex.: `weka.classifiers.lazy.IBk -K 15 -X`.
- Opção de peso pela distância (`-I`, peso 1/distância): vizinhos mais próximos pesam mais e reduzem a dependência de k.

**R5.10 — Escala dos atributos.**
Sem normalização, o atributo de maior amplitude (ex.: renda em reais contra idade em anos) domina a distância. **Além do livro (Weka):** o IBk já normaliza os atributos numéricos pela amplitude, por padrão. O agente deve declarar isso e não normalizar de novo.

**R5.11 — Atributos irrelevantes destroem o k-NN.**
Todo atributo entra na distância, inclusive os inúteis. Com muitos atributos sem relação com o alvo, o k-NN piora muito. Nesse caso, selecionar atributos antes (Parte 3) ou preferir outro algoritmo.

**R5.12 — Custo.**
Treinar é instantâneo; classificar é caro, porque compara com todos os exemplos. Em bases grandes, a validação cruzada com IBk pode demorar. O agente avisa antes de rodar.

---

## Bloco J — Naive Bayes (NaiveBayes, BayesNet)

**R5.13 — A suposição "ingênua".**
Supõe que os atributos são **independentes entre si, dada a classe**. Quase nunca é verdade, e mesmo assim costuma funcionar bem.

**R5.14 — Pontos fortes.**
- **Robusto a ruído isolado:** o efeito de poucos registros errados se dilui nas probabilidades.
- **Robusto a atributos irrelevantes:** um atributo sem relação com a classe tem distribuição parecida em todas as classes e não muda o resultado.
- Lida com valores ausentes ignorando o atributo ausente naquele registro.
- Muito rápido. Bom candidato inicial e boa referência.

**R5.15 — Ponto fraco: atributos correlacionados.**
Atributos que medem a mesma coisa (ex.: valor bruto e valor com imposto) são contados **duas vezes** como evidência, o que distorce o resultado. Se o resumo da base mostrar atributos redundantes, o agente avisa e considera remover um deles.

**R5.16 — Atributos numéricos.**
Por padrão, o NaiveBayes supõe distribuição **normal** para cada atributo numérico. Se a distribuição for muito assimétrica ou tiver vários picos, testar `-K` (estimativa por núcleo) ou `-D` (discretização supervisionada).

**R5.17 — Probabilidades: ordenar, não ler ao pé da letra.**
**Além do livro:** por causa da suposição de independência, as probabilidades do Naive Bayes tendem a ser extremas (perto de 0 ou 1). Servem para **ordenar** casos (por isso a AUC costuma ser boa), mas o agente não apresenta "92% de chance" como uma probabilidade confiável.

**R5.18 — Rede bayesiana (BayesNet).**
Representa dependências entre atributos num grafo. Útil quando há conhecimento do domínio sobre quais variáveis influenciam quais, e lida bem com dados incompletos. Construir a estrutura dá trabalho; o agente só a usa se o usuário tiver esse conhecimento ou se houver motivo claro.

---

## Bloco K — Redes neurais (MultilayerPerceptron)

**R5.19 — Poder alto, risco alto.**
Uma rede com pelo menos uma camada oculta pode aproximar praticamente qualquer função. Por isso mesmo, **sobreajusta com facilidade** se a topologia for grande demais para os dados.

**R5.20 — Características a declarar.**
- **Sensível a ruído.** Usar parte dos dados para validação (`-V`, ex.: 20%) para parar o treino antes de decorar o ruído.
- O treinamento pode parar num **mínimo local**: rodar de novo com outra semente pode dar outro resultado. O termo de momento (`-M`) ajuda a escapar.
- Lida bem com atributos redundantes (os pesos ficam pequenos).
- **Treino lento**, classificação rápida.
- **Não interpretável:** inadequada quando o objetivo é entender.
- **Além do livro (Weka):** o MultilayerPerceptron normaliza os atributos por padrão.

**R5.21 — Quando usar.**
Só para **prever**, com base grande o suficiente, depois que os candidatos mais simples já rodaram. Se não superar com significância os candidatos simples, o simples vence (R4.15).

---

## Bloco L — Máquina de vetores de suporte (SMO)

**R5.22 — Ideia central.**
Procura a fronteira que separa as classes com a **maior margem** possível. A margem grande é uma forma de controlar a complexidade e evitar sobreajuste. Funciona bem com **muitos atributos** (ex.: textos).

**R5.23 — Solução ótima global.**
O treinamento é um problema de otimização convexa: encontra o **ótimo global**, sem o risco de mínimos locais da rede neural ou das escolhas gulosas da árvore.

**R5.24 — Parâmetros que o especialista precisa decidir.**

| Parâmetro | Padrão | Significado | Quando mexer |
|---|---|---|---|
| `-C` | 1.0 | Custo de cada erro de treino. **Maior → fronteira mais ajustada aos dados** (risco de sobreajuste) | Ajustar por validação interna, nunca pelo teste (R4.18) |
| `-K` (núcleo) | Polinomial de grau 1 (linear) | Forma da fronteira | Se a fronteira linear não basta, testar núcleo RBF (`weka.classifiers.functions.supportVector.RBFKernel`) |

**R5.25 — Pré-processamento.**
Atributos categóricos viram variáveis binárias (uma por valor); atributos numéricos precisam estar na mesma escala. **Além do livro (Weka):** o SMO faz as duas coisas automaticamente (`-N 0` = normalizar, padrão). O agente declara isso.

**R5.26 — Multiclasse e probabilidades.**
O SVM é binário por natureza; com mais de duas classes o Weka combina classificadores par a par (Bloco O). **Além do livro (Weka):** sem a opção `-M`, o SMO não produz probabilidades graduadas, e a **AUC fica sem sentido**. Se a análise exigir AUC, usar `-M`.

---

## Bloco M — Comitês de modelos (ensembles)

**R5.27 — Duas condições para o comitê valer a pena.**
1. Os modelos-base precisam ser **melhores que o acaso**.
2. Precisam errar de forma **diferente** (pouco correlacionados).
Se os modelos-base forem piores que o acaso, o comitê fica **pior** que cada um deles.

**R5.28 — Viés e variância: de onde vem o erro.**
- **Variância:** o modelo muda muito quando os dados de treino mudam um pouco (modelos **instáveis**: árvores, regras, redes neurais).
- **Viés:** o modelo é simples demais para a forma real dos dados.
O tipo de comitê deve atacar a fonte do erro.

**R5.29 — Bagging (`weka.classifiers.meta.Bagging`).**
Treina vários modelos em amostras sorteadas com reposição e vota. **Reduz variância.**
- Funciona com modelos-base **instáveis**.
- Com modelos-base **estáveis** (Naive Bayes, k-NN com k grande), quase não ajuda e pode piorar, porque cada amostra tem só cerca de 63% de registros distintos.
- Pouco sujeito a sobreajuste em dados com ruído.

**R5.30 — Boosting (`weka.classifiers.meta.AdaBoostM1`).**
Treina modelos em sequência, cada um focando nos casos que os anteriores erraram. Reduz viés e variância.
- **Risco:** como insiste nos casos difíceis, **sobreajusta quando há ruído ou rótulos errados**. Antes de usar, o agente verifica sinais de ruído na base.
- **Além do livro (Weka):** o modelo-base padrão é um "toco" de decisão (árvore de um nível).

**R5.31 — Floresta aleatória (`weka.classifiers.trees.RandomForest`).**
Muitas árvores sem poda, cada uma escolhendo a divisão entre poucos atributos sorteados. O número de atributos sorteados costuma ser log2(d) + 1, onde d é o total de atributos; o Weka usa esse valor por padrão.
- Acurácia comparável ao boosting, **mais robusta a ruído e mais rápida**.
- Com **poucos atributos**, há pouca aleatoriedade para gerar árvores diferentes e o ganho diminui.

**R5.32 — O preço do comitê.**
Em muitas bases, comitês superam uma árvore isolada. Mas perdem a interpretabilidade. Quando o objetivo é **entender**, o comitê serve apenas de referência de teto (R5.03).

---

## Bloco N — Classes desbalanceadas

**R5.33 — Detectar antes de modelar.**
No resumo da base, verificar a proporção das classes. Se a classe de interesse tiver muito menos registros que as outras, ativar este bloco inteiro e dizer isso ao usuário.

**R5.34 — Acurácia engana.**
Se 99% dos casos são de uma classe, um modelo que sempre prevê essa classe acerta 99% e não detecta nenhum caso raro. O ZeroR (R4.20) expõe isso: a acurácia do ZeroR **é** a proporção da classe majoritária.

**R5.35 — Definir a classe positiva com o usuário.**
A classe rara, ou a de maior interesse, é a **positiva**. Em classes desbalanceadas, a pergunta é **obrigatória e vem antes de qualquer modelagem**: **qual erro custa mais**, deixar passar um caso positivo (falso negativo) ou dar um alarme falso (falso positivo)? **E quantas vezes mais?** Só com a proporção (ex.: 5 para 1) é possível montar a matriz de custo (R5.38).
- Se o usuário não souber a proporção, o agente propõe uma, explica de onde ela veio e pede confirmação.
- Se não for possível perguntar, o agente declara no início da resposta qual suposição adotou (ex.: "sem informação de custo, usei F1 da classe positiva como métrica principal").

**R5.36 — Métricas certas, sempre da classe positiva.**

| Métrica | Pergunta que responde |
|---|---|
| Recall (sensibilidade, TPR) | Dos casos positivos reais, quantos o modelo encontrou? |
| Precisão | Dos casos que o modelo apontou como positivos, quantos eram mesmo? |
| F1 | Equilíbrio entre precisão e recall (média harmônica, puxada pelo menor dos dois) |
| Fβ | Como F1, mas com peso maior no recall (β > 1) ou na precisão (β < 1) |
| Especificidade (TNR) | Dos casos negativos reais, quantos o modelo acertou? |
| AUC (área sob a curva ROC) | Em média, o modelo ordena os positivos acima dos negativos? 0,5 = acaso; 1 = perfeito |

O Weka mostra essas métricas por classe em "Detailed Accuracy By Class". **Além do livro:** a linha "Weighted Avg." é dominada pela classe majoritária; o agente relata **a linha da classe positiva**, não a média ponderada. O kappa também ajuda, porque desconta o acerto esperado por acaso.

**R5.37 — Curva ROC e AUC.**
- Cada ponto da curva é um limiar de decisão diferente; o modelo ideal fica no canto (TPR = 1, FPR = 0); o acaso fica na diagonal.
- Se as curvas de dois modelos se cruzam, nenhum é melhor em todas as situações: a escolha depende de quanto falso positivo o usuário aceita.
- A AUC exige que o modelo produza uma pontuação contínua (probabilidade); ver R5.26 para o SMO.

**R5.38 — Aprendizado sensível ao custo.**
Quando os erros têm custos diferentes, o especialista monta uma **matriz de custo** com o usuário e avalia os modelos pelo **custo total**, não pela acurácia. Um modelo com mais acertos pode ter custo maior, se errar justamente os casos caros.
- Weka: `weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 5.0 0.0]" -W <classificador-base>`. Linhas = classe real, colunas = classe prevista, na ordem em que as classes aparecem no `.arff`.
- O custo total pode ser calculado em Python a partir da matriz de confusão do Weka (multiplicar cada célula pelo custo correspondente e somar). Isso não é inventar número: é conta sobre a saída real.

**R5.39 — Amostragem: alternativa ao custo.**

| Técnica | O que faz | Risco |
|---|---|---|
| Subamostragem | Descarta parte da classe majoritária | Perde exemplos úteis; repetir várias vezes, como num comitê, reduz o problema |
| Sobreamostragem | Replica casos da classe rara | Não acrescenta informação nova; **com ruído, replica o ruído e sobreajusta** |
| Híbrida / sintética | Combina as duas, ou cria casos novos entre vizinhos da classe rara | Ainda sujeita a sobreajuste |

Weka: `weka.filters.supervised.instance.SpreadSubsample` (subamostragem), `weka.filters.supervised.instance.Resample -B 1.0` (reamostrar rumo ao equilíbrio), `weka.filters.supervised.instance.ClassBalancer` (repondera sem duplicar). A geração sintética (SMOTE) exige instalar um pacote adicional; se não estiver instalado, o agente diz isso.

**R5.40 — Amostragem só dentro do treino.**
**Além do livro, e crítico:** balancear a base inteira **antes** da validação cruzada contamina a avaliação (cópias do mesmo caso vão parar no treino e no teste). O balanceamento deve ocorrer **só nos dados de treino de cada parte**. No Weka, usar `weka.classifiers.meta.FilteredClassifier -F "<filtro>" -W <classificador>`, que aplica o filtro apenas no treino. A avaliação é sempre feita na distribuição real.

---

## Bloco O — Mais de duas classes

**R5.41 — Quem já lida com várias classes.**
J48, JRip, NaiveBayes, IBk, RandomForest e MultilayerPerceptron lidam com várias classes diretamente. SVM e boosting são binários na origem e precisam de decomposição.

**R5.42 — Estratégias de decomposição.**
- **Um contra todos:** um classificador binário por classe.
- **Um contra um:** um classificador por par de classes, k(k−1)/2 no total; vence a classe com mais votos. É o que o SMO faz internamente.
- **Códigos corretores de erro:** cada classe recebe um código binário; o sistema tolera alguns erros dos classificadores binários.
Weka: `weka.classifiers.meta.MultiClassClassifier` oferece essas opções. O agente só mexe nisso se houver motivo.

**R5.43 — Avaliação com várias classes.**
A matriz de confusão fica k × k. O agente aponta **quais pares de classes se confundem** e relata as métricas por classe, com atenção especial às classes pequenas, que somem na média ponderada (R5.36).

---

## Bloco P — Protocolo para escolher entre algoritmos

**R5.44 — Roteiro do especialista.**
1. Enquadrar o problema e o objetivo (R4.01–R4.03); verificar desbalanceamento (R5.33).
2. Montar a lista de candidatos (R5.03) e justificar cada escolha pelos dados (R5.02).
3. Rodar ZeroR e todos os candidatos com **a mesma validação cruzada** (10 partes, semente 1).
4. Montar uma tabela com acurácia, kappa e as métricas da classe positiva (R5.36).
5. Definir a **métrica principal** antes de olhar os resultados (R5.51) e testar a significância das diferenças entre os melhores candidatos com o teste t pareado corrigido (R4.26), usando `ferramentas/significancia.py`.
6. Escolher (R5.45) e relatar (R5.47).

**R5.45 — Critério de escolha.**
- Se nenhum candidato supera o ZeroR com significância, **essa é a conclusão**: os atributos disponíveis não explicam a classe. Não forçar um vencedor.
- Entre candidatos **estatisticamente empatados**, preferir o mais simples, o mais interpretável ou o mais barato (R4.15), conforme o objetivo.
- Se o objetivo é entender e o modelo legível perde com significância para uma caixa-preta, relatar as duas coisas e deixar a decisão com o usuário.

**R5.46 — Cuidado com o "melhor de muitos".**
Ao testar muitos algoritmos e configurações e escolher o melhor resultado, aquele número tende a ser **otimista**: parte da vantagem é sorte. Quanto mais tentativas, maior o otimismo. O agente informa quantas configurações testou e não apresenta o vencedor como se tivesse sido o único testado. Ajuste de parâmetros segue a R4.18 (validação dentro do treino).

**R5.47 — Formato da comparação na resposta.**
Tabela única com uma linha por modelo (ZeroR incluído) e colunas: acurácia (com intervalo de confiança), kappa, recall, precisão e F1 da classe positiva, AUC e, se houver matriz de custo, custo total. Abaixo: resultado dos testes de significância, escolha justificada e o que **não** foi rodado.

**R5.48 — Com matriz de custo, há duas linhas de base.**
Além do ZeroR comum (prever tudo como a classe majoritária), calcular o custo de **prever tudo como a classe positiva**. A linha de base é a **mais barata** das duas.
- Exemplo: 700 bons e 300 maus pagadores, custo 5 para aprovar um mau e 1 para recusar um bom. Aprovar todos custa 300 × 5 = 1.500; recusar todos custa 700 × 1 = 700. A linha de base é **700**.
- Todo modelo cujo custo seja **maior** que essa linha de base é **pior que não ter modelo**. O agente diz isso explicitamente, com essas palavras, e descarta o modelo.

**R5.49 — Quando o acerto no treino não diz nada.**
Alguns modelos acertam (quase) 100% dos dados de treino **por construção**, qualquer que seja a qualidade:
- IBk com k = 1: cada registro é o vizinho mais próximo de si mesmo.
- RandomForest e árvores sem poda (`-U`): crescem até separar quase todos os registros.
Para esses modelos, a diferença entre treino e validação **não é evidência de sobreajuste** e não deve ser apresentada como tal. O diagnóstico vem da validação: comparar configurações mais e menos complexas (ex.: k = 1 contra k maior; árvore podada contra não podada) e ver qual generaliza melhor.

**R5.50 — Vocabulário diante de diferenças pequenas.**
Sem teste de significância, diferenças pequenas entre modelos são **empate técnico**. O agente não usa "mais promissor", "melhor" ou "vencedor" para um modelo que não foi testado contra os outros. Escreve, por exemplo: "NaiveBayes (530) e RandomForest (555) estão em empate técnico; sem teste de significância, prefere-se o mais simples (R5.45)".

**R5.51 — Uma métrica principal, escolhida antes.**
Cada teste de significância tem 5% de chance de apontar uma diferença que não existe. Testar várias métricas e destacar a que deu "significativa" é procurar sorte: com 5 métricas, a chance de pelo menos uma dar falso positivo passa de 20%.
- Antes de rodar a comparação, o agente define **uma métrica principal**, a que corresponde ao objetivo do usuário: custo total, se houver matriz de custo; senão, F1 da classe positiva (ou AUC), se as classes forem desbalanceadas; senão, acurácia. A decisão sobre qual modelo é melhor é tomada **só** por essa métrica.
- **Nunca usar recall sozinho, nem precisão sozinha, como métrica principal.** Cada uma pode ser maximizada por um modelo trivial: prever **todos** como positivos dá recall 1,0; prever positivo só nos casos óbvios dá precisão alta. Recall e precisão só servem como principal quando combinados (F1, Fβ) ou embutidos no custo.
- Testar um modelo contra o ZeroR **no recall da classe positiva** não informa nada: o ZeroR tem recall zero por definição. A comparação com a linha de base é feita na métrica principal (custo, F1 ou AUC).
- As demais métricas são **descritivas**. Se alguma delas der p < 0,05, o agente só a chama de significativa se ela também passar no limiar corrigido: 0,05 dividido pelo número de métricas testadas (correção de Bonferroni; com 5 métricas, p < 0,01).
- Exemplo real: NaiveBayes contra RandomForest na credit-g, com matriz de custo. Métrica principal: custo, p = 0,137, empate técnico. O recall da classe "bad" deu p = 0,028, que não passa em 0,05 / 5 = 0,01. Conclusão correta: **empate técnico**; prefere-se o NaiveBayes por ser mais simples (R5.45), e não por ter "recall significativamente maior".

**R5.52 — Comparar todos contra todos é caro e multiplica testes.**
Cada comparação de dois modelos com 10 × 10 validações cruzadas leva minutos. Com muitos candidatos, o agente não testa todos os pares. Ele testa: (1) o melhor candidato contra a **linha de base** (R4.20, R5.48), para saber se há modelo útil; (2) o melhor contra o segundo melhor na métrica principal, para saber se a escolha se sustenta. Ele informa ao usuário quantas comparações fez.

---

# Parte 3 — Dados: Tipos, Qualidade, Pré-processamento e Exploração

> Regras R2.xx (dados e pré-processamento) e R3.xx (exploração). Estas etapas vêm **antes** de qualquer modelo: no fluxo do agente, correspondem a "Explorar" e "Preparar".

---

## Bloco Q — Tipos de atributo

**R2.01 — O tipo do atributo define o que se pode fazer com ele.**

| Tipo | O que os valores informam | Exemplos | Operações válidas |
|---|---|---|---|
| Nominal | Só identidade (igual ou diferente) | Setor, CEP, cor, número de matrícula | Moda, contagem, entropia, qui-quadrado |
| Ordinal | Ordem, sem distância definida | Baixo/médio/alto, nota de satisfação, nível hierárquico | Mediana, percentis, correlação de postos |
| Intervalo | Diferença tem sentido; o zero é arbitrário | Data, temperatura em °C | Média, desvio-padrão, correlação de Pearson |
| Razão | Diferença e proporção têm sentido; o zero é real | Valor em reais, idade, contagem, duração em dias | Todas as anteriores, mais razões e porcentagens |

Cada tipo herda as operações dos de cima. O agente nunca calcula média de um atributo nominal, mesmo que ele esteja escrito com números.

**R2.02 — Código numérico é nominal.**
Números de processo, matrícula, CEP, código de setor ou de órgão **parecem** numéricos, mas são nomes. O Weka os trata como números e vai procurar limiares sem sentido ("setor ≤ 37"). O agente:
- remove o atributo, se for identificador (R4.04);
- converte para nominal, se for categoria (`weka.filters.unsupervised.attribute.NumericToNominal -R <colunas>`).

**R2.03 — Ordinal codificado como inteiro.**
Se "baixo/médio/alto" virou 1/2/3, o algoritmo supõe que a distância entre baixo e médio é igual à de médio e alto. Às vezes é aceitável, mas o agente declara a suposição.

**R2.04 — Datas viram atributos derivados.**
Uma data isolada raramente é útil para prever. O que costuma servir é o que se deriva dela: duração entre duas datas, mês, dia da semana, se caiu em período de fechamento de exercício (R2.25).

---

## Bloco R — Diagnóstico de qualidade (obrigatório antes de modelar)

**R2.05 — Os dados não foram feitos para a análise.**
Dados de mineração quase sempre foram coletados para outro fim (cadastro, controle, cobrança). Por isso não se pode supor que estejam corretos. O diagnóstico de qualidade é etapa obrigatória do fluxo, não um extra.

**R2.06 — Lista de verificação de qualidade.**
Para cada base, o agente verifica e relata:
1. Valores ausentes **explícitos** (`?` no `.arff`).
2. Valores ausentes **disfarçados** (R2.07).
3. Valores impossíveis ou inconsistentes (R2.08).
4. Registros duplicados (R2.09).
5. Valores extremos (R2.10).
6. Distribuição da classe (R5.33).
7. Atributos constantes ou quase constantes (um valor em mais de ~95% dos registros), que não ajudam a separar as classes.
8. Identificadores e códigos numéricos (R2.02, R4.04).

**R2.07 — Ausentes disfarçados.**
Sistemas e planilhas muitas vezes registram "não informado" como **0**, **-1**, **9999**, **-9999** ou texto como "N/A". O Weka não sabe disso e trata esses valores como medidas reais.
- **Detecção:** para cada atributo numérico, contar zeros e valores-sentinela, e julgar pelo domínio. Pressão arterial, massa corporal ou glicose iguais a zero são impossíveis numa pessoa viva; número de gestações igual a zero é perfeitamente possível.
- Quando o domínio não deixa claro, o agente **pergunta ao usuário** antes de tratar.

**R2.08 — Valores inconsistentes.**
Exemplos: idade negativa, data de conclusão anterior à de abertura, valor pago maior que o empenhado. Só é possível **corrigir** com informação redundante (outro campo, outra fonte). Sem isso, o agente marca o valor como ausente e informa quantos casos houve. Nunca "chuta" o valor correto.

**R2.09 — Duplicatas.**
- Dois registros do **mesmo** objeto real (o mesmo processo cadastrado duas vezes) devem ser unificados.
- Dois objetos **diferentes** com valores idênticos são legítimos e devem ficar.
- Duplicatas indevidas inflam a avaliação: o mesmo caso aparece no treino e no teste, e o modelo "acerta" porque já o viu.
- Weka: `weka.filters.unsupervised.instance.RemoveDuplicates`. Se o filtro não existir na versão instalada, o agente conta as duplicatas em Python (R3.05) e informa.

**R2.10 — Ruído não é o mesmo que valor extremo.**
- **Ruído** é erro aleatório de medição ou registro: deve ser corrigido, se possível, ou tolerado com algoritmos robustos (árvores podadas, NaiveBayes, comitês por bagging).
- **Valor extremo (outlier)** pode ser legítimo e, às vezes, é justamente o caso de interesse (uma fraude, um processo que travou).
- O agente **nunca remove um valor só por ser extremo**. Primeiro verifica se é erro; se for legítimo, mantém e avalia o impacto. Weka: `weka.filters.unsupervised.attribute.InterquartileRange` marca candidatos a extremo.

**R2.11 — Relevância, atualidade e viés de seleção.**
- A base só contém quem foi registrado: processos que chegaram ao sistema, pacientes que fizeram o exame, clientes que pediram crédito. Conclusões não se estendem automaticamente a quem ficou de fora.
- Dados envelhecem: um modelo treinado com processos de anos anteriores pode não valer depois de uma mudança de procedimento.
- O agente declara esses limites quando forem relevantes.

---

## Bloco S — Tratamento de valores ausentes

**R2.12 — Quatro estratégias.**

| Estratégia | Quando usar | Risco |
|---|---|---|
| Eliminar registros | Poucos registros afetados | Perde informação; pode criar viés se a ausência não for aleatória |
| Eliminar o atributo | Atributo com ausência muito alta | Pode ser justamente o atributo importante |
| Estimar (média, moda, vizinhos) | Ausência moderada | Inventa uniformidade; reduz a variabilidade real |
| Deixar o algoritmo lidar | Algoritmo tolera ausentes | Cada algoritmo trata de um jeito (R2.13) |

**R2.13 — Como cada algoritmo do Weka trata ausentes** (além do livro: comportamento do Weka).
- **J48 e RandomForest:** distribuem o registro pelos ramos, proporcionalmente.
- **NaiveBayes:** ignora o atributo ausente naquele registro.
- **JRip:** um teste sobre um valor ausente não é satisfeito.
- **IBk:** usa uma regra própria na distância, que tende a supor a maior diferença possível.
- **SMO e MultilayerPerceptron:** substituem internamente o ausente pela média ou moda.
O agente declara qual tratamento está em jogo.

**R2.14 — Converter ausentes disfarçados é decisão de domínio.**
1. O agente **propõe** quais valores de quais atributos são ausentes disfarçados (R2.07) e explica por quê.
2. O usuário **confirma**.
3. O agente gera uma **nova base** em `dados/`, com sufixo (ex.: `diabetes_ausentes.arff`), trocando esses valores por `?`. A base original não é alterada.
4. Registra quantos valores foram trocados em cada atributo e o script usado.
5. **Se o usuário não souber dizer** o que os valores significam, o agente não fica paralisado nem decide sozinho. Ele faz uma **análise de sensibilidade**: mantém a base original como análise principal, gera a base tratada como **cenário alternativo** e roda os mesmos modelos nas duas. Se as conclusões forem as mesmas, a dúvida não importa para a decisão; se mudarem, o agente mostra as duas e diz que a resposta depende de esclarecer o significado dos valores com quem conhece os dados.
Essa conversão pode ser feita em Python, porque não inventa número nenhum: só marca como desconhecido o que já era desconhecido.

**R2.15 — A ausência pode ser informação.**
**Além do livro:** às vezes o fato de faltar o dado diz algo (o exame não foi pedido porque o caso parecia simples; o campo ficou vazio porque o processo foi arquivado cedo). Antes de imputar, o agente considera criar um atributo indicador ("insulina ausente: sim/não") e testa se ele ajuda.

**R2.16 — Tratamento não é melhoria garantida.**
O agente roda os mesmos modelos na base original e na base tratada, com a mesma validação, e compara na métrica principal com o teste de significância (R5.51). Se o tratamento não melhorar, a conclusão é essa: o tratamento é mais correto conceitualmente, mas não mudou o desempenho.

---

## Bloco T — Regra geral: o que aprende com os dados fica dentro da validação

**R2.17 — Vazamento de informação no pré-processamento.**
Qualquer passo que **calcula algo a partir dos dados** precisa ser aprendido **só com o treino** de cada parte da validação cruzada. Senão, informação do teste vaza para o modelo e a avaliação fica otimista.
- **Precisam ficar dentro da validação:** imputação por média ou moda, normalização com média e desvio, discretização supervisionada, seleção de atributos, balanceamento (R5.40) e componentes principais.
  - Weka: `weka.classifiers.meta.FilteredClassifier -F <filtro> -W <classificador>` para filtros; `weka.classifiers.meta.AttributeSelectedClassifier` para seleção de atributos.
- **Podem ser feitos antes:** remover identificadores pelo nome, converter códigos para nominal, marcar como ausente um valor impossível por regra de domínio. Esses passos não olham para a distribuição dos dados.

---

## Bloco U — Seleção de atributos e dimensionalidade

**R2.18 — Maldição da dimensionalidade.**
Com muitos atributos e poucos registros, os dados ficam esparsos: não há exemplos suficientes para cobrir as combinações, e as distâncias perdem o sentido. O k-NN e o agrupamento sofrem mais.

**R2.19 — Primeiro o bom senso.**
Antes de qualquer método automático: remover identificadores, um de cada par de atributos redundantes óbvios (valor e valor com imposto) e atributos claramente sem relação com o objetivo.

**R2.20 — Três abordagens de seleção.**
- **Embutida:** o próprio algoritmo escolhe (árvores já fazem isso).
- **Filtro:** escolhe antes, independente do algoritmo. Weka: `CfsSubsetEval`, que procura atributos muito relacionados com a classe e pouco relacionados entre si.
- **Envoltória (wrapper):** testa subconjuntos usando o próprio algoritmo. É mais cara e corre mais risco de sobreajuste (R5.46).
- Weka: `weka.classifiers.meta.AttributeSelectedClassifier -W <classificador>`. O padrão do Weka já é `CfsSubsetEval` com busca `BestFirst`, e a seleção roda dentro de cada parte da validação (R2.17).

**R2.21 — Onde a seleção mais ajuda.**
NaiveBayes, que sofre com atributos correlacionados (R5.15), e IBk, que sofre com irrelevantes (R5.11). Em árvores e florestas, que já selecionam atributos, o ganho costuma ser pequeno.

**R2.22 — Validar a seleção.**
Comparar o modelo com todos os atributos e com os selecionados, na mesma validação e na métrica principal. Se empatarem, ficar com menos atributos (R4.15). Se a seleção piorar, descartá-la.

**R2.23 — Componentes principais (PCA).**
Cria atributos novos que combinam os originais. Reduz a dimensão de dados numéricos, mas os atributos novos **não têm significado direto**. Não usar quando o objetivo é entender (R4.03). Weka: `weka.filters.unsupervised.attribute.PrincipalComponents`.

---

## Bloco V — Criação, agregação e transformação de atributos

**R2.24 — Um bom atributo vale mais que um algoritmo melhor.**
Muitas vezes, criar o atributo certo melhora mais o resultado do que trocar de algoritmo. Exemplos: duração (data final menos data inicial), número de etapas percorridas, valor por unidade, índice de massa corporal a partir de peso e altura. O agente sugere atributos derivados quando o domínio indicar e testa se eles ajudam (R2.22).

**R2.25 — Agregação e unidade de análise.**
Quando há vários registros por objeto (vários movimentos por processo, várias compras por cliente), é preciso decidir **qual é o objeto da análise** antes de modelar, e agregar os registros até ele: soma, média, contagem, primeiro e último valor, duração.
- Agregar reduz a variabilidade e o volume, mas **perde detalhe** (a média mensal esconde o dia da semana).
- Misturar níveis (um registro por movimento, mas classe definida por processo) faz o mesmo processo aparecer no treino e no teste, e a avaliação fica otimista (mesmo efeito da R2.09).

**R2.26 — Discretização.**
Transforma um número em faixas. Alguns algoritmos exigem (regras de associação); árvores não precisam (R4.09).
- **Não supervisionada** (faixas de largura igual ou de frequência igual): não usa a classe e pode ser feita antes.
- **Supervisionada** (usa a classe para escolher os cortes; Weka: `weka.filters.supervised.attribute.Discretize`): precisa ficar dentro da validação (R2.17).
- Sempre perde informação. Usar só com motivo.

**R2.27 — Binarização.**
Transformar uma categoria em várias colunas sim/não (uma por valor) evita criar relações artificiais entre categorias. Weka: `weka.filters.unsupervised.attribute.NominalToBinary`. O SMO faz isso sozinho (R5.25).

**R2.28 — Transformações funcionais (logaritmo, raiz etc.).**
Servem para amplitudes enormes (de 1 a 1 bilhão) ou distribuições muito assimétricas. Cuidados:
- logaritmo não aceita zero nem negativos;
- 1/x **inverte a ordem** dos valores;
- perguntar sempre: a ordem precisa ser mantida? A transformação vale para todos os valores?
- **Além do livro:** árvores não mudam com transformações que preservam a ordem (logaritmo, raiz). A transformação só faz diferença para algoritmos que usam distâncias ou somas (IBk, SMO, MultilayerPerceptron) e para o NaiveBayes com distribuição normal (R5.16).

**R2.29 — Normalização.**
- **Padronização** (média 0, desvio 1) ou **normalização para o intervalo 0–1**: necessária quando atributos de escalas diferentes entram juntos numa distância ou soma.
- A normalização 0–1 depende do mínimo e do máximo, e por isso é sensível a valores extremos.
- IBk, SMO e MultilayerPerceptron já normalizam no Weka (R5.10, R5.25, R5.20). O agente declara isso e não normaliza duas vezes.

---

## Bloco W — Exploração dos dados

**R3.01 — Perfil da base antes de modelar.**
O resumo do Weka não basta. O agente monta um perfil com:
- **Atributos numéricos:** mínimo, máximo, média, mediana, desvio-padrão, intervalo interquartil (IQR), número de zeros e número de ausentes.
- **Atributos nominais:** número de valores distintos, valor mais frequente e frequência do valor mais raro.
- **Classe:** distribuição (R5.33).

**R3.02 — Média longe da mediana é sinal de alerta.**
A média é sensível a valores extremos e a distribuições assimétricas; a mediana não. Se as duas forem muito diferentes, o agente relata a mediana e investiga extremos e ausentes disfarçados (zeros puxam a média para baixo).

**R3.03 — Medidas de dispersão robustas.**
O desvio-padrão e a amplitude são sensíveis a valores extremos. Para descrever a dispersão de atributos assimétricos, usar o IQR (diferença entre o 3º e o 1º quartis).
- **Além do livro:** candidatos a extremo são os valores abaixo de Q1 − 1,5 × IQR ou acima de Q3 + 1,5 × IQR (regra de Tukey). O filtro `InterquartileRange` do Weka usa fatores próprios (opções `-O` e `-E`); o agente informa quais usou.

**R3.04 — Correlação entre atributos.**
Uma correlação alta (em módulo) entre dois atributos numéricos indica redundância, o que prejudica o NaiveBayes (R5.15). Limites:
- a correlação só mede relação **linear**;
- correlação de um atributo com a classe não substitui o modelo;
- não vale para atributos nominais (usar tabela de contingência).

**R3.05 — Exploração em Python é permitida, com registro.**
Estatísticas descritivas (contagens, quartis, correlações) podem ser calculadas em Python a partir do `.arff`, porque descrevem os dados e não são modelagem. O agente registra o código usado e salva a saída em `resultados/` com data e hora, como faz com o Weka. Modelos, matrizes de confusão e métricas de desempenho continuam vindo **só** do Weka.

**R3.06 — A exploração gera hipóteses, não conclusões.**
O que o perfil sugere ("estes zeros parecem ausentes", "estes dois atributos parecem redundantes") vira uma hipótese: o agente confirma com o usuário (R2.14) ou testa no Weka (R2.16, R2.22) antes de agir.

---

# Parte 4 — Análise de Associação

> Regras R6.xx (conceitos básicos) e R7.xx (tipos de atributo e sequências). A associação **descreve o que aparece junto**; não prevê uma classe e não prova causa.

---

## Bloco X — Quando usar associação

**R6.01 — Associação responde a outra pergunta.**
- Classificação: "dado um caso novo, qual será a classe?" (Partes 1 e 2).
- Associação: "que características ou itens aparecem juntos com frequência?"
Se o usuário quer prever um alvo, o agente usa classificação. Se quer descobrir combinações frequentes, sem um alvo definido, usa associação.

**R6.02 — Coocorrência não é causa.**
Uma regra "A → B" diz que B costuma aparecer quando A aparece. Não diz que A provoca B. Causalidade exige conhecimento do domínio e, em geral, ordem no tempo. O agente nunca escreve "A causa B" nem "A leva a B" a partir de uma regra de associação.

**R6.03 — Definir a transação.**
Toda análise de associação começa com a pergunta: **o que é uma transação?** Uma compra, um paciente, um processo, um atendimento. Cada transação vira uma linha, e os itens são as características presentes nela. É a mesma decisão de unidade de análise da R2.25: se o mesmo processo aparecer em várias linhas, as contagens ficam infladas.

---

## Bloco Y — Preparar os dados para associação

**R7.01 — Cada par "atributo = valor" vira um item.**
"Setor = Finanças" e "Setor = Saúde" são itens diferentes. Problemas típicos:
- **Valores raros** quase nunca atingem o suporte mínimo. Solução: agrupar valores parecidos em categorias maiores ou num "Outros".
- **Valores muito frequentes** (presentes em mais de ~85% das transações) geram regras redundantes, que só repetem o óbvio. Solução: removê-los da análise ou analisá-los à parte.

**R7.02 — Presença e ausência.**
Na associação, o que importa costuma ser a **presença** do item. No Weka, para que a ausência não vire item, ela deve ser registrada como `?` (é o que a base `supermarket.arff` faz). Em atributos sim/não (como `vote.arff`), os dois valores viram itens, e regras feitas só de "não" quase sempre são pouco informativas. O agente decide com o usuário se a ausência interessa.

**R7.03 — Atributos numéricos precisam virar faixas.**
O Apriori só trabalha com categorias. Discretizar (`weka.filters.unsupervised.attribute.Discretize`, com `-B` faixas, ou `-F` para faixas de frequência igual) envolve um compromisso:
- faixas **largas** demais misturam casos diferentes e a confiança cai;
- faixas **estreitas** demais têm suporte baixo e as regras somem.
O agente testa pelo menos duas divisões e informa se as regras principais se mantêm.

**R7.04 — Remover relações óbvias por construção.**
Atributos derivados de outros geram regras triviais. Exemplo: um atributo "total da compra = alto" aparece como consequência de qualquer combinação de muitos itens. Identificadores também saem (R4.04). O agente remove esses atributos ou avisa que as regras com eles são esperadas.

---

## Bloco Z — Limiares e algoritmo

**R6.04 — Suporte e confiança.**
- **Suporte:** fração das transações que contêm todos os itens da regra. Regras com suporte muito baixo podem ser acaso.
- **Confiança:** entre as transações que têm o antecedente, a fração que também tem o consequente. Mede a confiabilidade da regra.

**R6.05 — Como o Apriori do Weka escolhe o suporte.**
**Além do livro (Weka):** o `weka.associations.Apriori` começa com suporte 100% (`-U 1.0`) e vai baixando de 5 em 5 pontos (`-D 0.05`) até encontrar o número de regras pedido (`-N`, padrão 10) ou chegar ao suporte mínimo (`-M`, padrão 0,1). Portanto, "10 regras" é um **critério de parada**, não um resultado. O agente define `-N` e `-M` de propósito e informa **o suporte efetivamente alcançado** (o Weka o mostra na saída).

**R6.06 — Suporte distorcido.**
Quando alguns itens são muito frequentes e a maioria é rara:
- suporte mínimo alto perde padrões raros, mas importantes (o item caro, o processo excepcional);
- suporte mínimo baixo multiplica as regras e gera **padrões de suporte cruzado**: um item muito frequente combinado com um muito raro. Esses padrões costumam ser espúrios, porque a relação entre os itens é fraca.
Antes de minerar, o agente examina a frequência de cada item (perfil, R3.01) e, se houver distorção forte, analisa os grupos de itens separadamente ou remove os quase universais (R7.01).

**R6.07 — Excesso de regras.**
O número possível de regras cresce exponencialmente com o número de itens. O agente nunca despeja centenas de regras: ordena por uma medida de interesse (R6.11) e apresenta as principais, dizendo quantas foram geradas no total.

**R6.08 — Regras redundantes.**
Se "A → C" e "A, B → C" têm confiança parecida, a segunda não acrescenta nada: o item B é supérfluo. O agente relata a regra mais geral e descarta as que só acrescentam itens sem aumentar o interesse.
- **Regras longas e regras no limite de corte são frágeis.** Regras com muitos itens só servem se forem interpretáveis e úteis para o usuário. Regras cujo suporte está exatamente no limite mínimo mudariam com um limite um pouco diferente. Quando as regras de maior lift estiverem todas no limite, o agente diz isso, testa um segundo limite e verifica quais regras sobrevivem. Para apresentar ao usuário, prefere regras de 2 ou 3 itens, a menos que as mais longas tragam algo que as curtas não trazem.

**R6.09 — Apriori ou FP-Growth.**
Os dois encontram os mesmos conjuntos frequentes; o FP-Growth costuma ser mais rápido em bases grandes. **Além do livro (Weka):** o `weka.associations.FPGrowth` exige atributos binários. A escolha afeta o tempo de execução, não a validade dos padrões.

---

## Bloco AA — Avaliar se uma regra interessa

**R6.10 — Confiança sozinha engana.**
Exemplo: 75% das pessoas que tomam chá também tomam café, o que parece uma regra forte. Mas 80% de **todas** as pessoas tomam café. Saber que alguém toma chá **diminui** a chance de tomar café. A confiança ignora a frequência do consequente.

**R6.11 — Sempre relatar o lift.**
Lift = confiança da regra ÷ frequência do consequente.
- Lift = 1: os itens são independentes; a regra não diz nada.
- Lift > 1: associação positiva.
- Lift < 1: associação negativa (como no exemplo do chá).
Weka: a opção `-T` escolhe a medida que ordena as regras (0 = confiança, 1 = lift, 2 = leverage, 3 = convicção), e a saída do Weka mostra todas para cada regra. O agente ordena por lift (com suporte e confiança mínimos) e relata, para cada regra, **suporte (contagem e %), confiança e lift**.

**R6.12 — Nenhuma medida é perfeita.**
Com itens raros, o lift pode ficar alto mesmo quando os itens quase nunca aparecem juntos. Por isso o agente olha as três medidas juntas e desconfia de lift alto com suporte muito baixo.

**R6.13 — Óbvio não é interessante.**
"Pão → manteiga" pode ter suporte, confiança e lift altos e não ensinar nada. O agente separa regras **esperadas** (que confirmam o que o domínio já sabe) de regras **surpreendentes**, e pergunta ao usuário quais fazem sentido. A conclusão de uma análise de associação depende do conhecimento de quem conhece o domínio.

**R6.14 — Paradoxo de Simpson.**
Uma associação que aparece nos dados juntos pode **sumir ou se inverter** dentro de cada grupo, quando existe uma variável escondida (ano, setor, tipo de processo; em saúde, idade e sexo). Antes de apresentar uma regra como achado, o agente verifica se ela se mantém nos principais grupos (estratificação).

**R6.15 — Muitas regras, muito acaso.**
**Além do livro:** quanto mais regras se examinam, mais aparecem regras fortes por puro acaso, como no caso das várias métricas (R5.51). Para os achados que serão usados, o agente faz uma **verificação de replicação**:
1. Embaralha as transações com semente fixa e as divide ao meio, gerando dois arquivos (Weka: `weka.filters.unsupervised.instance.Randomize -S 1` e depois `weka.filters.unsupervised.instance.RemovePercentage -P 50`, uma vez sem e outra com `-V`).
2. Roda o Apriori **só na metade de descoberta**.
3. Confere suporte, confiança e lift dessas regras **na metade de conferência**, que o Apriori nunca viu. A contagem pode ser feita em Python (R3.05).
- **Erro a evitar:** minerar com a base inteira e conferir numa metade dela não é replicação, porque a metade de conferência participou da descoberta. É como corrigir a prova olhando o gabarito.
- Regras que não se repetem na metade de conferência são descartadas ou apresentadas como fracas.

**R6.16 — Regras com classe não substituem classificador.**
O Weka pode gerar regras cujo consequente é a classe (`Apriori -A`). Elas descrevem combinações frequentes, mas **não foram validadas para prever** casos novos. Para prever, usar classificadores (JRip, J48) com validação cruzada (Partes 1 e 2).

---

## Bloco AB — Quando a ordem importa: sequências

**R7.05 — Coocorrência ignora a ordem.**
A associação comum trata a transação como um saco de itens. Quando a **ordem** importa (etapas de um processo, setores por onde um documento passou, consultas de um paciente), o padrão certo é **sequencial**: "A, depois B, depois C".
- Os dados precisam de três colunas: identificador do objeto, momento e evento.
- Restrições de tempo mudam o resultado: intervalo máximo entre eventos, janela, duração total. O agente declara as que usou.
- **Além do livro (Weka):** o suporte do Weka a padrões sequenciais é limitado (`weka.associations.GeneralizedSequentialPatterns`, se estiver disponível na versão instalada). Para analisar o fluxo de processos, existe uma área própria (mineração de processos), com ferramentas e conceitos que este manual não cobre. O agente diz isso em vez de forçar a associação comum.

---

## Bloco AC — Formato da resposta em associação

**R6.17 — Estrutura.**
1. **Preparação:** o que é a transação, como os atributos viraram itens, discretizações e remoções.
2. **Parâmetros:** comando, `-N`, `-M`, medida de ordenação e o **suporte efetivamente alcançado**.
3. **Regras:** tabela com antecedente → consequente, suporte (contagem e %), confiança e lift, ordenada por lift; total de regras geradas.
4. **Interpretação:** associação, não causa; regras esperadas contra surpreendentes; regras redundantes descartadas.
5. **Verificações:** estratificação (R6.14), replicação (R6.15) e o que não foi feito.

---

## Pendências para próximas partes
- Parte 5 (caps. 8–9): agrupamento (SimpleKMeans, hierárquico, DBSCAN).
- Parte 6 (cap. 10): detecção de anomalias.
