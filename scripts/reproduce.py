#!/usr/bin/env python3
"""Reproduce the finalized study in an isolated workspace; no API generation."""
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

REPO = Path(__file__).resolve().parents[1]
STAGE = Path('research/단계별 진행경과')
CONTROL = STAGE/'09_FMR 통제 재검증'


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


def prepare(work, download, mode):
    if work.exists():
        raise FileExistsError(f'Use run to resume or choose a new workspace: {work}')
    assets = [a for a in read(REPO/'scripts/manifests/assets.json')
              if mode != 'full' or a['group'] != 'checkpoints']
    for asset in assets:
        path = REPO/'.assets'/asset['name']
        if not path.exists() and download:
            path.parent.mkdir(exist_ok=True)
            subprocess.run(['gh', 'release', 'download', asset['release'], '--repo',
                            asset['repository'], '--pattern', asset['name'],
                            '--dir', str(path.parent)], check=True)
        if not path.exists() or sha(path) != asset['sha256']:
            raise ValueError(f'Missing/corrupt asset: {path.name}')
    shutil.copytree(REPO/'source', work)
    for asset in assets:
        with tarfile.open(REPO/'.assets'/asset['name']) as tf:
            tf.extractall(work, filter='data')
    for name in ('1. 원본데이터', '02_UD캐시'):
        (work/STAGE/name).symlink_to(Path('..')/name, target_is_directory=True)
    write(work/'validation/workspace.json', {'mode': mode})
    verify(work)


def verify(work):
    mode = read(work/'validation/workspace.json')['mode']
    rows = [r for r in read(REPO/'scripts/manifests/files.json')
            if mode != 'full' or r['asset'] != 'checkpoints']
    wrong = [r['path'] for r in rows if not (work/r['path']).is_file()
             or sha(work/r['path']) != r['sha256']]
    write(work/'validation/initial-integrity.json',
          {'files': len(rows), 'mismatches': wrong, 'passed': not wrong, 'mode': mode})
    if wrong:
        raise ValueError(f'Integrity check failed: {wrong[:10]}')
    print(f'PASS: {len(rows)} package files ({mode})', flush=True)


def env_for(work):
    env = os.environ.copy()
    env.update(HOME=str(work/'home'), STANZA_RESOURCES_DIR=str(work/'models/stanza'),
               PYTHONDONTWRITEBYTECODE='1', TOKENIZERS_PARALLELISM='false',
               HF_HUB_OFFLINE='1', MPLBACKEND='Agg', PYTHONHASHSEED='0')
    for key in list(env):
        if any(token in key.upper() for token in ('API_KEY', 'AUTH_TOKEN', 'GH_TOKEN', 'GITHUB_TOKEN')):
            env.pop(key)
    return env


