#!/usr/bin/env python3
"""Run identical ELF benchmarks; preserve compressed output and termination cycles."""
import argparse
import concurrent.futures
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import time


def run_one(variant, sim, binary, out, converter, timeout):
    work = out / variant / binary.stem
    work.mkdir(parents=True, exist_ok=True)
    result = dict(variant=variant, benchmark=binary.name,
                  sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    converted = subprocess.run([str(converter), str(binary), 'Mem.hex'], cwd=work,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (work / 'conversion.log').write_bytes(converted.stdout)
    if converted.returncode:
        result['error'] = 'ELF conversion failed'
    else:
        start = time.monotonic()
        process = subprocess.Popen([str(sim), '+tohost'], cwd=work,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        pending = b''
        tail = b''
        with selectors.DefaultSelector() as ready, gzip.open(work / 'simulation.log.gz', 'wb', compresslevel=1) as log:
            ready.register(process.stdout, selectors.EVENT_READ)
            while ready.get_map():
                if time.monotonic() - start > timeout and result.get('error') != 'timeout':
                    import signal
                    os.killpg(process.pid, signal.SIGKILL)
                    result['error'] = 'timeout'
                for key, _ in ready.select(1):
                    chunk = os.read(key.fd, 256 * 1024)
                    if not chunk:
                        ready.unregister(key.fileobj)
                        continue
                    log.write(chunk)
                    tail = (tail + chunk)[-8192:]
                    lines = (pending + chunk).split(b'\n')
                    pending = lines.pop()
                    for line in lines:
                        match = re.search(rb'(\d+): mmioPlatform.rl_tohost: 0x([0-9a-fA-F]+)', line)
                        if match:
                            result['cycles_to_tohost'] = int(match[1])
                            result['tohost'] = int(match[2], 16)
                            result['exit_value'] = result['tohost'] >> 1
                        if b'assertion' in line.lower() and b'failed' in line.lower():
                            result['error'] = line.decode(errors='replace')
                        match = re.search(rb'instret:(\d+)', line)
                        if match:
                            result['last_logged_instret'] = int(match[1])
        result['returncode'] = process.wait()
        result['wall_seconds'] = round(time.monotonic() - start, 2)
        (work / 'tail.txt').write_bytes(tail)
        if 'cycles_to_tohost' not in result:
            result.setdefault('error', 'no tohost termination')
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', action='append', required=True, help='name=/absolute/simulator')
    parser.add_argument('--binaries', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--converter', type=Path, default=Path('/tmp/toooba-elf-to-hex'))
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=3600)
    parser.add_argument('--resume', action='store_true', help='reuse completed results; requires an unchanged simulator')
    args = parser.parse_args()
    variants = [v.split('=', 1) for v in args.variant]
    binaries = sorted(args.binaries.resolve().glob('*.bin'))
    assert binaries, 'No benchmark binaries found'
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = []
        for name, sim in variants:
            for binary in binaries:
                saved = args.output / name / binary.stem / 'result.json'
                if args.resume and saved.exists():
                    result = json.loads(saved.read_text())
                    if not result.get('error') and result['sha256'] == hashlib.sha256(binary.read_bytes()).hexdigest():
                        results.append(result)
                        continue
                jobs.append(pool.submit(run_one, name, Path(sim).resolve(), binary,
                                        args.output.resolve(), args.converter.resolve(), args.timeout))
        for job in concurrent.futures.as_completed(jobs):
            results.append(job.result())
    (args.output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
