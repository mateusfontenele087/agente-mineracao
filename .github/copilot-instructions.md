# Contexto do projeto: Agente Especialista em Mineração de Dados

> Arquivo de contexto para o assistente de programação (Copilot: salvar como `.github/copilot-instructions.md`; Claude Code: salvar como `CLAUDE.md` na raiz do projeto).

## Quem sou eu
- Mestrando no Mestrado Profissional do PPgCTI/UFRN (linha Gestão da Inovação).
- **Nível iniciante em programação e estatística.** Comecei a programar no mestrado. Uso Python e Anaconda.
- Quero aprender, não só receber código pronto. Trabalho bem com passos curtos e sem pressa.

## Objetivo do projeto
Tarefa da disciplina [NOME DA DISCIPLINA – prof. NOME]: construir um **agente especialista em mineração de dados** que:
1. Tem como base de conhecimento o livro *Introduction to Data Mining*, de Pang-Ning Tan, Michael Steinbach e Vipin Kumar ([EDIÇÃO]).
2. **Executa as análises no Weka de verdade** (pré-processamento, treino, avaliação, matrizes de confusão).
3. **Toma as decisões que um especialista tomaria** e as justifica pelos fundamentos.
4. **Não cita o livro.** O conhecimento deve estar incorporado nas decisões, não em referências.

## Arquitetura (3 camadas)
1. **Conhecimento – manual de decisões** (`conhecimento/manual_decisoes.md`): o livro destilado em regras de especialista (quando usar cada técnica, pré-processamento, avaliação, armadilhas). O livro completo em Markdown fica em `conhecimento/livro/` como consulta interna.
2. **Ferramentas – camada Weka** (`ferramentas/`): scripts Python que chamam o Weka (linha de comando via `java -cp weka.jar` ou biblioteca `python-weka-wrapper3`) e devolvem a saída real.
3. **Raciocínio – fluxo do especialista**: explorar os dados → decidir pré-processamento → testar algoritmos candidatos → comparar com rigor → escolher e justificar.

## Tabela de tradução: conceito do livro → Weka
| Conceito (Tan) | Weka |
|---|---|
| Linha de base | ZeroR |
| Árvore de decisão (C4.5) | J48 |
| Regras (RIPPER) | JRip |
| Naive Bayes | NaiveBayes |
| k-NN | IBk |
| SVM | SMO |
| Redes neurais | MultilayerPerceptron |
| Ensembles | Bagging, AdaBoostM1, RandomForest |
| Regras de associação | Apriori |
| k-means | SimpleKMeans |
| Agrupamento hierárquico | HierarchicalClusterer |
| DBSCAN | pacote adicional (DBSCAN/optics) |
| Comparação estatística entre modelos | Experimenter – teste t pareado corrigido |

Detecção de anomalias tem suporte limitado no Weka: o agente deve dizer isso, não inventar.

## Regras inegociáveis
- **Nenhum número inventado.** Toda métrica, matriz ou árvore apresentada pelo agente deve vir da saída real do Weka. Se o Weka não rodou, o agente diz que não rodou.
- **Reprodutibilidade:** fixar semente (`-s 1`), usar validação cruzada estratificada de 10 partes (`-x 10`) por padrão, registrar o comando exato usado.
- **Rigor de especialista:** sempre comparar com ZeroR; não declarar um modelo melhor sem teste de significância; em classes desbalanceadas, não usar só acurácia (olhar precisão, recall, F1, kappa, AUC).
- **LGPD:** dados da Prefeitura com informação pessoal não entram em nenhuma ferramenta de IA sem anonimização.

## Como quero que você (assistente) trabalhe comigo
- Explique o que cada trecho de código faz, em português, com comentários no código.
- Prefira código simples e legível a código "esperto".
- Faça mudanças pequenas e uma de cada vez; pergunte antes de reestruturar o projeto.
- Quando houver mais de um caminho, mostre as opções e o porquê da recomendação.
- Se eu estiver errado, diga diretamente e explique.

## Ambiente
- Sistema operacional: [PREENCHER]
- Java: [versão] (necessário para o Weka)
- Weka: [versão] – caminho do `weka.jar`: [PREENCHER]
- Python: Anaconda, ambiente `[nome]`

## Estrutura de pastas (planejada)
```
agente-mineracao/
├── .github/copilot-instructions.md   # este arquivo
├── conhecimento/
│   ├── livro/                       # livro do Tan em .md (não versionar se houver restrição de direitos)
│   └── manual_decisoes.md
├── dados/                           # bases .arff
├── ferramentas/                     # scripts que executam o Weka
├── agente/                          # lógica do agente
├── testes/                          # casos para validar as decisões do agente
└── README.md
```

## Como vamos validar
- Exemplos pequenos do livro transcritos para `.arff` (conferíveis à mão).
- Bases que vêm com o Weka (iris, weather, diabetes…).
- Conferir: os números do agente batem com o Weka na interface gráfica? As decisões batem com o que o livro recomenda?