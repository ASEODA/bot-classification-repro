#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""최종 동질성 규칙의 귀무 오류율 및 위치 이동 불변성 점검. 고정 사람 풀 640개, 1,000회 모의 비교. 실행은 저장소 run.sh를 사용한다."""

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
DATA_DIR = os.path.expanduser("~/DM_LAB_data/12_OpenRouter")

ACCDICT_JSON = os.path.join(DATA_DIR, "13-0_계정사전.json")        # 13-0 산출 (읽기만)
SPLIT_JSON = os.path.join(HERE, "12_OpenRouter생성_준비", "분할.json")
PY10 = os.path.join(HERE, "10_동질성검정.py")
# 관문 2 대조 대상 : 보관된 10 v1.1 정본 JSON (v1.2 정본은 이 파일 뒤에 돈다)
J05 = os.path.join(HERE, "05_사용률검수.json")      # 관문 2 : F 조립 대조 (계정별 사용률)
PY091 = os.path.join(HERE, "09-1_분량통제.py")
J091 = os.path.join(HERE, "09-1_분량통제.json")
MEASURE_JSON = os.path.join(HERE, "04_기능어측정.json")
REPARSE_JSON = os.path.join(HERE, "04-1_확장재파싱.json")
FUNCWORDS_JSON = os.path.join(HERE, "02_기능어목록.json")
FEATURE_JSON = os.path.join(HERE, "07_형태자질비교.json")
ACCOUNTS_JSON = os.path.join(HERE, "01_적격계정.json")
FMR_JSON = os.path.join(FMR_DIR, "FMR_세통제_결과.json")
PREREG_12 = os.path.join(HERE, "12_OpenRouter생성_사전선언_뼈대.md")
PREREG_10 = os.path.join(HERE, "10_동질성검정_사전선언.md")

# 원 단계 소스 (10 결정 M의 COPY_SOURCES와 같은 대응). 관문 1에서 AST 대조.
FROM_10 = ["compute_rates", "build_axis_map", "axis_of", "denom_kind_of", "compute_ratios",
           "compute_upos_ratios", "coef_variation", "compute_features", "dense_vectors",
           "normalize_apostrophe", "nanmedian_cols", "nanmean_cols", "centers", "residuals",
           "residual_scale", "scaled_residuals", "block_distances", "ratio_of", "perm_ratios",
           "p_values", "exact_p", "five"]
FROM_091 = ["caliper_match"]

OUT_JSON = os.path.join(HERE, "10-1_귀무오류율.json")

# ── 과제 상수 (12 뼈대 5절 8항 · 작업 지시) ─────────────────────
SEED = 20260926
N_REP = 200                    # 기본 반복 수 (--reps로 바꾼다). 산출 이름에 접미사가 붙지 않는 수
DECLARED_REP = 1000            # v1.3 선언 판정 반복 수 (사전선언 개정 기록 v1.3)
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
CAP = 5                        # 10 v1.3 결정 B3 : 표준화 잔차 상한
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
    "E11_척도기록": "(v1.3) 반복마다 척도 규칙으로 빠진 자질·평균 대체 자질·상한 5를 넘은 칸 수를 기록.",
    "E12_이동불변": "반복마다 F·M·R의 |비율_A - 비율_B| ≤ 1e-9이고 p 셋(위·아래·양측) 완전 일치. 한쪽만 무효면 위반. 잔차·척도·거리 최대차를 함께 기록.",
    "E13_중심차": "(v1.3) 척도 단위 중심차 = 자질별 |c_봇 - c_사람| ÷ s_j의 평균(제외 자질 뺌). 기록만.",
    "E14_반복수": "--reps N(기본 200). 시드 20260926 + r이라 1,000회의 앞 200회는 200회 실행과 같음. N이 200이 아니면 산출 이름에 _N회. (v1.3) 선언 판정은 1,000회 실행, 200회는 병기.",
    "E15_관문2": "(v1.3) 자질 조립 대조: F는 05 계정별 사용률과 칸마다 같음, M·R은 결측 칸·자질별 결측 계정 수가 보관된 10 v1.1 JSON과 같음. 실제 라벨의 10 결과(비율·p)는 계산하지 않음(10 v1.3 실제 자료 실행은 이 관문 통과 뒤).",
}


