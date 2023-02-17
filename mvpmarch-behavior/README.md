# mvpmarch

AUMC simualtion with NODES controller and Behavior
https://github.nrel.gov/AUMC/mvpmarch/tree/behavior

## To run the simulation 
1. Activate the conda environment. 

2. agentbehavior/agent24.json needs to be edited to point to the correctn location of the opendss feeder on your system. 
The logdir needs to point to a path on your system to store the voltage and power logs generated from the simulation. 

```     "model_parameters": {
        "masterfile": "<full path on your system>/feederdata/p1uhs0_1247--p1udt104/Master_XZ.dss"
    },
    "logdir": "<full path to log directory>",
   ```

3. Please install helics in order to run the parallel simualtions: 

``` pip install helics ```



4. Launch the helics broker in a terminal:

``` helics_broker -t zmq -f 14 --local_port=25002 --log_level=debug ```



5. In a seperate terminal launch the agents:

``` mpirun --oversubscribe -n 14 python launch.py   ```


## Notes

1. mesamodel.py containes the simple behavior model. 
2. nodecocntrollerfolder contains modules for the nodes RTOPF controller. 
3. aumcfunctions.py has the helics federates that take care of communication. 
4. fap.py defines and instantiates the simualtion federateafgent. 
5. the configuration of the agents can be found in agentbehavior folder. 





