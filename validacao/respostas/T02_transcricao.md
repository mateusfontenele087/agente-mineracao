# Transcrição T02

### Usuário

Quero prever recorrência do câncer de mama com essa base (breast-cancer.arff). Qual algoritmo devo usar?


### Agente

Antes de recomendar um algoritmo, preciso conhecer a base. Vou começar lendo o manual de decisões e rodando o resumo.

- `Bash`: `ls; ls dados ferramentas resultados 2>/dev/null | head -50; wc -l conhecimento/manual_decisoes.md`
- `Read`: `/home/user/agente-mineracao/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/breast-cancer.arff`
- `Bash`: `python3 ferramentas/weka_runner.py resumo breast-cancer.arff; ls -t resultados | head -3`

### Agente

O resumo do Weka não mostra a distribuição das classes nem dos valores. Vou montar o perfil completo em Python (só descritivo) e salvar em `resultados/`.

- `Bash`: `cat > /tmp/claude-0/-home-user-agente-mineracao/78392a33-4eed-4d74-99a8-d0a625fed7f2/scratchpad/perfil_bc.py << 'EOF'
# Perfil descritivo da base breast-cancer (só contagens; nenhum modelo)
import re, collections, datetime
linhas = open("dados/breast-cancer.arff").read().splitlines()
attrs, dados, e`

### Agente

Rodei o resumo da base no Weka e montei um perfil descritivo em Python. Ainda não treinei nenhum modelo, porque surgiu um ponto que você precisa decidir antes.

## Resposta curta

Não dá para escolher o algoritmo antes de testar. Nenhum algoritmo é o melhor para todas as bases. O que faço é montar uma lista de candidatos adequados a esta base, rodar todos nas mesmas condições e escolher pelo resultado, com teste estatístico. Para esta base, os candidatos são:

| Candidato (Weka) | Por que entra |
|---|---|
| **ZeroR** | Linha de base obrigatória. Prevê sempre "não recorre" e acerta 201/286 = 70,3% só por isso |
| **NaiveBayes** | Todos os atributos são categóricos, o que combina com ele. Lida bem com ruído e com atributos sem relação com a classe, e esta base é conhecida por ser ruidosa. Também é um bom ponto de partida |
| **J48** (árvore podada) | Mostra *quais fatores* indicam recorrência. A poda é importante porque 286 casos é pouco |
| **JRip** (regras) | Concentra o esforço na classe rara, que aqui é "recorrência" |
| **RandomForest** | Serve de teto: mostra quanto um modelo não interpretável ainda conseguiria ganhar |
| **IBk** com k escolhido por validação (`-X`) | Faz comparação por casos parecidos. Entra com ressalva, porque atributos irrelevantes atrapalham esse método |

Deixei de fora o MultilayerPerceptron (rede neural). Ele precisa de bases maiores e é sensível a ruído, e 286 casos são poucos para ele.

## O que a exploração mostrou

- **286 pacientes e 9 atributos**, todos categóricos.
- **Classes desbalanceadas:** 201 sem recorrência (70%) e 85 com recorrência (30%). Por isso a acurácia sozinha engana: um modelo que só acerta 70% pode não ter aprendido nada.
- **Valores ausentes:** 8 em `node-caps` e 1 em `breast-quad`. São poucos. J48, NaiveBayes e RandomForest lidam com isso sozinhos, então não proponho eliminar nem estimar esses valores.
- **Faixas ordenadas guardadas como categorias soltas.** `age`, `tumor-size`, `inv-nodes` e `deg-malig` são faixas com ordem, mas o Weka trata cada uma como uma categoria sem relação com as outras. Ele não sabe que "30-34" é maior que "20-24". Com poucos casos em cada faixa, isso fragmenta os dados. Vou declarar isso como limitação. Depois, podemos testar se converter para número ajuda.
- **14 registros duplicados.** Sem um identificador, não dá para saber se são a mesma paciente cadastrada duas vezes ou pacientes diferentes com o mesmo perfil. Com atributos em faixas largas, a segunda hipótese é plausível. Proponho manter os registros e tratar isso como limitação, a menos que você saiba a origem dos dados.
- **Primeiros sinais**, que por enquanto são só hipóteses:
  - Grau de malignidade 3: 45 de 85 casos recorrem (53%). No grau 1, são 12 de 71 (17%).
  - `node-caps = yes`: 31 de 56 recorrem (55%).
  - Os modelos vão dizer se esses padrões se sustentam.

