#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
12-0_fox8재파싱.py
────────────────────────────────────────────────────────────────────────────
한계 먼저
    · 이 파일은 새 결과를 만들지 않는다. 옛 12(보관)가 한 번 지나가며 버린
      정보 — 문장마다의 길이 — 를 같은 길로 다시 지나가며 줍는 일이다.
      04-1이 BotSim에서 한 일을 fox8에서 한다.
    · 정합 관문이 통과해도 "옛 12와 같은 문서를 같은 파서로 읽었다"는 것까지만
      보증한다. fox8 자료 자체의 교란(봇 2023 · 사람 ≤2020, 답글 비율 차이)은
      하나도 건드리지 않는다. 그것은 12의 서술 규칙(사전선언 9절)이 맡는다.
    · 문장 경계는 stanza 토크나이저가 정한다. 트윗은 마침표 없이 끝나거나
      이모지·해시태그로 끊기는 일이 많아 '문장'이 레딧보다 덜 문법적인
      단위다. 문장 길이 목록은 그 경계를 그대로 믿은 값이다.

목적
    12(fox8 전이)의 시험 (a)·(b)·(c)는 R 자질(문장당 토큰수·구두점 비율·
    문장길이 변동계수)을 fox8에서도 재야 한다. 그런데 옛 12 JSON에는 계정별
    문장수·토큰수 합계만 있고 문장 길이 목록이 없다. 변동계수는 합계에서
    복원할 수 없다. 그래서 한 번 더 파싱한다(사전선언 12의 3절).

무엇을 따르나
    12_fox8전이_사전선언.md 의 2절(자료)과 3절(12-0 fox8 재파싱).
        · 대상 — 옛 12 JSON "계정"의 1,991계정(봇 1,094 · 사람 897).
        · 정제 — 옛 12의 clean_doc 와 문서 선택 규칙을 한 글자도 바꾸지 않고
          복사한다(is_retweet = 0 · 자기폭로 문장 절제 · URL·멘션 제거 ·
          20자 미만 제거 · 계정별 시간순 최근 200건).
        · 파싱 — stanza tokenize,pos · use_gpu=False · 계정 단위 bulk_process
          (04·04-1과 같은 구성).
        · 저장 — 계정별 문서수·문장수·토큰수·구두점 제외 토큰수·구두점
          토큰수·문장 길이 목록(구두점 제외 토큰수, 08 정의). 기능어·UPOS·
          자질 카운트도 함께 둔다(정합 관문의 보조 대조용).
        · 정합 관문 — 계정별 문장수·토큰수가 옛 12의 '연도별' 합산과 같아야
          한다. 어긋난 계정이 1%를 넘으면 중단한다.
        · 100계정마다 중간 저장, 재개 가능.

라벨 규율
    라벨(봇/사람)은 옛 12 JSON에서 읽어 결과 파일에 **저장만** 한다. 문서
    선택·정제·파싱·정합 판정 어디에도 들어가지 않는다. 라벨이 닿는 지점은
    로그에 [라벨 사용] 표시를 단다(저장 1곳, 관문 불일치의 라벨별 분해 1곳 —
    후자는 원인 진단용이며 판정에 쓰지 않는다).

구현 결정 (사전선언에 없어 이 파일을 쓰며 정한 것 — JSON 설정에도 적는다)
    D1. 계정 단위 langid 판정은 계정 목록을 정할 뿐 문서 선택에 관여하지
        않는다. 대상 목록은 옛 12 JSON에서 오므로 langid는 '재현 확인'으로만
        돌린다(적격 1,991계정이 다시 나오는지). langid가 없으면 건너뛴다.
    D2. 파싱 전 '문서 선택 재현 관문'을 하나 더 둔다. 계정별·버킷별
        (연도|답글여부) 문서수가 옛 12와 같은지 본다. 문서수가 어긋나면
        문장수·토큰수도 어긋날 수밖에 없으므로, 95분을 쓰기 전에 잡으려는
        것이다. 문턱은 본 관문과 같은 1%다.
    D3. 정합 관문이 1%를 넘으면 '중단'을 이렇게 구현한다: 측정치는 버리지
        않고 JSON에 저장하되 설정.관문통과 = false 로 적고 종료 코드 1로
        끝낸다. 12는 이 값이 false이면 읽지 않는다. 95분짜리 측정치를
        버리면 원인 진단 재료까지 버리게 되기 때문이다.
    D4. 사전선언 3절에는 12-0 전용 예측(P12-*)이 없다. 3절에 적힌 기대값
        셋(문서 165,532건 · 정합 완전 일치 · 약 95분)을 실행 전 고정값으로
        삼아 자동 대조한다. '약 95분'의 판정 폭은 ±25%(71~119분)로 둔다.
    D5. 시드 20260926 을 torch에 건다. 12-0에는 무작위 절차가 없고 추론은
        평가 모드라 결과에 영향이 없어야 한다. 공통 규칙이라 걸어 둔다.
    D6. stanza 모델은 ~/stanza_resources 가 아니라 stanza 1.14 기본 위치
        (~/Library/Caches/stanza/1.14.0/resources)에 있다. 옛 12도 경로를
        지정하지 않고 기본값으로 Pipeline을 만들었으므로 같은 호출을 쓴다.
        실제 모델 경로를 JSON에 적는다.
    D7. 버킷별(연도|답글여부) 문서수·문장수·토큰수·구두점 제외 토큰수를
        함께 저장한다. 관문이 어긋났을 때 어느 버킷에서 어긋났는지 보려는
        진단 재료다. 문장 길이 목록은 계정 단위로만 저장한다.

실행
    python -u 12-0_fox8재파싱.py            ← 본 실행 (이 폴더에 산출)
    python -u 12-0_fox8재파싱.py 20 <폴더>   ← 시험 실행: 앞 20계정만, <폴더>에 산출
    venv: /Users/son/.claude/venvs/audio-transcribe/bin/python (stanza 1.14.0)

산출 (이 파일과 같은 폴더)
    12-0_fox8재파싱.json         계정별 측정치 · 관문 결과 · 기대값 대조
    12-0_fox8재파싱_출력.log     화면 출력 그대로 (tee로 받는다)
    12-0_fox8재파싱_진행.json    중간 저장. 끝나면 지운다.
