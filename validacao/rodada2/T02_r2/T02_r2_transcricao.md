# Transcrição T02_r2

### Usuário

Quero prever recorrência do câncer de mama com essa base (breast-cancer.arff). Qual algoritmo devo usar?


### Agente

Vou seguir o fluxo de especialista: primeiro leio o manual de decisões, depois exploro a base. Como o objetivo é **prever**, vou parar antes de modelar para combinar com você o custo dos erros.

- `Bash`: `ls && ls dados ferramentas resultados analises 2>/dev/null | head -50 && wc -l conhecimento/manual_decisoes.md`
- `Read`: `/tmp/copias_validacao/T02_r2/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/breast-cancer.arff`
- `Read`: `/tmp/copias_validacao/T02_r2/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo breast-cancer.arff; ls -t resultados | head -3`

### Agente

Agora o perfil dos atributos nominais (contagens por valor, distribuição da classe, duplicatas), que o resumo do Weka não mostra. Vou registrar o script conforme as regras do projeto.

- `Bash`: `cat requirements.txt; ls analises/scripts 2>/dev/null; grep -n "@attribute" dados/breast-cancer.arff`
- `Write`: `/tmp/copias_validacao/T02_r2/analises/scripts/2026-11-21_perfil_breast_cancer.py`
- `Bash`: `python3 analises/scripts/2026-11-21_perfil_breast_cancer.py`

### Agente

Não existe um algoritmo que seja o melhor para qualquer base. O certo aqui é testar alguns candidatos nas mesmas condições e escolher pelo resultado no Weka. Antes de rodar qualquer modelo, preciso de três respostas suas: o objetivo é **prever**, e o custo de cada tipo de erro é uma decisão sua, não algo que os dados dizem.

## O que já fiz: exploração da base

Comandos: `python3 ferramentas/weka_runner.py resumo breast-cancer.arff` e `python3 analises/scripts/2026-11-21_perfil_breast_cancer.py`. A saída do perfil ficou em `resultados/20261121_141451_perfil_breast_cancer.txt`.

| Item | O que encontrei | Consequência |
|---|---|---|
| Tamanho | 286 pacientes, 9 atributos e a classe | Base pequena, então as estimativas terão margem de erro larga |
| Classe | 201 sem recorrência (70,3%) e 85 com recorrência (29,7%) | Um modelo que sempre diz "não recorre" já acerta cerca de 70%. Acurácia sozinha engana |
| Tipos | Os 9 atributos são nominais | Idade, tamanho do tumor, linfonodos e grau são **faixas com ordem**, mas os algoritmos vão tratá-las como categorias soltas e perder a ordem |
| Ausentes | `node-caps`: 8 (2,8%); `breast-quad`: 1 | Poucos. Deixo cada algoritmo tratar do seu jeito |
| Valores raros | Por exemplo, `age=20-29` com 1 caso e `inv-nodes=24-26` com 1 caso | Uma árvore pode criar ramos com base em um único paciente |
| Registros repetidos | 14 linhas idênticas a outra | Com atributos em faixas largas, pacientes diferentes podem coincidir. Por isso não removo |
| Rótulos conflitantes | 6 combinações iguais de atributos com desfechos diferentes | Há um limite de acerto que nenhum algoritmo ultrapassa com esses atributos |

**Hipóteses (ainda não são conclusões).** Pelas tabelas cruzadas, a taxa de recorrência sobe bastante com:
- `deg-malig=3`: 52,9%, contra 16,9% no grau 1;
- `node-caps=yes`: 55,4%, contra 23,0%;
- `inv-nodes` acima de 0-2;
- `irradiat=yes`: 45,6%.

Só os modelos vão dizer se esses sinais servem para prever casos novos.

## Candidatos que pretendo testar, e por quê

- **ZeroR**: linha de base obrigatória.
- **J48** e **JRip**: lidam bem com atributos nominais e com ruído quando há poda. O JRip concentra o esforço na classe minoritária, que aqui é a recorrência.
- **NaiveBayes**: resiste bem a ruído e a atributos irrelevantes, e costuma ir bem em bases pequenas e todas nominais como esta.
- **SMO com `-M`**: o `-M` é necessário para a AUC ter sentido.
- **IBk com `-X`**: o k será escolhido por validação interna, não pelo resultado do teste.
- **RandomForest**: serve como referência de teto. Com só 9 atributos, a diversidade entre as árvores é limitada.

Tudo será rodado com validação cruzada estratificada de 10 partes e semente 1. Depois uso o teste t pareado corrigido para comparar o melhor modelo com a linha de base e com o segundo colocado.

## Preciso que você responda antes de eu modelar

1. **Classe de interesse:** confirma que é `recurrence-events`, ou seja, a recorrência?
2. **Qual erro custa mais, e quantas vezes mais?**
   - Falso negativo: o modelo diz "não recorre" e a paciente recorre (fica sem acompanhamento mais intenso).
   - Falso positivo: o modelo diz "recorre" e não recorre (acompanhamento ou tratamento extra sem necessidade).
   - Se você não tiver um número, minha **proposta** é que deixar passar uma recorrência custe **3 vezes** mais que um alarme falso. Esse valor não vem dos dados: é uma suposição de que perder um caso é bem mais grave. Ainda assim, é decisão sua, e eu também poderia mostrar o resultado com 2 e com 5.
