# Transcrição T02_r1

### Usuário

Quero prever recorrência do câncer de mama com essa base (breast-cancer.arff). Qual algoritmo devo usar?


### Agente

Antes de qualquer análise, vou ler o manual de decisões e localizar a base.

- `Bash`: `ls; ls dados ferramentas; wc -l conhecimento/manual_decisoes.md; find / -name "breast-cancer.arff" 2>/dev/null | head`
- `Read`: `/tmp/copias_validacao/T02_r1/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/breast-cancer.arff`
- `Bash`: `python3 ferramentas/weka_runner.py resumo breast-cancer.arff; ls resultados | tail -5`
- `Read`: `/tmp/copias_validacao/T02_r1/conhecimento/manual_decisoes.md`

### Agente

O resumo do Weka não mostra a distribuição da classe nem os valores de cada atributo. Vou montar o perfil completo em Python e registrar o script.

- `Bash`: `grep -i "@attribute" dados/breast-cancer.arff; ls analises/scripts | head`
- `Bash`: `mkdir -p analises/scripts && cat > analises/scripts/20261121_perfil_breast_cancer.py <<'EOF'
# Perfil descritivo da base breast-cancer.arff (somente contagens; nenhum modelo).
# Uso: python3 analises/scripts/20261121_perfil_breast_cancer.py
import csv, io
from collections import Counter

caminho = "`

### Agente

## Resposta curta: ainda não dá para escolher o algoritmo

Ninguém deveria escolher o algoritmo antes de rodar. Nenhum algoritmo é o melhor em todas as bases. O jeito certo é testar alguns candidatos que combinam com os dados, nas mesmas condições, e decidir pelo resultado comparado com o ZeroR (o modelo que sempre chuta a classe mais comum). Antes de rodar, porém, preciso de uma informação que só você tem: **quanto custa cada tipo de erro.** Explico abaixo.

## O que já fiz: explorei a base (nenhum modelo rodou ainda)

- Resumo no Weka: `python3 ferramentas/weka_runner.py resumo breast-cancer.arff`
- Perfil dos atributos em Python. O script está em `analises/scripts/20261121_perfil_breast_cancer.py` e a saída em `resultados/20261121_perfil_breast_cancer.txt`.

**O que encontrei:**

| Ponto | Achado | Consequência |
|---|---|---|
| Tamanho | 286 pacientes, 9 atributos e a classe | A base é pequena, então as estimativas vão oscilar bastante e os intervalos de confiança vão sair largos. |
| Classe | 201 `no-recurrence-events` (70,3%) e 85 `recurrence-events` (29,7%) | Um modelo que diga sempre "não recorre" já acerta cerca de 70%. Por isso a acurácia sozinha engana aqui. |
| Tipos | Todos os atributos são nominais. Idade, tamanho do tumor e linfonodos (`inv-nodes`) vêm em faixas, e o grau de malignidade (`deg-malig`) em 1, 2 e 3. | São atributos com ordem, mas o Weka vai tratá-los como categorias soltas e perde essa ordem. Vou deixar isso registrado como limitação. |
| Categorias raras | `tumor-size` tem 11 faixas, algumas com 3 a 4 casos. `inv-nodes` tem faixas com 1 a 3 casos. | A árvore pode criar ramos apoiados em poucos casos. Isso favorece poda forte e modelos robustos a ruído. |
| Ausentes | 8 em `node-caps` e 1 em `breast-quad` | É pouco. Os algoritmos conseguem lidar com isso sem imputação. |
| Repetições | 14 registros idênticos a outros | Como tudo é faixa, dois pacientes diferentes podem coincidir. Se forem o mesmo paciente digitado duas vezes, a avaliação fica otimista. |
| Conflitos | 6 combinações de atributos aparecem com as duas classes | Há pacientes com o mesmo perfil e desfechos diferentes. Nenhum modelo acerta todos esses casos, o que sugere que os atributos explicam a recorrência só em parte. |

## Os candidatos que vou testar, e por quê

Como o objetivo é **prever**, a lista é esta, sempre com o ZeroR como referência:

- **J48 (árvore)**, com poda. É legível e tolera ruído.
- **JRip (regras)**. Ele começa pela classe rara, que aqui é a recorrência.
- **NaiveBayes**. Costuma ir bem em bases pequenas com ruído e não sofre com atributos irrelevantes.
- **IBk (vizinhos mais próximos)**, com o k escolhido por validação interna (`-X`), e não pelo resultado do teste.
- **SMO (SVM)**, com a opção `-M` para que a AUC tenha sentido.
- **RandomForest**, como referência de teto.

Deixo de fora a rede neural (MultilayerPerceptron): com 286 casos o risco de sobreajuste é alto e não há ganho esperado.

## O que preciso saber de você antes de modelar

1. **A classe de interesse é `recurrence-events` (recorrência)?** Imagino que sim.
2. **Qual erro custa mais, e quantas vezes mais?**
   - **Falso negativo:** o modelo diz "não vai recorrer" e a paciente recorre. Ela pode ficar sem o acompanhamento que precisava.
   - **Falso positivo:** o modelo diz "vai recorrer" e ela não recorre. Isso gera acompanhamento ou tratamento a mais, além de ansiedade.

   Preciso de uma proporção, por exemplo "deixar passar uma recorrência custa 3 vezes mais que um alarme falso". Com ela monto a matriz de custo, e o custo total passa a ser a métrica que decide qual modelo é melhor. Se você não tiver um número, posso propor um e explicar de onde ele veio, para você confirmar ou ajustar.
3. **Os 14 registros repetidos são pacientes diferentes ou cópias?** Se você não souber, rodo a base original como análise principal e a base sem repetições como cenário alternativo, e mostro se a conclusão muda.

Com essas respostas, rodo todos os candidatos com validação cruzada estratificada de 10 partes e semente 1. Depois comparo o melhor com a linha de base, e o melhor com o segundo melhor, usando o teste de significância.


### Usuário

Deixar de prever uma recorrência é 3 vezes pior que um alarme falso.

- `Bash`: `sed -n 1,80p ferramentas/weka_runner.py; grep -n "def \|add_argument\|custo" ferramentas/weka_runner.py | head -60`
- `Bash`: `grep -n "def \|add_argument\|custo\|print" ferramentas/significancia.py | head -80`
- `Bash`: `sed -n 160,240p ferramentas/weka_runner.py; sed -n 170,206p ferramentas/significancia.py; sed -n 366,400p ferramentas/significancia.py; sed -n 494,530p ferramentas/significancia.py; echo $WEKA_CP`
- `Bash`: `grep -n "CLASSIFICADOR_CUSTO\|WEKA_JAR =" ferramentas/significancia.py; grep -n "breast\|custo\|-M" conhecimento/manual_decisoes.md | sed -n 1,5p; ls validacao | head; git log --oneline | head -5`
- `Bash`: `CM="[0.0 1.0; 3.0 0.0]"; CS=weka.classifiers.meta.CostSensitiveClassifier
run(){ echo "=== $1"; python3 ferramentas/weka_runner.py comparar breast-cancer.arff $CS -cost-matrix "$CM" -S 1 -W "${@:2}" > /dev/null 2>&1; ls -t resultados/*classificador*.txt | head -1; }
run J48 weka.classifiers.trees.J4`
- `Bash`: `for f in resultados/20261121_14144{1_152823,1_977932,2_830523,3_675835,4_731769,5_918472}_classificador.txt resultados/20261121_141445_918472_baseline_ZeroR.txt; do echo "##### $f"; head -1 $f | cut -c1-400; awk '/=== Stratified cross-validation ===/{p=1} p' $f | grep -v "^$"; done`

### Agente

Os seis candidatos já rodaram no Weka. Agora calculo o custo de cada um e rodo os testes de significância, que levam alguns minutos.

- `Bash`: `cat > analises/scripts/20261121_custos_breast_cancer.py <<'EOF'
# Custo total e intervalo de confiança da acurácia, calculados a partir das
# matrizes de confusão da validação cruzada do Weka (arquivos em resultados/).
# Custo: FP (alarme falso) = 1; FN (recorrência não prevista) = 3.
import math
# `

