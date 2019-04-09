#this is a test comment
import numpy as np
import os, sys, time, traci, shutil, random, argparse
from models.dqn import Dqn
from models.fixed import Fixed

from utilities.led import led_demo
from utilities.util import get_state
from utilities.util import global_consts
from utilities.util import num_cars_halted_other_directions
from utilities.util import fail_safe
from utilities.util import get_phase

import xml.etree.ElementTree as ET
# Finished imports

# Process and store options
class Options:
    def __init__(self):
        self.cmdParser = argparse.ArgumentParser(description="Artificially Intelligent Traffic Controller Version 1.0")
        self.args = ""
        self.model = "dqn"
        self.benchmark = 0
        self.run = 3500
        self.runstep = 7
        self.weights = ""
        self.train = 20000
        self.demo = ""
        self.mapfile = ""
        self.switch_factor = 1
        self.log = ""
        self.verbosity = 1
        self.check = 0
        self.reward_function = "maxpass_minhalt"

        self.debug=False
        self.log_handle = None
        self.mode = "demo"
        self.epochs = 0

    def parse(self):
        self.cmdParser.add_argument("-m", "--model", choices=["fixed", "dqn", "ddqn", "ddpg"], default="dqn", help="Specify neural network model types to use for AI Traffic Controller")
        self.cmdParser.add_argument("-g", "--reward_function", choices=["maxpass", "minhalt", "maxpass_minhalt"], default="maxpass_minhalt", help="Specify reward function for Training")
        #self.cmdParser.add_argument("-b", "--benchmark", action="store_true", help="If specified, run fixed model vs dqn|ddqn|ddpg model for same traffic pattern")
        self.cmdParser.add_argument("-b", "--benchmark", type=int, default=0, help="If specified, run fixed model vs dqn|ddqn|ddpg model for same traffic pattern for given number of iterations")

        self.cmdParser.add_argument("-r", "--run", type=int, default=3500, help="Specify number of traci time units for which to run simulation")
        self.cmdParser.add_argument("-s", "--runstep", type=int, default=7, help="Specify number of traci time units for which to step simulation by")
        self.cmdParser.add_argument("-w", "--weights", default="", help="Specify file continating trained AI Traffic Controller model weights")
        # if want to make --train and --demo mutually exclusive toggle next 3 lines with 5th and 6th
        group = self.cmdParser.add_mutually_exclusive_group()
        group.add_argument("-t", "--train", type=int, default=0, help="Specify number of epochs to train the AI Traffic Controller model")
        group.add_argument("-d", "--demo", choices=["cmd", "gui", "led", "gui_led"], default="cmd", help="Specify kind(s) of demo to be run")
        #self.cmdParser.add_argument("-t", "--train", type=int, default=0, help="Specify number of epochs to train the AI Traffic Controller model")
        #self.cmdParser.add_argument("-d", "--demo", choices=["none", "gui", "led", "all"], default="none", help="Specify kind(s) of demo to be run")
        self.cmdParser.add_argument("-p", "--pattern", default="", help="Specify map.rou XML file for traffic pattern")
        self.cmdParser.add_argument("-f", "--fixed_switch_factor", type=int, default=16, help="Specify a factor of runstep by which fixed traffic light state should switch")
        self.cmdParser.add_argument("-l", "--log", default="", help="Specify log file name")
        self.cmdParser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2, 3], default=1, help="Set verbosity level. 0: silent, 1: benchmark, 2: stats: 3: details")
        self.cmdParser.add_argument("-c", "--check", type=int, choices=[0, 1], default=0, help="Set fail safe check level: 0 = disable, 1 = enable")


        self.args = self.cmdParser.parse_args()

        self.model = self.args.model
        self.benchmark = self.args.benchmark
        self.run = self.args.run
        self.runstep = self.args.runstep
        self.weights = self.args.weights
        self.train = self.args.train
        self.demo = self.args.demo
        self.mapfile = self.args.pattern
        self.switch_factor = self.args.fixed_switch_factor
        self.log = self.args.log
        self.verbosity = self.args.verbosity
        self.check = self.args.check
        self.reward_function = self.args.reward_function

        if(self.train > 0):
            self.mode = "training"
            self.epochs = self.train
            if(self.benchmark > 0):
                print("Error: The option --benchmark (-b) can only be specified with --demo (-d)\n")
                exit(1)
        else:
            self.epochs = 1
            self.mode = "demo"
            if (self.weights =="" and self.model != "fixed"):
                print("Weights file was not specified using --weights (-w) option\n")
                print("If --demo dqn|ddqn|ddp, then --weights must be specified\n")
                exit(1)

        if(self.benchmark > 0):
            if(self.model == "fixed"):
                print("The --benchmark can only be specified with -m dqn|ddqn|ddpg as it runs AI model against fixed\n")

        if(not self.log==""):
            self.debug = True
            self.log_handle = open(self.log, "w+")
            if(not self.log_handle):
                print("Could not create {}".format(self.log))
                sys.exit(1)
            else:
                self.log_handle.write("*******Log of sumo run*********\n***************************\n\n")

        if(self.verbosity > 2):
            print("AI Model:{}, Run: {}, Weights:{}, Train:{}, Demo:{}, Log:{}, Vebosity:{}, Benchmark:{}".format(self.model, self.run, self.weights, self.train, self.demo, self.log, self.verbosity, self.benchmark))


