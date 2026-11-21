# Perfil descritivo de cpu.arff (estatística descritiva em Python, sem modelos).
import statistics as st, sys
from collections import Counter
linhas = open("dados/cpu.arff").read().splitlines()
i = [n for n, l in enumerate(linhas) if l.strip().lower() == "@data"][0]
nomes = [l.split()[1] for l in linhas if l.lower().startswith("@attribute")]
dados = [list(map(float, l.split(","))) for l in linhas[i+1:] if l.strip() and not l.startswith("%")]
print("n =", len(dados))
def q(v, p):  # quartil por interpolação linear
    v = sorted(v); k = (len(v)-1)*p; f = int(k); c = min(f+1, len(v)-1)
    return v[f] + (v[c]-v[f])*(k-f)
print(f"{'atrib':6} {'min':>8} {'Q1':>8} {'mediana':>8} {'media':>9} {'Q3':>8} {'max':>8} {'IQR':>8} {'zeros':>5} {'>Q3+3IQR':>9}")
for j, nome in enumerate(nomes):
    v = [d[j] for d in dados]; q1, q3 = q(v, .25), q(v, .75); iqr = q3-q1
    print(f"{nome:6} {min(v):8.0f} {q1:8.1f} {st.median(v):8.1f} {st.mean(v):9.1f} {q3:8.1f} {max(v):8.0f} {iqr:8.1f} {sum(x==0 for x in v):5d} {sum(x>q3+3*iqr for x in v):9d}")
dup = Counter(tuple(d) for d in dados)
print("linhas duplicadas (todas as 7 colunas):", sum(c-1 for c in dup.values() if c > 1))
dup6 = Counter(tuple(d[:6]) for d in dados)
print("grupos com configuração idêntica (6 atributos) e >1 máquina:", sum(1 for c in dup6.values() if c > 1))
# inconsistências lógicas
print("MMIN > MMAX:", [n+1 for n, d in enumerate(dados) if d[1] > d[2]])
print("CHMIN > CHMAX:", [n+1 for n, d in enumerate(dados) if d[4] > d[5]])
