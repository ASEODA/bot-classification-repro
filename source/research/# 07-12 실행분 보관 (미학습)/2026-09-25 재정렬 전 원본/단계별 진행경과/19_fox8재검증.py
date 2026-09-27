#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
19_fox8재검증.py
────────────────────────────────────────────────────────────────────────────
목적
    12가 낸 fox8 전이 결과에서 **자기폭로 문구를 가진 봇 계정을 전부 빼고**
    같은 계산을 다시 한다. 남는 것이 무엇인지 보는 것이 19의 일이다.

    ■ 왜 이 일을 하나 ■
    12의 로그에 이렇게 적혀 있다 — "자기폭로 문장이 걸린 문서 bot 1,160 ·
    human 1". 자기폭로 문구란 "as an ai language model" 같은, ChatGPT가
    거절할 때 뱉는 상투구다. fox8 봇넷은 바로 그 문구로 발견된 계정 무더기다.

    그렇다면 12의 전이 성공은 "더 쉬운 시험"이었을 수 있다. 라벨을 붙인
    사람이 그 문구를 보고 봇이라 적었고, 그 문구를 뱉는 계정은 애초에
    ChatGPT 원문을 그대로 흘리는 계정이므로 문체도 가장 기계에 가깝다.
    지문이 옮겨 간 것이 아니라 **가장 티 나는 봇만 골라 놓고 시험한 것**일
    수 있다는 뜻이다.

    19는 그 의심을 직접 시험한다. 자기폭로 문구가 원문에 한 번도 없는 봇
    계정만 남기고 — 즉 그 문구로는 발견될 수 없었던 봇만 남기고 — 12와
    똑같은 세 가족 비교와 전이 상관과 산포를 다시 낸다.

    ■ 결과를 미리 정해 두지 않는다 ■ 사전선언 19의 예측 넷은 "그래도 유지될
    것"이라고 적었다. 빗나가면 12의 전이 주장은 "자기폭로로 발견된 봇에
    한정"으로 좁힌다 — 사전선언이 그렇게 못 박았고, 그 문장을 [9/9]가
    결과와 무관하게 찍는다.

무엇을 따르나
    13-19_사전선언.md 의 「19 fox8 재검증」 절을 그대로 구현한다.
        봇 제한   자기폭로 문장이 원문에 한 번이라도 걸린 계정을 뺀다
                  ① 비리트윗 기준 — 12가 정제를 건 행 집합에서 걸린 계정을 뺀다
                  ② 엄격 기준 — 리트윗까지 포함해 어느 행에서도 안 걸린 계정만
                  둘 다 낸다. 사전선언의 "원문에 한 번도 없는"에 더 가까운
                  ②를 주 판정으로 삼고 ①은 보조로 함께 싣는다.
        사람      12와 동일 (그대로 둔다)
        주비교    12와 같은 세 BH 가족 — F 172종 · 형태자질 · UPOS
        전이      06·07의 방향 벡터와의 Spearman ρ, 12와 같은 구현
        산포      계정별 거리 δ, 12와 같은 방식
        예측 넷   아래 PREDICTIONS 상수에 박아 두고 [9/9]가 대조한다
    문턱(q ≤ 0.05 · |δ| ≥ 0.147)도 분모 규칙도 06·07·12와 같은 값을 쓴다.
    결과가 마음에 안 든다고 방법을 바꾸지 않는다.

■ 왜 다시 파싱하지 않는가 — 19의 가장 큰 결정 ■
    12는 fox8 문서 165,532건을 stanza로 파싱하는 데 한 시간 가까이 썼다.
    19가 그 일을 다시 할 이유가 있는지 먼저 따졌고, 없다고 판단했다.

        19가 바꾸는 것은 **비교에 들어가는 봇 계정의 명단**뿐이다.
        문서를 고르는 규칙도, 정제도, 파싱도, 세는 방법도 12와 같다.
        계정 하나의 카운트는 그 계정의 문서에서만 나오므로, 다른 계정을
        명단에서 빼도 남은 계정의 카운트는 한 자리도 바뀌지 않는다.

    12는 계정별 카운트를 **연도·답글 버킷으로 나누어 JSON에 저장해 두었다**
    (12_fox8전이.json 의 "계정" 블록). 19는 그 버킷을 다시 합쳐 12가 쓰던
    것과 똑같은 측정치 사전을 만든다. 덧셈은 결합법칙을 따르므로 결과가
    같아야 하고, [5/9]의 **재현 관문**이 그 '같아야 한다'를 말로만 두지 않고
    실제로 검사한다 — 봇을 하나도 빼지 않은 상태로 12의 δ를 다시 계산해
    12_fox8전이.json 에 적힌 값과 한 자리도 다르지 않은지 대조한다.
    한 항목이라도 어긋나면 본 계산에 들어가지 않고 멈춘다.

■ 2026-09-02 고침 ■
    처음 판(.19_fox8재검증_v1_리트윗버그.py)에는 조용한 결함이 있었다.
    scan_self_reveal 이 반환 사전을 비리트윗 카운터의 키로만 만들어, 리트윗
    에서만 걸린 계정이 사전에서 통째로 빠졌다. 그래서 "리트윗포함시_추가로_
    걸리는_잔류봇" 칸이 구조적으로 언제나 0으로 찍혔다 — 걸린 계정을 세는
    코드가 걸린 계정을 못 세고 있었고, 화면에는 아무 이상도 안 나왔다.
    고치고 나니 잔류 봇 187계정 중 70계정이 리트윗에서 자기폭로 문구에
    걸린다. 그 70을 마저 뺀 무더기(117계정)를 ② 엄격 기준으로 두고, 기존
    무더기(187)와 둘 다 계산한다. 앞 단계 산출물(01~12·13~18)은 손대지 않는다.

    다시 파싱해야 하는 것이 하나 남는다 — **자기폭로 판정**이다. 12는 걸린
    문서 수만 라벨별로 세고 계정별로는 남기지 않았다. 그래서 원본 sqlite를
    다시 훑어 12의 clean_doc 을 그대로 돌리고, 걸린 계정을 표시한다. 정규식
    한 번씩이라 몇십 초면 끝난다(파싱이 아니다).

산출
    19_fox8재검증.json · 19_fox8재검증_출력.log
    19_fox8재검증_진행.json (중간 저장. 전부 끝나면 지운다)

실행
    cd 연구주제 && python -u 19_fox8재검증.py 2>&1 | tee 19_fox8재검증_출력.log
    소표본 시험:  python -u 19_fox8재검증.py --소표본
        20계정(봇 10 · 사람 10)으로 파이프라인 전체를 한 번 돌려 본다.
        재현 관문은 표본이 달라 성립하지 않으므로 건너뛴다고 적고 넘어간다.
        본 실행 전에 반드시 한 번 통과시킨다.
"""

import ast
import functools
import hashlib
import json
import math
import os
import re
import sqlite3
import statistics
import sys
import time
import unicodedata
from collections import Counter

# 진행 표시가 즉시 화면에 찍히게 한다. [04·12에서 가져옴]
print = functools.partial(print, flush=True)


# ════════════════════════════════════════════════════════════════════════
# [경로]
# ════════════════════════════════════════════════════════════════════════
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = f"{HERE}/1. 원본데이터"
FOX8_DB = f"{BASE}/3. fox8 Data/fox8_23_dataset.sqlite"
KEEP = f"{HERE}/# 07-12 실행분 보관 (미학습)"      # 07~12 산출물이 있는 곳

ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"          # 01 — 라벨(BotSim)
MEASURE_JSON = f"{HERE}/04_기능어측정.json"         # 04 — 축 판별에 함께 넣는다
RATES_JSON = f"{HERE}/05_사용률검수.json"           # 05 — 희소성표(172종)
COMPARE_JSON = f"{HERE}/06_비교결과.json"           # 06 — F 블록 δ 기준선
SRC06_PY = f"{HERE}/06_봇사람비교.py"               # 통계 함수의 원본
FEATURE_JSON = f"{KEEP}/07_형태자질비교.json"        # 07 — M·UPOS δ 기준선, 축분류
DISPERSION_JSON = f"{KEEP}/09_산포검정.json"         # 09 — 산포 기준선
FOX8_JSON = f"{KEEP}/12_fox8전이.json"              # 12 — 계정별 버킷 카운트·기준값
SRC12_PY = f"{KEEP}/12_fox8전이.py"                 # 절차 함수의 원본

OUT_JSON = f"{HERE}/19_fox8재검증.json"
PROGRESS_JSON = f"{HERE}/19_fox8재검증_진행.json"


# ════════════════════════════════════════════════════════════════════════
# [설정 1] 01·12에서 그대로 가져온 정제 규칙 — 한 글자도 바꾸지 않는다
# ────────────────────────────────────────────────────────────────────────
# 19가 이 규칙을 쓰는 곳은 단 하나, **자기폭로 판정**이다. 12가 정제 단계에서
# 걸었던 그 정규식을 그대로 원문에 다시 걸어, 계정마다 한 번이라도 걸렸는지를
# 본다. 규칙을 조금이라도 바꾸면 12가 센 1,160건과 19가 세는 건수가 갈리고,
# 그러면 "12의 봇에서 자기폭로 계정을 뺐다"는 문장이 성립하지 않는다.
# ════════════════════════════════════════════════════════════════════════
MIN_CHARS = 20          # [01·12에서 가져옴] 정제 후 20자 미만 문서는 버린다
MIN_DOCS = 10           # [01·12에서 가져옴] 적격 문서 10건 미만 계정 제외
MAX_DOCS = 200          # [01·12에서 가져옴] 계정당 최근 200건까지

SELF_REVEAL = re.compile(
    r"(as an ai language model"
    r"|i'?m sorry,? but (i cannot|as an ai)"
    r"|i cannot (comply|fulfill|browse)"
    r"|openai'?s? (content )?polic)", re.I)

RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")      # [01·12에서 가져옴]
RE_URL = re.compile(r"(https?://\S+|www\.\S+)")       # [01·12에서 가져옴]
RE_MENTION = re.compile(r"@\w+")                      # [01·12에서 가져옴]
RE_WS = re.compile(r"\s+")                            # [01·12에서 가져옴]

FOX8_BOT_LABEL = "bot"
FOX8_HUMAN_LABEL = "human"
FOX8_KEY = "FOX8:"      # [12에서 가져옴] 계정 사전의 접두사


# ════════════════════════════════════════════════════════════════════════
# [설정 2] 06·07·12와 같은 판정 눈금
# ────────────────────────────────────────────────────────────────────────
# 부호 규약도 12와 같다. 그룹1 = fox8 봇(자기폭로 없는 계정만) · 그룹2 =
# fox8 사람. δ > 0 이면 봇이 높다.
# ════════════════════════════════════════════════════════════════════════
GROUP1, GROUP2 = "bot", "human"
BOT_LABEL = "bot"

Q_ALPHA = 0.05          # BH 보정 후 유의 판정 문턱 (06·07·12와 같은 값)
DELTA_NOTABLE = 0.147   # '주목'의 효과크기 하한 (앞 단계와 같음)
SPARSE_FRAC = 0.10      # 출현 계정이 전체의 이 비율 미만이면 '희소' 표시

RATE_DIGITS = 6         # 비율·중앙값 저장 자릿수
STAT_DIGITS = 4         # U·z·δ·ρ·AUC 저장 자릿수
SIG_DIGITS = 6          # p·q는 유효숫자로 자른다

DENOM_AXIS = "축내부합"
DENOM_TOKEN = "토큰수_구두점제외"

TOP_SHOW = 25           # 대조 표에 몇 줄을 띄울 것인가
SMALL_N = 10            # --소표본 모드에서 무더기당 계정 수

FUNCWORD_HASH = "382b68572f03bc23"   # 05 JSON이 적어 둔 기능어 172종 해시


# ════════════════════════════════════════════════════════════════════════
# [설정 3] 12 실행분의 값 — 나란히 놓고 견줄 기준선
# ────────────────────────────────────────────────────────────────────────
# 상수로 박아 두는 이유는 12와 같다. 결과가 나온 뒤에 12의 로그를 뒤지기
# 시작하면 나온 결과에 맞는 대목만 골라 인용하게 된다. 아래 값은 결과와
# 무관하게 [1/9]와 [9/9]가 같은 자리에 찍는다.
#
# ■ 사전선언 19가 적은 수와 12 실행분이 어긋나는 곳 ■
# 사전선언 19는 "봇 계정의 83.0%(945/1,139)가 자기폭로를 갖고 있었다 ·
# 예상 194 · 사람 1,139는 그대로"라고 적었다. 그런데 12 실행분의 실제
# 적격 계정은 **봇 1,094 · 사람 897**이다(12 로그 [2/9]). 사전선언의
# 945/1,139는 12를 돌리기 전의 어림이었고, 12는 그 어림과 어긋난 사실을
# 자기 로그에 이미 적어 두었다("적격 계정 · human: 다시 셈 897 ≠ 사전선언
# 1,080"). 19는 어림이 아니라 12 실행분을 잇는다 — 어림을 따라가면 12와
# 19가 서로 다른 자료를 견주게 된다. 어긋난 사실은 [4/9]가 표로 찍는다.
# ════════════════════════════════════════════════════════════════════════
V12_N_BOT = 1094                 # 12 실행분 적격 봇 계정
V12_N_HUMAN = 897                # 12 실행분 적격 사람 계정
V12_DOCS = 165532                # 12 실행분 적격 문서
V12_EXCISED_DOCS = {"bot": 1160, "human": 1}   # 12가 센 자기폭로 걸린 문서
V12_RHO = {"F블록": 0.3179, "형태자질": 0.3469, "UPOS": 0.3235}
V12_DIR_RATE = {"F블록": 0.5965, "형태자질": 0.6034, "UPOS": 0.4706}
V12_TOTAL_DELTA = -0.065         # 총사용률 δ
V12_TENSE_PAST_DELTA = -0.798    # Tense=Past δ
V12_DIST_DELTA = -0.974          # 계정별 거리 δ
V12_NOTABLE = {"F블록": 79, "형태자질": 27}     # 12의 주목 종수(참고)

# 사전선언 19가 적어 둔 어림. 실제 수와 나란히 찍기만 하고, 계산에는 쓰지 않는다.
PRE_EXPECT_SELFREVEAL_ACCOUNTS = 945
PRE_EXPECT_BOT_TOTAL = 1139
PRE_EXPECT_KEPT = 194

# 사전선언 19가 못 박은 문장. 결과와 무관하게 [9/9]가 그대로 찍는다.
NARROWING_LINE = ("P19-1이 빗나가면 12의 전이 주장은 "
                  "'자기폭로로 발견된 봇에 한정'으로 좁힌다.")


# ════════════════════════════════════════════════════════════════════════
# [사전 예측] 13-19_사전선언 「19」의 예측 넷
# ────────────────────────────────────────────────────────────────────────
# 판정은 07·12와 같은 규칙이다 — 문장 단위 전부-아니면-빗나감. 한 문장에
# 조건이 여럿이면 전부 충족해야 적중이다. 빗나간 예측도 지우지 않는다.
# ════════════════════════════════════════════════════════════════════════
PREDICTIONS = [
    {"번호": "P19-1",
     "문장": "세 집합의 방향 상관 ρ가 모두 양수로 유지된다(F ρ ≥ +0.20).",
     "판정근거": "세 가족 전체 ρ가 모두 > 0 이고, F블록 ρ ≥ +0.20 이면 적중.",
     "빗나가면": "12의 전이 주장을 '자기폭로로 발견된 봇에 한정'으로 좁힌다."},
    {"번호": "P19-2",
     "문장": "Tense=Past δ ≤ −0.50 유지.",
     "판정근거": "제한 표본의 형태자질 Tense=Past δ가 −0.50 이하면 적중.",
     "빗나가면": "과거시제 축이 자기폭로 봇에 얹혀 있던 신호였다는 뜻이다."},
    {"번호": "P19-3",
     "문장": "계정별 거리 δ < 0 유지(자기폭로 없는 봇끼리도 닮음).",
     "판정근거": "계정별 거리 중앙값의 봇 대 사람 δ가 0보다 작으면 적중.",
     "빗나가면": "동질성이 자기폭로 문구를 공유한 데서 왔다는 뜻이다."},
    {"번호": "P19-4",
     "문장": ("봇 194계정의 문서수 중앙값이 945계정보다 작다"
            "(발견되지 않은 봇은 활동량이 적다) — 표본 성격 기록."),
     "판정근거": "잔류 봇 문서수 중앙값 < 제외 봇 문서수 중앙값이면 적중. "
              "예측이라기보다 표본 성격의 기록이다.",
     "빗나가면": "발견되지 않은 봇이 오히려 더 많이 쓴다는 뜻이다."},
]


# ════════════════════════════════════════════════════════════════════════
# [자가검증 고정 예제] 06·12에서 그대로 가져온 상수
# ────────────────────────────────────────────────────────────────────────
#   (설명, A(=그룹1), B(=그룹2), 기대 U_A, 기대 δ, 기대 σ²)
# 손계산은 06_봇사람비교.py 의 self_check() docstring에 그대로 있다.
# ════════════════════════════════════════════════════════════════════════
SELF_CHECK_U = [
    ("완전 분리", [1, 2, 3], [4, 5, 6], 0.0, -1.0, 5.25),
    ("동점 포함", [1, 1, 2], [1, 2, 2], 3.0, -1.0 / 3.0, 4.05),
]
SELF_CHECK_BH_P = [0.01, 0.02, 0.03, 0.04]
SELF_CHECK_BH_Q = [0.04, 0.04, 0.04, 0.04]
SELF_CHECK_TOL = 1e-9

# [12에서 그대로 가져옴] 셋째가 동점 사례다. 단축 공식으로 풀면 0.95가 나와
# 실패한다 — 그것이 이 예제를 둔 이유다.
SELF_CHECK_RHO = [
    ("완전 양의 단조", [1.0, 2.0, 3.0, 4.0], [2.0, 4.0, 6.0, 8.0], 1.0),
    ("완전 음의 단조", [1.0, 2.0, 3.0, 4.0], [8.0, 6.0, 4.0, 2.0], -1.0),
    ("동점 포함", [1.0, 2.0, 2.0, 3.0], [1.0, 2.0, 3.0, 4.0],
     0.9486832980505138),      # = √0.9
]

# ── 19 고유 예제 1. 자기폭로 판정 ───────────────────────────────
# 손으로 답을 정해 둔 원문 다섯. 12의 clean_doc 이 세 번째 인자로 돌려주는
# '절제 여부'가 곧 자기폭로 판정이다.
#   (원문, 걸려야 하는가, 왜)
#
# ■ 두 번째와 세 번째 줄을 눈여겨보라 ■ 정규식에 'i cannot' 이 두 군데 나오고
# 둘이 서로 다르다.
#     i'?m sorry,? but (i cannot|as an ai)      ← 뒤 낱말을 가리지 않는다
#     i cannot (comply|fulfill|browse)          ← 세 낱말만 잡는다
# 그래서 "I'm sorry, but I cannot help…" 은 걸리고 "I cannot help…" 은 안
# 걸린다. 처음 이 예제를 적을 때 나는 둘을 하나로 읽고 앞엣것을 '안 걸림'
# 으로 적었다가 자가검증에 걸렸다. 관문이 실제로 한 일이 그것이라 예제를
# 고치되 이 주석은 남겨 둔다.
SELF_CHECK_REVEAL = [
    ("As an AI language model, I cannot browse the internet for you.",
     True, "상투구 그대로. 대소문자를 가리지 않아야 한다"),
    ("I'm sorry, but I cannot help with that request today, my friend.",
     True, "사과 가지는 뒤 낱말을 가리지 않는다 — i cannot 이면 걸린다"),
    ("I cannot help you with that request today, my friend.",
     False, "사과 없이 온 i cannot 은 comply·fulfill·browse 만 걸린다"),
    ("i'm sorry but as an ai i can't do that for you here today.",
     True, "곧은 아포스트로피 없는 im 형태도 i'?m 으로 잡아야 한다"),
    ("This violates OpenAI's content policy and I will not continue.",
     True, "openai'?s? (content )?polic 가 잡는다"),
    ("The weather in Seoul is lovely today and I am going outside.",
     False, "아무 상투구도 없다"),
]

# ── 19 고유 예제 2. 계정 단위 집계 ──────────────────────────────
# 문서 단위 판정을 계정 단위로 OR 하는 자리다. 한 건이라도 걸리면 그 계정은
# 제외다("원문에 한 번이라도 걸린 계정"). 손으로 만든 세 계정.
SELF_CHECK_ACCOUNT_REVEAL = {
    "acc_A": (["As an AI language model, I refuse to answer that question.",
               "Nice day for a walk in the park with the dogs today."],
              True),      # 한 건 걸림 → 제외
    "acc_B": (["Nice day for a walk in the park with the dogs today.",
               "The market closed higher again this afternoon in Seoul."],
              False),     # 한 건도 안 걸림 → 잔류
    "acc_C": (["openai's content policy blocks this one entirely, sorry.",
               "This one violates OpenAI's policy as well, I am afraid."],
              True),      # 두 건 걸림 → 제외
}

# ── 19 고유 예제 3. 봇 명단을 좁히면 δ가 어떻게 움직이나 ────────
# 19가 실제로 하는 일(봇 명단에서 몇을 빼고 같은 검정을 다시 돌리는 것)을
# 세 줄로 줄인 예제다. 손계산:
#   전체 봇 [1, 2, 3, 100] 대 사람 [4, 5, 6]
#     합쳐 정렬 1 2 3 4 5 6 100 → 봇의 순위 1,2,3,7 → R1 = 13
#     U1 = 13 − 4·5/2 = 3.0,  δ = 2·3/(4·3) − 1 = −0.5
#   봇에서 100을 빼면 [1, 2, 3] 대 [4, 5, 6]
#     U1 = 0,  δ = −1.0        ← 제한이 δ를 −0.5에서 −1.0으로 끌어내린다
# 명단을 좁히는 코드가 실제로 값을 바꾸는지, 바꾼다면 손계산과 같은 값으로
# 바꾸는지를 본다. "빼는 코드를 썼는데 아무것도 안 빠졌다"가 가장 조용한 실패다.
SELF_CHECK_RESTRICT = (
    [1.0, 2.0, 3.0, 100.0], [100.0], [4.0, 5.0, 6.0], 3.0, -0.5, 0.0, -1.0)

# ── 19 고유 예제 4. 버킷 합산 항등식 ────────────────────────────
# 19는 12가 저장한 연도·답글 버킷을 다시 합쳐 쓴다. 합쳐서 얻은 카운트가
# 손으로 더한 값과 같아야 한다. 덧셈의 결합법칙이 코드에서도 성립하는지를
# 보는 자리다.
SELF_CHECK_BUCKET = {
    "연도별": {
        "2023|0": {"문서수": 2, "문장수": 3, "토큰수": 30,
                   "토큰수_구두점제외": 25, "기능어": {"the": 4, "we": 1},
                   "UPOS": {"NOUN": 10, "PUNCT": 5},
                   "자질": {"Tense=Past": 2, "Tense=Pres": 3}},
        "2023|1": {"문서수": 1, "문장수": 2, "토큰수": 12,
                   "토큰수_구두점제외": 10, "기능어": {"the": 2, "must": 1},
                   "UPOS": {"NOUN": 6, "PUNCT": 2},
                   "자질": {"Tense=Past": 1}},
    }
}
SELF_CHECK_BUCKET_SUM = {"문서수": 3, "문장수": 5, "토큰수": 42,
                         "토큰수_구두점제외": 35,
                         "기능어": {"the": 6, "we": 1, "must": 1},
                         "UPOS": {"NOUN": 16, "PUNCT": 7},
                         "자질": {"Tense=Past": 3, "Tense=Pres": 3}}


# ════════════════════════════════════════════════════════════════════════
# [복사 대장] 어느 함수를 어느 파일에서 그대로 가져왔는가
# ────────────────────────────────────────────────────────────────────────
# 아래 두 목록은 장식이 아니다. [3/9]의 자가검증이 이 목록을 들고 06과 12의
# 원본 파일을 열어, **이 파일에 붙어 있는 함수의 소스와 원본의 소스가 글자
# 하나까지 같은지**를 대조한다. 하나라도 다르면 본 계산에 들어가지 않는다.
#
# ■ 왜 이런 검사를 하나 ■ 복사해 온 코드는 조용히 갈라진다. 여기서 한 줄을
# 고치면 19의 δ와 12의 δ가 다른 계산에서 나온 값이 되는데, 화면에는 아무
# 이상도 안 찍힌다. 12가 "복사 과정에서 부호 하나가 바뀌어도 코드는 멀쩡히
# 돌고 그럴듯한 p값이 나온다"고 적은 그 위험이다. 12는 그것을 고정 예제로
# 막았고, 19는 고정 예제에 더해 소스 대조까지 건다.
# ════════════════════════════════════════════════════════════════════════
COPIED_FROM_06 = ["normal_cdf", "ranks_with_ties", "mann_whitney",
                  "bh_qvalues", "quartiles", "sig", "direction_of"]
COPIED_FROM_12 = ["_disp", "rpad", "lpad", "line", "write_json", "rnd",
                  "fmt_dur", "five_number", "auc_from_delta", "auc_from_u",
                  "auc_strength", "pearson", "spearman", "direction_disp",
                  "clean_doc", "empty_counts", "merge_buckets",
                  "subset_measures", "compute_rates", "word_vector",
                  "word_presence", "build_axis_map", "axis_of",
                  "denom_kind_of", "compute_ratios", "compute_upos_ratios",
                  "defined_values", "compare_family", "family_summary",
                  "pair_with_baseline", "correlation_block",
                  "print_correlation", "print_pair_table", "iqr_of",
                  "abs_deviations", "brown_forsythe", "pack_disp",
                  "dense_vectors", "within_group_distances", "pile_table"]

# 06과 12에 같은 이름으로 들어 있으나 12판이 무언가를 더 하는 함수들이다.
# 이름이 겹치므로 06판은 아래에서 이름을 바꿔 보관하고, 실제 계산에는 12판을
# 쓴다. [3/9]가 두 판이 같은 답을 내는지 매 실행마다 확인한다.
#   mann_whitney   12판은 반환에 "n1n2" 한 칸을 더 담는다(AUC 검산용)
#   sig            12판은 None 을 받으면 None 을 돌려준다
#   direction_of   12판은 주어를 인자로 받는다(기본값이 06판과 같은 "봇이")
DUAL_NAMES = ["mann_whitney", "sig", "direction_of"]


# ════════════════════════════════════════════════════════════════════════
# [06에서 AST로 복사] 통계 함수 일곱
# ────────────────────────────────────────────────────────────────────────
# 명세가 못 박은 목록이다 — ranks_with_ties · mann_whitney · bh_qvalues ·
# normal_cdf · quartiles · sig · direction_of. 손으로 옮겨 적지 않고
# ast.get_source_segment 로 뽑아 붙였다. 06 파일의 함수 정의를 통째로,
# 주석과 docstring까지 그대로 가져온 것이라 아래 글은 06이 쓴 글이다.
# ════════════════════════════════════════════════════════════════════════
def normal_cdf(x):
    """
    표준정규분포의 누적확률 Φ(x) — "x보다 작을 확률".

    math.erf가 오차함수를 정확히 내 주므로 Φ(x) = ½(1 + erf(x/√2))로 끝난다.
    표를 들고 다니거나 근사식을 쓸 필요가 없다.

    한 가지 한계: |x|가 8을 넘어가면 Φ(x)가 배정도 실수에서 정확히 1.0이 되고
    1 − Φ(x)가 0.0으로 바닥을 친다. p = 0.0으로 찍히는 것은 "차이가 없을
    확률이 0"이라는 뜻이 아니라 "이 계산으로는 더 작은 값을 구분할 수 없다"는
    뜻이다. 어차피 그 언저리면 어떤 문턱으로도 유의다.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def ranks_with_ties(values):
    """
    값에 오름차순 순위를 매긴다. 같은 값끼리는 자리 번호를 나눠 갖는다.

    왜 평균 순위인가. [0.0, 0.0, 0.3]의 앞 두 값은 1등과 2등을 가릴 근거가
    없다. 둘 다 1.5등으로 두면 어느 무더기에 넣든 순위합이 같아져, 검정이
    동점을 '반반'으로 셈한다. 이 처리가 있어야 Cliff's δ의 동점 ½ 규칙이
    따로 코드를 쓰지 않고도 저절로 맞는다.

    여기서 동점은 흔한 정도가 아니라 지배적이다. 172종 중 상당수가 대부분의
    계정에서 0회라, 사용률 벡터의 절반 이상이 정확히 0.0인 단어가 수두룩하다.
    동점 처리와 아래의 분산 보정이 이 자료에서 특히 무겁게 걸리는 이유다.

    같은 값인지는 == 로 본다. 05가 사용률을 소수 6자리로 반올림해 저장했고
    0회는 아예 0.0이므로, '같은 값'은 실제로 똑같은 float이다. 부동소수
    오차를 허용 오차로 얼버무릴 자리가 아니다.

    반환: (입력 순서 그대로의 순위 리스트, 크기 2 이상인 동점 묶음 크기 목록)
    """
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    sv = [values[i] for i in order]
    ranks = [0.0] * n
    ties = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sv[j + 1] == sv[i]:
            j += 1
        # order[i..j]가 같은 값이다. 이들이 차지한 자리 번호는 i+1 … j+1 이고
        # 그 평균은 ((i+1) + (j+1)) / 2 다.
        avg = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        if j > i:
            ties.append(j - i + 1)
        i = j + 1
    return ranks, ties


