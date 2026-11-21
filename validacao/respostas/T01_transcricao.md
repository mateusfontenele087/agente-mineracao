# Transcrição T01

### Usuário

Quero um modelo de triagem de hipotireoidismo a partir desses exames. A base é hypothyroid.arff.


### Agente

Vou começar lendo o manual de decisões e explorando a base.

- `Bash`: `ls; ls dados ferramentas resultados 2>/dev/null | head -50; wc -l conhecimento/manual_decisoes.md; find / -name "hypothyroid*.arff" 2>/dev/null | head`
- `Read`: `/home/user/agente-mineracao/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/hypothyroid.arff 2>&1 | tail -80`
- `Bash`: `python3 ferramentas/weka_runner.py resumo hypothyroid.arff 2>&1 | tail -70`

### Agente

Agora o perfil detalhado (classe, quartis, extremos, duplicatas) em Python, salvo em `resultados/`.

- `Bash`: `ls analises validacao | head; python3 -c "import scipy, pandas; print('ok')"; sed -n 1,40p dados/hypothyroid.arff | cut -c1-200`
- `Bash`: `grep -n "@attribute" dados/hypothyroid.arff | sed -n '27,30p'; grep -c . dados/hypothyroid.arff; head -50 analises/2026-10-31_diabetes_reanalise.md; python3 ferramentas/significancia.py -h | head -40`
- `Bash`: `mkdir -p /tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad && cat > /tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad/perfil.py <<'EOF'
# Perfil descritivo da base hypothyroid.arff (só lê; não altera a base)
from collect`
- `Bash`: `pip install -q scipy 2>&1 | tail -2; python3 -c "import scipy; print(scipy.__version__)"`

### Agente

Ainda não rodei nenhum modelo. A exploração mostrou que as classes são muito desbalanceadas, e há pontos que só você pode decidir. Por isso parei aqui, antes de treinar qualquer coisa.

## O que já foi feito
- Resumo do Weka: `python3 ferramentas/weka_runner.py resumo hypothyroid.arff`
- Perfil em Python (quartis, extremos, duplicatas, coerência entre atributos), salvo em `resultados/20261121_132621_perfil_hypothyroid.txt`
- Instalei o `scipy`. O `significancia.py` precisa dele e não estava instalado.

## O que a exploração encontrou

**Classe (3.772 registros, 4 valores):**

| Classe | n | % |
|---|---|---|
| negative | 3.481 | 92,3% |
| compensated_hypothyroid | 194 | 5,1% |
| primary_hypothyroid | 95 | 2,5% |
| secondary_hypothyroid | **2** | 0,05% |

Um modelo que diz "negativo" para todo mundo acerta 92%. Por isso a acurácia não serve como métrica aqui. E com apenas 2 casos de hipotireoidismo secundário, nenhum modelo consegue aprender essa classe.

**Problemas de qualidade:**
1. **`TBG` está 100% ausente** e `TBG measured` é constante. Vou removê-los, porque não informam nada.
2. **`age = 455`** em um registro. É uma idade impossível. Proponho marcar como ausente, sem tentar adivinhar o valor certo.
3. **O TSH falta só nos negativos** (369 de 3.481; zero ausentes nas classes de hipotireoidismo). É o ponto mais sério. O modelo pode aprender que "TSH não pedido" significa "negativo", e isso reflete a decisão do médico, não a doença. Numa triagem real o TSH está disponível, então essa regra inflaria o desempenho sem servir na prática. O mesmo risco vale para os outros atributos `... measured`.
4. **61 linhas duplicadas, todas negativas.** Podem ser pacientes diferentes com exames iguais (aí ficam) ou o mesmo registro repetido (aí saem).
5. **`hypopituitary`** tem um único caso "t" e não ajuda a separar as classes. **Extremos** em TSH (até 530) e TT4 são plausíveis no hipotireoidismo, então eu os mantenho.
6. **`on thyroxine`:** 464 pessoas já tomam hormônio tireoidiano, e 455 delas estão classificadas como negativas. Isso muda o sentido de "triagem" para esse grupo.

## Preciso que você decida

1. **O que o modelo deve responder?**
   - (a) **Binário:** "tem hipotireoidismo (qualquer tipo)" contra "negativo". É o mais natural para triagem, e eu recomendo este. Os 2 casos secundários entram no grupo positivo.
   - (b) **Multiclasse:** distinguir compensado de primário. Nesse caso o secundário teria de sair da análise.