def getAvgTimeLost():
    tree = ET.parse(global_consts.TripInfoFile)
    root = tree.getroot()
    tot_lost, max_lost, num = 0,0,0
    for child in root.findall('tripinfo'):
        x = child.attrib
        num += 1
        y = float(x['timeLoss'])
        tot_lost += y
        if(max_lost < y):
           max_lost = y
    return tot_lost / num

def cars_passed(passed):
    detectorIDs = traci.inductionloop.getIDList()
    cars_passed = passed
    for detector in detectorIDs:
        data = traci.inductionloop.getVehicleData(detector)
        if len(data) > 0:
            if data[0][3] > 0:
                cars_passed += 1
    return cars_passed

def calc_reward_maxpass_minhalt(old_halt, new_halt, new_passed):
    passed = new_passed
    change = old_halt - new_halt
    reward = 0
    if(passed == 0 ):
        if(new_halt == 0):
            reward = 0
        else:
            reward = - new_halt
    else:
        if(new_halt == 0):
            reward = 4 * passed
        elif(change > 0):
            reward = 2 * passed
        elif(change == 0):
            reward = passed
        elif(change < 0):
            reward = change
    return reward

def calc_reward_maxpass(old_halt, new_halt, new_passed):
    passed = new_passed
    change = old_halt - new_halt
    reward = -1
    if(passed > 0 ):
        reward = 2 * passed
    return reward

def calc_reward_minhalt(old_halt, new_halt, new_passed):
    passed = new_passed
    change = old_halt - new_halt
    reward = 0
    if(change > 0):
        reward = 1
    elif(change < 0):
        reward = -1
    return reward

def calc_reward(options, old_halt, new_halt, new_passed):
    reward = 0
    if(options.reward_function == "maxpass_minhalt"):
        reward = calc_reward_maxpass_minhalt(old_halt, new_halt, new_passed)
    elif(options.reward_function == "maxpass"):
        reward = calc_reward_maxpass(old_halt, new_halt, new_passed)
    else:
        reward = calc_reward_minhalt(old_halt, new_halt, new_passed)
    return reward


def createAgent(options, model):
    exploration = 0
    agent = None
    if(options.mode == "training"):
        exploration = 1

    if(model == "dqn"):
        agent = Dqn(global_consts.StateSize, global_consts.ActionSize, exploration)
    elif(model == "ddqn"):
        print("Error: Model {} is not implemented yet".format(model))
        exit(1)
    elif(model == "ddpg"):
        print("Error: Model {} is not implemented yet".format(model))
        exit(1)
    elif(model == "fixed"):
        agent = Fixed(global_consts.StateSize, global_consts.ActionSize, options.switch_factor)
    else:
        print("Error: Model {} is not implemented yet".format(model))
        exit(1)

    if(not options.weights==""):
        print("Loading weights: {}".format(options.weights))
        agent.load(options.weights)

    return agent

def setupTrafficPattern(options):
    gen_map_sim_steps = 0
    if(options.mapfile == ""):
        #generate random traffic pattern
        # Uniform random range over [global_consts.MinNumVehicleSeed, global_consts.MaxNumVehicleSeed - global_consts.MinNumVehicleSeed))
        gen_map_sim_steps = int(global_consts.MinNumVehicleSeed + np.random.random_sample() * (global_consts.MaxNumVehicleSeed - global_consts.MinNumVehicleSeed))
        os.system(global_consts.GenMapCmd + " " + repr(gen_map_sim_steps))
    else:
        shutil.copyfile(options.mapfile, global_consts.MapFile)
    return gen_map_sim_steps

def getSumoCmd(options):
    cmd=global_consts.SumoCmd
    if (options.mode == "demo"):
        if(options.demo == "cmd" or options.demo == "led"):
            cmd = global_consts.SumoCmd
        else:
            cmd = global_consts.SumoCmd_GUI
    return cmd

