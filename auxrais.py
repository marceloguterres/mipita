#!/usr/bin/python
# coding=utf8

"""
 +---------------+
 |  M I P I T A  |
 +---------------+

Manipulação de dados RAIS no contexto do objeto Mipita

by Mauro Zac
"""
import numpy as np
import pandas as pd

from auxdata import sigla_UF
from lago import carregar_RAIS_municipal, carregar_compatibiliza_CNAE, carregar_RAIS_BR68


def rais_valor(ano, area, pesos, exceto, path):
    """ Hipótese de regionalização RAIS_Valor
        -------------------------------------
        => atividade na 'área' é estimada pela fração salarial paga
        na 'area' frente ao Brasil, temos assim o valor do trabalho
        como estimador (Warea/Wbrasil)
        => assume que tecnologia e produtividade são homogêneas no país
        => ignora trabalho informal e PJs
        => ignora diferenças salarias entre regiões

        Brene (2014): valor do trablho dá melhor resultado do que número
        de trabalhadores.

        A cada atividade corresponde um coeficiente locacional.
        A estimativa da matriz sxs regional é feita pela multiplicação
        dos inputs de cada atividade por seu respectivo coeficiente,
        porque por hipótese ele define o tamanho da produção naquela área.
        por exemplo: o coef da atividade 0191 multiplica todos os valores
        da coluna 0191 da matriz sxs.
    """
    # passo 1: obter tabela somada e ponderada da RAIS para 673 setores
    nomes_csv = ["RAIS/"+ano+"/"+sigla_UF(a[:2])+"/RAIS"+a+"ano"+ano+".csv" for a in area]
    tabela_rais_673 = soma_rais(nomes_csv, pesos, path)
    # passo 2: agregar tabela RAIS para 68 atividades
    tabela_rais_68 = agregar_68_atividades(tabela_rais_673, path)
    # passo 3: gerar coef locacional
    tabela_rais_68_BR = carregar_RAIS_BR68(ano, path)
    Warea = tabela_rais_68["Valor do Trabalho (R$ nom)"]
    Wbrasil = tabela_rais_68_BR["Valor do Trabalho (R$ nom)"]
    quociente_locacional = Warea.divide(Wbrasil).fillna(0.0)
    # Variante => gerar qL BR exceto área
    if exceto:
        Warea = Wbrasil - Warea
        quociente_locacional = Warea.divide(Wbrasil).fillna(1.0)
    return quociente_locacional


def rais_valor_tamanho(ano, area, pesos, path):
    """ Hipótese de regionalização RAIS_Valor + Tamanho estabelecimento
        ---------------------------------------------------------------
        => atividade na 'área' é estimada pela fração de pessoal empregado
        na 'area' frente ao Brasil, temos assim a quantidade de trabalho
        como estimador (Tarea/Tbrasil)
        => assume que produtividade acompanha tamanho do estabelecimento
        => ignora trabalho informal e PJs

        A cada atividade corresponde um coeficiente locacional.
        A estimativa da matriz sxs regional é feita pela multiplicação
        dos inputs de cada atividade por seu respectivo coeficiente,
        porque por hipótese ele define o tamanho da produção naquela área.
        por exemplo: o coef da atividade 0191 multiplica todos os valores
        da coluna 0191 da matriz sxs.
    """
    # passo 1: obter tabela somada e ponderada da RAIS para 673 setores
    nomes_csv = ["RAIS/"+ano+"/"+sigla_UF(a[:2])+"/RAIS"+a+"ano"+ano+".csv" for a in area]
    tabela_rais_673 = soma_rais(nomes_csv, pesos, path)
    # passo 2: agregar tabela RAIS para 68 atividades
    tabela_rais_68 = agregar_68_atividades(tabela_rais_673, path)
    # passo 3: gerar coef locacional
    tabela_rais_68_BR = carregar_RAIS_BR68(ano, path)
    Warea = tabela_rais_68["Valor do Trabalho (R$ nom)"]
    Wbrasil = tabela_rais_68_BR["Valor do Trabalho (R$ nom)"]
    Sarea = tabela_rais_68["Tamanho"]
    Sbrasil = tabela_rais_68_BR["Tamanho"]

    quociente_locacional = (Tarea/Tbrasil)*((Sarea/Sbrasil)**0.5)  # alisado pela raiz
    quociente_locacional.fillna(0.0, inplace=True)
    return quociente_locacional


def rais_trabalho(ano, area, pesos, path):
    """ Hipótese de regionalização RAIS_Trabalho
        ----------------------------------------
        => atividade na 'área' é estimada pela fração de pessoal empregado
        na 'area' frente ao Brasil, temos assim a quantidade de trabalho
        como estimador (Tarea/Tbrasil)
        => assume que tecnologia e produtividade são homogêneas no país
        => ignora trabalho informal e PJs
        => ignora diferenças de produtividade por trabalhador entre regiões

        A cada atividade corresponde um coeficiente locacional.
        A estimativa da matriz sxs regional é feita pela multiplicação
        dos inputs de cada atividade por seu respectivo coeficiente,
        porque por hipótese ele define o tamanho da produção naquela área.
        por exemplo: o coef da atividade 0191 multiplica todos os valores
        da coluna 0191 da matriz sxs.
    """
    # passo 1: obter tabela somada e ponderada da RAIS para 673 setores
    nomes_csv = ["RAIS/"+ano+"/"+sigla_UF(a[:2])+"/RAIS"+a+"ano"+ano+".csv" for a in area]
    tabela_rais_673 = soma_rais(nomes_csv, pesos, path)
    # passo 2: agregar tabela RAIS para 68 atividades
    tabela_rais_68 = agregar_68_atividades(tabela_rais_673, path)
    # passo 3: gerar coef locacional
    tabela_rais_68_BR = carregar_RAIS_BR68(ano, path)
    Tarea = tabela_rais_68["Pessoal empregado"]
    Tbrasil = tabela_rais_68_BR["Pessoal empregado"]
    quociente_locacional = Tarea/Tbrasil
    quociente_locacional.fillna(0.0, inplace=True)
    return quociente_locacional



