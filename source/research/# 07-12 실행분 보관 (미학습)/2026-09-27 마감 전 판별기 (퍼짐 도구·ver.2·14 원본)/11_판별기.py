#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
11_판별기.py  (v2.1 · 사전선언 11_판별기_사전선언.md v2.1, 2026-09-27)
────────────────────────────────────────────────────────────────────────────
한계 먼저
    · 이 파일의 성능 수치는 전부 "BotSim 매칭 표본 안에서"의 값이다.
      학습 표본은 글 길이를 맞춘 1,024계정(봇 512 · 사람 512)이다. 짧거나
      긴 계정은 캘리퍼 매칭에서 이미 빠져 있다. 단일 모델 · 단일 프레임워크
      자료다. 다른 자료로의 일반화는 12 · 13이 따로 묻는다.
    · 여덟 행(기준선 · 위치 5행 · 퍼짐 · 제안)은 같은 fold 배정으로 돈다. 여덟
      결과는 서로 독립이 아니다. 행 사이의 작은 AUC 차이를 검정 결과처럼 읽지 않는다.
    · 천장 때문에 BotSim 안에서는 도구 사이의 우열과 비중을 판정할 수 없다.
      비중(1:1)은 여기서 고르지 않는다. 비중 선택은 12 사전선언의 규칙으로만 한다.
    · 퍼짐 도구의 중심은 gpt-4o-mini 봇의 중심이다. 다른 모델의 봇이 그 중심에서
      멀면 절대 거리는 옮겨 가지 않는다. 옮겨 갈 수 있는 것은 순위다.
    · 퍼짐 도구는 학습 fold에서 봇 또는 사람의 퍼짐이 0인 자질(대부분 희소 기능어)을
      쓰지 않는다. 남은 자질 위의 거리다(v2.1).
    · 가중치는 자질 사이 상관이 크면 흩어진다. 가중치 순위는 "판별에 쓰였다"의
      약한 증거일 뿐, 자질 하나의 인과적 기여가 아니다.

개정 v2.1 (2026-09-27, v2 실행 뒤)
    v2 정본 실행에서 퍼짐 하한 1e-6이 자질 250개 가운데 봇 114개 · 사람 101개에
    걸렸다. 점수가 ±1만 단위로 커졌고 희소 기능어의 "최빈값(0)을 벗어났는가"가
    점수를 지배했다. v2.1은 학습 fold의 봇 또는 사람에서 퍼짐이 0인 자질을 거리에서
    빼고, 그 수를 fold별 · 블록별로 적는다. 결과를 본 뒤 고친 규칙이다. 그 밖의 논리
    (겹 · 백분위 · 로지스틱 · 기준선 · 순위 평균 · 소거 · 문턱 · 지표 · 라벨 뒤섞기 ·
    예측 P11-1~7)는 v2와 같다. JSON 최상위 "실행기록"에 sys.flags.optimize와 실행
    시각을 적는다.

목적
    사전선언 v2.1을 그대로 구현한다(Q3).
    계정 하나의 F·M·R 자질 250개만으로 봇과 사람을 얼마나 가를 수 있는지,
    어느 층위(F 기능어 · M 형태/품사 · R 리듬)가 기여하는지, 퍼짐(동질성) 도구가
    위치 도구에 무엇을 보태는지를 잰다. 그리고 12 · 13이 읽을 전이용 고정 모델
    한 벌을 저장한다.

도구 넷 (v1은 위치 도구 하나였다. v2가 셋을 더했다)
    · 위치 도구: 로지스틱 회귀. 자질 250개의 가중 합이 봇 쪽으로 얼마나 가
      있는지를 확률로 낸다. 소거 5행(F만 · M만 · R만 · F+M · 전부)도 이 도구다.
    · 퍼짐 도구(중심 거리): 학습 fold의 봇 계정으로 자질별 중앙값(봇 중심 c_b)과
      자질별 중앙절대편차(봇 퍼짐 s_b)를 만든다. 사람도 같다(c_h, s_h).
      봇 또는 사람의 퍼짐이 0인 자질은 뺀다(v2.1). 남은 자질 집합을 K라 한다.
          d_b = K의 자질에 대한 |x_f − c_bf| ÷ s_bf 의 평균   (d_h도 같은 K 위에서)
          점수 = d_h − d_b   (클수록 봇 중심에 더 가깝다)
      10(동질성)의 논리 "봇은 자기 중심에 모이고 사람은 흩어진다"를 계정
      하나의 점수로 옮긴 것이다.
    · 제안: 검증 fold 안에서 위치 확률의 순위와 퍼짐 점수의 순위를 1:1로
      평균한다. 확률(0~1)과 거리 차는 눈금이 달라 그대로 더할 수 없다.
      순위로 바꾸면 둘 다 1~n 눈금이 된다.
    · 기준선: 랜덤 포레스트(나무 500). 표에 한 행으로만 둔다. 설명하지 않는다.

왜 이렇게 하나
    · 백분위 변환: F 사용률은 0~0.2, R 문장당 토큰수는 5~40이다. 눈금을
      0~1로 맞추면 L2 규제가 자질마다 같은 무게로 걸린다. 이상치에도 강하다.
      변환 함수는 학습 fold에서만 만든다. 검증 fold 값이 순위에 끼면 그
      계정의 정보가 학습 쪽 눈금에 새어 들어간다. 퍼짐 · 기준선도 같은 백분위
      값을 입력으로 쓴다. 거리를 자질 사이에서 평균하려면 눈금이 같아야 한다.
    · 쌍 단위 fold: 매칭 쌍의 두 계정은 글 길이가 거의 같다. 한 쌍을
      갈라 학습과 검증에 나누면 "길이가 같은 짝이 반대편에 있다"는 구조가
      검증에 섞인다. 쌍을 통째로 한 fold에 두면 층화도 자동으로 된다.
    · 문턱을 내부 5겹으로 고르는 이유: 검증 fold 점수로 문턱을 고르면
      검증 fold의 라벨이 문턱에 쓰인다. 내부 OOF 점수는 학습 fold 안에서만
      나오므로 검증 fold는 끝까지 한 번도 보지 않은 채로 판정된다. 여덟 행
      모두 같은 규칙이다.
    · 중앙값 · 중앙절대편차: 평균 · 표준편차는 튀는 계정 몇 개에 끌려간다.
      중앙값은 절반 넘는 계정이 움직여야 움직인다. 학습 봇(또는 사람)의 절반
      넘게 같은 값을 가진 자질은 퍼짐이 0이다. v2는 그 자질을 1e-6으로 나눴다.
      그러자 그 자질에서 조금만 벗어나도 거리가 크게 뛰었다. v2.1은 봇 또는 사람의
      퍼짐이 0인 자질을 거리에서 뺀다(사전선언 v2.1). 손 예제 2가 이 제외를 숫자로
      보여 준다.
    · 튜닝 없음 · 자질 선별 없음: C = 1.0, 나무 500 고정. 동질성(10) 결과를 보고
      자질을 빼지 않는다. 같은 라벨로 자질을 고르는 셈이 되기 때문이다.

무엇을 따르나 (사전선언 3절 일곱 단계)
    1. 쌍 단위 5겹. 한 쌍의 두 계정은 같은 fold.
    2. 학습 fold에서 자질별 백분위 변환 함수. 검증 fold는 그 함수에 통과,
       범위 밖은 0 또는 1로 자른다.
    3. [라벨 사용] 위치 도구: 로지스틱 회귀. L2, C = 1.0, 절편, 클래스 가중 없음,
       lbfgs, 최대 반복 1,000.
    4. [라벨 사용] 퍼짐 도구: 학습 fold 봇 · 사람의 중심과 퍼짐. 봇 또는 사람의 퍼짐이
       0인 자질은 거리에서 뺀다(v2.1). 검증 fold 계정은 어느 중심 계산에도 들어가지
       않는다(단언).
    5. [라벨 사용] 기준선: 랜덤 포레스트. 나무 500, random_state 20260926, 나머지 기본값.
    6. 제안과 소거: 검증 fold 안 순위 평균(1:1). 소거 = 위치(전부). 여덟 행 같은 fold.
    7. 문턱 = 학습 fold 안 내부 5겹 점수의 균형정확도 최대점(여덟 행 각자).
       지표 다섯(AUC · 균형정확도 · 봇 탐지율 · 사람 오탐률 · F1)과 보조 둘
       (사람 오탐 5% · 10%에서 봇 탐지율). OOF 값과 fold별 평균 · 표준편차.
    전이용 고정 모델: 1,024 전부로 2~5를 한 번 더. 문턱은 본 교차검증 OOF 점수의
    균형정확도 최대점(v1 규칙). 문턱은 내부 보고용이다.

자가검증 관문 (통과해야 본 계산에 들어간다)
    관문 1    손 예제(위치): 8계정(4쌍) × 4자질 (v1 그대로)
    관문 1-2  손 예제(퍼짐): 6계정(봇 3 · 사람 3) × 3자질, 새 계정 2개, 순위 평균
              (v2.1 제외 규칙으로 상수를 다시 손 계산했다)
    관문 2    입력 정합: 1,024계정 · 기능어 172종 · 해시 · 자질 재현 (v1 그대로)
    관문 3    누설 교란 검사: 검증 fold 값을 바꿔도 학습 산물이 비트 단위로 같은가
    관문 4    라벨 뒤섞기: 가짜 라벨에서 위치(전부) · 제안의 OOF AUC가 0.45~0.55인가

구현 결정 (사전선언이 정하지 않은 자리. JSON 설정.구현결정에 같은 문장을 싣는다)
    아래 IMPLEMENTATION_DECISIONS 상수를 보라. 결과를 보기 전에 적었다.

실행
    python -u 11_판별기.py   (IDLE F5도 된다)
    파이썬: /Users/son/.claude/venvs/audio-transcribe/bin/python
    필요: numpy · scikit-learn · scipy · joblib.
    읽기 전용 입력: 04_기능어측정.json · 04-1_확장재파싱.json · 01_적격계정.json
    ("라벨" 키만) · 07_형태자질비교.json · 09_FMR 통제 재검증/입력코퍼스.json
    · 09_FMR 통제 재검증/FMR_세통제_결과.json. 정본 파일에는 한 글자도 쓰지 않는다.

산출 (이 파일과 같은 폴더에만 쓴다)
    11_판별기.json · 11_판별기_모델.joblib · 11_판별기_출력.log
