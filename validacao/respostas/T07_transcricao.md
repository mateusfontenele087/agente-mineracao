# Transcrição T07

### Usuário

Quais máquinas dessa base (cpu.arff) parecem fora do padrão e merecem revisão?


### Agente

Vou começar lendo o manual de decisões e localizando a base.

- `Grep`: `{"pattern": "(?i)anomal|atípic|outlier|LOF|IQR", "path": "/home/user/agente-mineracao/conhecimento/manual_decisoes.md", "output_mode": "content", "-n": true}`
- `Glob`: `{"pattern": "**/cpu*.arff"}`
- `Bash`: `ls ferramentas resultados dados 2>/dev/null | head -50`
- `Read`: `/home/user/agente-mineracao/conhecimento/manual_decisoes.md`
- `Bash`: `cat dados/cpu.arff | grep -v '^%' | head -30 && python3 ferramentas/weka_runner.py resumo dados/cpu.arff`
- `Bash`: `python3 ferramentas/weka_runner.py resumo cpu.arff; grep -n -A6 -E '^\*\*R(8\.04|8\.16|2\.07|2\.18|3\.03)' conhecimento/manual_decisoes.md`
- `Bash`: `sed -n 1,80p ferramentas/agrupamento.py; grep -n "def \|AddCluster\|resultados" ferramentas/agrupamento.py | head -40; grep -n "def \|WEKA\|weka.jar\|classpath" ferramentas/weka_runner.py | head -30; ls ~/wekafiles/packages 2>/dev/null`
- `Bash`: `mkdir -p resultados/anomalias_cpu && cat > resultados/anomalias_cpu/perfil.py <<'EOF'
# Perfil descritivo de cpu.arff (estatística descritiva em Python, sem modelos).
import statistics as st, sys
from collections import Counter
linhas = open("dados/cpu.arff").read().splitlines()
i = [n for n, l in e`
- `Bash`: `f=resultados/20261121_132701_299622_anomalias_cpu_iqr.arff; ls resultados/*iqr* ; grep -i "@attribute\|^%" $f | head; ls resultados | tail -5`

### Agente

Rápido status: perfil pronto (todos os atributos têm cauda longa à direita) e o filtro de extremos do Weka já rodou. Agora vou detalhar quais atributos disparam o alerta em cada máquina.

- `Bash`: `head -5 resultados/20261121_132701_299622_filtrar_anomalias_cpu_iqr_arff.txt; python3 ferramentas/weka_runner.py filtrar cpu.arff anomalias_cpu_iqr_por_atributo.arff weka.filters.unsupervised.attribute.InterquartileRange -R first-last -P 2>&1 | grep -v "Picked up"`
- `Bash`: `grep -v '^%' dados/cpu.with.vendor.arff | grep -i "@attribute" ; cat > resultados/anomalias_cpu/ler_iqr.py <<'EOF'
# Lê as saídas do filtro InterquartileRange do Weka e lista as máquinas marcadas.
def ler(caminho):
    L = open(caminho).read().splitlines()
    nomes = [l.split()[1] for l in L if l.l`
- `Bash`: `python3 - <<'EOF'
a=[l for l in open("dados/cpu.arff").read().split("@data")[1].splitlines() if l.strip() and not l.startswith("%")]
b=[l.split(",",1)[1] for l in open("dados/cpu.with.vendor.arff").read().split("@data")[1].splitlines() if l.strip() and not l.startswith("%")]
print("linhas iguais (cp`
- `Bash`: `python3 - <<'EOF'
a=[list(map(float,l.split(","))) for l in open("dados/cpu.arff").read().split("@data")[1].splitlines() if l.strip() and not l.startswith("%")]
b=[l.split(",") for l in open("dados/cpu.with.vendor.arff").read().split("@data")[1].splitlines() if l.strip() and not l.startswith("%")]
b`
- `Bash`: `head -3 resultados/20261121_132732_015762_filtrar_cpu_log_arff.txt; grep -v '^%' resultados/20261121_132732_015762_cpu_log.arff | sed -n '1,14p'`

