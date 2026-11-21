# Transcrição T03_r3

### Usuário

Quero entender o que diferencia democratas de republicanos nessas votações (vote.arff).


### Agente

Vou começar lendo o manual de decisões e localizando a base.

- `Bash`: `ls; ls dados ferramentas analises resultados 2>/dev/null | head -50; wc -l conhecimento/manual_decisoes.md; find / -name "vote.arff" 2>/dev/null | head`
- `Read`: `/tmp/copias_validacao/T03_r3/conhecimento/manual_decisoes.md`
- `Read`: `/tmp/copias_validacao/T03_r3/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/vote.arff 2>&1 | tail -60; head -40 dados/vote.arff | grep -i attribute`
- `Bash`: `python3 ferramentas/weka_runner.py resumo vote.arff 2>&1 | tail -60; grep -n "@attribute\|^%.*[0-9]\." dados/vote.arff | head -60`
- `Read`: `/tmp/copias_validacao/T03_r3/dados/vote.arff`
- `Bash`: `sed -n 51,76p dados/vote.arff; ls analises/scripts 2>/dev/null; sed -n 1,60p ferramentas/weka_runner.py | grep -n "def \|argv\|usage" `
- `Bash`: `python3 ferramentas/significancia.py -h 2>&1 | grep -v JAVA | head -40; grep -n "metric\|métrica" ferramentas/significancia.py | head -30`
- `Bash`: `mkdir -p analises/scripts && cat > analises/scripts/2026-11-21_perfil_vote.py <<'EOF'
# Perfil descritivo da base vote.arff (só contagens; nenhum modelo aqui).
# Uso: python3 analises/scripts/2026-11-21_perfil_vote.py
import collections, datetime

linhas_dados, atributos, lendo = [], [], False
with `

### Agente

Perfil pronto. Agora os modelos no Weka: J48 e JRip (legíveis, foco principal), NaiveBayes (apoio) e RandomForest (só como teto).

- `Bash`: `for c in "weka.classifiers.trees.J48 -C 0.25 -M 2" "weka.classifiers.rules.JRip" "weka.classifiers.bayes.NaiveBayes" "weka.classifiers.trees.RandomForest"; do echo "######## $c"; python3 ferramentas/weka_runner.py comparar vote.arff $c 2>&1 | grep -v "JAVA_\|_JAVA" | tail -8; done; ls -t resultados `

### Agente

Vou ler os arquivos gerados (preciso separar o bloco de validação cruzada do de treino).

- `Bash`: `cd /tmp/copias_validacao/T03_r3/resultados && for f in 20261121_142651_110787_classificador.txt 20261121_142652_122720_classificador.txt; do echo "=========== $f"; grep -v "JAVA_\|_JAVA" $f; done`
- `Bash`: `for f in 20261121_142653_182569_classificador.txt 20261121_142654_157870_classificador.txt; do echo "=========== $f"; head -1 $f; sed -n '/=== Stratified cross-validation ===/,$p' $f; done; echo "=========== ZeroR"; head -1 20261121_142651_110787_baseline_ZeroR.txt; sed -n '/=== Stratified cross-val`
- `Bash`: `cd /tmp/copias_validacao/T03_r3 && python3 ferramentas/weka_runner.py comparar vote.arff weka.classifiers.rules.OneR -B 6 2>&1 | grep -v "JAVA_\|_JAVA" | tail -3; f=$(ls -t resultados/*_classificador.txt | head -1); head -1 $f; sed -n '/=== Classifier model/,/Time taken to build/p' $f; sed -n '/=== `

### Agente

Uma única votação acerta 95,6%. Agora os testes de significância (10×10 validações, teste t corrigido), três em paralelo: J48 × ZeroR, J48 × RandomForest e J48 × OneR.