"""

import functools
import hashlib
import heapq
import json
import os
import platform
import re
import sqlite3
import statistics
import sys
import time
import unicodedata
from collections import Counter

# 진행 표시가 즉시 화면에 찍히게 한다. 한 시간짜리 작업이 버퍼에 갇히면
# 멈춘 것처럼 보인다. [04에서 가져옴]
print = functools.partial(print, flush=True)


# ════════════════════════════════════════════════════════════════════════
# [경로]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더를 기준으로 잡는다. 연구 폴더를 통째로 옮겨도 깨지지 않는다.
#   HERE      = …/단계별 진행경과/# 시뮬레이션 10-12
#   STAGE_DIR = …/단계별 진행경과          (02 기능어 목록이 있는 곳)
#   ROOT      = …/연구주제                 (원본데이터·보관 폴더가 있는 곳)
HERE = os.path.dirname(os.path.abspath(__file__))
STAGE_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(STAGE_DIR)

FOX8_DB = f"{ROOT}/1. 원본데이터/3. fox8 Data/fox8_23_dataset.sqlite"
OLD12_DIR = f"{ROOT}/# 07-12 실행분 보관 (미학습)"
OLD12_JSON = f"{OLD12_DIR}/12_fox8전이.json"       # 대상 계정 · 정합 관문 상대
OLD12_PY = f"{OLD12_DIR}/12_fox8전이.py"           # 정제 규칙의 원본 (해시만 잰다)
FUNCWORDS_JSON = f"{STAGE_DIR}/02_기능어목록.json"  # 기능어 172종

# 시험 실행이면 산출 폴더를 바꾼다(정본 폴더에 시험 산출이 섞이지 않게).
TEST_N = int(sys.argv[1]) if len(sys.argv) > 1 else None
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else HERE
SUFFIX = "_시험" if TEST_N else ""
OUT_JSON = f"{OUT_DIR}/12-0_fox8재파싱{SUFFIX}.json"
PROGRESS_JSON = f"{OUT_DIR}/12-0_fox8재파싱{SUFFIX}_진행.json"


# ════════════════════════════════════════════════════════════════════════
# [설정 1] 옛 12의 정제·선택 규칙 — 한 글자도 바꾸지 않는다
# ────────────────────────────────────────────────────────────────────────
# ■ 왜 복사하나 ■
# 정합 관문은 "같은 문서를 같은 파서로 읽으면 같은 수가 나온다"를 묻는다.
# 문서가 한 건이라도 다르면 관문은 파서가 아니라 정제 규칙의 차이를 잡는다.
# 아래 상수·정규식·함수는 옛 12_fox8전이.py 에서 그대로 복사했다
# (그 파일은 다시 01_botsim_적격검열.py 에서 복사해 왔다).
# ════════════════════════════════════════════════════════════════════════
MIN_CHARS = 20          # [옛 12에서 가져옴] 정제 후 20자 미만 문서는 버린다
MIN_DOCS = 10           # [옛 12에서 가져옴] 적격 문서가 10건 미만인 계정은 제외
MAX_DOCS = 200          # [옛 12에서 가져옴] 계정당 최근 200건까지만 사용
LANG_TARGET = "en"      # [옛 12에서 가져옴] 계정 단위 langid 판정 (D1: 재현 확인용)

SELF_REVEAL = re.compile(
    r"(as an ai language model"
    r"|i'?m sorry,? but (i cannot|as an ai)"
    r"|i cannot (comply|fulfill|browse)"
    r"|openai'?s? (content )?polic)", re.I)

RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")      # [옛 12에서 가져옴]
RE_URL = re.compile(r"(https?://\S+|www\.\S+)")       # [옛 12에서 가져옴]
RE_MENTION = re.compile(r"@\w+")                      # [옛 12에서 가져옴]
RE_WS = re.compile(r"\s+")                            # [옛 12에서 가져옴]


# ════════════════════════════════════════════════════════════════════════
# [설정 2] 파싱·저장·관문
# ════════════════════════════════════════════════════════════════════════
SEED = 20260926                 # 공통 규칙 (D5)
CHECKPOINT_EVERY = 100          # 사전선언 3절: 100계정마다 중간 저장
WARMUP_ACCOUNTS = 20            # 처음 20계정의 실측 속도로 끝을 추정한다 [04]
GATE_MAX_FRAC = 0.01            # 사전선언 3절: 어긋난 계정이 1%를 넘으면 중단
EXPECTED_FW_HASH = "382b68572f03bc23"   # 옛 12 설정.기능어_해시 (사슬 확인)
EXPECTED_ACCOUNTS = 1991
EXPECTED_LABELS = {"bot": 1094, "human": 897}

# 사전선언 3절에 적힌 기대값 (D4). 결과를 보기 전에 고정한 값이다.
# 빗나가도 지우지 않는다. 화면과 JSON에 그대로 남긴다.
EXPECTATIONS = [
    {"번호": "E12-0-1",
     "서술": "재구성한 코퍼스가 165,532문서다 (3절 '165,532문서')",
     "판정규칙": "적격 1,991계정의 문서수 합이 정확히 165,532이면 적중"},
    {"번호": "E12-0-2",
     "서술": "계정별 문장수·토큰수가 옛 12의 연도 합산값과 일치한다 (3절 정합 관문)",
     "판정규칙": "불일치 계정 0이면 적중. 0 < 불일치 ≤ 1%면 '관문 통과·예측 빗나감', "
                "1% 초과면 관문 실패"},
    {"번호": "E12-0-3",
     "서술": "파싱 소요가 약 95분이다 (3절 '165,532문서 × 약 34ms ≈ 95분')",
     "판정규칙": "이번 실행의 파싱 소요(재개 시 누적)가 95분 ±25%(71~119분) 안이면 "
                "적중 (구현 결정 D4)"},
]
EXPECTED_DOCS = 165532
EXPECTED_MINUTES = 95.0
EXPECTED_MIN_TOL = 0.25

# 축약형 자가검증 — 04와 같은 문장, 곧은 판과 굽은 판 [04·옛 12에서 가져옴]
SELF_CHECK_TEXT = "I don't think they've seen it, and it isn't mine."
SELF_CHECK_TEXT_CURLY = "I don’t think they’ve seen it, and it isn’t mine."
SELF_CHECK_EXPECT = {"n't": 4, "'ve": 2}


# ════════════════════════════════════════════════════════════════════════
# [도구] 출력·저장
# ════════════════════════════════════════════════════════════════════════
def line(title=""):
    """구분선 한 줄. [09에서 가져옴]"""
    print("\n" + "═" * 74)
    if title:
        print(title)
        print("═" * 74)


def write_json(path, obj, indent=None):
    """
    임시 파일에 먼저 쓰고 이름을 바꿔치기한다. [04·옛 12에서 가져옴]
    쓰는 도중에 멈춰도 파일은 '이전 것' 아니면 '새 것'이다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def fmt_dur(sec):
    """초를 사람이 읽는 단위로 바꾼다. [04에서 가져옴]"""
    if sec < 90:
        return f"{sec:.0f}초"
    if sec < 5400:
        return f"{sec / 60:.1f}분"
    return f"{sec / 3600:.2f}시간"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def file_sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ════════════════════════════════════════════════════════════════════════