def mann_whitney(group1, group2):
    """
    Mann-Whitney U 검정(양측)과 Cliff's δ를 한 번에 낸다. 그룹1 기준이다.

    무엇을 하는 계산인가. 두 무더기의 값을 한데 모아 순위를 매기고, 그룹1이
    가져간 순위의 합을 본다. 그룹1이 대체로 크면 순위합이 커지고, 대체로
    작으면 작아진다. 평균이 아니라 순위를 쓰므로 극단값 하나가 결과를 끌고
    가지 못하고, 분포 모양에 정규성 같은 가정을 걸 필요도 없다. 사용률처럼
    0에 몰리고 오른쪽으로 꼬리가 긴 자료에 맞는 도구다.

    ── 계산 순서 ─────────────────────────────────────────────
    N = n1 + n2 개를 오름차순 정렬, 동점은 평균 순위.

    R1 = 그룹1이 가져간 순위의 합.

    U1 = R1 − n1(n1+1)/2
         "그룹1끼리 서로 앞선 몫"을 빼낸 것이다. n1개가 최하위를 싹 쓸었을 때
         R1 = 1+2+…+n1 = n1(n1+1)/2 이므로, 그 값을 빼면 U1의 바닥이 0이 된다.
         남은 U1은 "그룹1의 값이 그룹2의 값보다 큰 쌍의 수"와 같다
         (동점 쌍은 ½씩). 최대는 모든 쌍을 이길 때의 n1·n2.

    δ = 2·U1/(n1·n2) − 1                                   (Cliff's δ)
         U1/(n1n2)는 이긴 쌍의 비율이다. 2배 하고 1을 빼면 −1 … +1로 펴진다.
         뜻: 무작위로 그룹1에서 하나, 그룹2에서 하나 뽑았을 때
             (그룹1이 클 확률) − (그룹2가 클 확률).
         동점은 평균 순위 덕에 자동으로 ½씩 갈려 이 정의와 맞아떨어진다.

    σ² = (n1·n2/12) · [ (N+1) − Σ(t³−t) / (N·(N−1)) ]      (동점 보정 분산)
         앞부분 n1n2(N+1)/12 가 동점이 없을 때의 U 분산이다. 뒤의 뺄셈이
         동점 보정으로, t는 각 동점 묶음의 크기다. 동점이 많으면 U가 취할 수
         있는 값의 폭이 좁아져 실제 분산이 작아진다. 이 항을 빼지 않으면
         분모를 부풀려 z를 줄이고, 있는 차이를 놓친다. 0.0이 잔뜩 깔린 희소
         단어에서 특히 크게 걸리는 항이다.

    z = (U1 − n1·n2/2 − c) / σ
         n1n2/2 는 "차이가 없을 때 U1이 있어야 할 자리"다. 거기서 얼마나
         떨어졌는지를 σ로 나눠 표준화한다. c는 연속성 보정으로, U는 반 칸씩
         띄엄띄엄한 값인데 정규분포는 이어져 있어 생기는 간극을 메운다.
         언제나 중앙 쪽으로 반 칸 당기는 방향이라 p를 보수적으로 만든다.
             U1 > n1n2/2 → c = +0.5
             U1 < n1n2/2 → c = −0.5
             정확히 중앙 → c = 0, z = 0

    양측 p = 2·(1 − Φ(|z|)), 1.0을 넘지 않게 자른다.
         "이만한 차이가 우연히 생길 확률"이다. 방향을 미리 정해 두지 않았으니
         양쪽 꼬리를 다 센다(사전선언: 양측).

    σ = 0이면 두 무더기의 값이 전부 같다는 뜻이다. 비교할 것이 없으므로
    δ = 0, z = 0, p = 1.0 으로 둔다. 172종 중 어느 계정에서도 나오지 않은
    단어가 있다면 여기로 온다.
    """
    n1, n2 = len(group1), len(group2)
    ranks, ties = ranks_with_ties(group1 + group2)
    r1 = sum(ranks[:n1])
    u1 = r1 - n1 * (n1 + 1) / 2.0
    n = n1 + n2

    tie_term = sum(t ** 3 - t for t in ties) / (n * (n - 1))
    var = (n1 * n2 / 12.0) * ((n + 1) - tie_term)
    if var <= 0.0:
        return {"U": u1, "z": 0.0, "p": 1.0, "델타": 0.0, "시그마제곱": 0.0}

    delta = 2.0 * u1 / (n1 * n2) - 1.0
    mid = n1 * n2 / 2.0
    if u1 > mid:
        c = 0.5
    elif u1 < mid:
        c = -0.5
    else:
        c = 0.0
    z = (u1 - mid - c) / math.sqrt(var)
    p = min(1.0, 2.0 * (1.0 - normal_cdf(abs(z))))
    return {"U": u1, "z": z, "p": p, "델타": delta, "시그마제곱": var}


def bh_qvalues(pvals):
    """
    Benjamini-Hochberg FDR 보정. p값 한 가족을 받아 q값을 같은 순서로 돌려준다.

    무엇을 하는 계산인가. 172번 검정하면 두 무더기가 실제로 똑같아도 우연히
    p < 0.05 인 단어가 여덟아홉 개는 나온다(172 × 0.05 ≈ 8.6). 그것을 발견이라
    부르면 안 된다. BH는 "유의하다고 부른 것들 중 헛것의 기대 비율(FDR)"을
    문턱 이하로 잡아 주는 방식이다.

        p를 오름차순으로 늘어놓고,  q_(i) = min_{j ≥ i} ( p_(j) · m / j )

    p_(i)·m/i 는 "i번째로 작은 p를 살리면 헛것 비율이 대략 얼마가 되는가"이고,
    뒤에서부터 최솟값을 끌고 오는 min이 q를 단조 증가로 만든다(더 작은 p가 더
    큰 q를 갖는 뒤집힘을 막는다). 1.0을 넘으면 1.0으로 자른다.

    본페로니(p × m)보다 훨씬 덜 가혹하다. 본페로니는 "헛것이 하나라도 있을
    확률"을 막느라 172로 나누는 문턱을 쓰고, 그러면 실제 차이도 거의 다
    놓친다. BH는 "발견 목록의 오염률"을 관리한다 — 탐색적 비교에 맞는 저울이다.

    이 함수는 단어 172종에만 쓴다. 총사용률 비교 1건은 가족 밖의 단독 검정이라
    보정 대상이 아니다.
    """
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    q = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):        # 가장 큰 p부터 거꾸로 훑는다
        idx = order[rank - 1]
        val = pvals[idx] * m / rank
        if val < running:               # min_{j ≥ i} 를 누적으로 구현
            running = val
        q[idx] = min(1.0, running)
    return q


def quartiles(values):
    """중앙값과 사분위수 한 벌. 값이 둘 미만이면 사분위가 성립하지 않는다."""
    if len(values) < 2:
        m = values[0] if values else 0.0
        return {"Q1": m, "중앙": m, "Q3": m}
    # method="inclusive"는 가진 자료가 모집단 전체일 때 쓰는 정의다(05와 같다).
    q1, med, q3 = statistics.quantiles(sorted(values), n=4, method="inclusive")
    return {"Q1": q1, "중앙": med, "Q3": q3}


def sig(x, digits=SIG_DIGITS):
    """
    p·q를 유효숫자 기준으로 자른다.

    소수 자릿수로 반올림하면(round(p, 6)) 3e-40 같은 값이 통째로 0이 된다.
    유효숫자로 자르면 크기를 잃지 않으면서 파일이 짧아진다.
    """
    if x == 0.0:
        return 0.0
    return float(f"{x:.{digits}g}")


def direction_of(delta):
    """δ의 부호를 말로 옮긴다. 그룹1 = 봇으로 고정되어 있어야 뜻이 맞다."""
    if delta > 0:
        return "봇이 높음"
    if delta < 0:
        return "봇이 낮음"
    return "차이 없음"


# ── 06판 보관 ───────────────────────────────────────────────────
# 아래 12 블록이 같은 이름으로 세 함수를 다시 정의한다. 06판을 잃지 않도록
# 여기서 이름을 바꿔 붙들어 둔다. [3/9]가 두 판을 나란히 돌려 대조한다.
mann_whitney_06 = mann_whitney
sig_06 = sig
direction_of_06 = direction_of


# ════════════════════════════════════════════════════════════════════════
# [12에서 AST로 복사] 적재·정제·분모·비교·상관·산포의 절차 함수
# ────────────────────────────────────────────────────────────────────────
# 12_fox8전이.py 에서 그대로 뽑아 붙였다. 12가 07·09·11에서 가져왔다고 적어
# 둔 함수는 그 표기가 docstring에 그대로 남아 있다 — 출처의 사슬이 코드 안에
# 보이게 두는 편이 낫다.
#
# 여기 없는 12의 함수는 19가 쓰지 않는 것들이다(완화 A·B의 Wilcoxon, 산점도,
# 단독 AUC 순위표, 출처 4분할, sqlite 실태표…). 사전선언 19가 요구한 것은
# 주비교 세 집합 · 전이 상관 · 계정별 거리 셋이고, 요구하지 않은 계산을
# 덧붙이지 않는다.
# ════════════════════════════════════════════════════════════════════════
def _disp(s):
    """
    터미널에서 이 문자열이 차지하는 칸 수. 한글·한자는 두 칸이다. [11에서 가져옴]

    len()으로 폭을 맞추면 한글이 든 칸만 오른쪽으로 밀린다.
    """
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def rpad(s, width):
    """폭 width에 오른쪽 정렬. 한글 두 칸을 셈에 넣는다. [11에서 가져옴]"""
    return " " * max(0, width - _disp(s)) + s


def lpad(s, width):
    """폭 width에 왼쪽 정렬. 한글 두 칸을 셈에 넣는다. [11에서 가져옴]"""
    return s + " " * max(0, width - _disp(s))


def line(title=""):
    """구분선 한 줄. [09에서 가져옴]"""
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다. [04·09·10·11에서 가져옴]

    임시 파일에 먼저 쓰고 이름을 바꿔치기한다(os.replace). 중간 저장 파일을
    쓰는 도중에 창을 닫으면 파일이 반쯤 잘린 채 남고, 다음 실행에서 그 파일을
    읽다 깨진다. 이름 바꾸기는 쪼개지지 않는 연산이라, 어느 시점에 멈춰도
    파일은 '이전 것' 아니면 '새 것'이다. 한 시간짜리 작업에서 이것이 있고
    없고는 크다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def sig(x, digits=SIG_DIGITS):
    """
    p·q를 유효숫자 기준으로 자른다. [09에서 가져옴]

    소수 자릿수로 반올림하면(round(p, 6)) 3e-40 같은 값이 통째로 0이 된다.
    유효숫자로 자르면 크기를 잃지 않으면서 파일이 짧아진다.
    """
    if x is None:
        return None
    if x == 0.0:
        return 0.0
    return float(f"{x:.{digits}g}")


def rnd(x, digits):
    """None을 그대로 통과시키는 round. [09에서 가져옴] 검정 불가 칸이 None이라 필요하다."""
    return None if x is None else round(x, digits)


def fmt_dur(sec):
    """초를 사람이 읽는 단위로 바꾼다. [04에서 가져옴]"""
    if sec < 90:
        return f"{sec:.0f}초"
    if sec < 5400:
        return f"{sec / 60:.1f}분"
    return f"{sec / 3600:.2f}시간"


def five_number(values):
    """최소·Q1·중앙·Q3·최대 한 벌. [09에서 가져옴]"""
    if not values:
        return {"n": 0, "최소": None, "Q1": None, "중앙": None,
                "Q3": None, "최대": None}
    q = quartiles(values)
    return {"n": len(values), "최소": min(values), "Q1": q["Q1"],
            "중앙": q["중앙"], "Q3": q["Q3"], "최대": max(values)}


