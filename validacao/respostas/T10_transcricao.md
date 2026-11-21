# Transcrição T10

### Usuário

Analise a base soybean.arff.


### Agente

Vou começar lendo o manual de decisões e localizando a base.

- `Bash`: `ls; ls dados ferramentas resultados 2>/dev/null | head -80; wc -l conhecimento/manual_decisoes.md; find / -name "soybean.arff" 2>/dev/null | head`
- `Read`: `/home/user/agente-mineracao/conhecimento/manual_decisoes.md`

### Agente

A base tem atributo de classe, então começo pela exploração. Vou rodar o resumo do Weka.

- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/soybean.arff 2>&1 | tail -80; ls -t resultados | head -3`
- `Bash`: `python3 ferramentas/weka_runner.py resumo soybean.arff 2>&1 | tail -90`

### Agente

Agora o perfil detalhado em Python (distribuição da classe, ausentes por classe, duplicatas, atributos quase constantes), salvo em `resultados/`.

- `Bash`: `mkdir -p analises && cat > analises/perfil_soybean.py <<'EOF'
# Perfil descritivo da base soybean.arff (só descreve os dados; nenhum modelo aqui).
from scipy.io import arff
import pandas as pd
from datetime import datetime
import io, contextlib

dados, meta = arff.loadarff("dados/soybean.arff")
df =`

### Agente

O leitor do scipy tropeçou num espaço no cabeçalho do `.arff`. Troco por uma leitura simples das linhas de dados.

- `Bash`: `python3 - <<'EOF'
import re
p="analises/perfil_soybean.py"
s=open(p).read()
s=s.replace('''from scipy.io import arff
''','').replace('''dados, meta = arff.loadarff("dados/soybean.arff")
df = pd.DataFrame(dados)
# O scipy lê nominais como bytes; convertemos para texto e '?' vira ausente (None)
for c `
- `Bash`: `sed -i 's/x = df.drop(columns="class").astype(str)/x = df.drop(columns="class").fillna("?").astype(str)/; s/df.astype(str)/df.fillna("?").astype(str)/g' analises/perfil_soybean.py && python3 analises/perfil_soybean.py`
- `Bash`: `python3 - <<'EOF'
exec(open("analises/perfil_soybean.py").read().split("saida = io.StringIO()")[0])
x = df.drop(columns="class").fillna("?").astype(str).apply("|".join, axis=1)
g = df.groupby(x)["class"].agg(lambda s: dict(s.value_counts()))
print(g[g.apply(len) > 1].tolist())
# quantos ausentes por`

### Agente

Fiz o enquadramento e a exploração. **Parei antes de modelar**, porque as classes são desbalanceadas e há duas decisões que dependem de você.

## 1. Enquadramento
- 683 registros e 35 atributos de sintomas e condições da planta e da lavoura. Todos os atributos são nominais, então não há números para normalizar nem zeros que possam esconder valores ausentes.
- O alvo `class` tem **19 doenças da soja**. É uma tarefa de **classificação multiclasse** com alvo nominal, sem ordem entre as classes.

## 2. O que a exploração mostrou
Comandos: `python3 ferramentas/weka_runner.py resumo soybean.arff` e `python3 analises/perfil_soybean.py`. A saída está em `resultados/20261121_133239_soybean_perfil.txt`.

| Verificação | Achado | Consequência |
|---|---|---|
| **Distribuição da classe** | De 92 casos (brown-spot) a 8 (herbicide-injury), uma razão de 11,5 para 1. Quatro classes têm cerca de 13% cada; 13 classes têm entre 8 e 20 casos. | A acurácia vai refletir sobretudo as 4 classes grandes. As pequenas precisam ser olhadas uma a uma. Com 8 casos, cada parte da validação cruzada testa menos de 1 caso de herbicide-injury, então a estimativa dessa classe é instável. |
| **Ausentes** | 121 registros (18%) têm algum ausente, e eles estão **todos em 5 classes**. Em 2-4-d-injury, cyst-nematode, herbicide-injury e diaporthe-pod-&-stem-blight, **100% dos registros** têm ausentes (de 11 a 30 atributos vazios por registro). Em phytophthora-rot, são 68 de 88. | **A própria ausência identifica a doença.** O modelo pode acertar essas classes por "faltar dado", e não pelos sintomas. Isso só é legítimo se, na prática, os casos novos forem registrados do mesmo jeito. |
| **Duplicatas** | 93 registros estão envolvidos em duplicatas exatas, com 52 cópias excedentes (17 delas em phytophthora-rot e 15 em brown-spot). Um par tem sintomas idênticos e classes diferentes (alternarialeaf-spot × frog-eye-leaf-spot). | Com atributos tão grosseiros, plantas diferentes podem coincidir de verdade. Mas, se forem a mesma planta registrada duas vezes, a validação fica otimista. O par conflitante mostra que essas duas doenças nem sempre se distinguem pelos atributos disponíveis. |
| **Quase constantes** | `mycelium` é "absent" em 99,1% dos casos (só 6 "present"); `sclerotia` é "absent" em 96,9%. | Ajudam pouco no geral, mas podem marcar uma doença específica. Mantenho os dois e deixo as árvores decidirem. |
| **Identificadores** | Não há. | Nada a remover. |

## 3. Perguntas antes de modelar
1. **Objetivo: entender ou prever?** Para entender quais sintomas distinguem cada doença, o foco são J48 e JRip, com RandomForest só como referência do melhor desempenho possível. Para diagnosticar casos novos, entram NaiveBayes, IBk, SMO e RandomForest como candidatos de pleno direito.
2. **Alguma doença é prioritária, ou algum erro custa mais?** Uma matriz de custo 19 × 19 não é viável de montar com você. A pergunta prática é se há doenças cuja falha de diagnóstico é grave, por exemplo as que se espalham ou as que exigem ação imediata.
   - **Se não houver prioridade, eu proponho** como métrica principal o **F1 médio por classe (macro)**, em que cada doença pesa igual. A acurácia, que favorece as 4 classes grandes, e o kappa ficam como métricas descritivas. O `significancia.py` foi feito para F1 de uma classe positiva, então preciso confirmar se ele calcula a média por classe. Se não calcular, uso a acurácia como métrica do teste e declaro essa limitação.
3. **Ausentes:** você sabe se, na prática, esses campos também ficariam vazios nos casos novos dessas doenças? Se não souber, faço uma **análise de sensibilidade**: a base original como análise principal e, como cenário alternativo, uma versão com um indicador de "registro incompleto", para ver quanto do acerto vem da ausência e não dos sintomas.
4. **Duplicatas:** é a mesma planta registrada duas vezes, ou plantas diferentes com sintomas iguais? Se você não souber, também rodo os dois cenários, com e sem duplicatas.

## O que ainda não foi feito
Nenhum modelo rodou, nem o ZeroR, então ainda não há métricas de desempenho. Com as suas respostas, rodo o ZeroR e os candidatos em validação cruzada estratificada de 10 partes com semente 1, e depois os testes de significância.

Se quiser que eu siga sem responder, eu adoto: objetivo **entender**, nenhuma doença prioritária, F1 macro como métrica principal, e as duas análises de sensibilidade (ausentes e duplicatas). Essas suposições ficam declaradas no início do relatório.


### Usuário

Quero prever a doença a partir dos sintomas. Nas outras perguntas, siga as suas recomendações.

- `Bash`: `wc -l ferramentas/*.py && grep -n "argparse\|add_argument\|def \|f1\|F1\|metric\|metrica" ferramentas/significancia.py | head -80`
- `Read`: `/home/user/agente-mineracao/ferramentas/significancia.py`
- `Read`: `/home/user/agente-mineracao/ferramentas/significancia.py`

### Agente

`significancia.py` só calcula F1 para uma classe positiva, sem média por classe. Antes de decidir como contornar isso, vou ver como o `weka_runner.py` grava as saídas.

- `Bash`: `sed -n 1,60p ferramentas/weka_runner.py && grep -n "def \|-x\|-s\|ZeroR\|-c" ferramentas/weka_runner.py | head -40`
- `Bash`: `mkdir -p /tmp/claude-0/sb && for c in "weka.classifiers.trees.J48 -C 0.25 -M 2" "weka.classifiers.bayes.NaiveBayes" "weka.classifiers.lazy.IBk -K 15 -X" "weka.classifiers.functions.SMO" "weka.classifiers.trees.RandomForest"; do python3 ferramentas/weka_runner.py comparar soybean.arff $c > /tmp/claud`
- `Bash`: `cat > analises/tabela_soybean.py <<'EOF'
# Lê as saídas do Weka (só o bloco de validação cruzada) e monta a tabela comparativa.
# Nada é inventado: acurácia, kappa e matriz vêm do Weka; F1 macro e IC são contas sobre esses números.
import sys, re, math, glob
from datetime import datetime

def ler(ar`
- `Edit`: `/home/user/agente-mineracao/ferramentas/significancia.py`
- `Bash`: `python3 - <<'EOF'
p="ferramentas/significancia.py"; s=open(p).read()
rep=[("def _calcular_metricas(classes, matriz, positiva, custo):","def _calcular_metricas(classes, matriz, positiva, custo, f1_macro=False):"),
("    sem_envelope=False,\n):","    sem_envelope=False,\n    f1_macro=False,\n):"),
("c`

### Agente

Rodo as duas comparações previstas: o melhor (SMO) contra o ZeroR e o melhor contra o segundo (NaiveBayes), cada uma com 10 × 10 validações cruzadas.

- `Bash`: `cd /home/user/agente-mineracao/ferramentas && (python3 significancia.py soybean.arff --a weka.classifiers.functions.SMO --b weka.classifiers.rules.ZeroR --f1-macro --repeticoes 10 > /tmp/claude-0/sb/sig_zeror.log 2>&1 &) ; python3 significancia.py soybean.arff --a weka.classifiers.functions.SMO --b `
- `Bash`: `cd /home/user/agente-mineracao && python3 ferramentas/weka_runner.py filtrar soybean.arff soybean_sem_dup.arff weka.filters.unsupervised.instance.RemoveDuplicates 2>&1 | grep -v JAVA_ | tail -5; grep -c "^[^@%]" dados/soybean_sem_dup.arff; grep -vc "^\s*$\|^@\|^%" dados/soybean_sem_dup.arff`
- `Bash`: `cd /home/user/agente-mineracao && cp resultados/20261121_134354_672159_soybean_sem_dup.arff dados/soybean_sem_dup.arff && awk 'f&&NF&&!/^%/{n++} /^@data/{f=1} END{print n" registros"}' dados/soybean_sem_dup.arff
cat > analises/indicador_incompleto_soybean.py <<'EOF'
# Gera dados/soybean_indicador.ar`

### Agente

O Weka removeu 52 registros (683 → 631), o que bate com a contagem da exploração. Agora rodo SMO e NaiveBayes nos dois cenários.

- `Bash`: `for b in soybean_sem_dup.arff soybean_indicador.arff; do for c in weka.classifiers.functions.SMO weka.classifiers.bayes.NaiveBayes; do python3 ferramentas/weka_runner.py comparar $b $c > /tmp/claude-0/sb/cen_${b%.arff}_${c##*.}.log 2>&1; ls -t resultados/*_classificador.txt | head -1 >> /tmp/claude-`

### Agente

A linha do ZeroR saiu do arquivo errado: foi a do último cenário nas duas tabelas. Corrijo usando o ZeroR que rodou na própria base sem duplicatas.

- `Bash`: `z=$(grep -l "soybean_sem_dup" resultados/*_baseline_ZeroR.txt | head -1); echo $z; python3 analises/tabela_soybean.py $z $(cat /tmp/claude-0/sb/arquivos_soybean_sem_dup.arff.txt) | head -4; cat /tmp/claude-0/sb/arquivos_*`

### Agente

Agora vejo onde os dois modelos empatados erram: a matriz de confusão da validação cruzada.

- `Bash`: `for f in $(grep -l "NaiveBayes -t .*soybean.arff\|SMO -t .*soybean.arff" resultados/20261121_133353_*_classificador.txt); do head -1 $f; python3 - "$f" <<'EOF'
import sys,re
t=open(sys.argv[1]).read(); cv=t[t.index("=== Stratified cross-validation ==="):]
b=cv.split("=== Confusion Matrix ===")[1]
ro`

### Agente

Concluí a análise. O SMO e o NaiveBayes ficaram estatisticamente empatados, e eu recomendo o **NaiveBayes**, que é o mais simples dos dois. O resultado se manteve nos dois cenários alternativos (sem duplicatas e com um indicador de registro incompleto).

**Premissas que você confirmou:** o objetivo é **prever** a doença; nenhuma doença tem prioridade, então todas as 19 pesam igual; a métrica principal é o **F1 macro**, definido antes de ver qualquer resultado; ausentes e duplicatas foram tratados como análises de sensibilidade.

## 1. O que foi feito
- **Pré-processamento:** nenhum na análise principal. Os atributos são todos nominais e não há identificadores. Cada algoritmo lida com os ausentes do seu jeito: o NaiveBayes ignora o atributo ausente naquele registro, e o SMO o substitui pela moda.
- **Candidatos:** J48, NaiveBayes, IBk (com `-K 15 -X`, que escolheu k = 2 por validação interna), SMO e RandomForest, todos com os parâmetros padrão, além do ZeroR.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1. Comando base: `python3 ferramentas/weka_runner.py comparar soybean.arff <classificador> [opções]`.
- **Mudança no projeto:** acrescentei a opção `--f1-macro` em `ferramentas/significancia.py`. É opcional e não muda o comportamento padrão. Por enquanto a mudança não está commitada.

## 2–3. Resultado do Weka (só o bloco de validação cruzada) e comparação com o ZeroR

| Modelo | Acurácia | IC 95% | Kappa | **F1 macro** |
|---|---:|---|---:|---:|
| ZeroR | 0,135 | [0,111; 0,162] | 0,000 | 0,013 |
| **SMO** | 0,939 | [0,918; 0,954] | 0,933 | **0,960** |
| **NaiveBayes** | 0,930 | [0,908; 0,947] | 0,923 | **0,956** |
| RandomForest | 0,930 | [0,908; 0,947] | 0,923 | 0,947 |
| IBk (k = 2) | 0,911 | [0,887; 0,930] | 0,902 | 0,926 |
| J48 | 0,915 | [0,892; 0,934] | 0,907 | 0,919 |

O F1 macro é uma conta sobre as matrizes de confusão do Weka, e o intervalo é o de Wilson. A tabela completa, com o F1 de cada classe, está em `resultados/20261121_134434_soybean_tabela.txt`.

## 4. Confiabilidade
Usei o teste t pareado corrigido, com 10 × 10 validações cruzadas, no F1 macro. Fiz só as duas comparações previstas:
- **SMO × ZeroR:** 0,953 contra 0,013, p < 0,001. **Há um modelo útil.**
- **SMO × NaiveBayes:** 0,953 contra 0,951, p = 0,79. **Empate técnico.**

Como estão empatados, fico com o **NaiveBayes**: é mais simples e mais rápido, e a diferença entre o acerto no treino e na validação é bem menor (93,7% contra 93,0%, enquanto o SMO vai de 97,8% para 93,9%). Seis configurações foram testadas no total, então os números do primeiro colocado tendem a ser um pouco otimistas.

**Análises de sensibilidade:** nenhuma das duas mudou a conclusão.

| Cenário | SMO (F1 macro) | NaiveBayes (F1 macro) |
|---|---:|---:|
| Original | 0,960 | 0,956 |
| Sem duplicatas (631 registros) | 0,955 | 0,950 |
| Com indicador de registro incompleto | 0,960 | 0,957 |

- **Duplicatas:** retirá-las baixa o desempenho só meio ponto. Elas não estavam inflando a avaliação de forma relevante.
- **Ausentes:** dar ao modelo a informação explícita de que "faltou dado" não acrescenta quase nada. Os modelos não estão acertando por causa do padrão de preenchimento.
- **Comparabilidade:** a base sem duplicatas tem outro conjunto de teste, então esses números são descritivos e não foram testados contra a análise principal.

## 5. Interpretação: onde o modelo erra
O NaiveBayes errou 48 dos 683 casos, e quase todos os erros acontecem **dentro de duas famílias de doenças com sintomas parecidos**:
- **Manchas foliares**, que concentram 44 dos 48 erros:
  - frog-eye-leaf-spot classificado como alternarialeaf-spot: 22 casos. A exploração já tinha mostrado um par de registros com sintomas idênticos e um rótulo de cada uma dessas doenças.
  - brown-spot e phyllosticta-leaf-spot confundidas entre si e com as outras manchas: 22 casos.
  - Por isso essas são as classes com o pior F1: phyllosticta 0,81, frog-eye 0,81, alternaria 0,86 e brown-spot 0,89.
- **Doenças bacterianas:** bacterial-pustule classificada como bacterial-blight, 2 casos.
- **Classes reconhecidas sem erro (F1 = 1,00):** 12 doenças. Entre elas estão herbicide-injury, apesar de ter só 8 casos, e cyst-nematode.

O SMO tem o mesmo padrão de erros.

## 6. Alertas e próximos passos
- **Uso prático:** o modelo resolve bem 15 das 19 doenças. Para as quatro manchas foliares, os atributos disponíveis não bastam para distingui-las com segurança. Nesses casos, faz sentido tratar a previsão como "grupo de mancha foliar" e confirmar o diagnóstico por outro meio. A decisão de adotar isso é de domínio e cabe a você.
- **Classes pequenas:** com 8 a 20 casos, o F1 dessas classes é instável. O J48, por exemplo, teve F1 de só 0,55 em herbicide-injury.
- **Ausentes:** o resultado só vale se os casos novos forem registrados como nesta base.
- **Limitação dos dados:** o pior desempenho do IBk pode vir de atributos irrelevantes pesando na distância. Não testei seleção de atributos, porque o IBk ficou longe dos primeiros colocados.
- **O que não foi feito:**
  - AUC: não relatei, porque o SMO rodou sem `-M` e a AUC não é a métrica principal.
  - NaiveBayes com `-K` ou `-D`: não se aplica, porque não há atributos numéricos.
  - MultilayerPerceptron: não rodei.
  - Ajuste de parâmetros: não fiz.
  - Comparações par a par além das duas descritas: não fiz.

Os scripts estão em `analises/`, as bases novas em `dados/` (`soybean_sem_dup.arff` e `soybean_indicador.arff`) e todas as saídas do Weka em `resultados/`.

