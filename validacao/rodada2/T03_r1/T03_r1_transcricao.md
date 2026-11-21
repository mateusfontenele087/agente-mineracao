# Transcrição T03_r1

### Usuário

Quero entender o que diferencia democratas de republicanos nessas votações (vote.arff).


### Agente

Vou começar lendo o manual de decisões e conferindo a base.

- `Bash`: `ls; ls dados ferramentas analises resultados 2>/dev/null | head -50; wc -l conhecimento/manual_decisoes.md`
- `Read`: `/tmp/copias_validacao/T03_r1/conhecimento/manual_decisoes.md`
- `Read`: `/tmp/copias_validacao/T03_r1/conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/vote.arff 2>&1 | tail -60; head -30 analises/2026-10-31_diabetes_reanalise.md`
- `Bash`: `python3 ferramentas/weka_runner.py resumo vote.arff 2>&1 | tail -60`

### Agente

Resumo rodou. Agora o perfil dos atributos por partido (descritivo, em Python) e a contagem de duplicatas.

- `Bash`: `ls analises/scripts 2>/dev/null; grep -n "^@" dados/vote.arff | head -20`
- `Write`: `/tmp/copias_validacao/T03_r1/analises/scripts/2026-11-21_perfil_vote.py`
- `Bash`: `python3 analises/scripts/2026-11-21_perfil_vote.py`
- `Bash`: `for c in "weka.classifiers.trees.J48 -C 0.25 -M 2" "weka.classifiers.rules.JRip" "weka.classifiers.bayes.NaiveBayes" "weka.classifiers.trees.RandomForest"; do echo "######## $c"; python3 ferramentas/weka_runner.py comparar vote.arff $c 2>&1 | grep -v "Picked up"; done > /tmp/claude-0/-tmp-copias-val`
- `Bash`: `F=/tmp/claude-0/-tmp-copias-validacao-T03-r1/d2fb8b7f-ecb1-490c-9ade-66634706913b/scratchpad/runs.txt; grep -n -E "########|=== Resultado|Stratified cross|Error on training|Correctly Classified|Kappa|Size of|Number of Rules|Comando|resultados/" $F | head -80`
- `Bash`: `F=/tmp/claude-0/-tmp-copias-validacao-T03-r1/d2fb8b7f-ecb1-490c-9ade-66634706913b/scratchpad/runs.txt; sed -n '76,104p;134,160p;232,254p;284,310p;511,537p;656,682p' $F | grep -v -E "ARPACK|^$"; ls -t resultados | head -10`

### Agente

J48 tem a maior acurácia na validação cruzada, e a RandomForest vem logo atrás. Agora os testes de significância na acurácia: J48 × ZeroR e J48 × RandomForest.

- `Bash`: `python3 ferramentas/significancia.py --help 2>&1 | grep -v "Picked up" | head -40`
- `Bash`: `(python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --opcoes-a="-C 0.25 -M 2" --b weka.classifiers.rules.ZeroR --positiva republican --repeticoes 10 2>&1 | grep -v -E "Picked up|ARPACK" ; echo "=================="; python3 ferramentas/significancia.py vote.arff --a weka.cl`

### Agente

Os dois testes saíram. Vou calcular os intervalos de confiança a partir dos acertos do Weka e rodar uma checagem descritiva: quanto uma única votação explica sozinha (OneR).

- `Bash`: `python3 - <<'EOF'
# IC 95% (aproximação normal) a partir dos acertos da validação cruzada do Weka
from math import sqrt
n=435
for nome,ac in [("ZeroR",267),("J48",419),("JRip",415),("NaiveBayes",392),("RandomForest",418)]:
    p=ac/n; e=1.96*sqrt(p*(1-p)/n)
    print(f"{nome:13s} {100*p:6.2f}%  IC95`

### Agente

Uma única votação já acerta 95,6% na validação cruzada. A pergunta de especialista é se o resto da árvore acrescenta algo real. Vou testar J48 × OneR.