def runSimulation(gen_map_sim_steps, cmd, simulation, options, agent):

    phase_time = 1
    traci.start(cmd)
    # passed = cars_passed(0)
    passed = 0
    halted_delta = 0
    passed_delta = 0
    detectorIDs = traci.inductionloop.getIDList()
    state = get_state(detectorIDs, phase_time, passed, halted_delta, passed_delta)
    go = True
    predictor_count = 0
    total_halt = 0
    total_passed = 0
    total_reward = 0
    sim_step = 0
    phase_time = 0
    action = 0
    new_action = 0
    new_halt = 0
    reward = 0

    while sim_step < options.run and go:

        sim_batch = int(sim_step / options.runstep)
        new_action = agent.act(state, action)
        #print("State:{} action:{} new_action:{} phase time:{}".format(state[0], action, new_action, phase_time))
        #print("Before filter: A:{} NA:{} T:{}".format(action, new_action, phase_time))
        if(options.mode == "demo" and options.check == 1):
            action = fail_safe(new_action, action, phase_time)
        else:
            action = new_action
        #print("After filter: A:{:d} NA:{:d} T:{:d}".format(action, new_action, phase_time))

        if(agent.predicting() == True):
            predictor_count = predictor_count + 1

        curr_phase = traci.trafficlights.getPhase(global_consts.TrafficLightId)
        new_phase = get_phase(action)
        phase_changed = False
        if(curr_phase != new_phase):
            phase_changed = True

        old_halt = new_halt

        if(phase_changed):
            passed = 0
            phase_time = 0

        old_passed = passed
        new_passed = 0
        for i in range(options.runstep):
            if(i==0 and phase_changed == True):
                traci.trafficlights.setPhase(global_consts.TrafficLightId, curr_phase + 1)
            if(i ==2):
                traci.trafficlights.setPhase(global_consts.TrafficLightId, new_phase)
            traci.simulationStep()
            sim_step += 1
            phase_time += 1
            passed = cars_passed(passed)

        new_passed = passed - old_passed
        new_halt = num_cars_halted_other_directions(curr_phase)
        halted_delta = old_halt-new_halt # positive is better
        passed_delta = new_passed # positive is better
        next_state = get_state(detectorIDs, phase_time, passed, halted_delta, passed_delta)
        if(options.mode == "training"):
            reward = calc_reward(options, old_halt, new_halt, new_passed)
            total_reward += reward

        total_passed += new_passed

        # Debugging log
        if(options.debug):
            if(options.verbosity > 1):
                options.log_handle.write("Epoch:{} Sim Step:{} Old Halt:{} New Halt:{} Reward:{}\n".format(simulation, sim_step, old_halt, new_halt, reward))
                options.log_handle.write("Phase Time:{} Car Passed:{} Predictor:{} Action:{} \n".format(phase_time, new_passed, agent.predicting(), action))
            if(options.verbosity > 2):
                options.log_handle.write("State:{} \nNext State:{}\nQ Table:{}\n".format(tuple(state), tuple(next_state), tuple(agent.getQTable())))
        # End debugging log

        if(options.mode == "training"):
            agent.remember(state, action, reward, next_state)

        state = next_state
        cars_left = traci.simulation.getMinExpectedNumber()
        if cars_left == 0:
            #print("Carf left is zero")
            go = False
        # end while sim_step < options.run and go

    traci.close()
    lost_time = float(getAvgTimeLost())


    if(options.verbosity > 1):
        print("Epoch:%i Predictor:%i Map Seed:%i Passed:%i Sim Step:%i Lost Time:%i Reward:%i Cars Left:%i" % (simulation, predictor_count, gen_map_sim_steps, total_passed, sim_step, lost_time, total_reward, cars_left))
        if(options.debug):
            if(options.verbosity > 2):
                options.log_handle.write("Epoch:{} Predictor:{} Map Seed:{} Passed:{} Sim Step:{} Lost Time:{} Reward:{} Cars Left:{}\n".format(simulation, predictor_count, gen_map_sim_steps, total_passed, sim_step, lost_time, total_reward, cars_left))
                options.log_handle.write("Training Memory Len:{} \n".format(len(agent.getTrainingMemory())))

    if(options.mode == "training"):
        agent.replay()
        if (simulation % global_consts.WeightDumpInterval == 0) & (simulation != 0):
            agent.save(global_consts.OutputDir + "./traffic" + repr(simulation) + ".h5")

    return (sim_step, lost_time)

