from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
import keras
from keras.layers import Input, Dense, Conv1D, MaxPooling1D, GlobalAveragePooling1D, Reshape, Flatten
from keras.optimizers import SGD

from sklearn.preprocessing import Imputer
from sklearn import preprocessing
import numpy as np
import pandas as pd
from scipy import stats

import time

import os
import os.path
from pathlib import Path

#np.random.seed(1337)

_script_path = Path().absolute() #location of our script
_dataset_folder_name = 'Filtered_Dataframes'
_dataset_folder_path = os.path.join(str(_script_path), _dataset_folder_name)

_file_names = []
_folder_locations = []
_dataset_list = []

for dirpath, dirnames, filenames in os.walk(_dataset_folder_path):
    for filename in [f for f in filenames if f.endswith(".csv")]:
        location = os.path.join(dirpath, filename)
        _folder_locations.append(location)
        _file_names.append(filename)

for i,location in enumerate(_folder_locations):
    temp_df = pd.read_csv(location)
    temp_df = temp_df.truncate(after = 17999)
    temp_df['participant_no'] = i
    if "anger" in location:
        temp_df['emotion'] = 0
    elif "calmness" in location:
        temp_df['emotion'] = 1
    elif "disgust" in location:
        temp_df['emotion'] = 2
    elif "fear" in location:
        temp_df['emotion'] = 3
    elif "happiness" in location:
        temp_df['emotion'] = 4
    elif "sadness" in location:
        temp_df['emotion'] = 5
    unc_columns = ['hr','spo2','timest']
    temp_df = temp_df.drop(unc_columns,axis=1)
    _dataset_list.append(temp_df)

_dataset = pd.concat(_dataset_list,axis=0)
_dataset.index = range(0,len(_dataset))

train_x = _dataset.iloc[:,0:4]
train_x = train_x.drop(['participant_no'],axis=1)
train_y = _dataset.iloc[:,4:]

print('Row count= ', len(_dataset))

def create_segments_and_labels(df, time_steps, step, label_name):

    """
    This function receives a dataframe and returns the reshaped segments
    of x,y,z acceleration as well as the corresponding labels
    Args:
        df: Dataframe in the expected format
        time_steps: Integer value of the length of a segment that is created
    Returns:
        reshaped_segments
        labels:
    """

    # x, y, z acceleration as features
    N_FEATURES = 3
    # Number of steps to advance in each iteration (for me, it should always
    # be equal to the time_steps in order to have no overlap between segments)
    # step = time_steps
    segments = []
    labels = []
    for i in range(0, len(df) - time_steps, step):
        xs = df['ecg'].values[i: i + time_steps]
        ys = df['gsr'].values[i: i + time_steps]
        zs = df['temp'].values[i: i + time_steps]

        y = df['emotion'].values[i: i+time_steps]

        # Retrieve the most often used label in this segment
        #print(xs,ys,zs)
        #label = stats.mode(df[label_name][i: i + time_steps])[0][0]
        #print(label)
        segments.append([xs, ys, zs])
        labels.append(y)

    # Bring the segments into a better shape
    reshaped_segments = np.asarray(segments, dtype= np.float32).reshape(-1, time_steps, N_FEATURES)

    labels = np.asarray(labels)

    return reshaped_segments,labels

input_shape = 18000*3

LABELS = ["0","1","2","3","4","5"]

train_x,train_y = create_segments_and_labels(_dataset,18000,18000,LABELS)
train_x = train_x.reshape(train_x.shape[0],input_shape)
print(train_x.shape)
print(train_y.shape)

model = Sequential()
#model.add(Flatten())
model.add(Reshape((18000,3),input_shape=(input_shape,)))
model.add(Conv1D(100,700,activation='relu',input_shape=(18000,3)))
model.add(Conv1D(100,700,activation='relu'))
model.add(MaxPooling1D(4))
model.add(Conv1D(160,700,activation='relu'))
model.add(Conv1D(160,700,activation='relu'))
model.add(GlobalAveragePooling1D())
model.add(Dropout(0.5))
model.add(Dense(1,activation='softmax'))

print(model.summary())


rmsprop = keras.optimizers.RMSprop(lr=0.001, rho=0.9, epsilon=None, decay=0.0)
sgd = keras.optimizers.SGD(lr=0.01, momentum=0.0, decay=0.0, nesterov=False)
adagrad = keras.optimizers.Adagrad(lr=0.01, epsilon=None, decay=0.0)
adam = keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)

model.compile(optimizer = sgd, loss = 'binary_crossentropy', metrics = ['acc'])
model.fit(train_x,train_y,epochs = 300, batch_size = 32, validation_split=0.33, shuffle=False)