## Antes de modelar, preciso de três respostas suas

Como as classes são desbalanceadas, a métrica que decide qual modelo é melhor depende do custo de cada erro. Isso é decisão sua, não minha:

1. **A classe de interesse é "recurrence-events" (recorrência)?** Vou supor que sim.
2. **Qual erro custa mais?**
   - Deixar passar uma recorrência (falso negativo): a paciente não recebe o acompanhamento de que precisaria.
   - Dar um alarme falso (falso positivo): a paciente passa por acompanhamento ou tratamento que não precisava.
3. **Quantas vezes mais custa?** Por exemplo: "deixar passar custa 5 vezes mais que o alarme falso". Com essa proporção, monto a matriz de custo e escolho o modelo pelo **custo total**.

Mais uma pergunta: você quer **entender** o que leva à recorrência ou só **acertar** casos novos? Você disse "prever", mas, se for para um trabalho acadêmico, normalmente ajuda também conseguir explicar o modelo. Isso muda o peso que dou ao J48 e ao JRip.

Se você não souber a proporção dos custos, posso propor uma e explicar de onde ela veio. Outra opção é usar o F1 da classe "recorrência" como métrica principal, mas aí eu declaro isso como suposição no início da análise.

O perfil descritivo ficou salvo em `resultados/` (arquivo `*_perfil_breast-cancer.txt`).


### Usuário

Deixar de prever uma recorrência é 3 vezes pior que um alarme falso.

- `Bash`: `grep -n "@attribute 'Class'\|@attribute Class" -i dados/breast-cancer.arff; python3 ferramentas/weka_runner.py --help 2>&1 | tail -30; python3 ferramentas/significancia.py --help 2>&1 | tail -30`
- `Bash`: `grep -n "def \|subprocess\|cmd\|custo\|cost" ferramentas/weka_runner.py | head -60; grep -n "def \|cost\|custo\|cmd" ferramentas/significancia.py | head -60`
- `Read`: `/home/user/agente-mineracao/ferramentas/significancia.py`
- `Read`: `/home/user/agente-mineracao/ferramentas/weka_runner.py`
- `Bash`: `grep -n "CLASSIFICADOR_CUSTO\s*=" -A3 ferramentas/significancia.py`
- `Bash`: `C="weka.classifiers.meta.CostSensitiveClassifier"; M="[0.0 1.0; 3.0 0.0]"
for base in "weka.classifiers.bayes.NaiveBayes" "weka.classifiers.trees.J48 -- -C 0.25 -M 2" "weka.classifiers.rules.JRip" "weka.classifiers.trees.RandomForest" "weka.classifiers.lazy.IBk -- -K 15 -X"; do
  set -- $base
  echo`

### Agente

Os 5 candidatos já rodaram no Weka. Agora vou extrair da saída só o bloco da validação cruzada.

- `Bash`: `for f in 20261121_132707_549076 20261121_132708_974317 20261121_132710_406589 20261121_132712_199760 20261121_132714_502741; do echo "######## $f"; head -1 resultados/${f}_classificador.txt; awk '/=== Stratified cross-validation ===/{p=1} p' resultados/${f}_classificador.txt | grep -v "^$" | grep -E`
- `Bash`: `(python3 ferramentas/significancia.py breast-cancer.arff --a weka.classifiers.bayes.NaiveBayes --b weka.classifiers.rules.ZeroR --custo "0 1; 3 0" --positiva recurrence-events --repeticoes 10 > /tmp/claude-0/-home-user-agente-mineracao/78392a33-4eed-4d74-99a8-d0a625fed7f2/scratchpad/sig_nb_zeror.txt`
- `Bash`: `cat > /tmp/claude-0/-home-user-agente-mineracao/78392a33-4eed-4d74-99a8-d0a625fed7f2/scratchpad/custos.py << 'EOF'
# Custo total e IC 95% da acurácia, a partir das matrizes de confusão do Weka (validação cruzada)
import math, datetime
custo = [[0, 1], [3, 0]]          # linhas = real (não, sim); col`

### Agente

Os testes de significância ainda estão rodando. Enquanto isso, vou ver qual k o IBk escolheu.