# [1] 정제 — 옛 12의 함수 그대로
# ════════════════════════════════════════════════════════════════════════
def normalize_apostrophe(s):
    """굽은 아포스트로피(’)를 곧은 것(')으로. [옛 12에서 가져옴] 토큰과 목록 양쪽에 건다."""
    return s.replace("’", "'")


def clean_doc(text):
    """
    글 1건을 정제한다. [옛 12에서 한 글자도 고치지 않고 가져옴]

    통과하면 (정제 문자열, None, 절제여부), 탈락하면 (None, 사유, 절제여부).
    순서: 1) 자기폭로 문장 절제 → 2) URL·멘션 제거 → 3) 길이 검사.
    URL을 먼저 지우고 길이를 재야 링크만 붙은 짧은 트윗이 20자 문턱을
    넘어 들어오지 않는다.
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


def year_of(created_at):
    """created_at 앞 네 글자 = 연도. 숫자가 아니면 "?". [옛 12에서 가져옴]"""
    s = (created_at or "")[:4]
    return s if len(s) == 4 and s.isdigit() else "?"


def bucket_key(year, is_reply):
    """문서를 담을 버킷 이름 "연도|답글여부". [옛 12에서 가져옴]"""
    return f"{year}|{1 if is_reply else 0}"


def build_fox8_corpus(conn):
    """
    옛 12의 build_fox8_corpus 에서 문서 선택 부분을 그대로 옮긴 것.

    ■ 문서 선택 규칙 (정합 관문이 맞으려면 이것이 정확해야 한다) ■
      · 쿼리: "SELECT user_id, created_at, text, is_reply FROM tweets
               WHERE is_retweet = 0"  — ORDER BY 없음. 옛 12와 글자까지 같게
        둔다. 같은 파일·같은 쿼리면 sqlite가 같은 순서로 행을 흘려 준다.
      · 행마다 clean_doc → 통과한 것만 계정별 힙에 넣는다.
      · 힙의 정렬키: (시각못읽음 0/1, created_at 문자열, 등장순번 seq).
        seq는 통과한 행에만 매기는 전역 순번이다. 크기 200을 넘으면 가장 작은
        (= 가장 오래된) 것을 밀어낸다 → 계정별 '최근 200건'.
      · 남은 문서를 같은 키로 오름차순 정렬(시간순) → 파서에 이 순서로 넣는다.
      · 10건 미만 계정 제외. 계정 단위 langid 'en' 판정.

    이 함수는 langid 판정 전의 후보 전체(candidates)와 깔때기 수치를 돌려준다.
    대상 계정을 고르는 것은 main()이 옛 12 JSON 목록으로 한다(D1).
    """
    cur = conn.cursor()
    drop = Counter()
    heaps = {}
    n_rows = n_trimmed = n_time_bad = 0
    n_excised = n_excised_kept = 0
    seq = 0

    t0 = time.time()
    for uid, created, text, is_reply in cur.execute(
            "SELECT user_id, created_at, text, is_reply FROM tweets "
            "WHERE is_retweet = 0"):
        n_rows += 1
        if not uid:
            drop["작성자 없음"] += 1
            continue

        cleaned, reason, excised = clean_doc(text)
        if excised:
            n_excised += 1
        if cleaned is None:
            drop[reason] += 1
            continue
        if excised:
            n_excised_kept += 1

        yr = year_of(created)
        if yr == "?":
            n_time_bad += 1
        bad_time = 1 if yr == "?" else 0
        item = (bad_time, created or "", seq, cleaned,
                bucket_key(yr, is_reply))
        seq += 1
        h = heaps.setdefault(uid, [])
        if len(h) < MAX_DOCS:
            heapq.heappush(h, item)
        else:
            heapq.heappushpop(h, item)      # 가장 오래된 것을 밀어낸다
            n_trimmed += 1
    print(f"      비리트윗 {n_rows:,}행 훑기 {time.time() - t0:.1f}초 · "
          f"통과 문서를 가진 계정 {len(heaps):,}개")

    candidates = {}
    n_short = 0
    for uid in sorted(heaps):
        items = sorted(heaps[uid])
        docs = [(c, k) for _, _, _, c, k in items]
        if len(docs) >= MIN_DOCS:
            candidates[uid] = docs
        else:
            n_short += 1
    heaps.clear()

    funnel = {
        "비리트윗_행수": n_rows,
        "행_탈락사유": dict(drop.most_common()),
        "상한초과_절삭문서수": n_trimmed,
        "자기폭로_절제문서수": n_excised,
        "자기폭로_절제후_생존문서수": n_excised_kept,
        "시각파싱_실패문서수": n_time_bad,
        "문서부족_탈락계정수": n_short,
        "언어판정_대상계정수": len(candidates),
    }
    return candidates, funnel


def langid_eligible(candidates):
    """
    옛 12의 계정 단위 언어 판정을 다시 돌려 'en' 계정 집합을 돌려준다 (D1).
    langid가 없으면 None. 이 집합은 재현 확인에만 쓰고 대상 선정에는 안 쓴다.
    """
    try:
        import langid
    except ImportError:
        return None
    out = set()
    for uid in sorted(candidates):
        joined = " ".join(c for c, _ in candidates[uid])
        lang, _ = langid.classify(joined)
        if lang == LANG_TARGET:
            out.add(uid)
    return out


# ════════════════════════════════════════════════════════════════════════
# [2] 집계 — 04-1의 aggregate 에서 문장 길이 규칙을, 옛 12에서 버킷을 가져온다
# ════════════════════════════════════════════════════════════════════════
def aggregate(parsed, keys, funcword_set):
    """
    파싱된 문서 목록(한 계정분)을 받아 저장할 값 한 벌을 만든다.

    parsed 는 .sentences → .words → (.text, .upos, .feats) 를 갖는 문서의
    목록이다. stanza Document가 그 모양이고, 자가검증은 같은 모양의 가짜
    객체를 넣는다. 그래야 집계 규칙을 파서 없이 손계산과 맞춰 볼 수 있다.

    ── 세는 규칙 (04·04-1·옛 12와 같다) ─────────────────────────
      토큰        sent.words 의 원소 하나 (MWT 분해 뒤의 낱말 단위)
      구두점      UPOS == "PUNCT"
      문장 길이   문장마다 구두점을 뺀 토큰수 (08 정의)
      기능어      소문자 + 아포스트로피 정규화 표면형이 172종 목록에 있으면 1회
      자질        feats 문자열을 "|"로 끊어 "키=값" 단위로 센다

    반드시 성립해야 하는 관계 (정합 관문에서 전 계정 검사):
      len(문장길이) == 문장수 · sum(문장길이) == 토큰수_구두점제외 ·
      구두점토큰수 == 토큰수 − 토큰수_구두점제외 == UPOS["PUNCT"]
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
    """계정 하나를 04와 같은 방식(계정 단위 bulk_process)으로 파싱해 집계한다."""
    parsed = nlp.bulk_process(docs)
    return aggregate(parsed, keys, funcword_set)


