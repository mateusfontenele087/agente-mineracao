"""Testes de aceite das ferramentas do agente.

Rodar antes de usar qualquer ferramenta alterada:
    python ferramentas/testes_aceite.py

Os testes 1 a 3 são de conta (não chamam o Weka) e rodam em segundos.
Os testes 4 a 6 chamam o Weka e levam alguns minutos; os relatórios que eles
geram vão para resultados/, como qualquer execução da ferramenta.
"""

import contextlib
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import significancia  # noqa: E402
import weka_runner  # noqa: E402

FALHAS = []


def verificar(condicao, mensagem):
    """Registra o resultado de uma verificação e mostra na tela."""
    print(("  ok    " if condicao else "  FALHOU ") + mensagem)
    if not condicao:
        FALHAS.append(mensagem)


def f1(vp, reais, previstos):
    """F1 de uma classe, calculado à mão a partir das contagens."""
    precisao = vp / previstos if previstos else 0.0
    recall = vp / reais if reais else 0.0
    return 2 * precisao * recall / (precisao + recall) if precisao + recall else 0.0


def linha_do_relatorio(caminho, metrica):
    """Lê a linha de uma métrica na tabela do relatório de significancia.py."""
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        if linha.startswith("| {} |".format(metrica)):
            partes = [p.strip() for p in linha.strip("|").split("|")]
            return {
                "media_a": float(partes[1]),
                "media_b": float(partes[3]),
                "diferenca": float(partes[5]),
                "conclusao": partes[8],
            }
    raise AssertionError("Métrica {} não encontrada em {}".format(metrica, caminho))


def comparar_em_silencio(*args, **kwargs):
    """Roda significancia.comparar sem despejar o relatório inteiro na tela."""
    with contextlib.redirect_stdout(io.StringIO()):
        return significancia.comparar(*args, **kwargs)


# ---------------------------------------------------------------------------
print("Teste 1: F1 macro numa matriz 3x3 conferida à mão")
classes = ["a", "b", "c"]
matriz = [[5, 1, 0], [2, 3, 1], [0, 0, 4]]  # linhas = classe real
esperado = (f1(5, 6, 7) + f1(3, 6, 4) + f1(4, 4, 5)) / 3
metricas, _ = significancia._calcular_metricas(classes, matriz, None, None, True)
verificar(abs(metricas["f1_macro"] - esperado) < 1e-12,
          "f1_macro = {:.6f} (esperado {:.6f})".format(metricas["f1_macro"], esperado))

print("Teste 2: em base binária, F1 macro = média do F1 das duas classes")
matriz = [[40, 10], [5, 45]]
metricas_pos, _ = significancia._calcular_metricas(["x", "y"], matriz, "y", None, True)
metricas_neg, _ = significancia._calcular_metricas(["x", "y"], matriz, "x", None, False)
media = (metricas_pos["f1_y"] + metricas_neg["f1_x"]) / 2
verificar(abs(metricas_pos["f1_macro"] - media) < 1e-12,
          "f1_macro = {:.6f}; média dos F1 por classe = {:.6f}".format(
              metricas_pos["f1_macro"], media))

print("Teste 3: classe ausente na parte de teste e nunca prevista fica de fora da média")
matriz = [[5, 1, 0], [2, 3, 0], [0, 0, 0]]
esperado = (f1(5, 6, 7) + f1(3, 5, 4)) / 2
metricas, _ = significancia._calcular_metricas(classes, matriz, None, None, True)
verificar(abs(metricas["f1_macro"] - esperado) < 1e-12,
          "f1_macro = {:.6f} (esperado {:.6f}, média de 2 classes)".format(
              metricas["f1_macro"], esperado))

print("Teste 4: weka_runner reproduz o valor do README (NaiveBayes na credit-g, AUC 0,787)")
with contextlib.redirect_stdout(io.StringIO()) as saida:
    weka_runner.main(["comparar", "credit-g.arff", "weka.classifiers.bayes.NaiveBayes"])
texto = saida.getvalue()
bloco = texto[texto.rfind("Stratified cross-validation"):]
auc = re.search(r"Weighted Avg\.\s+(?:\S+\s+){6}(\S+)", bloco)
verificar(auc is not None and auc.group(1) == "0.787",
          "AUC média ponderada = {}".format(auc.group(1) if auc else "não encontrada"))

print("Teste 5: classificador contra ele mesmo, com --f1-macro, dá diferença zero e empate")
caminho = comparar_em_silencio(
    "soybean.arff", "weka.classifiers.bayes.NaiveBayes", [],
    "weka.classifiers.bayes.NaiveBayes", [], repeticoes=2, f1_macro=True)
linha = linha_do_relatorio(caminho, "f1_macro")
verificar(linha["diferenca"] == 0.0 and linha["conclusao"] == "empate técnico",
          "diferença = {}; conclusão = {}".format(linha["diferenca"], linha["conclusao"]))

print("Teste 6: --sem-envelope com o envelope escrito à mão = envelope feito pela ferramenta")
custo = "0 1; 3 0"
envelope = ["-cost-matrix", "[0.0 1.0; 3.0 0.0]", "-W"]
manual = comparar_em_silencio(
    "breast-cancer.arff",
    "weka.classifiers.meta.CostSensitiveClassifier", envelope + ["weka.classifiers.trees.J48"],
    "weka.classifiers.meta.CostSensitiveClassifier", envelope + ["weka.classifiers.bayes.NaiveBayes"],
    custo_texto=custo, positiva="recurrence-events", repeticoes=2, sem_envelope=True)
automatico = comparar_em_silencio(
    "breast-cancer.arff",
    "weka.classifiers.trees.J48", [],
    "weka.classifiers.bayes.NaiveBayes", [],
    custo_texto=custo, positiva="recurrence-events", repeticoes=2)
linha_manual = linha_do_relatorio(manual, "custo_total")
linha_auto = linha_do_relatorio(automatico, "custo_total")
verificar(linha_manual == linha_auto,
          "custo médio J48/NB com envelope manual {:.2f}/{:.2f}; automático {:.2f}/{:.2f}".format(
              linha_manual["media_a"], linha_manual["media_b"],
              linha_auto["media_a"], linha_auto["media_b"]))

# ---------------------------------------------------------------------------
print()
if FALHAS:
    print("{} teste(s) falharam.".format(len(FALHAS)))
    sys.exit(1)
print("Todos os testes passaram.")
