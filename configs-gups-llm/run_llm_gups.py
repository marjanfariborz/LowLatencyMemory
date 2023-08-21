import m5
from m5.objects import *
from m5.util.convert import *
from m5.util import addToPath

addToPath("system")


from GUPSBenchSystem import GUPSBenchSystem

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("num_cores", type=int, help="number of gups gens")
parser.add_argument("mem_type", type=str, help="type of memory to test")
parser.add_argument(
    "num_chnls",
    type=int,
    default=1,
    help="number of channels in the memory system, \
                    could only be a power of 2, e.g. 1, 2, 4, 8, ..",
)
parser.add_argument(
    "num_updates",
    type=int,
    default=100000,
    help="number of channels in the memory system, \
                    could only be a power of 2, e.g. 1, 2, 4, 8, ..",
)

args = parser.parse_args()

num_cores = args.num_cores
mem_type = args.mem_type
num_chnls = args.num_chnls
num_updates = args.num_updates

system = GUPSBenchSystem(num_cores, mem_type, num_chnls, num_updates)

root = Root(full_system=False, system=system)

m5.instantiate()

done = 0

while done < num_cores:
    exit_event = m5.simulate()
    if "finished updating the memory" in exit_event.getCause():
        print(exit_event.getCause())
        done = done + 1
        print("done: ", done)

print("Finished Simulation")