def soma_rais(nomes_csv, pesos, path):
    """
    recebe
    nomes_csv: list ['2014/SP/RAIS350055ano2014.csv', '2014/SP/RAIS350053ano2014.csv']  # arquivos base
    pesos: array  # mesmo tamanho
    path: "" ou diretorio local

    retorna DataFrame com a soma
    """
    # A base econodata-RAIS tem 673 classes cnae
    # Não pode somar simplesmente os dataframes pq há colunas com taxas
    # init
    col1 = np.zeros(673)
    col2 = np.array([0.000001 for _ in range(673)])  # para evitar NaN na divisao
    col3 = np.zeros(673)
    col4 = np.zeros(673)
    index = 0  # para percorrrer os pesos
    for arquivo in nomes_csv:
        p = pesos[index]
        index += 1
        data = carregar_RAIS_municipal(arquivo, path)
        col0 = data["Classe CNAE"]
        col1 += data['Valor do Trabalho (R$ nom)'].values*p
        col3 = (col3*col2 + data['Escolaridade'].values*data['Pessoal empregado'].values*p) / (col2+data['Pessoal empregado'].values*p)
        col4 = (col4*col2 + data['Tamanho do estabelecimentos'].values*data['Pessoal empregado'].values*p) / (col2+data['Pessoal empregado'].values*p)
        col2 += data['Pessoal empregado'].values*p
        # pessoal vai por ultimo para não estragar a ponderação de col3 e col4
    df = pd.DataFrame(
        {
            "Classe CNAE": col0,
            "Valor do Trabalho (R$ nom)": col1,  # soma dos salários pagos + 13º + extras
            "Pessoal empregado": col2,  # n de empregados, pode ser fracionado
            "Escolaridade": col3,  # indice medio de escolaridade
            "Tamanho do estabelecimentos": col4, # indice medio do tamanho do estabelecimento
        })
    return df


def agregar_68_atividades(tabela_rais_673, path):
    """
    recebe:
    tabela_rais_673: DataFrame [673 rows x 6 columns]  # soma ponderada de uma area
    retorna:
    tabela_rais_68: DataFrame [68 rows x 6 columns]
    """
    # adicionar coluna com CNAE 4 digitos para busca
    # a Classe CNAE orignial vem com digito verificador 0111-3
    # a Classe CNAE do dicionario de compatibilização vem sem o digito verif
    tabela_rais_673['temp_quatro'] = [cnae[:4] for cnae in tabela_rais_673["Classe CNAE"]]
    # dados de compatibilização 673 classses -> 68 setores
    compat = carregar_compatibiliza_CNAE(path)
    """
    {
        "atividade": "4180",
        "desc": "Construção",
        "classes": ["4110","4120","4211","4212","4213","4221","4222","4223","4291",
        "4292","4299","4311","4312","4313","4319","4321","4322","4329","4330","4391",
        "4399"]
    }
    """
    controle = [] # para não adicionar mais de uma vez [melhorar]
    col0, col1, col2, col3, col4 = [], [], [], [], []
    for regra in compat:
        # tem que consolidar um por um por que tamanhos variam
        v1, v2, v3, v4 = 0.0, 0.000001, 0.0, 0.0
        col0.append(regra['atividade'])
        for classe in regra['classes']:
            if classe in controle:
                # aqui elimina p.e. dupla contagem de educação e saúde (pub e priv)
                continue
            x = tabela_rais_673.loc[tabela_rais_673["temp_quatro"] == classe]
            try:
                v1 += x['Valor do Trabalho (R$ nom)'].iloc[0]
                v3 = (v3*v2 + x["Escolaridade"].iloc[0]*x['Pessoal empregado'].iloc[0]) / (v2+x['Pessoal empregado'].iloc[0])
                v4 = (v4*v2 + x["Tamanho do estabelecimentos"].iloc[0]*x['Pessoal empregado'].iloc[0]) / (v2+x['Pessoal empregado'].iloc[0])
                v2 += x['Pessoal empregado'].iloc[0]
            except:
                print(classe, regra, x)
            controle.append(classe)
        col1.append(v1)
        col2.append(v2)
        col3.append(v3)
        col4.append(v4)
    tabela_rais_68 = pd.DataFrame({
            "Atividades_68": col0,
            "Valor do Trabalho (R$ nom)": col1,  # soma dos salários pagos + 13º + extras
            "Pessoal empregado": col2,  # n de empregados, pode ser fracionado
            "Escolaridade": col3,  # media das escolaridades
            "Tamanho": col4,  # soma dos tamanhos
        })
    return tabela_rais_68