"""

import hashlib
import json
import math
import os
import platform
import statistics
import sys
import time
import warnings
from datetime import datetime

import joblib
import numpy as np
import scipy
import sklearn
from scipy.stats import rankdata
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve


# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더(단계별 진행경과)를 기준으로 잡는다. v2 정본 실행은 단계
# 폴더 안에서 돌므로 정본 단계 폴더가 곧 HERE다. 산출물은 HERE에만 쓴다.
HERE = os.path.dirname(os.path.abspath(__file__))
STEP = HERE
FMR_DIR = os.path.join(STEP, "09_FMR 통제 재검증")

MEASURE_JSON = os.path.join(STEP, "04_기능어측정.json")        # 04: 원카운트
REPARSE_JSON = os.path.join(STEP, "04-1_확장재파싱.json")      # 04-1: 문장길이
ACCOUNTS_JSON = os.path.join(STEP, "01_적격계정.json")         # 01: "라벨"만
FEATURE_JSON = os.path.join(STEP, "07_형태자질비교.json")      # 07: M 자질 키
CORPUS_JSON = os.path.join(FMR_DIR, "입력코퍼스.json")         # 기능어 172종
FMR_JSON = os.path.join(FMR_DIR, "FMR_세통제_결과.json")       # 쌍 · 축 지도 · U

OUT_JSON = os.path.join(HERE, "11_판별기.json")
OUT_MODEL = os.path.join(HERE, "11_판별기_모델.joblib")
OUT_LOG = os.path.join(HERE, "11_판별기_출력.log")
INPUT_FILES = [MEASURE_JSON, REPARSE_JSON, ACCOUNTS_JSON, FEATURE_JSON,
               CORPUS_JSON, FMR_JSON]

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
# 열 순서(F · M형태 · M품사 · R)대로 블록 이름을 펼친 배열. 퍼짐 제외 자질을 블록별로 센다(v2.1).
FEATURE_BLOCKS = np.repeat(list(BLOCK_SIZES), list(BLOCK_SIZES.values()))
RKEYS = ("문장당_토큰수", "구두점_비율", "문장길이_변동계수")
MIN_SENTENCES_CV = 5          # 08과 같은 값. 문장 5개 미만은 변동계수 결측
RATE_DIGITS = 6               # 05와 같은 값. F 사용률 반올림 자릿수
GROUP_BOT, GROUP_HUMAN = "bot", "human"

# 여덟 행의 이름(사전선언 3절 표). 위치 5행은 로지스틱 소거 실험이다.
# M은 형태자질 58 + 품사 17 = 75종이다(사전선언 2절).
ABLATIONS = {
    "위치(F만)": ("F",),
    "위치(M만)": ("M형태", "M품사"),
    "위치(R만)": ("R",),
    "위치(F+M)": ("F", "M형태", "M품사"),
    "위치(전부)": ("F", "M형태", "M품사", "R"),
}
ROW_BASE = "기준선"             # 랜덤 포레스트, 250
ROW_POS = "위치(전부)"          # 로지스틱, 250 (= 소거: 퍼짐을 뺀 제안)
ROW_SPREAD = "퍼짐(전부)"       # 중심 거리, 250
ROW_PROP = "제안"               # 위치(전부) 순위 + 퍼짐(전부) 순위의 1:1 평균
ROW_BASE_RAW = "기준선(원값)"   # P11-7이 빗나갈 때만 도는 보조 행(사전선언 6절)
ROWS = [ROW_BASE, *ABLATIONS, ROW_SPREAD, ROW_PROP]
EXTRAS_MAIN = (ROW_BASE, ROW_SPREAD, ROW_PROP)   # 위치 5행 밖의 본 행

RF_PARAMS = dict(n_estimators=500, random_state=SEED)   # 나머지는 scikit-learn 기본값
SPREAD_FLOOR = 1e-6             # 남은 자질 K에서 퍼짐이 0일 때의 대체값(v2.1 제외 규칙상 발동하지 않는다)
PROPOSAL_WEIGHTS = (0.5, 0.5)   # 위치 순위 : 퍼짐 순위 = 1:1 고정. BotSim 결과로 바꾸지 않는다
SHUFFLE_RANGE = (0.45, 0.55)    # 라벨 뒤섞기 관문의 OOF AUC 허용 범위
BASELINE_AUC_CUT = 0.98         # P11-7 기준. 빗나가면 기준선(원값) 보조 행을 돈다

# 06·07 머리 10종(사전선언 6절 P11-4). (블록, 키)
HEAD10 = [("F", "we"), ("F", "must"), ("F", "our"), ("F", "was"), ("F", "he"),
          ("M형태", "Tense=Past"), ("M형태", "Number=Sing"),
          ("M형태", "Gender=Neut"), ("M형태", "Gender=Masc"),
          ("M형태", "Gender=Fem")]

IMPLEMENTATION_DECISIONS = [
    "입력 원천: 매칭 1,024계정은 전체 코퍼스 계정이다. 09 FMR의 fmr_controls.py가 "
    "기준선·분량매칭에 쓴 것과 같게 04_기능어측정.json(원카운트)과 04-1_확장재파싱.json"
    "(문장길이)을 읽는다. 제한코퍼스_원카운트.json은 댓글한정·politics한정 제한 "
    "코퍼스(1,436·995계정)의 재파싱 카운트라 전체 코퍼스 자질의 원천이 아니므로 읽지 않는다. "
    "같은 자질임은 관문에서 FMR 분량매칭 250종 U 통계량 완전 일치로 확인한다.",
    "축 지도: M형태 분모 규칙의 축 지도는 FMR_세통제_결과.json 설정.axis_map_fixed_to_baseline"
    "(1,869계정에서 라벨 없이 유도)을 쓰고, 04에서 다시 유도해 같은지 단언한다.",
    "품사 17종의 분모는 07 스크립트 compute_upos_ratios 그대로 토큰수_구두점제외다"
    "(07·10 문서의 '전체 토큰 대비'는 이 규칙을 가리킨다).",
    "백분위 변환 함수: 학습 fold 값(결측 제외 n개)의 평균 순위 r로 p = (r-1)/(n-1)을 "
    "매기고(최솟값 0, 최댓값 1, 동점은 같은 p), 새 값 x는 학습 고유값과 그 p 사이를 "
    "선형 보간한다(np.interp). 범위 밖은 0 또는 1로 자른다. n = 1이거나 모든 값이 같으면 "
    "p = 0.5 상수.",
    "결측 대치 순서: 결측(원값 None)은 그 자질의 학습 fold 원값 중앙값(결측 제외)으로 "
    "먼저 채우고, 그다음 백분위 함수에 통과시킨다. 고정 모델에는 이 원값 중앙값을 저장한다.",
    "로지스틱 회귀: scikit-learn 1.8에서 penalty 인자가 폐기 예정이라 L2를 l1_ratio=0.0으로 "
    "지정한다(C=1.0, fit_intercept=True, class_weight=None, solver='lbfgs', max_iter=1000). "
    "뜻은 사전선언과 같다.",
    "점수와 판정: 점수는 predict_proba의 봇 확률. 점수 ≥ 문턱이면 봇으로 판정한다.",
    "문턱 후보와 동점 규칙: 후보는 내부 OOF 점수의 고유값 전부. 균형정확도 최대가 여럿이면 "
    "그중 가장 작은 점수를 문턱으로 한다.",
    "내부 5겹도 쌍 단위다(학습 fold 쌍을 시드 [20260926, 바깥fold]로 섞어 5등분).",
    "바깥 5겹 배정: 512쌍을 Generator(20260926)로 섞어 np.array_split으로 5등분(103·103·102·102·102쌍).",
    "fold별 표준편차는 5개 값의 표본표준편차(ddof=1).",
    "OOF 지표: 다섯 fold의 검증 점수와 판정(각 fold 자기 문턱)을 모아 한 번에 계산한다. "
    "AUC는 모은 점수로 계산한다.",
    "보조 지표(사람 오탐 5%·10%에서 봇 탐지율): ROC 곡선에서 오탐률 ≤ 목표인 점 가운데 "
    "최대 탐지율을 읽는다. 검증 점수 위에서 읽는 기술 통계이며 배포 가능한 문턱이 아니다.",
    "P11-3은 |AUC(전부) − AUC(F+M)| ≤ 0.02로 판정한다. P11-1~3은 OOF AUC를 쓴다.",
    "P11-4의 '전부 모델 가중치'는 전이용 고정 모델(1,024 전체 학습)의 계수다. fold별 계수의 "
    "머리 10종 포함 수는 참고로만 적는다.",
    "전체 1,869계정 참고 결과: 쌍이 없으므로 계정 단위 층화 5겹(내부도 계정 단위 층화)으로 같은 "
    "파이프라인을 돌린다. 판정에 쓰지 않는다.",
    "누설 검사: fold마다 집합 단언에 더해, 첫 바깥 fold에서 검증 fold 원값을 난수로 바꿔 다시 "
    "적합해도 백분위 함수·중앙값·가중치·문턱이 비트 단위로 같은지 단언한다.",
    "v2 퍼짐 도구 입력: 학습 fold 원값 중앙값으로 결측을 채우고 그 fold의 백분위 함수를 "
    "통과한 값(위치 도구와 같은 입력 P). 중심 = 자질별 np.median, 퍼짐 = 자질별 "
    "median(|x − 중심|)(척도 상수 1.4826을 곱하지 않은 중앙절대편차). 봇 · 사람 따로.",
    "v2.1 퍼짐 제외: 학습 fold의 봇 퍼짐 또는 사람 퍼짐이 정확히 0(== 0.0)인 자질은 d_b와 "
    "d_h 둘 다에서 뺀다(두 거리를 같은 자질 집합 K 위에서 잰다). 제외 수를 바깥 fold마다 · "
    "블록마다(F · M형태 · M품사 · R) 기록하고, 봇만 0 · 사람만 0 · 둘 다 0으로도 나눠 적는다. "
    "고정 모델(1,024 전부)도 같은 규칙이며 K를 불리언 배열(spread.keep)로 저장한다. 하한 1e-6은 "
    "K 안에서 퍼짐이 0인 자질에만 쓰고 발동 수를 기록한다(제외 규칙상 0이어야 한다). 제외된 "
    "자질의 퍼짐 값은 원값(0 포함) 그대로 저장한다. 내부 5겹 적합도 같은 규칙이다. 제외 수 기록은 "
    "바깥 fold(본 계산 · 참고 1,869)와 고정 모델만 한다. K가 비면 중단한다(단언).",
    "v2.1 퍼짐 점수 = d_h − d_b, d = K의 자질에 대한 |x − c| ÷ s 의 산술평균. 판정은 v1과 같이 "
    "점수 ≥ 문턱이면 봇.",
    "v2.1 실행 기록: JSON 최상위 '실행기록'에 sys.flags.optimize, __debug__(단언 활성 여부), "
    "시작 · 끝 시각, 파이썬 실행 파일 경로를 적는다.",
    "v2 제안 점수: 채점 묶음(바깥 검증 fold, 내부 검증 fold, 참고 1,869의 검증 fold) 안에서 "
    "위치(전부) 봇 확률과 퍼짐 점수를 각각 scipy rankdata(method='average')로 순위화한다"
    "(작은 값 1 ~ 큰 값 n, 큰 값 = 봇 쪽). 1:1 평균 r̄, 정규화 (r̄ − 1) ÷ (n − 1). "
    "v1 백분위 정의 p = (r − 1)/(n − 1)과 같은 꼴이며 범위는 [0, 1]이다. 순위를 보존하는 "
    "변환이라 fold 안 AUC는 정규화 전과 같다. OOF 점수는 fold마다 따로 정규화한 값을 모은 것이다.",
    "v2 기준선: sklearn RandomForestClassifier(n_estimators=500, random_state=20260926), "
    "나머지 기본값(n_jobs도 기본). 입력은 위치 도구와 같은 백분위 값 250종. 내부 문턱용 "
    "랜덤 포레스트도 500그루 그대로다. 점수는 predict_proba의 봇 확률.",
    "v2 문턱: 여덟 행 각자 v1 규칙(내부 5겹 OOF 점수의 균형정확도 최대, 동점은 가장 작은 후보). "
    "제안의 내부 점수는 내부 검증 fold마다 따로 순위 평균 · 정규화한 값을 모은 것이다.",
    "v2 라벨 뒤섞기(관문 4): np.random.default_rng(20260926).permutation(y)로 1,024 라벨을 "
    "전역 순열한다. 쌍 단위 fold는 유지하되 층화는 뒤섞인 라벨의 쌍 구성((0,0) · (0,1) · (1,1))으로 "
    "한다. 바깥 fold 시드는 본 계산과 같은 20260926. 위치(전부)와 제안(재료인 퍼짐은 내부에서 "
    "계산)을 본 계산과 같은 부품으로 한 번 돌려 두 OOF AUC만 적는다. 두 값이 모두 [0.45, 0.55] "
    "안이어야 통과이고, 벗어나면 본 계산에 들어가지 않는다.",
    "v2 누설 검사: 집합 단언을 백분위 함수 · 로지스틱 · 중심 · 퍼짐 · 랜덤 포레스트가 본 행으로 "
    "넓힌다. 교란 재적합 비교에 중심 · 퍼짐 배열과 퍼짐 제외 마스크(v2.1), 랜덤 포레스트 나무 500그루의 구조(분기 자질 · "
    "분기값 · 자식 · 잎 값), 여덟 행 문턱을 더한다.",
    "v2 전이용 고정 모델: 1,024 전부로 백분위 함수 · 위치(전부) 로지스틱 · 중심 · 퍼짐 · 랜덤 "
    "포레스트를 적합한다. 문턱은 네 도구(기준선 · 위치(전부) · 퍼짐(전부) · 제안) 각각 본 교차검증 "
    "OOF 점수의 균형정확도 최대점(v1 규칙). 제안 문턱은 fold 안 정규화 점수 위의 값이라 채점 "
    "묶음이 바뀌면 뜻이 달라진다. 문턱은 내부 보고용이며 12 · 13 판정에 쓰지 않는다(사전선언 3절 7).",
    "v2 예측 판정: P11-5는 퍼짐(전부) OOF AUC ≥ 0.95, P11-6은 |AUC(제안) − AUC(위치(전부))| ≤ 0.01, "
    "P11-7은 기준선 OOF AUC ≥ 0.98. P11-1~4의 '전부'는 위치(전부)다. P11-7이 빗나가면 "
    "사전선언대로 '기준선(원값)' 보조 행을 같은 fold · 같은 문턱 규칙으로 한 번 돌린다. 입력은 "
    "학습 fold 원값 중앙값 대치 뒤 원값 그대로(백분위 변환 없음). 보조 행으로 판정을 다시 하지 않는다.",
    "v2 참고 1,869: 여덟 행 모두 같은 파이프라인(계정 단위 층화 5겹)으로 돈다. 판정에 쓰지 않는다.",
]


# ════════════════════════════════════════════════════════════════════════
# [사전 예측] 실행 전에 고정. [6/6]이 자동 대조한다. 빗나가도 지우지 않는다.
# ════════════════════════════════════════════════════════════════════════
PREDICTIONS = [
    {"번호": "P11-1",
     "서술": "위치(전부) OOF AUC가 0.90 이상이다.",
     "근거": "06·07에서 |δ| ≥ 0.147인 자질이 144종이고 머리 자질은 |δ| 0.8~0.94다."},
    {"번호": "P11-2",
     "서술": "F만 AUC와 M만 AUC가 각각 R만 AUC보다 높다.",
     "근거": "R은 3지표뿐이다."},
    {"번호": "P11-3",
     "서술": "위치(전부)와 F+M의 AUC 차이가 0.02 이하다.",
     "근거": "R의 추가 정보가 작다."},
    {"번호": "P11-4",
     "서술": "위치(전부)의 가중치 절댓값 상위 10 자질 가운데 06·07 머리 10종"
             "(we·must·our·was·he·Tense=Past·Number=Sing·Gender=Neut·"
             "Gender=Masc·Gender=Fem)이 5개 이상 든다.",
     "근거": "차이가 큰 자질이 판별에도 쓰일 것이다. 다만 자질 사이 상관이 크면 "
             "가중치가 흩어질 수 있다."},
    {"번호": "P11-5",
     "서술": "퍼짐(전부) OOF AUC가 0.95 이상이다.",
     "근거": "10 논리에서 봇은 자기 중심에 가깝고 사람은 멀다. 계정별 거리 δ가 "
             "옛 09에서 −0.906이었다."},
    {"번호": "P11-6",
     "서술": "제안과 위치(전부)의 OOF AUC 차이가 0.01 이하다.",
     "근거": "BotSim 안에서는 둘 다 천장에 있을 것이다. 이것이 비중을 BotSim에서 "
             "고를 수 없는 이유다."},
    {"번호": "P11-7",
     "서술": "기준선 OOF AUC가 0.98 이상이다.",
     "근거": "같은 자질에 트리를 돌려도 천장일 것이다. 빗나가면 트리 쪽이 백분위 "
             "입력에 약한 것이므로 원값 입력 판을 보조로 낸다."},
]


# ════════════════════════════════════════════════════════════════════════
# [손 예제] 8계정(4쌍) × 4자질. 기대값은 손으로 푼 상수다.
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
# [손 예제 2] 퍼짐(중심 거리)과 순위 평균. 6계정(봇 3 · 사람 3) × 3자질.
# ────────────────────────────────────────────────────────────────────────
# 값은 백분위 변환을 이미 거친 0~1 값이라고 본다(변환은 손 예제 1이 검사한다).
# 1/8 눈금 값만 써서 2진 부동소수로 정확히 표현된다.
#
#              f1      f2      f3
#     B1     .250    .500    .750
#     B2     .500    .625    .875
#     B3     .375    .250    .750
#     H1     .750    .125    .250
#     H2     .500    .375    .500
#     H3    1.000    .250    .000
#
# 손 계산 (v2.1 규칙: 봇 또는 사람의 퍼짐이 0인 자질은 거리에서 뺀다)
#   봇 중심 c_b = 자질별 중앙값
#     f1 {.25 .375 .5} → .375 · f2 {.25 .5 .625} → .5 · f3 {.75 .75 .875} → .75
#   봇 퍼짐 s_b = |x − c_b| 의 중앙값
#     f1 {.125 .125 0} → .125 · f2 {0 .125 .25} → .125
#     f3 {0 .125 0} → 0   ← 봇 퍼짐 0. 이 예제의 "퍼짐 0 자질"이다.
#   사람 중심 c_h: f1 {.5 .75 1} → .75 · f2 {.125 .25 .375} → .25 · f3 {0 .25 .5} → .25
#   사람 퍼짐 s_h: f1 {0 .25 .25} → .25 · f2 {.125 .125 0} → .125
#                  f3 {0 .25 .25} → .25
#   제외: f3은 사람 퍼짐이 .25지만 봇 퍼짐이 0이므로 d_b · d_h 둘 다에서 빠진다.
#     남은 자질 K = {f1, f2}. 제외 합 1 (봇만 0: 1 · 사람만 0: 0 · 둘 다 0: 0).
#     K 안에는 퍼짐 0이 없다 → 하한 1e-6 발동 0 (봇 0 · 사람 0).
#     제외된 f3의 퍼짐은 원값 그대로 저장한다 (봇 0 · 사람 .25).
#
#   새 계정 N1 = (.5, .5, .75)
#     d_b = (|.5−.375|/.125 + |.5−.5|/.125) / 2 = (1 + 0)/2 = 1/2
#     d_h = (|.5−.75|/.25 + |.5−.25|/.125) / 2 = (1 + 2)/2 = 3/2
#     점수 = d_h − d_b = 3/2 − 1/2 = 1   (양수: 봇 중심이 더 가깝다)
#   새 계정 N2 = (.625, .25, .5)
#     d_b = (|.625−.375|/.125 + |.25−.5|/.125) / 2 = (2 + 2)/2 = 2
#     d_h = (|.625−.75|/.25 + |.25−.25|/.125) / 2 = (.5 + 0)/2 = 1/4
#     점수 = 1/4 − 2 = −7/4   (음수: 사람 중심이 더 가깝다)
#   ↳ v2 규칙(f3을 1e-6으로 나눔)에서는 N2가 f3에서 .25 벗어난 것 하나로
#     d_b = (2 + 2 + 250000)/3 = 250004/3, 점수 = −500005/6 이었다. v2.1에서는
#     f3이 빠지므로 N1 · N2의 f3 값을 무엇으로 바꿔도 점수가 같다. 관문이 f3을
#     (0, 1)로 바꿔 점수가 비트 단위로 같은지도 확인한다.
#
#   순위 평균 ①: N1 · N2의 위치 확률을 .3 · .6으로 고정
#     위치 순위 (1, 2) · 퍼짐 점수 (1, −7/4)의 순위 (2, 1)
#     평균 (1.5, 1.5) → (r̄ − 1)/(n − 1) = (.5, .5). 두 도구가 엇갈리면 가운데로 모인다.
#   순위 평균 ②(동점 포함, 퍼짐 규칙과 무관해 v2 그대로): 5계정
#     위치 확률 (.9 .2 .7 .7 .1) → 순위 (5 2 3.5 3.5 1)
#     퍼짐 점수 (1.5 −2 3 0 −2) → 순위 (4 1.5 5 3 1.5)
#     평균 (4.5 1.75 4.25 3.25 1.25) → (r̄ − 1)/4 = (.875 .1875 .8125 .5625 .0625)
# ════════════════════════════════════════════════════════════════════════
HS_X = np.array([
    [0.250, 0.500, 0.750],   # B1
    [0.500, 0.625, 0.875],   # B2
    [0.375, 0.250, 0.750],   # B3
    [0.750, 0.125, 0.250],   # H1
    [0.500, 0.375, 0.500],   # H2
    [1.000, 0.250, 0.000],   # H3
])
HS_Y = np.array([1, 1, 1, 0, 0, 0])
HS_NEW = np.array([
    [0.500, 0.500, 0.750],   # N1
    [0.625, 0.250, 0.500],   # N2
])
HS_CB_EXPECT = [0.375, 0.5, 0.75]
HS_SB_EXPECT = [0.125, 0.125, 0.0]      # f3은 제외 자질이라 하한 없이 원값 0
HS_CH_EXPECT = [0.75, 0.25, 0.25]
HS_SH_EXPECT = [0.25, 0.125, 0.25]
HS_KEEP_EXPECT = [True, True, False]    # 남은 자질 K = {f1, f2}
HS_EXCL_EXPECT = {"합": 1, "봇만0": 1, "사람만0": 0, "둘다0": 0, "남은자질": 2}
HS_FLOORED_EXPECT = {"봇": 0, "사람": 0}   # K 안 하한 발동 수
HS_DB_EXPECT = [1 / 2, 2.0]
HS_DH_EXPECT = [3 / 2, 1 / 4]
HS_SCORE_EXPECT = [1.0, -7 / 4]
HS_NEW_F3_ALT = [0.0, 1.0]              # 제외된 f3을 이 값으로 바꿔도 점수가 같아야 한다
HS_POS = np.array([0.3, 0.6])
HS_RANKMEAN_EXPECT = [0.5, 0.5]
RK_POS = np.array([0.9, 0.2, 0.7, 0.7, 0.1])
RK_SPREAD = np.array([1.5, -2.0, 3.0, 0.0, -2.0])
RK_EXPECT = [0.875, 0.1875, 0.8125, 0.5625, 0.0625]


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


# ════════════════════════════════════════════════════════════════════════
# [1] 자질 계산: 05 · 07 · 08 규칙 복사
# ────────────────────────────────────────────────────────────────────────
# 분모 규칙을 새로 짜지 않는다. 05 compute_rates(F), 07 compute_ratios ·
# compute_upos_ratios(M), 08 compute_features(R)의 나눗셈을 그대로 옮겼다.
# 같은 자로 쟀는지는 [2] 관문에서 FMR 분량매칭 U 250개 완전 일치로 확인한다.
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
# [파이프라인 부품] 백분위 · 대치 · 로지스틱 · 문턱 · 지표
# ════════════════════════════════════════════════════════════════════════
def fit_prep(Xtr, fitted_on):
    """
    학습 행만으로 자질별 백분위 함수와 원값 중앙값을 만든다.

    fitted_on: 이 변환이 본 행의 전역 번호. 누설 단언에 쓴다.
    반환 사전의 xp[j] · fp[j]가 j번 자질의 변환 함수 전부다(12가 그대로 쓴다).
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
# [fold] 단위(쌍 또는 계정) 묶음으로 나눈다. 같은 단위는 언제나 같은 fold.
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
# [v2 도구] 퍼짐(중심 거리) · 제안(순위 평균) · 기준선(랜덤 포레스트)
# ────────────────────────────────────────────────────────────────────────
# 세 도구 모두 입력은 위치 도구와 같은 백분위 값 P다. 자질마다 눈금이 0~1로
# 맞춰져 있어야 "중심에서 얼마나 떨어졌나"를 자질 사이에서 평균할 수 있다.
# ════════════════════════════════════════════════════════════════════════
SPREAD_KEYS = ("center_bot", "spread_bot", "center_human", "spread_human", "keep")


