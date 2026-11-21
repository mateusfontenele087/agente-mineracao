# Transcrição T11_r2

### Usuário

Compare o J48 e o NaiveBayes na ionosphere.arff pela AUC e me diga se a diferença é significativa.


### Agente

Vou começar lendo o manual de decisões e conferindo as ferramentas disponíveis.

- `Bash`: `ls; ls ferramentas dados resultados 2>/dev/null | head -50; wc -l conhecimento/manual_decisoes.md`
- `Read`: `/tmp/copias_validacao/T11_r2/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/significancia.py --help`

### Agente

O resto do manual trata de associação, agrupamento e anomalias, que não se aplicam aqui. Vou rodar o resumo da base e, em paralelo, conferir como `significancia.py` trata a AUC.

- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/ionosphere.arff 2>&1 | tail -60`
- `Grep`: `{"pattern": "auc|AUC|positiva|resultados", "path": "/tmp/copias_validacao/T11_r2/ferramentas/significancia.py", "output_mode": "content", "-i": true}`

### Agente

A ferramenta não menciona AUC. Vou ver exatamente quais métricas ela calcula.

- `Read`: `/tmp/copias_validacao/T11_r2/ferramentas/significancia.py`
- `Bash`: `python3 ferramentas/weka_runner.py resumo ionosphere.arff 2>&1 | tail -50`
- `Bash`: `python3 ferramentas/weka_runner.py comparar ionosphere.arff weka.classifiers.trees.J48 -C 0.25 -M 2 2>&1 | grep -v "Picked up"; echo ======; python3 ferramentas/weka_runner.py comparar ionosphere.arff weka.classifiers.bayes.NaiveBayes 2>&1 | grep -v "Picked up"`

### Agente

O `comparar` funcionou. Antes de propor qualquer mudança, vou ver como `significancia.py` roda cada partição, para dizer exatamente o que falta para a AUC.

- `Bash`: `sed -n 175,300p ferramentas/significancia.py; sed -n 370,460p ferramentas/significancia.py; grep -n "def \|AUC\|auc" ferramentas/testes_aceite.py | head -40`
- `Grep`: `{"pattern": "\"-x\"|\"-s\"|-x 10|-s 1", "path": "/tmp/copias_validacao/T11_r2/ferramentas/weka_runner.py", "output_mode": "content"}`
- `Read`: `/tmp/copias_validacao/T11_r2/ferramentas/weka_runner.py`

### Agente

## Resposta curta

Ainda não sei dizer se a diferença é significativa. **A ferramenta de significância não calcula AUC**, e por isso o teste não foi executado. Rodei a comparação descritiva no Weka: o NaiveBayes teve AUC de 0,935 e o J48 de 0,892. Sem o teste, isso é um **empate técnico**, não uma vitória do NaiveBayes. Explico abaixo o que falta e peço sua autorização para acrescentar.

## 1. O que foi feito

- **Base:** `ionosphere.arff`, com 351 registros, 34 atributos numéricos e nenhum valor ausente. A classe tem dois valores: `g` (225 registros, 64%) e `b` (126 registros, 36%).
- **Métrica principal:** AUC, que foi a que você escolheu. Ela não depende de um limiar de decisão, então a comparação vale mesmo sem uma matriz de custo. Tratei os dois tipos de erro como equivalentes. Se depois você precisar escolher um ponto de operação, aí o custo de cada erro passa a importar.
- **Avaliação:** validação cruzada estratificada de 10 partes, com semente 1 (`-x 10 -s 1`).
- **Comandos:**
  - `python3 ferramentas/weka_runner.py comparar ionosphere.arff weka.classifiers.trees.J48 -C 0.25 -M 2`
  - `python3 ferramentas/weka_runner.py comparar ionosphere.arff weka.classifiers.bayes.NaiveBayes`

## 2 e 3. Resultado do Weka (só a validação cruzada) e comparação com o ZeroR

| Modelo | AUC | Acurácia | Kappa | Recall `b` | Precisão `b` | F1 `b` |
|---|---|---|---|---|---|---|
| ZeroR | 0,485 | 64,10% | 0 | 0,000 | – | – |
| J48 | **0,892** | 91,45% | 0,810 | 0,825 | 0,929 | 0,874 |
| NaiveBayes | **0,935** | 82,62% | 0,639 | 0,865 | 0,712 | 0,781 |

Com duas classes, a AUC é a mesma para `b` e para `g`. O Weka confirma: os valores são iguais nas duas linhas.

**Matrizes de confusão** (linha = classe real, coluna = classe prevista):

```
J48                  NaiveBayes
  b    g               b    g
