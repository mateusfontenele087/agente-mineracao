# Transcrição T04_r2

### Usuário

Qual o melhor modelo para prever se um acordo trabalhista é bom ou ruim? Base labor.arff.

- `Bash`: `ls; ls dados ferramentas; wc -l conhecimento/manual_decisoes.md`
- `Read`: `/tmp/copias_validacao/T04_r2/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/labor.arff`
- `Bash`: `python3 ferramentas/weka_runner.py resumo labor.arff; ls resultados | tail -5`
- `Read`: `/tmp/copias_validacao/T04_r2/conhecimento/manual_decisoes.md`
- `Bash`: `grep -n "class" -A5 dados/labor.arff | head -30; grep -c "good$" dados/labor.arff; grep -c "bad$" dados/labor.arff`
- `Bash`: `sed -n '/@data/,$p' dados/labor.arff | grep -v '@data' | grep -v '^%' | awk -F, 'NF>1{print $NF}' | sort | uniq -c`

### Agente

Antes de rodar qualquer modelo, preciso de uma informação que só você pode dar. Já li a base e a explorei no Weka. Seguem o que encontrei e as perguntas.

## O que a base mostra

Comando: `python3 ferramentas/weka_runner.py resumo labor.arff`

- **57 acordos e 16 atributos**, mais a classe. Os atributos tratam de duração, reajustes salariais, jornada, pensão, plano de saúde e outros.
- **Classe:** 37 `good` (65%) e 20 `bad` (35%). O ZeroR, que sempre prevê `good`, vai acertar cerca de 65%. Esse é o mínimo que um modelo precisa superar.
- **A base é muito pequena.** Em cada parte da validação cruzada ficam só 5 ou 6 casos de teste. Por isso as estimativas vão variar bastante, e diferenças entre modelos dificilmente vão aparecer como significativas.
- **Faltam muitos valores:**
  - `standby-pay`: 84% ausentes
  - `wage-increase-third-year`: 74%
  - `education-allowance`: 61%
  - `pension`: 53%
  - `longterm-disability`: 51%

  Isso pode ter um significado. Se o acordo não menciona o item, talvez ele simplesmente não exista naquele acordo. Vou usar algoritmos que lidam com ausentes (J48, NaiveBayes, RandomForest etc.) e informar como cada um os trata. Não vou apagar esses atributos nem preencher os valores sem antes conversar com você.

## Preciso que você responda antes de eu modelar

Você quer **prever** a classe de acordos novos. Nesse caso a escolha do "melhor modelo" depende de quanto custa cada tipo de erro. Os dados não dizem isso, só você pode dizer:

1. **Qual é a classe de interesse?** Sugiro `bad` (acordo ruim), porque normalmente é o caso que se quer detectar.
2. **Qual erro custa mais?**
   - (a) Classificar como **bom** um acordo que na verdade é **ruim** (deixar passar).
   - (b) Classificar como **ruim** um acordo que na verdade é **bom** (alarme falso).
3. **Quantas vezes mais?** Por exemplo, "deixar passar um acordo ruim é 3 vezes pior que um alarme falso".

Com a resposta, monto a matriz de custo e uso o **custo total** como métrica principal, definida antes de ver os resultados.

**Se você não souber ou preferir não definir custos**, considero os dois erros equivalentes e uso o **F1 da classe `bad`** como métrica principal. Também posso ajudar a pensar na proporção a partir do contexto do seu trabalho.

## O que vem depois da sua resposta

Os modelos que pretendo testar são ZeroR (linha de base), J48, JRip, NaiveBayes, IBk (com o k escolhido por validação interna), SMO (com `-M`) e RandomForest. Todos vão rodar com validação cruzada estratificada de 10 partes e semente 1. Em seguida vem o teste t pareado corrigido, comparando o melhor modelo com a linha de base e com o segundo colocado.

Por enquanto **nenhum modelo foi rodado**, então ainda não tenho nenhum número de desempenho.


### Usuário

Os dois erros custam o mesmo.

- `Bash`: `python3 ferramentas/significancia.py --help 2>&1 | grep -v JAVA; python3 ferramentas/weka_runner.py 2>&1 | grep -v -i java | head -30`

### Agente

Métrica principal, definida agora, antes de qualquer resultado: **F1 da classe `bad`**, com os dois erros tratados como equivalentes. Vou rodar os candidatos.

- `Bash`: `for c in "weka.classifiers.trees.J48 -C 0.25 -M 2" "weka.classifiers.rules.JRip" "weka.classifiers.bayes.NaiveBayes" "weka.classifiers.lazy.IBk -K 15 -X" "weka.classifiers.functions.SMO -M" "weka.classifiers.trees.RandomForest"; do echo "######## $c"; python3 ferramentas/weka_runner.py comparar labo`
- `Bash`: `cd /tmp/copias_validacao/T04_r2/resultados && cat 20261121_142453_854894_classificador.txt | head -80; echo ======; cat 20261121_142453_854894_baseline_ZeroR.txt | grep -A30 "Stratified"`