def fit_spread(P, y, fitted_on):
    """
    [라벨 사용] 퍼짐 도구 적합. 학습 행의 백분위 값 P와 라벨 y만 받는다.

    봇 중심 c_b = 봇 계정들의 자질별 중앙값
    봇 퍼짐 s_b = 봇 계정들의 자질별 중앙절대편차 median(|x − c_b|)
    사람도 같다(c_h, s_h).
    v2.1: 봇 또는 사람의 퍼짐이 정확히 0인 자질은 거리에서 뺀다. 남은 자질 집합 K를
    keep(불리언 배열)으로 둔다. 학습 봇(또는 사람)의 절반 넘게 같은 값을 가진 자질이
    여기에 걸린다. v2는 이 자질을 1e-6으로 나눠 점수가 ±1만 단위로 커졌다.
    K 안에서 퍼짐이 0이면 SPREAD_FLOOR(1e-6)로 둔다. 제외 규칙상 이 하한은
    발동하지 않는다. floored에 발동 수를 적어 그것을 확인한다.
    제외된 자질의 퍼짐은 원값(0 포함) 그대로 둔다. 거리 계산에 쓰이지 않는다.

    fitted_on: 중심 · 퍼짐 계산에 들어간 행의 전역 번호. 누설 단언에 쓴다.
    """
    out = {"fitted_on": np.asarray(fitted_on).copy(), "floored": {}}
    raw = {}
    for g, name, tag in ((1, "bot", "봇"), (0, "human", "사람")):
        V = P[y == g]
        assert V.shape[0] > 0, f"학습 행에 {tag} 계정이 없다"
        c = np.median(V, axis=0)
        raw[name] = np.median(np.abs(V - c[None, :]), axis=0)
        out[f"center_{name}"] = c
        out[f"n_{name}"] = int(V.shape[0])
    out["zero_bot"], out["zero_human"] = raw["bot"] == 0, raw["human"] == 0
    keep = ~(out["zero_bot"] | out["zero_human"])
    assert keep.any(), "퍼짐이 0이 아닌 자질이 하나도 없다"
    out["keep"] = keep
    for name, tag in (("bot", "봇"), ("human", "사람")):
        s = raw[name]
        hit = keep & (s == 0)
        out["floored"][tag] = int(np.sum(hit))
        out[f"spread_{name}"] = np.where(hit, SPREAD_FLOOR, s)
    return out


