# Reanálise de diabetes.arff — 31/10/2026

## Objetivo e dados

O objetivo é prever `tested_positive` (caso positivo para diabetes) versus `tested_negative`. A base `../dados/diabetes.arff` tem 768 registros, 8 atributos numéricos e 2 classes: 268 positivos (34,9%) e 500 negativos (65,1%).

Usei o custo definido pelo usuário: deixar passar um caso positivo (falso negativo) custa cinco vezes mais que um alarme falso (falso positivo). Na ordem de classes do ARFF (`tested_negative`, `tested_positive`), a matriz é:

```text
             previsto negativo   previsto positivo
real negativo          0                 1
real positivo          5                 0
```

Portanto, a métrica principal é o custo total, calculado como `FP + 5 × FN`.

## Exploração e qualidade

O resumo do Weka encontrou 768 registros, 9 atributos e nenhum ausente explícito. Uma contagem direta do ARFF também não encontrou linhas duplicadas idênticas.

Zeros encontrados em atributos nos quais podem indicar ausência de medição: `plas` 5, `pres` 35, `skin` 227, `insu` 374 e `mass` 11. `preg=0` (111 registros) pode significar nenhuma gestação. Como o usuário não confirmou a semântica dos demais zeros, **não alterei nem tratei a base**; os modelos consideram esses zeros como valores observados. Esse é um limite importante dos resultados.

O perfil numérico completo (mínimo, quartis, mediana, máximo, média, zeros e ausentes) está em [perfil da base](../resultados/20261031_195704_860400_perfil_diabetes.txt). O resumo produzido pelo Weka está em [saída do resumo](../resultados/20261031_195517_401496_resumo.txt).

Este foi o código Python usado para calcular o perfil; ele apenas lê o ARFF e não modifica a base:

```python
from collections import Counter
from math import ceil, floor
from pathlib import Path
from statistics import mean, median

linhas = Path(r"dados\diabetes.arff").read_text(encoding="utf-8-sig").splitlines()
atributos = [
    linha.split()[1].strip("'")
    for linha in linhas
    if linha.strip().lower().startswith("@attribute")
]
inicio = next(i for i, linha in enumerate(linhas) if linha.strip().lower() == "@data")
registros = [
    [valor.strip() for valor in linha.split(",")]
    for linha in linhas[inicio + 1:]
    if linha.strip() and not linha.lstrip().startswith("%")
]

def quartil(valores, proporcao):
    ordenados = sorted(valores)
    posicao = (len(ordenados) - 1) * proporcao
    inferior, superior = floor(posicao), ceil(posicao)
    return ordenados[inferior] + (
        ordenados[superior] - ordenados[inferior]
    ) * (posicao - inferior)

print("Classes:", Counter(registro[-1] for registro in registros))
print("Ausentes:", sum(valor == "?" for registro in registros for valor in registro))
print("Duplicatas excedentes:", len(registros) - len({tuple(r) for r in registros}))
for indice, nome in enumerate(atributos[:-1]):
    valores = [float(registro[indice]) for registro in registros if registro[indice] != "?"]
    q1, q3 = quartil(valores, 0.25), quartil(valores, 0.75)
    print(
        nome, min(valores), q1, median(valores), q3, q3 - q1,
        max(valores), mean(valores), sum(valor == 0 for valor in valores)
    )
```

## Método

Todos os modelos foram avaliados por validação cruzada estratificada de 10 partes, semente 1. A matriz de custo foi aplicada durante o treinamento com `weka.classifiers.meta.CostSensitiveClassifier`. Foram comparadas seis configurações: J48, NaiveBayes padrão, NaiveBayes `-K` (estimativa por núcleo), IBk (`-K 15 -X`), SMO (`-M`) e RandomForest. `-K` foi incluído no NaiveBayes devido à assimetria de alguns atributos; `-M` no SMO permite interpretar a AUC.

As linhas de ZeroR e do classificador que prevê sempre positivo são as duas referências de custo:

- ZeroR prevê sempre negativo: `5 × 268 = 1.340`.
- Sempre positivo: `1 × 500 = 500`; esta é a referência de menor custo.

Os intervalos de acurácia são aproximações de Wilson a 95%, calculadas a partir das previsões da validação cruzada. As métricas da tabela são apenas do bloco de validação cruzada do Weka. Em cada matriz, linhas são classes reais e colunas são classes previstas.

## Resultados

| Modelo | Acurácia (IC 95%) | Kappa | Recall positivo | Precisão positiva | F1 positivo | AUC | Custo total |
|---|---:|---:|---:|---:|---:|---:|---:|
| ZeroR (sempre negativo) | 65,10% (61,67–68,39%) | 0,0000 | 0,000 | — | — | 0,497 | 1.340 |
| Sempre positivo (referência) | 34,90% (31,61–38,33%) | 0,0000 | 1,000 | 0,349 | 0,517 | — | **500** |
| J48 | 62,24% (58,76–65,60%) | 0,2978 | 0,854 | 0,477 | 0,612 | 0,753 | 446 |
| NaiveBayes | 70,31% (66,99–73,44%) | 0,4173 | 0,836 | 0,549 | 0,663 | 0,819 | 404 |
| NaiveBayes `-K` | 64,45% (61,00–67,76%) | 0,3480 | 0,922 | 0,495 | 0,644 | 0,827 | 357 |
| IBk `-K 15 -X` | 69,92% (66,59–73,06%) | 0,3363 | 0,563 | 0,570 | 0,567 | 0,697 | **699** |
| SMO `-M` | 65,76% (62,33–69,03%) | 0,3683 | 0,925 | 0,505 | 0,653 | 0,827 | **343** |
| RandomForest | 72,40% (69,13–75,44%) | 0,4479 | 0,821 | 0,573 | 0,675 | 0,818 | 404 |

