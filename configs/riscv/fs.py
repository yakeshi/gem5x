
import argparse
import os
import m5
import m5.util

m5.util.addToPath("../../gem5/configs")

from gem5.components.boards.riscv_board import RiscvBoard
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.cachehierarchies.classic.\
    private_l1_private_l2_cache_hierarchy import (
        PrivateL1PrivateL2CacheHierarchy,
    )
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.resources.resource import Resource, CustomResource
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent

from common import SysPaths

from m5.ext.pyfdt import pyfdt
from m5.util.fdthelper import (FdtState, Fdt)

# Run a check to ensure the right version of gem5 is being used.
requires(isa_required=ISA.RISCV)

default_disk = 'riscv-disk-img'
default_kernel = 'riscv-bootloader-vmlinux-5.10'

cpu_types = {
    "atomic" : CPUTypes.ATOMIC,
    "timing" : CPUTypes.TIMING,
    "minor"  : CPUTypes.MINOR,
    "o3"     : CPUTypes.O3,
    "kvm"    : CPUTypes.KVM,
}

def addOptions(parser):
    parser.add_argument("--restore-from", type=str, default=None,
                        help="Restore from checkpoint")
    parser.add_argument("--kernel", type=str, default=None,
                        help="Linux kernel")
    parser.add_argument("--disk", type=str, default=None,
                        help="Disks to instantiate")
    parser.add_argument("--cpu-type", type=str, choices=list(cpu_types.keys()),
                        default="timing",
                        help="CPU simulation mode. Default: %(default)s")
    parser.add_argument("--with-cores", action="store_true", default=False,
                        help="Import external hardware IP cores")
    return parser

def instantiate(options):
    """Instantiate Simulator object."""
    cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
        l1d_size="32KiB", l1i_size="32KiB", l2_size="512KiB")
    # Setup the system memory.
    memory = SingleChannelDDR3_1600()

    # Setup a single core Processor.
    processor = SimpleProcessor(
        cpu_type=cpu_types[options.cpu_type],
        isa=ISA.RISCV,
        num_cores=1)

    # Setup the board.
    board = RiscvBoard(
        clk_freq="1GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy)

    if options.with_cores:
        try:
            import cores
        except:
            print('Can not import external hardware IP cores')
            exit(-1)
        cores.load(['m5.objects.rng'])

        from m5.objects.rng import RandomNumberGenerator

        board.extra_rng = RandomNumberGenerator(
            pio_addr=0x10004000,
            pio_size=8)

        board._off_chip_devices.append(board.extra_rng)

    if options.kernel is None or len(options.kernel) == 0:
        kernel = Resource(default_kernel)
    elif os.path.isabs(options.kernel):
        kernel = CustomResource(local_path=options.kernel)
    else:
        kernel = CustomResource(local_path=SysPaths.binary(options.kernel))

    if options.disk is None or len(options.disk) == 0:
        disk = Resource(default_disk)
    elif os.path.isabs(options.disk):
        disk = CustomResource(local_path=options.disk)
    else:
        disk = CustomResource(local_path=SysPaths.disk(options.disk))

    # Set the Full System workload.
    board.set_kernel_disk_workload(kernel=kernel, disk_image=disk)

    if options.with_cores:
        # Append extra_rng to dts
        new_fdt = Fdt()
        outdir = m5.options.outdir
        with open(os.path.join(outdir, 'device.dtb'), 'rb') as infile:
            dtb = pyfdt.FdtBlobParse(infile)
            fdt = dtb.to_fdt()
            soc_node = fdt.resolve_path('/soc')
            soc_state = FdtState(addr_cells=2, size_cells=2)
            extra_rng = board.extra_rng
            extra_rng_node = extra_rng.generateBasicPioDeviceNode(
                soc_state, "extra_rng", extra_rng.pio_addr, extra_rng.pio_size
            )
            extra_rng_node.appendCompatible(["mmio"])
            soc_node.append(extra_rng_node)
            new_fdt.add_rootnode(fdt.get_rootnode())
        new_fdt.writeDtsFile(os.path.join(outdir, "device.dts"))
        new_fdt.writeDtbFile(os.path.join(outdir, "device.dtb"))

    # Set checkpoint path
    if options.restore_from:
        if not os.path.isabs(options.restore_from):
            cpt = options.restore_from
        else:
            cpt = os.path.abspath(options.restore_from)
            if not os.path.isdir(cpt):
                cpt = os.path.join(m5.options.outdir, options.restore_from)
        if not os.path.isdir(cpt):
            raise IOError("Can't find checkpoint directory")
        simulator = Simulator(board=board, checkpoint_path=cpt)
    else:
        simulator = Simulator(board=board)

    return simulator

def main():
    parser = argparse.ArgumentParser(
        description="Generic RISC-V Full System configuration")
    addOptions(parser)
    options = parser.parse_args()
    simulator = instantiate(options)
    print("Beginning simulation!")
    simulator.run()
    exit_cause = simulator.get_last_exit_event_cause()
    exit_enum = ExitEvent.translate_exit_status(exit_cause)
    if exit_enum is ExitEvent.CHECKPOINT:
        simulator.save_checkpoint(m5.options.outdir)
        print('Saved checkpoint')


if __name__ == "__m5_main__":
    main()
