"""Executa K-means no Weka e valida os grupos com medidas calculadas em Python."""

import argparse
import math
import random
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

from weka_runner import JAVA, PASTA_PROJETO, WEKA_JAR, _resolver_arquivo_arff


CLUSTERER = "weka.clusterers.SimpleKMeans"
ADD_CLUSTER = "weka.filters.unsupervised.attribute.AddCluster"
REMOVE = "weka.filters.unsupervised.attribute.Remove"


def _executar(comando):
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


def _tokenizar_linha(linha):
    """Separa valores ARFF por vírgula, sem dividir valores entre aspas."""
    valores = []
    inicio = 0
    aspas = None
    escapado = False
    for indice, caractere in enumerate(linha):
        if escapado:
            escapado = False
        elif caractere == "\\" and aspas is not None:
            escapado = True
        elif aspas is not None and caractere == aspas:
            aspas = None
        elif aspas is None and caractere in ("'", '"'):
            aspas = caractere
        elif aspas is None and caractere == ",":
            valores.append(linha[inicio:indice].strip())
            inicio = indice + 1
    if aspas is not None:
        raise ValueError("Linha ARFF contém aspas sem fechamento: {}".format(linha))
    valores.append(linha[inicio:].strip())
    return valores


def _decodificar_token(token):
    token = token.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        conteudo = token[1:-1]
        return re.sub(r"\\(.)", r"\1", conteudo)
    return token


def _separar_nome_tipo(declaracao):
    declaracao = declaracao.strip()
    if not declaracao:
        raise ValueError("Declaração @attribute sem nome.")
    if declaracao[0] in ("'", '"'):
        aspas = declaracao[0]
        escapado = False
        for indice in range(1, len(declaracao)):
            caractere = declaracao[indice]
            if escapado:
                escapado = False
            elif caractere == "\\":
                escapado = True
            elif caractere == aspas:
                return (
                    _decodificar_token(declaracao[: indice + 1]),
                    declaracao[indice + 1 :].strip(),
                )
        raise ValueError("Nome de atributo ARFF sem fechamento: {}".format(declaracao))
    partes = declaracao.split(None, 1)
    if len(partes) != 2:
        raise ValueError("Declaração @attribute inválida: {}".format(declaracao))
    return partes[0], partes[1].strip()


def _ler_arff(caminho):
    linhas_cabecalho = []
    atributos = []
    linhas_dados = []
    lendo_dados = False
    with caminho.open("r", encoding="utf-8-sig", errors="replace") as arquivo:
        for linha in arquivo:
            texto = linha.strip()
            if not lendo_dados:
                linhas_cabecalho.append(linha.rstrip("\r\n"))
                correspondencia = re.match(r"(?i)^@attribute\s+(.+)$", texto)
                if correspondencia:
                    nome, tipo = _separar_nome_tipo(correspondencia.group(1))
                    tipo_minusculo = tipo.lower()
                    if tipo_minusculo in ("numeric", "real", "integer"):
                        atributos.append(
                            {"name": nome, "type": tipo, "kind": "numeric", "values": []}
                        )
                    elif tipo.startswith("{") and tipo.endswith("}"):
                        valores = [
                            _decodificar_token(valor)
                            for valor in _tokenizar_linha(tipo[1:-1])
                        ]
                        if not valores:
                            raise ValueError(
                                "Atributo nominal sem valores: {}".format(nome)
                            )
                        atributos.append(
                            {
                                "name": nome,
                                "type": tipo,
                                "kind": "nominal",
                                "values": valores,
                            }
                        )
                    else:
                        raise ValueError(
                            "Tipo de atributo não suportado para agrupamento: "
                            "{} ({})".format(nome, tipo)
                        )
                elif re.match(r"(?i)^@data\s*$", texto):
                    lendo_dados = True
                    linhas_cabecalho.pop()
                continue
            if not texto or texto.startswith("%"):
                continue
            linhas_dados.append(texto)

    if not lendo_dados:
        raise ValueError("O arquivo não contém a seção @data: {}".format(caminho))
    if not atributos:
        raise ValueError("O arquivo ARFF não contém atributos.")

    registros = []
    for numero_linha, linha in enumerate(linhas_dados, start=1):
        if linha.startswith("{") and linha.endswith("}"):
            valores = [0.0 if a["kind"] == "numeric" else a["values"][0] for a in atributos]
            for item in _tokenizar_linha(linha[1:-1]):
                partes = _tokenizar_par_colon(item)
                indice = int(partes[0])
                if indice < 0 or indice >= len(atributos):
                    raise ValueError("Índice fora dos atributos na linha ARFF {}.".format(numero_linha))
                valores[indice] = _converter_valor(partes[1], atributos[indice], numero_linha)
        else:
            tokens = _tokenizar_linha(linha)
            if len(tokens) != len(atributos):
                raise ValueError(
                    "A linha de dados {} tem {} valores; eram esperados {}.".format(
                        numero_linha, len(tokens), len(atributos)
                    )
                )
            valores = [
                _converter_valor(token, atributo, numero_linha)
                for token, atributo in zip(tokens, atributos)
            ]
        registros.append(valores)
    if not registros:
        raise ValueError("O arquivo ARFF não contém registros.")
    return linhas_cabecalho, atributos, registros


