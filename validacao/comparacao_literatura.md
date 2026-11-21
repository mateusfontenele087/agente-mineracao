# Comparação com resultados publicados

## A referência

Holte, R. C. (1993). *Very Simple Classification Rules Perform Well on Most Commonly Used Datasets*.
**Machine Learning**, 11, 63–91. DOI: [10.1023/A:1022631118932](https://doi.org/10.1023/A:1022631118932).

Holte comparou uma árvore de decisão podada (**C4**, antecessor do C4.5, que no Weka é o **J48**)
com a melhor regra de um único atributo (**1R**, que no Weka é o **OneR**) em 16 bases do repositório
UCI. Os valores abaixo foram lidos no artigo: Tabela 2 (p. 65) para a linha de base e Tabela 3 (p. 66)
para as acurácias.

**O protocolo é diferente do nosso.** Holte fez 25 divisões aleatórias, com 2/3 para treino e 1/3 para
teste, e tirou a média. Nós usamos validação cruzada estratificada de 10 partes com semente 1. Por isso
os números **não precisam ser iguais**. O que se compara é (a) a linha de base, que depende só da
base, e (b) as **conclusões**: a ordem dos modelos e se eles superam a linha de base.

## Bases comparáveis

Três bases do artigo são as mesmas versões que o agente analisou. Duas não são comparáveis: o "HY" de
Holte tem 3.163 casos e 2 classes, e a nossa hypothyroid tem 3.772 casos e 4 classes. O "SO" é a
soybean pequena, com 47 casos, e a nossa tem 683. A glass entra só como referência, porque o agente
não fez classificação nela (fez agrupamento, na T06).

| Base | Linha de base (Holte) | Linha de base (ZeroR, nosso) | C4 (Holte) | J48 (nosso) | 1R (Holte) | OneR (nosso) |
|---|---:|---:|---:|---:|---:|---:|
| vote | 61,4 | 61,4 | 95,6 | 96,3 | 95,2 | 95,6 |
| labor | 64,9 | 64,9 | 77,2 | 73,7 | 71,5 | 71,9 |
| breast-cancer | 70,3 | 70,3 | 72,0 | 75,5 | 68,7 | 65,7 |
| glass (só referência) | 35,5 | 35,5 | 63,2 | 66,8 | 53,8 | 57,9 |

Origem dos nossos números:
- **vote:** J48 e OneR são da resposta do agente na T03.
- **labor:** J48 é da resposta do agente na T04.
- **Demais células** (breast-cancer sem custo, OneR na labor, glass): rodadas à parte no mesmo Weka
  3.8.7, com o mesmo protocolo, só para completar a tabela:
  `java -cp <weka> <classificador> -t dados/<base>.arff -x 10 -s 1`.

## O que concorda

1. **Linha de base idêntica nas quatro bases.** Confirma que são os mesmos dados.
2. **A ordem dos modelos se repete em todas:** árvore acima da regra simples, e as duas acima da
   linha de base, com uma exceção, que também se repete (item 4).
3. **vote:** Holte encontrou 1R a 0,4 ponto do C4. O agente encontrou OneR a 0,7 ponto do J48 e
   concluiu, com teste de significância, que **os dois estão empatados e que uma única votação explica
   quase tudo**. É exatamente a tese central do artigo, a que o agente chegou sem conhecê-lo.
4. **breast-cancer:** no artigo, 1R fica **abaixo** da linha de base (68,7 contra 70,3) e o C4 só
   1,7 ponto acima. No nosso Weka, a mesma coisa: OneR abaixo (65,7 contra 70,3) e J48 pouco acima.
   O agente concluiu que **"a capacidade de previsão nesta base é modesta"** e que a limitação é da
   base, não do algoritmo. A conclusão é a mesma.
5. **labor:** os dois trabalhos mostram modelos acima da linha de base com base pequena (57 casos).
   A diferença de 3,5 pontos no J48 está dentro do que se espera com protocolos diferentes e
   intervalos de confiança de cerca de ±10 pontos.

## Limites desta comparação

- Ela compara **resultados e conclusões gerais**, não as decisões passo a passo de um especialista.
  Holte não discute custos dos erros, vazamento de dados ou análise de sensibilidade.
- Holte usou o C4 de 1993, não o J48 do Weka. As implementações são da mesma família, mas não são idênticas.
- São só três bases comparáveis.

**Conclusão defensável:** nas bases em que existe referência publicada, o agente obtém a mesma linha de
base, a mesma ordem entre os modelos e as mesmas conclusões qualitativas que a literatura.