def spread_dist(sp, P):
    """
    계정마다 봇 중심 거리 d_b와 사람 중심 거리 d_h.
    남은 자질 K(sp["keep"]) 위 자질별 표준화 거리의 산술평균(v2.1).
    """
    k = sp["keep"]
    Pk = P[:, k]
    d_b = np.mean(np.abs(Pk - sp["center_bot"][k][None, :]) / sp["spread_bot"][k][None, :], axis=1)
    d_h = np.mean(np.abs(Pk - sp["center_human"][k][None, :]) / sp["spread_human"][k][None, :],
                  axis=1)
    return d_b, d_h


def spread_exclusion(sp, blocks=None):
    """
    v2.1 퍼짐 제외 기록. 제외 합 · (blocks를 주면) 블록별 · 봇만 0 · 사람만 0 · 둘 다 0 ·
    남은 자질 수 · 하한 발동 수. blocks는 열마다 블록 이름(FEATURE_BLOCKS).
    """
    keep, zb, zh = sp["keep"], sp["zero_bot"], sp["zero_human"]
    exc = ~keep
    out = {"합": int(exc.sum())}
    if blocks is not None:
        assert len(blocks) == len(keep), "블록 배열 길이가 자질 수와 다르다"
        out["블록별"] = {b: int(exc[blocks == b].sum()) for b in BLOCK_SIZES}
    out.update({"봇만0": int(np.sum(zb & ~zh)), "사람만0": int(np.sum(zh & ~zb)),
                "둘다0": int(np.sum(zb & zh)), "남은자질": int(keep.sum()),
                "하한발동": dict(sp["floored"])})
    return out


def spread_score(sp, P):
    """퍼짐 점수 = d_h − d_b. 클수록 봇 중심에 더 가깝다(봇 쪽)."""
    d_b, d_h = spread_dist(sp, P)
    return d_h - d_b


def rank_mean(s_pos, s_spread):
    """
    제안 점수. 채점 묶음(검증 fold) 안에서만 순위를 매긴다.
        순위: 작은 값 1 ~ 큰 값 n (큰 값 = 봇 쪽), 동점은 평균 순위
        r̄ = 위치 순위 × 0.5 + 퍼짐 순위 × 0.5   (비중 1:1 고정)
        점수 = (r̄ − 1) ÷ (n − 1)   → [0, 1]. v1 백분위 p = (r − 1)/(n − 1)과 같은 꼴.
    순위로 바꾸는 이유: 확률(0~1)과 거리 차는 눈금이 달라 그대로 더할 수 없다.
    """
    n = len(s_pos)
    assert n == len(s_spread) and n >= 2
    w_pos, w_spr = PROPOSAL_WEIGHTS
    r = w_pos * rankdata(s_pos, method="average") + w_spr * rankdata(s_spread, method="average")
    return (r - 1.0) / (n - 1.0)


def impute_raw(prep, X):
    """결측만 학습 fold 원값 중앙값으로 채운 원값. 기준선(원값) 보조 행에만 쓴다."""
    return np.where(np.isnan(X), prep["median"][None, :], X)


def fit_rf(Z, y, fitted_on):
    """[라벨 사용] 기준선 랜덤 포레스트. 나무 500, random_state 고정, 나머지 기본값. 튜닝 없음."""
    m = RandomForestClassifier(**RF_PARAMS).fit(Z, y)
    return {"model": m, "fitted_on": np.asarray(fitted_on).copy()}


def row_list(abl_cols, extras):
    """이번에 낼 행 이름을 표 순서(ROWS, 보조 행은 맨 뒤)대로 늘어놓는다."""
    return [r for r in ROWS + [ROW_BASE_RAW] if r in abl_cols or r in extras]


def fit_all(X, y, rows, abl_cols, extras):
    """
    [라벨 사용] 학습 행 rows만으로 도구 전부를 적합한다.
        · 백분위 함수(라벨 없음) → 학습 행의 백분위 값 P
        · 위치: 소거 행마다 로지스틱
        · 퍼짐: 봇 · 사람 중심과 퍼짐 (제안만 켜도 재료로 필요하다)
        · 기준선: 랜덤 포레스트(백분위 입력) · 기준선(원값): 랜덤 포레스트(대치 원값 입력)
    rows 밖의 행은 한 줄도 만지지 않는다(X[rows], y[rows]만 쓴다).
    """
    rows = np.asarray(rows)
    Xr, yr = X[rows], y[rows]
    prep = fit_prep(Xr, rows)
    P = apply_prep(prep, Xr)
    fit = {"prep": prep, "models": {}, "spread": None, "rf": {}, "n_conv": 0}
    for a, cols in abl_cols.items():
        m, c = fit_lr(P[:, cols], yr)
        fit["n_conv"] += c
        fit["models"][a] = m
    if ROW_SPREAD in extras or ROW_PROP in extras:
        fit["spread"] = fit_spread(P, yr, rows)
    if ROW_BASE in extras:
        fit["rf"][ROW_BASE] = fit_rf(P, yr, rows)
    if ROW_BASE_RAW in extras:
        fit["rf"][ROW_BASE_RAW] = fit_rf(impute_raw(prep, Xr), yr, rows)
    return fit


def score_all(fit, Xs, abl_cols, extras):
    """
    적합이 끝난 도구로 채점 묶음 Xs(원값)를 채점한다. 라벨은 받지 않는다.
    제안은 이 묶음 안에서 순위를 매긴다. 그래서 채점 묶음은 언제나 fold 하나다.
    """
    P = apply_prep(fit["prep"], Xs)
    s = {}
    if ROW_BASE in extras:
        s[ROW_BASE] = fit["rf"][ROW_BASE]["model"].predict_proba(P)[:, 1]
    for a, cols in abl_cols.items():
        s[a] = fit["models"][a].predict_proba(P[:, cols])[:, 1]
    if fit["spread"] is not None:
        sp_score = spread_score(fit["spread"], P)
        if ROW_SPREAD in extras:
            s[ROW_SPREAD] = sp_score
    if ROW_PROP in extras:
        assert ROW_POS in abl_cols, "제안에는 위치(전부)가 필요하다"
        s[ROW_PROP] = rank_mean(s[ROW_POS], sp_score)
    if ROW_BASE_RAW in extras:
        s[ROW_BASE_RAW] = fit["rf"][ROW_BASE_RAW]["model"].predict_proba(
            impute_raw(fit["prep"], Xs))[:, 1]
    return s


