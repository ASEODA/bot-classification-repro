#!/usr/bin/env python3
"""Run unchanged study programs in an isolated, relocatable workspace. No API generation."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import unicodedata

REPO = Path(__file__).resolve().parents[1]
STAGE = Path('research/단계별 진행경과')
NFC = lambda value: unicodedata.normalize('NFC', str(value))

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()

def prepare(work, download):
    if work.exists():
        raise FileExistsError(f'Use a new workspace or continue with run/verify: {work}')
    assets = read(REPO/'scripts/manifests/assets.json')
    for asset in assets:
        path = REPO/'.assets'/asset['name']
        if not path.exists() and download:
            path.parent.mkdir(exist_ok=True)
            subprocess.run(['gh', 'release', 'download', asset['release'], '--repo',
                            asset['repository'], '--pattern', asset['name'],
                            '--dir', str(path.parent)], check=True)
        if not path.exists() or sha(path) != asset['sha256']:
            raise ValueError(f'Missing/corrupt asset: {path.name}; use prepare --download')
    shutil.copytree(REPO/'source', work)
    for asset in assets:
        with tarfile.open(REPO/'.assets'/asset['name']) as tf:
            tf.extractall(work, filter='data')
    # Early scripts predate the folder move. Relative aliases preserve source hashes.
    for name in ('1. 원본데이터', '02_UD캐시'):
        (work/STAGE/name).symlink_to(Path('..')/name, target_is_directory=True)
    # This parser was authored one directory below STAGE, before its later rename.
    parser = work/STAGE/'fox8_parser/13-1_fox8재파싱.py'
    parser.parent.mkdir()
    shutil.copy2(work/STAGE/'13-1_fox8재파싱.py', parser)
    verify(work)

def verify(work):
    rows = read(REPO/'scripts/manifests/files.json')
    wrong = [r['path'] for r in rows if not (work/r['path']).is_file()
             or sha(work/r['path']) != r['sha256']]
    report = {'files': len(rows), 'mismatches': wrong, 'passed': not wrong}
    write(work/'validation/initial-integrity.json', report)
    if wrong:
        raise ValueError(f'Integrity check failed: {wrong[:10]}')
    print(f'PASS: {len(rows)} source/data/model/checkpoint files', flush=True)

def env_for(work):
    env = os.environ.copy()
    env.update(HOME=str(work/'home'), STANZA_RESOURCES_DIR=str(work/'models/stanza'),
               PYTHONDONTWRITEBYTECODE='1', TOKENIZERS_PARALLELISM='false',
               HF_HUB_OFFLINE='1', MPLBACKEND='Agg', PYTHONHASHSEED='0')
    # No credentials are required or passed to the analytical pipeline.
    for key in list(env):
        if any(token in key.upper() for token in ('API_KEY', 'AUTH_TOKEN', 'GH_TOKEN', 'GITHUB_TOKEN')):
            env.pop(key)
    return env

def stash(work, relative):
    path = work/relative
    if path.exists():
        dest = work/'.previous'/str(time.time_ns())/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(path, dest)

def execute(work, relative, args=(), python=None):
    script = work/relative
    log = work/'logs'/(script.stem+'-'+str(time.time_ns())+'.log')
    log.parent.mkdir(exist_ok=True)
    print(f'RUN {relative} {" ".join(args)} → {log.relative_to(work)}', flush=True)
    started = time.monotonic()
    with log.open('w', encoding='utf-8') as f:
        p = subprocess.run([str(python or sys.executable), '-u', str(script), *args], cwd=script.parent,
                           env=env_for(work), stdout=f, stderr=subprocess.STDOUT)
    record = {'script': str(relative), 'arguments': list(args), 'exit_code': p.returncode,
              'elapsed_seconds': round(time.monotonic()-started, 3), 'log': str(log.relative_to(work))}
    with (work/'validation/runs.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False)+'\n')
    if p.returncode:
        print(log.read_text(encoding='utf-8')[-6000:])
        raise RuntimeError(f'Step failed; no later step was run: {script.name}')
    print(f'PASS {script.name} ({record["elapsed_seconds"]}s)', flush=True)

RAW_STEPS = [
    ('01_botsim_적격검열.py', '01_적격계정.json'),
    ('02_기능어목록_생성.py', '02_기능어목록.json'),
    ('04_기능어측정.py', '04_기능어측정.json'),
    ('05_사용률검수.py', '05_사용률검수.json'),
    ('06_봇사람비교.py', '06_비교결과.json'),
    ('07_형태자질비교.py', '07_형태자질비교.json'),
    ('04-1_확장재파싱.py', '04-1_확장재파싱.json'),
    ('08_R블록.py', '08_R블록.json'),
    ('09-1_분량통제.py', '09-1_분량통제.json'),
    ('09-2_게시물유형통제.py', '09-2_게시물유형통제.json'),
    ('09-3_서브레딧통제.py', '09-3_서브레딧통제.json'),
    ('02-1_임계값민감도.py', '02-1_임계값민감도.json'),
]

def raw(work, botsim_python):
    fox = work/'research/1. 원본데이터/3. fox8 Data'
    rebuilt = fox/('rebuilt-'+str(time.time_ns())+'.sqlite')
    subprocess.run([sys.executable, str(REPO/'scripts/import_fox8.py'),
                    str(fox/'fox8_23_dataset.ndjson.gz'), str(rebuilt)], check=True)
    stash(work, Path('research/1. 원본데이터/3. fox8 Data/fox8_23_dataset.sqlite'))
    shutil.move(rebuilt, fox/'fox8_23_dataset.sqlite')
    for script, output in RAW_STEPS:
        stash(work, STAGE/output)
        execute(work, STAGE/script, python=botsim_python)
        if not (work/STAGE/output).is_file():
            raise RuntimeError(f'Step returned without required output: {output}')
    control = STAGE/'09_FMR 통제 재검증'
    stash(work, control/'입력코퍼스.json')
    execute(work, control/'fmr_prepare_measure.py', ['prepare'], python=botsim_python)
    execute(work, control/'fmr_prepare_measure.py', ['measure'], python=botsim_python)
    execute(work, control/'fmr_controls.py', python=botsim_python)
    execute(work, STAGE/'10-1_귀무오류율.py', ['--reps', '1000'])
    parser = STAGE/'fox8_parser/13-1_fox8재파싱.py'
    execute(work, parser)
    # Only an output filename relocation; measured values and metadata are unchanged.
    stash(work, STAGE/'13-1_fox8재파싱.json')
    shutil.move(work/STAGE/'fox8_parser/12-0_fox8재파싱.json', work/STAGE/'13-1_fox8재파싱.json')
    analyze(work)

def analyze(work):
    for script, args in [
        ('10_동질성검정.py', []),
        ('11_판별기.py', ['--overwrite']),
        ('12-3_판별기적용.py', ['--overwrite']),
        ('13_fox8전이.py', ['--overwrite']),
    ]:
        execute(work, STAGE/script, args)
    subprocess.run([sys.executable, str(REPO/'scripts/check_results.py'), str(work)], check=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['prepare','verify','raw','analysis','step','smoke-fox8'])
    ap.add_argument('--work', type=Path, default=REPO/'work')
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--botsim-python', type=Path, help='Python of requirements-botsim.txt environment; required for raw')
    ap.add_argument('--script', help='Relative to the study stage; only for step')
    ap.add_argument('--args', nargs=argparse.REMAINDER, default=[])
    a = ap.parse_args(); work = a.work.expanduser().resolve()
    if a.command == 'prepare': prepare(work, a.download)
    elif a.command == 'verify': verify(work)
    elif a.command == 'raw':
        if not a.botsim_python: ap.error('raw requires --botsim-python (see requirements-botsim.txt)')
        raw(work, a.botsim_python.expanduser().resolve())
    elif a.command == 'analysis': analyze(work)
    elif a.command == 'step':
        if not a.script: ap.error('step requires --script')
        relative = STAGE/a.script
        if not (work/relative).resolve().is_relative_to(work/STAGE): ap.error('script outside stage')
        execute(work, relative, a.args)
    else:
        out = work/'smoke-fox8'; out.mkdir(exist_ok=True)
        execute(work, STAGE/'fox8_parser/13-1_fox8재파싱.py', ['3', str(out)])

if __name__ == '__main__': main()
