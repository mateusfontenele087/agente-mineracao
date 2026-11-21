# Lê as saídas do Weka (só o bloco de validação cruzada) e monta a tabela comparativa.
# Nada é inventado: acurácia, kappa e matriz vêm do Weka; F1 macro e IC são contas sobre esses números.
import sys, re, math, glob
from datetime import datetime

def ler(arq):
    txt = open(arq, encoding="utf-8").read()
    cmd = txt.splitlines()[0].replace("Comando executado: ", "")
    cv = txt[txt.index("=== Stratified cross-validation ==="):]   # só a validação cruzada
    acc = float(re.search(r"Correctly Classified Instances\s+\d+\s+([\d.]+)", cv).group(1)) / 100
    n = int(re.search(r"Total Number of Instances\s+(\d+)", cv).group(1))
    kappa = float(re.search(r"Kappa statistic\s+([-\d.]+)", cv).group(1))
    # Matriz de confusão: linhas = classe real, colunas = prevista
    bloco = cv.split("=== Confusion Matrix ===")[1]
    matriz, classes = [], []
    for l in bloco.splitlines():
        m = re.match(r"^\s*([\d\s]+?)\s+\|\s+\S+\s*=\s*(.*)$", l)
        if m:
            matriz.append([int(v) for v in m.group(1).split()]); classes.append(m.group(2).strip())
    # F1 por classe; classe nunca prevista -> F1 = 0 (precisão indefinida, recall 0)
    f1s = {}
    for i, c in enumerate(classes):
        vp = matriz[i][i]; real = sum(matriz[i]); prev = sum(r[i] for r in matriz)
        p = vp / prev if prev else 0; r = vp / real if real else 0
        f1s[c] = 2*p*r/(p+r) if p+r else 0.0
    macro = sum(f1s.values()) / len(f1s)
    # IC 95% de Wilson para a acurácia
    z = 1.96; centro = (acc + z*z/(2*n)) / (1 + z*z/n)
    meia = z*math.sqrt(acc*(1-acc)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return dict(cmd=cmd, acc=acc, ic=(centro-meia, centro+meia), kappa=kappa, macro=macro,
                f1s=f1s, matriz=matriz, classes=classes, txt=txt)

arquivos = sys.argv[1:]
saida = []
saida.append(f"{'modelo':<40}{'acurácia':>9}  {'IC95%':<15}{'kappa':>7}{'F1 macro':>10}")
res = {}
for a in arquivos:
    r = ler(a); nome = r["cmd"].split()[3].split(".")[-1] + " " + " ".join(r["cmd"].split()[4:]).split(" -t ")[0]
    if "ZeroR" in a: nome = "ZeroR"
    res[nome] = r
    saida.append(f"{nome:<40}{r['acc']:>9.4f}  [{r['ic'][0]:.3f}; {r['ic'][1]:.3f}]{r['kappa']:>7.3f}{r['macro']:>10.4f}")
saida.append("\nF1 por classe (validação cruzada):")
nomes = list(res)
classes = res[nomes[0]]["classes"]
saida.append(f"{'classe':<30}" + "".join(f"{n.split()[0][:10]:>11}" for n in nomes))
for c in classes:
    saida.append(f"{c:<30}" + "".join(f"{res[n]['f1s'][c]:>11.3f}" for n in nomes))
texto = "\n".join(saida)
print(texto)
arq = f"resultados/{datetime.now():%Y%m%d_%H%M%S}_soybean_tabela.txt"
open(arq, "w").write("Arquivos: " + ", ".join(arquivos) + "\n\n" + texto + "\n")
print("\nSalvo em", arq)
