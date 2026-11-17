# CHERI-D simulator benchmarks

The `CHERID` branch contains only CHERI-D/ObjID-adapted benchmark binaries.
Root `*.bin` files are RISC-V ELF executables, ready for Toooba's ELF-to-hex
converter. Ordinary CHERI controls are kept outside this published suite.

| Binary | Workload | Validation |
| --- | --- | --- |
| `patricia.bin` | Historical ObjID-enabled Patricia | Completed on Reloaded LSOQ and pre-BRAM models without assertions |
| `treeadd-objid.bin` | 511 packed coloured nodes; four traversals | Every sum checked |
| `treeadd-wide-objid.bin` | 2047 packed coloured nodes; four traversals | Every sum checked |
| `treeadd-warm-objid.bin` | 511 nodes; construction and a traversal before timing | Every sum checked |
| `bisort-objid.bin` | Two identical 127-node coloured trees; sort ascending/descending | Order, count and sum checked |

All five binaries completed on the current Reloaded LSOQ model with
19 ObjQueue entries and **50 added DRAM cycles**. `manifest.json` records exact
binary hashes, source revisions, build commands, model configuration and
observed counters. Patricia also retains its earlier no-added-delay validation.
The completed [ObjQueue size study](study/objqueue-2026-11-17/README.md) finds
13 effective entries sufficient for a 1% body-cycle budget, with 16 as the
recommended separately compiled configuration. Do not interpret the execution-only
validation of historical Patricia as an independent algorithm-correctness proof.

## Verify and run

Run `make` (Python 3 required). It checks that every root binary is listed in
the manifest, has the expected hash, and is a RISC-V ELF. It does not rerun the
simulator or overwrite committed binaries with ordinary CHERI builds.

Run Toooba's `Tests/elf_to_hex` converter **inside an isolated run directory**
so `Mem.hex` and `symbol_table.txt` remain together; then run Bluesim with
`+tohost`. These timed binaries encode body cycles in `tohost >> 1`; a positive
value is not an ISA-test failure status. The Olden drivers reserve bit30 for
failures. Reject assertions, missing tohost, timeouts, and high-bit statuses
even when Bluesim's process return code is zero.

The local validation model derives from Toooba commit
`60d7c8295eceb3cc8c4249753d70866c300d47fc`. `validation/model.patch` contains
its two study-only changes: a DRAM-path instance of the existing AXI delay
shim and a selectable effective ObjQueue ring size. Apply that patch in the
Toooba source root, then build the normal
`builds/RV64ACDFIMSUxCHERI_Toooba_bluesim` simulator. Default added latency is
50; `+memlat0` selects zero. `+objqN` selects N effective entries (1..19),
with 19 physical entries. The ObjID lookup cache is unchanged. This model is
for performance study; it does not measure FPGA area or frequency.
`validation/probes.json` records positive and faulting load/store probes.
A separately compiled physical queue must cross-check any size recommendation.

## Rebuild the Olden binaries

Initialise only the needed source submodule:

```
git submodule update --init Toooba-olden
```

The pinned `Toooba-olden:CHERID` source includes `cherid/build.py`, drivers,
allocator, startup code, native algorithm checks, and positive/negative ObjID
probes. Use each build command in `manifest.json`, replacing `/path/to/sdk`
with a CHERI bare-metal SDK. The recorded compiler is CHERI LLVM13 revision
`c45239938ef27816bf169758f5f1b32639f6303c`; custom operations use checked raw
encodings, so a private LLVM fork is not required. Debug paths are mapped to
stable names; a treeadd rebuild from another source directory produced an
identical ELF. See the source README for allocation limits and validation.

The inherited bisort algorithm does not correctly descending-sort an already
ascending tree at 511 nodes in native tests. This driver sorts fresh identical
trees in the two directions. Larger inputs also fail native checks, so the
ported driver limits levels to9; the committed workload uses levels7.

`Toooba-mibench2` remains a reference source pin. The exact historical adapted
Patricia source and compiler invocation have not been recovered. Its binary
provenance is recorded explicitly; it is not silently rebuilt from ordinary
Patricia source.

Add new binaries only with corresponding source pins, validation and manifest
updates. Leave uncoloured controls, generated traces and failed binaries out
of the root suite.
