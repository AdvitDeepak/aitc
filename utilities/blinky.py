import os, sys, traci

def edge_to_strip(edge, lane):
    strip = ""
    # Eastbound
    if edge == -393625777:
        if lane == 0:
            strip = "W0"
        if lane == 1:
            strip = "W1"
        if lane == 2:
            strip = "W2"

    if edge == -393627613:
        if lane == 0:
            strip = "E4"
        if lane == 1:
            strip = "E3"

    # Westbound
    if edge == 393627613:
        if lane == 0:
            strip = "E0"
        if lane == 1:
            strip = "E1"
        if lane == 2:
            strip = "E2"

    if edge == 393625777:
        if lane == 1:
            strip = "W3"
        if lane == 0:
            strip = "W4"

    # Northbound
    if edge == 393645138:
        if lane == 0:
            strip = "S0"
        if lane == 1:
            strip = "S1"

    if edge == 393645129:
        if lane == 0:
            strip = "S0"
        if lane == 1:
            strip = "S1"
        if lane == 2:
            strip = "S2"

    if edge == 393645126:
        if lane == 0:
            strip = "N4"
        if lane == 1:
            strip = "N3"

    if edge == 393645137:
        if lane == 0:
            strip = "N4"
        if lane == 1:
            strip = "N3"

    # Southbound
    if edge == -393645137:
        if lane == 0:
            strip = "N0"
        if lane == 1:
            strip = "N1"

    if edge == -393645126:
        if lane == 0:
            strip = "N0"
        if lane == 1:
            strip = "N1"
        if lane == 2:
            strip = "N2"

    if edge == -393645129:
        if lane == 0:
            strip = "S4"
        if lane == 1:
            strip = "S3"

    if edge == -393645138:
        if lane == 0:
            strip = "S4"
        if lane == 1:
            strip = "S3"

    return strip

def strip_pos_normal(strip, pos, length, edge):

    if strip[0] == 'W':

        if strip[1] == '3' or strip[1] == '4':
            pos = length - pos

        length = length - 170
        pos = abs(pos - 170)

        light_pos = int((pos / length)*19)


    if strip[0] == 'E':


        if strip[1] == '3' or strip[1] == '4':
            pos = length - pos

        length = length - 170
        pos = abs(pos - 170)

        light_pos = int((pos / length)*16)

    if strip[0] == 'N':
        # There are 18 LEDs
        length = 324

        if edge == -393645126:
            pos = pos + length * 292/324
        if edge == 393645126:
            pos = 35 - pos + 292
        if edge == 393645137:
            pos = 292 - pos

        length = 324 - 170
        pos = abs(pos - 170)

        light_pos = int((pos / length) * 15)

    if strip[0] == 'S':
        # There are 22 LEDs
        length = 324

        if edge == 393645129:
            pos = pos + length * 292/324
        if edge == -393645129:
            pos = 35 - pos + 292
        if edge == -393645138:
            pos = 292 - pos

        length = 324 - 170
        pos = abs(pos - 170)

        light_pos = int((pos / length) *18)

    return (light_pos)

def strip_pos_isct(strip, pos, length, vehicle, turn_time):
    vehicle = vehicle.split('_')[0]
    states = []

    if strip == "W0":
        if vehicle == "right":
            states = [456,456,456]
        if vehicle == "through":
            states = [457,458,459]

    if strip == "W1":
        if vehicle == "through":
            states = [457,458,459]

    if strip == "W2":
        if vehicle == "left":
            states = [370,157,287]



    if strip == "E0":
        if vehicle == "right":
            states = [288,288,288]
        if vehicle == "through":
            states = [287,286,285]

    if strip == "E1":
        if vehicle == "through":
            states = [111,157,197]

    if strip == "E2":
        if vehicle == "left":
            states = [372,371,456]



    if strip == "N0":
        if vehicle == "right":
            states = [285,285,285]
        if vehicle == "through":
            states = [285,370,456]

    if strip == "N1":
        if vehicle == "through":
            states = [197,370,456]

    if strip == "N2":
        if vehicle == "left":
            states = [286,372,70]



    if strip == "S0":
        if vehicle == "right":
            states = [459,459,459]
        if vehicle == "through":
            states = [459,70,71]

    if strip == "S1":
        if vehicle == "through":
            states = [458,372,287]

    if strip == "S2":
        if vehicle == "left":
            states = [457,371,197]

    return states[int(turn_time)]

def light_to_illuminate(strip, light_strip_pos):
    if strip == 'N0':
        start = -262
    if strip == 'N1':
        start = 180
    if strip == 'N2':
        start = -176
    if strip == 'N3':
        start = 93
    if strip == 'N4':
        start = -90

    if strip == 'S0':
        start = 52
    if strip == 'S1':
        start = -132
    if strip == 'S2':
        start = 138
    if strip == 'S3':
        start = -218
    if strip == 'S4':
        start = 222



    if strip == 'E0':
        start = -304
    if strip == 'E1':
        start = 309
    if strip == 'E2':
        start = -389
    if strip == 'E3':
        start = 393
    if strip == 'E4':
        start = -475

    if strip == 'W0':
        start = 437
    if strip == 'W1':
        start = -433
    if strip == 'W2':
        start = 351
    if strip == 'W3':
        start = -345
    if strip == 'W4':
        start = 266

    return abs(light_strip_pos + start)

