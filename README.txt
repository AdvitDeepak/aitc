Packages to install: 
	Follow the instructions on the page below: 
		https://machinelearningmastery.com/setup-python-environment-machine-learning-deep-learning-anaconda/
	Download SUMO: 
		https://sumo.dlr.de/userdoc/Downloads.html
	Start Anaconda Prompt: 
		pip install git 
	If using blinkytape: 
		pip install BlinkyTape 
		Note that the util/led.py is calibrated to work for a specific light pattern which must be followed. 

Example usage: 
	python aitc.py -w t39K.h5 -r 10000 -s 20 -m dqn -d gui 
	python aitc.py -h (for help)

data: Folder containing data files that configure simulation of traci sumo
models: Neural Network models used by aitc
utils: Library of unitity scripts used by aitc
aitc.py: Main Artificiallly Intelligent Traffic Controller program
bm.rou.xml: A benchmark traffic pattern (route) file for SUMO   
README: this file
t39K.h5: A tensorflow neural network trained weights file for the dqn model 

State (21 input values):
8: # Halted in each direction (Left and Through for each side)
8: # in each direction (do not have to be halted, Left and Through for each side)
1: Current Phase
1: Elapsed Phase Time
1: Rate of cars passed for phase time
1: Change in # halted
1: Change in # passed
