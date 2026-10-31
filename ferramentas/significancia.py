"""Compara dois classificadores do Weka com o teste t corrigido de Nadeau-Bengio."""

import argparse
import math
import re
import shlex
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from scipy.stats import t as student_t

from weka_runner import JAVA, PASTA_PROJETO, WEKA_JAR, _resolver_arquivo_arff


NUM_PARTES = 10
CLASSIFICADOR_CUSTO = "weka.classifiers.meta.CostSensitiveClassifier"


def _executar(comando):
    """Executa um comando Weka e propaga sua saída em caso de erro."""
    processo = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
    )
    if processo.returncode != 0:
        raise RuntimeError(
            "O Weka terminou com código {}.\nComando: {}\n{}".format(
                processo.returncode,
                subprocess.list2cmdline(comando),
                processo.stdout,
            )
        )
    return processo.stdout


def _analisar_custo(texto):
    """Converte a matriz informada no CLI para números e para a sintaxe do Weka."""
    try:
        linhas = [
            [float(valor) for valor in linha.split()]
            for linha in texto.split(";")
        ]
    except ValueError as erro:
        raise ValueError(
            'Matriz de custo inválida. Use o formato "0 1; 5 0".'
        ) from erro

    if not linhas or any(not linha for linha in linhas):
        raise ValueError("A matriz de custo não pode conter linhas vazias.")
    if any(len(linha) != len(linhas) for linha in linhas):
        raise ValueError("A matriz de custo precisa ser quadrada.")
    if any(not math.isfinite(valor) or valor < 0 for linha in linhas for valor in linha):
        raise ValueError("Os custos devem ser números finitos e não negativos.")

    texto_weka = "[{}]".format(
        "; ".join(" ".join(str(valor) for valor in linha) for linha in linhas)
    )
    return linhas, texto_weka


def _extrair_matriz_teste(saida):
    """Lê somente a matriz que aparece depois do cabeçalho de teste do Weka."""
    inicio_bloco = saida.rfind("=== Error on test data ===")
    if inicio_bloco == -1:
        raise ValueError("A saída do Weka não contém o bloco 'Error on test data'.")

    inicio_matriz = saida.find("=== Confusion Matrix ===", inicio_bloco)
    if inicio_matriz == -1:
        raise ValueError(
            "Não foi encontrada matriz de confusão dentro do bloco de teste do Weka."
        )

    bloco = saida[inicio_matriz:].split("=== Confusion Matrix ===", 1)[1]
    linhas = []
    classes = []
    for linha in bloco.splitlines():
        correspondencia = re.match(
            r"^\s*(\d+(?:\s+\d+)*)\s+\|\s+\S+\s*=\s*(.*?)\s*$", linha
        )
        if correspondencia:
            linhas.append([int(valor) for valor in correspondencia.group(1).split()])
            classes.append(correspondencia.group(2).strip())
        elif linhas and linha.strip():
            break

    if not linhas or len(linhas) != len(classes):
        raise ValueError("Não foi possível interpretar a matriz de confusão do Weka.")
    if any(len(linha) != len(linhas) for linha in linhas):
        raise ValueError("A matriz de confusão do Weka não é quadrada.")
    if len(set(classes)) != len(classes):
        raise ValueError("A saída do Weka contém nomes de classe duplicados.")

    return classes, linhas


