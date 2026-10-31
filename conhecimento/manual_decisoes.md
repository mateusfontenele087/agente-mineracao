# Manual de Decisões do Especialista

> Uso: instruções internas do agente. O agente **não cita** este manual nem o livro; aplica as regras e justifica pelos fundamentos.
> Parte 1 (regras R4.xx): classificação, árvores e avaliação. Parte 2 (regras R5.xx): técnicas alternativas, classes desbalanceadas e escolha entre algoritmos.
> Status: **rascunho v0.4** — para revisão regra a regra.

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
A classe rara, ou a de maior interesse, é a **positiva**. O agente pergunta, se não estiver claro: **qual erro custa mais**, deixar passar um caso positivo (falso negativo) ou dar um alarme falso (falso positivo)?

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
- Antes de rodar a comparação, o agente define **uma métrica principal**, a que corresponde ao objetivo do usuário: custo total, se houver matriz de custo; senão, F1 ou recall da classe positiva, se as classes forem desbalanceadas; senão, acurácia. A decisão sobre qual modelo é melhor é tomada **só** por essa métrica.
- As demais métricas são **descritivas**. Se alguma delas der p < 0,05, o agente só a chama de significativa se ela também passar no limiar corrigido: 0,05 dividido pelo número de métricas testadas (correção de Bonferroni; com 5 métricas, p < 0,01).
- Exemplo real: NaiveBayes contra RandomForest na credit-g, com matriz de custo. Métrica principal: custo, p = 0,137, empate técnico. O recall da classe "bad" deu p = 0,028, que não passa em 0,05 / 5 = 0,01. Conclusão correta: **empate técnico**; prefere-se o NaiveBayes por ser mais simples (R5.45), e não por ter "recall significativamente maior".

**R5.52 — Comparar todos contra todos é caro e multiplica testes.**
Cada comparação de dois modelos com 10 × 10 validações cruzadas leva minutos. Com muitos candidatos, o agente não testa todos os pares. Ele testa: (1) o melhor candidato contra a **linha de base** (R4.20, R5.48), para saber se há modelo útil; (2) o melhor contra o segundo melhor na métrica principal, para saber se a escolha se sustenta. Ele informa ao usuário quantas comparações fez.

---

## Pendências para próximas partes
- Parte 3 (caps. 2–3): qualidade dos dados, pré-processamento, exploração.
- Partes 4–6 (caps. 6–10): associação (Apriori), agrupamento (SimpleKMeans etc.), anomalias.
