# Perfil descritivo da base glass.arff (estatísticas descritivas, não modelos).
from scipy.io import arff
import pandas as pd

dados, meta = arff.loadarff("dados/glass.arff")
df = pd.DataFrame(dados)
df["Type"] = df["Type"].str.decode("utf-8")
X = df.drop(columns="Type")

perfil = pd.DataFrame({
    "min": X.min(), "max": X.max(), "media": X.mean(), "mediana": X.median(),
    "Q1": X.quantile(.25), "Q3": X.quantile(.75),
    "zeros_%": (X == 0).mean() * 100,
    "assimetria": X.skew(),
})
q1, q3 = X.quantile(.25), X.quantile(.75); iqr = q3 - q1
# Extremos pela regra de 3*IQR (mesma ideia do filtro InterquartileRange, fator de extremo padrão 6? -> usamos 3 só como triagem)
perfil["fora_1.5IQR"] = ((X < q1 - 1.5*iqr) | (X > q3 + 1.5*iqr)).sum()
pd.set_option("display.width", 200)
print(perfil.round(3))
print("\nSoma dos óxidos (deveria ser ~100%):"); print((X.drop(columns="RI").sum(axis=1)).describe().round(2))
print("\nLinhas duplicadas (atributos químicos):", X.duplicated().sum())
print("\nDistribuição da classe Type (só para verificação posterior):"); print(df["Type"].value_counts())
print("\nCorrelações |r|>0.5:")
c = X.corr()
for i in c.columns:
    for j in c.columns:
        if i < j and abs(c.loc[i,j]) > 0.5: print(f"  {i}-{j}: {c.loc[i,j]:.2f}")