NaiveBayes sem `-K` e RandomForest tiveram o mesmo custo total nesta validação; não interprete a maior acurácia da floresta como vantagem para o objetivo de custo.

### Matrizes de confusão (validação cruzada)

| Modelo | Real negativo: previsto neg./pos. | Real positivo: previsto neg./pos. | FP | FN |
|---|---:|---:|---:|---:|
| ZeroR | 500 / 0 | 268 / 0 | 0 | 268 |
| Sempre positivo | 0 / 500 | 0 / 268 | 500 | 0 |
| J48 | 249 / 251 | 39 / 229 | 251 | 39 |
| NaiveBayes | 316 / 184 | 44 / 224 | 184 | 44 |
| NaiveBayes `-K` | 248 / 252 | 21 / 247 | 252 | 21 |
| IBk `-K 15 -X` | 386 / 114 | 117 / 151 | 114 | 117 |
| SMO `-M` | 257 / 243 | 20 / 248 | 243 | 20 |
| RandomForest | 336 / 164 | 48 / 220 | 164 | 48 |

O IBk custa 699, acima da referência de menor custo (500); portanto, neste cenário, é pior que não usar modelo. Os demais custos desta validação são inferiores a 500.

## Significância e recomendação

O teste t pareado corrigido, em 10 repetições de validação cruzada de 10 partes, indicou:

- SMO `-M` contra a referência sensível a custo baseada em ZeroR (que prevê sempre positivo): custo médio de 35,12 contra 50 por parte; diferença significativa a 5% (`p < 0,000001`).
- SMO `-M` contra NaiveBayes `-K`: custo médio de 35,12 contra 35,47 por parte; **empate técnico** (`p = 0,895861`).

Assim, há evidência de que um modelo pode reduzir o custo em relação à melhor previsão constante, mas não há evidência de que SMO supere NaiveBayes `-K`. Se for necessário escolher um ponto de partida, NaiveBayes `-K` é uma opção mais simples; mantenha SMO como alternativa. Isso não é uma conclusão clínica e precisa de validação externa antes de qualquer uso real.

## Limitações e próximos passos

- Os zeros suspeitos permaneceram como valores numéricos reais. Com a autorização e definição do domínio, o próximo passo é criar uma cópia ARFF com os zeros confirmados como ausentes e comparar as duas versões.
- A base é histórica e contém mulheres de pelo menos 21 anos da população Pima, conforme o cabeçalho do próprio arquivo. Os resultados não se generalizam automaticamente a outras populações.
- A validação cruzada estima desempenho; não identifica pacientes novos. Não foram fornecidos registros sem rótulo para previsão individual.
- O modelo não deve ser usado para diagnóstico ou decisão clínica sem validação externa, revisão profissional e avaliação apropriada.

## Reprodutibilidade

Comandos de comparação executados (cada arquivo de saída também registra o comando completo):

```powershell
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\weka_runner.py' resumo 'diabetes.arff'
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\weka_runner.py' comparar 'diabetes.arff' 'weka.classifiers.meta.CostSensitiveClassifier' -cost-matrix '[0 1; 5 0]' -W 'weka.classifiers.trees.J48' --
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\weka_runner.py' comparar 'diabetes.arff' 'weka.classifiers.meta.CostSensitiveClassifier' -cost-matrix '[0 1; 5 0]' -W 'weka.classifiers.bayes.NaiveBayes' --
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\weka_runner.py' comparar 'diabetes.arff' 'weka.classifiers.meta.CostSensitiveClassifier' -cost-matrix '[0 1; 5 0]' -W 'weka.classifiers.bayes.NaiveBayes' -- -K
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\weka_runner.py' comparar 'diabetes.arff' 'weka.classifiers.meta.CostSensitiveClassifier' -cost-matrix '[0 1; 5 0]' -W 'weka.classifiers.lazy.IBk' -- -K 15 -X
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\weka_runner.py' comparar 'diabetes.arff' 'weka.classifiers.meta.CostSensitiveClassifier' -cost-matrix '[0 1; 5 0]' -W 'weka.classifiers.functions.SMO' -- -M
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\weka_runner.py' comparar 'diabetes.arff' 'weka.classifiers.meta.CostSensitiveClassifier' -cost-matrix '[0 1; 5 0]' -W 'weka.classifiers.trees.RandomForest' --
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\significancia.py' 'diabetes.arff' --a 'weka.classifiers.functions.SMO' --opcoes-a=-M --b 'weka.classifiers.rules.ZeroR' --custo '0 1; 5 0' --positiva 'tested_positive' --repeticoes 10
& 'C:\Users\Mateus\anaconda3\python.exe' 'ferramentas\significancia.py' 'diabetes.arff' --a 'weka.classifiers.functions.SMO' --opcoes-a=-M --b 'weka.classifiers.bayes.NaiveBayes' --opcoes-b=-K --custo '0 1; 5 0' --positiva 'tested_positive' --repeticoes 10
```

Saídas da validação estão nos arquivos `20261031_195927_*` em `../resultados/`. Os testes de significância estão em [SMO contra a referência](../resultados/20261031_200210_314097_significancia.txt) e [SMO contra NaiveBayes-K](../resultados/20261031_200217_139979_significancia.txt). O cálculo dos intervalos está em [intervalos de acurácia](../resultados/20261031_200239_106902_intervalos_diabetes.txt).