def _calcular_metricas(classes, matriz, positiva, custo):
    total = sum(sum(linha) for linha in matriz)
    if total == 0:
        raise ValueError("Uma das partições de teste não contém instâncias.")
    metricas = {"acuracia": sum(matriz[i][i] for i in range(len(matriz))) / total}

    if positiva is not None:
        if positiva not in classes:
            raise ValueError(
                "A classe positiva {!r} não está entre as classes {}.".format(
                    positiva, ", ".join(classes)
                )
            )
        indice = classes.index(positiva)
        verdadeiros_positivos = matriz[indice][indice]
        reais_positivos = sum(matriz[indice])
        previstos_positivos = sum(linha[indice] for linha in matriz)
        recall = (
            verdadeiros_positivos / reais_positivos if reais_positivos else None
        )
        precisao = (
            verdadeiros_positivos / previstos_positivos
            if previstos_positivos
            else None
        )
        if precisao is None or recall is None:
            f1 = None
        elif precisao + recall:
            f1 = 2 * precisao * recall / (precisao + recall)
        else:
            f1 = 0.0
        metricas.update(
            {
                "recall_{}".format(positiva): recall,
                "precisao_{}".format(positiva): precisao,
                "f1_{}".format(positiva): f1,
            }
        )

    if custo is not None:
        if len(custo) != len(matriz):
            raise ValueError(
                "A matriz de custo tem dimensão {}, mas o Weka encontrou {} classes."
                .format(len(custo), len(matriz))
            )
        custo_total = sum(
            matriz[real][prevista] * custo[real][prevista]
            for real in range(len(matriz))
            for prevista in range(len(matriz))
        )
        metricas["custo_total"] = custo_total

    return metricas, total


def _comando_classificador(classificador, opcoes, treino, teste, texto_custo):
    comando = [JAVA, "-cp", WEKA_JAR]
    if texto_custo is None:
        comando.append(classificador)
        comando.extend(opcoes)
        comando.extend(
            ["-t", str(treino), "-T", str(teste), "-o", "-c", "last"]
        )
    else:
        comando.extend(
            [
                CLASSIFICADOR_CUSTO,
                "-t",
                str(treino),
                "-T",
                str(teste),
                "-o",
                "-c",
                "last",
                "-cost-matrix",
                texto_custo,
                "-W",
                classificador,
                "--",
            ]
        )
        comando.extend(opcoes)
    return comando


def _formatar_numero(valor, casas=6):
    if valor is None:
        return "n/a"
    if isinstance(valor, str):
        return valor
    return "{:.{}f}".format(valor, casas)


def _resumir_metricas(valores_a, valores_b, graus_liberdade):
    metricas = []
    for chave in valores_a[0]:
        serie_a = [linha[chave] for linha in valores_a]
        serie_b = [linha[chave] for linha in valores_b]
        diferencas = [
            a - b
            for a, b in zip(serie_a, serie_b)
            if a is not None and b is not None
        ]
        estatisticas_validas = (
            len(diferencas) == len(serie_a)
            and all(valor is not None for valor in serie_a + serie_b)
        )
        media_a = statistics.mean(serie_a) if all(v is not None for v in serie_a) else None
        media_b = statistics.mean(serie_b) if all(v is not None for v in serie_b) else None
        desvio_a = (
            statistics.stdev(serie_a)
            if len(serie_a) > 1 and all(v is not None for v in serie_a)
            else (0.0 if len(serie_a) == 1 and serie_a[0] is not None else None)
        )
        desvio_b = (
            statistics.stdev(serie_b)
            if len(serie_b) > 1 and all(v is not None for v in serie_b)
            else (0.0 if len(serie_b) == 1 and serie_b[0] is not None else None)
        )
        media_diferenca = statistics.mean(diferencas) if diferencas else None

        t_calculado = None
        p_valor = None
        if not estatisticas_validas:
            conclusao = "não calculável (métrica indefinida em alguma parte)"
        elif not diferencas:
            conclusao = "não calculável (sem diferenças pareadas)"
        else:
            variancia = statistics.variance(diferencas) if len(diferencas) > 1 else 0
            if variancia == 0:
                t_calculado = "não calculável: variância zero"
                if media_diferenca == 0:
                    conclusao = "empate técnico"
                else:
                    conclusao = "não calculável (variância zero)"
            else:
                erro_padrao = math.sqrt(
                    (1 / len(diferencas) + 1 / 9) * variancia
                )
                t_calculado = media_diferenca / erro_padrao
                p_valor = float(
                    2 * student_t.sf(abs(t_calculado), graus_liberdade)
                )
                if p_valor >= 0.05:
                    conclusao = "empate técnico"
                elif (media_diferenca > 0) == (chave != "custo_total"):
                    conclusao = "diferença significativa (A melhor)"
                else:
                    conclusao = "diferença significativa (B melhor)"

        metricas.append(
            (
                chave,
                media_a,
                desvio_a,
                media_b,
                desvio_b,
                media_diferenca,
                t_calculado,
                p_valor,
                conclusao,
            )
        )
    return metricas


