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

class HBMRubySynthSystem(System):
    def __init__(self, num_gens, mem_type, num_chnls, channel_size):
        super(HBMRubySynthSystem, self).__init__()
        self._num_gens = num_gens
        self._num_channels = num_chnls
        self._channel_size = channel_size
        self._mem_type = mem_type
        # Set up the clock domain and the voltage domain
        self.clk_domain = SrcClockDomain()
        self.clk_domain.clock = '4GHz'
        self.clk_domain.voltage_domain = VoltageDomain()
        self._channel_size = channel_size
        self._mem_size = str(self._channel_size * self._num_channels) + 'MB'
        self.mem_ranges = [AddrRange(self._mem_size)]

        self.tgens = [PyTrafficGen(progress_check = "1s") for i in range(self._num_gens)]
        self.createMemoryControllers()

        # Create the cache hierarchy for the system.
        self.caches = MOESIHammerCache()

        self.caches.setup(self, self.tgens, self.mem_ctrls)

    def createMemoryControllers(self):
        mem_ctrls = []
        num_int = self._num_channels
        addr_range = self.mem_ranges[0]
        intlv_low_bit = 6
        intlv_bits = int(log(num_int, 2))

        for i in range(num_int):
            if self._mem_type == "SIMPLE":
                ctrl = SimpleMemory(latency = "40ns", bandwidth = "1024GiB/s")
                ctrl.range = AddrRange(addr_range.start, size = addr_range.size(),
                            intlvHighBit = intlv_low_bit + intlv_bits - 1,
                            xorHighBit = 0,
                            intlvBits = intlv_bits,
                            intlvMatch = i)
            else:
                if self._mem_type == 'HBM':
                    interface = HBM_1000_4H_1x64()
                    interface.device_size = str(self._channel_size) + 'MB'
                elif self._mem_type == 'HBMSALP':
                    interface = HBM_1000_4H_1x64()
                    interface.device_size = str(self._channel_size) + 'MB'
                    interface.subarray_per_bank = 8
                    interface.tWA = '3ns'
                    interface.salp_enable = True
                elif self._mem_type == 'DDR4':
                    interface = DDR4_2400_8x8()
                interface.range = AddrRange(addr_range.start, size = addr_range.size(),
                            intlvHighBit = intlv_low_bit + intlv_bits - 1,
                            xorHighBit = 0,
                            intlvBits = intlv_bits,
                            intlvMatch = i)
                ctrl = MemCtrl()
                ctrl.dram = interface
                if self._mem_type == 'HBM' or self._mem_type == 'HBMSALP':
                    ctrl.dram.page_policy = 'open_adaptive'
            mem_ctrls.append(ctrl)
        self.mem_ctrls = mem_ctrls
