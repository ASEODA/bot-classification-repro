#!/usr/bin/env python3
"""Check full account measurements, feature comparisons, scores and fold assignments."""
from pathlib import Path
import hashlib
import json
import math
import sys
import unicodedata

REPO = Path(__file__).resolve().parents[1]


def normalized(value):
    if isinstance(value, dict):
        return {unicodedata.normalize('NFC', k): normalized(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalized(v) for v in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        return round(value, 10)
    if isinstance(value, str):
        return unicodedata.normalize('NFC', value)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(normalized(value), ensure_ascii=False,
                                    sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def check(work):
    rows = json.loads((REPO/'scripts/manifests/expected_artifacts.json').read_text())
    stage = work/'research/단계별 진행경과'
    cache, results = {}, []
    for r in rows:
        if r['file'] not in cache:
            cache[r['file']] = json.loads((stage/r['file']).read_text())
        value = cache[r['file']]
        for key in r['keys']:
            value = value[key]
        got = digest(value)
        results.append({**r, 'actual': got, 'passed': got == r['sha256']})
    passed = all(r['passed'] for r in results)
    report = {'passed': passed, 'checks': results,
              'scope': 'All entries in selected account counts, feature tables, scores, splits and model coefficients; floats rounded to 10 decimals, text NFC. Timings and machine paths excluded.'}
    (work/'validation/artifact-comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('PASS' if passed else 'FAIL', f'{len(results)} detailed artifact comparisons')
    for row in results:
        if not row['passed']:
            print(row['file'], '/'.join(row['keys']))
    return passed


if __name__ == '__main__':
    sys.exit(not check(Path(sys.argv[1]).resolve()))