3. **Em que momento a previsão seria feita?** `irradiat` registra se a paciente fez radioterapia, ou seja, uma decisão de tratamento. Se a previsão for feita **antes** de decidir o tratamento, esse atributo não estaria disponível e deve sair da base. Se for **depois**, pode ficar.

Com essas respostas eu monto a matriz de custo, fixo a métrica principal (custo total) **antes** de ver os resultados e rodo todos os candidatos no Weka.

**Ainda não executei nenhum modelo, nem mesmo o ZeroR.** Por isso não há métricas de desempenho nesta resposta.


### Usuário

Deixar de prever uma recorrência é 3 vezes pior que um alarme falso.


### Agente

Combinado: a classe de interesse é a recorrência, e deixar passar uma recorrência custa 3 vezes mais que um alarme falso. Antes de rodar, vejo como as ferramentas recebem a matriz de custo e como as análises anteriores do projeto fizeram isso.

- `Bash`: `wc -l ferramentas/*.py && grep -n "custo\|cost\|def \|argv\|add_argument" ferramentas/weka_runner.py | head -60`
- `Bash`: `sed -n 1,80p analises/2026-10-31_credit-g_v3.md`
- `Bash`: `sed -n 1,60p ferramentas/significancia.py && grep -n "CostSensitive\|ZeroR\|linha de base\|todos\|def " ferramentas/significancia.py`
- `Bash`: `sed -n 176,205p ferramentas/significancia.py && sed -n 366,540p ferramentas/significancia.py`
- `Bash`: `python3 ferramentas/weka_runner.py comparar breast-cancer.arff weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 3.0 0.0]" -W weka.classifiers.bayes.NaiveBayes -- 2>&1 | grep -v "Picked up"`

### Agente

O NaiveBayes rodou. Agora rodo os outros cinco candidatos, mostrando só o bloco da validação cruzada:

- `Bash`: `run(){ nome=$1; shift; python3 ferramentas/weka_runner.py comparar breast-cancer.arff weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 3.0 0.0]" -W "$@" > /tmp/claude-0/-tmp-copias-validacao-T02-r2/d70d621a-dae3-43d4-9746-1db9fd471d3b/scratchpad/$nome.txt 2>&1; }
mkdir -p /tmp/c`
- `Bash`: `cd /tmp/copias_validacao/T02_r2/ferramentas && S=/tmp/claude-0/-tmp-copias-validacao-T02-r2/d70d621a-dae3-43d4-9746-1db9fd471d3b/scratchpad
python3 significancia.py breast-cancer.arff --a weka.classifiers.bayes.NaiveBayes --b weka.classifiers.rules.ZeroR --custo "0 1; 3 0" --positiva recurrence-even`
- `Bash`: `S=/tmp/claude-0/-tmp-copias-validacao-T02-r2/d70d621a-dae3-43d4-9746-1db9fd471d3b/scratchpad; grep -E "^\| |Relatório" $S/sig_smo.txt; cd /tmp/copias_validacao/T02_r2; ls -t resultados | head -16; grep -n "neighbour\|nearest" $S/IBk.txt | head; grep -nE "Number of Leaves|Size of the tree" $S/J48.txt`
- `Bash`: `python3 -c "
from math import sqrt
n=286;z=1.96
for m,c in [('ZeroR(todos recorre)',85),('NaiveBayes',190),('SMO',175),('IBk',182),('JRip',169),('RF',177),('J48',160)]:
  p=c/n;d=1+z*z/n;ce=(p+z*z/(2*n))/d;h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
  print(f'{m}: {100*p:.1f}% ({100*(ce-h):.1f}-{100*(ce+h):.1`
- `Write`: `/tmp/copias_validacao/T02_r2/analises/2026-11-21_breast-cancer.md`

### Agente

Minha recomendação é o **NaiveBayes ajustado pela matriz de custo**. Ele teve o menor custo de todos e foi o único dos testados que ficou significativamente mais barato que não usar modelo nenhum. Mas ele **não venceu** o SMO de forma comprovada: os dois empataram no teste. Escolho o NaiveBayes por ser o mais simples dos dois.

**Uma suposição sua para confirmar:** mantive o atributo `irradiat`, como se a previsão fosse feita **depois** de decidir a radioterapia. Você não respondeu essa pergunta, e eu não testei a base sem esse atributo.

