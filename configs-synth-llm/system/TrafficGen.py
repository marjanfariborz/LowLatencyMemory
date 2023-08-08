def createLinearTraffic(tgen, tgen_options):
    yield tgen.createLinear(tgen_options.duration,
                            tgen_options.min_addr,
                            tgen_options.max_addr,
                            tgen_options.block_size,
                            tgen_options.min_period,
                            tgen_options.max_period,
                            tgen_options.rd_perc, 0)
    yield tgen.createExit(0)

def createRandomTraffic(tgen, tgen_options):
    yield tgen.createRandom(tgen_options.duration,
                            tgen_options.min_addr,
                            tgen_options.max_addr,
                            tgen_options.block_size,
                            tgen_options.min_period,
                            tgen_options.max_period,
                            tgen_options.rd_perc, 0)
    yield tgen.createExit(0)

def createStridedTraffic(tgen, tgen_options):
    yield tgen.createStrided(tgen_options.duration,
                            tgen_options.min_addr,
                            tgen_options.max_addr,
                            tgen_options.block_size,
                            tgen_options.block_size * (tgen_options.num_tgens + 1),
                            # tgen_options.block_size * (tgen_options.num_tgens),
                            tgen_options.index,
                            tgen_options.min_period,
                            tgen_options.max_period,
                            tgen_options.rd_perc, 0)
    yield tgen.createExit(0)

def createTraceTraffic(tgen, tgen_options):
    file_name = 'configs-synth-llm/mem_traces/cc/{}/encode/chnl_{}.trc'.format(tgen_options.memory, tgen_options.index)
    yield tgen.createTrace(duration = tgen_options.duration,
                            trace_file = file_name)
    yield tgen.createExit(0)