# ════════════════════════════════════════════════════════════════════════
# [3] 자가검증 관문
# ════════════════════════════════════════════════════════════════════════
class _W:
    """자가검증용 가짜 낱말. stanza Word의 세 속성만 흉내 낸다."""
    def __init__(self, text, upos, feats=None):
        self.text, self.upos, self.feats = text, upos, feats


class _S:
    def __init__(self, words):
        self.words = words


class _D:
    def __init__(self, sentences):
        self.sentences = sentences


def self_check_aggregate(funcword_set):
    """
    집계 규칙을 손계산과 맞춘다. 파서를 부르지 않는다.

    손 예제 (문서 2건, 버킷 "2023|0"·"2023|1"):
      문서 1  문장 ① "The dog ran ."   → the(DET) dog(NOUN) ran(VERB) .(PUNCT)
                                          길이 3 (구두점 1 제외)
              문장 ② "It 's mine !"   → it(PRON) 's(AUX) mine(PRON) !(PUNCT)
                                          길이 3
      문서 2  문장 ③ ", , ok"          → ,(PUNCT) ,(PUNCT) ok(INTJ)  길이 1
    손계산:
      토큰    4 + 4 + 3 = 11
      구두점  1 + 1 + 2 = 4      → 구두점 제외 11 − 4 = 7
      문장길이 [3, 3, 1]          → 합 7 = 구두점 제외 (관계 성립)
    기대값: 문서수 2 · 문장수 3 · 토큰수 11 · 구두점 제외 7 · 구두점 4 ·
            기능어 the·it·'s·mine 각 1 (172종 목록에 든 것만; ’s 는 정규화 뒤 's) ·
            버킷 2023|0 = [1, 2, 8, 6] · 2023|1 = [1, 1, 3, 1]
    """
    print("\n  ── (1) 집계 규칙 손계산 대조 (파서 없이) ──")
    d1 = _D([_S([_W("The", "DET", "Definite=Def|PronType=Art"),
                 _W("dog", "NOUN", "Number=Sing"),
                 _W("ran", "VERB", "Tense=Past"),
                 _W(".", "PUNCT")]),
             _S([_W("It", "PRON"), _W("’s", "AUX"),
                 _W("mine", "PRON"), _W("!", "PUNCT")])])
    d2 = _D([_S([_W(",", "PUNCT"), _W(",", "PUNCT"), _W("ok", "INTJ")])])
    got = aggregate([d1, d2], ["2023|0", "2023|1"], funcword_set)

    # 기대 기능어는 예제의 표면형 일곱 개 가운데 172종 목록에 든 것이다.
    # (처음엔 the·it·'s 셋만 적었다가 mine 도 목록에 있어 관문에 걸렸다 —
    #  목록 소속을 손으로 외우지 말고 목록으로 정한다.)
    fw_expect = {w: 1 for w in ("the", "dog", "ran", "it", "'s", "mine", "ok")
                 if w in funcword_set}
    checks = [
        ("문서수", got["문서수"], 2),
        ("문장수", got["문장수"], 3),
        ("토큰수", got["토큰수"], 11),
        ("토큰수_구두점제외", got["토큰수_구두점제외"], 7),
        ("구두점토큰수", got["구두점토큰수"], 4),
        ("문장길이", got["문장길이"], [3, 3, 1]),
        ("기능어(굽은 ’s 정규화 포함)", got["기능어"], fw_expect),
        ("UPOS PUNCT", got["UPOS"].get("PUNCT"), 4),
        ("자질 Tense=Past", got["자질"].get("Tense=Past"), 1),
        ("버킷 2023|0", got["버킷별"].get("2023|0"), [1, 2, 8, 6]),
        ("버킷 2023|1", got["버킷별"].get("2023|1"), [1, 1, 3, 1]),
    ]
    ok = True
    for name, actual, expect in checks:
        good = actual == expect
        ok = ok and good
        print(f"    {name:<28} 기대 {expect} · 실제 {actual}  {'통과' if good else '실패'}")
    return ok, [{"항목": n, "기대": e, "실제": a, "통과": a == e} for n, a, e in checks]


def self_check_clean():
    """
    clean_doc 복사본이 옛 12의 동작을 내는지 손 예제로 본다.
      · 링크·멘션만 붙은 짧은 트윗은 20자 미만으로 탈락해야 한다.
      · 자기폭로 문장만 도려내고 나머지는 남아야 한다.
    """
    print("\n  ── (2) 정제 규칙 손 예제 ──")
    cases = [
        ("@abc hi there https://t.co/xxxxxxxxxx", (None, "20자 미만", False)),
        ("As an AI language model, I cannot. The weather is lovely today in Paris.",
         ("The weather is lovely today in Paris.", None, True)),
        ("As an AI language model I refuse", (None, "자기폭로 절제 후 내용 없음", True)),
        ("Check   this\nout @bob: the market is up www.x.com",
         ("Check this out : the market is up", None, False)),
    ]
    ok = True
    rows = []
    for text, expect in cases:
        got = clean_doc(text)
        good = got == expect
        ok = ok and good
        rows.append({"입력": text, "기대": list(expect), "실제": list(got), "통과": good})
        print(f"    {text[:44]!r:<48} {'통과' if good else '실패  실제=' + repr(got)}")
    return ok, rows


def self_check_contraction(nlp, funcword_set):
    """
    02 목록(UD 분해형: do + n't)과 stanza 토큰화가 맞물리는지 본다. [04·옛 12]
    분해가 안 되면 부정 표현이 조용히 0으로 세어진다. 본 측정과 같은
    measure_account 를 부른다.
    """
    print("\n  ── (3) 축약형이 기능어로 잡히는가 (실제 파서) ──")
    got = measure_account(nlp, [SELF_CHECK_TEXT, SELF_CHECK_TEXT_CURLY],
                          ["검사|0", "검사|0"], funcword_set)
    ok = True
    rows = []
    for word, expect in SELF_CHECK_EXPECT.items():
        actual = got["기능어"].get(word, 0)
        good = actual == expect
        ok = ok and good
        rows.append({"항목": word, "기대": expect, "실제": actual, "통과": good})
        print(f"    {word:<6} 기대 {expect}회 · 실제 {actual}회   {'통과' if good else '실패'}")
    rel = (len(got["문장길이"]) == got["문장수"]
           and sum(got["문장길이"]) == got["토큰수_구두점제외"]
           and got["구두점토큰수"] == got["토큰수"] - got["토큰수_구두점제외"])
    ok = ok and rel
    rows.append({"항목": "len·sum·구두점 관계", "통과": rel})
    print(f"    실제 파싱에서 len(문장길이)=문장수 · sum=구두점제외 · 구두점=차  "
          f"{'통과' if rel else '실패'}")
    return ok, rows


