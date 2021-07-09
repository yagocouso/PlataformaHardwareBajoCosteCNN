# -*- coding: utf-8 -*-
"""
Created on Thu May 27 21:59:41 2021

@author: Yago
"""

import pandas as pd
import numpy as np
from datetime import datetime
from Conexion import Conexion
import plotly.graph_objects as go
import pickle  # Para guardar el escalado
import keras
from keras.layers import Dense
from keras.models import Model
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

cnx = Conexion('Arduino')
"""
final = pd.DataFrame(cnx('datos_etiquetados').find({}, {'_id':0}))

anterior = final.loc[:final.shape[0]-2].copy().reset_index(drop = True)
posterior = final.loc[1:].copy().reset_index(drop = True)

posterior[['ax', 'ay', 'az', 'gx', 'gy', 'gz']] = posterior[['ax', 'ay', 'az', 'gx', 'gy', 'gz']] - anterior[['ax', 'ay', 'az', 'gx', 'gy', 'gz']]

final = posterior.copy()

recortar = ((final['stop']==1.0) | (final['stop']==0.0)) & ((final['walk']==1.0) | (final['walk']==0.0)) & ((final['run']==1.0) | (final['run']==0.0))
final = final[recortar]
final = final.reset_index()
cnx('datos_entrenenamiento_dense').insert_many(final.to_dict('records'))
"""

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


for n_epoch in range(20, 120, 20):
    for n_batch in range(0, 25, 5):
        if n_batch == 0: n_batch = 1
        for i in range(10, 11):
            
##############################################################################
##################### CONFIGURACION RED NEURONAL #############################
##############################################################################
            NombreArchivo = f"NBatch_{n_batch}_NEpoch_{n_epoch}_values_{i}"
            #n_epoch = 20 # Repeticiones del entrenamiento
            #n_batch = 1 # Número de ejemplos que van a ser propagados por el modelo en el entrenamiento
            #Capas = [[22, 'relu'], [11, 'relu'], [4, 'sigmoid']] #Capas ocultas y salida red neuronal
            keras_optimizer = 'rmsprop' # Adam suele ser el mejor para entrenamientos en general.
            loss_function = 'categorical_crossentropy' 
            metrics = ['accuracy']  

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
                grupo = MediaoDatos(grupo, i, 'ax', 'ay', 'az', 'gx', 'gy', 'gz')
                dividido[index] = grupo.copy()
            
            zona_final = pd.concat(dividido)
            Entrada = zona_final[['ax', 'ay', 'az', 'gx', 'gy', 'gz']]
            Salida = zona_final[['stop', 'walk', 'run']]
            
            Entrada = np.array(Entrada)
            Salida = np.array(Salida)
            
            Capas = [[Entrada.shape[1]*2, 'relu'], [Entrada.shape[1], 'relu'], [Salida.shape[1], 'softmax']] #Capas ocultas y salida red neuronal
            
            inputs = keras.layers.Input(shape= (len(Entrada[0]), ))
            outputs = None
            
            for i, val in enumerate(Capas):
                outputs = Dense(val[0], activation=val[1])(inputs if i == 0 else outputs)
             
            # Inciando el modelo
            model = Model(inputs=inputs, outputs=outputs)
            # Compilamos el modelo
            model.compile(loss=loss_function, optimizer=keras_optimizer, metrics=metrics)
            print(model.summary())
            print("Inputs: ", inputs)
            print("Outputs:", outputs)
            
            #Creanmos los escalados de normalizacion
            scaler_X = MinMaxScaler(feature_range=(0, 1))
            scaler_Y = MinMaxScaler(feature_range=(0, 1))
            
            # Normalizamos los datos que tenemos 
            x_scaled = scaler_X.fit_transform(Entrada)
            y_scaled = scaler_Y.fit_transform(Salida)
            
            #Creamos los archivos de escalado
            pickle.dump(scaler_X, open('./' + NombreArchivo + '_scaler_X.sav', 'wb'))
            pickle.dump(scaler_Y, open('./' + NombreArchivo + '_scaler_Y.sav', 'wb'))
            
            #Dividimos los datos de entrada, en este caso, 10 por ciento para tesy, 
            # el 90% para entrenamiento
            x_train, x_test, y_train, y_test = train_test_split(
            x_scaled, y_scaled, test_size = 0.20 , random_state = 123, shuffle=True)
            
            print('for_test_x: ', x_test)
            print("x_train.shape:", x_train.shape)
            print("y_train.shape:", y_train.shape)
            
            #Entrenamos el modelo
            train_log = model.fit(x_train, y_train, epochs = n_epoch, batch_size = n_batch, verbose=1)
            
            # Guardamos el modelo
            model.save("./" + NombreArchivo + "_model.h5")
            
            test_loss, test_accuracy = model.evaluate(x_test, y_test)
            
            loss = train_log.history['loss']
            accuracy = train_log.history['accuracy']
            epochs = range(1, len(loss) + 1)
            plt.plot(epochs, loss, 'b', label='Loss')
            plt.plot(epochs, accuracy, 'r', label='Accuracy')
            plt.title('Training accuracy, and validation loss')
            plt.xlabel('Epochs')
            plt.ylabel('Loss')
            plt.legend()
            plt.show()
            valor_insertar = {
                'NombreArchivo': NombreArchivo,
                'fecha': datetime.now(),
                'n_epoch': n_epoch, 
                'n_batch': n_batch,
                'valores_concatenados': i,
                'log_accuracy': accuracy,
                'log_loss': loss, 
                'test_loss': test_loss, 
                'test_accuracy': test_accuracy
                }
            
            cnx('Resumen_entrenamientos').insert_one(valor_insertar)
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            # Resumen final
            print(f"""
                {now}
                Parámetros usados para el entrenamiento:
                
                # Número de entradas
                number_inputs   = {len(Entrada[0])}
                
                # Parámetros entrenamiento
                n_batch         = {n_batch}
                n_epoch         = {n_epoch}
                
                # Lista de capas para entrenar
                hidden_c        = {Capas}
                
                # Función de loss en el compilado
                loss_function   = {loss_function}
                # Funcion de optimización en el compilado
                keras_optimizer = {keras_optimizer}
            """)
            
            #Resultado = model.predict(np.array(x_test), batch_size=n_batch, verbose=1)
            #x_tested = scaler_X.inverse_transform(x_test)
            #y_tested = scaler_Y.inverse_transform(y_test)
            #Resultado = scaler_Y.inverse_transform(Resultado)
            #Diferencia = y_tested - Resultado
            
            #print("Diferencia, entre el test, y lo real", Diferencia)
            
            """fig = go.Figure()
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
            
            fig.write_html('test.html', auto_open=True)"""