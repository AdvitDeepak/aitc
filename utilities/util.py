import traci
import numpy as np

class global_consts:
    ProgramName = "AITC"
    Version = "1.0"
    TrafficLightId = "65616300"
    # Declare all globals in capital
    SumoConfig = "data/map.sumocfg"
    SumoCmd = ["sumo", "-c", SumoConfig, "--tripinfo-output", "data/tripinfo.xml",  "--start", "--no-warnings", "--time-to-teleport", "-1"]
    SumoCmd_GUI = ["sumo-gui", "-c", SumoConfig, "--tripinfo-output", "data/tripinfo.xml",  "--no-warnings", "--time-to-teleport", "-1"]
    StateSize = 19
    ActionSize = 8
    PhaseToActionRatio = 2
    MaxNumVehicleSeed = 400
    MinNumVehicleSeed = 100
    TripInfoFile = "data/tripinfo.xml"
    GenMapCmd = "python ./utilities/generateMap.py"
    OutputDir = "output"
    BenchMarkOutFile = "bm.txt"
    MapFile = "data/map.rou.xml"
    Lanes = {
        'lane1':"-393625777_0", 'lane2':"-393625777_1", 'lane3':"-393625777_2",
        'lane4':"393627613_0",  'lane5':"393627613_1", 'lane6':"393627613_2",
        'lane7':"-393645137",   'lane8':"-393645126_0", 'lane9':"-393645126_2",
        'lane10':"-393645126_1", 'lane11':"393645138",   'lane12':"393645129_0",
        'lane13':"393645129_2", 'lane14':"393645129_1"
    }


def make_func_lane(isHaltingNumber):
    if(isHaltingNumber):
        return lambda x: traci.lane.getLastStepHaltingNumber(x)
    else:
        return lambda x: traci.lane.getLastStepVehicleNumber(x)

def make_func_edge(isHaltingNumber):
    if(isHaltingNumber):
        return lambda x: traci.edge.getLastStepHaltingNumber(x)
    else:
        return lambda x: traci.edge.getLastStepVehicleNumber(x)


def get_vehicle_count(func_lane, func_edge):
    # W0, W1
    WT = func_lane(global_consts.Lanes['lane1']) + \
         func_lane(global_consts.Lanes['lane2'])
    # W2
    WL = func_lane(global_consts.Lanes['lane3'])
    # E0, E1
    ET = func_lane(global_consts.Lanes['lane4']) + \
         func_lane(global_consts.Lanes['lane5'])
    # E2
    EL = func_lane(global_consts.Lanes['lane6'])
    # N0, N1
    NT = func_edge(global_consts.Lanes['lane7']) + \
         func_lane(global_consts.Lanes['lane8'])
    # N2
    NL = func_lane(global_consts.Lanes['lane9']) + \
         func_lane(global_consts.Lanes['lane10'])
    # S0, S1
    ST = func_edge(global_consts.Lanes['lane11']) + \
         func_lane(global_consts.Lanes['lane12'])
    # S2
    SL = func_lane(global_consts.Lanes['lane13']) + \
         func_lane(global_consts.Lanes['lane14'])

    return WT, WL, ET, EL, NT, NL, ST, SL


def get_vehicle_in_each_direction():
    func_lane = make_func_lane(False)
    func_edge = make_func_edge(False)
    #print("vehicle: {} {}\n".format(func_lane, func_edge))
    WT, WL, ET, EL, NT, NL, ST, SL = get_vehicle_count(func_lane, func_edge)
    return WT, WL, ET, EL, NT, NL, ST, SL

def get_halted_in_each_direction():
    func_lane = make_func_lane(True)
    func_edge = make_func_edge(True)
    #print("halted: {} {}\n".format(func_lane, func_edge))
    WT, WL, ET, EL, NT, NL, ST, SL = get_vehicle_count(func_lane, func_edge)
    return WT, WL, ET, EL, NT, NL, ST, SL

def num_cars_behind(curr_phase, WT, WL, ET, EL, NT, NL, ST, SL):
    cars_behind = 0
    if curr_phase % global_consts.PhaseToActionRatio == 1:
        curr_phase = curr_phase - 1
    if curr_phase == 0:
        cars_behind = WL + EL
    elif curr_phase == 2:
        cars_behind = NL + SL
    elif curr_phase == 4:
        cars_behind = WT + ET
    elif curr_phase == 6:
        cars_behind = NT + ST
    elif curr_phase == 8:
        cars_behind = ET + EL
    elif curr_phase == 10:
        cars_behind = ST + SL
    elif curr_phase == 12:
        cars_behind = WT + WL
    elif curr_phase == 14:
        cars_behind = NT + NL
    return cars_behind

