#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
10-1_귀무오류율.py  (v1.2 규칙)
────────────────────────────────────────────────────────────────────────────
판 기록
    v1.1 규칙 실행(2026-09-27 05:01)은 불통과였다. 산출은 이름을 바꿔 두었다
    (10-1_귀무오류율_v1.1규칙.json · _출력.log). 모의 A 위쪽 거짓 유의 F 16/200 ·
    M 10/200 · R 7/200, 모의 B 위쪽 F 200/200 · M 194/200 · R 107/200.
    v1.2 규칙: 10 결정 B2(중심 정렬)를 반복 절차에 넣었다. 백분위 직전에 가짜
    집단마다 원값 중앙값을 뺀다. 판정(200회, 칸마다 Wilson 95% 상한 ≤ 0.10)은
    그대로다. 이동 불변 관문(D)과 --reps 옵션을 더했다.

한계 먼저
    · 이 파일은 10 절차(자기 중심 거리 + 쌍 안 교환 순열)의 거짓 유의율만 잰다.
      봇 자료는 쓰지 않는다. 12 표 (a) 풀의 사람 640명만 쓴다.
    · 귀무 모의는 사람을 무작위로 반분한 가짜 두 집단이다. 실제 봇과 사람 사이의
      다른 차이(주제 폭, 글 길이 분포 모양)는 모의에 들어가지 않는다.
    · 위치 이동 모의(B)는 자질마다 같은 크기(사람 640의 MAD × 1)를 더하는 한
      가지 형태만 본다. 다른 모양의 위치 차이는 재지 않는다.
    · 200회 반복이라 거짓 유의율의 Wilson 95% 구간 폭이 약 ±0.03이다. 참 거짓
      유의율이 정확히 0.05여도 한 칸의 상한이 0.10을 넘을 확률이 약 0.30이다.
      관문 자체의 이 오경보율을 JSON에 계산해 적는다. 규칙은 고치지 않는다.

목적
    12 뼈대 v3.1 5절 8항 "10 절차 귀무 오류율 관문". 12 표 (a)의 (iii)열은 10
    절차의 F·M·R 비율과 p를 쓴다. 그 절차가 "산포가 같은" 두 집단에서 α = 0.05
    근처로 거짓 유의를 내는지, 위치만 다르고 산포가 같을 때도 그런지 본다.

절차 (10 사전선언 4절, 10 정본 함수 승계)
    A. 반분 반복 r = 0..199
       1. 640명(uid 오름차순)을 시드 20260926 + r로 섞어 앞 320명 = 가짜 봇,
          뒤 320명 = 가짜 사람.
       2. 09-1 캘리퍼 매칭: |log 토큰수_구두점제외 비| ≤ 0.10, 그리디, 가짜 봇을
          random.Random(20260926 + r)로 섞고, 사람은 uid 오름차순에서 최근접.
       3. 쌍 표본 안에서 [가짜 라벨] 중심 정렬(10 결정 B2 : 자질마다 가짜 봇·가짜
          사람 각자의 원값 중앙값을 뺀다) → 백분위 → [가짜 라벨] 집단 중심 →
          자기 중심 블록 거리 → 비율(가짜 사람 거리 중앙값 ÷ 가짜 봇 거리 중앙값).
       4. [가짜 라벨] 쌍 안 교환 순열 999회(같은 시드 흐름). 위쪽 단측 p(비율 > 1
          쪽), 아래쪽 단측 p(비율 < 1 쪽), 양측 p를 모두 적는다.
       5. F·M·R 블록마다 따로. 세 블록은 같은 교환 행렬을 쓴다(10 결정 G).
    B. 위치 이동 모의: A와 같은 r의 같은 반분·매칭·교환 행렬에서, 가짜 봇 쪽
       원값(백분위 전)에 자질별로 사람 640의 MAD × 1을 더한 뒤 3~5를 다시 한다.
       0인 값에도 그대로 더한다. 결측은 결측. v1.2 규칙에서는 정렬이 이 이동을
       지우므로 B는 A와 같아야 한다.
    C. 판정: A·B 각각 F·M·R의 거짓 유의율(p < 0.05 비율) Wilson 95% 상한이
       0.10 이하면 통과. 아니면 불통과로 기록만 한다(규칙 수정 없음). 선언된
       판정은 200회 실행에 건다. --reps로 늘린 실행은 참고로 같은 표를 적는다.
    D. (v1.2) 이동 불변 관문: 반복마다 F·M·R의 |비율_A − 비율_B| ≤ 1e-9이고
       p(위·아래·양측)가 같아야 한다. 어긋난 반복은 숨기지 않고 적는다. 예상되는
       원인은 부동소수점뿐이다. (x + s) − 중앙(x + s)와 x − 중앙(x)는 끝자리가
       다를 수 있고, 그러면 두 가짜 집단 사이의 동점이 풀리거나 새로 생겨 순위가
       움직인다. 어긋난 반복마다 정렬값 최대차와 백분위가 달라진 자질 수를 함께
       적어 이 설명이 맞는지 보인다.

관문 (하나라도 실패하면 본 계산에 들어가지 않고 JSON을 쓰지 않는다)
    관문 1  함수 승계: 10 정본(v1.2)에서 옮긴 함수 21개(v1.2의 center_groups 포함)와
            09-1 caliper_match가 원본과 같은 AST다(docstring 제외). 원 단계(04·05·
            07·08·옛 09)와도 대조한다. 앞 단계 상수도 대조한다.
            손 예제: 10 v1.2의 6계정(3쌍) × 3자질을 본 계산과 같은 run_procedure로
            돌려 정렬값·백분위·중심·거리·비율·교환 8가지·p(위·아래·양측)를
            손계산과 대조한다. 매칭 손 예제(09-1의 8계정), MAD·이동 손 예제, Wilson 구간을
            scipy와 대조한다.
    관문 2  실제 자료 재현: 10 정본 입력(04·04-1·02·07·FMR 쌍)으로 1,024계정의
            F·M·R 비율(F 1.237610 등)·계정별 거리·중심·p·순열 분포 요약을 같은
            run_procedure(교환 10,000회, 시드 20260926)로 재현한다. (v1.2) 대조
            대상은 보관된 10 v1.1 정본 JSON이고 run_procedure를 center=False로
            부른다. v1.2 정본(10 실행)은 사전선언 순서상 이 파일 뒤에 돈다. 정렬
            경로는 AST 대조(center_groups)와 손 예제가 지킨다. 09-1의 512쌍
            목록을 같은 caliper_match(시드 20260827)로 재현한다.
    관문 3  사람 풀: 13-0 계정사전의 관문통과 = true, 역할 표a인 사람 = 분할.json의
            표a = 640, 시험(봉인) 234와 교집합 0, 라벨 human, 내부 관계
            (문장길이 개수·합, 구두점토큰수 = UPOS PUNCT), 기능어 키 ⊂ 172종.

구현 결정 (규격에 없어 이 파일을 쓰며 정한 것. JSON 설정에도 같은 목록)
    E1  자질 목록과 축 분류는 10 정본과 같게 04 전체 1,869계정에서 유도한다
        (형태 58 + 품사 17, 축 분류 = FMR 고정값). 13-0에서 유도한 값과 다르면
        기록만 한다. 12 표 (a)가 10과 같은 250자질을 써야 10과 견줄 수 있고,
        09-2(댓글 한정)도 FMR 고정 축 분류를 썼다.
    E2  난수 흐름: 반복 r마다 numpy default_rng(20260926 + r) 하나로 반분
        (permutation)을 뽑고 같은 흐름에서 이어 교환 행렬(random)을 뽑는다. 같은
        시드로 생성기를 두 번 새로 만들면 반분과 교환이 같은 비트를 공유한다.
        매칭의 봇 섞기는 09-1 함수 그대로 random.Random(20260926 + r)이다.
    E3  반분 크기는 320 : 320. 매칭 입력은 봇·사람 모두 uid 오름차순 목록이다.
    E4  MAD = 사람 640 원값의 median(|x - median(x)|). 1.4826 보정 없음, 결측 제외,
        640 전체에서 한 번 구한다. F는 05 규칙으로 6자리 반올림한 사용률에 더하고
        다시 반올림하지 않는다. MAD가 0인 자질은 이동이 0이다(수를 기록).
    E5  A와 B는 같은 r에서 같은 반분·매칭·교환 행렬을 쓴다. 두 시나리오의 차이는
        이동 하나뿐이다.
    E6  아래쪽 단측 p = (순열비율 ≤ 관측비율 횟수 + 1) ÷ (999 + 1). 상대 허용오차
        1e-12(10 결정 H의 거울). 위쪽 단측 p와 양측 p는 10 p_values 그대로.
    E7  주 판정 방향은 위쪽(비율 > 1, 가짜 봇이 더 좁음)이다. 10과 12가 이
        방향으로 주장한다. 아래쪽은 같은 문턱으로 보조 판정을 적고, 두 방향 모두
        통과인지도 적는다. 양측 p는 기록만 한다.
    E8  반복 안에서 거리를 정의할 수 없는 블록(nan 거리, 봇 거리 중앙값 0)이
        나오면 그 반복의 그 블록을 무효로 세고 분모에서 뺀다. 수를 보고한다.
        10은 이때 멈췄지만 모의 200회 가운데 한 번 때문에 전체를 멈추지 않는다.
    E9  Wilson 95%의 z = 1.959963984540054. scipy는 관문 1의 대조에만 쓴다.
    E10 복사 함수의 docstring은 줄표 금지 규칙 때문에 짧게 다시 썼고 주석의
        줄표는 쌍점으로 바꿨다. 대조는 docstring을 뺀 AST로 한다(13-0 G1 방식).
    E11 반복 안에서 정의된 계정이 2개 미만인 자질은 그 반복의 거리 평균에 들어가지
        않는다(percentile_column이 nan을 돌려준다). 수를 기록한다.
    E12 (v1.2) 이동 불변 관문(D)의 허용오차는 비율 1e-9, p는 완전 일치. 한쪽만
        무효인 블록은 위반으로 센다. 위반은 판정 표와 따로 적는다.
    E13 (v1.2) 반복 안의 중심 정렬에서 가짜 집단의 정의된 값이 2개 미만인 자질은
        그 집단만 빼지 않는다(10 결정 B2). 수를 기록한다.
    E14 (v1.2) --reps N(기본 200). 시드는 r = 0..N-1에 20260926 + r이라 1,000회
        실행의 앞 200회는 200회 실행과 같은 반분·매칭·교환이다. N이 200이 아니면
        산출 이름에 _N회를 붙인다(10-1_귀무오류율_1000회.json). 선언된 판정은
        200회 실행에 건다.

라벨 사용 지점
    · 관문 2의 10 재현과 09-1 재현(실제 라벨: 쌍 구분, 01 라벨)
    · 관문 3의 사람 풀 정의(역할 표a, 라벨 human 확인)
    · 반복 안의 중심 정렬·중심·순열은 가짜 라벨(무작위 반분)이다. 실제 라벨은
      쓰지 않는다.

실행
    단계별 진행경과 폴더에서:
    PYTHONDONTWRITEBYTECODE=1 /Users/son/.claude/venvs/audio-transcribe/bin/python -u \\
        10-1_귀무오류율.py | tee 10-1_귀무오류율_출력.log
    1,000회 참고 실행:
    PYTHONDONTWRITEBYTECODE=1 /Users/son/.claude/venvs/audio-transcribe/bin/python -u \\
        10-1_귀무오류율.py --reps 1000 | tee 10-1_귀무오류율_1000회_출력.log

산출
    10-1_귀무오류율.json : 설정·해시·관문·반복별 값·요약·판정 (--reps N이면 _N회)
