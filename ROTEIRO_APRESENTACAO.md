# Roteiro para explicar o agente com suas palavras

Este roteiro **não é um texto para decorar.** Ele lista o que você precisa entender para explicar o
projeto e responder às perguntas do professor. Use assim:
1. Leia cada parte.
2. Feche o arquivo e escreva, com suas palavras, uma explicação de 1 página.
3. Confira a sua versão contra as perguntas da seção 5. Onde travar, volte aqui.

---

## 1. O que foi construído, em uma frase

Um assistente que **decide como um analista de mineração de dados decidiria** (com base nas regras do
livro de Tan, Steinbach e Kumar) e **executa as análises no Weka de verdade**, sem inventar números.

## 2. As três camadas e o que cada uma faz

| Camada | Arquivo | Pergunta que ela responde |
|---|---|---|
| Conhecimento | `conhecimento/manual_decisoes.md` | *O que* um especialista faria? (116 regras de decisão tiradas do livro) |
| Ferramentas | `ferramentas/*.py` | *Como* executar no Weka e calcular a significância, sem inventar resultado? |
| Raciocínio | `.github/agents/especialista-mineracao.agent.md` | *Em que ordem* agir, o que é proibido e como responder? |

**Ponto que o professor pode explorar:** o modelo de linguagem (o "cérebro" genérico) **não foi
treinado** com o livro. Ele recebe o manual como instrução a cada conversa. **Não diga "treinei o
agente".** Diga "construí uma base de conhecimento a partir do livro e um conjunto de regras que o
agente é obrigado a seguir".

**Por que separar em camadas?** Porque cada erro tem um lugar para ser corrigido:
- decisão errada (por exemplo, não perguntar o custo) → corrige o **manual**;
- número errado → corrige a **ferramenta**;
- passo fora de ordem → corrige o **raciocínio**.

## 3. Como o agente foi desenvolvido: testar, achar o erro, virar regra

1. Deu uma tarefa ao agente (credit-g).
2. Conferiu a resposta contra o Weka.
3. Cada erro virou uma regra nova no manual. Exemplo: na v2 ele usou recall como métrica, mas
   "recusar todos" tem recall 1,0. Daí veio a regra "nunca recall sozinho".
4. Repetiu a tarefa até as respostas ficarem corretas.
5. Testou numa base **nova** (diabetes) **sem mexer nas regras**, para ver se ele generalizava.

**Por que o passo 5 importa:** regras ajustadas olhando para uma base podem só "decorar" aquela base.
O nome disso é sobreajuste, o mesmo conceito da disciplina aplicado ao próprio agente.

## 4. Como ele foi validado

### Rodada 1: 10 tarefas novas
- Bases que o agente nunca tinha visto.
- **Gabarito escrito antes** de rodar, guardado fora do alcance do agente; no git foi registrado só o
  "hash" (uma impressão digital do arquivo). Se alguém mudasse o gabarito depois de ver as respostas,
  o hash não bateria. **Isso é pré-registro**, a mesma ideia usada em pesquisa científica.
- Resultado: 10 de 10 aprovadas. Foram encontrados 4 defeitos de disciplina, não de mineração
  (detalhes em `validacao/RELATORIO.md`).

### Correções
- **D1:** o agente às vezes não perguntava o custo dos erros, porque "classes desbalanceadas" não
  tinha definição. Agora ele pergunta sempre que o objetivo é prever.
- **D2:** o agente alterou uma ferramenta validada sem pedir. Agora é proibido, e foram criados
  testes de aceite (`ferramentas/testes_aceite.py`).

### Rodada 2: as correções funcionam e o resultado se repete?
- Cada tarefa rodou **3 vezes**, cada vez numa cópia isolada do projeto.
- Resultado em `validacao/RELATORIO_RODADA2.md`.

### Comparação com a literatura
- Holte (1993) testou árvore de decisão contra regra de um atributo nas mesmas bases.
- O agente chegou à **mesma linha de base, à mesma ordem entre os modelos e às mesmas conclusões**
  (por exemplo: na vote, uma única votação explica quase tudo; na breast-cancer, a base é difícil).
  Ver `validacao/comparacao_literatura.md`.

## 5. Perguntas que o professor provavelmente vai fazer

Tente responder sozinho antes de olhar a pista.

1. **"Como eu sei que ele não inventou os números?"**
   *Pista:* toda saída do Weka fica salva em `resultados/` com o comando exato. Dá para rodar o mesmo
   comando e conferir. Na validação, todos os números citados foram conferidos.
2. **"Por que comparar com o ZeroR?"**
   *Pista:* o ZeroR prevê sempre a classe mais comum. Se um modelo não o supera, ele não aprendeu nada.
   Com custo, a linha de base pode ser "recusar todos".
3. **"Por que não usar a acurácia no treino?"**
   *Pista:* o modelo já viu aqueles dados. O IBk com k = 1 acerta 100% no treino por construção.
4. **"Por que o teste t corrigido e não o teste t comum?"**
   *Pista:* nas validações cruzadas os conjuntos de treino se sobrepõem, então as medidas não são
   independentes. O teste comum acharia diferença onde não há. A correção de Nadeau e Bengio
   compensa isso, e é a que o Weka Experimenter usa.
5. **"O que é empate técnico e por que escolher o mais simples?"**
   *Pista:* diferença que o teste não confirma pode ser acaso. Entre empatados, o mais simples é mais
   fácil de explicar e tende a sobreajustar menos.
6. **"Por que ele para e pergunta o custo dos erros?"**
   *Pista:* deixar passar um doente e dar um alarme falso não custam o mesmo, e só o usuário sabe
   quanto custa cada um. Sem isso, a métrica escolhida pode premiar o modelo errado.
7. **"O agente chega às mesmas conclusões que um especialista?"**
   *Resposta honesta:* ele segue as decisões que a literatura prescreve, passou em 10 tarefas novas
   com gabarito pré-registrado e chega às mesmas conclusões publicadas por Holte (1993) nas bases
   comparáveis. **Não houve comparação com um especialista humano às cegas.** Essa é a principal
   limitação e o próximo passo natural.
8. **"Quais são os limites?"**
   *Pista:*
   - só o Weka (sem séries temporais, texto ou inferência causal);
   - o comportamento varia entre execuções, por isso foram feitas 3 repetições;
   - o gabarito foi escrito com ajuda de uma IA, não por um especialista independente;
   - a validação rodou no Claude Code, não no Copilot.
9. **"Por que ele recusou a planilha de servidores?"**
   *Pista:* a planilha tinha nome e CPF. Pela LGPD, dados pessoais não anonimizados não entram em
   ferramenta de IA. Os dados do teste eram fictícios, justamente para testar a recusa.

## 6. Se o professor quiser testar o agente na hora

Deixe que ele escolha uma base do Weka e faça um pedido. Depois:
1. Mostre que o agente pergunta o objetivo e o custo dos erros.
2. Abra o arquivo de `resultados/` citado e mostre que os números batem.
3. Rode o mesmo modelo no Weka Explorer, na interface gráfica, com validação cruzada de 10 partes e
   semente 1. A matriz de confusão deve ser **idêntica**. Essa é a demonstração mais forte que você
   pode fazer ao vivo.

**Antes da apresentação, ensaie esse passo a passo pelo menos uma vez no seu computador.**