2. **Qual erro custa mais, e quantas vezes mais?** Um hipotireoidismo que passa sem ser detectado (falso negativo) ou um exame confirmatório pedido à toa (falso positivo)? Em triagem costuma pesar mais o falso negativo, mas preciso da proporção: 5 para 1? 10 para 1? Com ela monto a matriz de custo, e o custo total vira a métrica principal. Se você não souber, uso o F1 da classe positiva e deixo essa suposição escrita.
3. **Para quem é a triagem?** Pessoas que já fizeram os exames, ou qualquer paciente? Isso define o que faço com os registros sem TSH e com os atributos `... measured`. Minha recomendação é tirar os `... measured` e rodar com e sem os 369 registros sem TSH, como análise de sensibilidade.
4. **Pacientes que já tomam tiroxina** (`on thyroxine = t`): mantenho ou excluo da população?
5. **Duplicatas:** são pacientes diferentes ou o mesmo registro repetido? Se não souber, mantenho e testo sem elas como cenário alternativo.

## Depois da sua resposta
1. Gero uma base nova em `dados/` (a original fica intacta) com as remoções e correções confirmadas.
2. Rodo ZeroR, as duas linhas de base de custo e os candidatos: J48 e JRip (interpretáveis; o JRip descreve bem classes raras), NaiveBayes, IBk com escolha de k por validação interna e RandomForest. Todos com validação cruzada estratificada de 10 partes, semente 1. Os ajustes que aprendem com os dados ficam dentro da validação.
3. Testo a significância do melhor modelo contra a linha de base e contra o segundo melhor, só na métrica principal.

Se a ideia for só um rascunho rápido, posso seguir com os padrões que recomendei: binário, custo 5:1 (deixar passar um caso custa 5 vezes mais), sem os `... measured` e com a análise de sensibilidade do TSH. Nesse caso, deixo cada suposição declarada no início do relatório.


### Usuário

A classe de interesse é qualquer tipo de hipotireoidismo. Deixar passar um doente custa 10 vezes mais que um alarme falso. Nas outras perguntas, siga as suas recomendações.

- `Bash`: `wc -l ferramentas/*.py && sed -n 1,400p ferramentas/weka_runner.py`
- `Bash`: `echo $WEKA_CP; sed -n 1,120p ferramentas/significancia.py; grep -n "CostSensitive\|-cost-matrix\|MinimizeExpected\|-M" analises/2026-10-31_credit-g_v3.md | head -20`
- `Bash`: `sed -n 120,500p ferramentas/significancia.py | grep -v '^\s*$' | head -300`

### Agente

Combinado. Vou montar a base de trabalho em `dados/` (a original fica intacta), com um script registrado.

- `Write`: `/home/user/agente-mineracao/analises/2026-11-21_preparar_hypothyroid.py`
- `Bash`: `python3 analises/2026-11-21_preparar_hypothyroid.py && python3 ferramentas/weka_runner.py resumo hypothyroid_bin.arff 2>&1 | grep -v "^Picked"`
- `Bash`: `nproc && cat > /tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad/rodar.sh <<'EOF'
#!/bin/bash
# Roda cada candidato (com custo 10:1) contra o ZeroR, na mesma validação (10 partes, semente 1)
cd /home/user/agente-mineracao
BASE=$1
CS="weka.classifiers.meta.Cost`
- `Bash`: `cd /tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad && cat > extrair.py <<'EOF'
# Extrai SÓ o bloco de validação cruzada de cada saída do Weka e calcula custo e IC 95% da acurácia
import re, sys, math, glob, os
pasta = sys.argv[1]
def bloco_cv(txt):
    # a s`
- `Bash`: `S=/tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad; python3 ferramentas/weka_runner.py comparar hypothyroid_bin.arff weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 10.0 0.0]" -M -W weka.classifiers.trees.RandomForest > $S/saidas_hypothy`
- `Bash`: `grep -n "texto_custo\|add_argument\|def main\|comparar(" ferramentas/significancia.py | sed -n 1,80p; sed -n 440,500p ferramentas/significancia.py`
- `Bash`: `sed -n 349,360p ferramentas/significancia.py && sed -n 405,416p ferramentas/significancia.py`

### Agente

Estou adicionando a opção `--sem-envelope` ao `significancia.py`. Depois rodo os testes de significância.

- `Edit`: `/home/user/agente-mineracao/ferramentas/significancia.py`
- `Edit`: `/home/user/agente-mineracao/ferramentas/significancia.py`
- `Edit`: `/home/user/agente-mineracao/ferramentas/significancia.py`
- `Edit`: `/home/user/agente-mineracao/ferramentas/significancia.py`

