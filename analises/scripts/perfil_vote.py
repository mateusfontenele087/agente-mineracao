"""Perfil descritivo da base vote.arff (só contagens; nenhum modelo aqui)."""
from collections import Counter
from datetime import datetime
from pathlib import Path

linhas, atributos, dados = Path("dados/vote.arff").read_text().splitlines(), [], False
registros = []
for l in linhas:
    s = l.strip()
    if not s or s.startswith("%"):
        continue
    if s.lower().startswith("@attribute"):
        atributos.append(s.split()[1].strip("'"))
    elif s.lower().startswith("@data"):
        dados = True
    elif dados:
        registros.append([v.strip().strip("'") for v in s.split(",")])

saida = []
p = saida.append
classe = [r[-1] for r in registros]
p(f"Registros: {len(registros)}")
p(f"Classe: {Counter(classe)}")
# Duplicatas: registros idênticos (incluindo a classe)
cont = Counter(tuple(r) for r in registros)
dup = sum(c - 1 for c in cont.values() if c > 1)
p(f"Registros repetidos (cópias além da primeira): {dup}")
# Registros idênticos nos votos mas com classe diferente (conflitos)
votos = {}
for r in registros:
    votos.setdefault(tuple(r[:-1]), set()).add(r[-1])
p(f"Perfis de voto idênticos com partidos diferentes: {sum(1 for v in votos.values() if len(v) > 1)}")
p(f"Registros com pelo menos um '?': {sum(1 for r in registros if '?' in r)}")
p("")
p(f"{'atributo':40s} {'%sim dem':>9s} {'%sim rep':>9s} {'%? dem':>7s} {'%? rep':>7s}")
for i, a in enumerate(atributos[:-1]):
    lin = []
    for partido in ("democrat", "republican"):
        vals = [r[i] for r in registros if r[-1] == partido]
        val = [v for v in vals if v != "?"]
        lin.append((100 * val.count("y") / len(val), 100 * vals.count("?") / len(vals)))
    p(f"{a:40s} {lin[0][0]:9.1f} {lin[1][0]:9.1f} {lin[0][1]:7.1f} {lin[1][1]:7.1f}")

texto = "\n".join(saida)
print(texto)
arq = Path("resultados") / f"{datetime.now():%Y%m%d_%H%M%S}_perfil_vote.txt"
arq.write_text("Script: analises/scripts/perfil_vote.py\n\n" + texto + "\n")
print("\nSalvo em", arq)
