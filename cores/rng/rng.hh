#ifndef __IP_CORES_RNG_HH__
#define __IP_CORES_RNG_HH__

#include <random>

#include "base/compiler.hh"
#include "dev/io_device.hh"
#include "params/RandomNumberGenerator.hh"

namespace gem5 {

class RandomNumberGenerator : public BasicPioDevice {
protected:
    static const int READ_ADDR = 0;

    int rng_fd;

public:
    using Params = RandomNumberGeneratorParams;
    RandomNumberGenerator(const Params &p);

    Tick read(PacketPtr pkt) override;
    Tick write(PacketPtr pkt) override;
};

}
#endif