### Agente

Agora os três testes, em paralelo: RF `-M` contra a linha de base, RF `-M` contra J48 e J48 contra a linha de base.

- `Bash`: `S=/tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad
CS=weka.classifiers.meta.CostSensitiveClassifier
RFM='-cost-matrix "[0.0 1.0; 10.0 0.0]" -M -W weka.classifiers.trees.RandomForest'
J48='-cost-matrix "[0.0 1.0; 10.0 0.0]" -W weka.classifiers.trees.J48 -- -C `

### Agente

O problema era só a montagem das aspas no shell. Vou rodar com os comandos escritos por extenso.

- `Bash`: `S=/tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad
python3 significancia.py hypothyroid_bin.arff --a weka.classifiers.meta.CostSensitiveClassifier --opcoes-a='-cost-matrix "[0.0 1.0; 10.0 0.0]" -M -W weka.classifiers.trees.RandomForest' --b weka.classifiers.r`
- `Bash`: `S=/tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad; grep -v "^Repetição\|^Picked" $S/sig_RFM_J48.txt | tail -25`
- `Bash`: `S=/tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad
python3 significancia.py hypothyroid_bin.arff --a weka.classifiers.meta.CostSensitiveClassifier --opcoes-a='-cost-matrix "[0.0 1.0; 10.0 0.0]" -M -W weka.classifiers.trees.RandomForest' --b weka.classifiers.m`

### Agente

Na métrica principal, J48 e RF `-M` estão empatados (p = 0,45), e os dois superam a linha de base com folga. Falta a análise de sensibilidade: rodar o J48 nas duas bases alternativas.

- `Bash`: `cd /home/user/agente-mineracao && S=/tmp/claude-0/-home-user-agente-mineracao/43d67422-6169-4121-9dbe-1a4a95ad44a1/scratchpad
for B in hypothyroid_bin_sem_dup hypothyroid_bin_com_tsh; do mkdir -p $S/saidas_$B; python3 ferramentas/weka_runner.py comparar $B.arff weka.classifiers.meta.CostSensitiveCla`

### Agente

A conclusão se mantém nos três cenários. Vou localizar os arquivos de saída e registrar o relatório em `analises/`.

- `Bash`: `cd /home/user/agente-mineracao/resultados && for f in $(ls -t | head -60 | grep classificador); do c=$(head -1 $f); case "$c" in *hypothyroid_bin*) echo "$f :: $(echo $c | grep -o 'hypothyroid_bin[a-z_]*.arff') :: $(echo $c | grep -oE '\-M -W [A-Za-z.]+|-W [A-Za-z.]+' | head -1) $(echo $c | grep -oE`
- `Bash`: `grep -l "hypothyroid_bin.arff" 20261121_13*classificador.txt | while read f; do echo "$f :: $(head -1 $f | sed 's/.*CostSensitiveClassifier//; s/-t .*-s 1//' | cut -c1-120)"; done`
- `Write`: `/home/user/agente-mineracao/analises/2026-11-21_hypothyroid.md`

### Agente

Recomendo uma **árvore de decisão (J48)** como modelo de triagem. Ela deixou passar 7 dos 291 doentes e deu 15 alarmes falsos em 3.772 pacientes, com custo total **85**. Não ter modelo nenhum custaria **2.910**. O relatório completo está em `analises/2026-11-21_hypothyroid.md`.

## 1. O que foi feito
- **Base de trabalho** `dados/hypothyroid_bin.arff`, gerada pelo script `analises/2026-11-21_preparar_hypothyroid.py` (a original não foi alterada):
  - A classe virou binária: hipotireoidismo de qualquer tipo × negativo.
  - Saíram `TBG` (100% ausente), os 6 atributos `... measured` e `hypopituitary` (um único caso "t").
  - A idade 455 virou valor ausente.
- **Métrica principal, definida antes de rodar os modelos:** custo total = alarmes falsos + 10 × doentes não detectados.
- **Linha de base:** prever todos como negativos custa 291 × 10 = **2.910**. Prever todos como doentes custaria 3.481, então a linha de base é 2.910.
- **Candidatos:** 7 configurações, todas com o ajuste de custo 10:1 do Weka (`CostSensitiveClassifier`). Validação cruzada estratificada de 10 partes, semente 1.
- **Comando do modelo escolhido:**
  `python3 ferramentas/weka_runner.py comparar hypothyroid_bin.arff weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 10.0 0.0]" -W weka.classifiers.trees.J48 -- -C 0.25 -M 2`

