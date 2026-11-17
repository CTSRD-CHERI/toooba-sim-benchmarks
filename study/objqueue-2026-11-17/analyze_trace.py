#!/usr/bin/env python3
"""Count validated ObjQueue allocation high-water and sole-cause admission events."""
import argparse,collections,gzip,json,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('runs',type=Path,nargs='+')
p.add_argument('--ledger',type=Path,required=True)
p.add_argument('--binaries',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--nm',type=Path,default=Path('/local/scratch/jdw57/cheri/output/sdk/bin/llvm-nm'))
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
expected={(r['benchmark'],r['entries']):r for r in json.loads(a.ledger.read_text())}
block=re.compile(r'^OBJQ_BLOCK cycle=(\d+) pc=0x([0-9a-f]+) lane=(\d+) used=(\d+) limit=(\d+) tail=(\d+) load=(\d+)$')
high=re.compile(r'^OBJQ_HIGH cycle=(\d+) used=(\d+) limit=(\d+)$')
rows=[]
for folder in a.runs:
    for result_path in sorted(folder.glob('q*/*/result.json')):
        r=json.loads(result_path.read_text());n=int(r['variant'][1:])
        assert not r.get('error') and r['returncode']==0,r
        ref=expected[r['benchmark'],n]
        assert (r['sha256'],r['exit_value'],r['cycles_to_tohost'])==(ref['sha256'],ref['body_cycles'],ref['whole_cycles']), 'Tracing changed timing: '+str(r)
        peak=0;events=[];pcs=collections.Counter();lanes=collections.Counter();classes=collections.Counter();examples=[]
        with gzip.open(result_path.parent/'simulation.log.gz','rt',errors='replace') as f:
            for line in f:
                line=line.strip()
                assert not any(t in line for t in ('unsupported OBJQ_','ERROR:','FATAL','PANIC','FAIL:')),line
                if m:=high.match(line):
                    cycle,used,limit=map(int,m.groups());assert limit==n and 0<used<=n
                    if cycle>=r['cycles_to_tohost']:continue
                    peak=max(peak,used)
                elif m:=block.match(line):
                    cycle,pc,lane,used,limit,tail,ld=m.groups()
                    cycle,lane,used,limit,tail,ld=map(int,(cycle,lane,used,limit,tail,ld))
                    assert used==limit==n and 0<=tail<n and lane in (0,1) and ld in (0,1),line
                    if cycle>=r['cycles_to_tohost']:continue  # exclude termination-cycle ordering artifacts
                    events.append(cycle);pcs[int(pc,16)]+=1;lanes[lane]+=1;classes['LQ' if ld else 'SQ']+=1
                    if len(examples)<5:examples.append(line)
        assert len(set(events))==len(events),'More than one blocked event per cycle'
        assert peak>0,'Missing high-water trace'
        events.sort();longest=0;streak=0;prev=None
        for cycle in events:
            streak=streak+1 if prev is not None and cycle==prev+1 else 1
            longest=max(longest,streak);prev=cycle
        symbols=[]
        for line in subprocess.check_output([str(a.nm),'--defined-only','--numeric-sort','--print-size',str(a.binaries/r['benchmark'])],text=True).splitlines():
            bits=line.split()
            if len(bits)>=4 and bits[2] in ('t','T') and not bits[3].startswith('.L'):
                symbols.append((int(bits[0],16),int(bits[1],16),bits[3]))
        def symbol(pc):
            matches=[s for s in symbols if s[0]<=pc and (s[1]==0 or pc<s[0]+s[1])]
            if not matches:return 'unknown'
            s=max(matches,key=lambda s:s[0]);return s[2]+'+0x'+format(pc-s[0],'x')
        functions=collections.Counter()
        for pc,count in pcs.items():functions[symbol(pc).split('+')[0]]+=count
        top=[{'pc':'0x'+format(pc,'x'),'symbol':symbol(pc),'cycles':count} for pc,count in pcs.most_common(10)]
        rows.append({'benchmark':r['benchmark'],'entries':n,'peak_allocated':peak,'reached_capacity':peak==n,
                     'objqueue_only_blocked_cycles':len(events),'fraction_of_whole_cycles_percent':100*len(events)/r['cycles_to_tohost'],
                     'longest_consecutive_blocked_cycles':longest,'blocked_by_lane':dict(lanes),'blocked_by_payload_queue':dict(classes),
                     'body_cycles':r['exit_value'],'whole_cycles':r['cycles_to_tohost'],'timing_match':'exact',
                     'sha256':r['sha256'],'blocked_by_function':dict(functions.most_common()),'top_pcs':top,'examples':examples,'source':str(result_path)})
(a.output/'admission-trace.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['| Workload | Entries | Peak allocated | ObjQueue-only blocked cycles | First lane | Second lane | % of whole run | Longest consecutive block |',
       '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for r in rows:
    lines.append(f"| {r['benchmark']} | {r['entries']} | {r['peak_allocated']} | {r['objqueue_only_blocked_cycles']:,} | {r['blocked_by_lane'].get(0,0):,} | {r['blocked_by_lane'].get(1,0):,} | {r['fraction_of_whole_cycles_percent']:.2f}% | {r['longest_consecutive_blocked_cycles']} |")
(a.output/'admission-trace.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
