# Transcrição T04_r1

### Usuário

Qual o melhor modelo para prever se um acordo trabalhista é bom ou ruim? Base labor.arff.


### Agente

Vou começar lendo o manual de decisões e explorando a base, antes de qualquer modelagem.

- `Bash`: `ls; ls dados ferramentas conhecimento; wc -l conhecimento/manual_decisoes.md`
- `Read`: `/tmp/copias_validacao/T04_r1/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/labor.arff`
- `Bash`: `python3 ferramentas/weka_runner.py resumo labor.arff; sed -n 634,700p conhecimento/manual_decisoes.md`
- `Bash`: `ls analises analises/scripts resultados 2>/dev/null | head -50; grep -n "@attribute" dados/labor.arff; grep -c "^[^@%]" dados/labor.arff; python3 -c "import scipy, pandas; print('ok')"`
- `Bash`: `mkdir -p analises/scripts && cat > analises/scripts/2026-11-21_perfil_labor.py <<'EOF'
# Perfil descritivo da base labor.arff (somente estatística descritiva, sem modelos).
# Uso: python3 analises/scripts/2026-11-21_perfil_labor.py
import datetime
from scipy.io import arff
import pandas as pd

# Lê `

### Agente

A seção de nominais saiu vazia (o pandas instalado guarda texto num tipo próprio, então o teste `dtype == object` falhou). Corrijo o teste:

- `Bash`: `sed -i 's/    if df\[col\].dtype == object and col != "class":/    if not pd.api.types.is_numeric_dtype(df[col]) and col != "class":/' analises/scripts/2026-11-21_perfil_labor.py && python3 analises/scripts/2026-11-21_perfil_labor.py | sed -n '/nominais/,/Proporção/p'; ls -t resultados | head -3`
- `Bash`: `rm resultados/20261121_141352_perfil_labor.txt`

### Agente

Explorei a base, mas **ainda não rodei nenhum modelo**. Antes disso preciso de uma informação que só você pode dar: o custo de cada tipo de erro. Primeiro, o que a exploração mostrou.

## O que a exploração mostrou

Usei o resumo do Weka e um perfil descritivo em Python. O script está em `analises/scripts/2026-11-21_perfil_labor.py` e a saída em `resultados/20261121_141356_perfil_labor.txt`.

| Item verificado | Resultado | O que isso significa |
|---|---|---|
| Tamanho | **57 acordos**, 16 atributos + classe | A base é muito pequena. Com 10 partes, cada parte testa só 5 ou 6 acordos. O resultado vai variar bastante e o intervalo de confiança vai ser largo. Também vai ser difícil um modelo superar outro com significância. |
| Classe | **good = 37 (65%)**, **bad = 20 (35%)** | O ZeroR vai prever sempre "good" e acertar cerca de 65%. É essa a marca que os modelos precisam superar. |
| Ausentes | Muitos: `standby-pay` 84%, `wage-increase-third-year` 74%, `education-allowance` 61%, `pension` 53%, `longterm-disability` 51% | Quase metade das células está vazia. Cada algoritmo trata isso de um jeito, e esse tratamento vai pesar no resultado. |
| **A própria ausência indica a classe** | `pension` falta em **76% dos acordos bons** e em **10% dos ruins**. `education-allowance`: 73% contra 40%. | É o achado mais importante da exploração. Parece que os acordos ruins foram registrados com mais detalhe. Se for isso, um modelo pode acertar só porque percebe "campo preenchido", sem aprender nada sobre o conteúdo do acordo. Vou testar esse efeito e mostrar o resultado na análise. |
| Ausentes disfarçados | Nenhum encontrado | Não há zeros impossíveis. Existe um único zero, em `shift-differential`, e ele é plausível: significa que não há adicional de turno. |
| Duplicatas e identificadores | Nenhum | |
| Quase constante | `bereavement-assistance`: 27 "yes" e só 3 "no" entre os preenchidos | Esse atributo deve ajudar pouco a separar as classes. |
| Ordinais | `vacation` (abaixo da média, na média, generosa) e `duration` (1 a 3 anos) | Os algoritmos tratam `vacation` como categoria sem ordem, então a ordem se perde. Aviso isso na análise. |