- `Bash`: `grep -i "nearest neighbour" resultados/20261121_132714_502741_classificador.txt | head -3`
- `Bash`: `sleep 1; cat /tmp/claude-0/-home-user-agente-mineracao/78392a33-4eed-4d74-99a8-d0a625fed7f2/scratchpad/sig_nb_zeror.txt | tail -30`

### Agente

The tests are still running. I'll wait for the completion notification.

- `ToolSearch`: `{"query": "select:Monitor", "max_results": 1}`

### Agente

Os modelos já rodaram. Faltam os dois testes de significância, que repetem a validação cruzada 10 vezes e levam alguns minutos. Vou receber um aviso quando terminarem e então te entrego a análise completa.

Por enquanto, estes são os custos da validação cruzada, sem teste ainda. Por isso nenhum modelo pode ser chamado de melhor:

| Modelo | Custo total | Acurácia (IC 95%) |
|---|---|---|
| Linha de base: prever "recorre" para todas | **201** | 29,7% |
| ZeroR: prever "não recorre" para todas | 255 | 70,3% [64,7–75,3] |
| NaiveBayes | 152 | 66,4% [60,8–71,7] |
| IBk (k escolhido por `-X`) | 178 | 63,6% [57,9–69,0] |
| JRip | 187 | 59,1% [53,3–64,6] |
| RandomForest | 197 | 61,9% [56,1–67,3] |
| J48 | 198 | 55,9% [50,1–61,6] |

Os testes em andamento comparam o NaiveBayes, que teve o menor custo, com a linha de base e com o IBk, que ficou em segundo.


### Usuário

<task-notification>
<task-id>bxetu0ky7</task-id>
<tool-use-id>toolu_01AYiAtubUTyGegkjrPzkRF2</tool-use-id>
<output-file>/tmp/claude-0/-home-user-agente-mineracao/78392a33-4eed-4d74-99a8-d0a625fed7f2/tasks/bxetu0ky7.output</output-file>
<status>completed</status>
<summary>Background command "Run significance tests NB vs ZeroR and NB vs IBk" completed (exit code 0)</summary>
</task-notification>

- `Bash`: `cd /tmp/claude-0/-home-user-agente-mineracao/78392a33-4eed-4d74-99a8-d0a625fed7f2/scratchpad && grep -v "^Repetição" sig_nb_zeror.txt; echo =========; grep -v "^Repetição" sig_nb_ibk.txt`

### Agente

# Recomendação: NaiveBayes com custo (3:1)

O NaiveBayes gera **custo significativamente menor do que não ter modelo** (p = 0,006). Ele ficou em empate técnico com o segundo colocado, o IBk, e por isso é o escolhido: é mais simples, mais rápido e mais fácil de explicar. A capacidade de previsão nesta base é modesta: o modelo encontra cerca de 2 de cada 3 recorrências, ao preço de muitos alarmes falsos.

## 1. O que foi feito
- **Base:** `breast-cancer.arff` original, com 286 casos e sem pré-processamento. Os 9 valores ausentes ficaram por conta do NaiveBayes, que simplesmente ignora o atributo ausente naquele caso.
- **Custo:** perder uma recorrência custa 3; um alarme falso custa 1. Cada candidato foi treinado dentro do `CostSensitiveClassifier`, para aprender já levando esse custo em conta.
- **Métrica principal, definida antes de ver os resultados:** custo total, quanto menor, melhor.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1.
- **Comando do modelo escolhido:**
  `java ... weka.classifiers.meta.CostSensitiveClassifier -t breast-cancer.arff -x 10 -s 1 -cost-matrix "[0.0 1.0; 3.0 0.0]" -W weka.classifiers.bayes.NaiveBayes`

## 2. Resultado do Weka para o NaiveBayes (validação cruzada)

| | previsto: não recorre | previsto: recorre |
|---|---|---|
| **real: não recorre** (201) | 133 | 68 ← alarmes falsos |
| **real: recorre** (85) | 28 ← recorrências perdidas | 57 |

Métricas da classe "recorrência":

| Métrica | Valor |
|---|---|
| Recall | 0,671 |
| Precisão | 0,456 |
| F1 | 0,543 |
| AUC | 0,698 |
| Kappa | 0,293 |
| Acurácia | 66,4%, IC 95% de 60,8% a 71,7% |
| **Custo total** | 68 × 1 + 28 × 3 = **152** |

## 3. Comparação com as linhas de base e os outros candidatos