- `Bash`: `python3 ferramentas/significancia.py vote.arff --a weka.classifiers.trees.J48 --opcoes-a="-C 0.25 -M 2" --b weka.classifiers.rules.OneR --opcoes-b="-B 6" --positiva republican --repeticoes 10 2>&1 | grep -E "^\||Relatório"`
- `Grep`: `{"pattern": "1984|Congress|\\?", "path": "/tmp/copias_validacao/T03_r1/dados/vote.arff", "output_mode": "content", "head_limit": 15}`
- `Read`: `/tmp/copias_validacao/T03_r1/dados/vote.arff`

### Agente

Tenho tudo. Vou registrar o relatório em `analises/`.

- `Write`: `/tmp/copias_validacao/T03_r1/analises/2026-11-21_vote.md`

### Agente

# O que diferencia democratas de republicanos (vote.arff)

**Resposta curta:** quase tudo se resume a **uma votação, `physician-fee-freeze`** (congelamento dos honorários médicos). 98,8% dos republicanos votaram "sim" e só 5,4% dos democratas. Essa votação sozinha classifica corretamente 95,6% dos deputados. Uma árvore um pouco maior chega a 96,3%, mas a diferença entre as duas não é estatisticamente significativa.

> Como o objetivo é **entender** e você não informou custos, tratei os dois erros como equivalentes: confundir um democrata com republicano pesa o mesmo que o contrário. Defini a **acurácia** como métrica principal antes de olhar os resultados.

## 1. O que foi feito
- **Base:** 435 deputados da Câmara dos EUA em 1984, com 16 votações sim/não. São 267 democratas (61,4%) e 168 republicanos (38,6%).
- **Qualidade dos dados:**
  - **Valores `?`:** aparecem em todas as votações, de 7 casos em `immigration` até 104 (24%) em `export-administration-act-south-africa`. O cabeçalho do arquivo avisa que `?` não quer dizer "dado desconhecido": quer dizer que o deputado não votou nem sim nem não (abstenção, por exemplo). O Weka trata esses casos como ausentes. Como a abstenção pode carregar informação, isso é uma limitação.
  - **Linhas repetidas:** 93 linhas são iguais a outras. São deputados diferentes que votaram igual, e não registros duplicados por erro, por isso mantive todas.
  - Não há identificadores nem atributos constantes.
- **Modelos:**
  - J48 e JRip, porque produzem árvore e regras legíveis.
  - NaiveBayes, como apoio.
  - RandomForest, só como referência de teto.
  - OneR, depois de ver a árvore, como checagem descritiva.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1.
- **Comando** (exemplo do J48): `python3 ferramentas/weka_runner.py comparar vote.arff weka.classifiers.trees.J48 -C 0.25 -M 2`

## 2. Resultado do Weka (só o bloco da validação cruzada)
| Modelo | Acurácia | IC 95% | Kappa | F1 republicano | AUC |
|---|---|---|---|---|---|
| ZeroR | 61,38% | 56,8–66,0 | 0 | – | 0,491 |
| **J48** | **96,32%** | 94,6–98,1 | 0,922 | 0,952 | 0,971 |
| RandomForest | 96,09% | 94,3–97,9 | 0,918 | 0,949 | 0,993 |
| OneR (1 votação) | 95,63% | – | 0,909 | 0,945 | 0,959 |
| JRip | 95,40% | 93,4–97,4 | 0,904 | 0,942 | 0,942 |
| NaiveBayes | 90,11% | 87,3–92,9 | 0,795 | 0,877 | 0,973 |

Matriz de confusão do J48:
```
   dem  rep   <- previsto
   259    8 | democrat
     8  160 | republican
```
O J48 erra pouco e erra de forma equilibrada: 8 democratas e 8 republicanos.

## 3. Comparação com o ZeroR
Prever sempre "democrata" acerta 61,4%. O J48 acerta 34,9 pontos a mais. No teste t pareado corrigido, com 10 repetições de 10 partes, essa vantagem é significativa (p < 0,001). As votações explicam o partido de verdade.

