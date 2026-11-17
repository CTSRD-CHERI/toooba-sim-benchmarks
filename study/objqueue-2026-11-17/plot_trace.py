#!/usr/bin/env python3
"""Plot whole-run admission pressure; these counts are not added runtime."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('results',type=Path);a=p.parse_args()
rows=json.loads((a.results/'admission-trace.json').read_text())
lookup={(r['benchmark'],r['entries']):r for r in rows}
fig,axes=plt.subplots(1,2,figsize=(10,4.7),layout='constrained')
for ax,name,title in zip(axes,('bisort-objid.bin','treeadd-warm-objid.bin'),('Bisort: includes two tree constructions','Treeadd warm: includes untimed construction')):
    points=[lookup[name,n] for n in (13,16,19)]
    bars=ax.bar(['13','16','19'],[r['objqueue_only_blocked_cycles'] for r in points],color=['#0072b2','#e69f00','#999999'])
    for bar,r in zip(bars,points):
        ax.annotate(f"{r['objqueue_only_blocked_cycles']:,}\n({r['fraction_of_whole_cycles_percent']:.2f}% of run)",
                    (bar.get_x()+bar.get_width()/2,bar.get_height()),xytext=(0,5),textcoords='offset points',ha='center',fontsize=9)
    ax.set_title(title,fontsize=11);ax.set_xlabel('ObjQueue entries')
    ax.set_ylabel('ObjQueue-only blocked admission cycles');ax.set_ylim(0,max(r['objqueue_only_blocked_cycles'] for r in points)*1.3)
    ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.suptitle('The queue fills even at 19 entries; admission pressure falls with capacity',fontsize=13)
fig.savefig(a.results/'admission-pressure.png',dpi=160);fig.savefig(a.results/'admission-pressure.svg')
