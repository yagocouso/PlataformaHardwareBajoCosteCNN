import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from Conexion import Conexion
from random import randrange, choice
import plotly.graph_objects as go


cnx = Conexion('Arduino')
#final = pd.DataFrame(cnx('datos_replicados').find({}, {'_id':0}))

final = pd.DataFrame(cnx('datos_entrenenamiento_dense').find({}, {'_id':0}))


def valorAbsoluto(array, *elementos):
    array[list(elementos)] = np.absolute(array[list(elementos)].values)
    return array

def sumatorioDatos(array, valores = 3, *elementos):
    array = array.reset_index(drop = True)
    array_original = array.copy()
    for i in range(valores - 1):
        anterior = array_original[list(elementos)].loc[i + 1:].copy().reset_index(drop = True)
        array[list(elementos)] = array[list(elementos)] + anterior
    return array.dropna()

def MediaoDatos(array, valores = 3, *elementos):
    array = array.reset_index(drop = True)
    array_original = array.copy()
    for i in range(valores - 1):
        anterior = array_original[list(elementos)].loc[i + 1:].copy().reset_index(drop = True)
        array[list(elementos)] = array[list(elementos)] + anterior
    array[list(elementos)] = array[list(elementos)] / valores
    return array.dropna()



cortes = []
last_value = 0
for index in final['index']:
    if index != last_value + 1: cortes.append(index - (len(cortes)))    
    last_value = index
cortes.append(last_value)  

dividido = []
for index in range(len(cortes) - 1):
    dividido.append(final.loc[cortes[index]:cortes[index + 1] - 1])
    

for index in range(len(dividido)):
    grupo = dividido[index]
    grupo = valorAbsoluto(grupo, 'ax', 'ay', 'az', 'gx', 'gy', 'gz')
    grupo = MediaoDatos(grupo, 4, 'ax', 'ay', 'az', 'gx', 'gy', 'gz')
    dividido[index] = grupo.copy()

final = pd.concat(dividido)
#Entrada = final[['ax', 'ay', 'az', 'gx', 'gy', 'gz']]
#Salida = final[['stop', 'walk', 'run']]

fig = go.Figure()


fig.add_trace(go.Scatter(x=final['date'], y=final['gx'], mode='lines', name='gx'))
fig.add_trace(go.Scatter(x=final['date'], y=final['gy'], mode='lines', name='gy'))
fig.add_trace(go.Scatter(x=final['date'], y=final['gz'], mode='lines', name='gz'))

fig.add_trace(go.Scatter(x=final['date'], y=final['ax'], mode='lines', name='ax'))
fig.add_trace(go.Scatter(x=final['date'], y=final['ay'], mode='lines', name='ay'))
fig.add_trace(go.Scatter(x=final['date'], y=final['az'], mode='lines', name='az'))

fig.write_html('test.html', auto_open=True)