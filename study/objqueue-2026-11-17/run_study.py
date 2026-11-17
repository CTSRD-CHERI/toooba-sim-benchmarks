#!/usr/bin/env python3
"""Run identical ELF inputs at independent ObjQueue capacities; save raw evidence."""
import argparse, hashlib, json, os, shlex, subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--sim',type=Path,required=True)
p.add_argument('--binaries',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--reference',type=Path,help='reuse identical q19 baseline from this completed sweep')
p.add_argument('--sizes',default='19,16,12,8,6,4,3,2,1')
p.add_argument('--latency',type=int,choices=[0,50],default=50)
p.add_argument('--jobs',type=int,default=4)
p.add_argument('--timeout',type=int,default=3600)
a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
sim=a.sim.resolve();flags=[]
reference_rows=[]
if a.reference:
    config=json.loads((a.reference/'configuration.json').read_text())
    assert config['simulator_library_sha256']==hashlib.sha256(Path(str(sim)+'.so').read_bytes()).hexdigest()
    assert config['added_DRAM_latency']==a.latency
    for binary in sorted(a.binaries.glob('*.bin')):
        path=a.reference/'q19'/binary.stem/'result.json'
        row=json.loads(path.read_text())
        assert not row.get('error') and row['sha256']==hashlib.sha256(binary.read_bytes()).hexdigest()
        row['reference_file']=str(path.resolve())
        saved=out/'q19'/binary.stem/'result.json';saved.parent.mkdir(parents=True,exist_ok=True)
        saved.write_text(json.dumps(row,indent=2)+'\n');reference_rows.append(row)
for size in map(int,a.sizes.split(',')):
    assert 1<=size<=19
    if a.reference and size==19:continue
    wrapper=out/f'objq{size}'
    wrapper.write_text('#!/bin/sh\nexec '+shlex.quote(str(sim))+f' +objq{size} +memlat{a.latency} "$@"\n');wrapper.chmod(0o755)
    flags+=['--variant',f'q{size}={wrapper}']
(out/'configuration.json').write_text(json.dumps({'simulator':str(sim),'simulator_library_sha256':hashlib.sha256(Path(str(sim)+'.so').read_bytes()).hexdigest(),'added_DRAM_latency':a.latency,'effective_capacities':a.sizes,'physical_capacity':19,'comparison':'Same physical model; ring wrap changes effective capacity only. Requires separate physical-capacity validation.'},indent=2)+'\n')
runner=Path(__file__).with_name('run_benchmarks.py')
assert flags, 'Choose at least one new capacity'
subprocess.run(['python3',str(runner),*flags,'--binaries',str(a.binaries.resolve()),'--output',str(out),'--jobs',str(a.jobs),'--timeout',str(a.timeout)],check=True)
rows=json.loads((out/'results.json').read_text())+reference_rows
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
base={r['benchmark']:r for r in rows if r['variant']=='q19'}
lines=['| Benchmark | Queue entries | Body cycles | Change vs 19 |','| --- | ---: | ---: | ---: |']
for r in rows:
    if r.get('error') or r.get('returncode') or not 0<r.get('exit_value',0)<0x40000000:
        raise RuntimeError('Invalid timing result: '+str(r))
    if r['benchmark'] in base:
        b=base[r['benchmark']]
        assert r['sha256']==b['sha256']
        delta=100*(r['exit_value']/b['exit_value']-1)
        lines.append(f"| {r['benchmark']} | {r['variant'][1:]} | {r['exit_value']:,} | {delta:+.2f}% |")
(out/'comparison.md').write_text('\n'.join(lines)+'\n')
