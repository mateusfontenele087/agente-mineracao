"""Prepara a base hypothyroid.arff para a triagem binária de hipotireoidismo.

Decisões confirmadas pelo usuário em 21/11/2026:
- Classe binária: 'hypothyroid' (compensado, primário ou secundário) x 'negative'.
- Remover TBG (100% ausente) e TBG measured (constante).
- Remover os atributos '... measured' (indicam se o exame foi pedido, e não o
  estado da tireoide; a ausência de TSH só ocorre em negativos).
- Remover hypopituitary (um único caso 't'; não ajuda a separar as classes).
- age = 455 é impossível: vira ausente ('?'). Nada é "adivinhado".

Gera três bases (a original não é alterada):
- hypothyroid_bin.arff            -> análise principal
- hypothyroid_bin_sem_dup.arff    -> cenário alternativo: sem linhas duplicadas
- hypothyroid_bin_com_tsh.arff    -> cenário alternativo: só quem tem TSH medido

Estes passos usam regras de domínio e não aprendem nada com a distribuição dos
dados, por isso podem ser feitos antes da validação cruzada.
Uso (na raiz do projeto): python3 analises/2026-11-21_preparar_hypothyroid.py
"""

from pathlib import Path

ORIGEM = Path("dados/hypothyroid.arff")
REMOVER = {
    "TSH measured", "T3 measured", "TT4 measured", "T4U measured",
    "FTI measured", "TBG measured", "TBG", "hypopituitary",
}
POSITIVAS = {"compensated_hypothyroid", "primary_hypothyroid", "secondary_hypothyroid"}

linhas = ORIGEM.read_text(encoding="utf-8-sig").splitlines()

# 1. Separa o cabeçalho (@attribute) dos dados (@data)
cabecalho_attr = []          # linhas @attribute originais
for linha in linhas:
    if linha.strip().lower().startswith("@attribute"):
        cabecalho_attr.append(linha)
inicio = next(i for i, l in enumerate(linhas) if l.strip().lower() == "@data")
registros = [
    [v.strip() for v in l.split(",")]
    for l in linhas[inicio + 1:]
    if l.strip() and not l.lstrip().startswith("%")
]


def nome_do_atributo(linha):
    """Extrai o nome, que pode vir entre aspas e conter espaços."""
    resto = linha.strip()[len("@attribute"):].strip()
    if resto.startswith("'"):
        return resto[1:resto.index("'", 1)]
    return resto.split()[0]


nomes = [nome_do_atributo(l) for l in cabecalho_attr]
manter = [i for i, n in enumerate(nomes) if n not in REMOVER]
i_idade = nomes.index("age")

# 2. Monta os registros novos
novos = []
idades_corrigidas = 0
for r in registros:
    r = list(r)
    if r[i_idade] != "?" and float(r[i_idade]) > 110:   # idade impossível
        r[i_idade] = "?"
        idades_corrigidas += 1
    r[-1] = "hypothyroid" if r[-1] in POSITIVAS else "negative"
    novos.append([r[i] for i in manter])

# 3. Novo cabeçalho: mesmos atributos mantidos, classe redefinida
attrs_saida = [cabecalho_attr[i] for i in manter[:-1]]
attrs_saida.append("@attribute 'Class' { negative, hypothyroid}")
i_tsh = [nomes[i] for i in manter].index("TSH")


def gravar(nome, regs, descricao):
    texto = [
        f"% Gerado por analises/2026-11-21_preparar_hypothyroid.py a partir de {ORIGEM}",
        f"% {descricao}",
        "@relation hypothyroid_bin",
        "",
        *attrs_saida,
        "",
        "@data",
        *[",".join(r) for r in regs],
    ]
    Path("dados", nome).write_text("\n".join(texto) + "\n", encoding="utf-8")
    pos = sum(r[-1] == "hypothyroid" for r in regs)
    print(f"{nome}: {len(regs)} registros, {pos} positivos, {len(regs) - pos} negativos")


# Base principal
gravar("hypothyroid_bin.arff", novos, "Base principal (binária).")

# Cenário: sem duplicatas (mantém a primeira ocorrência de cada linha idêntica)
vistos, sem_dup = set(), []
for r in novos:
    if tuple(r) not in vistos:
        vistos.add(tuple(r))
        sem_dup.append(r)
print(f"Duplicatas removidas: {len(novos) - len(sem_dup)}")
gravar("hypothyroid_bin_sem_dup.arff", sem_dup, "Cenário: linhas duplicadas removidas.")

# Cenário: só registros com TSH medido
com_tsh = [r for r in novos if r[i_tsh] != "?"]
gravar("hypothyroid_bin_com_tsh.arff", com_tsh, "Cenário: apenas registros com TSH medido.")

print(f"Idades impossíveis marcadas como ausentes: {idades_corrigidas}")
print("Atributos removidos:", sorted(REMOVER))