def _tokenizar_par_colon(item):
    aspas = None
    escapado = False
    for indice, caractere in enumerate(item):
        if escapado:
            escapado = False
        elif caractere == "\\" and aspas is not None:
            escapado = True
        elif aspas is not None and caractere == aspas:
            aspas = None
        elif aspas is None and caractere in ("'", '"'):
            aspas = caractere
        elif caractere == ":" and aspas is None:
            return item[:indice].strip(), item[indice + 1 :].strip()
    raise ValueError("Valor esparso ARFF inválido: {}".format(item))


def _converter_valor(token, atributo, numero_linha):
    if token.strip() == "?":
        raise ValueError(
            "Valor ausente (?) encontrado na linha {}. Trate os valores ausentes "
            "antes de executar o agrupamento.".format(numero_linha)
        )
    valor = _decodificar_token(token)
    if atributo["kind"] == "numeric":
        try:
            numero = float(valor)
        except ValueError as erro:
            raise ValueError(
                "Valor numérico inválido na linha {}: {!r}.".format(numero_linha, valor)
            ) from erro
        if not math.isfinite(numero):
            raise ValueError(
                "Valor numérico não finito na linha {}.".format(numero_linha)
            )
        return numero
    if valor not in atributo["values"]:
        raise ValueError(
            "Valor nominal {!r} não declarado para o atributo {}.".format(
                valor, atributo["name"]
            )
        )
    return valor


def _escrever_arff(caminho, cabecalho, atributos, registros):
    with caminho.open("w", encoding="utf-8", newline="\n") as arquivo:
        for linha in cabecalho:
            arquivo.write(linha + "\n")
        arquivo.write("@data\n")
        for registro in registros:
            arquivo.write(
                ",".join(
                    _formatar_valor(valor, atributo)
                    for valor, atributo in zip(registro, atributos)
                )
                + "\n"
            )


def _formatar_valor(valor, atributo):
    if atributo["kind"] == "numeric":
        return format(valor, ".17g")
    texto = str(valor)
    if (
        not texto
        or any(caractere.isspace() or caractere in ",{}%?'\"" for caractere in texto)
        or texto.startswith("%")
    ):
        return '"' + texto.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return texto


def _comando_kmeans(caminho, k, semente):
    return [
        JAVA,
        "-cp",
        WEKA_JAR,
        CLUSTERER,
        "-t",
        str(caminho),
        "-N",
        str(k),
        "-S",
        str(semente),
        "-init",
        "1",
    ]


def _sse_weka(caminho, k, semente):
    comando = _comando_kmeans(caminho, k, semente)
    saida = _executar(comando)
    correspondencia = re.search(
        r"Within cluster sum of squared errors:\s*([0-9.eE+-]+)", saida
    )
    if not correspondencia:
        raise ValueError(
            "Não foi possível ler o SSE da saída do Weka.\nComando: {}\n{}".format(
                subprocess.list2cmdline(comando), saida
            )
        )
    return float(correspondencia.group(1)), comando