# The phase for which light is on, cars are moving, so do
# not count those
def num_cars_halted_other_directions(curr_phase):
    WT, WL, ET, EL, NT, NL, ST, SL = get_halted_in_each_direction()
    total = WT + WL + ET + EL + NT + NL + ST + SL
    cars_behind = num_cars_behind(curr_phase, WT, WL, ET, EL, NT, NL, ST, SL)
    cars_behind = total - cars_behind
    return cars_behind

def num_cars_behind_line(curr_phase):
    WT, WL, ET, EL, NT, NL, ST, SL = get_vehicle_in_each_direction()
    cars_behind = num_cars_behind(curr_phase, WT, WL, ET, EL, NT, NL, ST, SL)
    return cars_behind

def num_cars_halted_line(curr_phase):
    WT, WL, ET, EL, NT, NL, ST, SL = get_halted_in_each_direction()
    cars_behind = num_cars_behind(curr_phase, WT, WL, ET, EL, NT, NL, ST, SL)
    return cars_behind

def get_phase(action):
    return action * global_consts.PhaseToActionRatio

def increment_action(action, by_count):
    new_action = (action + by_count) % global_consts.ActionSize
    return new_action

def go_to_phase_that_has_halted_cars(action):

    max_iteration = 0
    while (num_cars_halted_line(get_phase(action)) == 0 and max_iteration < global_consts.ActionSize):

         action = increment_action(action, 1)
         #print("Loop:{} Action:{} \n".format(num_cars_halted_line(get_phase(action)), action))
         max_iteration += 1
    return action

def get_state(detectorIDs, phase_time, passed):
    state = []
    # halted in each direction (12 vals)
    for detector in detectorIDs:
        lane = traci.inductionloop.getLaneID(detector)
        halt = traci.lane.getLastStepHaltingNumber(lane)
        state.append(halt)

    halt = traci.lane.getLastStepHaltingNumber("393645138_0")
    state.append(halt)

    halt = traci.lane.getLastStepHaltingNumber("393645138_1")
    state.append(halt)

    halt = traci.lane.getLastStepHaltingNumber("-393645137_0")
    state.append(halt)

    halt = traci.lane.getLastStepHaltingNumber("-393645137_1")
    state.append(halt)

    # current phase (1 val)
    curr_phase = traci.trafficlights.getPhase(global_consts.TrafficLightId)
    state.append(curr_phase)

    # elapsedTime (1 val)
    #print("Elapsed:", phase_time)
    state.append(phase_time)

    # rateGoing (1 val)
    cars_passed = passed
    rate = cars_passed / phase_time
    state.append(rate)

    state = np.array(state)
    state = state.reshape((1, state.shape[0]))

    return state

def get_total_halt():
    total_halt = 0
    for edge in traci.edge.getIDList():
        total_halt += traci.edge.getLastStepHaltingNumber(edge)
    return total_halt

def fail_safe(new_action, action, phase_time):

    #curr_phase = traci.trafficlights.getPhase(global_consts.TrafficLightId)
    curr_phase = get_phase(action)
    new_halt = num_cars_halted_other_directions(curr_phase)
    if(new_halt == 0):
        # There is no car in other directions, keep current phase
        #print("Debug1: New halted: {} phase_time: {} current phase:{} Action:{} New Action:{} \n".format(new_halt, phase_time, curr_phase, action, new_action))
        return action
    cars_behindline_curr_phase = num_cars_behind_line(curr_phase)
    if(cars_behindline_curr_phase == 0 and (num_cars_behind_line(new_action * 2) == 0)):
        final_action = go_to_phase_that_has_halted_cars(action)
        #print("Debug2: Cuur phase cars behind: {} New halted: {} phase_time: {} current phase:{} Action:{} New Action:{} Final Action:{} \n".format(cars_behindline_curr_phase, new_halt, phase_time, curr_phase, action, new_action, final_action))
        return final_action

    #print("Debug3: New halted: {} phase_time: {} current phase:{} Action:{} New Action:{} \n".format(new_halt, phase_time, curr_phase, action, new_action))
    return new_action
