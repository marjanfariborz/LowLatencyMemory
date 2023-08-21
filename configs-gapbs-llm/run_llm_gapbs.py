import m5
from m5.objects import *
from m5.util.convert import *
from m5.util import addToPath

from TrafficGen import createTraceTraffic

import argparse


parser = argparse.ArgumentParser()

parser.add_argument(
    "trace_dir",
    type=str,
    help="path to directory including trace files to use.",
)

parser.add_argument(
    "num_cores",
    type=int,
    default=1,
    help="number of traffic generators to create \
                        synthetic traffic",
)

parser.add_argument("mem_type", type=str, help="type of memory to test")

parser.add_argument(
    "num_chnls",
    type=int,
    default=1,
    help="number of channels in the memory system, \
                    could only be a power of 2, e.g. 1, 2, 4, 8, ..",
)

parser.add_argument(
    "chnl_cap",
    type=int,
    default=256,
    help="number of channels in the memory system, \
                    could only be a power of 2, e.g. 1, 2, 4, 8, ..",
)

args = parser.parse_args()

if args.mem_type in ["FGDRAM", "LLM"]:
    addToPath("LLM_Configs")
    from llm_ruby_system import LLMRubySynthSystem

    system = LLMRubySynthSystem(
        args.num_cores, args.mem_type, args.num_chnls, args.chnl_cap
    )
else:
    addToPath("HBM_Configs")
    from hbm_ruby_system import HBMRubySynthSystem

    system = HBMRubySynthSystem(
        args.num_cores, args.mem_type, args.num_chnls, args.chnl_cap
    )

# args.duration = int(toLatency(args.duration) * 1e12)

mem_size = args.chnl_cap * 1048576 * args.num_chnls
mem_chunk = int(mem_size / args.num_cores)


root = Root(full_system=False, system=system)


m5.instantiate()

for i, tgen in enumerate(system.tgens):
    tgen.progress_check = "1s"
    args.index = i
    tgen.start(createTraceTraffic(tgen, i, args.trace_dir))

done = 0
while done < args.num_cores:
    exit_event = m5.simulate()
    print("A trace finished: ", m5.curTick(), exit_event.getCause())
    done += 1
print("Done running traces!")
exit()
