from m5.util.convert import *
from m5.util import addToPath
# import m5.pystats.loader as loader
addToPath('system')
addToPath('../../gem5-new/configs')

from TestBenchSystem import *
from TrafficGen import *

import argparse
import math


parser = argparse.ArgumentParser()

parser.add_argument('mode', type = str,
                    help = 'type of traffic to be generated')

parser.add_argument('num_tgens', type = int, default = 1,
                    help = 'number of traffic generators to create \
                        synthetic traffic')

parser.add_argument('mem_type', type = str,
                    help = '''memory model to simulate''')

parser.add_argument('num_chnls', type = int, default = 1,
                    help = 'number of channels in the memory system, \
                    could only be a power of 2, e.g. 1, 2, 4, 8, ..')

parser.add_argument('chnl_cap', type = int, default = 256,
                    help = 'number of channels in the memory system, \
                    could only be a power of 2, e.g. 1, 2, 4, 8, ..')

parser.add_argument('duration', type = str,
                    help = '''real time duration to generate traffic
                    e.g. 1s, 1ms, 1us, 1ns''')

parser.add_argument('injection_rate', type = int,
                    help = '''The amount of traffic generated
                    by the traffic generator in GBps''')

parser.add_argument('rd_perc', type = int,
                    help = '''Percentage of read request,
                    rd_perc = 100 - write requests percentage''')

parser.add_argument('data_limit', type = int, default = 0)

options = parser.parse_args()

system = TestBenchSystem(options.num_tgens, options.mem_type, options.num_chnls, options.chnl_cap)

options.block_size = 64
options.duration = int(toLatency(options.duration) * 1e12)

mem_size = options.chnl_cap * 1048576 * options.num_chnls
mem_chunk = int(mem_size / options.num_tgens)
options.min_addr = 0
options.max_addr = toMemorySize(str(256 * options.num_chnls) + 'MB')

injection_period = int((1e12 * options.block_size) /
                    (options.injection_rate * 1073741824))

options.min_period = injection_period
options.max_period = injection_period
options.memory = options.mem_type.lower()

root = Root(full_system = False, system = system)


m5.instantiate()

if options.mode == 'LINEAR':
    for i, tgen in enumerate(system.tgens):
        options.min_addr = i * mem_chunk
        options.max_addr = (i + 1) * mem_chunk
        tgen.start(createLinearTraffic(tgen, options))
elif options.mode == 'STRIDED':
    for i, tgen in enumerate(system.tgens):
        options.index = i
        tgen.start(createStridedTraffic(tgen, options))
elif options.mode == 'RANDOM':
    for tgen in system.tgens:
        tgen.start(createRandomTraffic(tgen, options))
elif options.mode == 'TRACE':
    for i, tgen in enumerate(system.tgens):
        options.index = i
        tgen.start(createTraceTraffic(tgen, options))
else:
    print('Traffic type not supported!')

exit_event = m5.simulate()