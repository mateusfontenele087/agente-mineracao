import random
import re
from pathlib import Path


PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_ARFF = PASTA_PROJETO / "dados" / "supermarket.arff"
ARQUIVO_SAIDA = Path(__file__).with_suffix(".txt")

REGRAS = [
    (
        ("bread and cake", "canned vegetables", "frozen foods"),
        ("baking needs", "biscuits", "vegetables"),
    ),
    (
        ("canned vegetables", "frozen foods"),
        ("biscuits", "margarine", "vegetables"),
    ),
    (
        ("bread and cake", "juice-sat-cord-ms", "biscuits"),
        ("party snack foods", "tissues-paper prd", "fruit"),
    ),
    (
        ("juice-sat-cord-ms", "sauces-gravy-pkle", "fruit"),
        ("bread and cake", "party snack foods", "vegetables"),
    ),
    (
        ("laundry needs", "party snack foods"),
        ("sauces-gravy-pkle", "tissues-paper prd"),
    ),
]


def carregar_base(caminho):
    atributos = []
    transacoes = []
    lendo_dados = False

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("%"):
            continue

        if not lendo_dados:
            if linha.lower().startswith("@attribute"):
                correspondencia = re.match(
                    r"@attribute\s+('.*?'|\".*?\"|\S+)",
                    linha,
                    re.IGNORECASE,
                )
                atributos.append(correspondencia.group(1).strip("'\""))
            elif linha.lower() == "@data":
                lendo_dados = True
        else:
            transacoes.append([valor.strip() for valor in linha.split(",")])

    indice_total = atributos.index("total")
    atributos.pop(indice_total)
    transacoes = [
        (
            transacao[:indice_total] + transacao[indice_total + 1 :],
            transacao[indice_total],
        )
        for transacao in transacoes
    ]
    return atributos, transacoes


def calcular_metricas(atributos, transacoes, antecedente, consequente):
    indices = {nome: atributos.index(nome) for nome in antecedente + consequente}
    contagem_antecedente = 0
    contagem_conjunto = 0
    contagem_consequente = 0

    for transacao in transacoes:
        tem_antecedente = all(
            transacao[indices[nome]] == "t" for nome in antecedente
        )
        tem_consequente = all(
            transacao[indices[nome]] == "t" for nome in consequente
        )
        contagem_antecedente += tem_antecedente
        contagem_consequente += tem_consequente
        contagem_conjunto += tem_antecedente and tem_consequente

    confianca = contagem_conjunto / contagem_antecedente
    suporte_consequente = contagem_consequente / len(transacoes)
    lift = confianca / suporte_consequente
    suporte = contagem_conjunto / len(transacoes)
    return contagem_conjunto, suporte, confianca, lift


def main():
    atributos, transacoes = carregar_base(ARQUIVO_ARFF)
    random.Random(1).shuffle(transacoes)
    validacao = transacoes[len(transacoes) // 2 :]
    linhas_por_grupo = [
        ("geral", [transacao for transacao, _ in validacao])
    ]
    for grupo in ("low", "high"):
        linhas_por_grupo.append(
            (
                "total={}".format(grupo),
                [
                    transacao
                    for transacao, valor_total in validacao
                    if valor_total == grupo
                ],
            )
        )

    linhas = [
        "Validacao em metade reservada da base.",
        "Divisao aleatoria com semente 1; ausencias nao contam como itens.",
        "O atributo total foi excluido por nao ser um departamento.",
        "Transacoes na validacao: {}".format(len(validacao)),
        "",
    ]

    for nome_grupo, transacoes_grupo in linhas_por_grupo:
        linhas.append(nome_grupo)
        for antecedente, consequente in REGRAS:
            contagem, suporte, confianca, lift = calcular_metricas(
                atributos, transacoes_grupo, antecedente, consequente
            )
            linhas.append(
                "{} -> {} | n={} ({:.1%}) | confianca={:.3f} | lift={:.3f}".format(
                    " + ".join(antecedente),
                    " + ".join(consequente),
                    contagem,
                    suporte,
                    confianca,
                    lift,
                )
            )
        linhas.append("")

    resultado = "\n".join(linhas) + "\n"
    ARQUIVO_SAIDA.write_text(resultado, encoding="utf-8")
    print(resultado, end="")


if __name__ == "__main__":
    main()
