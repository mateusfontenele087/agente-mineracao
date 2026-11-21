# Transcrição T04

### Usuário

Qual o melhor modelo para prever se um acordo trabalhista é bom ou ruim? Base labor.arff.


### Agente

Vou começar lendo o manual de decisões e localizando a base.

- `Bash`: `ls; ls dados ferramentas resultados 2>/dev/null | head -50; wc -l conhecimento/manual_decisoes.md; find / -name "labor.arff" 2>/dev/null | head`
- `Read`: `/home/user/agente-mineracao/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/labor.arff`

### Agente

As partes restantes do manual tratam de associação, agrupamento e anomalias, e não se aplicam aqui. Agora o resumo da base:

- `Bash`: `python3 ferramentas/weka_runner.py resumo labor.arff; cat dados/labor.arff | grep -v "^%" | head -80`

### Agente

A base tem 57 registros e 16 atributos, com muitos valores ausentes. Vou ver como as ferramentas funcionam e montar o perfil descritivo.

- `Bash`: `sed -n 1,80p ferramentas/significancia.py; grep -n "argparse\|add_argument\|def \|metric\|auc\|AUC\|f1" ferramentas/significancia.py | head -80; grep -n "def \|sys.argv\|-x\|-s " ferramentas/weka_runner.py | head -40`
- `Bash`: `sed -n 100,160p ferramentas/significancia.py; sed -n 196,270p ferramentas/significancia.py; sed -n 40,80p ferramentas/weka_runner.py`
- `Bash`: `ls analises validacao; git log --oneline | head -5; ls resultados | tail -5`
- `Bash`: `ls analises/scripts; head -40 analises/scripts/* | head -80`

### Agente

I'll write the descriptive profile script for labor (counts and quartiles only, no models).

- `Write`: `/home/user/agente-mineracao/analises/scripts/perfil_labor.py`
- `Bash`: `python3 analises/scripts/perfil_labor.py`
- `Bash`: `for c in "weka.classifiers.trees.J48 -C 0.25 -M 2" "weka.classifiers.rules.JRip" "weka.classifiers.bayes.NaiveBayes" "weka.classifiers.bayes.NaiveBayes -K" "weka.classifiers.lazy.IBk -K 15 -X" "weka.classifiers.functions.SMO -M" "weka.classifiers.trees.RandomForest"; do echo "#### $c"; python3 ferra`

### Agente

Agora leio o bloco de validação cruzada de cada arquivo (ignorando o desempenho no treino):

- `Bash`: `cd /home/user/agente-mineracao/resultados && for f in 20261121_132645_680200_baseline_ZeroR.txt 20261121_1326{45_680200,46_475672,47_358484,48_051362,48_835118,49_781440,51_239623}_classificador.txt; do echo "################ $f"; head -3 $f | grep -i "comando\|java" | cut -c1-200; awk '/=== Stratif`

### Agente

Os números vêm todos do bloco de validação cruzada. Vejo qual k o IBk escolheu por validação interna:

- `Bash`: `grep -n "nearest neighbour\|using [0-9]* nearest" 20261121_132648_835118_classificador.txt; grep -n "Comando" 20261121_132648_835118_classificador.txt | cut -c1-400`
- `Bash`: `cd /home/user/agente-mineracao && python3 ferramentas/significancia.py labor.arff --a weka.classifiers.lazy.IBk --opcoes-a="-K 15 -X" --b weka.classifiers.rules.ZeroR --positiva bad --repeticoes 10 2>&1 | grep -v "Picked up" | tail -25; echo =========; python3 ferramentas/significancia.py labor.arff`
- `Bash`: `python3 ferramentas/significancia.py labor.arff --a weka.classifiers.bayes.NaiveBayes --b weka.classifiers.rules.ZeroR --positiva bad --repeticoes 10 2>&1 | grep -v "Picked up" | tail -7; python3 - <<'EOF'
# Intervalo de confiança de 95% (Wilson) para a acurácia da validação cruzada do Weka.
# Entra`

### Agente

Por último, veja as médias por classe que o NaiveBayes aprendeu, para a interpretação:

- `Bash`: `cd /home/user/agente-mineracao/resultados && awk '/Naive Bayes Classifier/{f=1} /Time taken/{f=0} f' 20261121_132647_358484_classificador.txt | sed -n 1,40p`

### Agente

# Melhor modelo para prever se um acordo trabalhista é bom ou ruim (labor.arff)

**Resposta curta:** recomendo o **NaiveBayes**. Ele, o IBk (k-NN) e a RandomForest ficaram estatisticamente empatados, perto de 90% de acerto, contra 65% da linha de base (ZeroR). No empate fico com o mais simples, e o NaiveBayes lida bem com os muitos valores ausentes desta base.

**Suposição que adotei.** As classes estão moderadamente desbalanceadas: 37 acordos bons (65%) e 20 ruins (35%). Como você não disse qual erro custa mais, defini **antes de ver os resultados** a **acurácia** como métrica principal. Tentei também o F1 da classe "bad", mas cada parte da validação tem só 2 acordos ruins. Assim, quando um modelo não aponta nenhum "bad" numa parte, a precisão fica indefinida e a ferramenta não consegue testar o F1. Se deixar passar um acordo ruim custar mais que um alarme falso, me diga **quantas vezes mais**: com isso eu refaço a análise com uma matriz de custo.

