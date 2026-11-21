# Transcrição T11_r1

### Usuário

Compare o J48 e o NaiveBayes na ionosphere.arff pela AUC e me diga se a diferença é significativa.


### Agente

Vou começar lendo o manual de decisões e conferindo o que a ferramenta de significância suporta.

- `Bash`: `ls; ls ferramentas dados resultados 2>/dev/null | head -50; wc -l conhecimento/manual_decisoes.md`
- `Bash`: `python3 ferramentas/significancia.py --help; grep -n -i "auc\|metric\|métrica" ferramentas/significancia.py | head -60`
- `Read`: `/tmp/copias_validacao/T11_r1/ferramentas/significancia.py`
- `Grep`: `{"pattern": "(?i)auc|roc", "path": "/tmp/copias_validacao/T11_r1/conhecimento/manual_decisoes.md", "output_mode": "content"}`
- `Read`: `/tmp/copias_validacao/T11_r1/conhecimento/manual_decisoes.md`

### Agente

A ferramenta de significância não calcula AUC; volto a isso no fim. Antes, rodo o que as ferramentas validadas já permitem: o resumo da base e a validação cruzada de cada modelo contra o ZeroR.

- `Bash`: `python3 ferramentas/weka_runner.py resumo dados/ionosphere.arff 2>&1 | tail -60`
- `Bash`: `python3 ferramentas/weka_runner.py comparar dados/ionosphere.arff weka.classifiers.trees.J48 -C 0.25 -M 2 2>&1 | tail -40; echo ======; python3 ferramentas/weka_runner.py comparar dados/ionosphere.arff weka.classifiers.bayes.NaiveBayes 2>&1 | tail -40`
- `Bash`: `python3 ferramentas/weka_runner.py resumo ionosphere.arff 2>&1 | tail -60`
- `Bash`: `python3 ferramentas/weka_runner.py comparar ionosphere.arff weka.classifiers.trees.J48 -C 0.25 -M 2 2>&1 | tail -40; echo ======; python3 ferramentas/weka_runner.py comparar ionosphere.arff weka.classifiers.bayes.NaiveBayes 2>&1 | tail -40`

### Agente

O final das saídas foi cortado. Vou ler os arquivos completos em `resultados/` para confirmar qual bloco é de validação cruzada e pegar o ZeroR e os comandos.

- `Bash`: `ls -t resultados | head -6; for f in $(ls -t resultados | head -4); do echo "##### $f"; grep -v "Picked up" resultados/$f | head -80; done`

### Agente

Os blocos de validação cruzada estão confirmados. Calculo o intervalo de confiança das acurácias a partir dos acertos que o Weka relatou.

- `Bash`: `python3 -c "
from math import sqrt
z=1.96;n=351
for nome,acertos in [('ZeroR',225),('J48',321),('NaiveBayes',290)]:
    p=acertos/n; c=(p+z*z/(2*n))/(1+z*z/n); m=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    print(f'{nome}: {p:.4f}  IC95% Wilson [{c-m:.3f}; {c+m:.3f}]')
"`

### Agente

# J48 × NaiveBayes na ionosphere pela AUC

**Ainda não sei dizer se a diferença é significativa, e por isso não chamo nenhum dos dois de "melhor".** As AUCs abaixo vêm de uma única validação cruzada no Weka. O teste de significância não rodou porque `ferramentas/significancia.py` não calcula AUC. Ela só lê a matriz de confusão de cada parte e dela tira acurácia, precisão, recall, F1 e custo. A AUC precisa das probabilidades que o modelo dá a cada caso, e a ferramenta não as coleta. Ela está validada, então não a alterei sem a sua autorização (detalhes no fim).

**Suposição:** a métrica principal é a AUC, como você pediu, e foi definida antes de ver os resultados. Tomei `b` (sinal "ruim" do radar, 36% da base) como classe de interest. Sem informação de custo, tratei os dois erros como equivalentes. Em duas classes a AUC é a mesma para `b` e para `g`.

