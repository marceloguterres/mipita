#!/usr/bin/python
# coding=utf8
"""
 +---------------+
 |  M I P I T A  |
 +---------------+

Análise da economia brasileira com matrizes de insumo-produto

import matriz
path = '/home/mauro/econodata/'
n = matriz.Nereus(2010, path=path)
m = n.extrair_mipita()
m.preparar_qL(['354990'], path=path)
m.regionalizar(path=path)

k = n.extrair_mipita()
k.preparar_qL(['354990'], path=path, exceto=True)
k.regionalizar(path=path)

"""

__version__ = "v.1.2 | 2021.11.17"
__author__ = "Mauro Zackiewicz"
__email__ = "maurozac@gmail.com"


import json

import numpy as np
import pandas as pd

from lago import *
from auxrais import *
from auxdata import *


class Mipita:
    """Objeto base para Matriz de Insumos Produtos.

    Padrão Mipita
    -------------
    68 x 68 atividades
    77 x 76 para toda a economia

    insumos [entradas/linhas]
    'importado do mundo',
    'impostos de importação',
    'importado do Brasil',
    'impostos',
    'salários',
    'contribuições sociais',
    'margem',
    'outros impostos e subsídeos',
    'total_insumos'

    produtos [saídas/colunas]
    'exportado ao mundo',
    'exportado ao Brasil',
    'governo',
    'isfl',
    'famílias',
    'capital fixo',
    'estoque',
    'total_produtos'

    """
    def __init__(self):
        self.ano = ''
        self.recorte = ''
        self.fonte = ''
        self.mipita = None
        self.codigos = None
        self.atividades = None
        self.empregos = None


    def __repr__(self):
        r = "Matriz de Insumo-Produto - Mipita\n"
        r += "---------------------------------\n"
        r += self.ano
        if hasattr(self, 'mipreg'):
            r += "\nmipreg: " + self.recorte
        r += "\ndados: " + self.fonte + ", RAIS e IBGE"
        return r


    def limpar_mipita(self):
        """Remove todos os atributos não essenciais do objeto Mipita.
        """
        # FAZER
        return None


    def preparar_qL(self, area, pesos=None, metodo="rais_valor", exceto=False, path=''):
        """Gera vetor qL requerido pelo método regionaliza()
        """
        if type(area) is not list or len(area) == 0:
            return None
        self.area = area
        # pesos: array com pesos para ponderar participação de cada área
        # deve ter mesmo comprimento que a list das areas com coef de 0 a 1
        if not pesos:
            pesos = np.array([1. for _ in range(len(area))])
        self.pesos = pesos
        if metodo == 'rais_valor':
            self.qL = rais_valor(self.ano, self.area, self.pesos, exceto, path)
            self.qL.index = self.codigos
        M = []  # juntar informações de todos os municípios
        for mun in self.area:
            res = 'MU74/'+self.ano+'/'+sigla_UF(mun[0:2])+'/MU'+mun+"ano"+self.ano+'.csv'
            M.append(carregar_MU74(res, path))
        # ibge => dados do ibge para todos os municipios na area escolhida
        self.ibge = pd.concat(M, axis=0)
        # propT: proporção em relação ao total de população
        # campo m045: PIB municipal / PIB Brasil
        self.propT = self.ibge['m045'].astype(float).multiply(self.pesos).sum()
        if exceto:
            self.propT = 1 - self.propT


    def regionalizar(self, label="", path=""):
        """Regionalização de matriz de insumos-produtos brasileira

        qL: list-like; 68 setores, 0 <= qi <= 1; calculado previamente
        """
        if not hasattr(self, 'qL'):
            return None
        if not label:
            label = "Regionalizada QL:" + str(np.array(self.qL).mean())
        self.recorte = label

        # BLOCO A # Inputs da Economia, 68x68 e linha abaixo da matriz sxs
        self.sxs = self.mipita.iloc[0:68, 0:68].multiply(self.qL, axis=1)
        importado_inter = self.mipita.loc['importado do mundo'][0:68].multiply(self.qL)
        importado_inter_impostos = self.mipita.loc['impostos de importação'][0:68].multiply(self.qL)
        impostos_inter = self.mipita.loc['impostos'][0:68].multiply(self.qL)
        salarios = self.mipita.loc['salários'][0:68].multiply(self.qL)
        sociais = self.mipita.loc['contribuições sociais'][0:68].multiply(self.qL)
        margem = self.mipita.loc['margem'][0:68].multiply(self.qL)
        outros = self.mipita.loc['outros impostos e subsídeos'][0:68].multiply(self.qL)
        self.insumos = pd.concat([
            self.sxs,
            pd.DataFrame({'importado do mundo': importado_inter}).T,
            pd.DataFrame({'impostos de importação': importado_inter_impostos}).T,
            pd.DataFrame({'importado do Brasil': np.zeros(68)}, index=self.codigos).T,
            pd.DataFrame({'impostos': impostos_inter}).T,
            pd.DataFrame({'salários': salarios}).T,
            pd.DataFrame({'contribuições sociais': sociais}).T,
            pd.DataFrame({'margem': margem}).T,
            pd.DataFrame({'outros impostos e subsídeos': outros}).T,
        ], axis=0)  # 76x68
        insumos = pd.DataFrame({"total_insumos":self.insumos.sum(axis=0)})
        self.insumos = pd.concat([self.insumos, insumos.T], axis=0)  # 77x68

        # BLOCO B # Outpus em colunas à direita do bloco A
        # propL: aplica a colunas que dependem da proporção de produção local
        # prod_inter_reg = self.sxs.sum(axis=1)  # soma as colunas
        # prod_inter_nac = self.mipita.iloc[0:68,0:68].sum(axis=1)
        # self.propL = prod_inter_reg.divide(prod_inter_nac).fillna(0.0)
        # colunas que dependem da produção local
        exporta = self.mipita['exportado ao mundo'][0:68].multiply(self.qL)
        capfixo = self.mipita['capital fixo'][0:68].multiply(self.qL)
        estoque = self.mipita['estoque'][0:68].multiply(self.qL)
        # propT: aplica a colunas que dependem do tamanho do PIB/Pop local
        governo = self.mipita['governo'][0:68].multiply(self.propT)
        semlucro = self.mipita['isfl'][0:68].multiply(self.propT)
        familias = self.mipita['famílias'][0:68].multiply(self.propT)
        self.consumo = pd.concat([
            exporta,
            pd.DataFrame({"exportado ao Brasil":np.zeros(68)}, index=self.codigos),
            governo,
            semlucro,
            familias,
            capfixo,
            estoque,
        ], axis=1) # 68x7
        self.consumo.columns = ['exportado ao mundo', 'exportado ao Brasil',
            'governo', 'isfl', 'famílias', 'capital fixo', 'estoque']

        # BLOCO C # Importado e impostos do consumo, demais linhas zeradas
        C = pd.DataFrame(
            {
                'exportado ao mundo': np.zeros(9),
                'exportado ao Brasil': np.zeros(9),
                'governo': np.zeros(9),
                'isfl': np.zeros(9),
                'famílias': np.zeros(9),
                'capital fixo': np.zeros(9),
                'estoque': np.zeros(9),
            },
            index = ['importado do mundo', 'impostos de importação', 'importado do Brasil',
            'impostos', 'salários','contribuições sociais', 'margem',
            'outros impostos e subsídeos', 'total_insumos']
        ) # 9x7
        # Estima mantendo a proporção entre o consumo local e o consumo nacional
        # consumo_local = self.consumo.sum(axis=0)  # 68x7   soma as linhas
        # consumo_nac = self.mipita.iloc[0:68,68:75].sum(axis=0)  # 68x7
        # self.propC = consumo_local.divide(consumo_nac).fillna(0.0)  # 7x1
        C.loc['importado do mundo'] = self.mipita.loc['importado do mundo'][68:75].multiply(self.propT)
        C.loc['impostos de importação'] = self.mipita.loc['impostos de importação'][68:75].multiply(self.propT)
        C.loc['impostos'] = self.mipita.loc['impostos'][68:75].multiply(self.propT)
        C.loc['salários'] = self.mipita.loc['salários'][68:75].multiply(self.propT)
        C.loc['contribuições sociais'] = self.mipita.loc['contribuições sociais'][68:75].multiply(self.propT)
        # Juntar (B + C) + A
        BC = pd.concat([self.consumo, C], axis=0)
        self.mipreg = pd.concat([self.insumos, BC], axis=1)  # 77x75
        self.mipreg['total_produtos'] = self.mipreg.sum(axis=1) # 77x76

        # EQUALIZAR imp e exp para o Brasil
        """Hipótese subjacente da modelagem para as compras e vendas ao Brasil
        => compras e vendas são realizadas apenas pelas atividades intermediarias
        => consumo final não compra direto de fora da região [PENSAR NISSO]
        """
        E = self.mipreg["total_produtos"][0:68] - self.mipreg.loc['total_insumos'][0:68]
        comprou, vendeu = [], []
        for eq in E:
            if eq >= 0:  # demanda maior que o produto => comprou
                comprou.append(eq)
                vendeu.append(0.0)
            else:        # produto maior que a demanda => vendeu
                comprou.append(0.0)
                vendeu.append(abs(eq))
        self.comprou = comprou
        self.vendeu = vendeu
        self.mipreg.loc['importado do Brasil'] = comprou + np.zeros(76-68).tolist()
        self.mipreg['exportado ao Brasil'] = vendeu + np.zeros(77-68).tolist()
        # soma tudo de novo
        self.mipreg.loc['total_insumos'][0:68] = self.mipreg.iloc[0:76,0:68].sum(axis=0)
        self.mipreg['total_produtos'] = self.mipreg.iloc[0:77,0:75].sum(axis=1)
        self.ajuste = self.avaliar(path)
        self.A = matriz_coeficientes_tecnicos(self.mipreg, fechada=False)
        self.Af = matriz_coeficientes_tecnicos(self.mipreg, fechada=True)
        self.L = matriz_leontief(self.A)
        self.Lf = matriz_leontief(self.Af)
        # empregos => p/ multiplicadores
        self.empregos_regiao = self.empregos[0:68].multiply(self.qL)
        self.multiplicadores = multiplicadores(self.mipreg, self.empregos_regiao, self.L, self.Lf)
        self.HRtras, self.HRfrente, self.chave = indice_HR(self.L)

        return None


    def avaliar(self, path=""):
        """Calcula a diferença entre o PIB municipal do IBGE e o estimado pela regionalização.
        res: str na forma 'MU74/2014/SP/MU350055ano2014.csv'

        PreçoBásico = PreçoConsumidor - MargemComércio - MargemTransporte -
        	ImpostoImportação - IPI - ICMS - OutrosImpostosExSubsídios

        => no agregado as margens de comércio e transporte se anulam
        	vale a relção VAbruto_mip (básico) = VAbruto_mun (consumidor) - Impostos líquidos de sub

        => nos setoriais precisaria distribuir as margens de transp e comercio
        	essas margens correspondem a ~10% do PIB e retirar impostos...
        	. VAbruto_mip serviços é tipo 10% subestimado
        	. VAbruto_mip agro e ind 10% sobrestimado

        => para medir a qualidade vale mesmo o valor para o PIB agregado
        	. os desagregados é mais para ter uma idéia das distorções

        """
        if not hasattr(self, 'ibge'):
            return None
        # vabM: valor adicionado bruto via dados IBGE
        # produto_interno_bruto_a_precos_correntes => m038
        # impostos_liquidos_de_subsidios_sobre_produtos_a_precos_correntes => m037
        vabM = self.ibge['m038'].astype(float).multiply(self.pesos).sum() - self.ibge['m037'].astype(float).multiply(self.pesos).sum()
        # vabR: valor adicionado bruto estimado pelo modelo de regionalização (R$1.000.000)
        # valor adicionado bruto = salários + contribuições sociais + margem + outros impostos e subsídeos
        v = ['salários', 'contribuições sociais', 'margem', 'outros impostos e subsídeos']
        vabR = self.mipreg["total_produtos"].loc[v].sum() * 1000
        desvioT = vabR/vabM
        # vab desagregados em 3 setores
        vabMagro = self.ibge['m032'].astype(float).multiply(self.pesos).sum()
        # valor_adicionado_bruto_da_industria_a_precos_correntes: m033
        vabMind = self.ibge['m033'].astype(float).multiply(self.pesos).sum()
        # valor_adicionado_bruto_dos_servicos_a_precos_correntes_exceto_ADESPSS: m034
        # valor_adicionado_bruto_ADESPSS_a_precos_correntes: m035
        vabMserv = self.ibge['m034'].astype(float).multiply(self.pesos).sum() + self.ibge['m035'].astype(float).multiply(self.pesos).sum()
        # dicionario para mapear 68 atividades em 3 setores
        map3 = carregar_compatibiliza_atividades_a_3(path)
        # vab via regionalização da mip
        vabRagro = self.mipreg[map3['agricultura']].loc[v].sum().sum() * 1000
        vabRind = self.mipreg[map3['indústria']].loc[v].sum().sum() * 1000
        vabRserv = self.mipreg[map3['serviços']].loc[v].sum().sum() * 1000
        desvioA = vabRagro/vabMagro
        desvioI = vabRind/vabMind
        desvioS = vabRserv/vabMserv
        # casos limítrofes
        if vabRagro == 0: desvioA = 1.0
        if vabRind == 0: desvioI = 1.0
        if vabRserv == 0: desvioS = 1.0
        # 1: ajuste perfeito
        # <1: sub estimado
        # >1: sobre estimado
        # VALE a igualdade: vabM == vabMagro+vabMind+vabMserv
        ajuste = {
            'PIB': desvioT,
            'agricultura': desvioA,
            'indústria': desvioI,
            'serviços': desvioS,
            'nota': '1.0 significa ajuste perfeito; >1.0 sobrestimativa; <1.0 subestimativa',
            'erro PIB': vabR - vabM,
            'erro agricultura': vabRagro - vabMagro,
            'erro indústria': vabRind - vabMind,
            'erro serviços': vabRserv - vabMserv,
            'erro': 'diferença em R$ 1.000 entre o estimado e a referência IBGE',
            'partagro': round(100*vabMagro/vabM, 2),
            'partind': round(100*vabMind/vabM, 2),
            'partserv': round(100*vabMserv/vabM, 2),
        }
        return ajuste


    def salvar(self):
        """Salva um excel com mipita regionalizada, As, Ls, e multiplicadores"""

        if hasattr(self, 'mipreg'):
            atividades = [self.codigos[i] + ": " + self.atividades[i] for i in range(68)]
            ler = atividades + list(self.mipreg.index[68:]) # index legivel
            sheet1 = self.mipreg
            sheet1.index = ler
            sheet2 = self.multiplicadores
            sheet3 = self.A
            sheet3.index = atividades
            sheet4 = self.L
            sheet4.index = atividades
            sheet5 = self.Af
            sheet5.index = atividades + ['famílias']
            sheet6 = self.Lf
            sheet6.index = atividades + ['famílias']

            with pd.ExcelWriter(self.recorte + '.xlsx') as writer:
                sheet1.to_excel(writer, sheet_name='MIP ' + self.ano)
                sheet2.to_excel(writer, sheet_name='Multiplicadores')
                sheet3.to_excel(writer, sheet_name='Matriz A')
                sheet4.to_excel(writer, sheet_name='Matriz L')
                sheet5.to_excel(writer, sheet_name='Matriz A fechada')
                sheet6.to_excel(writer, sheet_name='Matriz L fechada')
        else:
            print('[oo] Não há matriz regionalizada para salvar')


    def fornecedores(self, j=None, q=5):
        """Setores encadeados a montante, i.e, os principais fornecedores do setor j.
        """
        if not j: j = '0191'
        j = str(j)
        print('Principais FORNECEDORES do setor', j)
        mapa = [[self.L.at[i,j], i, self.legenda[i]] for i in self.L[j].index]
        mapa.sort(reverse=True)
        mapa[0][0] -= 1
        mapa.sort(reverse=True)
        return pd.DataFrame(mapa[:q])


    def compradores(self, i=None, q=5):
        """Setores encadeados a montante, i.e, os principais fornecedores do setor j.
        """
        if not i: i = '0191'
        i = str(i)
        print('Principais COMPRADORES do setor', i)
        mapa = [[self.L.at[i,j], j, self.legenda[j]] for j in self.L[i].index]
        mapa.sort(reverse=True)
        mapa[0][0] -= 1
        mapa.sort(reverse=True)
        return pd.DataFrame(mapa[:q])



