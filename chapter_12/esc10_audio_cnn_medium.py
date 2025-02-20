#
#  file:  esc10_audio_cnn_medium.py
#
#  1D convolutional network, medium depth
#
#  RTK, 13-Nov-2019
#  Last update:  21-May-2023
#
################################################################

import sys
import tensorflow.keras as keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv1D, MaxPooling1D
from tensorflow.keras import backend as K
import numpy as np

batch_size = 32
num_classes = 10
epochs = 16
nsamp = (441*2,1)

kstr = sys.argv[1]
z=int(kstr)

x_train = np.load("../data/audio/ESC-10/esc10_raw_train_audio.npy")
y_train = np.load("../data/audio/ESC-10/esc10_raw_train_labels.npy")
x_test  = np.load("../data/audio/ESC-10/esc10_raw_test_audio.npy")
y_test  = np.load("../data/audio/ESC-10/esc10_raw_test_labels.npy")

x_train = (x_train.astype('float32') + 32768) / 65536
x_test = (x_test.astype('float32') + 32768) / 65536

y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Conv1D(32, kernel_size=z,
                 activation='relu',
                 input_shape=nsamp))
model.add(Conv1D(64, kernel_size=3, activation='relu'))
model.add(Conv1D(64, kernel_size=3, activation='relu'))
model.add(MaxPooling1D(pool_size=3))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adam(),
              metrics=['accuracy'])

history = model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=0)

score = model.evaluate(x_test, y_test, verbose=0)
print("k=%2d, score=%0.3f%%" % (z,100.0*score[1],))

