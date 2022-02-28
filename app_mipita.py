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



list_br = ['multiplicadores_br', 'multiplicadores_ta_br' ]


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
   
    ano = st.sidebar.slider('Ano', 2010, 2021, 2015)  # min, max, default
    code_municipio= st.text_input('Código IBGE do Município?')
        
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
# Cálculo de impacto econômico
#=============================================================================


st.title('Cálculo do impacto econômico')      

st.markdown("""Use o menu de inputs para indicar a taxa de variação da demanda 
por Transporte Aéreo""")


st.subheader('Multiplicadores Transporte Aéreo BR:')
with st.expander("Veja nota informativa sobre os multiplicadores:"):
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


st.subheader('Valor total da demanda por transporte aéreo:')
st.write("R$ milhões/ano")
st.write(demanda_ta_br)



st.subheader('Impactos estimados pelos multiplicadores:')
with st.expander("Veja nota informativa dos impactos estimados pelos multiplicadores:"):
     st.markdown("""Referem-se à alteração de 1 unidade na demanda agregada total
para encontrar os efeitos no conjunto da economia basta multiplicar pela 
quantidade de unidades perdidas ou ganhas nessa demanda.""")
st.table(impactos_ta_br)