# ════════════════════════════════════════════════════════════════════════
# [손 예제] 10 정본(v1.3)과 같은 6계정(3쌍) × 3자질. 손계산은 10 파일 상수 주석에 있다.
# 아래쪽 p만 이 파일에서 새로 센다.
#   교환 8가지 비율 17/6 · 2/3 · 2/3 · 17/6 · 6/17 · 3/2 · 3/2 · 6/17
#   관측 17/6 이하: 8개 전부 → 정확 아래쪽 p = 8/8, 공식 (8+1)/(8+1) = 9/9
# ════════════════════════════════════════════════════════════════════════
HAND_IDS = ["B1", "B2", "B3", "H1", "H2", "H3"]
HAND_PAIRS = [("B1", "H1"), ("B2", "H2"), ("B3", "H3")]
HAND_VALUES = {
    "a": {"B1": 3, "B2": 4, "B3": 5, "H1": 0, "H2": 6, "H3": 7},
    "b": {"B1": 10, "B2": 10, "B3": 20, "H1": 30, "H2": 5, "H3": 40},
    "c": {"B1": 0.5, "B2": 0.125, "B3": None, "H1": 0.875, "H2": 0.25, "H3": 0.75},
}
HAND_CENTER_BOT = {"a": 4, "b": 10, "c": 0.3125}
HAND_CENTER_HUMAN = {"a": 6, "b": 30, "c": 0.75}
HAND_RESID = {
    "a": {"B1": -1, "B2": 0, "B3": 1, "H1": -6, "H2": 0, "H3": 1},
    "b": {"B1": 0, "B2": 0, "B3": 10, "H1": 0, "H2": -25, "H3": 10},
    "c": {"B1": 0.1875, "B2": -0.1875, "B3": None, "H1": 0.125, "H2": -0.5, "H3": 0.0},
}
HAND_SCALE = {"a": 1.0, "b": 5.0, "c": 0.1875}
HAND_Z = {
    "a": {"B1": 1, "B2": 0, "B3": 1, "H1": 5, "H2": 0, "H3": 1},
    "b": {"B1": 0, "B2": 0, "B3": 2, "H1": 0, "H2": 5, "H3": 2},
    "c": {"B1": 1, "B2": 1, "B3": None, "H1": 2 / 3, "H2": 8 / 3, "H3": 0},
}
HAND_DIST = {"B1": 2 / 3, "B2": 1 / 3, "B3": 3 / 2,
             "H1": 17 / 9, "H2": 23 / 9, "H3": 1}
