#!/usr/bin/env python3
"""Relink existing Bluesim objects with output-only display/write wrappers."""
import argparse
from pathlib import Path
import subprocess
import os, shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('repo', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
source = Path(__file__).with_name('trace_quiet_bluesim.cc')
out = args.output.resolve()
out.parent.mkdir(parents=True, exist_ok=True)
build = args.repo.resolve() / 'builds/RV64ACDFIMSUxCHERI_Toooba_bluesim'
library = (Path(os.environ['BLUESPECDIR']) if os.environ.get('BLUESPECDIR') else Path(shutil.which('bsc')).resolve().parent.parent/'lib')/'Bluesim'
obj = out.parent / 'quiet.o'
wrapped = out.parent / 'quiet-wrapped.o'
subprocess.run(['g++', '-O2', '-fPIC', '-c', '-I'+str(library), str(source), '-o', str(obj)], check=True)
names = [line.split()[-1] for line in subprocess.check_output(['nm', '-g', '--defined-only', str(obj)], text=True).splitlines()
         if 'dollar_' in line]
renames = out.parent / 'wrap-symbols.txt'
renames.write_text(''.join(name+' __wrap_'+name+'\n' for name in names))
subprocess.run(['objcopy', '--redefine-syms='+str(renames), str(obj), str(wrapped)], check=True)
command = ['bsc', '-sim', '-parallel-sim-link', '8', '+RTS', '-K128M', '-RTS',
           '-bdir', 'build_dir', '-simdir', 'build_dir', '-info-dir', 'build_dir',
           '-e', 'mkTop_HW_Side', '-o', str(out), '-Xc', '-O1', '-Xc++', '-O1',
           '-Xl', str(wrapped)]
for name in names:
    command += ['-Xl', '-Wl,--wrap='+name]
command += ['../../src_Verifier/BSV-RVFI-DII/SocketPacketUtils/socket_packet_utils.c',
            '../../src_Testbench/Top/C_Imported_Functions.c']
subprocess.run(command, cwd=build, check=True)