| Modelo | Custo | Acurácia (IC 95%) | Recall | Precisão | F1 | Kappa |
|---|---|---|---|---|---|---|
| Prever "não recorre" para todas (ZeroR comum) | 255 | 70,3% (64,7–75,3) | 0,000 | – | – | 0 |
| **Prever "recorre" para todas (linha de base)** | **201** | 29,7% | 1,000 | 0,297 | – | 0 |
| **NaiveBayes** | **152** | 66,4% (60,8–71,7) | 0,671 | 0,456 | 0,543 | 0,293 |
| IBk (k escolhido por `-X`, até 15) | 178 | 63,6% (57,9–69,0) | 0,565 | 0,417 | 0,480 | 0,210 |
| JRip | 187 | 59,1% (53,3–64,6) | 0,588 | 0,379 | 0,461 | 0,156 |
| RandomForest | 197 | 61,9% (56,1–67,3) | 0,482 | 0,387 | 0,429 | 0,148 |
| J48 | 198 | 55,9% (50,1–61,6) | 0,576 | 0,353 | 0,437 | 0,109 |

**Por que o ZeroR, com 70% de acurácia, não é o melhor:** ele nunca aponta uma recorrência, e cada recorrência perdida custa 3. Com esses custos, a linha de base que vale é a mais barata das duas, "tratar todas como recorrência", com custo 201. Todos os modelos ficaram abaixo dela, mas J48 (198) e RandomForest (197) ficaram praticamente no mesmo nível: na prática, não acrescentam nada. Não testei a significância deles.

## 4. Confiabilidade: teste t pareado corrigido, 10 × 10 validações cruzadas, no custo

| Comparação | Custo médio por parte | p | Conclusão |
|---|---|---|---|
| NaiveBayes × linha de base | 15,7 × 20,1 | **0,006** | NaiveBayes significativamente melhor |
| NaiveBayes × IBk | 15,7 × 18,6 | 0,057 | **Empate técnico** |

Como NaiveBayes e IBk empataram, a escolha vai para o NaiveBayes: é mais simples, rápido para classificar casos novos, e suas probabilidades por atributo podem ser lidas. Ao todo testei 5 configurações e fiz 2 testes de significância. O custo do vencedor tende a ser um pouco otimista, porque parte da vantagem de quem fica em primeiro entre vários é sorte.

## 5. Interpretação
- Uma possível explicação para o NaiveBayes se sair melhor: a base é pequena e ruidosa, e ele lida bem com ruído. Árvores e regras precisam cortar os 286 casos em grupos cada vez menores e acabam decidindo com base em poucos casos.
- Na exploração, os sinais mais fortes foram grau de malignidade 3 (53% de recorrência contra 17% no grau 1) e `node-caps = yes` (55%). **Ainda não extraí as probabilidades do modelo** para confirmar quais atributos pesam mais. Posso fazer isso se você quiser explicar o modelo no trabalho.

## 6. Alertas e próximos passos
- **Desempenho modesto:** cerca de 1 em cada 3 recorrências continua passando, e mais da metade dos alertas é falso (precisão de 0,46). Os atributos disponíveis explicam pouco da recorrência. Isso é limitação da base, não do algoritmo.
- **Atributos relacionados entre si:** `inv-nodes` e `node-caps`, e também `age` e `menopause`, provavelmente medem coisas parecidas. O NaiveBayes conta essa evidência duas vezes. Um teste possível é a seleção de atributos com `AttributeSelectedClassifier`.
- **Faixas tratadas sem ordem:** idade, tamanho do tumor e número de linfonodos foram usados como categorias soltas. Converter para número ordinal pode ajudar o J48 e o IBk.
- **14 registros duplicados**, mantidos porque não há como saber se são a mesma paciente.
- **O que não rodei:**
  - Comparação de desempenho entre treino e validação para checar sobreajuste.
  - SMO e MultilayerPerceptron, que deixei de fora de propósito pelo tamanho da base.
  - Testes de significância entre os demais pares de modelos.
  - Variações de parâmetros.
- **Decisão sua:** a proporção 3:1 define o resultado. Se o custo real for maior (por exemplo, 5:1), o modelo passa a alertar mais. Vale confirmar esse número.

Os arquivos ficaram em `resultados/`:
- saídas do Weka: `20261121_1327*`
- custos e intervalos: `*_custos_breast-cancer.txt`
- testes de significância: `20261121_133509_368694_significancia.txt` e `20261121_133524_629829_significancia.txt`

