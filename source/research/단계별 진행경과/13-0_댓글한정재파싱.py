#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
13-0_댓글한정재파싱.py
────────────────────────────────────────────────────────────────────────────
한계 먼저
    · 이 파일은 비교에 쓸 계정 사전을 만들 뿐 판정을 하지 않는다. 표 (a)·판별기
      ver.2는 이 사전을 읽는 뒤 단계가 한다.
    · 생성 모델 칸(새 모델 4개, gpt-4o-mini 재생성)은 아직 없다. 생성이 끝나면
      같은 함수로 이 사전에 덧붙인다(뼈대 v3 5절 1항). 이번 실행은 사람 874,
      원 봇 509, 완전 모방기 509 세 집단만 만든다.
    · 완전 모방기 문서에는 시각이 없다(12 결정 AC). 뼈대 5절 1항은 "BotSim 지연
      규칙으로 시각 부여"를 적었지만 이번에는 계획일 문자열을 정렬 키로 쓴다(D3).
      계정당 슬롯이 최대 101건이라 최근 200건 상한이 걸리지 않으므로 문서 집합은
      시각 부여 방식과 무관하다. 달라지는 것은 파서에 넣는 순서뿐이다.
    · 문장 경계는 stanza 토크나이저가 정한다. 문장 길이 목록은 그 경계를 그대로
      믿은 값이다(12-0과 같다).

목적
    12(OpenRouter 생성) 5절 분석은 사람, 원 봇, 귀무 행을 모두 "댓글 한정" 문서로
    같은 파서에 통과시킨 계정 단위 측정치를 필요로 한다. 09-2는 사람과 봇의
    댓글(comment_1 + comment_2)을 쟀지만 원 봇 참고 행은 1차 댓글만, 복사 슬롯
    제외여야 하고, 완전 모방기는 새로 만든 문서다. 문장 길이 목록도 09-2에는 없다.

대상 집단 셋 (집단 열)
    사람        09-2 계정 가운데 Users.csv 라벨 human 874. 문서 = comment_1 +
                comment_2 본문. 역할 열 = 분할.json 사람 역할(표a·시험·학습).
                판별기 시험 234는 "봉인" 표시.
    원봇        분할.json 페르소나 509의 원 uid. 문서 = comment_1 본문만. 복사 슬롯
                (대장의 원봇복사슬롯 열, 또는 본문 = 대상 게시물 제목)은 뺀다.
    완전모방기  ~/DM_LAB_data/12_OpenRouter/완전모방기_문서.jsonl (uid 접두 MIM_).
    세 집단 모두 09-2와 같은 정제·적격 규칙: 01 clean_doc(자기폭로 문장 절제,
    URL·멘션 제거, 20자 미만 탈락) → 시각 오름차순(안정 정렬) → 최근 200건 →
    10건 이상 → 계정 단위 langid "en".

측정 (12-0 measure_account 재사용)
    stanza tokenize,pos · use_gpu=False · 계정 단위 bulk_process. 계정별 라벨·
    문서수·문장수·토큰수·토큰수_구두점제외·구두점토큰수·문장길이 목록·기능어·
    UPOS·자질(+ 진단용 버킷별).

관문
    G1 함수 동일성: clean_doc = 01 = 12-0, aggregate·measure_account·
       normalize_apostrophe = 12-0 (docstring 뺀 AST 비교). 기능어 172종 해시.
    G2 입력 사슬: 분할.json 입력sha256(원본 JSON, Users.csv, 01 py, 09-2 JSON)과
       준비 요약의 산출sha256(분할, 대장, 완전 모방기)이 지금 파일과 같다.
    G3 집단 구성: 사람 874·역할 표a 640/시험 234/학습 234, 페르소나 509 ⊂ 09-2
       봇, 대장 원댓글id = 원 봇 comment_1 전부, 완전 모방기 슬롯 = 대장 "프롬프트
       있음" 슬롯, 세 집단 uid 교집합 0.
    G4 사람 문서 선택 재현: 파싱 전, 사람 계정별 문서수가 09-2와 모두 같다.
    G5 12-0 정합: 12-0 JSON 첫 계정을 fox8 sqlite에서 12-0과 같은 쿼리·힙 규칙으로
       다시 짓고 같은 함수로 재어 모든 필드가 같다.
    G6 손 대조: 집단마다 계정 2개(합 6), 계정마다 문서 2개를 nlp(문서)로 따로 돌린
       문장수·구두점 제외 토큰수 = bulk 결과. 계정 합계도 독립 코드로 다시 센다.
       본 측정 뒤에 그 6계정의 본 측정치가 관문 때 값과 같은지(결정성) 본다.
    G7 내부 관계(전 계정): len(문장길이) = 문장수 · sum(문장길이) =
       토큰수_구두점제외 · 구두점토큰수 = 토큰수 − 토큰수_구두점제외 = UPOS PUNCT.
    G8 사람 09-2 대조(파싱 뒤): 계정별 문장수·토큰수가 09-2와 같다. 어긋난 계정이
       1%를 넘으면 실패(12-0과 같은 문턱).
    관문 검사는 assert 문이 아니라 check()로 한다. python -O에서도 꺼지지 않는다.

라벨 규율
    라벨은 Users.csv에서 읽는다. 쓰는 곳은 (1) 사람 집단 정의(과제 규격이 라벨로
    정의), (2) 원 봇 509가 bot인지 확인, (3) 결과 파일 저장. 로그에 [라벨 사용]을
    단다. 문서 선택·정제·파싱에는 들어가지 않는다.

구현 결정 (규격에 없어 이 파일을 쓰며 정한 것, JSON 설정에도 적는다)
    D1. langid는 09-2처럼 적격 판정의 마지막 단계로 세 집단 모두에 건다.
    D2. 복사 슬롯 = 대장 원봇복사슬롯 True(근거 "대상 제목"·"다른 게시물 제목")
        ∪ norm_text(본문) = norm_text(대상 게시물 제목). 자극 없음 슬롯은 원 봇
        댓글이 있으므로 원봇에 넣는다.
    D3. 완전 모방기 정렬 키 = 계획일 문자열, 동률은 파일 순서(= 슬롯 순서).
    D4. 버킷 키: 사람 "comment_1"/"comment_2", 원봇 "comment_1", 모방기 "모방".
        aggregate를 12-0과 같은 코드로 두려고 키를 넘긴다. 진단용이다.
    D5. stanza.Pipeline에 download_method=None을 준다(네트워크 금지). 모델
        파일은 12-0과 같은 기본 위치에서 읽고 경로를 12-0 JSON과 대조한다.
    D6. 손 대조 계정·문서는 시드 20260926 random으로 고른다. smoke에서는
        smoke 대상 안에서 고른다.
    D7. 완전 모방기 라벨 = "bot"(표 (a)에서 봇 쪽 행을 맡는 가상 계정). 본문은
        모방 풀 사람의 원문이다.
    D8. 중간 저장 파일은 산출 JSON과 같은 폴더(볼트 밖)에 둔다. 재개 지문 =
        기능어 해시 + 코퍼스 해시 + 측정 함수 AST 해시 + stanza 버전.

실행
    python -u 13-0_댓글한정재파싱.py                      ← 본 실행
    python -u 13-0_댓글한정재파싱.py --smoke --out-dir D  ← 집단마다 5계정, D에 산출
    venv: /Users/son/.claude/venvs/audio-transcribe/bin/python (stanza 1.14.0)

