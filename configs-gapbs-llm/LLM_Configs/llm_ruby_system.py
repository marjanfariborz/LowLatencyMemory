# -*- coding: utf-8 -*-
# Copyright (c) 2016 Jason Lowe-Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Jason Lowe-Power

import m5

from math import log
from m5.objects import *
from MOESI_hammer import MOESIHammerCache

class LLMRubySynthSystem(System):

    def __init__(self, num_gens, mem_type, num_chnls, channel_size):
        super(LLMRubySynthSystem, self).__init__()
        self._num_gens = num_gens
        self._num_channels = num_chnls
        self._channel_size = channel_size
        self._mem_type = mem_type
        if (self._mem_type == 'LLM'):
            self._bpc = 64
        if (self._mem_type == 'FGDRAM'):
            self._bpc = 32
        if (self._mem_type == 'FGDRAM+'):
            pass
        if (self._mem_type == 'FGDRAM++'):
            pass
        # Set up the clock domain and the voltage domain
        self.clk_domain = SrcClockDomain()
        self.clk_domain.clock = '4GHz'
        self.clk_domain.voltage_domain = VoltageDomain()

        self._mem_size = str(self._channel_size * self._num_channels) + 'MB'
        self.mem_ranges = [AddrRange(self._mem_size)]

        self.tgens = [PyTrafficGen(progress_check = "1s") for i in range(self._num_gens)]
        self.createMemoryControllers()

        # Create the cache hierarchy for the system
        self.caches = MOESIHammerCache()

        self.caches.setup(self, self.tgens, self.mem_scheds)

    def createMemoryControllers(self):
        mem_ctrls = []
        num_int = self._num_channels * self._bpc
        bpc = self._bpc
        addr_range = self.mem_ranges[0]
        intlv_low_bit = 6
        intlv_bits = int(log(num_int, 2))
        if (self._mem_type == 'LLM'):
            for i in range(num_int):
                interface = LLM()
                interface.range = AddrRange(addr_range.start, size = addr_range.size(),
                            intlvHighBit = intlv_low_bit + intlv_bits - 1,
                            xorHighBit = 0,
                            intlvBits = intlv_bits,
                            intlvMatch = i)
                interface.subarray_per_bank = 8
                ctrl = MemCtrl()
                ctrl.dram = interface
                interface.device_size = str(int(self._channel_size / bpc)) + 'MB'
                ctrl.dram.read_buffer_size = 6
                ctrl.dram.write_buffer_size = 8
                ctrl.dram.page_policy = 'close'
                ctrl.write_high_thresh_perc = 100
                ctrl.write_low_thresh_perc = 90
                ctrl.min_writes_per_switch = 1
                mem_ctrls.append(ctrl)

        elif (self._mem_type == 'FGDRAM'):
            for i in range(num_int):
                interface = FGDRAM()
                interface.range = AddrRange(addr_range.start, size = addr_range.size(),
                            intlvHighBit = intlv_low_bit + intlv_bits - 1,
                            xorHighBit = 0,
                            intlvBits = intlv_bits,
                            intlvMatch = i)
                ctrl = MemCtrl()
                ctrl.dram = interface
                interface.device_size = str(int(self._channel_size / bpc)) + 'MB'
                ctrl.dram.page_policy = 'open_adaptive'
                mem_ctrls.append(ctrl)
        self.mem_ctrls = mem_ctrls

        scheds = [MemScheduler(read_buffer_size = 8,
                            write_buffer_size = 32,
                            resp_buffer_size = 0,
                            unified_queue = True,
                            service_write_threshold = 60)
                            for i in range(self._num_channels)]
        self.mem_scheds = scheds
        for sched in self.mem_scheds:
            sched._range = []

        addr_range = []
        for i, mem_ctrl in enumerate(self.mem_ctrls):
            self.mem_scheds[int(i % self._num_channels)].mem_side = mem_ctrl.port
            self.mem_scheds[int(i % self._num_channels)]._range.append(mem_ctrl.dram.range)
