#!/usr/bin/env python3
"""완료 후 결과·노트·원본 보존을 대조한다. 기존 파일은 읽기만 한다."""
import sys
sys.dont_write_bytecode = True
import csv
import hashlib
import json
import math
import re
import statistics
import unicodedata
from datetime import datetime
from pathlib import Path
from fmr_prepare_measure import HERE, STEP, ROOT, read, save, sha


def run():
    d=read(HERE/'FMR_세통제_결과.json')
    measured=read(HERE/'제한코퍼스_원카운트.json')
    inputs=read(HERE/'입력코퍼스.json')
    expanded=read(STEP/'04-1_확장재파싱.json')['계정']
    original=read(STEP/'01_적격계정.json')['계정']
    checks={}
    checks['세조건']=set(d['통제'])=={'분량매칭','댓글한정','politics한정'}
    checks['파싱정합']=measured['정합검사']['통과']
    checks['기준선재현']=read(HERE/'기준선_재현점검.json')['통과']
    checks['표본수']=d['표본']=={'전체':{'bot':646,'human':1223},'분량매칭':{'bot':512,'human':512},
                              '댓글한정':{'bot':562,'human':874},'politics한정':{'bot':290,'human':705}}
    checks['자질규모']=all({f:len(rs) for f,rs in rows.items()}=={'F':172,'M형태':58,'M품사':17,'R':3}
                          for rows in d['통제'].values())
    old_hashes=read(HERE/'기존파일_보존해시.json')
    changes=[p for p,h in old_hashes.items() if sha(ROOT/p)!=h]
    checks['기존파일보존']=not changes
    # 새 문장 길이 목록 자체의 정합: 제한해도 글이 전혀 바뀌지 않은 계정은 옛 목록과 같아야 한다.
    length_checks={};length_mismatches=[]
    for name in ('comments','politics'):
        n=0
        for uid,a in measured['계정'][name].items():
            assert len(a['문장길이'])==a['문장수'] and sum(a['문장길이'])==a['토큰수_구두점제외']
            if inputs[name][uid]==original[uid]:
                n+=1
                if a['문장길이']!=expanded[uid]['문장길이']:
                    length_mismatches.append((name,uid))
        length_checks[name]=n
    checks['동일원문_문장길이재현']=not length_mismatches and sum(length_checks.values())>0
    checks['구두점단조변환']=all(rows['M품사']['PUNCT']['U']==rows['R']['구두점_비율']['U']
                                  for rows in [d['전체기준선'],*d['통제'].values()])
    with (HERE/'FMR_세통제_전체자질.csv').open(encoding='utf-8-sig',newline='') as f:
        records=list(csv.DictReader(f))
    checks['CSV1000행']=len(records)==1000
    checks['CSV셀대조']=True
    for row in records:
        source=d['전체기준선'] if row['조건']=='전체기준선' else d['통제'][row['조건']]
        result=source[row['블록']][row['자질']]
        for k in ('U','p','q','델타','봇_중앙','사람_중앙'):
            if result[k] is None:
                checks['CSV셀대조'] &= row[k]==''
            else:
                checks['CSV셀대조'] &= float(row[k])==result[k]
    names={unicodedata.normalize('NFC',p.stem) for p in ROOT.rglob('*.md')}
    missing_links=[];bad_placeholders=[]
    notes=list(HERE.glob('*.md'))
    for p in notes:
        text=p.read_text();body=text.split('---',2)[2]
        for target in re.findall(r'\[\[([^\]]+)\]\]',body):
            target=target.split('|')[0].split('#')[0]
            if target and unicodedata.normalize('NFC',target) not in names:
                missing_links.append([p.name,target])
        if re.search(r'__[A-Z_]+__',text):bad_placeholders.append(p.name)
    checks['노트5개']=len(notes)==5
    checks['내부링크']=not missing_links
    checks['치환누락없음']=not bad_placeholders
    output={'검증일':datetime.now().astimezone().isoformat(),'통과':all(checks.values()),'항목':checks,
            '보존검사파일수':len(old_hashes),'기존파일변경':changes,
            '동일원문_문장길이비교계정수':length_checks,'문장길이불일치':length_mismatches,
            '깨진링크':missing_links,'치환누락':bad_placeholders}
    save(HERE/'최종_QA.json',output)
    print(json.dumps(output,ensure_ascii=False,indent=2))
    assert output['통과']


if __name__=='__main__':
    run()
