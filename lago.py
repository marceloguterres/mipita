#!/usr/bin/python
# coding=utf8

"""
 +---------------------+
 |  E C O N O D A T A  |
 +---------------------+

Script Auxiliar para carregar dados Econodata
Default: bucket S3 mantido por Mauro Zac
ou especificar path para acessar dados localmente
"""

import json

import requests
import pandas as pd

from auxdata import sigla_UF, codigo_UF


def carregar_mip_nereus(ano=2018, path=""):
    """Carrega as matrizes insumo produtos de 2010 a 2018.
    fonte dos dados: matriz SxS NEREUS-USP formatada em econodata
    https://econodata.s3.amazonaws.com/Nereus/mip68br2010.csv
    retorna dataFrame do ano especificado
    """
    url = "https://econodata.s3.amazonaws.com/"
    res = "Nereus/mip68br"
    if path: 
    	url = path
    ano = str(ano)
    anos = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018']
    if ano in anos:
        mip = pd.read_csv(url+res+ano+".csv", index_col=0)
        if path:
            print('[~~] Carregada MIP SxS Brasil | Nereus USP | ' + ano)
        else:
            print('[s3] Carregada MIP SxS Brasil | Nereus USP | ' + ano)
        return mip
    return None


def carregar_atividades68(path=""):
    url = "https://econodata.s3.amazonaws.com/"
    res = "Classificas/atividadesMip67e68.json"
    if path:
        print('[~~] Códigos e descrição das atividades para MIP 68')
        with open(path+res) as f: 
            atividades = json.loads(f.read())
    else:
        print('[s3] Códigos e atividades para MIP 68')
        atividades = json.loads(requests.get(url+res).text)
    cods68 = atividades["codigos_atividades_68"]
    labels68 = atividades["labels_atividades_68"]
    mapa = {}
    for i in range(len(cods68)):
        mapa[cods68[i]] = labels68[i]
    return cods68, labels68, mapa


def carregar_classes_CNAE(path=""):
    """Carrega dados sobre 673 classes CNAEs da S3.
    Alternativamente, carrega do path local especificado.
    docs:
    https://servicodados.ibge.gov.br/api/docs/cnae?versao=2#api-Classes-classesGet
    """
    url = "https://econodata.s3.amazonaws.com/"
    res = "Classificas/CNAEclasses.json"
    if path:
        print('[~~] Classes da CNAE')
        with open(path+res) as f:
            return json.loads(f.read())
    cnaes = json.loads(requests.get(url+res).text)
    print('[s3] Classes da CNAE')
    return cnaes


def carregar_compatibiliza_CNAE(path=""):
    """Carrega referencia para compatibilizar 673 Classes Cnae em 68 Atividades
    """
    url = "https://econodata.s3.amazonaws.com/"
    res = "Classificas/compatibiliza673a68.json"
    if path:
        print('[~~] Compatibilização 673 classes para 68 atividades')
        with open(path+res) as f:
            return json.loads(f.read())
    compa = json.loads(requests.get(url+res).text)
    print('[S3] Compatibilização 673 classes para 68 atividades')
    return compa


def carregar_compatibiliza_ISIC(path=""):
    """Carrega referencia para compatibilizar 416 classes ISIC 4.0 em 68 Atividades
    """
    url = "https://econodata.s3.amazonaws.com/"
    res = "Classificas/compatibilizaISICa68.json"
    if path:
        print('[~~] Compatibilização 416 classes ISIC para 68 atividades')
        with open(path+res) as f:
            return json.loads(f.read())
    compa = json.loads(requests.get(url+res).text)
    print('[S3] Compatibilização classes ISIC para 68 atividades')
    return compa


def carregar_RAIS_BR68(ano, path=""):
    """Carrega dados pré-processados da RAIS agregados para o país.
    68 atividades."""
    url = "https://econodata.s3.amazonaws.com/"
    res = "RAIS/"+ano+"/Brasil68ano"+ano+".csv"
    if path: 
        url = path
        print('[~~] RAIS Brasil 68 atividades')
    else:
        print('[S3] RAIS Brasil 68 atividades')
    return pd.read_csv(url+res, dtype={'Atividades_68':str}, index_col=0)


def carregar_RAIS_municipal(res, path=""):
    """Carrega dados pré-processados da RAIS para um município.
    673 classes CNAE.
    res: str na forma 'RAIS/2014/SP/RAIS350055ano2014.csv'
    """
    url = "https://econodata.s3.amazonaws.com/"
    if path: 
        url = path
        print('[~~] RAIS Municipal 673 classes', res)
    else:
        print('[S3] RAIS Municipal 673 classes', res)
    return pd.read_csv(url+res, dtype={"Classe CNAE":str}, index_col=0)


def carregar_compatibiliza_atividades_a_3(path=""):
    """Carrega referencia para compatibilizar 68 atividades nos 3 grandes setores
    """
    url = "https://econodata.s3.amazonaws.com/"
    res = "Classificas/compatibiliza68a03.json"
    if path:
        print('[~~] Compatibilização 68 atividades em 3 setores')
        with open(path+res) as f:
            return json.loads(f.read())
    compa = json.loads(requests.get(url+res).text)
    print('[S3] Compatibilização 68 atividades em 3 setores')
    return compa


def carregar_MU74(res, path=""):
    """Carrega dados IBGE para um município.
    74 campos com classifições, PIBs e comparações com UF e BR
    
    res: str na forma 'MU74/2014/SP/MU350055ano2014.csv'
    """
    url = "https://econodata.s3.amazonaws.com/"
    if path: 
        url = path
        print('[~~] MU74', res)
    else:
        print('[S3] MU74', res)
    df = pd.read_csv(url+res, index_col=0).T
    return df


def carregar_IPCA(path=""):
    """Carrega indices do IPCA com índice base dez1993 = 100
    """
    url = "https://econodata.s3.amazonaws.com/"
    if path: 
        url = path
        print('[~~] IPCA')
    else:
        print('[S3] IPCA')
    df = pd.read_csv(url+'Indices/ipca.csv', index_col=0, dtype={'Data':str})
    df.index = df['Data']
    return df


def carregar_QLimporta(ano, path=""):
    """Carrega QLs de importação MUN x 68 atividades + valores em US$ e R$.
    """
    url = "https://econodata.s3.amazonaws.com/"
    ano = str(ano)
    if path: 
        url = path
        print('[~~] QL importação', ano)
    else:
        print('[S3] QL importação', ano)
    df = pd.read_csv(url+'Comex/'+ano+"/QL_importa"+ano+'.csv', index_col=0)
    return df


def carregar_QLexporta(ano, path=""):
    """Carrega QLs de exportação MUN x 68 atividades + valores em US$ e R$.
    """
    url = "https://econodata.s3.amazonaws.com/"
    ano = str(ano)
    if path: 
        url = path
        print('[~~] QL exportação', ano)
    else:
        print('[S3] QL exportação', ano)
    df = pd.read_csv(url+'Comex/'+ano+"/QL_exporta"+ano+'.csv', index_col=0)
    return df