## 4. Confiabilidade
Fiz três comparações na métrica principal:
- **J48 × ZeroR:** J48 melhor, p < 0,001.
- **J48 × RandomForest:** empate técnico, p = 0,83. A árvore legível não perde nada para o modelo caixa-preta, então a interpretabilidade sai de graça nesta base.
- **J48 × OneR:** empate técnico na acurácia, p = 0,16.
  - Em precisão para "republicano", o J48 ficou à frente (0,96 contra 0,92; p = 0,003). Essa métrica é só descritiva. Ela passa no limiar corrigido para 4 métricas (0,0125), mas não decide a escolha.
  - Na prática, as votações extras da árvore servem para não rotular como republicanos alguns democratas que votaram "sim" no congelamento.

Seguindo a regra de preferir o modelo mais simples quando há empate, **a descrição mais honesta é a de uma votação só**. A árvore acrescenta detalhes sobre as exceções.

## 5. Interpretação

Árvore do J48 (6 folhas):
```
physician-fee-freeze = n → democrat
physician-fee-freeze = y
|  synfuels-corporation-cutback = n → republican
|  synfuels-corporation-cutback = y
|  |  mx-missile = y → democrat
|  |  mx-missile = n
|  |  |  adoption-of-the-budget-resolution = n → republican
|  |  |  adoption-of-the-budget-resolution = y → (anti-satellite-test-ban decide; folhas com ~2 e ~5 casos)
```
- **Quem votou "não" no congelamento** é democrata em quase todos os casos (cerca de 253 casos, ~4 erros).
- **Quem votou "sim"** é republicano, a não ser que também tenha apoiado o corte na `synfuels-corporation` **e** o míssil MX. Esse perfil identifica os democratas que se desviam da linha do partido.
- **Ramos mais fundos:** as folhas mais profundas têm de 2 a 5 casos. Essas divisões têm pouca base e não devem ser levadas a sério.
- **Regras do JRip:** dizem o mesmo. As três regras para "republicano" começam por `physician-fee-freeze = y`; o resto é democrata.

**Visão geral das votações** (diferença na % de "sim" entre os partidos, calculada em Python sobre o `.arff`):
- **Muito polarizadas** (diferença acima de 60 pontos): congelamento dos honorários (−93), orçamento (+75), ajuda a El Salvador (−74), gastos com educação (−73), ajuda aos Contras (+68), míssil MX (+64) e crime (−63).
- **Sem diferença:** `water-project-cost-sharing` (−0,5) e `immigration` (−8,6). Essas votações não separam os partidos.

Por que as outras votações polarizadas não aparecem na árvore? Os deputados votam em bloco. Depois que a árvore usa o congelamento, as demais votações trazem quase a mesma informação e ficam de fora. Elas não são irrelevantes, são redundantes. O mesmo efeito explica o NaiveBayes ter ficado atrás: ele conta várias vezes a mesma evidência, porque supõe que as votações são independentes entre si.

## 6. Alertas e próximos passos
- **Sobreajuste:** não há sinal. O J48 acerta 97,2% no treino e 96,3% na validação; o JRip, 96,6% e 95,4%. Não comparei treino e validação da RandomForest, porque ela acerta o treino por construção.
- **Abstenções (`?`):** como o `?` tem significado próprio, um próximo passo útil seria transformar o `?` num terceiro valor ("outro") e repetir a análise, para ver se as abstenções também diferenciam os partidos. **Não rodei isso.**
- **Escopo:** os dados são de uma única sessão da Câmara (1984). As conclusões descrevem aquele momento político e não valem automaticamente para outros períodos.
- **Associação, não causa:** a árvore mostra o que acompanha o partido nas votações, e não o que leva alguém a ser de um partido.
- **Não rodado:** SMO, IBk e MultilayerPerceptron. Com o objetivo de entender, e com o J48 empatado com a RandomForest, eles não mudariam a conclusão.

Fiz 6 rodadas de classificação (ZeroR, J48, JRip, NaiveBayes, RandomForest e OneR) e 3 testes de significância.

Arquivos:
- Relatório: `analises/2026-11-21_vote.md`
- Script do perfil: `analises/scripts/2026-11-21_perfil_vote.py`
- Saídas do Weka: `resultados/20261121_14*`

