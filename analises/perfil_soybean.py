# Perfil descritivo da base soybean.arff (só descreve os dados; nenhum modelo aqui).
import pandas as pd
from datetime import datetime
import io, contextlib

# Leitura simples do .arff: nomes em "@attribute", valores após "@data"
nomes, linhas, na_secao_dados = [], [], False
for linha in open("dados/soybean.arff"):
    linha = linha.strip()
    if not linha or linha.startswith("%"):
        continue
    if linha.lower().startswith("@attribute"):
        nomes.append(linha.split()[1])
    elif linha.lower().startswith("@data"):
        na_secao_dados = True
    elif na_secao_dados:
        linhas.append([v.strip().strip("'") for v in linha.split(",")])
df = pd.DataFrame(linhas, columns=nomes).replace("?", None)  # '?' = ausente

saida = io.StringIO()
with contextlib.redirect_stdout(saida):
    print("Registros:", len(df), "| Atributos:", df.shape[1])
    print("\n== Distribuição da classe ==")
    dist = df["class"].value_counts()
    print(pd.DataFrame({"n": dist, "%": (dist / len(df) * 100).round(1)}))
    print("Razão maior/menor classe:", round(dist.max() / dist.min(), 1))

    print("\n== Registros com algum ausente, por classe ==")
    tem_aus = df.drop(columns="class").isna().any(axis=1)
    print(pd.DataFrame({"com_ausente": tem_aus.groupby(df["class"]).sum(),
                        "total": df["class"].value_counts()}).query("com_ausente > 0"))
    print("Total de registros com algum ausente:", tem_aus.sum())

    print("\n== Atributos quase constantes (valor mais frequente > 95% dos não ausentes) ==")
    for c in df.columns[:-1]:
        vc = df[c].value_counts(normalize=True)
        if vc.iloc[0] > 0.95:
            print(f"{c}: '{vc.index[0]}' em {vc.iloc[0]*100:.1f}%")

    print("\n== Valor mais raro por atributo (contagem < 10) ==")
    for c in df.columns[:-1]:
        vc = df[c].value_counts()
        if vc.min() < 10:
            print(f"{c}: '{vc.idxmin()}' aparece {vc.min()} vezes")

    print("\n== Duplicatas ==")
    dup_total = df.fillna("?").astype(str).duplicated(keep=False)
    print("Registros envolvidos em duplicatas exatas (com classe):", dup_total.sum())
    print("Cópias excedentes:", df.fillna("?").astype(str).duplicated().sum())
    x = df.drop(columns="class").fillna("?").astype(str)
    grupos = df.assign(chave=x.apply("|".join, axis=1)).groupby("chave")["class"].nunique()
    print("Conjuntos de atributos idênticos com classes DIFERENTES:", (grupos > 1).sum())
    print("\nDuplicatas por classe:")
    print(df[df.fillna("?").astype(str).duplicated()]["class"].value_counts())

texto = saida.getvalue()
print(texto)
arq = f"resultados/{datetime.now():%Y%m%d_%H%M%S}_soybean_perfil.txt"
open(arq, "w").write(texto)
print("Salvo em", arq)