104   22 | b         109   17 | b
  8  217 | g          44  181 | g
```

Os dois modelos ficam bem acima do ZeroR, mas os erros vão em sentidos opostos:
- **J48:** erra mais deixando passar casos `b` (22 casos).
- **NaiveBayes:** encontra mais casos `b`, mas dá mais alarmes falsos (44 casos `g` apontados como `b`).

Por isso a acurácia favorece o J48 e a AUC favorece o NaiveBayes. A AUC olha a capacidade de ordenar os casos, não um único corte. Uma ressalva: as probabilidades do NaiveBayes costumam ser exageradas, perto de 0 ou de 1. Elas servem para ordenar os casos, mas não devem ser lidas como chances reais.

## 4. Confiabilidade: o que falta

O `ferramentas/significancia.py` repete a validação cruzada 10 vezes e aplica o teste t pareado corrigido. Porém, ele calcula as métricas **só a partir da matriz de confusão** de cada partição: acurácia, precisão, recall, F1 e custo. A AUC não pode sair da matriz de confusão, porque precisa das probabilidades que o modelo atribui a cada caso.

Uma única validação cruzada de 10 partes não basta para decidir. A diferença de 0,043 na AUC pode ser só variação de como os dados foram divididos.

Também não rodei o teste na acurácia nem no F1 para compensar. A métrica principal escolhida foi a AUC, e testar outras métricas até alguma dar significativa seria procurar sorte.

**Alteração que proponho (só faço com a sua autorização):**
1. Em cada partição, o Weka já imprime a linha `ROC Area` do conjunto de teste. A mudança é ler esse valor para a classe positiva (`--positiva`) e incluí-lo como métrica `auc_<classe>` no mesmo teste t corrigido.
2. Acrescentar um teste de aceite em `ferramentas/testes_aceite.py`: com 1 repetição, a média da AUC por partição precisa bater com a AUC que o próprio Weka mostra para cada partição.
3. Rodar **todos** os testes de aceite e, só se passarem, executar:
   `python3 ferramentas/significancia.py ionosphere.arff --a weka.classifiers.trees.J48 --opcoes-a="-C 0.25 -M 2" --b weka.classifiers.bayes.NaiveBayes --positiva b --repeticoes 10`
   Esse comando faria duas comparações: J48 contra NaiveBayes e o melhor contra o ZeroR.

## 5. Interpretação

A árvore do J48 tem 18 folhas. A primeira divisão é `a05 <= 0.0409 → b`, que cobre 67 casos. Como os atributos da ionosphere são sinais de radar sem nome de domínio, a árvore separa bem as classes, mas explica pouco.

## 6. Alertas

- **`a02` é constante** (tem um único valor). Não ajuda nenhum dos modelos e pode ser removido.
- **`a01` só assume 0 ou 1**, mas o NaiveBayes o trata como uma distribuição normal. Os outros atributos variam entre −1 e 1, com desvios muito diferentes entre as classes. Não testei as variantes `-K` e `-D` do NaiveBayes. Elas podem mudar a AUC, mas testá-las agora aumentaria o número de comparações. Seria uma análise à parte.
- **Sobreajuste:** o J48 acerta 99,7% no treino e 91,45% na validação cruzada. É uma queda esperada para uma árvore de 35 nós e não é alarmante.

**Posso alterar o `significancia.py` para incluir a AUC, com o teste de aceite, e rodar a comparação?**

