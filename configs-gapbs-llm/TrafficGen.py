prime_finder = {
    0: 0,
    1: 8388672,
    2: 16777344,
    3: 33554560,
    4: 67109120,
    5: 134218176,
    6: 268436352,
    7: 536872768,
}


def createTraceTraffic(tgen, index, base_dir):
    index_rem = index % 8
    offset = prime_finder[int(index / 8)]
    file_name = f"{base_dir}/cpu_{index_rem}.trc"
    yield tgen.createTrace(
        duration=0, trace_file=file_name, addr_offset=offset
    )
    yield tgen.createExit(0)