### Agente

Good. Now let me extract the CV metrics for all six models.

- `Bash`: `for f in $(ls -t *_classificador.txt | head -6 | tac); do echo "## $f"; head -1 $f | sed 's/.*lib\/\* //'; sed -n '/Stratified cross-validation/,$p' $f | grep -E "Correctly|Kappa|^ +[0-9.]+ .* bad$"; done`

### Agente

F1 da classe `bad`: IBk tem 0,872 e NaiveBayes tem 0,857, as duas mais altas. Agora rodo os dois testes de significância: IBk contra ZeroR e IBk contra NaiveBayes.

- `Bash`: `cd /tmp/copias_validacao/T04_r2 && grep -i -E "k=|neighbour|nearest" resultados/20261121_142451_922225_classificador.txt | head; python3 ferramentas/significancia.py labor.arff --a weka.classifiers.lazy.IBk --opcoes-a="-K 15 -X" --b weka.classifiers.rules.ZeroR --positiva bad --repeticoes 10 2>&1 | `

### Agente

O teste contra o ZeroR não conseguiu calcular o F1, porque a precisão do ZeroR para `bad` fica indefinida: ele nunca prevê `bad`. Explico isso na resposta. Agora rodo IBk contra NaiveBayes.

- `Bash`: `python3 ferramentas/significancia.py labor.arff --a weka.classifiers.lazy.IBk --opcoes-a="-K 15 -X" --b weka.classifiers.bayes.NaiveBayes --positiva bad --repeticoes 10 2>&1 | grep -A8 "Resumo por métrica"`

### Agente

Os dois ficaram em empate técnico. Vou recomendar o NaiveBayes, que é o mais simples, por isso também testo o NaiveBayes contra o ZeroR.

- `Bash`: `python3 ferramentas/significancia.py labor.arff --a weka.classifiers.bayes.NaiveBayes --b weka.classifiers.rules.ZeroR --positiva bad --repeticoes 10 2>&1 | grep -A8 "Resumo por métrica"; ls -t resultados | head -1`
- `Bash`: `python3 -c "
from math import sqrt
n=57;z=1.96
for m,a in [('ZeroR',37),('J48',42),('JRip',44),('NaiveBayes',51),('IBk',52),('SMO',50),('RandomForest',51)]:
    p=a/n; c=p+z*z/(2*n); r=z*sqrt(p*(1-p)/n+z*z/(4*n*n)); d=1+z*z/n
    print(f'{m}: {p:.3f} IC95% Wilson [{(c-r)/d:.3f}, {(c+r)/d:.3f}]')
" |`

### Agente

# O melhor modelo para prever se um acordo trabalhista é bom ou ruim

**Recomendo o NaiveBayes.** Ele e o IBk acertam mais que os outros modelos, mas a diferença entre os dois não é significativa. O NaiveBayes é o mais simples e o mais barato, por isso fica com ele. Há uma ressalva sobre o teste: o F1, que era a métrica principal, não pôde ser testado pela ferramenta. A decisão se apoia no teste da acurácia, como explico no item 4.

## 1. O que foi feito
- **Base:** `labor.arff`, com 57 acordos (37 `good` e 20 `bad`). A base não foi alterada. Os valores ausentes ficaram com cada algoritmo: J48 e RandomForest dividem o caso entre os ramos, o NaiveBayes ignora o atributo ausente, o SMO usa a média ou a moda e o IBk supõe a maior diferença possível.
- **Métrica principal, escolhida antes de ver os resultados:** F1 da classe `bad`. Como você disse que os dois erros custam o mesmo, não há matriz de custo.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1. Os números abaixo vêm só do bloco de validação cruzada.
- **Comandos:** `python3 ferramentas/weka_runner.py comparar labor.arff <classificador> [opções]` para cada modelo:
  - `J48 -C 0.25 -M 2`
  - `JRip`
  - `NaiveBayes`
  - `IBk -K 15 -X` (a validação interna escolheu **k = 3**)
  - `SMO -M`
  - `RandomForest`

## 2 e 3. Resultados no Weka, comparados com o ZeroR

Recall, precisão e F1 são da classe `bad`.

