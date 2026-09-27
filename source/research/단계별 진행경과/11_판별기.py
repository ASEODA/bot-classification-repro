#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""BotSim: 쌍 단위 교차검증 로지스틱/RF, 평가 묶음 내 k=10 이웃 밀도, 순위 1:1 결합. 최종 규칙. 실행은 저장소 run.sh를 사용한다."""

import argparse
import ast
import hashlib
import json
import math
import os
import platform
import statistics
import sys
import time
import traceback
import types
import unicodedata
import warnings
from datetime import datetime

sys.dont_write_bytecode = True

import joblib
import numpy as np
import scipy
import sklearn
from scipy.spatial.distance import cdist
from scipy.stats import rankdata
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
SCRIPT_PATH = nfc(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPT_PATH)
STEP = HERE
ROOT = os.path.dirname(STEP)
FMR_DIR = os.path.join(STEP, "09_FMR 통제 재검증")

MEASURE_JSON = os.path.join(STEP, "04_기능어측정.json")        # 04: 원카운트
REPARSE_JSON = os.path.join(STEP, "04-1_확장재파싱.json")      # 04-1: 문장길이
ACCOUNTS_JSON = os.path.join(STEP, "01_적격계정.json")         # 01: "라벨"만
FEATURE_JSON = os.path.join(STEP, "07_형태자질비교.json")      # 07: M 자질 키
CORPUS_JSON = os.path.join(FMR_DIR, "입력코퍼스.json")         # 기능어 172종
FMR_JSON = os.path.join(FMR_DIR, "FMR_세통제_결과.json")       # 쌍 · 축 지도 · U
PREDECL_MD = os.path.join(STEP, "11_판별기_사전선언.md")

# 보관 판(읽기 전용): AST 대조 원본 · 재현 관문의 번들과 JSON
OLD_ROW_POS, OLD_ROW_BASE = "위치(전부)", "기준선"   # 보관 판의 행 이름(재현 대조에만 쓴다)

OUT_BASE = "11_판별기"
OUT_JSON = os.path.join(HERE, "11_판별기.json")
OUT_MODEL = os.path.join(HERE, "11_판별기_모델.joblib")
OUT_LOG = os.path.join(HERE, "11_판별기_출력.log")
OUT_ABORT = os.path.join(HERE, "11_판별기_중단.json")
OUT_ABORT_LOG = os.path.join(HERE, "11_판별기_중단_출력.log")
PARTIAL = ".partial"            # 산출은 이 꼬리를 붙여 쓰고 성공하면 떼어 낸다
INPUT_FILES = [MEASURE_JSON, REPARSE_JSON, ACCOUNTS_JSON, FEATURE_JSON,
               CORPUS_JSON, FMR_JSON, PREDECL_MD]

SEED = 20260926
N_OUTER = 5
N_INNER = 5
LR_PARAMS = dict(C=1.0, l1_ratio=0.0, fit_intercept=True, class_weight=None,
                 solver="lbfgs", max_iter=1000)
FPR_TARGETS = (0.05, 0.10)
FUNCWORD_HASH = "382b68572f03bc23"
N_ACCOUNTS_ALL = 1869
N_PAIRS = 512
BLOCK_SIZES = {"F": 172, "M형태": 58, "M품사": 17, "R": 3}
# 열 순서(F · M형태 · M품사 · R)대로 블록 이름을 펼친 배열.
FEATURE_BLOCKS = np.repeat(list(BLOCK_SIZES), list(BLOCK_SIZES.values()))
RKEYS = ("문장당_토큰수", "구두점_비율", "문장길이_변동계수")
MIN_SENTENCES_CV = 5          # 08과 같은 값. 문장 5개 미만은 변동계수 결측
RATE_DIGITS = 6               # 05와 같은 값. F 사용률 반올림 자릿수
GROUP_BOT, GROUP_HUMAN = "bot", "human"

# 도구 넷(사전선언 3절). 밀도의 참고 k 두 행은 판정에 쓰지 않는다.
ROW_POS = "위치"
ROW_DENS = "밀도"
ROW_PROP = "제안"
ROW_BASE = "기준선"
TOOLS = (ROW_POS, ROW_DENS, ROW_PROP, ROW_BASE)
DENS_K = 10                     # 밀도 도구의 k (고정)
DENS_KS = (5, 10, 20)           # 14와 같은 세 k. 5 · 20은 참고
REF_ROWS = {k: f"밀도(k={k})" for k in DENS_KS if k != DENS_K}
RF_PARAMS = dict(n_estimators=500, random_state=SEED)   # 나머지는 scikit-learn 기본값
PROPOSAL_WEIGHTS = (0.5, 0.5)   # 위치 순위 : 밀도 순위 = 1:1 고정. BotSim 결과로 바꾸지 않는다
SHUFFLE_RANGE = (0.45, 0.55)    # 라벨 뒤섞기 관문의 AUC 허용 범위
N_BOOT = 2000
CEILING = 0.999
BOOT_KEY = {"사람": (11, 1), "봇": (11, 2)}             # 부트스트랩 열쇠(시드 [20260926, 열쇠…])

IMPLEMENTATION_DECISIONS = [
    "D1 입력 원천: 매칭 1,024계정은 전체 코퍼스 계정이다. 09 FMR의 fmr_controls.py가 기준선 · 분량매칭에 쓴 것과 "
    "같게 04_기능어측정.json(원카운트)과 04-1_확장재파싱.json(문장길이)을 읽는다. 같은 자질임은 관문 2에서 FMR "
    "분량매칭 250종 U 통계량 · 결측 수 완전 일치로 확인한다.",
    "D2 축 지도: M형태 분모 규칙의 축 지도는 FMR_세통제_결과.json 설정.axis_map_fixed_to_baseline(1,869계정에서 "
    "라벨 없이 유도)을 쓰고, 04에서 다시 유도해 같은지 확인한다. 품사 17종의 분모는 07 compute_upos_ratios 그대로 "
    "토큰수_구두점제외다.",
    "D3 백분위 변환 함수: 학습 fold 값(결측 제외 n개)의 평균 순위 r로 p = (r − 1)/(n − 1)을 매기고, 새 값 x는 학습 "
    "고유값과 그 p 사이를 선형 보간한다(np.interp). 범위 밖은 0 또는 1로 자른다. n = 1이거나 모든 값이 같으면 "
    "p = 0.5 상수. 결측은 그 자질의 학습 fold 원값 중앙값으로 먼저 채운다. 고정 모델에는 이 원값 중앙값을 저장한다.",
    "D4 로지스틱 회귀: scikit-learn 1.8에서 penalty 인자가 폐기 예정이라 L2를 l1_ratio=0.0으로 지정한다(C=1.0, "
    "fit_intercept=True, class_weight=None, solver='lbfgs', max_iter=1000). 점수는 predict_proba의 봇 확률.",
    "D5 문턱: 후보는 점수 고유값 전부, 점수 ≥ 문턱이면 봇. 균형정확도 최대가 여럿이면 가장 작은 후보. 위치 · 기준선의 "
    "fold 문턱은 학습 fold 안 내부 5겹(쌍 단위, 시드 [20260926, 바깥fold]) OOF 점수에서 고른다.",
    "D6 바깥 5겹 배정: 512쌍을 Generator(20260926)로 섞어 np.array_split으로 5등분. fold별 표준편차는 표본표준편차"
    "(ddof=1). OOF 지표는 다섯 fold의 검증 점수와 판정(각 fold 자기 문턱)을 모아 계산한다.",
    "D7 밀도(14 density 그대로): 채점 묶음의 원값 행렬에서 결측을 묶음 안 열 중앙값(np.nanmedian)으로 채우고, 열마다 "
    "(rankdata(average) − 1)/(n − 1) 백분위로 바꾼 뒤, cdist(cityblock)/250으로 L1 평균 거리를 잰다. 자기 자신은 "
    "무한대로 두고 np.partition으로 k번째 거리를 읽는다. 점수 = −거리. 열 전체 결측이면 중단한다. 라벨을 받지 않는다. "
    "BotSim에서는 1,024 묶음 전체에서 한 번 잰다(겹 없음).",
    "D8 제안(보관 판 11 rank_mean과 같은 식): 채점 묶음 안에서 위치 점수와 밀도(k = 10) 점수를 각각 rankdata(average)로 "
    "순위화(큰 값 = 봇 쪽)하고 r̄ = 0.5 · r_위치 + 0.5 · r_밀도, 점수 = (r̄ − 1)/(n − 1). 정수 · 반정수 순위를 먼저 "
    "평균하므로 순위합이 같은 계정은 정확히 같은 점수(동점)를 받는다. BotSim에서는 위치의 OOF 점수(1,024)로 만든다.",
    "D9 기준선: RandomForestClassifier(n_estimators=500, random_state=20260926), 나머지 기본값. 입력은 위치와 같은 "
    "백분위 값 250종. 내부 문턱용 랜덤 포레스트도 500그루 그대로다.",
    "D10 표의 AUC 구간: 봇 · 사람을 따로 계정 단위 복원 추출(12-3 boot_counts, 열쇠 사람 (11, 1) · 봇 (11, 2), "
    "2,000회). 모든 도구가 같은 재추출 행렬을 쓴다(짝지은 부트스트랩). 점수는 재추출마다 다시 계산하지 않는다. "
    "점추정 AUC는 비교 행렬 평균이며 roc_auc_score와 대조한다.",
    "D11 밀도 · 제안의 문턱 지표: fold 문턱이 없으므로 1,024 묶음 점수의 균형정확도 최대점에서 지표를 내고 '기술"
    "(낙관적)'으로 표시한다. 탐지율@오탐5% · 10%는 네 도구 모두 ROC 곡선에서 읽는다.",
    "D12 라벨 뒤섞기(관문 4): np.random.default_rng(20260926).permutation(y)로 1,024 라벨을 전역 순열한다. 쌍 단위 fold를 "
    "유지하되 층화는 뒤섞인 라벨의 쌍 구성으로 한다. 위치는 본 계산과 같은 부품으로 교차검증하고, 제안은 뒤섞기 위치 "
    "OOF 점수와 같은 밀도 점수(라벨 없음)의 순위 평균이다. 두 AUC를 뒤섞은 라벨로 잰다. 둘 다 [0.45, 0.55] 안이어야 "
    "통과한다. 기준선은 뒤섞기에서 돌리지 않는다.",
    "D13 누설 교란(관문 3): 첫 바깥 fold의 검증 원값을 난수로 바꿔 다시 적합해도 백분위 함수 · 중앙값 · 로지스틱 · "
    "랜덤 포레스트 나무 500그루 구조 · 두 문턱이 비트 단위로 같은지 본다. 밀도는 라벨이 없는 묶음 안 도구라 검증 "
    "fold 값을 쓰는 것이 정의다(누설 개념이 없다).",
    "D14 고정 모델: 1,024 전부로 백분위 함수 · 로지스틱 · 랜덤 포레스트를 적합한다. 위치 문턱은 본 교차검증 OOF 점수의 "
    "균형정확도 최대점, 제안 문턱은 1,024 묶음 제안 점수의 균형정확도 최대점. 둘 다 BotSim 내부 기술값이다. 제안 "
    "문턱은 묶음 안 정규화 순위 위의 값이라 묶음이 바뀌면 뜻이 달라진다. 기준선 · 밀도 문턱은 저장하지 않는다.",
    "D15 재현(관문 5): 1,024 고정 로지스틱의 coef_ · intercept_가 보관 번들(sha256 e6b75865…, 열기 전 대조)의 coef · "
    "intercept · model.coef_와 np.array_equal · == 로 같아야 한다. 다르면 번들을 저장하지 않고 중단한다. 백분위 함수 · "
    "중앙값 · 랜덤 포레스트 나무 구조 · 위치 문턱 · 계정별 OOF 점수 · fold 배정의 보관 판 일치는 함께 적는다(기록). "
    "보관 판은 위치 점수를 P[:, 열 250개] 사본(F 순서 메모리)으로 냈고 이 판은 P(C 순서)를 그대로 쓴다. 적합은 "
    "scikit-learn이 C 순서로 바꿔 하므로 계수는 같고, 채점 행렬곱의 합산 순서만 달라 점수가 마지막 자리(최대 약 2e-16)에서 "
    "다를 수 있다. 그 최대차를 기록한다.",
    "D16 결정성(관문 6): 같은 프로세스에서 교차검증 · 밀도 · 제안 · 고정 모델을 한 번 더 계산해, 계정별 점수 · fold "
    "배정 · 문턱 · 계수 · 나무 구조의 canonical JSON sha256이 같은지 본다. 프로세스 사이는 JSON의 결과_digest"
    "(시각 · 경로 · 소요초 · 번들 파일 해시를 뺀 결과의 sha256)로 대조한다.",
    "D17 짝지은 차: 제안 − 위치, 밀도 − 위치 AUC 차의 짝지은 부트스트랩 95% 구간(D10 재추출). P11-3은 점추정 차로 판정한다.",
    "D18 AST 동일: 12-3 func_ast 규칙(docstring을 뺀 ast.dump)으로 함수를, 대입 값의 ast.dump로 상수를 원본과 대조한다. "
    "보관 판에서 이름 · 행을 바꾼 함수(rank_mean의 인자 이름, load_and_gate의 머리 10종 확인 제거, 교차검증 부품)는 "
    "'고친 함수'로 따로 적고 대조하지 않는다.",
]


