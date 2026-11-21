#!/usr/bin/env bash
# Roda uma tarefa numa cópia isolada do projeto (git worktree), para que execuções paralelas
# não alterem os arquivos umas das outras. Uso:
#   validacao/rodada_isolada.sh <ID> <repetição> "<pedido>" "<resposta roteirizada>"
# Se no 1º turno o agente não rodar nenhum classificador, considera-se que parou para perguntar
# e a resposta roteirizada é enviada como 2º turno.
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
ID="$1"; REP="$2"; PEDIDO="$3"; RESPOSTA="$4"
NOME="${ID}_r${REP}"
COPIA="${COPIAS:-/tmp/copias_validacao}/$NOME"
DESTINO="$RAIZ/validacao/rodada2/$NOME"
mkdir -p "$(dirname "$COPIA")" "$DESTINO"
git -C "$RAIZ" worktree add -q --detach "$COPIA" "${COMMIT_BASE:-HEAD}"
cd "$COPIA"
# Remove da cópia tudo o que foi gerado durante a validação (respostas, relatórios, gabaritos,
# análises e saídas da rodada 1), para o agente não ler nada disso. Ficam só as correções
# (manual, agente, ferramentas, requirements) e os scripts de execução.
git diff --name-only --diff-filter=A "${COMMIT_PRE_VALIDACAO:-e1536cb}" HEAD \
  | grep -v -E '^(ferramentas/|requirements.txt$|validacao/(rodar_tarefa.sh|rodada_isolada.sh|transcricao.py)$)' \
  | xargs -r git rm -q --cached
git -c user.email=validacao@local -c user.name=validacao commit -q -m "copia limpa" --no-verify
git clean -fdq
git reset -q --hard
validacao/rodar_tarefa.sh "$NOME" "$PEDIDO"
if ! git status --porcelain resultados | grep -q "classificador.txt\|significancia.txt"; then
  echo "parou_para_perguntar=sim" > "$DESTINO/processo.txt"
  validacao/rodar_tarefa.sh "$NOME" "$RESPOSTA" continuar
else
  echo "parou_para_perguntar=nao" > "$DESTINO/processo.txt"
fi
python3 validacao/transcricao.py "$NOME" > /dev/null
# Registra se alguma ferramenta foi alterada e o que foi gerado.
{ echo "ferramentas_alteradas:"; git diff --stat -- ferramentas/; echo "arquivos_novos:"; git status --porcelain | grep -v "^?? validacao/respostas" ; } >> "$DESTINO/processo.txt"
cp validacao/respostas/"$NOME"* "$DESTINO/"
git diff -- ferramentas/ > "$DESTINO/diff_ferramentas.patch"
mkdir -p "$DESTINO/resultados" && git status --porcelain resultados | awk '{print $2}' | xargs -r -I{} cp -r {} "$DESTINO/resultados/"
echo "$NOME concluída"
