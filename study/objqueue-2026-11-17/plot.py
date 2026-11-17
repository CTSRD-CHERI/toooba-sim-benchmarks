#!/usr/bin/env python3
"""Create standalone performance figures from the archived cycle ledger."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser()
p.add_argument('results',type=Path,help='directory containing cycles.json')
a=p.parse_args()
rows=json.loads((a.results/'cycles.json').read_text())
labels={'bisort-objid.bin':'bisort (127 + 127 nodes)',
        'patricia.bin':'Patricia ObjID (historical)',
        'treeadd-objid.bin':'treeadd (511 nodes)',
        'treeadd-warm-objid.bin':'treeadd warm (511 nodes)',
        'treeadd-wide-objid.bin':'treeadd (2047 nodes)'}
colors=['#0072b2','#d55e00','#009e73','#cc79a7','#e69f00']
plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})
for zoom in (False,True):
    fig,ax=plt.subplots(figsize=(10,5.5),layout='constrained')
    for color,(name,label) in zip(colors,labels.items()):
        points=sorted((r for r in rows if r['benchmark']==name),key=lambda r:r['entries'])
        ax.plot([r['entries'] for r in points],[r['overhead_percent'] for r in points],
                marker='o',markersize=4,linewidth=1.5,label=label,color=color)
    ax.axhline(1,color='#333',ls='--',lw=1,label='1% comparison threshold')
    ax.axhline(0,color='#999',lw=.7)
    ax.grid(alpha=.2)
    ax.set_title('ObjQueue capacity: 50 added DRAM cycles; ObjID lookup cache fixed at 64 entries')
    ax.set_xlabel('Effective ObjQueue entries (simulator compiled for 19 entries)')
    ax.set_ylabel('Extra benchmark body cycles versus 19 entries (%)')
    ax.set_xticks(list(range(1,17))+[19])
    if zoom:ax.set_xlim(7.6,19.4);ax.set_ylim(-1,3.5)
    ax.legend(loc='upper right',fontsize=8,framealpha=.92)
    name='queue-overhead-zoom' if zoom else 'queue-overhead'
    fig.savefig(a.results/(name+'.svg'))
    fig.savefig(a.results/(name+'.png'),dpi=160)
    plt.close(fig)
points=sorted((r for r in rows if r['benchmark']=='treeadd-control.bin'),key=lambda r:r['entries'])
fig,ax=plt.subplots(figsize=(8,4.5),layout='constrained')
ax.plot([r['entries'] for r in points],[r['overhead_percent'] for r in points],marker='o',color='#0072b2')
ax.axhline(1,color='#333',ls='--',lw=1,label='1% threshold')
ax.set_xlabel('Effective ObjQueue entries');ax.set_ylabel('Extra body cycles versus 19 entries (%)')
ax.set_xticks([r['entries'] for r in points]);ax.grid(alpha=.2)
ax.set_title('Uncoloured treeadd control: ordinary memory operations also reserve credits')
ax.legend();fig.savefig(a.results/'uncoloured-control.svg');fig.savefig(a.results/'uncoloured-control.png',dpi=160)