def mann_whitney(group1, group2):
    """
    Mann-Whitney U 검정(양측)과 Cliff's δ. 그룹1 기준. [09에서 가져옴]

        R1  = 그룹1이 가져간 순위의 합
        U1  = R1 − n1(n1+1)/2            (그룹1이 이긴 쌍의 수, 동점은 ½)
        δ   = 2·U1/(n1·n2) − 1           (Cliff's δ, −1 … +1)
        σ²  = (n1·n2/12)·[(N+1) − Σ(t³−t)/(N(N−1))]      (동점 보정 분산)
        z   = (U1 − n1·n2/2 − c)/σ       (c = ±0.5 연속성 보정)
        p   = 2·(1 − Φ(|z|))             (양측)

    σ² ≤ 0 이면 두 무더기의 값이 전부 같다는 뜻이라 δ = 0, z = 0, p = 1.0.

    ■ 12에서 이 함수가 하나 더 하는 일 ■
    U1 은 그대로 **단독 AUC의 분자**다. AUC = U1/(n1·n2) 이고, 위 δ 정의와
    합치면 AUC = (δ+1)/2 가 된다. 그래서 이 함수를 한 번 부르면 검정과
    효과크기와 단독 판별력이 한꺼번에 나온다 — 새로 계산할 것이 없다.
    n1·n2 를 함께 돌려주어 AUC를 두 길로 검산할 수 있게 한다.
    """
    n1, n2 = len(group1), len(group2)
    ranks, ties = ranks_with_ties(group1 + group2)
    r1 = sum(ranks[:n1])
    u1 = r1 - n1 * (n1 + 1) / 2.0
    n = n1 + n2

    tie_term = sum(t ** 3 - t for t in ties) / (n * (n - 1))
    var = (n1 * n2 / 12.0) * ((n + 1) - tie_term)
    if var <= 0.0:
        return {"U": u1, "z": 0.0, "p": 1.0, "델타": 0.0, "시그마제곱": 0.0,
                "n1n2": n1 * n2}

    delta = 2.0 * u1 / (n1 * n2) - 1.0
    mid = n1 * n2 / 2.0
    if u1 > mid:
        c = 0.5
    elif u1 < mid:
        c = -0.5
    else:
        c = 0.0
    z = (u1 - mid - c) / math.sqrt(var)
    p = min(1.0, 2.0 * (1.0 - normal_cdf(abs(z))))
    return {"U": u1, "z": z, "p": p, "델타": delta, "시그마제곱": var,
            "n1n2": n1 * n2}


def direction_of(delta, subj="봇이"):
    """
    δ의 부호를 말로 옮긴다. 위치 검정용 문구다(06·07과 같은 뜻). [11에서 가져옴]
    """
    if delta > 0:
        return f"{subj} 높음"
    if delta < 0:
        return f"{subj} 낮음"
    return "차이 없음"


def direction_disp(delta, subj="봇이"):
    """
    산포 검정용 문구. [09·11에서 가져옴]

    같은 δ라도 순위를 매긴 대상이 값이 아니라 절대편차라 뜻이 다르다.
    δ < 0 이면 그룹1의 절대편차가 작다 = 그룹1이 더 뭉쳐 있다. 위치 δ와
    한 표에 섞어 읽지 말 것.
    """
    if delta > 0:
        return f"{subj} 더 흩어짐"
    if delta < 0:
        return f"{subj} 더 뭉침"
    return "차이 없음"


def auc_from_delta(delta):
    """
    Cliff's δ 를 단독 AUC로 옮긴다.  AUC = (δ + 1) / 2.

    δ 가 None(검정 불가)이면 None을 돌려준다 — 0.5를 돌려주면 "판별력이
    없다"로 읽히는데 사실은 "잴 수 없었다"이기 때문이다.
    """
    return None if delta is None else (delta + 1.0) / 2.0


def auc_from_u(u1, n1n2):
    """
    U 통계량으로 곧장 낸 단독 AUC.  AUC = U1 / (n1·n2).

    auc_from_delta 와 값이 같아야 한다. 두 길을 다 두는 이유는 [3/9]에서
    서로 검산시키기 위해서다 — 한 길만 검사하면 옮겨 적다 생긴 오류를 못
    잡는다. 본 계산에는 auc_from_delta 를 쓴다(δ가 이미 표에 있으므로).
    """
    return None if (u1 is None or not n1n2) else u1 / n1n2


def auc_strength(auc):
    """
    |AUC − 0.5|. 항목의 '세기'다. 방향은 여기서 빠지고 부호로 따로 읽는다.

    0.0 이면 동전 던지기, 0.5 면 완전 분리다.
    """
    return None if auc is None else abs(auc - 0.5)


def pearson(xs, ys):
    """
    피어슨 적률상관. [11에서 가져옴]

        r = Σ(x−x̄)(y−ȳ) / √( Σ(x−x̄)² · Σ(y−ȳ)² )

    한쪽 분산이 0이면(모든 값이 같으면) 분모가 0이라 정의되지 않는다.
    그때는 None을 돌려준다 — 0.0을 돌려주면 "상관이 없다"로 읽히는데,
    사실은 "상관을 말할 수 없다"이기 때문이다.
    """
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0.0 or syy <= 0.0:
        return None
    return sxy / math.sqrt(sxx * syy)


def spearman(xs, ys):
    """
    Spearman 순위상관. 두 벡터에 각각 순위를 매기고 순위끼리 피어슨을 낸다.
    [11에서 가져옴]
    """
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    rx, _ = ranks_with_ties(xs)
    ry, _ = ranks_with_ties(ys)
    return pearson(rx, ry)


