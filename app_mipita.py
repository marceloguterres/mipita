# -*- coding: utf-8 -*-
"""
Spyder Editor

@author: guterres

"""
#-----------------------------------------------------------------------------------
# Bibliotecas Python
import numpy as np
import pandas as pd
import requests
import json

# Bibliotecas Impacto
import matriz
import auxrais
from lago import *
from auxrais import *
from auxdata import *
import streamlit as st

#=============================================================================
# Funçoes
#=============================================================================

def table_br(parametro_br):
    if parametro_br == 'multiplicadores_br':
        table = multiplicadores_br
    else:
        table = multiplicadores_ta_br
    return table


@st.cache
def convert_df(df):
   return df.to_csv().encode('utf-8')


#=============================================================================
# Listas definidas
#=============================================================================


list_codes  = pd.read_csv('codes_municipios.csv', sep=';', encoding='latin-1').astype(str)
list_br     = ['multiplicadores_br', 'multiplicadores_ta_br' ]



#=============================================================================
# Set page config
#=============================================================================
st.apptitle = 'Projeto IMPACTO'

st.title('🔍 Análise Insumo Produto')


with st.expander("Veja nota informativa sobre os multiplicadores: 👉"):
     st.markdown("""Os multiplicadoes são medidas sintéticas obtidas da Matriz 
L e da Matriz L fechada (que modela os impactos diretos+indiretos+induzidos ao 
incorporar o trabalho como mais um setor produtivo;

-e: efeito a partir de um acréscimo de 1 unidade na demanda;

-m: multiplicador sobre a própria unidade (Tipo 1 e Tipo 2), ex sobre acréscimo de 1 unidade de emprego;

-D: direto;

-N: indireto; 
 
-Z: induzido;

-Z+ induzido plus (sobrestimado por incorporar também o efeito-renda sobre os salários""")
                   

#=============================================================================
# Configurção sidebar
#=============================================================================
with st.sidebar:
    
    st.title('🎯 Projeto Impacto')
    st.info("🎈**VERSÃO:** 2022.01.03 - [ITA](https://www.ita.br)" )
    st.sidebar.header('Seleção dos parâmetros') 
    
    ano             = st.sidebar.slider('Ano', 2010, 2017, 2017)  # min, max, default    
    code_municipio  = st.selectbox('Código IBGE do Município?', list_codes, index= 3826)
    tx_demanda_setor= st.number_input('Varição da demanda do setor selecionado?')   
    code_setor      = st.text_input('Código do setor?', '5100')
    metrica         = st.text_input('Métrica?',  'Valor do Trabalho (R$ nom)')
    classe          = st.text_input('classe?',  '5111')
    ano_str = str(ano)
    
    
#=============================================================================
# Análise Insumo Produto Nacional br
#=============================================================================

nereus = matriz.Nereus(ano)  #carrega módulo matriz e puxa dados na S3 para a MIP 2015
mipita_br = nereus.mipita
A_br      = nereus.A
L_br      = nereus.L  
Af_br     = nereus.Af
Lf_br     = nereus.Lf 

multiplicadores_br    = nereus.multiplicadores 
multiplicadores_setor_br = nereus.multiplicadores[code_setor] 

demanda_setor_br = nereus.mipita.loc[code_setor]['total_produtos']
impactos_setor_br = multiplicadores_br[code_setor] * demanda_setor_br  * tx_demanda_setor * 1

                                       
#=============================================================================
# Análise Insumo Produto Regionalizada (xx)
#=============================================================================

mipita_xx = nereus.extrair_mipita()   
mipita_xx.preparar_qL([code_municipio]) 
qL = mipita_xx.qL                
propT = mipita_xx.propT                  
mipita_xx.regionalizar() 
A_xx = mipita_xx.A                      
mipreg_xx = mipita_xx.mipreg             
ajuste_xx = mipita_xx.ajuste
compradores_xx  = mipita_xx.compradores(i=code_setor) 
fornecedores_xx = mipita_xx.fornecedores(j=code_setor, q=10)

           
#=============================================================================
# Modelo simplificado para entender e estudar o comportamento do modelo 
# interregional de ISARD (yy)
# A matriz A_yy é a matriz Brasil menos a regionalizada para xx
#=============================================================================