class Nereus:
    """Cria objeto do tipo Nereus a partir dos dados preparados pelo Nereus FEA-USP.

    > a matriz original do IBGE tem 67 setores. A matriz Nereus decompõe em dois setores
    o comércio, separando o comércio de veículos.

    """

    def __init__(self, ano, path=""):
        #--> objeto base
        self.ano = str(ano)
        self.recorte = "Brasil"
        self.fonte = "NEREUS (FEA-USP)"
        self.nereus = carregar_mip_nereus(self.ano, path)  # 93 x 77
        self.mipita = None
        self.codigos, self.atividades, self.legenda = carregar_atividades68(path=path)
        #<--
        self.sxs = self.nereus.iloc[0:68,0:68]
        self.sxs.index = self.codigos
        self.sxs.columns = self.codigos

        self.importado_inter = self.nereus.iloc[69:70,0:68]
        self.importado_inter.columns = self.codigos
        self.importado_inter_impostos = self.nereus.iloc[70:71,0:68]
        self.importado_inter_impostos.columns = self.codigos
        self.impostos_inter = self.nereus.iloc[71:77,0:68]
        self.impostos_inter.columns = self.codigos

        self.adicionados = self.nereus.iloc[78:91,0:68]
        self.adicionados.columns = self.codigos
        self.remuneracoes = self.nereus.iloc[78:84,0:68]
        self.remuneracoes.columns = self.codigos
        self.salarios = self.nereus.iloc[79:80,0:68]
        self.salarios.columns = self.codigos
        self.margem = self.nereus.iloc[84:87,0:68]
        self.margem.columns = self.codigos
        self.outros_impostos = self.nereus.iloc[88:90,0:68]
        self.outros_impostos.columns = self.codigos

        self.total_da_economia_insumos = self.nereus.iloc[91:92,0:68]
        self.total_da_economia_insumos.columns = self.codigos

        self.demandas = self.nereus.iloc[0:68,69:76]
        self.demandas.index = self.codigos
        self.exporta = self.nereus.iloc[0:68,69:70]
        self.exporta.index = self.codigos
        self.governo = self.nereus.iloc[0:68,70:71]
        self.governo.index = self.codigos
        self.sfl = self.nereus.iloc[0:68,71:72]
        self.sfl.index = self.codigos
        self.familias = self.nereus.iloc[0:68,72:73]
        self.familias.index = self.codigos
        self.capital_fixo = self.nereus.iloc[0:68,73:74]
        self.capital_fixo.index = self.codigos
        self.estoque = self.nereus.iloc[0:68,74:75]
        self.estoque.index = self.codigos

        self.importado_final = self.nereus.iloc[69:70,69:76]
        self.importado_final_impostos = self.nereus.iloc[70:71,69:76]
        self.impostos_final = self.nereus.iloc[71:77,69:76]

        self.total_da_economia_produtos = self.nereus['demanda total']

        self.empregos = self.nereus.loc['fator trabalho (ocupações)'][0:68]
        self.empregos.index = self.codigos

        self.mipita = self.mipita_nereus()
        self.A = matriz_coeficientes_tecnicos(self.mipita, fechada=False)
        self.Af = matriz_coeficientes_tecnicos(self.mipita, fechada=True)
        self.L = matriz_leontief(self.A)
        self.Lf = matriz_leontief(self.Af)
        self.multiplicadores = multiplicadores(self.mipita, self.empregos, self.L, self.Lf)
        self.HRtras, self.HRfrente, self.chave = indice_HR(self.L)


    def __repr__(self):
        r = "Matriz de Insumo-Produto - Brasil\n"
        r += "---------------------------------\n"
        r += self.ano
        r += "\ndados: " + self.fonte
        return r


    def mipita_nereus(self):
        """MIP padrão ITA apenas com os dados essenciais, obtida a partir da mip Nereus."""
        # A
        # editar e adicionar blocos sob o bloco SxS
        # passo 1 - importado do mundo e do Br
        importado = self.importado_inter
        importado.rename({"importado":"importado do mundo"}, axis=0, inplace=True)
        impostos_imp = self.importado_inter_impostos
        impostos_imp.rename({"imp import":"impostos de importação"}, axis=0, inplace=True)
        impbr = pd.DataFrame({"importado do Brasil":np.zeros(68)}).T
        impbr.columns = self.codigos
        passo1 = pd.concat([self.sxs, importado, impostos_imp, impbr], axis=0)
        # passo 2 - impostos
        impostos = pd.DataFrame({"impostos": self.impostos_inter.sum()}).T
        passo2 = pd.concat([passo1, impostos], axis=0)
        # passo 3 - componentes do valor adiocionado
        salario = pd.DataFrame({"salários": self.adicionados.loc["salários"]}).T
        previ = pd.DataFrame({"contribuições sociais":
            (self.adicionados.loc["remunerações"].values - salario.values)[0]
        }, index = self.codigos).T
        margem = pd.DataFrame(
            {"margem": self.adicionados.loc["excedente operacional bruto e rendimento misto bruto"]}
        ).T
        outros = pd.DataFrame({"outros impostos e subsídeos":
            self.adicionados.loc["outros impostos sobre a produção"] + self.adicionados.loc["outros subsídios à produção"]}
        ).T
        passo3 = pd.concat([passo2, salario, previ, margem, outros], axis=0)
        # soma de todos os insumos
        insumos = pd.DataFrame({"total_insumos":passo3.sum(axis=0)})  # soma as linhas
        passo4 = pd.concat([passo3, insumos.T], axis=0)
        # B
        # completar colunas à direita do bloco SxS, nesse ponto com 77 rows x 68 columns
        # passo 5 - importado do mundo e do Br
        demandas = self.demandas.iloc[0:68, 0:6]
        colunas = ['exportado ao mundo', 'governo', 'isfl', 'famílias', 'capital fixo', 'estoque']
        demandas.columns = colunas
        importado = self.importado_final.iloc[0:1, 0:6]
        importado.columns = colunas
        importado.rename({"importado":"importado do mundo"}, axis=0, inplace=True)
        impostos_imp = self.importado_final_impostos.iloc[0:1, 0:6]
        impostos_imp.columns = colunas
        impostos_imp.rename({"imp import":"impostos de importação"}, axis=0, inplace=True)
        impbr = pd.DataFrame({"importado do Brasil":np.zeros(6)}).T
        impbr.columns = colunas
        passo5 = pd.concat([demandas, importado, impostos_imp, impbr], axis=0)
        # passo 6 - impostos
        impostos = pd.DataFrame({"impostos": self.impostos_final.sum()[0:6]}).T
        impostos.columns = colunas
        passo6 = pd.concat([passo5, impostos], axis=0)
        # passo 7 - componentes do valor adiocionado ZERADOS
        salario = pd.DataFrame({"salários": np.zeros(6)}).T
        salario.columns = colunas
        previ = pd.DataFrame({"contribuições sociais": np.zeros(6)}).T
        previ.columns = colunas
        margem = pd.DataFrame({"margem": np.zeros(6)}).T
        margem.columns = colunas
        outros = pd.DataFrame({"outros impostos e subsídeos":np.zeros(6)}).T
        outros.columns = colunas
        insumos = pd.DataFrame({"total_insumos": np.zeros(6)}).T
        insumos.columns = colunas
        passo7 = pd.concat([passo6, salario, previ, margem, outros, insumos], axis=0)
        # C
        # adicionar coluna de exp para Brasil e juntar
        passo7.insert(1, "exportado ao Brasil", np.zeros(77))
        passo7.rename({"exportação de bens e serviços":"exportado ao mundo"}, axis=1, inplace=True)
        # passo 8 - juntar
        passo8 = pd.concat([passo4, passo7], axis=1)
        # D - totais
        produtos = pd.DataFrame({"total_produtos":passo8.sum(axis=1)})  # soma as colunas
        passo9 = pd.concat([passo8, produtos], axis=1)
        return passo9


    def extrair_mipita(self):
        """Extrai dados no padrão mipita."""
        M = Mipita()
        M.ano = self.ano
        M.recorte = self.recorte
        M.fonte = self.fonte
        M.mipita = self.mipita
        M.codigos = self.codigos
        M.atividades = self.atividades
        M.legenda = self.legenda
        M.empregos = self.empregos[0:68]
        return M


    def fornecedores(self, j=None, q=5):
        """Setores encadeados a montante, i.e, os principais fornecedores do setor j.
        """
        if not j: j = '0191'
        j = str(j)
        print('Principais FORNECEDORES do setor', j)
        mapa = [[self.L.at[i,j], i, self.legenda[i]] for i in self.L[j].index]
        mapa.sort(reverse=True)
        mapa[0][0] -= 1
        mapa.sort(reverse=True)
        return pd.DataFrame(mapa[:q])


    def compradores(self, i=None, q=5):
        """Setores encadeados a montante, i.e, os principais fornecedores do setor j.
        """
        if not i: i = '0191'
        i = str(i)
        print('Principais COMPRADORES do setor', i)
        mapa = [[self.L.at[i,j], j, self.legenda[j]] for j in self.L[i].index]
        mapa.sort(reverse=True)
        mapa[0][0] -= 1
        mapa.sort(reverse=True)
        return pd.DataFrame(mapa[:q])


    def resumo(self):
        """Relatório com as diversas identidades contábeis existentes na Mip."""
        tppb = self.mipita['total_produtos'].loc['total_insumos']
        importa = self.mipita['total_produtos'].loc[['importado do mundo', 'importado do Brasil']]
        impostos = self.mipita['total_produtos'].loc[['impostos de importação', 'impostos']].sum()
        produção_inter = self.mipita.iloc[0:68, 0:68].sum().sum()
        valor_adicionado_bruto = self.mipita['total_produtos'].loc[
            ['salários', 'contribuições sociais', 'margem', 'outros impostos e subsídeos']].sum()
        demanda_final = self.mipita[['exportado ao mundo', 'exportado ao Brasil', 'governo',
            'isfl', 'famílias', 'capital fixo', 'estoque']].sum().sum()

        to_df = [
            {"Produção intermediária": produção_inter},  # preços básicos
            {"Importação de bens e serviços": importa},
            {"Impostos intermediários": tppb + impostos - demanda_final - produção_inter},
            {"Consumo intermediário": tppb + importa + impostos - demanda_final},  # preços consumidor
            {"Valor Adicionado Bruto": valor_adicionado_bruto},
            {"Total de impostos líquidos de subsídeos": impostos},
            {"Produto Interno Bruto": valor_adicionado_bruto + impostos},
            {"Demanda final": demanda_final},  # preços consumidor
            {"Total do produto": tppb},
            {"Total da economia": tppb + importa},  # preços básicos
            {"Oferta total a preços de consumidor": tppb + importa + impostos},
        ]

        return to_df