def tL_to_illuminate(state):
    r = (0,255,0)
    g = (255,0,0)
    y = (255,255,0)
    n = (0,0,0)
    lights = []
    if state == 4:
        for i in range(50):
            if i ==  2 or i == 18 :
                lights.append(g)
            elif i == 3 or i == 21 or i == 29 or i == 24 or i == 8 or i == 13:
                lights.append(r)
            else:
                lights.append(n)

    if state == 5:
        for i in range(50):
            if i == 1  or i == 17 :
                lights.append(y)
            elif i == 3 or i == 21 or i == 29 or i == 24 or i == 8 or i == 13:
                lights.append(r)
            else:
                lights.append(n)



    if state == 6:
        for i in range(50):
            if i == 27 or i == 10:
                lights.append(g)
            elif i == 24 or i == 13 or i == 21 or i == 16 or i == 0 or i == 3:
                lights.append(r)
            else:
                lights.append(n)

    if state == 7:
        for i in range(50):
            if i == 27 or i == 10:
                lights.append(y)
            elif i == 24 or i == 13 or i == 21 or i == 16 or i == 0 or i == 3:
                lights.append(r)
            else:
                lights.append(n)



    if state == 0:
        for i in range(50):
            if i == 19 or i == 5:
                lights.append(g)
            elif i == 0 or i == 16 or i == 29 or i == 24 or i == 8 or i == 13:
                lights.append(r)
            else:
                lights.append(n)

    if state == 1:
        for i in range(50):
            if i == 20 or i == 4:
                lights.append(y)
            elif i == 0 or i == 16 or i == 29 or i == 24 or i == 8 or i == 13:
                lights.append(r)
            else:
                lights.append(n)



    if state == 2:
        for i in range(50):
            if i == 26 or i == 11:
                lights.append(g)
            elif i == 29 or i == 8 or i == 21 or i == 16 or i == 0 or i == 3:
                lights.append(r)
            else:
                lights.append(n)

    if state == 3:
        for i in range(50):
            if i == 25 or i == 12:
                lights.append(y)
            elif i == 29 or i == 8 or i == 21 or i == 16 or i == 0 or i == 3:
                lights.append(r)
            else:
                lights.append(n)



    if state == 8:
        for i in range(50):
            if i == 2 or i == 5:
                lights.append(g)
            elif i == 29 or i == 8 or i == 13 or i == 24 or i == 21 or i == 16:
                lights.append(r)
            else:
                lights.append(n)

    if state == 9:
        for i in range(50):
            if i == 1 or i == 4:
                lights.append(y)
            elif i == 29 or i == 8 or i == 13 or i == 24 or i == 21 or i == 16:
                lights.append(r)
            else:
                lights.append(n)


    if state == 10:
        for i in range(50):
            if i == 10 or i ==11:
                lights.append(g)
            elif i == 29 or i == 16 or i == 21 or i == 24 or i == 21 or i == 16:
                lights.append(r)
            else:
                lights.append(n)

    if state == 11:
        for i in range(50):
            if i == 9 or i ==12:
                lights.append(y)
            elif i == 29 or i == 16 or i == 21 or i == 24 or i == 21 or i == 16:
                lights.append(r)
            else:
                lights.append(n)


    if state == 12:
        for i in range(50):
            if i == 19 or i == 18:
                lights.append(g)
            elif i == 29 or i == 8 or i == 13 or i == 24 or i == 0 or i == 3:
                lights.append(r)
            else:
                lights.append(n)

    if state == 13:
        for i in range(50):
            if i == 20 or i == 17:
                lights.append(y)
            elif i == 29 or i == 8 or i == 13 or i == 24 or i == 0 or i == 3:
                lights.append(r)
            else:
                lights.append(n)



    if state == 14:
        for i in range(50):
            if i == 26 or i == 27:
                lights.append(g)
            elif i == 16 or i == 8 or i == 13 or i == 21 or i == 0 or i == 3:
                lights.append(r)
            else:
                lights.append(n)

    if state == 15:
        for i in range(50):
            if i == 25 or i == 28:
                lights.append(y)
            elif i == 16 or i == 8 or i == 13 or i == 21 or i == 0 or i == 3:
                lights.append(r)
            else:
                lights.append(n)

    return lights

def show_names(color):
    lights = []
    vals = [61,62,63,65,66,67,116,120,152,148,202,206,239,238,237,234,
            75,77,80,81,83,84,85,97,99,101,103,105,107,161,163,165,167,169,170,171,183,185,187,189,191,193,248,252,253,255,257
            ,51,52,53,129,131,137,138,139,217,223, 55,127,141,213,227, 58,124,125,
            290,292,294,297,299,302,309,311,312,314,316,317,319,321,376,379,380,381,382,384,385,386,387,
            395,396,398,400,401,403,406,462,465,468,470,473,
            268,270,271,272,274,275,278,279,281,330,333,335,337,339,341,343,353,355,356,357,359,361,363,364,366,
            416,419,421,423,425,427,429,437,438,439,441,443,445,446,449,450,452,453]
    for i in range(511):
        if i in vals:
            lights.append(color)
        else:
            lights.append((0,0,0))

    return lights