# ════════════════════════════════════════════════════════════════════════
# [사전 예측] 사전선언 6절 원문 그대로(관문 0-2가 글자 대조). 빗나가도 지우지 않는다.
# ════════════════════════════════════════════════════════════════════════
PREDICTIONS = [
    {"번호": "P11-1", "서술": "위치 OOF AUC가 0.99 이상이다."},
    {"번호": "P11-2", "서술": "밀도 AUC가 0.90 이상이다."},
    {"번호": "P11-3", "서술": "제안 AUC − 위치 OOF AUC가 −0.01 이상이다."},
    {"번호": "P11-4", "서술": "라벨 뒤섞기에서 위치와 제안의 AUC가 모두 0.45~0.55 안이다."},
]
P111_AUC, P112_AUC, P113_DIFF = 0.99, 0.90, -0.01


# ════════════════════════════════════════════════════════════════════════
# [손 예제] 8계정(4쌍) × 4자질. 기대값은 손으로 푼 상수다. (보관 판 11 그대로)
# ────────────────────────────────────────────────────────────────────────
# 행 순서: B1 H1 B2 H2 B3 H3 (학습 = 쌍 1~3) · B4 H4 (검증 = 쌍 4)
# 손 계산 요약
#   f1 학습값 .1 .3 .2 .5 .4 .6 → 정렬 .1~.6 → p 0 .2 .4 .6 .8 1
#      B4 .45 → .4(.6)와 .5(.8) 사이 보간 .7 / H4 .9 → 범위 밖 위 → 1
#   f2 학습값 .5 .2 .4 .1 .6 .3 → p 같은 눈금
#      B4 .55 → .9 / H4 0 → 범위 밖 아래 → 0
#   f3 학습값 3 1 3 2 3 1 → 동점 평균 순위 1은 1.5, 2는 3, 3은 5
#      p = (r−1)/5 → 1→.1, 2→.4, 3→.8 / B4 2.5 → .6 / H4 1 → .1
#   f4 학습값 결측 2 4 1 3 5 → n=5, p 0 .25 .5 .75 1, 원값 중앙값 3
#      B1 결측 → 3 → .5 / B4 결측 → 3 → .5 / H4 6 → 1
#   고정 가중치 w = ln3 · (−5, 5, 0, 0), 절편 0 → z = 5·ln3·(p2 − p1)
#      z/ln3 = B1 4, H1 −1, B2 2, H2 −4, B3 2, H3 −3, B4 1, H4 −5
#      점수 = 3^k/(1+3^k) → 81/82, 1/4, 9/10, 1/82, 9/10, 1/28, 3/4, 1/244
#   문턱 0.5에서 균형정확도 1. 문턱 선택(후보=점수 고유값)은 3/4.
# ════════════════════════════════════════════════════════════════════════
NAN = float("nan")
HAND_X = np.array([
    [0.10, 0.50, 3.0, NAN],   # B1
    [0.30, 0.20, 1.0, 2.0],   # H1
    [0.20, 0.40, 3.0, 4.0],   # B2
    [0.50, 0.10, 2.0, 1.0],   # H2
    [0.40, 0.60, 3.0, 3.0],   # B3
    [0.60, 0.30, 1.0, 5.0],   # H3
    [0.45, 0.55, 2.5, NAN],   # B4 (검증)
    [0.90, 0.00, 1.0, 6.0],   # H4 (검증)
])
HAND_Y = np.array([1, 0, 1, 0, 1, 0, 1, 0])
HAND_TRAIN, HAND_TEST = np.arange(6), np.array([6, 7])
HAND_P_EXPECT = np.array([
    [0.0, 0.8, 0.8, 0.5],
    [0.4, 0.2, 0.1, 0.25],
    [0.2, 0.6, 0.8, 0.75],
    [0.8, 0.0, 0.4, 0.0],
    [0.6, 1.0, 0.8, 0.5],
    [1.0, 0.4, 0.1, 1.0],
    [0.7, 0.9, 0.6, 0.5],
    [1.0, 0.0, 0.1, 1.0],
])
HAND_MEDIAN_EXPECT = [0.35, 0.35, 2.5, 3.0]
HAND_IMPUTE_EXPECT = {"학습": 1, "검증": 1}
HAND_W = math.log(3) * np.array([-5.0, 5.0, 0.0, 0.0])
HAND_B = 0.0
HAND_SCORE_EXPECT = [81 / 82, 1 / 4, 9 / 10, 1 / 82, 9 / 10, 1 / 28, 3 / 4, 1 / 244]
HAND_BA_AT_HALF = 1.0
HAND_THRESH_FIXED = 3 / 4

# 문턱 선택 예제(겹침 있음): 봇 .9 .7 .6 .2 / 사람 .8 .5 .3 .1
#   t=.1 BA .5 | .2 .625 | .3 .5 | .5 .625 | .6 .75 | .7 .625 | .8 .5 | .9 .625
#   → 문턱 .6, BA .75, 탐지율 .75, 오탐률 .25, F1 .75
#   AUC = 봇>사람 쌍 4+3+3+1 = 11 / 16 = .6875
#   오탐 ≤ 5% · 10%(사람 4명 → 0명)에서 탐지율 .25
THR_SCORES = np.array([0.9, 0.7, 0.6, 0.2, 0.8, 0.5, 0.3, 0.1])
THR_Y = np.array([1, 1, 1, 1, 0, 0, 0, 0])
THR_EXPECT = {"문턱": 0.6, "균형정확도": 0.75, "봇탐지율": 0.75, "사람오탐률": 0.25,
              "F1": 0.75, "AUC": 11 / 16, "탐지율@오탐5%": 0.25, "탐지율@오탐10%": 0.25}
# 동점 예제: 봇 .9 .7 .4 .2 / 사람 .8 .5 .3 .1 → .2 .4 .7 .9 모두 BA .625 → 가장 작은 .2
TIE_SCORES = np.array([0.9, 0.7, 0.4, 0.2, 0.8, 0.5, 0.3, 0.1])
TIE_EXPECT = {"문턱": 0.2, "균형정확도": 0.625}
HAND_TOL = 1e-9


# ════════════════════════════════════════════════════════════════════════
# [손 예제 2] 밀도와 순위 평균. 6계정(A~F) × 2자질, k = 2. (14 hand_gate의 값)
# ────────────────────────────────────────────────────────────────────────
#            f1   f2
#     A       0    0
#     B       0    1
#     C       1    0
#     D       1    2
#     E       2   결측
#     F       2    2
#
# ① 중앙값 대치: f2 관측값 0 1 0 2 2 → 중앙값 1 → E.f2 = 1. (f1 중앙값도 1)
# ② 묶음 안 백분위 (r − 1)/(n − 1), n = 6
#     f1 0 0 1 1 2 2 → 평균 순위 1.5 1.5 3.5 3.5 5.5 5.5 → .1 .1 .5 .5 .9 .9
#     f2 0 1 0 2 1 2 → 0 둘 1.5 · 1 둘 3.5 · 2 둘 5.5 → A .1 B .5 C .1 D .9 E .5 F .9
# ③ 거리 = 두 자질 백분위 절대차의 평균. 모두 .2의 배수라 손으로 5를 곱해 적는다.
#          A  B  C  D  E  F
#     A    0  1  1  3  3  4
#     B    1  0  2  2  2  3
#     C    1  2  0  2  2  3
#     D    3  2  2  0  2  1
#     E    3  2  2  2  0  1
#     F    4  3  3  1  1  0      (÷ 5)
# ④ 자기 자신을 뺀 2번째 가까운 거리: A 1 · B 2 · C 2 · D 2 · E 2 · F 1 (÷ 5)
#     밀도 점수 = −(그 거리) → −.2 −.4 −.4 −.4 −.4 −.2
# ⑤ 밀도 순위 백분위: −.4 넷 → 평균 순위 2.5 → .3 · −.2 둘 → 5.5 → .9
# ⑥ 제안: 위치 점수를 0 1 2 3 4 5로 두면 위치 순위 1~6, 밀도 순위 5.5 2.5 2.5 2.5 2.5 5.5
#     r̄ = (1+5.5)/2 = 3.25 · 1.75 · 2.25 · 2.75 · 3.25 · 5.75 → (r̄ − 1)/5
#     = .45 .25 .35 .45 .55 .95  (= 9 5 7 9 11 19 ÷ 20)
# ⑦ 동점 순위 평균: 5계정
#     위치 (.9 .2 .7 .7 .1) → 순위 (5 2 3.5 3.5 1)
#     밀도 (1.5 −2 3 0 −2) → 순위 (4 1.5 5 3 1.5)
#     평균 (4.5 1.75 4.25 3.25 1.25) → (r̄ − 1)/4 = (.875 .1875 .8125 .5625 .0625)
# ════════════════════════════════════════════════════════════════════════
DH_X = np.array([[0, 0], [0, 1], [1, 0], [1, 2], [2, NAN], [2, 2]], dtype=float)
DH_K = 2
DH_MEDIAN = [1.0, 1.0]
DH_P = np.array([[1, 1], [1, 5], [5, 1], [5, 9], [9, 5], [9, 9]]) / 10.0
DH_D = np.array([[0, 1, 1, 3, 3, 4], [1, 0, 2, 2, 2, 3],
                 [1, 2, 0, 2, 2, 3], [3, 2, 2, 0, 2, 1],
                 [3, 2, 2, 2, 0, 1], [4, 3, 3, 1, 1, 0]]) / 5.0
DH_KDIST = np.array([1, 2, 2, 2, 2, 1]) / 5.0
DH_DRANK = np.array([9, 3, 3, 3, 3, 9]) / 10.0
DH_POS = np.arange(6.0)
DH_PROP = np.array([9, 5, 7, 9, 11, 19]) / 20.0
RK_POS = np.array([0.9, 0.2, 0.7, 0.7, 0.1])
RK_DENS = np.array([1.5, -2.0, 3.0, 0.0, -2.0])
RK_EXPECT = [0.875, 0.1875, 0.8125, 0.5625, 0.0625]

# 관문 0이 원본과 AST를 대조하는 복사본 표. 값은 SOURCES의 열쇠다.
# 보관 판에서 고친 함수(대조하지 않는다. 고친 까닭은 D18과 각 docstring)


# ════════════════════════════════════════════════════════════════════════
# [도구] 로그 · 구분선 · 저장 · 해시
# ════════════════════════════════════════════════════════════════════════
class Tee:
    """화면과 로그 파일에 같은 글을 쓴다. IDLE에서 돌려도 로그가 남는다."""

    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8")
        self.out = sys.stdout

    def write(self, s):
        self.out.write(s)
        self.f.write(s)

    def flush(self):
        self.out.flush()
        self.f.flush()


def say(*args):
    print(*args, flush=True)


def line(title=""):
    say("\n" + "═" * 74)
    if title:
        say(title)
        say("═" * 74)


def label_use(where):
    """라벨을 쓰는 지점마다 같은 꼴의 마커를 찍는다."""
    say(f"  [라벨 사용] {where}")