def matriz_coeficientes_tecnicos(mip, fechada=False):
    """Gerador da Matriz A

    mip: DataFrame (matriz insumo-produto no padrão "mipita")
    fechada: bool (se True calcula matriz A incluindo remunerações e consumo das famílias)

    retorna
    A: DataFrame (matriz A dos coeficientes técnicos)
    na qual a[ij] = z[ij]/x[j], valor comprado de i por j / total da produção de j

    NOTAS:
    [cf] Blair e Miller 2009, p.34-41 @pdf 66

    """
    setores = mip.iloc[0:68, 0:68]
    # o coeficiente técnico correponde à parcela vinda do setor i sobre o total de insumos
    total = mip.loc['total_insumos'][0:68]   # vetor
    A = setores.divide(total, axis=1)   # divide no sentido das colunas
    if fechada:
        """
        seguindo a notação de Miller e Blair (exemplo p.38)
        e a discussão detalhada em Zackiewicz (2021)

        Af = | A_  hc |
             | hr  h  |

        A_: matriz A sem o setor 9700 serviços domésticos
        hc: consumo das famílias
        hr: remuneração das famílias (salário + cs)
        h: remuneração familías => famílias
        """
        # coef remuneração: remu/total insumos
        remu = mip.loc[['salários', 'contribuições sociais']].sum()[0:67]
        hr = remu/total[0:67]
        input_familias = mip['famílias'].sum()
        """
        o total de insumos para as famílias incluem:
        . importados do mundo e do Br
        . impostos pagos
        . => inclui remuneração recebida via setor 9700

        => o valor antes indicado como consumo de servico 9700 em familias
        vira salarios => BUT a soma não muda
        vira tbem valor adicionado pelas familias
        """
        hc = mip['famílias'][0:67]/input_familias
        h = mip.loc[['salários', 'contribuições sociais']].sum()['9700']/input_familias
        Af = A.iloc[0:67, 0:67]   # A_
        hr['famílias'] = h
        Af['famílias'] = hc
        Af.loc['famílias'] = hr  # com h já incluso
        return Af
    return A