mipita_yy = nereus.extrair_mipita()
mipita_yy.preparar_qL([code_municipio], exceto=True) 
mipita_yy.regionalizar()
A_yy = mipita_yy.A

A_xy = A_br.subtract(A_yy)
A_yx = A_br.subtract(A_xx)

A_x = pd.concat([A_xx, A_xy], axis=1) 
A_y = pd.concat([A_yx, A_yy], axis=1)
nomes = nereus.codigos + [i+'_' for i in nereus.codigos]
A_intreg = pd.concat([A_x, A_y], axis=0)
A_intreg.index = nomes
A_intreg.columns = nomes
L_intreg = matriz.matriz_leontief(A_intreg)

#=============================================================================
# Desagregação setorial da MIP
#=============================================================================

url = "https://econodata.s3.amazonaws.com/"

# para 68 atividades agregadas para o Brasil
_br68 = "RAIS/"+ano_str+"/Brasil68ano"+ano_str+".csv"
br68 = pd.read_csv(url+_br68, dtype={'Atividades_68':str}, index_col=0)


# para 673 classes agregados para o Brasil
_br673 = "RAIS/"+ano_str+"/Brasil673ano"+ano_str+".csv"
br673 = pd.read_csv(url+_br673, dtype={'Classe CNAE':str}, index_col=0)


res = "Classificas/compatibiliza673a68.json"
compa = json.loads(requests.get(url+res).text)

aereo = [s['classes'] for s in compa if s['atividade'] == code_setor][0]

# dados RAIS para a atividade 5100 
raisA = br68[br68['Atividades_68'] ==  code_setor]

br673.index = [a[0:4] for a in br673['Classe CNAE']]  # precisa arrumar o index para ficar compatível (4 dígitos)
raisB = br673.loc[aereo]

metrica = 'Valor do Trabalho (R$ nom)'  
total_atividade = raisA[metrica].values[0]
prop = raisB[metrica] / total_atividade

colunas = {}
for classe in aereo:
  colunas[classe+'c'] = nereus.A[code_setor]

df = pd.DataFrame(colunas)
Atemp = pd.concat([nereus.A, df], axis=1)  
Atemp = Atemp.drop(columns=[code_setor])


linhas = {}
for classe in aereo:
  linhas[classe+'c'] = nereus.A.loc[code_setor] * prop[classe]   


df2 = pd.DataFrame(linhas).T       
df2 = df2.drop(columns=[code_setor])   

Atemp2 = pd.concat([Atemp, df2], axis=0)


miolo = {}
for classe in aereo:
  miolo[classe+'c'] = Atemp2.at[code_setor, classe+'c'] * prop

df3 = pd.DataFrame(miolo)
df3.index=[classe+'c' for classe in aereo]

novos = [classe+'c' for classe in aereo]
Atemp2.loc[novos, novos] = df3  


Ad = Atemp2.drop(code_setor)
Ld = matriz.matriz_leontief(Ad)   # método que está no objeto matriz e calcula a inv(I-A)



#=============================================================================
# Interface Análise Insumo Produto Nacional br
#=============================================================================

"""
---
"""

st.title('🎯 Resultados MIP Brasil')

csv = convert_df(mipita_br)
st.download_button("Press to Download Matriz MIPITA BR", 
                   csv,"mipita_br.csv", 
                   "text/csv", 
                   key='download-csv')

csv = convert_df(A_br)
st.download_button("Press to Download Matriz A", 
                   csv,"A_br.csv", 
                   "text/csv", 
                   key='download-csv')