def execute(work, relative, args=(), python=None):
    script = work/relative
    log = work/'logs'/(script.stem+'-'+str(time.time_ns())+'.log')
    log.parent.mkdir(exist_ok=True)
    print(f'RUN {relative} {" ".join(args)} → {log.relative_to(work)}', flush=True)
    started = time.monotonic()
    with log.open('w', encoding='utf-8') as f:
        p = subprocess.run([str(python or sys.executable), '-u', str(script), *args],
                           cwd=script.parent, env=env_for(work), stdout=f, stderr=subprocess.STDOUT)
    record = {'script': str(relative), 'arguments': list(args), 'exit_code': p.returncode,
              'elapsed_seconds': round(time.monotonic()-started, 3), 'log': str(log.relative_to(work))}
    with (work/'validation/runs.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False)+'\n')
    if p.returncode:
        print(log.read_text(encoding='utf-8')[-6000:])
        raise RuntimeError(f'Step failed: {script.name}')
    print(f'PASS {script.name} ({record["elapsed_seconds"]}s)', flush=True)


def step(work, script, outputs, args=(), python=None):
    """Resume only outputs produced by this workspace, never packaged caches."""
    state_path = work/'validation/completed.json'
    state = read(state_path) if state_path.exists() else {}
    key = str(script) + ' ' + ' '.join(args)
    outputs = [Path(p) for p in outputs]
    code = sha(work/script)
    if key in state:
        old = state[key]
        if old['code'] != code or any(not (work/p).exists() or sha(work/p) != h
                                      for p, h in old['outputs'].items()):
            raise ValueError(f'Completed step was modified; use a fresh workspace: {key}')
        print(f'RESUME: completed {key}', flush=True)
        return
    execute(work, script, args, python)
    missing = [str(p) for p in outputs if not (work/p).is_file()]
    if missing:
        raise RuntimeError(f'Step produced no required output: {missing}')
    state[key] = {'code': code, 'outputs': {str(p): sha(work/p) for p in outputs}}
    write(state_path, state)


def fox_db(work):
    folder = work/'research/1. 원본데이터/3. fox8 Data'
    target = folder/'fox8_23_dataset.sqlite'
    if not target.exists():
        temp = folder/'fox8-building.sqlite'
        # A failed import leaves no final DB; preserve an interrupted temp outside the next run.
        if temp.exists():
            temp.rename(folder/f'fox8-interrupted-{time.time_ns()}.sqlite')
        subprocess.run([sys.executable, str(REPO/'scripts/import_fox8.py'),
                        str(folder/'fox8_23_dataset.ndjson.gz'), str(temp)], check=True)
        temp.rename(target)


STAT_STEPS = [
    ('05_사용률검수.py', '05_사용률검수.json'),
    ('06_봇사람비교.py', '06_비교결과.json'),
    ('07_형태자질비교.py', '07_형태자질비교.json'),
    ('08_R블록.py', '08_R블록.json'),
    ('09-1_분량통제.py', '09-1_분량통제.json'),
    ('02-1_임계값민감도.py', '02-1_임계값민감도.json'),
]
RAW_STEPS = [
    ('01_botsim_적격검열.py', '01_적격계정.json'),
    ('02_기능어목록_생성.py', '02_기능어목록.json'),
    ('04_기능어측정.py', '04_기능어측정.json'),
    *STAT_STEPS[:3],
    ('04-1_확장재파싱.py', '04-1_확장재파싱.json'),
    *STAT_STEPS[3:],
]


def run(work, botsim_python=None):
    mode = read(work/'validation/workspace.json')['mode']
    if mode == 'full' and not botsim_python:
        raise ValueError('full requires --botsim-python')
    fox_db(work)
    for script, output in RAW_STEPS if mode == 'full' else STAT_STEPS:
        step(work, STAGE/script, [STAGE/output], python=botsim_python)
    if mode == 'full':
        step(work, CONTROL/'fmr_prepare_measure.py', [CONTROL/'입력코퍼스.json', CONTROL/'입력_실행전_해시.json'],
             ['prepare'], botsim_python)
        step(work, CONTROL/'fmr_prepare_measure.py', [CONTROL/'제한코퍼스_원카운트.json'],
             ['measure'], botsim_python)
        step(work, STAGE/'13-1_fox8재파싱.py', [STAGE/'13-1_fox8재파싱.json'])
    else:
        paths = [STAGE/'04_기능어측정.json', STAGE/'04-1_확장재파싱.json',
                 CONTROL/'입력코퍼스.json', CONTROL/'제한코퍼스_원카운트.json']
        write(work/CONTROL/'입력_실행전_해시.json',
              {str(p.relative_to('research')): sha(work/p) for p in paths})
    step(work, CONTROL/'test_fmr_controls.py', [])
    step(work, CONTROL/'fmr_controls.py', [CONTROL/'FMR_세통제_결과.json'], python=botsim_python)
    step(work, STAGE/'10-1_귀무오류율.py', [STAGE/'10-1_귀무오류율_1000회.json'], ['--reps','1000'])
    for script, output, args in [
        ('10_동질성검정.py', '10_동질성검정.json', []),
        ('11_판별기.py', '11_판별기.json', ['--overwrite']),
        ('12-3_판별기적용.py', '12_판별기적용.json', ['--overwrite']),
        ('13_fox8전이.py', '13_fox8전이.json', ['--overwrite']),
    ]:
        outputs = [STAGE/output]
        if script == '11_판별기.py':
            outputs.append(STAGE/'11_판별기_모델.joblib')
        step(work, STAGE/script, outputs, args)
    for check in ('check_results.py', 'check_artifacts.py'):
        subprocess.run([sys.executable, str(REPO/'scripts'/check), str(work)], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['prepare','verify','run','step'])
    ap.add_argument('--work', type=Path, default=REPO/'work')
    ap.add_argument('--mode', choices=['analysis','full'], default='analysis')
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--botsim-python', type=Path)
    ap.add_argument('--script', help='Relative to the experiment directory (step only)')
    ap.add_argument('--args', nargs=argparse.REMAINDER, default=[])
    a = ap.parse_args()
    work = a.work.expanduser().resolve()
    if a.command == 'prepare': prepare(work, a.download, a.mode)
    elif a.command == 'verify': verify(work)
    elif a.command == 'run': run(work, a.botsim_python.resolve() if a.botsim_python else None)
    else:
        if not a.script: ap.error('step requires --script')
        relative = STAGE/a.script
        if not (work/relative).resolve().is_relative_to(work/STAGE): ap.error('script outside experiment directory')
        execute(work, relative, a.args, a.botsim_python)


if __name__ == '__main__': main()
