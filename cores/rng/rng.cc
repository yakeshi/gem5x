#include "cores/rng/rng.hh"

#include <fcntl.h>
#include <unistd.h>

#include "base/trace.hh"
#include "debug/IPCoreRng.hh"

namespace gem5 {

RandomNumberGenerator::RandomNumberGenerator(const Params &p)
    : BasicPioDevice(p, p.pio_size) {
    rng_fd = open(p.entropy_source.c_str(), O_RDONLY);
    if (rng_fd < 0) {
        DPRINTF(IPCoreRng, "error when open entropy source: %s\n",
                p.entropy_source.c_str());
    }
}

Tick RandomNumberGenerator::read(PacketPtr pkt) {
    Addr daddr = pkt->getAddr() - pioAddr;

    DPRINTF(IPCoreRng, "Read register %#x\n", daddr);

    if (rng_fd >= 0 && daddr == READ_ADDR) {
        ssize_t size = ::read(rng_fd, pkt->getPtr<void>(), pkt->getSize());
        if (size < 0) {
            panic("Read entropy file failed");
        }
    }

    pkt->makeAtomicResponse();
    return pioDelay;
}

Tick RandomNumberGenerator::write(PacketPtr pkt) {
    pkt->makeAtomicResponse();

    DPRINTF(IPCoreRng, "write - va=%#x size=%d \n",
                pkt->getAddr(), pkt->getSize());

    return pioDelay;
}

}