csv = convert_df(L_br)
st.download_button("Press to Download Matriz L", 
                   csv,"L_br.csv", 
                   "text/csv", 
                   key='download-csv')      


csv = convert_df(Af_br)
st.download_button("Press to Download Matriz Af", 
                   csv,"Af_br.csv", 
                   "text/csv", 
                   key='download-csv')   

csv = convert_df(Lf_br)
st.download_button("Press to Download Matriz Lf ", 
                   csv,"Lf_br.csv", 
                   "text/csv", 
                   key='download-csv')


csv = convert_df(multiplicadores_br)
st.download_button("Press to Download multiplicadores br ", 
                   csv,"multiplicadores_br .csv", 
                   "text/csv", 
                   key='download-csv')


csv = convert_df(multiplicadores_setor_br)
st.download_button("Press to Download multiplicadores setor", 
                   csv,"multiplicadores_setor_br.csv", 
                   "text/csv", 
                   key='download-csv')



#=============================================================================
# resultados br
#=============================================================================

"""
---
"""

st.title('🎯 Cálculo do impacto econômico Brasil') 

                   
"""
**Valor total da demanda Brasil do setor selecionado** (R$ milhões/ano): 
    
"""
st.write(demanda_setor_br)   


"""
**Multiplicadores para o Brasil do setor selecionado para análise:**

"""
st.table(multiplicadores_setor_br)


"""
**Impactos estimados pelos multiplicadores Brasil devido a uma 
variação na demanda nacional do setor selecionado:**

"""

with st.expander("Veja nota informativa dos impactos estimados pelos multiplicadores: 👉"):
     st.markdown("""Referem-se à alteração de 1 unidade na demanda agregada total
para encontrar os efeitos no conjunto da economia basta multiplicar pela 
quantidade de unidades perdidas ou ganhas nessa demanda.""")
st.table(impactos_setor_br)

"""
---
"""
     
#=============================================================================
# resultados Regionalização da MIP
#=============================================================================
                     
st.title('🎯 Regionalização da MIP')  

with st.expander("Veja nota informativa do processo de Regionalização: 👉"):
     st.markdown("""A matriz de insumo-produtos é um modelo estrutural de uma economia, 
ela retrata o total das transações entre os setores intermediários durante
o período de um ano, medidas pelo valor transacionado.

A regionalização consiste em obter modelos derivados do modelo nacional para 
territórios contidos no país. Para tanto, diferentes premissas e metodologias
podem ser adotadas, dependendo dos dados disponíveis e dos objetivos da análise.

Para o nosso problema, começamos com os modelos de região única (modelo regional simples). 
Estes focalizam a estrutura produtiva de uma determinada região e os impactos que ocorrem 
nesaa estrutura a partir de choques de demanda. O modelo de região única não
 captura os efeitos transbordados para o restante do país. Neste sentido, 
 por exemplo, aos efeitos operação de um aeroporto em uma determinada região 
 serão medidos apenas para a própria região. Os efeitos causados fora dessa região,
 mesmo que existam, são ignorados. O modelo regional simples funciona, assim, 
 como um building bloc para os passos subsequentes de sofisticação 
 da modelagem..""")
 
 
with st.expander("Veja nota informativa dos coeficientes locacionais: 👉"):
     st.markdown("""O processo de regionalização envolver obter uma 
                 estimativa da estrutura produtiva de região alvo.
                 Esta estimativa pode ser feita a partir da seguinte pergunta:
                   
                "Quanto de cada atividade econômica é realizada no território alvo"?
                
O coeficiente locacional fornece essa medida. Conceitualmente ele
fornece a proporção, variando de 0 a 1, de quanto uma determinada 
atividade econômica acontece em um determinado território com 
relação ao todo nacional.""")

with st.expander("Veja nota informativa do atributo propT: 👉"):
     st.markdown("""Enquanto o coeficiente locacional estima as proporções
                 do lado das atividades de produção o atributo .propT 
                 será empregado para estimar as colunas relacionadas à 
                 demanda final.""")
                 
