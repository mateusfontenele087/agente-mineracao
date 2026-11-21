# Gera dados/soybean_indicador.arff: acrescenta o atributo "registro_incompleto" (sim/nao),
# marcado como "sim" quando o registro tem pelo menos um valor ausente ('?').
# É uma regra fixa (não aprende nada com os dados), por isso pode ser feita antes da validação.
entrada, saida = "dados/soybean.arff", "dados/soybean_indicador.arff"
linhas, na_secao_dados, n_sim = [], False, 0
for linha in open(entrada):
    s = linha.strip()
    if s.lower().startswith("@attribute class"):
        # novo atributo entra logo antes da classe (que continua sendo o último)
        linhas.append("@attribute registro_incompleto {sim,nao}\n")
    if na_secao_dados and s and not s.startswith("%"):
        valores = [v.strip() for v in s.split(",")]
        flag = "sim" if "?" in valores[:-1] else "nao"
        n_sim += flag == "sim"
        linha = ",".join(valores[:-1] + [flag, valores[-1]]) + "\n"
    if s.lower().startswith("@data"):
        na_secao_dados = True
    linhas.append(linha)
open(saida, "w").writelines(linhas)
print(f"{saida} gerado; registros marcados como incompletos: {n_sim}")