def _montar_relatorio(
    arquivo_arff,
    classificador_a,
    opcoes_a,
    classificador_b,
    opcoes_b,
    repeticoes,
    positiva,
    custo,
    texto_custo,
    tamanhos_teste,
    valores_a,
    valores_b,
    comandos_exemplo,
):
    linhas = [
        "Comparação de classificadores — teste t pareado corrigido de Nadeau-Bengio",
        "Arquivo ARFF: {}".format(arquivo_arff),
        "Classificador A: {} {}".format(classificador_a, " ".join(opcoes_a)).strip(),
        "Classificador B: {} {}".format(classificador_b, " ".join(opcoes_b)).strip(),
        "Matriz de custo: {}".format(texto_custo or "não informada"),
        "Classe positiva: {}".format(positiva or "não informada"),
        "Repetições: {}; partes por repetição: {}; total de pares: {}".format(
            repeticoes, NUM_PARTES, repeticoes * NUM_PARTES
        ),
        "Sementes: 1..{}; proporção n_teste/n_treino usada: 1/9".format(repeticoes),
        "",
        "Exemplos dos comandos Weka executados:",
    ]
    linhas.extend(
        subprocess.list2cmdline(comando) for comando in comandos_exemplo
    )
    linhas.extend(["", "Tamanhos das partes de teste (por repetição):"])
    for repeticao, tamanhos in enumerate(tamanhos_teste, start=1):
        linhas.append(
            "Repetição {}/{}: {}; soma={}".format(
                repeticao,
                repeticoes,
                ", ".join(str(tamanho) for tamanho in tamanhos),
                sum(tamanhos),
            )
        )
    linhas.extend(
        [
            "",
            "Resumo por métrica (A - B; custo: menor é melhor):",
            "| Métrica | Média A | DP A | Média B | DP B | Dif. média | t | p bilateral | Conclusão (5%) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    graus_liberdade = repeticoes * NUM_PARTES - 1
    for resultado in _resumir_metricas(valores_a, valores_b, graus_liberdade):
        (
            chave,
            media_a,
            desvio_a,
            media_b,
            desvio_b,
            media_diferenca,
            t_calculado,
            p_valor,
            conclusao,
        ) = resultado
        linhas.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                chave,
                _formatar_numero(media_a),
                _formatar_numero(desvio_a),
                _formatar_numero(media_b),
                _formatar_numero(desvio_b),
                _formatar_numero(media_diferenca),
                _formatar_numero(t_calculado),
                _formatar_numero(p_valor),
                conclusao,
            )
        )
    return "\n".join(linhas) + "\n"


