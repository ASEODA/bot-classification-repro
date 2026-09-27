#!/usr/bin/env python3
"""Export recorded terminal slot rows as a readable dataset; never call an API.
Each row is a recorded generation slot, NOT automatically an eligible analysis document.
Retries/copy filtering/language filtering are specified in the study parser and account dictionaries.
"""
import argparse
import json
from pathlib import Path

def export(folder, output):
    output.parent.mkdir(parents=True,exist_ok=True)
    count=0
    with output.open('w',encoding='utf-8') as out:
        for path in sorted(folder.glob('호출기록_*.jsonl')):
            for line_number,line in enumerate(path.open(encoding='utf-8'),1):
                row=json.loads(line)
                if row.get('종류') != '슬롯':continue
                selected={'source_file':path.name,'source_line':line_number,
                          'slot_id':row.get('슬롯id'),'model':row.get('요청모델'),
                          'status':row.get('상태'),'post_id':row.get('게시물id'),
                          'post_time':row.get('게시물시각'),'comment':row.get('댓글'),
                          'settings_hash':row.get('설정해시')}
                out.write(json.dumps(selected,ensure_ascii=False)+'\n');count+=1
    print(json.dumps({'exported_slot_rows':count,'output':str(output)},ensure_ascii=False))
    return count

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();export(a.folder,a.output)
