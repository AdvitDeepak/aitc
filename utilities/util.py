import traci
import numpy as np

class global_consts:
    ProgramName = "AITC"
    Version = "1.1"
    TrafficLightId = "65616300"
    # Declare all globals in capital
    SumoConfig = "data/map.sumocfg"
    SumoCmd = ["sumo", "-c", SumoConfig, "--tripinfo-output", "data/tripinfo.xml",  "--start", "--no-warnings", "--time-to-teleport", "-1"]
    SumoCmd_GUI = ["sumo-gui", "-c", SumoConfig, "--tripinfo-output", "data/tripinfo.xml",  "--no-warnings", "--time-to-teleport", "-1"]
    StateSize = 21
    ActionSize = 8
    PhaseToActionRatio = 2
    MaxNumVehicleSeed = 400
    MinNumVehicleSeed = 100
    TripInfoFile = "data/tripinfo.xml"
    GenMapCmd = "python ./utilities/generateMap.py"
    OutputDir = "output"
    BenchMarkOutFile = "bm.txt"
    WeightDumpInterval = 100
    MapFile = "data/map.rou.xml"
    Lanes = {
        'lane1':"-393625777_0", 'lane2':"-393625777_1", 'lane3':"-393625777_2",
        'lane4':"393627613_0", 'lane5':"393627613_1", 'lane6':"393627613_2",
        'lane7a':"-393645137_0", 'lane7b':"-393645137_1", 'lane8':"-393645126_0", 'lane9':"-393645126_2",
        'lane10':"-393645126_1", 'lane11a':"393645138_0", 'lane11b':"393645138_1", 'lane12':"393645129_0",
        'lane13':"393645129_2", 'lane14':"393645129_1"
    }
    MaxPhaseTime = 500


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
#lambda is a way to write a function in statement in one line; saves time to return x

def get_vehicle_count(func_lane, func_edge):
    # W0, W1
    ET = func_lane(global_consts.Lanes['lane1']) + \
         func_lane(global_consts.Lanes['lane2'])
    # W2
    EL = func_lane(global_consts.Lanes['lane3'])
    # E0, E1
    WT = func_lane(global_consts.Lanes['lane4']) + \
         func_lane(global_consts.Lanes['lane5'])
    # E2
    WL = func_lane(global_consts.Lanes['lane6'])
    # N0, N1
    ST = func_lane(global_consts.Lanes['lane7a']) + \
         func_lane(global_consts.Lanes['lane8']) + \
         func_lane(global_consts.Lanes['lane10'])
    if (func_lane(global_consts.Lanes['lane10']) >= 5):
        ST += func_lane(global_consts.Lanes['lane7b'])
    # N2
    SL = func_lane(global_consts.Lanes['lane9'])
    if (func_lane(global_consts.Lanes['lane9']) >= 5):
        SL += func_lane(global_consts.Lanes['lane7b'])
    # S0, S1
    NT = func_lane(global_consts.Lanes['lane11a']) + \
         func_lane(global_consts.Lanes['lane12']) + \
         func_lane(global_consts.Lanes['lane14'])
    if (func_lane(global_consts.Lanes['lane14']) >= 5):
        NT += func_lane(global_consts.Lanes['lane11b'])
    # S2
    NL = func_lane(global_consts.Lanes['lane13'])
    if (func_lane(global_consts.Lanes['lane13']) >= 5):
        NL += func_lane(global_consts.Lanes['lane11b'])

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

def num_cars_my_direction(curr_phase, WT, WL, ET, EL, NT, NL, ST, SL):
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
        cars_behind = WT + WL
    elif curr_phase == 10:
        cars_behind = NT + NL
    elif curr_phase == 12:
        cars_behind = ET + EL
    elif curr_phase == 14:
        cars_behind = ST + SL
    return cars_behind

# The phase for which light is on, cars are moving, so do
# not count those
def num_cars_halted_other_directions(curr_phase):
    WT, WL, ET, EL, NT, NL, ST, SL = get_halted_in_each_direction()
    total = WT + WL + ET + EL + NT + NL + ST + SL
    cars_behind = num_cars_my_direction(curr_phase, WT, WL, ET, EL, NT, NL, ST, SL)
    cars_behind = total - cars_behind

    #print("WT {} WL {} ET {} EL {} NT {} NL {} ST {} SL {} | P {} Behind other {}".format(WT, WL, ET, EL, NT, NL, ST, SL, curr_phase, cars_behind ))

    return cars_behind

