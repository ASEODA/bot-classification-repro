#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
01_botsim_적격검열.py   (2026-08-17 전면 개정)
────────────────────────────────────────────────────────────────────────────
목적
    BotSim-24 데이터셋에서 "분석에 쓸 수 있는 계정"만 골라낸다.
    특성 측정은 하지 않는다. 대상 확정만 한다.

────────────────────────────────────────────────────────────────────────────
개정 이유 — 이전 판의 결함 (반드시 읽을 것)
────────────────────────────────────────────────────────────────────────────
이전 판은 문서 하나하나에 대해 "영어 기능어 10개(the, and, of, is, it, you,
that, for, with, this) 중 하나라도 있어야 통과"라는 규칙을 썼다.

두 가지가 잘못됐다.

(1) 정상 영어를 대량으로 버린다.
    실측: 아래 문장들이 전부 탈락했다.
        "now we are really happy at korea trip"
        "I think we should go there tomorrow"
        "He asked me why I did not come"
        "why are people so angry these days"
    are·at·to·in·we·they·I·not 같은 흔한 단어가 목록에 없기 때문이다.

(2) 더 심각한 문제 — 결과변수로 표본을 골랐다.
    우리가 측정하려는 것이 바로 기능어 사용이다. 그런데 기능어가 없다는
    이유로 문서를 지우면, 기능어 사용이 특이한 문서일수록 데이터에서
    사라진다. 봇과 사람의 기능어 사용이 다르다면 양쪽이 다른 비율로
    삭제되고, 측정하려는 차이 자체가 필터에 깎인다.
    방향도 예측된다 — 짧은 문서가 주로 탈락하는데, 짧은 글은 사람 문서에
    더 많다(선행 측정: 사람 34% vs 봇 10%). 즉 사람 문서를 더 지운다.

────────────────────────────────────────────────────────────────────────────
개정 내용 — 언어 판정을 문서에서 계정으로 옮긴다
────────────────────────────────────────────────────────────────────────────
원래 이 필터가 막으려던 것은 "계정 전체가 비영어인 계정들이 서로 닮아 보이는"
현상이었다. 그렇다면 판정도 계정 단위로 하는 것이 맞다.

    이전:  문서마다 영어인지 판정 → 아니면 그 문서 삭제
    개정:  계정의 글 전체를 합쳐 영어인지 판정 → 아니면 계정째 제외

이렇게 하면
    · 문서 단위 선택 편향이 원천적으로 사라진다
      (계정이 통과하면 그 계정의 문서는 전부 남는다)
    · 판정 대상 텍스트가 길어져 언어 판정 자체가 훨씬 정확해진다
    · 원래 목표(비영어 계정 배제)는 더 정확히 달성된다

그리고 언어 판정을 임의로 고른 단어 목록으로 하지 않는다.
langid.py를 쓴다 — 학술적으로 발표되고 널리 쓰이는 언어 식별 도구다.
    Lui, M. & Baldwin, T. (2012). langid.py: An Off-the-shelf Language
    Identification Tool. ACL 2012 System Demonstrations.
97개 언어에 대해 사전 학습된 모델이 패키지에 포함돼 있어 별도 다운로드가
없고, 판정 근거가 우리 손을 떠나 있다.

────────────────────────────────────────────────────────────────────────────
실행
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 01_botsim_적격검열.py
    필요 패키지: langid  (설치됨 — pip install langid)

산출
    01_적격계정.json  — 다음 단계들의 유일한 입력
    화면에는 깔때기와 함께 "이전 규칙과 무엇이 달라졌는지"를 출력한다.