def fold_fit(X, y, tr_idx, units, abl_cols, inner_seed, extras=EXTRAS_MAIN):
    """
    바깥 학습 fold 하나로 할 일 전부: 내부 5겹 점수 → 행마다 문턱, 그리고 학습 fold
    전체로 백분위 함수 · 로지스틱 가중치 · 중심 · 퍼짐 · 랜덤 포레스트.

    이 함수는 tr_idx 밖의 행을 받지 않는다(X[tr_idx]만 만진다). 누설 단언은
    아래에서 집합으로 한 번 더 건다. 제안의 내부 점수는 내부 검증 fold마다
    따로 순위를 매겨 정규화한 값이다(바깥 검증 fold와 같은 규칙).
    """
    tr_set = set(int(i) for i in tr_idx)
    tr_units = [u for u in units if all(int(i) in tr_set for i in u)]
    assert sum(len(u) for u in tr_units) == len(tr_idx), "단위가 fold 경계를 넘는다"
    inner = make_folds(tr_units, y, N_INNER, np.random.default_rng(inner_seed))
    pos_of = {int(i): p for p, i in enumerate(tr_idx)}
    rows = row_list(abl_cols, extras)
    inner_scores = {a: np.full(len(tr_idx), NAN) for a in rows}
    n_conv = 0
    for f in range(N_INNER):
        iva = np.array([i for i in tr_idx if inner[int(i)] == f])
        itr = np.array([i for i in tr_idx if inner[int(i)] != f])
        assert set(iva.tolist()) <= tr_set and set(itr.tolist()) <= tr_set
        assert not (set(iva.tolist()) & set(itr.tolist()))
        fit_in = fit_all(X, y, itr, abl_cols, extras)
        n_conv += fit_in["n_conv"]
        s_in = score_all(fit_in, X[iva], abl_cols, extras)
        where = [pos_of[int(i)] for i in iva]
        for a in rows:
            inner_scores[a][where] = s_in[a]
    thresholds = {}
    for a in rows:
        assert not np.isnan(inner_scores[a]).any()
        thresholds[a] = choose_threshold(inner_scores[a], y[tr_idx])
    fit = fit_all(X, y, tr_idx, abl_cols, extras)
    fit.update({"thresholds": thresholds, "inner_scores": inner_scores,
                "n_conv": n_conv + fit["n_conv"]})
    return fit


def run_cv(X, y, units, abl_cols, seed, label_note, ids=None, record_detail=True,
           extras=EXTRAS_MAIN):
    """
    바깥 5겹. 반환: 행별 OOF 지표 · fold별 지표 · 문턱 · 배정 · OOF 점수.
    행 = 위치 소거 행(abl_cols) + extras(기준선 · 퍼짐(전부) · 제안 · 보조 행).
    제안의 OOF 점수는 fold마다 따로 정규화한 순위 평균을 모은 것이다.
    """
    n = len(y)
    outer = make_folds(units, y, N_OUTER, np.random.default_rng(seed))
    fold_of = np.array([outer[i] for i in range(n)])
    # 누설 단언 ①: 단위(쌍)의 모든 계정은 같은 fold
    for u in units:
        assert len({outer[int(i)] for i in u}) == 1, "쌍이 fold를 가로지른다"
    rows = row_list(abl_cols, extras)
    oof = {a: np.full(n, NAN) for a in rows}
    oof_pred = {a: np.zeros(n, dtype=bool) for a in rows}
    per_fold = {a: [] for a in rows}
    fold_info = []
    label_use(f"{label_note}: 로지스틱 · 중심 거리 · 랜덤 포레스트 학습 · 내부 OOF 문턱 선택 · "
              "검증 지표 계산")
    for f in range(N_OUTER):
        va_idx = np.where(fold_of == f)[0]
        tr_idx = np.where(fold_of != f)[0]
        fit = fold_fit(X, y, tr_idx, units, abl_cols, [seed, f], extras)
        va_set, tr_set = set(va_idx.tolist()), set(tr_idx.tolist())
        # 누설 단언 ②: 백분위 함수 · 중심 · 퍼짐 · 랜덤 포레스트가 본 행 ∩ 검증 fold = ∅
        seen = set(fit["prep"]["fitted_on"].tolist())
        assert not (seen & va_set), "검증 fold가 백분위 함수에 쓰였다"
        assert seen == tr_set
        if fit["spread"] is not None:
            seen_sp = set(fit["spread"]["fitted_on"].tolist())
            assert not (seen_sp & va_set), "검증 fold 계정이 중심 · 퍼짐 계산에 들어갔다"
            assert seen_sp == tr_set
            assert fit["spread"]["n_bot"] + fit["spread"]["n_human"] == len(tr_idx)
        for r_name, rf in fit["rf"].items():
            seen_rf = set(rf["fitted_on"].tolist())
            assert not (seen_rf & va_set), f"검증 fold가 {r_name} 학습에 쓰였다"
            assert seen_rf == tr_set
        for a, m in fit["models"].items():
            assert m.n_features_in_ == len(abl_cols[a])
        assert all(len(s) == len(tr_idx) for s in fit["inner_scores"].values()), \
            "문턱용 점수에 학습 fold 밖 계정이 섞였다"
        s_va = score_all(fit, X[va_idx], abl_cols, extras)
        info = {"fold": f, "학습n": int(len(tr_idx)), "검증n": int(len(va_idx)),
                "검증_봇": int(y[va_idx].sum()), "수렴경고": int(fit["n_conv"]),
                "검증_결측대치수": int(np.isnan(X[va_idx]).sum()),
                "학습_결측대치수": int(np.isnan(X[tr_idx]).sum()),
                "문턱": {}, "내부OOF_균형정확도": {}, "반복수": {}}
        if fit["spread"] is not None:
            info["퍼짐_제외자질"] = spread_exclusion(fit["spread"], FEATURE_BLOCKS)
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
            if a in fit["models"]:
                info["반복수"][a] = int(fit["models"][a].n_iter_[0])
        if record_detail and ROW_POS in fit["models"]:
            info["위치(전부)_계수"] = [float(c) for c in fit["models"][ROW_POS].coef_[0]]
            info["위치(전부)_절편"] = float(fit["models"][ROW_POS].intercept_[0])
        fold_info.append(info)
        say(f"    fold {f}: 학습 {len(tr_idx)} · 검증 {len(va_idx)} · AUC "
            + " · ".join(f"{a} {per_fold[a][-1]['AUC']:.4f}" for a in rows))
        if "퍼짐_제외자질" in info:
            ex = info["퍼짐_제외자질"]
            say(f"      퍼짐 제외 자질 {ex['합']} ("
                + " · ".join(f"{b} {n}" for b, n in ex["블록별"].items())
                + f") · 남은 {ex['남은자질']} · 하한 발동 {ex['하한발동']}")
    table = {}
    for a in rows:
        assert not np.isnan(oof[a]).any()
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
        n_feat = len(abl_cols[a]) if a in abl_cols else int(X.shape[1])
        table[a] = {"자질수": n_feat, "OOF": row_oof,
                    "fold평균": fold_mean, "fold표준편차": fold_sd,
                    "fold별": per_fold[a]}
    return {"table": table, "fold_of": fold_of, "fold_info": fold_info,
            "oof": oof, "oof_pred": oof_pred}


def say_table(table, title):
    """여덟 행 표를 로그에 찍는다. 위치(전부)는 소거 행이기도 하다."""
    say(f"\n  {title} (OOF; 괄호는 fold 평균 ± 표준편차)")
    say("  행                 n    AUC              균형정확도        봇탐지율  사람오탐률  "
        "F1      탐지@5%  탐지@10%")
    for a, r in table.items():
        name = a + (" =소거" if a == ROW_POS else "")
        o, m, s = r["OOF"], r["fold평균"], r["fold표준편차"]
        say(f"  {name:<13} {r['자질수']:>4}  {o['AUC']:.4f}({m['AUC']:.3f}±{s['AUC']:.3f})  "
            f"{o['균형정확도']:.4f}({m['균형정확도']:.3f}±{s['균형정확도']:.3f})  "
            f"{o['봇탐지율']:.4f}   {o['사람오탐률']:.4f}     {o['F1']:.4f}  "
            f"{o['탐지율@오탐5%']:.4f}   {o['탐지율@오탐10%']:.4f}")


# ════════════════════════════════════════════════════════════════════════
# [관문 1] 손 예제
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
# [관문 1-2] 손 예제(퍼짐) · 순위 평균
# ════════════════════════════════════════════════════════════════════════
def rclose(a, b, tol=HAND_TOL):
    """상대 허용오차 비교. 1e-6으로 나눈 25만 단위 값은 절대오차로는 못 잰다."""
    return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))