### Agente

No `MathExpression`, a opção `-R` indica as colunas a **ignorar**, então pedi sem querer para ignorar todas. Vou rodar de novo sem ela.

- `Bash`: `rm resultados/20261121_132732_015762_cpu_log.arff resultados/20261121_132732_015762_filtrar_cpu_log_arff.txt && python3 ferramentas/weka_runner.py filtrar cpu.arff cpu_log.arff weka.filters.unsupervised.attribute.MathExpression -E "log(A+1)" 2>&1 | tail -1; f=$(ls -t resultados/*_cpu_log.arff | head`
- `Bash`: `cd /home/user/agente-mineracao/ferramentas && (python3 agrupamento.py cpu_log.arff --kmin 2 --kmax 8 --sementes 5 --embaralhamentos 20 2>&1 | grep -v "Picked up\|ARPACK\|BLAS\|LAPACK" > ../resultados/anomalias_cpu/agrup_log.log) & (python3 agrupamento.py cpu.arff --kmin 2 --kmax 8 --sementes 5 --emb`
- `Bash`: `R=/home/user/agente-mineracao/resultados/anomalias_cpu; for b in cpu_log cpu; do python3 ferramentas/agrupamento.py $b.arff --kmin 2 --kmax 8 --sementes 5 --embaralhamentos 20 2>&1 | grep -v "Picked up\|ARPACK\|BLAS\|LAPACK" > $R/agrup_$b.log; done; tail -5 $R/agrup_cpu_log.log; ls -t resultados | h`
- `Bash`: `cat resultados/20261121_133039_534507_cpu_log_agrupamento.txt | head -90; echo ======; grep -iE "^k|silhueta|embaralh|estab|final" resultados/20261121_133316_569434_cpu_agrupamento.txt | head -30`
- `Bash`: `sed -n '/^k | melhor/,/^$/p' resultados/20261121_133316_569434_cpu_agrupamento.txt; python3 ferramentas/weka_runner.py filtrar cpu_log.arff cpu_log_k3.arff weka.filters.unsupervised.attribute.AddCluster -W "weka.clusterers.SimpleKMeans -N 3 -S 1 -init 1" 2>&1 | tail -1`
- `Bash`: `cat > resultados/anomalias_cpu/pontuar.py <<'EOF'
# Pontuações de anomalia calculadas em PYTHON (o Weka padrão não tem essas pontuações).
# Os grupos vêm do Weka (AddCluster/SimpleKMeans sobre cpu_log.arff).
# Normalização: min-max 0-1 de cada atributo, igual à distância euclidiana padrão do Weka.
i`

### Agente

As pontuações estão prontas. Faltam duas conferências para explicar os candidatos: (1) se máquinas de memória alta sem cache são de fato raras e (2) quais máquinas têm zero canais.

- `Bash`: `cat > resultados/anomalias_cpu/conferencias.py <<'EOF'
# Conferências descritivas para explicar os candidatos (Python, só contagens).
L = open("dados/cpu.arff").read().split("@data")[1].splitlines()
D = [list(map(float, l.split(","))) for l in L if l.strip() and not l.startswith("%")]
alta = [i+1 fo`

### Agente

# Máquinas fora do padrão em `cpu.arff`

Seis máquinas se destacam com consistência. Todas ficaram entre as 15 mais atípicas nas quatro pontuações que calculei. O motivo principal de quase todas é uma **combinação** incomum de características, e não um valor extremo isolado. Isso não significa que haja erro em alguma delas: são candidatas a revisão.