산출
    ~/DM_LAB_data/12_OpenRouter/13-0_계정사전.json          계정별 측정치(대용량)
    ~/DM_LAB_data/12_OpenRouter/13-0_계정사전_진행.json     중간 저장. 끝나면 지운다.
    단계별 진행경과/13-0_댓글한정재파싱_요약.json            집단별 수, 관문, 해시
    단계별 진행경과/13-0_댓글한정재파싱_출력.log            화면 출력
"""

import argparse
import ast
import csv
import functools
import hashlib
import heapq
import json
import os
import platform
import random
import re
import sqlite3
import statistics
import sys
import tempfile
import time
import unicodedata
from collections import Counter

print = functools.partial(print, flush=True)


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ════════════════════════════════════════════════════════════════════════
# [경로] 모두 NFC로 둔다
# ════════════════════════════════════════════════════════════════════════
SCRIPT_PATH = nfc(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPT_PATH)              # …/연구주제/단계별 진행경과
ROOT = os.path.dirname(HERE)                     # …/연구주제
BOTSIM_DIR = f"{ROOT}/1. 원본데이터/2. BotSim Data/BotSim-24-Dataset"
POSTS_JSON = f"{BOTSIM_DIR}/user_post_comment.json"
USERS_CSV = f"{BOTSIM_DIR}/Users.csv"
PY01 = f"{HERE}/01_botsim_적격검열.py"
FUNCWORDS_JSON = f"{HERE}/02_기능어목록.json"
J092 = f"{HERE}/09-2_게시물유형통제.json"
PREP_DIR = f"{HERE}/12_OpenRouter생성_준비"
SPLIT_JSON = f"{PREP_DIR}/분할.json"
LEDGER_JSONL = f"{PREP_DIR}/프롬프트대장.jsonl"
PREP_SUMMARY = f"{PREP_DIR}/요약.json"
ARCH_DIR = f"{ROOT}/# 07-12 실행분 보관 (미학습)/2026-09-26 시뮬레이션 10-12 (탐색, 미학습)"
PY120 = f"{ARCH_DIR}/12-0_fox8재파싱.py"
J120 = f"{ARCH_DIR}/12-0_fox8재파싱.json"
FOX8_DB = f"{ROOT}/1. 원본데이터/3. fox8 Data/fox8_23_dataset.sqlite"
DATA_DIR = nfc(os.path.expanduser("~/DM_LAB_data/12_OpenRouter"))
MIMIC_JSONL = f"{DATA_DIR}/완전모방기_문서.jsonl"

ap = argparse.ArgumentParser()
ap.add_argument("--smoke", action="store_true", help="집단마다 5계정만")
ap.add_argument("--out-dir", default=None, help="smoke 산출 폴더(기본: 임시 폴더)")
ARGS = ap.parse_args()
SMOKE = ARGS.smoke
if SMOKE:
    OUT_DIR = nfc(os.path.abspath(ARGS.out_dir)) if ARGS.out_dir else nfc(tempfile.mkdtemp(prefix="13-0_smoke_"))
    OUT_JSON = f"{OUT_DIR}/13-0_계정사전_smoke.json"
    PROGRESS_JSON = f"{OUT_DIR}/13-0_계정사전_smoke_진행.json"
    SUMMARY_JSON = f"{OUT_DIR}/13-0_댓글한정재파싱_요약_smoke.json"
else:
    if ARGS.out_dir:
        sys.exit("--out-dir는 --smoke와만 씁니다. 본 실행 산출 위치는 고정입니다.")
    OUT_JSON = f"{DATA_DIR}/13-0_계정사전.json"
    PROGRESS_JSON = f"{DATA_DIR}/13-0_계정사전_진행.json"
    SUMMARY_JSON = f"{HERE}/13-0_댓글한정재파싱_요약.json"


# ════════════════════════════════════════════════════════════════════════
# [설정]
# ════════════════════════════════════════════════════════════════════════
MIN_CHARS = 20          # [01] 정제 후 20자 미만 문서는 버린다
MIN_DOCS = 10           # [01] 적격 문서 10건 미만 계정 제외
MAX_DOCS = 200          # [01] 계정당 최근 200건
LANG_TARGET = "en"      # [01] 계정 단위 langid

SELF_REVEAL = re.compile(
    r"(as an ai language model"
    r"|i'?m sorry,? but (i cannot|as an ai)"
    r"|i cannot (comply|fulfill|browse)"
    r"|openai'?s? (content )?polic)", re.I)
RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
RE_URL = re.compile(r"(https?://\S+|www\.\S+)")
RE_MENTION = re.compile(r"@\w+")
RE_WS = re.compile(r"\s+")

SEED = 20260926
CHECKPOINT_EVERY = 100
SMOKE_N = 5
HAND_ACCOUNTS = 2
HAND_DOCS = 2
GATE_MAX_FRAC = 0.01
EXPECTED_FW_HASH = "382b68572f03bc23"
GROUPS = ("사람", "원봇", "완전모방기")
MS_LOW, MS_HIGH = 9.86, 89.0     # 12-0 실측, 09-2 재파싱 실측 (ms/문서)


# ════════════════════════════════════════════════════════════════════════
# [도구]
# ════════════════════════════════════════════════════════════════════════
class GateError(RuntimeError):
    pass


def check(cond, msg):
    """관문 판정. assert와 달리 python -O에서도 꺼지지 않는다."""
    if not cond:
        raise GateError(msg)


def line(title=""):
    print("\n" + "═" * 74)
    if title:
        print(title)
        print("═" * 74)


def write_json(path, obj, indent=None):
    """임시 파일에 쓰고 fsync 뒤 이름을 바꾼다. 중간에 멈춰도 이전 것 아니면 새 것."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def fmt_dur(sec):
    if sec < 90:
        return f"{sec:.0f}초"
    if sec < 5400:
        return f"{sec / 60:.1f}분"
    return f"{sec / 3600:.2f}시간"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    return nfc(os.path.relpath(path, ROOT)) if path.startswith(ROOT) else path


# ════════════════════════════════════════════════════════════════════════
# [1] 정제 (01 clean_doc 그대로. G1이 AST로 확인한다)
# ════════════════════════════════════════════════════════════════════════
def clean_doc(text):
    """
    글 1건을 정제한다. [01_botsim_적격검열.py에서 가져옴, 12-0과 같음]
    통과하면 (정제 문자열, None, 절제여부), 탈락하면 (None, 사유, 절제여부).
    순서: 자기폭로 문장 절제 → URL·멘션 제거 → 길이 검사.
    """
    if not text:
        return None, "빈 문자열", False
    t = unicodedata.normalize("NFC", str(text))

    # (1) 자기폭로 문장만 도려내기
    excised = False
    if SELF_REVEAL.search(t):
        sents = RE_SENT_SPLIT.split(t)
        kept = [s for s in sents if s.strip() and not SELF_REVEAL.search(s)]
        t = " ".join(kept)
        excised = True
        if not t.strip():
            return None, "자기폭로 절제 후 내용 없음", True

    # (2) 링크·멘션 제거
    t = RE_URL.sub(" ", t)
    t = RE_MENTION.sub(" ", t)
    t = RE_WS.sub(" ", t).strip()

    # (3) 길이 검사
    if len(t) < MIN_CHARS:
        reason = ("자기폭로 절제 후 " if excised else "") + f"{MIN_CHARS}자 미만"
        return None, reason, excised
    return t, None, excised