HAND_RATIO = 17 / 6
HAND_SWAPS = {
    (0, 0, 0): 17 / 6, (1, 0, 0): 2 / 3, (0, 1, 0): 2 / 3, (0, 0, 1): 17 / 6,
    (1, 1, 0): 6 / 17, (1, 0, 1): 3 / 2, (0, 1, 1): 3 / 2, (1, 1, 1): 6 / 17,
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


# ── [10_동질성검정.py] nanmean_cols (v1.3) ──
def nanmean_cols(M):
    """[10 v1.3] 열별 평균. 열 전체가 nan이면 nan. 척도 대체값에 쓴다."""
    out = np.full(M.shape[1], np.nan)
    for j in range(M.shape[1]):
        v = M[:, j]
        v = v[~np.isnan(v)]
        if v.size:
            out[j] = np.mean(v)
    return out


# ── [10_동질성검정.py] centers (v1.3) ──
def centers(X, is_bot):
    """[10 v1.3 결정 B3] 집단별 자질 원값 중앙값. 반복 안에서는 가짜 라벨이다."""
    return nanmedian_cols(X[is_bot]), nanmedian_cols(X[~is_bot])


# ── [10_동질성검정.py] residuals (v1.3) ──
def residuals(X, is_bot, c_bot, c_hum):
    """[10 v1.3] 잔차 = 원값 - 자기 집단 중심. 결측은 결측."""
    C = np.where(is_bot[:, None], c_bot[None, :], c_hum[None, :])
    return X - C


# ── [10_동질성검정.py] residual_scale (v1.3) ──
def residual_scale(R):
    """[10 v1.3] 척도 = 두 집단 전 계정 |잔차| 중앙값. 0이면 평균, 평균도 0이거나 정의 2개 미만이면 제외(nan). 반환 (s, 종류 목록)."""
    A = np.abs(R)
    med, mean = nanmedian_cols(A), nanmean_cols(A)
    n_def = (~np.isnan(A)).sum(axis=0)
    s = np.full(R.shape[1], np.nan)
    kind = []
    for j in range(R.shape[1]):
        if n_def[j] < 2:
            kind.append("제외_정의2미만")
        elif med[j] > 0:
            s[j] = med[j]
            kind.append("중앙값")
        elif mean[j] > 0:
            s[j] = mean[j]
            kind.append("평균")
        else:
            kind.append("제외_0")
    return s, kind


# ── [10_동질성검정.py] scaled_residuals (v1.3) ──
def scaled_residuals(R, s):
    """[10 v1.3] z = min(|잔차| ÷ 척도, CAP). 제외 자질은 nan."""
    with np.errstate(invalid="ignore"):
        return np.minimum(np.abs(R) / s[None, :], CAP)


# ── [10_동질성검정.py] block_distances (v1.3) ──
def block_distances(Z):
    """[10 v1.3] 계정별 블록 거리 = 정의된 자질의 z 평균. 사용 자질 수도 돌려준다."""
    used = (~np.isnan(Z)).sum(axis=1)
    with np.errstate(invalid="ignore"):
        d = np.nansum(Z, axis=1) / np.where(used > 0, used, np.nan)
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


def run_procedure(X, n, swaps):
    """
    10 절차 한 번(v1.3 결정 B3). X = 블록별 원값 행렬, 행 = 봇 n개 다음 사람 n개
    (같은 i가 같은 쌍).
      집단 중심(원값 중앙값) → 잔차 → 척도 s_j → z(상한 5) → 블록 거리 → 비율 →
      쌍 안 교환 순열
    손 예제·본 반복이 모두 이 함수를 지난다. 밑줄로 시작하는 키는 내부 배열이라
    JSON에 넣지 않는다.
    """
    is_bot = np.array([True] * n + [False] * n)
    out = {}
    for b in X:
        cb, ch = centers(X[b], is_bot)
        R = residuals(X[b], is_bot, cb, ch)
        s, kind = residual_scale(R)
        Z = scaled_residuals(R, s)
        d, used = block_distances(Z)
        d_bot, d_hum = d[:n], d[n:]
        with np.errstate(invalid="ignore"):
            over = int(np.sum(np.abs(R) / s[None, :] > CAP))
            g = np.abs(cb - ch) / s                                  # E13
        g = g[~np.isnan(g)]
        gap = float(g.mean()) if g.size else float("nan")
        scale = {"평균대체": kind.count("평균"), "제외": sum(1 for k in kind if k.startswith("제외"))}
        if np.isnan(d).any():
            out[b] = {"무효": "nan 거리", "척도": scale, "상한칸": over}
            continue
        if not np.median(d_bot) > 0:
            out[b] = {"무효": "봇 거리 중앙값 0", "척도": scale, "상한칸": over}
            continue
        r = ratio_of(d_bot, d_hum)
        pr = perm_ratios(d_bot, d_hum, swaps)
        p1, p2, ge, ge2 = p_values(r, pr)
        pl, le = p_lower(r, pr)
        out[b] = {"무효": None, "비율": r, "p_위": p1, "p_아래": pl, "p_양측": p2,
                  "위_횟수": ge, "아래_횟수": le, "양측_횟수": ge2,
                  "봇거리_중앙": float(np.median(d_bot)), "사람거리_중앙": float(np.median(d_hum)),
                  "중심차_평균": gap, "척도": scale, "상한칸": over,
                  "_R": R, "_s": s, "_Z": Z, "_c": (cb, ch), "_d": d, "_used": used, "_pr": pr}
    return out


def _maxdiff(u, v):
    """두 배열의 최대 절대차(결측 칸은 뺀다). 결측 위치가 다르면 inf."""
    u, v = np.asarray(u, dtype=float), np.asarray(v, dtype=float)
    if not np.array_equal(np.isnan(u), np.isnan(v)):
        return float("inf")
    g = np.abs(u - v)
    g = g[~np.isnan(g)]
    return float(g.max()) if g.size else 0.0


def invariance(fullA, fullB):
    """
    이동 불변 관문(D, E12). 같은 반복의 A와 B를 블록마다 대조한다.
    비율 차 ≤ 1e-9이고 p 셋(위·아래·양측)이 같아야 통과다. 무엇이 얼마나
    달랐는지 보이려고 잔차·척도·거리의 최대차를 함께 적는다.
    """
    out = {}
    for b in fullA:
        a, c = fullA[b], fullB[b]
        if a["무효"] or c["무효"]:
            out[b] = {"통과": a["무효"] == c["무효"], "무효": [a["무효"], c["무효"]]}
            continue
        dr = abs(a["비율"] - c["비율"])
        same_p = a["p_위"] == c["p_위"] and a["p_아래"] == c["p_아래"] and a["p_양측"] == c["p_양측"]
        out[b] = {"비율차": dr, "p같음": bool(same_p),
                  "잔차_최대차": _maxdiff(a["_R"], c["_R"]), "척도_최대차": _maxdiff(a["_s"], c["_s"]),
                  "거리_최대차": _maxdiff(a["_d"], c["_d"]),
                  "통과": bool(dr <= INVAR_TOL and same_p)}
    return out


def public(res):
    """run_procedure 결과에서 내부 배열을 뺀다."""
    return {b: {k: v for k, v in r.items() if not k.startswith("_")} for b, r in res.items()}


# ════════════════════════════════════════════════════════════════════════
# [관문 1] 함수 승계 · 손 예제
# ════════════════════════════════════════════════════════════════════════


def gate_hand():
    """10 v1.3 손 예제를 본 계산과 같은 run_procedure로 돌린다."""
    feats = ["a", "b", "c"]
    X = np.array([[np.nan if HAND_VALUES[f][u] is None else HAND_VALUES[f][u]
                   for f in feats] for u in HAND_IDS], dtype=float)
    keys = list(HAND_SWAPS)
    swaps = np.array(keys, dtype=bool)
    res = run_procedure({"H": X}, 3, swaps)["H"]
    fails = []
    cb, ch = res["_c"]
    for j, f in enumerate(feats):
        if not close(cb[j], HAND_CENTER_BOT[f]):
            fails.append(f"봇 중심 {f}: {cb[j]}")
        if not close(ch[j], HAND_CENTER_HUMAN[f]):
            fails.append(f"사람 중심 {f}: {ch[j]}")
    R, Z = res["_R"], res["_Z"]
    for i, u in enumerate(HAND_IDS):
        for j, f in enumerate(feats):
            if not close(R[i, j], HAND_RESID[f][u]):
                fails.append(f"잔차 {u}.{f}: {R[i, j]} ≠ {HAND_RESID[f][u]}")
            if not close(Z[i, j], HAND_Z[f][u]):
                fails.append(f"z {u}.{f}: {Z[i, j]} ≠ {HAND_Z[f][u]}")
    for j, f in enumerate(feats):
        if not close(res["_s"][j], HAND_SCALE[f]):
            fails.append(f"척도 {f}: {res['_s'][j]} ≠ {HAND_SCALE[f]}")
    if res["척도"] != {"평균대체": 0, "제외": 0} or res["상한칸"] != 1:
        fails.append(f"척도 기록 {res['척도']} · 상한 칸 {res['상한칸']} (기대 0·0·1)")
    d = res["_d"]
    for i, u in enumerate(HAND_IDS):
        if not close(d[i], HAND_DIST[u]):
            fails.append(f"거리 {u}: {d[i]} ≠ {HAND_DIST[u]}")
    if list(res["_used"]) != [3, 3, 2, 3, 3, 3]:
        fails.append(f"사용 자질 수 {list(res['_used'])}")
    if not close(res["비율"], HAND_RATIO):
        fails.append(f"관측 비율 {res['비율']} ≠ 17/6")
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
    say(f"      중심 6 · 잔차 18칸 · 척도 3 · z 18칸(상한 1칸) · 거리 6 · 비율 17/6 · 교환 8가지  "
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
    n = 200                                    # 대조용 고정 n (200회 병기 실행의 반복 수)
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


def gate_assembly(words):
    """
    (v1.3) 관문 2 : 이 파일의 자질 조립이 정본 입력과 맞는지 본다(E15). 실제 라벨로
    10 절차의 비율·p는 계산하지 않는다. 10 v1.3의 실제 자료 실행은 이 파일의 선언
    판정(1,000회)을 통과한 뒤에만 한다.
      · 입력 사슬: 04 계정 1,869 · 04-1 계정 집합 · 매칭 512쌍 · 축 분류 = FMR 고정값 ·
        형태 58 · 품사 17
      · F : 매칭 1,024계정의 F 원값 행렬이 05 산출(계정별 사용률)과 칸마다 같다
      · M·R : 결측 칸 수와 자질별 결측 계정 수(봇·사람)가 보관된 10 v1.1 JSON과 같다
    """
    d04 = json.load(open(MEASURE_JSON, encoding="utf-8"))
    d041 = json.load(open(REPARSE_JSON, encoding="utf-8"))
    fmr = json.load(open(FMR_JSON, encoding="utf-8"))
    d07 = json.load(open(FEATURE_JSON, encoding="utf-8"))
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

    label_marker("관문 2 : 10 정본의 매칭 쌍(봇·사람 구분)으로 1,024계정을 세운다 (자질 조립만 대조, 결과 계산 없음)")
    ids = [b for b, _ in pairs] + [h for _, h in pairs]
    n = len(pairs)
    merged = {u: {**acc[u], "문장길이": acc1[u]["문장길이"]} for u in ids}
    X = build_features(merged, ids, words, axis_map, feat_keys, upos_keys)

    r05 = json.load(open(J05, encoding="utf-8"))["계정"]
    F05 = np.array([[r05[u]["사용률"].get(w, 0.0) for w in words] for u in ids], dtype=float)
    chk["F_=_05_계정별사용률(1024×172)"] = bool(np.array_equal(X["F"], F05))
    del r05

    keys = {"F": list(words), "M": feat_keys + upos_keys, "R": list(RKEYS)}
    rows = {}
    for b in ("M", "R"):
        miss = np.isnan(X[b])
        per = {keys[b][j]: {"봇": int(miss[:n, j].sum()), "사람": int(miss[n:, j].sum())}
               for j in range(miss.shape[1]) if miss[:, j].any()}
        rows[b] = {"결측칸": int(miss.sum()), "결측자질수": len(per), "자질별": per}
    for k, v in chk.items():
        say(f"      {k:<30} {'통과' if v else '실패'}")
    say(f"      (결과 계산 없음) 10 v1.3 비율·p는 선언 판정 통과 뒤 10 스크립트가 계산한다.")
    out = {"검사": chk, "블록별_결측": rows}
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
    out["척도_합"] = {k: int(sum(r["척도"][k] for r in rows)) for k in ("평균대체", "제외")}
    out["상한칸_합"] = int(sum(r["상한칸"] for r in rows))
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
    ap = argparse.ArgumentParser(description="10-1 귀무 오류율 관문 (v1.3 규칙)")
    ap.add_argument("--reps", type=int, default=N_REP,
                    help=f"반복 수 (기본 {N_REP}, 선언된 판정은 {DECLARED_REP}회 실행에 건다)")
    n_rep = ap.parse_args().reps
    if n_rep < 1:
        stop("--reps는 1 이상이어야 합니다.")
    out_json = OUT_JSON if n_rep == N_REP else os.path.join(HERE, f"10-1_귀무오류율_{n_rep}회.json")
    declared = n_rep == DECLARED_REP

    t_start = time.time()
    run_at = datetime.now().astimezone().isoformat(timespec="seconds")
    say("=" * 74)
    say(f"10-1 귀무 오류율 관문 v1.3 규칙 (10 절차를 사람 640의 무작위 반분에 {n_rep}회 × 2 시나리오)")
    say("=" * 74)
    say(f"  실행 {run_at} · python {platform.python_version()} · numpy {np.__version__} · "
        f"sys.flags.optimize {sys.flags.optimize}")
    say(f"  시드 {SEED} + r · 반복 {n_rep} · 순열 {N_PERM}회 · α {ALPHA} · 캘리퍼 {CALIPER} · "
        f"이동 MAD × {SHIFT_MAD_MULT} · 판정 문턱 Wilson 상한 ≤ {GATE_UPPER}")
    say(f"  규칙 v1.3 (10 결정 B3 원값 잔차 척도, 상한 {CAP}) · 이동 불변 허용오차 {INVAR_TOL} · "
        f"{'선언 판정 실행' if declared else f'병기 실행 (선언 판정은 {DECLARED_REP}회)'} · 산출 {os.path.basename(out_json)}")
    script_sha = sha256_file(os.path.abspath(__file__))
    say(f"  스크립트 sha256 {script_sha}")

    say("\n[1/7] 관문 1 : 함수 승계 · 손 예제")
    hand_res, hand_ok = gate_hand()
    match_res, match_ok = gate_match_hand()
    mad_res, mad_ok = gate_mad_hand()
    wil_res, wil_ok = gate_wilson()
    if not hand_ok:
        for f in hand_res["실패"]:
            say(f"      × {f}")
        stop("손 예제가 손계산과 맞지 않습니다.")
    if not (match_ok and mad_ok and wil_ok):
        stop("매칭·MAD·Wilson 손 예제 가운데 실패가 있습니다.")
    say("  관문 1 통과.")

    say("\n[2/7] 관문 2 : 자질 조립 대조(04·04-1·02·05·07·FMR 쌍, 결과 계산 없음) · 09-1 매칭 재현")
    words, fw_hash = load_words()
    w_ok = len(words) == EXPECT_WORDS and fw_hash == EXPECT_HASH
    say(f"      기능어 {len(words)}종 · 해시 {fw_hash}  {'통과' if w_ok else '실패'}")
    if not w_ok:
        stop("기능어 목록 해시가 다릅니다.")
    r10, r10_ok, acc04, pairs_raw, axis_map, feat_keys, upos_keys = gate_assembly(words)
    if not r10_ok:
        stop("자질 조립 대조가 어긋났습니다: "
             + ", ".join(k for k, v in r10["검사"].items() if not v))
    r091, r091_ok = gate_repro091(acc04, pairs_raw)
    del acc04
    if not r091_ok:
        stop("09-1 매칭 512쌍을 재현하지 못했습니다.")
    say("  관문 2 통과. 이 파일의 자질 조립이 05·10 v1.1 기록과 같고 09-1 매칭을 재현한다.")

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

    say(f"\n[5/7] 반복 {n_rep}회 : 반분 → 매칭 → A(이동 없음)·B(가짜 봇 + MAD) 각각 10 절차(v1.3 원값 잔차 척도)")
    say("      중심·잔차·순열의 라벨은 가짜 라벨(무작위 반분)이다. 실제 라벨은 쓰지 않는다.")
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
    say("      시나리오 블록  Q1       중앙     Q3       최소     최대     | 중심차 평균(척도 단위) 중앙")
    for sc in ("A", "B"):
        for b in BLOCKS:
            q = summ[sc][b]["비율분포"]
            g = summ[sc][b]["중심차평균_분포"]
            say(f"      {sc:<8} {b:<5} {q['Q1']:.4f}   {q['중앙']:.4f}   {q['Q3']:.4f}   "
                f"{q['최소']:.4f}   {q['최대']:.4f}   | {g['중앙']:.4f}")
    inval = {sc: {b: summ[sc][b]["무효반복"] for b in BLOCKS} for sc in ("A", "B")}
    say(f"      무효 반복 {inval}")
    say(f"      척도 합(평균 대체·제외 자질 수를 반복마다 더함) "
        f"{ {sc: {b: summ[sc][b]['척도_합'] for b in BLOCKS} for sc in ('A', 'B')} }")
    say(f"      상한 {CAP}을 넘은 칸 합 "
        f"{ {sc: {b: summ[sc][b]['상한칸_합'] for b in BLOCKS} for sc in ('A', 'B')} }")

    # ── 이동 불변 관문 요약 (D) ──
    say(f"\n      이동 불변 관문 (D) : 반복마다 |비율_A − 비율_B| ≤ {INVAR_TOL} 이고 p(위·아래·양측) 같음")
    inv_sum = {}
    for b in BLOCKS:
        rows = [x["이동불변"][b] for x in reps]
        viol = [x["r"] for x in reps if not x["이동불변"][b]["통과"]]
        inv_sum[b] = {"위반수": len(viol), "위반반복": viol,
                      "비율차_최대": max(x.get("비율차", 0.0) for x in rows),
                      "잔차차_최대": max(x.get("잔차_최대차", 0.0) for x in rows),
                      "척도차_최대": max(x.get("척도_최대차", 0.0) for x in rows),
                      "거리차_최대": max(x.get("거리_최대차", 0.0) for x in rows)}
        s = inv_sum[b]
        say(f"      {b}  위반 {s['위반수']}/{n_rep} · 비율차 최대 {s['비율차_최대']:.1e} · 거리차 최대 "
            f"{s['거리차_최대']:.1e} · 잔차차 최대 {s['잔차차_최대']:.1e} · 척도차 최대 {s['척도차_최대']:.1e}")
    inv_pass = all(inv_sum[b]["위반수"] == 0 for b in BLOCKS)
    say(f"      → 이동 불변 관문 {'통과' if inv_pass else '불통과'}")

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
    gate_pred = {
        "문장": ("10-1에서 A와 B가 같고(이동 불변, 차 ≤ 1e-9), 1,000회 판정에서 여섯 칸 모두 "
                "Wilson 95% 상한 ≤ 0.10. 200회 결과는 병기한다(200회는 참율 0.05에서도 한 칸이 "
                "불통과할 확률이 0.30이라 판정은 1,000회로 한다. 이 변경은 v1.3 실행 전에 적는다)."),
        "조건": [{"조건": "A = B (이동 불변 관문 위반 0)", "충족": inv_pass},
                {"조건": "여섯 칸(A·B × F·M·R 위쪽) Wilson 상한 ≤ 0.10", "충족": main_pass}],
        "판정": "적중" if (inv_pass and main_pass) else "빗나감",
        "효력": "선언 판정" if declared else f"병기 ({n_rep}회). 선언 판정은 {DECLARED_REP}회 실행",
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
        "판정_효력": "선언 판정" if declared else f"병기 ({n_rep}회). 선언 판정은 {DECLARED_REP}회 실행",
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
    say(f"\n      관문 예측(v1.3): {gate_pred['문장']}")
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
                          (ACCDICT_JSON, SPLIT_JSON, PY10, J05, PY091, J091, MEASURE_JSON, REPARSE_JSON,
                           FUNCWORDS_JSON, FEATURE_JSON, ACCOUNTS_JSON, FMR_JSON, PREREG_12, PREREG_10)},
            "사전선언": "12_OpenRouter생성_사전선언_뼈대.md 5절 8항 · 10_동질성검정_사전선언.md 4절 · 개정 기록 v1.3",
            "규칙": "v1.3 (10 결정 B3 원값 잔차 척도를 반복 절차에 포함)", "CAP": CAP,
            "관문2_대조대상": "자질 조립: F는 05 계정별 사용률, M·R은 보관된 10 v1.1 JSON의 결측 구성. 실제 라벨의 10 결과는 계산하지 않음",
            "시드": f"{SEED} + r (r = 0..{n_rep - 1})", "반복": n_rep, "선언_반복": DECLARED_REP,
            "이동불변_허용오차": INVAR_TOL, "순열": N_PERM, "유의수준": ALPHA,
            "캘리퍼": CALIPER, "이동": f"가짜 봇 원값 + 사람 640 MAD × {SHIFT_MAD_MULT}",
            "판정문턱": GATE_UPPER, "Wilson_z": WILSON_Z,
            "기능어_해시": fw_hash, "블록_자질수": {b: len(keys[b]) for b in BLOCKS},
            "M_구성": {"형태자질": feat_keys, "품사": upos_keys, "축분류": axis_map},
            "척도_규칙": "쌍 표본 안에서 가짜 집단별 원값 중앙값을 뺀 잔차, 척도 = 두 집단 |잔차| 중앙값(0이면 평균, 평균도 0이거나 정의 2개 미만이면 제외), z = min(|잔차| ÷ 척도, 5), 거리 = z 평균 (10 결정 B3)",
            "p_규칙": {"위쪽": "(순열비율 ≥ 관측 횟수 + 1) ÷ 1,000", "아래쪽": "(순열비율 ≤ 관측 횟수 + 1) ÷ 1,000",
                     "양측": "(|log 순열비율| ≥ |log 관측| 횟수 + 1) ÷ 1,000"},
            "라벨_사용": ["관문 2 10 재현(정본 쌍의 봇·사람)", "관문 2 09-1 매칭 재현(01 라벨)",
                      "관문 3 사람 풀 정의(역할 표a·라벨 human 확인)", "반복 안 중심·잔차·순열은 가짜 라벨"],
            "구현결정": IMPL_DECISIONS,
        },
        "관문": {"1_손예제": hand_res, "1_매칭손예제": match_res,
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
