#!/usr/bin/env python3
"""Produce coverage-aware summaries, without assuming monotonic performance."""
from pathlib import Path
import json
root=Path(__file__).resolve().parent
rows=json.loads((root/'results/cycles.json').read_text())
workloads=['bisort-objid.bin','patricia.bin','treeadd-objid.bin','treeadd-warm-objid.bin','treeadd-wide-objid.bin']
selected=[r for r in rows if r['benchmark'] in workloads]
summary=[]
for size in sorted({r['entries'] for r in selected}):
    points=[r for r in selected if r['entries']==size]
    worst=max(points,key=lambda r:r['overhead_percent'])
    complete={r['benchmark'] for r in points}==set(workloads)
    verdict='fails' if worst['overhead_percent']>1 else ('passes' if complete else 'pending')
    summary.append({'entries':size,'tested_workloads':len(points),'complete':complete,
                    'worst_overhead_percent':worst['overhead_percent'],'worst_workload':worst['benchmark'],'one_percent_criterion':verdict})
lines=['| Entries | Largest measured body overhead | Workloads tested | Meets 1% on every workload? |',
       '| ---: | ---: | ---: | --- |']
for r in summary:
    lines.append(f"| {r['entries']} | {r['worst_overhead_percent']:+.2f}% | {r['tested_workloads']}/5 | {r['one_percent_criterion']} |")
(root/'results/capacity-summary.md').write_text('\n'.join(lines)+'\n')
(root/'results/capacity-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['| Workload | 4 entries | 8 entries | 12 entries | 13 entries | 16 entries | 19 entries |',
       '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
lookup={(r['benchmark'],r['entries']):r for r in selected}
for name in workloads:
    values=[]
    for size in (4,8,12,13,16,19):
        r=lookup.get((name,size));values.append(f"{r['overhead_percent']:+.2f}%" if r else 'pending')
    lines.append('| '+name+' | '+' | '.join(values)+' |')
(root/'results/overhead-matrix.md').write_text('\n'.join(lines)+'\n')
print((root/'results/capacity-summary.md').read_text())