## Preciso de três respostas suas antes de modelar

Você quer **prever**. Nesse caso, qual modelo é "o melhor" depende de quanto custa cada tipo de erro, e essa informação vem do uso que você vai dar ao modelo, não dos dados.

1. **Qual é a classe de interesse?** Imagino que seja **bad**, o acordo ruim que se quer identificar. Confirma?
2. **Qual erro é pior?**
   - **Falso negativo:** o modelo diz que um acordo ruim é bom, e ele passa sem revisão.
   - **Falso positivo:** o modelo diz que um acordo bom é ruim, e alguém revisa ou contesta um acordo que estava bom.
3. **Quantas vezes pior?** Por exemplo, "deixar passar um acordo ruim custa 3 vezes mais que um alarme falso". Com esse número eu monto a matriz de custo.

Se você não tiver um número, há dois caminhos:
- **Eu proponho uma proporção.** Você confirma ou ajusta.
- **Tratamos os dois erros como equivalentes.** Nesse caso a métrica principal passa a ser o **F1 da classe bad**, e eu declaro essa suposição no início da análise.

## O que vou fazer depois da sua resposta

- **Linha de base:** ZeroR. Se houver matriz de custo, também calculo o custo de prever "bad" para todos e uso a mais barata das duas.
- **Candidatos:**
  - J48: árvore podada, lida bem com ausentes.
  - NaiveBayes: robusto em base pequena, ignora o atributo ausente em cada registro.
  - IBk, com k escolhido por validação interna (`-K 15 -X`).
  - SMO com `-M`, para que a AUC tenha sentido.
  - RandomForest.
  - Rede neural fica de fora, porque 57 registros são poucos para ela.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1, registrando os comandos exatos.
- **Escolha:** teste t pareado corrigido na métrica principal, comparando o melhor modelo com a linha de base e o melhor com o segundo melhor.
- **Efeito dos ausentes:** confiro se o melhor modelo está se apoiando no padrão de campos vazios.


### Usuário

Os dois erros custam o mesmo.


### Agente

Então a matriz de custo é simétrica: `[0 1; 1 0]`. Nesse caso o custo total é igual ao número de erros. A **métrica principal**, que defino agora, antes de ver qualquer resultado, é o **custo total**, ou seja, a quantidade de acordos classificados errado. A classe positiva é **bad**. Vou conferir como as ferramentas recebem os parâmetros.

- `Bash`: `python3 ferramentas/significancia.py -h 2>&1 | grep -v JAVA; grep -n "def \|argv\|-x\|-s 1\|-t" ferramentas/weka_runner.py | head -60`
- `Bash`: `sed -n 1,60p ferramentas/significancia.py; grep -n "envelope\|CostSensitive\|-M\b" ferramentas/significancia.py | head -30`

### Agente

Agora rodo o ZeroR e os cinco candidatos, todos com a mesma validação cruzada (10 partes, semente 1). As rodadas são independentes, então rodo em paralelo.

- `Bash`: `export R=ferramentas/weka_runner.py
( python3 $R comparar labor.arff weka.classifiers.trees.J48 -C 0.25 -M 2 > /dev/null 2>&1; echo J48 $? ) &
( python3 $R comparar labor.arff weka.classifiers.bayes.NaiveBayes > /dev/null 2>&1; echo NB $? ) &
( python3 $R comparar labor.arff weka.classifiers.lazy.IB`

### Agente

Leio os arquivos de saída e extraio só o bloco da validação cruzada de cada um:

- `Bash`: `cd /tmp/copias_validacao/T04_r1/resultados && for f in 20261121_141438_*_classificador.txt 20261121_141438_353608_baseline_ZeroR.txt; do echo "################ $f"; head -3 $f; sed -n '/=== Stratified cross-validation ===/,$p' $f | grep -v "^$" | grep -v "Total Number\|Root relative\|Relative abs\|R`

### Agente

Faltou o kappa no filtro que usei. Também preciso ver o k que o IBk escolheu e a árvore do J48. Em seguida rodo os testes de significância e uma checagem do efeito dos ausentes.

