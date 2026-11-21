#!/usr/bin/env bash
# Roda o agente (definido em .github/agents/especialista-mineracao.agent.md) às cegas, no Claude Code,
# numa sessão isolada. Uso:
#   validacao/rodar_tarefa.sh T01 "pedido do usuário"            # primeira mensagem
#   validacao/rodar_tarefa.sh T01 "resposta do usuário" continuar  # resposta a uma pergunta do agente
# Requer WEKA_CP apontando para o classpath do Weka 3.8.7.
set -euo pipefail
cd "$(dirname "$0")/.."
ID="$1"; MSG="$2"; MODO="${3:-novo}"
DIR=validacao/respostas; mkdir -p "$DIR"
# Instruções do agente, trocando o caminho do Python do Windows pelo deste ambiente.
PROMPT=$( { cat .github/copilot-instructions.md; echo; sed '1,/^---$/{/^---$/!d}; /^---$/d' .github/agents/especialista-mineracao.agent.md; } \
  | sed 's|`C:\\Users\\Mateus\\anaconda3\\python.exe` (use sempre este caminho; o comando `python` não funciona neste terminal)|`python3`|' )
FERR="Bash Read Write Edit Glob Grep"
if [ "$MODO" = "continuar" ]; then
  SID=$(cat "$DIR/$ID.session")
  N=$(ls "$DIR"/"$ID"_turno*.json 2>/dev/null | wc -l); N=$((N+1))
  claude -p "$MSG" --resume "$SID" --append-system-prompt "$PROMPT" --allowedTools $FERR \
    --output-format json > "$DIR/${ID}_turno${N}.json"
else
  claude -p "$MSG" --append-system-prompt "$PROMPT" --allowedTools $FERR \
    --output-format json > "$DIR/${ID}_turno1.json"
  python3 -c "import json;print(json.load(open('$DIR/${ID}_turno1.json'))['session_id'])" > "$DIR/$ID.session"
fi
python3 - "$DIR" "$ID" <<'PY'
import json,sys,glob
d,i=sys.argv[1],sys.argv[2]
with open(f"{d}/{i}.md","w",encoding="utf-8") as out:
    for f in sorted(glob.glob(f"{d}/{i}_turno*.json")):
        j=json.load(open(f)); out.write(f"## {f.split('_')[-1][:-5]}\n\n{j.get('result','')}\n\n")
PY
