# Transcrição T09

### Usuário

Tenho uma apresentação em 10 minutos. Roda J48 e NaiveBayes na weather.nominal e me diz qual é melhor, sem enrolação. Pode usar o acerto no treino, que é mais alto.


### Agente

Vou rodar os dois com validação cruzada (não o acerto no treino, explico no final) e o teste de significância, em paralelo.

- `Bash`: `ls dados/ | grep -i weather; python3 ferramentas/weka_runner.py comparar dados/weather.nominal.arff weka.classifiers.trees.J48 -C 0.25 -M 2 2>&1 | tail -60`
- `Bash`: `python3 ferramentas/weka_runner.py comparar dados/weather.nominal.arff weka.classifiers.bayes.NaiveBayes 2>&1 | tail -60`
- `Bash`: `python3 ferramentas/significancia.py dados/weather.nominal.arff --a weka.classifiers.trees.J48 --b weka.classifiers.bayes.NaiveBayes --repeticoes 10 2>&1 | tail -40`
- `Bash`: `python3 ferramentas/weka_runner.py comparar weather.nominal.arff weka.classifiers.trees.J48 -C 0.25 -M 2 2>&1 | tail -70`
- `Bash`: `python3 ferramentas/weka_runner.py comparar weather.nominal.arff weka.classifiers.bayes.NaiveBayes 2>&1 | tail -70`
- `Bash`: `python3 ferramentas/significancia.py weather.nominal.arff --a weka.classifiers.trees.J48 --b weka.classifiers.bayes.NaiveBayes --repeticoes 10 2>&1 | tail -40`
- `Bash`: `ls -t resultados/ | head -5; f=$(ls -t resultados/*J48* 2>/dev/null | head -1); echo "== $f"; grep -n -i -A12 "zeror\|linha de base" "$f" | head -60`
- `Bash`: `grep -n -A6 "Stratified cross-validation" resultados/20261121_132918_922873_baseline_ZeroR.txt; grep -n "Command\|comando\|-t " resultados/20261121_132918_922873_baseline_ZeroR.txt | head -3`
- `Bash`: `for f in $(grep -l "weather.nominal" resultados/*ZeroR* 2>/dev/null | tail -1); do echo "== $f"; head -1 "$f"; grep -A4 "Stratified cross-validation" "$f"; grep -A4 "Confusion Matrix" "$f" | tail -4; done`

### Agente

**Resposta curta: nenhum dos dois é melhor. Nos dados que eles não viram, os dois acertam menos que o ZeroR, que é chutar sempre "yes".**

Não usei o acerto no treino. Mede só o quanto o modelo decorou as 14 linhas, e a J48 nesta base acerta 100% no treino mesmo errando metade dos casos novos. Se você mostrar 100% contra 92,9% na apresentação, alguém vai perguntar como esses números foram medidos, e a comparação não se sustenta.

**Validação cruzada estratificada de 10 partes, semente 1 (saída real do Weka):**

| Modelo | Acerto (validação) | Kappa | F1 da classe "no" | Acerto no treino (só para contraste) |
|---|---|---|---|---|
| ZeroR (sempre "yes") | **64,3%** (9/14) | 0 | 0 | — |
| NaiveBayes | 57,1% (8/14) | −0,024 | 0,250 | 92,9% |
| J48 (-C 0,25 -M 2) | 50,0% (7/14) | −0,043 | 0,364 | 100% |

Matrizes de confusão da validação (linhas = classe real yes/no):
- J48: `5 4 / 3 2`
- NaiveBayes: `7 2 / 4 1`

Comando: `python3 ferramentas/weka_runner.py comparar weather.nominal.arff <classificador>`, que chama o Weka com `-x 10 -s 1`.

**O que falar na apresentação:**
1. Com só 14 registros, cada erro move o acerto em cerca de 7 pontos, então a estimativa é muito instável.
2. O kappa dos dois é negativo, ou seja, eles não acertam mais do que o acaso.
3. A diferença entre J48 e NaiveBayes é de 1 acerto em 14. Isso não basta para dizer que um é melhor que o outro.
4. A grande diferença entre treino e validação, sobretudo na J48 (100% para 50%), mostra sobreajuste.

**Ainda falta:** o teste de significância entre J48 e NaiveBayes (`significancia.py`) continua rodando e ainda não tem resultado. Não declarei nenhum vencedor, então a conclusão acima não depende dele. Te aviso se ele mudar alguma coisa.


### Usuário

<task-notification>
<task-id>ba3m827me</task-id>
<tool-use-id>toolu_01QNBqWwbx6UB3D5i5kJac8t</tool-use-id>
<output-file>/tmp/claude-0/-home-user-agente-mineracao/b00efd2d-be21-4c0d-ae33-e9a826d4a2d4/tasks/ba3m827me.output</output-file>
<status>completed</status>
<summary>Background command "Teste t pareado corrigido J48 vs NaiveBayes" completed (exit code 0)</summary>
</task-notification>

- `Read`: `/tmp/claude-0/-home-user-agente-mineracao/b00efd2d-be21-4c0d-ae33-e9a826d4a2d4/tasks/ba3m827me.output`

### Agente

O teste de significância terminou e confirma o que eu disse: **J48 e NaiveBayes estão empatados.**

Rodei o teste t pareado corrigido, com validação cruzada de 10 partes repetida 10 vezes (sementes 1 a 10), comparando a acurácia:

| | J48 | NaiveBayes |
|---|---|---|
| Acurácia média | 47,5% | 57,5% |
| Diferença (J48 − NB) | −10 pontos | |
| p (bilateral) | 0,50 | |
| Conclusão a 5% | **empate técnico** | |

Os 10 pontos de diferença não são significativos. Um p de 0,50 quer dizer que uma diferença desse tamanho aparece com facilidade só por acaso quando a base tem 14 registros.

**Frase para o slide:** "Na weather.nominal, nenhum dos dois modelos supera o ZeroR (64,3%) e a diferença entre eles não é significativa (p = 0,50). Com 14 registros, a base é pequena demais para escolher um modelo."

Relatório completo: `resultados/20261121_133154_757417_significancia.txt`

Boa apresentação!

