"""한 진입점: fast(저장 측정값), full(원문 재측정), smoke(원문 3계정씩), verify."""
import sys
sys.dont_write_bytecode = True
import argparse
import gzip
import importlib.metadata
import json
import shutil
import subprocess
import tarfile
import time
import zipfile
from pathlib import Path
import numpy as np
import common as C


def inputs(mode):
    manifest = C.read_json(C.DATA / "manifest.json")
    checked = 0
    for rel,h in manifest["files"].items():
        if mode in ("fast", "verify") and rel.startswith("data/raw/"):
            continue
        p = C.ROOT / rel
        if not p.is_file():
            raise FileNotFoundError(f"자료 누락: {rel}. README의 데이터 준비 절차를 확인하세요.")
        C.check(C.sha256_file(p) == h, f"입력 해시 불일치: {rel}")
        checked += 1
    C.say(f"입력 무결성: {checked}개 파일 일치")


def prepare_fast():
    for name,path in C.TABLE.items():
        path.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(C.DATA/"features"/(name+".csv.gz"),"rb") as src, path.open("wb") as dst:
            shutil.copyfileobj(src,dst)


def unpack_raw():
    C.WORK.mkdir(parents=True,exist_ok=True)
    for name in ("botsim", "ud-ewt"):
        with zipfile.ZipFile(C.DATA/"raw"/(name+".zip")) as z:
            for f in z.namelist():
                C.check(C.WORK in (C.WORK/f).resolve().parents,"압축파일 경로 이탈")
            z.extractall(C.WORK)
    if not (C.STANZA_DIR/"resources.json").exists():
        with tarfile.open(C.DATA/"raw/stanza-models.tar.gz") as t:
            t.extractall(C.WORK,filter="data")
    if not C.FOX8_DB.exists():
        subprocess.run([sys.executable,str(C.ROOT/"code/import_fox8.py"),
                        str(C.DATA/"raw/fox8.ndjson.gz"),str(C.FOX8_DB)],check=True)


class Checks:
    def add(self,name,expected,actual,ok):
        C.check(ok,f"{name}: expected={expected}, actual={actual}")


def raw_features(limit=None):
    import features as F
    unpack_raw()
    src = F.full_parse(limit)
    schema = C.read_json(C.DATA/"records/schema.json")
    words,hash_ = C.funcword_list(src["raw_words"])
    C.check(words == schema["function_words"],"UD 목록 불일치")
    keys = schema["keys"]
    axis = schema["axis_map"]
    if limit is None:
        C.check(C.feature_keys(src["botsim"],words) == keys,"250자질 종류 불일치")
        C.check(C.build_axis_map(src["botsim"]) == axis,"M 분모 범주 불일치")
    order = C.feature_order(keys)
    trunc, _ = F.fox8_trunc(Checks(),src,limit=limit)
    src["fox8_trunc"] = trunc
    fox_sources = C.fox8_sources()
    compared = {}
    for name in C.TABLE:
        acc = src[name]
        ids = sorted(acc)
        if not ids:
            continue
        X = C.build_matrix(acc,ids,keys,axis)
        if name.startswith("fox8"):
            cols = ["라벨","자료원"]+C.META_COLS+["연도_중앙값","연도_최대","답글비율","문서수_2023"]
            info = {u:{"라벨":fox_sources[u][0],"자료원":fox_sources[u][1],
                       **{c:acc[u][c] for c in C.META_COLS},**F.fox8_caveat_cols(acc[u])} for u in ids}
        else:
            cols = ["라벨"]+C.META_COLS
            info = {u:{"라벨":src["labels"][u],**{c:acc[u][c] for c in C.META_COLS}} for u in ids}
        path = C.RESULTS/"raw_check"/(name+".csv") if limit else C.TABLE[name]
        C.write_table(path,ids,cols,info,order,X)
        # Compare measured values to the independently saved reference table, including missing cells.
        ref = C.WORK/("reference_"+name+".csv")
        with gzip.open(C.DATA/"features"/(name+".csv.gz"),"rb") as a, ref.open("wb") as b:
            shutil.copyfileobj(a,b)
        rids,rinfo,rorder,RX = C.read_table(ref)
        rpos = {u:i for i,u in enumerate(rids)}
        C.check(order == rorder and all(u in rpos for u in ids),f"{name} 행/열 불일치")
        expected = RX[[rpos[u] for u in ids]]
        C.check(np.array_equal(X,expected,equal_nan=True),f"{name} 원문 재측정값 불일치")
        for u in ids:
            for col in cols:
                C.check(info[u][col] == rinfo[col][rpos[u]],f"{name} {u} 메타데이터 {col} 불일치")
        if limit is None:
            C.check(ids == rids,f"{name} 전체 계정 불일치")
        compared[name] = len(ids)
    work,_ = F.full_fox8_corpus()
    exclusion = C.read_json(C.DATA/"records/excluded_fox8.json")
    flagged = sorted(u for u,docs in work.items() if any(
        s in C.normalize_apostrophe(t.lower()) for t,_ in docs for s in exclusion["strings"]))
    C.check(flagged == exclusion["uids"],"문구 제외 계정 재계산 불일치")
    C.write_json(C.RESULTS/"raw_check.json",{"mode":"smoke" if limit else "full",
                 "accounts_compared":compared,"all_features_exact":True,"excluded_accounts_exact":True})


