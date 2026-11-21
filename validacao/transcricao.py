"""Gera a transcrição completa de uma tarefa da validação (texto do agente + comandos executados).

O campo `result` do `claude -p` traz só a última mensagem; a sessão inteira fica no histórico do
Claude Code (~/.claude/projects/...). Uso: python3 validacao/transcricao.py T01 [T02 ...]
"""
import glob
import json
import os
import sys

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "respostas")

for tarefa in sys.argv[1:]:
    sessao = open(os.path.join(PASTA, tarefa + ".session")).read().strip()
    arquivos = glob.glob(os.path.expanduser("~/.claude/projects/*/" + sessao + ".jsonl"))
    if not arquivos:
        print(tarefa, ": histórico da sessão não encontrado")
        continue
    linhas = []
    for linha in open(arquivos[0], encoding="utf-8"):
        evento = json.loads(linha)
        tipo = evento.get("type")
        conteudo = evento.get("message", {}).get("content")
        if tipo == "user" and isinstance(conteudo, str):
            linhas.append("\n### Usuário\n\n" + conteudo + "\n")
        elif tipo == "assistant":
            for parte in conteudo:
                if parte["type"] == "text":
                    linhas.append("\n### Agente\n\n" + parte["text"] + "\n")
                elif parte["type"] == "tool_use":
                    entrada = parte["input"]
                    resumo = entrada.get("command") or entrada.get("file_path") or json.dumps(entrada, ensure_ascii=False)
                    linhas.append("- `" + parte["name"] + "`: `" + str(resumo).replace("`", "'")[:300] + "`")
    with open(os.path.join(PASTA, tarefa + "_transcricao.md"), "w", encoding="utf-8") as saida:
        saida.write("# Transcrição " + tarefa + "\n" + "\n".join(linhas) + "\n")
    print(tarefa, ": ok")
