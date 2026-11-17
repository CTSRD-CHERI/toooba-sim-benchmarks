#!/usr/bin/env python3
"""Check independently compiled capacities against matching effective-capacity runs."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
rows=[]
for n,sweep in [(8,'sweep-initial'),(16,'sweep-high')]:
    folder=root/f'physical{n}-runs'
    model=root/f'quiet-sim-physical{n}/exe_HW_sim.so'
    for binary in sorted((root/'study-binaries').glob('*.bin')):
        actual=json.loads((folder/f'physical{n}'/binary.stem/'result.json').read_text())
        expected=json.loads((root/sweep/f'q{n}'/binary.stem/'result.json').read_text())
        assert not actual.get('error') and actual['returncode']==0
        for k in ('sha256','cycles_to_tohost','tohost','exit_value'):
            assert actual[k]==expected[k],(n,binary.name,k,actual[k],expected[k])
        rows.append({'capacity':n,'benchmark':binary.name,'sha256':actual['sha256'],
                     'body_cycles':actual['exit_value'],'whole_cycles':actual['cycles_to_tohost'],
                     'match':'exact','physical_model_sha256':hashlib.sha256(model.read_bytes()).hexdigest()})
(root/'results/physical-validation.json').write_text(json.dumps(rows,indent=2)+'\n')
print(f'PASS: {len(rows)} independently compiled runs match effective-capacity models exactly')
