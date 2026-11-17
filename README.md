# CHERI-D simulator benchmarks

The `CHERID` branch contains only CHERI-D/ObjID-adapted benchmark binaries.
Root `*.bin` files are RISC-V ELF executables, ready for Toooba's ELF-to-hex
converter. Ordinary CHERI binaries are intentionally excluded from this suite.

## Included binaries

| Binary | Adaptation | Validation |
| --- | --- | --- |
| `patricia.bin` | Historical ObjID-enabled Patricia; custom instructions and metadata accesses in `pat_insert` | Completed on Reloaded LSOQ `60d7c829` and the pre-BRAM design without assertions |

`manifest.json` records the exact binary hash, provenance, simulator revision,
and observed counters. These existing runs have **no additional DRAM latency**;
the approximately 50-cycle backing-memory study has not been run yet.
Execution completed successfully, but no independent algorithm-correctness proof
or stale-ID negative test is claimed for this historical binary.

## Check the committed suite

Run `make` (Python 3 required). This checks that every root binary is listed in
the manifest, has the expected hash, and is a RISC-V ELF. It does not rerun the
simulator or rebuild historical binaries. A normal checkout is sufficient.

To execute a binary, convert it with Toooba's `Tests/elf_to_hex` tool to
`Mem.hex` in an isolated run directory, then launch the simulator with `+tohost`.
Patricia encodes measured body cycles in `tohost >> 1`; a positive value is not
an ISA-test failure status. Record assertions as failures even if Bluesim exits
with process status zero.

## Source repositories and additions

`Toooba-mibench2` and `Toooba-olden` retain the upstream source pins inherited
from `cheri-cam`. They are reference sources, **not yet reproducible CHERI-D
build inputs**. The exact source changes and compiler invocation for the
historical Patricia binary have not been recovered.

Use existing CHERI-D branches in those source repositories when available;
otherwise create `CHERID` branches for the adaptations. Add Olden binaries here
only after they exercise ObjID checks and pass validation. Update their source
pins, hashes, build instructions, and validation records together. The default
Makefile verifies the committed suite so it cannot accidentally replace it with
ordinary CHERI builds from the reference sources.
