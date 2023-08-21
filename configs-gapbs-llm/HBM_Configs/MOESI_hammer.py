#Copyright (c) 2020 The Regents of the University of California.
#All Rights Reserved
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


""" This file creates a set of Ruby caches for the MESI TWO Level protocol
This protocol models two level cache hierarchy. The L1 cache is split into
instruction and data cache.
This system support the memory size of up to 3GB.
"""




import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

class MOESIHammerCache(RubySystem):

    def __init__(self):
        if buildEnv['PROTOCOL'] != 'MOESI_hammer':
            fatal("This system assumes MOESI_hammer!")

        super(MOESIHammerCache, self).__init__()


    def setup(self, system, gens, mem_ctrls):
        """Set up the Ruby cache subsystem. Note: This can't be done in the
           constructor because many of these items require a pointer to the
           ruby system (self). This causes infinite recursion in initialize()
           if we do this in the __init__.
        """
        # Ruby's global network.
        self.network = garnetNetwork(self)
        self._numL2Caches = len(gens)

        self.number_of_virtual_networks = 6
        self.network.number_of_virtual_networks = 6

        self._mem_type = system._mem_type

        pf_size = MemorySize('1 MB')
        pf_size.value = pf_size.value * 2 * self._numL2Caches / len(mem_ctrls)
        dir_bits = int(math.log(len(mem_ctrls), 2))
        pf_bits = int(math.log(pf_size.value, 2))
        block_size_bits = int(math.log(system.cache_line_size, 2))
        if dir_bits > 0:
            pf_start_bit = dir_bits + block_size_bits - 1
        else:
            pf_start_bit = block_size_bits

        # Run each of the ruby memory controllers at a ratio of the frequency of
        # the ruby system
        # clk_divider value is a fix to pass regression.
        self.memctrl_clk_domain = DerivedClockDomain(
                                            clk_domain=self.clk_domain,
                                            clk_divider=3)

        self.monitor = [CommMonitor() for i in range(len(mem_ctrls))]
        # There is a single global list of all of the controllers to make it
        # easier to connect everything to the global network. This can be
        # customized depending on the topology/network requirements.
        # L1 caches are private to a core, hence there are one L1 cache per CPU core.
        # The number of L2 caches are dependent to the architecture.
        self.controllers = \
            [L1Cache(system, self, gen, self._numL2Caches) for gen in gens] + \
            [DirController(self, self.monitor[j], mem_ctrls[j], pf_size, pf_start_bit)
                            for j in range(len(mem_ctrls))]

        # Create one sequencer per CPU and dma controller.
        # Sequencers for other controllers can be here here.
        self.sequencers = [RubySequencer(version = i,
                                # Grab dcache from ctrl
                                dcache = self.controllers[i].L1Dcache,
                                clk_domain = self.controllers[i].clk_domain,
                                # pio_request_port = iobus.cpu_side_ports,
                                # mem_request_port = iobus.cpu_side_ports,
                                # pio_response_port = iobus.mem_side_ports
                                ) for i in range(len(gens))]

        for i,c in enumerate(self.controllers[:len(gens)]):
            c.sequencer = self.sequencers[i]


        self.num_of_sequencers = len(self.sequencers)

        # Create the network and connect the controllers.
        # NOTE: This is quite different if using Garnet!
        self.network.connectControllers(self.controllers, len(gens), len(mem_ctrls))

        # Set up a proxy port for the system_port. Used for load binaries and
        # other functional-only things.
        self.sys_port_proxy = RubyPortProxy()
        system.system_port = self.sys_port_proxy.in_ports
        # self.sys_port_proxy.pio_request_port = iobus.cpu_side_ports

        # Connect the cpu's cache, interrupt, and TLB ports to Ruby
        for i, gen in enumerate(gens):
            gen.port = self.sequencers[i].in_ports