def write_json(path, obj):
    """임시 파일에 쓰고 이름을 바꿔치기한다. 도중에 멈춰도 반쪽 파일이 남지 않는다."""
    assert os.path.dirname(os.path.abspath(path)) == HERE, "시뮬레이션 폴더 밖 쓰기 금지"
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, allow_nan=False)
    os.replace(tmp, path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fnum(x):
    """JSON용. NaN은 None으로, numpy 수는 파이썬 수로."""
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else x


# ── [14_이웃밀도.py] check · canonical · digest ──
def check(condition, message):
    if not condition:
        raise AssertionError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


# ── [12-3_판별기ver2.py] func_ast · jsonable ──
def func_ast(src, name):
    """소스에서 함수 name의 AST를 docstring을 빼고 문자열로. [13-0 func_ast와 같은 규칙]"""
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            body = n.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                n.body = body[1:]
            return ast.dump(n)
    return None


def jsonable(o):
    """numpy 값을 파이썬 값으로. NaN · inf는 None."""
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return [jsonable(v) for v in o.tolist()]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        x = float(o)
        return None if (math.isnan(x) or math.isinf(x)) else x
    return o


# ════════════════════════════════════════════════════════════════════════
# [실행 안전] 산출 이름 · 중단 기록
# ════════════════════════════════════════════════════════════════════════
RUN = types.SimpleNamespace(tee=None, gates={})


def stop(msg):
    """관문 실패 또는 예외. 정본 산출은 만들지 않고 중단 기록만 남긴다."""
    say(f"\n■ 중단 : {msg}")
    say("  결과 파일을 만들지 않고 끝냅니다.")
    write_json(OUT_ABORT, jsonable({"중단": msg, "관문": RUN.gates,
                                    "시각": datetime.now().astimezone().isoformat()}))
    for p in (OUT_JSON, OUT_MODEL):
        if os.path.exists(p + PARTIAL):
            os.remove(p + PARTIAL)
    say(f"  중단 기록: {OUT_ABORT}")
    sys.stdout.flush()
    if RUN.tee is not None:
        sys.stdout = RUN.tee.out
        RUN.tee.f.close()
        os.replace(OUT_LOG + PARTIAL, OUT_ABORT_LOG)
        print(f"  중단 로그: {OUT_ABORT_LOG}")
    sys.exit(1)


# ════════════════════════════════════════════════════════════════════════
# [1] 자질 계산: 05 · 07 · 08 규칙 복사 (보관 판 11 그대로)
# ────────────────────────────────────────────────────────────────────────
# 분모 규칙을 새로 짜지 않는다. 05 compute_rates(F), 07 compute_ratios ·
# compute_upos_ratios(M), 08 compute_features(R)의 나눗셈을 그대로 옮겼다.
# 같은 자로 쟀는지는 관문 2에서 FMR 분량매칭 U 250개 완전 일치로 확인한다.
# ════════════════════════════════════════════════════════════════════════
def axis_of(key):
    return key.split("=", 1)[0]


def build_axis_map(accounts):
    """07 build_axis_map 복사. 자료 전체(라벨 없음)에서 축별 값 종류를 모은다."""
    axis_values = {}
    for a in accounts.values():
        for key in a.get("자질", {}):
            axis, sep, val = key.partition("=")
            if not sep:
                axis, val = key, ""
            axis_values.setdefault(axis, set()).add(val)
    return {ax: sorted(vs) for ax, vs in axis_values.items()}


def f_rates(a, keys):
    """05 규칙: 기능어 카운트 ÷ 토큰수_구두점제외, 6자리 반올림. 없는 키는 0회."""
    w = a["토큰수_구두점제외"]
    return [round(a["기능어"].get(k, 0) / w, RATE_DIGITS) if w else None for k in keys]


def m_ratios(a, keys, axis_map):
    """
    07 규칙: 대립값 ≥ 2인 축은 그 계정의 축 내부 합으로, 대립값 1개인 자질은
    토큰수_구두점제외로 나눈다. 축을 한 번도 안 쓴 계정은 결측(None).
    """
    feats = a.get("자질", {})
    denom_tok = a.get("토큰수_구두점제외", 0)
    axis_total = {}
    for k, n in feats.items():
        axis_total[axis_of(k)] = axis_total.get(axis_of(k), 0) + n
    row = []
    for k in keys:
        cnt = feats.get(k, 0)
        if len(axis_map.get(axis_of(k), [""])) >= 2:
            d = axis_total.get(axis_of(k), 0)
        else:
            d = denom_tok
        row.append(None if d == 0 else cnt / d)
    return row


def upos_ratios(a, keys):
    """07 규칙: 품사 카운트 ÷ 토큰수_구두점제외."""
    pos = a.get("UPOS", {})
    d = a.get("토큰수_구두점제외", 0)
    return [None if d == 0 else pos.get(k, 0) / d for k in keys]


def rhythm(a):
    """08 규칙: 문장당 토큰수, 구두점 비율(전체 토큰 분모), 변동계수(표본표준편차, 문장 5개 미만 결측)."""
    tok, tok_np, n_sent = a["토큰수"], a["토큰수_구두점제외"], a["문장수"]
    lengths = a["문장길이"]
    assert len(lengths) == n_sent and sum(lengths) == tok_np, "문장길이 정합 실패"
    r1 = tok_np / n_sent if n_sent > 0 else None
    r2 = (tok - tok_np) / tok if tok > 0 else None
    r3 = None
    if n_sent >= MIN_SENTENCES_CV:
        mean = sum(lengths) / n_sent
        if mean > 0:
            r3 = statistics.stdev(lengths) / mean
    return [r1, r2, r3]


def build_matrix(accounts, ids, keys, axis_map):
    """(len(ids) × 250) 행렬. 결측은 NaN. 열 순서 = F · M형태 · M품사 · R."""
    rows = []
    for u in ids:
        a = accounts[u]
        rows.append(f_rates(a, keys["F"]) + m_ratios(a, keys["M형태"], axis_map)
                    + upos_ratios(a, keys["M품사"]) + rhythm(a))
    return np.array([[NAN if v is None else v for v in r] for r in rows], dtype=float)


# ════════════════════════════════════════════════════════════════════════
# [위치 부품] 백분위 · 대치 · 로지스틱 · 문턱 · 지표 (보관 판 11 그대로)
# ════════════════════════════════════════════════════════════════════════
def fit_prep(Xtr, fitted_on):
    """
    학습 행만으로 자질별 백분위 함수와 원값 중앙값을 만든다.

    fitted_on: 이 변환이 본 행의 전역 번호. 누설 단언에 쓴다.
    반환 사전의 xp[j] · fp[j]가 j번 자질의 변환 함수 전부다(12-3 · 13이 그대로 쓴다).
    """
    d = Xtr.shape[1]
    xp, fp, med = [], [], np.empty(d)
    for j in range(d):
        v = Xtr[:, j]
        v = v[~np.isnan(v)]
        assert v.size > 0, f"{j}번 자질이 학습 fold에서 전부 결측"
        med[j] = np.median(v)
        uniq = np.unique(v)
        if v.size == 1 or uniq.size == 1:
            xp.append(uniq.copy())
            fp.append(np.array([0.5]))
            continue
        r = rankdata(v, method="average")
        p = (r - 1.0) / (v.size - 1.0)
        # 같은 원값은 같은 평균 순위 → 같은 p. 고유값마다 한 번씩만 담는다.
        order = np.argsort(v, kind="mergesort")
        vs, ps = v[order], p[order]
        first = np.concatenate(([True], vs[1:] != vs[:-1]))
        xp.append(vs[first].copy())
        fp.append(ps[first].copy())
    return {"xp": xp, "fp": fp, "median": med,
            "fitted_on": np.asarray(fitted_on).copy()}


def apply_prep(prep, X):
    """결측을 학습 원값 중앙값으로 채운 뒤 백분위 함수에 통과. 범위 밖은 0 · 1로 자른다."""
    Xf = np.where(np.isnan(X), prep["median"][None, :], X)
    P = np.empty_like(Xf)
    for j in range(X.shape[1]):
        P[:, j] = np.clip(np.interp(Xf[:, j], prep["xp"][j], prep["fp"][j]), 0.0, 1.0)
    return P


def fit_lr(P, y):
    """[라벨 사용] 로지스틱 회귀. 수렴 경고 수를 함께 돌려준다."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        m = LogisticRegression(**LR_PARAMS).fit(P, y)
    n_conv = sum(issubclass(w.category, ConvergenceWarning) for w in caught)
    return m, n_conv


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def rates_at(scores, y, t):
    pred = scores >= t
    pos, neg = y == 1, y == 0
    tp = int(np.sum(pred & pos)); fn = int(np.sum(~pred & pos))
    fp = int(np.sum(pred & neg)); tn = int(np.sum(~pred & neg))
    return tp, fn, fp, tn


def balanced_accuracy(tp, fn, fp, tn):
    return 0.5 * (tp / (tp + fn) + tn / (tn + fp))


def choose_threshold(scores, y):
    """
    [라벨 사용] 균형정확도 최대 문턱. 후보 = 점수 고유값, 판정 = 점수 ≥ 문턱.
    최대가 여럿이면 가장 작은 후보(구현 결정).
    """
    cands = np.unique(scores)
    s = scores[None, :]
    pred = s >= cands[:, None]
    pos, neg = (y == 1), (y == 0)
    tpr = (pred & pos[None, :]).sum(1) / pos.sum()
    tnr = (~pred & neg[None, :]).sum(1) / neg.sum()
    ba = 0.5 * (tpr + tnr)
    best = ba.max()
    idx = np.where(np.isclose(ba, best, rtol=0.0, atol=1e-12))[0][0]
    return float(cands[idx]), float(best)


def tpr_at_fpr(scores, y, target):
    fpr, tpr, _ = roc_curve(y, scores, drop_intermediate=False)
    ok = fpr <= target + 1e-12
    return float(tpr[ok].max())


def metrics(scores, y, t):
    """고정 지표 다섯 + 보조 둘."""
    tp, fn, fp, tn = rates_at(scores, y, t)
    out = {
        "AUC": float(roc_auc_score(y, scores)),
        "균형정확도": balanced_accuracy(tp, fn, fp, tn),
        "봇탐지율": tp / (tp + fn),
        "사람오탐률": fp / (fp + tn),
        "F1": (2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else 0.0,
    }
    for tg in FPR_TARGETS:
        out[f"탐지율@오탐{int(round(tg * 100))}%"] = tpr_at_fpr(scores, y, tg)
    out["혼동"] = {"TP": tp, "FN": fn, "FP": fp, "TN": tn}
    return out


METRIC_KEYS = ["AUC", "균형정확도", "봇탐지율", "사람오탐률", "F1",
               "탐지율@오탐5%", "탐지율@오탐10%"]


# ════════════════════════════════════════════════════════════════════════
# [fold] 단위(쌍) 묶음으로 나눈다. 같은 단위는 언제나 같은 fold. (보관 판 11 그대로)
# ════════════════════════════════════════════════════════════════════════
def make_folds(units, y, k, rng):
    """
    units: 행 번호 튜플의 목록(쌍이면 (봇, 사람)). 단위의 라벨 구성으로 층화한다.
    반환: 행 번호 → fold 번호 배열의 사전.
    """
    kinds = {}
    for ui, u in enumerate(units):
        kinds.setdefault(tuple(sorted(int(y[i]) for i in u)), []).append(ui)
    assign = {}
    for kind in sorted(kinds):
        idx = np.array(kinds[kind])
        perm = idx[rng.permutation(idx.size)]
        for f, chunk in enumerate(np.array_split(perm, k)):
            for ui in chunk:
                for i in units[ui]:
                    assign[int(i)] = f
    return assign


# ════════════════════════════════════════════════════════════════════════
# [밀도 · 제안] 14 density 그대로 · 순위 평균
# ────────────────────────────────────────────────────────────────────────
# 밀도는 채점 묶음 하나의 원값 행렬만 받는다. 라벨 · 학습 중심 · 번들 변환을
# 쓰지 않는다. 묶음 안에서 결측을 채우고 백분위를 새로 만든다.
# ════════════════════════════════════════════════════════════════════════
def ranks(values):
    return (rankdata(values, method="average", axis=0) - 1.0) / (len(values) - 1.0)


def density(matrix, ks):
    check(matrix.ndim == 2 and len(matrix) > max(ks), "행렬 크기 또는 k 오류")
    check(not np.isinf(matrix).any(), "자질에 무한값 존재")
    check(not np.isnan(matrix).all(axis=0).any(), "열 전체 결측: 사전선언의 중앙값을 정의할 수 없음")
    medians = np.nanmedian(matrix, axis=0)
    imputed = np.where(np.isnan(matrix), medians, matrix)
    percentiles = ranks(imputed)
    distances = cdist(percentiles, percentiles, metric="cityblock") / matrix.shape[1]
    np.fill_diagonal(distances, np.inf)
    ordered = np.partition(distances, [k - 1 for k in ks], axis=1)
    scores = {k: -ordered[:, k - 1] for k in ks}
    return scores, medians, percentiles, distances


def rank_mean(s_pos, s_dens):
    """
    제안 점수. 채점 묶음 안에서만 순위를 매긴다.
        순위: 작은 값 1 ~ 큰 값 n (큰 값 = 봇 쪽), 동점은 평균 순위
        r̄ = 위치 순위 × 0.5 + 밀도 순위 × 0.5   (비중 1:1 고정)
        점수 = (r̄ − 1) ÷ (n − 1)   → [0, 1]. 백분위 p = (r − 1)/(n − 1)과 같은 꼴.
    순위로 바꾸는 이유: 확률(0~1)과 이웃 거리는 눈금이 달라 그대로 더할 수 없다.
    정수 · 반정수 순위를 먼저 평균하므로 순위합이 같은 계정은 정확히 같은 점수를 받는다.
    """
    n = len(s_pos)
    assert n == len(s_dens) and n >= 2
    w_pos, w_dens = PROPOSAL_WEIGHTS
    r = w_pos * rankdata(s_pos, method="average") + w_dens * rankdata(s_dens, method="average")
    return (r - 1.0) / (n - 1.0)


def score_bundle(b, X):
    """
    고정 모델 번들 한 벌로 채점 묶음 X(원값, 계정 × 250, 결측 NaN)를 채점한다. 라벨은 받지 않는다.
    12-3 · 13은 이 함수를 그대로 복사해 쓴다(AST 대조).
        위치   = 번들 로지스틱의 봇 확률 (번들 원값 중앙값 대치 → 번들 백분위 함수)
        기준선 = 번들 랜덤 포레스트의 봇 확률 (같은 입력)
        밀도   = density(X) : 묶음 안 대치 · 묶음 안 백분위 · k번째 이웃 거리의 음수 (번들 k)
        제안   = rank_mean(위치, 밀도)  : 묶음 안 순위 1:1 평균
    참고 k(번들 density_ks 가운데 k가 아닌 것)는 '밀도(k=…)' 이름으로 함께 돌려준다.
    반환: (도구별 점수 사전, 번들 백분위 값 P)
    """
    prep = {"xp": b["percentile_xp"], "fp": b["percentile_fp"], "median": b["impute_raw_median"]}
    P = apply_prep(prep, X)
    ks = tuple(b["density_ks"])
    dens, _, _, _ = density(X, ks)
    s = {ROW_POS: b["model"].predict_proba(P)[:, 1], ROW_DENS: dens[b["density_k"]]}
    s[ROW_PROP] = rank_mean(s[ROW_POS], s[ROW_DENS])
    s[ROW_BASE] = b["rf"].predict_proba(P)[:, 1]
    for k in ks:
        if k != b["density_k"]:
            s[f"밀도(k={k})"] = dens[k]
    return s, P


# ════════════════════════════════════════════════════════════════════════
# [부트스트랩 AUC] 12-3 · 13 그대로
# ════════════════════════════════════════════════════════════════════════
def boot_counts(key, strata, R):
    """
    [부트스트랩 재추출 행렬] (R × 단위 수). 칸 값 = 그 재추출에서 그 단위가 뽑힌 횟수.
    층마다 따로 복원 추출한다. 같은 열쇠는 언제나 같은 행렬이다(시드 [20260926, 열쇠…]).
    """
    rng = np.random.default_rng([SEED, *key])
    strata = np.asarray(strata)
    W = np.zeros((R, len(strata)))
    for s in sorted(set(strata.tolist())):
        idx = np.where(strata == s)[0]
        W[:, idx] = rng.multinomial(idx.size, np.full(idx.size, 1.0 / idx.size), size=R)
    return W


def cmp_matrix(sb, sh):
    """봇 × 사람 비교 행렬: 봇 점수가 크면 1, 같으면 0.5, 작으면 0. 평균이 곧 AUC다."""
    return (sb[:, None] > sh[None, :]).astype(float) + 0.5 * (sb[:, None] == sh[None, :])


def boot_auc(C, Wb, Wh):
    """재추출마다의 AUC = 뽑힌 횟수로 가중한 비교 행렬 평균."""
    return ((Wb @ C) * Wh).sum(axis=1) / (Wb.sum(axis=1) * Wh.sum(axis=1))


def ci95(dist):
    lo, hi = np.percentile(dist, [2.5, 97.5])
    return [float(lo), float(hi)]


def auc_boot(s, bidx, hidx, Wb, Wh):
    """점추정 AUC와 재추출 분포(cmp_matrix · boot_auc). 점추정은 roc_auc_score와 대조."""
    C = cmp_matrix(s[bidx], s[hidx])
    pt = float(C.mean())
    ref = roc_auc_score(np.r_[np.ones(len(bidx)), np.zeros(len(hidx))], np.r_[s[bidx], s[hidx]])
    check(abs(pt - ref) < 1e-12, "비교 행렬 AUC ≠ roc_auc_score")
    return pt, boot_auc(C, Wb, Wh)


def paired_diff(pa, da, pb, db):
    """짝지은 부트스트랩 차 A − B. 두 AUC가 모두 CEILING 이상이면 천장 동률."""
    lo, hi = ci95(da - db)
    return {"차": pa - pb, "CI95": [lo, hi], "천장동률": bool(pa >= CEILING and pb >= CEILING),
            "하한>0": bool(lo > 0), "상한<0": bool(hi < 0), "0포함": bool(lo <= 0 <= hi)}


# ════════════════════════════════════════════════════════════════════════
# [위치 · 기준선 교차검증] 쌍 단위 5겹, 내부 5겹 문턱
# ════════════════════════════════════════════════════════════════════════
def fit_rf(Z, y, fitted_on):
    """[라벨 사용] 기준선 랜덤 포레스트. 나무 500, random_state 고정, 나머지 기본값. 튜닝 없음."""
    m = RandomForestClassifier(**RF_PARAMS).fit(Z, y)
    return {"model": m, "fitted_on": np.asarray(fitted_on).copy()}


def fold_rows(with_base):
    return [ROW_POS, ROW_BASE] if with_base else [ROW_POS]


def fit_all(X, y, rows, with_base=True):
    """
    [라벨 사용] 학습 행 rows만으로 적합한다.
        · 백분위 함수(라벨 없음) → 학습 행의 백분위 값 P
        · 위치: 로지스틱
        · 기준선: 랜덤 포레스트(백분위 입력). with_base가 거짓이면 건너뛴다(라벨 뒤섞기).
    rows 밖의 행은 한 줄도 만지지 않는다(X[rows], y[rows]만 쓴다).
    """
    rows = np.asarray(rows)
    Xr, yr = X[rows], y[rows]
    prep = fit_prep(Xr, rows)
    P = apply_prep(prep, Xr)
    model, n_conv = fit_lr(P, yr)
    fit = {"prep": prep, "model": model, "rf": None, "n_conv": n_conv}
    if with_base:
        fit["rf"] = fit_rf(P, yr, rows)
    return fit


def score_fold(fit, Xs):
    """
    적합이 끝난 위치 · 기준선으로 원값 Xs를 채점한다. 라벨은 받지 않는다.
    두 점수는 계정마다 따로 정해진다(묶음과 무관). 밀도 · 제안은 묶음 단위라 여기서 내지 않는다.
    """
    P = apply_prep(fit["prep"], Xs)
    s = {ROW_POS: fit["model"].predict_proba(P)[:, 1]}
    if fit["rf"] is not None:
        s[ROW_BASE] = fit["rf"]["model"].predict_proba(P)[:, 1]
    return s


def fold_fit(X, y, tr_idx, units, inner_seed, with_base=True):
    """
    바깥 학습 fold 하나로 할 일 전부: 내부 5겹 점수 → 도구마다 문턱, 그리고 학습 fold
    전체로 백분위 함수 · 로지스틱 · 랜덤 포레스트. tr_idx 밖의 행은 만지지 않는다.
    """
    tr_set = set(int(i) for i in tr_idx)
    tr_units = [u for u in units if all(int(i) in tr_set for i in u)]
    check(sum(len(u) for u in tr_units) == len(tr_idx), "단위가 fold 경계를 넘는다")
    inner = make_folds(tr_units, y, N_INNER, np.random.default_rng(inner_seed))
    pos_of = {int(i): p for p, i in enumerate(tr_idx)}
    rows = fold_rows(with_base)
    inner_scores = {a: np.full(len(tr_idx), NAN) for a in rows}
    n_conv = 0
    for f in range(N_INNER):
        iva = np.array([i for i in tr_idx if inner[int(i)] == f])
        itr = np.array([i for i in tr_idx if inner[int(i)] != f])
        check(set(iva.tolist()) <= tr_set and set(itr.tolist()) <= tr_set, "내부 fold가 학습 fold 밖")
        check(not (set(iva.tolist()) & set(itr.tolist())), "내부 학습 · 검증이 겹친다")
        fit_in = fit_all(X, y, itr, with_base)
        n_conv += fit_in["n_conv"]
        s_in = score_fold(fit_in, X[iva])
        where = [pos_of[int(i)] for i in iva]
        for a in rows:
            inner_scores[a][where] = s_in[a]
    thresholds = {}
    for a in rows:
        check(not np.isnan(inner_scores[a]).any(), "내부 점수에 빈칸")
        thresholds[a] = choose_threshold(inner_scores[a], y[tr_idx])
    fit = fit_all(X, y, tr_idx, with_base)
    fit.update({"thresholds": thresholds, "inner_scores": inner_scores,
                "n_conv": n_conv + fit["n_conv"]})
    return fit


def run_cv(X, y, units, seed, label_note, with_base=True, record_detail=True, verbose=True):
    """
    바깥 5겹. 반환: 도구별(위치 · 기준선) OOF 지표 · fold별 지표 · 문턱 · 배정 · OOF 점수.
    """
    n = len(y)
    outer = make_folds(units, y, N_OUTER, np.random.default_rng(seed))
    fold_of = np.array([outer[i] for i in range(n)])
    for u in units:        # 누설 단언 ①: 단위(쌍)의 모든 계정은 같은 fold
        check(len({outer[int(i)] for i in u}) == 1, "쌍이 fold를 가로지른다")
    rows = fold_rows(with_base)
    oof = {a: np.full(n, NAN) for a in rows}
    oof_pred = {a: np.zeros(n, dtype=bool) for a in rows}
    per_fold = {a: [] for a in rows}
    fold_info = []
    if verbose:
        label_use(f"{label_note}: 로지스틱{' · 랜덤 포레스트' if with_base else ''} 학습 · 내부 OOF 문턱 선택 · "
                  "검증 지표 계산")
    for f in range(N_OUTER):
        va_idx = np.where(fold_of == f)[0]
        tr_idx = np.where(fold_of != f)[0]
        fit = fold_fit(X, y, tr_idx, units, [seed, f], with_base)
        va_set, tr_set = set(va_idx.tolist()), set(tr_idx.tolist())
        # 누설 단언 ②: 백분위 함수 · 랜덤 포레스트가 본 행 ∩ 검증 fold = ∅
        seen = set(fit["prep"]["fitted_on"].tolist())
        check(not (seen & va_set) and seen == tr_set, "검증 fold가 백분위 함수에 쓰였다")
        if fit["rf"] is not None:
            seen_rf = set(fit["rf"]["fitted_on"].tolist())
            check(not (seen_rf & va_set) and seen_rf == tr_set, "검증 fold가 기준선 학습에 쓰였다")
        check(fit["model"].n_features_in_ == X.shape[1], "로지스틱 입력 자질 수")
        check(all(len(s) == len(tr_idx) for s in fit["inner_scores"].values()),
              "문턱용 점수에 학습 fold 밖 계정이 섞였다")
        s_va = score_fold(fit, X[va_idx])
        info = {"fold": f, "학습n": int(len(tr_idx)), "검증n": int(len(va_idx)),
                "검증_봇": int(y[va_idx].sum()), "수렴경고": int(fit["n_conv"]),
                "검증_결측대치수": int(np.isnan(X[va_idx]).sum()),
                "학습_결측대치수": int(np.isnan(X[tr_idx]).sum()),
                "문턱": {}, "내부OOF_균형정확도": {}, "위치_반복수": int(fit["model"].n_iter_[0])}
        for a in rows:
            s = s_va[a]
            t, ba_in = fit["thresholds"][a]
            oof[a][va_idx] = s
            oof_pred[a][va_idx] = s >= t
            met = metrics(s, y[va_idx], t)
            met["문턱"] = t
            per_fold[a].append(met)
            info["문턱"][a] = t
            info["내부OOF_균형정확도"][a] = ba_in
        if record_detail:
            info["위치_계수"] = [float(c) for c in fit["model"].coef_[0]]
            info["위치_절편"] = float(fit["model"].intercept_[0])
        fold_info.append(info)
        if verbose:
            say(f"    fold {f}: 학습 {len(tr_idx)} · 검증 {len(va_idx)} · AUC "
                + " · ".join(f"{a} {per_fold[a][-1]['AUC']:.4f}" for a in rows))
    table = {}
    for a in rows:
        check(not np.isnan(oof[a]).any(), "OOF 점수에 빈칸")
        pred = oof_pred[a]
        pos, neg = y == 1, y == 0
        tp = int(np.sum(pred & pos)); fn = int(np.sum(~pred & pos))
        fp = int(np.sum(pred & neg)); tn = int(np.sum(~pred & neg))
        row_oof = {"AUC": float(roc_auc_score(y, oof[a])),
                   "균형정확도": balanced_accuracy(tp, fn, fp, tn),
                   "봇탐지율": tp / (tp + fn), "사람오탐률": fp / (fp + tn),
                   "F1": 2 * tp / (2 * tp + fp + fn)}
        for tg in FPR_TARGETS:
            row_oof[f"탐지율@오탐{int(round(tg * 100))}%"] = tpr_at_fpr(oof[a], y, tg)
        row_oof["혼동"] = {"TP": tp, "FN": fn, "FP": fp, "TN": tn}
        fold_mean = {k: float(np.mean([m[k] for m in per_fold[a]])) for k in METRIC_KEYS}
        fold_sd = {k: float(np.std([m[k] for m in per_fold[a]], ddof=1)) for k in METRIC_KEYS}
        table[a] = {"OOF": row_oof, "fold평균": fold_mean, "fold표준편차": fold_sd,
                    "fold별": per_fold[a]}
    return {"table": table, "fold_of": fold_of, "fold_info": fold_info,
            "oof": oof, "oof_pred": oof_pred}


# ════════════════════════════════════════════════════════════════════════
# [관문 0] 복사 함수 · 상수 AST 대조, 사전선언 예측 원문
# ════════════════════════════════════════════════════════════════════════


def gate_predecl_text():
    """예측 P11-1~4가 사전선언 파일의 문장과 글자까지 같은가."""
    txt = open(PREDECL_MD, encoding="utf-8").read()
    rows = {p["번호"]: f"- **{p['번호']}**: {p['서술']}" in txt for p in PREDICTIONS}
    rows["마감판 표시"] = "마감판" in txt
    for k, v in rows.items():
        say(f"      {k:<10} {'원문 일치' if v else '■ 원문과 다름'}")
    return {"항목": rows, "사전선언_sha256": sha256_file(PREDECL_MD)}, all(rows.values())


# ════════════════════════════════════════════════════════════════════════
# [관문 1] 손 예제(위치) : 보관 판 11 그대로
# ════════════════════════════════════════════════════════════════════════
def close(a, b, tol=HAND_TOL):
    return abs(float(a) - float(b)) <= tol


def gate_hand():
    line("[관문 1] 손 예제: 8계정(4쌍) × 4자질")
    res = {}
    prep = fit_prep(HAND_X[HAND_TRAIN], HAND_TRAIN)
    P = apply_prep(prep, HAND_X)
    ok_p = bool(np.all(np.abs(P - HAND_P_EXPECT) <= HAND_TOL))
    ok_med = all(close(prep["median"][j], HAND_MEDIAN_EXPECT[j]) for j in range(4))
    imp = {"학습": int(np.isnan(HAND_X[HAND_TRAIN]).sum()),
           "검증": int(np.isnan(HAND_X[HAND_TEST]).sum())}
    ok_imp = imp == HAND_IMPUTE_EXPECT
    say(f"  백분위 변환 32칸 (보간 · 동점 · 범위 밖 자르기 포함): {'일치' if ok_p else '■ 불일치'}")
    if not ok_p:
        say(f"    계산 {P.tolist()}")
    say(f"  원값 중앙값 {prep['median'].tolist()} vs 손 {HAND_MEDIAN_EXPECT}: "
        f"{'일치' if ok_med else '■ 불일치'}")
    say(f"  결측 대치 수 {imp} vs 손 {HAND_IMPUTE_EXPECT}: {'일치' if ok_imp else '■ 불일치'}")
    scores = sigmoid(HAND_B + P @ HAND_W)
    ok_s = all(close(scores[i], HAND_SCORE_EXPECT[i]) for i in range(8))
    say(f"  고정 가중치 점수 8개: {'일치' if ok_s else '■ 불일치'}  "
        f"({', '.join(f'{s:.6f}' for s in scores)})")
    ba_half = balanced_accuracy(*rates_at(scores, HAND_Y, 0.5))
    ok_ba = close(ba_half, HAND_BA_AT_HALF)
    t_fixed, _ = choose_threshold(scores, HAND_Y)
    ok_tf = close(t_fixed, HAND_THRESH_FIXED)
    say(f"  문턱 0.5 균형정확도 {ba_half} vs 손 {HAND_BA_AT_HALF}: {'일치' if ok_ba else '■ 불일치'}")
    say(f"  고정 점수의 문턱 선택 {t_fixed} vs 손 {HAND_THRESH_FIXED}: {'일치' if ok_tf else '■ 불일치'}")
    t, ba = choose_threshold(THR_SCORES, THR_Y)
    met = metrics(THR_SCORES, THR_Y, t)
    got = {"문턱": t, "균형정확도": ba, "봇탐지율": met["봇탐지율"],
           "사람오탐률": met["사람오탐률"], "F1": met["F1"], "AUC": met["AUC"],
           "탐지율@오탐5%": met["탐지율@오탐5%"], "탐지율@오탐10%": met["탐지율@오탐10%"]}
    ok_thr = all(close(got[k], THR_EXPECT[k]) for k in THR_EXPECT)
    say(f"  문턱 선택 예제(겹침) {got}")
    say(f"    손 {THR_EXPECT}: {'일치' if ok_thr else '■ 불일치'}")
    t2, ba2 = choose_threshold(TIE_SCORES, THR_Y)
    ok_tie = close(t2, TIE_EXPECT["문턱"]) and close(ba2, TIE_EXPECT["균형정확도"])
    say(f"  동점 규칙(가장 작은 문턱) {t2}, BA {ba2} vs 손 {TIE_EXPECT}: "
        f"{'일치' if ok_tie else '■ 불일치'}")
    # 쌍 단위 fold 단언도 손 예제에서 한 번 건다.
    units = [(0, 1), (2, 3), (4, 5), (6, 7)]
    fa = make_folds(units, HAND_Y, 2, np.random.default_rng(SEED))
    ok_pair = all(fa[a] == fa[b] for a, b in units)
    say(f"  손 예제 쌍 단위 fold(2겹) 쌍 동일 fold: {'성립' if ok_pair else '■ 깨짐'}")
    ok = all([ok_p, ok_med, ok_imp, ok_s, ok_ba, ok_tf, ok_thr, ok_tie, ok_pair])
    res.update({"백분위": ok_p, "중앙값": ok_med, "대치수": ok_imp, "고정가중치점수": ok_s,
                "균형정확도": ok_ba, "문턱선택_고정점수": ok_tf, "문턱선택_겹침예제": ok_thr,
                "동점규칙": ok_tie, "쌍동일fold": ok_pair, "통과": ok,
                "계산_백분위": P.tolist(), "계산_점수": scores.tolist(),
                "계산_문턱예제": got})
    say(f"  → 손 예제 관문 {'통과' if ok else '■ 실패'}")
    return ok, res


# ════════════════════════════════════════════════════════════════════════
# [관문 1-2] 손 예제(밀도 · 제안)
# ════════════════════════════════════════════════════════════════════════
def gate_hand_density():
    """
    파일 위 주석의 손계산(14 hand_gate의 값)과 대조한다. 본 계산과 같은 density · ranks ·
    rank_mean을 부른다. 동점 5계정 순위 평균도 본다.
    """
    line("[관문 1-2] 손 예제(밀도 · 제안): 6계정 × 2자질, k = 2 · 동점 순위 평균 5계정")
    s, med, p, d = density(DH_X, (DH_K,))
    diag_inf = bool(np.isinf(np.diag(d)).all())
    d0 = d.copy()
    np.fill_diagonal(d0, 0.0)
    got = {"중앙값": med, "백분위": p, "거리": d0, "k번째거리": -s[DH_K],
           "밀도순위": ranks(s[DH_K]), "제안": rank_mean(DH_POS, s[DH_K])}
    want = {"중앙값": np.array(DH_MEDIAN), "백분위": DH_P, "거리": DH_D, "k번째거리": DH_KDIST,
            "밀도순위": DH_DRANK, "제안": DH_PROP}
    ok = {k: bool(np.allclose(got[k], want[k], rtol=0.0, atol=1e-12)) for k in want}
    ok["자기자신_제외(대각 무한)"] = diag_inf
    rk = rank_mean(RK_POS, RK_DENS)
    ok["동점_순위평균"] = all(close(rk[i], RK_EXPECT[i]) for i in range(5))
    for k, v in ok.items():
        say(f"  {k:<18} {'일치' if v else '■ 불일치'}")
    say(f"  k번째 거리 {np.round(-s[DH_K], 12).tolist()} · 제안 {np.round(got['제안'], 12).tolist()} · "
        f"동점 순위 평균 {rk.tolist()}")
    passed = all(ok.values())
    say(f"  → 손 예제(밀도 · 제안) 관문 {'통과' if passed else '■ 실패'}")
    return passed, {"항목": ok, "k": DH_K, "허용오차": 1e-12,
                    "계산": {k: np.asarray(v).tolist() for k, v in got.items()},
                    "계산_동점순위평균": rk.tolist()}


# ════════════════════════════════════════════════════════════════════════
# [관문 2] 입력 정합: 1,024 · 172 · 해시 · 같은 자질
# ════════════════════════════════════════════════════════════════════════
def u_stat(xb, xh):
    """봇 기준 Mann-Whitney U. 평균 순위. FMR과 같은 정의."""
    allv = np.concatenate([xb, xh])
    r = rankdata(allv, method="average")
    return float(r[:xb.size].sum() - xb.size * (xb.size + 1) / 2)


def load_and_gate():
    line("[1/7] 입력 적재 · [관문 2] 입력 정합")
    hashes_before = {os.path.relpath(p, ROOT): sha256_file(p) for p in INPUT_FILES}
    d04 = json.load(open(MEASURE_JSON, encoding="utf-8"))
    d13 = json.load(open(REPARSE_JSON, encoding="utf-8"))["계정"]
    d07 = json.load(open(FEATURE_JSON, encoding="utf-8"))
    corpus = json.load(open(CORPUS_JSON, encoding="utf-8"))
    fmr = json.load(open(FMR_JSON, encoding="utf-8"))
    conf04, acc04 = d04["설정"], d04["계정"]
    fw = corpus["function_words"]
    del corpus
    keys = {"F": list(fw), "M형태": sorted(d07["형태자질"]), "M품사": sorted(d07["UPOS"]),
            "R": list(RKEYS)}
    gate = {}
    gate["블록자질수"] = {b: len(keys[b]) for b in keys}
    ok_sizes = gate["블록자질수"] == BLOCK_SIZES
    h = hashlib.sha256("\n".join(fw).encode("utf-8")).hexdigest()[:16]
    gate["기능어_해시_재계산"] = h
    gate["기능어_해시_04"] = conf04.get("기능어_해시")
    ok_hash = (h == FUNCWORD_HASH == conf04.get("기능어_해시")) and len(fw) == 172
    ok_n = len(acc04) == N_ACCOUNTS_ALL and set(acc04) == set(d13)
    accounts = {u: {**a, "문장길이": d13[u]["문장길이"]} for u, a in acc04.items()}
    del d13
    axis_saved = fmr["설정"]["axis_map_fixed_to_baseline"]
    axis_map = build_axis_map(accounts)
    ok_axis = axis_map == axis_saved
    pairs = [(b, h_, g) for b, h_, g in fmr["설정"]["matching"]["pairs"]]
    ids_m = [u for b, h_, _ in pairs for u in (b, h_)]
    ok_pairs = len(pairs) == N_PAIRS and len(set(ids_m)) == 2 * N_PAIRS
    say(f"  04 계정 {len(acc04):,} · 04-1 같은 집합: {ok_n}")
    say(f"  기능어 {len(fw)}종 · 해시 재계산 {h} · 04 기록 {conf04.get('기능어_해시')} · "
        f"선언 {FUNCWORD_HASH}: {'일치' if ok_hash else '■ 불일치'}")
    say(f"  블록 자질수 {gate['블록자질수']}: {'일치' if ok_sizes else '■ 불일치'} (합 "
        f"{sum(gate['블록자질수'].values())})")
    say(f"  축 지도 재유도 == FMR 고정 축 지도: {ok_axis}")
    say(f"  매칭 쌍 {len(pairs)} · 고유 계정 {len(set(ids_m))}: {ok_pairs}")

    labels_all = json.load(open(ACCOUNTS_JSON, encoding="utf-8")).get("라벨") or {}
    labels = {u: labels_all.get(u) for u in accounts}
    del labels_all
    label_use("01_적격계정.json '라벨' 키 개봉: 쌍 구성 확인과 자질 재현 대조")
    ok_lab = all(labels[b] == GROUP_BOT and labels[h_] == GROUP_HUMAN for b, h_, _ in pairs)
    n_bot = sum(labels[u] == GROUP_BOT for u in ids_m)
    say(f"  쌍마다 (봇, 사람): {ok_lab} · 봇 {n_bot} · 사람 {len(ids_m) - n_bot}")

    feat_names = [(b, k) for b in ("F", "M형태", "M품사", "R") for k in keys[b]]
    X = build_matrix(accounts, ids_m, keys, axis_map)
    y = np.array([1 if labels[u] == GROUP_BOT else 0 for u in ids_m])
    # 같은 자질인가: FMR 분량매칭의 U와 결측 수를 250종 모두 대조
    ref = fmr["통제"]["분량매칭"]
    mism = []
    for j, (b, k) in enumerate(feat_names):
        col = X[:, j]
        xb = col[(y == 1) & ~np.isnan(col)]
        xh = col[(y == 0) & ~np.isnan(col)]
        u = u_stat(xb, xh)
        miss = int(np.isnan(col).sum())
        if u != ref[b][k]["U"] or miss != ref[b][k]["결측"]:
            mism.append({"블록": b, "자질": k, "U": u, "FMR_U": ref[b][k]["U"],
                         "결측": miss, "FMR_결측": ref[b][k]["결측"]})
    ok_repro = not mism
    say(f"  자질 재현: FMR 분량매칭 U · 결측 250종 대조 불일치 {len(mism)}건: "
        f"{'완전 일치' if ok_repro else '■ 불일치'}")
    fmr_meta = {"pairs_sha256": hashlib.sha256(json.dumps(fmr["설정"]["matching"]["pairs"])
                                               .encode()).hexdigest(),
                "matching_seed": fmr["설정"]["matching"]["seed"]}
    del fmr
    ok = all([ok_sizes, ok_hash, ok_n, ok_axis, ok_pairs, ok_lab, ok_repro])
    gate.update({"계정수_04": len(acc04), "04_04-1_같은집합": ok_n, "기능어수": len(fw),
                 "해시일치": ok_hash, "축지도일치": ok_axis, "쌍수": len(pairs),
                 "매칭계정수": len(set(ids_m)), "쌍구성": ok_lab,
                 "자질재현_불일치": mism, "자질재현": ok_repro, "통과": ok, **fmr_meta})
    say(f"  → 입력 정합 관문 {'통과' if ok else '■ 실패'}")
    return ok, gate, {"accounts": accounts, "labels": labels, "keys": keys,
                      "axis_map": axis_map, "pairs": pairs, "ids": ids_m, "X": X,
                      "y": y, "feat_names": feat_names, "fw": fw,
                      "hashes_before": hashes_before}


# ════════════════════════════════════════════════════════════════════════
# [관문 3] 누설 교란 검사: 검증 fold 값을 바꿔도 학습 산물이 같은가
# ════════════════════════════════════════════════════════════════════════
def rf_same(ma, mb):
    """두 랜덤 포레스트의 나무가 구조(분기 자질 · 분기값 · 자식 · 잎 값)까지 같은가."""
    if len(ma.estimators_) != len(mb.estimators_):
        return False
    for ta, tb in zip(ma.estimators_, mb.estimators_):
        a, b = ta.tree_, tb.tree_
        for k in ("feature", "threshold", "children_left", "children_right", "value"):
            if not np.array_equal(getattr(a, k), getattr(b, k)):
                return False
    return True


def gate_leak_perturb(X, y, units):
    line("[관문 3] 누설 교란 검사: 첫 바깥 fold의 검증 원값을 난수로 바꿔 다시 적합")
    outer = make_folds(units, y, N_OUTER, np.random.default_rng(SEED))
    fold_of = np.array([outer[i] for i in range(len(y))])
    va_idx, tr_idx = np.where(fold_of == 0)[0], np.where(fold_of != 0)[0]
    label_use("누설 검사용 재적합(학습 fold 라벨만)")
    a = fold_fit(X, y, tr_idx, units, [SEED, 0])
    Xp = X.copy()
    rng = np.random.default_rng([SEED, 999])
    Xp[va_idx] = rng.normal(size=(va_idx.size, X.shape[1])) * 1e3
    b = fold_fit(Xp, y, tr_idx, units, [SEED, 0])
    same_prep = True
    for j in range(X.shape[1]):
        same_prep &= np.array_equal(a["prep"]["xp"][j], b["prep"]["xp"][j])
        same_prep &= np.array_equal(a["prep"]["fp"][j], b["prep"]["fp"][j])
    same_prep &= np.array_equal(a["prep"]["median"], b["prep"]["median"])
    same_lr = (np.array_equal(a["model"].coef_, b["model"].coef_)
               and np.array_equal(a["model"].intercept_, b["model"].intercept_))
    same_rf = rf_same(a["rf"]["model"], b["rf"]["model"])
    same_thr = all(a["thresholds"][r] == b["thresholds"][r] for r in fold_rows(True))
    detail = {"백분위함수_중앙값": bool(same_prep), "로지스틱_가중치": bool(same_lr),
              "랜덤포레스트_나무구조": bool(same_rf), "문턱_위치·기준선": bool(same_thr)}
    for k, v in detail.items():
        say(f"  {k} 비트 단위 동일: {'성립' if v else '■ 깨짐'}")
    ok = all(detail.values())
    say("  밀도는 라벨이 없는 묶음 안 도구라 검증 fold 값을 쓰는 것이 정의다(누설 개념 없음, D13).")
    detail.update({"쌍동일fold_단언": True, "검증fold_미사용_단언": True, "교란재적합_동일": ok})
    return ok, detail


# ════════════════════════════════════════════════════════════════════════
# [관문 4] 라벨 뒤섞기: 가짜 라벨이면 AUC가 0.5 근처여야 한다
# ════════════════════════════════════════════════════════════════════════
def gate_label_shuffle(X, y, units, dens10):
    line("[관문 4] 라벨 뒤섞기: 시드로 라벨을 섞어 위치(교차검증)와 제안(+ 같은 밀도)을 한 번 돌린다")
    y_sh = np.random.default_rng(SEED).permutation(y)
    kinds = {}
    for u in units:
        k = "".join("봇" if y_sh[i] == 1 else "사람" for i in u)
        kinds[k] = kinds.get(k, 0) + 1
    n_same = int(np.sum(y_sh == y))
    say(f"  뒤섞은 라벨: 봇 {int(y_sh.sum())} · 원래 라벨과 같은 계정 {n_same}/{len(y)} · "
        f"쌍 구성 {kinds}")
    cv = run_cv(X, y_sh, units, SEED, "라벨 뒤섞기(가짜 라벨)", with_base=False, record_detail=False)
    pos_sh = cv["oof"][ROW_POS]
    prop_sh = rank_mean(pos_sh, dens10)
    label_use("라벨 뒤섞기: 가짜 라벨로 AUC")
    auc = {ROW_POS: float(roc_auc_score(y_sh, pos_sh)), ROW_PROP: float(roc_auc_score(y_sh, prop_sh)),
           "참고_밀도": float(roc_auc_score(y_sh, dens10))}
    lo, hi = SHUFFLE_RANGE
    ok = all(lo <= auc[r] <= hi for r in (ROW_POS, ROW_PROP))
    for r, v in auc.items():
        say(f"  {r} AUC {v:.6f} (기대 {lo}~{hi}): {'범위 안' if lo <= v <= hi else '■ 범위 밖'}"
            f"{' (참고, 판정 미사용)' if r.startswith('참고') else ''}")
    say(f"  → 라벨 뒤섞기 관문 {'통과' if ok else '■ 실패'}")
    return ok, {"시드": SEED, "방식": "np.random.default_rng(20260926).permutation(y), 전역 순열, "
                                      "쌍 단위 fold 유지(뒤섞인 라벨의 쌍 구성으로 층화). 제안 = 뒤섞기 위치 OOF와 "
                                      "같은 밀도(라벨 없음)의 순위 평균",
                "AUC": auc, "기대범위": [lo, hi], "통과": ok,
                "원래라벨과_같은계정수": n_same, "쌍구성": kinds}


# ════════════════════════════════════════════════════════════════════════
# [본 계산 부품] 네 도구 평가 · 결정성 요약
# ════════════════════════════════════════════════════════════════════════
def rf_digest(m):
    """랜덤 포레스트 나무 500그루 구조의 sha256(결정성 관문용)."""
    h = hashlib.sha256()
    for t in m.estimators_:
        for k in ("feature", "threshold", "children_left", "children_right", "value"):
            h.update(np.ascontiguousarray(getattr(t.tree_, k)).tobytes())
    return h.hexdigest()


def compute_core(X, y, units, verbose=True):
    """
    [라벨 사용] 교차검증(위치 · 기준선) → 밀도(1,024 묶음, 라벨 없음) → 제안 → 고정 모델.
    결정성 관문이 같은 함수를 한 번 더 부른다.
    """
    cv = run_cv(X, y, units, SEED, "매칭 1,024 교차검증", verbose=verbose)
    dens, dmed, dP, _ = density(X, DENS_KS)
    prop = rank_mean(cv["oof"][ROW_POS], dens[DENS_K])
    if verbose:
        label_use("고정 모델 적합(1,024 전체 라벨)")
    fx = fit_all(X, y, np.arange(len(y)), with_base=True)
    return {"cv": cv, "dens": dens, "dens_median": dmed, "dens_P": dP, "prop": prop, "fx": fx}


def core_digest(core):
    """결정성 관문의 비교 대상: 계정별 점수 · fold 배정 · 문턱 · 계수 · 나무 구조."""
    cv, fx = core["cv"], core["fx"]
    obj = {"fold": cv["fold_of"].tolist(),
           "OOF": {a: [float(v).hex() for v in cv["oof"][a]] for a in cv["oof"]},
           "fold문턱": [info["문턱"] for info in cv["fold_info"]],
           "밀도": {str(k): [float(v).hex() for v in core["dens"][k]] for k in DENS_KS},
           "제안": [float(v).hex() for v in core["prop"]],
           "계수": [float(v).hex() for v in fx["model"].coef_[0]],
           "절편": float(fx["model"].intercept_[0]).hex(),
           "나무": rf_digest(fx["rf"]["model"])}
    return digest(obj)


def evaluate(scores, y, cv, W):
    """
    [라벨 사용] 네 도구(+ 밀도 참고 k)의 AUC · 95% 구간 · 탐지율@오탐, 문턱 지표.
    위치 · 기준선은 OOF(fold 문턱), 밀도 · 제안은 1,024 묶음 위 기술값(낙관적).
    """
    Wb, Wh = W
    bidx, hidx = np.where(y == 1)[0], np.where(y == 0)[0]
    table, dist = {}, {}
    for name, s in scores.items():
        pt, d = auc_boot(s, bidx, hidx, Wb, Wh)
        dist[name] = d
        row = {"AUC": pt, "CI95": ci95(d),
               **{f"탐지율@오탐{int(round(tg * 100))}%": tpr_at_fpr(s, y, tg) for tg in FPR_TARGETS}}
        if name in cv["table"]:
            r = cv["table"][name]
            row.update({"문턱종류": "fold 안 내부 5겹 문턱(OOF)", "OOF": r["OOF"],
                        "fold평균": r["fold평균"], "fold표준편차": r["fold표준편차"]})
        elif name in (ROW_DENS, ROW_PROP):
            t, ba = choose_threshold(s, y)
            m = metrics(s, y, t)
            m["문턱"] = t
            row.update({"문턱종류": "1,024 묶음 위 균형정확도 최대점(기술, 낙관적)", "기술문턱지표": m})
        table[name] = row
    diffs = {"제안-위치": paired_diff(table[ROW_PROP]["AUC"], dist[ROW_PROP], table[ROW_POS]["AUC"], dist[ROW_POS]),
             "밀도-위치": paired_diff(table[ROW_DENS]["AUC"], dist[ROW_DENS], table[ROW_POS]["AUC"], dist[ROW_POS])}
    return table, diffs


def say_table(table, diffs):
    say("\n  네 도구 표 (BotSim 매칭 1,024 · AUC 구간 = 계정 부트스트랩 2,000회)")
    say("  도구         AUC [95%]                    문턱 종류                     BA       탐지     오탐     "
        "탐지@5%  탐지@10%")
    for name, r in table.items():
        m = r.get("OOF") or r.get("기술문턱지표")
        mm = (f"{m['균형정확도']:.4f}   {m['봇탐지율']:.4f}   {m['사람오탐률']:.4f}" if m else
              "  -        -        -   ")
        kind = {"fold 안 내부 5겹 문턱(OOF)": "OOF(fold 문턱)"}.get(r.get("문턱종류"), "기술(낙관적)"
                                                               if r.get("문턱종류") else "참고 k(문턱 없음)")
        say(f"  {name:<10} {r['AUC']:.6f} [{r['CI95'][0]:.4f}, {r['CI95'][1]:.4f}]   {kind:<18} {mm}   "
            f"{r['탐지율@오탐5%']:.4f}   {r['탐지율@오탐10%']:.4f}")
    for k, d in diffs.items():
        say(f"  짝지은 차 {k}: {d['차']:+.6f} [{d['CI95'][0]:+.6f}, {d['CI95'][1]:+.6f}]"
            f"{' (천장 동률)' if d['천장동률'] else ''}")


# ════════════════════════════════════════════════════════════════════════
# [관문 5] 재현: 고정 로지스틱 == 보관 번들
# ════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════
# [예측 대조]
# ════════════════════════════════════════════════════════════════════════
def check_predictions(table, shuf):
    out = []
    a_pos, a_dens, a_prop = table[ROW_POS]["AUC"], table[ROW_DENS]["AUC"], table[ROW_PROP]["AUC"]
    lo, hi = SHUFFLE_RANGE
    conds = {
        "P11-1": (a_pos >= P111_AUC, f"위치 OOF AUC = {a_pos:.6f} (기준 ≥ {P111_AUC})"),
        "P11-2": (a_dens >= P112_AUC, f"밀도 AUC = {a_dens:.6f} (기준 ≥ {P112_AUC})"),
        "P11-3": (a_prop - a_pos >= P113_DIFF,
                  f"제안 {a_prop:.6f} − 위치 {a_pos:.6f} = {a_prop - a_pos:+.6f} (기준 ≥ {P113_DIFF})"),
        "P11-4": (all(lo <= shuf["AUC"][r] <= hi for r in (ROW_POS, ROW_PROP)),
                  f"뒤섞기 AUC 위치 {shuf['AUC'][ROW_POS]:.6f} · 제안 {shuf['AUC'][ROW_PROP]:.6f} (기준 {lo}~{hi})"),
    }
    for p in PREDICTIONS:
        hit, obs = conds[p["번호"]]
        out.append({**p, "판정": "적중" if hit else "빗나감", "관측": obs})
    return out


# ════════════════════════════════════════════════════════════════════════
# [본 계산]
# ════════════════════════════════════════════════════════════════════════
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="11 판별기 (마감판)")
    ap.add_argument("--overwrite", action="store_true", help="이미 있는 산출(.json · _모델.joblib · _출력.log)을 덮어쓴다")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if sys.flags.optimize:
        sys.exit("python -O로는 실행하지 않습니다(assert가 꺼진다). -O 없이 다시 실행하십시오.")
    have = [os.path.basename(p) for p in (OUT_JSON, OUT_MODEL, OUT_LOG) if os.path.exists(p)]
    if have and not args.overwrite:
        sys.exit(f"산출이 이미 있습니다: {have}. 덮어쓰려면 --overwrite를 붙이십시오.")
    for p in INPUT_FILES:
        if not os.path.exists(p):
            sys.exit(f"입력이 없습니다: {p}")
    t0 = time.time()
    started = datetime.now().astimezone().isoformat()
    stage = {}
    RUN.tee = Tee(OUT_LOG + PARTIAL)
    sys.stdout = RUN.tee
    gates = RUN.gates
    say("=" * 74)
    say("11 판별기 (마감판): F·M·R 자질 250개로 계정 하나를 봇/사람으로 가른다  (라벨을 읽는다)")
    say("  도구 넷 = 위치(로지스틱) · 밀도(묶음 안 10번째 이웃 거리) · 제안(순위 1:1 평균) · 기준선(랜덤 포레스트)")
    say("=" * 74)
    say(f"실행 {started} · python {platform.python_version()} · numpy {np.__version__} · "
        f"scikit-learn {sklearn.__version__} · scipy {scipy.__version__} · joblib {joblib.__version__}")
    say("성능 문장은 모두 'BotSim 매칭 표본 안에서'의 값이다.")
    say(f"sys.flags.optimize {sys.flags.optimize} · 단언 {'활성' if __debug__ else '■ 꺼짐'} · "
        f"실행 파일 {sys.executable}")

    t = time.time()
    # 과거 판 소스/모델 대조는 배포 회귀검사로 분리했다.
    pd_res, pd_ok = gate_predecl_text()
    gates["관문0-2_사전선언원문"] = {**pd_res, "통과": pd_ok}
    if not pd_ok:
        stop("예측 문장이 사전선언 원문과 다릅니다.")
    ok_hand, hand = gate_hand()
    gates["관문1_손예제_위치"] = hand
    if not ok_hand:
        stop("손 예제(위치) 관문 실패.")
    ok_hd, hand_d = gate_hand_density()
    gates["관문1-2_손예제_밀도제안"] = {**hand_d, "통과": ok_hd}
    if not ok_hd:
        stop("손 예제(밀도 · 제안) 관문 실패.")
    ok_in, gate_in, D = load_and_gate()
    gates["관문2_입력정합"] = gate_in
    if not ok_in:
        stop("입력 정합 관문 실패.")
    X, y, feat_names, ids = D["X"], D["y"], D["feat_names"], D["ids"]
    idx_of = {u: i for i, u in enumerate(ids)}
    units = [(idx_of[b], idx_of[h]) for b, h, _ in D["pairs"]]
    blocks = np.array([b for b, _ in feat_names])
    check(np.array_equal(blocks, FEATURE_BLOCKS), "열 순서가 블록 순서(FEATURE_BLOCKS)와 다르다")
    miss_per_feat = {f"{b}|{k}": int(np.isnan(X[:, j]).sum())
                     for j, (b, k) in enumerate(feat_names) if np.isnan(X[:, j]).any()}
    miss_block = {b: int(np.isnan(X[:, blocks == b]).sum()) for b in BLOCK_SIZES}
    n_impute = int(np.isnan(X).sum())
    say(f"  결측(=대치 대상) 칸 수 블록별 {miss_block} · 합 {n_impute} · 결측 있는 자질 {len(miss_per_feat)}종")
    stage["관문0~2_입력"] = round(time.time() - t, 2)

    t = time.time()
    ok_leak, leak = gate_leak_perturb(X, y, units)
    gates["관문3_누설교란"] = {**leak, "통과": ok_leak}
    stage["관문3_누설교란"] = round(time.time() - t, 2)
    if not ok_leak:
        stop("누설 교란 검사 실패.")

    line("[2/7] 밀도: 1,024 묶음 전체에서 한 번 (라벨 없음, 겹 없음)")
    t = time.time()
    dens0, _, _, _ = density(X, DENS_KS)
    say(f"  k = {DENS_K} (참고 {', '.join(str(k) for k in DENS_KS if k != DENS_K)}) · 묶음 {len(y):,}계정 · "
        f"밀도 점수 범위 [{dens0[DENS_K].min():.6f}, {dens0[DENS_K].max():.6f}]")
    stage["밀도"] = round(time.time() - t, 2)

    t = time.time()
    ok_shuf, shuf = gate_label_shuffle(X, y, units, dens0[DENS_K])
    gates["관문4_라벨뒤섞기"] = {**shuf, "통과": ok_shuf}
    stage["관문4_라벨뒤섞기"] = round(time.time() - t, 2)
    if not ok_shuf:
        stop("라벨 뒤섞기 관문 실패.")

    line("[3/7] 쌍 단위 5겹 교차검증(위치 · 기준선) · 제안(위치 OOF + 밀도) · 고정 모델")
    t = time.time()
    core = compute_core(X, y, units)
    cv, dens, prop, fx = core["cv"], core["dens"], core["prop"], core["fx"]
    check(all(np.array_equal(dens[k], dens0[k]) for k in DENS_KS), "밀도가 두 번 계산에서 다르다")
    stage["본계산"] = round(time.time() - t, 2)
    label_use("네 도구 평가: AUC · 계정 부트스트랩(봇 · 사람 층) · 문턱 지표")
    bidx, hidx = np.where(y == 1)[0], np.where(y == 0)[0]
    W = (boot_counts(BOOT_KEY["봇"], [0] * len(bidx), N_BOOT), boot_counts(BOOT_KEY["사람"], [0] * len(hidx), N_BOOT))
    scores = {ROW_POS: cv["oof"][ROW_POS], ROW_DENS: dens[DENS_K], ROW_PROP: prop, ROW_BASE: cv["oof"][ROW_BASE],
              **{REF_ROWS[k]: dens[k] for k in REF_ROWS}}
    table, diffs = evaluate(scores, y, cv, W)
    say_table(table, diffs)

    line("[4/7] 고정 모델: 문턱 · 가중치 · [관문 5] 재현")
    t = time.time()
    model, prep, rf = fx["model"], fx["prep"], fx["rf"]["model"]
    label_use("고정 모델 문턱: 위치 = 본 교차검증 OOF, 제안 = 1,024 묶음 제안 점수 (균형정확도 최대점)")
    thr_pos, thr_pos_ba = choose_threshold(cv["oof"][ROW_POS], y)
    thr_prop, thr_prop_ba = choose_threshold(prop, y)
    coef = model.coef_[0]
    say(f"  위치: 반복 {int(model.n_iter_[0])} · 수렴경고 {fx['n_conv']} · 절편 {model.intercept_[0]:.6f}")
    say(f"  문턱 위치 {thr_pos!r} (OOF 균형정확도 {thr_pos_ba:.6f}) · 제안 {thr_prop!r} "
        f"(1,024 묶음 균형정확도 {thr_prop_ba:.6f}, 기술)")
    order = np.argsort(-np.abs(coef), kind="mergesort")
    top20 = [{"순위": r + 1, "블록": feat_names[j][0], "자질": feat_names[j][1], "가중치": float(coef[j])}
             for r, j in enumerate(order[:20])]
    say("  위치 가중치 절댓값 상위 20 (+ 봇 쪽 · − 사람 쪽)")
    for tt in top20:
        say(f"    {tt['순위']:>2}. {tt['블록']:<4} {tt['자질']:<22} {tt['가중치']:+.4f}")
    bundle = {
        "설명": ("11 판별기 마감판 고정 모델. 12-3 · 13은 이 파일만 읽는다(score_bundle 복사본). "
                 "원값 x(feature_order 순서, 결측 NaN) → NaN을 impute_raw_median으로 채움 → 자질 j마다 "
                 "p_j = clip(np.interp(x_j, percentile_xp[j], percentile_fp[j]), 0, 1). "
                 "위치: z = intercept + coef·p, 점수 = 1/(1+exp(−z)). 기준선: rf.predict_proba(p)[:, 1]. "
                 "밀도: 채점 묶음 원값에서 묶음 안 열 중앙값 대치 → 묶음 안 (rankdata(average) − 1)/(n − 1) "
                 "백분위 → 250자질 L1 평균 거리 → 자기 자신을 뺀 density_k번째 가까운 거리의 음수. "
                 "제안: 채점 묶음 안에서 위치 점수와 밀도 점수를 각각 평균 순위(큰 값 = 큰 순위)로 바꿔 "
                 "1:1 평균 r̄, 점수 = (r̄ − 1)/(n − 1). 판정: 점수 ≥ thresholds[도구]이면 봇. 문턱은 BotSim "
                 "내부 기술값이다. 제안 문턱은 묶음 안 정규화 순위 위의 값이라 묶음이 바뀌면 뜻이 달라진다."),
        "feature_order": [[b, k] for b, k in feat_names],
        "percentile_xp": prep["xp"], "percentile_fp": prep["fp"],
        "impute_raw_median": prep["median"],
        "coef": coef.copy(), "intercept": float(model.intercept_[0]),
        "model": model, "lr_params": LR_PARAMS,
        "rf": rf, "rf_params": RF_PARAMS,
        "density_k": DENS_K, "density_ks": list(DENS_KS),
        "density_rule": "묶음 안 np.nanmedian 대치 · 묶음 안 평균 순위 백분위 · cdist(cityblock)/250 · 자기 제외 k번째 거리의 음수",
        "proposal_weights": PROPOSAL_WEIGHTS,
        "proposal_rule": "채점 묶음 안 rankdata(average) 순위의 1:1 평균 r̄ → (r̄ − 1)/(n − 1)",
        "thresholds": {ROW_POS: thr_pos, ROW_PROP: thr_prop},
        "threshold_rule": "score >= threshold → bot",
        "threshold_source": {ROW_POS: "매칭 1,024 쌍 단위 5겹 본 교차검증 OOF 점수의 균형정확도 최대점(동점은 최소)",
                             ROW_PROP: "매칭 1,024 묶음 제안 점수(위치 OOF + 밀도)의 균형정확도 최대점(동점은 최소), 기술값"},
        "feature_rules": {
            "F": "기능어 카운트 ÷ 토큰수_구두점제외, round 6 (05). 기능어는 소문자+아포스트로피 정규화 표면형(04).",
            "M형태": "축 대립값 ≥ 2: 카운트 ÷ 그 계정의 축 내부 합, 대립값 1: ÷ 토큰수_구두점제외 (07). 축 사용 0이면 결측.",
            "M품사": "UPOS 카운트 ÷ 토큰수_구두점제외 (07).",
            "R": "문장당_토큰수 = 토큰수_구두점제외/문장수; 구두점_비율 = (토큰수−토큰수_구두점제외)/토큰수; "
                 "문장길이_변동계수 = 표본표준편차/평균, 문장 5개 미만 결측 (08).",
        },
        "axis_map": D["axis_map"], "function_words": D["fw"], "funcword_hash": FUNCWORD_HASH,
        "train_ids": ids, "seed": SEED,
        "versions": {"numpy": np.__version__, "sklearn": sklearn.__version__,
                     "python": platform.python_version()},
        "created_at": datetime.now().astimezone().isoformat(),
    }
    joblib.dump(bundle, OUT_MODEL + PARTIAL)
    model_sha = sha256_file(OUT_MODEL + PARTIAL)
    # 재적재 검산: 저장본만으로 score_bundle과 손 공식을 다시 내 적합 직후 값과 대조
    # (joblib은 pickle이다. 여기서는 이 스크립트가 방금 쓴 파일만 읽으므로 안전하다)
    bl = joblib.load(OUT_MODEL + PARTIAL)
    sb, Pm = score_bundle(bl, X)
    s_manual = sigmoid(bl["intercept"] + Pm @ bl["coef"])
    s_sk = model.predict_proba(apply_prep(prep, X))[:, 1]
    diff = {"위치_손공식": float(np.max(np.abs(s_manual - s_sk))),
            "위치_score_bundle": float(np.max(np.abs(sb[ROW_POS] - s_sk))),
            "기준선_score_bundle": float(np.max(np.abs(sb[ROW_BASE] - rf.predict_proba(apply_prep(prep, X))[:, 1])))}
    same_dens = all(np.array_equal(sb[ROW_DENS if k == DENS_K else REF_ROWS[k]], dens[k]) for k in DENS_KS)
    same_prop = bool(np.array_equal(sb[ROW_PROP], rank_mean(s_sk, dens[DENS_K])))
    reload_ok = all(v < 1e-12 for v in diff.values()) and same_dens and same_prop
    say(f"  joblib 재적재 → score_bundle · 손 공식 == 적합 직후 (최대차 {diff}, 밀도 동일 {same_dens}, "
        f"제안 동일 {same_prop}): {'성립' if reload_ok else '■ 깨짐'}")
    check(reload_ok, "번들 재적재 검산 실패")
    say(f"  모델 파일 sha256 {model_sha}")
    insample = metrics(s_sk, y, thr_pos)
    stage["고정모델_재현"] = round(time.time() - t, 2)

    line("[5/7] [관문 6] 결정성: 같은 프로세스에서 한 번 더 계산")
    t = time.time()
    dg1 = core_digest(core)
    core2 = compute_core(X, y, units, verbose=False)
    dg2 = core_digest(core2)
    ok_det = dg1 == dg2
    say(f"  결과 digest 1 {dg1}\n  결과 digest 2 {dg2} → {'같음' if ok_det else '■ 다름'}")
    gates["관문6_결정성"] = {"digest": [dg1, dg2], "통과": ok_det}
    stage["관문6_결정성"] = round(time.time() - t, 2)
    if not ok_det:
        stop("같은 프로세스 안 재계산이 비트 단위로 같지 않습니다.")

    line("[6/7] 입력 불변 확인")
    hashes_after = {os.path.relpath(p, ROOT): sha256_file(p) for p in INPUT_FILES}
    ok_same = hashes_after == D["hashes_before"]
    say(f"  입력 {len(INPUT_FILES)}개 sha256 실행 전후 동일: {ok_same}")
    gates["입력불변"] = {"통과": ok_same}
    if not ok_same:
        stop("실행 중 입력 파일이 바뀌었습니다.")

    line("[7/7] 사전 예측 자동 대조 (빗나가도 기록)")
    preds = check_predictions(table, shuf)
    for p in preds:
        say(f"  {p['번호']} [{p['판정']}] {p['서술']}")
        say(f"      관측: {p['관측']}")
    hits = sum(p["판정"] == "적중" for p in preds)
    say(f"  네 예측 중 적중 {hits} · 빗나감 {len(preds) - hits}")

    fold_assign = {ids[i]: int(cv["fold_of"][i]) for i in range(len(ids))}
    results = {
        "관문_요약": {k: bool(v.get("통과")) for k, v in gates.items()},
        "표": table, "짝지은차": diffs,
        "fold배정": {"계정": fold_assign,
                     "쌍": [[b, h, int(cv["fold_of"][idx_of[b]])] for b, h, _ in D["pairs"]]},
        "OOF점수": {name: {ids[i]: float(s[i]) for i in range(len(ids))} for name, s in scores.items()},
        "밀도": {"k": DENS_K, "참고k": [k for k in DENS_KS if k != DENS_K], "묶음": "매칭 1,024 전체(라벨 없음)",
                 "대치중앙값": [fnum(v) for v in core["dens_median"]],
                 "백분위_digest": digest(core["dens_P"].tolist())},
        "라벨뒤섞기": shuf,
        "고정모델": {"파일": os.path.basename(OUT_MODEL),
                     "문턱": {ROW_POS: thr_pos, ROW_PROP: thr_prop},
                     "문턱_균형정확도": {ROW_POS: thr_pos_ba, ROW_PROP: thr_prop_ba},
                     "문턱_주의": "BotSim 내부 기술값. 제안 문턱은 묶음 안 정규화 순위 위의 값이다.",
                     "절편": float(model.intercept_[0]), "반복수": int(model.n_iter_[0]),
                     "수렴경고": fx["n_conv"],
                     "계수": {f"{b}|{k}": float(coef[j]) for j, (b, k) in enumerate(feat_names)},
                     "가중치_상위20": top20,
                     "참고_학습표본내_위치지표(낙관적)": insample,
                     "재적재검산": {"통과": reload_ok, "최대차": diff}},
        "예측대조": preds,
    }
    out = {
        "설정": {
            "실행시각": started,
            "사전선언": "11_판별기_사전선언.md (마감판, 2026-09-27)",
            "사전선언_sha256": sha256_file(PREDECL_MD),
            "시드": SEED, "바깥겹": N_OUTER, "내부겹": N_INNER, "부트스트랩": N_BOOT,
            "로지스틱": LR_PARAMS, "랜덤포레스트": RF_PARAMS, "밀도_k": DENS_K, "밀도_참고k": list(REF_ROWS),
            "제안_비중": list(PROPOSAL_WEIGHTS), "사람오탐_목표": list(FPR_TARGETS), "도구": list(TOOLS),
            "구현결정": IMPLEMENTATION_DECISIONS, "사전예측": PREDICTIONS,
            "버전": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit-learn": sklearn.__version__, "scipy": scipy.__version__,
                     "joblib": joblib.__version__},
            "입력_sha256": D["hashes_before"],
            "스크립트_sha256": sha256_file(SCRIPT_PATH),
            "라벨사용": ("쌍 구성 확인 · 자질 재현 대조 · 로지스틱 · 랜덤 포레스트 학습 · 문턱 선택 · 지표 · 부트스트랩 층 · "
                         "라벨 뒤섞기. 밀도는 라벨을 쓰지 않는다"),
            "방법변경": "최종 판별기는 중심 거리가 아닌 묶음 내 이웃 밀도를 사용한다.",
        },
        "관문": gates,
        "자질": {"순서": [[b, k] for b, k in feat_names],
                 "결측칸수_블록별": miss_block, "결측칸수_자질별": miss_per_feat,
                 "대치수_합계": n_impute,
                 "대치규칙": "위치 · 기준선: 학습 fold 원값 중앙값 → 백분위 변환. 밀도: 묶음 안 열 중앙값"},
        **results,
        "fold별": {"지표": {a: r["fold별"] for a, r in cv["table"].items()}, "fold정보": cv["fold_info"]},
    }
    out["결과_digest"] = digest(jsonable(results))
    out["고정모델"]["파일_sha256"] = model_sha
    out["소요초_단계별"] = stage
    out["소요초"] = round(time.time() - t0, 2)
    out["실행기록"] = {"sys.flags.optimize": int(sys.flags.optimize), "__debug__": bool(__debug__),
                   "시작": started, "끝": datetime.now().astimezone().isoformat(),
                   "python_실행파일": sys.executable}
    write_json(OUT_JSON + PARTIAL, jsonable(out))
    say(f"\n결과_digest {out['결과_digest']}")
    say(f"저장(성공 시 '{PARTIAL}'을 떼어 정본 이름으로 바꾼다): {OUT_JSON}\n      {OUT_MODEL}\n      {OUT_LOG}")
    say(f"단계별 소요초 {stage}")
    say(f"소요 {time.time() - t0:.1f}초")
    sys.stdout.flush()
    RUN.tee.f.close()
    sys.stdout = RUN.tee.out
    for p in (OUT_JSON, OUT_MODEL, OUT_LOG):
        os.replace(p + PARTIAL, p)
    print(f"정본 이름으로 바꿈: {', '.join(os.path.basename(p) for p in (OUT_JSON, OUT_MODEL, OUT_LOG))}")
    return out


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except AssertionError as e:      # check()가 던진 관문 실패. python -O에서도 꺼지지 않는다
        if RUN.tee is None:
            raise
        stop(f"관문(check) 실패: {e}")
    except Exception:
        if RUN.tee is None:
            raise
        stop("예외: " + traceback.format_exc())