def norm_text(s):
    """복사 슬롯 대조용: NFC + 공백 정규화. [12_OpenRouter생성.py 결정 AA와 같음]"""
    return " ".join(unicodedata.normalize("NFC", str(s or "")).split())


# ════════════════════════════════════════════════════════════════════════
# [2] 집계 (12-0 aggregate·measure_account 그대로. G1이 AST로 확인한다)
# ════════════════════════════════════════════════════════════════════════
def normalize_apostrophe(s):
    """굽은 아포스트로피(’)를 곧은 것(')으로. [12-0에서 가져옴]"""
    return s.replace("’", "'")


def aggregate(parsed, keys, funcword_set):
    """
    파싱된 문서 목록(한 계정분)을 받아 저장할 값 한 벌을 만든다. [12-0에서 가져옴]
      토큰        sent.words 의 원소 하나 (MWT 분해 뒤의 낱말 단위)
      구두점      UPOS == "PUNCT"
      문장 길이   문장마다 구두점을 뺀 토큰수 (08 정의)
      기능어      소문자 + 아포스트로피 정규화 표면형이 172종 목록에 있으면 1회
      자질        feats 문자열을 "|"로 끊어 "키=값" 단위로 센다
    """
    fw, upos, feats = Counter(), Counter(), Counter()
    buckets = {}
    sent_lens = []
    n_sent = n_tok = n_nopunct = n_punct = 0

    for doc, key in zip(parsed, keys):
        b = buckets.get(key)
        if b is None:
            b = buckets[key] = [0, 0, 0, 0]  # 문서수·문장수·토큰수·구두점제외
        b[0] += 1
        for sent in doc.sentences:
            n_sent += 1
            b[1] += 1
            sent_len = 0
            for w in sent.words:
                n_tok += 1
                b[2] += 1
                upos[w.upos] += 1
                if w.upos == "PUNCT":
                    n_punct += 1
                else:
                    n_nopunct += 1
                    b[3] += 1
                    sent_len += 1
                surface = normalize_apostrophe(w.text.lower())
                if surface in funcword_set:
                    fw[surface] += 1
                if w.feats:
                    for kv in w.feats.split("|"):
                        feats[kv] += 1
            sent_lens.append(sent_len)

    return {
        "문서수": len(parsed),
        "문장수": n_sent,
        "토큰수": n_tok,
        "토큰수_구두점제외": n_nopunct,
        "구두점토큰수": n_punct,
        "문장길이": sent_lens,
        "기능어": dict(fw.most_common()),
        "UPOS": dict(upos.most_common()),
        "자질": dict(feats.most_common()),
        "버킷별": {k: buckets[k] for k in sorted(buckets)},
    }


def measure_account(nlp, docs, keys, funcword_set):
    """계정 하나를 계정 단위 bulk_process로 파싱해 집계한다. [12-0에서 가져옴]"""
    parsed = nlp.bulk_process(docs)
    return aggregate(parsed, keys, funcword_set)


# 12-0 fox8 정합(G5)에만 쓰는 두 함수. [12-0에서 가져옴]
def year_of(created_at):
    s = (created_at or "")[:4]
    return s if len(s) == 4 and s.isdigit() else "?"


def bucket_key(year, is_reply):
    return f"{year}|{1 if is_reply else 0}"


def relations_ok(a):
    """G7 내부 관계."""
    return (len(a["문장길이"]) == a["문장수"]
            and sum(a["문장길이"]) == a["토큰수_구두점제외"]
            and a["구두점토큰수"] == a["토큰수"] - a["토큰수_구두점제외"]
            and a["구두점토큰수"] == a["UPOS"].get("PUNCT", 0))


# ════════════════════════════════════════════════════════════════════════
# [3] 관문 G1: 함수 동일성
# ════════════════════════════════════════════════════════════════════════
def func_ast(src, name):
    """소스에서 함수 name의 AST를 docstring을 빼고 문자열로. 없으면 None."""
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            body = n.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                n.body = body[1:]
            return ast.dump(n)
    return None


def gate_function_identity():
    me = open(SCRIPT_PATH, encoding="utf-8").read()
    s01 = open(PY01, encoding="utf-8").read()
    s120 = open(PY120, encoding="utf-8").read()
    pairs = [("clean_doc", "01", s01), ("clean_doc", "12-0", s120),
             ("aggregate", "12-0", s120), ("measure_account", "12-0", s120),
             ("normalize_apostrophe", "12-0", s120),
             ("year_of", "12-0", s120), ("bucket_key", "12-0", s120)]
    rows = []
    for name, where, src in pairs:
        a, b = func_ast(me, name), func_ast(src, name)
        same = a is not None and a == b
        rows.append({"함수": name, "대상": where, "같음": same})
        print(f"      {name:<22} = {where:<5} {'같음' if same else '다름'}")
    # 정제 상수도 같아야 한다(함수 밖에 있으므로 따로 본다).
    for const in ("MIN_CHARS = 20", "MIN_DOCS = 10", "MAX_DOCS = 200",
                  'RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\\s+|\\n+")',
                  'RE_URL = re.compile(r"(https?://\\S+|www\\.\\S+)")',
                  'RE_MENTION = re.compile(r"@\\w+")', 'RE_WS = re.compile(r"\\s+")'):
        same = const in s01 and const in me
        rows.append({"상수": const, "01과같음": same})
        check(same, f"정제 상수가 01과 다릅니다: {const}")
    sr = re.compile(r"SELF_REVEAL = re\.compile\((.*?)re\.I\)", re.S)
    m01, mme = sr.search(s01), sr.search(me)
    strip = lambda m: re.sub(r"#[^\n]*", "", m.group(1)).split() if m else None
    same_sr = strip(m01) is not None and strip(m01) == strip(mme)
    rows.append({"상수": "SELF_REVEAL", "01과같음": same_sr})
    print(f"      정제 상수(MIN_CHARS·MIN_DOCS·MAX_DOCS·정규식 5개) = 01  "
          f"{'같음' if same_sr else '다름'}")
    check(all(r.get("같음", r.get("01과같음")) for r in rows),
          "함수 또는 상수가 01·12-0과 다릅니다.")
    code_hash = sha16("\n".join(func_ast(me, n) for n in
                                ("clean_doc", "normalize_apostrophe", "aggregate", "measure_account")))
    return rows, code_hash