def _atribuicoes_weka(caminho, caminho_saida, k, semente):
    opcoes_clusterer = "{} -N {} -S {} -init 1".format(CLUSTERER, k, semente)
    comando = [
        JAVA,
        "-cp",
        WEKA_JAR,
        ADD_CLUSTER,
        "-W",
        opcoes_clusterer,
        "-i",
        str(caminho),
        "-o",
        str(caminho_saida),
    ]
    _executar(comando)
    _, atributos_saida, registros_saida = _ler_arff(caminho_saida)
    indices_cluster = [
        indice
        for indice, atributo in enumerate(atributos_saida)
        if atributo["name"].lower() == "cluster"
    ]
    if len(indices_cluster) != 1:
        raise ValueError(
            "O AddCluster do Weka não produziu exatamente um atributo 'cluster'."
        )
    indice_cluster = indices_cluster[0]
    etiquetas = [registro[indice_cluster] for registro in registros_saida]
    mapa = {}
    atribuicoes = []
    for etiqueta in etiquetas:
        if etiqueta not in mapa:
            mapa[etiqueta] = len(mapa)
        atribuicoes.append(mapa[etiqueta])
    return atribuicoes, comando


def _distancias_normalizadas(registros, atributos):
    limites = []
    for indice, atributo in enumerate(atributos):
        if atributo["kind"] == "numeric":
            valores = [registro[indice] for registro in registros]
            limites.append((min(valores), max(valores)))
        else:
            limites.append(None)
    return limites


def _distancia(a, b, atributos, limites):
    soma = 0.0
    for indice, atributo in enumerate(atributos):
        if atributo["kind"] == "numeric":
            minimo, maximo = limites[indice]
            diferenca = (
                0.0
                if maximo == minimo
                else (a[indice] - b[indice]) / (maximo - minimo)
            )
            soma += diferenca * diferenca
        elif a[indice] != b[indice]:
            soma += 1.0
    return math.sqrt(soma)


def _calcular_silhuetas(registros, atributos, atribuicoes):
    grupos = {}
    for indice, grupo in enumerate(atribuicoes):
        grupos.setdefault(grupo, []).append(indice)
    if len(grupos) < 2:
        raise ValueError("A silhueta exige pelo menos dois grupos não vazios.")

    limites = _distancias_normalizadas(registros, atributos)
    silhuetas = []
    for indice, grupo in enumerate(atribuicoes):
        membros_proprios = grupos[grupo]
        if len(membros_proprios) == 1:
            silhuetas.append(0.0)
            continue
        distancia_interna = sum(
            _distancia(registros[indice], registros[outro], atributos, limites)
            for outro in membros_proprios
            if outro != indice
        ) / (len(membros_proprios) - 1)
        distancia_externa = min(
            sum(
                _distancia(registros[indice], registros[outro], atributos, limites)
                for outro in membros
            )
            / len(membros)
            for outro_grupo, membros in grupos.items()
            if outro_grupo != grupo
        )
        denominador = max(distancia_interna, distancia_externa)
        silhuetas.append(
            0.0
            if denominador == 0
            else (distancia_externa - distancia_interna) / denominador
        )
    medias_grupo = {
        grupo: sum(silhuetas[indice] for indice in membros) / len(membros)
        for grupo, membros in grupos.items()
    }
    return sum(silhuetas) / len(silhuetas), medias_grupo


def _perfil(registros, atributos, atribuicoes):
    grupos = {}
    for indice, grupo in enumerate(atribuicoes):
        grupos.setdefault(grupo, []).append(registros[indice])
    resultado = []
    for grupo in sorted(grupos):
        linhas = ["Grupo {} (n={}):".format(grupo + 1, len(grupos[grupo]))]
        for indice, atributo in enumerate(atributos):
            valores_gerais = [registro[indice] for registro in registros]
            valores_grupo = [registro[indice] for registro in grupos[grupo]]
            if atributo["kind"] == "numeric":
                geral_media = sum(valores_gerais) / len(valores_gerais)
                grupo_media = sum(valores_grupo) / len(valores_grupo)
                geral_mediana = _mediana(valores_gerais)
                grupo_mediana = _mediana(valores_grupo)
                resumo_geral = "média={:.6g}, mediana={:.6g}".format(
                    geral_media, geral_mediana
                )
                resumo_grupo = "média={:.6g}, mediana={:.6g}".format(
                    grupo_media, grupo_mediana
                )
            else:
                resumo_geral = "moda={}".format(_moda(valores_gerais))
                resumo_grupo = "moda={}".format(_moda(valores_grupo))
            linhas.append(
                "  {} | geral: {} | grupo: {}".format(
                    atributo["name"], resumo_geral, resumo_grupo
                )
            )
        resultado.extend(linhas)
    return resultado


