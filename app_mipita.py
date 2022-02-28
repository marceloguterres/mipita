# -*- coding: utf-8 -*-
"""
Spyder Editor

@author: guterres

"""

# Bibliotecas Python
import numpy as np
import pandas as pd

# Bibliotecas Impacto
import matriz
import auxrais
from lago import *
from auxrais import *
from auxdata import *
import streamlit as st


list_codes  = pd.read_csv('codes_municipios.csv', sep=';', encoding='latin-1').astype(str)
list_br     = ['multiplicadores_br', 'multiplicadores_ta_br' ]



def table_br(parametro_br):
    if parametro_br == 'multiplicadores_br':
        table = multiplicadores_br
    else:
        table = multiplicadores_ta_br
    return table

@st.cache
def convert_df(df):
   return df.to_csv().encode('utf-8')


#-----------------------------------------------------------------------------------
# -- Set page config

st.apptitle = 'Projeto IMPACTO'
st.title('Análise Insumo Produto Nacional')


#-----------------------------------------------------------------------------------

with st.sidebar:
    
    st.info("🎈**VERSÃO:** 2022.27.02 - [ITA](https://www.ita.br)" )
    st.sidebar.header('Seleção dos parâmetros') 
    
    ano             = st.sidebar.slider('Ano', 2010, 2021, 2015)  # min, max, default
    code_municipio  = st.selectbox('Código IBGE do Município?', list_codes, index= 3826)


    st.sidebar.markdown('## MIPITA')
    tx_demanda_ta = st.number_input('Varição da demanda?')



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
multiplicadores_ta_br = nereus.multiplicadores['5100'] 

demanda_ta_br = nereus.mipita.loc['5100']['total_produtos']
impactos_ta_br = multiplicadores_br['5100'] * demanda_ta_br  * tx_demanda_ta * 1


                                        

#=============================================================================
# csvs
#=============================================================================



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


csv = convert_df(multiplicadores_br )
st.download_button("Press to Download multiplicadores br ", 
                   csv,"multiplicadores_br .csv", 
                   "text/csv", 
                   key='download-csv')


csv = convert_df(multiplicadores_ta_br)
st.download_button("Press to Download multiplicadores TA", 
                   csv,"multiplicadores_ta_br.csv", 
                   "text/csv", 
                   key='download-csv')



#=============================================================================
# resultados br
#=============================================================================


st.subheader('🎯 Cálculo do impacto econômico') 

st.markdown("""Use o menu de inputs para indicar a taxa de variação da demanda 
por Transporte Aéreo""")


"""
📊 **Multiplicadores Transporte Aéreo BR:**
"""


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
     
st.table(multiplicadores_ta_br)

"""
🎯 **Valor total da demanda por transporte aéreo** (R$ milhões/ano):
"""
st.write(demanda_ta_br)


"""
🎯 **Impactos estimados pelos multiplicadores:**
"""

with st.expander("Veja nota informativa dos impactos estimados pelos multiplicadores: 👉"):
     st.markdown("""Referem-se à alteração de 1 unidade na demanda agregada total
para encontrar os efeitos no conjunto da economia basta multiplicar pela 
quantidade de unidades perdidas ou ganhas nessa demanda.""")
st.table(impactos_ta_br)

"""
---
"""
#=============================================================================
# Análise Insumo Produto Regionalizada (xx)
#=============================================================================

mipita_xx = nereus.extrair_mipita()   # o objeto Mipita é extraído do objeto Nereus, para cada região você começa aqui criando uma nova instância do objeto Mipita
mipita_xx.preparar_qL([code_municipio])  # os parâmetros não definidos assumem os valores padrão
qL = mipita_xx.qL                
propT = mipita_xx.propT                  # atributo .propT será empregado para estimar as colunas relacionadas à demanda final.
mipita_xx.regionalizar() 
A_xx = mipita_xx.A                      
mipreg_xx = mipita_xx.mipreg             
ajuste_xx = mipita_xx.ajuste
compradores_xx  = mipita_xx.compradores(i='5100') 
fornecedores_xx = mipita_xx.fornecedores(j='5100', q=10)
           
     

                     
st.title('Regionalização da MIP')  

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
 
"""
🆔 **Município selecionado**:
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
📊 **Os coeficientes locacionais**:
"""
with st.expander("Veja nota informativa dos coeficientes locacionais: 👉"):
     st.markdown("""O processo de regionalização envolver obter uma 
                 estimativa da estrutura produtiva de região alvo.
                 Esta estimativa pode ser feita a partir da seguinte pergunta:
                   
                "Quanto de cada atividade econômica é realizada no território alvo"?
                
O coeficiente locacional fornece essa medida. Conceitualmente ele
fornece a proporção, variando de 0 a 1, de quanto uma determinada 
atividade econômica acontece em um determinado território com 
relação ao todo nacional.""")
st.table(qL)


"""
🔍 **O atributo propT**:
"""

with st.expander("Veja nota informativa do atributo propT: 👉"):
     st.markdown("""Enquanto o coeficiente locacional estima as proporções
                 do lado das atividades de produção o atributo .propT 
                 será empregado para estimar as colunas relacionadas à 
                 demanda final.""")
st.write(propT)




"""
👀 **Principais compradores do setor 5100**:
"""
st.table(compradores_xx)


"""
👀 **Principais forncedores do setor 5100**:
"""
st.table(fornecedores_xx)


"""
⛳ **'O atributo ajuste**:
"""
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

#st.table(pd.DataFrame([ajuste_xx]))
st.write(ajuste_xx)



#=============================================================================
# Modelo simplificado para entender e estudar o comportamento do modelo 
# interregional de ISARD (yy)
#=============================================================================
# A matriz A_yy é a matriz Brasil menos a regionalizada para xx


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


"""
---
"""

st.title('Modelo interregional')  
with st.expander("Veja nota informativa do atributo ajuste: 👉"):
     st.markdown("""O modelo interregional (modelo de Isard) consiste 
                 na expansão da matriz insumo-produto nacional de modo 
                 a identificar não apenas os fluxos intersetoriais, 
                 mas também os fluxos interregionais.
                 Desse modo, um modelo para N regiões irá expandir 
                 a matriz exponencialmente""")

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

"""🥈 **O município comprou**:""" 
st.write(sum(mipita_xx.comprou))


"""🥈 **O município vendeu**:"""
st.write(sum(mipita_yy.vendeu))


"""↗️ **Um aumento de 1 unidade na agricultura de Brasil 
gera aumento na agricultura do município de**:"""
st.write(L_intreg.at['0191', '0191_'])

"""↗️ **Um aumento de 1 na agricultura município gera 
aumento na agricultura do Brasil de**:"""
L_intreg.at['0191_', '0191'] 