## 1. O que foi feito
- **Exploração:** são 57 acordos e 16 atributos. Não há registros duplicados nem ausentes disfarçados: o único zero, em `shift-differential`, é plausível (adicional de turno igual a 0). Há **muitos ausentes explícitos**: `standby-pay` 84%, `wage-increase-third-year` 74%, `education-allowance` 61%, `pension` 53%. Os ausentes ficaram como estão, e cada algoritmo trata ausentes do seu jeito.
- **Perfil descritivo:** script `analises/scripts/perfil_labor.py`, saída em `resultados/20261121_132640_perfil_labor.txt`.
- **Candidatos:** como o objetivo é prever, testei J48, JRip, NaiveBayes (padrão e `-K`), IBk com `-K 15 -X` (k escolhido por validação interna; o escolhido foi k = 3), SMO `-M` e RandomForest, todos comparados com o ZeroR.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1. Exemplo de comando:
  `python3 ferramentas/weka_runner.py comparar labor.arff weka.classifiers.bayes.NaiveBayes`
  (internamente: `java ... weka.classifiers.bayes.NaiveBayes -t dados/labor.arff -x 10 -s 1`)

## 2–3. Resultados do Weka (só o bloco da validação cruzada), com o ZeroR

| Modelo | Acurácia | IC 95% | Kappa | Recall bad | Precisão bad | F1 bad | AUC |
|---|---|---|---|---|---|---|---|
| **ZeroR** (linha de base) | 64,9% | 51,9–76,0 | 0 | 0,000 | – | – | 0,472 |
| J48 | 73,7% | 61,0–83,4 | 0,44 | 0,700 | 0,609 | 0,651 | 0,695 |
| JRip | 77,2% | 64,8–86,2 | 0,49 | 0,650 | 0,684 | 0,667 | 0,779 |
| **NaiveBayes** | 89,5% | 78,9–95,1 | 0,77 | 0,900 | 0,818 | 0,857 | 0,965 |
| NaiveBayes `-K` | 89,5% | 78,9–95,1 | 0,78 | 0,950 | 0,792 | 0,864 | 0,970 |
| IBk (k = 3) | 91,2% | 81,1–96,2 | 0,81 | 0,850 | 0,895 | 0,872 | 0,947 |
| SMO `-M` | 87,7% | 76,8–93,9 | 0,73 | 0,850 | 0,810 | 0,829 | 0,811 |
| RandomForest | 89,5% | 78,9–95,1 | 0,76 | 0,800 | 0,889 | 0,842 | 0,943 |

**Matriz de confusão do NaiveBayes:**
```
  a  b   <-- classificado como
 18  2 |  a = bad
  4 33 |  b = good
```
O modelo deixou passar 2 dos 20 acordos ruins e marcou como ruins 4 dos 37 acordos bons.

## 4. Confiabilidade (teste t pareado corrigido, 10 repetições × 10 partes, métrica principal: acurácia)

| Comparação | Média A | Média B | p | Conclusão |
|---|---|---|---|---|
| IBk × ZeroR | 90,5% | 64,7% | < 0,001 | IBk significativamente melhor |
| NaiveBayes × ZeroR | 93,6% | 64,7% | < 0,001 | NaiveBayes significativamente melhor |
| IBk × NaiveBayes | 90,5% | 93,6% | 0,43 | **empate técnico** |

Fiz 3 comparações. Na validação única o IBk ficou na frente, mas na repetida a ordem se inverteu. Essa inversão mostra que a diferença entre eles é ruído. No empate, o NaiveBayes é o mais simples e lida bem com ausentes, porque ignora o atributo que está faltando. A RandomForest, também com 89,5%, não foi testada contra os outros: ela está no mesmo empate, e por ser mais complexa não seria preferida.

## 5. Interpretação (parâmetros reais aprendidos pelo NaiveBayes)
- **O reajuste salarial é o que mais separa as classes.** No 1º ano, a média dos acordos ruins é 2,66% contra 4,38% nos bons. No 2º ano, 2,95% contra 4,45%.
- **Jornada semanal:** um pouco mais longa nos acordos ruins (39,5 h contra 37,5 h).
- O reajuste do 3º ano também difere, mas a média dos ruins vem de apenas 4 acordos, porque o resto está ausente. É evidência fraca.
- As probabilidades do NaiveBayes servem para **ordenar** acordos do mais para o menos arriscado, não como probabilidade literal ("92% de chance de ser ruim").

## 6. Alertas e próximos passos
- **A base é muito pequena (57 registros).** Os intervalos de confiança têm cerca de ±8 a 10 pontos e se sobrepõem entre NaiveBayes, IBk, RandomForest e SMO. A conclusão segura é "há modelo útil, bem acima da linha de base". "Este é o melhor por pouco" não se sustenta.
- **O número do vencedor é otimista.** Testei 7 configurações, e escolher o melhor entre muitos embute um pouco de sorte.
- **A falta de dados pode carregar informação.** `pension` está ausente em 76% dos acordos bons e em só 10% dos ruins. Isso pode refletir como os dados foram coletados, e não o conteúdo dos acordos. Vale perguntar a quem conhece a origem dos dados.
- **J48 e JRip** ficaram visivelmente abaixo (74% e 77%), o que é coerente com uma árvore se fragmentando em poucos dados com muitos ausentes. Essa diferença não foi testada formalmente.
- **NaiveBayes com atributos numéricos:** testei `-K` (estimativa por núcleo) e a acurácia foi a mesma, então a suposição de distribuição normal não prejudicou.
- **O que não foi rodado:**
  - teste de significância na AUC (a ferramenta não calcula AUC por parte);
  - análise com matriz de custo;
  - seleção de atributos;
  - MultilayerPerceptron (a base é pequena demais para uma rede neural);
  - atributos indicadores de ausência.

**Decisões que cabem a você:**
1. Qual erro custa mais, e quantas vezes mais: deixar passar um acordo ruim ou rejeitar um bom? Com isso eu refaço a análise com uma matriz de custo.
2. Quer que eu salve este relatório em `analises/` e faça o commit, como nas análises anteriores?

