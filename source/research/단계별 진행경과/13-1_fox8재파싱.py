#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""fox8 원문 정제·적격 계정 선정·Stanza 측정. 최종 연구 규칙 고정판."""

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
STAGE_DIR = HERE
ROOT = os.path.dirname(STAGE_DIR)

FOX8_DB = f"{ROOT}/1. 원본데이터/3. fox8 Data/fox8_23_dataset.sqlite"
FUNCWORDS_JSON = f"{STAGE_DIR}/02_기능어목록.json"  # 기능어 172종

# 시험 실행이면 산출 폴더를 바꾼다(정본 폴더에 시험 산출이 섞이지 않게).
TEST_N = int(sys.argv[1]) if len(sys.argv) > 1 else None
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else HERE
SUFFIX = "_시험" if TEST_N else ""
OUT_JSON = f"{OUT_DIR}/13-1_fox8재파싱{SUFFIX}.json"
PROGRESS_JSON = f"{OUT_DIR}/13-1_fox8재파싱{SUFFIX}_진행.json"


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
EXPECTED_FW_HASH = "382b68572f03bc23"   # 옛 12 설정.기능어_해시 (사슬 확인)
EXPECTED_ACCOUNTS = 1991
EXPECTED_LABELS = {"bot": 1094, "human": 897}

# 사전선언 3절에 적힌 기대값 (D4). 결과를 보기 전에 고정한 값이다.
# 빗나가도 지우지 않는다. 화면과 JSON에 그대로 남긴다.
EXPECTED_DOCS = 165532

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
    main()에서 langid 영어 판정으로 적격 계정을 정한다.
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
    langid가 없으면 None. main()은 이를 오류로 처리한다.
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




# ════════════════════════════════════════════════════════════════════════
# [6] 본 흐름
# ════════════════════════════════════════════════════════════════════════
def main():
    """원본 DB에서 적격 계정을 다시 선정한다. 과거 실행 JSON은 사용하지 않는다."""
    import stanza
    import torch
    started = time.time()
    funcwords = sorted({normalize_apostrophe(w) for w in
                        json.load(open(FUNCWORDS_JSON, encoding="utf-8"))["기능어"]})
    fw_hash = sha16("\n".join(funcwords))
    assert len(funcwords) == 172 and fw_hash == EXPECTED_FW_HASH
    conn = sqlite3.connect(f"file:{FOX8_DB}?mode=ro", uri=True)
    candidates, funnel = build_fox8_corpus(conn)
    labels_all = dict(conn.execute("SELECT user_id, label FROM users"))
    conn.close()
    eligible = langid_eligible(candidates)
    if eligible is None:
        raise RuntimeError("langid가 필요합니다. requirements.txt 환경을 사용하세요.")
    work = {u: candidates[u] for u in sorted(eligible)}
    labels = {u: labels_all[u] for u in work}
    assert len(work) == EXPECTED_ACCOUNTS
    assert dict(Counter(labels.values())) == EXPECTED_LABELS
    assert sum(map(len, work.values())) == EXPECTED_DOCS
    if TEST_N:
        work = {u: work[u] for u in sorted(work)[:TEST_N]}
    corpus_hash = sha16("\n".join(f"{u}\t{k}\t{text}" for u in sorted(work)
                                  for text, k in work[u]))
    fp = {"기능어_해시": fw_hash, "계정수": len(work),
          "문서수": sum(map(len, work.values())), "코퍼스_해시": corpus_hash}
    print("원본에서 재선정:", fp)
    for fn in (self_check_aggregate,):
        assert fn(set(funcwords))[0]
    assert self_check_clean()[0]
    torch.manual_seed(SEED)
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos", verbose=False,
                          use_gpu=False, download_method=None)
    assert self_check_contraction(nlp, set(funcwords))[0]
    res = run_measurement(nlp, work, set(funcwords), fp)
    if res is None:
        raise RuntimeError("파싱 재개 입력 지문 불일치")
    done, run_sec, total_sec = res
    for u, a in done.items():
        assert len(a["문장길이"]) == a["문장수"]
        assert sum(a["문장길이"]) == a["토큰수_구두점제외"]
        assert a["UPOS"].get("PUNCT", 0) == a["토큰수"] - a["토큰수_구두점제외"]
    out = {"설정": {"관문통과": True, "입력지문": fp,
             "정제규칙": {"MIN_CHARS": MIN_CHARS, "MIN_DOCS": MIN_DOCS, "MAX_DOCS": MAX_DOCS,
                          "LANG_TARGET": LANG_TARGET},
             "문서선택": "비리트윗 → 정제 → 최근 200건 → 10건 이상 → 계정 단위 영어 판정",
             "깔때기": funnel, "stanza": stanza.__version__, "torch": torch.__version__,
             "소요초": time.time()-started, "파싱초": total_sec},
           "계정": {u: {"라벨": labels[u], **done[u]} for u in sorted(done)}}
    write_json(OUT_JSON, out)
    print("저장:", OUT_JSON)


if __name__ == "__main__":
    main()
