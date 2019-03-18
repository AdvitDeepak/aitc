import numpy as np
import random, traci
from utilities.util import global_consts
from collections import deque

from utilities.util import get_phase
from utilities.util import increment_action
from utilities.util import num_cars_halted_line
from utilities.util import go_to_phase_that_has_halted_cars


class Fixed:
    def __init__(self, state_space_size, action_space_size, switch_factor):
        self.state_size = state_space_size
        self.action_size = action_space_size
        self.memory = deque(maxlen=20)
        self.count = 0
        self.MaxCount = switch_factor
        self.mode = 0


    def predicting(self):
        return False

    def type(self):
        return "fixed"

    def getQTable(self):
        arr = [0]
        arr[0] = self.count
        return arr

    def getTrainingMemory(self):
        return self.memory

    def getMode(self):
        return self.mode

    def setMode(self, mode):
        self.mode = mode
        return

    def act(self, state, action):
        self.count +=1

        if( self.count == self.MaxCount):
            self.count = 0
            action = go_to_phase_that_has_halted_cars(action)

        return action
        # self.count +=1
        #
        # if( self.count == self.MaxCount):
        #     self.count = 0
        #     max_iteration = 0
        #     action = increment_action(action, 1)
        #     while (num_cars_halted_line(get_phase(action)) == 0 and max_iteration < global_consts.ActionSize):
        #          action = increment_action(action, 1)
        #          max_iteration += 1

        return action

    def remember(self, state, action, reward, next_state):
        # Do nothing
        return

    def replay(self):
        # do nothing
        return

    def load(self, name):
          # do nothing
          return

    def save(self, name):
        # do nothing
        return