# ════════════════════════════════════════════════════════════════════════
# [4] 문서 선택 (09-2 build_comment_corpus와 같은 순서)
# ════════════════════════════════════════════════════════════════════════
def select_group(accounts):
    """
    accounts: {uid: [(본문, 정렬키, 버킷키), ...]} (원본 순서).
    09-2와 같은 순서로 정제 → 정렬키 오름차순 안정 정렬 → 최근 MAX_DOCS건 →
    MIN_DOCS건 이상 → 계정 단위 langid en.
    반환: (work {uid: [(정제문, 버킷키), ...]}, 깔때기)
    """
    import langid
    drop = Counter()
    n_in = n_trim = n_exc = n_exc_kept = 0
    short, cand = [], {}
    for uid in sorted(accounts):
        rows = []
        for text, ts, key in accounts[uid]:
            n_in += 1
            cleaned, reason, excised = clean_doc(text)
            if excised:
                n_exc += 1
            if cleaned is None:
                drop[reason] += 1
                continue
            if excised:
                n_exc_kept += 1
            rows.append((ts, cleaned, key))
        rows.sort(key=lambda r: r[0])
        if len(rows) > MAX_DOCS:
            n_trim += len(rows) - MAX_DOCS
            rows = rows[-MAX_DOCS:]
        if len(rows) >= MIN_DOCS:
            cand[uid] = [(c, k) for _, c, k in rows]
        else:
            short.append({"uid": uid, "정제후문서수": len(rows)})
    work, nonen, langs = {}, [], Counter()
    for uid in sorted(cand):
        lang, _ = langid.classify(" ".join(c for c, _ in cand[uid]))
        langs[lang] += 1
        if lang == LANG_TARGET:
            work[uid] = cand[uid]
        else:
            nonen.append({"uid": uid, "lang": lang})
    funnel = {
        "대상계정수": len(accounts),
        "원본문서수": n_in,
        "문서탈락_사유별": dict(drop.most_common()),
        "문서탈락_합": sum(drop.values()),
        "자기폭로_절제문서수": n_exc,
        "자기폭로_절제후_생존문서수": n_exc_kept,
        "상한초과_절삭문서수": n_trim,
        "문서부족_탈락계정수": len(short),
        "문서부족_탈락계정": short,
        "언어판정_대상계정수": len(cand),
        "언어별_계정수": dict(langs.most_common()),
        "비영어_탈락계정수": len(nonen),
        "비영어_탈락계정": nonen,
        "적격계정수": len(work),
        "적격문서수": sum(len(v) for v in work.values()),
    }
    return work, funnel


# ════════════════════════════════════════════════════════════════════════
# [5] 관문 G5: 12-0 정합 (fox8 1계정)
# ════════════════════════════════════════════════════════════════════════
def fox8_account_docs(target):
    """
    12-0 build_fox8_corpus의 선택 규칙을 계정 하나에 적용한다. 쿼리는 글자까지
    같게 두고 전체를 흘린다(같은 스캔 순서). 힙 키 (시각못읽음, created_at, 순번)의
    순번은 12-0에서 전역 통과 순번이지만, 한 계정 안의 상대 순서는 스캔 순서와
    같으므로 계정 안 순번으로 바꿔도 뽑히는 200건과 순서가 같다.
    """
    conn = sqlite3.connect(f"file:{FOX8_DB}?mode=ro", uri=True)
    heap, seq = [], 0
    for uid, created, text, is_reply in conn.execute(
            "SELECT user_id, created_at, text, is_reply FROM tweets "
            "WHERE is_retweet = 0"):
        if not uid or str(uid) != target:
            continue
        cleaned, _, _ = clean_doc(text)
        if cleaned is None:
            continue
        yr = year_of(created)
        item = ((1 if yr == "?" else 0), created or "", seq, cleaned, bucket_key(yr, is_reply))
        seq += 1
        if len(heap) < MAX_DOCS:
            heapq.heappush(heap, item)
        else:
            heapq.heappushpop(heap, item)
    conn.close()
    items = sorted(heap)
    return [c for _, _, _, c, _ in items], [k for _, _, _, _, k in items]


def gate_12_0(nlp, funcword_set, old_rec, uid):
    docs, keys = fox8_account_docs(uid)
    got = measure_account(nlp, docs, keys, funcword_set)
    fields = ["문서수", "문장수", "토큰수", "토큰수_구두점제외", "구두점토큰수",
              "문장길이", "기능어", "UPOS", "자질", "버킷별"]
    rows = {f: (got[f] == old_rec[f]) for f in fields}
    for f in fields:
        a, b = got[f], old_rec[f]
        show = (f"{a} / {b}" if not isinstance(a, (list, dict))
                else f"{len(a)}항목 / {len(b)}항목")
        print(f"      {f:<16} 재계산 / 12-0  {show}  {'같음' if rows[f] else '다름'}")
    return {"계정": uid, "필드별_같음": rows, "통과": all(rows.values()),
            "문서수": got["문서수"], "문장수": got["문장수"],
            "토큰수_구두점제외": got["토큰수_구두점제외"]}


# ════════════════════════════════════════════════════════════════════════
# [6] 관문 G6: 손 대조
# ════════════════════════════════════════════════════════════════════════
def hand_counts(doc):
    """aggregate와 별개의 코드로 문장수·구두점 제외 토큰수를 센다."""
    return (len(doc.sentences),
            sum(1 for s in doc.sentences for w in s.words if w.upos != "PUNCT"))


def gate_hand(nlp, funcword_set, work, group_of):
    rng = random.Random(SEED)
    rows, expect = [], {}
    for g in GROUPS:
        uids = sorted(u for u in work if group_of[u] == g)
        for uid in rng.sample(uids, min(HAND_ACCOUNTS, len(uids))):
            texts = [t for t, _ in work[uid]]
            keys = [k for _, k in work[uid]]
            parsed = nlp.bulk_process(texts)
            agg = aggregate(parsed, keys, funcword_set)
            # 계정 합계를 독립 코드로 다시 센다
            hs = [hand_counts(d) for d in parsed]
            tot_ok = (sum(h[0] for h in hs) == agg["문장수"]
                      and sum(h[1] for h in hs) == agg["토큰수_구두점제외"])
            idx = sorted(rng.sample(range(len(texts)), min(HAND_DOCS, len(texts))))
            for i in idx:
                single = hand_counts(nlp(texts[i]))
                bulk = hs[i]
                ok = single == bulk
                rows.append({"집단": g, "계정": uid, "문서순번": i, "글자수": len(texts[i]),
                             "단독_문장수": single[0], "단독_구두점제외토큰수": single[1],
                             "bulk_문장수": bulk[0], "bulk_구두점제외토큰수": bulk[1],
                             "같음": ok})
                print(f"      {g:<6} {uid:<14} 문서 {i:>3} ({len(texts[i]):>5}자)  단독 {single} · "
                      f"bulk {bulk}  {'같음' if ok else '다름'}")
                check(ok, f"손 대조 실패: {g} {uid} 문서 {i} 단독 {single} ≠ bulk {bulk}")
            print(f"      {g:<6} {uid:<14} 계정 합계 독립 재셈 = aggregate  "
                  f"{'같음' if tot_ok else '다름'}")
            check(tot_ok, f"손 대조 실패: {uid} 계정 합계가 aggregate와 다릅니다.")
            check(relations_ok(agg), f"손 대조 실패: {uid} 내부 관계 위반.")
            expect[uid] = agg
    return rows, expect


# ════════════════════════════════════════════════════════════════════════
# [7] 중간 저장·재개
# ════════════════════════════════════════════════════════════════════════
def load_progress():
    if not os.path.exists(PROGRESS_JSON):
        return None
    return json.load(open(PROGRESS_JSON, encoding="utf-8"))


def save_progress(done, fp, elapsed):
    write_json(PROGRESS_JSON, {
        "안내": "13-0 중간 저장. 측정이 끝나면 자동으로 지웁니다.",
        "지문": fp, "완료계정수": len(done), "누적소요초": round(elapsed, 1),
        "저장시각": time.strftime("%Y-%m-%d %H:%M:%S"), "계정": done})