## 1. O que foi feito
- **Base:** 351 instâncias, 34 atributos numéricos, classe `b` com 126 casos e `g` com 225. Não há valores ausentes. O atributo `a02` tem um único valor e não informa nada. Não atrapalha nenhum dos dois modelos, mas fica registrado.
- **Pré-processamento:** nenhum.
- **Avaliação:** validação cruzada estratificada de 10 partes, semente 1.
- **Comandos:**
  ```
  java -cp .../weka/lib/* weka.classifiers.trees.J48 -t dados/ionosphere.arff -x 10 -s 1 -C 0.25 -M 2
  java -cp .../weka/lib/* weka.classifiers.bayes.NaiveBayes -t dados/ionosphere.arff -x 10 -s 1
  java -cp .../weka/lib/* weka.classifiers.rules.ZeroR -t dados/ionosphere.arff -x 10 -s 1
  ```

## 2 e 3. Resultado do Weka (só a validação cruzada) e comparação com o ZeroR

| Modelo | **AUC** | Acurácia (IC 95%) | Kappa | Recall `b` | Precisão `b` | F1 `b` |
|---|---|---|---|---|---|---|
| ZeroR | 0,485 | 64,1% [59,0; 68,9] | 0 | 0,000 | — | — |
| J48 | **0,892** | 91,5% [88,1; 93,9] | 0,810 | 0,825 | 0,929 | 0,874 |
| NaiveBayes | **0,935** | 82,6% [78,3; 86,2] | 0,639 | 0,865 | 0,712 | 0,781 |

Matrizes de confusão (linha = classe real):
```
J48:          b    g          NaiveBayes:   b    g
   b        104   22             b        109   17
   g          8  217             g         44  181
```

Os dois modelos ficam muito acima do ZeroR, que tem AUC 0,485, perto do acaso. Essa folga é grande, mas também não passou por teste formal.

## 4. Confiabilidade
- A diferença de AUC é de 0,043 a favor do NaiveBayes, e **não foi testada**. Até ser testada, os dois estão em **empate técnico** na métrica principal.
- **Atenção:** a ordem dos modelos se inverte conforme a métrica. O J48 tem maior acurácia e kappa, e o NaiveBayes tem maior AUC.
  - A AUC mede se o modelo **ordena** bem os casos, ou seja, se coloca os `b` acima dos `g`.
  - A acurácia mede se ele acerta no **limiar padrão** de 0,5.
  - O NaiveBayes ordena bem, mas com esse limiar gera 44 alarmes falsos.
  - Isso mostra por que a métrica precisa ser escolhida antes. Não vale olhar os resultados e escolher a métrica que favorece um dos modelos.

## 5. Interpretação
- O J48 gerou uma árvore com 18 folhas. A primeira divisão, `a05 <= 0.0409 → b`, isola sozinha 67 casos `b`.
- Para o NaiveBayes, as probabilidades servem para ordenar os casos, mas não devem ser lidas como chances confiáveis. A suposição de independência entre atributos as empurra para perto de 0 ou de 1.

## 6. Alertas
- **Sobreajuste no J48:** o J48 acerta 99,7% no treino e 91,5% na validação. A árvore é podada, então essa diferença de cerca de 8 pontos é um sinal moderado de sobreajuste.
- **NaiveBayes:** ele supõe distribuição normal para cada atributo numérico, e eu não verifiquei se as distribuições são assimétricas. Também não testei as opções `-K` e `-D`. É uma limitação em aberto.
- **O que não foi executado:** o teste de significância da AUC (nem J48 × NaiveBayes, nem cada um × ZeroR), as versões `-K` e `-D` do NaiveBayes e a análise de custos.

## O que falta na ferramenta, e o pedido de autorização
Para testar a AUC, `significancia.py` precisa calcular a AUC em cada uma das 10 × 10 partes de teste. A proposta:
1. Pedir ao Weka as probabilidades de cada caso de teste, com a opção `-classifications "weka.classifiers.evaluation.output.prediction.CSV"`.
2. Calcular a AUC da parte a partir dessas probabilidades. É uma conta sobre a saída real do Weka, sem inventar números.
3. Aplicar o mesmo teste t corrigido que a ferramenta já usa.
4. Criar um teste de aceite em `ferramentas/testes_aceite.py` que confira a AUC calculada pela ferramenta contra a "ROC Area" que o próprio Weka mostra, e rodar todos os testes antes de usar a ferramenta.

**Posso fazer essa alteração?** Se autorizar, faço em passos pequenos e explico cada trecho. Uma alternativa sem mexer na ferramenta é usar o Experimenter na interface gráfica do Weka, que já testa a "Area under ROC" com o teste t corrigido. Nesse caso, você roda e me traz a saída para eu interpretar.