with st.expander("Veja nota informativa do atributo ajuste: 👉"):
     st.markdown("""O atributo ajuste contém os parâmetros resultantes 
da avaliação da qualidade do ajuste. A partir da MIP 
é possível estimar o PIB municipal e seus componentes.

A avaliação consiste na comparação deste PIB estimado via MIP municipal 
e o PIB municipal divulgado oficialmente pelo IBGE e também informa a 
participação relativa de agricultura, indústrias e serviços (que inclui adm 
pública) no PIB local. 

O arquivo baixado durante o processamento contém o dicionário para
compatibizar as 68 atividades da MIP com esses 3 setores.""")                 
                 
 

"""
**Município selecionado**:
"""
st.table(list_codes.loc[list_codes['code'] == code_municipio])

csv = convert_df(A_xx)
st.download_button("Press to Download Matriz MIPITA REG", 
                         csv,"mipreg_xx.csv", 
                         "text/csv", 
                         key='download-csv')
    
            
csv = convert_df(A_xx)
st.download_button("Press to Download Matriz A REG", 
                   csv,"A_xx.csv", 
                   "text/csv", 
                   key='download-csv')

"""
**Os coeficientes locacionais**:    
"""
st.table(qL)


"""
**O atributo propT**:   
"""
st.write(propT)

"""
**Principais compradores do setor selecionado**:
"""
st.table(compradores_xx)


"""
**Principais forncedores do setor**:
"""
st.table(fornecedores_xx)


"""
**'O atributo ajuste**:
"""

#st.table(pd.DataFrame([ajuste_xx]))
st.write(ajuste_xx)


"""
---
"""

st.title('🎯 Modelo interregional') 

with st.expander("Veja nota informativa do Modelo interregional: 👉"):
     st.markdown("""O modelo interregional (modelo de Isard) consiste 
                 na expansão da matriz insumo-produto nacional de modo 
                 a identificar não apenas os fluxos intersetoriais, 
                 mas também os fluxos interregionais.
                 Desse modo, um modelo para N regiões irá expandir 
                 a matriz exponencialmente""")

"""
**Resultados do processamento do Modelo interregional**
"""

csv = convert_df(A_xx)
st.download_button("Press to Download Matriz A_xx", 
                         csv,"A_xx.csv", 
                         "text/csv", 
                         key='download-csv')


csv = convert_df(A_yy)
st.download_button("Press to Download Matriz A_yy", 
                         csv,"A_yy.csv", 
                         "text/csv", 
                         key='download-csv')


csv = convert_df(A_xy)
st.download_button("Press to Download Matriz A_xy", 
                         csv,"A_xy.csv", 
                         "text/csv", 
                         key='download-csv')


csv = convert_df(A_yx)
st.download_button("Press to Download Matriz A_yx", 
                         csv,"A_yx.csv", 
                         "text/csv", 
                         key='download-csv')


csv = convert_df(A_intreg)
st.download_button("Press to Download Matriz A_intreg", 
                         csv,"A_intreg.csv", 
                         "text/csv", 
                         key='download-csv')

csv = convert_df(L_intreg)
st.download_button("Press to Download Matriz A_intreg", 
                         csv,"L_intreg.csv", 
                         "text/csv", 
                         key='download-csv')

"""**O município comprou**:""" 
st.write(sum(mipita_xx.comprou))


"""**O município vendeu**:"""
st.write(sum(mipita_yy.vendeu))

"""↗️ **Um aumento de 1 unidade na agricultura de Brasil 
gera aumento na agricultura do município de**:"""
st.write(L_intreg.at['0191', '0191_'])

"""↗️ **Um aumento de 1 na agricultura município gera 
aumento na agricultura do Brasil de**:"""
L_intreg.at['0191_', '0191'] 

"""
---
"""




