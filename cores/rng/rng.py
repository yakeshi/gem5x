from m5.params import *
from m5.objects.Device import BasicPioDevice

class RandomNumberGenerator(BasicPioDevice):
    type = 'RandomNumberGenerator'
    cxx_header = 'cores/rng/rng.hh'
    cxx_class = 'gem5::RandomNumberGenerator'

    entropy_source = Param.String("/dev/random", "The source of entropy")
    pio_size = Param.Addr(0x4, "Size of address range")
