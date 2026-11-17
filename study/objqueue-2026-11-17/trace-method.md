The optional simulation flag `+trace_objq` emits two kinds of records:

```
OBJQ_HIGH cycle=... used=... limit=...
OBJQ_BLOCK cycle=... pc=0x... lane=... used=... limit=... tail=... load=...
```

`OBJQ_HIGH` reports each new allocation high-water mark, including the new
reservation. It can prove that the queue reaches capacity even if a credit is
returned next cycle and admission never stalls.

`OBJQ_BLOCK` records an instruction denied admission at rename when the ObjQueue
is full and the other explicit admission prerequisites are available: correct
path, no replay/trap/MMIO barrier, ROB/rename space, memory reservation-station
space, corresponding LQ/SQ space, and no conflicting squash. Occupancy uses the
same EHR phase as the allocation guard, including same-cycle credit returns.
`load=1` identifies the LQ class; zero identifies the SQ class.

A blocked first lane is observed by a separate rule, because the normal rename
rule is disabled when no instruction progresses. Second-lane events are logged
inside the normal rule after an older non-memory instruction progresses. Thus
second-lane events are lost admission opportunities, not complete pipeline
stalls. The observer is explicitly disabled when it has nothing to report.

These events measure admission into the LSQ, not the issue of an already
renamed request to the data cache. They cover the whole run, including startup,
allocation and untimed warm-up. They are not restricted to the benchmark body's
measurement window. Event counts are not equal to added execution cycles:
admission can wait while older work is already keeping the processor busy.

The first draft included the head pointer in the snapshot, which created an
incompatible EHR scheduling order and inhibited retirement. The regression
caught this; the final snapshot omits that read. The tested snapshot contains
only allocation-phase occupancy, capacity, full status and allocation pointer.
The regression distinguishes ObjQueue exhaustion with free payload space from
payload-queue exhaustion with free ObjQueue credits.

The trace is simulation-only (`BSIM`) and disabled unless requested. A tiny
2-entry smoke test forces exhaustion: uninstrumented and instrumented models
produce identical termination cycles and results. Full-output and filtered
models preserve all 503 pre-termination smoke-test records. Records from the
termination cycle itself are excluded, since display ordering around `$finish`
can leave an extra diagnostic row in one output path.

`analyze_trace.py` requires each traced workload's binary hash, body cycles and
whole-program cycles to match its original sweep point exactly. It checks that
every block event has occupancy equal to the configured capacity, records
allocation peaks, counts first/second-lane events, measures consecutive block
runs, and maps the most frequent PCs using `llvm-nm`.

Recount the archived filtered logs from this study directory with:

```
python3 analyze_trace.py traces --ledger results/cycles.json --binaries ../.. --output /tmp/objqueue-recount --nm /path/to/sdk/bin/llvm-nm
```
