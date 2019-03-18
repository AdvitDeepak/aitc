import random, traci
import numpy as np
import sys

def generate_routefile(sim_steps):
    # Demand per second from different directions (calculated from SJDoT data)

    random.seed(0)

    pNL = 0.07704
    pNT = 0.26444
    pNR = 0.08606
    pSL = 0.04547
    pST = 0.08320
    pSR = 0.04171
    pEL = 0.01089
    pET = 0.09019
    pER = 0.03758
    pWL = 0.04021
    pWT = 0.20782
    pWR = 0.01578

    # All directions referring to which way the vehicle is bound
    # Ex. NT = Car is on Meridian heading up

    with open("./data/map.rou.xml", "w") as routes:
        print("""<routes>
        <vType id="slow" accel="3" decel="4" sigma="0.5" length="5.5" width="2.3" minGap="2.5" maxSpeed="15" guiShape="delivery" color="1,0.84314,0.14902" />
        <vType id="fast" accel="3.5" decel="4.572" sigma="0.5" length="4.2" width="1.9" minGap="2.5" maxSpeed="16.2" guiShape="passenger" color="1,0.84314,0.14902" />
        <vType id="norm" accel="4" decel="5.15" sigma="0.5" length="4.8" width="2.1" minGap="2.5" maxSpeed="15.6" guiShape="passenger/van" color="1,0.84314,0.14902" />

        <route id="NL" edges="393645138 393645129 393625777" />
        <route id="NT" edges="393645138 393645129 393645126 393645137" />
        <route id="NR" edges="393645138 393645129 -393627613" />
        <route id="SL" edges="-393645137 -393645126 -393627613" />
        <route id="ST" edges="-393645137 -393645126 -393645129 -393645138" />
        <route id="SR" edges="-393645137 -393645126 393625777" />
        <route id="ER" edges="-393625777 -393645129 -393645138" />
        <route id="ET" edges="-393625777 -393627613" />
        <route id="EL" edges="-393625777 393645126 393645137 " />
        <route id="WL" edges="393627613 -393645129 -393645138" />
        <route id="WT" edges="393627613 393625777" />
		    <route id="WR" edges="393627613 393645126 393645137" />""", file=routes)

        lastVeh = 0
        vehNr = 0

        # Where i refers to the total timeSteps in the simulation
        # if statements in order from least to greatest probability per each direction
        # makes sure that only one car can enter from every side every time step

        for i in range(sim_steps):

            if random.uniform(0, 1) < pNL:
                print('    <vehicle id="left_%i" type="%s" route="NL" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i

            if random.uniform(0, 1) < pNT:
                print('    <vehicle id="through_%i" type="%s" route="NT" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i
            if random.uniform(0, 1) < pNR:
                print('    <vehicle id="right_%i" type="%s" route="NR" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i


            if random.uniform(0, 1) < pSL:
                print('    <vehicle id="left_%i" type="%s" route="SL" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i
            if random.uniform(0, 1) < pST:
                print('    <vehicle id="through_%i" type="%s" route="ST" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i
            if random.uniform(0, 1) < pSR:
                print('    <vehicle id="right_%i" type="%s" route="SR" depart="%i"/>' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i


            if random.uniform(0, 1) < pEL:
                print('    <vehicle id="left_%i" type="%s" route="EL" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i
            if random.uniform(0, 1) < pET:
                print('    <vehicle id="through_%i" type="%s" route="ET" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i
            if random.uniform(0, 1) < pER:
                print('    <vehicle id="right_%i" type="%s" route="ER" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i


            if random.uniform(0, 1) < pWL:
                print('    <vehicle id="left_%i" type="%s" route="WL" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i
            if random.uniform(0, 1) < pWT:
                print('    <vehicle id="through_%i" type="%s" route="WT" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i
            if random.uniform(0, 1) < pWR:
                print('    <vehicle id="right_%i" type="%s" route="WR" depart="%i" />' % (
                    vehNr, chooseVehicleType(i), i), file=routes)
                vehNr += 1
                lastVeh = i
        print("</routes>", file=routes)

    # Creating the environment + exporting the vehicle data

def chooseVehicleType(i):
    if i%5 == 0:
        vType = "norm"
    elif i%5 == 1:
        vType = "slow"
    else:
        vType = "fast"

    return(str(vType))

def main():
        num_sim_steps = 300
        if(len(sys.argv) == 2):
            num_sim_steps = int(sys.argv[1])

        generate_routefile(num_sim_steps)

if __name__ == '__main__':
    main()