"""

import argparse
import ast
import hashlib
import json
import math
import os
import platform
import random
import statistics
import sys
import time
from datetime import datetime

import numpy as np

sys.dont_write_bytecode = True


# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
HERE = os.path.dirname(os.path.abspath(__file__))      # 단계별 진행경과
ROOT = os.path.dirname(HERE)                           # 연구주제
FMR_DIR = os.path.join(HERE, "09_FMR 통제 재검증")
ARCHIVE = os.path.join(ROOT, "# 07-12 실행분 보관 (미학습)")
DATA_DIR = os.path.expanduser("~/DM_LAB_data/12_OpenRouter")

ACCDICT_JSON = os.path.join(DATA_DIR, "13-0_계정사전.json")        # 13-0 산출 (읽기만)
SPLIT_JSON = os.path.join(HERE, "12_OpenRouter생성_준비", "분할.json")
PY10 = os.path.join(HERE, "10_동질성검정.py")
# 관문 2 대조 대상 : 보관된 10 v1.1 정본 JSON (v1.2 정본은 이 파일 뒤에 돈다)
J10_V11 = os.path.join(ARCHIVE, "2026-09-27 10 v1.1 (귀무 오류율 관문 불통과)", "10_동질성검정.json")
PY091 = os.path.join(HERE, "09-1_분량통제.py")
J091 = os.path.join(HERE, "09-1_분량통제.json")
PY130 = os.path.join(HERE, "13-0_댓글한정재파싱.py")
MEASURE_JSON = os.path.join(HERE, "04_기능어측정.json")
REPARSE_JSON = os.path.join(HERE, "04-1_확장재파싱.json")
FUNCWORDS_JSON = os.path.join(HERE, "02_기능어목록.json")
FEATURE_JSON = os.path.join(HERE, "07_형태자질비교.json")
ACCOUNTS_JSON = os.path.join(HERE, "01_적격계정.json")
FMR_JSON = os.path.join(FMR_DIR, "FMR_세통제_결과.json")
PREREG_12 = os.path.join(HERE, "12_OpenRouter생성_사전선언_뼈대.md")
PREREG_10 = os.path.join(HERE, "10_동질성검정_사전선언.md")

# 원 단계 소스 (10 결정 M의 COPY_SOURCES와 같은 대응). 관문 1에서 AST 대조.
ORIGINAL_SOURCES = {
    "compute_rates": os.path.join(HERE, "05_사용률검수.py"),
    "build_axis_map": os.path.join(HERE, "07_형태자질비교.py"),
    "axis_of": os.path.join(HERE, "07_형태자질비교.py"),
    "denom_kind_of": os.path.join(HERE, "07_형태자질비교.py"),
    "compute_ratios": os.path.join(HERE, "07_형태자질비교.py"),
    "compute_upos_ratios": os.path.join(HERE, "07_형태자질비교.py"),
    "coef_variation": os.path.join(HERE, "08_R블록.py"),
    "compute_features": os.path.join(HERE, "08_R블록.py"),
    "dense_vectors": os.path.join(ARCHIVE, "09_산포검정.py"),
    "normalize_apostrophe": os.path.join(HERE, "04_기능어측정.py"),
}
FROM_10 = ["compute_rates", "build_axis_map", "axis_of", "denom_kind_of", "compute_ratios",
           "compute_upos_ratios", "coef_variation", "compute_features", "dense_vectors",
           "normalize_apostrophe", "percentile_column", "percentile_matrix", "nanmedian_cols",
           "center_groups", "centers", "block_distances", "ratio_of", "perm_ratios", "p_values", "exact_p", "five"]
FROM_091 = ["caliper_match"]

OUT_JSON = os.path.join(HERE, "10-1_귀무오류율.json")

# ── 과제 상수 (12 뼈대 5절 8항 · 작업 지시) ─────────────────────
SEED = 20260926
N_REP = 200                    # 선언된 반복 수. 판정은 이 수에 건다(--reps로 늘린 실행은 참고)
N_PERM = 999
ALPHA = 0.05
CALIPER = 0.10                 # 09-1
SHIFT_MAD_MULT = 1.0           # B : 사람 MAD × 1
GATE_UPPER = 0.10              # C : Wilson 상한 문턱
INVAR_TOL = 1e-9               # D : 이동 불변 관문의 비율 허용오차 (E12)
WILSON_Z = 1.959963984540054   # 표준정규 0.975 분위 (E9)
EXPECT_POOL = 640
EXPECT_TEST = 234

# ── 10 정본 재현 상수 ─────────────────────────────────────────
N_PERM_10 = 10_000
SEED_091 = 20260827            # 09-1 매칭 시드
EXPECT_ACCOUNTS = 1869
EXPECT_WORDS = 172
EXPECT_HASH = "382b68572f03bc23"
EXPECT_PAIRS = 512
EXPECT_M_FEAT = 58
EXPECT_M_UPOS = 17
REPRO_TOL = 1e-12

# ── 앞 단계 함수가 쓰는 상수 (10 정본과 같은 값. 관문 1에서 대조) ──
RATE_DIGITS = 6
DENOM_AXIS = "축내부합"
DENOM_TOKEN = "토큰수_구두점제외"
MIN_SENTENCES_CV = 5
RKEYS = ["문장당_토큰수", "구두점_비율", "문장길이_변동계수"]
BLOCKS = ["F", "M", "R"]
REL_TOL = 1e-12
HAND_TOL = 1e-9

IMPL_DECISIONS = {
    "E1_자질목록": "10 정본과 같게 04 전체 1,869계정에서 유도(형태 58 + 품사 17, 축 분류 = FMR 고정값). 13-0에서 유도한 값과의 차이는 기록만.",
    "E2_난수흐름": "반복 r마다 numpy default_rng(20260926 + r) 하나로 반분(permutation) 뒤 같은 흐름에서 교환 행렬(random). 매칭 봇 섞기는 09-1 함수 그대로 random.Random(20260926 + r).",
    "E3_반분": "uid 오름차순 640명을 섞어 앞 320 = 가짜 봇, 뒤 320 = 가짜 사람. 매칭 입력은 두 목록 모두 uid 오름차순.",
    "E4_MAD": "사람 640 원값의 median(|x - median(x)|), 1.4826 보정 없음, 결측 제외, 640 전체에서 한 번. F는 6자리 반올림 사용률에 더하고 재반올림 없음. MAD 0 자질은 이동 0.",
    "E5_AB짝": "A와 B는 같은 r에서 같은 반분·매칭·교환 행렬. 차이는 이동 하나.",
    "E6_아래쪽p": "(순열비율 ≤ 관측비율 횟수 + 1) ÷ 1,000, 상대 허용오차 1e-12. 위쪽·양측 p는 10 p_values 그대로.",
    "E7_판정방향": "주 판정 = 위쪽(비율 > 1). 아래쪽은 같은 문턱의 보조 판정. 두 방향 모두 통과인지도 기록. 양측 p는 기록만.",
    "E8_무효반복": "반복 안에서 nan 거리 또는 봇 거리 중앙값 0이면 그 반복의 그 블록을 무효로 세고 분모에서 뺌.",
    "E9_Wilson": "z = 1.959963984540054. scipy binomtest wilson과 관문 1에서 대조(scipy는 대조에만 씀).",
    "E10_복사함수": "코드는 10 정본(caliper_match는 09-1) 그대로. docstring은 줄표 금지 때문에 다시 썼고 주석의 줄표는 쌍점으로. docstring을 뺀 AST로 대조.",
    "E11_정의2미만": "반복 안에서 정의된 계정 2개 미만인 자질은 그 반복의 거리 평균에서 빠짐. 수를 기록.",
    "E12_이동불변": "(v1.2) 반복마다 F·M·R의 |비율_A - 비율_B| ≤ 1e-9이고 p 셋(위·아래·양측) 완전 일치. 한쪽만 무효면 위반. 위반은 정렬값 최대차·백분위 다른 자질 수와 함께 기록.",
    "E13_정렬제외": "(v1.2) 반복 안 중심 정렬에서 가짜 집단의 정의된 값이 2개 미만인 자질은 그 집단만 빼지 않음(10 결정 B2). 수를 기록.",
    "E14_반복수": "(v1.2) --reps N(기본 200). 시드 20260926 + r이라 1,000회의 앞 200회는 200회 실행과 같음. N이 200이 아니면 산출 이름에 _N회. 선언 판정은 200회 실행.",
    "관문2_대조대상": "(v1.2) 보관된 10 v1.1 정본 JSON을 run_procedure(center=False)로 재현. v1.2 정본은 사전선언 순서상 10-1 뒤에 실행.",
}


# ════════════════════════════════════════════════════════════════════════
# [손 예제] 10 정본(v1.2)과 같은 6계정(3쌍) × 3자질. 손계산은 10 파일 상수 주석에 있다.
# 아래쪽 p만 이 파일에서 새로 센다.
#   교환 8가지 비율 4/3 · 6/5 · 5/6 · 4/3 · 3/4 · 6/5 · 5/6 · 3/4
#   관측 4/3 이하: 8개 전부 → 정확 아래쪽 p = 8/8, 공식 (8+1)/(8+1) = 9/9
# ════════════════════════════════════════════════════════════════════════
HAND_IDS = ["B1", "B2", "B3", "H1", "H2", "H3"]
HAND_PAIRS = [("B1", "H1"), ("B2", "H2"), ("B3", "H3")]
HAND_VALUES = {
    "a": {"B1": 3, "B2": 4, "B3": 5, "H1": 1, "H2": 6, "H3": 7},
    "b": {"B1": 10, "B2": 10, "B3": 20, "H1": 30, "H2": 5, "H3": 40},
    "c": {"B1": 0.5, "B2": 0.125, "B3": None, "H1": 0.875, "H2": 0.25, "H3": 0.75},
}
HAND_CENTERED = {
    "a": {"B1": -1, "B2": 0, "B3": 1, "H1": -5, "H2": 0, "H3": 1},
    "b": {"B1": 0, "B2": 0, "B3": 10, "H1": 0, "H2": -25, "H3": 10},
    "c": {"B1": 0.1875, "B2": -0.1875, "B3": None, "H1": 0.125, "H2": -0.5, "H3": 0.0},
}
HAND_PCT = {
    "a": {"B1": 0.2, "B2": 0.5, "B3": 0.9, "H1": 0.0, "H2": 0.5, "H3": 0.9},
    "b": {"B1": 0.4, "B2": 0.4, "B3": 0.9, "H1": 0.4, "H2": 0.0, "H3": 0.9},
    "c": {"B1": 1.0, "B2": 0.25, "B3": None, "H1": 0.75, "H2": 0.0, "H3": 0.5},
}
HAND_CENTER_BOT = {"a": 0.5, "b": 0.4, "c": 0.625}
HAND_CENTER_HUMAN = {"a": 0.5, "b": 0.4, "c": 0.5}
HAND_DIST = {"B1": 9 / 40, "B2": 1 / 8, "B3": 9 / 20,
             "H1": 1 / 4, "H2": 3 / 10, "H3": 3 / 10}
HAND_RATIO = 4 / 3
HAND_SWAPS = {
    (0, 0, 0): 4 / 3, (1, 0, 0): 6 / 5, (0, 1, 0): 5 / 6, (0, 0, 1): 4 / 3,
    (1, 1, 0): 3 / 4, (1, 0, 1): 6 / 5, (0, 1, 1): 5 / 6, (1, 1, 1): 3 / 4,
}
HAND_EXACT_P1 = 2 / 8
HAND_EXACT_P2 = 4 / 8
HAND_EXACT_PLOW = 8 / 8
HAND_FORMULA_P1 = 3 / 9
HAND_FORMULA_P2 = 5 / 9
HAND_FORMULA_PLOW = 9 / 9
HAND_MC_TOL = 0.02

# ── 매칭 손 예제 (09-1 self_check_matching과 같은 인공 계정) ─────
#   b2(1000)의 후보: h3 1100(0.0953) · h5 1050(0.0488) → h5. h2 900은 0.1054로 경계 밖.
#   b1(100)·b3(103)은 h1(105) 하나를 다툰다 → 쌍 2, 탈락 봇 1. 섞기 순서와 무관한 성질만 본다.
MATCH_BOT_DENOM = {"b1": 100, "b2": 1000, "b3": 103}
MATCH_HUM_DENOM = {"h1": 105, "h2": 900, "h3": 1100, "h4": 10000, "h5": 1050}

# ── MAD·이동 손 예제 (5계정 × 3자질, 행 0·4가 가짜 봇) ─────────────
#   a [1,2,3,4,100]      중앙 3, |차| [2,1,0,1,97] → MAD 1
#   b [0,0,0,5,결측]     중앙 0, |차| [0,0,0,5]    → MAD 0
#   c [0,4,6,8,결측]     중앙 5, |차| [5,1,1,3]    → MAD 2
#   이동 뒤 행 0 = [2, 0, 2] (0에도 MAD를 더함) · 행 4 = [101, 결측, 결측]
MAD_X = [[1, 0, 0], [2, 0, 4], [3, 0, 6], [4, 5, 8], [100, None, None]]
MAD_BOT_ROWS = [0, 4]
MAD_EXPECT = [1.0, 0.0, 2.0]
MAD_SHIFTED_ROW0 = [2.0, 0.0, 2.0]
MAD_SHIFTED_ROW4 = [101.0, None, None]

# ── Wilson 손 예제 (k = 10, n = 200) ─────────────────────────────
#   p = 0.05, z² = 3.841459, 중심 (0.05 + 0.0096036) ÷ 1.0192073 = 0.058480
#   반폭 1.959964 × √(0.0002375 + 0.0000240091) ÷ 1.0192073 = 0.031098
#   → [0.027383, 0.089578]
WILSON_HAND = (10, 200, 0.027383, 0.089578)
WILSON_HAND_TOL = 1e-6


# ════════════════════════════════════════════════════════════════════════
# [복사한 함수] 코드는 10 정본(caliper_match는 09-1) 그대로 (E10).
# 관문 1이 docstring을 뺀 AST로 원본과 대조한다.
# ════════════════════════════════════════════════════════════════════════
# ── [10_동질성검정.py ← 05_사용률검수.py] compute_rates ──
def compute_rates(accounts):
    """[05 compute_rates, 10 정본 경유] 계정별 기능어 사용률. 분모 토큰수_구두점제외, 소수 6자리 반올림. 분모 0 계정은 따로 돌려준다."""
    rates, undefined = {}, []
    # uid 오름차순으로 담는다: 다시 돌려도 파일 순서가 같아야 비교가 쉽다.
    for uid in sorted(accounts):
        a = accounts[uid]
        denom = a["토큰수_구두점제외"]
        if denom == 0:
            undefined.append(uid)
            continue
        counts = a["기능어"]
        rates[uid] = {
            "총사용률": round(sum(counts.values()) / denom, RATE_DIGITS),
            "분모": denom,
            "사용률": {w: round(n / denom, RATE_DIGITS)
                     for w, n in counts.items()},
        }
    return rates, undefined


# ── [10_동질성검정.py ← 07_형태자질비교.py] build_axis_map ──
def build_axis_map(accounts):
    """[07 build_axis_map] 자료 전체에서 축별로 나타난 값 목록을 모은다. 반환 {축: 정렬된 값 목록}."""
    axis_values = {}
    for a in accounts.values():
        for key in a.get("자질", {}):
            axis, sep, val = key.partition("=")
            if not sep:
                # "="가 없는 키. UD 표기에서는 나올 일이 아니지만, 나온다면
                # 축 내부 비율을 정의할 방법이 없으므로 단일값 축으로 본다.
                axis, val = key, ""
            axis_values.setdefault(axis, set()).add(val)
    return {ax: sorted(vs) for ax, vs in axis_values.items()}


# ── [10_동질성검정.py ← 07_형태자질비교.py] axis_of ──
def axis_of(key):
    """[07 axis_of] 자질 키에서 축 이름만 떼어 낸다."""
    return key.split("=", 1)[0]


# ── [10_동질성검정.py ← 07_형태자질비교.py] denom_kind_of ──
def denom_kind_of(key, axis_map):
    """[07 denom_kind_of] 대립값 2개 이상인 축은 축 내부 합, 아니면 토큰수_구두점제외를 분모로."""
    return DENOM_AXIS if len(axis_map.get(axis_of(key), [""])) >= 2 else DENOM_TOKEN


# ── [10_동질성검정.py ← 07_형태자질비교.py] compute_ratios ──
def compute_ratios(accounts, keys, axis_map):
    """[07 compute_ratios] 형태자질 비율. 없는 키는 0회, 분모 0은 결측(None). 반환 (판정용, 보조용, 출현계정수)."""
    kinds = {k: denom_kind_of(k, axis_map) for k in keys}
    ratios, aux, presence = {}, {}, {k: 0 for k in keys}

    for uid in sorted(accounts):
        a = accounts[uid]
        feats = a.get("자질", {})
        denom_tok = a.get("토큰수_구두점제외", 0)

        # 이 계정의 축별 총 출현수. 축 내부 비율의 분모가 된다.
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
            # 보조값은 언제나 전체 토큰이 분모다. 토큰수가 0인 계정(01의 적격
            # 기준상 나올 일이 없다)에서만 결측이 된다.
            arow[k] = None if denom_tok == 0 else cnt / denom_tok
        ratios[uid] = row
        aux[uid] = arow
    return ratios, aux, presence


# ── [10_동질성검정.py ← 07_형태자질비교.py] compute_upos_ratios ──
def compute_upos_ratios(accounts, keys):
    """[07 compute_upos_ratios] 품사 비율. 분모는 토큰수_구두점제외."""
    ratios, presence = {}, {k: 0 for k in keys}
    for uid in sorted(accounts):
        a = accounts[uid]
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


# ── [10_동질성검정.py ← 08_R블록.py] coef_variation ──
def coef_variation(lengths, min_n=MIN_SENTENCES_CV):
    """[08 coef_variation] 문장 길이 변동계수 = 표본표준편차 ÷ 평균. 문장 5개 미만이거나 평균 0이면 결측."""
    n = len(lengths)
    if n < min_n:
        return None
    mean = sum(lengths) / n
    if mean <= 0:
        return None
    return statistics.stdev(lengths) / mean


# ── [10_동질성검정.py ← 08_R블록.py] compute_features ──
def compute_features(accounts):
    """[08 compute_features] R 자질 3종(문장당 토큰수, 구두점 비율, 문장 길이 변동계수). 분모 0은 결측."""
    out = {}
    for uid, a in accounts.items():
        tok = a["토큰수"]
        tok_np = a["토큰수_구두점제외"]
        n_sent = a["문장수"]
        lengths = a["문장길이"]

        row = {}
        # ① 문장당 토큰수: 분모는 문장수
        row["문장당_토큰수"] = (tok_np / n_sent) if n_sent > 0 else None
        # ② 구두점 비율: 분모는 전체 토큰수(구두점을 포함한 쪽이다)
        row["구두점_비율"] = ((tok - tok_np) / tok) if tok > 0 else None
        # ③ 문장 길이 변동계수: 문장 5개 미만은 결측
        row["문장길이_변동계수"] = coef_variation(lengths)
        out[uid] = row
    return out


# ── [10_동질성검정.py ← 09_산포검정.py(보관)] dense_vectors ──
def dense_vectors(uids, rates, words):
    """[옛 09 dense_vectors, 10 정본 경유] 계정마다 기능어 사용률 벡터. 없는 단어는 0.0."""
    return [[rates[u]["사용률"].get(w, 0.0) for w in words] for u in uids]


# ── [10_동질성검정.py ← 04_기능어측정.py] normalize_apostrophe ──
def normalize_apostrophe(s):
    """[04 normalize_apostrophe] 굽은 아포스트로피(U+2019)를 곧은 것(U+0027)으로 바꾼다."""
    return s.replace("’", "'")


# ── [10_동질성검정.py] percentile_column ──
def percentile_column(col):
    """[10] 자질 하나를 순위 백분위로. 동점 평균순위, (평균순위 - 1) ÷ (정의된 계정 수 - 1), 결측은 nan 유지. 라벨 안 씀."""
    col = np.asarray(col, dtype=float)
    out = np.full(col.shape, np.nan)
    ok = ~np.isnan(col)
    v = col[ok]
    n = v.size
    if n < 2:
        return out, n
    order = np.argsort(v, kind="mergesort")
    sv = v[order]
    ranks = np.empty(n)
    i = 0
    while i < n:
        j = i + 1
        while j < n and sv[j] == sv[i]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.0      # 순위 i+1 … j 의 평균
        i = j
    out[ok] = (ranks - 1.0) / (n - 1.0)
    return out, n


# ── [10_동질성검정.py] percentile_matrix ──
def percentile_matrix(X):
    """[10] 계정 × 자질 행렬을 열마다 백분위로. 열마다 정의된 계정 수도 돌려준다."""
    P = np.full(X.shape, np.nan)
    n_def = []
    for j in range(X.shape[1]):
        P[:, j], n = percentile_column(X[:, j])
        n_def.append(n)
    return P, n_def


# ── [10_동질성검정.py] nanmedian_cols ──
def nanmedian_cols(M):
    """[10] 열별 중앙값. 열 전체가 nan이면 nan."""
    out = np.full(M.shape[1], np.nan)
    for j in range(M.shape[1]):
        v = M[:, j]
        v = v[~np.isnan(v)]
        if v.size:
            out[j] = np.median(v)
    return out


# ── [10_동질성검정.py] center_groups (v1.2 결정 B2) ──
def center_groups(X, is_bot):
    """[10 v1.2 결정 B2] 자질마다 집단별 결측 제외 원값 중앙값을 그 집단 계정에서 뺀다. 정의된 값이 2개 미만인 집단은 빼지 않는다. 반환 (정렬 행렬, 봇 중앙값, 사람 중앙값, 봇 제외 표시, 사람 제외 표시)."""
    Xc = np.array(X, dtype=float)
    meds, skips = [], []
    for grp in (is_bot, ~is_bot):
        G = Xc[grp]
        few = (~np.isnan(G)).sum(axis=0) < 2
        m = nanmedian_cols(G)
        Xc[grp] = G - np.where(few, 0.0, m)[None, :]
        meds.append(np.where(few, np.nan, m))
        skips.append(few)
    return Xc, meds[0], meds[1], skips[0], skips[1]


# ── [10_동질성검정.py] centers ──
def centers(P, is_bot):
    """[10] 집단별 자질 중앙값. 반복 안에서는 가짜 라벨이다."""
    return nanmedian_cols(P[is_bot]), nanmedian_cols(P[~is_bot])


# ── [10_동질성검정.py] block_distances ──
def block_distances(P, is_bot, c_bot, c_hum):
    """[10] 자기 집단 중심까지 |백분위 - 중심|의 평균. 결측 자질은 뺀다. 사용 자질 수도 돌려준다."""
    C = np.where(is_bot[:, None], c_bot[None, :], c_hum[None, :])
    A = np.abs(P - C)
    used = (~np.isnan(A)).sum(axis=1)
    with np.errstate(invalid="ignore"):
        d = np.nansum(A, axis=1) / np.where(used > 0, used, np.nan)
    return d, used


# ── [10_동질성검정.py] ratio_of ──
def ratio_of(d_bot, d_hum):
    """[10] 비율 = 사람 거리 중앙값 ÷ 봇 거리 중앙값. 1보다 크면 봇이 더 좁다."""
    return float(np.median(d_hum)) / float(np.median(d_bot))


# ── [10_동질성검정.py] perm_ratios ──
def perm_ratios(d_bot, d_hum, swaps):
    """[10] 쌍 안 교환 순열. swaps[k, i]가 참이면 k번째 순열에서 쌍 i의 두 거리 값을 맞바꾼다. 중심은 다시 만들지 않는다."""
    b = np.where(swaps, d_hum[None, :], d_bot[None, :])
    h = np.where(swaps, d_bot[None, :], d_hum[None, :])
    return np.median(h, axis=1) / np.median(b, axis=1)


# ── [10_동질성검정.py] p_values ──
def p_values(obs, perm):
    """[10] 위쪽 단측 p = (순열 ≥ 관측 횟수 + 1) ÷ (순열 수 + 1). 양측 p는 |log| 기준. 상대 허용오차 1e-12."""
    perm = np.asarray(perm, dtype=float)
    ge = int(np.sum(perm >= obs * (1 - REL_TOL)))
    lo = abs(math.log(obs))
    ge2 = int(np.sum(np.abs(np.log(perm)) >= lo * (1 - REL_TOL)))
    n = perm.size
    return (ge + 1) / (n + 1), (ge2 + 1) / (n + 1), ge, ge2


# ── [10_동질성검정.py] exact_p ──
def exact_p(obs, all_ratios):
    """[10] 교환을 전부 늘어놓았을 때의 정확 p(+1 없음). 손 예제 전용."""
    r = np.asarray(all_ratios, dtype=float)
    lo = abs(math.log(obs))
    return (float(np.mean(r >= obs * (1 - REL_TOL))),
            float(np.mean(np.abs(np.log(r)) >= lo * (1 - REL_TOL))))


# ── [10_동질성검정.py] five ──
def five(v):
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    q1, q2, q3 = np.percentile(v, [25, 50, 75])
    return {"n": int(v.size), "최소": float(v.min()), "Q1": float(q1),
            "중앙": float(q2), "Q3": float(q3), "최대": float(v.max()),
            "평균": float(v.mean())}


# ── [09-1_분량통제.py] caliper_match ──
def caliper_match(bot_ids, human_ids, logd, caliper, seed):
    """[09-1 caliper_match] |log 분모 차| ≤ caliper 그리디 1:1. 봇을 random.Random(seed)로 섞고 사람 목록 앞쪽이 동점에서 이긴다. 반환 (쌍 [(봇, 사람, 거리)], 탈락 봇, 쓰인 사람 집합)."""
    rng = random.Random(seed)
    order = list(bot_ids)
    rng.shuffle(order)

    used = set()
    pairs = []
    unmatched_bots = []
    for b in order:
        lb = logd[b]
        best, best_gap = None, None
        for h in human_ids:
            if h in used:
                continue
            gap = abs(logd[h] - lb)
            if gap > caliper:
                continue
            if best_gap is None or gap < best_gap:
                best, best_gap = h, gap
        if best is None:
            unmatched_bots.append(b)
        else:
            used.add(best)
            pairs.append((b, best, best_gap))
    return pairs, unmatched_bots, used


# ════════════════════════════════════════════════════════════════════════
# [공통 도구]
# ════════════════════════════════════════════════════════════════════════
def line(title=""):
    print("─" * 74, flush=True)
    if title:
        print(f"  {title}", flush=True)
        print("─" * 74, flush=True)


def say(msg=""):
    print(msg, flush=True)


def label_marker(where):
    say(f"  [라벨 사용] {where}")


def stop(msg):
    """관문 실패. 본 계산에 들어가지 않고 JSON도 쓰지 않는다."""
    say()
    say(f"■ 중단 : {msg}")
    say("  관문을 통과하지 못했습니다. 산출 JSON을 쓰지 않고 끝냅니다.")
    sys.exit(1)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _np_default(o):
    """numpy 스칼라(np.bool_·np.float64 등)는 파이썬 값으로. 그 밖은 오류."""
    if isinstance(o, np.generic):
        return o.item()
    raise TypeError(f"JSON으로 쓸 수 없는 값: {type(o).__name__}")


def write_json(path, obj):
    """허용된 산출 경로에 바로 쓴다(다른 파일을 만들지 않는다)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, allow_nan=False, default=_np_default)
        f.flush()
        os.fsync(f.fileno())