def gate_hand_spread():
    line("[관문 1-2] 손 예제(퍼짐, v2.1 제외 규칙): 6계정(봇 3 · 사람 3) × 3자질, 새 계정 2개, "
         "순위 평균")
    sp = fit_spread(HS_X, HS_Y, np.arange(6))
    ok_cb = all(close(sp["center_bot"][j], HS_CB_EXPECT[j]) for j in range(3))
    ok_sb = all(close(sp["spread_bot"][j], HS_SB_EXPECT[j]) for j in range(3))
    ok_ch = all(close(sp["center_human"][j], HS_CH_EXPECT[j]) for j in range(3))
    ok_sh = all(close(sp["spread_human"][j], HS_SH_EXPECT[j]) for j in range(3))
    ok_keep = sp["keep"].tolist() == HS_KEEP_EXPECT
    ex = spread_exclusion(sp)
    ok_ex = all(ex[k] == v for k, v in HS_EXCL_EXPECT.items())
    ok_fl = sp["floored"] == HS_FLOORED_EXPECT
    ok_n = (sp["n_bot"] == 3 and sp["n_human"] == 3
            and sp["fitted_on"].tolist() == list(range(6)))
    say(f"  봇 중심 {sp['center_bot'].tolist()} vs 손 {HS_CB_EXPECT}: {'일치' if ok_cb else '■ 불일치'}")
    say(f"  봇 퍼짐 {sp['spread_bot'].tolist()} vs 손 {HS_SB_EXPECT}: {'일치' if ok_sb else '■ 불일치'}")
    say(f"  사람 중심 {sp['center_human'].tolist()} vs 손 {HS_CH_EXPECT}: "
        f"{'일치' if ok_ch else '■ 불일치'}")
    say(f"  사람 퍼짐 {sp['spread_human'].tolist()} vs 손 {HS_SH_EXPECT}: "
        f"{'일치' if ok_sh else '■ 불일치'}")
    say(f"  남은 자질 K {sp['keep'].tolist()} vs 손 {HS_KEEP_EXPECT}: {'일치' if ok_keep else '■ 불일치'}")
    say(f"  제외 수 { {k: ex[k] for k in HS_EXCL_EXPECT} } vs 손 {HS_EXCL_EXPECT}: "
        f"{'일치' if ok_ex else '■ 불일치'}")
    say(f"  하한 발동 수 {sp['floored']} vs 손 {HS_FLOORED_EXPECT}: {'일치' if ok_fl else '■ 불일치'}")
    say(f"  적합에 든 행 봇 {sp['n_bot']} · 사람 {sp['n_human']}: {'성립' if ok_n else '■ 깨짐'}")
    d_b, d_h = spread_dist(sp, HS_NEW)
    sc = spread_score(sp, HS_NEW)
    ok_db = all(rclose(d_b[i], HS_DB_EXPECT[i]) for i in range(2))
    ok_dh = all(rclose(d_h[i], HS_DH_EXPECT[i]) for i in range(2))
    ok_sc = all(rclose(sc[i], HS_SCORE_EXPECT[i]) for i in range(2))
    say(f"  새 계정 d_b {d_b.tolist()} vs 손 {HS_DB_EXPECT}: {'일치' if ok_db else '■ 불일치'}")
    say(f"  새 계정 d_h {d_h.tolist()} vs 손 {HS_DH_EXPECT}: {'일치' if ok_dh else '■ 불일치'}")
    say(f"  새 계정 점수 {sc.tolist()} vs 손 {HS_SCORE_EXPECT}: {'일치' if ok_sc else '■ 불일치'}")
    alt = HS_NEW.copy()
    alt[:, 2] = HS_NEW_F3_ALT
    sc_alt = spread_score(sp, alt)
    ok_inv = bool(np.array_equal(sc_alt, sc))
    say(f"  제외된 f3을 {HS_NEW_F3_ALT}로 바꾼 점수 {sc_alt.tolist()} == 원래 점수: "
        f"{'성립' if ok_inv else '■ 깨짐'}")
    rm = rank_mean(HS_POS, sc)
    ok_rm = all(close(rm[i], HS_RANKMEAN_EXPECT[i]) for i in range(2))
    say(f"  순위 평균 ①(두 도구 엇갈림) {rm.tolist()} vs 손 {HS_RANKMEAN_EXPECT}: "
        f"{'일치' if ok_rm else '■ 불일치'}")
    rk = rank_mean(RK_POS, RK_SPREAD)
    ok_rk = all(close(rk[i], RK_EXPECT[i]) for i in range(5))
    say(f"  순위 평균 ②(동점 포함) {rk.tolist()} vs 손 {RK_EXPECT}: {'일치' if ok_rk else '■ 불일치'}")
    ok = all([ok_cb, ok_sb, ok_ch, ok_sh, ok_keep, ok_ex, ok_fl, ok_n, ok_db, ok_dh, ok_sc,
              ok_inv, ok_rm, ok_rk])
    res = {"봇중심": ok_cb, "봇퍼짐": ok_sb, "사람중심": ok_ch, "사람퍼짐": ok_sh,
           "남은자질": ok_keep, "제외수": ok_ex, "하한발동수": ok_fl, "적합행": ok_n,
           "d_b": ok_db, "d_h": ok_dh, "점수": ok_sc, "제외자질_값바꿔도_점수불변": ok_inv,
           "순위평균_엇갈림": ok_rm, "순위평균_동점": ok_rk, "통과": ok,
           "계산_제외": ex, "계산_d_b": d_b.tolist(), "계산_d_h": d_h.tolist(),
           "계산_점수": sc.tolist(), "계산_순위평균": rm.tolist(), "계산_순위평균_동점": rk.tolist()}
    say(f"  → 손 예제(퍼짐) 관문 {'통과' if ok else '■ 실패'}")
    return ok, res


# ════════════════════════════════════════════════════════════════════════
# [관문 2] 입력 정합: 1,024 · 172 · 해시 · 같은 자질
# ════════════════════════════════════════════════════════════════════════
def u_stat(xb, xh):
    """봇 기준 Mann-Whitney U. 평균 순위. FMR과 같은 정의."""
    allv = np.concatenate([xb, xh])
    r = rankdata(allv, method="average")
    return float(r[:xb.size].sum() - xb.size * (xb.size + 1) / 2)


