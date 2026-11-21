"""Perfil descritivo da base labor.arff (só estatísticas descritivas; nenhum modelo aqui).

O que o script faz:
1. Lê o .arff linha a linha (cabeçalho -> nomes e tipos; @data -> registros).
2. Para cada atributo numérico: mínimo, máximo, média, mediana, quartis, IQR, zeros e ausentes.
3. Para cada atributo nominal: contagem de cada valor e de ausentes.
4. Conta duplicatas e mostra a taxa de ausentes por classe (a ausência pode ser informação).
5. Salva tudo em resultados/<data_hora>_perfil_labor.txt.
"""
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

linhas = Path("dados/labor.arff").read_text().splitlines()
atributos, tipos, registros, em_dados = [], [], [], False
for linha in linhas:
    s = linha.strip()
    if not s or s.startswith("%"):
        continue
    if s.lower().startswith("@attribute"):
        partes = s.split(None, 2)  # '@attribute', nome, tipo
        atributos.append(partes[1].strip("'"))
        tipos.append("num" if partes[2].lower().startswith("numeric") else "nom")
    elif s.lower().startswith("@data"):
        em_dados = True
    elif em_dados:
        registros.append([v.strip().strip("'") for v in s.split(",")])

saida = []
p = saida.append
classe = [r[-1] for r in registros]
p(f"Registros: {len(registros)}")
p(f"Distribuição da classe: {dict(Counter(classe))}")

# Duplicatas exatas (todas as colunas iguais)
copias = sum(c - 1 for c in Counter(tuple(r) for r in registros).values() if c > 1)
p(f"Registros repetidos (cópias além da primeira): {copias}")
p("")

p("ATRIBUTOS NUMÉRICOS")
p(f"{'atributo':28s} {'n':>3s} {'aus':>4s} {'min':>6s} {'Q1':>6s} {'med':>6s} {'media':>6s} {'Q3':>6s} {'max':>6s} {'IQR':>6s} {'zeros':>5s}")
for i, (a, t) in enumerate(zip(atributos, tipos)):
    if t != "num":
        continue
    vals = sorted(float(r[i]) for r in registros if r[i] != "?")
    q1, med, q3 = statistics.quantiles(vals, n=4, method="inclusive")
    p(f"{a:28s} {len(vals):3d} {len(registros)-len(vals):4d} {min(vals):6.2f} {q1:6.2f} {med:6.2f} "
      f"{statistics.mean(vals):6.2f} {q3:6.2f} {max(vals):6.2f} {q3-q1:6.2f} {vals.count(0.0):5d}")
p("")

p("ATRIBUTOS NOMINAIS (contagem por valor)")
for i, (a, t) in enumerate(zip(atributos, tipos)):
    if t == "nom" and i < len(atributos) - 1:
        p(f"{a:32s} {dict(Counter(r[i] for r in registros))}")
p("")

# A ausência pode carregar informação: % de '?' em cada atributo, separado por classe
p("PERCENTUAL DE AUSENTES POR CLASSE")
p(f"{'atributo':32s} {'%? bad':>7s} {'%? good':>8s}")
for i, a in enumerate(atributos[:-1]):
    taxas = []
    for c in ("bad", "good"):
        vals = [r[i] for r in registros if r[-1] == c]
        taxas.append(100 * vals.count("?") / len(vals))
    p(f"{a:32s} {taxas[0]:7.1f} {taxas[1]:8.1f}")

texto = "\n".join(saida)
print(texto)
destino = Path("resultados") / f"{datetime.now():%Y%m%d_%H%M%S}_perfil_labor.txt"
destino.write_text(texto + "\n")
print(f"\nSalvo em {destino}")