def clean_doc(text):
    """
    글 1건을 정제한다. [01에서 한 글자도 고치지 않고 가져옴 · 11을 경유]

    통과하면 (정제 문자열, None, 절제여부), 탈락하면 (None, 사유, 절제여부).

    순서가 중요하다.
      1) 자기폭로 문장 절제 — 남은 문장으로 계속 진행
      2) URL·멘션 제거
      3) 길이 검사 — 절제 뒤의 길이로 판정해야 정확하다
    URL을 먼저 지우고 길이를 재야, 링크만 잔뜩 붙은 짧은 글이 '긴 글'로
    위장되지 않는다.

    ■ fox8에서 이 순서가 특히 크게 작동한다 ■
    트윗은 t.co 단축 링크를 본문에 그대로 달고 다닌다("https://t.co/xxxxxxxxxx"
    가 23자다). 링크를 지우기 전에 길이를 재면 링크만 붙은 한 마디짜리 트윗이
    20자 문턱을 넘어 들어온다. 멘션도 마찬가지다 — 답글은 본문 앞에
    "@아무개"가 줄줄이 붙는데, fox8은 답글 비율이 봇 49.2% · 사람 22.8%로
    어긋나 있어 멘션을 지우지 않으면 그 어긋남이 곧바로 길이 필터의
    비대칭으로 이어진다. RE_MENTION 이 그것을 지운다.
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

    # (2) 링크·멘션 제거 — 문체가 아니라 행동의 흔적
    t = RE_URL.sub(" ", t)
    t = RE_MENTION.sub(" ", t)
    t = RE_WS.sub(" ", t).strip()

    # (3) 길이 검사
    if len(t) < MIN_CHARS:
        reason = ("자기폭로 절제 후 " if excised else "") + f"{MIN_CHARS}자 미만"
        return None, reason, excised
    return t, None, excised


def empty_counts():
    """04와 같은 꼴의 빈 카운트 한 벌."""
    return {"문서수": 0, "문장수": 0, "토큰수": 0, "토큰수_구두점제외": 0,
            "기능어": {}, "UPOS": {}, "자질": {}}


def merge_buckets(buckets, pick=None):
    """
    버킷 여럿을 04 꼴의 카운트 한 벌로 합친다.

    pick — 버킷 이름을 받아 참/거짓을 돌려주는 함수. None이면 전부 더한다.
    반환은 04의 계정 한 칸과 완전히 같은 모양이라, 뒤의 compute_rates ·
    compute_ratios · compute_upos_ratios 가 04의 자료를 다룰 때와 한 글자도
    다르지 않게 동작한다. 부분집합 분석마다 계산 코드를 새로 쓰지 않는
    것이 요점이다 — 새로 쓰면 그 사본이 언젠가 본체와 갈라진다.
    """
    out = empty_counts()
    for key, c in buckets.items():
        if pick is not None and not pick(key):
            continue
        out["문서수"] += c["문서수"]
        out["문장수"] += c["문장수"]
        out["토큰수"] += c["토큰수"]
        out["토큰수_구두점제외"] += c["토큰수_구두점제외"]
        for field in ("기능어", "UPOS", "자질"):
            dst = out[field]
            for k, n in c[field].items():
                dst[k] = dst.get(k, 0) + n
    return out


def subset_measures(measures, uids, pick=None):
    """
    계정별로 원하는 버킷만 합쳐 '04 꼴 측정치 사전'을 만든다.

    이 한 함수가 12의 부분집합 분석 전부를 떠받친다.
        주 비교      pick = None                        (전부)
        완화 A       pick = 연도가 2019 또는 2020        (사람만)
        완화 B 후    pick = 연도가 2023                  (봇만)
        보조 분석    pick = 답글이 아님                  (양쪽)
    돌려받은 사전은 04의 "계정" 블록과 모양이 같으므로 뒤의 모든 계산 코드가
    그대로 돌아간다.

    문서가 하나도 없는 계정(그 부분집합에 해당 문서가 없는 계정)은 빼고
    돌려준다. 남겨 두면 분모가 0이 되어 '분모 0 계정'으로 세어지는데, 그것은
    나눗셈 불성립이 아니라 애초에 표본에 없는 계정이다. 둘을 섞으면 안 된다.
    """
    out = {}
    for uid in uids:
        rec = measures.get(uid)
        if not rec:
            continue
        merged = merge_buckets(rec["연도별"], pick)
        if merged["문서수"] > 0:
            out[uid] = merged
    return out


def compute_rates(measures, prefix=""):
    """
    계정마다 단어별 사용률과 총 사용률을 낸다. [05·11에서 가져옴]

    분모는 토큰수_구두점제외 하나로 고정이다(05-06 사전선언 결정 1). 구두점
    습관은 R 블록이 다룰 신호라 F 블록과 섞지 않는다. 트윗은 구두점 습관이
    레딧과 크게 다를 수 있어(해시태그·말줄임·이모지) 이 분리가 12에서 더
    중요하다.

    희소 저장은 04·05의 방식을 그대로 잇는다 — 0회인 단어는 담지 않는다.
    없는 키 = 0으로 읽으면 되고, 아래 word_vector()가 그 규약을 지킨다.

    prefix — 계정에 붙일 접두사([설정 2]). 트위터 user_id와 레딧 계정 ID가
    우연히 같아도 두 자료가 한 사전에서 서로를 덮어쓰지 않게 한다.

    자릿수도 05와 같은 RATE_DIGITS로 자른다. 05가 저장해 둔 BotSim 사용률과
    같은 눈금이어야 두 무더기를 견줄 수 있다.
    """
    rates, undefined = {}, []
    for uid in sorted(measures):
        a = measures[uid]
        denom = a["토큰수_구두점제외"]
        if denom == 0:
            undefined.append(uid)
            continue
        counts = a["기능어"]
        rates[prefix + uid] = {
            "총사용률": round(sum(counts.values()) / denom, RATE_DIGITS),
            "분모": denom,
            "사용률": {w: round(n / denom, RATE_DIGITS)
                     for w, n in counts.items()},
        }
    return rates, undefined


def word_vector(uids, rates, word):
    """
    한 단어에 대해, 주어진 계정들의 사용률을 순서대로 늘어놓는다. [06·09·10·11에서]

    ■ 여기가 F 블록에서 가장 틀리기 쉬운 한 줄이다. ■
    사용률은 '희소 저장'이라 한 번도 안 쓴 단어는 그 계정의 사전에 아예 키가
    없다. 그래서 .get(word, 0.0) 의 기본값 0.0이 반드시 있어야 한다. 없는
    키를 건너뛰면 "그 단어를 한 번도 안 쓴 계정"이 통째로 표본에서 사라지고,
    정작 재려던 '덜 쓴다'가 바로 그 사라진 0들이다. 결과 전체가 뒤집힌다.
    """
    return [rates[u]["사용률"].get(word, 0.0) for u in uids]


def word_presence(uids, rates, words):
    """주어진 표본 안에서 각 단어를 한 번이라도 쓴 계정 수. [09에서 가져옴]"""
    out = {w: 0 for w in words}
    for u in uids:
        used = rates[u]["사용률"]
        for w in words:
            if used.get(w, 0.0) > 0:
                out[w] += 1
    return out


def build_axis_map(measures):
    """
    자료 전체를 훑어 축마다 어떤 값들이 나타나는지 모은다. [07에서 가져옴]

    12는 여기에 **04의 계정 전부 + fox8 계정 전부**를 넘긴다(위 주석 참조).

    반환: {축 이름: 정렬된 값 목록}
    """
    axis_values = {}
    for a in measures.values():
        for key in a.get("자질", {}):
            axis, sep, val = key.partition("=")
            if not sep:
                axis, val = key, ""
            axis_values.setdefault(axis, set()).add(val)
    return {ax: sorted(vs) for ax, vs in axis_values.items()}


def axis_of(key):
    """자질 키에서 축 이름만 떼어 낸다. [07에서 가져옴] "="가 없으면 키 전체가 축이다."""
    return key.split("=", 1)[0]


def denom_kind_of(key, axis_map):
    """
    이 자질에 어떤 분모를 쓸지 정한다. [07에서 가져옴] 사전선언 07의 표 그대로다.

        대립값 ≥ 2  →  그 계정의 해당 축 총 출현수      (DENOM_AXIS)
        대립값 = 1  →  그 계정의 토큰수_구두점제외      (DENOM_TOKEN)
    """
    return DENOM_AXIS if len(axis_map.get(axis_of(key), [""])) >= 2 else DENOM_TOKEN


def compute_ratios(measures, keys, axis_map):
    """
    계정마다 자질 비율을 낸다. [07에서 가져옴] 반환은 (판정용, 보조용, 출현계정수).

    없는 키는 0회다 — 결측이 아니다. 결측 판정은 오로지 분모로만 한다.
        Tense=Past 0회, Tense=Pres 12회  →  0 / 12 = 0.0    (값이 있다)
        Tense 축 자체가 0회              →  0 / 0  = 결측   (나눗셈 불성립)
    """
    kinds = {k: denom_kind_of(k, axis_map) for k in keys}
    ratios, aux, presence = {}, {}, {k: 0 for k in keys}

    for uid in sorted(measures):
        a = measures[uid]
        feats = a.get("자질", {})
        denom_tok = a.get("토큰수_구두점제외", 0)

        axis_total = {}
        for k, n in feats.items():
            ax = axis_of(k)
            axis_total[ax] = axis_total.get(ax, 0) + n

        row, arow = {}, {}
        for k in keys:
            cnt = feats.get(k, 0)          # ← 없는 키는 0회. 위 설명을 보라.
            if cnt:
                presence[k] += 1
            if kinds[k] == DENOM_AXIS:
                d = axis_total.get(axis_of(k), 0)
            else:
                d = denom_tok
            row[k] = None if d == 0 else cnt / d
            arow[k] = None if denom_tok == 0 else cnt / denom_tok
        ratios[uid] = row
        aux[uid] = arow
    return ratios, aux, presence


def compute_upos_ratios(measures, keys):
    """
    품사 비율. [07에서 가져옴] 분모는 언제나 토큰수_구두점제외다(사전선언 07).

    PUNCT 줄만은 분모가 구두점을 뺀 수인데 분자는 구두점 수라 '말 토큰 대비
    구두점'이라는 다른 뜻의 값이 된다. 07·08·09·10·11이 그랬듯 12도 그 줄을
    해석하지 않는다.
    """
    ratios, presence = {}, {k: 0 for k in keys}
    for uid in sorted(measures):
        a = measures[uid]
        pos = a.get("UPOS", {})
        denom = a.get("토큰수_구두점제외", 0)
        row = {}
        for k in keys:
            cnt = pos.get(k, 0)            # ← 없는 키는 0회 (자질과 같은 규율)
            if cnt:
                presence[k] += 1
            row[k] = None if denom == 0 else cnt / denom
        ratios[uid] = row
    return ratios, presence


def defined_values(uids, ratios, key):
    """
    결측(None)을 뺀 값만 순서대로 늘어놓는다. [07에서 가져옴]

    결측은 그 자질의 검정에서만 빠진다. 계정이 통째로 빠지는 것이 아니라
    칸 하나가 빠지는 것이라, 같은 계정이 Tense 검정에는 들어가고 Mood 검정에는
    빠질 수 있다. 그래서 유효 계정 수가 자질마다 다르고, 표에 그 수를 싣는다.
    """
    out = []
    for u in uids:
        v = ratios[u][key]
        if v is not None:
            out.append(v)
    return out


def compare_family(keys, g1_ids, g2_ids, getter, presence, sparse_cut,
                   kinds=None, subj="봇이"):
    """
    한 가족을 통째로 검정하고 BH를 건다. [07의 compare_family + 09의 getter 방식]

    계산은 07과 한 글자도 다르지 않다. 달라진 것은 값을 꺼내는 방법을 밖에서
    넣어 준다는 것뿐이다 — F 블록은 사용률에서(word_vector), M·UPOS는 07의
    분모 규칙으로 만든 비율에서(defined_values) 꺼낸다.

    그룹1 = 봇, 그룹2 = 사람이다([설정 4]). δ > 0 이면 봇이 높다. 06·07과
    같은 부호 규약이다.

    ■ 단독 AUC를 여기서 함께 낸다 ■ 결정 0-2가 요구한 특징별 단독 효과다.
    AUC = (δ+1)/2 이므로 새로 계산할 것이 없고, U 로 낸 값과 어긋나지
    않는지를 그 자리에서 검산해 '환산검산' 칸에 남긴다.

    ■ BH 가족에서 검정 불가 항목을 빼는 이유 ■
    한쪽 무더기가 비면 U를 계산할 수 없다. p가 없는 항목을 BH에 넣을 방법이
    없으므로(m만 부풀린다) 가족에서 뺀다. 뺀 개수는 화면과 JSON에 그대로
    적는다 — m이 58이 아니라 56이었다는 사실은 q값의 뜻을 바꾸므로 숨기면
    안 된다. 이것은 사후 문턱이 아니다. 문턱은 "값이 있는데 작아서 버리는
    것"이고, 여기는 값 자체가 없다.

    반환: (|δ| 내림차순 (키, 결과) 목록, 검정 가능 항목 수)
    """
    n_all = len(g1_ids) + len(g2_ids)
    rows = []
    for k in keys:
        v1 = getter(g1_ids, k)
        v2 = getter(g2_ids, k)
        r = {
            "축": axis_of(k),
            "분모종류": (kinds or {}).get(k, DENOM_TOKEN),
            "봇_유효n": len(v1),
            "사람_유효n": len(v2),
            "결측계정수": n_all - len(v1) - len(v2),
            "출현계정수": presence.get(k, 0),
            "희소": presence.get(k, 0) < sparse_cut,
        }
        if not v1 or not v2:
            r.update({"검정가능": False, "U": None, "z": None, "p": None,
                      "q": None, "델타": None, "방향": "검정 불가",
                      "봇_중앙": None, "사람_중앙": None,
                      "단독AUC": None, "AUC세기": None, "환산검산": None,
                      "유의": False, "주목": False})
        else:
            res = mann_whitney(v1, v2)
            auc_d = auc_from_delta(res["델타"])
            auc_u = auc_from_u(res["U"], res["n1n2"])
            r.update({"검정가능": True, "U": res["U"], "z": res["z"],
                      "p": res["p"], "델타": res["델타"],
                      "방향": direction_of(res["델타"], subj),
                      "봇_중앙": statistics.median(v1),
                      "사람_중앙": statistics.median(v2),
                      "단독AUC": auc_d,
                      "AUC세기": auc_strength(auc_d),
                      "환산검산": abs(auc_d - auc_u) <= 1e-9})
        rows.append((k, r))

    testable = [(k, r) for k, r in rows if r["검정가능"]]
    qs = bh_qvalues([r["p"] for _, r in testable])
    for (k, r), q in zip(testable, qs):
        r["q"] = q
        r["유의"] = q <= Q_ALPHA
        r["주목"] = r["유의"] and abs(r["델타"]) >= DELTA_NOTABLE

    # 검정 불가는 |δ|를 −1로 쳐서 맨 뒤로 보낸다(δ의 하한이 −1이라 겹치지 않는다).
    rows.sort(key=lambda kv: -(abs(kv[1]["델타"]) if kv[1]["검정가능"] else -1.0))
    return rows, len(testable)


def family_summary(rows, n_family, sparse_cut, n_all, label):
    """가족 하나의 요약을 찍는다. [07·11의 family_summary · 주어만 봇으로]"""
    sig_n = sum(1 for _, r in rows if r["유의"])
    notable = [(k, r) for k, r in rows if r["주목"]]
    up = sum(1 for _, r in notable if r["델타"] > 0)
    down = sum(1 for _, r in notable if r["델타"] < 0)
    sparse_n = sum(1 for _, r in notable if r["희소"])
    untestable = sum(1 for _, r in rows if not r["검정가능"])
    bad_conv = sum(1 for _, r in rows if r["환산검산"] is False)

    print(f"\n      [{label}] BH 가족 크기                  {n_family:>4}종 "
          f"/ {len(rows)}종")
    if untestable:
        print(f"        검정 불가로 가족에서 빠짐           {untestable:>4}종")
    print(f"        유의 (q ≤ {Q_ALPHA})                      {sig_n:>4}종")
    print(f"        주목 (q ≤ {Q_ALPHA} 그리고 |δ| ≥ {DELTA_NOTABLE})   "
          f"{len(notable):>4}종")
    print(f"          봇이 높음                          {up:>4}종")
    print(f"          봇이 낮음                          {down:>4}종")
    print(f"          그중 희소 표시                     {sparse_n:>4}종")
    print(f"        (희소 = 그 항목이 나온 계정이 {sparse_cut:,}개 미만 — "
          f"비교 표본 {n_all:,}계정의 {SPARSE_FRAC:.0%})")
    if bad_conv:
        print(f"        ■ AUC 환산 검산 실패 {bad_conv}종 — (δ+1)/2 와 U/(n1n2)가")
        print("          어긋났다. 순위 계산이 두 곳에서 갈렸다는 뜻이다.")
    return {
        "가족크기": n_family,
        "대상종수": len(rows),
        "검정불가": untestable,
        "유의": sig_n,
        "주목": len(notable),
        "봇이높음": up,
        "봇이낮음": down,
        "희소포함": sparse_n,
        "AUC환산검산_실패": bad_conv,
        "주목목록": [k for k, _ in notable],
    }


def pair_with_baseline(rows, baseline):
    """
    12의 δ에 06·07의 δ를 나란히 붙이고 부호 일치를 판정한다.

    ■ 각 칸의 뜻 ■
        BotSim델타   06 또는 07이 낸 δ (BotSim 봇 대 BotSim 사람)
        fox8델타     12가 낸 δ (fox8 봇 대 fox8 사람)
        BotSim주목   앞 단계에서 q ≤ 0.05 이면서 |δ| ≥ 0.147 이었는가
        주목         12에서 같은 두 조건을 넘었는가
        부호일치     두 δ의 부호가 같은가
        단독AUC      (δ_fox8 + 1)/2 — 그 항목 하나로 낸 판별력
        추적         BotSim에서 주목이었던 항목이 fox8에서 어떻게 되었나

    ■ δ가 정확히 0인 항목을 어떻게 다루나 ■
    부호일치를 None으로 둔다. 0은 "같은 방향"도 "다른 방향"도 아니다.
    한쪽으로 몰아 넣으면 "아무도 그 단어를 안 썼다"는 사실이 방향 주장으로
    둔갑한다. 일치율의 분모에서도 뺀다(그 수를 따로 보고한다).

    ■ '유지/약화/역방향' — 12가 쓰는 어휘 ■
    08·10은 같은 자료를 다른 조건으로 다시 잰 것이라 '유지/무너짐'을 물을
    수 있었고, 11은 다른 자료라 방향만 물었다. 12는 그 중간이다 — 다른
    자료지만 **같은 물음**(봇 대 사람)을 던지므로 "옮겨 갔는가"를 물을 수
    있다. 다만 '무너짐'이라는 말은 쓰지 않는다. fox8에서 작다고 BotSim의
    값이 틀린 것이 아니기 때문이다. 그래서 약화라고 적는다.
        역방향   부호가 반대
        유지     부호가 같고 |δ_fox8| ≥ 0.147
        약화     부호가 같고 |δ_fox8| < 0.147
    """
    out = []
    for k, r in rows:
        b = (baseline or {}).get(k) or {}
        d_old = b.get("델타")
        prior_notable = bool(b.get("주목"))
        d_new = r["델타"] if r["검정가능"] else None

        if d_old is None or d_new is None or d_old == 0.0 or d_new == 0.0:
            same = None
        else:
            same = (d_old > 0) == (d_new > 0)

        if d_new is None:
            track = "검정불가"
        elif same is None:
            track = "방향 없음"
        elif not same:
            track = "역방향"
        elif abs(d_new) >= DELTA_NOTABLE:
            track = "유지"
        else:
            track = "약화"

        out.append((k, {
            "BotSim델타": d_old,
            "BotSim주목": prior_notable,
            "BotSimAUC": rnd(auc_from_delta(d_old), STAT_DIGITS),
            "fox8델타": rnd(d_new, STAT_DIGITS),
            "차이": rnd(d_new - d_old, STAT_DIGITS)
                  if (d_old is not None and d_new is not None) else None,
            "q": sig(r.get("q")),
            "방향": r.get("방향"),
            "주목": bool(r.get("주목")),
            "부호일치": same,
            "추적": track,
            "단독AUC": rnd(r.get("단독AUC"), STAT_DIGITS),
            "AUC세기": rnd(r.get("AUC세기"), STAT_DIGITS),
            "봇_유효n": r.get("봇_유효n"),
            "사람_유효n": r.get("사람_유효n"),
            "출현계정수": r.get("출현계정수"),
            "희소": bool(r.get("희소")),
        }))
    return out


def correlation_block(pairs, only_prior_notable=False):
    """
    한 가족의 δ 벡터 상관과 방향 일치율을 낸다. [11에서 가져옴]

    only_prior_notable=True 면 06·07에서 주목이었던 항목만 추린다.

    ■ 왜 따로 내나 ■
    가족 전체에는 δ가 0 근처인 항목이 많다. 그런 항목의 δ는 대부분 잡음이라
    두 자료에서 서로 무관하게 흩어지고, 그 흩어짐이 상관을 0 쪽으로 끌어
    내린다(희석). 그래서 전체 ρ가 낮아도 "주목 항목에서는 잘 맞는다"가
    성립할 수 있다. 두 값을 나란히 놓아야 이 구분이 보인다.

    ■ 그런데 판정에는 전체를 쓴다 ■
    "주목이었던 것만 고른다"는 선택은 앞 단계 결과를 보고 하는 선택이다.
    예측 1의 판정에 그것을 쓰면 사전등록의 뜻이 옅어진다.

    반환: 기록용 사전. x·y 벡터도 함께 담아 산점도가 다시 계산하지 않게 한다.
    """
    xs, ys, keys = [], [], []
    for k, c in pairs:
        if c["BotSim델타"] is None or c["fox8델타"] is None:
            continue
        if only_prior_notable and not c["BotSim주목"]:
            continue
        keys.append(k)
        xs.append(c["BotSim델타"])
        ys.append(c["fox8델타"])

    rho = spearman(xs, ys)
    zero = sum(1 for x, y in zip(xs, ys) if x == 0.0 or y == 0.0)
    judged = len(xs) - zero
    same = sum(1 for x, y in zip(xs, ys)
               if x != 0.0 and y != 0.0 and (x > 0) == (y > 0))
    return {
        "항목수": len(xs),
        "rho": rnd(rho, STAT_DIGITS),
        "방향일치수": same,
        "방향판정대상": judged,
        "방향일치율": rnd(same / judged, 4) if judged else None,
        "델타0_제외수": zero,
        "x_BotSim": xs,
        "y_fox8": ys,
        "항목목록": keys,
    }


def print_correlation(label, whole, notable):
    """가족 하나의 상관 두 벌(전체·주목 한정)을 나란히 찍는다. [11에서 가져옴]"""
    def fmt(block):
        rho = block["rho"]
        rate = block["방향일치율"]
        return (f"{block['항목수']:>5}종   "
                f"ρ = {('  —' if rho is None else f'{rho:+.4f}')}   "
                f"방향 일치 {block['방향일치수']:>4}/{block['방향판정대상']:<4}"
                f"({'  —' if rate is None else f'{rate:.1%}'})")

    print(f"\n      [{label}]")
    print(f"        가족 전체      {fmt(whole)}")
    print(f"        앞 주목 한정   {fmt(notable)}")
    if whole["델타0_제외수"]:
        print(f"        (δ가 정확히 0이라 방향 판정에서 뺀 항목 "
              f"{whole['델타0_제외수']}종. ρ 계산에는 들어간다.)")


def print_pair_table(pairs, base_label, title, limit=None):
    """
    δ_BotSim 과 δ_fox8 을 한 줄에 놓고 단독 AUC와 추적 판정을 붙인다.
    [08·10·11의 대조표를 12의 판정에 맞게]
    """
    shown = pairs if limit is None else pairs[:limit]
    if not shown:
        print("\n      띄울 줄이 없습니다.")
        return
    print(f"\n      {title}")
    print(f"      항목          {base_label} δ   fox8 δ      차이   단독AUC"
          "          q  추적    비고")
    for k, c in shown:
        if c["fox8델타"] is None or c["BotSim델타"] is None:
            reason = ("12 검정불가" if c["fox8델타"] is None
                      else f"{base_label}에 없음")
            print(f"      {k:<12}{'—':>7}{'—':>9}{'—':>10}{'—':>9}{'—':>11}  "
                  f"{'—':<6}  {reason}")
            continue
        note = []
        if c["BotSim주목"]:
            note.append(f"{base_label}주목")
        if c["주목"]:
            note.append("12주목")
        if c["희소"]:
            note.append("희소")
        print(f"      {k:<12}{c['BotSim델타']:>+7.3f}{c['fox8델타']:>+9.3f}"
              f"{c['차이']:>+10.3f}{c['단독AUC']:>9.3f}{c['q']:>11.4f}  "
              f"{lpad(c['추적'], 6)}  {' '.join(note)}")


def iqr_of(values):
    """사분위 범위 Q3 − Q1. [09에서 가져옴] 값이 둘 미만이면 0.0."""
    if len(values) < 2:
        return 0.0
    q = quartiles(values)
    return q["Q3"] - q["Q1"]


def abs_deviations(values):
    """
    그 무더기의 **자기 중앙값**에서 잰 절대편차. [09에서 가져옴] Brown-Forsythe의 재료다.

    ■ 왜 그룹별 중앙값인가 ■
    두 무더기를 합친 공통 중앙값을 쓰면, 위치가 다른 무더기는 그것만으로
    편차가 커진다. 그러면 표에는 '산포가 크다'로 찍히지만 실제로 잰 것은
    '위치가 다르다'다. 각 무더기에서 자기 중앙값을 빼면 두 무더기가 같은
    자리로 옮겨진 뒤 흩어짐만 남는다.

    반환된 편차들의 중앙값이 곧 그 무더기의 MAD다.
    """
    med = statistics.median(values)
    return [abs(v - med) for v in values], med


def brown_forsythe(v1, v2, subj="봇이"):
    """
    두 무더기의 산포를 견준다. 그룹1 기준. [09에서 가져옴 · 주어만 인자로]

        1. 각 무더기에서 그 무더기의 중앙값을 뺀 절대편차를 만든다.
        2. 두 절대편차 무더기를 Mann-Whitney U로 견주고 Cliff's δ를 낸다.
        3. δ < 0  →  그룹1의 절대편차가 작다  =  그룹1이 더 뭉쳐 있다.

    IQR·MAD·중앙값을 함께 담아 돌려준다. 검정이 "어느 쪽이 넓은가"만
    말한다면 IQR·MAD는 "얼마나 넓은가"를 말한다. 둘 다 있어야 읽힌다.
    한쪽이 비면 None을 돌려준다(검정 불가).
    """
    if not v1 or not v2:
        return None
    d1, m1 = abs_deviations(v1)
    d2, m2 = abs_deviations(v2)
    res = mann_whitney(d1, d2)
    iqr1, iqr2 = iqr_of(v1), iqr_of(v2)
    return {
        "검정가능": True,
        "U": res["U"], "z": res["z"], "p": res["p"],
        "델타": res["델타"], "방향": direction_disp(res["델타"], subj),
        "그룹1_중앙": m1, "그룹2_중앙": m2,
        "그룹1_IQR": iqr1, "그룹2_IQR": iqr2,
        "그룹1_MAD": statistics.median(d1), "그룹2_MAD": statistics.median(d2),
        # 비는 언제나 그룹2(사람) ÷ 그룹1이다. 1보다 크면 사람이 넓다.
        # 그룹1의 IQR이 0이면 나눗셈이 성립하지 않아 None — '무한대'가 아니라
        # '이 자료로는 비를 말할 수 없다'로 읽어야 한다.
        "IQR비": (iqr2 / iqr1) if iqr1 > 0 else None,
        "MAD비": (statistics.median(d2) / statistics.median(d1))
                if statistics.median(d1) > 0 else None,
        "그룹1_유효n": len(v1), "그룹2_유효n": len(v2),
    }


def pack_disp(r):
    """산포 결과 한 칸을 JSON에 담을 꼴로 바꾼다. [09의 pack_one · 11 경유]"""
    if r is None or not r.get("검정가능"):
        return {"검정가능": False, "델타": None, "q": None, "방향": "검정 불가"}
    return {
        "검정가능": True,
        "U": rnd(r["U"], 1), "z": rnd(r["z"], STAT_DIGITS),
        "p": sig(r["p"]), "q": sig(r["p"]),
        "q비고": "가족 밖 단독 검정이라 q = p (m = 1 에서 BH는 항등).",
        "델타": rnd(r["델타"], STAT_DIGITS), "방향": r["방향"],
        "그룹1_중앙": rnd(r["그룹1_중앙"], RATE_DIGITS),
        "그룹2_중앙": rnd(r["그룹2_중앙"], RATE_DIGITS),
        "그룹1_IQR": rnd(r["그룹1_IQR"], RATE_DIGITS),
        "그룹2_IQR": rnd(r["그룹2_IQR"], RATE_DIGITS),
        "그룹1_MAD": rnd(r["그룹1_MAD"], RATE_DIGITS),
        "그룹2_MAD": rnd(r["그룹2_MAD"], RATE_DIGITS),
        "IQR비": rnd(r["IQR비"], STAT_DIGITS),
        "MAD비": rnd(r["MAD비"], STAT_DIGITS),
        "그룹1_유효n": r["그룹1_유효n"], "그룹2_유효n": r["그룹2_유효n"],
    }


def dense_vectors(uids, rates, words):
    """
    계정마다 172차원 사용률 벡터를 만든다. [09에서 가져옴] 희소 저장을 조밀하게 편다.

    없는 키는 0.0이다 — word_vector()와 같은 규율이고 같은 이유다. 안 쓴
    단어를 빠뜨리면 벡터의 길이가 계정마다 달라져 거리를 잴 수 없다.
    """
    return [[rates[u]["사용률"].get(w, 0.0) for w in words] for u in uids]


def within_group_distances(vecs):
    """
    한 무더기 안의 모든 계정쌍 L1 거리. [09에서 가져옴] n개면 n(n−1)/2 쌍이다.

        L1(a, b) = Σ_j |a_j − b_j|          (172개 성분의 절대차 합)

    ■ 왜 L1인가 ■
    유클리드(L2)는 큰 성분 하나에 제곱으로 끌려간다. 172종 중 the·of·to
    같은 몇 단어가 사용률의 대부분을 차지하므로, L2를 쓰면 사실상 그 몇
    단어의 거리가 된다. L1은 모든 성분을 같은 무게로 더한다.

    ■ 반환 ■ (모든 쌍 거리 목록, 계정별 거리 목록)

    ■ 속도 ■ fox8은 두 무더기가 각각 천 계정을 넘는다. 봇 1,100이면 60만
    쌍, 사람 1,080이면 58만 쌍이다. 172성분을 곱하면 2억 번대의 뺄셈이라
    몇십 초가 걸린다. [9/9]가 미리 규모를 찍고 시간을 잰다.
    """
    n = len(vecs)
    dists = []
    per = [[] for _ in range(n)]
    for i in range(n - 1):
        vi = vecs[i]
        pi = per[i]
        for j in range(i + 1, n):
            d = sum(abs(a - b) for a, b in zip(vi, vecs[j]))
            dists.append(d)
            pi.append(d)
            per[j].append(d)
    return dists, per


def pile_table(name_values):
    """
    무더기별 다섯 숫자와 IQR·MAD를 한 표로 찍는다. [11에서 가져옴]

    name_values — [(무더기 이름, 값 목록), ...] 순서대로 찍는다.
    반환: {이름: {n, 중앙, IQR, MAD, 다섯숫자}}
    """
    out = {}
    print("        무더기          계정      중앙       IQR       MAD")
    for name, vals in name_values:
        if not vals:
            print(f"        {lpad(name, 12)}{0:>7,}   (비어 있음)")
            out[name] = {"n": 0, "중앙": None, "IQR": None, "MAD": None,
                         "다섯숫자": five_number([])}
            continue
        med = statistics.median(vals)
        devs, _ = abs_deviations(vals)
        mad = statistics.median(devs)
        iqr = iqr_of(vals)
        print(f"        {lpad(name, 12)}{len(vals):>7,}{med:>10.4f}"
              f"{iqr:>10.4f}{mad:>10.4f}")
        out[name] = {"n": len(vals), "중앙": rnd(med, RATE_DIGITS),
                     "IQR": rnd(iqr, RATE_DIGITS), "MAD": rnd(mad, RATE_DIGITS),
                     "다섯숫자": {k: rnd(v, RATE_DIGITS)
                              for k, v in five_number(vals).items()}}
    return out


# ════════════════════════════════════════════════════════════════════════
# [19 고유] 복사 무결성 대조 — 붙여 넣은 소스가 원본과 같은가
# ════════════════════════════════════════════════════════════════════════
def func_sources(path):
    """
    파이썬 파일에서 최상위 함수 정의의 소스를 이름별로 뽑는다.

    ast.get_source_segment 은 정의가 차지한 줄 전체를 원문 그대로 돌려준다 —
    데코레이터 없는 최상위 def 라면 "def" 부터 본문 끝까지다. 그래서 이
    함수로 뽑은 문자열끼리 비교하면 '글자 하나까지 같은가'를 물을 수 있다.

    실패하면 예외를 올린다. 원본을 못 읽는 상태로 자가검증을 통과시키면
    검사가 있으나 마나다.
    """
    src = open(path, encoding="utf-8").read()
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef):
            out[node.name] = ast.get_source_segment(src, node)
    return out


def source_of_self(name, dup_index=0):
    """
    이 파일 자신에서 함수 하나의 소스를 뽑는다. 같은 이름이 두 번 정의된
    함수(mann_whitney·sig·direction_of)는 dup_index 로 몇 번째인지 고른다.

    0 = 위쪽(06 블록) · 1 = 아래쪽(12 블록). 두 판을 각각 제 원본과 맞춰야
    하므로 순서를 알아야 한다.
    """
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    found = [n for n in ast.parse(src).body
             if isinstance(n, ast.FunctionDef) and n.name == name]
    if dup_index >= len(found):
        return None
    return ast.get_source_segment(src, found[dup_index])


def sha16(text):
    """문자열의 sha256 앞 16자. 로그에 적을 짧은 지문."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def check_copies():
    """
    COPIED_FROM_06 · COPIED_FROM_12 의 함수가 원본과 글자까지 같은지 본다.

    이름이 겹치는 셋은 06판을 앞쪽(dup_index 0), 12판을 뒤쪽(1)에서 찾아
    각각 제 원본과 맞춘다.

    반환: (통과 여부, 기록용 목록)
    """
    src06 = func_sources(SRC06_PY)
    src12 = func_sources(SRC12_PY)
    rows, ok = [], True

    for name in COPIED_FROM_06:
        mine = source_of_self(name, 0)
        theirs = src06.get(name)
        good = mine is not None and theirs is not None and mine == theirs
        ok = ok and good
        rows.append({"함수": name, "출처": "06", "해시": sha16(theirs),
                     "일치": good})
    for name in COPIED_FROM_12:
        idx = 1 if name in DUAL_NAMES else 0
        mine = source_of_self(name, idx)
        theirs = src12.get(name)
        good = mine is not None and theirs is not None and mine == theirs
        ok = ok and good
        rows.append({"함수": name, "출처": "12", "해시": sha16(theirs),
                     "일치": good})
    return ok, rows


# ════════════════════════════════════════════════════════════════════════
# [19 고유] 자기폭로 판정 — 원문에 한 번이라도 걸린 계정을 찾는다
# ════════════════════════════════════════════════════════════════════════
def scan_self_reveal(conn, progress=None):
    """
    fox8 원본 sqlite 의 **모든 행**에 12의 clean_doc 을 다시 걸어, 자기폭로
    문구가 한 번이라도 걸린 계정을 두 벌로 표시한다 — 비리트윗 행에서만
    걸린 횟수와, 리트윗까지 합친 횟수.

    ■ 왜 두 벌인가 ■
    12가 정제를 건 자리는 비리트윗 행이다(SELECT … WHERE is_retweet = 0).
    12의 판정 규칙을 그대로 쓰라는 것이 사전선언의 지시이므로 그 행 집합의
    카운트를 그대로 둔다. 그러나 사전선언 19의 문구는 "자기폭로 문장이
    **원문에 한 번도 없는** 계정"이다. 리트윗도 그 계정의 타임라인에 실제로
    실린 원문이고, 그 문구로 그 계정이 발견될 수 있었던 경로다. 그래서
    리트윗까지 합친 카운트를 함께 남겨, 두 기준의 무더기를 둘 다 낸다.
        비리트윗 기준   12의 정제 대상과 같은 행 집합
        엄격 기준       리트윗 포함, 어떤 행에서도 걸리지 않은 계정만 남긴다

    ■ 왜 정제를 통과한 문서만 보지 않나 ■
    사전선언이 "자기폭로 문장이 **원문에** 한 번도 없는 계정"이라고 적었다.
    20자 미만이라 버려진 글이나 200건 상한에 밀려난 글에 상투구가 있었다면,
    그 계정은 그 문구로 발견될 수 있었던 계정이다. 살아남은 문서만 보면
    그런 계정이 '자기폭로 없음'으로 새어 들어온다.

    ■ 2026-09-02 고침 ■ 처음 판은 반환 사전을 `hit`(비리트윗 카운터)의 키로만
    만들었다. 리트윗에서만 걸린 계정은 `hit` 에 키가 없으므로 사전에서 통째로
    빠졌고, 그래서 "리트윗포함시_추가로_걸리는_잔류봇"이 구조적으로 언제나
    0으로 찍혔다. 걸린 계정을 세는 코드가 걸린 계정을 못 세는, 조용한 종류의
    실패다. 아래에서 두 카운터의 **합집합**으로 사전을 만든다.

    반환: {uid: {"걸린문서수": n, "걸린문서수_리트윗포함": n2}}
          (둘 중 하나라도 1 이상인 계정 전부. 비리트윗 0 · 리트윗 3 인 계정도
           키가 있고, 그 계정은 "걸린문서수": 0 으로 남는다.)
    """
    if progress and progress.get("자기폭로"):
        print("      진행 파일에 자기폭로 판정 결과가 있어 그대로 씁니다.")
        return progress["자기폭로"]

    cur = conn.cursor()
    hit, hit_rt = Counter(), Counter()
    n_rows = n_rows_rt = 0
    t0 = time.time()
    for uid, text, is_rt in cur.execute(
            "SELECT user_id, text, is_retweet FROM tweets"):
        if not uid:
            continue
        _, _, excised = clean_doc(text)
        if is_rt:
            n_rows_rt += 1
            if excised:
                hit_rt[uid] += 1
            continue
        n_rows += 1
        if excised:
            hit[uid] += 1
            hit_rt[uid] += 1
    print(f"      비리트윗 {n_rows:,}행 + 리트윗 {n_rows_rt:,}행 훑기 "
          f"{time.time() - t0:.1f}초")
    # 두 카운터의 합집합으로 만든다. hit 의 키만 쓰면 리트윗에서만 걸린 계정이
    # 통째로 빠진다(위 docstring의 '2026-09-02 고침').
    print(f"      걸린 계정  비리트윗 기준 {len(hit):,} · "
          f"리트윗 포함 {len(set(hit) | set(hit_rt)):,}")
    return {uid: {"걸린문서수": hit.get(uid, 0),
                  "걸린문서수_리트윗포함": hit_rt.get(uid, 0)}
            for uid in sorted(set(hit) | set(hit_rt))}


