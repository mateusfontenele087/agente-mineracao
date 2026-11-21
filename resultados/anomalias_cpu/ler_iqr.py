# Lê as saídas do filtro InterquartileRange do Weka e lista as máquinas marcadas.
def ler(caminho):
    L = open(caminho).read().splitlines()
    nomes = [l.split()[1] for l in L if l.lower().startswith("@attribute")]
    i = [n for n, l in enumerate(L) if l.strip().lower() == "@data"][0]
    return nomes, [l.split(",") for l in L[i+1:] if l.strip()]
import glob
geral = sorted(glob.glob("resultados/*_anomalias_cpu_iqr.arff"))[-1]
por = sorted(glob.glob("resultados/*_anomalias_cpu_iqr_por_atributo.arff"))[-1]
n1, d1 = ler(geral); n2, d2 = ler(por)
# vendedor (mesma ordem de linhas em cpu.with.vendor.arff?)
nv, dv = ler("dados/cpu.with.vendor.arff")
print("Outlier=yes:", sum(r[-2]=="yes" for r in d1), " ExtremeValue=yes:", sum(r[-1]=="yes" for r in d1))
for k, (r, rp) in enumerate(zip(d1, d2)):
    if r[-2] == "yes" or r[-1] == "yes":
        flags = []
        for j, nome in enumerate(n2):
            if r[-2]=="yes" or True:
                pass
        ext = [n2[j].replace("_ExtremeValue","") for j in range(len(n2)) if n2[j].endswith("_ExtremeValue") and rp[j]=="yes"]
        out = [n2[j].replace("_Outlier","") for j in range(len(n2)) if n2[j].endswith("_Outlier") and rp[j]=="yes"]
        print(f"linha {k+1:3d} {dv[k][0]:>14} {','.join(r[:7]):38} extremo={r[-1]:3} | outlier em: {out} | extremo em: {ext}")
