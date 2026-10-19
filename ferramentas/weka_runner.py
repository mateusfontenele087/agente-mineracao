"""Executa classificadores do Weka e registra os resultados."""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


JAVA = "java"
WEKA_JAR = r"C:\Program Files\Weka-3-8-7\weka.jar"
PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "dados"
PASTA_RESULTADOS = "resultados"


def _resolver_arquivo_arff(arquivo_arff):
    """Usa caminhos absolutos diretamente e procura caminhos relativos em dados/."""
    caminho = Path(arquivo_arff)
    if not caminho.is_absolute():
        caminho = PASTA_DADOS / caminho

    if not caminho.is_file():
        raise FileNotFoundError("Arquivo ARFF não encontrado: {}".format(caminho))

    return caminho.resolve()


def _salvar_saida(saida, comando, identificador, data_hora):
    pasta_resultados = PASTA_PROJETO / PASTA_RESULTADOS
    pasta_resultados.mkdir(parents=True, exist_ok=True)

    nome_seguro = re.sub(r"[^A-Za-z0-9_-]+", "_", identificador)
    caminho_saida = pasta_resultados / "{}_{}.txt".format(data_hora, nome_seguro)
    with caminho_saida.open("w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write("Comando executado: {}\n\n".format(subprocess.list2cmdline(comando)))
        arquivo.write(saida)
        if saida and not saida.endswith("\n"):
            arquivo.write("\n")

    return caminho_saida


def _executar_weka(arquivo_arff, classificador, opcoes, identificador, data_hora):
    caminho_dados = _resolver_arquivo_arff(arquivo_arff)
    comando = [
        JAVA,
        "-cp",
        WEKA_JAR,
        classificador,
        "-t",
        str(caminho_dados),
        "-x",
        "10",
        "-s",
        "1",
    ]
    comando.extend(opcoes)

    processo = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    saida = processo.stdout
    caminho_saida = _salvar_saida(saida, comando, identificador, data_hora)

    if processo.returncode != 0:
        print(saida, file=sys.stderr, end="" if saida.endswith("\n") else "\n")
        raise RuntimeError(
            "O Weka terminou com código {}. A saída foi salva em: {}".format(
                processo.returncode, caminho_saida
            )
        )

    return saida


def classificar(arquivo_arff, classificador, opcoes=()):
    """Treina e avalia um classificador por validação cruzada de 10 partes."""
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return _executar_weka(
        arquivo_arff,
        classificador,
        list(opcoes),
        "classificador",
        data_hora,
    )


def comparar_com_baseline(arquivo_arff, classificador, opcoes=()):
    """Executa ZeroR e o classificador escolhido, retornando as duas saídas."""
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    saida_baseline = _executar_weka(
        arquivo_arff,
        "weka.classifiers.rules.ZeroR",
        [],
        "baseline_ZeroR",
        data_hora,
    )
    saida_classificador = _executar_weka(
        arquivo_arff,
        classificador,
        list(opcoes),
        "classificador",
        data_hora,
    )
    return saida_baseline, saida_classificador


def resumir(arquivo_arff):
    """Exibe e salva o resumo dos atributos produzido pelo Weka."""
    caminho_dados = _resolver_arquivo_arff(arquivo_arff)
    comando = [
        JAVA,
        "-cp",
        WEKA_JAR,
        "weka.core.Instances",
        str(caminho_dados),
    ]
    processo = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    saida = processo.stdout
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    caminho_saida = _salvar_saida(saida, comando, "resumo", data_hora)

    if processo.returncode != 0:
        print(saida, file=sys.stderr, end="" if saida.endswith("\n") else "\n")
        raise RuntimeError(
            "O Weka terminou com código {}. A saída foi salva em: {}".format(
                processo.returncode, caminho_saida
            )
        )

    return saida


def main(argv=None):
    """Executa os subcomandos da interface de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Executa tarefas de mineração de dados com o Weka."
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    parser_resumo = subparsers.add_parser(
        "resumo", help="mostra o resumo dos atributos de uma base ARFF"
    )
    parser_resumo.add_argument("arquivo_arff")

    parser_comparar = subparsers.add_parser(
        "comparar", help="compara um classificador com a baseline ZeroR"
    )
    parser_comparar.add_argument("arquivo_arff")
    parser_comparar.add_argument("classificador")
    parser_comparar.add_argument("opcoes", nargs=argparse.REMAINDER)

    argumentos = parser.parse_args(argv)

    try:
        if argumentos.comando == "resumo":
            print(resumir(argumentos.arquivo_arff), end="")
        else:
            saida_baseline, saida_classificador = comparar_com_baseline(
                argumentos.arquivo_arff,
                argumentos.classificador,
                argumentos.opcoes,
            )
            print("=== Resultado do baseline ZeroR ===")
            print(saida_baseline)
            print("=== Resultado do classificador {} ===".format(argumentos.classificador))
            print(saida_classificador)
    except (FileNotFoundError, RuntimeError) as erro:
        print(erro, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
