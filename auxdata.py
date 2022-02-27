#!/usr/bin/python
# coding=utf8

"""
TESTES de DATA QUALITY e
UTILIDADES de CONSISTÊNCIA

USO da GERAL

by Mauro Zac
"""

import datetime


def deflator_ipca(valor, data, data_ref, path=''):
    """
    Deflaciona pelo IPCA um valor dado, usando o mês da data de referência.
    
    Se data é ano, usa o mês de dezembro.
    
    valor: float    valor em reais a ser deflacionado
    data: datetime ou YYYY [string ou int]  
    data_ref: datetime ou YYYY [string ou int]  
    """
    valor = float(valor)
    deflacionado, d, dR = None, None, None
    if type(data) is datetime.datetime:
        ano = str(data.year)
        mes = str(data.month)
        if len(mes) == 1: mes = "0" + mes
        d = ano + '.' + mes
    else:
        ano = str(data)
        if len(ano) == 4 and ano.isdigit():
            d = ano + '.12'
    if type(data_ref) is datetime.datetime:
        ano = str(data_ref.year)
        mes = str(data_ref.month)
        if len(mes) == 1: mes = "0" + mes
        dR = ano + '.' + mes
    else:
        ano = str(data_ref)
        if len(ano) == 4 and ano.isdigit():
            dR = ano + '.12'
    if d and dR:
        z = carregar_IPCA(path=path)
        v = z.loc[d]['IPCAib']
        vR = z.loc[dR]['IPCAib']
        deflacionado = valor * (vR/v)    
    return deflacionado


def sigla_UF(uf):
    """Recebe uf em uma das formas válidas: 35, "35", "SP", "sp"
    Retorna forma canônica "SP" ou nada
    """
    uf = str(uf)
    if len(uf) != 2:
        return None
    codigos = {
        '12':'AC', '27':'AL', '16':'AP', '13':'AM', '29':'BA', '23':'CE', '53':'DF',
        '32':'ES', '52':'GO', '21':'MA', '51':'MT', '50':'MS', '31':'MG', '15':'PA',
        '25':'PB', '41':'PR', '26':'PE', '22':'PI', '33':'RJ', '24':'RN', '43':'RS',
        '11':'RO', '14':'RR', '42':'SC', '35':'SP', '28':'SE', '17':'TO',}
    if uf.isdigit():
        if uf not in codigos.keys():
            return None
        return codigos[uf]
    UFs = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',]
    uf = uf.upper()
    if uf not in UFs:
        return None
    return uf


def codigo_UF(uf):
    """Retorna codigo numerico de uma sigla de UF"""
    numerico = {
        'AC': '12', 'AL': '27', 'AP': '16', 'AM': '13', 'BA': '29', 'CE': '23',
        'DF': '53', 'ES': '32', 'GO': '52', 'MA': '21', 'MT': '51', 'MS': '50',
        'MG': '31', 'PA': '15', 'PB': '25', 'PR': '41', 'PE': '26', 'PI': '22',
        'RJ': '33', 'RN': '24', 'RS': '43', 'RO': '11', 'RR': '14', 'SC': '42',
        'SP': '35', 'SE': '28', 'TO': '17'}
    return numerico[uf]