## 1. O que foi feito
- **Pré-processamento:** nenhum. Os ausentes (8 em `node-caps` e 1 em `breast-quad`) ficaram para cada algoritmo tratar.
- **Custo:** cada candidato rodou dentro do `CostSensitiveClassifier` com a matriz `[0 1; 3 0]`. Esse classificador dá mais peso aos casos de recorrência no treino.
- **Métrica principal:** custo total, definida antes de ver os resultados. Quanto menor, melhor.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1. Testei 6 configurações além da linha de base.
- **Comando do NaiveBayes:**
  `python3 ferramentas/weka_runner.py comparar breast-cancer.arff weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 1.0; 3.0 0.0]" -W weka.classifiers.bayes.NaiveBayes --`

## 2. Resultado do Weka (somente validação cruzada)

Matriz de confusão do NaiveBayes:
```
                 prev. não   prev. recorre
real não            133          68
real recorre         28          57
```
Custo = 68×1 + 28×3 = **152**.

| Modelo | Acurácia (IC 95%) | Kappa | Recall rec. | Precisão rec. | F1 rec. | AUC | Custo |
|---|---:|---:|---:|---:|---:|---:|---:|
| **NaiveBayes** | 66,4% (60,8–71,7) | 0,293 | 0,671 | 0,456 | 0,543 | 0,698 | **152** |
| SMO `-M` | 61,2% (55,4–66,7) | 0,203 | 0,635 | 0,403 | 0,493 | 0,650 | 173 |
| IBk (k = 13, escolhido por validação interna) | 63,6% (57,9–69,0) | 0,210 | 0,565 | 0,417 | 0,480 | 0,635 | 178 |
| JRip | 59,1% (53,3–64,6) | 0,156 | 0,588 | 0,379 | 0,461 | 0,599 | 187 |
| RandomForest | 61,9% (56,1–67,3) | 0,148 | 0,482 | 0,387 | 0,429 | 0,629 | 197 |
| J48 | 55,9% (50,1–61,6) | 0,109 | 0,576 | 0,353 | 0,437 | 0,553 | 198 |

## 3. Comparação com a linha de base
Com matriz de custo há duas linhas de base:
- **Prever "não recorre" para todas** (o ZeroR comum): acerta 70,3%, mas deixa passar as 85 recorrências. Custo de 85×3 = 255.
- **Prever "recorre" para todas:** custo de 201×1 = **201**. Esta é a linha de base que vale, porque é a mais barata.

Todos os modelos ficaram abaixo de 201. Porém J48 (198) e RandomForest (197) ficaram **praticamente no nível de não ter modelo**. Não os recomendo.

Note que a acurácia do NaiveBayes (66%) é **menor** que a do ZeroR comum (70%), e mesmo assim ele é muito mais útil. A acurácia não mede o que importa aqui.

## 4. Confiabilidade
Teste t pareado corrigido, com 10 repetições de validação cruzada de 10 partes, sobre o custo:
- **NaiveBayes × linha de base:** custo médio de 15,7 contra 20,1 por parte; **p = 0,0065**. A redução de custo é real.
- **NaiveBayes × SMO:** 15,7 contra 17,0; **p = 0,199**. É um **empate técnico**. Fico com o NaiveBayes por ser o mais simples.

Fiz só essas duas comparações. O ganho é real, mas modesto: em cada 10 pacientes que o modelo aponta como "recorre", só cerca de 4,6 recorrem de fato (precisão de 0,456). E 28 das 85 recorrências passam despercebidas.

## 5. Interpretação
O NaiveBayes não gera regras legíveis. Nas tabelas de probabilidade dele, os valores que mais aumentam a chance de recorrência são:
- `deg-malig=3`;
- `node-caps=yes`;
- `inv-nodes` acima de 0-2;
- `irradiat=yes`;
- tumores de 30-34.

Isso confirma o que a exploração já sugeria. São associações, não causas: a radioterapia, por exemplo, provavelmente foi indicada porque o caso já era mais grave.

## 6. Alertas e próximos passos
- **Sobreajuste na J48:** a árvore tem 24 folhas e acerta 73,4% no treino, mas só 55,9% na validação. Árvores fragmentam demais uma base de 286 casos com rótulos conflitantes.
- **Base pequena e ruidosa:** os intervalos de confiança têm cerca de 11 pontos de largura. Há combinações de atributos idênticas com desfechos opostos, o que limita o acerto de qualquer modelo.
- **Faixas ordenadas tratadas como categorias:** idade, tamanho do tumor e linfonodos perderam a ordem entre as faixas.
- **Ainda não rodei:**
  - a base sem `irradiat`;
  - os atributos convertidos em ordinais;
  - seleção de atributos;
  - o `CostSensitiveClassifier` em modo `-M`, que escolhe a previsão de menor custo esperado em vez de dar mais peso no treino;
  - o MultilayerPerceptron.
- **Antes de qualquer uso real:** esta é uma base didática antiga. Qualquer uso clínico exigiria dados atuais e validação com especialistas.

**Decisão que cabe a você:** a previsão seria feita antes ou depois de decidir a radioterapia? Se for antes, rodo de novo sem `irradiat` e digo se a conclusão muda.

O relatório completo está em `analises/2026-11-21_breast-cancer.md`, e as saídas do Weka estão em `resultados/` (arquivos de 21/11/2026).

