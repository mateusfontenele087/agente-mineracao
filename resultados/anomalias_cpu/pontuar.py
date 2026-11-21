# Pontuações de anomalia calculadas em PYTHON (o Weka padrão não tem essas pontuações).
# Os grupos vêm do Weka (AddCluster/SimpleKMeans sobre cpu_log.arff).
# Normalização: min-max 0-1 de cada atributo, igual à distância euclidiana padrão do Weka.
import glob, math, statistics as st
def ler(c):
    L = open(c).read().splitlines(); i = [n for n,l in enumerate(L) if l.strip().lower()=="@data"][0]
    return [l.split(",") for l in L[i+1:] if l.strip() and not l.startswith("%")]
log = [list(map(float, r)) for r in ler("dados/cpu_log.arff")]
bruto = [r for r in ler("dados/cpu.arff")]
vend = [r[0] for r in ler("dados/cpu.with.vendor.arff")]
k2 = [r[-1] for r in ler(sorted(glob.glob("resultados/*_cpu_log_k2_clusters.arff"))[-1])]
k3 = [r[-1] for r in ler(sorted(glob.glob("resultados/*_cpu_log_k3.arff"))[-1])]
p = len(log[0]); mn = [min(r[j] for r in log) for j in range(p)]; mx = [max(r[j] for r in log) for j in range(p)]
X = [[(r[j]-mn[j])/(mx[j]-mn[j]) for j in range(p)] for r in log]
d = lambda a, b: math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))
def dist_relativa(rot):  # distância ao centro do grupo / mediana das distâncias do grupo
    s = {}
    for g in set(rot):
        m = [i for i in range(len(X)) if rot[i]==g]
        c = [st.mean(X[i][j] for i in m) for j in range(p)]
        di = {i: d(X[i], c) for i in m}; med = st.median(di.values())
        s.update({i: di[i]/med for i in m})
    return [s[i] for i in range(len(X))]
def dist_knn(k):  # distância ao k-ésimo vizinho mais próximo
    return [sorted(d(X[i], X[j]) for j in range(len(X)) if j!=i)[k-1] for i in range(len(X))]
sc = {"agr_k2": dist_relativa(k2), "agr_k3": dist_relativa(k3), "knn5": dist_knn(5), "knn10": dist_knn(10)}
rank = {n: {i: r+1 for r, i in enumerate(sorted(range(len(X)), key=lambda i: -v[i]))} for n, v in sc.items()}
TOP = 15
print("Máquinas no top-15 de pelo menos uma pontuação (ordenadas pela posição média):")
cand = [i for i in range(len(X)) if any(rank[n][i] <= TOP for n in sc)]
cand.sort(key=lambda i: st.mean(rank[n][i] for n in sc))
print(f"{'linha':>5} {'fabr':>12} {'MYCT,MMIN,MMAX,CACH,CHMIN,CHMAX,class':40} " + " ".join(f"{n:>11}" for n in sc) + "  nTop15 g2 g3")
for i in cand:
    print(f"{i+1:5d} {vend[i]:>12} {','.join(bruto[i]):40} " + " ".join(f"{sc[n][i]:6.2f}({rank[n][i]:3d})" for n in sc) + f"  {sum(rank[n][i]<=TOP for n in sc):6d} {k2[i]} {k3[i]}")
print("\nTamanho dos grupos k3:", {g: k3.count(g) for g in set(k3)})