## 1. Pergunta e definição
- **Anômalo em relação a quê:** à base toda e ao grupo de máquinas parecidas. Olhei a combinação dos 7 atributos, incluindo o desempenho (`class`).
- **Sem rótulos:** a base não diz quais máquinas são "anômalas", então o resultado é uma pontuação, não um veredito.
- **Identificação:** a base não tem identificador. Uso o número da linha e o fabricante, tirado de `cpu.with.vendor.arff`. Conferi que as 209 linhas coincidem nos 6 atributos de configuração.

## 2. Preparação
- **Qualidade:** não há valores ausentes explícitos, linhas duplicadas, nem casos com mínimo maior que máximo.
- **Distribuições:** os 7 atributos têm cauda longa à direita. A média fica bem acima da mediana; por exemplo, `class` tem média 105,6 e mediana 50.
- **Escala:** apliquei logaritmo no Weka com `MathExpression -E "log(A+1)"`. A base nova está em `dados/cpu_log.arff` e a original ficou intacta.
  - Motivo: memória e canais crescem em potências de 2. Na escala original, as poucas máquinas gigantes dominam as distâncias.
  - Os dados confirmam: na escala original os grupos do K-means ficaram instáveis (ARI 0,53 com k=2). Em log, a estabilidade foi de 0,97.
- **Possíveis ausentes disfarçados (decisão sua):** 5 máquinas têm `CHMIN = CHMAX = 0`, ou seja, nenhum canal de E/S. São as linhas 123, 124, 125, 208 e 209. Não sei se "0" significa "zero canais" ou "não informado". Não alterei esses valores.

## 3. Técnicas e o que rodou onde
| Técnica | Onde rodou | Parâmetros |
|---|---|---|
| Extremos por atributo (IQR) | **Weka**: `InterquartileRange -R first-last` (com e sem `-P`) | padrão: outlier `-O 3`, extremo `-E 6` |
| Agrupamento K-means | **Weka**: `SimpleKMeans -init 1`, `AddCluster` | k=2 (semente 1) e k=3 (semente 1) |
| Distância relativa ao centro do grupo | **Python**, sobre os grupos do Weka | distância ao centro ÷ mediana do grupo |
| Distância ao k-ésimo vizinho | **Python** (o Weka padrão não tem) | k=5 e k=10 |

**Validação dos grupos (Weka + `agrupamento.py`):**
- Com k=2: silhueta 0,38 (estrutura moderada), estabilidade (ARI) 0,97, SSE real 35,3. Nas 20 versões com dados embaralhados, o SSE ficou entre 51,3 e 52,1, então os grupos não são acaso.
- Com k=3: silhueta 0,31 e ARI 0,90.

**Resultado do IQR sozinho:** marcou 36 máquinas (17% da base). Quase todas são a cauda natural da distribuição, como as máquinas antigas com ciclo de 800 a 1500 ns e os grandes computadores. Por isso, o IQR serve aqui só como apoio à explicação.

## 4. Candidatos a revisão
Como ler a tabela:
- **Dist. rel. k2 / k3:** 1,0 é uma máquina típica do seu grupo; 2,4 está 2,4 vezes mais longe do centro que a máquina mediana do grupo.
- **(nº):** posição no ranking, de 1 a 209.
- **Valores:** MYCT, MMIN, MMAX, CACH, CHMIN, CHMAX, class.

**Robustas (top 15 nas 4 pontuações):**