def run_measurement(nlp, work, order, funcword_set, fp, group_of):
    done, prev = {}, 0.0
    prog = load_progress()
    if prog:
        if prog.get("지문") != fp:
            print(f"■ 중단: 중간 저장 지문이 다릅니다.\n  저장: {prog.get('지문')}\n  지금: {fp}")
            print(f"  기준이 다른 수치를 이어 붙이지 않습니다. {PROGRESS_JSON} 을(를) 지우고 다시 실행하십시오.")
            sys.exit(1)
        done, prev = prog["계정"], prog.get("누적소요초", 0.0)
        print(f"      중간 저장 발견: 완료 {len(done):,}계정 (누적 {fmt_dur(prev)}). 이어서 합니다.")
    else:
        print("      중간 저장 없음. 처음부터 시작합니다.")
    todo = [u for u in order if u not in done]
    todo_docs = sum(len(work[u]) for u in todo)
    print(f"      남은 계정 {len(todo):,} · 문서 {todo_docs:,}건 · 예상 "
          f"{fmt_dur(todo_docs * MS_LOW / 1000)}({MS_LOW} ms/문서) ~ "
          f"{fmt_dur(todo_docs * MS_HIGH / 1000)}({MS_HIGH} ms/문서)")
    t0 = time.time()
    docs_run = 0
    per_group = {g: [0, 0.0] for g in GROUPS}
    for i, uid in enumerate(todo, 1):
        ta = time.time()
        items = work[uid]
        a = measure_account(nlp, [t for t, _ in items], [k for _, k in items], funcword_set)
        check(relations_ok(a), f"내부 관계 위반: {uid}")
        done[uid] = a
        docs_run += len(items)
        per_group[group_of[uid]][0] += len(items)
        per_group[group_of[uid]][1] += time.time() - ta
        if i % CHECKPOINT_EVERY == 0 or i == len(todo):
            el = time.time() - t0
            save_progress(done, fp, prev + el)
            left = (todo_docs - docs_run) * el / max(docs_run, 1)
            print(f"      {len(done):,}/{len(order):,} 계정 · 경과 {fmt_dur(el)} · "
                  f"{el / max(docs_run, 1) * 1000:.1f} ms/문서 · 잔여 추정 {fmt_dur(left)} · 저장")
    run_sec = time.time() - t0
    return done, run_sec, prev + run_sec, per_group