def matriz_leontief(A):
    """Gerador da Matriz L

    A: DataFrame (matriz A dos coeficientes técnicos)

    retorna
    L: DataFrame (matriz L de Leontief)
    """
    I = np.identity(len(A.index))
    L = np.linalg.inv(I-A)
    return pd.DataFrame(L, index=A.index, columns=A.columns)


def multiplicadores(mip, empregos, L, Lf):
    """
    Calcula os diferentes multiplicadores associados à matriz de insumo-produto
    [cf] Miller e Blair 2009, p.243-260  @pdf 275
    [oo] tabelas 6.3 (p.258) e 6.4 (p.259)

    => efeitos do aumento de 1 milhão de reais na demanda do setor j (sempre relativo
    ao produto):
    eD: efeito direto
    eDN: efeito direto + indireto
    eDNZ: efeito direto + indireto + induzido (truncado)
    eDNZ+: efeito direto + indireto + induzido (total, sobrestimado)

    => efeitos do aumento de 1 [unidade] na demanda do setor j (relativo à unidade
    do multiplicador), também chamados de Tipo I e Tipo II:
    mD: efeito direto
    mDN: efeito direto + indireto
    mDNZ: efeito direto + indireto + induzido (truncado)
    mDNZ+: efeito direto + indireto + induzido (total, sobrestimado)

    => todos os 8 para:
    produto
    valor adicionado
    salários
    emprego

    => parâmetros:
    mip: matriz-insumo produto no padrao mipita
    empregos: vetor de número de empregos nos j setores
    L: matriz Leontief aberta (68 setores)
    Lf: matriz Leontief fechada (68 setores, famílias no lugar de 9700)

    => retorna:
    DataFrame [28 multiplicadores x 68 setores]
    """

    # vetores identidade 1x68
    i68 = pd.DataFrame({'i': [1 for _ in range(68)]}, index = L.index).T
    i68f = pd.DataFrame({'i': [1 for _ in range(68)]}, index = Lf.index).T

    """
    Multiplicadores de Produto
    --------------------------
    """
    # Efeitos Diretos => por definição é o próprio aumento da demanda
    eD_produto = i68

    # Efeito Direto + Indireto: dados pela matriz L
    # eq. 6.5 (o produto escalar com um vetor unitário dá a soma das colunas)
    eDN_produto = i68.dot(L)

    # Efeito Direto + Indireto + Induzido Total: dados pela matriz Lf
    # eq. 6.6
    eDNZs_produto = i68f.dot(Lf)

    # Efeito Direto + Indireto + Induzido Truncado: exclui famílias
    # eq. 6.10
    eDNZ_produto = eDNZs_produto.subtract(Lf.loc['famílias'])

    # no caso PRODUTO, os multiplicadores tipo I e II são iguais aos efeitos

    produto = pd.concat([
        eD_produto,
        eDN_produto,
        eDNZ_produto,
        eDNZs_produto,
    ])
    produto.index = [
        'eD produto', 'eDN produto', 'eDNZ produto', 'eDNZ+ produto',
    ]

    """
    Multiplicadores de Valor Adicionado
    -----------------------------------
    """
    # vetor linha do va 1x68 [com va do setor 9700]
    # o mesmo valor para va vale para o caso com famílias]
    ad = ['salários', 'contribuições sociais', 'margem']
    va = pd.DataFrame(mip[L.columns].loc[ad].sum()).T
    vaf = va.copy()
    vaf.columns = Lf.index

    # vetor linha do input total
    X = pd.DataFrame(mip[L.columns].loc['total_insumos']).T
    # input total fechado para famílias
    Xf = pd.DataFrame(mip[Lf.columns].loc['total_insumos']).T
    Xf['famílias'] = mip['famílias'].sum()

    # vetor linha va/input => efeitos diretos
    eD_va = va.divide(X.values)

    # efeitos diretos e indiretos
    eDN_va = eD_va.dot(L)

    # efeitos diretos e indiretos e induzidos totais
    # precisa antes calcular o efeito direto para o caso fechado
    # pq X != Xf
    eD_vaf = vaf.divide(Xf.values)
    eDNZs_va = eD_vaf.dot(Lf)
    # o produto escalar é equivamente à soma nas colunas, com cada elemento
    # ponderado pelo correspondente em eD_vaf
    # cada linha i de Lf é multiplicada pelo i-esimo elemento do vetor
    # eDNZs_va = Lf.multiply(eD_vaf.values, axis=0).sum()

    # efeitos diretos e indiretos e induzidos truncados
    # subtrai a linha ponderada da matriz LF para famílias
    eDNZ_va = eDNZs_va.subtract(Lf.loc['famílias'] * eD_vaf['famílias'].values[0])

    # multiplicadores tipo I e II
    mD_va = eD_va.divide(eD_va)
    mDN_va = eDN_va.divide(eD_va)
    mDNZ_va = eDNZ_va.divide(eD_vaf)
    mDNZs_va = eDNZs_va.divide(eD_vaf)

    adicionado = pd.concat([
        eD_va,
        eDN_va,
        eDNZ_va,
        eDNZs_va,
        mD_va,
        mDN_va,
        mDNZ_va,
        mDNZs_va,
    ])
    adicionado.index = [
        'eD adicionado', 'eDN adicionado', 'eDNZ adicionado', 'eDNZ+ adicionado',
        'mD adicionado', 'mDN adicionado', 'mDNZ adicionado', 'mDNZ+ adicionado',
    ]

    # Lad = pd.DataFrame(
    #         np.diag(va68.values[0]).dot(np.linalg.inv(np.diag(x68.values[0]))).dot(L),  # eq. 6.18
    #         index=L.index, columns=L.columns
    #     )

    """
    Multiplicadores de Salários
    ---------------------------
    """
    # vetor linha dos salarios 1x68 [com salários do setor 9700]
    # o mesmo valor para os salários vale para o caso com famílias]
    sal = pd.DataFrame(mip[L.columns].loc['salários']).T
    salf = sal.copy()
    salf.columns = Lf.index

    # vetor linha do input total
    X = pd.DataFrame(mip[L.columns].loc['total_insumos']).T
    # input total fechado para famílias
    Xf = pd.DataFrame(mip[Lf.columns].loc['total_insumos']).T
    Xf['famílias'] = mip['famílias'].sum()

    # vetor linha dos salarios/input => efeitos diretos
    eD_sal = sal.divide(X.values)

    # efeitos diretos e indiretos
    eDN_sal = eD_sal.dot(L)

    # efeitos diretos e indiretos e induzidos totais
    # precisa antes calcular o efeito direto para o caso fechado
    # pq X != Xf
    eD_salf = salf.divide(Xf.values)
    eDNZs_sal = eD_salf.dot(Lf)

    # efeitos diretos e indiretos e induzidos truncados
    # subtrai a linha ponderada da matriz LF para famílias
    eDNZ_sal = eDNZs_sal.subtract(Lf.loc['famílias'] * eD_salf['famílias'].values[0])

    # multiplicadores tipo I e II
    mD_sal = eD_sal.divide(eD_sal)
    mDN_sal = eDN_sal.divide(eD_sal)
    mDNZ_sal = eDNZ_sal.divide(eD_salf)
    mDNZs_sal = eDNZs_sal.divide(eD_salf)

    salarios = pd.concat([
        eD_sal,
        eDN_sal,
        eDNZ_sal,
        eDNZs_sal,
        mD_sal,
        mDN_sal,
        mDNZ_sal,
        mDNZs_sal,
    ])
    salarios.index = [
        'eD salários', 'eDN salários', 'eDNZ salários', 'eDNZ+ salários',
        'mD salários', 'mDN salários', 'mDNZ salários', 'mDNZ+ salários',
    ]

    # Lr = pd.DataFrame(
    #         np.diag(sal68.values[0]).dot(np.linalg.inv(np.diag(x68.values[0]))).dot(L),  # eq. 6.18
    #         index=L.index, columns=L.columns
    #     )

    """
    Multiplicadores de Emprego
    --------------------------
    """
    # vetor linha dos empregos 1x68 [com empregos do setor 9700]
    # o mesmo valor para os empregos vale para o caso com famílias]
    emp = pd.DataFrame(empregos[L.columns]).T
    empf = emp.copy()
    empf.columns = Lf.index

    # vetor linha do input total
    X = pd.DataFrame(mip[L.columns].loc['total_insumos']).T
    # input total fechado para famílias
    Xf = pd.DataFrame(mip[Lf.columns].loc['total_insumos']).T
    Xf['famílias'] = mip['famílias'].sum()

    # vetor linha dos empregos/input => efeitos diretos
    eD_emp = emp.divide(X.values)

    # efeitos diretos e indiretos
    eDN_emp = eD_emp.dot(L)

    # efeitos diretos e indiretos e induzidos totais
    # precisa antes calcular o efeito direto para o caso fechado
    # pq X != Xf
    eD_empf = empf.divide(Xf.values)
    eDNZs_emp = eD_empf.dot(Lf)

    # efeitos diretos e indiretos e induzidos truncados
    eDNZ_emp = eDNZs_emp.subtract(Lf.loc['famílias'] * eD_empf['famílias'].values[0])

    # multiplicadores tipo I e II
    mD_emp = eD_emp.divide(eD_emp)
    mDN_emp = eDN_emp.divide(eD_emp)
    mDNZ_emp = eDNZ_emp.divide(eD_empf)
    mDNZs_emp = eDNZs_emp.divide(eD_empf)

    emprego = pd.concat([
        eD_emp,
        eDN_emp,
        eDNZ_emp,
        eDNZs_emp,
        mD_emp,
        mDN_emp,
        mDNZ_emp,
        mDNZs_emp,
    ])
    emprego.index = [
        'eD emprego', 'eDN emprego', 'eDNZ emprego', 'eDNZ+ emprego',
        'mD emprego', 'mDN emprego', 'mDNZ emprego', 'mDNZ+ emprego',
    ]

    # Lem = pd.DataFrame(
    #         np.diag(em68.values[0]).dot(np.linalg.inv(np.diag(x68.values[0]))).dot(L),  # eq. 6.18
    #         index=L.index, columns=L.columns
    #     )

    df_multi = pd.concat([produto, adicionado, salarios, emprego], axis=0)

    return df_multi