def runTrainingEpochs(options, cmd, agent):
    for simulation in range(options.epochs):
        gen_map_sim_steps = setupTrafficPattern(options)
        (sim_step, lost_time) = runSimulation(gen_map_sim_steps, cmd, simulation, options, agent)

def runDemo(gen_map_sim_steps, options, cmd, agent):
    (sim_step, lost_time) = (0, 0)
    # Special handling for LED demo
    if (options.mode == "demo" and options.demo == "led"):
        led_demo(options.runstep, options.run, agent)
        sys.exit(0)
    else:
        # Run demo for one epoch for steps given in options
        (sim_step, lost_time) = runSimulation(gen_map_sim_steps, cmd, 0, options, agent)

    return (sim_step, lost_time)

def runBenchMark(options, cmd):
    if(options.model == "fixed"):
        print ("--model must be one of dqn|ddqn|ddpg if -b is specified. --model "+repr(options.model)+" was specified")
        exit(1)

    bm_h = open(global_consts.BenchMarkOutFile, "w+")
    if(not bm_h):
        print("Could not create {}".format(global_consts.BenchMarkOutFile))
        sys.exit(1)
    bm_h.write("Comparison between {} and {} for {} iterations\n".format("fixed", options.model, options.benchmark))
    bm_h.write("{}              {}   {}       {}          {}        {}         {}\n".format("itercount", "factor", "fixed_step[i]", "fixed_lossed_time[factor]", "ai_setp", "ai_lossed_time", "Improvement"))

    for itercount in range(options.benchmark):
        gen_map_sim_steps = setupTrafficPattern(options)
        factors = [1, 2, 4, 8, 16, 32]
        fixed_step = [0] * len(factors)
        fixed_lossed_time = [0] * len(factors)
        agent = createAgent(options, "fixed")
        agent.setMode(0)
        for i, fac in enumerate(factors):
            #print("{} {}".format(i, len(factors)))
            # Crrate Fixed model and run a demo and get numbers
            options.switch_factor = fac
            #print("factor[i]:{}".format( factors[i]))
            (step, loss) = runDemo(gen_map_sim_steps, options, cmd, agent)
            fixed_step[i] = step
            fixed_lossed_time[i] = loss
            #print("factor[i]:{} fixed_step[i]:{} fixed_lossed_time[i]:{}".format( factors[i], fixed_step[i], fixed_lossed_time[i] ))
        # Create now given neural net model and run with same traffic setupTrafficPattern
        # Check  options.model is not fixed
        agent = createAgent(options, options.model)
        agent.setMode(0)
        (ai_step, ai_lossed_time) = runDemo(gen_map_sim_steps, options, cmd, agent)

        for i, fac in enumerate(factors):
            bm_h.write("{}              {}   {}       {}          {}        {}         {}\n".format(itercount,  fac, fixed_step[i], fixed_lossed_time[i], ai_step, ai_lossed_time, (fixed_lossed_time[i] * fixed_step[i])/(ai_step*ai_lossed_time) ))
            if(options.verbosity > 0):
                print("Iter:{} Facter:{} Fixed Sim Step:{} Fixed Lost Time:{} AI Sim Step:{} AI Lost Time:{} Improvement:{}".format(itercount,  fac, fixed_step[i], fixed_lossed_time[i], ai_step, ai_lossed_time, (fixed_lossed_time[i] * fixed_step[i])/(ai_step*ai_lossed_time)))

    bm_h.close()

def initialize():
    np.set_printoptions(linewidth=320)
    np.set_printoptions(precision=2, suppress=True)
    np.set_printoptions(formatter={'float': '{: 8.2f}'.format})
    np.set_printoptions(formatter={'int': '{: 8d}'.format})
    options = Options()
    options.parse()
    if(options.verbosity > 0):
        print("{} version:{}\n".format(global_consts.ProgramName, global_consts.Version))

    #create dir/file etc.
    if(not os.path.exists(global_consts.OutputDir)):
        os.mkdir(global_consts.OutputDir)
    return options

def finalize(options):
    if(options.log_handle):
        options.log_handle.close()


def main():

    options = initialize()
    cmd = getSumoCmd(options)
    if(options.benchmark > 0):
        runBenchMark(options, cmd)
    else:
        agent = createAgent(options, options.model)
        if(options.mode == "training"):
            runTrainingEpochs(options, cmd, agent)
        else:
            gen_map_sim_steps = setupTrafficPattern(options)
            (sim_step, lost_time) = runDemo(gen_map_sim_steps, options, cmd, agent)
            if(options.verbosity > 0):
                print("Sim Steps:{} Lost Time:{}\n".format(sim_step, lost_time))
    finalize(options)

if __name__ == '__main__':
    main()
