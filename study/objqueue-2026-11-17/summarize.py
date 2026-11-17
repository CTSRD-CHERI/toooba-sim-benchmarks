#!/usr/bin/env python3
"""Aggregate completed runs and chart deterministic cycle overheads."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('runs',type=Path,nargs='+')
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
rows={}
for folder in a.runs:
    for path in sorted(folder.glob('q*/*/result.json')):
        r=json.loads(path.read_text());r['source']=str(path)
        if r.get('error') or r.get('returncode') or not 0<r.get('exit_value',0)<0x40000000:
            raise RuntimeError(f'Invalid performance result: {r}')
        key=r['benchmark'],int(r['variant'][1:])
        if key in rows:
            assert all(r.get(k)==rows[key].get(k) for k in ('sha256','exit_value','cycles_to_tohost')), f'Non-deterministic repeated run: {key}'
        rows[key]=r
base={name:r for (name,size),r in rows.items() if size==19}
out=[]
for (name,size),r in sorted(rows.items()):
    if name not in base:continue
    b=base[name];assert r['sha256']==b['sha256']
    out.append({'benchmark':name,'entries':size,'body_cycles':r['exit_value'],
                'overhead_percent':100*(r['exit_value']/b['exit_value']-1),
                'whole_cycles':r['cycles_to_tohost'],
                'whole_overhead_percent':100*(r['cycles_to_tohost']/b['cycles_to_tohost']-1),
                'sha256':r['sha256'],'source':r['source']})
if not out:raise SystemExit('No completed runs with a 19-entry baseline yet')
with (a.output/'cycles.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
(a.output/'cycles.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['| Benchmark | Entries | Body cycles | Overhead | Whole-program overhead |',
       '| --- | ---: | ---: | ---: | ---: |']
for r in out:
    lines.append(f"| {r['benchmark']} | {r['entries']} | {r['body_cycles']:,} | {r['overhead_percent']:+.2f}% | {r['whole_overhead_percent']:+.2f}% |")
(a.output/'table.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