"""

import json
import csv
import os
import re
import sys
import time
import unicodedata
from collections import Counter

# ════════════════════════════════════════════════════════════════════════
# [경로]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더를 기준으로 잡는다 — 연구 폴더를 통째로 옮겨도 깨지지 않는다.
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = f"{HERE}/1. 원본데이터"
BOTSIM_DIR = f"{BASE}/2. BotSim Data/BotSim-24-Dataset"
POSTS_JSON = f"{BOTSIM_DIR}/user_post_comment.json"   # 계정별 글 원문
USERS_CSV = f"{BOTSIM_DIR}/Users.csv"                  # 라벨(봇/사람) 판정용
OUT_JSON = f"{HERE}/01_적격계정.json"


# ════════════════════════════════════════════════════════════════════════
# [설정] 판단 기준
# ════════════════════════════════════════════════════════════════════════

# ── 문서 단위 기준 (2개뿐) ──────────────────────────────────────
MIN_CHARS = 20
# 정제 후 20자 미만 문서는 버린다.
# 이유: 측정 신뢰도. "ㅋㅋ" 수준의 초단문은 어떤 비율을 계산해도 분모가
#       너무 작아 값이 튄다. 이것은 문체 기준이 아니라 측정 기준이다.

# 자기폭로 문구 처리 — 문서를 버리지 않고 그 문장만 도려낸다.
#
# "As an AI language model..." 은 봇임을 그대로 실토하는 문장이다.
# 남겨두면 어떤 방법을 써도 봇을 맞히게 되므로(=누설) 반드시 제거해야 한다.
#
# 그런데 문서를 통째로 버리면 안 된다. 실측(2026-08-17):
#     fox8   봇 문서의 1.16%(1,160/99,628)가 해당, 사람은 1건
#            봇 계정의 83%(945/1,140)가 최소 1건 보유
#     BotSim 봇 문서의 0.024%(12/49,309), 사람 0건
# 즉 삭제는 거의 전적으로 봇 쪽에만 적용된다. 문서를 버리면 봇 데이터만
# 비대칭적으로 깎이고, 그 문서에 함께 들어 있던 정상 텍스트도 사라진다.
#
# 이 문구는 계정의 '문체'가 아니라 모델이 캐릭터를 깬 시스템 아티팩트다.
# 따라서 해당 문장만 도려내고 나머지 문장은 살린다.
# (구절만 지우면 ", I cannot express opinions" 같은 비문이 남아 품사 분석이
#  왜곡되므로, 문장 단위로 잘라낸다)
SELF_REVEAL = re.compile(
    r"(as an ai language model"
    r"|i'?m sorry,? but (i cannot|as an ai)"
    r"|i cannot (comply|fulfill|browse)"
    r"|openai'?s? (content )?polic)", re.I)

# 문장 경계. 마침표·물음표·느낌표 뒤 공백, 또는 줄바꿈.
# SNS 글은 문장부호가 불완전하므로 완벽한 분리는 기대하지 않는다.
# 목적은 정확한 구문 분석이 아니라 "문제 문장만 떼어내기"다.
RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

# ※ 언어 관련 문서 필터는 전부 없앴다. 위 개정 이유 참조.

# ── 계정 단위 기준 (3개) ────────────────────────────────────────
MIN_DOCS = 10
# 정제 통과 문서가 10건 미만인 계정은 제외.
# 이유: 글 몇 건으로는 그 계정의 문체라 부를 통계가 안 나온다.
#       후속 실험에서 글을 전반/후반 반으로 갈라 비교하므로 각 5건은 필요하다.

MAX_DOCS = 200
# 계정당 최근 200건까지만 사용.
# 이유: 글이 수천 건인 계정이 모든 집계를 지배하는 것을 막는다.
#       200이라는 값은 fox8의 수집 상한(계정당 최근 200트윗)에 맞춘 것으로,
#       세 데이터셋을 같은 조건으로 비교하기 위한 선택이다.

LANG_TARGET = "en"
# 계정의 글 전체를 합쳐 langid로 판정했을 때 이 언어여야 통과.

# ── 비교용: 이전 규칙 (실제 필터링에는 쓰지 않음) ───────────────
# 개정으로 무엇이 얼마나 달라졌는지 수치로 보기 위해서만 계산한다.
OLD_ASCII_RATIO = 0.70
OLD_EN_MARKER = re.compile(r"\b(the|and|of|is|it|you|that|for|with|this)\b", re.I)

# 정제용 정규식
RE_URL = re.compile(r"(https?://\S+|www\.\S+)")
RE_MENTION = re.compile(r"@\w+")
RE_WS = re.compile(r"\s+")


# ════════════════════════════════════════════════════════════════════════
# [1단계] 원본 적재
# ════════════════════════════════════════════════════════════════════════
def load_raw():
    """
    원본 JSON을 {계정ID: [(글 원문, 작성시각), ...]}로 펼친다.

    BotSim의 한 계정은 글을 세 군데에 나눠 갖고 있다(posts / comment_1 /
    comment_2). 셋을 구분하지 않고 "그 계정이 쓴 글"로 합친다.
    문체는 글의 종류가 아니라 쓴 주체에 붙는 성질이라고 보기 때문이다.
    """
    data = json.load(open(POSTS_JSON, encoding="utf-8"))
    raw = {}
    for uid, u in data.items():
        items = []
        for p in (u.get("posts") or []):
            items.append((str(p.get("posts") or ""),
                          str(p.get("created_utc") or "")))
        for block in ("comment_1", "comment_2"):
            for c in (u.get(block) or []):
                items.append((str(c.get("comment_body") or ""),
                              str(c.get("created_utc") or "")))
        if items:
            raw[uid] = items
    return raw


def load_labels():
    """
    봇/사람 라벨을 읽는다.
    BotSim은 '봇' 열이 없다. character_setting(그 계정에 부여된 캐릭터 설정
    프롬프트)이 채워져 있으면 시뮬레이션 봇, 비어 있으면 실제 사람 글이다.

    주의: 라벨은 '채점'에만 쓴다. 적격 판정에는 절대 쓰지 않는다.
          이 파일에서 라벨은 맨 마지막 집계 구간에서 처음 등장한다.
    """
    labels = {}
    with open(USERS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            setting = (row.get("character_setting") or "").strip()
            labels[row["user_id"]] = "bot" if setting else "human"
    return labels


# ════════════════════════════════════════════════════════════════════════
# [2단계] 문서 정제 — 언어는 보지 않는다
# ════════════════════════════════════════════════════════════════════════
def clean_doc(text):
    """
    글 1건을 정제한다. 통과하면 (정제 문자열, None, 절제여부),
    탈락하면 (None, 사유, 절제여부).

    순서가 중요하다.
      1) 자기폭로 문장 절제 — 남은 문장으로 계속 진행
      2) URL·멘션 제거
      3) 길이 검사 — 절제 뒤의 길이로 판정해야 정확하다
    URL을 먼저 지우고 길이를 재야, 링크만 잔뜩 붙은 짧은 글이 '긴 글'로
    위장되지 않는다.
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
            # 문서 전체가 자기폭로 문장뿐이었던 경우
            return None, "자기폭로 절제 후 내용 없음", True

    # (2) 링크·멘션 제거 — 문체가 아니라 행동의 흔적
    t = RE_URL.sub(" ", t)
    t = RE_MENTION.sub(" ", t)
    t = RE_WS.sub(" ", t).strip()

    # (3) 길이 검사
    if len(t) < MIN_CHARS:
        reason = ("자기폭로 절제 후 " if excised else "") + f"{MIN_CHARS}자 미만"
        return None, reason, excised
    return t, None, excised