def fnum(x):
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else x


def close(a, b, tol=HAND_TOL):
    if a is not None and math.isnan(float(a)):
        a = None
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= tol


def func_ast(src, name):
    """소스에서 함수 name의 AST를 docstring을 빼고 문자열로. 없으면 None. (13-0 방식)"""
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            body = n.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                n.body = body[1:]
            return ast.dump(n)
    return None


def module_consts(src, names):
    """소스 최상위의 단순 대입 상수를 literal_eval로 읽는다."""
    out = {}
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            if n.targets[0].id in names:
                try:
                    out[n.targets[0].id] = ast.literal_eval(n.value)
                except ValueError:
                    pass
    return out


def quart(v):
    """최소·Q1·중앙·Q3·최대·평균 (numpy 선형 보간 분위)."""
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if not v.size:
        return None
    q1, q2, q3 = np.percentile(v, [25, 50, 75])
    return {"n": int(v.size), "최소": float(v.min()), "Q1": float(q1), "중앙": float(q2),
            "Q3": float(q3), "최대": float(v.max()), "평균": float(v.mean())}


# ════════════════════════════════════════════════════════════════════════
# [이 파일이 더하는 계산]
# ════════════════════════════════════════════════════════════════════════
def p_lower(obs, perm):
    """
    아래쪽 단측 p = (순열비율 ≤ 관측비율 횟수 + 1) ÷ (순열 수 + 1)   (E6)
    10 p_values의 위쪽 비교(≥ obs × (1 - 1e-12))를 거울로 뒤집은 것이다.
    """
    perm = np.asarray(perm, dtype=float)
    le = int(np.sum(perm <= obs * (1 + REL_TOL)))
    return (le + 1) / (perm.size + 1), le