class L1Cache(L1Cache_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
        return cls._version - 1

    def __init__(self, system, ruby_system, gen, num_l2Caches):
        """Creating L1 cache controller. Consist of both instruction
           and data cache. The size of data cache is 512KB and
           8-way set associative. The instruction cache is 32KB,
           2-way set associative.
        """
        super(L1Cache, self).__init__()

        self.version = self.versionCount()
        block_size_bits = int(math.log(system.cache_line_size, 2))
        l1i_size = '32kB'
        l1i_assoc = '2'
        l1d_size = '32kB'
        l1d_assoc = '8'
        # This is the cache memory object that stores the cache data and tags
        self.L1Icache = RubyCache(size = l1i_size,
                                assoc = l1i_assoc,
                                start_index_bit = block_size_bits ,
                                is_icache = True)
        self.L1Dcache = RubyCache(size = l1d_size,
                            assoc = l1d_assoc,
                            start_index_bit = block_size_bits,
                            is_icache = False)
        self.L2cache = RubyCache(size ='1 MB',
                           assoc =8,
                           start_index_bit = self.getBlockSizeBitsL2(system, num_l2Caches))
        self.clk_domain = gen.clk_domain
        self.prefetcher = RubyPrefetcher()
        self.send_evictions = True
        self.transitions_per_cycle = 4
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

    def getBlockSizeBitsL2(self, system, num_l2caches):
        l2_bits = int(math.log(num_l2caches, 2))
        bits = int(math.log(system.cache_line_size, 2)) + l2_bits
        return bits

    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("Cache line size not a power of 2!")
        return bits

    def connectQueues(self, ruby_system):
        """Connect all of the queues for this controller.
        """
        self.mandatoryQueue = MessageBuffer()
        self.forwardToCache = MessageBuffer()
        self.forwardToCache.out_port = ruby_system.network.in_port
        self.responseToCache = MessageBuffer()
        self.responseToCache.out_port = ruby_system.network.in_port

        self.triggerQueue = MessageBuffer()
        self.requestFromCache = MessageBuffer()
        self.requestFromCache.out_port = ruby_system.network.in_port
        self.responseFromCache = MessageBuffer()
        self.responseFromCache.out_port = ruby_system.network.in_port
        self.unblockFromCache = MessageBuffer()
        self.unblockFromCache.out_port = ruby_system.network.in_port




class DirController(Directory_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
        return cls._version - 1

    def __init__(self, ruby_system, monitor, mem_ctrl, pf_size, pf_start_bit):
        """ranges are the memory ranges assigned to this controller.
        """
        # if len(mem_ctrls) > 1:
        #     panic("This cache system can only be connected to one mem ctrl")
        super(DirController, self).__init__()
        self.ProbeFilter = RubyCache(size = pf_size, assoc = 4,
                         start_index_bit = pf_start_bit)
        self.version = self.versionCount()
        if ruby_system._mem_type == "SIMPLE":
            self.addr_ranges = mem_ctrl.range
        else:
            self.addr_ranges = mem_ctrl.dram.range
        self.ruby_system = ruby_system
        self.directory = RubyDirectoryMemory()
        self.memory = monitor.cpu_side_port
        monitor.mem_side_port = mem_ctrl.port
        pf = self.ProbeFilter
        self.connectQueues(ruby_system, pf)
    def connectQueues(self, ruby_system, pf):

        self.probeFilter = pf
        self.probe_filter_enabled = True
        self.full_bit_dir_enabled = True



        self.forwardFromDir = MessageBuffer()
        self.forwardFromDir.in_port = ruby_system.network.out_port
        self.responseFromDir = MessageBuffer()
        self.responseFromDir.out_port = ruby_system.network.in_port
        self.dmaResponseFromDir = MessageBuffer(ordered = True)
        self.dmaResponseFromDir.out_port = ruby_system.network.in_port

        self.triggerQueue = MessageBuffer(ordered = True)

        self.unblockToDir = MessageBuffer()
        self.unblockToDir.in_port = ruby_system.network.out_port
        self.responseToDir = MessageBuffer()
        self.responseToDir.in_port = ruby_system.network.out_port
        self.requestToDir = MessageBuffer()
        self.requestToDir.in_port = ruby_system.network.out_port
        self.dmaRequestToDir = MessageBuffer(ordered = True)
        self.dmaRequestToDir.in_port = ruby_system.network.out_port
        self.requestToMemory = MessageBuffer()
        self.responseFromMemory = MessageBuffer()

class DMAController(DMA_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
        return cls._version - 1

    def __init__(self, ruby_system):
        super(DMAController, self).__init__()
        self.version = self.versionCount()
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

    def connectQueues(self, ruby_system):
        self.mandatoryQueue = MessageBuffer()
        self.responseFromDir = MessageBuffer(ordered = True)
        self.responseFromDir.in_port = ruby_system.network.out_port
        self.requestToDir = MessageBuffer()
        self.requestToDir.out_port = ruby_system.network.in_port


class garnetNetwork(GarnetNetwork):
    """A simple point-to-point network. This doesn't not use garnet.
    """

    def __init__(self, ruby_system):
        super(garnetNetwork, self).__init__()
        self.vcs_per_vnet = 4
        self.ni_flit_size = 64
        self.routing_algorithm = 0
        self.garnet_deadlock_threshold = 1000000
        self.ruby_system = ruby_system

    def connectControllers(self, controllers, num_cpus, num_scheduler):
        """Connect all of the controllers to routers and connec the routers
           together in a point-to-point network.
        """
        # Create one router/switch per controller in the system
        self.routers = [GarnetRouter(router_id = i) for i in range(num_cpus)] + \
                    [GarnetRouter(router_id = i + num_cpus, latency = 20) for i in range(num_scheduler)]

        self.ext_links = [GarnetExtLink(link_id=i, ext_node=c,
                                        int_node=self.routers[i],
                                        latency = 8)
                          for i, c in enumerate(controllers)]

        self.netifs = [GarnetNetworkInterface(id=i) \
                    for (i,n) in enumerate(self.ext_links)]
        # Make an "internal" link (internal to the network) between every pair
        # of routers.
        link_count = 0
        self.int_links = []
        for i, ri in enumerate(self.routers):
            for j, rj in enumerate(self.routers):
                if ri == rj: continue # Don't connect a router to itself!
                link_count += 1
                self.int_links.append(GarnetIntLink(link_id = link_count,
                                                    src_node = ri,
                                                    dst_node = rj,
                                                    latency = 8,
                                                    weight  = 1))
                                                    # 4