def compare_tree(actual,expected,path="",failures=None):
    if failures is None: failures=[]
    if isinstance(expected,dict):
        if not isinstance(actual,dict): failures.append(path); return failures
        for k,v in expected.items():
            if k not in actual: failures.append(path+"/"+k+" missing")
            else: compare_tree(actual[k],v,path+"/"+k,failures)
    elif isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected): failures.append(path+" length")
        else:
            for i,(a,e) in enumerate(zip(actual,expected)): compare_tree(a,e,path+f"/{i}",failures)
    elif isinstance(expected,(int,float)) and not isinstance(expected,bool):
        if actual is None or not np.isclose(actual,expected,rtol=1e-10,atol=1e-10): failures.append(path)
    elif actual!=expected: failures.append(path)
    return failures


def verify():
    failures=[]
    for name in ("analysis","training","evaluation"):
        compare_tree(C.read_json(C.RESULTS/(name+".json")),
                     C.read_json(C.ROOT/"expected"/(name+".json")),name,failures)
    result={"passed":not failures,"differences":failures,"tolerance":1e-10}
    C.write_json(C.RESULTS/"verification.json",result)
    C.check(not failures,f"기준 결과 불일치 {len(failures)}개: {failures[:10]}")
    C.say("기준 결과 대조: 전체 일치")


def report(a,e):
    lines=["# 재현 결과", "", "## 판별 AUC", "", "| 자료 | L | G | 결합 |", "|---|---:|---:|---:|"]
    t=C.read_json(C.RESULTS/"training.json")
    lines.append(f"| BotSim 5겹 평가 | {t['auc']:.6f} | — | — |")
    main=e["집합"]["501"]
    for w,name in (("W0","fox8 확인"),("W1","중심 차이 제거"),("W2","퍼짐 차이 축소")):
        r=main[w]["AUC"]
        lines.append(f"| {name} | {r['L'][0]:.6f} | {r['G'][0]:.6f} | {r['S'][0]:.6f} |")
    d=main["W0"]["차"]["S−L"]
    lines += ["",f"결합 − L: {d[0]:.6f}, 95% 구간 [{d[1]:.6f}, {d[2]:.6f}]", "", "## 봇 비중을 줄인 확인 집합", "",
              "| 목표 봇 비중 | 평균 결합 AUC | 평균 결합 − L |", "|---|---:|---:|"]
    for name,rows in e["하위표집"].items():
        auc=np.mean([r["W0"]["AUC"]["S"][0] for r in rows])
        gain=np.mean([r["W0"]["차"]["S−L"][0] for r in rows])
        lines.append(f"| {name} | {auc:.6f} | {gain:.6f} |")
    lines += ["", "5%는 봇 24개·사람 449개이며 3회 중 한 구간이 0을 포함한다.",
              "자기폭로 유사 문구 제외 조건에서는 퍼짐 조작 관문을 통과하지 못했다.",
              "점수 고정 부트스트랩이며, fox8은 개발 이력이 있는 외부 확인 자료다.", "", "## FMR 차이와 동질성", ""]
    n=sum(r["주목"] for family in a["전체기준선"].values() for r in family.values())
    lines.append(f"전체 주목 특성: {n}/250")
    for name,r in a["요약"].items(): lines.append(f"- {name}: 기존 주목 중 {sum(v['효과유지'] for v in r.values())}개 효과 유지")
    for name,r in a["동질성"].items(): lines.append(f"- {name}: "+", ".join(f"{b} {v['비율']:.6f}" for b,v in r["블록별"].items()))
    lines += ["", "세부값: analysis.json / training.json / evaluation.json", "검증: verification.json", ""]
    C.write_text(C.RESULTS/"summary.md","\n".join(lines))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode",nargs="?",choices=("fast","full","smoke","verify"),default="fast")
    mode=ap.parse_args().mode
    C.RESULTS.mkdir(exist_ok=True)
    inputs(mode)
    if mode=="verify": verify(); return
    started=time.time()
    if mode=="fast": prepare_fast()
    else:
        raw_features(limit=3 if mode=="smoke" else None)
        if mode=="smoke":
            C.say("원문 부분 재측정 검증 완료. 전량 재측정 완료를 뜻하지 않습니다.")
            return
    import analysis, train, evaluation
    a=analysis.run()
    b=train.run(a)
    e=evaluation.run(b)
    verify()
    report(a,e)
    C.write_json(C.RESULTS/"run.json",{"mode":mode,"finished":C.now(),"seconds":time.time()-started,
                 "python":sys.version,"packages":{k:importlib.metadata.version(k) for k in
                                                     ("numpy","scipy","scikit-learn","joblib")}})
    C.say("완료:",C.RESULTS/"summary.md")


if __name__=="__main__":
    main()