### Agente

NaiveBayes tem o menor custo (152). O segundo menor é o do SMO (173), e a linha de base mais barata custa 201. Agora testo se essas diferenças são reais.

- `Bash`: `python3 ferramentas/significancia.py breast-cancer.arff --a weka.classifiers.bayes.NaiveBayes --b weka.classifiers.rules.ZeroR --custo "0 1; 3 0" --positiva recurrence-events --repeticoes 10 2>&1 | grep -v "Picked up\|Repetição\|repeti"`
- `Bash`: `python3 ferramentas/significancia.py breast-cancer.arff --a weka.classifiers.bayes.NaiveBayes --b weka.classifiers.functions.SMO --opcoes-b=-M --custo "0 1; 3 0" --positiva recurrence-events --repeticoes 10 2>&1 | grep -v "Picked up\|Repetição\|repeti"`
- `Bash`: `grep -i "nearest neighbour" resultados/20261121_141443_675835_classificador.txt; awk '/Error on training data/{p=1} /Stratified cross-validation/{p=0} p' resultados/20261121_141442_830523_classificador.txt | grep -A4 "Correctly\|Confusion"`

### Agente

## Resposta: use o NaiveBayes, ajustado para o custo dos erros

Entre os seis candidatos, o NaiveBayes teve o menor custo: **152, contra 201** da melhor linha de base. A diferença para a linha de base é estatisticamente significativa. Ele não ficou à frente do segundo colocado, o SMO, com significância. Estão em empate técnico, e o NaiveBayes fica com a vaga por ser mais simples e mais rápido.

### 1. O que foi feito

- **Base:** `breast-cancer.arff` original, com 286 casos. Nenhum pré-processamento: os poucos ausentes (9) ficaram por conta de cada algoritmo, e o NaiveBayes simplesmente ignora o atributo que falta.
- **Classe positiva:** `recurrence-events`.
- **Matriz de custo:** `[0 1; 3 0]`. Deixar passar uma recorrência custa 3; um alarme falso custa 1.
- **Métrica principal:** custo total, definida antes de ver os resultados.
- **Ajuste ao custo:** cada candidato rodou dentro do `CostSensitiveClassifier`. Ele dá mais peso aos casos de recorrência no treino, para o modelo aprender que errá-los é mais caro.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1.
- **Comando do modelo escolhido:**
  ```
  python3 ferramentas/weka_runner.py comparar breast-cancer.arff weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 3.0 0.0]" -S 1 -W weka.classifiers.bayes.NaiveBayes
  ```
- **Arquivos:** saídas em `resultados/20261121_1414*_classificador.txt`; custos calculados por `analises/scripts/20261121_custos_breast_cancer.py`.

### 2. Resultado do Weka para o NaiveBayes (validação cruzada)

```
   a   b   <-- classificado como
 133  68 |   a = no-recurrence-events
  28  57 |   b = recurrence-events
```

- **Acurácia:** 66,4%.
- **Kappa:** 0,293, que é um acerto apenas modesto além do acaso.
- **Classe recorrência:** recall 0,671, precisão 0,456, F1 0,543, AUC 0,698.
- **Custo total:** 68 × 1 + 28 × 3 = **152**.

Em palavras: o modelo encontra 57 das 85 recorrências. Para isso, dá 68 alarmes falsos. Mais da metade dos casos que ele aponta como recorrência não recorre.

### 3. Comparação com as linhas de base e os outros candidatos