#=============================================================================
# Inerface desagregação setorial da MIP
#=============================================================================

st.title('🎯 Modelo de desagregação setorial da MIP')  

with st.expander("Veja nota informativa da desagregação setorial da MIP: 👉"):
     st.markdown("""**Descrição do problema:** A MIP é publicada com uma desagregação
                 setorial máxima de 68 setores,a partir da qual impactos, 
                 multiplicadores e outros indicadores podem
                 ser calculados. 
                 
*É possível desagregar um ou mais setores ainda mais? Sob quais hipóteses? 
Quais métodos podem ser usados para desagregar?
Uma vez desagregado um setor, como fica a interpretação dos 
impactos, multiplicadores e outros indicadores?*
                 
**✏️ H1**. É possível usar informações da RAIS para estimar a proporção
de cada classe CNAE na formação de cada atividade agregada 
na MIP;
                 
                           
**✏️ H2**. As classes que formam cada atividade possuem coeficientes
técnicos muito similares, especialmente no que se refere à 
proporção de gastos com pessoal. Portanto, supor que são iguais 
é uma aproximação razoável. """)


"""
**Dados RAIS para 68 atividades agregadas para o Brasil e 
para 673 classes agregados para o Brasil.**

"""

csv = convert_df(br68)
st.download_button("Press to Download Matriz br68", 
                         csv,"br68.csv", 
                         "text/csv", 
                         key='download-csv')


csv = convert_df(br673)
st.download_button("Press to Download Matriz br673", 
                         csv,"br673.csv", 
                         "text/csv", 
                         key='download-csv')

st.subheader("🔍 Operacional da H1")

"""
**Para a atividade selecionada as classes compõem esta atividade são:**

"""

st.table(aereo)

"""
**Em complemento a próxima Tabela  mostra os dados RAIS para atividade selecionada
de forma agregada.**
"""

st.table(raisA)

"""
**Na sequência a Tabela  mostra os dados RAIS com as classes
que compõem atividade selecionada de forma desagregada.**

"""
st.table(raisB)

"""
**Cálculo das proporções de cada classe dentro da atividade selecionada.
Para tanto, definir a métrica a ser usada, isto é, o nome exato da coluna de dados.**
"""

st.table(prop)

st.subheader("🔍 Operacional da H2")
"""
**Para avaliação da H2 devem ser estimados os coeficientes 
técnicos da atividade analisada tendo como referência a
matriz A do modelo Insumo Produto nacional.**

"""
st.table(A_br[code_setor]) 


"""
**Segundo a hipótese 2, os coeficientes técnicos dos setores 
desagregados serão iguais aos da atividade agregada. Portanto, 
para testar a H2 na sequênia são realizados vários cálculos 
computacionais para obtenção da matriz Ad e Ld.**

"""

"""
**📚 Ad é a matriz desagregada:**
"""
csv = convert_df(Ad)
st.download_button("Press to Download Matriz Ad", 
                         csv,"Ad.csv", 
                         "text/csv", 
                         key='download-csv')

"""
**📚 Ld é a matriz de Leontief desagregada:**
"""

csv = convert_df(Ld)
st.download_button("Press to Download Matriz Ld", 
                         csv,"Ld.csv", 
                         "text/csv", 
                         key='download-csv')

st.subheader("🔍 Comparando A e Ad")

"""
**A soma dos coeficientes da matriz A no sentido das 
linhas (i.e. soma dos valores de cada coluna) para o
setor  que foi desagregado:***
"""

st.write(nereus.A.sum(axis=0)[code_setor])


"""
**Soma dos coeficientes da matriz Ad no sentido das linhas 
(i.e. soma dos valores de cada coluna) :**
"""
st.table(Ad.sum(axis=0))
         
"""
**Resultado: a soma dos coeficientes técnicos das novas
colunas é igual à do setor original, a soma dos coef
das outras colunas permanece inalterado.**
"""
         

