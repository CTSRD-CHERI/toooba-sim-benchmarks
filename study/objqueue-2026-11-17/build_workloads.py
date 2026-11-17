#!/usr/bin/env python3
"""Rebuild the fixed ObjID workload matrix and an uncoloured control."""
from pathlib import Path
import json, hashlib, subprocess
root=Path(__file__).resolve().parent
builder=root.parents[1]/'Toooba-olden/cherid/build.py'
specs=[('treeadd-objid','treeadd',9,[]),('treeadd-wide-objid','treeadd',11,[]),
       ('treeadd-warm-objid','treeadd',9,['--algorithm-only']),('bisort-objid','bisort',7,[]),
       ('treeadd-control','treeadd',9,['--control'])]
manifest=[]
for name,benchmark,levels,flags in specs:
    folder=root/('control-binaries' if '--control' in flags else 'study-binaries')
    path=folder/(name+'.bin')
    cmd=['python3',str(builder),'--benchmark',benchmark,'--levels',str(levels),*flags,'--output',str(path)]
    subprocess.run(cmd,check=True)
    manifest.append({'file':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'benchmark':benchmark,'levels':levels,'flags':flags,'build_command':cmd,
                     'source_commit':subprocess.check_output(['git','-C',str(root.parents[1]/'Toooba-olden'),'rev-parse','HEAD'],text=True).strip()})
(root/'workloads.json').write_text(json.dumps(manifest,indent=2)+'\n')