# ════════════════════════════════════════════════════════════════════════
# [8] 본 흐름
# ════════════════════════════════════════════════════════════════════════
def main():
    t_start = time.time()
    run_info = {
        "실행시각": time.strftime("%Y-%m-%d %H:%M:%S"),
        "스크립트": rel(SCRIPT_PATH),
        "스크립트_sha256": file_sha256(SCRIPT_PATH),
        "sys.flags.optimize": sys.flags.optimize,
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}",
        "smoke": SMOKE,
        "경로_NFC": all(p == nfc(p) for p in (SCRIPT_PATH, OUT_JSON, SUMMARY_JSON, PROGRESS_JSON)),
    }
    line("13-0 댓글 한정 재파싱: 사람 874 · 원 봇 509 · 완전 모방기 509 (뼈대 v3 5절 1항)")
    for k, v in run_info.items():
        print(f"  {k}: {v}")
    print(f"  산출 {OUT_JSON}\n  요약 {SUMMARY_JSON}\n  중간 저장 {PROGRESS_JSON}")
    gates = {}
    summary = {"안내": "13-0 댓글 한정 재파싱 요약. 계정별 측정치는 산출.계정사전 경로(볼트 밖).",
               "상태": "시작", "실행": run_info}

    def dump_summary(state):
        summary["상태"] = state
        summary["관문"] = gates
        write_json(SUMMARY_JSON, summary, indent=1)

    # ── [0/7] 입력 확인과 사슬 ─────────────────────────────────
    line("[0/7] 입력 확인 · sha256 · 입력 사슬(G2)")
    inputs = {"원본JSON": POSTS_JSON, "Users.csv": USERS_CSV, "01_py": PY01,
              "02_기능어": FUNCWORDS_JSON, "09-2_JSON": J092, "분할.json": SPLIT_JSON,
              "프롬프트대장.jsonl": LEDGER_JSONL, "준비_요약.json": PREP_SUMMARY,
              "완전모방기_문서.jsonl": MIMIC_JSONL, "12-0_py": PY120, "12-0_JSON": J120,
              "fox8_sqlite": FOX8_DB}
    in_sha = {}
    for name, p in inputs.items():
        check(os.path.exists(p), f"입력 없음: {p}")
        in_sha[name] = file_sha256(p)
        print(f"      {name:<22} {in_sha[name][:16]}…  {rel(p)}")
    summary["입력"] = {k: {"경로": rel(p), "sha256": in_sha[k]} for k, p in inputs.items()}

    split_all = json.load(open(SPLIT_JSON, encoding="utf-8"))
    prep_sum = json.load(open(PREP_SUMMARY, encoding="utf-8"))
    chain = {}
    sp_in = split_all["입력sha256"]
    for key, name in [("1. 원본데이터/2. BotSim Data/BotSim-24-Dataset/user_post_comment.json", "원본JSON"),
                      ("1. 원본데이터/2. BotSim Data/BotSim-24-Dataset/Users.csv", "Users.csv"),
                      ("단계별 진행경과/01_botsim_적격검열.py", "01_py"),
                      ("단계별 진행경과/09-2_게시물유형통제.json", "09-2_JSON")]:
        chain[f"분할.입력sha256[{name}]"] = sp_in.get(key) == in_sha[name]
    chain["준비요약[분할.json]"] = prep_sum["산출sha256"]["분할.json"] == in_sha["분할.json"]
    chain["준비요약[프롬프트대장.jsonl]"] = prep_sum["산출sha256"]["프롬프트대장.jsonl"] == in_sha["프롬프트대장.jsonl"]
    chain["준비요약[완전모방기_문서.jsonl]"] = (prep_sum["볼트밖_산출"]["완전모방기_문서.jsonl"]["sha256"]
                                         == in_sha["완전모방기_문서.jsonl"])
    for k, v in chain.items():
        print(f"      사슬 {k:<40} {'같음' if v else '다름'}")
    gates["G2_입력사슬"] = {"항목": chain, "통과": all(chain.values())}
    check(all(chain.values()), "입력 사슬이 끊겼습니다(12 준비 산출과 지금 입력이 다름).")

    # ── [1/7] 함수 동일성 · 기능어 ─────────────────────────────
    line("[1/7] 함수 동일성(G1): 01·12-0과 docstring 뺀 AST 비교")
    fn_rows, code_hash = gate_function_identity()
    funcwords = json.load(open(FUNCWORDS_JSON, encoding="utf-8"))["기능어"]
    funcwords = sorted({normalize_apostrophe(w) for w in funcwords})
    funcword_set = set(funcwords)
    fw_hash = sha16("\n".join(funcwords))
    print(f"      기능어 {len(funcwords)}종 · 해시 {fw_hash} (12-0 {EXPECTED_FW_HASH})")
    check(fw_hash == EXPECTED_FW_HASH and len(funcwords) == 172, "기능어 목록이 12-0과 다릅니다.")
    gates["G1_함수동일성"] = {"행": fn_rows, "측정코드_해시": code_hash,
                          "기능어_해시": fw_hash, "기능어_개수": len(funcwords), "통과": True}

    # ── [2/7] 집단 구성 ──────────────────────────────────────
    line("[2/7] 집단 구성(G3)")
    data = json.load(open(POSTS_JSON, encoding="utf-8"))
    labels = {}
    with open(USERS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels[row["user_id"]] = "bot" if (row.get("character_setting") or "").strip() else "human"
    acc092 = json.load(open(J092, encoding="utf-8"))["계정"]
    humans = sorted(u for u in acc092 if labels.get(u) == "human")
    print(f"      [라벨 사용] 09-2 계정 {len(acc092):,} 가운데 Users.csv 라벨 human {len(humans)} (집단 정의)")
    check(len(humans) == 874, f"사람 수 {len(humans)} ≠ 874")

    sp = split_all["분할"]
    roles = {r["uid"]: r["역할"] for r in sp["사람"]["역할표"]}
    role_cnt = Counter()
    for u in humans:
        r = roles.get(u)
        check(r is not None and "모방" not in r and set(r) <= {"표a", "시험", "학습"},
              f"사람 {u}의 역할이 이상합니다: {r}")
        for x in r:
            role_cnt[x] += 1
    print(f"      사람 역할 {dict(role_cnt)}")
    check(dict(role_cnt) == {"표a": 640, "시험": 234, "학습": 234}, "사람 역할 수가 3절과 다릅니다.")

    personas = sp["페르소나"]
    bots = [p["원봇uid"] for p in personas]
    pinfo = {p["원봇uid"]: p for p in personas}
    check(len(bots) == 509 and len(set(bots)) == 509, "페르소나가 509가 아닙니다.")
    check(set(bots) <= set(acc092), "페르소나 원 uid가 09-2 계정 밖에 있습니다.")
    bot_labs = Counter(labels.get(u) for u in bots)
    print(f"      [라벨 사용] 페르소나 509 원 uid 라벨 {dict(bot_labs)} (확인용)")
    check(bot_labs == Counter({"bot": 509}), "페르소나 원 uid가 모두 bot이 아닙니다.")

    ledger = [json.loads(l) for l in open(LEDGER_JSONL, encoding="utf-8")]
    # 원 자료에는 한 계정 안에서 comment_id가 같고 시각·본문이 다른 댓글이 있다
    # (v0tq0xa의 i6194rr 두 건). 그래서 (원 uid, comment_id, 시각)으로 짝짓는다.
    def ckey(u, c):
        return (u, c["comment_id"], str(c.get("created_utc") or ""))
    led_by_key = {}
    for r in ledger:
        k = (r["원봇uid"], r["원댓글id"], r["원댓글시각"])
        check(k not in led_by_key, f"대장 (uid, 원댓글id, 시각) 중복: {k}")
        led_by_key[k] = r
    dup_cid = sorted(k for k, v in Counter(r["원댓글id"] for r in ledger).items() if v > 1)
    print(f"      대장 원댓글id 중복 {len(dup_cid)}건 {dup_cid} → (uid, id, 시각) 키로 짝지음")
    cover_bad = [u for u in bots
                 if any(ckey(u, c) not in led_by_key for c in (data[u].get("comment_1") or []))]
    led_uids = Counter(r["원봇uid"] for r in ledger)
    raw_c1 = {u: len(data[u].get("comment_1") or []) for u in bots}
    cover_ok = (not cover_bad and set(led_uids) == set(bots)
                and all(led_uids[u] == raw_c1[u] for u in bots))
    print(f"      대장 {len(ledger):,}행 = 원 봇 509 comment_1 전부  {'같음' if cover_ok else '다름'}")
    check(cover_ok, f"대장이 원 봇 comment_1과 맞지 않습니다: {cover_bad[:5]}")

    mimic_rows = [json.loads(l) for l in open(MIMIC_JSONL, encoding="utf-8")]
    prompt_slots = {r["슬롯id"] for r in ledger if r["상태"] == "프롬프트 있음"}
    mim_slots = [r["슬롯id"] for r in mimic_rows]
    pid2uid = {p["페르소나id"]: p["원봇uid"] for p in personas}
    mim_ok = (len(mim_slots) == len(set(mim_slots)) and set(mim_slots) == prompt_slots
              and all(r["uid"] == "MIM_" + pid2uid[r["페르소나id"]] for r in mimic_rows))
    print(f"      완전 모방기 {len(mimic_rows):,}행 = 대장 '프롬프트 있음' 슬롯 {len(prompt_slots):,}  "
          f"{'같음' if mim_ok else '다름'}")
    check(mim_ok, "완전 모방기 문서가 대장 슬롯과 맞지 않습니다.")

    # 복사 슬롯 (D2)
    titles = {}
    for u, blk in data.items():
        for p in (blk.get("posts") or []):
            titles[str(p.get("submission_id"))] = norm_text(p.get("posts"))
    copy_flag = copy_title = copy_union = 0
    copy_ids = set()
    copy_reason = Counter()
    for u in bots:
        for c in (data[u].get("comment_1") or []):
            r = led_by_key[ckey(u, c)]
            target = c["link_id"].split("_", 1)[1]
            body_n = norm_text(c.get("comment_body"))
            by_title = bool(body_n) and target in titles and body_n == titles[target]
            by_flag = bool(r["원봇복사슬롯"])
            copy_flag += by_flag
            copy_title += by_title
            if by_flag or by_title:
                copy_union += 1
                copy_ids.add(ckey(u, c))
                copy_reason[r["원봇복사_근거"] or "본문=대상제목(대장 표시 없음)"] += 1
    copy_info = {"대장_원댓글id_중복": dup_cid, "대장표시": copy_flag, "본문=대상게시물제목": copy_title, "합집합_제외": copy_union,
                 "근거별": dict(copy_reason)}
    print(f"      복사 슬롯: 대장 표시 {copy_flag} · 본문=대상 제목 {copy_title} · 제외(합집합) {copy_union} "
          f"· 근거 {dict(copy_reason)}")

    all_sets = [set(humans), set(bots), {r["uid"] for r in mimic_rows}]
    disjoint = not (all_sets[0] & all_sets[1] or all_sets[0] & all_sets[2] or all_sets[1] & all_sets[2])
    check(disjoint, "세 집단 uid가 겹칩니다.")
    gates["G3_집단구성"] = {"사람": len(humans), "사람역할": dict(role_cnt), "원봇": len(bots),
                        "대장_커버": cover_ok, "완전모방기_슬롯일치": mim_ok, "uid_교집합0": disjoint,
                        "통과": True}

    # ── [3/7] 문서 선택 ──────────────────────────────────────
    line("[3/7] 문서 선택: 09-2 규칙(정제 → 시각순 → 최근 200 → 10건 이상 → langid en)")
    acc_h = {}
    for u in humans:
        items = []
        for block in ("comment_1", "comment_2"):
            for c in (data[u].get(block) or []):
                items.append((str(c.get("comment_body") or ""), str(c.get("created_utc") or ""), block))
        acc_h[u] = items
    acc_b = {}
    for u in bots:
        acc_b[u] = [(str(c.get("comment_body") or ""), str(c.get("created_utc") or ""), "comment_1")
                    for c in (data[u].get("comment_1") or []) if ckey(u, c) not in copy_ids]
    acc_m = {}
    for r in mimic_rows:
        acc_m.setdefault(r["uid"], []).append((str(r.get("comment_body") or ""), r["계획일"], "모방"))
    del data

    work, group_of, funnels = {}, {}, {}
    for g, accs in (("사람", acc_h), ("원봇", acc_b), ("완전모방기", acc_m)):
        t0 = time.time()
        w, fn = select_group(accs)
        funnels[g] = fn
        for u in w:
            group_of[u] = g
        work.update(w)
        print(f"      {g:<6} 대상 {fn['대상계정수']:>4} · 원본문서 {fn['원본문서수']:>6,} · 문서탈락 "
              f"{fn['문서탈락_합']:>5,} {fn['문서탈락_사유별']} · 절삭 {fn['상한초과_절삭문서수']} · "
              f"문서부족 탈락 {fn['문서부족_탈락계정수']} · 비영어 탈락 {fn['비영어_탈락계정수']} → "
              f"적격 {fn['적격계정수']}계정 · {fn['적격문서수']:,}문서 ({time.time() - t0:.1f}초)")
    funnels["원봇"]["복사슬롯"] = copy_info
    funnels["원봇"]["원본문서수_복사제외전"] = sum(raw_c1.values())

    # G4 사람 문서 선택 재현
    h_elig = [u for u in work if group_of[u] == "사람"]
    doc_bad = [u for u in humans if u not in work or len(work[u]) != acc092[u]["문서수"]]
    print(f"      G4 사람 계정별 문서수 = 09-2: 적격 {len(h_elig)}/874 · 불일치 {len(doc_bad)}")
    gates["G4_사람문서선택재현"] = {"적격": len(h_elig), "불일치계정수": len(doc_bad),
                             "불일치계정": doc_bad[:50], "통과": not doc_bad}
    check(not doc_bad, f"사람 문서 선택이 09-2와 다릅니다: {doc_bad[:10]}")

    # 역할·봉인 요약
    h_roles = Counter(x for u in h_elig for x in roles[u])
    funnels["사람"]["적격_역할별"] = dict(h_roles)
    funnels["사람"]["봉인_계정수"] = sum(1 for u in h_elig if "시험" in roles[u])
    for g in ("원봇", "완전모방기"):
        side = Counter(pinfo[u[4:] if g == "완전모방기" else u]["쪽"] for u in work if group_of[u] == g)
        funnels[g]["적격_쪽별"] = dict(side)
    summary["집단"] = funnels

    # 대상 순서 (smoke면 집단마다 앞 5계정)
    order = []
    for g in GROUPS:
        us = sorted(u for u in work if group_of[u] == g)
        order += us[:SMOKE_N] if SMOKE else us
    if SMOKE:
        work = {u: work[u] for u in order}
        print(f"      smoke: 집단마다 {SMOKE_N}계정 → {len(order)}계정 · {sum(len(v) for v in work.values()):,}문서")
    n_docs = sum(len(work[u]) for u in order)
    exp = {"문서수": n_docs, "하한_분": round(n_docs * MS_LOW / 60000, 1),
           "상한_분": round(n_docs * MS_HIGH / 60000, 1),
           "기준": f"{MS_LOW} ms/문서(12-0 실측) ~ {MS_HIGH} ms/문서(09-2 재파싱 실측)"}
    summary["예상소요"] = exp
    print(f"      파싱 대상 {len(order):,}계정 · {n_docs:,}문서 · 예상 {exp['하한_분']}~{exp['상한_분']}분")
    corpus_hash = sha16("\n".join(f"{u}\t{k}\t{t}" for u in order for t, k in work[u]))
    dump_summary("문서 선택 끝, 파이프라인 준비")

    # ── [4/7] 파이프라인 · 12-0 정합 · 손 대조 ───────────────────
    line("[4/7] 파이프라인: stanza tokenize,pos · use_gpu=False · 계정 단위 bulk_process")
    import stanza
    import torch
    torch.manual_seed(SEED)
    t0 = time.time()
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos", verbose=False,
                          use_gpu=False, download_method=None)
    model_paths = {name: proc.config.get("model_path") for name, proc in nlp.processors.items()}
    print(f"      생성 {time.time() - t0:.1f}초 · stanza {stanza.__version__} · torch {torch.__version__} · "
          f"스레드 {torch.get_num_threads()}")
    j120 = json.load(open(J120, encoding="utf-8"))
    same_models = model_paths == j120["설정"]["모델경로"]
    for name, p in model_paths.items():
        print(f"      모델 {name:<9} {p}")
    print(f"      모델 경로 = 12-0 설정.모델경로  {'같음' if same_models else '다름'}")
    check(same_models and stanza.__version__ == j120["설정"]["stanza"], "stanza 모델·버전이 12-0과 다릅니다.")
    pipe_info = {"stanza": stanza.__version__, "torch": torch.__version__,
                 "스레드": torch.get_num_threads(), "모델경로": model_paths,
                 "호출": 'stanza.Pipeline(lang="en", processors="tokenize,pos", verbose=False, '
                         'use_gpu=False, download_method=None) · 계정 단위 bulk_process'}
    summary["파이프라인"] = pipe_info

    line("[4/7] G5 12-0 정합: 12-0 JSON 첫 계정을 fox8에서 다시 짓고 같은 함수로 잰다")
    g5_uid = sorted(j120["계정"])[0]
    g5 = gate_12_0(nlp, funcword_set, j120["계정"][g5_uid], g5_uid)
    del j120
    gates["G5_12-0정합"] = g5
    print(f"      → {'통과' if g5['통과'] else '실패'}")
    check(g5["통과"], "12-0 정합 실패: 같은 문서·같은 함수로 12-0과 다른 값이 나왔습니다.")

    line("[4/7] G6 손 대조: 집단마다 2계정 × 문서 2건을 단독 파싱과 bulk로 비교")
    hand_rows, hand_expect = gate_hand(nlp, funcword_set, work, group_of)
    gates["G6_손대조"] = {"행": hand_rows, "계정": sorted(hand_expect), "통과": True}
    print(f"      → 통과 ({len(hand_rows)}문서, {len(hand_expect)}계정)")
    dump_summary("관문 G1~G6 통과, 파싱 중")

    # ── [5/7] 파싱 ──────────────────────────────────────────
    line(f"[5/7] 파싱: {CHECKPOINT_EVERY}계정마다 중간 저장, 재개 가능")
    fp = {"기능어_해시": fw_hash, "측정코드_해시": code_hash, "stanza": stanza.__version__,
          "계정수": len(order), "문서수": n_docs, "코퍼스_해시": corpus_hash}
    print(f"      지문 {fp}")
    done, run_sec, total_sec, per_group = run_measurement(nlp, work, order, funcword_set, fp, group_of)

    # ── [6/7] 사후 관문 ─────────────────────────────────────
    line("[6/7] 사후 관문: G7 내부 관계 · G6 결정성 · G8 사람 09-2 대조")
    rel_bad = [u for u in order if not relations_ok(done[u])]
    gates["G7_내부관계"] = {"대상": len(order), "위반계정수": len(rel_bad), "위반": rel_bad[:50],
                        "통과": not rel_bad}
    print(f"      G7 내부 관계 위반 {len(rel_bad)}/{len(order)}")
    det_bad = [u for u in hand_expect if done[u] != hand_expect[u]]
    gates["G6_손대조"]["본측정_결정성_불일치"] = det_bad
    gates["G6_손대조"]["통과"] = not det_bad
    print(f"      G6 손 대조 계정의 본 측정 = 관문 때 값: 불일치 {len(det_bad)}/{len(hand_expect)}")
    h_done = [u for u in order if group_of[u] == "사람"]
    mism, aux = [], Counter()
    for u in h_done:
        a, o = done[u], acc092[u]
        if a["문장수"] != o["문장수"] or a["토큰수"] != o["토큰수"]:
            mism.append({"uid": u, "문장수": [a["문장수"], o["문장수"]], "토큰수": [a["토큰수"], o["토큰수"]]})
        for f in ("문서수", "토큰수_구두점제외", "기능어", "UPOS", "자질"):
            if a[f] != o[f]:
                aux[f] += 1
    frac = len(mism) / len(h_done) if h_done else 0.0
    gates["G8_사람09-2대조"] = {"대상": len(h_done), "불일치계정수": len(mism), "불일치비율": frac,
                            "문턱": GATE_MAX_FRAC, "보조필드_불일치": dict(aux), "예시": mism[:15],
                            "완전일치": not mism and not aux, "통과": frac <= GATE_MAX_FRAC}
    print(f"      G8 사람 문장수·토큰수 = 09-2: 불일치 {len(mism)}/{len(h_done)} ({frac:.2%}) · "
          f"보조 필드 불일치 {dict(aux)}")
    passed = all(v.get("통과") for v in gates.values())

    # ── [7/7] 저장 ──────────────────────────────────────────
    line("[7/7] 저장")
    out_acc = {}
    for u in order:
        g = group_of[u]
        if g == "사람":
            head = {"집단": g, "라벨": labels[u], "역할": roles[u], "봉인": "시험" in roles[u]}
        else:
            p = pinfo[u[4:] if g == "완전모방기" else u]
            head = {"집단": g, "라벨": "bot", "페르소나id": p["페르소나id"], "쪽": p["쪽"],
                    "모델슬롯": p["모델슬롯"], "봉인": False}
        out_acc[u] = {**head, **done[u]}   # [라벨 사용] 저장만
    print("      [라벨 사용] 라벨을 결과 파일에 저장만 합니다.")
    grp_docs = {g: sum(done[u]["문서수"] for u in order if group_of[u] == g) for g in GROUPS}
    rate = {g: {"문서수(이번 실행)": per_group[g][0],
                "ms_per_문서": round(per_group[g][1] / per_group[g][0] * 1000, 2) if per_group[g][0] else None}
            for g in GROUPS}
    all_lens = [n for u in order for n in done[u]["문장길이"]]
    stats = {g: {"계정수": sum(1 for u in order if group_of[u] == g), "문서수": grp_docs[g],
                 "문장수": sum(done[u]["문장수"] for u in order if group_of[u] == g),
                 "토큰수_구두점제외": sum(done[u]["토큰수_구두점제외"] for u in order if group_of[u] == g)}
             for g in GROUPS}
    wall = time.time() - t_start
    setting = {
        "실행": run_info, "smoke": SMOKE, "관문통과": passed,
        "사전선언": "12_OpenRouter생성_사전선언_뼈대.md 2절 참고 행·귀무 행, 3절 사람 풀, 5절 1항",
        "파이프라인": pipe_info, "시드": SEED,
        "정제규칙": {"MIN_CHARS": MIN_CHARS, "MIN_DOCS": MIN_DOCS, "MAX_DOCS": MAX_DOCS,
                 "LANG_TARGET": LANG_TARGET, "출처": "01 clean_doc(= 12-0), 09-2 build_comment_corpus 순서"},
        "집단정의": {"사람": "09-2 계정 ∩ Users.csv human, comment_1 + comment_2",
                 "원봇": "분할.json 페르소나 509 원 uid, comment_1만, 복사 슬롯 제외(D2)",
                 "완전모방기": "완전모방기_문서.jsonl, uid MIM_ 접두"},
        "봉인": "사람 역할에 '시험'이 있는 계정(판별기 시험 234)은 봉인=true. ver.2 동결 전 분석에 쓰지 않는다.",
        "라벨": "사람 human(Users.csv), 원봇 bot, 완전모방기 bot(D7)",
        "구현결정": {
            "D1": "langid en을 세 집단 모두의 마지막 적격 단계로 건다(09-2와 같음).",
            "D2": "복사 슬롯 = 대장 원봇복사슬롯 ∪ 본문=대상 게시물 제목(NFC·공백 정규화). 자극 없음 슬롯은 원봇에 넣는다.",
            "D3": "완전 모방기 정렬 키 = 계획일, 동률은 파일 순서. BotSim 지연 규칙 시각은 부여하지 않았다(상한 200 미도달이라 문서 집합 불변).",
            "D4": "버킷 키: 사람 comment_1/comment_2, 원봇 comment_1, 모방기 '모방'(진단용).",
            "D5": "download_method=None(네트워크 금지). 모델 경로는 12-0과 대조.",
            "D6": "손 대조 계정·문서는 시드 20260926 random.",
            "D7": "완전 모방기 라벨 = bot(표 (a)의 봇 쪽 가상 계정).",
            "D8": "중간 저장은 산출 JSON 옆(볼트 밖). 재개 지문 = 기능어·코퍼스·측정코드 해시 + stanza 버전.",
        },
        "집단": funnels, "관문": gates, "집단별_합계": stats, "속도": rate,
        "소요": {"파싱_이번실행초": run_sec, "파싱_누적초": total_sec, "전체_이번실행초": wall},
        "문장길이요약": {"문장수_전체": len(all_lens),
                    "평균": statistics.fmean(all_lens) if all_lens else None,
                    "중앙": statistics.median(all_lens) if all_lens else None,
                    "구두점제외_0토큰_문장수": sum(1 for n in all_lens if n == 0)},
        "입력": summary["입력"],
    }
    write_json(OUT_JSON, {"설정": setting, "계정": out_acc})
    out_sha = file_sha256(OUT_JSON)
    print(f"      저장 {OUT_JSON} ({os.path.getsize(OUT_JSON) / 1e6:.1f} MB) sha256 {out_sha[:16]}…")
    if os.path.exists(PROGRESS_JSON):
        os.remove(PROGRESS_JSON)
        print("      중간 저장 파일을 지웠습니다.")
    summary.update({"산출": {"계정사전": OUT_JSON, "sha256": out_sha,
                           "MB": round(os.path.getsize(OUT_JSON) / 1e6, 2)},
                    "집단별_합계": stats, "속도": rate, "소요": setting["소요"], "관문통과": passed})
    dump_summary("완료" if passed else "완료(관문 실패)")
    for g in GROUPS:
        s = stats[g]
        print(f"      {g:<6} {s['계정수']:>4}계정 · {s['문서수']:>6,}문서 · 문장 {s['문장수']:>7,} · "
              f"{rate[g]['ms_per_문서']} ms/문서")
    line("끝")
    print(f"      관문 {'모두 통과' if passed else '실패 있음'} · 전체 {fmt_dur(wall)}")
    if not passed:
        print("■ 관문 실패: 12 분석은 이 파일을 쓰면 안 됩니다(설정.관문통과=false).")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except GateError as e:
        print(f"\n■ 중단(관문): {e}")
        sys.exit(1)
