# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 16:26:16 2021

@author: Yago
"""

import tensorflow as tf
from keras.models import load_model

# Create a model using high-level tf.keras.* APIs
model = load_model('model.h5')
# (to generate a SavedModel) tf.saved_model.save(model, "saved_model_keras_dir")

# Convert the model.
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the model.
with open('model.tflite', 'wb') as f:
  f.write(tflite_model)