- `Bash`: `for f in 20261121_141438_*; do echo "$f: $(head -1 $f | grep -o 'weka.classifiers[^ ]*') | $(sed -n '/Stratified cross/,$p' $f | grep Kappa)"; done; grep -i "nearest neighbour" 20261121_141438_379328_classificador.txt; sed -n '/J48 pruned tree/,/Size of the tree/p' 20261121_141438_353608_classificad`
- `Bash`: `cd /tmp/copias_validacao/T04_r1 && S=ferramentas/significancia.py; R=ferramentas/weka_runner.py
( python3 $S labor.arff --a weka.classifiers.lazy.IBk --opcoes-a="-K 15 -X" --b weka.classifiers.rules.ZeroR --custo "0 1; 1 0" --positiva bad --repeticoes 10 --sem-envelope > /dev/null 2>&1; echo sigZ $?`
- `Bash`: `cd /tmp/copias_validacao/T04_r1/resultados && for f in 20261121_141507_*_classificador.txt; do echo "######## $(head -1 $f | sed 's/.*weka.classifiers/weka.classifiers/;s/-t .*-s 1//')"; sed -n '/Stratified cross/,$p' $f | grep -E "Correctly|Incorrectly|Kappa|bad$|^ +[0-9]+ +[0-9]+ \|"; done; for f `
- `Bash`: `cd /tmp/copias_validacao/T04_r1 && python3 ferramentas/significancia.py labor.arff --a weka.classifiers.bayes.NaiveBayes --b weka.classifiers.rules.ZeroR --custo "0 1; 1 0" --positiva bad --repeticoes 10 --sem-envelope 2>&1 | sed -n '/Resumo por métrica/,$p'
cat > analises/scripts/2026-11-21_ic_labo`
- `Write`: `/tmp/copias_validacao/T04_r1/analises/2026-11-21_labor.md`

### Agente

# Melhor modelo para prever acordos ruins na labor.arff

**Recomendo o NaiveBayes, com uma ressalva:** ele está em empate técnico com o IBk e o RandomForest. Os três acertam bem mais que a linha de base, e essa diferença é estatisticamente significativa. Entre eles, nenhuma diferença é significativa. Por isso escolhi o NaiveBayes pelos critérios de desempate explicados abaixo, e não por ter vencido os outros.

Como você disse que os dois erros custam o mesmo, a **métrica principal é o custo total**, que aqui é simplesmente o número de acordos classificados errado. Defini essa métrica antes de rodar os modelos.

## 1. O que foi feito

- **Base:** a original, sem pré-processamento. A exploração não encontrou ausentes disfarçados, duplicatas nem identificadores.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1. Comando: `weka.classifiers.<modelo> -t labor.arff -x 10 -s 1 [opções]`.
- **Candidatos:**
  - J48 (`-C 0.25 -M 2`);
  - NaiveBayes;
  - IBk (`-K 15 -X`): o Weka testou valores de k só com os dados de treino e escolheu **k = 3**;
  - SMO (`-M`), para que a AUC tenha sentido;
  - RandomForest.

## 2 e 3. Resultados do Weka (validação cruzada) e comparação com a linha de base

| Modelo | Erros (custo) | Acurácia [IC 95%] | Kappa | Recall bad | Precisão bad | F1 bad | AUC |
|---|---:|---|---:|---:|---:|---:|---:|
| ZeroR (prevê good para todos) | 20 | 0,649 [0,519; 0,760] | 0,00 | 0,000 | – | – | 0,472 |
| Prever bad para todos | 37 | – | – | – | – | – | – |
| J48 | 15 | 0,737 [0,610; 0,834] | 0,44 | 0,700 | 0,609 | 0,651 | 0,695 |
| **NaiveBayes** | **6** | 0,895 [0,789; 0,951] | 0,77 | 0,900 | 0,818 | 0,857 | 0,965 |
| IBk (k = 3) | 5 | 0,912 [0,811; 0,962] | 0,81 | 0,850 | 0,895 | 0,872 | 0,947 |
| SMO -M | 7 | 0,877 [0,768; 0,939] | 0,73 | 0,850 | 0,810 | 0,829 | 0,811 |
| RandomForest | 6 | 0,895 [0,789; 0,951] | 0,76 | 0,800 | 0,889 | 0,842 | 0,943 |

