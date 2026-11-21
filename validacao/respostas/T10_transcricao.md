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

