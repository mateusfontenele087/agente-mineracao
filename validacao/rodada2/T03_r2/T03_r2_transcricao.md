# Transcrição T03_r2

### Usuário

Quero entender o que diferencia democratas de republicanos nessas votações (vote.arff).


### Agente

Vou começar lendo o manual de decisões, como manda o fluxo, e localizar a base.

- `Bash`: `ls && ls dados ferramentas resultados analises 2>/dev/null | head -50 && wc -l conhecimento/manual_decisoes.md && find / -name "vote.arff" 2>/dev/null | head`
- `Read`: `/tmp/copias_validacao/T03_r2/conhecimento/manual_decisoes.md`
- `Read`: `/tmp/copias_validacao/T03_r2/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/vote.arff 2>&1 | tail -60; head -60 dados/vote.arff | grep -i "@attribute"`
- `Bash`: `python3 ferramentas/weka_runner.py resumo vote.arff 2>&1 | tail -70`

### Agente

Weka rodou. Agora o perfil descritivo (distribuição da classe, votos por partido, ausentes, duplicatas) em Python, com o script registrado.

- `Bash`: `mkdir -p analises/scripts && cat > analises/scripts/2026-11-21_perfil_vote.py <<'EOF'
# Perfil descritivo da base vote.arff (só estatística descritiva, sem modelo).
# Uso: python3 analises/scripts/2026-11-21_perfil_vote.py
import re, collections, datetime

caminho = "dados/vote.arff"
atributos, linh`

### Agente

Perfil pronto. Antes de modelar, vejo o que `significancia.py` aceita como métrica, para fixar a métrica principal.

- `Bash`: `python3 ferramentas/significancia.py --help 2>&1 | tail -30; grep -n "metric\|acur\|percent_correct\|kappa\|f_measure" ferramentas/significancia.py | head -30`
- `Bash`: `for c in "weka.classifiers.trees.J48 -C 0.25 -M 2" "weka.classifiers.rules.JRip" "weka.classifiers.bayes.NaiveBayes" "weka.classifiers.trees.RandomForest"; do echo "######## $c"; python3 ferramentas/weka_runner.py comparar vote.arff $c 2>&1 | grep -v "Picked up"; done > /tmp/claude-0/-tmp-copias-val`
- `Read`: `/tmp/claude-0/-tmp-copias-validacao-T03-r2/96a26990-d16f-4249-a893-6b9105785fe3/scratchpad/saida.txt`
- `Bash`: `cd /tmp/claude-0/-tmp-copias-validacao-T03-r2/96a26990-d16f-4249-a893-6b9105785fe3/scratchpad && awk 'NR>=311' saida.txt | grep -n -A 25 "=== Stratified cross-validation ===" | grep -v "^--$" | sed -n '27,200p'`

### Agente

Quatro candidatos rodaram. J48 tem a maior acurácia (96,32%), seguido de RandomForest (96,09%). Pela regra, faço dois testes: J48 contra o ZeroR e J48 contra o segundo colocado (RandomForest).

- `Bash`: `python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --opcoes-a="-C 0.25 -M 2" --b weka.classifiers.rules.ZeroR --positiva republican --repeticoes 10 2>&1 | grep -v "Picked up\|ARPACK\|WARNING" | tail -40`
- `Bash`: `python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --opcoes-a="-C 0.25 -M 2" --b weka.classifiers.trees.RandomForest --positiva republican --repeticoes 10 2>&1 | grep -v "Picked up\|ARPACK\|WARNING" | tail -40`

### Agente

Os dois testes rodaram. Falta o intervalo de confiança de 95% das acurácias, que calculo a partir dos acertos que o Weka informou.

- `Bash`: `python3 -c "
import math
n=435
for nome,ac in [('ZeroR',267),('J48',419),('RandomForest',418),('JRip',415),('NaiveBayes',392)]:
    p=ac/n; m=1.96*math.sqrt(p*(1-p)/n)
    print(f'{nome:13s} {100*p:6.2f}%  IC95% [{100*(p-m):.2f}; {100*(p+m):.2f}]')
" | tee resultados/20261121_ic_vote.txt`

### Agente

Antes de escrever a interpretação, confiro no cabeçalho do arquivo o que o `?` significa nesta base.

- `Grep`: `{"pattern": "\\?|unknown|present|abstain", "path": "/tmp/copias_validacao/T03_r2/dados/vote.arff", "output_mode": "content", "head_limit": 15, "-i": true}`
- `Write`: `/tmp/copias_validacao/T03_r2/analises/2026-11-21_vote.md`

### Agente

# O que diferencia democratas de republicanos (vote.arff)

**Em resumo:** um único voto quase separa os dois partidos. Quem votou **contra o congelamento de honorários médicos** (`physician-fee-freeze = n`) é democrata em quase todos os casos. Isso vale para 253 dos 435 parlamentares, com cerca de 4 erros. Entre quem votou a favor, a maioria é republicana. O voto sobre **cortes na corporação de combustíveis sintéticos** (`synfuels-corporation-cutback`) separa a maior parte dos poucos democratas que estão nesse grupo.