- **Linha de base:** existem duas formas triviais de classificar. Prever "good" para todos erra os 20 acordos ruins. Prever "bad" para todos erra os 37 bons. A mais barata é a primeira, então a linha de base é **custo 20**. Todos os modelos ficaram abaixo dela.
- **Matriz de confusão do NaiveBayes** (linhas = classe real, colunas = classe prevista):
  ```
          bad  good
  bad      18     2   ← deixou passar 2 acordos ruins
  good      4    33   ← 4 alarmes falsos
  ```

## 4. Confiabilidade

Teste t pareado corrigido sobre o custo, repetindo a validação cruzada 10 vezes (100 partes no total):

| Comparação | Custo médio por parte (A × B) | p | Conclusão |
|---|---|---:|---|
| NaiveBayes × ZeroR | 0,37 × 2,00 | < 0,001 | NaiveBayes é melhor |
| IBk × ZeroR | 0,54 × 2,00 | < 0,001 | IBk é melhor |
| IBk × NaiveBayes | 0,54 × 0,37 | 0,433 | empate técnico |
| IBk × RandomForest | 0,54 × 0,65 | 0,707 | empate técnico |

- Com semente 1, o IBk errou 5 acordos e o NaiveBayes errou 6. A diferença é de **um único acordo**. Nas 10 repetições a ordem se inverteu e o NaiveBayes teve o menor custo médio. Isso confirma que a diferença entre os dois é ruído.
- Com 57 registros, os intervalos de confiança são largos: o do NaiveBayes vai de 79% a 95%. Os intervalos dos três primeiros modelos se sobrepõem quase totalmente.

**Por que o NaiveBayes, entre os empatados:**
- É o mais simples dos três.
- Teve o menor custo médio quando a validação foi repetida 10 vezes.
- **Não depende do padrão de campos vazios.** Na exploração, vimos que a ausência de dados quase indica a classe sozinha: `pension` falta em 76% dos acordos bons e em só 10% dos ruins. O NaiveBayes ignora o atributo ausente, então acerta pelo conteúdo do acordo. O IBk usa parte desse padrão: quando substituí os ausentes dentro da validação, ele passou de 5 para 7 erros. Se no futuro o registro dos acordos for feito de outro jeito, o IBk tende a perder desempenho e o NaiveBayes não.

## 5. Interpretação

- **J48:** a árvore usa só dois atributos. Aumento salarial no 1º ano ≤ 2,5% indica acordo ruim. Acima disso, 10 feriados ou menos também indica ruim, e mais de 10 indica bom. A árvore é legível, mas **instável**: acerta 87,7% no treino e só 73,7% na validação. Com tão poucos dados, cada divisão se apoia em poucos acordos. Ela serve como pista do que pesa na classificação, não como modelo de previsão.
- **NaiveBayes:** é só parcialmente interpretável. Não extraí as probabilidades por atributo. As probabilidades que ele dá para cada acordo servem para **ordenar** casos (AUC de 0,965), não para serem lidas literalmente como "X% de chance".

## 6. Alertas e próximos passos

- **Base muito pequena.** Em uso real, espere variação em torno de 85–90% de acerto. Os intervalos de confiança indicam isso.
- **Ausentes informativos.** É preciso esclarecer com quem conhece os dados por que os acordos ruins têm mais campos preenchidos. Se for um efeito da forma de coleta, um modelo que aprende com esse padrão não vai valer para casos novos.
- **Ordem perdida:** `vacation` foi tratado como categoria sem ordem.
- **Verificações feitas:**
  - NaiveBayes com `-K` (6 erros) e com `-D` (8 erros): a suposição de distribuição normal não prejudicou o modelo.
  - IBk: não testei seleção de atributos. Atributos irrelevantes podem prejudicar esse modelo.
- **Configurações testadas:** 8, além do ZeroR, com 4 testes de significância. O melhor número de uma lista tende a ser otimista, por isso o desempate seguiu os critérios acima e não a menor contagem de erros.
- **Não rodei:** JRip, MultilayerPerceptron (base pequena demais para uma rede neural) e comitês além do RandomForest.

O relatório completo está em `analises/2026-11-21_labor.md`. As saídas do Weka estão em `resultados/`, nos arquivos que começam com `20261121_`.