- `Bash`: `
python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --opcoes-a="-C 0.25 -M 2" --b weka.classifiers.rules.ZeroR --positiva republican --repeticoes 10 > /tmp/claude-0/-tmp-copias-validacao-T03-r3/8906b1cb-cac7-4eac-a98d-203e436c4231/scratchpad/s1.txt 2>&1 &
python3 ferrament`
- `Bash`: `cat > analises/scripts/2026-11-21_ic_vote.py <<'EOF'
# IC de 95% (aproximação normal) para as acurácias da validação cruzada do Weka.
import math, datetime
acertos = {"ZeroR": 267, "J48": 419, "RandomForest": 418, "OneR": 416, "JRip": 415, "NaiveBayes": 392}
N = 435
linhas = []
for nome, k in acerto`
- `Write`: `/tmp/copias_validacao/T03_r3/analises/2026-11-21_vote.md`

### Agente

# O que diferencia democratas de republicanos (vote.arff)

Uma única votação separa os dois partidos em cerca de 96% dos casos: a do **congelamento dos honorários médicos** (`physician-fee-freeze`). Quase todo republicano votou "sim" e quase todo democrata votou "não". Árvore, regras e floresta aleatória chegam a essa mesma votação. Acrescentar as outras 15 votações não melhora o modelo de forma estatisticamente significativa.

Como seu objetivo é **entender**, não prever, tratei os dois tipos de erro (confundir democrata com republicano e o contrário) como igualmente graves. Escolhi a **acurácia** como métrica principal antes de ver os resultados.

## 1. O que foi feito

- **Dados:** 435 deputados da Câmara dos EUA em 1984 (267 democratas e 168 republicanos) e 16 votações com resposta sim/não. Não removi nenhum atributo e não troquei nenhum valor.
- **Avaliação:** validação cruzada estratificada de 10 partes, com semente 1. Comando base: `java ... weka.classifiers.trees.J48 -t vote.arff -x 10 -s 1 -C 0.25 -M 2`. Os comandos de cada modelo estão na primeira linha de cada arquivo em `resultados/`.
- **Modelos:**
  - **J48** (árvore de decisão) e **JRip** (regras): são legíveis, por isso foram os principais.
  - **NaiveBayes:** modelo de apoio.
  - **RandomForest:** é uma caixa-preta, entrou só para mostrar o máximo que se consegue com esses dados.
  - **OneR:** usa uma única votação. Entrou depois de ver que a árvore começava por uma só votação, para medir quanto ela explica sozinha.

## 2 e 3. Resultados do Weka (validação cruzada) e comparação com o ZeroR

| Modelo | Acurácia (IC 95%) | Kappa | F1 republicano | AUC |
|---|---|---|---|---|
| **ZeroR** (sempre "democrata") | 61,38% (56,8–66,0) | 0 | – | 0,491 |
| **J48** | **96,32%** (94,6–98,1) | 0,922 | 0,952 | 0,971 |
| RandomForest (máximo alcançável) | 96,09% (94,3–97,9) | 0,918 | 0,949 | 0,993 |
| OneR (1 votação) | 95,63% (93,7–97,6) | 0,909 | 0,945 | 0,959 |
| JRip | 95,40% (93,4–97,4) | 0,904 | 0,942 | 0,942 |
| NaiveBayes | 90,11% (87,3–92,9) | 0,795 | 0,877 | 0,973 |

Matriz de confusão do J48 (linhas = partido real, colunas = partido previsto):

```
   dem  rep
   259    8   democrata
     8  160   republicano
```

O J48 erra 16 deputados, 8 em cada sentido. Os erros não se concentram num partido.

## 4. Confiabilidade

Usei o teste t pareado corrigido, com 10 repetições da validação cruzada de 10 partes, sobre a acurácia.

| Comparação | Diferença | p | Conclusão |
|---|---|---|---|
| J48 × ZeroR | +35,2 pontos | < 0,000001 | o J48 é melhor |
| J48 × RandomForest | +0,1 ponto | 0,83 | empate técnico |
| J48 × OneR | +0,9 ponto | 0,16 | empate técnico |

- **J48 × RandomForest:** usar uma caixa-preta não traz ganho, então interpretar o modelo não custa nada em desempenho.
- **J48 × OneR:** na métrica principal, as outras 15 votações não acrescentam nada que se possa demonstrar. A árvore tem precisão maior para a classe republicana (p = 0,003, e ainda significativa depois de corrigir para as 4 métricas testadas). Mesmo assim, a conclusão sobre qual modelo é melhor continua sendo empate.

