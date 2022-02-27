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





list_br = ['mipita_br','A_br', 'L_br', 'Af_br', 'Lf_br', 'multiplicadores_br', 'multiplicadores_ta_br' ]


def table_br(parametro_br):
    if parametro_br == 'mipita_br':
        table = st.table(mipita_br)
    elif parametro_br == 'A_br':
        table = st.table(A_br)
    elif parametro_br == 'L_br':
        table = st.table(L_br)
    elif parametro_br == 'Af_br':
        table = st.table(Af_br)
    elif parametro_br == 'Lf_br':
        table = st.table(Lf_br)
    elif parametro_br == 'multiplicadores_br':
          table = st.table(multiplicadores_br)
    elif parametro_br == 'multiplicadores_ta_br':
          table = st.table(multiplicadores_ta_br)
    return table 


#-----------------------------------------------------------------------------------
# -- Set page config

st.apptitle = 'Projeto IMPACTO'
st.title('MIPITA')
st.markdown("""A matriz de insumo-produtos brasileira""")



#-----------------------------------------------------------------------------------

with st.sidebar:
    
    st.info("🎈**VERSÃO:** 2022.27.02 - [ITA](https://www.ita.br)" )
    st.sidebar.header('Seleção dos parâmetros') 
   
    ano = st.sidebar.slider('Ano', 2010, 2021, 2015)  # min, max, default
    code_municipio= st.text_input('Código IBGE do Município?')
        
    st.sidebar.markdown('## MIPITA')
    parametro_br = st.sidebar.selectbox('Brasil', list_br)




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

demanda_br = nereus.mipita.loc['5100']['total_produtos']


table_br(parametro_br)

st.title('Regionalização da MIP brasileira')

with st.beta_expander("Veja nota informativa sobre a Regionalização da MIP brasileira:"):
    st.markdown("""- A matriz de insumo-produtos é um modelo estrutural de uma economia, 
 ela retrata o total das transações entre os setores intermediários durante 
o período de um ano, medidas pelo valor transacionado. 
A regionalização consiste em obter modelos derivados do modelo nacional para territórios 
contidos no país. Para tanto, diferentes premissas e metodologias podem ser adotadas,
dependendo dos dados disponíveis e dos objetivos da análise.
                    
- Para o nosso problema, começamos com os modelos de região única 
(modelo regional simples). Estes focalizam a estrutura produtiva de uma 
determinada região e os impactos que ocorrem nesaa estrutura a partir de 
choques de demanda. O modelo de região única não captura os efeitos
transbordados para o restante do país. Neste sentido, por exemplo, 
aos efeitos operação de um aeroporto em uma determinada região serão 
medidos apenas para a própria região. Os efeitos causados fora dessa região, 
mesmo que existam, são ignorados. O modelo regional simples funciona, assim, 
como um *building bloc* para os passos subsequentes de sofisticação da modelagem.""")
 