def num_cars_my_direction_line(curr_phase):
    WT, WL, ET, EL, NT, NL, ST, SL = get_vehicle_in_each_direction()
    cars_behind = num_cars_my_direction(curr_phase, WT, WL, ET, EL, NT, NL, ST, SL)
    return cars_behind

def num_cars_halted_line(curr_phase):
    WT, WL, ET, EL, NT, NL, ST, SL = get_halted_in_each_direction()
    cars_behind = num_cars_my_direction(curr_phase, WT, WL, ET, EL, NT, NL, ST, SL)
    #print("NCHL WT {} WL {} ET {} EL {} NT {} NL {} ST {} SL {} | P {} Behind {}".format(WT, WL, ET, EL, NT, NL, ST, SL, curr_phase, cars_behind))
    return cars_behind

def get_phase(action):
    return action * global_consts.PhaseToActionRatio

def increment_action(action, by_count):
    new_action = (action + by_count) % global_consts.ActionSize
    return new_action

def go_to_phase_that_has_halted_cars(action):

    max_iteration = 0
    #print("BEFORE Num_cars_halted:{} Action:{} Max_Iteration:{}\n".format(num_cars_halted_line(get_phase(action)), action, max_iteration))
    while (num_cars_halted_line(get_phase(action)) == 0 and max_iteration < global_consts.ActionSize):

         action = increment_action(action, 1)
         #print("Num_cars_halted:{} Action:{} Max_Iteration:{}\n".format(num_cars_halted_line(get_phase(action)), action, max_iteration))
         max_iteration += 1
    return action

def get_state(detectorIDs, phase_time, passed, halted_delta, passed_delta):
    state = []

    # halted in each direction (8 vals)
    WTh, WLh, ETh, ELh, NTh, NLh, STh, SLh = get_halted_in_each_direction()
    state.extend([WTh, WLh, ETh, ELh, NTh, NLh, STh, SLh])

    # total vehicles in each direction (8 vals)
    WT, WL, ET, EL, NT, NL, ST, SL = get_vehicle_in_each_direction()
    state.extend([WT, WL, ET, EL, NT, NL, ST, SL])

    # current phase (1 val)
    curr_phase = traci.trafficlights.getPhase(global_consts.TrafficLightId)
    state.append(curr_phase)

    # elapsedTime (1 val)
    state.append(phase_time)

    # rateGoing (1 val)
    cars_passed = passed
    rate = cars_passed / phase_time
    state.append(rate)

    # the change in the number of cars halted (1 val)
    state.append(halted_delta)

    # the change in the number of cars passed (1 val)
    state.append(passed_delta)

    #print("WTh {} WLh {} ETh {} ELh {} NTh {} NLh {} STh {} SLh {} | WT {} WL {} ET {} EL {} NT {} NL {} ST {} SL {} | P {} Time {} Rate {} dHalt {} dPass {}".format(WTh, WLh, ETh, ELh, NTh, NLh, STh, SLh, WT, WL, ET, EL, NT, NL, ST, SL, curr_phase, phase_time, rate, halted_delta, passed_delta ))
    state = np.array(state)
    #print("State:{} Shape:{}".format(state, state.shape[0]))
    state = state.reshape((1, state.shape[0]))
    #print("State after reshape:{} Shape:{}".format(state, state.shape[0]))

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
    cars_behindline_curr_phase = num_cars_my_direction_line(curr_phase)
    #print("Debug2: Cuur phase cars behind: {} New halted: {} phase_time: {} current phase:{} Action:{} New Action:{} \n".format(cars_behindline_curr_phase, new_halt, phase_time, curr_phase, action, new_action))
    if( (cars_behindline_curr_phase == 0 and new_halt > 0) or (phase_time > global_consts.MaxPhaseTime) ):
        final_action = go_to_phase_that_has_halted_cars(action)
        #print("Debug3: Cuur phase cars behind: {} New halted: {} phase_time: {} current phase:{} Action:{} New Action:{} Final Action:{} \n".format(cars_behindline_curr_phase, new_halt, phase_time, curr_phase, action, new_action, final_action))
        return final_action

    #print("Debug3: New halted: {} phase_time: {} current phase:{} Action:{} New Action:{} \n".format(new_halt, phase_time, curr_phase, action, new_action))
    return new_action
