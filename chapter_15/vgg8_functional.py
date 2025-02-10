#
#  file:  vgg8_functional.py
#
#  VGG8 for CIFAR-10 using Keras functional API-style blocks
#
#  RTK, 14-Aug-2023
#  Last update:  31-Aug-2023
#
################################################################

import os
import sys
import pickle
from sklearn.metrics import matthews_corrcoef
import tensorflow.keras as keras
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv2D, MaxPooling2D, ReLU
from tensorflow.keras.layers import Softmax, SpatialDropout2D
from tensorflow.keras.layers import BatchNormalization
import numpy as np

def ConfusionMatrix(pred, y):
    """Return a confusion matrix"""
    cm = np.zeros((10,10), dtype="uint16")
    for i in range(len(y)):
        cm[y[i], pred[i]] += 1
    acc = np.diag(cm).sum() / cm.sum()
    return cm, acc


class ConvBlock:
    """Build a VGG convolution-relu-maxpooling block w/optional dropout"""

    def __init__(self, filters, dropout=0, pct=0.25, useBN=False):
        """Constructor"""
        self.filters = filters
        self.dropout = dropout
        self.pct = pct
        self.useBN = useBN

    def __call__(self, _):
        """Functional API portion"""
        if (self.useBN):
            _ = Conv2D(self.filters, (3,3), padding='same')(_)
            _ = BatchNormalization()(_)  # BN before activation
            _ = ReLU()(_)
            _ = Conv2D(self.filters, (3,3), padding='same')(_)
            _ = BatchNormalization()(_)
            _ = ReLU()(_)
        else:
            _ = Conv2D(self.filters, (3,3), padding='same')(_)
            _ = ReLU()(_)
            if (self.dropout==1):        # Dropout after activation
                _ = Dropout(self.pct)(_)
            elif (self.dropout==2):
                _ = SpatialDropout2D(self.pct)(_)
            _ = Conv2D(self.filters, (3,3), padding='same')(_)
            _ = ReLU()(_)
            if (self.dropout==1):
                _ = Dropout(self.pct)(_)
            elif (self.dropout==2):
                _ = SpatialDropout2D(self.pct)(_)
        return MaxPooling2D((2,2))(_)


class DenseBlock:
    """Build a Dense-ReLU-Dropout block"""

    def __init__(self, nodes, useBN=False):
        """Constructor"""
        self.nodes = nodes
        self.useBN = useBN
    
    def __call__(self, _):
        """Functional API portion"""
        _ = Dense(self.nodes)(_)
        if (self.useBN):
            _ = BatchNormalization()(_)
        _ = ReLU()(_)
        _ = Dropout(0.5)(_)
        return _


#  Command line
if (len(sys.argv) == 1):
    print()
    print("vgg8 <minibatch> <epochs> <dropout_type> <dropout_pct> <useBN> <outdir>")
    print()
    print("  <minibatch>    -  minibatch size (e.g. 128)")
    print("  <epochs>       -  number of training epochs (e.g. 16)")
    print("  <dropout_type> -  0=none, 1=dropout/dropout, 2=spatial/dropout")
    print("  <dropout_pct>  -  for dense, pct/2 for conv (e.g. 0.5)")
    print("  <useBN>        -  0=no, 1=yes (ignores dropout settings yes)")
    print("  <outdir>       -  output file directory (overwritten)")
    print()
    exit(0)

batch_size = int(sys.argv[1])  # VGG paper uses 256
epochs = int(sys.argv[2])
dropout = int(sys.argv[3])
pct = float(sys.argv[4])
useBN = True if int(sys.argv[5]) else False
outdir = sys.argv[6]

#  Other parameters
num_classes = 10
img_rows, img_cols = 32, 32
input_shape = (img_rows, img_cols, 3)

#  Load the full RGB CIFAR-10 dataset (unaugmented)
x_train = np.load("../data/cifar10/cifar10_train_images.npy")
ytrain  = np.load("../data/cifar10/cifar10_train_labels.npy").squeeze()
x_test  = np.load("../data/cifar10/cifar10_test_images.npy")
ytest   = np.load("../data/cifar10/cifar10_test_labels.npy").squeeze()

#  Scale [0,1]
x_train = x_train.astype('float32') / 255
x_test = x_test.astype('float32') / 255

#  Convert labels to one-hot vectors
y_train = keras.utils.to_categorical(ytrain, num_classes)
y_test = keras.utils.to_categorical(ytest, num_classes)

#  Model suitable for 32x32 CIFAR-10 (VGG8)
inp = Input(input_shape)
_ = ConvBlock( 64, dropout=dropout, pct=pct, useBN=useBN)(inp)
_ = ConvBlock(128, dropout=dropout, pct=pct, useBN=useBN)(_)
_ = ConvBlock(256, dropout=dropout, pct=pct, useBN=useBN)(_)
_ = Flatten()(_)
_ = DenseBlock(2048, useBN=useBN)(_)
_ = DenseBlock(2048, useBN=useBN)(_)
_ = Dense(num_classes)(_)
outp = Softmax()(_)

model = Model(inputs=inp, outputs=outp)
model.summary()

#  Compile and train
model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adam(),
              metrics=['accuracy'])

history = model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))

#  Results
tloss = history.history['loss']
vloss = history.history['val_loss']
terr = 1.0 - np.array(history.history['accuracy'])
verr = 1.0 - np.array(history.history['val_accuracy'])
d = [tloss,vloss,terr,verr]
os.system("rm -rf %s; mkdir %s" % (outdir,outdir))
pickle.dump(d, open(outdir+"/results.pkl", "wb"))
pred = model.predict(x_test, verbose=0)
plabel = np.argmax(pred, axis=1)
cm, acc = ConfusionMatrix(plabel, ytest)
mcc = matthews_corrcoef(ytest, plabel)
s = 'Test set accuracy: %0.4f, MCC: %0.4f' % (acc,mcc)
with open(outdir+"/accuracy_mcc.txt", "w") as f:
    f.write(s+"\n")
np.save(outdir+"/confusion_matrix.npy", cm)
np.save(outdir+"/predictions.npy", pred)
model.save(outdir+"/model.keras")
print(s)
print(cm)