def indice_HR(L):
    """Índice de Ligação de Hirschman-Rasmussen

    Mede poder de encadeamento das atividades produtivas da economia
    Para trás (T): o quanto um setor demanda dos demais setores da economia
    Para frente (F): o quanto um setor é demandado pelos demais setores da economia

    T > 1 e F > 1 define um SETOR CHAVE
    """

    Lj = L.sum(axis=0)  # soma dos elementos das colunas
    Li = L.sum(axis=1)  # soma dos elementos das linhas
    L_ = Lj.sum()       # soma de todos os elementos de L
    n = L.shape[0]      # setores
    mLj = Lj/n          # media dos inputs
    mLi = Li/n          # media dos outputs
    mL = L_/(n*n)       # media global

    T = mLj/mL          # para trás: PODER DE DISPERSÂO
    F = mLi/mL          # para frente: SENSIBILIDADE DA DISPERSAO

    chave = []
    for j in T.index:
        ch = False
        if T[j] > 1 and F[j] > 1:
            ch = True
        chave.append((j, ch))

    return T, F, chave



"""
## COMO USAR

import matriz
path = '/home/mauro/econodata/'
n = matriz.Nereus(2015, path=path)  # objeto Mip Nereus

m1 = n.extrair_mipita()   # cria objeto Mipita
m1.regionalizar(['354990'], recorte="SJC", path=path)  # objeto Mipita regionalizado e avaliado
m1.salvar()

m2 = n.extrair_mipita()   # cria objeto Mipita
m2.regionalizar(['354990'], recorte="SJC Comex",
    exporta='comex', importa='comex',
    path=path)
m2.salvar()





m.regionalizar(['354990', '350850'], pesos=[0.7, 0.7])   # exemplo com peso


m.mipita   # mostra a matriz Brasil no formato mipita
m.mipreg   # mostra a matriz regionalizada (se construída)
m.ajuste   # mostra a qualidade da regionalização
m.multiplicadores  # mostra os multiplicadores
m.multiplicadores['5100']  # apenas para o setor de transporte aéreo
m.multiplicadores['5100'].to_csv('nome_do_arquivo.csv')  # exporta csv



import matriz
path = '/home/mauro/econodata/'
n = matriz.Nereus(2010, path=path)
m = n.extrair_mipita()
m.regionalizar(['354990'], path=path)




"""

def percentual_demanda(m, n):
    ''' entra a matriz regionalizada m, para testar identidade
    com o metodo expresso em Guilhoto 2011'''

    P = []
    for j in range(68):
        X = m.mipreg.loc['total_insumos'][j]
        E = m.mipreg['exportado ao Brasil'][j] + m.mipreg['exportado ao mundo'][j]
        M = m.mipreg.loc['importado do Brasil'][j] + m.mipreg.loc['importado do mundo'][j]
        if X-E+M == 0.0:
            p = 0.0
        else:
            p = (X-E)/(X-E+M)
        P.append(p)

    Ar = np.matmul(np.diag(P), n.A)

    """Ops, não bate com o meu método..."""

    return Ar