def load_and_gate():
    line("[1/6] 입력 적재 · [관문 2] 입력 정합")
    for p in INPUT_FILES:
        if not os.path.exists(p):
            say(f"  {p} 이(가) 없습니다. 아무것도 하지 않고 끝냅니다.")
            sys.exit(1)
    hashes_before = {os.path.relpath(p, STEP): sha256_file(p) for p in INPUT_FILES}
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
    ok_head = all(k in keys[b] for b, k in HEAD10)
    say(f"  04 계정 {len(acc04):,} · 04-1 같은 집합: {ok_n}")
    say(f"  기능어 {len(fw)}종 · 해시 재계산 {h} · 04 기록 {conf04.get('기능어_해시')} · "
        f"선언 {FUNCWORD_HASH}: {'일치' if ok_hash else '■ 불일치'}")
    say(f"  블록 자질수 {gate['블록자질수']}: {'일치' if ok_sizes else '■ 불일치'} (합 "
        f"{sum(gate['블록자질수'].values())})")
    say(f"  축 지도 재유도 == FMR 고정 축 지도: {ok_axis}")
    say(f"  매칭 쌍 {len(pairs)} · 고유 계정 {len(set(ids_m))}: {ok_pairs}")
    say(f"  머리 10종 키 존재: {ok_head}")

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
    ok = all([ok_sizes, ok_hash, ok_n, ok_axis, ok_pairs, ok_head, ok_lab, ok_repro])
    gate.update({"계정수_04": len(acc04), "04_04-1_같은집합": ok_n, "기능어수": len(fw),
                 "해시일치": ok_hash, "축지도일치": ok_axis, "쌍수": len(pairs),
                 "매칭계정수": len(set(ids_m)), "쌍구성": ok_lab, "머리10존재": ok_head,
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


def gate_leak_perturb(X, y, units, abl_cols):
    line("[관문 3] 누설 교란 검사: 첫 바깥 fold의 검증 원값을 난수로 바꿔 다시 적합")
    outer = make_folds(units, y, N_OUTER, np.random.default_rng(SEED))
    fold_of = np.array([outer[i] for i in range(len(y))])
    va_idx, tr_idx = np.where(fold_of == 0)[0], np.where(fold_of != 0)[0]
    label_use("누설 검사용 재적합(학습 fold 라벨만)")
    a = fold_fit(X, y, tr_idx, units, abl_cols, [SEED, 0])
    Xp = X.copy()
    rng = np.random.default_rng([SEED, 999])
    Xp[va_idx] = rng.normal(size=(va_idx.size, X.shape[1])) * 1e3
    b = fold_fit(Xp, y, tr_idx, units, abl_cols, [SEED, 0])
    same_prep = True
    for j in range(X.shape[1]):
        same_prep &= np.array_equal(a["prep"]["xp"][j], b["prep"]["xp"][j])
        same_prep &= np.array_equal(a["prep"]["fp"][j], b["prep"]["fp"][j])
    same_prep &= np.array_equal(a["prep"]["median"], b["prep"]["median"])
    same_lr = True
    for k in abl_cols:
        same_lr &= np.array_equal(a["models"][k].coef_, b["models"][k].coef_)
        same_lr &= np.array_equal(a["models"][k].intercept_, b["models"][k].intercept_)
    same_sp = all(np.array_equal(a["spread"][k], b["spread"][k]) for k in SPREAD_KEYS)
    same_rf = rf_same(a["rf"][ROW_BASE]["model"], b["rf"][ROW_BASE]["model"])
    same_thr = (set(a["thresholds"]) == set(ROWS)
                and all(a["thresholds"][r] == b["thresholds"][r] for r in ROWS))
    detail = {"백분위함수_중앙값": bool(same_prep), "로지스틱_가중치": bool(same_lr),
              "중심_퍼짐": bool(same_sp), "랜덤포레스트_나무구조": bool(same_rf),
              "문턱_여덟행": bool(same_thr)}
    for k, v in detail.items():
        say(f"  {k} 비트 단위 동일: {'성립' if v else '■ 깨짐'}")
    ok = all(detail.values())
    detail.update({"쌍동일fold_단언": True, "검증fold_미사용_단언": True, "교란재적합_동일": ok})
    return ok, detail


# ════════════════════════════════════════════════════════════════════════
# [관문 4] 라벨 뒤섞기: 가짜 라벨이면 AUC가 0.5 근처여야 한다
# ────────────────────────────────────────────────────────────────────────
# 라벨을 뒤섞으면 자질과 라벨 사이의 관계가 끊긴다. 그래도 AUC가 0.5에서 멀면
# 파이프라인 어딘가에서 검증 fold의 라벨이 새고 있다는 뜻이다.
# ════════════════════════════════════════════════════════════════════════
def gate_label_shuffle(X, y, units, abl_cols):
    line("[관문 4] 라벨 뒤섞기: 시드로 라벨을 섞어 위치(전부)와 제안을 한 번 돌린다")
    y_sh = np.random.default_rng(SEED).permutation(y)
    kinds = {}
    for u in units:
        k = "".join("봇" if y_sh[i] == 1 else "사람" for i in u)
        kinds[k] = kinds.get(k, 0) + 1
    n_same = int(np.sum(y_sh == y))
    say(f"  뒤섞은 라벨: 봇 {int(y_sh.sum())} · 원래 라벨과 같은 계정 {n_same}/{len(y)} · "
        f"쌍 구성 {kinds}")
    cols = {ROW_POS: abl_cols[ROW_POS]}
    cv = run_cv(X, y_sh, units, cols, SEED, "라벨 뒤섞기(가짜 라벨)", record_detail=False,
                extras=(ROW_PROP,))
    auc = {r: cv["table"][r]["OOF"]["AUC"] for r in (ROW_POS, ROW_PROP)}
    lo, hi = SHUFFLE_RANGE
    ok = all(lo <= v <= hi for v in auc.values())
    for r, v in auc.items():
        say(f"  {r} OOF AUC {v:.6f} (기대 {lo}~{hi}): {'범위 안' if lo <= v <= hi else '■ 범위 밖'}")
    say(f"  → 라벨 뒤섞기 관문 {'통과' if ok else '■ 실패'}")
    res = {"시드": SEED, "방식": "np.random.default_rng(20260926).permutation(y), 전역 순열, "
                                  "쌍 단위 fold 유지(뒤섞인 라벨의 쌍 구성으로 층화)",
           "OOF_AUC": auc, "기대범위": [lo, hi], "통과": ok,
           "원래라벨과_같은계정수": n_same, "쌍구성": kinds}
    return ok, res


# ════════════════════════════════════════════════════════════════════════
# [예측 대조]
# ════════════════════════════════════════════════════════════════════════
def check_predictions(table, top10_keys):
    auc = {a: table[a]["OOF"]["AUC"] for a in table}
    heads = set(HEAD10)
    n_head = sum(1 for k in top10_keys if k in heads)
    res = []
    for p in PREDICTIONS:
        num = p["번호"]
        if num == "P11-1":
            hit = auc[ROW_POS] >= 0.90
            obs = f"위치(전부) OOF AUC = {auc[ROW_POS]:.6f} (기준 ≥ 0.90)"
        elif num == "P11-2":
            f_, m_, r_ = auc["위치(F만)"], auc["위치(M만)"], auc["위치(R만)"]
            hit = f_ > r_ and m_ > r_
            obs = f"F만 {f_:.6f} · M만 {m_:.6f} · R만 {r_:.6f}"
        elif num == "P11-3":
            d = abs(auc[ROW_POS] - auc["위치(F+M)"])
            hit = d <= 0.02
            obs = (f"|위치(전부) {auc[ROW_POS]:.6f} − F+M {auc['위치(F+M)']:.6f}| = {d:.6f} "
                   f"(기준 ≤ 0.02)")
        elif num == "P11-4":
            hit = n_head >= 5
            obs = (f"상위 10 중 머리 10종 {n_head}개: "
                   + ", ".join(f"{b}:{k}" for b, k in top10_keys if (b, k) in heads))
        elif num == "P11-5":
            hit = auc[ROW_SPREAD] >= 0.95
            obs = f"퍼짐(전부) OOF AUC = {auc[ROW_SPREAD]:.6f} (기준 ≥ 0.95)"
        elif num == "P11-6":
            d = abs(auc[ROW_PROP] - auc[ROW_POS])
            hit = d <= 0.01
            obs = (f"|제안 {auc[ROW_PROP]:.6f} − 위치(전부) {auc[ROW_POS]:.6f}| = {d:.6f} "
                   f"(기준 ≤ 0.01)")
        else:
            hit = auc[ROW_BASE] >= BASELINE_AUC_CUT
            obs = f"기준선 OOF AUC = {auc[ROW_BASE]:.6f} (기준 ≥ {BASELINE_AUC_CUT})"
        res.append({**p, "판정": "적중" if hit else "빗나감", "관측": obs})
    return res


# ════════════════════════════════════════════════════════════════════════
# [본 계산]
# ════════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    started = datetime.now().astimezone().isoformat()
    stage_sec = {}
    sys.stdout = Tee(OUT_LOG)
    say("=" * 74)
    say("11 판별기 v2.1: F·M·R 자질 250개로 계정 하나를 봇/사람으로 가른다  (라벨을 읽는다)")
    say("  여덟 행 = 기준선(랜덤 포레스트) · 위치 5행(로지스틱 소거) · 퍼짐(중심 거리) · "
        "제안(순위 1:1 평균)")
    say("=" * 74)
    say(f"실행 {started} · python {platform.python_version()} · "
        f"numpy {np.__version__} · scikit-learn {sklearn.__version__} · scipy {scipy.__version__}")
    say("성능 문장은 모두 'BotSim 매칭 표본 안에서'의 값이다.")
    say(f"sys.flags.optimize {sys.flags.optimize} · 단언 {'활성' if __debug__ else '■ 꺼짐'} · "
        f"실행 파일 {sys.executable}")

    ok_hand, hand = gate_hand()
    if not ok_hand:
        say("■ 중단: 손 예제(위치) 관문 실패. 본 계산에 들어가지 않는다.")
        sys.exit(2)
    ok_hand_sp, hand_sp = gate_hand_spread()
    if not ok_hand_sp:
        say("■ 중단: 손 예제(퍼짐) 관문 실패. 본 계산에 들어가지 않는다.")
        sys.exit(2)
    ok_in, gate_in, D = load_and_gate()
    if not ok_in:
        say("■ 중단: 입력 정합 관문 실패. 본 계산에 들어가지 않는다.")
        write_json(OUT_JSON, {"중단": "입력 정합 관문 실패", "관문": gate_in})
        sys.exit(3)
    X, y, feat_names, ids = D["X"], D["y"], D["feat_names"], D["ids"]
    idx_of = {u: i for i, u in enumerate(ids)}
    units = [(idx_of[b], idx_of[h]) for b, h, _ in D["pairs"]]
    blocks = np.array([b for b, _ in feat_names])
    assert np.array_equal(blocks, FEATURE_BLOCKS), "열 순서가 블록 순서(FEATURE_BLOCKS)와 다르다"
    abl_cols = {a: np.where(np.isin(blocks, bl))[0] for a, bl in ABLATIONS.items()}
    say("  위치 소거 입력 자질수: " + " · ".join(f"{a} {len(c)}" for a, c in abl_cols.items()))
    miss_per_feat = {f"{b}|{k}": int(np.isnan(X[:, j]).sum())
                     for j, (b, k) in enumerate(feat_names) if np.isnan(X[:, j]).any()}
    miss_block = {b: int(np.isnan(X[:, blocks == b]).sum()) for b in BLOCK_SIZES}
    n_impute = int(np.isnan(X).sum())
    say(f"  결측(=대치 대상) 칸 수 블록별 {miss_block} · 합 {n_impute} · "
        f"결측 있는 자질 {len(miss_per_feat)}종")
    stage_sec["관문1~2_입력"] = round(time.time() - t0, 2)

    t = time.time()
    ok_leak, leak = gate_leak_perturb(X, y, units, abl_cols)
    stage_sec["관문3_누설교란"] = round(time.time() - t, 2)
    if not ok_leak:
        say("■ 중단: 누설 교란 검사 실패.")
        sys.exit(4)

    t = time.time()
    ok_shuf, shuf = gate_label_shuffle(X, y, units, abl_cols)
    stage_sec["관문4_라벨뒤섞기"] = round(time.time() - t, 2)
    if not ok_shuf:
        say("■ 중단: 라벨 뒤섞기 관문 실패. 본 계산에 들어가지 않는다.")
        write_json(OUT_JSON, {"중단": "라벨 뒤섞기 관문 실패", "라벨뒤섞기": shuf,
                              "관문": {"손예제": hand, "손예제_퍼짐": hand_sp,
                                       "입력정합": gate_in, "누설": leak}})
        sys.exit(5)

    line("[2/6] 쌍 단위 5겹 교차검증 · 여덟 행 (같은 fold 배정)")
    t = time.time()
    cv = run_cv(X, y, units, abl_cols, SEED, "매칭 1,024 교차검증")
    stage_sec["본계산_교차검증"] = round(time.time() - t, 2)
    table = cv["table"]
    say_table(table, "여덟 행 표")

    # P11-7이 빗나가면 사전선언 6절대로 원값 입력 판을 같은 fold로 한 번 더 낸다.
    aux = None
    auc_base = table[ROW_BASE]["OOF"]["AUC"]
    if auc_base < BASELINE_AUC_CUT:
        say(f"\n  기준선 OOF AUC {auc_base:.6f} < {BASELINE_AUC_CUT}: 보조 행 '{ROW_BASE_RAW}'을 "
            "같은 fold로 돌린다(판정은 다시 하지 않는다).")
        t = time.time()
        cv_raw = run_cv(X, y, units, {}, SEED, "보조 기준선(원값)", record_detail=False,
                        extras=(ROW_BASE_RAW,))
        stage_sec["보조_기준선원값"] = round(time.time() - t, 2)
        assert np.array_equal(cv_raw["fold_of"], cv["fold_of"]), "보조 행의 fold가 본 계산과 다르다"
        say_table(cv_raw["table"], "보조 행")
        aux = {a: {"자질수": r["자질수"], "OOF": r["OOF"], "fold평균": r["fold평균"],
                   "fold표준편차": r["fold표준편차"]} for a, r in cv_raw["table"].items()}
    else:
        say(f"\n  기준선 OOF AUC {auc_base:.6f} ≥ {BASELINE_AUC_CUT}: 보조 행을 돌리지 않는다.")

    line("[3/6] 전이용 고정 모델: 1,024 전체로 백분위 · 가중치 · 중심 · 퍼짐 · 랜덤 포레스트")
    t = time.time()
    all_idx = np.arange(len(y))
    label_use("고정 모델 적합(1,024 전체) · 본 교차검증 OOF 점수로 문턱 선택")
    fx = fit_all(X, y, all_idx, {ROW_POS: abl_cols[ROW_POS]}, EXTRAS_MAIN)
    prep, model, n_conv = fx["prep"], fx["models"][ROW_POS], fx["n_conv"]
    sp, rf = fx["spread"], fx["rf"][ROW_BASE]["model"]
    P = apply_prep(prep, X)
    thr_rows = (ROW_BASE, ROW_POS, ROW_SPREAD, ROW_PROP)
    thr_all = {r: choose_threshold(cv["oof"][r], y) for r in thr_rows}
    thr, thr_ba = thr_all[ROW_POS]
    coef = model.coef_[0]
    say(f"  위치(전부): 반복 {int(model.n_iter_[0])} · 수렴경고 {n_conv} · "
        f"절편 {model.intercept_[0]:.6f}")
    sp_ex = spread_exclusion(sp, FEATURE_BLOCKS)
    excl_names = [f"{b}|{k}" for j, (b, k) in enumerate(feat_names) if not sp["keep"][j]]
    say(f"  퍼짐: 제외 자질 {sp_ex['합']} (블록별 {sp_ex['블록별']} · 봇만0 {sp_ex['봇만0']} · "
        f"사람만0 {sp_ex['사람만0']} · 둘다0 {sp_ex['둘다0']}) · 남은 {sp_ex['남은자질']} · "
        f"하한 발동 {sp_ex['하한발동']}")
    for r in thr_rows:
        say(f"  문턱 {r}: {thr_all[r][0]:.6g} (본 교차검증 OOF 균형정확도 {thr_all[r][1]:.6f})")
    order = np.argsort(-np.abs(coef), kind="mergesort")
    top20 = [{"순위": r + 1, "블록": feat_names[j][0], "자질": feat_names[j][1],
              "가중치": float(coef[j]), "머리10": feat_names[j] in set(HEAD10)}
             for r, j in enumerate(order[:20])]
    say("  위치(전부) 가중치 절댓값 상위 20 (+ 봇 쪽 · − 사람 쪽)")
    for tt in top20:
        say(f"    {tt['순위']:>2}. {tt['블록']:<4} {tt['자질']:<22} {tt['가중치']:+.4f}"
            f"{'  ← 머리10' if tt['머리10'] else ''}")
    top10_keys = [(tt["블록"], tt["자질"]) for tt in top20[:10]]
    fold_head = []
    for info in cv["fold_info"]:
        c = np.array(info["위치(전부)_계수"])
        o = np.argsort(-np.abs(c), kind="mergesort")[:10]
        fold_head.append(sum(feat_names[j] in set(HEAD10) for j in o))
    say(f"  참고: fold별 위치(전부) 상위 10의 머리 10종 수 {fold_head}")

    bundle = {
        "설명": ("11 판별기 v2.1 전이용 고정 모델. 12 · 13은 이 파일만 읽는다. "
                 "공통 전처리: 원값 x(feature_order 순서, 결측 NaN) → NaN을 impute_raw_median으로 "
                 "채움 → 자질 j마다 p_j = clip(np.interp(x_j, percentile_xp[j], percentile_fp[j]), 0, 1). "
                 "위치: z = intercept + coef·p, 점수 = 1/(1+exp(−z)). "
                 "퍼짐(v2.1): K = spread['keep']가 참인 자질, d_b = mean_{j∈K} |p_j − center_bot_j| "
                 "/ spread_bot_j, d_h도 같은 K 위에서, 점수 = d_h − d_b. "
                 "기준선: rf.predict_proba(p)[:, 1]. "
                 "제안: 채점 묶음 안에서 위치 점수와 퍼짐 점수를 각각 평균 순위(큰 값 = 큰 순위)로 "
                 "바꿔 1:1 평균 r̄, 점수 = (r̄ − 1)/(n − 1). "
                 "판정: 점수 ≥ thresholds[행] 이면 봇. 문턱은 BotSim 내부 보고용이며 12 · 13 판정에 "
                 "쓰지 않는다(사전선언 3절 7)."),
        "feature_order": [[b, k] for b, k in feat_names],
        "percentile_xp": prep["xp"], "percentile_fp": prep["fp"],
        "impute_raw_median": prep["median"],
        "coef": coef.copy(), "intercept": float(model.intercept_[0]),
        "threshold": thr, "threshold_rule": "score >= threshold → bot",
        "threshold_source": "매칭 1,024 쌍 단위 5겹 본 교차검증 OOF 점수의 균형정확도 최대점(동점은 최소)",
        "thresholds": {r: thr_all[r][0] for r in thr_rows},
        "model": model, "lr_params": LR_PARAMS,
        "spread": {k: sp[k].copy() for k in SPREAD_KEYS},
        "spread_floor": SPREAD_FLOOR, "spread_floored": dict(sp["floored"]),
        "spread_excluded": sp_ex, "spread_excluded_features": excl_names,
        "spread_rule": ("v2.1: 1,024 학습 표본의 봇 또는 사람 중앙절대편차가 0인 자질은 거리에서 "
                        "제외(keep=False). 남은 자질에서 퍼짐이 0이면 spread_floor로 둔다"
                        "(발동 수 spread_floored)."),
        "rf": rf, "rf_params": RF_PARAMS,
        "proposal_weights": PROPOSAL_WEIGHTS,
        "proposal_rule": "채점 묶음 안 rankdata(average) 순위의 가중 평균 r̄ → (r̄ − 1)/(n − 1)",
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
    assert os.path.dirname(OUT_MODEL) == HERE
    joblib.dump(bundle, OUT_MODEL)
    model_sha = sha256_file(OUT_MODEL)
    # 재적재 검산: 저장본만으로 손 공식 점수를 다시 내 적합 직후 점수와 대조
    # (joblib은 pickle이다. 여기서는 이 스크립트가 방금 쓴 파일만 읽으므로 안전하다)
    bl = joblib.load(OUT_MODEL)
    Xf = np.where(np.isnan(X), bl["impute_raw_median"][None, :], X)
    Pm = np.column_stack([np.clip(np.interp(Xf[:, j], bl["percentile_xp"][j],
                                            bl["percentile_fp"][j]), 0, 1)
                          for j in range(X.shape[1])])
    s_manual = sigmoid(bl["intercept"] + Pm @ bl["coef"])
    s_sk = model.predict_proba(P)[:, 1]
    bs = bl["spread"]
    kk = bs["keep"]
    sp_manual = (np.mean(np.abs(Pm[:, kk] - bs["center_human"][kk]) / bs["spread_human"][kk], axis=1)
                 - np.mean(np.abs(Pm[:, kk] - bs["center_bot"][kk]) / bs["spread_bot"][kk], axis=1))
    sp_fit = spread_score(sp, P)
    rf_reload = bl["rf"].predict_proba(Pm)[:, 1]
    rf_fit = rf.predict_proba(P)[:, 1]
    diff = {"위치": float(np.max(np.abs(s_manual - s_sk))),
            "퍼짐": float(np.max(np.abs(sp_manual - sp_fit) / np.maximum(1.0, np.abs(sp_fit)))),
            "기준선": float(np.max(np.abs(rf_reload - rf_fit)))}
    reload_ok = all(v < 1e-12 for v in diff.values())
    say(f"  joblib 재적재 → 손 공식 점수 == 적합 직후 점수 (최대차 {diff}): "
        f"{'성립' if reload_ok else '■ 깨짐'}")
    assert reload_ok
    say(f"  모델 파일 sha256 {model_sha}")
    insample = metrics(s_sk, y, thr)
    stage_sec["고정모델"] = round(time.time() - t, 2)

    line("[4/6] 참고: 전체 1,869계정 (계정 단위 층화 5겹, 여덟 행, 판정에 쓰지 않음)")
    t = time.time()
    ids_all = sorted(D["accounts"])
    X_all = build_matrix(D["accounts"], ids_all, D["keys"], D["axis_map"])
    label_use("참고 1,869: 라벨로 층화 · 학습 · 지표")
    y_all = np.array([1 if D["labels"][u] == GROUP_BOT else 0 for u in ids_all])
    units_all = [(i,) for i in range(len(ids_all))]
    cv_all = run_cv(X_all, y_all, units_all, abl_cols, SEED + 1869, "참고 1,869 교차검증",
                    record_detail=False)
    ref_table = {a: {"자질수": r["자질수"], "OOF": r["OOF"], "fold평균": r["fold평균"],
                     "fold표준편차": r["fold표준편차"]} for a, r in cv_all["table"].items()}
    for a, r in ref_table.items():
        say(f"  {a:<8} OOF AUC {r['OOF']['AUC']:.4f} · 균형정확도 {r['OOF']['균형정확도']:.4f}")
    stage_sec["참고_1869"] = round(time.time() - t, 2)

    line("[5/6] 입력 불변 확인")
    hashes_after = {os.path.relpath(p, STEP): sha256_file(p) for p in INPUT_FILES}
    ok_same = hashes_after == D["hashes_before"]
    say(f"  입력 6개 sha256 실행 전후 동일: {ok_same}")
    assert ok_same

    line("[6/6] 사전 예측 자동 대조 (빗나가도 기록)")
    preds = check_predictions(table, top10_keys)
    for p in preds:
        say(f"  {p['번호']} [{p['판정']}] {p['서술']}")
        say(f"      관측: {p['관측']}")
    hits = sum(p["판정"] == "적중" for p in preds)
    say(f"  일곱 예측 중 적중 {hits} · 빗나감 {len(preds) - hits}")

    fold_assign = {ids[i]: int(cv["fold_of"][i]) for i in range(len(ids))}
    decl = os.path.join(HERE, "11_판별기_사전선언.md")
    out = {
        "설정": {
            "실행시각": datetime.now().astimezone().isoformat(),
            "사전선언": "11_판별기_사전선언.md (v2.1, 2026-09-27)",
            "사전선언_sha256": sha256_file(decl) if os.path.exists(decl) else None,
            "시드": SEED, "바깥겹": N_OUTER, "내부겹": N_INNER,
            "로지스틱": LR_PARAMS, "랜덤포레스트": RF_PARAMS,
            "퍼짐_하한": SPREAD_FLOOR, "제안_비중": list(PROPOSAL_WEIGHTS),
            "퍼짐_제외규칙": ("v2.1: 학습 fold의 봇 또는 사람 중앙절대편차가 0인 자질은 d_b · d_h "
                              "둘 다에서 제외. 남은 자질의 퍼짐 0은 하한으로 대체(발동 수 기록)."),
            "사람오탐_목표": list(FPR_TARGETS),
            "행": ROWS,
            "소거": {a: list(bl_) for a, bl_ in ABLATIONS.items()},
            "머리10": [[b, k] for b, k in HEAD10],
            "구현결정": IMPLEMENTATION_DECISIONS,
            "버전": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit-learn": sklearn.__version__, "scipy": scipy.__version__,
                     "joblib": joblib.__version__},
            "입력_sha256": D["hashes_before"],
            "스크립트_sha256": sha256_file(os.path.abspath(__file__)),
            "라벨사용": ("로지스틱 · 중심 거리 · 랜덤 포레스트 학습 · 문턱 선택 · 지표 계산 · 쌍 구성 확인 · "
                         "자질 재현 대조 · 라벨 뒤섞기 · 참고 1,869 층화"),
        },
        "관문": {"손예제": hand, "손예제_퍼짐": hand_sp, "입력정합": gate_in,
                 "누설": leak, "라벨뒤섞기_통과": ok_shuf,
                 "고정모델_재적재검산": {"통과": reload_ok, "최대차": diff}},
        "라벨뒤섞기": shuf,
        "퍼짐_제외자질": {
            "설명": ("v2.1 규칙으로 퍼짐 도구 거리에서 뺀 자질 수. 합 · 블록별 · 봇만0 · 사람만0 · "
                     "둘다0 · 남은자질 · 하한발동(남은 자질 안에서 1e-6 대체 수)."),
            "본교차검증_fold별": [info["퍼짐_제외자질"] for info in cv["fold_info"]],
            "고정모델": sp_ex,
            "고정모델_제외자질_목록": excl_names,
            "참고1869_fold별": [info["퍼짐_제외자질"] for info in cv_all["fold_info"]],
        },
        "자질": {"순서": [[b, k] for b, k in feat_names],
                 "결측칸수_블록별": miss_block, "결측칸수_자질별": miss_per_feat,
                 "대치수_합계": n_impute,
                 "대치규칙": "학습 fold 원값 중앙값(결측 제외) → 백분위 변환"},
        "fold배정": {"계정": fold_assign,
                     "쌍": [[b, h, int(cv["fold_of"][idx_of[b]])] for b, h, _ in D["pairs"]]},
        "여덟행표": {a: {"자질수": r["자질수"], "OOF": r["OOF"], "fold평균": r["fold평균"],
                        "fold표준편차": r["fold표준편차"]} for a, r in table.items()},
        "fold별": {"지표": {a: r["fold별"] for a, r in table.items()},
                   "fold정보": cv["fold_info"]},
        "OOF점수": {a: {ids[i]: float(cv["oof"][a][i]) for i in range(len(ids))} for a in table},
        "보조_기준선원값": aux,
        "고정모델": {"파일": os.path.basename(OUT_MODEL), "파일_sha256": model_sha,
                     "문턱": {r: thr_all[r][0] for r in thr_rows},
                     "문턱_본교차검증OOF_균형정확도": {r: thr_all[r][1] for r in thr_rows},
                     "문턱_주의": "BotSim 내부 보고용. 12 · 13 판정에 쓰지 않는다. 제안 문턱은 fold 안 "
                                 "정규화 점수 위의 값이다.",
                     "절편": float(model.intercept_[0]), "반복수": int(model.n_iter_[0]),
                     "수렴경고": n_conv,
                     "계수": {f"{b}|{k}": float(coef[j]) for j, (b, k) in enumerate(feat_names)},
                     "가중치_상위20": top20,
                     "참고_fold별_상위10_머리10수": fold_head,
                     "참고_학습표본내_지표(낙관적)": insample,
                     "퍼짐": {"퍼짐_제외자질": sp_ex,
                              **{k: [float(v) for v in sp[k]] for k in SPREAD_KEYS if k != "keep"},
                              "keep": [bool(v) for v in sp["keep"]]},
                     "대치수_자질별": miss_per_feat},
        "참고_전체1869": {"표본": {"봇": int(y_all.sum()), "사람": int(len(y_all) - y_all.sum())},
                        "여덟행표": ref_table,
                        "fold정보": cv_all["fold_info"]},
        "예측대조": preds,
        "소요초_단계별": stage_sec,
        "소요초": round(time.time() - t0, 2),
        "실행기록": {"sys.flags.optimize": int(sys.flags.optimize), "__debug__": bool(__debug__),
                     "시작": started, "끝": datetime.now().astimezone().isoformat(),
                     "python_실행파일": sys.executable},
    }
    write_json(OUT_JSON, out)
    say(f"\n저장: {OUT_JSON}\n      {OUT_MODEL}\n      {OUT_LOG}")
    say(f"단계별 소요초 {stage_sec}")
    say(f"소요 {time.time() - t0:.1f}초")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