# ════════════════════════════════════════════════════════════════════════
# [4] 중간 저장 / 이어서 하기 — 04의 방식
# ════════════════════════════════════════════════════════════════════════
def load_progress():
    if not os.path.exists(PROGRESS_JSON):
        return None
    return json.load(open(PROGRESS_JSON, encoding="utf-8"))


def save_progress(done, fp, elapsed_total):
    """끝난 계정만 저장한다. 남은 일은 다음 실행이 코퍼스를 다시 지어 계산한다."""
    write_json(PROGRESS_JSON, {
        "안내": "12-0의 중간 저장 파일입니다. 측정이 끝나면 자동으로 지워집니다.",
        "지문": fp,
        "완료계정수": len(done),
        "누적소요초": round(elapsed_total, 1),
        "저장시각": time.strftime("%Y-%m-%d %H:%M:%S"),
        "계정": done,
    })


def run_measurement(nlp, work, funcword_set, fp):
    """
    계정을 uid 오름차순으로 하나씩 파싱한다. 100계정마다 저장.
    반환: (측정치, 이번 실행초, 누적초). 지문이 다르면 None.
    """
    done, prev_sec = {}, 0.0
    prog = load_progress()
    if prog:
        if prog.get("지문") != fp:
            print("■ 중단 — 중간 저장 파일과 지금의 입력이 다릅니다.")
            print(f"  저장 당시: {prog.get('지문')}")
            print(f"  지금:      {fp}")
            print("  기준이 다른 수치를 이어 붙이면 한 파일에 잣대 둘이 섞입니다.")
            print(f"  → {PROGRESS_JSON} 을(를) 지우고 다시 실행하십시오.")
            return None
        done = prog["계정"]
        prev_sec = prog.get("누적소요초", 0.0)
        print(f"      중간 저장을 찾았습니다 — 완료 {len(done):,}계정 "
              f"(그때까지 {fmt_dur(prev_sec)}). 이어서 합니다.")
    else:
        print("      중간 저장 없음. 처음부터 시작합니다.")

    todo = [uid for uid in sorted(work) if uid not in done]
    todo_docs = sum(len(work[u]) for u in todo)
    print(f"      남은 계정 {len(todo):,}개 · 문서 {todo_docs:,}건")
    if todo_docs:
        print(f"      사전선언 3절 추정 34 ms/문서면 {fmt_dur(todo_docs * 0.034)}.")
    if not todo:
        return done, 0.0, prev_sec

    t_run = time.time()
    docs_run = 0
    for i, uid in enumerate(todo, 1):
        items = work[uid]
        done[uid] = measure_account(nlp, [t for t, _ in items],
                                    [k for _, k in items], funcword_set)
        docs_run += len(items)

        if i == WARMUP_ACCOUNTS:
            el = time.time() - t_run
            per_doc = el / docs_run
            print(f"      ── 속도 실측 (처음 {WARMUP_ACCOUNTS}계정) 문서 {docs_run:,}건 · "
                  f"{el:.1f}초 → {per_doc * 1000:.1f} ms/문서 · "
                  f"남은 예상 {fmt_dur((todo_docs - docs_run) * per_doc)}")

        if i % CHECKPOINT_EVERY == 0:
            el = time.time() - t_run
            save_progress(done, fp, prev_sec + el)
            left = (todo_docs - docs_run) * el / docs_run
            print(f"      {len(done):,}/{len(work):,} 계정 · 경과 {fmt_dur(el)} · "
                  f"잔여 추정 {fmt_dur(left)} · 저장 완료")

    run_sec = time.time() - t_run
    save_progress(done, fp, prev_sec + run_sec)
    print(f"      {len(done):,}/{len(work):,} 계정 완료 · 이번 실행 {fmt_dur(run_sec)}")
    return done, run_sec, prev_sec + run_sec


# ════════════════════════════════════════════════════════════════════════
# [5] 정합 관문
# ════════════════════════════════════════════════════════════════════════
def old_totals(old_rec):
    """옛 12 계정 한 칸의 '연도별' 버킷을 합산한다."""
    tot = {"문서수": 0, "문장수": 0, "토큰수": 0, "토큰수_구두점제외": 0}
    fw, up, ft = Counter(), Counter(), Counter()
    for b in old_rec["연도별"].values():
        for k in tot:
            tot[k] += b[k]
        fw.update(b["기능어"])
        up.update(b["UPOS"])
        ft.update(b["자질"])
    tot["기능어"], tot["UPOS"], tot["자질"] = dict(fw), dict(up), dict(ft)
    return tot