def old_rule_pass(cleaned):
    """
    이전 판의 문서 단위 언어 필터. 비교용으로만 계산한다.
    (ASCII 비율 70% 이상 그리고 기능어 10개 중 1개 이상)
    """
    if not cleaned:
        return False
    ascii_n = sum(1 for c in cleaned if ord(c) < 128)
    if ascii_n / len(cleaned) < OLD_ASCII_RATIO:
        return False
    return bool(OLD_EN_MARKER.search(cleaned))


# ════════════════════════════════════════════════════════════════════════
# [3단계] 계정 구성 + 계정 단위 언어 판정
# ════════════════════════════════════════════════════════════════════════
def build_accounts(raw):
    """
    문서를 정제하고 계정을 구성한 뒤, 계정 단위로 언어를 판정한다.

    반환:
      accounts   {계정ID: [정제 문서, ...]}   ← 최종 적격 계정
      funnel     단계별 집계
      lang_info  계정별 언어 판정 결과(진단용)
    """
    import langid

    drop_reasons = Counter()
    n_docs_in = 0
    n_docs_trimmed = 0
    n_acct_short = 0
    old_rule_dropped_docs = 0     # 이전 규칙이었다면 지워졌을 문서 수
    n_excised = 0                 # 자기폭로 문장을 도려낸 문서 수
    n_excised_kept = 0            # 그중 살아남은 문서 수

    # ── 3-1. 문서 정제 + 계정 구성 ──────────────────────────────
    candidates = {}
    for uid, items in raw.items():
        rows = []
        for text, ts in items:
            n_docs_in += 1
            cleaned, reason, excised = clean_doc(text)
            if excised:
                n_excised += 1
            if cleaned is None:
                drop_reasons[reason] += 1
                continue
            if excised:
                n_excised_kept += 1
            if not old_rule_pass(cleaned):
                old_rule_dropped_docs += 1     # 집계만, 실제로 버리지 않음
            rows.append((str(ts or ""), cleaned))

        rows.sort(key=lambda r: r[0])          # 시각 오름차순
        if len(rows) > MAX_DOCS:
            n_docs_trimmed += len(rows) - MAX_DOCS
            rows = rows[-MAX_DOCS:]            # 최근분만
        if len(rows) >= MIN_DOCS:
            candidates[uid] = [c for _, c in rows]
        else:
            n_acct_short += 1

    # ── 3-2. 계정 단위 언어 판정 ────────────────────────────────
    # 계정의 글 전체를 합쳐 한 번 판정한다.
    # 긴 텍스트라 판정이 안정적이고, 문서 단위 선택 편향이 생기지 않는다.
    print(f"      계정 {len(candidates):,}개 언어 판정 중...", end=" ", flush=True)
    t0 = time.time()
    accounts, lang_info = {}, {}
    lang_counter = Counter()
    for uid, docs in candidates.items():
        joined = " ".join(docs)
        lang, score = langid.classify(joined)
        lang_info[uid] = {"lang": lang, "score": round(float(score), 1),
                          "chars": len(joined)}
        lang_counter[lang] += 1
        if lang == LANG_TARGET:
            accounts[uid] = docs
    print(f"{time.time()-t0:.1f}초")

    funnel = {
        "원본_계정수": len(raw),
        "원본_문서수": n_docs_in,
        "문서_탈락사유": dict(drop_reasons),
        "상한초과_절삭문서수": n_docs_trimmed,
        "문서부족_탈락계정수": n_acct_short,
        "언어판정_대상계정수": len(candidates),
        "언어별_계정수": dict(lang_counter.most_common()),
        "비영어_탈락계정수": len(candidates) - len(accounts),
        "적격_계정수": len(accounts),
        "적격_문서수": sum(len(v) for v in accounts.values()),
        "참고_이전규칙이면_탈락했을_문서수": old_rule_dropped_docs,
        "자기폭로_절제문서수": n_excised,
        "자기폭로_절제후_생존문서수": n_excised_kept,
    }
    return accounts, funnel, lang_info