## 2–3. Resultado do Weka (só a validação cruzada) e comparação com o ZeroR

| Modelo | Acurácia (IC 95%) | Kappa | Recall | Precisão | F1 | AUC | **Custo** |
|---|---|---|---|---|---|---|---|
| ZeroR | 92,29% ± 0,85 | 0,000 | 0,000 | — | — | 0,498 | **2.910** |
| **J48** | **99,42% ± 0,24** | 0,960 | 0,976 | 0,950 | 0,963 | 0,987 | **85** |
| RandomForest `-M` | 98,36% ± 0,41 | 0,894 | 0,993 | 0,828 | 0,903 | 0,988 | **80** |
| JRip | 99,20% ± 0,28 | 0,945 | 0,973 | 0,928 | 0,950 | 0,984 | 102 |
| NaiveBayes `-K` | 91,54% ± 0,89 | 0,524 | 0,722 | 0,469 | 0,568 | 0,924 | 1.048 |
| RandomForest (reponderado) | 96,58% ± 0,58 | 0,707 | 0,581 | 0,960 | 0,724 | 0,986 | 1.227 |
| NaiveBayes | 90,93% ± 0,92 | 0,442 | 0,567 | 0,433 | 0,491 | 0,887 | 1.476 |
| IBk (k = 1, escolhido por `-X`) | 89,10% ± 0,99 | 0,241 | 0,302 | 0,297 | 0,300 | 0,617 | 2.238 |

Recall, precisão e F1 são da classe hipotireoidismo.

**Matriz de confusão do J48:**

| | previsto negativo | previsto hipotireoidismo |
|---|---|---|
| **real negativo** | 3.466 | 15 |
| **real hipotireoidismo** | 7 | 284 |

## 4. Confiabilidade
Fiz 3 comparações com o teste t pareado corrigido (10 repetições × 10 partes), todas no custo:
- **J48 × ZeroR:** p < 0,001, o J48 é melhor.
- **RandomForest `-M` × ZeroR:** p < 0,001, o RandomForest é melhor.
- **RandomForest `-M` × J48:** custo médio por parte de 7,29 contra 5,87, p = 0,45. É **empate técnico**. Com o empate, fico com o J48, que é mais simples e pode ser lido por quem vai usar a triagem.

**Análise de sensibilidade:** rodei o J48 em duas bases alternativas. Sem as 61 duplicatas, o custo foi 64. Só com pacientes que têm TSH medido, foi 47. A conclusão não muda, então as duplicatas e a falta de TSH não estavam inflando o resultado.

## 5. Interpretação da árvore
- **TSH ≤ 6:** a árvore diz que é negativo, com uma exceção que comento nos alertas.
- **TSH > 6, sem tiroxina, sem cirurgia de tireoide, sem bócio e TT4 ≤ 144:** hipotireoidismo. Esse ramo cobre a grande maioria dos doentes.
- **TSH > 6 em quem já toma tiroxina:** só é hipotireoidismo se o FTI for ≤ 62. Acima disso, o tratamento parece estar controlando o quadro.

O JRip, rodado separadamente, chegou a uma primeira regra quase igual: TSH ≥ 6,1 e TT4 ≤ 148, sem tiroxina e sem cirurgia. Isso dá mais confiança de que o padrão é real.

## 6. Alertas e próximos passos
- **Sobreajuste:** não há sinal. A árvore acerta 99,68% no treino e 99,42% na validação, com 16 folhas.
- **Um ramo suspeito:** "TSH ≤ 6, TT4 ≤ 49 e origem do encaminhamento = other → hipotireoidismo". Ele depende de um atributo administrativo e se apoia em poucos casos. Sugiro mostrar esse ramo a um endocrinologista ou testar a árvore sem `referral source`.
- **Testei 7 configurações.** Com tantas tentativas, o número do melhor modelo tende a sair um pouco otimista.
- **Os dados são de 1987 e de um único centro australiano.** Antes de qualquer uso real, o modelo precisa ser validado com dados atuais da população que será triada.
- **Os 7 doentes não detectados** merecem revisão caso a caso.
- **Não executado:** IBk com seleção de atributos, NaiveBayes `-D`, J48 com a opção `-M` do ajuste de custo e o teste JRip × J48.
- **Mudei uma ferramenta do projeto:** `ferramentas/significancia.py` ganhou a opção `--sem-envelope`. Sem ela, a ferramenta não conseguia testar o RandomForest com `-M`. Sem a opção, o comportamento antigo continua igual. Também instalei o `scipy`, que a ferramenta exige e não estava no ambiente.