def consistency_gate(done, old_acc, labels):
    """
    계정별로 옛 12와 맞춰 본다.
      본 관문(사전선언 3절): 문장수·토큰수가 둘 다 같아야 '일치'.
      보조 대조(판정에 안 씀): 문서수 · 구두점 제외 토큰수 · 기능어·UPOS·자질
        카운트 전체 · 버킷별 [문서수, 문장수, 토큰수, 구두점제외].
      내부 관계(전 계정): len(문장길이)=문장수 · sum(문장길이)=구두점제외 ·
        구두점토큰수 = 토큰수 − 구두점제외.
    """
    uids = sorted(done)
    mism, examples = [], []
    aux = Counter()
    rel_bad = []
    for uid in uids:
        a, o_rec = done[uid], old_acc[uid]
        o = old_totals(o_rec)
        if a["문장수"] != o["문장수"] or a["토큰수"] != o["토큰수"]:
            mism.append(uid)
            if len(examples) < 15:
                examples.append({"계정": uid,
                                 "문장수": [a["문장수"], o["문장수"]],
                                 "토큰수": [a["토큰수"], o["토큰수"]],
                                 "문서수": [a["문서수"], o["문서수"]]})
        if a["문서수"] != o["문서수"]:
            aux["문서수_불일치"] += 1
        if a["토큰수_구두점제외"] != o["토큰수_구두점제외"]:
            aux["토큰수_구두점제외_불일치"] += 1
        for field in ("기능어", "UPOS", "자질"):
            if a[field] != o[field]:
                aux[f"{field}_불일치"] += 1
        old_b = {k: [v["문서수"], v["문장수"], v["토큰수"], v["토큰수_구두점제외"]]
                 for k, v in o_rec["연도별"].items()}
        if a["버킷별"] != old_b:
            aux["버킷별_불일치"] += 1
        if not (len(a["문장길이"]) == a["문장수"]
                and sum(a["문장길이"]) == a["토큰수_구두점제외"]
                and a["구두점토큰수"] == a["토큰수"] - a["토큰수_구두점제외"]
                and a["구두점토큰수"] == a["UPOS"].get("PUNCT", 0)):
            rel_bad.append(uid)

    n = len(uids)
    frac = len(mism) / n if n else 0.0
    # [라벨 사용] 불일치의 라벨별 분해 — 원인 진단용. 판정에는 쓰지 않는다.
    by_label = dict(Counter(labels[u] for u in mism))
    return {
        "규칙": "계정별 문장수·토큰수가 옛 12 JSON 계정[uid]['연도별'] 합산값과 둘 다 같으면 일치",
        "대상계정수": n,
        "불일치계정수": len(mism),
        "불일치비율": frac,
        "문턱": GATE_MAX_FRAC,
        "통과": frac <= GATE_MAX_FRAC,
        "완전일치": len(mism) == 0,
        "불일치계정": mism,
        "불일치_예시": examples,
        "불일치_라벨별_진단용": by_label,
        "보조대조_불일치계정수": {k: aux.get(k, 0) for k in
                          ("문서수_불일치", "토큰수_구두점제외_불일치", "기능어_불일치",
                           "UPOS_불일치", "자질_불일치", "버킷별_불일치")},
        "내부관계_위반계정수": len(rel_bad),
        "내부관계_위반계정": rel_bad[:50],
        "합계_재파싱": {k: sum(done[u][k] for u in uids) for k in
                     ("문서수", "문장수", "토큰수", "토큰수_구두점제외", "구두점토큰수")},
        "합계_옛12": {k: sum(old_totals(old_acc[u])[k] for u in uids) for k in
                    ("문서수", "문장수", "토큰수", "토큰수_구두점제외")},
    }