def residual_language_check(accounts, sample_per_acct=5):
    """
    통과한 영어 계정 안에 비영어 문서가 얼마나 남아 있는지 진단한다.

    계정 단위 판정의 대가로, 영어 계정이 쓴 소수의 비영어 글은 그대로 남는다.
    그 양이 미미한지 확인해야 한다. 필터링에는 쓰지 않고 보고만 한다.
    (짧은 문서에 대한 언어 판정은 원래 불안정하므로 근사치로 읽을 것)
    """
    import langid
    import random
    rng = random.Random(20260817)
    n_en = n_other = 0
    other_langs = Counter()
    for uid, docs in accounts.items():
        for d in rng.sample(docs, min(sample_per_acct, len(docs))):
            lang, _ = langid.classify(d)
            if lang == LANG_TARGET:
                n_en += 1
            else:
                n_other += 1
                other_langs[lang] += 1
    total = n_en + n_other
    return {"표본문서수": total,
            "비영어_비율": round(n_other / total, 4) if total else None,
            "상위_비영어_판정": dict(other_langs.most_common(5))}


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 72)
    print("BotSim-24 적격 계정 검열  (2026-08-17 개정판)")
    print("=" * 72)
    print("문서 기준: 20자 이상 · 자기폭로 문구 없음  (언어 안 봄)")
    print("계정 기준: 최근 200건 이내 · 적격 문서 10건 이상 · langid 판정 en")
    print()

    print("[1/4] 원본 적재 중...")
    raw = load_raw()
    print(f"      계정 {len(raw):,}개")

    print("[2/4] 문서 정제 및 계정 구성 중...")
    print("[3/4] 계정 단위 언어 판정")
    accounts, funnel, lang_info = build_accounts(raw)

    print("[4/4] 라벨 대조 및 진단 중...")
    labels = load_labels()
    residual = residual_language_check(accounts)

    # ── 깔때기 ──────────────────────────────────────────────────
    print()
    print("─" * 72)
    print("깔때기")
    print("─" * 72)
    print(f"원본 계정                      {funnel['원본_계정수']:>8,}")
    print(f"원본 문서                      {funnel['원본_문서수']:>8,}")
    print()
    print("문서 탈락:")
    for reason, n in sorted(funnel["문서_탈락사유"].items(), key=lambda x: -x[1]):
        print(f"  - {reason:<22} {n:>8,}")
    print(f"  - 계정당 {MAX_DOCS}건 상한 초과       {funnel['상한초과_절삭문서수']:>8,}")
    print()
    print(f"문서 {MIN_DOCS}건 미만 탈락 계정          {funnel['문서부족_탈락계정수']:>8,}")
    print(f"언어 판정 대상 계정             {funnel['언어판정_대상계정수']:>8,}")
    print(f"  비영어로 판정돼 제외          {funnel['비영어_탈락계정수']:>8,}")
    print()
    print(f"적격 계정                      {funnel['적격_계정수']:>8,}")
    print(f"적격 문서                      {funnel['적격_문서수']:>8,}")

    # ── 언어 분포 ───────────────────────────────────────────────
    print()
    print("─" * 72)
    print("계정 단위 언어 판정 결과 (상위 8개)")
    print("─" * 72)
    for lang, n in list(funnel["언어별_계정수"].items())[:8]:
        mark = "  ← 채택" if lang == LANG_TARGET else ""
        print(f"  {lang:<6} {n:>6,}{mark}")

    # ── 개정 효과 ───────────────────────────────────────────────
    print()
    print("─" * 72)
    print("개정 효과 — 이전 규칙과의 차이")
    print("─" * 72)
    old_dropped = funnel["참고_이전규칙이면_탈락했을_문서수"]
    kept = funnel["적격_문서수"]
    print(f"  이전 규칙(문서 단위 영어 필터)이었다면 지워졌을 문서: {old_dropped:>8,}건")
    print(f"  현재 적격 문서 수:                                 {kept:>8,}건")
    if kept:
        print(f"  → 개정으로 되살아난 비율(적격 문서 대비):          {old_dropped/kept:>8.1%}")
    print()
    print("  이 문서들은 대부분 정상 영어인데 the/is/that 등이 없어 탈락했던 것이다.")
    print("  기능어 유무로 문서를 거르면, 기능어를 측정하는 이 연구에서는")
    print("  결과변수로 표본을 고르는 셈이 된다.")
    print()
    ex, exk = funnel["자기폭로_절제문서수"], funnel["자기폭로_절제후_생존문서수"]
    print(f"  자기폭로 문장을 도려낸 문서: {ex:,}건 (그중 {exk:,}건 생존, "
          f"{ex-exk:,}건은 남은 내용이 짧아 탈락)")
    print("  → 이전 판은 이 문서들을 통째로 버렸다. 삭제가 거의 봇에만 적용되므로")
    print("     (fox8 실측: 봇 1.16% vs 사람 0.00%) 문장만 절제해 비대칭을 줄인다.")

    # ── 잔여 비영어 진단 ────────────────────────────────────────
    print()
    print("─" * 72)
    print("잔여 비영어 문서 진단 (계정 단위 판정의 대가)")
    print("─" * 72)
    print(f"  표본 문서 {residual['표본문서수']:,}건 중 비영어 판정 "
          f"{residual['비영어_비율']:.2%}")
    if residual["상위_비영어_판정"]:
        print(f"  판정 내역: {residual['상위_비영어_판정']}")
    print("  ※ 짧은 문서의 언어 판정은 원래 불안정하다. 근사치로 읽을 것.")

    # ── 라벨 분포 (여기서 라벨이 처음 등장한다) ─────────────────
    lab_count = Counter(labels.get(uid, "라벨없음") for uid in accounts)
    docs_by_label = Counter()
    for uid, docs in accounts.items():
        docs_by_label[labels.get(uid, "라벨없음")] += len(docs)
    print()
    print("─" * 72)
    print("적격 계정의 라벨 분포")
    print("  (라벨은 위 판정 과정 어디에도 쓰이지 않았다. 여기서 처음 쓴다)")
    print("─" * 72)
    for lab, n in sorted(lab_count.items()):
        avg = docs_by_label[lab] / n if n else 0
        print(f"  {lab:<8} 계정 {n:>6,}   문서 {docs_by_label[lab]:>8,}   "
              f"(계정당 {avg:.1f}건)")
    print()
    print("  ※ 계정당 문서 수가 라벨 간에 크게 다르면, 이후 비교에서")
    print("     '분량 차이'가 '문체 차이'로 오해될 수 있다. 미리 확인해 둘 것.")

    # ── 저장 ────────────────────────────────────────────────────
    out = {
        "설정": {"MIN_CHARS": MIN_CHARS, "MIN_DOCS": MIN_DOCS,
                 "MAX_DOCS": MAX_DOCS, "LANG_TARGET": LANG_TARGET,
                 "언어판정도구": "langid.py (Lui & Baldwin, ACL 2012)",
                 "판정단위": "계정(글 전체 결합)"},
        "깔때기": funnel,
        "잔여비영어_진단": residual,
        "라벨분포": dict(lab_count),
        "계정": accounts,
        "라벨": {uid: labels.get(uid, "라벨없음") for uid in accounts},
        "언어판정": lang_info,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print()
    print(f"저장 완료: {OUT_JSON}")
    print("이후 단계(02·03)는 이 파일만 입력으로 사용한다.")


if __name__ == "__main__":
    main()