def _mediana(valores):
    ordenados = sorted(valores)
    meio = len(ordenados) // 2
    if len(ordenados) % 2:
        return ordenados[meio]
    return (ordenados[meio - 1] + ordenados[meio]) / 2


def _moda(valores):
    return Counter(valores).most_common(1)[0][0]


def _formatar_numero(valor):
    return "{:.10g}".format(valor)


def _positivos(valor):
    numero = int(valor)
    if numero < 1:
        raise argparse.ArgumentTypeError("O valor precisa ser pelo menos 1.")
    return numero


def _argumentos(argv):
    parser = argparse.ArgumentParser(
        description="Executa e valida agrupamentos K-means feitos pelo Weka."
    )
    parser.add_argument("arquivo_arff")
    parser.add_argument("--remover", help='Índices Weka a remover, por exemplo "last" ou "1,5".')
    parser.add_argument("--kmin", type=_positivos, default=2)
    parser.add_argument("--kmax", type=_positivos, default=10)
    parser.add_argument("--sementes", type=_positivos, default=5)
    parser.add_argument("--embaralhamentos", type=_positivos, default=20)
    parser.add_argument("--k-final", type=_positivos)
    argumentos = parser.parse_args(argv)
    if argumentos.kmin < 2:
        parser.error("--kmin precisa ser pelo menos 2 para calcular a silhueta.")
    if argumentos.kmax < argumentos.kmin:
        parser.error("--kmax precisa ser maior ou igual a --kmin.")
    if argumentos.k_final is not None and not (
        argumentos.kmin <= argumentos.k_final <= argumentos.kmax
    ):
        parser.error("--k-final precisa estar entre --kmin e --kmax.")
    return argumentos


