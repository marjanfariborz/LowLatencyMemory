from __future__ import print_function
from __future__ import absolute_import

import m5
from m5.objects import *

from math import log as log
from random import randint as randint

class TestBenchSystem(System):

    def __init__(self, num_cores, mem_type, num_chnls):
        super(TestBenchSystem, self).__init__()
        if mem_type == 'LLM':
            self._mem_type = LLM
            self._bpc = 64
            self._policy = 'close'
        elif mem_type == 'HBM':
            self._mem_type = HBM_1000_4H_1x128
            self._bpc = 1
            self._policy = 'open_adaptive'
        elif mem_type == 'FGDRAM':
            self._mem_type = FGDRAM
            self._bpc = 32
            self._policy = 'open_adaptive'
        else:
            fatal('Memory type not supported.')

        self._num_cores = num_cores
        self._num_chnls = num_chnls

        self._mem_size = str(256 * self._num_chnls) + 'MB'
        self._addr_range = AddrRange(self._mem_size)

        self.clk_domain = SrcClockDomain()
        self.clk_domain.clock = '4GHz'
        self.clk_domain.voltage_domain = VoltageDomain()
        self.cache_line_size = 64

        self.mmap_using_noreserve = True
        self.mem_mode = 'timing'
        self.mem_ranges = [self._addr_range]

        self.tgens = [PyTrafficGen() for i in range(self._num_cores)]
        self.createMemoryCtrl()

        self.connectComponents()

    def createMemoryCtrl(self):
        mem_ctrls = []
        addr_range = self.mem_ranges[0]
        cls = self._mem_type

        intlv_size = self.cache_line_size
        intlv_low_bit = int(log(intlv_size, 2))
        intlv_bits = intlv_bits = int(log(self._num_chnls * self._bpc, 2))

        for chnl in range(self._num_chnls * self._bpc):
            if self._mem_type == LLM:
                interface = cls()
                interface.range = AddrRange(addr_range.start,
                            size = addr_range.size(),
                            intlvHighBit = intlv_low_bit + intlv_bits - 1,
                            xorHighBit = 0,
                            intlvBits = intlv_bits,
                            intlvMatch = chnl)
                ctrl = MemCtrl()

                ctrl.dram = interface
                ctrl.dram.null = True
                ctrl.dram.read_buffer_size = 2
                ctrl.dram.write_buffer_size = 2

                ctrl.write_high_thresh_perc = 100
                ctrl.write_low_thresh_perc = 75
                ctrl.min_writes_per_switch = 1
                mem_ctrls.append(ctrl)

            else:
                interface = cls()
                interface.range = AddrRange(addr_range.start, size = addr_range.size(),
                            intlvHighBit = intlv_low_bit + intlv_bits - 1,
                            xorHighBit = 0,
                            intlvBits = intlv_bits,
                            intlvMatch = chnl)
                ctrl = MemCtrl()
                ctrl.dram = interface
                ctrl.dram.null = True

                mem_ctrls.append(ctrl)

        self.mem_ctrls = mem_ctrls

    def createMemoryCtrl(self):
        mem_ctrls = []
        addr_range = self.mem_ranges[0]
        cls = self._mem_type

        intlv_size = self.cache_line_size
        intlv_low_bit = int(log(intlv_size, 2))
        intlv_bits = intlv_bits = int(log(self._num_chnls * self._bpc, 2))

        for chnl in range(self._num_chnls * self._bpc):
            if self._mem_type != HBM_1000_4H_1x128:
                interface = cls()
                interface.page_policy = self._policy
                interface.range = AddrRange(addr_range.start,
                            size = addr_range.size(),
                            intlvHighBit = intlv_low_bit + intlv_bits - 1,
                            xorHighBit = 0,
                            intlvBits = intlv_bits,
                            intlvMatch = chnl)
                ctrl = MemCtrl()

                ctrl.dram = interface
                ctrl.dram.null = True
                ctrl.dram.read_buffer_size = 2
                ctrl.dram.write_buffer_size = 2

                ctrl.write_high_thresh_perc = 100
                ctrl.write_low_thresh_perc = 75
                ctrl.min_writes_per_switch = 1
                mem_ctrls.append(ctrl)

            else:
                interface = cls()
                interface.page_policy = self._policy
                interface.range = AddrRange(addr_range.start, size = addr_range.size(),
                            intlvHighBit = intlv_low_bit + intlv_bits - 1,
                            xorHighBit = 0,
                            intlvBits = intlv_bits,
                            intlvMatch = chnl)
                ctrl = MemCtrl()
                ctrl.dram = interface
                ctrl.dram.null = True

                mem_ctrls.append(ctrl)

        self.mem_ctrls = mem_ctrls

    def connectComponents(self):
        if self._mem_type != HBM_1000_4H_1x128:
            self.membuses = [SystemXBar(
                            width = 64,
                            max_routing_table_size = 1073741824,
                            snoop_response_latency = 1,
                            frontend_latency = 1,
                            forward_latency = 0,
                            response_latency = 1)
                            for i in range(self._num_cores)]
            self.scheds = [MemScheduler(read_buffer_size = 1,
                                        resp_buffer_size = 0)
                                        for i in range(self._num_chnls)]

            for i, tgen in enumerate(self.tgens):
                tgen.port = self.membuses[i].cpu_side_ports

            for membus in self.membuses:
                for sched in self.scheds:
                    sched.cpu_side = membus.mem_side_ports

            for i, mem_ctrl in enumerate(self.mem_ctrls):
                self.scheds[i % self._num_chnls].mem_side = mem_ctrl.port

            self.system_port = self.membuses[0].cpu_side_ports

        else :
            self.membuses = SystemXBar(width = 64,
                            max_routing_table_size = 16777216)

            for tgen in self.tgens:
                tgen.port = self.membuses.cpu_side_ports
            for mem_ctrl in self.mem_ctrls:
                self.membuses.mem_side_ports = mem_ctrl.port
            self.system_port = self.membuses.cpu_side_ports