Você disse que quer **entender**, não prever. Por isso não perguntei qual erro custa mais e tratei os dois erros como equivalentes.

## 1. O que foi feito
- **A base:** 435 parlamentares, 16 votos (sim/não) e 2 classes: 267 democratas (61,4%) e 168 republicanos (38,6%).
- **Qualidade dos dados:**
  - Não há identificadores nem atributos constantes.
  - O cabeçalho do arquivo diz que `?` **não é** "valor desconhecido". Significa que o parlamentar não votou nem sim nem não: votou "presente", se absteve ou faltou. Em cada votação, de 2% a 24% dos parlamentares estão nessa situação.
  - 93 linhas repetem outras. São parlamentares diferentes que votaram igual, por isso ficaram. Nenhum perfil de votos idêntico aparece com partidos diferentes.
  - Não houve pré-processamento.
- **Modelos testados:**
  - J48 (árvore) e JRip (regras): são legíveis, que é o que serve para entender.
  - NaiveBayes: como apoio.
  - RandomForest: só como referência de teto, ou seja, o melhor desempenho que um modelo não legível alcança.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1. **Métrica principal: acurácia**, definida antes de ver os resultados.
- **Comando:** `python3 ferramentas/weka_runner.py comparar vote.arff weka.classifiers.trees.J48 -C 0.25 -M 2`. Os outros modelos rodaram com o mesmo comando, trocando o classificador.

## 2–4. Resultados do Weka (somente o bloco de validação cruzada)

| Modelo | Acurácia (IC 95%) | Kappa | F1 dos republicanos | AUC |
|---|---|---|---|---|
| ZeroR | 61,38% [56,80; 65,95] | 0 | — | 0,491 |
| **J48** | **96,32% [94,55; 98,09]** | 0,922 | 0,952 | 0,971 |
| RandomForest (teto) | 96,09% [94,27; 97,91] | 0,918 | 0,949 | 0,993 |
| JRip | 95,40% [93,43; 97,37] | 0,904 | 0,942 | 0,942 |
| NaiveBayes | 90,11% [87,31; 92,92] | 0,795 | 0,877 | 0,973 |

**Matriz de confusão do J48** (linhas = partido real):

| | previsto democrata | previsto republicano |
|---|---|---|
| democrata | 259 | 8 |
| republicano | 8 | 160 |

Os erros estão equilibrados entre os dois partidos.

**Teste de significância** (teste t pareado corrigido, 10 repetições da validação cruzada de 10 partes, métrica acurácia):
- **J48 contra ZeroR:** 0,966 contra 0,614, p < 0,000001. A diferença é real.
- **J48 contra RandomForest:** 0,966 contra 0,965, p = 0,83. É **empate técnico**: a árvore legível não perde nada para o modelo não legível. Fico com a árvore, que é mais simples e explica o resultado.

Rodei 4 candidatos e fiz 2 comparações.

## 5. Interpretação
```
physician-fee-freeze = n → democrata            (253 casos, ~4 erros)
physician-fee-freeze = y
   synfuels-cutback = n → republicano           (146 casos, 4 erros)
   synfuels-cutback = y → mx-missile, budget, anti-satellite...  (folhas de 2 a 23 casos)
```
- **O voto mais decisivo:** só 5,4% dos democratas votaram a favor do congelamento de honorários, contra 98,8% dos republicanos.
- **Outros votos que também separam bem os partidos:**
  - resolução orçamentária: 89% dos democratas a favor, 13% dos republicanos;
  - ajuda a El Salvador: 22% contra 95%;
  - gastos com educação: 15% contra 87%;
  - ajuda aos Contras: 83% contra 15%.

  A árvore não usa esses votos porque eles andam juntos com o primeiro: os partidos votam em bloco. Depois do primeiro voto, eles acrescentam pouca informação. Isso não quer dizer que não diferenciem os partidos.
- **Votos que não separam os partidos:** cota de custos de projetos de água (50% contra 51%) e imigração (47% contra 56%).
- **As regras do JRip confirmam a árvore:** o parlamentar é republicano se votou a favor do congelamento **e** contra o corte de combustíveis sintéticos, a favor da lei de exportação para a África do Sul ou contra a resolução orçamentária. Caso contrário, é democrata.

## 6. Alertas e próximos passos
- **Folhas pequenas:** os ramos mais profundos da árvore se apoiam em 2 a 6 casos. Não interprete esses ramos como padrões. São os poucos parlamentares que votaram fora da linha do próprio partido.
- **Abstenção tratada como "desconhecido":** os modelos trataram `?` como valor ausente, mas aqui a abstenção pode ser informação. Por exemplo, 31% dos democratas se abstiveram na lei sobre a África do Sul, contra 13% dos republicanos. **Não rodei** o cenário em que `?` vira um terceiro valor ("absteve"). Posso rodar se você quiser ver se isso muda a conclusão.
- **Período limitado:** os dados são de uma única legislatura, então a conclusão não se estende a outros períodos.

**Arquivos gerados:**
- relatório: `analises/2026-11-21_vote.md`
- script do perfil: `analises/scripts/2026-11-21_perfil_vote.py`
- saídas: em `resultados/` (perfil, intervalos de confiança e os dois testes de significância)