# ════════════════════════════════════════════════════════════════════════
# [19 고유] 진행 체크포인트 — 중간에 끊겨도 이어서 한다
# ════════════════════════════════════════════════════════════════════════
def load_progress(fingerprint):
    """
    진행 파일을 읽는다. 입력 지문이 다르면 버린다.

    지문이 다르다는 것은 12 JSON이나 sqlite가 그 사이에 바뀌었다는 뜻이다.
    바뀐 입력 위에 옛 중간값을 얹으면 두 자료가 섞인 결과가 나오는데, 화면
    에는 아무 이상도 안 찍힌다. 그래서 버리고 처음부터 한다.
    """
    if not os.path.exists(PROGRESS_JSON):
        return {}
    try:
        d = json.load(open(PROGRESS_JSON, encoding="utf-8"))
    except (ValueError, OSError):
        print("      진행 파일을 읽을 수 없어 무시합니다.")
        return {}
    if d.get("입력지문") != fingerprint:
        print("      진행 파일의 입력 지문이 지금 입력과 다릅니다 — 버리고 "
              "처음부터 합니다.")
        return {}
    return d


def save_progress(d):
    """진행 파일을 덮어쓴다. 완료 후 [9/9]가 지운다."""
    write_json(PROGRESS_JSON, d)


def input_fingerprint():
    """
    입력 세 개의 크기·수정시각으로 만든 지문. 진행 파일의 유효성 판단에 쓴다.

    내용 해시를 쓰지 않는 이유는 12 JSON이 11 MB, sqlite가 120 MB이기 때문이다.
    매 실행마다 통째로 해시하면 그 자체가 시간을 잡아먹는다. 크기와 수정
    시각이면 '그 사이에 바뀌었는가'를 가리기에 충분하다.
    """
    parts = []
    for p in (FOX8_JSON, FOX8_DB, MEASURE_JSON):
        st = os.stat(p)
        parts.append(f"{os.path.basename(p)}:{st.st_size}:{int(st.st_mtime)}")
    return sha16("|".join(parts))


# ════════════════════════════════════════════════════════════════════════
# [19 고유] 자가검증 — 손으로 푼 예제를 먼저 통과시킨다
# ════════════════════════════════════════════════════════════════════════
def self_check():
    """
    검정 기계와 19 고유 규칙을 손으로 푼 예제와 맞춘다. 하나라도 어긋나면
    본 계산에 들어가지 않는다.

    ── (1) 06의 세 고정 예제 ─────────────────────────────────
        완전 분리 · 동점 포함 · BH 보정. 손계산은 06의 self_check()
        docstring에 그대로 있다. 06·07·09·10·11·12가 전부 이 예제를 걸었고
        19도 같은 자리에 건다.

    ── (2) 06판과 12판이 같은 답을 내는가 ────────────────────
        mann_whitney·sig·direction_of 는 06과 12에 같은 이름으로 있고 12판이
        무언가를 더 한다. 두 판을 나란히 돌려 겹치는 칸이 전부 같은지 본다.
        다르면 19의 δ는 06의 δ와 다른 기계에서 나온 값이 된다.

    ── (3) Spearman 셋 ───────────────────────────────────────
        [12에서 가져옴] 셋째가 동점 사례다. 전이 상관이 이 함수 위에 서 있다.

    ── (4) 19 고유 — 자기폭로 판정 여섯 ──────────────────────
        SELF_CHECK_REVEAL 의 여섯 문장. 둘째와 셋째가 짝이다 — 사과 가지가
        앞에 붙은 "I cannot" 은 걸리고, 사과 없이 온 "I cannot help" 는
        안 걸린다. 정규식의 두 'i cannot' 이 서로 다른 것을 잡기 때문이며,
        이 구분이 무너지면 봇 무더기가 필요 이상으로 줄어 남은 봇이
        '자기폭로 없는 봇'이 아니라 '아무 사과도 안 하는 봇'이 된다.

    ── (5) 19 고유 — 계정 단위 OR ────────────────────────────
        문서 판정을 계정 판정으로 올리는 자리. 한 건이라도 걸리면 제외다.

    ── (6) 19 고유 — 명단을 좁히면 δ가 움직이는가 ────────────
        손계산은 SELF_CHECK_RESTRICT 주석에 있다. 봇 [1,2,3,100] → δ −0.5,
        100을 빼면 δ −1.0. 빼는 코드가 실제로 값을 바꾸는지 본다.

    ── (7) 19 고유 — 버킷 합산 항등식 ────────────────────────
        12가 나눠 담은 버킷을 다시 합친 값이 손으로 더한 값과 같은가.
        19의 모든 수가 이 덧셈 위에 서 있다.

    통과하면 True.
    """
    line("[자가검증] 손으로 푼 예제를 먼저 통과시킨다")
    ok = True

    # (1) 06의 세 고정 예제
    print("  ── (1) 06의 세 고정 예제 — U · δ · BH ──")
    for name, a, b, exp_u, exp_d, exp_var in SELF_CHECK_U:
        got = mann_whitney(a, b)
        print(f"  {name}  A={a}  B={b}")
        for label, actual, expect in (("U", got["U"], exp_u),
                                      ("δ", got["델타"], exp_d),
                                      ("σ²", got["시그마제곱"], exp_var)):
            good = abs(actual - expect) <= SELF_CHECK_TOL
            ok = ok and good
            print(f"    {label} 기대 {expect:>8.4f} · 실제 {actual:>8.4f} "
                  f"{'통과' if good else '실패'}")
        auc_u = auc_from_u(got["U"], got["n1n2"])
        auc_d = auc_from_delta(got["델타"])
        good = abs(auc_u - auc_d) <= SELF_CHECK_TOL
        ok = ok and good
        print(f"    AUC  U/(n1n2) = {auc_u:.6f} · (δ+1)/2 = {auc_d:.6f}  "
              f"{'통과' if good else '실패'}")
    got_q = bh_qvalues(SELF_CHECK_BH_P)
    good = all(abs(g - e) <= SELF_CHECK_TOL
               for g, e in zip(got_q, SELF_CHECK_BH_Q))
    ok = ok and good
    print(f"  BH 보정  p={SELF_CHECK_BH_P}")
    print(f"    기대 q={SELF_CHECK_BH_Q}")
    print(f"    실제 q={[round(v, 4) for v in got_q]}  "
          f"{'통과' if good else '실패'}")

    # (2) 06판 ↔ 12판
    print("\n  ── (2) 06판과 12판이 같은 답을 내는가 ──")
    print("  같은 이름의 함수가 두 파일에 있고 12판이 칸을 하나 더 담는다.")
    print("  겹치는 칸이 다르면 19의 δ는 06의 δ와 다른 기계에서 나온 값이다.")
    for name, a, b, _, _, _ in SELF_CHECK_U:
        r06, r12 = mann_whitney_06(a, b), mann_whitney(a, b)
        same = all(abs(r06[k] - r12[k]) <= SELF_CHECK_TOL for k in r06)
        ok = ok and same
        print(f"    mann_whitney  {name:<8} 겹치는 칸 {len(r06)}개 "
              f"{'전부 같음' if same else '어긋남'}  "
              f"{'통과' if same else '실패'}")
    same = all(sig_06(x) == sig(x) for x in (0.0, 1.0, 0.049999, 3e-40, 0.5))
    ok = ok and same
    print(f"    sig           다섯 값 {'전부 같음' if same else '어긋남'}  "
          f"{'통과' if same else '실패'}  (12판은 None도 받는다: "
          f"{sig(None)!r})")
    same = all(direction_of_06(d) == direction_of(d)
               for d in (0.5, -0.5, 0.0))
    ok = ok and same
    print(f"    direction_of  세 부호 {'전부 같음' if same else '어긋남'}  "
          f"{'통과' if same else '실패'}")

    # (3) Spearman
    print("\n  ── (3) Spearman — 순위의 피어슨으로 구현했는가 ──")
    for name, xs, ys, expect in SELF_CHECK_RHO:
        actual = spearman(xs, ys)
        good = actual is not None and abs(actual - expect) <= SELF_CHECK_TOL
        ok = ok and good
        shown = "None" if actual is None else f"{actual:>10.7f}"
        print(f"    {lpad(name, 14)} 기대 {expect:>10.7f} · 실제 {shown}  "
              f"{'통과' if good else '실패'}")
    print("    (셋째가 동점 사례다. 단축 공식 1−6Σd²/n(n²−1) 로 풀면 0.95가")
    print("     나와 실패한다 — 그것이 이 예제를 둔 이유다.)")

    # (4) 자기폭로 판정
    print("\n  ── (4) 19 고유 — 자기폭로 판정 여섯 ──")
    for text, expect, why in SELF_CHECK_REVEAL:
        _, _, got = clean_doc(text)
        good = (got == expect)
        ok = ok and good
        mark = "걸림" if got else "안 걸림"
        want = "걸림" if expect else "안 걸림"
        print(f"    기대 {lpad(want, 8)} 실제 {lpad(mark, 8)} "
              f"{'통과' if good else '실패'}  {why}")
        print(f"      원문: {text[:60]}")

    # (5) 계정 단위 OR
    print("\n  ── (5) 19 고유 — 계정 단위로 올리기(한 건이라도 걸리면 제외) ──")
    for acc, (docs, expect) in sorted(SELF_CHECK_ACCOUNT_REVEAL.items()):
        n_hit = sum(1 for t in docs if clean_doc(t)[2])
        got = n_hit > 0
        good = (got == expect)
        ok = ok and good
        print(f"    {acc}  문서 {len(docs)}건 중 걸린 것 {n_hit}건 → "
              f"{'제외' if got else '잔류'}  "
              f"(기대 {'제외' if expect else '잔류'})  "
              f"{'통과' if good else '실패'}")

    # (6) 명단 제한이 δ를 움직이는가
    print("\n  ── (6) 19 고유 — 봇 명단을 좁히면 δ가 움직이는가 ──")
    allb, drop, hum, eu_all, ed_all, eu_keep, ed_keep = SELF_CHECK_RESTRICT
    keep = [v for v in allb if v not in drop]
    r_all, r_keep = mann_whitney(allb, hum), mann_whitney(keep, hum)
    for label, res, eu, ed in (("제한 전", r_all, eu_all, ed_all),
                               ("제한 후", r_keep, eu_keep, ed_keep)):
        good = (abs(res["U"] - eu) <= SELF_CHECK_TOL
                and abs(res["델타"] - ed) <= SELF_CHECK_TOL)
        ok = ok and good
        print(f"    {label}  봇 n={len(allb if label == '제한 전' else keep)} "
              f"U 기대 {eu:.1f} 실제 {res['U']:.1f} · "
              f"δ 기대 {ed:+.4f} 실제 {res['델타']:+.4f}  "
              f"{'통과' if good else '실패'}")
    moved = abs(r_all["델타"] - r_keep["델타"]) > SELF_CHECK_TOL
    ok = ok and moved
    print(f"    두 δ가 실제로 다른가 — {'다르다' if moved else '같다'}  "
          f"{'통과' if moved else '실패'}")
    print("    ('빼는 코드를 썼는데 아무것도 안 빠졌다'가 가장 조용한 실패다.)")

    # (7) 버킷 합산
    print("\n  ── (7) 19 고유 — 버킷 합산 항등식 ──")
    merged = merge_buckets(SELF_CHECK_BUCKET["연도별"])
    good = True
    for k, expect in SELF_CHECK_BUCKET_SUM.items():
        got = merged[k]
        same = (got == expect)
        good = good and same
        print(f"    {lpad(k, 18)} 기대 {expect} · 실제 {got}  "
              f"{'통과' if same else '실패'}")
    ok = ok and good
    sub = subset_measures({"x": SELF_CHECK_BUCKET, "y": {"연도별": {}}},
                          ["x", "y"])
    good = ("x" in sub and "y" not in sub)
    ok = ok and good
    print(f"    문서 0건 계정은 빠지는가 — 남은 계정 {sorted(sub)}  "
          f"{'통과' if good else '실패'}")

    # (8) 복사 무결성
    print("\n  ── (8) 붙여 넣은 함수가 원본과 글자까지 같은가 ──")
    copy_ok, copy_rows = check_copies()
    ok = ok and copy_ok
    bad = [r for r in copy_rows if not r["일치"]]
    n06 = sum(1 for r in copy_rows if r["출처"] == "06")
    n12 = sum(1 for r in copy_rows if r["출처"] == "12")
    print(f"    06에서 복사한 함수 {n06}개 · 12에서 복사한 함수 {n12}개")
    print(f"    06: {', '.join(COPIED_FROM_06)}")
    print(f"    12: {', '.join(COPIED_FROM_12[:12])} …")
    if bad:
        print(f"    ■ 원본과 다른 함수 {len(bad)}개 — "
              f"{', '.join(r['함수'] for r in bad)}")
    else:
        print(f"    전부 원본과 같다 (통과)")

    if not ok:
        print()
        print("■ 중단 — 자가검증 실패")
        print("  손계산과 어긋난 자리가 있습니다. 본 계산을 시작하지 않습니다.")
        print("  짚어 볼 곳:")
        print("   · 통계 기계가 어긋났다면 06·12에서 복사한 함수가 손으로")
        print("     수정된 것은 아닌가 (위 (8)의 소스 대조를 먼저 보라)")
        print("   · 자기폭로 판정이 어긋났다면 SELF_REVEAL 정규식이 12와")
        print("     다른 것은 아닌가")
        print("   · 버킷 합산이 어긋났다면 12 JSON의 '계정' 블록 모양이")
        print("     바뀐 것은 아닌가")
        print("  이 상태로 돌리면 틀린 표가 조용히 나옵니다.")
    return ok, copy_rows


# ════════════════════════════════════════════════════════════════════════
# [19 고유] 재현 관문 — 12를 그대로 다시 낼 수 있는가
# ════════════════════════════════════════════════════════════════════════
def reproduce_gate(now_rows, base12, label, digits=STAT_DIGITS):
    """
    봇을 하나도 빼지 않은 상태로 다시 계산한 δ·q가 12 JSON의 값과 같은지 본다.

    ■ 이 관문이 무엇을 지키나 ■
    19는 12의 저장된 카운트를 재사용한다. 재사용이 정당하려면 "같은 입력에서
    같은 답이 나온다"가 성립해야 하는데, 그것은 논증할 일이 아니라 검사할
    일이다. 버킷을 잘못 합쳤거나, 계정 명단이 어긋났거나, 축 지도가 달라졌
    으면 여기서 어긋난 항목이 나온다.

    12가 저장한 δ는 소수 4자리로 반올림된 값이므로 같은 자리에서 견준다.

    반환: (일치 항목 수, 불일치 목록)
    """
    same, diff = 0, []
    for k, r in now_rows:
        b = base12.get(k)
        if b is None:
            diff.append({"항목": k, "12": None, "19": rnd(r.get("델타"), digits),
                         "사유": "12 JSON에 없는 항목"})
            continue
        d12, d19 = b.get("델타"), rnd(r.get("델타"), digits)
        if d12 == d19:
            same += 1
        else:
            diff.append({"항목": k, "12": d12, "19": d19, "사유": "δ 불일치"})
    print(f"      {lpad(label, 10)} 12와 같은 항목 {same:>4}/{len(now_rows)}"
          + ("" if not diff else f"  ■ 어긋남 {len(diff)}개"))
    for row in diff[:3]:
        print(f"        {row['항목']}: 12 {row['12']} vs 19 {row['19']} "
              f"({row['사유']})")
    return same, diff