# ════════════════════════════════════════════════════════════════════════
# [6] 본 흐름
# ════════════════════════════════════════════════════════════════════════
def main():
    t_start = time.time()
    line("12-0 fox8 재파싱 — 문장 길이 목록 확보 (사전선언 12의 3절)")
    print(f"  실행 {time.strftime('%Y-%m-%d %H:%M:%S')} · python {platform.python_version()}"
          f" · {platform.system()} {platform.machine()}")
    if TEST_N:
        print(f"  ※ 시험 실행: 앞 {TEST_N}계정만. 산출 폴더 {OUT_DIR}")

    # ── [0/5] 입력 확인 ─────────────────────────────────────────
    line("[0/5] 입력 확인 — 정본은 읽기만 한다")
    for path, what in [(FOX8_DB, "fox8 sqlite"), (OLD12_JSON, "옛 12 JSON"),
                       (OLD12_PY, "옛 12 스크립트"), (FUNCWORDS_JSON, "02 기능어 목록")]:
        if not os.path.exists(path):
            print(f"■ 중단 — {what} 없음: {path}")
            sys.exit(1)
        print(f"      있음  {what}")

    funcwords = json.load(open(FUNCWORDS_JSON, encoding="utf-8"))["기능어"]
    funcwords = sorted({normalize_apostrophe(w) for w in funcwords})
    funcword_set = set(funcwords)
    fw_hash = sha16("\n".join(funcwords))
    print(f"      기능어 {len(funcwords)}종 · 해시 {fw_hash} "
          f"(옛 12 {EXPECTED_FW_HASH}) → {'일치' if fw_hash == EXPECTED_FW_HASH else '불일치'}")
    if fw_hash != EXPECTED_FW_HASH:
        print("■ 중단 — 기능어 목록이 옛 12와 다르면 기능어 대조가 성립하지 않습니다.")
        sys.exit(1)

    old = json.load(open(OLD12_JSON, encoding="utf-8"))
    old_acc = old["계정"]
    old_conf = old["설정"]
    old_corpus = old["코퍼스"]
    del old
    print(f"      옛 12 계정 {len(old_acc):,}개 · 문서 {sum(v['문서수'] for v in old_acc.values()):,}건")
    # [라벨 사용] 저장만 한다. 선택·정제·파싱·판정에 쓰지 않는다.
    labels = {u: v["라벨"] for u, v in old_acc.items()}
    lab_count = dict(Counter(labels.values()))
    print(f"      [라벨 사용] 라벨을 읽어 결과 파일 저장용으로만 보관 → {lab_count}")
    if len(old_acc) != EXPECTED_ACCOUNTS or lab_count != EXPECTED_LABELS:
        print(f"■ 중단 — 대상 계정 수가 사전선언 2절(1,991: 봇 1,094·사람 897)과 다릅니다.")
        sys.exit(1)

    # ── [1/5] 자가검증 (파서 없이) ──────────────────────────────
    line("[1/5] 자가검증 관문 — 집계·정제 규칙을 손계산과 맞춘다")
    ok_agg, rows_agg = self_check_aggregate(funcword_set)
    ok_cln, rows_cln = self_check_clean()
    if not (ok_agg and ok_cln):
        print("■ 중단 — 자가검증 실패. 파싱을 시작하지 않습니다.")
        sys.exit(1)
    print("\n      두 검사 통과.")

    # ── [2/5] 문서 선택 재현 ────────────────────────────────────
    line("[2/5] 문서 선택 재현 — 옛 12의 규칙으로 코퍼스를 다시 짓는다")
    print("      규칙: is_retweet=0 → clean_doc(자기폭로 절제·URL·멘션·20자) →")
    print("            계정별 (시각, 순번) 최근 200건 → 10건 이상 → 계정 단위 langid en")
    conn = sqlite3.connect(f"file:{FOX8_DB}?mode=ro", uri=True)
    candidates, funnel = build_fox8_corpus(conn)
    conn.close()

    # 깔때기 수치를 옛 12와 나란히 본다 (정보용).
    old_filter = old_corpus["필터별_탈락"]
    funnel_cmp = {
        "행_탈락사유": [funnel["행_탈락사유"], old_filter["행_탈락사유"]],
        "상한초과_절삭문서수": [funnel["상한초과_절삭문서수"], old_filter["상한초과_절삭문서수"]],
        "언어판정_대상계정수": [funnel["언어판정_대상계정수"], old_filter["언어판정_대상계정수"]],
        "자기폭로_절제문서수": [funnel["자기폭로_절제문서수"],
                        sum(old_filter["자기폭로_절제문서수"].values())],
    }
    for k, (new_v, old_v) in funnel_cmp.items():
        print(f"      {k:<16} 재구성 {new_v} · 옛 12 {old_v}  {'같음' if new_v == old_v else '다름'}")
    funnel_same = all(a == b for a, b in funnel_cmp.values())

    t0 = time.time()
    eligible = langid_eligible(candidates)
    if eligible is None:
        lang_check = {"수행": False, "사유": "langid 없음"}
        print("      langid 없음 → 계정 집합 재현 확인을 건너뜀 (D1)")
    else:
        target = set(old_acc)
        lang_check = {"수행": True, "재현_en계정수": len(eligible),
                      "옛12에만": sorted(target - eligible),
                      "재현에만": sorted(eligible - target),
                      "일치": eligible == target}
        print(f"      langid 재현: en {len(eligible):,}계정 · 옛 12와 "
              f"{'완전히 같음' if eligible == target else '다름'} "
              f"(옛12에만 {len(target - eligible)} · 재현에만 {len(eligible - target)}) "
              f"· {time.time() - t0:.1f}초")

    missing = sorted(set(old_acc) - set(candidates))
    if missing:
        print(f"■ 중단 — 옛 12 계정 {len(missing)}개가 재구성 후보에 없습니다: {missing[:10]}")
        sys.exit(1)
    work = {u: candidates[u] for u in sorted(old_acc)}
    del candidates

    # 파싱 전 관문 (D2): 계정별·버킷별 문서수가 옛 12와 같은가
    doc_mism = []
    for u, docs in work.items():
        mine = Counter(k for _, k in docs)
        theirs = {k: v["문서수"] for k, v in old_acc[u]["연도별"].items()}
        if dict(mine) != theirs:
            doc_mism.append(u)
    n_docs = sum(len(v) for v in work.values())
    doc_frac = len(doc_mism) / len(work)
    print(f"      대상 {len(work):,}계정 · 문서 {n_docs:,}건 (옛 12 {EXPECTED_DOCS:,})")
    print(f"      버킷별 문서수 불일치 계정 {len(doc_mism)} ({doc_frac:.2%}) "
          f"→ {'통과' if doc_frac <= GATE_MAX_FRAC else '실패'}")
    if doc_frac > GATE_MAX_FRAC:
        print("■ 중단 — 파서에 넣기 전 문서 선택이 옛 12와 다릅니다. 정제 규칙·쿼리 순서를 보십시오.")
        print(f"  예: {doc_mism[:10]}")
        sys.exit(1)

    if TEST_N:
        work = {u: work[u] for u in sorted(work)[:TEST_N]}
        print(f"      시험 실행: {len(work)}계정으로 줄임")

    corpus_hash = sha16("\n".join(f"{u}\t{k}\t{t}" for u in sorted(work)
                                  for t, k in work[u]))
    fp = {"기능어_해시": fw_hash, "계정수": len(work),
          "문서수": sum(len(v) for v in work.values()), "코퍼스_해시": corpus_hash}
    print(f"      입력 지문 {fp}")

    # ── [3/5] 파이프라인 + 축약형 검사 ──────────────────────────
    line("[3/5] 파이프라인 — stanza tokenize,pos · use_gpu=False (04·옛 12와 같은 호출)")
    import stanza
    import torch
    torch.manual_seed(SEED)
    t0 = time.time()
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos",
                          verbose=False, use_gpu=False)
    model_paths = {name: proc.config.get("model_path")
                   for name, proc in nlp.processors.items()}
    print(f"      생성 {time.time() - t0:.1f}초 · stanza {stanza.__version__} · "
          f"torch {torch.__version__} · 프로세서 {list(nlp.processors)}")
    for name, pth in model_paths.items():
        print(f"      모델 {name:<9} {pth}")
    if not hasattr(nlp, "bulk_process"):
        print("■ 중단 — 이 stanza 버전에는 bulk_process가 없습니다.")
        sys.exit(1)
    ok_tok, rows_tok = self_check_contraction(nlp, funcword_set)
    if not ok_tok:
        print("■ 중단 — 축약형 검사 실패. stanza 버전·모델·02 목록을 확인하십시오.")
        sys.exit(1)

    # ── [4/5] 파싱 ─────────────────────────────────────────────
    line(f"[4/5] 파싱 — 계정 단위 bulk_process · {CHECKPOINT_EVERY}계정마다 중간 저장")
    res = run_measurement(nlp, work, funcword_set, fp)
    if res is None:
        sys.exit(1)
    done, run_sec, total_sec = res

    # ── [5/5] 정합 관문 · 기대값 대조 · 저장 ──────────────────────
    line("[5/5] 정합 관문 — 계정별 문장수·토큰수 대 옛 12 '연도별' 합산")
    gate = consistency_gate(done, old_acc, labels)
    print(f"      대상 {gate['대상계정수']:,}계정 · 불일치 {gate['불일치계정수']} "
          f"({gate['불일치비율']:.4%}) · 문턱 {GATE_MAX_FRAC:.0%} → "
          f"{'통과' if gate['통과'] else '실패'}{' (완전 일치)' if gate['완전일치'] else ''}")
    print(f"      합계 재파싱 {gate['합계_재파싱']}")
    print(f"      합계 옛 12   {gate['합계_옛12']}")
    print(f"      보조 대조 불일치 계정수 {gate['보조대조_불일치계정수']}")
    print(f"      내부 관계 위반 계정 {gate['내부관계_위반계정수']}")
    if gate["불일치계정수"]:
        print(f"      [라벨 사용] 불일치 라벨별(진단용) {gate['불일치_라벨별_진단용']}")
        for ex in gate["불일치_예시"][:10]:
            print(f"        {ex}")
    if gate["내부관계_위반계정수"]:
        print("■ 내부 관계 위반 — 집계 코드 결함. 관문 실패로 처리합니다.")
        gate["통과"] = False

    # 원인 서술 — 완전 일치가 아니면 로그에 적는다(공통 규칙).
    cause = None
    if not gate["완전일치"]:
        aux = gate["보조대조_불일치계정수"]
        if aux["문서수_불일치"] or aux["버킷별_불일치"]:
            cause = ("버킷별 문서수 또는 문장수·토큰수가 어긋난다. 문서 선택(정제 규칙·"
                     "쿼리 순서)의 차이가 먼저 의심된다.")
        else:
            cause = ("문서수·버킷 구성은 같고 문장·토큰 경계만 어긋난다. 같은 문서를 "
                     "파서가 다르게 끊은 것이다 — stanza/torch 버전·모델 파일·수치 "
                     "연산(스레드 수 등)의 차이가 의심된다.")
        print(f"      원인 추정: {cause}")
    gate["원인추정"] = cause

    # 기대값 대조 (D4)
    line("기대값 자동 대조 — 사전선언 3절에 적힌 값 (빗나가도 지우지 않는다)")
    n_docs_done = sum(done[u]["문서수"] for u in done)
    minutes = total_sec / 60
    lo, hi = EXPECTED_MINUTES * (1 - EXPECTED_MIN_TOL), EXPECTED_MINUTES * (1 + EXPECTED_MIN_TOL)
    exp_results = []
    for e in EXPECTATIONS:
        r = dict(e)
        if e["번호"] == "E12-0-1":
            r["실측"] = n_docs_done
            r["적중"] = (n_docs_done == EXPECTED_DOCS) if not TEST_N else None
        elif e["번호"] == "E12-0-2":
            r["실측"] = f"불일치 {gate['불일치계정수']}/{gate['대상계정수']}"
            r["적중"] = gate["완전일치"]
            r["관문통과"] = gate["통과"]
        else:
            r["실측"] = f"{minutes:.1f}분 ({total_sec / max(n_docs_done, 1) * 1000:.2f} ms/문서)"
            r["적중"] = (lo <= minutes <= hi) if not TEST_N else None
        exp_results.append(r)
        mark = {True: "적중", False: "빗나감", None: "시험 실행이라 판정 안 함"}[r["적중"]]
        print(f"      {r['번호']}  {r['서술']}")
        print(f"               실측 {r['실측']} → {mark}")

    # 요약 통계 (라벨 없이)
    all_lens = [n for u in done for n in done[u]["문장길이"]]
    summary = {
        "문장수_전체": len(all_lens),
        "문장길이_평균": statistics.fmean(all_lens) if all_lens else None,
        "문장길이_중앙": statistics.median(all_lens) if all_lens else None,
        "문장길이_최대": max(all_lens) if all_lens else None,
        "구두점제외_0토큰_문장수": sum(1 for n in all_lens if n == 0),
        "문장5개미만_계정수": sum(1 for u in done if done[u]["문장수"] < 5),
    }
    print(f"\n      문장 길이 요약(라벨 없이) {summary}")

    out_acc = {}
    for u in sorted(done):
        a = dict(done[u])
        a = {"라벨": labels[u], **a}     # [라벨 사용] 저장만
        out_acc[u] = a

    wall = time.time() - t_start
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.machine()}",
            "stanza": stanza.__version__,
            "torch": torch.__version__,
            "모델경로": model_paths,
            "파이프라인": 'stanza.Pipeline(lang="en", processors="tokenize,pos", '
                     'verbose=False, use_gpu=False) · 계정 단위 bulk_process',
            "사전선언": "12_fox8전이_사전선언.md 2절·3절",
            "시드": SEED,
            "시험실행": TEST_N,
            "관문통과": gate["통과"],
            "입력": {"fox8_sqlite": os.path.relpath(FOX8_DB, ROOT),
                   "옛12_JSON": os.path.relpath(OLD12_JSON, ROOT),
                   "옛12_JSON_sha16": file_sha16(OLD12_JSON),
                   "옛12_py_sha16": file_sha16(OLD12_PY),
                   "옛12_실행일": old_conf.get("실행일"),
                   "기능어_JSON": os.path.relpath(FUNCWORDS_JSON, ROOT),
                   "기능어_해시": fw_hash, "기능어_개수": len(funcwords)},
            "입력지문": fp,
            "정제규칙": {"MIN_CHARS": MIN_CHARS, "MIN_DOCS": MIN_DOCS, "MAX_DOCS": MAX_DOCS,
                     "LANG_TARGET": LANG_TARGET, "is_retweet": 0,
                     "쿼리": "SELECT user_id, created_at, text, is_reply FROM tweets WHERE is_retweet = 0",
                     "정렬키": "(시각못읽음, created_at, 통과순번) 오름차순 · 계정별 최근 200건",
                     "출처": "옛 12_fox8전이.py 의 clean_doc·build_fox8_corpus 그대로"},
            "저장필드": {"문장길이": "문장마다 구두점(UPOS PUNCT)을 뺀 토큰수 (08 정의)",
                     "구두점토큰수": "UPOS PUNCT 토큰수 = 토큰수 − 토큰수_구두점제외",
                     "버킷별": "연도|답글여부 → [문서수, 문장수, 토큰수, 토큰수_구두점제외] (D7)",
                     "라벨": "저장만. 파싱·관문 판정에 쓰지 않음"},
            "구현결정": {
                "D1": "langid는 대상 선정이 아니라 재현 확인에만 쓴다. 대상은 옛 12 JSON '계정' 1,991.",
                "D2": "파싱 전 계정별·버킷별 문서수 대조 관문(문턱 1%)을 추가.",
                "D3": "정합 관문 1% 초과 시 측정치는 저장하되 설정.관문통과=false, 종료 코드 1.",
                "D4": "사전선언 3절의 기대값 셋을 자동 대조. '약 95분' 판정 폭은 ±25%(71~119분).",
                "D5": "torch.manual_seed(20260926). 12-0에는 무작위 절차가 없다.",
                "D6": "stanza 모델은 ~/stanza_resources가 아니라 1.14 기본 위치(모델경로 참조). 옛 12와 같은 기본 호출.",
                "D7": "버킷별 문서수·문장수·토큰수·구두점제외를 진단용으로 저장.",
            },
            "자가검증": {"집계": rows_agg, "정제": rows_cln, "축약형": rows_tok},
            "문서선택재현": {"깔때기": funnel, "깔때기_옛12대조": funnel_cmp,
                       "깔때기_일치": funnel_same, "langid재현": lang_check,
                       "버킷별문서수_불일치계정수": len(doc_mism),
                       "버킷별문서수_불일치계정": doc_mism[:50]},
            "정합관문": gate,
            "기대값대조": exp_results,
            "문장길이요약": summary,
            "소요": {"파싱_이번실행초": run_sec, "파싱_누적초": total_sec, "전체_이번실행초": wall},
            "라벨별_계정수": lab_count,
        },
        "계정": out_acc,
    }
    write_json(OUT_JSON, out)
    print(f"\n      저장 {OUT_JSON} ({os.path.getsize(OUT_JSON) / 1e6:.1f} MB)")
    if os.path.exists(PROGRESS_JSON):
        os.remove(PROGRESS_JSON)
        print("      중간 저장 파일을 지웠습니다.")

    line("끝")
    print(f"      정합 관문 {'통과' if gate['통과'] else '실패'} · 전체 {fmt_dur(wall)}")
    if not gate["통과"]:
        print("■ 중단 — 정합 관문 실패. 12는 이 파일을 쓰면 안 됩니다 (설정.관문통과=false).")
        sys.exit(1)


if __name__ == "__main__":
    main()