def comparar(
    arquivo_arff,
    classificador_a,
    opcoes_a=(),
    classificador_b=None,
    opcoes_b=(),
    custo_texto=None,
    positiva=None,
    repeticoes=10,
):
    """Executa folds repetidos no Weka e compara as métricas pareadas."""
    if repeticoes < 1:
        raise ValueError("--repeticoes deve ser pelo menos 1.")
    caminho_dados = _resolver_arquivo_arff(arquivo_arff)
    custo, texto_custo = (
        _analisar_custo(custo_texto) if custo_texto is not None else (None, None)
    )
    opcoes_a = list(opcoes_a)
    opcoes_b = list(opcoes_b)
    valores_a = []
    valores_b = []
    tamanhos_teste = []
    comandos_exemplo = []

    with tempfile.TemporaryDirectory(prefix="weka_significancia_") as pasta_temp:
        pasta_temp = Path(pasta_temp)
        for repeticao in range(1, repeticoes + 1):
            print(
                "Repetição {}/{}".format(repeticao, repeticoes),
                file=sys.stderr,
                flush=True,
            )
            tamanhos_da_repeticao = []
            for parte in range(1, NUM_PARTES + 1):
                teste = pasta_temp / "teste_r{}_f{}.arff".format(repeticao, parte)
                treino = pasta_temp / "treino_r{}_f{}.arff".format(repeticao, parte)
                comando_teste = [
                    JAVA,
                    "-cp",
                    WEKA_JAR,
                    "weka.filters.supervised.instance.StratifiedRemoveFolds",
                    "-i",
                    str(caminho_dados),
                    "-o",
                    str(teste),
                    "-c",
                    "last",
                    "-N",
                    str(NUM_PARTES),
                    "-F",
                    str(parte),
                    "-S",
                    str(repeticao),
                ]
                comando_treino = comando_teste.copy()
                comando_treino[comando_treino.index(str(teste))] = str(treino)
                comando_treino.append("-V")
                _executar(comando_teste)
                _executar(comando_treino)

                comando_a = _comando_classificador(
                    classificador_a, opcoes_a, treino, teste, texto_custo
                )
                comando_b = _comando_classificador(
                    classificador_b, opcoes_b, treino, teste, texto_custo
                )
                saida_a = _executar(comando_a)
                saida_b = _executar(comando_b)
                classes_a, matriz_a = _extrair_matriz_teste(saida_a)
                classes_b, matriz_b = _extrair_matriz_teste(saida_b)
                if classes_a != classes_b:
                    raise ValueError(
                        "A ordem das classes diferiu entre os classificadores: "
                        "{} vs {}.".format(classes_a, classes_b)
                    )
                metricas_a, tamanho_a = _calcular_metricas(
                    classes_a, matriz_a, positiva, custo
                )
                metricas_b, tamanho_b = _calcular_metricas(
                    classes_b, matriz_b, positiva, custo
                )
                if tamanho_a != tamanho_b:
                    raise ValueError(
                        "Os classificadores avaliaram tamanhos de teste diferentes."
                    )
                tamanhos_da_repeticao.append(tamanho_a)
                valores_a.append(metricas_a)
                valores_b.append(metricas_b)
                if not comandos_exemplo:
                    comandos_exemplo.extend(
                        [comando_teste, comando_treino, comando_a, comando_b]
                    )
            tamanhos_teste.append(tamanhos_da_repeticao)

    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    relatorio = _montar_relatorio(
        caminho_dados,
        classificador_a,
        opcoes_a,
        classificador_b,
        opcoes_b,
        repeticoes,
        positiva,
        custo,
        texto_custo,
        tamanhos_teste,
        valores_a,
        valores_b,
        comandos_exemplo,
    )
    pasta_resultados = PASTA_PROJETO / "resultados"
    pasta_resultados.mkdir(parents=True, exist_ok=True)
    caminho_saida = pasta_resultados / "{}_significancia.txt".format(data_hora)
    caminho_saida.write_text(relatorio, encoding="utf-8", newline="\n")
    print(relatorio, end="")
    print("Relatório salvo em: {}".format(caminho_saida))
    return caminho_saida


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compara dois classificadores do Weka com o teste t corrigido."
    )
    parser.add_argument("arquivo_arff")
    parser.add_argument("--a", required=True, dest="classificador_a")
    parser.add_argument("--opcoes-a", default="")
    parser.add_argument("--b", required=True, dest="classificador_b")
    parser.add_argument("--opcoes-b", default="")
    parser.add_argument("--custo")
    parser.add_argument("--positiva")
    parser.add_argument("--repeticoes", type=int, default=10)
    argumentos = parser.parse_args(argv)

    try:
        comparar(
            argumentos.arquivo_arff,
            argumentos.classificador_a,
            shlex.split(argumentos.opcoes_a),
            argumentos.classificador_b,
            shlex.split(argumentos.opcoes_b),
            argumentos.custo,
            argumentos.positiva,
            argumentos.repeticoes,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as erro:
        print(erro, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
