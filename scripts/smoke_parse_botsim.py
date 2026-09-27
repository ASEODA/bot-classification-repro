#!/usr/bin/env python3
"""Parse one bot and one human account with the original measurement code and compare counts."""
from pathlib import Path
import importlib.util
import json
import os
import sys

work=Path(sys.argv[1]).resolve()
os.environ['STANZA_RESOURCES_DIR']=str(work/'models/stanza')
os.environ['HF_HUB_OFFLINE']='1'
sys.dont_write_bytecode=True
stage=work/'research/단계별 진행경과'
spec=importlib.util.spec_from_file_location('measurement',stage/'04_기능어측정.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
read=lambda name:json.loads((stage/name).read_text(encoding='utf-8'))
source=read('01_적격계정.json');reference=read('04_기능어측정.json')['계정']
words=set(m.normalize_apostrophe(w.lower()) for w in read('02_기능어목록.json')['기능어'])
ids=[next(uid for uid in sorted(source['계정']) if source['라벨'][uid]==label) for label in ['bot','human']]
nlp=m.build_pipeline();checks={}
for uid in ids:
    measured=m.measure_account(nlp,source['계정'][uid],words)
    checks[uid]={'label':source['라벨'][uid],'documents':len(source['계정'][uid]),'equal':measured==reference[uid]}
report={'passed':all(r['equal'] for r in checks.values()),'accounts':checks,'scope':'two complete accounts; not a full-corpus parse'}
(work/'validation/botsim-parser-smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False));sys.exit(0 if report['passed'] else 1)
