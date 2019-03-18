import pygame
import numpy as np
import os, sys, time, serial, traci, random, math
from utilities.blinkytape import BlinkyTape

from utilities.blinky import edge_to_strip
from utilities.blinky import strip_pos_normal
from utilities.blinky import strip_pos_isct
from utilities.blinky import light_to_illuminate
from utilities.blinky import tL_to_illuminate
from utilities.blinky import show_names

from utilities.util import get_state
from utilities.util import global_consts



def send_lights(sim_steps, prev_states, bb):

    vehicles = traci.vehicle.getIDList()
    lights, colors, final_lights = [], [], []
    for vehicle in vehicles:
        lane = traci.vehicle.getLaneID(vehicle)
        edge = traci.lane.getEdgeID(lane)
        pos = traci.vehicle.getLanePosition(vehicle)
        col = traci.vehicle.getColor(vehicle)

        detectors = traci.inductionloop.getIDList()
        veh_detector = 0

        for detector in detectors:
            if traci.inductionloop.getLaneID(detector) == lane:
                veh_detector = detector
                detector_data = traci.inductionloop.getVehicleData(veh_detector)

        try:
            det_veh_name = detector_data[0][0]
            det_veh_exit = detector_data[0][3]
        except:
            det_veh_name = "There are no cars"
            det_veh_exit = "None have left"

        length_lane = traci.lane.getLength(lane)
        lane = int(lane.split("_")[1])

        geo_pos = traci.vehicle.getPosition(vehicle)
        tL_pos = (229.57,287.73)

        driving_dist = math.sqrt((geo_pos[0] - tL_pos[0])*(geo_pos[0] - tL_pos[0]) + (geo_pos[1] - tL_pos[1])*(geo_pos[1] - tL_pos[1]))

        if (driving_dist < 150):
            if edge[0:1] != ":":
                light_strip = edge_to_strip(int(edge), lane)
                prev_states[vehicle] = [light_strip, 0, edge]

                light_strip_pos = strip_pos_normal(light_strip, pos, length_lane, int(edge))
                illuminate = light_to_illuminate(light_strip, light_strip_pos)
                lights.append(illuminate)
                colors.append(col)

            else:
                ls = prev_states[vehicle][0]
                if ls[0:1] != "N" and ls[0:1] != "S":
                    prev_state = prev_states[vehicle]
                    light_strip = prev_state[0]
                    turn_time = prev_state[1]
                    illuminate = strip_pos_isct(str(light_strip), pos, length_lane, vehicle, turn_time)
                    if turn_time == 2:
                        prev_states[vehicle] = [light_strip, 0, prev_state[2]]
                    elif turn_time == 1:
                        prev_states[vehicle] = [light_strip, 2, prev_state[2]]
                    else:
                        prev_states[vehicle] = [light_strip, 1, prev_state[2]]

                    lights.append(illuminate)
                    colors.append(col)
                else:
                    edge = prev_states[vehicle][2]
                    light_strip = prev_states[vehicle][0]
                    light_strip_pos = strip_pos_normal(light_strip, pos, length_lane, int(edge))
                    illuminate = light_to_illuminate(light_strip, light_strip_pos)
                    prev_states[vehicle] = [light_strip,0,edge]


    for j in range(511):
        if j in lights:
            color_pos = lights.index(j)
            color = colors[color_pos]
            color = color[:3]

            final_lights.append(color)
        else:
            final_lights.append((0,0,0))

    final_lights = final_lights[51:]
    final_traffic_lights = tL_to_illuminate(traci.trafficlights.getPhase(global_consts.TrafficLightId))
    final = final_traffic_lights + final_lights

    bb.send_list(final)
    return prev_states

def get_buttons():
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    on = None
    for i in range(4):
        button = joystick.get_button(i)
        if button == 1:
            on = i
    return on

def start_traci(sumoBinary, sumoConfig):
    sumoCmd = [sumoBinary, "-c", sumoConfig, "--tripinfo-output", "data/tripinfo.xml"]
    traci.start(sumoCmd)
    prev_states = {"0":[0,0,"0"]}

    return prev_states

def cars_passed(passed):
    detectorIDs = traci.inductionloop.getIDList()
    cars_passed = passed
    for detector in detectorIDs:
        data = traci.inductionloop.getVehicleData(detector)
        if len(data) > 0:
            if data[0][3] > 0:
                cars_passed += 1
    return cars_passed

def one_simulation_step(curr_action, sim_steps, run_step, passed, phase_time, prev_states, bb, agent):
    passed = cars_passed(passed)
    detectorIDs = traci.inductionloop.getIDList()
    state = get_state(detectorIDs, phase_time, passed)
    action = agent.act(state, curr_action)
    new_phase = action * 2

    if (traci.trafficlights.getPhase(global_consts.TrafficLightId) != new_phase):
        phase_time = 1
    else:
        phase_time += 1

    if (sim_steps % run_step == 0):
        traci.trafficlights.setPhase(global_consts.TrafficLightId, new_phase)

    for vehicle in traci.simulation.getDepartedIDList():
        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255), 0)
        traci.vehicle.setColor(vehicle, color)

    traci.simulationStep()
    prev_states = send_lights(sim_steps, prev_states, bb)

    return prev_states, passed, phase_time, action

def led_demo(run_step, run, agent):
    bb = BlinkyTape("COM10")
    sumoBinary = "sumo-gui"
    sumoConfig = "data/map.sumocfg"
    pygame.init()

    size = [60, 30]
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("My Game")
    done = False
    clock = pygame.time.Clock()
    pygame.joystick.init()

    prev_states = start_traci(sumoBinary, sumoConfig)
    passed = 0
    phase_time = 1
    sim_steps = 0
    curr_action = 0
    action = 0
    counts_2_pressed = 0
    delays = [0,0,0,0.01,0.02,0.05,0.1]
    curr_delay = 0
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done=True

        button_state = get_buttons()

        if button_state == 0:
            # Reset the simulation
            traci.close()
            sys.exit(0)
        elif button_state == 1:
            # Show credits
            pause = True
            white = (60,0,0)
            bb.send_list(show_names(white))
            while pause:
                button_state = get_buttons()
                if button_state == 1:
                    pause = False

        elif button_state == 2:
            # Rotate through traffic patterns
            counts_2_pressed += 1
            curr_delay = delays[counts_2_pressed %7]
        elif button_state == 3:
            # Pause/restart the simulation
            pause = True
            while pause:
                button_state = get_buttons()
                if button_state == 3:
                    pause = False
        else:
            (prev_states, passed, phase_time, curr_action) = one_simulation_step(curr_action, sim_steps, run_step, passed, phase_time, prev_states, bb, agent)
            sim_steps += 1

        if sim_steps == run:
            done = True

        pygame.display.flip()
        clock.tick(20)
        time.sleep(curr_delay)

    pygame.quit()
    traci.close()
