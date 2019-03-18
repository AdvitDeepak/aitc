import os, sys, subprocess, traci

def osm_to_sumo():
    osm_folder = "raw_osm/map.osm"
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    osm_file_path = os.path.join(parent_dir, osm_folder)

    print("First:")
    subprocess.call("netconvert --osm-files %s --output.street-names -o %s" % (osm_file_path, "new_sumo/map.net.xml"))
    print("Second:")
    subprocess.call("netconvert --osm-files %s --tls.guess 1 -L 2 --no-warnings --output-file %s" % (osm_file_path, "new_sumo/map.net.xml"))
    print("Third:")
    subprocess.call("polyconvert --xml-validation \"auto\" --net-file %s --osm-files %s --type-file %s -o %s" %
                   ("new_sumo/map.net.xml", osm_file_path, "typemap.xml", "new_sumo/map.poly.xml"))
    print("Fourth:")
    subprocess.call("python randomTrips.py -n %s -r %s e 100 -l" % ("new_sumo/map.net.xml", "new_sumo/map.rou.xml"))
    # Converts the .osm file into: .net, .poly, .rou, .rou.alt

def import_sumocfg():
    raw_txt_path = os.path.join('..', "scripts/sumocfg.txt")
    r = open(raw_txt_path, "r+")

    f = open("new_sumo/map.sumocfg", "w+")
    g = open("new_sumo/map.sumo.cfg", "w+")

    for line in r.read():
        f.write(line), g.write(line)

    f.close(), r.close(), g.close()
    # Creates both a .sumocfg and a .sumo.cfg file

def add_detectors():
    det_file_path = "new_sumo/map.det.xml"
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    sumoBinary = "sumo"
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    sumoConfig = os.path.join(parent_dir, "new_sumo/map.sumo.cfg")
    sumoCmd = [sumoBinary, "-c", sumoConfig, "--start"]
    traci.start(sumoCmd)

    lanes_done = []
    with open(det_file_path, 'w') as f:
        f.write("<additional>\n")
        for trafficlight in traci.trafficlights.getIDList():
            # For each traffic light
            for lane in traci.trafficlights.getControlledLanes(trafficlight):
                # For each lane controlled by that traffic light
                if traci.lane.getLength(lane) > 10.0 and lane not in lanes_done:
                    # Make a detector if we haven't already
                    f.write("\t<inductionLoop id='{}' lane='{}' pos='{}' freq='100' "
                            "file='{}'/>\n".format(lane + "loop", lane, -5, os.path.join('..', "resultDetectors.xml")))
                    lanes_done.append(str(lane))

        f.write("</additional>")
    f.close()
    # Creates the .det file


def integrate_det_file():
    raw_txt_path = os.path.join('..', "scripts/sumocfg.txt")
    r = open(raw_txt_path, "r+")
    d = r.readlines()
    r.close()
    os.remove(raw_txt_path)

    new_r = open(raw_txt_path, "w+")
    for line in d:
        if "map.poly.xml" not in str(line):
            new_r.write(line)
        else:
            new_r.write("        <additional-files value=\"map.poly.xml map.det.xml\"/>\n")

    new_r.close()
    import_sumocfg()

    old_r = open(raw_txt_path, "w+")
    for line in d:
        old_r.write(line)
    old_r.close()
    # Adds the .det file to .sumocfg and .sumo.cfg files

def view():
    f = int(input("Would you like to see your amazing creation!? (1 for yes, 0 for no): "))
    if int(f) == 0:
        print("Yay, we did it!")
        exit()
    else:
        cfg_name = "new_sumo/map.sumo.cfg"
        subprocess.call("sumo-gui " + cfg_name)
    # Opens the gui for the .sumo.cfg

if __name__ == "__main__":
    osm_to_sumo()
    import_sumocfg()
    add_detectors()
    integrate_det_file()
    view()
