#
#  file:  cifar10_cnn_arbitrary.py
#
#  MNIST architecture applied to CIFAR-10
#  using arbitrary binary label assignment
#
#  RTK, 21-Oct-2019
#  Last update:  12-May-2023
#
################################################################

import tensorflow.keras as keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Activation
from tensorflow.keras import backend as K
import numpy as np
import sys

if (len(sys.argv) == 1):
    print("cifar10_cnn_arbitrary <train> <test> <model>")
    exit(0)

batch_size = 128
epochs = 12

if (sys.argv[1].find("all") != -1):
    num_classes = 10
else:
    num_classes = 2

img_rows, img_cols = 32, 32

x_train = np.load("../../data/cifar10/cifar10_train_images.npy")
y_train = np.load(sys.argv[1])

x_test = np.load("../../data/cifar10/cifar10_test_images.npy")
y_test = np.load(sys.argv[2])

if K.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 3, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 3, img_rows, img_cols)
    input_shape = (3, img_rows, img_cols)
else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 3)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 3)
    input_shape = (img_rows, img_cols, 3)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Conv2D(32, kernel_size=(3, 3),
                 activation='relu',
                 input_shape=input_shape))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adam(),
              metrics=['accuracy'])

model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test[:1000], y_test[:1000]))
score = model.evaluate(x_test[1000:], y_test[1000:], verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

model.save(sys.argv[3])