def exact_p_lower(obs, all_ratios):
    """교환을 전부 늘어놓았을 때의 정확 아래쪽 p(+1 없음). 손 예제 전용."""
    r = np.asarray(all_ratios, dtype=float)
    return float(np.mean(r <= obs * (1 + REL_TOL)))


def wilson(k, n, z=WILSON_Z):
    """Wilson 점수 구간. n = 0이면 (nan, nan)."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    z2 = z * z
    den = 1 + z2 / n
    mid = (p + z2 / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den
    return max(0.0, mid - half), min(1.0, mid + half)


def binom_tail_gt(kmax, n, p):
    """P(K > kmax), K ~ Binomial(n, p). 관문 자체의 오경보율 계산용."""
    return 1.0 - sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(kmax + 1))


def mad_cols(X):
    """열별 MAD = median(|x - median(x)|). 결측 제외, 보정 계수 없음 (E4)."""
    med = nanmedian_cols(X)
    return nanmedian_cols(np.abs(X - med[None, :]))


def shift_rows(X, rows_mask, shift):
    """rows_mask 행의 원값에 자질별 shift를 더한다. 0에도 더하고 nan은 nan으로 남는다."""
    Y = X.copy()
    Y[rows_mask] = Y[rows_mask] + shift[None, :]
    return Y


def build_features(accounts, ids, words, axis_map, feat_keys, upos_keys):
    """
    F·M·R 원값 행렬(라벨 없음). 행 순서 = ids. 계정마다 독립으로 계산되므로
    행을 뽑아 쓰는 것과 부분집합으로 다시 계산하는 것이 같은 값이다.
    F : 05 compute_rates(6자리 반올림) → dense_vectors, 없는 단어 0.0
    M : 07 compute_ratios(축 분류는 고정 axis_map) + compute_upos_ratios
    R : 08 compute_features (계정 사전에 문장길이 목록이 있어야 한다)
    10 build_blocks와 같은 조립이다. 관문 2가 10 정본 값 재현으로 확인한다.
    """
    sub = {u: accounts[u] for u in ids}
    rates, undefined = compute_rates(sub)
    if undefined:
        stop(f"F 분모 0 계정이 있습니다: {undefined[:5]}")
    XF = np.array(dense_vectors(ids, rates, words), dtype=float)
    mr, _, _ = compute_ratios(sub, feat_keys, axis_map)
    ur, _ = compute_upos_ratios(sub, upos_keys)
    XM = np.array([[np.nan if mr[u][k] is None else mr[u][k] for k in feat_keys]
                   + [np.nan if ur[u][k] is None else ur[u][k] for k in upos_keys]
                   for u in ids], dtype=float)
    rr = compute_features(sub)
    XR = np.array([[np.nan if rr[u][k] is None else rr[u][k] for k in RKEYS]
                   for u in ids], dtype=float)
    return {"F": XF, "M": XM, "R": XR}


def run_procedure(X, n, swaps, center=True):
    """
    10 절차 한 번. X = 블록별 원값 행렬, 행 = 봇 n개 다음 사람 n개(같은 i가 같은 쌍).
      (v1.2) 중심 정렬 → 백분위(쌍 표본 안) → 집단 중심 → 자기 중심 블록 거리 →
      비율 → 쌍 안 교환 순열
    손 예제·10 재현·본 반복이 모두 이 함수를 지난다. center=False는 관문 2의 v1.1
    정본 재현 전용이다(정렬을 건너뛰면 v1.1 규칙이다). 밑줄로 시작하는 키는 내부
    배열이라 JSON에 넣지 않는다.
    """
    is_bot = np.array([True] * n + [False] * n)
    out = {}
    for b in X:
        if center:
            Xc, _, _, sb, sh = center_groups(X[b], is_bot)
        else:
            Xc = X[b]
            sb = sh = np.zeros(X[b].shape[1], dtype=bool)
        skip = {"봇": int(sb.sum()), "사람": int(sh.sum())}          # E13
        P, n_def = percentile_matrix(Xc)
        cb, ch = centers(P, is_bot)
        d, used = block_distances(P, is_bot, cb, ch)
        d_bot, d_hum = d[:n], d[n:]
        few = int(sum(1 for k in n_def if k < 2))
        g = np.abs(cb - ch)
        g = g[~np.isnan(g)]
        gap = float(g.mean()) if g.size else float("nan")
        if np.isnan(d).any():
            out[b] = {"무효": "nan 거리", "정의2미만_자질": few, "정렬제외": skip}
            continue
        if not np.median(d_bot) > 0:
            out[b] = {"무효": "봇 거리 중앙값 0", "정의2미만_자질": few, "정렬제외": skip}
            continue
        r = ratio_of(d_bot, d_hum)
        pr = perm_ratios(d_bot, d_hum, swaps)
        p1, p2, ge, ge2 = p_values(r, pr)
        pl, le = p_lower(r, pr)
        out[b] = {"무효": None, "비율": r, "p_위": p1, "p_아래": pl, "p_양측": p2,
                  "위_횟수": ge, "아래_횟수": le, "양측_횟수": ge2,
                  "봇거리_중앙": float(np.median(d_bot)), "사람거리_중앙": float(np.median(d_hum)),
                  "중심차_평균": gap, "정의2미만_자질": few, "정렬제외": skip,
                  "_Xc": Xc, "_P": P, "_c": (cb, ch), "_d": d, "_used": used, "_pr": pr}
    return out


def invariance(fullA, fullB):
    """
    이동 불변 관문(D, E12). 같은 반복의 A와 B를 블록마다 대조한다.
    비율 차 ≤ 1e-9이고 p 셋(위·아래·양측)이 같아야 통과다. 위반의 원인을 보이려고
    정렬값 최대차와 백분위가 달라진 자질 수를 함께 적는다. 정렬값 차가 부동소수점
    크기(≤ 1e-12)이고 백분위가 달라진 자질이 있으면 "동점 변화로 설명됨"이다.
    """
    out = {}
    for b in fullA:
        a, c = fullA[b], fullB[b]
        if a["무효"] or c["무효"]:
            out[b] = {"통과": a["무효"] == c["무효"], "무효": [a["무효"], c["무효"]]}
            continue
        gap = np.abs(a["_Xc"] - c["_Xc"])
        gap = gap[~np.isnan(gap)]
        gmax = float(gap.max()) if gap.size else 0.0
        pa, pc = a["_P"], c["_P"]
        eq = (pa == pc) | (np.isnan(pa) & np.isnan(pc))
        ncol = int((~eq.all(axis=0)).sum())
        dr = abs(a["비율"] - c["비율"])
        same_p = a["p_위"] == c["p_위"] and a["p_아래"] == c["p_아래"] and a["p_양측"] == c["p_양측"]
        ok = bool(dr <= INVAR_TOL and same_p)
        out[b] = {"비율차": dr, "p같음": bool(same_p), "정렬값_최대차": gmax,
                  "결측위치_같음": bool(np.array_equal(np.isnan(a["_Xc"]), np.isnan(c["_Xc"]))),
                  "백분위다른_자질수": ncol, "통과": ok,
                  "동점변화로_설명됨": None if ok else bool(gmax <= 1e-12 and ncol > 0)}
    return out


def public(res):
    """run_procedure 결과에서 내부 배열을 뺀다."""
    return {b: {k: v for k, v in r.items() if not k.startswith("_")} for b, r in res.items()}


# ════════════════════════════════════════════════════════════════════════
# [관문 1] 함수 승계 · 손 예제
# ════════════════════════════════════════════════════════════════════════
def gate_copies():
    me = open(os.path.abspath(__file__), encoding="utf-8").read()
    s10 = open(PY10, encoding="utf-8").read()
    s091 = open(PY091, encoding="utf-8").read()
    rows = []
    for name in FROM_10:
        a, b = func_ast(me, name), func_ast(s10, name)
        rows.append({"함수": name, "대상": "10_동질성검정.py", "같음": a is not None and a == b})
    for name in FROM_091:
        a, b = func_ast(me, name), func_ast(s091, name)
        rows.append({"함수": name, "대상": "09-1_분량통제.py", "같음": a is not None and a == b})
    cache = {}
    for name, path in ORIGINAL_SOURCES.items():
        if path not in cache:
            cache[path] = open(path, encoding="utf-8").read()
        a, b = func_ast(me, name), func_ast(cache[path], name)
        rows.append({"함수": name, "대상": os.path.relpath(path, ROOT), "같음": a is not None and a == b})
    for r in rows:
        say(f"      {r['함수']:<22} = {os.path.basename(r['대상']):<22} {'같음' if r['같음'] else '다름'}")

    # 함수 밖 상수 (함수가 전역으로 읽는 값)
    names10 = ["RATE_DIGITS", "DENOM_AXIS", "DENOM_TOKEN", "MIN_SENTENCES_CV", "RKEYS",
               "BLOCKS", "REL_TOL", "SEED", "N_PERM", "ALPHA", "EXPECT_ACCOUNTS", "EXPECT_WORDS",
               "EXPECT_HASH", "EXPECT_PAIRS", "EXPECT_M_FEAT", "EXPECT_M_UPOS"]
    c10 = module_consts(s10, names10)
    mine = {k: globals()[k] for k in names10 if k != "N_PERM"}
    mine["N_PERM"] = N_PERM_10
    const_rows = [{"상수": k, "10": c10.get(k), "이 파일": mine[k], "같음": c10.get(k) == mine[k]}
                  for k in names10]
    c091 = module_consts(s091, ["CALIPER", "SEED"])
    const_rows.append({"상수": "CALIPER", "09-1": c091.get("CALIPER"), "이 파일": CALIPER,
                       "같음": c091.get("CALIPER") == CALIPER})
    const_rows.append({"상수": "SEED_091", "09-1": c091.get("SEED"), "이 파일": SEED_091,
                       "같음": c091.get("SEED") == SEED_091})
    bad = [r["상수"] for r in const_rows if not r["같음"]]
    say(f"      앞 단계 상수 {len(const_rows)}개 대조  {'같음' if not bad else '다름: ' + ', '.join(bad)}")
    dash = [hex(c) for c in (0x2014, 0x2013) if chr(c) in me]
    say(f"      이 파일의 줄표·반각 대시  {'없음' if not dash else '있음'}")
    ok = all(r["같음"] for r in rows) and not bad and not dash
    return {"함수": rows, "상수": const_rows, "줄표없음": not dash}, ok


def gate_hand():
    """10 손 예제를 본 계산과 같은 run_procedure로 돌린다."""
    feats = ["a", "b", "c"]
    X = np.array([[np.nan if HAND_VALUES[f][u] is None else HAND_VALUES[f][u]
                   for f in feats] for u in HAND_IDS], dtype=float)
    keys = list(HAND_SWAPS)
    swaps = np.array(keys, dtype=bool)
    res = run_procedure({"H": X}, 3, swaps)["H"]
    fails = []
    Z = res["_Xc"]
    for i, u in enumerate(HAND_IDS):
        for j, f in enumerate(feats):
            if not close(Z[i, j], HAND_CENTERED[f][u]):
                fails.append(f"정렬 {u}.{f}: {Z[i, j]} ≠ {HAND_CENTERED[f][u]}")
    if res["정렬제외"] != {"봇": 0, "사람": 0}:
        fails.append(f"정렬 제외 {res['정렬제외']} (없어야 함)")
    P = res["_P"]
    for i, u in enumerate(HAND_IDS):
        for j, f in enumerate(feats):
            if not close(P[i, j], HAND_PCT[f][u]):
                fails.append(f"백분위 {u}.{f}: {P[i, j]} ≠ {HAND_PCT[f][u]}")
    cb, ch = res["_c"]
    for j, f in enumerate(feats):
        if not close(cb[j], HAND_CENTER_BOT[f]):
            fails.append(f"봇 중심 {f}: {cb[j]}")
        if not close(ch[j], HAND_CENTER_HUMAN[f]):
            fails.append(f"사람 중심 {f}: {ch[j]}")
    d = res["_d"]
    for i, u in enumerate(HAND_IDS):
        if not close(d[i], HAND_DIST[u]):
            fails.append(f"거리 {u}: {d[i]} ≠ {HAND_DIST[u]}")
    if list(res["_used"]) != [3, 3, 2, 3, 3, 3]:
        fails.append(f"사용 자질 수 {list(res['_used'])}")
    if not close(res["비율"], HAND_RATIO):
        fails.append(f"관측 비율 {res['비율']} ≠ 4/3")
    got = res["_pr"]
    for k, g in zip(keys, got):
        if not close(g, HAND_SWAPS[k]):
            fails.append(f"교환 {k}: {g} ≠ {HAND_SWAPS[k]}")
    e1, e2 = exact_p(res["비율"], got)
    el = exact_p_lower(res["비율"], got)
    for nm, a, b in (("정확 위쪽", e1, HAND_EXACT_P1), ("정확 양측", e2, HAND_EXACT_P2),
                     ("정확 아래쪽", el, HAND_EXACT_PLOW),
                     ("공식 위쪽", res["p_위"], HAND_FORMULA_P1),
                     ("공식 양측", res["p_양측"], HAND_FORMULA_P2),
                     ("공식 아래쪽", res["p_아래"], HAND_FORMULA_PLOW)):
        if not close(a, b):
            fails.append(f"{nm} p {a} ≠ {b}")
    say(f"      정렬 18칸 · 백분위 18칸 · 중심 6 · 거리 6 · 비율 4/3 · 교환 8가지  "
        f"{'통과' if not fails else '실패'}")
    say(f"      p 정확: 위 {e1:.4f}(2/8) · 아래 {el:.4f}(8/8) · 양측 {e2:.4f}(4/8)")
    say(f"      p 공식: 위 {res['p_위']:.4f}(3/9) · 아래 {res['p_아래']:.4f}(9/9) · "
        f"양측 {res['p_양측']:.4f}(5/9)")

    rng = np.random.default_rng(SEED)
    mc = run_procedure({"H": X}, 3, rng.random((N_PERM_10, 3)) < 0.5)["H"]
    n0 = len(fails)
    if (abs(mc["p_위"] - HAND_EXACT_P1) > HAND_MC_TOL or abs(mc["p_양측"] - HAND_EXACT_P2) > HAND_MC_TOL
            or abs(mc["p_아래"] - HAND_EXACT_PLOW) > HAND_MC_TOL):
        fails.append("무작위 교환 10,000회 p가 정확 p에서 허용차를 넘음")
    say(f"      무작위 교환 10,000회: 위 {mc['p_위']:.4f} · 아래 {mc['p_아래']:.4f} · "
        f"양측 {mc['p_양측']:.4f} (허용차 ±{HAND_MC_TOL})  {'통과' if len(fails) == n0 else '실패'}")
    return {"교환8가지": [{"교환": "".join(map(str, k)), "기대": HAND_SWAPS[k], "계산": float(g)}
                      for k, g in zip(keys, got)],
            "정확p": {"위": e1, "아래": el, "양측": e2},
            "공식p": {"위": res["p_위"], "아래": res["p_아래"], "양측": res["p_양측"]},
            "무작위10000_p": {"위": mc["p_위"], "아래": mc["p_아래"], "양측": mc["p_양측"]},
            "실패": fails, "통과": not fails}, not fails


def gate_match_hand():
    logd = {u: math.log(v) for u, v in MATCH_BOT_DENOM.items()}
    logd.update({u: math.log(v) for u, v in MATCH_HUM_DENOM.items()})
    pairs, unmatched, used = caliper_match(sorted(MATCH_BOT_DENOM), sorted(MATCH_HUM_DENOM),
                                           logd, CALIPER, SEED)
    got = {b: h for b, h, _ in pairs}
    checks = {
        "쌍 2": len(pairs) == 2,
        "b2 짝 h5(최근접)": got.get("b2") == "h5",
        "h2 미사용(경계 0.1054 밖)": "h2" not in used,
        "h1 한 번만": sum(1 for _, h, _ in pairs if h == "h1") == 1,
        "탈락 봇 1": len(unmatched) == 1,
        "모든 쌍 캘리퍼 안": all(g <= CALIPER + HAND_TOL for _, _, g in pairs),
    }
    ok = all(checks.values())
    say(f"      매칭 손 예제(09-1 인공 8계정): 쌍 {[(b, h) for b, h, _ in pairs]} · 탈락 {unmatched}  "
        f"{'통과' if ok else '실패'}")
    return {"쌍": [[b, h, g] for b, h, g in pairs], "탈락": unmatched, "검사": checks, "통과": ok}, ok


def gate_mad_hand():
    X = np.array([[np.nan if v is None else v for v in row] for row in MAD_X], dtype=float)
    mad = mad_cols(X)
    mask = np.zeros(X.shape[0], dtype=bool)
    mask[MAD_BOT_ROWS] = True
    Y = shift_rows(X, mask, mad)
    ok = (all(close(a, b) for a, b in zip(mad, MAD_EXPECT))
          and all(close(a, b) for a, b in zip(Y[0], MAD_SHIFTED_ROW0))
          and all(close(a, b) for a, b in zip(Y[4], MAD_SHIFTED_ROW4))
          and np.array_equal(Y[1:4], X[1:4]))
    say(f"      MAD 손 예제: MAD {list(map(float, mad))} (기대 {MAD_EXPECT}) · 행0 {list(map(float, Y[0]))} · "
        f"행4 {[fnum(v) for v in Y[4]]}  {'통과' if ok else '실패'}")
    return {"MAD": [fnum(v) for v in mad], "행0": [fnum(v) for v in Y[0]],
            "행4": [fnum(v) for v in Y[4]], "통과": ok}, ok


def gate_wilson():
    from scipy.stats import binomtest          # 대조에만 쓴다 (E9)
    import scipy
    rows = []
    n = 200                                    # 대조용 고정 n (선언된 반복 수와 같은 값)
    for k in (0, 5, 10, 11, 12, 20, 200):
        lo, hi = wilson(k, n)
        ci = binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson")
        rows.append({"k": k, "n": n, "이파일": [lo, hi], "scipy": [float(ci.low), float(ci.high)],
                     "같음": abs(lo - ci.low) <= 1e-12 and abs(hi - ci.high) <= 1e-12})
    k, n, elo, ehi = WILSON_HAND
    lo, hi = wilson(k, n)
    hand_ok = abs(lo - elo) <= WILSON_HAND_TOL and abs(hi - ehi) <= WILSON_HAND_TOL
    ok = hand_ok and all(r["같음"] for r in rows)
    say(f"      Wilson: 손계산 k=10/200 [{lo:.6f}, {hi:.6f}] (기대 [{elo}, {ehi}]) · "
        f"scipy {scipy.__version__} 대조 {sum(r['같음'] for r in rows)}/{len(rows)}  {'통과' if ok else '실패'}")
    return {"손계산": {"k": k, "n": n, "기대": [elo, ehi], "계산": [lo, hi], "통과": hand_ok},
            "scipy대조": rows, "scipy": scipy.__version__, "통과": ok}, ok


# ════════════════════════════════════════════════════════════════════════
# [관문 2] 10 정본 재현 · 09-1 매칭 재현
# ════════════════════════════════════════════════════════════════════════
def load_words():
    raw = json.load(open(FUNCWORDS_JSON, encoding="utf-8"))["기능어"]
    words = sorted({normalize_apostrophe(w) for w in raw})
    h = hashlib.sha256("\n".join(words).encode("utf-8")).hexdigest()[:16]
    return words, h


def gate_repro10(words):
    d04 = json.load(open(MEASURE_JSON, encoding="utf-8"))
    d041 = json.load(open(REPARSE_JSON, encoding="utf-8"))
    fmr = json.load(open(FMR_JSON, encoding="utf-8"))
    d07 = json.load(open(FEATURE_JSON, encoding="utf-8"))
    j10 = json.load(open(J10_V11, encoding="utf-8"))      # 보관된 v1.1 정본
    acc, acc1 = d04["계정"], d041["계정"]
    pairs_raw = fmr["설정"]["matching"]["pairs"]
    pairs = [(b, h) for b, h, _ in pairs_raw]
    fmr_axis = fmr["설정"]["axis_map_fixed_to_baseline"]

    chk = {}
    chk["04_계정수_1869"] = len(acc) == EXPECT_ACCOUNTS
    chk["04-1_계정집합_=_04"] = set(acc1) == set(acc)
    chk["매칭_512쌍"] = len(pairs) == EXPECT_PAIRS
    axis_map = build_axis_map(acc)
    feat_keys = sorted({k for a in acc.values() for k in a.get("자질", {})})
    upos_keys = sorted({k for a in acc.values() for k in a.get("UPOS", {})})
    chk["축분류_=_FMR고정값"] = axis_map == fmr_axis
    chk["형태자질_58_=_07"] = len(feat_keys) == EXPECT_M_FEAT and feat_keys == sorted(d07["형태자질"])
    chk["품사_17_=_07"] = len(upos_keys) == EXPECT_M_UPOS and upos_keys == sorted(d07["UPOS"])
    del d07

    label_marker("관문 2 : 10 v1.1 정본(보관)의 매칭 쌍(봇·사람 구분)으로 1,024계정을 세운다 (중심 정렬 끔)")
    ids = [b for b, _ in pairs] + [h for _, h in pairs]
    merged = {u: {**acc[u], "문장길이": acc1[u]["문장길이"]} for u in ids}
    X = build_features(merged, ids, words, axis_map, feat_keys, upos_keys)
    t0 = time.time()
    swaps = np.random.default_rng(SEED).random((N_PERM_10, len(pairs))) < 0.5
    res = run_procedure(X, len(pairs), swaps, center=False)     # v1.1 규칙으로 재현
    sec = time.time() - t0

    rows = {}
    for b in BLOCKS:
        r, ref = res[b], j10["블록별"][b]
        if r.get("무효"):
            chk[f"{b}_유효"] = False
            continue
        n = len(pairs)
        d_bot, d_hum = r["_d"][:n], r["_d"][n:]
        ref_bot = np.array([ref["계정별_거리"]["봇"][u] for u in ids[:n]])
        ref_hum = np.array([ref["계정별_거리"]["사람"][u] for u in ids[n:]])
        dmax = float(max(np.max(np.abs(d_bot - ref_bot)), np.max(np.abs(d_hum - ref_hum))))
        keys = ({"F": words, "M": feat_keys + upos_keys, "R": RKEYS})[b]
        cb, ch = r["_c"]
        cref_b = np.array([np.nan if ref["중심"]["봇"][k] is None else ref["중심"]["봇"][k] for k in keys])
        cref_h = np.array([np.nan if ref["중심"]["사람"][k] is None else ref["중심"]["사람"][k] for k in keys])
        cmax = float(np.nanmax(np.abs(np.concatenate([cb - cref_b, ch - cref_h]))))
        cnan = bool(np.array_equal(np.isnan(cb), np.isnan(cref_b)) and np.array_equal(np.isnan(ch), np.isnan(cref_h)))
        pr = r["_pr"]
        qs = np.percentile(pr, [2.5, 50, 97.5])
        dist_now = {"평균": float(pr.mean()), "표준편차": float(pr.std()), "최소": float(pr.min()),
                    "Q2.5": float(qs[0]), "중앙": float(qs[1]), "Q97.5": float(qs[2]), "최대": float(pr.max())}
        dist_max = max(abs(dist_now[k] - ref["순열분포"][k]) for k in dist_now)
        ratio_diff = abs(r["비율"] - ref["비율"])
        ok_b = (ratio_diff <= REPRO_TOL * ref["비율"] and dmax <= REPRO_TOL and cmax <= REPRO_TOL and cnan
                and r["p_위"] == ref["p_단측"] and r["p_양측"] == ref["p_양측"]
                and r["위_횟수"] == ref["관측이상_횟수"] and r["양측_횟수"] == ref["양측_횟수"]
                and dist_max <= REPRO_TOL and len(keys) == ref["자질수"])
        chk[f"{b}_10재현"] = ok_b
        rows[b] = {"비율_재현": r["비율"], "비율_정본": ref["비율"], "비율_차": ratio_diff,
                   "p_위_재현": r["p_위"], "p_단측_정본": ref["p_단측"],
                   "p_양측_재현": r["p_양측"], "p_양측_정본": ref["p_양측"],
                   "p_아래_재현": r["p_아래"],
                   "계정별거리_최대차": dmax, "중심_최대차": cmax, "중심_결측위치_같음": cnan,
                   "순열분포요약_최대차": dist_max, "자질수": len(keys), "통과": ok_b}
        say(f"      {b}  비율 재현 {r['비율']:.6f} · v1.1 정본 {ref['비율']:.6f} · 차 {ratio_diff:.1e} · "
            f"거리 최대차 {dmax:.1e} · 중심 최대차 {cmax:.1e} · p 위 {r['p_위']:.6f}(정본 {ref['p_단측']:.6f}) · "
            f"순열 요약 최대차 {dist_max:.1e}  {'통과' if ok_b else '실패'}")
    say(f"      재현 계산 {sec:.1f}초 (순열 {N_PERM_10:,}회 × 3블록)")
    for k in ("04_계정수_1869", "04-1_계정집합_=_04", "매칭_512쌍", "축분류_=_FMR고정값",
              "형태자질_58_=_07", "품사_17_=_07"):
        say(f"      {k:<26} {'통과' if chk[k] else '실패'}")
    out = {"검사": chk, "블록별": rows, "재현초": sec}
    return out, all(chk.values()), acc, pairs_raw, axis_map, feat_keys, upos_keys


def gate_repro091(acc, pairs_raw):
    """09-1 매칭을 같은 caliper_match·시드 20260827로 다시 돌려 512쌍 목록이 같은지 본다."""
    label_marker("관문 2 : 09-1 매칭 재현에 01 라벨로 봇·사람 무더기를 나눈다")
    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    labels = data.get("라벨") or {}
    del data
    rates, _ = compute_rates(acc)
    cand_bot = [u for u in sorted(rates) if labels.get(u) == "bot" and rates[u]["분모"] > 0]
    cand_hum = [u for u in sorted(rates) if labels.get(u) == "human" and rates[u]["분모"] > 0]
    logd = {u: math.log(rates[u]["분모"]) for u in cand_bot + cand_hum}
    t0 = time.time()
    pairs, unmatched, _ = caliper_match(cand_bot, cand_hum, logd, CALIPER, SEED_091)
    sec = time.time() - t0
    q = json.load(open(J091, encoding="utf-8"))
    ref = q["매칭"]["쌍목록"]
    same_list = [[b, h] for b, h, _ in pairs] == ref
    same_fmr = [[b, h] for b, h, _ in pairs] == [[b, h] for b, h, _ in pairs_raw]
    gap_max = max(abs(g - gr) for (_, _, g), (_, _, gr) in zip(pairs, pairs_raw)) if same_fmr else None
    ok = same_list and same_fmr and gap_max is not None and gap_max <= REPRO_TOL
    say(f"      09-1 매칭 재현: 후보 봇 {len(cand_bot)} · 사람 {len(cand_hum)} → {len(pairs)}쌍 · "
        f"탈락 봇 {len(unmatched)} · 09-1 쌍목록과 순서까지 같음 {same_list} · FMR 쌍과 같음 {same_fmr} · "
        f"거리 최대차 {gap_max} · {sec:.1f}초  {'통과' if ok else '실패'}")
    return {"후보봇": len(cand_bot), "후보사람": len(cand_hum), "쌍수": len(pairs),
            "탈락봇": len(unmatched), "09-1쌍목록_같음": same_list, "FMR쌍_같음": same_fmr,
            "거리_최대차": gap_max, "초": sec, "통과": ok}, ok


# ════════════════════════════════════════════════════════════════════════
# [관문 3] 13-0 산출 · 사람 풀 640
# ════════════════════════════════════════════════════════════════════════
def gate_pool(words, axis_map, feat_keys, upos_keys):
    if not os.path.exists(ACCDICT_JSON):
        stop(f"13-0 계정사전이 없습니다: {ACCDICT_JSON}")
    d = json.load(open(ACCDICT_JSON, encoding="utf-8"))
    st = d.get("설정", {})
    accs = d["계정"]
    sp = json.load(open(SPLIT_JSON, encoding="utf-8"))["분할"]
    roles_sp = {r["uid"]: r["역할"] for r in sp["사람"]["역할표"]}
    chk = {}
    chk["13-0_관문통과"] = st.get("관문통과") is True
    chk["13-0_smoke_아님"] = st.get("smoke") is False

    label_marker("관문 3 : 사람 풀 = 역할 표a인 사람 (역할은 라벨로 정의된 사람 풀의 분할)")
    pool_sp = sorted(u for u, r in roles_sp.items() if "표a" in r)
    test_sp = sorted(u for u, r in roles_sp.items() if "시험" in r)
    pool_13 = sorted(u for u, a in accs.items() if a.get("집단") == "사람" and "표a" in (a.get("역할") or []))
    chk["분할_표a_640"] = len(pool_sp) == EXPECT_POOL
    chk["분할_시험_234"] = len(test_sp) == EXPECT_TEST
    chk["13-0_표a_=_분할_표a"] = pool_13 == pool_sp
    chk["표a_∩_시험_=_∅"] = not (set(pool_13) & set(test_sp))
    chk["표a_역할목록_=_분할"] = all(accs[u].get("역할") == roles_sp.get(u) for u in pool_13)
    chk["표a_봉인_false"] = all(accs[u].get("봉인") is False for u in pool_13)
    chk["표a_라벨_human"] = all(accs[u].get("라벨") == "human" for u in pool_13)

    rel_ok, fw_ok, den_ok, doc_ok = True, True, True, True
    wset = set(words)
    extra_feat, extra_upos = set(), set()
    for u in pool_13:
        a = accs[u]
        L = a["문장길이"]
        if (len(L) != a["문장수"] or sum(L) != a["토큰수_구두점제외"]
                or a["구두점토큰수"] != a["토큰수"] - a["토큰수_구두점제외"]
                or a["UPOS"].get("PUNCT", 0) != a["구두점토큰수"]):
            rel_ok = False
        if set(a["기능어"]) - wset:
            fw_ok = False
        if a["토큰수_구두점제외"] <= 0:
            den_ok = False
        if a["문서수"] < 10:
            doc_ok = False
        extra_feat |= set(a["자질"]) - set(feat_keys)
        extra_upos |= set(a["UPOS"]) - set(upos_keys)
    chk["내부관계(문장길이·구두점)"] = rel_ok
    chk["기능어키_⊂_172종"] = fw_ok
    chk["분모_>_0"] = den_ok
    chk["문서수_≥_10"] = doc_ok
    for k, v in chk.items():
        say(f"      {k:<28} {'통과' if v else '실패'}")

    # 기록만 (E1): 13-0에서 유도한 축 분류·키가 04 유도 값과 같은가
    ax_all13 = build_axis_map(accs)
    ax_pool = build_axis_map({u: accs[u] for u in pool_13})
    note = {
        "640에만_있는_형태자질키(무시됨)": sorted(extra_feat),
        "640에만_있는_품사키(무시됨)": sorted(extra_upos),
        "축분류_13-0전체_=_04고정": ax_all13 == axis_map,
        "축분류_640_=_04고정": ax_pool == axis_map,
        "축분류_차이_640": {ax: {"04": axis_map.get(ax), "640": ax_pool.get(ax)}
                        for ax in sorted(set(axis_map) | set(ax_pool)) if axis_map.get(ax) != ax_pool.get(ax)},
    }
    say(f"      (기록) 640에만 있는 형태자질 키 {len(extra_feat)} · 품사 키 {len(extra_upos)} · "
        f"축 분류 13-0 전체 = 04 고정 {note['축분류_13-0전체_=_04고정']} · 640 = 04 고정 {note['축분류_640_=_04고정']}")
    info = {"13-0_설정_관문통과": st.get("관문통과"), "13-0_smoke": st.get("smoke"),
            "13-0_계정수": len(accs), "표a": len(pool_13), "시험": len(test_sp)}
    sub = {u: accs[u] for u in pool_13}
    del d, accs
    return {"검사": chk, "기록": note, "정보": info}, all(chk.values()), sub, pool_13


# ════════════════════════════════════════════════════════════════════════
# [요약·판정]
# ════════════════════════════════════════════════════════════════════════
def summarize(reps, sc, b):
    rows = [x[sc][b] for x in reps]
    valid = [r for r in rows if not r["무효"]]
    n = len(valid)
    out = {"유효반복": n, "무효반복": len(rows) - n,
           "무효사유": sorted({r["무효"] for r in rows if r["무효"]})}
    for key, name in (("p_위", "위쪽(비율>1)"), ("p_아래", "아래쪽(비율<1)"), ("p_양측", "양측")):
        k = sum(1 for r in valid if r[key] < ALPHA)
        lo, hi = wilson(k, n)
        cell = {"거짓유의수": k, "율": k / n if n else None, "Wilson95": [lo, hi]}
        if key != "p_양측":
            cell["통과"] = bool(n and hi <= GATE_UPPER)
        hist, _ = np.histogram([r[key] for r in valid], bins=np.linspace(0, 1, 11))
        cell["p_십분위도수"] = [int(c) for c in hist]
        out[name] = cell
    out["비율분포"] = quart([r["비율"] for r in valid])
    out["봇거리중앙_분포"] = quart([r["봇거리_중앙"] for r in valid])
    out["사람거리중앙_분포"] = quart([r["사람거리_중앙"] for r in valid])
    out["중심차평균_분포"] = quart([r["중심차_평균"] for r in valid])
    out["정의2미만_자질_합"] = int(sum(r["정의2미만_자질"] for r in rows))
    out["정렬제외_합"] = {g: int(sum(r["정렬제외"][g] for r in rows)) for g in ("봇", "사람")}
    return out


def gate_false_alarm(n_rep):
    """관문 자체의 오경보율: 참 거짓 유의율이 a일 때 한 칸이 상한 > 0.10으로 걸릴 확률."""
    kmax = max((k for k in range(n_rep + 1) if wilson(k, n_rep)[1] <= GATE_UPPER), default=-1)
    rates = {}
    for a in (0.049, 0.05, 0.06, 0.07):
        rates[str(a)] = binom_tail_gt(kmax, n_rep, a)
    return {"통과_최대_거짓유의수": kmax, "n": n_rep,
            "한칸_불통과확률(참율별)": rates,
            "비고": "999회 순열에서 p < 0.05는 관측이상 횟수 ≤ 48과 같아 명목 크기는 0.049다. "
                  "6칸이 서로 독립이라면 참율 0.05에서 6칸 모두 통과할 확률은 (1 - 한칸값)^6이다. "
                  "실제로는 A·B가 같은 반분을 쓰고 블록이 서로 상관해 독립이 아니다."}


# ════════════════════════════════════════════════════════════════════════
# [본 절차]
# ════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="10-1 귀무 오류율 관문 (v1.2 규칙)")
    ap.add_argument("--reps", type=int, default=N_REP,
                    help=f"반복 수 (기본 {N_REP}, 선언된 판정은 {N_REP}회 실행에 건다)")
    n_rep = ap.parse_args().reps
    if n_rep < 1:
        stop("--reps는 1 이상이어야 합니다.")
    out_json = OUT_JSON if n_rep == N_REP else os.path.join(HERE, f"10-1_귀무오류율_{n_rep}회.json")
    declared = n_rep == N_REP

    t_start = time.time()
    run_at = datetime.now().astimezone().isoformat(timespec="seconds")
    say("=" * 74)
    say(f"10-1 귀무 오류율 관문 v1.2 규칙 (10 절차를 사람 640의 무작위 반분에 {n_rep}회 × 2 시나리오)")
    say("=" * 74)
    say(f"  실행 {run_at} · python {platform.python_version()} · numpy {np.__version__} · "
        f"sys.flags.optimize {sys.flags.optimize}")
    say(f"  시드 {SEED} + r · 반복 {n_rep} · 순열 {N_PERM}회 · α {ALPHA} · 캘리퍼 {CALIPER} · "
        f"이동 MAD × {SHIFT_MAD_MULT} · 판정 문턱 Wilson 상한 ≤ {GATE_UPPER}")
    say(f"  규칙 v1.2 (10 결정 B2 중심 정렬) · 이동 불변 허용오차 {INVAR_TOL} · "
        f"{'선언 판정 실행' if declared else f'참고 실행 (선언 판정은 {N_REP}회)'} · 산출 {os.path.basename(out_json)}")
    script_sha = sha256_file(os.path.abspath(__file__))
    say(f"  스크립트 sha256 {script_sha}")

    say("\n[1/7] 관문 1 : 함수 승계 · 손 예제")
    copy_res, copy_ok = gate_copies()
    hand_res, hand_ok = gate_hand()
    match_res, match_ok = gate_match_hand()
    mad_res, mad_ok = gate_mad_hand()
    wil_res, wil_ok = gate_wilson()
    if not copy_ok:
        stop("복사한 함수나 상수가 원본과 다릅니다.")
    if not hand_ok:
        for f in hand_res["실패"]:
            say(f"      × {f}")
        stop("손 예제가 손계산과 맞지 않습니다.")
    if not (match_ok and mad_ok and wil_ok):
        stop("매칭·MAD·Wilson 손 예제 가운데 실패가 있습니다.")
    say("  관문 1 통과.")

    say("\n[2/7] 관문 2 : 10 v1.1 정본(보관) 재현, 중심 정렬 끔(04·04-1·02·07·FMR 쌍) · 09-1 매칭 재현")
    words, fw_hash = load_words()
    w_ok = len(words) == EXPECT_WORDS and fw_hash == EXPECT_HASH
    say(f"      기능어 {len(words)}종 · 해시 {fw_hash}  {'통과' if w_ok else '실패'}")
    if not w_ok:
        stop("기능어 목록 해시가 다릅니다.")
    r10, r10_ok, acc04, pairs_raw, axis_map, feat_keys, upos_keys = gate_repro10(words)
    if not r10_ok:
        stop("10 v1.1 정본 결과를 재현하지 못했습니다: "
             + ", ".join(k for k, v in r10["검사"].items() if not v))
    r091, r091_ok = gate_repro091(acc04, pairs_raw)
    del acc04
    if not r091_ok:
        stop("09-1 매칭 512쌍을 재현하지 못했습니다.")
    say("  관문 2 통과. 정렬을 끈 이 파일의 함수 조립이 10 v1.1 정본·09-1과 같은 값을 낸다.")

    say("\n[3/7] 관문 3 : 13-0 계정사전과 사람 풀 640")
    acc_sha = sha256_file(ACCDICT_JSON) if os.path.exists(ACCDICT_JSON) else None
    say(f"      13-0 계정사전 sha256 {acc_sha}")
    pool_res, pool_ok, acc, uids = gate_pool(words, axis_map, feat_keys, upos_keys)
    if not pool_ok:
        stop("사람 풀 확인 실패: " + ", ".join(k for k, v in pool_res["검사"].items() if not v))
    say(f"  관문 3 통과. 사람 풀 {len(uids)}명.")

    say("\n[4/7] 자질 원값 (사람 640, 라벨 없음) · 자질별 MAD")
    X640 = build_features(acc, uids, words, axis_map, feat_keys, upos_keys)
    keys = {"F": list(words), "M": feat_keys + upos_keys, "R": list(RKEYS)}
    mad, feat_info = {}, {}
    for b in BLOCKS:
        mad[b] = mad_cols(X640[b])
        miss = np.isnan(X640[b])
        zero = int(np.sum(mad[b] == 0))
        feat_info[b] = {"자질수": len(keys[b]), "결측칸": int(miss.sum()),
                        "1개이상_결측계정": int(miss.any(axis=1).sum()),
                        "MAD0_자질수": zero,
                        "MAD": {k: fnum(v) for k, v in zip(keys[b], mad[b])}}
        say(f"      {b}  자질 {len(keys[b])} · 결측 칸 {feat_info[b]['결측칸']:,} · "
            f"MAD 0인 자질 {zero} (이동 0) · MAD 중앙 {float(np.nanmedian(mad[b])):.6g}")
    if sum(len(keys[b]) for b in BLOCKS) != 250:
        stop("자질 수 합이 250이 아닙니다.")
    logd = {u: math.log(acc[u]["토큰수_구두점제외"]) for u in uids}
    row_of = {u: i for i, u in enumerate(uids)}
    half = len(uids) // 2

    say(f"\n[5/7] 반복 {n_rep}회 : 반분 → 매칭 → A(이동 없음)·B(가짜 봇 + MAD) 각각 10 절차(v1.2 중심 정렬 포함)")
    say("      중심 정렬·중심·순열의 라벨은 가짜 라벨(무작위 반분)이다. 실제 라벨은 쓰지 않는다.")
    say(f"      반복마다 이동 불변 관문(D): |비율_A − 비율_B| ≤ {INVAR_TOL} · p 셋 같음. 위반은 바로 적는다.")
    reps = []
    t_loop = time.time()
    step = 20 if n_rep <= N_REP else max(20, n_rep // 10)
    for r in range(n_rep):
        seed = SEED + r
        rng = np.random.default_rng(seed)
        perm = rng.permutation(len(uids))
        fb = sorted(uids[i] for i in perm[:half])
        fh = sorted(uids[i] for i in perm[half:])
        pairs, unmatched, _ = caliper_match(fb, fh, logd, CALIPER, seed)
        n = len(pairs)
        swaps = rng.random((N_PERM, n)) < 0.5
        rows = [row_of[b] for b, _, _ in pairs] + [row_of[h] for _, h, _ in pairs]
        XA = {b: X640[b][rows] for b in BLOCKS}
        is_bot = np.array([True] * n + [False] * n)
        XB = {b: shift_rows(XA[b], is_bot, SHIFT_MAD_MULT * mad[b]) for b in BLOCKS}
        fullA = run_procedure(XA, n, swaps)
        fullB = run_procedure(XB, n, swaps)
        inv = invariance(fullA, fullB)
        resA, resB = public(fullA), public(fullB)
        del fullA, fullB
        reps.append({"r": r, "시드": seed, "쌍수": n, "탈락봇": len(unmatched),
                     "교환비율": float(swaps.mean()), "A": resA, "B": resB, "이동불변": inv})
        for b in BLOCKS:
            if not inv[b]["통과"]:
                say(f"      ! r={r} {b} 이동 불변 위반: {inv[b]}")
        if (r + 1) % step == 0 or r == 0:
            el = time.time() - t_loop
            fa = " ".join(f"{b} {resA[b].get('비율', float('nan')):.3f}/{resA[b].get('p_위', float('nan')):.3f}"
                          for b in BLOCKS)
            fbb = " ".join(f"{b} {resB[b].get('비율', float('nan')):.3f}/{resB[b].get('p_위', float('nan')):.3f}"
                           for b in BLOCKS)
            say(f"      r={r:>3} 쌍 {n} · A 비율/p위 {fa} · B {fbb} · 경과 {el:.0f}초 "
                f"(잔여 추정 {el / (r + 1) * (n_rep - r - 1):.0f}초)")
    loop_sec = time.time() - t_loop

    say("\n[6/7] 요약 : 거짓 유의율(p < 0.05 비율)과 Wilson 95% 구간")
    summ = {sc: {b: summarize(reps, sc, b) for b in BLOCKS} for sc in ("A", "B")}
    npairs = quart([x["쌍수"] for x in reps])
    nunm = quart([x["탈락봇"] for x in reps])
    say(f"      쌍 수: 최소 {npairs['최소']:.0f} · Q1 {npairs['Q1']:.1f} · 중앙 {npairs['중앙']:.1f} · "
        f"Q3 {npairs['Q3']:.1f} · 최대 {npairs['최대']:.0f} (탈락 봇 중앙 {nunm['중앙']:.1f})")
    say("\n      시나리오 블록  방향    거짓유의  율      Wilson 95%          판정")
    for sc in ("A", "B"):
        for b in BLOCKS:
            s = summ[sc][b]
            for name, short in (("위쪽(비율>1)", "위쪽"), ("아래쪽(비율<1)", "아래쪽"), ("양측", "양측")):
                c = s[name]
                verdict = "" if name == "양측" else ("통과" if c["통과"] else "불통과")
                say(f"      {sc:<8} {b:<5} {short:<6} {c['거짓유의수']:>3}/{s['유효반복']:<4} "
                    f"{c['율']:.3f}   [{c['Wilson95'][0]:.3f}, {c['Wilson95'][1]:.3f}]   {verdict}")
    say("\n      비율 분포 (가짜 사람 ÷ 가짜 봇)")
    say("      시나리오 블록  Q1       중앙     Q3       최소     최대     | 중심차 평균(백분위) 중앙")
    for sc in ("A", "B"):
        for b in BLOCKS:
            q = summ[sc][b]["비율분포"]
            g = summ[sc][b]["중심차평균_분포"]
            say(f"      {sc:<8} {b:<5} {q['Q1']:.4f}   {q['중앙']:.4f}   {q['Q3']:.4f}   "
                f"{q['최소']:.4f}   {q['최대']:.4f}   | {g['중앙']:.4f}")
    inval = {sc: {b: summ[sc][b]["무효반복"] for b in BLOCKS} for sc in ("A", "B")}
    say(f"      무효 반복 {inval} · 정의 2개 미만 자질 합 "
        f"{ {sc: {b: summ[sc][b]['정의2미만_자질_합'] for b in BLOCKS} for sc in ('A', 'B')} }")
    say(f"      정렬 제외(가짜 집단 정의 2개 미만) 합 "
        f"{ {sc: {b: summ[sc][b]['정렬제외_합'] for b in BLOCKS} for sc in ('A', 'B')} }")

    # ── (v1.2) 이동 불변 관문 요약 (D) ──
    say(f"\n      이동 불변 관문 (D) : 반복마다 |비율_A − 비율_B| ≤ {INVAR_TOL} 이고 p(위·아래·양측) 같음")
    inv_sum = {}
    for b in BLOCKS:
        rows = [x["이동불변"][b] for x in reps]
        viol = [x["r"] for x in reps if not x["이동불변"][b]["통과"]]
        pdiff = [x["r"] for x in reps if x["이동불변"][b].get("백분위다른_자질수", 0) > 0]
        expl = [x["r"] for x in reps if x["이동불변"][b].get("동점변화로_설명됨")]
        inv_sum[b] = {"위반수": len(viol), "위반반복": viol, "위반중_동점변화로_설명됨": len(expl),
                      "백분위가_달라진_반복수": len(pdiff), "백분위가_달라진_반복": pdiff,
                      "비율차_최대": max(x.get("비율차", 0.0) for x in rows),
                      "정렬값차_최대": max(x.get("정렬값_최대차", 0.0) for x in rows)}
        s = inv_sum[b]
        say(f"      {b}  위반 {s['위반수']}/{n_rep} · 백분위가 달라진 반복 {s['백분위가_달라진_반복수']} · "
            f"비율차 최대 {s['비율차_최대']:.1e} · 정렬값차 최대 {s['정렬값차_최대']:.1e}")
    inv_pass = all(inv_sum[b]["위반수"] == 0 for b in BLOCKS)
    say(f"      → 이동 불변 관문 {'통과' if inv_pass else '불통과'}")
    if not inv_pass:
        n_v = sum(inv_sum[b]["위반수"] for b in BLOCKS)
        n_e = sum(inv_sum[b]["위반중_동점변화로_설명됨"] for b in BLOCKS)
        say(f"      위반 {n_v}건 가운데 {n_e}건은 정렬값 차 ≤ 1e-12 이고 백분위가 달라진 자질이 있다.")
        say("      예상 원인은 부동소수점뿐이다: (x + s) − 중앙(x + s)와 x − 중앙(x)의 끝자리가")
        say("      달라 두 가짜 집단 사이의 동점이 풀리거나 새로 생기고, 순위가 움직인다.")

    say("\n[7/7] 판정 (C) : A·B 각각 F·M·R 거짓 유의율 Wilson 상한 ≤ 0.10 이면 통과. 규칙 수정 없음.")
    cells = []
    for sc in ("A", "B"):
        for b in BLOCKS:
            s = summ[sc][b]
            cells.append({"시나리오": sc, "블록": b,
                          "위쪽_율": s["위쪽(비율>1)"]["율"], "위쪽_상한": s["위쪽(비율>1)"]["Wilson95"][1],
                          "위쪽_통과": s["위쪽(비율>1)"]["통과"],
                          "아래쪽_율": s["아래쪽(비율<1)"]["율"], "아래쪽_상한": s["아래쪽(비율<1)"]["Wilson95"][1],
                          "아래쪽_통과": s["아래쪽(비율<1)"]["통과"]})
    main_pass = all(c["위쪽_통과"] for c in cells)
    low_pass = all(c["아래쪽_통과"] for c in cells)
    fa = gate_false_alarm(n_rep)
    a_cells_ok = all(c["위쪽_통과"] and c["아래쪽_통과"] for c in cells if c["시나리오"] == "A")
    gate_pred = {
        "문장": ("10-1을 v1.2 규칙으로 다시 돌리면 B는 A와 같아지고(이동 불변), "
                "A의 여섯 칸 가운데 Wilson 95% 상한이 0.10을 넘는 칸은 없다."),
        "조건": [{"조건": "B = A (이동 불변 관문 위반 0)", "충족": inv_pass},
                {"조건": "A 여섯 칸(F·M·R × 위쪽·아래쪽) Wilson 상한 ≤ 0.10", "충족": a_cells_ok}],
        "판정": "적중" if (inv_pass and a_cells_ok) else "빗나감",
        "효력": "선언 판정" if declared else f"참고 ({n_rep}회). 선언 판정은 {N_REP}회 실행",
    }
    verdict = {
        "규칙": "A·B 각각 F·M·R의 거짓 유의율(p < 0.05 비율) Wilson 95% 상한 ≤ 0.10이면 통과. 불통과면 기록만 하고 규칙은 고치지 않는다(12 뼈대 5절 8항은 '검정 규칙을 고치고 12를 다시 선언'이라 적었으나 이 실행은 기록만).",
        "주판정_방향": "위쪽(비율 > 1, 가짜 봇이 더 좁음) (E7)",
        "칸별": cells,
        "주판정": "통과" if main_pass else "불통과",
        "주판정_불통과칸": [f"{c['시나리오']}-{c['블록']}" for c in cells if not c["위쪽_통과"]],
        "보조_아래쪽": "통과" if low_pass else "불통과",
        "보조_아래쪽_불통과칸": [f"{c['시나리오']}-{c['블록']}" for c in cells if not c["아래쪽_통과"]],
        "두방향_모두": "통과" if (main_pass and low_pass) else "불통과",
        "관문_자체_오경보율": fa,
        "판정_효력": "선언 판정" if declared else f"참고 ({n_rep}회). 선언 판정은 {N_REP}회 실행",
        "이동불변_관문": {"규칙": f"반복마다 F·M·R의 |비율_A - 비율_B| ≤ {INVAR_TOL}이고 p 셋 같음",
                     "통과": inv_pass, "블록별": inv_sum},
        "관문예측_v1.2": gate_pred,
    }
    say(f"      주 판정(위쪽): {verdict['주판정']}  불통과 칸 {verdict['주판정_불통과칸'] or '없음'}")
    say(f"      보조(아래쪽): {verdict['보조_아래쪽']}  불통과 칸 {verdict['보조_아래쪽_불통과칸'] or '없음'}")
    say(f"      두 방향 모두: {verdict['두방향_모두']}")
    say(f"      관문 자체: {n_rep}회 중 거짓 유의 {fa['통과_최대_거짓유의수']}회까지 통과. 참율 0.05에서 한 칸 불통과 확률 "
        f"{fa['한칸_불통과확률(참율별)']['0.05']:.3f} · 0.049에서 {fa['한칸_불통과확률(참율별)']['0.049']:.3f}")
    say(f"      판정 효력: {verdict['판정_효력']}")
    say(f"      이동 불변 관문 (D): {'통과' if inv_pass else '불통과'}")
    say(f"\n      관문 예측(v1.2): {gate_pred['문장']}")
    for c in gate_pred["조건"]:
        say(f"             · {c['조건']:<44} {'충족' if c['충족'] else '불충족'}")
    say(f"             → {gate_pred['판정']} ({gate_pred['효력']})")

    total = time.time() - t_start
    out = {
        "설정": {
            "실행시각": run_at, "python": platform.python_version(), "numpy": np.__version__,
            "platform": f"{platform.system()} {platform.machine()}",
            "sys.flags.optimize": sys.flags.optimize,
            "스크립트_sha256": script_sha,
            "13-0_계정사전_sha256": acc_sha,
            "입력_sha256": {os.path.relpath(p, ROOT) if p.startswith(ROOT) else p: sha256_file(p) for p in
                          (ACCDICT_JSON, SPLIT_JSON, PY10, J10_V11, PY091, J091, PY130, MEASURE_JSON, REPARSE_JSON,
                           FUNCWORDS_JSON, FEATURE_JSON, ACCOUNTS_JSON, FMR_JSON, PREREG_12, PREREG_10)},
            "사전선언": "12_OpenRouter생성_사전선언_뼈대.md 5절 8항 · 10_동질성검정_사전선언.md 4절 · 개정 기록 v1.2",
            "규칙": "v1.2 (10 결정 B2 중심 정렬을 반복 절차에 포함)",
            "관문2_대조대상": "보관된 10 v1.1 정본 JSON, run_procedure(center=False)",
            "시드": f"{SEED} + r (r = 0..{n_rep - 1})", "반복": n_rep, "선언_반복": N_REP,
            "이동불변_허용오차": INVAR_TOL, "순열": N_PERM, "유의수준": ALPHA,
            "캘리퍼": CALIPER, "이동": f"가짜 봇 원값 + 사람 640 MAD × {SHIFT_MAD_MULT}",
            "판정문턱": GATE_UPPER, "Wilson_z": WILSON_Z,
            "기능어_해시": fw_hash, "블록_자질수": {b: len(keys[b]) for b in BLOCKS},
            "M_구성": {"형태자질": feat_keys, "품사": upos_keys, "축분류": axis_map},
            "백분위_규칙": "쌍 표본(2 × 쌍 수 계정) 안에서 자질마다 순위 백분위, 동점 평균순위, (평균순위 - 1) ÷ (정의된 계정 수 - 1), 결측은 순위 제외 (10 결정 B)",
            "p_규칙": {"위쪽": "(순열비율 ≥ 관측 횟수 + 1) ÷ 1,000", "아래쪽": "(순열비율 ≤ 관측 횟수 + 1) ÷ 1,000",
                     "양측": "(|log 순열비율| ≥ |log 관측| 횟수 + 1) ÷ 1,000"},
            "라벨_사용": ["관문 2 10 재현(정본 쌍의 봇·사람)", "관문 2 09-1 매칭 재현(01 라벨)",
                      "관문 3 사람 풀 정의(역할 표a·라벨 human 확인)", "반복 안 중심 정렬·중심·순열은 가짜 라벨"],
            "구현결정": IMPL_DECISIONS,
        },
        "관문": {"1_복사함수": copy_res, "1_손예제": hand_res, "1_매칭손예제": match_res,
               "1_MAD손예제": mad_res, "1_Wilson": wil_res,
               "2_10재현": r10, "2_09-1매칭재현": r091, "3_사람풀": pool_res},
        "자질": feat_info,
        "쌍수_분포": npairs, "탈락봇_분포": nunm,
        "요약": summ,
        "판정": verdict,
        "반복": reps,
        "소요초": {"반복": loop_sec, "전체": total},
    }
    write_json(out_json, out)
    say(f"\n  저장: {os.path.relpath(out_json, ROOT)} · 반복 {loop_sec:.1f}초 · 전체 {total:.1f}초")


if __name__ == "__main__":
    main()
