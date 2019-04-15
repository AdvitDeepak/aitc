import numpy as np
import keras
from keras.models import Sequential
from keras.layers import Dense
from collections import deque
import random
from keras.optimizers import Adam
import h5py
import os
from utilities.util import global_consts



class BlackForest:
    def __init__(self, state_space_size, action_space_size, exploration, log_handle):
        self.state_size = state_space_size
        self.action_size = action_space_size
        self.learning_rate = 0.001
        self.firstHidden = 604
        self.secondHidden = 1166
        self.regressor = self._build_model()
        self.exploration = exploration
        self.exploration_decay = 0.999995
        self.min_exploration = 0.01
        self.memory = deque(maxlen=2000)
        self.batch_size = 200
        self.gamma = 0.94
        self.predictor = False
        self.predictor_action = np.zeros((1,self.state_size))
        self.log_handle = log_handle


    def _build_model(self):
        #Ignore AVX2 warning
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        regressor = Sequential()
        #regressor.add(Dense(output_dim=self.firstHidden, input_dim=self.state_size, activation='relu'))
        #regressor.add(Dense(output_dim=self.secondHidden, activation='relu'))
        #regressor.add(Dense(output_dim=self.action_size, activation='linear'))
        # Use Keras 2 API
        regressor.add(Dense(input_dim=self.state_size, activation='relu', units=self.firstHidden))
        regressor.add(Dense(activation='relu', units=self.secondHidden))
        regressor.add(Dense(activation='linear', units=self.action_size))
        regressor.compile(optimizer=Adam(lr=self.learning_rate), loss='mse')
        return regressor

    def setMode(self, mode):
        self.exploration = mode

    def type(self):
        return "dqn"

    def getMode(self):
        return self.exploration

    def getQTable(self):
        return self.predictor_action

    def getTrainingMemory(self):
        return self.memory;

    def predicting(self):
        return self.predictor

    def act(self, state, action):
        if np.random.rand() <= self.exploration:
            action = np.random.choice(range(self.action_size))
            self.predictor = False
        else:
            #print("Predictor:  state:{}".format(state))
            #print("Prediction direct:{}".format(self.regressor.predict(state)))
            self.predictor_action = self.regressor.predict(state)
            #print("Prediction action:{}".format(self.predictor_action))
            action = np.argmax(self.predictor_action, axis=1)[0]
            self.predictor = True
        return action

    def remember(self, state, action, reward, next_state):
        #print("Remmeber: s:{} a:{} r:{} ns:{}".format(state, action, reward, next_state))
        self.memory.append((state, action, reward, next_state))

    def replay(self):
        #print(repr(self.memory))
        if len(self.memory) < self.batch_size:
            print ("Not enough data to train dqn model. batch size:{} memory size:{}".format(self.batch_size, len(self.memory)))
            return
        minibatch = random.sample(list(self.memory), self.batch_size)
        for state, action, reward, next_state in minibatch:
            target = reward + self.gamma*np.max(self.regressor.predict(next_state)[0])
            target_f = self.regressor.predict(state)
            if self.log_handle:
                self.log_handle.write("action:{:d} reward:{:d} target:{:6.2f}\n".format(action, reward, target))
                self.log_handle.write("target_f before:{}\n".format(target_f[0]))
            #print("action:{:d} reward:{:d} target:{:6.2f}".format(action, reward, target))
            #print("target_f before:{}".format(target_f[0]))
            self.predictor_action = target_f
            target_f[0][action] = target
            if self.log_handle:
                self.log_handle.write(" target_f after:{}\n".format(target_f[0]))
            #print(" target_f after:{}".format(target_f[0]))
            self.regressor.fit(state, target_f, epochs=1, verbose=0)
        if self.exploration > self.min_exploration:
            self.exploration *= self.exploration_decay

    def load(self, name):
        self.regressor.load_weights(name)

    def save(self, name):
        self.regressor.save_weights(name)
