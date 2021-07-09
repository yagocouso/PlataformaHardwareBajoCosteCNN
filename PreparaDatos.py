# -*- coding: utf-8 -*-
"""
Created on Thu May 27 20:04:38 2021

@author: Yago
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from Conexion import Conexion
from random import randrange, choice
import plotly.graph_objects as go



cnx = Conexion('Arduino')
final = pd.DataFrame(cnx('datos_replicados').find({}, {'_id':0}))

cortes = {
    1:{
       'time': datetime(2021, 5, 24, 18, 12, 6),
       'init':[1, 0, 0],
       'end': [0, 1, 0]
       }, 
    2:{
       'time': datetime(2021, 5, 24, 18, 33, 1),
       'init':[0, 1, 0],
       'end': [1, 0, 0]
       },
    3:{
       'time': datetime(2021, 5, 24, 19, 12, 40),
       'init':[1, 0, 0],
       'end': [0, 0, 1]
       },
    4:{
       'time': datetime(2021, 5, 24, 20, 30, 10),
       'init':[0, 0, 1],
       'end': [0, 1, 0]
      },
    5:{
       'time': datetime(2021, 5, 24, 21, 26, 43),
       'init':[0, 1, 0],
       'end': [1, 0, 0]
       },
    }

lista = ['stop', 'walk', 'run']
final[['stop', 'walk', 'run']] = 0
ultimo_indice = 0


for value in cortes.values():
    maximo = value['time'] + timedelta(seconds = 2)
    minimo = value['time'] - timedelta(seconds = 2)
    modif = final[(final['date'] > minimo) & (final['date'] < maximo)]
    indice_corte_inicio = modif.index[0]
    step = 1 / modif.shape[0]
    index_init = value['init'].index(1)
    final[lista[index_init]].loc[ultimo_indice: indice_corte_inicio] = 1 
    index_end = value['end'].index(1)    
    cambios = np.zeros([modif.shape[0], 3])
    rango_cre = np.linspace(0, 1, modif.shape[0]).reshape(modif.shape[0])
    rango_dec = np.linspace(1, 0, modif.shape[0]).reshape(modif.shape[0])
    cambios[:, index_init] = rango_dec
    cambios[:, index_end] = rango_cre
    modif[['stop', 'walk', 'run']] = cambios
    final[(final['date'] > minimo) & (final['date'] < maximo)] = modif
    ultimo_indice = modif.index[-1]
    print(value)


final[lista[index_end]].loc[ultimo_indice+1:] = 1 

#cnx('datos_etiquetados').insert_many(final.to_dict('records'))
check = final['stop'] + final['run'] + final['walk'] 

# Create traces
fig = go.Figure()
fig.add_trace(go.Scatter(x=final['date'], y=final['ax'],
                    mode='lines',
                    name='ax'))
fig.add_trace(go.Scatter(x=final['date'], y=final['ay'],
                    mode='lines',
                    name='ay'))
fig.add_trace(go.Scatter(x=final['date'], y=final['az'],
                    mode='lines', name='az'))

fig.add_trace(go.Scatter(x=final['date'], y=final['gx'],
                    mode='lines',
                    name='gx'))
fig.add_trace(go.Scatter(x=final['date'], y=final['gy'],
                    mode='lines',
                    name='gy'))
fig.add_trace(go.Scatter(x=final['date'], y=final['gz'],
                    mode='lines', name='gz'))

fig.write_html('test.html', auto_open=True)