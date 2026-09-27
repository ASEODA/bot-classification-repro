#!/usr/bin/env python3
"""Compare numerical results against the shared reference, not timestamps/file bytes."""
from pathlib import Path
import json
import math
import sys

REPO=Path(__file__).resolve().parents[1]

def collect(stage):
    read=lambda name: json.loads((stage/name).read_text(encoding='utf-8'))
    out={}
    control=read('09_FMR 통제 재검증/FMR_세통제_결과.json')
    out['samples']=control['표본']
    out['control_summary']=control['요약']
    hom=read('10_동질성검정.json')
    out['homogeneity_BotSim']={b:hom['블록별'][b]['비율'] for b in ('F','M','R')}
    j11=read('11_판별기.json')
    out['BotSim_AUC']={k:v['AUC'] for k,v in j11['표'].items()}
    out['BotSim_LR_confusion']=j11['표']['위치']['OOF']['혼동']
    j12=read('12_판별기적용.json')
    out['OpenRouter_AUC']={batch:{k:v['AUC'] for k,v in row['도구'].items()} for batch,row in j12['적용'].items()}
    j13=read('13_fox8전이.json')
    out['fox8_AUC']={k:v['AUC'] for k,v in j13['시험c_판별기전이']['표'].items()}
    out['fox8_adapted_confusion']={k:v['문턱적응_fox8']['OOF']['혼동'] for k,v in j13['시험c_판별기전이']['표'].items() if '문턱적응_fox8' in v}
    out['homogeneity_fox8']={b:j13['시험b_동질성전이']['블록별'][b]['비율'] for b in ('F','M','R')}
    return out

def compare(a,b,path=''):
    if isinstance(b,dict):
        if not isinstance(a,dict) or set(a)!=set(b): return [path+': keys differ']
        return [err for k in b for err in compare(a[k],b[k],path+'/'+k)]
    if isinstance(b,(int,float)):
        return [] if math.isclose(a,b,abs_tol=1e-10,rel_tol=1e-9) else [f'{path}: {a} != {b}']
    return [] if a==b else [path+': differs']

if __name__=='__main__':
    work=Path(sys.argv[1]).resolve()
    actual=collect(work/'research/단계별 진행경과')
    expected=json.loads((REPO/'scripts/manifests/expected_metrics.json').read_text(encoding='utf-8'))
    errors=compare(actual,expected)
    report={'passed':not errors,'differences':errors,'metrics':actual,
            'scope':'Numerical summaries only; historical timestamps and machine paths are not compared.'}
    (work/'validation/result-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS' if not errors else 'FAIL', 'numerical result comparison')
    if errors:
        print('\n'.join(errors[:20]));sys.exit(1)
