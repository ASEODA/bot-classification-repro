#!/usr/bin/env python3
"""09번 FMR 통제 재검증: 기존 규칙으로 코퍼스를 재구성하고 제한된 글을 재측정한다.
macOS 실행: arch -arm64 /usr/local/bin/python3 -u fmr_prepare_measure.py prepare|measure
기존 파일에는 쓰지 않는다. 중간 캐시도 삭제하지 않고 재개에 사용한다.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import importlib.util
import json
import platform
import sqlite3
import statistics
import time
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEP, ROOT = HERE.parent, HERE.parent.parent
SCALARS = ('문서수', '문장수', '토큰수', '토큰수_구두점제외')
COUNTS = ('기능어', 'UPOS', '자질')


def locate(directory, name):
    return next(p for p in directory.iterdir() if unicodedata.normalize('NFC', p.name) == name)


def read(path):
    return json.loads(Path(path).read_text())


def save(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False))
    tmp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def prepare():
    target = HERE / '입력코퍼스.json'
    if target.exists():
        raise FileExistsError('입력코퍼스가 이미 있습니다. 기존 준비 결과를 덮어쓰지 않습니다.')
    m01 = module(locate(STEP, '01_botsim_적격검열.py'), 'legacy01')
    m10 = module(STEP / '09-2_게시물유형통제.py', 'legacy10')
    m13 = module(STEP / '04-1_확장재파싱.py', 'legacy13')
    raw_path = locate(ROOT, '1. 원본데이터') / '2. BotSim Data/BotSim-24-Dataset/user_post_comment.json'
    d01 = read(STEP / '01_적격계정.json')
    original, labels = d01['계정'], d01['라벨']
    m10.POSTS_JSON = str(raw_path)
    raw_split = m10.load_raw_split(set(original))
    comments, funnel, lang_info = m10.build_comment_corpus(raw_split, labels)
    old_comments = read(STEP / '09-2_게시물유형통제.json')['계정']
    assert set(comments) == set(old_comments), '댓글 적격 계정 불일치'
    assert all(len(comments[u]) == old_comments[u]['문서수'] for u in comments)
    raw = read(raw_path)
    politics = {}
    for uid in sorted(original):
        rebuilt = m13.rebuild_docs(raw[uid], m01)
        assert [text for text, sub in rebuilt] == original[uid], ('원문 복원 불일치', uid)
        docs = [text for text, sub in rebuilt if sub == 'politics']
        if len(docs) >= 10:
            politics[uid] = docs
    d13 = read(STEP / '04-1_확장재파싱.json')['계정']
    expected = {u for u,a in d13.items() if a['서브레딧별'].get('politics',{}).get('문서수',0) >= 10}
    assert set(politics) == expected and len(expected) == 995
    words = sorted({x.lower().replace('’', "'") for x in read(STEP/'02_기능어목록.json')['기능어']})
    assert len(words) == 172
    inputs = {'created_at': datetime.now().astimezone().isoformat(), 'function_words': words,
              'comments': comments, 'politics': politics, 'comment_funnel': funnel,
              'comment_language': lang_info,
              'label_usage': '기존 결과 열람 후 후속 분석. 댓글 깔때기 집계 및 비교에 라벨 사용; 파서 입력에는 미사용.'}
    save(target, inputs)
    sources = [raw_path, locate(STEP,'01_botsim_적격검열.py'), STEP/'01_적격계정.json',
               STEP/'02_기능어목록.json', STEP/'04_기능어측정.json', STEP/'05_사용률검수.json',
               STEP/'06_비교결과.json', STEP/'07_형태자질비교.json',
               STEP/'07_형태자질비교.py', STEP/'09-1_분량통제.json',
               STEP/'09-1_분량통제.py', STEP/'09-2_게시물유형통제.json', STEP/'09-2_게시물유형통제.py',
               STEP/'04-1_확장재파싱.json', STEP/'04-1_확장재파싱.py', STEP/'09-3_서브레딧통제.json',
               STEP/'08_R블록.json', target, Path(__file__), HERE/'09번 FMR 통제 재검증 실행 전 고정 계획.md']
    save(HERE/'입력_실행전_해시.json', {str(p.relative_to(ROOT)): sha(p) for p in sources})
    print('준비 완료:', {k: (len(inputs[k]),sum(map(len,inputs[k].values()))) for k in ('comments','politics')}, flush=True)


def doc_counts(doc, words):
    a = {k: 0 for k in SCALARS}
    a.update({k: Counter() for k in COUNTS})
    a['문서수'] = 1
    a['문장길이'] = []
    for sent in doc.sentences:
        length = 0
        a['문장수'] += 1
        for w in sent.words:
            a['토큰수'] += 1
            a['UPOS'][w.upos] += 1
            if w.upos != 'PUNCT':
                length += 1
                a['토큰수_구두점제외'] += 1
            surface = w.text.lower().replace('’', "'")
            if surface in words:
                a['기능어'][surface] += 1
            for feature in (w.feats or '').split('|'):
                if feature:
                    a['자질'][feature] += 1
        a['문장길이'].append(length)
    return a


def combine(rows):
    a = {k: sum(x[k] for x in rows) for k in SCALARS}
    for k in COUNTS:
        c = Counter()
        for x in rows:
            c.update(x[k])
        a[k] = dict(c)
    a['문장길이'] = [v for x in rows for v in x['문장길이']]
    assert len(a['문장길이']) == a['문장수']
    assert sum(a['문장길이']) == a['토큰수_구두점제외']
    assert sum(a['UPOS'].values()) == a['토큰수']
    assert a['UPOS'].get('PUNCT',0) == a['토큰수']-a['토큰수_구두점제외']
    return a


def differences(actual, expected):
    return {k: {'new': actual.get(k), 'old': expected.get(k)}
            for k in SCALARS+COUNTS if actual.get(k) != expected.get(k)}


def measure():
    import stanza
    import torch
    from stanza.resources.common import DEFAULT_MODEL_DIR
    # CPU 기본값 8 threads 유지. 모델 다운로드/업데이트는 금지한다.
    assert stanza.__version__ == '1.14.0'
    inputs = read(HERE/'입력코퍼스.json')
    words = set(inputs['function_words'])
    nlp = stanza.Pipeline(lang='en', processors='tokenize,pos', use_gpu=False,
                          verbose=False, download_method=None)
    model_paths = sorted({str(v) for k,v in nlp.config.items() if k.endswith('_path') and Path(str(v)).is_file()})
    config = {'stanza': stanza.__version__, 'torch': torch.__version__, 'python': platform.python_version(),
              'machine': platform.machine(), 'cpu_threads': torch.get_num_threads(),
              'input_sha256': sha(HERE/'입력코퍼스.json'), 'code_sha256': sha(__file__),
              'models': {p:sha(p) for p in model_paths}, 'processors': list(nlp.processors),
              'created_at': inputs['created_at']}
    conn = sqlite3.connect(HERE/'문서파싱_캐시.sqlite3')
    conn.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS docs (hash TEXT PRIMARY KEY, counts TEXT NOT NULL)')
    old_meta = conn.execute("SELECT value FROM meta WHERE key='config'").fetchone()
    if old_meta:
        assert json.loads(old_meta[0]) == config, '캐시와 실행 환경/입력/코드가 다름'
    else:
        conn.execute('INSERT INTO meta VALUES (?,?)', ('config',json.dumps(config,sort_keys=True)))
        conn.commit()
    save(HERE/'파싱환경.json',config)
    old_comments = read(STEP/'09-2_게시물유형통제.json')['계정']
    old_expanded = read(STEP/'04-1_확장재파싱.json')['계정']
    results = {'comments':{},'politics':{}}
    mismatches = {'comments':{},'politics':{}}
    uids = sorted(set(inputs['comments']) | set(inputs['politics']))
    started = time.monotonic()
    parsed_count = 0
    for index,uid in enumerate(uids,1):
        # 동일 문서는 재사용하되, 집계는 조건별 원래 목록(중복 포함)으로 한다.
        texts = list(dict.fromkeys(inputs['comments'].get(uid,[])+inputs['politics'].get(uid,[])))
        hashes = {t:hashlib.sha256(t.encode()).hexdigest() for t in texts}
        counts, pending = {}, []
        for text in texts:
            row = conn.execute('SELECT counts FROM docs WHERE hash=?',(hashes[text],)).fetchone()
            if row:
                counts[text] = json.loads(row[0])
            else:
                pending.append(text)
        if pending:
            parsed = nlp.bulk_process(pending)
            assert len(parsed) == len(pending)
            for text,doc in zip(pending,parsed):
                a = doc_counts(doc,words)
                counts[text] = a
                conn.execute('INSERT INTO docs VALUES (?,?)',(hashes[text],json.dumps(a,ensure_ascii=False)))
            conn.commit()
            parsed_count += len(pending)
        for condition in results:
            docs = inputs[condition].get(uid)
            if docs is None:
                continue
            a = combine([counts[t] for t in docs])
            results[condition][uid] = a
            old = old_comments[uid] if condition == 'comments' else old_expanded[uid]['서브레딧별']['politics']
            diff = differences(a,old)
            if diff:
                mismatches[condition][uid] = diff
        if index == 1 or index % 25 == 0 or index == len(uids):
            elapsed = time.monotonic()-started
            print(f'{index}/{len(uids)} 계정 · 새 파싱 {parsed_count}문서 · {elapsed/60:.1f}분 · 불일치 '+str({k:len(v) for k,v in mismatches.items()}),flush=True)
            save(HERE/'측정진행.json', {'completed_accounts':index, 'total_accounts':len(uids),
                 'newly_parsed_docs':parsed_count, 'elapsed_seconds':elapsed,
                 'mismatch_counts':{k:len(v) for k,v in mismatches.items()},
                 'updated_at':datetime.now().astimezone().isoformat()})
    conn.close()
    save(HERE/'제한코퍼스_원카운트.json', {'환경':config, '계정':results,
         '정합검사':{'통과':not any(mismatches.values()), '불일치':mismatches},
         'completed_at':datetime.now().astimezone().isoformat()})
    print('측정 완료; 정합 검사', '통과' if not any(mismatches.values()) else '실패 — 차이 원인 확인 필요',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','measure'])
    args = parser.parse_args()
    {'prepare':prepare,'measure':measure}[args.stage]()