| Modelo | Acurácia (IC 95%) | Kappa | Recall | Precisão | **F1** | AUC |
|---|---|---|---|---|---|---|
| ZeroR | 0,649 [0,519–0,760] | 0 | 0,000 | – | – | 0,472 |
| J48 | 0,737 [0,610–0,834] | 0,442 | 0,700 | 0,609 | 0,651 | 0,695 |
| JRip | 0,772 [0,648–0,862] | 0,494 | 0,650 | 0,684 | 0,667 | 0,779 |
| **NaiveBayes** | 0,895 [0,789–0,951] | 0,774 | 0,900 | 0,818 | **0,857** | 0,965 |
| **IBk (k=3)** | 0,912 [0,811–0,962] | 0,805 | 0,850 | 0,895 | **0,872** | 0,947 |
| SMO -M | 0,877 [0,768–0,939] | 0,734 | 0,850 | 0,810 | 0,829 | 0,811 |
| RandomForest | 0,895 [0,789–0,951] | 0,764 | 0,800 | 0,889 | 0,842 | 0,943 |

**Matriz de confusão do NaiveBayes** (linhas = classe real, colunas = classe prevista):
```
  bad good
   18    2   bad   → deixou passar 2 acordos ruins
    4   33   good  → 4 alarmes falsos
```
O ZeroR prevê `good` para todos os acordos e nunca identifica um acordo ruim. Os quatro melhores modelos ficam bem acima dele. Os intervalos de confiança são largos, de cerca de ±8 pontos, porque a base tem só 57 casos.

## 4. Confiabilidade: testes de significância
Usei o teste t pareado corrigido com 10 repetições de validação cruzada de 10 partes. Fiz três comparações:

| Comparação | Acurácia | p | Conclusão |
|---|---|---|---|
| IBk × ZeroR | 0,905 × 0,647 | < 0,001 | IBk significativamente melhor |
| NaiveBayes × ZeroR | 0,936 × 0,647 | < 0,001 | NaiveBayes significativamente melhor |
| IBk × NaiveBayes | 0,905 × 0,936 | 0,434 | **empate técnico** |

**Ressalva importante:** a ferramenta não conseguiu calcular o p do F1 em nenhuma das comparações.
- Algumas partes de teste têm só 2 acordos ruins. Quando um modelo não prevê nenhum `bad` numa parte, a precisão fica indefinida (0 ÷ 0). No ZeroR isso acontece sempre; no IBk, em algumas partes.
- Por isso a conclusão se apoia na **acurácia**. Como os dois erros custam o mesmo, maximizar a acurácia equivale a minimizar o custo total, então ela responde à sua pergunta.
- As médias de F1 também não favorecem o IBk. Nas repetições, o NaiveBayes teve F1 médio de 0,912. O IBk só teve F1 calculável em parte das divisões, e lá ficou 0,033 abaixo.

Por que escolher o NaiveBayes no empate:
- é o mais simples e rápido;
- não depende da escolha de k;
- lida melhor com tantos valores ausentes;
- tolera atributos irrelevantes, enquanto o IBk se prejudica com eles.

Testei 6 configurações. O desempenho do vencedor, escolhido entre várias, tende a ser um pouco otimista.

## 5. Interpretação
O NaiveBayes é só parcialmente interpretável. Ele mostra quanto cada atributo muda a probabilidade de o acordo ser ruim, mas não gera regras legíveis. Se o objetivo fosse **entender** o que torna um acordo ruim, J48 e JRip produzem regras, mas ficam cerca de 15 pontos de acurácia abaixo. Essa diferença é o preço da legibilidade nesta base.

## 6. Alertas e próximos passos
- **Base pequena (57 casos):** as estimativas variam muito. Trate a acurácia de cerca de 90% como "algo entre 79% e 95%".
- **Muitos valores ausentes:** alguns atributos têm de 50% a 84% de ausentes, e não sei se ausente significa "o acordo não prevê o item". Seria útil confirmar isso com quem conhece os dados.
- **O que não rodei:**
  - NaiveBayes com `-K` ou `-D`, que seria útil se os atributos numéricos não tiverem distribuição normal. Não verifiquei isso.
  - Seleção de atributos para o IBk.
  - MultilayerPerceptron, por causa da base pequena.
- **Limitação da ferramenta:** `significancia.py` não testa o F1 quando ele fica indefinido em alguma parte. Para corrigir, a ferramenta poderia calcular o F1 juntando as previsões de cada repetição em vez de calcular parte a parte. Pela regra do projeto, só altero a ferramenta com sua autorização, acrescentando o teste de aceite e rodando todos os testes antes de usar. Quer que eu faça isso?

**Arquivos em `resultados/`:**
- saídas de cada modelo: `20261121_1424*_classificador.txt`
- testes de significância: `20261121_142710_*`, `20261121_143115_*` e `20261121_143447_*_significancia.txt`
- intervalos de confiança: `20261121_labor_ic_acuracia.txt`

