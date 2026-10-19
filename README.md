Agente Especialista em Mineração de Dados
Agente construído sobre o GitHub Copilot (VS Code) que atua como um especialista em mineração de dados: decide como um analista experiente decidiria e executa as análises no Weka de verdade, sem inventar resultados.
Trabalho da disciplina [NOME DA DISCIPLINA] – Mestrado Profissional PPgCTI/UFRN.
Como funciona
O agente tem três camadas:
Camada	Arquivo	Função
Conhecimento	`conhecimento/manual_decisoes.md`	Regras de decisão de especialista, destiladas do livro Introduction to Data Mining (Tan, Steinbach, Kumar, 1ª ed.) e reescritas com palavras próprias
Ferramentas	`ferramentas/weka_runner.py`	Executa o Weka 3.8.7 pela linha de comando e grava cada saída em `resultados/` com o comando exato
Raciocínio	`.github/agents/especialista-mineracao.agent.md`	Define o papel, as regras inegociáveis, o fluxo de trabalho e o formato da resposta do agente
O livro em si não está no repositório, por respeito aos direitos autorais. O agente usa o conhecimento incorporado no manual, sem citá-lo.
Regras principais do agente
Nenhum número inventado: toda métrica vem da saída real do Weka.
Avaliação por validação cruzada estratificada de 10 partes, semente 1.
Relata apenas o bloco de validação cruzada; o desempenho no treino só aparece como evidência de sobreajuste.
Sempre compara com a linha de base (ZeroR).
Calcula o intervalo de confiança da acurácia e não declara diferença sem significância estatística.
Pergunta se o objetivo é entender ou prever antes de modelar.
Validação da camada Weka
As matrizes de confusão geradas pelo script foram comparadas com as do Weka Explorer (interface gráfica), com a mesma base e a mesma configuração. Resultados idênticos.
Exemplo de análise do agente — `weather.nominal.arff`
Objetivo informado ao agente: entender os fatores associados a `play`.
Modelo	Acertos	Acurácia	IC 95% (Wilson)	Kappa
ZeroR (linha de base)	9/14	64,3%	38,8% – 83,7%	0
J48 (`-C 0.25 -M 2`)	7/14	50,0%	26,8% – 73,2%	−0,043
Matriz de confusão do J48 (validação cruzada):
```
 a b   <-- classificado como
 5 4 | a = yes
 3 2 | b = no
```
Conclusões do agente:
O J48 não superou a linha de base; os intervalos de confiança se sobrepõem quase inteiramente, então não há evidência de que um modelo seja melhor que o outro.
Sobreajuste: a árvore acerta 100% dos 14 registros no treino, mas só 50% na validação cruzada.
A árvore descreve padrões dos 14 casos (ensolarado → depende da umidade; nublado → joga; chuvoso → depende do vento), mas não são regras confiáveis para prever: a base é pequena demais.
As saídas completas do Weka estão em `resultados/`.
Como executar
Requisitos: Java 8+, Weka 3.8.7, Python 3, VS Code com GitHub Copilot.
Ajuste o caminho do `weka.jar` no topo de `ferramentas/weka_runner.py`.
No chat do Copilot, selecione o agente especialista-mineracao.
Peça, por exemplo: "Faça uma análise de weather.nominal.arff."
Uso direto das ferramentas:
```
python ferramentas/weka_runner.py resumo weather.nominal.arff
python ferramentas/weka_runner.py comparar weather.nominal.arff weka.classifiers.trees.J48 -C 0.25 -M 2
```
Estado do projeto
[x] Manual de decisões – Parte 1 (classificação, árvores, avaliação)
[x] Camada Weka validada
[x] Agente funcionando
[ ] Manual – Parte 2 (técnicas alternativas e classes desbalanceadas)
[ ] Manual – Partes 3 a 6 (dados, associação, agrupamento, anomalias)