| Modelo | Custo ↓ | Acurácia (IC 95%) | Kappa | Recall rec. | Precisão rec. | F1 rec. | AUC |
|---|---:|---|---:|---:|---:|---:|---:|
| Prever sempre "não recorre" (ZeroR) | 255 | 70,3% (65,0–75,6) | 0 | 0 | – | – | 0,483 |
| Prever sempre "recorre" | **201** | 29,7% | – | 1,0 | 0,297 | – | – |
| **NaiveBayes** | **152** | 66,4% (61,0–71,9) | 0,293 | 0,671 | 0,456 | 0,543 | 0,698 |
| SMO (`-M`) | 173 | 61,2% (55,5–66,8) | 0,203 | 0,635 | 0,403 | 0,493 | 0,650 |
| IBk (`-K 15 -X`, escolheu k = 13) | 178 | 63,6% (58,1–69,2) | 0,210 | 0,565 | 0,417 | 0,480 | 0,635 |
| JRip | 187 | 59,1% (53,4–64,8) | 0,156 | 0,588 | 0,379 | 0,461 | 0,599 |
| RandomForest | 197 | 61,9% (56,3–67,5) | 0,148 | 0,482 | 0,387 | 0,429 | 0,629 |
| J48 | 198 | 55,9% (50,2–61,7) | 0,109 | 0,576 | 0,353 | 0,437 | 0,553 |

A linha de base que importa é a de custo **201** (prever que todas recorrem), não a de acurácia 70%. O ZeroR tem a maior acurácia da tabela porque nunca prevê recorrência, mas é o mais caro de todos. É um exemplo concreto de como a acurácia engana aqui.

Todos os seis candidatos ficaram abaixo de 201, então nenhum é pior que não ter modelo. Mas J48 (198) e RandomForest (197) quase empatam com a regra trivial de "acompanhar todas". Na prática, não acrescentam nada.

### 4. Confiabilidade

Rodei duas comparações, com o teste t pareado corrigido, 10 repetições da validação cruzada de 10 partes, na métrica custo:

| Comparação | Custo médio por partição | p | Conclusão |
|---|---|---:|---|
| NaiveBayes × linha de base "tudo recorre" | 15,7 × 20,1 | **0,006** | NaiveBayes é **significativamente mais barato** |
| NaiveBayes × SMO | 15,7 × 17,0 | 0,199 | **Empate técnico** |

- Os outros pares não testei, para não multiplicar testes.
- A escolha final saiu do melhor de 6 configurações, então o custo de 152 tende a ser um pouco otimista.
- Os intervalos de confiança têm cerca de ±5,5 pontos, por causa dos 286 casos. Pequenas diferenças na tabela não querem dizer nada.

### 5. Interpretação

- **Por que o NaiveBayes se sai melhor:** a base é pequena e ruidosa. Seis combinações de atributos aparecem com as duas classes, e há várias categorias com 1 a 4 casos. O NaiveBayes estima cada atributo separadamente, então não depende de combinações raras. Árvores e regras, ao contrário, picotam os dados em grupos pequenos e caem para o fim da lista.
- **Sem sinal de sobreajuste:** no próprio treino, o custo do NaiveBayes foi 140, contra 152 na validação. A distância é pequena.
- **Limite das probabilidades:** o modelo é bom para ordenar pacientes por risco, mas a probabilidade que ele dá a cada paciente não deve ser lida ao pé da letra.

### 6. Alertas e próximos passos

- **O teto é baixo.** Com kappa de 0,29 e AUC de 0,70, os atributos explicam a recorrência só em parte. O modelo serve para priorizar o acompanhamento, não para decidir sozinho.
- **Atributos possivelmente redundantes:** `inv-nodes`, `node-caps` e `irradiat` provavelmente andam juntos (linfonodos afetados levam à irradiação). O NaiveBayes contaria essa evidência em dobro. Não testei seleção de atributos; esse seria o próximo passo, com `AttributeSelectedClassifier`.
- **A ordem das faixas se perde.** Idade, tamanho do tumor e linfonodos são faixas ordenadas, mas foram tratadas como categorias soltas.
- **Repetições ainda pendentes:** você não respondeu sobre os 14 registros repetidos, e eu não rodei a análise de sensibilidade sem eles. Se forem cópias do mesmo paciente, os resultados acima ficam um pouco otimistas. Posso rodar esse cenário.
- **Não executado:** MultilayerPerceptron (base pequena demais), variações de parâmetros e o ajuste ao custo por limiar de decisão (`-M` do `CostSensitiveClassifier`), que é uma alternativa à reponderação usada aqui.
- **A proporção de 3 para 1 é sua.** Se ela mudar, por exemplo para 5 para 1, a ordem dos modelos pode mudar, e vale rodar de novo.