# ════════════════════════════════════════════════════════════════════════
# [19 고유] 사전 예측 판정
# ════════════════════════════════════════════════════════════════════════
def print_prediction(pred, verdict, detail, note=None):
    """
    예측 한 줄을 판정과 함께 찍는다. [12의 형식을 따름]

    '문장' 칸은 13-19_사전선언의 **원문 그대로**다. 원문이 실행 전의 어림
    수치를 담고 있으면(P19-4의 '194계정 · 945계정') 그 수를 고치지 않고,
    note 로 받은 실측 대응을 바로 아래 괄호로 병기한다. 원문을 실측에 맞게
    다시 쓰면 사전등록 문서와 로그가 서로 다른 문장을 갖게 된다.
    """
    mark = {"적중": "적중", "빗나감": "빗나감", "판정불가": "판정불가"}[verdict]
    print(f"\n  [{pred['번호']}] {pred['문장']}")
    if note:
        print(f"      ({note})")
    print(f"      판정 근거   {pred['판정근거']}")
    for d in detail:
        print(f"      {d}")
    print(f"      → {mark}")
    if verdict == "빗나감":
        print(f"      빗나갔으므로: {pred['빗나가면']}")


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    t_start = time.time()
    small = "--소표본" in sys.argv
    out_json = (OUT_JSON.replace(".json", "_소표본.json") if small else OUT_JSON)

    print("=" * 74)
    print("19_fox8재검증 — 자기폭로 없는 봇 계정만으로 12를 다시 낸다")
    print("=" * 74)
    if small:
        print(f"■ 소표본 시험 모드 — 무더기당 {SMALL_N}계정으로 파이프라인을")
        print("  끝까지 한 번 돌려 본다. 재현 관문은 표본이 달라 성립하지")
        print("  않으므로 건너뛴다. 이 모드의 수치는 인용하지 않는다.")

    # ══════════════════════════════════════════════════════════════
    # [1/9] 입력과 기준선
    # ══════════════════════════════════════════════════════════════
    print("\n[1/9] 입력과 기준선")
    need = [(FOX8_DB, "fox8 원자료 sqlite — 자기폭로 판정에만 쓴다"),
            (FOX8_JSON, "12_fox8전이.json — 계정별 버킷 카운트"),
            (SRC12_PY, "12_fox8전이.py — 절차 함수의 원본"),
            (SRC06_PY, "06_봇사람비교.py — 통계 함수의 원본"),
            (ACCOUNTS_JSON, "01_적격계정.json — 라벨"),
            (MEASURE_JSON, "04_기능어측정.json — 축 판별에 함께 넣는다"),
            (RATES_JSON, "05_사용률검수.json — 희소성표 172종"),
            (COMPARE_JSON, "06_비교결과.json — F 블록 δ 기준선"),
            (FEATURE_JSON, "07_형태자질비교.json — M·UPOS δ 기준선")]
    missing = [(p, s) for p, s in need if not os.path.exists(p)]
    if missing:
        for p, s in missing:
            print(f"      {p} 이(가) 없습니다.  ({s})")
        print("\n      19는 12의 산출물 위에서만 성립합니다. 끝냅니다.")
        return

    d12 = json.load(open(FOX8_JSON, encoding="utf-8"))
    conf12 = d12["설정"]
    acc12 = d12["계정"]
    d04 = json.load(open(MEASURE_JSON, encoding="utf-8"))
    conf04 = d04["설정"]
    meas04 = d04["계정"]
    del d04
    d05 = json.load(open(RATES_JSON, encoding="utf-8"))
    review05, conf05 = d05["검수요약"], d05["설정"]
    del d05
    d06 = json.load(open(COMPARE_JSON, encoding="utf-8"))
    d07 = json.load(open(FEATURE_JSON, encoding="utf-8"))
    base_words = d06["단어별"]
    base_feats = d07["형태자질"]
    base_upos = d07["UPOS"]
    disp09 = {}
    if os.path.exists(DISPERSION_JSON):
        d09 = json.load(open(DISPERSION_JSON, encoding="utf-8"))
        disp09 = ((d09.get("쌍거리") or {}).get("계정별요약검정")) or {}
        del d09

    d01 = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    labels01 = dict(d01.get("라벨") or {})
    del d01

    words = sorted(review05.get("희소성표", {}))
    print(f"      12 산출물   계정 {len(acc12):,}개 "
          f"(실행일 {conf12.get('실행일', '?')}) · "
          f"봇 {conf12.get('n_bot')} · 사람 {conf12.get('n_human')}")
    print(f"      04 기준     계정 {len(meas04):,}개 "
          f"(실행일 {conf04.get('실행일', '?')}) — 축 판별에 함께 넣는다")
    print(f"      05 희소성표 {len(words)}종 — F 블록의 비교 대상")
    print(f"      06 기준선   단어 {len(base_words):,}종 (δ_BotSim)")
    print(f"      07 기준선   형태자질 {len(base_feats):,}종 · "
          f"UPOS {len(base_upos):,}종")
    print(f"      09 기준선   계정별 거리 δ = {disp09.get('델타')}")

    # ── 해시 사슬 ───────────────────────────────────────────────
    line("해시 사슬 — 기준선들이 같은 04에서 나왔는가")
    print("  19는 새로 파싱하지 않는다. 그런데도 04의 지문을 보는 이유는, 19가")
    print("  쓰는 값이 전부 그 04에서 흘러나온 것이기 때문이다 — 12의 카운트도,")
    print("  05의 희소성표도, 06·07의 δ 기준선도. 사슬이 한 군데서 끊기면 19는")
    print("  어긋난 자들 사이에서 비교를 하게 되고 화면에는 아무 이상도 안 찍힌다.")
    print()
    chain = {
        "04": conf04.get("기능어_해시"),
        "05": (conf05.get("04승계") or {}).get("기능어_해시"),
        "06": ((d06["설정"].get("05승계") or {}).get("04승계")
               or {}).get("기능어_해시"),
        "07": (d07["설정"].get("04승계") or {}).get("기능어_해시"),
        "12": conf12.get("기능어_해시"),
    }
    for k, v in chain.items():
        print(f"  {k}가 적어 둔 해시   {v}")
    chain_ok = (len(set(chain.values())) == 1
                and chain["04"] == FUNCWORD_HASH)
    print(f"\n  명세가 승계하라고 적은 해시  {FUNCWORD_HASH}")
    if chain_ok:
        print("  다섯 파일이 같은 해시를 적어 두었다. 사슬이 이어져 있다.")
    else:
        print("  ■ 중단 — 해시가 어긋납니다. 앞 단계 중 하나가 다시 돌았습니다.")
        print("    어긋난 기준선 위에서 낸 δ는 12의 δ와 견줄 수 없습니다.")
        return

    # ══════════════════════════════════════════════════════════════
    # [2/9] 라벨 규율
    # ══════════════════════════════════════════════════════════════
    line("[2/9] 라벨 — 19는 라벨을 아는 상태에서 수행된다")
    print("  ■ 여기서 라벨을 읽는다 ■")
    print("  13은 라벨을 읽지 않았다(04와 같다). 14~19는 읽는다. 19가 라벨을")
    print("  쓰는 자리는 셋이다.")
    print()
    print("   ① fox8 라벨 — 12 JSON의 계정별 '라벨' 칸(원본 users.label).")
    print("      봇 무더기와 사람 무더기를 가르는 데 쓴다. 12가 쓴 그 라벨이다.")
    print("   ② 자기폭로 판정 — 봇 무더기 안에서만 계정을 뺀다. 사람은 12와")
    print("      똑같이 둔다(사전선언 19). 그래서 어느 계정을 뺄지 정하려면")
    print("      먼저 라벨을 알아야 한다.")
    print("   ③ BotSim 라벨 — 01_적격계정.json 의 '라벨' 키. 06·07의 δ가 이미")
    print("      소비한 라벨이라 19가 다시 계산에 쓰지는 않고, 기준선이 몇")
    print("      계정에서 나온 값인지를 적기 위해 읽는다.")
    print()
    n_bs_bot = sum(1 for v in labels01.values() if v == BOT_LABEL)
    n_bs_hum = sum(1 for v in labels01.values() if v == GROUP2)
    print(f"  BotSim 라벨   계정 {len(labels01):,}개 → 봇 {n_bs_bot:,} · "
          f"사람 {n_bs_hum:,}   (06·07 기준선의 출처)")
    lab12 = Counter(v.get("라벨") for v in acc12.values())
    print(f"  fox8 라벨     계정 {len(acc12):,}개 → "
          + " · ".join(f"{k} {v:,}" for k, v in sorted(lab12.items())))

    # ══════════════════════════════════════════════════════════════
    # [3/9] 자가검증
    # ══════════════════════════════════════════════════════════════
    print("\n[3/9] 자가검증 관문")
    ok, copy_rows = self_check()
    if not ok:
        return
    print("\n  자가검증 통과. 본 계산으로 들어간다.")

    # ══════════════════════════════════════════════════════════════
    # [4/9] 자기폭로 판정 — 어느 봇을 뺄 것인가
    # ══════════════════════════════════════════════════════════════
    print("\n[4/9] 자기폭로 판정 (12의 clean_doc 을 원문에 다시 건다)")
    print("      12는 걸린 문서 수만 라벨별로 셌다(봇 1,160 · 사람 1). 계정별로는")
    print("      남기지 않았으므로 원본 sqlite를 다시 훑는다. 파싱이 아니라 정규식")
    print("      한 번씩이라 몇십 초면 끝난다.")
    fp = input_fingerprint()
    prog = load_progress(fp)
    conn = sqlite3.connect(FOX8_DB)
    reveal = scan_self_reveal(conn, prog)
    conn.close()
    prog = {"입력지문": fp, "자기폭로": reveal}
    save_progress(prog)

    def n_nrt(uid):
        """그 계정이 비리트윗 행에서 걸린 문서 수(12의 정제 대상과 같은 행)."""
        return (reveal.get(uid) or {}).get("걸린문서수", 0)

    def n_rt(uid):
        """리트윗까지 합쳐 걸린 문서 수."""
        return (reveal.get(uid) or {}).get("걸린문서수_리트윗포함", 0)

    rev_by_label = Counter()          # 비리트윗 기준 — 12가 센 것과 같은 자리
    rev_docs_by_label = Counter()
    rev_by_label_rt = Counter()       # 리트윗 포함 기준
    rev_docs_by_label_rt = Counter()
    for uid, info in reveal.items():
        lab = (acc12.get(uid) or {}).get("라벨", "적격아님")
        if info["걸린문서수"] > 0:
            rev_by_label[lab] += 1
            rev_docs_by_label[lab] += info["걸린문서수"]
        if info["걸린문서수_리트윗포함"] > 0:
            rev_by_label_rt[lab] += 1
            rev_docs_by_label_rt[lab] += info["걸린문서수_리트윗포함"]
    n_rev_nrt = sum(rev_by_label.values())
    print(f"\n      자기폭로가 걸린 계정")
    print("        라벨        비리트윗 기준          리트윗 포함")
    print("                    계정     걸린 문서     계정     걸린 문서")
    for lab in sorted(set(rev_by_label) | set(rev_by_label_rt)):
        print(f"        {lpad(lab, 10)}{rev_by_label[lab]:>5,}{rev_docs_by_label[lab]:>13,}"
              f"{rev_by_label_rt[lab]:>9,}{rev_docs_by_label_rt[lab]:>13,}")
    print(f"        {lpad('합계', 10)}{n_rev_nrt:>5,}"
          f"{sum(rev_docs_by_label.values()):>13,}"
          f"{sum(rev_by_label_rt.values()):>9,}"
          f"{sum(rev_docs_by_label_rt.values()):>13,}")
    print("      ('적격아님'은 12의 코퍼스에 들어오지 못한 계정이다 — 문서")
    print("       10건 미만이거나 비영어로 판정된 계정. 19의 무더기와 무관하다.)")

    bot_all = sorted(u for u, v in acc12.items()
                     if v.get("라벨") == FOX8_BOT_LABEL)
    hum_all = sorted(u for u, v in acc12.items()
                     if v.get("라벨") == FOX8_HUMAN_LABEL)
    bot_drop = [u for u in bot_all if n_nrt(u) > 0]
    bot_keep = [u for u in bot_all if n_nrt(u) == 0]          # 비리트윗 기준
    bot_keep_strict = [u for u in bot_keep if n_rt(u) == 0]   # 엄격 기준
    bot_rt_only = [u for u in bot_keep if n_rt(u) > 0]
    bot_drop_strict = [u for u in bot_all if n_rt(u) > 0]
    hum_hit = [u for u in hum_all if n_nrt(u) > 0]
    hum_hit_rt = [u for u in hum_all if n_rt(u) > 0]
    rt_only = len(bot_rt_only)

    print(f"\n      ── 봇 무더기를 어떻게 좁혔나 — 두 기준 ──")
    print("      사전선언 19의 문구는 '자기폭로 문장이 원문에 한 번도 없는")
    print("      계정'이다. '원문'을 어디까지로 볼 것인가에 따라 무더기가 둘로")
    print("      갈린다. 어느 하나를 골라 다른 하나를 감추지 않고, 둘 다 낸다.")
    print()
    print("        ① 비리트윗 기준 — 12가 정제를 건 행 집합과 같다.")
    print("           리트윗은 남의 글이라 '자기 입으로 폭로한 것'이 아니라고 본다.")
    print("        ② 엄격 기준 — 리트윗을 포함해 어떤 행에서도 걸리지 않은 계정만.")
    print("           리트윗도 그 계정의 타임라인에 실린 원문이고, 그 문구로")
    print("           발견될 수 있었던 경로다. 사전선언의 '한 번도 없는'에 더 가깝다.")
    print()
    print(f"        12의 적격 봇                       {len(bot_all):>6,}계정")
    print(f"        ① 비리트윗에서 걸린 봇             {len(bot_drop):>6,}계정  "
          f"({len(bot_drop) / len(bot_all):.1%})")
    print(f"        ① 잔류 봇 (비리트윗 기준)          {len(bot_keep):>6,}계정")
    print(f"           그중 리트윗에서 걸리는 계정     {rt_only:>6,}계정  "
          f"← 처음 판은 이 수를 언제나 0으로 찍었다(고침)")
    print(f"        ② 리트윗 포함해 걸린 봇            "
          f"{len(bot_drop_strict):>6,}계정  "
          f"({len(bot_drop_strict) / len(bot_all):.1%})")
    print(f"        ② 잔류 봇 (엄격 기준)              "
          f"{len(bot_keep_strict):>6,}계정")
    print(f"        사람 (12와 동일, 손대지 않음)      {len(hum_all):>6,}계정")
    print(f"           그중 비리트윗에서 걸린 계정     {len(hum_hit):>6,}계정")
    print(f"           그중 리트윗 포함해 걸린 계정    {len(hum_hit_rt):>6,}계정")
    print("           — 사람은 어느 기준에서도 빼지 않는다(사전선언 19).")
    print()
    print("        검산: ① 잔류 = ② 잔류 + 리트윗에서 걸린 계정  "
          f"{len(bot_keep):,} = {len(bot_keep_strict):,} + {rt_only:,}  "
          f"{'맞음' if len(bot_keep) == len(bot_keep_strict) + rt_only else '■ 어긋남'}")

    print(f"\n      ── 사전선언 19의 어림과 대조 ──")
    print("        사전선언은 12를 돌리기 전의 어림을 적었다. 19는 어림이 아니라")
    print("        12 실행분을 잇는다 — 어림을 따라가면 12와 19가 서로 다른")
    print("        자료를 견주게 된다.")
    print("        칸                        사전선언 어림      12·19 실측")
    print(f"        봇 계정 전체                   {PRE_EXPECT_BOT_TOTAL:>6,}"
          f"          {len(bot_all):>6,}")
    print(f"        자기폭로 걸린 봇               "
          f"{PRE_EXPECT_SELFREVEAL_ACCOUNTS:>6,}          {len(bot_drop):>6,}")
    print(f"        남는 봇 ①                      {PRE_EXPECT_KEPT:>6,}"
          f"          {len(bot_keep):>6,}")
    print(f"        남는 봇 ② (엄격)               {'—':>6}"
          f"          {len(bot_keep_strict):>6,}")
    print(f"        사람 계정                      "
          f"{PRE_EXPECT_BOT_TOTAL:>6,}          {len(hum_all):>6,}")
    print("        (12 로그 [2/9]도 자기 어림과 어긋난 사실을 같은 방식으로")
    print("         적어 두었다: '적격 계정 · human: 다시 셈 897 ≠ 사전선언 1,080'.)")

    if not bot_keep or not bot_keep_strict:
        print("\n■ 중단 — 자기폭로가 없는 봇 계정이 하나도 없습니다.")
        return

    # 소표본 모드 — 파이프라인 시험용
    if small:
        bot_keep = bot_keep[:SMALL_N]
        bot_keep_strict = bot_keep_strict[:SMALL_N]
        hum_all = hum_all[:SMALL_N]
        bot_all = (bot_keep + bot_drop[:SMALL_N])
        print(f"\n      ■ 소표본 모드 — 봇 ① {len(bot_keep)} · ② "
              f"{len(bot_keep_strict)} · 사람 {len(hum_all)} 로 줄여 "
              f"파이프라인만 시험한다.")

    # ══════════════════════════════════════════════════════════════
    # [5/9] 12 산출물 재사용과 재현 관문
    # ══════════════════════════════════════════════════════════════
    print("\n[5/9] 12의 카운트를 다시 합치고, 12를 그대로 재현할 수 있는지 본다")
    print("      12는 계정별 카운트를 연도·답글 버킷으로 나누어 저장해 두었다.")
    print("      버킷을 전부 더하면 12가 주 비교에 쓴 그 카운트가 된다. 그러니")
    print("      19는 파싱을 다시 하지 않는다 — 대신 '같아야 한다'를 검사한다.")

    meas_raw = {FOX8_KEY + uid: rec for uid, rec in acc12.items()}
    meas_main = subset_measures(meas_raw, sorted(meas_raw))
    tot_docs = sum(a["문서수"] for a in meas_main.values())
    print(f"\n      버킷을 합쳐 얻은 계정 {len(meas_main):,}개 · "
          f"문서 {tot_docs:,}건")
    print(f"      12 로그가 적은 값      계정 "
          f"{V12_N_BOT + V12_N_HUMAN:,}개 · 문서 {V12_DOCS:,}건")
    scale_ok = (len(meas_main) == V12_N_BOT + V12_N_HUMAN
                and tot_docs == V12_DOCS)
    print(f"      → {'같다' if scale_ok else '■ 어긋난다'}")

    rates_main, undefined = compute_rates(meas_main)
    if undefined:
        print(f"      ※ 분모가 0인 계정 {len(undefined)}개는 사용률을 정의할 수")
        print("        없어 빠집니다(분석적 제외가 아니라 나눗셈 불성립).")

    def pref(uids):
        """
        원시 user_id 목록을 계정 사전의 키로 바꾼다.

        12는 트위터 user_id와 레딧 계정 ID가 우연히 겹쳐 한쪽이 다른 쪽을
        조용히 덮어쓰는 일을 막으려고 내부 사전에 접두사를 붙였다(FOX8_KEY).
        19도 같은 사전을 쓰므로 같은 접두사를 붙여야 한다. 분모 0으로 빠진
        계정은 여기서 함께 걸러진다 — 사용률이 없는 계정을 명단에 남기면
        곧바로 KeyError 이거나, 더 나쁘게는 0으로 채워진 벡터가 된다.
        """
        return [k for k in (FOX8_KEY + u for u in uids) if k in rates_main]

    ids_bot_all = pref(bot_all)
    ids_bot_keep = pref(bot_keep)
    ids_bot_keep_strict = pref(bot_keep_strict)
    ids_hum = pref(hum_all)
    lost = ((len(bot_all) - len(ids_bot_all))
            + (len(hum_all) - len(ids_hum)))
    if lost:
        print(f"      ※ 사용률을 정의할 수 없어 명단에서 빠진 계정 {lost}개")

    # 축 지도 — 12와 같은 자료에서 유도한다
    print("\n      ── 축 지도 ──")
    print("      12는 '축은 한 번만 유도한다'고 못 박았다. 부분집합마다 다시")
    print("      유도하면 부분집합마다 분모의 정의가 달라져, '봇을 좁혔더니 δ가")
    print("      줄었다'가 사실은 '분모가 바뀌었다'일 수 있게 된다. 그래서 19도")
    print("      12와 **똑같은 자료**(04 전부 + fox8 전부 + 전 텍스트)에서")
    print("      유도한다 — 자기폭로 봇을 뺀 자리에서 다시 유도하지 않는다.")
    meas_axis = dict(meas_main)
    pre12 = (d12.get("완화B_전후대조") or {}).get("전텍스트_계정별원카운트") or {}
    meas_pre = subset_measures({("PRE:" + u): r for u, r in pre12.items()},
                               sorted("PRE:" + u for u in pre12))
    meas_axis.update(meas_pre)
    meas_axis.update(meas04)
    axis_map = build_axis_map(meas_axis)
    del meas_axis
    print(f"      축 {len(axis_map)}개 (12가 적어 둔 축 수 "
          f"{(conf12.get('축대조') or {}).get('12축수')}개)")

    def make_family(bot_ids, hum_ids):
        """
        무더기 둘을 받아 세 가족을 통째로 검정한다.

        재현 관문(봇 전체)과 본 계산(봇 제한)이 **같은 함수**를 지나가야
        한다. 두 벌을 따로 쓰면 그 사본이 언젠가 갈라지고, 그러면 관문이
        본 계산과 다른 것을 검사하게 된다.
        """
        n_all = len(bot_ids) + len(hum_ids)
        cut = int(n_all * SPARSE_FRAC)
        meas_cmp = {u: meas_main[u] for u in bot_ids + hum_ids}
        fkeys = sorted({k for a in meas_cmp.values() for k in a.get("자질", {})})
        ukeys = sorted({k for a in meas_cmp.values() for k in a.get("UPOS", {})})
        kinds = {k: denom_kind_of(k, axis_map) for k in fkeys}
        ratios, _aux, pres_f = compute_ratios(meas_cmp, fkeys, axis_map)
        upos_ratios, pres_u = compute_upos_ratios(meas_cmp, ukeys)
        pres_w = word_presence(bot_ids + hum_ids, rates_main, words)

        def wg(uids, key):
            return word_vector(uids, rates_main, key)

        def fg(uids, key):
            return defined_values(uids, ratios, key)

        def ug(uids, key):
            return defined_values(uids, upos_ratios, key)

        f_rows, f_m = compare_family(words, bot_ids, hum_ids, wg, pres_w, cut)
        m_rows, m_m = compare_family(fkeys, bot_ids, hum_ids, fg, pres_f, cut,
                                     kinds)
        u_rows, u_m = compare_family(ukeys, bot_ids, hum_ids, ug, pres_u, cut)
        tb = [rates_main[u]["총사용률"] for u in bot_ids]
        th = [rates_main[u]["총사용률"] for u in hum_ids]
        total = mann_whitney(tb, th)
        total["방향"] = direction_of(total["델타"])
        return {"F행": f_rows, "M행": m_rows, "U행": u_rows,
                "F가족": f_m, "M가족": m_m, "U가족": u_m,
                "자질키": fkeys, "UPOS키": ukeys, "희소기준": cut,
                "총사용률": total, "총봇": tb, "총사람": th,
                "getter": (wg, fg, ug), "n_all": n_all}

    gate = {"수행": not small, "규모일치": scale_ok}
    if small:
        print("\n      ── 재현 관문 — 소표본 모드라 건너뛴다 ──")
        print("      12를 재현하려면 12와 같은 무더기여야 한다. 소표본은 그렇지")
        print("      않으므로 관문을 걸 수 없다. 본 실행에서 반드시 통과시킨다.")
    else:
        print("\n      ── 재현 관문 — 봇을 하나도 빼지 않고 12를 다시 낸다 ──")
        print("      이 관문이 통과해야 '재파싱 없이 12의 카운트를 재사용한다'가")
        print("      정당해진다. 어긋나면 본 계산에 들어가지 않는다.")
        t0 = time.time()
        rep = make_family(ids_bot_all, ids_hum)
        print(f"      계산 {time.time() - t0:.1f}초 · 봇 {len(ids_bot_all):,} · "
              f"사람 {len(ids_hum):,}")
        s_f, d_f = reproduce_gate(rep["F행"], d12["주비교"]["F블록"], "F블록")
        s_m, d_m = reproduce_gate(rep["M행"], d12["주비교"]["형태자질"], "형태자질")
        s_u, d_u = reproduce_gate(rep["U행"], d12["주비교"]["UPOS"], "UPOS")
        t12 = d12["주비교"]["총사용률"]
        t19 = rnd(rep["총사용률"]["델타"], STAT_DIGITS)
        t_ok = (t12.get("델타") == t19)
        print(f"      {lpad('총사용률', 10)} 12 δ {t12.get('델타')} · "
              f"19 δ {t19}  {'같음' if t_ok else '■ 어긋남'}")
        gate.update({"F블록_일치": s_f, "F블록_불일치": d_f[:5],
                     "형태자질_일치": s_m, "형태자질_불일치": d_m[:5],
                     "UPOS_일치": s_u, "UPOS_불일치": d_u[:5],
                     "총사용률_일치": t_ok})
        gate["통과"] = (scale_ok and not d_f and not d_m and not d_u and t_ok)
        if not gate["통과"]:
            print("\n■ 중단 — 재현 관문 실패")
            print("  12의 카운트를 다시 합쳐 낸 δ가 12 JSON의 값과 어긋납니다.")
            print("  재사용의 전제가 깨졌으므로 본 계산에 들어가지 않습니다.")
            print("  짚어 볼 곳: 12 JSON의 '계정' 블록이 바뀌었는가 · 축 지도를")
            print("  같은 자료에서 유도했는가 · 계정 명단이 12와 같은가.")
            write_json(out_json, {"설정": {"중단": "재현 관문 실패"},
                                 "재현관문": gate})
            return
        print("\n      재현 관문 통과 — 12의 값을 한 자리도 어긋나지 않게 다시")
        print("      냈다. 이제 봇 무더기만 좁혀 같은 계산을 돌린다. 두 결과의")
        print("      차이는 오로지 '어느 봇이 들어갔나'에서만 온다.")
        del rep

    # ══════════════════════════════════════════════════════════════
    # [6/9] 주 비교 — 자기폭로 없는 봇 대 fox8 사람
    # ══════════════════════════════════════════════════════════════
    print("\n[6/9] 주 비교 (그룹1 = 자기폭로 없는 fox8 봇 · 그룹2 = fox8 사람)")
    print("      δ > 0 이면 봇이 높다. 06·07·12와 같은 부호 규약이다.")
    print("      [4/9]가 무더기를 둘로 갈랐으므로 같은 계산을 두 번 돌린다.")
    print("      사람 무더기는 두 번 다 같다 — 달라지는 것은 봇 명단뿐이다.")
    print(f"        ① 비리트윗 기준  봇 {len(ids_bot_keep):,} · "
          f"사람 {len(ids_hum):,}")
    print(f"        ② 엄격 기준      봇 {len(ids_bot_keep_strict):,} · "
          f"사람 {len(ids_hum):,}")
    print(f"        12               봇 {V12_N_BOT:,} · 사람 {V12_N_HUMAN:,}")

    def show_family(res, title):
        """무더기 하나의 총사용률과 세 가족 요약을 찍는다."""
        q_bot, q_hum = quartiles(res["총봇"]), quartiles(res["총사람"])
        tot = res["총사용률"]
        print(f"\n      ══ {title} ══")
        print("      ── 총 기능어 사용률 (1건 — BH 가족 밖 단독 검정) ──")
        print(" " * 21 + "Q1" + " " * 6 + "중앙" + " " * 8 + "Q3")
        for name, q, n in (("봇      ", q_bot, len(res["총봇"])),
                           ("사람    ", q_hum, len(res["총사람"]))):
            print(f"      {name}{q['Q1']:>7.2%}   {q['중앙']:>7.2%}   "
                  f"{q['Q3']:>7.2%}   (n={n:,})")
        print(f"\n      봇 대 사람   U = {tot['U']:,.1f}   z = {tot['z']:.3f}   "
              f"양측 p = {tot['p']:.3g}")
        print(f"      δ = {tot['델타']:+.4f}  →  {tot['방향']}   "
              f"단독 AUC = {auc_from_delta(tot['델타']):.3f}")
        print(f"      (12의 같은 값은 δ = {V12_TOTAL_DELTA:+.4f} 이었다. "
              f"차이 {tot['델타'] - V12_TOTAL_DELTA:+.4f})")
        print("      단독 검정이라 q = p 로 읽는다. m = 1 에서 BH는 항등.")
        print(f"\n      BH 가족 크기   F {res['F가족']}종 · 형태자질 "
              f"{res['M가족']}종 · UPOS {res['U가족']}종")
        s_f = family_summary(res["F행"], res["F가족"], res["희소기준"],
                             res["n_all"], "F 블록")
        s_m = family_summary(res["M행"], res["M가족"], res["희소기준"],
                             res["n_all"], "형태자질")
        s_u = family_summary(res["U행"], res["U가족"], res["희소기준"],
                             res["n_all"], "UPOS")
        return {"F블록": s_f, "형태자질": s_m, "UPOS": s_u,
                "총사용률사분위": (q_bot, q_hum)}

    t0 = time.time()
    res = make_family(ids_bot_keep, ids_hum)
    res_s = make_family(ids_bot_keep_strict, ids_hum)
    print(f"      계산 {time.time() - t0:.1f}초 (두 무더기)")

    f_rows, m_rows, u_rows = res["F행"], res["M행"], res["U행"]
    f_rows_s, m_rows_s, u_rows_s = res_s["F행"], res_s["M행"], res_s["U행"]
    cut = res["희소기준"]
    n_all = res["n_all"]

    print(f"\n      가족 1 F블록 {len(words)}종 · 가족 2 형태자질 "
          f"{len(res['자질키'])}종 · 가족 3 UPOS {len(res['UPOS키'])}종")
    print("      세 가족에 각각 따로 보정했다. 서로 다른 m에서 나온 q이므로")
    print("      세 표의 q를 한 줄로 세워 비교하면 안 된다(06·07·12와 같은 규율).")

    sums = show_family(res, f"① 비리트윗 기준 — 봇 {len(ids_bot_keep):,}계정")
    sums_s = show_family(res_s,
                         f"② 엄격 기준 — 봇 {len(ids_bot_keep_strict):,}계정")
    f_sum, m_sum, u_sum = sums["F블록"], sums["형태자질"], sums["UPOS"]
    f_sum_s, m_sum_s, u_sum_s = sums_s["F블록"], sums_s["형태자질"], sums_s["UPOS"]
    q_bot, q_hum = sums["총사용률사분위"]
    tot = res["총사용률"]
    tot_s = res_s["총사용률"]

    print(f"\n      ── 주목 종수를 나란히 ──")
    print("        가족          12(1,094)   ①(비리트윗)   ②(엄격)")
    for name, k12, sa, sb in (("F블록", V12_NOTABLE["F블록"], f_sum, f_sum_s),
                              ("형태자질", V12_NOTABLE["형태자질"], m_sum, m_sum_s),
                              ("UPOS", None, u_sum, u_sum_s)):
        k12_txt = "—" if k12 is None else f"{k12}"
        print(f"        {lpad(name, 12)}{k12_txt:>9}종{sa['주목']:>11}종"
              f"{sb['주목']:>10}종")
    print("      (봇이 1,094에서 줄었으므로 검정력이 줄고 q가 커진다. 주목")
    print("       종수가 줄어드는 것 자체는 신호가 사라진 증거가 아니다 —")
    print("       10의 교훈대로 표본이 줄면 |δ| 유지 여부로 읽는다.)")

    # ══════════════════════════════════════════════════════════════
    # [7/9] 전이 상관 — 06·07의 방향 벡터와 얼마나 맞는가
    # ══════════════════════════════════════════════════════════════
    print("\n[7/9] 전이 상관 (δ_BotSim 대 δ_19 · 12와 같은 구현)")
    print("      δ_BotSim = 06·07이 낸 δ (BotSim 봇 대 BotSim 사람)")
    print("      δ_19     = [6/9]가 낸 δ (자기폭로 없는 fox8 봇 대 fox8 사람)")
    print("      ρ는 순위의 피어슨으로 구한다 — 동점이 많아 단축 공식을 쓰면")
    print("      조용히 틀린 값이 나온다([3/9]의 셋째 예제가 그 검사다).")
    print("      무더기 둘을 각각 낸다. 기준선(06·07의 δ)은 둘 다 같은 것이다.")

    families = ("F블록", "형태자질", "UPOS")
    base_of = {"F블록": base_words, "형태자질": base_feats, "UPOS": base_upos}
    rows_of = {"F블록": f_rows, "형태자질": m_rows, "UPOS": u_rows}
    rows_of_s = {"F블록": f_rows_s, "형태자질": m_rows_s, "UPOS": u_rows_s}

    pairs = {f: pair_with_baseline(rows_of[f], base_of[f]) for f in families}
    pairs_s = {f: pair_with_baseline(rows_of_s[f], base_of[f]) for f in families}
    corr_whole = {f: correlation_block(pairs[f]) for f in families}
    corr_notable = {f: correlation_block(pairs[f], only_prior_notable=True)
                    for f in families}
    corr_whole_s = {f: correlation_block(pairs_s[f]) for f in families}
    corr_notable_s = {f: correlation_block(pairs_s[f], only_prior_notable=True)
                      for f in families}

    print(f"\n      ══ ① 비리트윗 기준 — 봇 {len(ids_bot_keep):,}계정 ══")
    for f in families:
        print_correlation(f, corr_whole[f], corr_notable[f])
    print(f"\n      ══ ② 엄격 기준 — 봇 {len(ids_bot_keep_strict):,}계정 ══")
    for f in families:
        print_correlation(f, corr_whole_s[f], corr_notable_s[f])

    print("\n      ── 12와 나란히 (가족 전체 ρ) ──")
    print(f"        가족            12 ρ    ①(봇 {len(ids_bot_keep):,})"
          f"    ②(봇 {len(ids_bot_keep_strict):,})    ①−12     ②−12")
    for f in families:
        r12 = V12_RHO[f]
        r1 = corr_whole[f]["rho"]
        r2 = corr_whole_s[f]["rho"]
        nan = float("nan")
        print(f"        {lpad(f, 12)}{r12:>+9.4f}"
              f"{(r1 if r1 is not None else nan):>+11.4f}"
              f"{(r2 if r2 is not None else nan):>+11.4f}"
              f"{(r1 - r12 if r1 is not None else nan):>+9.4f}"
              f"{(r2 - r12 if r2 is not None else nan):>+9.4f}")
    print("\n      ── 방향 일치율을 나란히 ──")
    print("        가족             12       ①       ②")
    for f in families:
        d1 = corr_whole[f]["방향일치율"]
        d2 = corr_whole_s[f]["방향일치율"]
        print(f"        {lpad(f, 12)}{V12_DIR_RATE[f]:>8.1%}"
              f"{(d1 or 0):>9.1%}{(d2 or 0):>9.1%}")
    print("      (판정에는 가족 전체 ρ를 쓴다. '앞에서 주목이었던 것만 고른다'는")
    print("       앞 결과를 보고 하는 선택이라 사전등록의 뜻이 옅어진다 — 12가")
    print("       같은 이유로 같은 선택을 했다.)")

    for tag, pp, ids in (("② 엄격", pairs_s, ids_bot_keep_strict),
                         ("① 비리트윗", pairs, ids_bot_keep)):
        for f, base_label in (("F블록", "06"), ("형태자질", "07"),
                              ("UPOS", "07")):
            prior = [(k, c) for k, c in pp[f] if c["BotSim주목"]]
            prior.sort(key=lambda kv: -(abs(kv[1]["BotSim델타"] or 0.0)))
            limit = None if f == "UPOS" else TOP_SHOW
            shown = len(prior) if limit is None else min(limit, len(prior))
            print_pair_table(prior, base_label,
                             f"[{tag} · 봇 {len(ids):,}] {f} — "
                             f"{base_label}에서 주목이었던 {len(prior)}종 중 "
                             f"|δ_BotSim| 상위 {shown}종", limit)

    # ══════════════════════════════════════════════════════════════
    # [8/9] 산포 — 자기폭로 없는 봇끼리도 서로 닮았는가
    # ══════════════════════════════════════════════════════════════
    print("\n[8/9] 산포 재검정 (계정별 거리 · 12와 같은 방식)")
    print("      09가 BotSim에서 잰 것은 '봇끼리 서로 닮았다'였다. 12는 fox8에서")
    print("      같은 것을 다시 재 δ = −0.974를 얻었다. 그런데 그 봇의 83%가")
    print("      같은 상투구를 뱉는 계정이었다면, 닮음의 상당 부분이 그 상투구일")
    print("      수 있다. 그것을 빼고 다시 잰다.")
    print(f"\n      ── 그룹 내 쌍거리 ({len(words)}차원 사용률 벡터의 L1) ──")
    pile_ids = (("봇①(비리트윗)", ids_bot_keep),
                ("봇②(엄격)", ids_bot_keep_strict),
                ("사람", ids_hum))
    for name, ids in pile_ids:
        n = len(ids)
        print(f"        {lpad(name, 18)}{n:>6,}계정 → {n * (n - 1) // 2:>10,}쌍")
    print("      (봇②는 봇①의 부분집합이다. 부분집합의 계정별 거리는 상대가")
    print("       달라져 새로 계산해야 한다 — 봇①의 값을 잘라 쓰면 안 된다.)")
    print("      계산 중...", end=" ", flush=True)
    t0 = time.time()
    per_med = {}
    for name, ids in pile_ids:
        if len(ids) < 2:
            per_med[name] = []
            continue
        vecs = dense_vectors(ids, rates_main, words)
        _, per = within_group_distances(vecs)
        del vecs
        per_med[name] = [statistics.median(v) for v in per]
        del per
    print(f"{time.time() - t0:.1f}초")

    print("\n      계정별 요약 — '같은 무더기 안 다른 계정들과의 거리 중앙값'")
    dist_piles = pile_table([(name, per_med[name]) for name, _ in pile_ids])
    med_bot = per_med["봇①(비리트윗)"]
    med_bot_s = per_med["봇②(엄격)"]
    med_hum = per_med["사람"]

    def dist_test(meds, label):
        """계정별 거리 중앙값을 사람과 견준다."""
        if not meds or not med_hum:
            print(f"\n        {label} — 계정이 모자라 검정 불가")
            return None
        r = mann_whitney(meds, med_hum)
        r["방향"] = direction_disp(r["델타"], "봇이")
        print(f"\n        {label}   n1 {len(meds):,} · n2 {len(med_hum):,} · "
              f"U = {r['U']:,.0f} · z = {r['z']:.3f} · p = {r['p']:.3g}")
        print(f"        δ = {r['델타']:+.4f}  →  {r['방향']}")
        return r

    acct = dist_test(med_bot, "① 비리트윗 기준 봇 대 사람")
    acct_s = dist_test(med_bot_s, "② 엄격 기준 봇 대 사람")
    print(f"\n        12의 같은 값은 δ = {V12_DIST_DELTA:+.4f} 였다 "
          f"(봇 {V12_N_BOT:,}계정).")
    print(f"        09가 BotSim 매칭 표본에서 낸 값은 {disp09.get('델타')} 였다.")
    print("\n        ── 계정별 거리 δ 를 나란히 ──")
    print("          12(1,094)     ①(비리트윗)     ②(엄격)     09(BotSim)")
    print(f"          {V12_DIST_DELTA:>+9.4f}"
          f"{(acct['델타'] if acct else float('nan')):>+16.4f}"
          f"{(acct_s['델타'] if acct_s else float('nan')):>+13.4f}"
          f"{(disp09.get('델타') or float('nan')):>+15.4f}")
    print()
    print("      ■ 쌍 자체에는 p를 붙이지 않았다 ■ [09·12에서 그대로]")
    print("      한 계정이 수백~수천 개 쌍에 동시에 들어가 쌍끼리 독립이 아니다.")
    print("      그래서 쌍은 계정당 값 하나로 줄인 뒤에 검정한다.")

    # 총사용률 산포도 12와 같은 도구로 함께 낸다(사전선언 19의 '산포도 12와 같은 방식')
    bf_total = brown_forsythe(res["총봇"], res["총사람"], "봇이")
    bf_total_s = brown_forsythe(res_s["총봇"], res_s["총사람"], "봇이")
    print("\n      ── 총 기능어 사용률의 산포 (Brown-Forsythe) ──")
    for tag, bf in (("① 비리트윗", bf_total), ("② 엄격", bf_total_s)):
        if not bf:
            print(f"        {tag}  검정 불가")
            continue
        ratio_txt = ("—" if bf["IQR비"] is None else f"{bf['IQR비']:.4f}배")
        print(f"        {lpad(tag, 12)}  δ = {bf['델타']:+.4f} → "
              f"{bf['방향']} · IQR비(사람 ÷ 봇) = {ratio_txt}")
    print("        (δ < 0 이면 봇의 절대편차가 작다 = 봇이 더 뭉쳐 있다.")
    print("         사전선언 19가 '산포도 12와 같은 방식으로'라고 적어")
    print("         계정별 거리와 함께 이 한 줄도 낸다.)")

    # ══════════════════════════════════════════════════════════════
    # [9/9] 사전 예측 대조 · 저장 · 확인 항목
    # ══════════════════════════════════════════════════════════════
    line("[9/9] 사전 예측 대조")
    print("  13-19_사전선언 「19」의 예측 넷이다. 판정은 07·12와 같은 규칙 —")
    print("  문장 단위 전부-아니면-빗나감. 빗나간 예측도 지우지 않고 그대로 싣는다.")
    if small:
        print("\n  ■ 소표본 모드의 판정이다. 인용하지 않는다.")

    print()
    print("  ■ 어느 무더기로 판정하나 ■")
    print("  사전선언 19의 문구는 '자기폭로 문장이 원문에 한 번도 없는 계정'")
    print("  이다. 리트윗도 그 계정의 타임라인에 실린 원문이므로, 그 문구에 더")
    print("  가까운 것은 ② 엄격 무더기다. 그래서 **② 를 주 판정으로** 삼고")
    print("  ① 비리트윗 무더기는 보조로 함께 싣는다. 어느 쪽도 감추지 않는다.")
    print("  판정 규칙은 두 무더기에서 같다 — 문장 단위 전부-아니면-빗나감.")

    def judge(rows_m, corr, acct_r, bot_list, tag, primary):
        """무더기 하나에 예측 넷을 건다. 판정 규칙은 두 무더기에서 같다."""
        print()
        print("  " + "─" * 70)
        print(f"  {'[주 판정]' if primary else '[보조 판정]'} {tag}")
        print("  " + "─" * 70)
        vs = []

        # P19-1
        rhos = {f: corr[f]["rho"] for f in families}
        all_pos = all(r is not None and r > 0 for r in rhos.values())
        f_ok = rhos["F블록"] is not None and rhos["F블록"] >= 0.20
        v1 = "적중" if (all_pos and f_ok) else "빗나감"
        detail = [f"ρ  F블록 {rhos['F블록']} · 형태자질 {rhos['형태자질']} · "
                  f"UPOS {rhos['UPOS']}",
                  f"모두 양수인가 {all_pos} · F블록 ≥ +0.20 인가 {f_ok}",
                  f"12의 ρ  F {V12_RHO['F블록']} · M {V12_RHO['형태자질']} · "
                  f"U {V12_RHO['UPOS']}"]
        print_prediction(PREDICTIONS[0], v1, detail)
        vs.append({"번호": "P19-1", "판정": v1, "실제": rhos})

        # P19-2
        tp = dict(rows_m).get("Tense=Past")
        tp_d = tp.get("델타") if tp else None
        v2 = ("판정불가" if tp_d is None
              else ("적중" if tp_d <= -0.50 else "빗나감"))
        detail = [f"Tense=Past δ = {rnd(tp_d, STAT_DIGITS)}  (문턱 ≤ −0.50)",
                  f"12의 값 {V12_TENSE_PAST_DELTA} · 07(BotSim)의 값 "
                  f"{(base_feats.get('Tense=Past') or {}).get('델타')}"]
        print_prediction(PREDICTIONS[1], v2, detail)
        vs.append({"번호": "P19-2", "판정": v2, "실제": rnd(tp_d, STAT_DIGITS)})

        # P19-3
        ad = acct_r["델타"] if acct_r else None
        v3 = "판정불가" if ad is None else ("적중" if ad < 0 else "빗나감")
        detail = [f"계정별 거리 δ = {rnd(ad, STAT_DIGITS)}  (문턱 < 0)",
                  f"12의 값 {V12_DIST_DELTA} · 09(BotSim 매칭 표본) "
                  f"{disp09.get('델타')}"]
        print_prediction(PREDICTIONS[2], v3, detail)
        vs.append({"번호": "P19-3", "판정": v3, "실제": rnd(ad, STAT_DIGITS)})

        # P19-4 — 사전선언 원문의 '194계정'과 '945계정'은 이 무더기의 잔류·제외다
        keep_set = set(bot_list)
        docs_keep = [acc12[u]["문서수"] for u in bot_list]
        docs_drop = [acc12[u]["문서수"] for u in bot_all if u not in keep_set]
        md_k = statistics.median(docs_keep) if docs_keep else None
        md_d = statistics.median(docs_drop) if docs_drop else None
        v4 = ("판정불가" if (md_k is None or md_d is None)
              else ("적중" if md_k < md_d else "빗나감"))
        note = (f"사전선언의 '봇 194계정' = 잔류 봇, '945계정' = 제외 봇의 "
                f"어림이다. 이 무더기의 실측은 잔류 {len(docs_keep):,} · "
                f"제외 {len(docs_drop):,}.")
        detail = [f"잔류 봇 {len(docs_keep):,}계정 문서수 중앙값 {md_k}",
                  f"제외 봇 {len(docs_drop):,}계정 문서수 중앙값 {md_d}",
                  "사전선언이 '표본 성격의 기록'이라고 적은 예측이다."]
        print_prediction(PREDICTIONS[3], v4, detail, note)
        vs.append({"번호": "P19-4", "판정": v4,
                   "실제": {"잔류_n": len(docs_keep), "잔류_중앙": md_k,
                          "제외_n": len(docs_drop), "제외_중앙": md_d}})

        n_hit = sum(1 for v in vs if v["판정"] == "적중")
        print(f"\n    적중 {n_hit} · 빗나감 "
              f"{sum(1 for v in vs if v['판정'] == '빗나감')} · 판정불가 "
              f"{sum(1 for v in vs if v['판정'] == '판정불가')}  (전 4건)")
        return vs, md_k, md_d

    verdicts_s, md_keep_s, md_drop_s = judge(
        m_rows_s, corr_whole_s, acct_s, bot_keep_strict,
        f"② 엄격 기준 — 봇 {len(ids_bot_keep_strict):,}계정 대 사람 "
        f"{len(ids_hum):,}계정", True)
    verdicts, md_keep, md_drop = judge(
        m_rows, corr_whole, acct, bot_keep,
        f"① 비리트윗 기준 — 봇 {len(ids_bot_keep):,}계정 대 사람 "
        f"{len(ids_hum):,}계정", False)

    print("\n  ── 두 판정표를 한 줄로 ──")
    print("    예측      ② 엄격(주)     ① 비리트윗(보조)")
    for a, b in zip(verdicts_s, verdicts):
        print(f"    {a['번호']}     {lpad(a['판정'], 12)}   {b['판정']}")

    v1_s = verdicts_s[0]["판정"]
    v1_1 = verdicts[0]["판정"]
    print()
    print(f"  {NARROWING_LINE}")
    if v1_s == "적중" and v1_1 == "적중":
        print("  P19-1은 두 무더기 모두에서 적중했다. 그러나 이것이 '전이가")
        print("  확립되었다'는 뜻은 아니다 — 12의 한계(연도 AUC 1.000 · fox8")
        print("  6회차 사용 · 대조군이 서로 다른 δ)는 19에도 그대로 남아 있다.")
        print("  19가 지운 것은 '자기폭로로 발견된 봇에 한정'이라는 의심 하나뿐이다.")
    elif v1_s == "빗나감":
        print("  주 판정(② 엄격)에서 P19-1이 빗나갔으므로 위 문장을 그대로")
        print("  이행한다. ① 무더기의 판정은 보조로만 읽는다.")
    else:
        print("  주 판정(② 엄격)에서는 적중했으나 보조 판정(①)이 빗나갔다.")
        print("  두 무더기가 갈리는 자리이므로 어느 쪽도 단독으로 인용하지 말 것.")

    # ── 저장 ────────────────────────────────────────────────────
    line("저장")
    elapsed = time.time() - t_start
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform_python(),
            "소표본모드": small,
            "방법": ("12_fox8전이의 계정별 버킷 카운트를 재사용해 봇 무더기만 "
                   "자기폭로 없는 계정으로 좁히고, 12와 같은 세 BH 가족 비교 · "
                   "전이 상관 · 계정별 거리를 다시 냈다. 재파싱하지 않았다. "
                   "봇 무더기는 두 기준으로 각각 만들었다 — ① 비리트윗 기준"
                   "(12가 정제를 건 행 집합) · ② 엄격 기준(리트윗 포함 어떤 "
                   "행에서도 걸리지 않은 계정). 주 판정은 ②."),
            "변경사유": ("2026-09-02 검수 결함 수정·엄격 무더기 추가. "
                     "(1) scan_self_reveal 이 반환 사전을 비리트윗 카운터의 "
                     "키로만 만들어, 리트윗에서만 걸린 계정이 통째로 빠졌다. "
                     "그래서 '리트윗포함시_추가로_걸리는_잔류봇'이 구조적으로 "
                     "언제나 0으로 기록됐다(v1 값 0 → 실제 70). 두 카운터의 "
                     "합집합으로 고쳤다. "
                     "(2) 그 고침으로 드러난 70계정을 마저 뺀 엄격 무더기"
                     "(117계정)를 만들고, 기존 무더기(187계정)와 둘 다 "
                     "주비교·전이 상관·계정별 거리를 냈다. 사전선언 19의 "
                     "'원문에 한 번도 없는'에 더 가까운 ②를 주 판정으로 "
                     "삼는다. "
                     "(3) 로그 절 번호 [2/9]·[9/9] 누락, 자가검증 (4)절 "
                     "제목의 예제 수(다섯→여섯), P19-4를 사전선언 원문 대신 "
                     "재진술로 찍던 것을 함께 고쳤다. "
                     "01~12·13~18 산출물은 건드리지 않았고 19만 덮어썼다. "
                     "고침 전 판은 .19_fox8재검증_v1_리트윗버그.{py,json,log} "
                     "로 보존했다."),
            "재사용_근거": ("19가 바꾸는 것은 비교에 들어가는 봇 계정의 명단뿐이며 "
                        "계정별 카운트는 그 계정의 문서에서만 나온다. 재현 관문이 "
                        "봇 전체로 12의 δ를 한 자리도 어긋나지 않게 다시 내어 "
                        "이 재사용을 검사했다."),
            "입력파일": {
                "12_fox8전이.json": os.path.basename(FOX8_JSON),
                "fox8_sqlite": os.path.basename(FOX8_DB),
                "04": os.path.basename(MEASURE_JSON),
                "05": os.path.basename(RATES_JSON),
                "06": os.path.basename(COMPARE_JSON),
                "07": os.path.basename(FEATURE_JSON),
                "01": os.path.basename(ACCOUNTS_JSON),
            },
            "승계_해시": chain,
            "기능어_해시": FUNCWORD_HASH,
            "라벨_사용": ("사용함. fox8 라벨(12 JSON의 계정별 '라벨')로 무더기를 "
                       "가르고, 봇 무더기에서만 자기폭로 계정을 뺐다. BotSim "
                       "라벨(01)은 기준선의 출처를 적기 위해서만 읽었다."),
            "복사한_함수": copy_rows,
            "판정규칙_상수": {"Q_ALPHA": Q_ALPHA, "DELTA_NOTABLE": DELTA_NOTABLE,
                         "SPARSE_FRAC": SPARSE_FRAC},
            "BH가족": {"F블록": res["F가족"], "형태자질": res["M가족"],
                     "UPOS": res["U가족"],
                     "엄격": {"F블록": res_s["F가족"], "형태자질": res_s["M가족"],
                            "UPOS": res_s["U가족"]},
                     "비고": ("세 가족에 각각 별도로 보정했다. 총사용률·산포·"
                            "계정별 거리는 가족 밖 단독이라 q = p 다. "
                            "위쪽 셋은 ① 비리트윗 무더기, '엄격'은 ② 무더기.")},
            "총소요초": round(elapsed, 1),
        },
        "봇제한": {
            "규칙": ("12의 clean_doc 자기폭로 탐지를 fox8 원본의 **모든 행**에 "
                   "다시 걸어 두 기준의 봇 무더기를 만들었다. ① 비리트윗 기준 — "
                   "12가 정제를 건 행 집합(is_retweet = 0)에서 한 번이라도 걸린 "
                   "계정을 뺀다. ② 엄격 기준 — 리트윗을 포함해 어떤 행에서도 "
                   "걸리지 않은 계정만 남긴다. 정제를 통과한 문서만이 아니라 "
                   "원문 전체를 본다. 사전선언 19의 '원문에 한 번도 없는'에 더 "
                   "가까운 ②를 주 판정으로 삼는다."),
            "12_적격봇": len(bot_all) if not small else None,
            "자기폭로_봇": len(bot_drop),
            "잔류_봇": len(bot_keep),
            "엄격": {
                "정의": ("리트윗을 포함해 어떤 행에서도 자기폭로 문구에 걸리지 "
                       "않은 봇 계정만. 사전선언 19의 문구 '자기폭로 문장이 "
                       "원문에 한 번도 없는 계정'에 더 가깝다."),
                "자기폭로_봇": len(bot_drop_strict),
                "잔류_봇": len(bot_keep_strict),
                "비리트윗_잔류중_리트윗에서_걸린_봇": rt_only,
                "검산": (len(bot_keep) == len(bot_keep_strict) + rt_only),
                "주판정": True,
            },
            "사람": len(hum_all),
            "사람_자기폭로_걸린계정": len(hum_hit),
            "사람_자기폭로_걸린계정_리트윗포함": len(hum_hit_rt),
            "사람은_빼지_않음": True,
            "리트윗포함시_추가로_걸리는_잔류봇": rt_only,
            "리트윗포함시_추가로_걸리는_잔류봇_비고": (
                "v1(.19_fox8재검증_v1_리트윗버그.json)은 이 칸을 0으로 적었다. "
                "scan_self_reveal 이 리트윗에서만 걸린 계정을 반환 사전에서 "
                "빠뜨려 구조적으로 0이 될 수밖에 없었다. 고친 뒤의 실측값이 "
                "이 수다."),
            "걸린계정_라벨별": dict(rev_by_label),
            "걸린문서_라벨별": dict(rev_docs_by_label),
            "걸린계정_라벨별_리트윗포함": dict(rev_by_label_rt),
            "걸린문서_라벨별_리트윗포함": dict(rev_docs_by_label_rt),
            "12가_센_걸린문서": V12_EXCISED_DOCS,
            "사전선언_어림": {"봇전체": PRE_EXPECT_BOT_TOTAL,
                        "자기폭로": PRE_EXPECT_SELFREVEAL_ACCOUNTS,
                        "남는봇": PRE_EXPECT_KEPT,
                        "비고": ("사전선언 19의 945/1,139는 12 실행 전의 어림이다. "
                               "12 실행분의 적격 계정은 봇 1,094 · 사람 897이며 "
                               "19는 어림이 아니라 12 실행분을 잇는다.")},
            "문서수_중앙값": {"잔류": md_keep, "제외": md_drop},
            "문서수_중앙값_엄격": {"잔류": md_keep_s, "제외": md_drop_s},
        },
        "재현관문": gate,
        "주비교": {
            "정의": "그룹1 = 자기폭로 없는 fox8 봇 · 그룹2 = fox8 사람 (12와 같은 사람)",
            "n_bot": len(ids_bot_keep), "n_human": len(ids_hum),
            "희소기준": cut,
            "총사용률": {
                "U": rnd(tot["U"], 1), "z": rnd(tot["z"], STAT_DIGITS),
                "p": sig(tot["p"]), "q": sig(tot["p"]),
                "델타": rnd(tot["델타"], STAT_DIGITS),
                "단독AUC": rnd(auc_from_delta(tot["델타"]), STAT_DIGITS),
                "방향": tot["방향"],
                "봇_요약": {k: rnd(v, RATE_DIGITS) for k, v in q_bot.items()},
                "사람_요약": {k: rnd(v, RATE_DIGITS) for k, v in q_hum.items()},
                "12_델타": V12_TOTAL_DELTA,
                "06_BotSim_델타_참고": (d06.get("총사용률_비교") or {}).get("델타"),
            },
            "가족요약": {"F블록": f_sum, "형태자질": m_sum, "UPOS": u_sum},
            "F블록": {k: c for k, c in pairs["F블록"]},
            "형태자질": {k: c for k, c in pairs["형태자질"]},
            "UPOS": {k: c for k, c in pairs["UPOS"]},
        },
        "주비교_엄격": {
            "정의": ("그룹1 = 리트윗 포함 어떤 행에서도 자기폭로가 없는 fox8 봇 · "
                   "그룹2 = fox8 사람 (12와 같은 사람). 주 판정 무더기."),
            "n_bot": len(ids_bot_keep_strict), "n_human": len(ids_hum),
            "희소기준": res_s["희소기준"],
            "총사용률": {
                "U": rnd(tot_s["U"], 1), "z": rnd(tot_s["z"], STAT_DIGITS),
                "p": sig(tot_s["p"]), "q": sig(tot_s["p"]),
                "델타": rnd(tot_s["델타"], STAT_DIGITS),
                "단독AUC": rnd(auc_from_delta(tot_s["델타"]), STAT_DIGITS),
                "방향": tot_s["방향"],
                "봇_요약": {k: rnd(v, RATE_DIGITS)
                        for k, v in sums_s["총사용률사분위"][0].items()},
                "사람_요약": {k: rnd(v, RATE_DIGITS)
                          for k, v in sums_s["총사용률사분위"][1].items()},
                "12_델타": V12_TOTAL_DELTA,
            },
            "가족요약": {"F블록": f_sum_s, "형태자질": m_sum_s, "UPOS": u_sum_s},
            "F블록": {k: c for k, c in pairs_s["F블록"]},
            "형태자질": {k: c for k, c in pairs_s["형태자질"]},
            "UPOS": {k: c for k, c in pairs_s["UPOS"]},
        },
        "전이": {
            "정의": "δ_BotSim(06·07) 과 δ_19 의 Spearman ρ와 방향 일치율. 12와 같은 구현.",
            "가족별": {f: {k: v for k, v in corr_whole[f].items()
                        if k not in ("x_BotSim", "y_fox8", "항목목록")}
                    for f in families},
            "앞주목_한정": {f: {k: v for k, v in corr_notable[f].items()
                          if k not in ("x_BotSim", "y_fox8", "항목목록")}
                      for f in families},
            "12와_나란히": {f: {"12_rho": V12_RHO[f],
                           "19_rho": corr_whole[f]["rho"],
                           "12_방향일치율": V12_DIR_RATE[f],
                           "19_방향일치율": corr_whole[f]["방향일치율"]}
                       for f in families},
        },
        "전이_엄격": {
            "정의": ("δ_BotSim(06·07) 과 δ_19(엄격 무더기) 의 Spearman ρ와 "
                   "방향 일치율. 12와 같은 구현. 주 판정 무더기."),
            "가족별": {f: {k: v for k, v in corr_whole_s[f].items()
                        if k not in ("x_BotSim", "y_fox8", "항목목록")}
                    for f in families},
            "앞주목_한정": {f: {k: v for k, v in corr_notable_s[f].items()
                          if k not in ("x_BotSim", "y_fox8", "항목목록")}
                      for f in families},
            "12와_나란히": {f: {"12_rho": V12_RHO[f],
                           "19엄격_rho": corr_whole_s[f]["rho"],
                           "19비리트윗_rho": corr_whole[f]["rho"],
                           "12_방향일치율": V12_DIR_RATE[f],
                           "19엄격_방향일치율": corr_whole_s[f]["방향일치율"],
                           "19비리트윗_방향일치율": corr_whole[f]["방향일치율"]}
                       for f in families},
        },
        "산포": {
            "정의": "계정별 '같은 무더기 안 다른 계정들과의 L1 거리 중앙값'을 U로 견준다.",
            "계정별거리_무더기": dist_piles,
            "계정별거리검정": ({"U": rnd(acct["U"], 1),
                          "z": rnd(acct["z"], STAT_DIGITS),
                          "p": sig(acct["p"]), "q": sig(acct["p"]),
                          "델타": rnd(acct["델타"], STAT_DIGITS),
                          "방향": acct["방향"],
                          "q비고": "가족 밖 단독 검정이라 q = p."}
                         if acct else {"검정가능": False}),
            "12_계정별거리_델타": V12_DIST_DELTA,
            "09_BotSim_매칭표본_델타": disp09.get("델타"),
            "총사용률_BF": pack_disp(bf_total),
            "무더기_이름": {"봇①(비리트윗)": "① 비리트윗 기준",
                       "봇②(엄격)": "② 엄격 기준(주 판정)",
                       "사람": "12와 같은 fox8 사람"},
        },
        "산포_엄격": {
            "정의": ("엄격 무더기의 계정별 '같은 무더기 안 다른 계정들과의 L1 "
                   "거리 중앙값'을 사람과 U로 견준다. 부분집합이라 거리를 새로 "
                   "계산했다 — 비리트윗 무더기의 값을 잘라 쓰지 않았다."),
            "계정별거리검정": ({"U": rnd(acct_s["U"], 1),
                          "z": rnd(acct_s["z"], STAT_DIGITS),
                          "p": sig(acct_s["p"]), "q": sig(acct_s["p"]),
                          "델타": rnd(acct_s["델타"], STAT_DIGITS),
                          "방향": acct_s["방향"],
                          "q비고": "가족 밖 단독 검정이라 q = p."}
                         if acct_s else {"검정가능": False}),
            "12_계정별거리_델타": V12_DIST_DELTA,
            "09_BotSim_매칭표본_델타": disp09.get("델타"),
            "총사용률_BF": pack_disp(bf_total_s),
        },
        "사전예측결과": verdicts,
        "사전예측결과_엄격": verdicts_s,
        "사전예측_주판정": {
            "주판정_무더기": "엄격(리트윗 포함 어떤 행에서도 걸리지 않은 봇)",
            "주판정_키": "사전예측결과_엄격",
            "보조판정_키": "사전예측결과",
            "이유": ("사전선언 19의 문구는 '자기폭로 문장이 원문에 한 번도 없는 "
                   "계정'이다. 리트윗도 그 계정의 타임라인에 실린 원문이므로 "
                   "엄격 무더기가 그 문구에 더 가깝다. 두 판정을 모두 싣고 "
                   "어느 쪽도 감추지 않는다."),
            "한줄대조": [{"번호": a["번호"], "엄격_주": a["판정"],
                      "비리트윗_보조": b["판정"]}
                     for a, b in zip(verdicts_s, verdicts)],
        },
    }
    write_json(out_json, out)
    size = os.path.getsize(out_json)
    print(f"  {os.path.basename(out_json)}  ({size:,} 바이트)")
    if os.path.exists(PROGRESS_JSON) and not small:
        os.remove(PROGRESS_JSON)
        print(f"  {os.path.basename(PROGRESS_JSON)} 삭제 (작업이 끝났다)")
    print(f"  총 소요 {fmt_dur(elapsed)}")

    # ── 확인 항목 ───────────────────────────────────────────────
    line("확인 항목")
    print("  이 파일이 스스로 검사할 수 없는 것들이다. 사람이 눈으로 보라.")
    print()
    print("  ① 재현 관문이 통과했는가. [5/9]가 봇을 하나도 빼지 않은 상태로")
    print("     12의 δ를 다시 내어 F 172 · 형태자질 · UPOS · 총사용률 전부가")
    print("     12 JSON과 같았는지 보라. 이 관문이 19의 재사용 전체를 떠받친다.")
    print("     어긋난 항목이 하나라도 있으면 아래 수는 읽지 말 것.")
    print()
    print("  ② 봇을 얼마나 뺐는가. [4/9]의 표를 보라. 사전선언은 945를 뺄")
    print("     것이라 어림했으나 실측은 다르다. 남은 봇이 너무 적으면(수십")
    print("     계정) 검정력이 무너져 |δ|만 읽어야 한다. 무더기가 둘이므로")
    print("     어느 무더기의 수를 인용하는지 반드시 밝히라 — ② 엄격이 주")
    print("     판정이고 ①은 보조다.")
    print()
    print("  ②-b 두 무더기의 판정이 갈리는 예측이 있는가. [9/9] 끝의 한 줄")
    print("     대조표를 보라. 갈린다면 그 예측은 '리트윗에서 자기폭로가 걸린")
    print(f"     {rt_only}계정을 넣느냐 빼느냐'에 달려 있다는 뜻이고, 어느 쪽도")
    print("     단독으로 인용할 수 없다.")
    print()
    print("  ③ 19가 지운 의심은 하나뿐이다. '자기폭로로 발견된 봇에 한정'이")
    print("     아니라는 것. 12의 다른 한계 — 봇 2023 / 사람 ≤2020 으로 연도")
    print("     AUC 1.000, fox8을 봉인 라인이 여섯 번 쓴 것, δ_BotSim과")
    print("     δ_fox8의 대조군이 서로 다른 것 — 는 19에도 그대로 남는다.")
    print("     19의 ρ가 양수라고 해서 그 셋이 해결되지 않는다.")
    print()
    print("  ④ 사람 무더기는 손대지 않았다. 사람 쪽에도 자기폭로가 걸린 계정이")
    print("     있다면([4/9]에 수가 있다) 그 계정을 왜 두었는지 스스로 답해")
    print("     보라 — 사전선언이 '사람은 그대로'라고 적었기 때문이다. 사후에")
    print("     양쪽을 다 빼는 쪽으로 바꾸면 그것은 결과를 보고 하는 선택이다.")
    print()
    print("  ⑤ 문서수 중앙값(P19-4)은 예측이 아니라 표본 성격의 기록이다.")
    print("     잔류 봇이 제외 봇보다 활동량이 적다면, 19의 봇 무더기는 '덜")
    print("     쓴 봇'이기도 하다. 분량 혼입(08)이 여기에 얹혀 있을 수 있다.")
    print()
    print("=" * 74)
    print("19 끝.")
    print("=" * 74)


def platform_python():
    """실행 환경 한 줄. JSON의 설정 칸에 남긴다."""
    return f"{sys.version.split()[0]}"


if __name__ == "__main__":
    main()