| Linha | Fabr. | Valores | Dist. rel. k2 | Dist. rel. k3 | kNN-5 | kNN-10 | O que a torna diferente |
|---|---|---|---|---|---|---|---|
| 1 | adviser | 125, 256, 6000, **256**, 16, **128**, 198 | 1,94 (3) | 2,42 (2) | 0,59 (2) | 0,70 (1) | Cache igual ao máximo da base e 128 canais, mas memória mínima de só 256. Também marcada pelo IQR. |
| 98 | ibm | 26, 8000, 32000, **0**, 8, 24, 277 | 1,81 (4) | 2,49 (1) | 0,59 (3) | 0,63 (3) | Máquina rápida e de memória alta **sem cache**. Das 27 máquinas com MMAX ≥ 32000, é a única sem cache. **O IQR não a detectou**: nenhum valor dela é extremo sozinho. |
| 15 | bti | 350, **64, 64**, 0, 1, 4, 10 | 1,97 (2) | 2,07 (7) | 0,64 (1) | 0,66 (2) | Memória mínima e máxima de 64, o menor valor da base (mediana do MMAX: 8000). Pode ser uma máquina muito pequena ou erro de digitação (64 em vez de 64000?). |
| 99 | ibm | 26, 8000, 16000, **0**, 8, 16, 185 | 1,77 (6) | 2,42 (3) | 0,52 (4) | 0,56 (4) | Mesmo padrão da 98: ciclo rápido sem cache. Só as linhas 98 e 99 têm MYCT ≤ 30 e cache zero (25 máquinas têm MYCT ≤ 30). |
| 208 | wang | 480, 512, 8000, 32, **0, 0**, 67 | 1,73 (10) | 2,39 (4) | 0,50 (6) | 0,53 (5) | Zero canais de E/S, mas com cache de 32. Pode ser um ausente disfarçado (ver seção 2). |
| 200 | sperry | 30, 8000, 64000, 128, 12, **176**, **1150** | 1,80 (5) | 1,80 (11) | 0,42 (12) | 0,46 (12) | Maior desempenho e maior número máximo de canais da base. Provavelmente um topo de linha, ou seja, variação natural extrema. |

**Frequentes (top 15 em 3 das 4 pontuações):**
- **Linha 10 (amdahl):** maior memória mínima (32000) e desempenho 1144. Provavelmente outro topo de linha.
- **Linhas 197 e 198 (sperry):** CHMIN = 52, o máximo da base. É quase o dobro do segundo maior valor (32, da linha 10).
- **Linha 83 (honeywell):** 112 canais numa máquina modesta (desempenho 38).
- **Linha 100 (ibm):** memória máxima de 512 e o menor desempenho da base (6).

As pontuações completas das 26 máquinas que aparecem em algum top 15 estão em `resultados/anomalias_cpu/pontuacoes.txt`.

## 5. Leitura
Para cada candidata há três explicações possíveis, e os números não dizem qual é a certa:
1. **Outro tipo de máquina:** as linhas 98 e 99 podem ter uma arquitetura diferente, por exemplo memória rápida que dispensa cache.
2. **Variação natural extrema:** é o mais provável para as linhas 10, 200 e 197/198, que são grandes computadores.
3. **Erro de registro:** é o que mais vale checar na linha 15 (64/64) e nas máquinas com zero canais.

**Mascaramento:** casos parecidos entre si se escondem uns aos outros.
- As linhas 123, 124 e 125 (IBM, sem canais) formam um trio e por isso pontuam pouco. Se os zeros forem erro, as três merecem a mesma revisão que a linha 208.
- Os pares 98/99, 197/198 e 199/200 também se "protegem" na pontuação com k=5. Mesmo assim continuaram altos com k=10.

## 6. Próximos passos e o que não foi feito
- **Sua revisão:** confira as 6 linhas robustas (principalmente 15, 98/99 e as de zero canais) e diga quais são erro, quais são legítimas e quais são de outro tipo. Essa revisão é a melhor evidência possível.
- **Pergunta para você:** canal = 0 significa "sem canal" ou "não informado"? Se for "não informado", trato esses valores como ausentes e recalculo.
- **Não rodei LOF nem DBSCAN.** Eles exigem pacotes adicionais do Weka e eu não instalei nada. Se você autorizar a instalação, posso rodar e verificar se esses métodos concordam com a lista.
- **Não testei** a versão sem o atributo `class`, que olharia só a configuração. Se o interesse for "configurações estranhas", posso rodar essa variante.

Scripts e saídas desta análise estão em `resultados/anomalias_cpu/`. As saídas do Weka estão em `resultados/` com data e hora no nome.