Fiz só essas três comparações.

## 5. Interpretação

**A árvore (J48), com 6 folhas:**

```
physician-fee-freeze = n → democrata                    (253 casos, ~4 erros)
physician-fee-freeze = y
|  synfuels-corporation-cutback = n → republicano       (146 casos, ~4 erros)
|  synfuels-corporation-cutback = y
|  |  mx-missile = y → democrata                          (6 casos)
|  |  mx-missile = n → mais 2 divisões, com 2 a 23 casos por folha
```

Como ler a árvore:

- **Primeira divisão:** quem votou "não" ao congelamento dos honorários médicos é democrata.
- **Segunda divisão:** entre quem votou "sim", os republicanos típicos também votaram contra o corte do subsídio aos combustíveis sintéticos (`synfuels-corporation-cutback`).
- **O resto:** os ramos mais fundos descrevem cerca de 36 deputados "cruzados", provavelmente democratas mais conservadores. Essas folhas têm poucos casos, então essa parte da árvore é frágil.

As regras do JRip dizem o mesmo de outra forma: "republicano se votou sim ao congelamento **e** (não ao corte dos combustíveis sintéticos, **ou** sim à lei sobre a África do Sul, **ou** não à resolução orçamentária); senão, democrata". As regras valem nessa ordem: cada uma só se aplica a quem não foi coberto pela anterior.

**Diferença entre os partidos em cada votação** (percentual de "sim" entre quem votou sim ou não):

| Votação | Democratas | Republicanos |
|---|---|---|
| physician-fee-freeze | 5% | 99% |
| adoption-of-the-budget-resolution | 89% | 13% |
| el-salvador-aid | 22% | 95% |
| education-spending | 15% | 87% |
| aid-to-nicaraguan-contras | 83% | 15% |
| water-project-cost-sharing | 50% | 51% |
| immigration | 47% | 56% |

As duas últimas votações praticamente não diferenciam os partidos. As cinco primeiras têm diferenças de 68 a 93 pontos. Ou seja, existe um bloco de votações alinhadas por partido, e o congelamento dos honorários é a mais clara delas. Não é a única votação que diferencia os partidos. Como as votações do bloco são redundantes entre si, a árvore usa a mais forte e ignora as outras.

Isso também explica por que o NaiveBayes ficou abaixo dos outros: ele conta como evidências independentes votações que dizem a mesma coisa. Os atributos são todos nominais, então as opções `-K` e `-D` do NaiveBayes não se aplicam aqui.

## 6. Alertas e próximos passos

- **Não há sinal de sobreajuste.** O J48 acerta 97,2% no treino e 96,3% na validação, e a árvore é pequena.
- **O "?" quer dizer outra coisa nesta base.** A documentação diz que "?" não é dado perdido: significa que o deputado não votou nem sim nem não (estava presente ou se absteve). 203 dos 435 registros têm pelo menos um "?". Analisei a base como ela é, e o Weka tratou "?" como desconhecido. Para estudar a abstenção como comportamento político, o próximo passo seria criar uma base nova em `dados/` com "?" virando um terceiro valor ("abstenção") e comparar com a original. **Isso não foi executado.** Quer que eu faça?
- **A documentação do arquivo traz a proporção errada.** O cabeçalho diz 45,2% democratas e 54,8% republicanos. A contagem real é 61,4% e 38,6%, e é essa que o Weka usou.
- **Votos idênticos.** 93 linhas repetem exatamente outra. São deputados diferentes que votaram igual, então mantive todas. Elas mostram votação em bloco e deixam a tarefa mais fácil, o que é uma característica real dos dados. Nenhum padrão de votos aparece nos dois partidos.
- **Alcance da conclusão.** A conclusão vale para essas 16 votações de 1984. Ela descreve o comportamento de voto e não diz por que cada deputado votou como votou.
- **Não rodei IBk, SMO nem MultilayerPerceptron.** Para entender os partidos eles não acrescentariam nada, e o modelo caixa-preta já testado empatou com a árvore.

O relatório está em `analises/2026-11-21_vote.md`. Os scripts auxiliares estão em `analises/scripts/2026-11-21_*.py` e as saídas do Weka em `resultados/`.

