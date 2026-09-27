#!/usr/bin/env python3
"""F·M·R 세 통제 재검증. 기존 파일은 읽기만 한다.
실행: arch -arm64 /usr/local/bin/python3 -u fmr_controls.py [--baseline-only]
기준선 및 분량 통제는 저장 카운트 재계산, 댓글/politics는 새 재파싱 결과 사용.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import math
import statistics
from collections import Counter
from datetime import datetime

import numpy as np
import scipy
from scipy.stats import mannwhitneyu, binomtest, false_discovery_control
from fmr_prepare_measure import HERE, STEP, ROOT, read, save, sha, module

FAMILIES = ('F','M형태','M품사','R')
RKEYS = ('문장당_토큰수','구두점_비율','문장길이_변동계수')
CONDITIONS = ('분량매칭','댓글한정','politics한정')


def bh(ps):
    m = len(ps)
    order = sorted(range(m), key=ps.__getitem__)
    qs, running = [1.0]*m, 1.0
    for rank in range(m,0,-1):
        i = order[rank-1]
        running = min(running, ps[i]*m/rank)
        qs[i] = running
    if ps:
        assert np.allclose(qs,false_discovery_control(np.asarray(ps,dtype=float),method='bh'),rtol=1e-12,atol=1e-15)
    return qs


def mw(x,y):
    """순위·동점 보정은 독립 계산, SciPy의 안정적인 p값과 전 항목 교차 검산."""
    if not x or not y:
        return {'U':None,'p':None,'델타':None,'z':None}
    nx,ny = len(x),len(y)
    n = nx+ny
    indexed = sorted([(v,0) for v in x]+[(v,1) for v in y])
    rank_sum, tie_sum, i = 0.0, 0.0, 0
    while i < n:
        j = i+1
        while j<n and indexed[j][0] == indexed[i][0]:
            j += 1
        rank_sum += ((i+1+j)/2)*sum(group==0 for _,group in indexed[i:j])
        t = j-i
        tie_sum += t**3-t
        i = j
    u = rank_sum-nx*(nx+1)/2
    variance = nx*ny/12*((n+1)-tie_sum/(n*(n-1)))
    difference = u-nx*ny/2
    if variance > 0:
        zabs = max(0.0,abs(difference)-0.5)/math.sqrt(variance)
        z = math.copysign(zabs,difference)
        p = math.erfc(zabs/math.sqrt(2))
    else:
        z,p = 0.0,1.0
    check = mannwhitneyu(x,y,alternative='two-sided',method='asymptotic',use_continuity=True)
    assert u == check.statistic
    assert math.isclose(p,check.pvalue,rel_tol=1e-9,abs_tol=1e-300), (p,check.pvalue)
    return {'U':u,'p':p,'델타':2*u/(nx*ny)-1,'z':z}


def summary(values):
    if not values:
        return {'Q1':None,'중앙':None,'Q3':None,'IQR':None}
    if len(values)==1:
        q1=med=q3=values[0]
    else:
        q1,med,q3 = statistics.quantiles(values,n=4,method='inclusive')
    return {'Q1':q1,'중앙':med,'Q3':q3,'IQR':q3-q1}


def rhythm(a):
    w,t,n = a['토큰수_구두점제외'],a['토큰수'],a['문장수']
    lengths = a['문장길이']
    assert len(lengths)==n and sum(lengths)==w
    mean = w/n if n else None
    return {RKEYS[0]:mean,RKEYS[1]:(t-w)/t if t else None,
            RKEYS[2]:statistics.stdev(lengths)/mean if n>=5 and mean>0 else None}


def vectors(accounts, keys, axes, m07):
    mr,_,_ = m07.compute_ratios(accounts,keys['M형태'],axes)
    pr,_ = m07.compute_upos_ratios(accounts,keys['M품사'])
    fs,rs = {},{}
    for uid,a in accounts.items():
        w=a['토큰수_구두점제외']
        fs[uid]={k:round(a['기능어'].get(k,0)/w,6) if w else None for k in keys['F']}
        rs[uid]=rhythm(a)
    return {'F':fs,'M형태':mr,'M품사':pr,'R':rs}


def compare(vec, keys, labels, ids=None):
    ids = sorted(ids if ids is not None else vec['F'])
    result={}
    for family in FAMILIES:
        rows={}
        for k in keys[family]:
            x=[vec[family][u][k] for u in ids if labels[u]=='bot' and vec[family][u][k] is not None]
            y=[vec[family][u][k] for u in ids if labels[u]=='human' and vec[family][u][k] is not None]
            row=mw(x,y)
            sx,sy=summary(x),summary(y)
            row.update({'봇_n':len(x),'사람_n':len(y),'결측':len(ids)-len(x)-len(y),
                        '봇_중앙':sx['중앙'],'사람_중앙':sy['중앙'],
                        '봇_IQR':sx['IQR'],'사람_IQR':sy['IQR'],
                        'IQR비':sx['IQR']/sy['IQR'] if sy['IQR'] and sx['IQR'] is not None else None})
            rows[k]=row
        # 사전에 정한 가족 크기를 유지. 검정 불가 항목은 p=1로 보정에만 포함.
        qs=bh([v['p'] if v['p'] is not None else 1.0 for v in rows.values()])
        for row,q in zip(rows.values(),qs):
            row['q']=q if row['p'] is not None else None
            row['주목']=row['p'] is not None and q<=.05 and abs(row['델타'])>=.147
        result[family]=rows
    return result


def add_reference(result, baseline):
    for fam,rows in result.items():
        for key,row in rows.items():
            ref=baseline[fam][key]
            d,b=row['델타'],ref['델타']
            row['기준선_델타']=b
            row['기준선_주목']=ref['주목']
            row['델타변화']=d-b if d is not None and b is not None else None
            row['효과유지']=bool(ref['주목'] and d is not None and b*d>0 and abs(d)>=.147)
            if not ref['주목']:
                status='신규주목' if row['주목'] else '기준선비주목'
            elif d is None:
                status='검정불가'
            elif b*d<0:
                status='방향역전'
            elif abs(d)<.147:
                status='효과문턱미달'
            else:
                status='효과유지'
            row['효과판정']=status


def paired_sign(vec,keys,pairs):
    result={}
    for fam in FAMILIES:
        rows={}
        for key in keys[fam]:
            ds=[vec[fam][b][key]-vec[fam][h][key] for b,h,_ in pairs
                if vec[fam][b][key] is not None and vec[fam][h][key] is not None]
            pos=sum(d>0 for d in ds);neg=sum(d<0 for d in ds)
            p=float(binomtest(pos,pos+neg,.5).pvalue) if pos+neg else 1.0
            rows[key]={'양의차이':pos,'음의차이':neg,'동점':len(ds)-pos-neg,
                       '결측쌍':len(pairs)-len(ds),'쌍내차이_중앙':statistics.median(ds) if ds else None,'p':p}
        for row,q in zip(rows.values(),bh([r['p'] for r in rows.values()])):
            row['q']=q
        result[fam]=rows
    return result


def balance(accounts, labels, ids):
    out={}
    for key in ['토큰수_구두점제외','문서수','문장수']:
        out[key]={lab:summary([accounts[u][key] for u in ids if labels[u]==lab]) for lab in ('bot','human')}
    b=[math.log(accounts[u]['토큰수_구두점제외']) for u in ids if labels[u]=='bot']
    h=[math.log(accounts[u]['토큰수_구두점제외']) for u in ids if labels[u]=='human']
    den=math.sqrt((statistics.variance(b)+statistics.variance(h))/2)
    out['log분모_SMD']=(statistics.mean(b)-statistics.mean(h))/den if den else None
    return out


def summarize(rows):
    return {f:{'자질수':len(rs),'주목':sum(x['주목'] for x in rs.values()),
               '기준선주목':sum(x.get('기준선_주목',False) for x in rs.values()),
               '효과유지':sum(x.get('효과유지',False) for x in rs.values()),
               '판정':dict(Counter(x.get('효과판정','기준선') for x in rs.values()))} for f,rs in rows.items()}


def punct_check(rows):
    a,b=rows['M품사']['PUNCT'],rows['R']['구두점_비율']
    assert a['U']==b['U'] and a['델타']==b['델타'], 'PUNCT 단조변환 순위 불일치'
    return True


def save_csv(path,results):
    output=[]
    for condition, rows in results.items():
        for fam,features in rows.items():
            for key,row in features.items():
                output.append({'조건':condition,'블록':fam,'자질':key,**row})
    columns=list(dict.fromkeys(k for row in output for k in row))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns)
        writer.writeheader();writer.writerows(output)


def run(baseline_only=False):
    m07=module(STEP/'07_형태자질비교.py','legacy07')
    m08=module(STEP/'09-1_분량통제.py','legacy08')
    d04=read(STEP/'04_기능어측정.json')['계정']
    d13=read(STEP/'04-1_확장재파싱.json')['계정']
    d07=read(STEP/'07_형태자질비교.json')
    labels=read(STEP/'01_적격계정.json')['라벨']
    inputs=read(HERE/'입력코퍼스.json')
    keys={'F':inputs['function_words'],'M형태':sorted(d07['형태자질']),
          'M품사':sorted(d07['UPOS']),'R':list(RKEYS)}
    assert [len(keys[f]) for f in FAMILIES]==[172,58,17,3]
    assert set(d04)==set(d13) and len(d04)==1869
    assert all(labels[u] in ('bot','human') for u in d04)
    accounts={u:{**a,'문장길이':d13[u]['문장길이']} for u,a in d04.items()}
    axes=m07.build_axis_map(accounts)
    basevec=vectors(accounts,keys,axes,m07)
    base=compare(basevec,keys,labels)
    punct_check(base)
    old={'F':read(STEP/'06_비교결과.json')['단어별'],'M형태':d07['형태자질'],
         'M품사':d07['UPOS'],'R':read(STEP/'08_R블록.json')['자질별']}
    baseline_diffs=[]
    for fam in FAMILIES:
        for k,row in base[fam].items():
            ref=old[fam][k]
            if row['U']!=ref['U'] or row['주목']!=ref['주목']:
                baseline_diffs.append({'블록':fam,'자질':k,'new_U':row['U'],'old_U':ref['U'],
                                       'new_notable':row['주목'],'old_notable':ref['주목']})
    save(HERE/'기준선_재현점검.json',{'통과':not baseline_diffs,'차이':baseline_diffs,
                                    '안정적p재계산':True,'블록요약':summarize(base)})
    assert not baseline_diffs, '기준선 재현 차이 확인 필요'
    bots=sorted(u for u in accounts if labels[u]=='bot')
    humans=sorted(u for u in accounts if labels[u]=='human')
    logs={u:math.log(a['토큰수_구두점제외']) for u,a in accounts.items() if a['토큰수_구두점제외']>0}
    pairs,dropped,used=m08.caliper_match([u for u in bots if u in logs],
                                       [u for u in humans if u in logs],logs,.1,20260827)
    assert [[b,h] for b,h,g in pairs] == read(STEP/'09-1_분량통제.json')['매칭']['쌍목록']
    assert len(pairs)==512
    matched_ids=sorted({u for b,h,g in pairs for u in (b,h)})
    matched=compare(basevec,keys,labels,matched_ids)
    add_reference(matched,base);punct_check(matched)
    metadata={'executed_at':datetime.now().astimezone().isoformat(),
              'scipy':scipy.__version__,'numpy':np.__version__,'script_sha256':sha(__file__),
              'axis_map_fixed_to_baseline':axes,'planned_families':{f:len(keys[f]) for f in FAMILIES},
              'label_usage':'후속 라벨 사용 분석. 무라벨 실험/외부 검증 아님.',
              'matching':{'seed':20260827,'caliper_log':.1,'pairs':pairs,'unmatched_bots':dropped,
                          'unmatched_humans':sorted(set(humans)-used),
                          'balance_before':balance(accounts,labels,list(accounts)),
                          'balance_after':balance(accounts,labels,matched_ids)},
              'method':'Mann–Whitney U asymptotic two-sided, tie/continuity correction; Cliff delta bot minus human; BH per fixed family; stable erfc tails.'}
    output={'설정':metadata,'전체기준선':base,'통제':{'분량매칭':matched},
            '동일계정_제한전':{},'매칭쌍_부호검정':paired_sign(basevec,keys,pairs),
            '표본':{'전체':dict(Counter(labels[u] for u in accounts)),
                    '분량매칭':dict(Counter(labels[u] for u in matched_ids))},'분모규칙_재유도시차이':{}}
    if baseline_only:
        save(HERE/'분량통제_선행결과.json',output)
        print('기준선 250종 U·주목 일치; 512 매칭쌍 재현; 분량 통제 완료',flush=True)
        print('R:',matched['R'],flush=True)
        return output
    measured=read(HERE/'제한코퍼스_원카운트.json')
    assert measured['정합검사']['통과'], '재파싱 원카운트 불일치: 자동 분석 중단'
    for name,source in [('댓글한정','comments'),('politics한정','politics')]:
        restricted=measured['계정'][source]
        assert set(restricted)==set(inputs[source])
        vec=vectors(restricted,keys,axes,m07)
        rows=compare(vec,keys,labels)
        add_reference(rows,base);punct_check(rows)
        output['통제'][name]=rows
        output['동일계정_제한전'][name]=compare(basevec,keys,labels,restricted)
        output['표본'][name]=dict(Counter(labels[u] for u in restricted))
        selected_axes=m07.build_axis_map(restricted)
        changes={k:{'fixed':m07.denom_kind_of(k,axes),'rederived':m07.denom_kind_of(k,selected_axes)}
                 for k in keys['M형태'] if m07.denom_kind_of(k,axes)!=m07.denom_kind_of(k,selected_axes)}
        output['분모규칙_재유도시차이'][name]=changes
    pooled=[row for name in CONDITIONS for fam in FAMILIES for row in output['통제'][name][fam].values()]
    assert len(pooled)==750
    for row,q in zip(pooled,bh([r['p'] if r['p'] is not None else 1.0 for r in pooled])):
        row['q_세통제750']=q if row['p'] is not None else None
        row['주목_세통제750']=row['p'] is not None and q<=.05 and abs(row['델타'])>=.147
    output['요약']={name:summarize(rows) for name,rows in output['통제'].items()}
    # 기존 결과와 수치 차이를 전부 기록. F 반올림/고정 분모 차이는 노트에서 별도 해석.
    older={'분량매칭':read(STEP/'09-1_분량통제.json'),
           '댓글한정':read(STEP/'09-2_게시물유형통제.json'),
           'politics한정':read(STEP/'09-3_서브레딧통제.json')['표본A']}
    audit=[]
    for name in CONDITIONS:
        for fam,oldkey in [('F','기능어' if name=='politics한정' else 'F블록'),('M형태','형태자질'),('M품사','UPOS')]:
            for k,row in output['통제'][name][fam].items():
                oldrow=older[name][oldkey][k]
                olddelta=oldrow.get('08델타',oldrow.get('델타'))  # '08델타'는 09-1_분량통제.json에 옛 번호로 남은 키 이름
                if olddelta is not None and row['델타'] is not None and abs(row['델타']-olddelta)>0.000051:
                    audit.append({'조건':name,'블록':fam,'자질':k,'old_delta':olddelta,'new_delta':row['델타']})
    output['기존통제_델타차이']=audit
    hashes=read(HERE/'입력_실행전_해시.json')
    changed=[path for path,h in hashes.items() if sha(ROOT/path)!=h]
    assert not changed, ('실행 중 입력 변경',changed)
    output['입력해시_검증']=True
    save(HERE/'FMR_세통제_결과.json',output)
    save_csv(HERE/'FMR_세통제_전체자질.csv',{'전체기준선':base,**output['통제']})
    print('세 통제 완료',output['표본'],flush=True)
    print(json_text(output['요약']),flush=True)
    return output


def json_text(obj):
    import json
    return json.dumps(obj,ensure_ascii=False,indent=2)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-only',action='store_true')
    run(p.parse_args().baseline_only)
