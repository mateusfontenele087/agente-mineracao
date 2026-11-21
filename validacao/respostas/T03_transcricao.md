# Transcrição T03

### Usuário

Quero entender o que diferencia democratas de republicanos nessas votações (vote.arff).


### Agente

Vou começar lendo o manual de decisões e localizando a base.

- `Bash`: `ls; ls dados ferramentas resultados 2>/dev/null | head -50; wc -l conhecimento/manual_decisoes.md`
- `Read`: `/home/user/agente-mineracao/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/vote.arff`

### Agente

A parte que falta do manual trata de associação, agrupamento e anomalias, que não se aplicam aqui. Agora o resumo da base:

- `Bash`: `python3 ferramentas/weka_runner.py resumo vote.arff; head -40 dados/vote.arff | grep -i "@attr"`

### Agente

Antes de modelar, vou montar o perfil em Python (distribuição da classe, duplicatas, ausentes por partido e voto "sim" por partido) e salvar em `resultados/`.

- `Bash`: `ls analises validacao; sed -n 1,60p ferramentas/weka_runner.py | head -60`
- `Bash`: `mkdir -p analises/scripts 2>/dev/null; cat > analises/scripts/perfil_vote.py <<'EOF'
"""Perfil descritivo da base vote.arff (só contagens; nenhum modelo aqui)."""
from collections import Counter
from datetime import datetime
from pathlib import Path

linhas, atributos, dados = Path("dados/vote.arff"`
- `Bash`: `for c in "weka.classifiers.trees.J48 -C 0.25 -M 2" "weka.classifiers.rules.JRip" "weka.classifiers.bayes.NaiveBayes" "weka.classifiers.trees.RandomForest"; do echo "=========== $c"; python3 ferramentas/weka_runner.py comparar vote.arff $c 2>&1 | grep -v "Picked up"; done > /tmp/claude-0/-home-user-a`
- `Read`: `/tmp/claude-0/-home-user-agente-mineracao/a019b214-914e-4e76-a2c6-144bb698bb01/scratchpad/runs.txt`

### Agente

J48 tem a maior acurácia, mas J48, RandomForest e JRip estão muito próximos. Pela regra, preciso testar a significância: J48 contra ZeroR e J48 contra o segundo melhor (RandomForest).

- `Bash`: `python3 ferramentas/significancia.py -h 2>&1 | grep -v "Picked up"`
- `Bash`: `python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --b weka.classifiers.rules.ZeroR --positiva republican --repeticoes 10 2>&1 | grep -v -e "Picked up" -e ARPACK -e "^Nov"; echo ==========; python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --b w`

### Agente

Para o objetivo de **entender**, também importa saber se a árvore e as regras empatam, e quanto uma única votação explica sozinha (OneR). Vou rodar as duas coisas.

- `Bash`: `python3 ferramentas/weka_runner.py comparar vote.arff weka.classifiers.rules.OneR -B 6 2>&1 | sed -n '/Resultado do classificador/,$p' | grep -v -e ARPACK -e "^Nov" | sed -n '1,20p;/Stratified/,$p'; echo =======; python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --b weka.`

### Agente

O OneR, usando uma única votação, chegou a 95,6%. Isso muda a pergunta principal: **a árvore acrescenta alguma coisa além dessa votação?** Vou testar.

- `Bash`: `python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --b weka.classifiers.rules.OneR --positiva republican --repeticoes 10 2>&1 | grep -A8 "Resumo por"; python3 -c "
import math
for n,a in [('ZeroR',267),('J48',419),('RF',418),('OneR',416),('JRip',415),('NB',392)]:
    p=a/4`
- `Write`: `/home/user/agente-mineracao/analises/2026-11-21_vote.md`

### Agente

# O que diferencia democratas de republicanos (vote.arff)

**Resposta curta:** uma única votação, o **congelamento de honorários médicos** (*physician-fee-freeze*), separa os dois partidos em cerca de 96% dos casos. Os outros modelos refinam essa separação, mas nenhum fica significativamente melhor do que essa regra simples.

## 1. O que foi feito

**Enquadramento.** É um problema de classificação com alvo binário (democrata/republicano). Seu objetivo é **entender** o que separa os partidos, então dei prioridade a modelos legíveis: J48 (árvore), JRip (regras) e OneR (a melhor regra de um só atributo). O NaiveBayes entrou como apoio e o RandomForest só como referência de teto.

**Métrica principal.** Escolhi a **acurácia** antes de ver os resultados. As classes estão em 267 × 168 (61/39), um desequilíbrio leve, e quando o objetivo é descrever não existe um erro que custe mais que o outro.

**Exploração.** Os números estão em `resultados/20261121_132611_perfil_vote.txt`. São 435 parlamentares e 16 votações, todas sim/não.
- **Valores `?`:** 203 registros têm pelo menos um. Nesta base, `?` quer dizer que o parlamentar não votou nem sim nem não (abstenção, ausência). Mantive esses valores como estão: o J48 distribui o caso pelos ramos e o NaiveBayes ignora o atributo. Um ponto de atenção: na votação sobre exportações para a África do Sul (*export-administration-act-south-africa*), 31% dos democratas não votaram, contra 13% dos republicanos. Aqui a ausência pode carregar informação.
- **Duplicatas:** 93 registros repetem exatamente um perfil de voto. São legítimos (parlamentares diferentes que votaram igual, seguindo o partido), por isso ficaram na base.
- **Conflitos:** nenhum perfil de voto idêntico aparece com partidos diferentes.