def executar(argumentos):
    caminho_original = _resolver_arquivo_arff(argumentos.arquivo_arff)
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    nome_base = re.sub(r"[^A-Za-z0-9_-]+", "_", caminho_original.stem)
    pasta_resultados = PASTA_PROJETO / "resultados"
    pasta_resultados.mkdir(parents=True, exist_ok=True)

    comando_remover = None
    resultados_k = {}
    with tempfile.TemporaryDirectory(prefix="agrupamento_weka_") as pasta_temporaria:
        temporario = Path(pasta_temporaria)
        caminho_trabalho = caminho_original
        if argumentos.remover:
            caminho_trabalho = temporario / "base_sem_atributos.arff"
            comando_remover = [
                JAVA,
                "-cp",
                WEKA_JAR,
                REMOVE,
                "-R",
                argumentos.remover,
                "-i",
                str(caminho_original),
                "-o",
                str(caminho_trabalho),
            ]
            _executar(comando_remover)

        cabecalho, atributos, registros = _ler_arff(caminho_trabalho)
        if any(len(registro) != len(atributos) for registro in registros):
            raise ValueError("A base contém linhas com quantidade inconsistente de atributos.")
        if argumentos.kmax >= len(registros):
            raise ValueError(
                "Cada k testado precisa ser menor que o número de registros ({}).".format(
                    len(registros)
                )
            )

        for k in range(argumentos.kmin, argumentos.kmax + 1):
            resultados_sementes = []
            for semente in range(1, argumentos.sementes + 1):
                print(
                    "k={}, semente {}/{}".format(
                        k, semente, argumentos.sementes
                    ),
                    flush=True,
                )
                sse, comando_sse = _sse_weka(caminho_trabalho, k, semente)
                caminho_saida = temporario / "clusters_k{}_s{}.arff".format(
                    k, semente
                )
                atribuicoes, comando_clusters = _atribuicoes_weka(
                    caminho_trabalho, caminho_saida, k, semente
                )
                if len(atribuicoes) != len(registros):
                    raise ValueError(
                        "As atribuições do Weka não correspondem aos registros "
                        "da base de trabalho."
                    )
                resultados_sementes.append(
                    {
                        "semente": semente,
                        "sse": sse,
                        "atribuicoes": atribuicoes,
                        "arquivo": caminho_saida,
                        "comando_sse": comando_sse,
                        "comando_clusters": comando_clusters,
                    }
                )

            melhor = min(resultados_sementes, key=lambda item: item["sse"])
            silhueta, silhuetas_grupo = _calcular_silhuetas(
                registros, atributos, melhor["atribuicoes"]
            )
            if argumentos.sementes > 1:
                try:
                    from sklearn.metrics import adjusted_rand_score
                except ImportError as erro:
                    raise RuntimeError(
                        "A estabilidade requer scikit-learn no Python usado para "
                        "executar a ferramenta."
                    ) from erro

                estabilidade = sum(
                    adjusted_rand_score(
                        melhor["atribuicoes"], resultado["atribuicoes"]
                    )
                    for resultado in resultados_sementes
                    if resultado is not melhor
                ) / (argumentos.sementes - 1)
            else:
                estabilidade = None
            resultados_k[k] = {
                "sementes": resultados_sementes,
                "melhor": melhor,
                "sse_min": melhor["sse"],
                "sse_max": max(item["sse"] for item in resultados_sementes),
                "silhueta": silhueta,
                "silhuetas_grupo": silhuetas_grupo,
                "estabilidade": estabilidade,
            }

        k_final = argumentos.k_final
        escolha_automatica = k_final is None
        if escolha_automatica:
            k_final = max(
                resultados_k, key=lambda k: resultados_k[k]["silhueta"]
            )
        resultado_final = resultados_k[k_final]
        atribuicoes_finais = resultado_final["melhor"]["atribuicoes"]

        sses_embaralhados = []
        comando_baseline_exemplo = None
        for versao in range(1, argumentos.embaralhamentos + 1):
            gerador = random.Random(versao)
            registros_embaralhados = [list(registro) for registro in registros]
            for indice_atributo in range(len(atributos)):
                coluna = [registro[indice_atributo] for registro in registros]
                gerador.shuffle(coluna)
                for indice_registro, valor in enumerate(coluna):
                    registros_embaralhados[indice_registro][indice_atributo] = valor
            caminho_embaralhado = temporario / "embaralhado_{}.arff".format(versao)
            _escrever_arff(
                caminho_embaralhado, cabecalho, atributos, registros_embaralhados
            )
            sses_sementes = []
            for semente in range(1, argumentos.sementes + 1):
                sse_embaralhado, comando_embaralhado = _sse_weka(
                    caminho_embaralhado, k_final, semente
                )
                sses_sementes.append(sse_embaralhado)
                if comando_baseline_exemplo is None:
                    comando_baseline_exemplo = comando_embaralhado
                print(
                    "Linha de base {}, semente {}/{}".format(
                        versao, semente, argumentos.sementes
                    ),
                    flush=True,
                )
            melhor_sse_embaralhado = min(sses_sementes)
            sses_embaralhados.append(melhor_sse_embaralhado)

        sse_real = resultado_final["sse_min"]
        abaixo_de_todos = all(sse_real < sse for sse in sses_embaralhados)
        caminho_arff_saida = pasta_resultados / "{}_{}_k{}_clusters.arff".format(
            data_hora, nome_base, k_final
        )
        shutil.copyfile(resultado_final["melhor"]["arquivo"], caminho_arff_saida)

        comandos_exemplo = []
        if comando_remover is not None:
            comandos_exemplo.append(comando_remover)
        comandos_exemplo.extend(
            [
                resultado_final["melhor"]["comando_sse"],
                resultado_final["melhor"]["comando_clusters"],
                comando_baseline_exemplo,
            ]
        )
        silhueta_grupos = resultado_final["silhuetas_grupo"]
        linhas_relatorio = [
            "Agrupamento K-means com Weka",
            "Base original: {}".format(caminho_original),
            "Base de trabalho: {}".format(caminho_trabalho),
            "Atributos removidos: {}".format(argumentos.remover or "nenhum"),
            "Registros: {}".format(len(registros)),
            "Atributos usados: {}".format(len(atributos)),
            "Parâmetros: k={}..{}, sementes={}, embaralhamentos={}".format(
                argumentos.kmin,
                argumentos.kmax,
                argumentos.sementes,
                argumentos.embaralhamentos,
            ),
            "Inicialização SimpleKMeans: -init 1; sementes Weka de 1 a {}.".format(
                argumentos.sementes
            ),
            "Versões embaralhadas: sementes fixas de 1 a {}; cada atributo foi "
            "embaralhado separadamente em cada versão.".format(
                argumentos.embaralhamentos
            ),
            "k final: {} ({})".format(
                k_final,
                "escolha automática pela maior silhueta média"
                if escolha_automatica
                else "informado em --k-final",
            ),
            "",
            "Exemplos dos comandos Weka executados:",
        ]
        linhas_relatorio.extend(
            subprocess.list2cmdline(comando) for comando in comandos_exemplo
        )
        linhas_relatorio.extend(
            [
                "",
                "Resultados por k (SSE e atribuições fornecidos pelo Weka):",
                "k | melhor semente | SSE mínimo | SSE máximo | silhueta média | "
                "estabilidade ARI",
            ]
        )
        for k, resultado in resultados_k.items():
            estabilidade = (
                "n/a"
                if resultado["estabilidade"] is None
                else _formatar_numero(resultado["estabilidade"])
            )
            linhas_relatorio.append(
                "{} | {} | {} | {} | {} | {}".format(
                    k,
                    resultado["melhor"]["semente"],
                    _formatar_numero(resultado["sse_min"]),
                    _formatar_numero(resultado["sse_max"]),
                    _formatar_numero(resultado["silhueta"]),
                    estabilidade,
                )
            )
        linhas_relatorio.extend(
            [
                "",
                "Silhueta média por grupo para k final:",
            ]
        )
        for grupo, media in sorted(silhueta_grupos.items()):
            linhas_relatorio.append(
                "Grupo {}: {}".format(grupo + 1, _formatar_numero(media))
            )

        linhas_relatorio.extend(
            [
                "",
                "Linha de base: atributos embaralhados independentemente em cada versão",
                "SSE real (menor SSE entre sementes): {}".format(
                    _formatar_numero(sse_real)
                ),
                "SSE embaralhado mínimo: {}".format(
                    _formatar_numero(min(sses_embaralhados))
                ),
                "SSE embaralhado médio: {}".format(
                    _formatar_numero(sum(sses_embaralhados) / len(sses_embaralhados))
                ),
                "SSE embaralhado máximo: {}".format(
                    _formatar_numero(max(sses_embaralhados))
                ),
                "Proporção de versões com SSE <= real: {}/{} ({:.6g})".format(
                    sum(sse <= sse_real for sse in sses_embaralhados),
                    len(sses_embaralhados),
                    sum(sse <= sse_real for sse in sses_embaralhados)
                    / len(sses_embaralhados),
                ),
                "Evidência contra dados embaralhados: {}".format(
                    "sim; SSE real abaixo de todas as versões"
                    if abaixo_de_todos
                    else "não; SSE real não está abaixo de todas as versões"
                ),
                "",
                "Perfil dos grupos finais (valores gerais ao lado dos valores do grupo):",
            ]
        )
        linhas_relatorio.extend(
            _perfil(registros, atributos, atribuicoes_finais)
        )
        linhas_relatorio.extend(
            [
                "",
                "Silhueta: calculada em Python a partir das atribuições do Weka, "
                "com atributos numéricos normalizados pelo intervalo observado e "
                "diferença nominal 0/1.",
                "As atribuições e o SSE do agrupamento foram produzidos pelo Weka.",
                "Arquivo ARFF com clusters: {}".format(caminho_arff_saida),
            ]
        )

    caminho_relatorio = pasta_resultados / "{}_{}_agrupamento.txt".format(
        data_hora, nome_base
    )
    with caminho_relatorio.open("w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write("\n".join(linhas_relatorio) + "\n")
    print("Relatório: {}".format(caminho_relatorio))
    print("ARFF com clusters: {}".format(caminho_arff_saida))
    print(
        "k final: {} | SSE real: {} | silhueta média: {}".format(
            k_final,
            _formatar_numero(resultado_final["sse_min"]),
            _formatar_numero(resultado_final["silhueta"]),
        )
    )
    return caminho_relatorio, caminho_arff_saida


def main(argv=None):
    try:
        executar(_argumentos(argv))
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as erro:
        print(erro, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