**Avaliação.** Validação cruzada estratificada de 10 partes, semente 1. Comando: `python3 ferramentas/weka_runner.py comparar vote.arff <classificador> [opções]`.

## 2 e 3. Resultados do Weka (validação cruzada) e comparação com o ZeroR

| Modelo | Acurácia (IC 95%) | Kappa | Recall rep. | Precisão rep. | F1 rep. |
|---|---|---|---|---|---|
| **ZeroR** (linha de base) | 61,38% [56,8; 66,0] | 0,000 | 0,000 | — | — |
| J48 `-C 0.25 -M 2` | 96,32% [94,6; 98,1] | 0,922 | 0,952 | 0,952 | 0,952 |
| RandomForest (teto) | 96,09% [94,3; 97,9] | 0,918 | 0,946 | 0,952 | 0,949 |
| OneR `-B 6` | 95,63% [93,7; 97,6] | 0,909 | 0,970 | 0,921 | 0,945 |
| JRip | 95,40% [93,4; 97,4] | 0,904 | 0,958 | 0,925 | 0,942 |
| NaiveBayes | 90,11% [87,3; 92,9] | 0,795 | 0,917 | 0,842 | 0,877 |

Matriz de confusão do J48 (linhas = partido real):
```
          dem  rep
democrat  259    8
republican  8  160
```

## 4. Confiabilidade

Teste t pareado corrigido, com 10 repetições de validação cruzada de 10 partes, feito na acurácia:

| Comparação | p | Conclusão |
|---|---|---|
| J48 × ZeroR | < 0,000001 | J48 significativamente melhor |
| J48 × RandomForest | 0,832 | empate técnico |
| J48 × JRip | 0,145 | empate técnico |
| J48 × OneR | 0,160 | empate técnico |

- **Modelos úteis:** existem. Superam a linha de base por mais de 34 pontos percentuais.
- **Quem venceu:** ninguém. J48, RandomForest, JRip e OneR estão empatados. Entre modelos empatados prefere-se o mais simples, e o mais simples é o OneR, com uma única pergunta.
- **Métrica secundária:** a precisão para republicanos do J48 ficou acima da do OneR (p = 0,003), e esse valor passa no limiar corrigido para 4 métricas (0,0125). Mas a decisão é tomada pela acurácia; a precisão só mostra *onde* a árvore ajuda (próxima seção).
- **Sobreajuste:** não há sinal. O J48 acerta 97,2% no treino e 96,3% na validação.

## 5. Interpretação: o que os dados revelam

**A regra principal (OneR):**
- Votou **"sim" no congelamento de honorários médicos** → republicano.
- Votou **"não"** ou não votou → democrata.

O perfil mostra por que funciona: 98,8% dos republicanos votaram "sim", contra 5,4% dos democratas.

**O que a árvore acrescenta:** ela trata a exceção, os democratas que votaram "sim" no congelamento.
```
congelamento de honorários = não  → democrata (253 casos)
congelamento de honorários = sim
├─ corte no subsídio a combustíveis sintéticos = não → republicano (146)
└─ corte no subsídio a combustíveis sintéticos = sim
   ├─ míssil MX = sim → democrata (6)
   └─ míssil MX = não
      ├─ resolução orçamentária = não → republicano (23)
      └─ resolução orçamentária = sim → depende do tratado antissatélite (7 casos)
```
- O primeiro desdobramento (corte no subsídio a combustíveis sintéticos) tem boa base: 146 casos.
- A partir do míssil MX, as folhas têm de 2 a 7 casos. Leia esses ramos como pistas, não como padrões firmes.

**Outras votações com grande diferença entre partidos** (perfil descritivo, % de "sim" entre democratas × republicanos):
- Ajuda a El Salvador: 22% × 95%
- Gastos com educação: 15% × 87%
- Endurecimento penal (*crime*): 35% × 98%
- Resolução orçamentária: 89% × 13%
- Míssil MX: 76% × 12%
- Ajuda aos *contras* da Nicarágua: 83% × 15%

**Por que o NaiveBayes ficou atrás:** essas votações seguem a mesma linha partidária, ou seja, são fortemente redundantes entre si. O NaiveBayes trata cada uma como evidência independente e acaba contando a mesma informação várias vezes. Isso não foi testado com significância contra o J48; é só uma diferença descritiva.

## 6. Alertas e próximos passos

- **"Diferencia" não é "causa":** o modelo mostra como os partidos *votaram*, não por quê.
- **Viés de otimismo:** testei 6 configurações e fiz 4 testes de significância. Os números do melhor modelo tendem a ser um pouco otimistas.
- **Duplicatas:** os 93 perfis repetidos podem cair no treino e no teste ao mesmo tempo, o que infla um pouco a acurácia. Não rodei a versão sem duplicatas.
- **O que não foi rodado:**
  - um atributo indicador de "não votou";
  - o modelo sem a votação do congelamento de honorários, que mostraria o *segundo* melhor separador;
  - SMO e IBk, porque não ajudam a entender.

  Se quiser, posso rodar o modelo sem o congelamento de honorários em seguida. É o passo que mais acrescentaria à sua pergunta.

O registro completo está em `analises/2026-11-21_vote.md`. O script do perfil é `analises/scripts/perfil_vote.py`.

