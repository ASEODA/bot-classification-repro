#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
12-3_판별기ver2.py  (12 사전선언 뼈대 v3.2 5절 4~7항 · 9항 민감도 · 7절 P12-3~P12-5)
────────────────────────────────────────────────────────────────────────────
한계 먼저
    · 이 파일의 AUC는 전부 "BotSim 공개 코드를 재구성한 댓글 생성 조건, 댓글 한정
      계정, Reddit 2023~24 사람 고정" 안의 값이다. 모델 일반화·환경 전이를 말하지 않는다.
    · 시험 쪽 칸 하나는 설계상 약 61~65 페르소나다. AUC 구간이 넓다. 칸 사이의
      작은 차이를 검정 결과처럼 읽지 않는다.
    · ver.1은 BotSim 매칭 1,024계정(전체 글)으로 학습한 고정 모델이다. 댓글 한정
      계정에 적용하면 자료 종류(전체 글 → 댓글)와 모델(gpt-4o-mini → 새 모델)이
      함께 바뀐다. 대조 행(gpt-4o-mini 재생성 댓글로 학습)이 그 둘을 가르는 장치다.
    · 문턱은 기술 보고만 한다. 판정은 AUC와 부트스트랩 구간으로만 한다.
    · 민감도(5절 9항)는 12-1이 민감도 계정(또는 문서별 측정치 · 본문)을 저장해야 돈다.
      없거나 대조가 어긋나면 "실행불가"로 적고 본 분석은 그대로 끝낸다.
    · 기준 행의 ver.1 AUC가 13-0 자료에서 이미 1.0이라 P12-3은 사실상 "칸의 95% 하한 > 0.95"다.
      P12-5는 천장 동률로 판정불가가 될 수 있다(뼈대 5절 5 구현 결정 ⑥).
    · 모델 하나 빼기의 ver.2는 페르소나 약 3/4로, 대조 행은 255 전부로 학습한다(ver.2에 보수적).
    · 퇴화 경로(시험 봇 2 미만 칸, 매칭 쌍 50 미만 판별기)는 중단하지 않고 판정불가로 적는다.

목적
    12(OpenRouter 생성) 5절의 판별기 부분을 사전선언대로 계산한다.
      4항  ver.1 적용: 11 고정 모델(위치 · 퍼짐 · 제안 · 기준선)을 칸별 시험 쪽 계정 +
           시험 사람 234에 적용한 AUC. 기준 행 = 원 봇 댓글 한정(ver.1 학습 밖 134).
      5항  ver.2 학습: 학습 쪽 새 모델 계정 + 학습 사람 234(쪽 안 캘리퍼 매칭)로
           11 v2.1의 3~5단계. 비중 규칙. joblib + sha256.
      6항  대조 행: 같은 절차를 gpt-4o-mini 재생성 계정(학습 쪽)으로.
      7항  ver.2 시험: (i) 주 시험 = 모델 하나 빼기 4회, (ii) 보조 = 시험 쪽 전체.
           ver.1 · 대조 행을 같은 시험 집합에서 병기. 판정은 AUC 차의 부트스트랩 구간.
      9항  민감도: 모방 예시 저자가 ver.1 학습 사람(106명)인 슬롯을 뺀 판으로 4 · 5 · 7항.
    그리고 예측 P12-3 · P12-4 · P12-5를 뼈대 문장 그대로 걸어 기계적으로 판정한다.

뼈대 항목 → 함수
    5절 4항  ver.1 적용 ............ gate_ver1(G1) · ver1_fit · evaluate()의 "ver1적용"
    5절 5항  ver.2 학습 ............ train_all() → train_detector("ver.2") · select_weight
    5절 6항  대조 행 ............... train_all() → train_detector("대조")
    5절 7항  ver.2 시험 ............ evaluate()의 "LOMO"(주) · "보조"
    5절 9항  민감도 ................ prepare_sensitivity() → train_all · evaluate 재실행
    7절      P12-3 · P12-4 · P12-5 .. judge_predictions()
    4절      판정불가(매칭 쌍 100) .. cell_status() · g5_flags()

도구 넷과 주 판정 도구
    11 v2.1과 같은 네 도구다. 위치(로지스틱 가중 합) · 퍼짐(학습 봇 · 사람 중심까지의
    표준화 거리 차) · 제안(두 순위의 가중 평균) · 기준선(랜덤 포레스트, 표에만).
    판별기의 단일 출력은 제안이다(11 사전선언 요약). 그래서 P12-5는 제안 AUC로
    판정한다. P12-3은 뼈대 문장이 "위치 도구"를 지정하므로 위치 AUC로 판정한다.

왜 이렇게 하나
    · 모델 하나 빼기: 새 모델 셋으로 학습하고 학습에 없던 모델 하나로 시험한다.
      "처음 보는 모델에서도 되는가"를 가장 곧게 묻는 설계다. 비중 선택도 그 회차의
      학습 표본 안에서만 한다. 빠진 모델의 자료가 어떤 결정에도 들어가지 않게 한다.
    · 짝지은 부트스트랩: 같은 시험 집합 위에서 두 판별기의 AUC 차를 잴 때, 재추출한
      계정 묶음 하나로 두 AUC를 같이 계산한다. 계정 난이도의 흔들림이 두 AUC에
      똑같이 들어가 차이에서 지워진다. 그래서 따로 재는 것보다 구간이 정직하게 좁다.
    · 봉인: 시험 사람 234는 ver.2 · 대조 · 모델 하나 빼기 · 민감도 학습과 관문 G3 · G4,
      ver.2 번들 저장이 끝난 뒤에야 계정 사전에 들어간다. 시험 자료가 학습 결정에
      끼어들 길을 코드 순서로 막는다.
    · 11 코드 재사용: 자질 행렬 · 백분위 · 로지스틱 · 중심 거리 · 랜덤 포레스트 ·
      내부 5겹 문턱 · 교차검증은 11_판별기.py 함수를 경로로 불러 그대로 쓴다. 새로
      짜면 "같은 절차"를 보장할 수 없다. G1이 그 함수로 11 정본 결과를 차이 0으로
      재현하는지 먼저 본다.

12-1 입력 계약 (12-1_계정사전.json; 이 파일은 12-1을 연 적이 없다. 계약으로만 적재한다)
    최상위 {"설정": {...}, "계정": {uid: 기록}}. 설정.관문통과가 true가 아니면 거부한다.
    파일 sha256은 12-1_생성댓글파싱_요약.json의 산출.sha256과 같아야 한다(없으면 경고 · 기록).
    기록마다
      필수  문서수 · 문장수 · 토큰수 · 토큰수_구두점제외 · 구두점토큰수 · 문장길이 ·
            기능어 · UPOS · 자질  (13-0 aggregate()가 내는 필드. 13-0과 같은 파서)
      모델  "모델" · "생성모델" · "model" 필드(모델 ID, 날짜 붙은 ID, MODEL_SLOT_k, 별칭).
            없으면 uid 접두 별칭(12-1 규약 G1_~G4_ · G0_, 그 밖 haiku_ · r4o_ 등).
            gpt-4o-mini면 재생성 계정, 그 밖은 새 모델 계정.
      페르소나  "페르소나id" → "원봇uid" → uid 마지막 "_" 뒤 조각 → uid 안 P### 순.
      선택  "적격": false면 건너뛴다. 문서 10건 미만도 건너뛴다(01 규칙).
    민감도용 (경로 셋 가운데 먼저 맞는 것. 모두 없으면 민감도만 실행불가)
      (가) 12-1 현행 형식(12-1_생성댓글파싱.py 코드 기준, 자료는 보지 않았다):
           최상위 "민감도_106제외" {uid: 같은 파싱에서 뺄 문서를 빼고 재집계한 계정 + "뺀문서수"},
           최상위 "문서별" {"열": [슬롯id, 시각, 정제글자수, 문장수, 토큰수_구두점제외, …],
           "계정": {uid: 행 목록}}, 설정."민감도_106명" · 설정."민감도_제외계정".
           이 파일은 다시 파싱하지 않고 대장 기준 뺄 슬롯 수와, 문서별 열(문장수 · 토큰수_구두점제외 ·
           Tense_Past · Tense_합)의 전 행 합 = 본 계정, 남은 행 합 = 줄인 계정으로 대조만 한다.
      (나) 계정마다 "문서별": [{"슬롯id", 문장수 · 토큰수 · 토큰수_구두점제외 · 구두점토큰수 ·
           문장길이 · 기능어 · UPOS · 자질}, ...] → 남은 문서 합산으로 재구성.
      (다) 계정마다 "슬롯id목록" + "문서"(정제 뒤 본문) → 13-0 measure_account로 재측정.
      슬롯의 모방 저자는 12-1이 아니라 프롬프트대장.jsonl의 "모방저자"에서 읽는다.
    13-0 집단(사람 · 원봇 · 완전모방기)과 MIM_ 계정은 12-1에 있어도 건너뛴다.
    사람 · 원 봇 · 완전 모방기는 13-0_계정사전.json(동결 해시)에서만 읽는다.

관문 (check()로 한다. python -O에서도 꺼지지 않는다)
    G0  입력 사슬: 분할 · 대장 · 모델ID표 · 13-0 계정사전 · 11 번들 sha256 = 동결.json,
        11_판별기.py sha256 = 11 JSON 기록, 13-0 관문통과, 09-1 caliper_match AST 동일,
        뼈대 7절 예측 원문 = 이 파일 상수(관문). 뼈대 sha256은 동결값 · 개정 기록 · 현재값을 적기만 한다
        (동결 뒤 개정은 예상된 차이). 12-1 sha256 = 12-1 요약 기록.
    G1  ver.1 재현: 번들 sha256 = e6b75865…(다르면 거부). 11 코드로 11 입력에서
        (가) 여덟 행 OOF AUC · 계정별 OOF 점수 · fold 배정이 11 JSON과 차이 0,
        (나) 1,024 전체 재적합이 번들 배열 · 나무 구조 · 문턱과 비트 단위로 같음,
        (다) 번들로 낸 학습 표본 내 지표 = 11 JSON. 번들은 fold 모델을 담지 않으므로
        OOF 재현은 11 코드 재실행으로 한다.
    G2  누설: 시험 사람 234가 어떤 학습 표본에도 없다. 한 판별기의 학습 페르소나와
        시험 페르소나가 겹치지 않는다. 학습 봇은 학습 쪽, 시험 봇은 시험 쪽이다.
        기준 행 134는 ver.1 학습 밖이다.
    G3  라벨 뒤섞기 20회(ver.2 학습 표본): 위치 · 제안 OOF AUC 평균의 위쪽 z ≤ 2.326.
        아래쪽 유의(교차검증 음의 편향)와 11 범위 0.45~0.55 밖 회차는 경고만 한다.
    G4  결정성: ver.2 학습을 같은 프로세스에서 다시 돌려 비트 단위로 같다.
        프로세스 사이는 JSON의 결과_digest로 대조한다.
    G5  4절: 칸의 생존 계정을 표 (a) 640과 매칭한 쌍이 100 미만인 칸은 판정불가.
        모든 AUC 행에 계급별 n과 "계급별n≥100" 표시를 함께 적는다.

구현 결정
    IMPLEMENTATION_DECISIONS 상수에 적었다. 생성 자료를 보기 전에 적었다.

실행 명령
    본 실행 (12-1_계정사전.json이 생기고 이 파일을 동결한 뒤. IDLE F5도 된다):
        cd "/Users/son/Desktop/Aseo/30. Research/DM LAB/연구주제/단계별 진행경과"
        PYTHONDONTWRITEBYTECODE=1 /Users/son/.claude/venvs/audio-transcribe/bin/python -u 12-3_판별기ver2.py
    배선 점검 (부트스트랩 200회, 산출은 --out-dir에만):
        PYTHONDONTWRITEBYTECODE=1 /Users/son/.claude/venvs/audio-transcribe/bin/python -u 12-3_판별기ver2.py \\
            --smoke --input <합성 12-1 JSON> --out-dir <볼트 밖 폴더>
    대체 입력 전체 실행 (합성 자료 등, 부트스트랩 2,000회):
        ... -u 12-3_판별기ver2.py --input <JSON> --out-dir <볼트 밖 폴더>
    필요: numpy · scipy · scikit-learn · joblib (민감도가 문서 본문 경로면 stanza · langid)

산출
    본 실행: 이 폴더의 12_판별기v2.json · 12_판별기v2.joblib · 12_판별기v2_출력.log
    (뼈대 10절 이름). 점검 실행은 같은 이름으로 --out-dir에 쓴다. 입력 파일에는
    한 글자도 쓰지 않는다.
"""

import argparse
import ast
import contextlib
import glob
import hashlib
import importlib.util
import io
import json
import math
import os
import platform
import random
import re
import sys
import time
import traceback
import unicodedata
from collections import Counter
from datetime import datetime

# 11 · 13-0 · 09-1을 경로로 불러 쓴다. 볼트 폴더에 __pycache__가 생기지 않게 막는다.
sys.dont_write_bytecode = True

import joblib
import numpy as np
import scipy
import sklearn
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ════════════════════════════════════════════════════════════════════════
# [경로]
# ════════════════════════════════════════════════════════════════════════
SCRIPT_PATH = nfc(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPT_PATH)
PREP_DIR = f"{HERE}/12_OpenRouter생성_준비"
SPLIT_JSON = f"{PREP_DIR}/분할.json"
LEDGER_JSONL = f"{PREP_DIR}/프롬프트대장.jsonl"
MODEL_TABLE_JSON = f"{PREP_DIR}/모델ID표.json"
FREEZE_JSON = f"{PREP_DIR}/동결.json"
PY11 = f"{HERE}/11_판별기.py"
J11 = f"{HERE}/11_판별기.json"
BUNDLE11 = f"{HERE}/11_판별기_모델.joblib"
PY091 = f"{HERE}/09-1_분량통제.py"
PY130 = f"{HERE}/13-0_댓글한정재파싱.py"
FUNCWORDS_JSON = f"{HERE}/02_기능어목록.json"
DECL_MD = f"{HERE}/12_OpenRouter생성_사전선언_뼈대.md"
DATA_DIR = nfc(os.path.expanduser("~/DM_LAB_data/12_OpenRouter"))
ACC130 = f"{DATA_DIR}/13-0_계정사전.json"
IN121_DEFAULT = f"{DATA_DIR}/12-1_계정사전.json"
OUT_NAMES = {"json": "12_판별기v2.json", "model": "12_판별기v2.joblib", "log": "12_판별기v2_출력.log"}
OUT_DIR = None          # main()이 정한다

# ════════════════════════════════════════════════════════════════════════
# [설정] 사전선언 값. 결과를 보고 바꾸지 않는다.
# ════════════════════════════════════════════════════════════════════════
SEED = 20260926
N_BOOT = 2000
N_BOOT_SMOKE = 200
CALIPER = 0.10                  # 09-1 규칙: |log 분모 차| ≤ 0.10
MIN_DOCS = 10                   # 01 규칙
N_MIN = 100                     # 4절: 매칭 쌍 100 미만 칸은 판정불가
CEILING = 0.999                 # 5절 7항: 두 AUC가 모두 이 값 이상이면 천장 동률
P123_MARGIN = 0.05              # P12-3: 0.05 이상 떨어지지 않는다
P124_BAND = 0.02                # P12-4: 부호 있는 평균 Δ의 구간이 ±0.02 띠 밖에 통째로(구현 결정 ①)
P124_MIN_BOTS = 30              # P12-4: 매칭 학습 봇 30 미만 모델이 있으면 판정불가
PAIRS_FALLBACK = 100            # 매칭 쌍이 이보다 적으면 그 실행에만 ver.1 학습 사람 406 추가(구현 결정 ②)
MIN_PAIRS_DET = 50              # 매칭 쌍이 이보다 적은 판별기는 판정불가(구현 결정 ③)
N_EXTRA_HUMS = 406              # ver.1 학습 사람 가운데 13-0 댓글 한정 계정이 있는 사람
TOL = 1e-12                     # 이득 · 최저 모델 AUC 비교 허용오차(구현 결정 ④)
WEIGHT_GAIN = 0.01              # 5절 5항: argmax가 1:1보다 0.01 이상
WEIGHT_GRID = tuple(round(i / 10, 1) for i in range(11))   # 위치 비중 w, 퍼짐 1 − w
N_SHUFFLE = 20                  # G3: 라벨 뒤섞기 회수(구현 결정 ④)
SHUFFLE_Z = 2.326               # G3: 20회 평균의 위쪽 z 문턱(한쪽 α 0.01)
MODEL_REGEN = "openai/gpt-4o-mini"
BUNDLE11_SHA = "e6b75865381dfeaa23e68dc0da0107bf10934b7c672bc5426cc65b9ffeb1e9b3"
FW_HASH = "382b68572f03bc23"
SLOTS = ("MODEL_SLOT_1", "MODEL_SLOT_2", "MODEL_SLOT_3", "MODEL_SLOT_4")
MEAS_FIELDS = ("문서수", "문장수", "토큰수", "토큰수_구두점제외", "구두점토큰수",
               "문장길이", "기능어", "UPOS", "자질")
OLD_GROUPS = ("사람", "원봇", "완전모방기")
GRP_NEW, GRP_REGEN = "새모델", "재생성"
DET_V1, DET_V2, DET_CTRL, DET_LOMO = "ver.1", "ver.2", "대조", "ver.2(하나빼기)"

# uid 접두 별칭(모델 필드가 없을 때만 쓴다). 긴 별칭부터 맞춘다.
MODEL_ALIASES = {
    "anthropic/claude-haiku-4.5": ("claude-haiku-4.5", "haiku", "claude", "anthropic",
                                   "model_slot_1", "slot1", "m1", "g1"),
    "openai/gpt-6-luna": ("gpt-6-luna", "luna", "gpt6", "gpt-6", "model_slot_2", "slot2", "m2", "g2"),
    "google/gemini-3.5-flash-lite": ("gemini-3.5-flash-lite", "gemini", "google",
                                     "model_slot_3", "slot3", "m3", "g3"),
    "deepseek/deepseek-v4.1-flash": ("deepseek-v4.1-flash", "deepseek", "model_slot_4",
                                     "slot4", "m4", "g4"),
    MODEL_REGEN: ("gpt-4o-mini", "4o-mini", "4omini", "gpt4omini", "r4o", "regen", "4o", "재생성", "g0"),
}

IMPLEMENTATION_DECISIONS = [
    "D1 ver.1 적용: 11 번들은 fold 모델이 아니라 1,024 전체로 적합한 고정 모델 한 벌이다"
    "(분위 변환 xp · fp, 원값 중앙값, 로지스틱, 봇 · 사람 중심과 퍼짐 · keep, 랜덤 포레스트, 문턱). "
    "번들 배열로 11 score_all에 넣을 적합 사전을 만들어 그대로 채점한다. 결측 → 번들 원값 중앙값, "
    "자질마다 np.interp(번들 xp, fp)를 0~1로 자름(11 apply_prep). 자질 정의(기능어 172 · 형태 58 · "
    "품사 17 · 리듬 3, 축 지도)도 번들 값을 쓴다. ver.2도 같은 자질 정의를 쓴다.",
    "D2 G1: 번들에 OOF 점수가 없으므로 11 코드(sha256 = 11 JSON 기록)로 11 입력에서 교차검증을 "
    "다시 돌려 여덟 행 OOF AUC · 계정별 OOF 점수 · fold 배정이 11 JSON과 == 로 같은지 본다. "
    "1,024 전체 재적합이 번들의 분위 함수 · 중앙값 · 계수 · 절편 · 중심 · 퍼짐 · keep · 나무 구조 · "
    "네 문턱과 비트 단위로 같은지 본다. 번들로 낸 학습 표본 내 지표가 11 JSON 기록과 같은지 본다.",
    "D3 기준 행 = 13-0 원봇 504 가운데 번들 train_ids 밖 134계정(쪽 무관, 뼈대 5절 4항 '학습 밖 "
    "134'). ver.1 학습 봇 목록은 11 JSON fold배정.쌍의 첫 원소이고 번들 train_ids와 대조한다.",
    "D4 시험 집합은 매칭하지 않는다. 칸의 시험 쪽 생존 계정 전부 + 시험 사람 234 전부. 채점 묶음 = "
    "그 집합 전체(제안 순위는 그 안에서 매긴다).",
    "D5 캘리퍼 매칭: 09-1 caliper_match를 그대로 복사(G0가 docstring 뺀 AST로 대조). 분모 = 계정의 "
    "토큰수_구두점제외, 캘리퍼 0.10, 그리디 1:1, 봇 순서 섞기 시드 20260926(12 공통 시드. 09-1 "
    "원 실행은 20260827). 봇 · 사람 목록은 uid 정렬 뒤 넘긴다(12-2 E2와 같음).",
    "D6 부트스트랩: 봇은 층(학습은 모델, 시험 칸은 한 층, 보조는 모델) 안에서, 사람은 따로 복원 "
    "추출한다(np.random.default_rng([20260926, 열쇠…]).multinomial). 2,000회(--smoke 200). 시험 "
    "사람 234의 재추출 행렬 하나를 모든 시험 집합이 공유한다. 같은 집합의 판별기 비교는 같은 "
    "재추출 위에서 한다(짝지은 부트스트랩). 구간 = np.percentile 2.5 · 97.5. 제안 점수는 채점 묶음 "
    "전체에서 한 번 순위화하고 재추출마다 다시 순위화하지 않는다. AUC = 봇 · 사람 비교 행렬"
    "(큼 1, 같음 0.5)의 가중 평균이며 점추정은 roc_auc_score와 대조한다.",
    "D7 비중: 위치 비중 w ∈ {0.0, 0.1, …, 1.0}, 퍼짐 1 − w. OOF 제안은 fold마다 가중 순위 평균을 "
    "(r̄ − 1)/(n − 1)로 정규화해 모은다(11 rank_mean과 같은 식. w = 0.5에서 11 제안 OOF와 == 단언). "
    "argmax 동점은 |w − 0.5|가 작은 쪽, 그다음 작은 w. 바꾸는 조건 다섯을 모두 요구한다: (가) OOF "
    "AUC 이득 ≥ 0.01, (나) 페르소나 부트스트랩 이득 95% 하한 > 0, (다) 모델별 OOF AUC 최솟값이 "
    "1:1보다 낮지 않음, (라) 그 학습 표본의 P12-4식 검사(D11)에서 판정가능이고 천장이 깨짐, "
    "(마) 계열 관문: ver.2 계열(모델 하나 빼기 넷, 민감도 ver.2 · 모델 하나 빼기)은 본 실행 ver.2의 "
    "P12-4가 적중일 때만 참이고 빗나감 · 판정불가면 계열 전체 1:1(뼈대 5절 5 구현 결정 ①). 대조 행은 "
    "자기 (라)만 본다. (가) · (다) 비교는 허용오차 1e-12(구현 결정 ④). 대조 행의 '모델별'은 페르소나의 "
    "배정 모델 칸이다.",
    "D8 문턱은 기술 보고만: ver.1은 번들 문턱, ver.2 · 대조는 학습 OOF 점수의 균형정확도 최대점"
    "(11 choose_threshold). 제안 문턱은 채점 묶음에 따라 뜻이 바뀐다.",
    "D9 주 판정 도구 = 제안. P12-3만 뼈대 문장대로 위치. 표에는 네 도구를 모두 적는다.",
    "D10 P12-3: 칸마다 AUC(칸, 위치) − AUC(기준 행, 위치)의 95% 하한 > −0.05면 그 칸 통과(시험 "
    "사람 재추출 공유). 삼값 판정: 판정 가능한 칸 하나라도 불통과면 빗나감, 네 칸 모두 판정 "
    "가능하고 통과면 적중, 그 밖은 판정불가. 기준 행 ver.1 AUC가 13-0 자료에서 이미 1.0이므로 사실상 "
    "'칸의 95% 하한 > 0.95'다(뼈대 5절 5 구현 결정 ⑥).",
    "D11 P12-4(뼈대 5절 5 구현 결정 ①): ver.2 학습 OOF에서 모델마다 부호 있는 Δ_m = AUC(위치) − "
    "AUC(퍼짐)(봇 = 그 모델의 매칭 학습 봇, 사람 = 매칭 학습 사람 전부), 모델 평균, 페르소나 부트스트랩 "
    "95% 구간. 구간이 [−0.02, +0.02] 띠 밖에 통째로 있으면(어느 쪽이든) 적중(천장이 깨진다), 띠에 "
    "걸치면 빗나감. 매칭 학습 봇이 30 미만인 모델이 있거나 4절 판정불가 칸이 있으면 판정불가. "
    "옛 통계(|Δ_m| 평균)는 참 차이 0에서도 양으로 치우쳐 참고로만 적는다.",
    "D12 P12-5: 회차마다 제안 AUC 차 (ver.2 − ver.1), (ver.2 − 대조)의 95% 하한 > 0이면 성공. 판정 "
    "가능한 회차 = 빠진 모델 칸이 4절 판정가능이고 시험 봇 2 이상이며 관련 판별기가 판정불가가 아니고 "
    "두 AUC가 모두 0.999 이상(천장 동률)이 아님. 두 부분 각각: 성공 ≥ 3이면 성립, 성공 + 판정불가 "
    "회차 < 3이면 불성립, 그 밖은 판정불가. 둘 다 성립이면 적중, 하나라도 불성립이면 빗나감, 그 밖은 "
    "판정불가. 위치 도구 판정은 참고로 적는다.",
    "D13 G5: 뼈대 4절 '매칭 쌍 100 미만인 모델 칸'을 칸 단위로 적용한다. 칸의 생존 계정 전부(두 쪽)를 "
    "표 (a) 풀 640과 D5 규칙으로 매칭한 쌍 수가 100 미만이면 그 칸의 AUC 행과 그 칸을 뺀 모델 하나 "
    "빼기 회차를 판정불가로 둔다. 칸이 아닌 행(재생성 · 기준 행 · 보조)은 계급별 n ≥ 100을 쓴다. "
    "모든 행에 계급별 n과 '계급별n≥100' 표시를 함께 적는다. 시험 쪽 칸은 설계상 61~65 페르소나라 "
    "'계급별 n ≥ 100'을 칸 행에 걸면 P12-3 · P12-5가 설계상 판정불가가 된다. 그래서 칸 행에는 "
    "뼈대 문언(매칭 쌍)을 쓴다.",
    "D14 G3(구현 결정 ④): ver.2 학습 표본에서 라벨 뒤섞기 20회(회차 i: np.random.default_rng("
    "[20260926, i]).permutation(y), 쌍 단위 fold 유지). 위치 · 제안 OOF AUC 20개의 평균을 경험 "
    "표준편차로 z검정한다. 누설은 AUC를 올리므로 관문은 위쪽 한쪽(z > 2.326, 한쪽 α 0.01이면 "
    "불통과). 평균이 유의하게 낮은 것은 교차검증 음의 편향(11 실측 0.466 · 0.464)이라 경고로만 "
    "적는다. 11 범위 0.45~0.55 밖 회차 수도 경고로 적는다.",
    "D15 12-1 적재: 설정.관문통과가 참(true)이어야 한다. 12-1 파일 sha256을 12-1_생성댓글파싱_요약.json"
    "의 산출.sha256과 대조한다(본 실행은 이 폴더의 요약, 점검 실행은 입력 파일 폴더의 "
    "12-1_생성댓글파싱_요약*.json). 다르면 거부, 요약이나 기록이 없으면 경고하고 적는다. 모델 = 모델 "
    "필드(모델 · 생성모델 · model) 우선, 없으면 uid 접두 별칭. 필드와 접두가 다르면 필드를 따르고 "
    "수를 적는다. 페르소나 = 페르소나id → 원봇uid → uid 마지막 '_' 뒤 조각 → uid 안 P###. 13-0 집단 · "
    "MIM_ · 13-0 uid는 건너뛴다. 적격 false와 문서 10건 미만은 건너뛴다. 새 모델 계정의 모델 = 페르소나 "
    "배정 칸의 모델(다르면 중단). 페르소나당 새 모델 · 재생성 계정은 하나씩(둘이면 중단). 문장길이 "
    "길이 = 문장수, 합 = 토큰수_구두점제외(13-0 G7)도 확인한다.",
    "D16 민감도: 106명 = 분할.json 역할 ['모방'] 이고 09-1매칭_ver1학습 참인 사람(번들 train_ids 안임도 "
    "확인). 뺄 슬롯 = 대장 모방저자 ∈ 106. 원 봇 · 사람 · 기준 행은 줄이지 않는다. 경로 (가): 12-1이 "
    "같은 파싱에서 재집계한 '민감도_106제외' 계정을 쓰고, 12-1의 106명 = 분할 106명, 계정마다 뺀문서수 = "
    "본 계정 뺀문서수(복사 슬롯, 없으면 0) + 최상위 문서별 슬롯id 가운데 대장 기준 뺄 슬롯 수, 문서별에 있는 열(문장수 · 토큰수_구두점제외 · "
    "Tense_Past · Tense_합)의 합이 본 계정(전 행)과 줄인 계정(남은 행)의 값과 같음(Tense_Past = 자질 "
    "Tense=Past, Tense_합 = Tense= 로 시작하는 자질 합), 줄인 계정 문서수 = 남은 행 수, 탈락 계정은 "
    "설정.민감도_제외계정 또는 최상위 변형_탈락.민감도_106제외에 사유가 있음을 대조한다(하나라도 어긋나면 민감도 실행불가). 경로 (나): 계정별 "
    "문서별 측정치를 합산(langid 재판정 불가, 기록). 경로 (다): 문서 본문을 13-0 measure_account로 "
    "재측정(10건 · langid en 재판정). 줄인 계정이 10건 미만이면 탈락. 대조 행도 줄인 재생성 계정으로 "
    "다시 학습한다(7항 병기가 같은 입력 위에 서도록). (나)(다) 재구성 정합: 빼는 슬롯이 없을 때의 "
    "재구성이 저장값과 같아야 한다(문서별은 전 계정, 본문은 시드 표본 3).",
    "D17 봉인: 시험 사람 234는 모든 학습, G3 · G4, ver.2 번들 저장이 끝난 뒤 계정 사전에 넣는다.",
    "D18 G4: 같은 프로세스에서 ver.2 학습을 다시 돌려 매칭 쌍 · OOF 점수(네 도구) · 비중 · 분위 함수 · "
    "계수 · 중심 · 퍼짐 · 나무 구조 · 요약이 비트 단위로 같은지 본다. 프로세스 사이는 결과_digest"
    "(시각 · 경로 · 번들 파일 해시를 뺀 결과의 sha256)로 대조한다.",
    "D19 부트스트랩 열쇠: 시험 사람 (1,), 시험 봇 (2, 민감도, 집합번호: 칸 1~4 · 재생성 5 · 보조 7), "
    "기준 행 (2, 0, 6)(민감도에서도 같음), 학습 봇 (3, 민감도, 학습번호), 학습 사람 (4, 민감도, "
    "학습번호). 학습번호: ver.2 0 · 대조 1 · 하나빼기 10 + k.",
    "D20 학습 사람(뼈대 3절 미결 [결정]을 5절 5 구현 결정 ②로 확정): 기본은 학습 사람 234. 어느 학습 "
    "실행이든(ver.2 · 대조 · 모델 하나 빼기 · 민감도) 캘리퍼 매칭 쌍이 100 미만이면 그 실행에만 ver.1 "
    "학습 사람 406명을 더해 234 + 406으로 다시 매칭한다. 406 = 11 JSON fold배정.쌍의 사람 512 가운데 "
    "13-0 댓글 한정 계정이 있는 사람(= 표a 640 − 학습 234와 같음을 단언), 시험 234 · 학습 234와 서로소 "
    "단언. 어느 실행이 썼는지 학습 요약의 사람풀 · ver1학습사람406_추가에 적는다.",
    "D21 퇴화 경로(구현 결정 ③)는 중단하지 않는다: 시험 봇 2 미만 칸은 그 칸의 ver.1 행 · P12-3 항 · "
    "모델 하나 빼기 회차를 판정불가. 406을 더한 뒤에도 매칭 쌍 50 미만이거나 학습 표본 전체 결측 자질이 "
    "있는 판별기는 그 판별기만 판정불가(그 판별기가 든 비교만 판정불가). ver.2가 판정불가면 번들 · G3 · "
    "G4는 해당없음으로 적고 P12-4는 판정불가. 관문이 아닌 예외도 중단 JSON(추적 포함)을 쓰고 0이 아닌 "
    "코드로 끝낸다.",
    "D22 범위 밖 백분위 칸 비율(뼈대 5절 9, 구현 결정 ⑤): ver.1 적용 행마다 결측이 아닌 원값 칸 가운데 "
    "번들 분위 함수 범위(xp 최솟값~최댓값) 밖이라 0 또는 1로 잘린 칸의 비율. 학습값이 한 가지뿐인 자질은 "
    "자르기가 없어 분모에서 뺀다. 봇 · 사람 따로, 블록별(F · M형태 · M품사 · R).",
    "D23 학습 규모 기록(구현 결정 ⑥): 모델 하나 빼기의 ver.2는 학습 쪽 페르소나 약 3/4로 학습하고 대조 "
    "행은 학습 쪽 255 전부로 학습한다. ver.2 − 대조 비교에서 ver.2에 불리한(보수적) 설계다. 회차마다 "
    "두 학습 페르소나 수를 적는다.",
]

# 뼈대 7절 원문. 뼈대 파일이 있으면 글자까지 대조한다(관문 G0 부속).
PRED_TEXT = {
    "P12-3": "ver.1 위치 도구의 칸별 AUC가 기준 행(ver.1 × 원 봇 댓글 한정) 대비 0.05 이상 떨어지지 않는다.",
    "P12-4": "학습 쪽에서 위치·퍼짐의 모델별 AUC 평균 차이가 0.02 이상(천장이 깨진다). 빗나가면 비중 1:1 유지, \"천장\" 행으로 기록.",
    "P12-5": "모델 하나 빼기 시험에서 ver.2 − ver.1 AUC 차의 95% 하한 > 0(4회 중 3회 이상). 대조 행보다도 높다.",
}

# 적대 검증 뒤 기록(JSON 설정.검토주석). 판정 규칙은 바꾸지 않는 기록이다.
REVIEW_NOTES = [
    "기준 행(원 봇 댓글 한정 134 + 시험 사람 234)의 ver.1 AUC는 13-0 자료에서 이미 1.0이다(적대 검증 e2). "
    "그래서 P12-3은 사실상 '칸의 95% 하한 > 0.95'를 요구하고, P12-5는 천장 동률로 판정불가가 될 수 있다"
    "(뼈대 5절 5 구현 결정 ⑥에 사전 기록).",
    "모델 하나 빼기의 ver.2는 학습 쪽 페르소나 약 3/4로 학습하고 대조 행은 255 전부로 학습한다. "
    "ver.2 − 대조 비교에서 ver.2에 보수적이다(D23).",
    "이 기준 행 값은 시험 사람 234를 ver.1로만 채점해 얻은 것이다(적대 검증과 합성 점검 실행). ver.2 학습 "
    "결정에는 들어가지 않는다.",
]

m11 = None      # 11_판별기.py 모듈(G0 해시 확인 뒤 불러온다)
CTX = None      # 실행 맥락(번들 · 자질 정의 · 집단). main()이 채운다


# ════════════════════════════════════════════════════════════════════════
# [도구]
# ════════════════════════════════════════════════════════════════════════
class GateError(RuntimeError):
    """관문 실패."""


def check(cond, msg):
    """관문 판정. assert와 달리 python -O에서도 꺼지지 않는다."""
    if not cond:
        raise GateError(msg)


class Tee:
    """화면과 로그 파일에 같은 글을 쓴다."""

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
    say(f"  [라벨 사용] {where}")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


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


def write_json(path, obj):
    """임시 파일에 쓰고 fsync 뒤 이름을 바꾼다. 산출 폴더 밖에는 쓰지 않는다."""
    check(os.path.dirname(path) == OUT_DIR, f"산출 폴더 밖 쓰기 금지: {path}")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(jsonable(obj), f, ensure_ascii=False, indent=1, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def import_by_path(name, path, argv=None):
    """경로로 모듈을 불러온다. argv를 주면 불러오는 동안만 sys.argv를 바꾼다(13-0은 import 때 argparse를 돈다)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    old = sys.argv
    if argv is not None:
        sys.argv = argv
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = old
    return mod


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


# ════════════════════════════════════════════════════════════════════════
# [매칭] 09-1 caliper_match 그대로 (G0가 AST로 대조한다)
# ════════════════════════════════════════════════════════════════════════
def caliper_match(bot_ids, human_ids, logd, caliper, seed):
    """
    [09-1_분량통제.py에서 가져옴. 본문 동일, docstring만 다름]
    봇을 시드로 섞고, 차례로 아직 안 쓰인 사람 가운데 |log 분모 차| ≤ caliper인
    가장 가까운 사람을 짝으로 삼는다. 후보가 없으면 그 봇은 탈락(캘리퍼를 넓히지 않는다).
    반환: (쌍 [(봇, 사람, 거리)…], 탈락 봇, 쓰인 사람 집합)
    """
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


def match(accs, bots, hums):
    """D5: 토큰수_구두점제외의 log로 09-1 규칙 매칭. 목록은 uid 정렬 뒤 넘긴다."""
    bots, hums = sorted(bots), sorted(hums)
    logd = {}
    for u in bots + hums:
        d = accs[u]["토큰수_구두점제외"]
        check(d > 0, f"{u}: 토큰수_구두점제외가 0이라 log 분모를 만들 수 없다")
        logd[u] = math.log(d)
    return caliper_match(bots, hums, logd, CALIPER, SEED)


# ════════════════════════════════════════════════════════════════════════
# [점수] 가중 순위 평균 · 부트스트랩 AUC
# ════════════════════════════════════════════════════════════════════════
def wrank(s_pos, s_spr, w_pos):
    """
    제안 점수(11 rank_mean의 가중 판). 채점 묶음 안에서 위치 · 퍼짐 점수를 각각 평균
    순위(작은 값 1 ~ 큰 값 n, 큰 값 = 봇 쪽)로 바꾸고 w : 1 − w로 평균해 [0, 1]로 정규화.
    w = 0.5이면 11의 제안과 같은 식이다.
    """
    n = len(s_pos)
    check(n >= 2 and n == len(s_spr), "제안 점수: 채점 묶음이 2계정 미만이거나 길이가 다르다")
    w_spr = 1.0 - w_pos
    r = w_pos * rankdata(s_pos, method="average") + w_spr * rankdata(s_spr, method="average")
    return (r - 1.0) / (n - 1.0)


def oof_wrank(oof_pos, oof_spr, fold_of, w):
    """교차검증 OOF 제안: fold(채점 묶음)마다 따로 가중 순위 평균을 매겨 모은다."""
    out = np.full(len(oof_pos), np.nan)
    for f in np.unique(fold_of):
        idx = np.where(fold_of == f)[0]
        out[idx] = wrank(oof_pos[idx], oof_spr[idx], w)
    return out


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


def g5_flags(nb, nh, cell_ok=None):
    """G5 표시. 칸 행은 4절 칸 판정(매칭 쌍 ≥ 100)을, 그 밖은 계급별 n ≥ 100을 판정 기준으로 쓴다."""
    per_class = nb >= N_MIN and nh >= N_MIN
    return {"n_봇": nb, "n_사람": nh, "계급별n≥100": per_class, "4절_칸판정가능": cell_ok,
            "판정가능": bool(cell_ok) if cell_ok is not None else per_class}


# ════════════════════════════════════════════════════════════════════════
# [자질 · 적합 사전] 11 함수 그대로
# ════════════════════════════════════════════════════════════════════════
def feat(accs, ids):
    """(len(ids) × 250) 원값 행렬. 11 build_matrix + 번들의 자질 정의 · 축 지도."""
    return m11.build_matrix(accs, ids, CTX.keys, CTX.axis_map)


def fit_from_bundle(b):
    """번들(11 또는 ver.2)을 11 score_all이 받는 적합 사전으로 옮긴다. 값은 바꾸지 않는다."""
    return {"prep": {"xp": b["percentile_xp"], "fp": b["percentile_fp"],
                     "median": b["impute_raw_median"]},
            "models": {m11.ROW_POS: b["model"]},
            "spread": dict(b["spread"]),
            "rf": {m11.ROW_BASE: {"model": b["rf"]}}}


def score(fit, w, X):
    """네 도구 점수. 채점 묶음 = X 전체. 제안은 비중 w로 다시 매긴다(w = 0.5면 11 제안과 == 단언)."""
    s = m11.score_all(fit, X, CTX.abl, m11.EXTRAS_MAIN)
    out = {t: s[t] for t in (m11.ROW_BASE, m11.ROW_POS, m11.ROW_SPREAD)}
    out[m11.ROW_PROP] = wrank(s[m11.ROW_POS], s[m11.ROW_SPREAD], w)
    if w == 0.5:
        check(np.array_equal(out[m11.ROW_PROP], s[m11.ROW_PROP]), "가중 순위 평균(0.5) ≠ 11 제안")
    return out


# ════════════════════════════════════════════════════════════════════════
# [G0] 입력 사슬
# ════════════════════════════════════════════════════════════════════════
def gate_inputs(gates):
    line("[G0] 입력 사슬: 동결.json 해시 · 11 정본 · 09-1 매칭 함수 · 뼈대 예측 원문")
    need = {"분할.json": SPLIT_JSON, "프롬프트대장.jsonl": LEDGER_JSONL, "모델ID표.json": MODEL_TABLE_JSON,
            "동결.json": FREEZE_JSON, "11_판별기.py": PY11, "11_판별기.json": J11,
            "11_판별기_모델.joblib": BUNDLE11, "09-1_분량통제.py": PY091,
            "13-0_계정사전.json": ACC130}
    for name, p in need.items():
        check(os.path.exists(p), f"입력 없음: {p}")
    sha = {name: sha256_file(p) for name, p in need.items() if name != "동결.json"}
    freeze = load_json(FREEZE_JSON)
    j11 = load_json(J11)
    rows = {
        "분할.json = 동결": sha["분할.json"] == freeze["분할.json"],
        "프롬프트대장.jsonl = 동결": sha["프롬프트대장.jsonl"] == freeze["프롬프트대장.jsonl"],
        "모델ID표.json = 동결": sha["모델ID표.json"] == freeze["모델ID표.json"],
        "13-0_계정사전.json = 동결": sha["13-0_계정사전.json"] == freeze["13-0_계정사전.json"],
        "11 번들 = 동결 = 정본(e6b75865…)": (sha["11_판별기_모델.joblib"] == freeze["11_정본모델.joblib"]
                                           == BUNDLE11_SHA),
        "11 JSON 모델 sha = 정본": j11["고정모델"]["파일_sha256"] == BUNDLE11_SHA,
        "11_판별기.py = 11 JSON 스크립트_sha256": sha["11_판별기.py"] == j11["설정"]["스크립트_sha256"],
    }
    me = open(SCRIPT_PATH, encoding="utf-8").read()
    s091 = open(PY091, encoding="utf-8").read()
    a, b = func_ast(me, "caliper_match"), func_ast(s091, "caliper_match")
    rows["caliper_match = 09-1 (AST)"] = a is not None and a == b
    for k, v in rows.items():
        say(f"  {k:<42} {'같음' if v else '■ 다름'}")
    # 예측 원문 일치(관문, 구현 결정 ④). 연구자가 '_뼈대'를 떼면 뗀 이름을 쓴다.
    cands = [p_ for p_ in (DECL_MD, DECL_MD.replace("_뼈대.md", ".md")) if os.path.exists(p_)]
    decl = {"후보": [os.path.basename(p_) for p_ in cands],
            "동결_뼈대_sha256": (freeze.get("뼈대") or {}).get("sha256"),
            "동결_개정_뼈대_sha256": {k: v.get("뼈대_sha256") for k, v in freeze.items()
                                   if k.startswith("개정") and isinstance(v, dict) and v.get("뼈대_sha256")}}
    if cands:
        txt = open(cands[0], encoding="utf-8").read()
        decl["경로"] = os.path.basename(cands[0])
        decl["현재_sha256"] = sha256_file(cands[0])
        decl["예측원문_일치"] = {k: (f"**{k}**: {v}" in txt) for k, v in PRED_TEXT.items()}
        rows["뼈대 7절 예측 원문 = 이 파일 상수"] = all(decl["예측원문_일치"].values())
    else:
        rows["뼈대 7절 예측 원문 = 이 파일 상수"] = False
    say(f"  뼈대 7절 예측 원문 글자 일치 {decl.get('예측원문_일치')} (관문)")
    say(f"  뼈대 sha256: 동결 {str(decl['동결_뼈대_sha256'])[:12]}… · 개정 기록 "
        f"{ {k: str(v)[:12] for k, v in decl['동결_개정_뼈대_sha256'].items()} } · 현재 "
        f"{str(decl.get('현재_sha256'))[:12]}… (동결 뒤 개정은 예상된 차이라 기록만 한다)")
    gates["G0_입력사슬"] = {"항목": rows, "뼈대": decl, "sha256": sha, "통과": all(rows.values())}
    check(all(rows.values()), "입력 사슬이 끊겼다(동결 해시 · 11 정본 · 09-1 함수 · 예측 원문 가운데 다른 것이 있다).")
    return sha, freeze, j11


# ════════════════════════════════════════════════════════════════════════
# [G1] ver.1 재현
# ════════════════════════════════════════════════════════════════════════
def gate_ver1(bundle, j11, gates):
    line("[G1] ver.1 재현: 11 코드로 11 입력에서 교차검증 · 고정 모델을 다시 만든다")
    ok_in, gate_in, D = m11.load_and_gate()
    check(ok_in, "11 입력 정합 관문 실패")
    X, y, ids, fn = D["X"], D["y"], D["ids"], D["feat_names"]
    idx_of = {u: i for i, u in enumerate(ids)}
    units = [(idx_of[b_], idx_of[h_]) for b_, h_, _ in D["pairs"]]
    blocks = np.array([b_ for b_, _ in fn])
    abl_cols = {a: np.where(np.isin(blocks, bl))[0] for a, bl in m11.ABLATIONS.items()}
    res = {}
    res["번들_자질순서"] = [list(x) for x in bundle["feature_order"]] == [list(x) for x in fn]
    res["번들_기능어"] = list(bundle["function_words"]) == list(D["fw"])
    res["번들_축지도"] = bundle["axis_map"] == D["axis_map"]
    res["번들_train_ids"] = list(bundle["train_ids"]) == list(ids)

    cv = m11.run_cv(X, y, units, abl_cols, m11.SEED, "G1 재현: 매칭 1,024 교차검증")
    auc_diff = {a: abs(cv["table"][a]["OOF"]["AUC"] - j11["여덟행표"][a]["OOF"]["AUC"])
                for a in j11["여덟행표"]}
    res["여덟행_OOF_AUC_최대차"] = max(auc_diff.values())
    n_bad = 0
    for a, sc in j11["OOF점수"].items():
        n_bad += sum(1 for u, v in sc.items() if cv["oof"][a][idx_of[u]] != v)
    res["계정별_OOF점수_불일치"] = n_bad
    res["fold배정_같음"] = all(int(cv["fold_of"][idx_of[u]]) == f
                            for u, f in j11["fold배정"]["계정"].items())

    label_use("G1 재현: 1,024 전체 재적합(학습 라벨)")
    fx = m11.fit_all(X, y, np.arange(len(y)), {m11.ROW_POS: abl_cols[m11.ROW_POS]}, m11.EXTRAS_MAIN)
    same_prep = (all(np.array_equal(fx["prep"]["xp"][j], bundle["percentile_xp"][j])
                     and np.array_equal(fx["prep"]["fp"][j], bundle["percentile_fp"][j])
                     for j in range(X.shape[1]))
                 and np.array_equal(fx["prep"]["median"], bundle["impute_raw_median"]))
    lr = fx["models"][m11.ROW_POS]
    same_lr = (np.array_equal(lr.coef_[0], bundle["coef"]) and float(lr.intercept_[0]) == bundle["intercept"]
               and np.array_equal(bundle["model"].coef_, lr.coef_))
    same_sp = all(np.array_equal(fx["spread"][k], bundle["spread"][k]) for k in m11.SPREAD_KEYS)
    same_rf = m11.rf_same(fx["rf"][m11.ROW_BASE]["model"], bundle["rf"])
    thr = {r: m11.choose_threshold(cv["oof"][r], y)[0] for r in bundle["thresholds"]}
    res.update({"재적합_분위함수_중앙값": same_prep, "재적합_로지스틱": same_lr, "재적합_중심퍼짐keep": same_sp,
                "재적합_랜덤포레스트_나무구조": same_rf, "네_문턱": thr == dict(bundle["thresholds"])})

    fit1 = fit_from_bundle(bundle)
    P = m11.apply_prep(fit1["prep"], X)
    s_sk = bundle["model"].predict_proba(P)[:, 1]
    s_manual = m11.sigmoid(bundle["intercept"] + P @ bundle["coef"])
    res["번들_손공식=predict_proba(최대차)"] = float(np.max(np.abs(s_manual - s_sk)))
    ins = m11.metrics(s_sk, y, bundle["threshold"])
    res["학습표본내_지표=11JSON"] = jsonable(ins) == j11["고정모델"]["참고_학습표본내_지표(낙관적)"]
    ok = (res["번들_자질순서"] and res["번들_기능어"] and res["번들_축지도"] and res["번들_train_ids"]
          and res["여덟행_OOF_AUC_최대차"] == 0.0 and n_bad == 0 and res["fold배정_같음"]
          and same_prep and same_lr and same_sp and same_rf and res["네_문턱"]
          and res["번들_손공식=predict_proba(최대차)"] < 1e-12 and res["학습표본내_지표=11JSON"])
    for k, v in res.items():
        say(f"  {k:<36} {v}")
    res["통과"] = ok
    gates["G1_ver1재현"] = res
    check(ok, "ver.1 번들 또는 11 코드가 11 정본 결과를 차이 0으로 재현하지 못한다.")
    pairs11 = j11["fold배정"]["쌍"]
    v1_bots = {p[0] for p in pairs11}
    v1_hums = {p[1] for p in pairs11}
    check(v1_bots | v1_hums == set(bundle["train_ids"]) and len(v1_bots) == 512,
          "11 JSON 쌍과 번들 train_ids가 다르다")
    say(f"  → G1 통과. ver.1 학습 봇 {len(v1_bots)} · 사람 {len(v1_hums)}")
    return v1_bots, v1_hums


# ════════════════════════════════════════════════════════════════════════
# [12-1 적재] 계약(머리말)대로 관대하게 읽고, 모순은 멈춘다
# ════════════════════════════════════════════════════════════════════════
def _alias_table():
    rows = []
    for mid, als in MODEL_ALIASES.items():
        for a in set(als) | {mid.lower(), mid.lower().replace("/", "_"), mid.lower().replace("/", "-"),
                             mid.split("/")[1].lower()}:
            rows.append((a.lower(), mid))
    rows.sort(key=lambda r: -len(r[0]))
    return rows


ALIAS_ROWS = _alias_table()


def model_from_value(v, slot_model):
    v = str(v).strip()
    if v in slot_model.values() or v == MODEL_REGEN:
        return v
    if v in slot_model:
        return slot_model[v]
    low = v.lower()
    for a, mid in ALIAS_ROWS:
        if low == a:
            return mid
    for mid in sorted(set(slot_model.values()) | {MODEL_REGEN}, key=len, reverse=True):
        if low.startswith(mid.lower() + "-") or low.startswith(mid.lower() + ":"):
            return mid          # 날짜 붙은 응답 모델명(예: openai/gpt-4o-mini-2024-07-18)
    return None


def model_from_uid(uid):
    """uid 접두 별칭. 접두에 없으면 마지막 조각(원 봇 uid)을 뺀 '_' 조각에서 하나로 정해질 때만."""
    low = uid.lower()
    for a, mid in ALIAS_ROWS:
        if low.startswith(a) and len(low) > len(a) and low[len(a)] in "_-:|.":
            return mid
    hits = {mid for tok in low.split("_")[:-1] for a, mid in ALIAS_ROWS if tok == a}
    return hits.pop() if len(hits) == 1 else None


def persona_of(uid, r, by_pid, pid_of_uid):
    pid = r.get("페르소나id")
    if pid:
        check(pid in by_pid, f"12-1 {uid}: 페르소나id {pid}가 509 밖이다")
        return pid, "페르소나id 필드"
    ou = r.get("원봇uid")
    if ou:
        check(ou in pid_of_uid, f"12-1 {uid}: 원봇uid {ou}가 509 밖이다")
        return pid_of_uid[ou], "원봇uid 필드"
    tail = uid.rsplit("_", 1)[-1]
    if tail in pid_of_uid:
        return pid_of_uid[tail], "uid 꼬리"
    m = re.search(r"(?<![A-Za-z0-9])P\d{3}(?![0-9])", uid)
    if m and m.group(0) in by_pid:
        return m.group(0), "uid 안 P###"
    return None, None


def load_121(path, acc130_ids, mode):
    line("[적재] 12-1 계정사전 (계약: 머리말 '12-1 입력 계약')")
    check(os.path.exists(path), f"12-1 산출이 없다: {path}")
    raw = load_json(path)
    conf = raw.get("설정") or {}
    check(conf.get("관문통과") is True, "12-1 설정.관문통과가 true가 아니다. 이 파일을 쓰지 않는다.")
    check(isinstance(raw.get("계정"), dict), "12-1 최상위에 '계정' 사전이 없다")
    if mode == "본실행":
        check(not conf.get("smoke") and not conf.get("시험입력") and not conf.get("합성"),
              "본 실행인데 12-1이 smoke · 시험입력 · 합성 산출이다")
    gen, rep = parse_records(raw["계정"], acc130_ids)
    rep = {"sha256": sha256_file(path), "설정_키": list(conf)[:40], "설정_관문통과": conf.get("관문통과"), **rep}
    say(f"  적재 {len(gen)}계정 · 건너뜀 {rep['건너뜀']} · 모델 출처 {rep['모델_출처']} · "
        f"페르소나 출처 {rep['페르소나_출처']}")
    if rep["모델필드_접두_불일치수"]:
        say(f"  주의: 모델 필드와 uid 접두가 다른 계정 {rep['모델필드_접두_불일치수']} (필드를 따름)")
    return gen, rep, raw


def check_121_summary(in121, mode, sha121):
    """
    D15: 12-1 계정사전 sha256을 12-1_생성댓글파싱_요약.json의 산출.sha256과 대조한다. 본 실행은 이 폴더의
    요약, 점검 실행은 입력 파일 폴더의 12-1_생성댓글파싱_요약*.json(산출.계정사전이 입력 경로인 것을 우선).
    다르면 거부한다. 요약이나 기록이 없으면 경고하고 적는다.
    """
    if mode == "본실행":
        cands = [f"{HERE}/12-1_생성댓글파싱_요약.json"]
    else:
        cands = sorted(glob.glob(os.path.join(os.path.dirname(in121), "12-1_생성댓글파싱_요약*.json")))
    cands = [c for c in cands if os.path.exists(c)]
    rec = {"후보": [os.path.basename(c) for c in cands], "12-1_sha256": sha121}
    summ = None
    for c in cands:
        d = load_json(c)
        if nfc(str((d.get("산출") or {}).get("계정사전") or "")) == in121 or len(cands) == 1:
            summ, rec["요약"] = d, os.path.basename(c)
            break
    if summ is None:
        rec.update({"상태": "경고: 12-1 요약을 찾지 못했다", "통과": True})
        say(f"  경고: 12-1 요약이 없다(후보 {rec['후보']}). sha256 대조를 못 하고 기록만 한다.")
        return rec
    rec["요약_관문통과"] = summ.get("관문통과")
    rec_sha = (summ.get("산출") or {}).get("sha256")
    if rec_sha is None:
        rec.update({"상태": "경고: 요약에 산출.sha256이 없다", "통과": True})
        say("  경고: 12-1 요약에 산출.sha256이 없다. 기록만 한다.")
        return rec
    rec.update({"요약_sha256": rec_sha, "상태": "대조", "통과": rec_sha == sha121})
    say(f"  12-1 sha256 = 요약 기록: {'같음' if rec_sha == sha121 else '■ 다름'}")
    check(rec_sha == sha121, "12-1 계정사전 sha256이 12-1 요약 기록과 다르다. 이 파일을 쓰지 않는다.")
    return rec


def parse_records(records, acc130_ids):
    """12-1 계정 기록(본 계정 또는 민감도 계정)을 계약대로 읽는다. 모순은 멈춘다."""
    by_pid, pid_of_uid, slot_model = CTX.by_pid, CTX.pid_of_uid, CTX.slot_model
    gen, skip, how_m, how_p = {}, Counter(), Counter(), Counter()
    disagree, seen = [], {}
    for uid in sorted(records):
        r = records[uid]
        if r.get("집단") in OLD_GROUPS or uid.startswith("MIM_") or uid in acc130_ids:
            skip["13-0 집단 · MIM_ · 13-0 uid"] += 1
            continue
        if r.get("적격") is False:
            skip["적격 false"] += 1
            continue
        mf = next((r[f] for f in ("모델", "생성모델", "model") if r.get(f)), None)
        m_field = model_from_value(mf, slot_model) if mf is not None else None
        check(mf is None or m_field is not None, f"12-1 {uid}: 모델 값 '{mf}'을 모델 칸에 대응시킬 수 없다")
        m_uid = model_from_uid(uid)
        if m_field and m_uid and m_field != m_uid:
            disagree.append([uid, m_field, m_uid])
        model = m_field or m_uid
        check(model is not None, f"12-1 {uid}: 모델을 알 수 없다(모델 필드도 uid 접두 별칭도 없음)")
        how_m["모델 필드" if m_field else "uid 접두"] += 1
        pid, src = persona_of(uid, r, by_pid, pid_of_uid)
        check(pid is not None, f"12-1 {uid}: 페르소나를 알 수 없다")
        how_p[src] += 1
        miss = [f for f in MEAS_FIELDS if f not in r]
        check(not miss, f"12-1 {uid}: 측정 필드 없음 {miss}")
        if r["문서수"] < MIN_DOCS:
            skip["문서 10건 미만"] += 1
            continue
        check(len(r["문장길이"]) == r["문장수"] and sum(r["문장길이"]) == r["토큰수_구두점제외"],
              f"12-1 {uid}: 문장길이와 문장수 · 토큰수_구두점제외가 맞지 않는다(13-0 G7)")
        grp = GRP_REGEN if model == MODEL_REGEN else GRP_NEW
        g_in = r.get("집단")
        if g_in in (GRP_NEW, GRP_REGEN):
            check(g_in == grp, f"12-1 {uid}: 집단 {g_in}과 모델 {model}이 맞지 않는다")
        p = by_pid[pid]
        if grp == GRP_NEW:
            check(model == slot_model[p["모델슬롯"]],
                  f"12-1 {uid}: 모델 {model} ≠ 페르소나 {pid} 배정 {slot_model[p['모델슬롯']]}")
        if r.get("쪽") is not None:
            check(r["쪽"] == p["쪽"], f"12-1 {uid}: 쪽 {r['쪽']} ≠ 분할 {p['쪽']}")
        key = (pid, grp)
        check(key not in seen, f"페르소나 {pid}의 {grp} 계정이 둘이다: {seen.get(key)} · {uid}")
        seen[key] = uid
        rec = {"집단": grp, "모델": model, "페르소나id": pid, "원봇uid": p["원봇uid"], "쪽": p["쪽"],
               "모델슬롯": p["모델슬롯"], "라벨": "bot"}
        rec.update({f: r[f] for f in MEAS_FIELDS})
        for f in ("슬롯id목록", "문서별", "문서"):
            if f in r:
                rec[f] = r[f]
        gen[uid] = rec
    return gen, {"적재계정": len(gen), "건너뜀": dict(skip), "모델_출처": dict(how_m),
                 "페르소나_출처": dict(how_p), "모델필드_접두_불일치": disagree[:20],
                 "모델필드_접두_불일치수": len(disagree)}


def survival_table(gen):
    tab = {}
    for grp in (GRP_NEW, GRP_REGEN):
        for slot in SLOTS:
            m = CTX.slot_model[slot]
            for side in ("학습", "시험"):
                n = sum(1 for r in gen.values() if r["집단"] == grp and r["모델슬롯"] == slot and r["쪽"] == side)
                tab[f"{grp}|{slot}|{m}|{side}"] = n
    return tab


# ════════════════════════════════════════════════════════════════════════
# [4절] 칸 판정가능 여부: 칸 생존 계정 × 표 (a) 640 매칭 쌍 수
# ════════════════════════════════════════════════════════════════════════
def cell_status(accs, gen, tag):
    label_use(f"{tag}: 4절 칸 판정(칸 봇 × 표 (a) 사람 640 캘리퍼 매칭)")
    out = {}
    for slot in SLOTS:
        m = CTX.slot_model[slot]
        bots = [u for u, r in gen.items() if r["집단"] == GRP_NEW and r["모델"] == m]
        pairs, un, _ = match(accs, bots, CTX.tab_a)
        out[slot] = {"모델": m, "생존계정": len(bots),
                     "쪽별": dict(Counter(gen[u]["쪽"] for u in bots)),
                     "표a매칭쌍": len(pairs), "판정가능": len(pairs) >= N_MIN}
        say(f"  {slot} {m:<30} 생존 {len(bots):>3} · 표a 매칭 쌍 {len(pairs):>3} → "
            f"{'판정가능' if len(pairs) >= N_MIN else '판정불가(4절)'}")
    return out


# ════════════════════════════════════════════════════════════════════════
# [5절 5 · 6항] 학습: 쪽 안 캘리퍼 매칭 → 11 v2.1 교차검증 → 비중 규칙 → 고정 모델
# ════════════════════════════════════════════════════════════════════════
def tools4():
    return (m11.ROW_BASE, m11.ROW_POS, m11.ROW_SPREAD, m11.ROW_PROP)


def select_weight(C_of, grid, Wb, Wh, bidx_by_m, p124, family_ok=True):
    """
    [라벨 사용] 5절 5항 비중 규칙(D7). 1:1이 기본이다. 다섯이 모두 성립할 때만 argmax로 바꾼다.
    grid: w → OOF 제안 점수. C_of: 점수 → 봇 × 사람 비교 행렬.
    (라) p124["천장깨짐"]: 이 학습 표본의 P12-4식 판정(판정가능이고 구간이 ±0.02 띠 밖에 통째로).
    (마) family_ok: ver.2 계열은 본 실행 ver.2의 P12-4가 적중일 때만 참(뼈대 5절 5 구현 결정 ①).
         대조 행은 자기 (라)만 본다(참으로 넘긴다).
    비교는 허용오차 1e-12로 한다(구현 결정 ④). 0.01 이득이 부동소수 오차로 떨어지지 않게 한다.
    """
    auc = {w: float(C_of(grid[w]).mean()) for w in WEIGHT_GRID}
    best = sorted(WEIGHT_GRID, key=lambda w: (-auc[w], abs(w - 0.5), w))[0]
    Cb, Ch = C_of(grid[best]), C_of(grid[0.5])
    gain = auc[best] - auc[0.5]
    d = boot_auc(Cb, Wb, Wh) - boot_auc(Ch, Wb, Wh)
    lo, hi = ci95(d)

    def min_model(C):
        return min(float(C[ix].mean()) for ix in bidx_by_m.values())

    mm_best, mm_half = min_model(Cb), min_model(Ch)
    cond = {"(가) 이득≥0.01": gain >= WEIGHT_GAIN - TOL, "(나) 이득 하한>0": lo > 0,
            "(다) 최저모델AUC 유지": mm_best >= mm_half - TOL,
            "(라) 이 표본 천장 깨짐": bool(p124.get("천장깨짐")), "(마) 계열 관문": bool(family_ok)}
    switch = best != 0.5 and all(cond.values())
    w = best if switch else 0.5
    return w, {"격자_OOF_AUC": {str(k): v for k, v in auc.items()}, "argmax": best, "이득": gain,
               "이득_CI95": [lo, hi], "최저모델AUC_argmax": mm_best, "최저모델AUC_1:1": mm_half,
               "조건": cond, "선택_위치비중": w, "바뀜": switch,
               "규칙": "D7: 1:1 기본, 조건 (가)~(마) 모두 성립할 때만 argmax. 비교 허용오차 1e-12"}


def p124_stat(per_model, dist_m, models_all, n_by_model, cells_ok):
    """
    P12-4식 통계(뼈대 5절 5 구현 결정 ①, D11).
        Δ_m = AUC(위치) − AUC(퍼짐)   (모델 m의 매칭 학습 봇 × 매칭 학습 사람 전부, OOF 점수)
        통계 = Δ_m의 모델 평균(부호 유지), 구간 = 같은 재추출 위의 평균의 백분위 95%
        천장 깨짐 = 구간이 [−0.02, +0.02] 띠 밖에 통째로 있다(어느 쪽이든)
        판정불가 = 후보 모델 가운데 매칭 학습 봇 30 미만이 있거나 4절 판정불가 칸이 있다
    옛 통계(|Δ_m| 평균)는 참 차이가 0이어도 양으로 치우쳐(적대 검증 e4) 참고로만 적는다.
    """
    pos, spr = m11.ROW_POS, m11.ROW_SPREAD
    present = [m for m in models_all if n_by_model.get(m, 0) > 0]
    delta = {m: per_model[m][pos]["AUC"] - per_model[m][spr]["AUC"] for m in present}
    few = {m: n_by_model.get(m, 0) for m in models_all if n_by_model.get(m, 0) < P124_MIN_BOTS}
    bad_cells = sorted(m for m, ok in (cells_ok or {}).items() if not ok)
    ok = bool(present) and not few and not bad_cells
    if present:
        pt = float(np.mean(list(delta.values())))
        lo, hi = ci95(np.mean([dist_m[(m, pos)] - dist_m[(m, spr)] for m in present], axis=0))
        f_pt = float(np.mean([abs(v) for v in delta.values()]))
        f_ci = ci95(np.mean([np.abs(dist_m[(m, pos)] - dist_m[(m, spr)]) for m in present], axis=0))
    else:
        pt, lo, hi, f_pt, f_ci = None, None, None, None, None
    outside = ok and (lo > P124_BAND or hi < -P124_BAND)
    verdict = "판정불가" if not ok else ("적중" if outside else "빗나감")
    return {"모델별_Δ(위치−퍼짐)": delta, "평균Δ": pt, "평균Δ_CI95": [lo, hi], "띠": [-P124_BAND, P124_BAND],
            "모델별_매칭학습봇": {m: n_by_model.get(m, 0) for m in models_all},
            "판정가능": ok, "판정불가_사유": {"매칭학습봇30미만": few, "4절판정불가칸": bad_cells},
            "천장깨짐": bool(outside), "판정": verdict,
            "참고_옛통계_절댓값평균(판정에 쓰지 않음)": {"점": f_pt, "CI95": f_ci},
            "규칙": "D11: 부호 있는 Δ_m 모델 평균의 95% 구간이 ±0.02 띠 밖에 통째로 있으면 천장 깨짐"}


def na_detector(tag, reason, info):
    """퇴화 경로(구현 결정 ③): 이 판별기만 판정불가로 두고 실행은 계속한다."""
    say(f"  ■ {tag}: 판정불가({reason}). 이 판별기만 빼고 계속한다.")
    return {"tag": tag, "판정불가": True, "사유": reason, "w": 0.5, "personas": set(), "humans": set(),
            "summary": {"이름": tag, "판정불가": True, "사유": reason, **info,
                        "P12-4통계": {"판정": "판정불가", "천장깨짐": False, "판정가능": False,
                                    "판정불가_사유": {"판별기": reason}}}}


def train_detector(tag, accs, bot_ids, strata_of, key, R, family_ok=True, cells_ok=None, expect_models=None):
    """
    판별기 하나를 학습한다(ver.2 · 대조 · 모델 하나 빼기 · 민감도가 모두 이 함수).
      1. 학습 봇 × 학습 사람 234를 09-1 규칙으로 매칭(쪽 안). 쌍이 100 미만이면 이 실행에만
         ver.1 학습 사람 406을 더해 다시 매칭한다(뼈대 5절 5 구현 결정 ②, D20).
      2. 쌍이 50 미만이면 이 판별기만 판정불가(구현 결정 ③). 실행은 계속한다.
      3. 11 run_cv: 쌍 단위 5겹, 학습 fold 분위 함수, 로지스틱 · 중심 거리 · 랜덤 포레스트,
         내부 5겹 문턱(11 v2.1 3~5단계 그대로)
      4. OOF 위치 · 퍼짐으로 P12-4식 통계와 비중 격자 → 5절 5항 규칙
      5. 매칭 표본 전체로 고정 모델(11 fit_all)
    """
    line(f"[학습] {tag}")
    base_h = list(CTX.train_hums)
    extra = list(getattr(CTX, "extra_hums", None) or sorted(set(CTX.tab_a) - set(CTX.train_hums)))
    check(not (set(base_h) & CTX.sealed_ids) and not (set(extra) & CTX.sealed_ids),
          f"{tag}: 시험 사람이 학습 사람 후보에 있다(G2)")
    check(not (set(base_h) & set(extra)), f"{tag}: 학습 사람 234와 ver.1 학습 사람 406이 겹친다")
    check(all(accs[u]["쪽"] == "학습" for u in bot_ids), f"{tag}: 학습 봇 가운데 시험 쪽 페르소나가 있다(G2)")
    label_use(f"{tag}: 봇 · 사람 집단으로 캘리퍼 매칭")
    pairs, unmatched, _ = match(accs, bot_ids, base_h)
    pool = {"사람풀": "학습 234", "1차매칭쌍": len(pairs), "ver1학습사람406_추가": False}
    hums = base_h
    if len(pairs) < PAIRS_FALLBACK:
        hums = base_h + extra
        pairs, unmatched, _ = match(accs, bot_ids, hums)
        pool = {"사람풀": "학습 234 + ver.1 학습 406", "1차매칭쌍": pool["1차매칭쌍"],
                "ver1학습사람406_추가": True, "추가뒤매칭쌍": len(pairs)}
        say(f"  매칭 쌍 {pool['1차매칭쌍']} < {PAIRS_FALLBACK}: 이 실행에만 ver.1 학습 사람 406을 더해 "
            f"다시 매칭 → {len(pairs)}쌍")
    # 기대 모델(칸)은 후보가 0이어도 센다. 칸이 통째로 비면 매칭 학습 봇 0 < 30 → P12-4식 판정불가
    models_all = sorted(set(strata_of[u] for u in bot_ids) | set(expect_models or ()))
    strata = [strata_of[b_] for b_, _, _ in pairs]
    info = {"봇후보": len(bot_ids), "봇후보_층별": dict(Counter(strata_of[u] for u in bot_ids)),
            "사람후보": len(hums), **pool, "매칭쌍": len(pairs), "매칭봇_층별": dict(Counter(strata)),
            "탈락봇_층별": dict(Counter(strata_of[u] for u in unmatched)),
            "학습페르소나수": len({accs[b_]["페르소나id"] for b_, _, _ in pairs})}
    say(f"  봇 후보 {len(bot_ids)} · 사람 후보 {len(hums)} · 매칭 쌍 {len(pairs)} · 탈락 봇 {len(unmatched)}")
    if len(pairs) < MIN_PAIRS_DET:
        return na_detector(tag, f"매칭 쌍 {len(pairs)} < {MIN_PAIRS_DET}", info)
    ids = [u for b_, h_, _ in pairs for u in (b_, h_)]
    check(not (set(ids) & CTX.sealed_ids), f"{tag}: 시험 사람이 학습 표본에 있다(G2)")
    X = feat(accs, ids)
    all_nan = np.where(np.isnan(X).all(axis=0))[0]
    if all_nan.size:
        return na_detector(tag, f"학습 표본 전체에서 결측인 자질 {all_nan.tolist()[:10]}"
                                "(11 v2.1 규칙이 정하지 않은 상황)", info)
    y = np.tile([1, 0], len(pairs))
    units = [(2 * i, 2 * i + 1) for i in range(len(pairs))]
    cv = m11.run_cv(X, y, units, CTX.abl, SEED, f"{tag} 쌍 단위 5겹", record_detail=False,
                    extras=m11.EXTRAS_MAIN)
    oof, fold_of = cv["oof"], cv["fold_of"]
    grid = {w: oof_wrank(oof[m11.ROW_POS], oof[m11.ROW_SPREAD], fold_of, w) for w in WEIGHT_GRID}
    check(np.array_equal(grid[0.5], oof[m11.ROW_PROP]), f"{tag}: OOF 가중 순위 평균(0.5) ≠ 11 제안 OOF")

    bidx = np.arange(0, len(ids), 2)
    hidx = np.arange(1, len(ids), 2)
    b_ids = [ids[i] for i in bidx]
    Wb = boot_counts((3, *key), strata, R)
    Wh = boot_counts((4, *key), [0] * len(hidx), R)

    def C_of(s):
        return cmp_matrix(s[bidx], s[hidx])

    bidx_by_m = {m: np.array([i for i, s in enumerate(strata) if s == m]) for m in sorted(set(strata))}
    label_use(f"{tag}: OOF 점수로 AUC · 모델별 AUC · P12-4식 통계 · 비중 선택")
    overall, per_model, dist_m = {}, {}, {}
    for t in tools4():
        C = C_of(oof[t])
        check(abs(float(C.mean()) - cv["table"][t]["OOF"]["AUC"]) < 1e-12, f"{tag}: 비교 행렬 AUC ≠ 11 OOF AUC")
        overall[t] = {"AUC": float(C.mean()), "CI95": ci95(boot_auc(C, Wb, Wh))}
        for m, ix in bidx_by_m.items():
            dm = boot_auc(C[ix], Wb[:, ix], Wh)
            dist_m[(m, t)] = dm
            per_model.setdefault(m, {})[t] = {"AUC": float(C[ix].mean()), "CI95": ci95(dm), "n_봇": int(ix.size)}
    n_by_model = {m: int(bidx_by_m[m].size) if m in bidx_by_m else 0 for m in models_all}
    p124 = p124_stat(per_model, dist_m, models_all, n_by_model, cells_ok)
    w, wsel = select_weight(C_of, grid, Wb, Wh, bidx_by_m, p124, family_ok)
    prop_w = grid[w]
    overall[f"{m11.ROW_PROP}(선택비중)"] = {"AUC": float(C_of(prop_w).mean()),
                                         "CI95": ci95(boot_auc(C_of(prop_w), Wb, Wh))}
    say("  OOF AUC " + " · ".join(f"{t} {v['AUC']:.4f}" for t, v in overall.items()))
    if p124["평균Δ"] is not None:
        say(f"  P12-4식: 평균 Δ(위치 − 퍼짐) {p124['평균Δ']:+.4f} [{p124['평균Δ_CI95'][0]:+.4f}, "
            f"{p124['평균Δ_CI95'][1]:+.4f}] · 띠 ±{P124_BAND} → {p124['판정']}")
    say(f"  비중: argmax w={wsel['argmax']} 이득 {wsel['이득']:+.4f} 조건 {wsel['조건']} → 위치 비중 {w}")

    label_use(f"{tag}: 고정 모델 적합(매칭 표본 전체) · OOF 문턱(기술)")
    fit = m11.fit_all(X, y, np.arange(len(y)), CTX.abl, m11.EXTRAS_MAIN)
    oof_sel = {t: oof[t] for t in (m11.ROW_BASE, m11.ROW_POS, m11.ROW_SPREAD)}
    oof_sel[m11.ROW_PROP] = prop_w
    thr = {t: m11.choose_threshold(s, y)[0] for t, s in oof_sel.items()}
    summary = {
        "이름": tag, "판정불가": False, **info,
        "OOF표": {t: {k: v for k, v in r.items() if k != "fold별"} for t, r in cv["table"].items()},
        "OOF_AUC_CI95": overall, "층별_OOF_AUC": per_model, "P12-4통계": p124, "비중선택": wsel,
        "문턱_기술": thr, "퍼짐제외_fold별": [fi.get("퍼짐_제외자질") for fi in cv["fold_info"]],
        "쌍": [[b_, h_, float(g)] for b_, h_, g in pairs],
    }
    return {"tag": tag, "판정불가": False, "pairs": pairs, "ids": ids, "X": X, "y": y, "units": units,
            "oof": oof, "oof_sel": oof_sel, "w": w, "fit": fit, "thr": thr, "summary": summary,
            "personas": {accs[u]["페르소나id"] for u in b_ids}, "humans": {ids[i] for i in hidx},
            "args": (bot_ids, strata_of, key, family_ok, cells_ok, expect_models)}


def p124_verdict(det):
    if det.get("판정불가"):
        return "판정불가"
    p = det["summary"]["P12-4통계"]
    return p.get("판정") or ("적중" if p.get("천장깨짐") else "빗나감")


def train_all(accs, gen, sens, R, cells=None, family_main=None):
    """
    ver.2 · 대조 · 모델 하나 빼기 넷을 학습한다(봉인 해제 전).
    ver.2 계열 관문(마): 본 실행(sens=0)의 ver.2 P12-4가 적중일 때만 계열(모델 하나 빼기 넷,
    민감도 ver.2 · 모델 하나 빼기)이 argmax 비중을 고를 수 있다. 빗나가거나 판정불가면 계열 전체 1:1.
    대조 행은 자기 P12-4식 검사(라)만 따른다.
    """
    newL = sorted(u for u, r in gen.items() if r["집단"] == GRP_NEW and r["쪽"] == "학습")
    regL = sorted(u for u, r in gen.items() if r["집단"] == GRP_REGEN and r["쪽"] == "학습")
    s_new = {u: gen[u]["모델"] for u in newL}
    s_reg = {u: CTX.slot_model[gen[u]["모델슬롯"]] for u in regL}   # 대조: 페르소나 배정 칸
    c_ok = None if cells is None else {CTX.slot_model[s]: cells[s]["판정가능"] for s in SLOTS}
    all_m = [CTX.slot_model[s] for s in SLOTS]
    tag = "민감도 " if sens else ""
    v2 = train_detector(f"{tag}ver.2 (새 모델 4, 학습 쪽)", accs, newL, s_new, (sens, 0), R,
                        family_ok=True if not sens else bool(family_main), cells_ok=c_ok, expect_models=all_m)
    fam = (p124_verdict(v2) == "적중") if not sens else bool(family_main)
    tr = {DET_V2: v2,
          DET_CTRL: train_detector(f"{tag}대조 (gpt-4o-mini 재생성, 학습 쪽)", accs, regL, s_reg, (sens, 1), R,
                                   expect_models=all_m),
          "LOMO": {},
          "계열관문": {"본_P12-4": p124_verdict(v2) if not sens else "(본 실행 판정을 따름)",
                    "ver.2계열_argmax허용": fam,
                    "규칙": "뼈대 5절 5 구현 결정 ①: P12-4가 빗나가거나 판정불가면 ver.2 계열 전체 1:1"}}
    for k, slot in enumerate(SLOTS, start=1):
        m = CTX.slot_model[slot]
        bots = [u for u in newL if gen[u]["모델"] != m]
        c3 = None if c_ok is None else {mm: v for mm, v in c_ok.items() if mm != m}
        tr["LOMO"][slot] = train_detector(f"{tag}ver.2 모델 하나 빼기: {m} 제외", accs, bots,
                                          {u: s_new[u] for u in bots}, (sens, 10 + k), R,
                                          family_ok=fam, cells_ok=c3, expect_models=[x for x in all_m if x != m])
    return tr


# ════════════════════════════════════════════════════════════════════════
# [G3 · G4]
# ════════════════════════════════════════════════════════════════════════
def gate_shuffle(det, gates):
    """
    [라벨 사용] 라벨 뒤섞기 20회(구현 결정 ④, D14). 회차 i의 가짜 라벨 =
    np.random.default_rng([20260926, i]).permutation(y). 위치 · 제안 OOF AUC의 20회 평균을
    경험 표준편차로 z검정한다. 누설은 AUC를 올리므로 관문은 위쪽 한쪽(z > 2.326, α 0.01)이다.
    평균이 유의하게 0.5보다 낮은 것은 교차검증 음의 편향(11 실측 0.466)이라 경고만 한다.
    11 범위(0.45~0.55) 밖 회차도 경고로 적는다.
    """
    line(f"[G3] 라벨 뒤섞기 {N_SHUFFLE}회: ver.2 학습 표본에서 위치 · 제안 OOF AUC 평균을 0.5와 비교")
    if det.get("판정불가"):
        gates["G3_라벨뒤섞기"] = {"해당없음": "ver.2 판정불가", "통과": True}
        say("  ver.2가 판정불가라 해당 없음")
        return
    label_use("G3: 가짜 라벨로 교차검증 20회")
    rows = (m11.ROW_POS, m11.ROW_PROP)
    vals = {r: [] for r in rows}
    for i in range(N_SHUFFLE):
        y_sh = np.random.default_rng([SEED, i]).permutation(det["y"])
        with contextlib.redirect_stdout(io.StringIO()):
            cv = m11.run_cv(det["X"], y_sh, det["units"], CTX.abl, SEED, f"G3 뒤섞기 {i}",
                            record_detail=False, extras=(m11.ROW_PROP,))
        for r in rows:
            vals[r].append(cv["table"][r]["OOF"]["AUC"])
        say(f"  {i + 1:>2}/{N_SHUFFLE} " + " · ".join(f"{r} {vals[r][-1]:.4f}" for r in rows))
    res, warn = {}, []
    for r, v in vals.items():
        v = np.array(v)
        mean, sd = float(v.mean()), float(v.std(ddof=1))
        se = sd / math.sqrt(len(v))
        z = (mean - 0.5) / se if se > 0 else (0.0 if mean == 0.5 else math.copysign(math.inf, mean - 0.5))
        out11 = int(np.sum((v < 0.45) | (v > 0.55)))
        res[r] = {"값": v, "평균": mean, "표준편차": sd, "z": z, "위쪽유의(관문 불통과)": z > SHUFFLE_Z,
                  "아래쪽유의(경고)": z < -SHUFFLE_Z, "11범위밖_회수(경고)": out11}
        say(f"  {r}: 평균 {mean:.4f} · 표준편차 {sd:.4f} · z {z:+.2f} (관문: z ≤ {SHUFFLE_Z})")
        if out11:
            warn.append(f"{r} {out11}/{N_SHUFFLE}회가 11 범위 0.45~0.55 밖")
        if z < -SHUFFLE_Z:
            warn.append(f"{r} 평균이 0.5보다 유의하게 낮다(교차검증 음의 편향, 누설 신호 아님)")
    for w_ in warn:
        say(f"  경고: {w_}")
    ok = all(not x["위쪽유의(관문 불통과)"] for x in res.values())
    gates["G3_라벨뒤섞기"] = {"회수": N_SHUFFLE, "도구별": res, "경고": warn, "방식": "D14", "통과": ok}
    check(ok, "라벨 뒤섞기 AUC 평균이 0.5보다 유의하게 높다(누설 의심).")


def same_fit(a, b):
    ok = all(np.array_equal(x, y) for x, y in zip(a["prep"]["xp"], b["prep"]["xp"]))
    ok &= all(np.array_equal(x, y) for x, y in zip(a["prep"]["fp"], b["prep"]["fp"]))
    ok &= np.array_equal(a["prep"]["median"], b["prep"]["median"])
    ok &= np.array_equal(a["models"][m11.ROW_POS].coef_, b["models"][m11.ROW_POS].coef_)
    ok &= np.array_equal(a["models"][m11.ROW_POS].intercept_, b["models"][m11.ROW_POS].intercept_)
    ok &= all(np.array_equal(a["spread"][k], b["spread"][k]) for k in m11.SPREAD_KEYS)
    ok &= m11.rf_same(a["rf"][m11.ROW_BASE]["model"], b["rf"][m11.ROW_BASE]["model"])
    return bool(ok)


def gate_determinism(det, accs, R, gates):
    line("[G4] 결정성: ver.2 학습을 같은 프로세스에서 다시 돌린다")
    if det.get("판정불가"):
        gates["G4_결정성"] = {"해당없음": "ver.2 판정불가", "통과": True}
        say("  ver.2가 판정불가라 해당 없음")
        return
    bot_ids, strata_of, key, family_ok, cells_ok, expect_models = det["args"]
    d2 = train_detector("ver.2 (결정성 재실행)", accs, bot_ids, strata_of, key, R, family_ok, cells_ok,
                        expect_models)

    def body(s):    # 이름(학습 표시)만 다르다
        return json.dumps(jsonable({k: v for k, v in s.items() if k != "이름"}), sort_keys=True,
                          ensure_ascii=False)

    res = {"매칭쌍": det["pairs"] == d2["pairs"],
           "OOF점수": all(np.array_equal(det["oof"][t], d2["oof"][t]) for t in det["oof"]),
           "비중": det["w"] == d2["w"], "고정모델": same_fit(det["fit"], d2["fit"]),
           "요약": body(det["summary"]) == body(d2["summary"])}
    for k, v in res.items():
        say(f"  {k:<8} {'같음' if v else '■ 다름'}")
    res["통과"] = all(res.values())
    gates["G4_결정성"] = res
    check(res["통과"], "ver.2 학습이 결정적이지 않다.")


def save_bundle(det, path, in121_sha):
    """ver.2 번들: 11 번들과 같은 꼴 + 비중. 재적재 검산 뒤 sha256을 돌려준다."""
    fit = det["fit"]
    lr = fit["models"][m11.ROW_POS]
    sp = fit["spread"]
    w = det["w"]
    bundle = {
        "설명": ("12 판별기 ver.2 (12-3_판별기ver2.py). 11 번들과 같은 꼴이다. 공통 전처리: 원값 x"
                 "(feature_order, 결측 NaN) → impute_raw_median → p_j = clip(interp(x_j, percentile_xp[j], "
                 "percentile_fp[j]), 0, 1). 위치: sigmoid(intercept + coef·p). 퍼짐: keep 자질 위 d_h − d_b. "
                 "기준선: rf.predict_proba(p)[:, 1]. 제안: 채점 묶음 안 평균 순위를 proposal_weights(위치, 퍼짐)로 "
                 "가중 평균한 r̄, (r̄ − 1)/(n − 1). 문턱은 기술 보고용이다."),
        "feature_order": CTX.bundle11["feature_order"],
        "percentile_xp": fit["prep"]["xp"], "percentile_fp": fit["prep"]["fp"],
        "impute_raw_median": fit["prep"]["median"],
        "coef": lr.coef_[0].copy(), "intercept": float(lr.intercept_[0]), "model": lr,
        "lr_params": m11.LR_PARAMS,
        "spread": {k: sp[k].copy() for k in m11.SPREAD_KEYS}, "spread_floor": m11.SPREAD_FLOOR,
        "spread_floored": dict(sp["floored"]), "spread_excluded": m11.spread_exclusion(sp, m11.FEATURE_BLOCKS),
        "rf": fit["rf"][m11.ROW_BASE]["model"], "rf_params": m11.RF_PARAMS,
        "proposal_weights": (w, 1.0 - w), "weight_selection": det["summary"]["비중선택"],
        "thresholds": det["thr"], "threshold_rule": "score >= threshold → bot (기술 보고용)",
        "axis_map": CTX.axis_map, "function_words": CTX.keys["F"], "funcword_hash": FW_HASH,
        "train_ids": det["ids"], "train_pairs": [[b_, h_] for b_, h_, _ in det["pairs"]],
        "human_pool": det["summary"]["사람풀"], "seed": SEED,
        "ver1_bundle_sha256": BUNDLE11_SHA, "input_121_sha256": in121_sha,
        "versions": {"numpy": np.__version__, "sklearn": sklearn.__version__,
                     "python": platform.python_version()},
        "created_at": datetime.now().astimezone().isoformat(),
    }
    check(os.path.dirname(path) == OUT_DIR, "번들을 산출 폴더 밖에 쓰려 한다")
    joblib.dump(bundle, path)
    sha = sha256_file(path)
    bl = joblib.load(path)      # 방금 이 실행이 쓴 파일만 읽는다(pickle)
    a, b = score(fit, w, det["X"]), score(fit_from_bundle(bl), bl["proposal_weights"][0], det["X"])
    check(all(np.array_equal(a[t], b[t]) for t in a), "ver.2 번들 재적재 점수가 적합 직후와 다르다")
    say(f"  ver.2 번들 저장 · 재적재 검산 통과 · sha256 {sha}")
    return sha


# ════════════════════════════════════════════════════════════════════════
# [시험] 채점 묶음 하나 = 시험 봇 + 시험 사람 234
# ════════════════════════════════════════════════════════════════════════
class TestSet:
    """
    시험 집합 하나. 같은 집합 위의 모든 판별기는 같은 재추출 행렬(Wb, Wh)을 쓴다.
    그래서 두 판별기의 AUC 차 구간은 짝지은 부트스트랩이다. Wh는 모든 집합이 공유한다.
    시험 봇이 2 미만인 집합은 만들지 않는다(evaluate가 판정불가 행으로 대신한다).
    """

    def __init__(self, name, accs, bots, strata, key, R):
        self.name, self.bots, self.hums = name, list(bots), list(CTX.test_hums)
        check(len(self.bots) >= 2, f"{name}: 시험 봇이 2계정 미만")
        self.nb = len(self.bots)
        self.y = np.array([1] * self.nb + [0] * len(self.hums))
        self.X = feat(accs, self.bots + self.hums)
        self.Wb = boot_counts(key, strata, R)
        self.Wh = CTX.Wh_test
        self.sc, self._C = {}, {}

    def add(self, det, scores):
        self.sc[det] = scores

    def auc(self, det, tool):
        k = (det, tool)
        if k not in self._C:
            s = self.sc[det][tool]
            C = cmp_matrix(s[:self.nb], s[self.nb:])
            check(abs(float(C.mean()) - roc_auc_score(self.y, s)) < 1e-12, "비교 행렬 AUC ≠ roc_auc_score")
            self._C[k] = (float(C.mean()), boot_auc(C, self.Wb, self.Wh))
        return self._C[k]

    def row(self, det, thresholds, g5):
        out = {"집합": self.name, "판별기": det, **g5, "도구": {}}
        for t in tools4():
            pt, dist = self.auc(det, t)
            out["도구"][t] = {"AUC": pt, "CI95": ci95(dist), "문턱": thresholds[t],
                            "문턱지표_기술": m11.metrics(self.sc[det][t], self.y, thresholds[t])}
        return out

    def diff(self, da, db, g5_ok):
        res = {}
        for t in tools4():
            pa, xa = self.auc(da, t)
            pb, xb = self.auc(db, t)
            lo, hi = ci95(xa - xb)
            tie = pa >= CEILING and pb >= CEILING
            res[t] = {"차": pa - pb, "CI95": [lo, hi], "천장동률": tie,
                      "판정가능": bool(g5_ok and not tie), "하한>0": lo > 0}
        return res


def na_row(name, det, nb, nh, reason, cell_ok=None):
    return {"집합": name, "판별기": det, **g5_flags(nb, nh, cell_ok), "판정가능": False, "사유": reason,
            "도구": None}


def na_diff(reason):
    return {t: {"차": None, "CI95": None, "천장동률": None, "판정가능": False, "하한>0": False, "사유": reason}
            for t in tools4()}


def out_of_range(ts):
    """
    뼈대 5절 9 "범위 밖 백분위 칸 비율"(구현 결정 ⑤, D22). 결측이 아닌 원값 칸 가운데 ver.1 학습
    분위 함수의 범위(xp 최솟값 ~ 최댓값) 밖이라 0 또는 1로 잘린 칸의 비율. 학습값이 한 가지뿐인
    자질(분위 함수가 상수 0.5)은 자르기가 일어나지 않으므로 분모에서 뺀다. 봇 · 사람을 따로, 블록별로.
    """
    xp = CTX.bundle11["percentile_xp"]
    lo = np.array([x[0] for x in xp])
    hi = np.array([x[-1] for x in xp])
    eff = np.array([len(x) > 1 for x in xp])
    blocks = m11.FEATURE_BLOCKS
    out = {}
    for name, M in (("봇", ts.X[:ts.nb]), ("사람", ts.X[ts.nb:])):
        ok = ~np.isnan(M) & eff[None, :]
        below = np.zeros(M.shape, dtype=bool)
        above = np.zeros(M.shape, dtype=bool)
        below[ok] = (M < lo[None, :])[ok]
        above[ok] = (M > hi[None, :])[ok]
        n = int(ok.sum())
        out[name] = {"칸수": n, "전체": float((below | above).sum() / n) if n else None,
                     "0으로": float(below.sum() / n) if n else None, "1로": float(above.sum() / n) if n else None,
                     "블록별": {bl: (float((below | above)[:, blocks == bl].sum() / ok[:, blocks == bl].sum())
                                  if ok[:, blocks == bl].sum() else None) for bl in m11.BLOCK_SIZES}}
    return out


def say_rows(rows, title):
    say(f"\n  {title}")
    say("  집합                                   판별기        n봇  n사람 판정  "
        "위치 AUC [95%]            퍼짐 AUC     제안 AUC [95%]            기준선   범위밖(봇 R)")
    for r in rows:
        if r["도구"] is None:
            say(f"  {r['집합']:<38} {r['판별기']:<12} {r['n_봇']:>4} {r['n_사람']:>5} 불가  ({r['사유']})")
            continue
        d = r["도구"]
        p, s, q, b = d[m11.ROW_POS], d[m11.ROW_SPREAD], d[m11.ROW_PROP], d[m11.ROW_BASE]
        orr = (r.get("범위밖_백분위칸비율") or {}).get("봇", {}).get("블록별", {}).get("R")
        say(f"  {r['집합']:<38} {r['판별기']:<12} {r['n_봇']:>4} {r['n_사람']:>5} "
            f"{'가능' if r['판정가능'] else '불가'}  "
            f"{p['AUC']:.4f} [{p['CI95'][0]:.4f}, {p['CI95'][1]:.4f}]  {s['AUC']:.4f}  "
            f"{q['AUC']:.4f} [{q['CI95'][0]:.4f}, {q['CI95'][1]:.4f}]  {b['AUC']:.4f}   "
            f"{'' if orr is None else f'{orr:.3f}'}")


def evaluate(accs, gen, tr, cells, sens, R):
    """
    [라벨 사용] 봉인 해제 뒤. 5절 4항(ver.1 적용) · 7항(모델 하나 빼기 · 보조)을 계산한다.
    퇴화 경로(구현 결정 ③): 시험 봇 2 미만 칸은 그 칸의 행 · P12-3 항 · 모델 하나 빼기 회차를
    판정불가로 두고, 판정불가 판별기는 그 판별기가 든 비교만 판정불가로 둔다.
    """
    tag = "민감도 " if sens else ""
    line(f"[시험] {tag}5절 4항 ver.1 적용 · 7항 ver.2 시험 (봉인 해제 뒤)")
    label_use(f"{tag}시험 봇 · 시험 사람 라벨로 AUC · 부트스트랩 구간")
    v1 = CTX.v1fit
    thr1 = dict(CTX.bundle11["thresholds"])
    nh = len(CTX.test_hums)
    out = {"ver1적용": [], "P12-3재료": {}, "LOMO": [], "보조": None}
    sets = {}

    def v1_row(name, bots, strata, key, cell_ok=None):
        if len(bots) < 2:
            return None, na_row(name, DET_V1, len(bots), nh, "시험 봇 2 미만", cell_ok)
        ts = TestSet(name, accs, bots, strata, key, R)
        ts.add(DET_V1, score(v1, 0.5, ts.X))
        row = ts.row(DET_V1, thr1, g5_flags(ts.nb, nh, cell_ok))
        row["범위밖_백분위칸비율"] = out_of_range(ts)
        return ts, row

    for k, slot in enumerate(SLOTS, start=1):
        m = CTX.slot_model[slot]
        bots = sorted(u for u, r in gen.items() if r["집단"] == GRP_NEW and r["모델"] == m and r["쪽"] == "시험")
        sets[slot], row = v1_row(f"새모델 {slot} {m} 시험 쪽", bots, [m] * len(bots), (2, sens, k),
                                 cells[slot]["판정가능"])
        out["ver1적용"].append(row)
    regT = sorted(u for u, r in gen.items() if r["집단"] == GRP_REGEN and r["쪽"] == "시험")
    _, row = v1_row("재생성 gpt-4o-mini 시험 쪽", regT, [CTX.slot_model[gen[u]["모델슬롯"]] for u in regT],
                    (2, sens, 5))
    out["ver1적용"].append(row)
    ts_base, base_row = v1_row("기준 행: 원 봇 댓글 한정(ver.1 학습 밖 134)", CTX.base134,
                               [0] * len(CTX.base134), (2, 0, 6))
    out["ver1적용"].append(base_row)
    say_rows(out["ver1적용"], f"{tag}ver.1 적용 (4항)")

    # P12-3 재료: 칸 − 기준 행 (위치), 시험 사람 재추출 공유
    bp, bdist = ts_base.auc(DET_V1, m11.ROW_POS)
    for slot in SLOTS:
        if sets[slot] is None:
            out["P12-3재료"][slot] = {"모델": CTX.slot_model[slot], "판정가능": False, "사유": "시험 봇 2 미만",
                                    "통과(하한>−0.05)": None}
            continue
        cp, cdist = sets[slot].auc(DET_V1, m11.ROW_POS)
        lo, hi = ci95(cdist - bdist)
        out["P12-3재료"][slot] = {"모델": CTX.slot_model[slot], "칸AUC": cp, "기준AUC": bp, "차": cp - bp,
                                "CI95": [lo, hi], "판정가능": cells[slot]["판정가능"] and base_row["판정가능"],
                                "통과(하한>−0.05)": lo > -P123_MARGIN}

    # 7항 (i) 주 시험: 모델 하나 빼기
    ctrl = tr[DET_CTRL]
    for slot in SLOTS:
        det, ts, m = tr["LOMO"][slot], sets[slot], CTX.slot_model[slot]
        ok_cell = cells[slot]["판정가능"]
        entry = {"빠진모델": m, "칸": slot, "하나빼기_판정불가": bool(det.get("판정불가")),
                 "대조_판정불가": bool(ctrl.get("판정불가")), "하나빼기_위치비중": det["w"], "대조_위치비중": ctrl["w"],
                 "학습페르소나수_하나빼기": det["summary"].get("학습페르소나수"),
                 "학습페르소나수_대조": ctrl["summary"].get("학습페르소나수")}
        if ts is None:
            entry.update({**g5_flags(0, nh, ok_cell), "판정가능": False, "사유": "시험 봇 2 미만", "AUC": {},
                          "차_ver2-ver1": na_diff("시험 봇 2 미만"), "차_ver2-대조": na_diff("시험 봇 2 미만")})
            out["LOMO"].append(entry)
            say(f"  하나빼기 {slot} {m:<30} 판정불가(시험 봇 2 미만)")
            continue
        test_p = {gen[u]["페르소나id"] for u in ts.bots}
        check(all(gen[u]["모델"] == m for u in ts.bots), f"{slot}: 하나빼기 시험 봇의 모델이 빠진 모델이 아니다")
        g5 = g5_flags(ts.nb, nh, ok_cell)
        entry.update(g5)
        entry["AUC"] = {DET_V1: ts.row(DET_V1, thr1, g5)["도구"]}
        if not det.get("판정불가"):
            check(not (det["personas"] & test_p), f"{slot}: 학습 페르소나와 시험 페르소나가 겹친다(G2)")
            check(not (det["humans"] & set(ts.hums)), f"{slot}: 학습 사람이 시험 사람에 있다(G2)")
            check(all(gen[b_]["모델"] != m for b_, _, _ in det["pairs"]), f"{slot}: 하나빼기 학습에 빠진 모델 계정이 있다")
            ts.add(DET_LOMO, score(det["fit"], det["w"], ts.X))
            entry["AUC"][DET_LOMO] = ts.row(DET_LOMO, det["thr"], g5)["도구"]
        if not ctrl.get("판정불가"):
            check(not (ctrl["personas"] & test_p), f"{slot}: 대조 학습 페르소나와 시험 페르소나가 겹친다(G2)")
            check(not (ctrl["humans"] & set(ts.hums)), f"{slot}: 대조 학습 사람이 시험 사람에 있다(G2)")
            ts.add(DET_CTRL, score(ctrl["fit"], ctrl["w"], ts.X))
            entry["AUC"][DET_CTRL] = ts.row(DET_CTRL, ctrl["thr"], g5)["도구"]
        entry["차_ver2-ver1"] = (na_diff("하나빼기 판별기 판정불가") if det.get("판정불가")
                               else ts.diff(DET_LOMO, DET_V1, ok_cell))
        entry["차_ver2-대조"] = (na_diff("하나빼기 또는 대조 판별기 판정불가")
                               if det.get("판정불가") or ctrl.get("판정불가") else ts.diff(DET_LOMO, DET_CTRL, ok_cell))
        out["LOMO"].append(entry)
        a = entry["AUC"]
        say(f"  하나빼기 {slot} {m:<30} n봇 {ts.nb:>3} · 제안 AUC "
            + " · ".join(f"{d} {a[d][m11.ROW_PROP]['AUC']:.4f}" for d in a)
            + f" · 차(ver.2−ver.1) 구간 {entry['차_ver2-ver1'][m11.ROW_PROP]['CI95']}"
            + f" · 차(ver.2−대조) 구간 {entry['차_ver2-대조'][m11.ROW_PROP]['CI95']}")

    # 7항 (ii) 보조: 시험 쪽 전체
    v2 = tr[DET_V2]
    allT = sorted(u for u, r in gen.items() if r["집단"] == GRP_NEW and r["쪽"] == "시험")
    if len(allT) < 2:
        out["보조"] = {**g5_flags(len(allT), nh), "판정가능": False, "사유": "시험 봇 2 미만", "AUC": {},
                     "차_ver2-ver1": na_diff("시험 봇 2 미만"), "차_ver2-대조": na_diff("시험 봇 2 미만")}
        return out
    ts = TestSet("보조: 새 모델 시험 쪽 전체", accs, allT, [gen[u]["모델"] for u in allT], (2, sens, 7), R)
    test_p = {gen[u]["페르소나id"] for u in allT}
    g5 = g5_flags(ts.nb, nh)
    ts.add(DET_V1, score(v1, 0.5, ts.X))
    rows = {DET_V1: thr1}
    for name_, d_ in ((DET_V2, v2), (DET_CTRL, ctrl)):
        if d_.get("판정불가"):
            continue
        check(not (d_["personas"] & test_p) and not (d_["humans"] & set(ts.hums)),
              f"보조: {name_} 학습 페르소나 · 사람이 시험과 겹친다(G2)")
        ts.add(name_, score(d_["fit"], d_["w"], ts.X))
        rows[name_] = d_["thr"]
    out["보조"] = {"n_봇_모델별": dict(Counter(gen[u]["모델"] for u in allT)), **g5,
                 "AUC": {d: ts.row(d, th, g5)["도구"] for d, th in rows.items()},
                 "차_ver2-ver1": (ts.diff(DET_V2, DET_V1, g5["판정가능"]) if DET_V2 in rows
                                 else na_diff("ver.2 판정불가")),
                 "차_ver2-대조": (ts.diff(DET_V2, DET_CTRL, g5["판정가능"]) if DET_V2 in rows and DET_CTRL in rows
                                 else na_diff("ver.2 또는 대조 판정불가"))}
    if not sens:
        out["보조"]["점수"] = {d: {t: dict(zip(allT + ts.hums, map(float, ts.sc[d][t]))) for t in ts.sc[d]}
                             for d in ts.sc}
    a = out["보조"]["AUC"]
    say(f"  보조 n봇 {ts.nb} · 제안 AUC " + " · ".join(f"{d} {a[d][m11.ROW_PROP]['AUC']:.4f}" for d in a))
    return out


# ════════════════════════════════════════════════════════════════════════
# [7절] 예측 판정 (삼값: 적중 · 빗나감 · 판정불가)
# ════════════════════════════════════════════════════════════════════════
def part_verdict(succ, n_unknown, need=3):
    if succ >= need:
        return "성립"
    if succ + n_unknown < need:
        return "불성립"
    return "판정불가"


def decision(code):
    return next(d for d in IMPLEMENTATION_DECISIONS if d.startswith(code + " "))


def judge_predictions(res, tr):
    preds = []
    # P12-3
    rows = res["P12-3재료"]
    fails = [s for s, r in rows.items() if r["판정가능"] and not r["통과(하한>−0.05)"]]
    allok = all(r["판정가능"] and r["통과(하한>−0.05)"] for r in rows.values())
    v = "빗나감" if fails else ("적중" if allok else "판정불가")
    preds.append({"번호": "P12-3", "원문": PRED_TEXT["P12-3"], "판정규칙": decision("D10"),
                  "판정": v, "칸별": rows})
    # P12-4
    v = p124_verdict(tr[DET_V2])
    preds.append({"번호": "P12-4", "원문": PRED_TEXT["P12-4"], "판정규칙": decision("D11"),
                  "판정": v, "관측": tr[DET_V2]["summary"].get("P12-4통계"),
                  "후속": ("비중 규칙 (라) · (마) 성립 가능" if v == "적중"
                         else "빗나감 또는 판정불가: ver.2 계열 전체 1:1 고정, '천장' 행으로 기록"),
                  "천장행": v != "적중", "ver.2_선택비중": tr[DET_V2]["w"]})
    # P12-5 (주: 제안, 참고: 위치)
    out5 = {}
    for tool in (m11.ROW_PROP, m11.ROW_POS):
        parts = {}
        for key in ("차_ver2-ver1", "차_ver2-대조"):
            ds = [r[key][tool] for r in res["LOMO"]]
            succ = sum(1 for d in ds if d["판정가능"] and d["하한>0"])
            unk = sum(1 for d in ds if not d["판정가능"])
            parts[key] = {"성공회차": succ, "판정불가회차": unk, "부분판정": part_verdict(succ, unk),
                          "회차별": [{"빠진모델": r["빠진모델"], **r[key][tool]} for r in res["LOMO"]]}
        pv = [x["부분판정"] for x in parts.values()]
        v = "적중" if all(x == "성립" for x in pv) else ("빗나감" if "불성립" in pv else "판정불가")
        out5[tool] = {"판정": v, "부분": parts}
    preds.append({"번호": "P12-5", "원문": PRED_TEXT["P12-5"], "판정규칙": decision("D12"),
                  "판정": out5[m11.ROW_PROP]["판정"], "주도구": m11.ROW_PROP, "도구별": out5})
    for p_ in preds:
        say(f"  {p_['번호']} [{p_['판정']}] {p_['원문']}")
    return preds


# ════════════════════════════════════════════════════════════════════════
# [5절 9항] 민감도: 106명 슬롯을 뺀 계정
# ════════════════════════════════════════════════════════════════════════
def resum(docs):
    """문서별 측정치를 합산해 계정 측정치로(13-0 aggregate의 합산과 같은 꼴)."""
    out = {"문서수": len(docs), "문장수": 0, "토큰수": 0, "토큰수_구두점제외": 0, "구두점토큰수": 0,
           "문장길이": []}
    fw, up, ft = Counter(), Counter(), Counter()
    for d in docs:
        for f in ("문장수", "토큰수", "토큰수_구두점제외", "구두점토큰수"):
            out[f] += d[f]
        out["문장길이"] += list(d["문장길이"])
        fw.update(d["기능어"])
        up.update(d["UPOS"])
        ft.update(d["자질"])
    out.update({"기능어": dict(fw), "UPOS": dict(up), "자질": dict(ft)})
    return out


def same_meas(a, b):
    return all(a[f] == b[f] for f in MEAS_FIELDS)


class Remeasurer:
    """13-0 measure_account로 문서 본문을 다시 잰다(stanza는 처음 쓸 때 한 번 만든다)."""

    def __init__(self):
        self.ready = False

    def setup(self):
        if self.ready:
            return
        self.m130 = import_by_path("m130_remeasure", PY130, argv=[PY130])
        import langid
        import stanza
        import torch
        torch.manual_seed(SEED)
        self.langid = langid
        self.nlp = stanza.Pipeline(lang="en", processors="tokenize,pos", verbose=False, use_gpu=False,
                                   download_method=None)
        fws = sorted({self.m130.normalize_apostrophe(w) for w in load_json(FUNCWORDS_JSON)["기능어"]})
        check(sha16("\n".join(fws)) == FW_HASH and len(fws) == 172, "기능어 목록이 12-0 · 13-0과 다르다")
        self.fwset = set(fws)
        self.info = {"stanza": stanza.__version__, "torch": torch.__version__, "13-0_sha256": sha256_file(PY130)}
        self.ready = True

    def measure(self, texts):
        """01 규칙 마지막 두 단계(10건 이상 · langid en) 뒤 13-0 measure_account."""
        self.setup()
        if len(texts) < MIN_DOCS:
            return None, "문서 10건 미만"
        lang, _ = self.langid.classify(" ".join(texts))
        if lang != "en":
            return None, f"langid {lang}"
        return self.m130.measure_account(self.nlp, list(texts), ["생성"] * len(texts), self.fwset), None


def slots_ok(uid, r, slots):
    """슬롯 계약: 수 = 문서수, 중복 없음, 그 페르소나의 '프롬프트 있음' 슬롯."""
    if len(slots) != r["문서수"] or len(set(slots)) != len(slots):
        return "슬롯 수 ≠ 문서수 또는 슬롯 중복"
    bad = [s for s in slots if s not in CTX.ledger or CTX.ledger[s][0] != r["페르소나id"]
           or CTX.ledger[s][2] != "프롬프트 있음"]
    return f"페르소나 밖 또는 프롬프트 없는 슬롯 {bad[:3]}" if bad else None


# 12-1 최상위 문서별 열 → 계정 측정치에서 같은 값을 내는 식(있는 열만 대조한다)
DOC_COL_CHECK = {
    "문장수": lambda a: a["문장수"],
    "토큰수_구두점제외": lambda a: a["토큰수_구두점제외"],
    "Tense_Past": lambda a: a["자질"].get("Tense=Past", 0),
    "Tense_합": lambda a: sum(v for k, v in a["자질"].items() if k.startswith("Tense=")),
}


def sens_from_121(gen, raw, acc130_ids):
    """
    경로 (가): 12-1이 같은 파싱에서 미리 만든 '민감도_106제외' 계정을 쓴다(다시 파싱하지 않는다).
    독립 대조: 12-1의 106명 = 분할.json 106명. 계정마다 최상위 '문서별'의 슬롯id에서 이 파일이
    대장으로 고른 뺄 슬롯 수를 세어 '뺀문서수'와 맞춘다. 문서별 열(DOC_COL_CHECK에 있는 것)의
    전 행 합 = 본 계정 값, 남은 행 합 = 줄인 계정 값, 줄인 계정 문서수 = 남은 행 수. 뺄 문서가 없으면
    본 계정과 측정치가 같다.
    줄인 계정이 없는 본 계정은 설정.민감도_제외계정에 사유가 있어야 한다.
    """
    conf = raw.get("설정") or {}
    problems = []
    if set(conf.get("민감도_106명") or []) != CTX.v106:
        problems.append(["설정", "12-1 민감도_106명 ≠ 분할.json 106명"])
    docs = raw.get("문서별") or {}
    cols = docs.get("열") or []
    if not all(c in cols for c in ("슬롯id", "문장수", "토큰수_구두점제외")):
        return None, {}, problems + [["문서별", "최상위 '문서별'.열에 슬롯id · 문장수 · 토큰수_구두점제외가 없다"]]
    ci = {c: cols.index(c) for c in cols}
    chk_cols = [c for c in DOC_COL_CHECK if c in ci]
    rows_of = docs.get("계정") or {}
    red, rep = parse_records(raw["민감도_106제외"], acc130_ids)
    # 탈락 기록: 옛 판은 설정.민감도_제외계정, 새 판은 최상위 변형_탈락.민감도_106제외
    dropped_why = {**(conf.get("민감도_제외계정") or {}),
                   **((raw.get("변형_탈락") or {}).get("민감도_106제외") or {})}
    declared = set(dropped_why)
    n_touch = n_docs = 0
    for uid in sorted(gen):
        r, rows = gen[uid], rows_of.get(uid)
        if rows is None:
            problems.append([uid, "최상위 문서별에 행이 없다"])
            continue
        slots = [x[ci["슬롯id"]] for x in rows]
        why = slots_ok(uid, r, slots)
        if why:
            problems.append([uid, why])
            continue
        bad_full = [c for c in chk_cols if sum(x[ci[c]] for x in rows) != DOC_COL_CHECK[c](r)]
        if bad_full:
            problems.append([uid, f"본 계정 값 ≠ 문서별 전 행 합: {bad_full}"])
            continue
        drop = [s in CTX.excl_slots for s in slots]
        n_ex = sum(drop)
        if uid not in red:
            if uid not in declared or n_ex == 0:
                problems.append([uid, "민감도 계정이 없는데 제외 기록이 없거나 뺄 문서가 없다"])
            continue
        s, kept = red[uid], [x for x, d in zip(rows, drop) if not d]
        # 뺀문서수는 두 기록 모두 파싱 목록(복사 제외 전) 기준이다: 본 계정 뺀문서수(복사 슬롯, 없으면 0) + 106 슬롯
        base_ex = (raw["계정"].get(uid) or {}).get("뺀문서수") or 0
        if raw["민감도_106제외"][uid].get("뺀문서수") != base_ex + n_ex:
            problems.append([uid, f"뺀문서수 {raw['민감도_106제외'][uid].get('뺀문서수')} ≠ 본 계정 뺀문서수 "
                                  f"{base_ex} + 대장 기준 {n_ex}"])
        elif n_ex == 0 and not same_meas(s, r):
            problems.append([uid, "뺄 문서가 없는데 측정치가 본 계정과 다르다"])
        elif s["문서수"] != len(kept) or any(sum(x[ci[c]] for x in kept) != DOC_COL_CHECK[c](s) for c in chk_cols):
            problems.append([uid, f"줄인 계정의 문서수 또는 {chk_cols} 가 남은 문서 행의 합과 다르다"])
        n_touch += n_ex > 0
        n_docs += n_ex
    extra = sorted(set(red) - set(gen))
    if extra:
        problems.append(["민감도_106제외", f"본 계정에 없는 uid {extra[:3]}"])
    info = {"경로": "(가) 12-1 민감도_106제외(같은 파싱의 재집계)", "대조열": chk_cols, "적재": rep,
            "줄인계정": n_touch,
            "뺀문서수": n_docs, "탈락계정수": len(set(gen) - set(red)), "남은계정": len(red),
            "탈락사유": {u: dropped_why.get(u) for u in sorted(set(gen) - set(red))}}
    return red, info, problems


def prepare_sensitivity(gen, raw121, acc130_ids, remeasurer, gates):
    """
    민감도용 계정 사전을 만든다. 계약을 못 지키면 None과 사유를 돌려준다(본 분석은 계속).
    경로 우선순위: (가) 12-1 '민감도_106제외' → (나) 계정별 '문서별' 측정치 합산 →
    (다) 계정별 '슬롯id목록' + '문서' 본문을 13-0 measure_account로 재측정.
    """
    line("[민감도 준비] 5절 9항: 모방 예시 저자가 ver.1 학습 사람(106)인 슬롯을 뺀 계정")
    excl = CTX.excl_slots
    n_prompt = sum(1 for s, v in CTX.ledger.items() if v[2] == "프롬프트 있음")
    n_ex = sum(1 for s in excl if CTX.ledger[s][2] == "프롬프트 있음")
    say(f"  뺄 슬롯 {len(excl):,} (프롬프트 있음 {n_ex:,}/{n_prompt:,} = {n_ex / n_prompt:.3%})")
    if isinstance(raw121.get("민감도_106제외"), dict):
        red, info, problems = sens_from_121(gen, raw121, acc130_ids)
        info.update({"뺄슬롯수": len(excl), "뺄슬롯_프롬프트있음": n_ex, "프롬프트있음_전체": n_prompt})
        if problems:
            say(f"  ■ 민감도 실행불가(경로 가): 대조 실패 {len(problems)}건 (예: {problems[:3]})")
            info.update({"실행가능": False, "위반수": len(problems), "위반예시": problems[:20]})
            gates["민감도_입력정합"] = {"통과": False, "경로": info["경로"], "위반수": len(problems)}
            return None, info
        info["실행가능"] = True
        gates["민감도_입력정합"] = {"통과": True, "경로": info["경로"], "대조": "106명 · 뺀문서수 · 남은 행 합 · 제외 기록"}
        say(f"  경로 (가) 대조 통과 · 줄인 계정 {info['줄인계정']} · 뺀 문서 {info['뺀문서수']:,} · "
            f"탈락 {info['탈락계정수']} · 남은 {info['남은계정']}")
        return red, info
    problems, plan = [], {}
    for uid in sorted(gen):
        r = gen[uid]
        if "문서별" in r:
            slots, src = [d.get("슬롯id") for d in r["문서별"]], "문서별"
        elif "슬롯id목록" in r:
            slots, src = list(r["슬롯id목록"]), ("문서" if "문서" in r else "슬롯만")
        else:
            problems.append([uid, "슬롯id목록 · 문서별 모두 없음"])
            continue
        why = slots_ok(uid, r, slots)
        if why:
            problems.append([uid, why])
            continue
        if src == "문서" and len(r["문서"]) != len(slots):
            problems.append([uid, "문서 수 ≠ 슬롯id목록 수"])
            continue
        drop = [s in excl for s in slots]
        if any(drop) and src == "슬롯만":
            problems.append([uid, "뺄 슬롯이 있는데 문서별 측정치 · 문서 본문이 없음"])
            continue
        plan[uid] = (src, slots, drop)
    info = {"경로": "(나) 계정별 문서별 합산 · (다) 문서 본문 재측정", "뺄슬롯수": len(excl),
            "뺄슬롯_프롬프트있음": n_ex, "프롬프트있음_전체": n_prompt,
            "필요계약": ("(가) 최상위 '민감도_106제외' + '문서별'{열: 슬롯id · 문장수 · 토큰수_구두점제외, 계정} + "
                       "설정.민감도_106명 · 민감도_제외계정, 또는 (나)(다) 계정마다 '슬롯id목록'(또는 '문서별'[].슬롯id)과, "
                       "뺄 슬롯이 든 계정은 '문서별' 측정치 또는 '문서' 본문. 슬롯은 그 페르소나의 '프롬프트 있음' "
                       "슬롯이며 중복이 없고 수가 문서수와 같다.")}
    if problems:
        say(f"  ■ 민감도 실행불가: 계약 위반 {len(problems)}계정 (예: {problems[:3]})")
        info.update({"실행가능": False, "위반계정수": len(problems), "위반예시": problems[:20]})
        gates["민감도_입력정합"] = {"통과": False, "사유": "계약 위반"}
        return None, info
    # 재구성 정합: 빼는 것이 없을 때의 재구성 = 저장값
    bad_sum = [u for u, (src, _, _) in plan.items()
               if src == "문서별" and not same_meas(resum(gen[u]["문서별"]), gen[u])]
    doc_accs = sorted(u for u, (src, _, _) in plan.items() if src == "문서")
    sample = random.Random(SEED).sample(doc_accs, min(3, len(doc_accs))) if doc_accs else []
    bad_doc = []
    for u in sample:
        agg, why = remeasurer.measure(gen[u]["문서"])
        if agg is None or not same_meas(agg, gen[u]):
            bad_doc.append([u, why or "측정치 다름"])
    rows = {"문서별_합산=저장값_불일치": len(bad_sum), "본문_재측정_표본": sample, "본문_재측정_불일치": bad_doc}
    say(f"  재구성 정합: 문서별 합산 불일치 {len(bad_sum)} · 본문 재측정 표본 {len(sample)} 불일치 {len(bad_doc)}")
    if bad_sum or bad_doc:
        info.update({"실행가능": False, "재구성정합": rows})
        gates["민감도_입력정합"] = {"통과": False, "사유": "재구성 정합 실패", **rows}
        say("  ■ 민감도 실행불가: 빼는 슬롯이 없을 때의 재구성이 저장값과 다르다")
        return None, info
    gates["민감도_입력정합"] = {"통과": True, **rows}
    red, touched, dropped, docs_removed = {}, Counter(), [], 0
    todo_parse = sum(sum(1 for d in drop if not d) for src, _, drop in plan.values() if src == "문서" and any(drop))
    if todo_parse:
        say(f"  본문 재측정 대상 문서 {todo_parse:,}건 (예상 {todo_parse * 0.0099 / 60:.1f}~{todo_parse * 0.089 / 60:.1f}분)")
    for uid in sorted(plan):
        src, slots, drop = plan[uid]
        r = gen[uid]
        if not any(drop):
            red[uid] = r
            continue
        touched[f"{r['집단']}|{r['모델']}"] += 1
        docs_removed += sum(drop)
        if src == "문서별":
            kept = [d for d, x in zip(r["문서별"], drop) if not x]
            new = resum(kept) if len(kept) >= MIN_DOCS else None
            why = None if new else "문서 10건 미만"
        else:
            new, why = remeasurer.measure([t for t, x in zip(r["문서"], drop) if not x])
        if new is None:
            dropped.append([uid, r["집단"], r["모델"], why])
            continue
        red[uid] = {**{k: v for k, v in r.items() if k not in ("문서별", "문서", "슬롯id목록")},
                    **{f: new[f] for f in MEAS_FIELDS}}
    info.update({"실행가능": True, "줄인계정_집단모델별": dict(touched), "뺀문서수": docs_removed,
                 "탈락계정": dropped, "탈락계정수": len(dropped), "남은계정": len(red),
                 "재측정": getattr(remeasurer, "info", None)})
    say(f"  줄인 계정 {sum(touched.values())} · 뺀 문서 {docs_removed:,} · 10건 미만 등 탈락 {len(dropped)} · "
        f"남은 {len(red)}")
    return red, info


# ════════════════════════════════════════════════════════════════════════
# [본 흐름]
# ════════════════════════════════════════════════════════════════════════
def parse_args():
    ap = argparse.ArgumentParser(description="12-3 판별기 ver.2 (뼈대 v3.2 5절 4~7 · 9항)")
    ap.add_argument("--smoke", action="store_true", help="부트스트랩 200회 배선 점검(--out-dir 필수)")
    ap.add_argument("--input", default=IN121_DEFAULT, help="12-1 계정사전 JSON (기본: 본 산출)")
    ap.add_argument("--out-dir", default=None, help="산출 폴더. 본 실행은 생략(= 이 파일 폴더)")
    return ap.parse_args()


def resolve_mode(args):
    inp = nfc(os.path.abspath(args.input))
    real_in = inp == IN121_DEFAULT
    if args.out_dir is None:
        if args.smoke or not real_in:
            sys.exit("--smoke 또는 대체 입력은 --out-dir(볼트 밖 폴더)가 필요합니다.")
        out = HERE
    else:
        out = nfc(os.path.abspath(args.out_dir))
        if out == HERE:
            sys.exit("--out-dir로 이 폴더를 줄 수 없습니다. 본 실행은 --out-dir 없이 돌립니다.")
    mode = "smoke" if args.smoke else ("본실행" if (real_in and out == HERE) else "대체입력")
    return mode, out, inp


def main():
    global OUT_DIR, m11, CTX
    args = parse_args()
    mode, OUT_DIR, in121 = resolve_mode(args)
    os.makedirs(OUT_DIR, exist_ok=True)
    out_json, out_model = f"{OUT_DIR}/{OUT_NAMES['json']}", f"{OUT_DIR}/{OUT_NAMES['model']}"
    R = N_BOOT_SMOKE if args.smoke else N_BOOT
    sys.stdout = Tee(f"{OUT_DIR}/{OUT_NAMES['log']}")
    t0 = time.time()
    started = datetime.now().astimezone().isoformat()
    gates, stage = {}, {}
    line("12-3 판별기 ver.2: 뼈대 v3.2 5절 4~7항 · 9항, 예측 P12-3~P12-5  (라벨을 읽는다)")
    say(f"실행 {started} · 모드 {mode} · 부트스트랩 {R}회 · python {platform.python_version()} · "
        f"numpy {np.__version__} · scikit-learn {sklearn.__version__} · scipy {scipy.__version__}")
    say(f"sys.flags.optimize {sys.flags.optimize} · 단언 {'활성' if __debug__ else '꺼짐(관문은 check로 유지)'}")
    say(f"12-1 입력 {in121}\n산출 {OUT_DIR}")
    try:
        sha, freeze, j11 = gate_inputs(gates)
        m11 = import_by_path("m11_판별기", PY11)
        bundle11 = joblib.load(BUNDLE11)       # sha256을 G0에서 확인한 뒤에만 연다(pickle)
        t = time.time()
        v1_bots, v1_hums = gate_ver1(bundle11, j11, gates)
        stage["G1"] = round(time.time() - t, 2)

        line("[적재] 13-0 계정사전 · 분할 · 모델ID표 · 프롬프트대장")
        acc130 = load_json(ACC130)
        check(acc130["설정"].get("관문통과") is True, "13-0 계정사전 관문통과가 true가 아니다")
        A130 = acc130["계정"]
        split = load_json(SPLIT_JSON)["분할"]
        slot_model = load_json(MODEL_TABLE_JSON)["표"]
        check(tuple(sorted(slot_model)) == SLOTS, "모델ID표 칸이 넷이 아니다")
        ledger = {}
        with open(LEDGER_JSONL, encoding="utf-8") as f:
            for ln in f:
                if ln.strip():
                    r = json.loads(ln)
                    ledger[r["슬롯id"]] = (r["페르소나id"], r.get("모방저자"), r.get("상태"))
        personas = split["페르소나"]
        by_pid = {p["페르소나id"]: p for p in personas}
        roles = split["사람"]["역할표"]
        v106 = {r["uid"] for r in roles if r["역할"] == ["모방"] and r["09-1매칭_ver1학습"]}
        hum = {u: a for u, a in A130.items() if a["집단"] == "사람"}
        test_hums = sorted(u for u, a in hum.items() if "시험" in a["역할"])
        train_hums = sorted(u for u, a in hum.items() if "학습" in a["역할"])
        tab_a = sorted(u for u, a in hum.items() if "표a" in a["역할"])
        orig = sorted(u for u, a in A130.items() if a["집단"] == "원봇")
        base134 = sorted(u for u in orig if u not in set(bundle11["train_ids"]))
        label_use("Users.csv 유래 집단(13-0 '집단' · '역할')으로 사람 · 봇을 가른다")
        check(len(personas) == 509 and len(hum) == 874 and len(test_hums) == 234 and len(train_hums) == 234
              and len(tab_a) == 640 and len(orig) == 504, "13-0 · 분할 집단 수가 3절과 다르다")
        check(len(base134) == 134 and not (set(base134) & v1_bots), "기준 행이 134가 아니거나 ver.1 학습과 겹친다(G2)")
        check(not (set(test_hums) & set(bundle11["train_ids"])), "시험 사람이 ver.1 학습에 있다(G2)")
        check(all(A130[u].get("봉인") is True for u in test_hums), "시험 사람 봉인 표시가 없다")
        check(len(v106) == 106 and v106 <= set(bundle11["train_ids"]), "민감도 106명이 ver.1 학습 사람과 맞지 않는다")
        excl = {s for s, v in ledger.items() if v[1] in v106}
        sealed = {u: A130[u] for u in test_hums}
        CTX = type("Ctx", (), {})()
        CTX.bundle11, CTX.v1fit = bundle11, fit_from_bundle(bundle11)
        CTX.keys = {b_: [k for bb, k in bundle11["feature_order"] if bb == b_] for b_ in m11.BLOCK_SIZES}
        check(CTX.keys["F"] == list(bundle11["function_words"]), "번들 자질 순서의 F가 기능어 목록과 다르다")
        CTX.axis_map = bundle11["axis_map"]
        CTX.abl = {m11.ROW_POS: np.arange(sum(m11.BLOCK_SIZES.values()))}
        CTX.slot_model, CTX.by_pid = slot_model, by_pid
        CTX.pid_of_uid = {p["원봇uid"]: p["페르소나id"] for p in personas}
        CTX.test_hums, CTX.train_hums, CTX.tab_a, CTX.base134 = test_hums, train_hums, tab_a, base134
        CTX.sealed_ids, CTX.ledger, CTX.excl_slots, CTX.v106 = set(test_hums), ledger, excl, v106
        # D20: ver.1 학습 사람 406 = 11 JSON 사람 512 가운데 13-0 댓글 한정 계정이 있는 사람
        extra = sorted(u for u in v1_hums if u in hum and u not in set(test_hums))
        check(len(extra) == N_EXTRA_HUMS and set(extra) == set(tab_a) - set(train_hums)
              and not (set(extra) & set(test_hums)) and not (set(extra) & set(train_hums)),
              "ver.1 학습 사람 406이 표a − 학습과 다르거나 시험 · 학습 사람과 겹친다")
        CTX.extra_hums = extra
        say(f"  사람 874 (시험 234 봉인 · 학습 234 · 표a 640) · 원봇 504 · 기준 행 134 · 민감도 106명 → 뺄 슬롯 {len(excl):,}")

        gen, rep121, raw121 = load_121(in121, set(A130), mode)
        gates["G0_12-1요약"] = check_121_summary(in121, mode, rep121["sha256"])
        surv = survival_table(gen)
        base_accs = {u: a for u, a in A130.items() if u not in sealed}
        A_main = {**base_accs, **gen}
        cells = cell_status(A_main, gen, "본")

        t = time.time()
        remeasurer = Remeasurer()
        red, sens_info = prepare_sensitivity(gen, raw121, set(A130), remeasurer, gates)
        del raw121
        stage["민감도준비"] = round(time.time() - t, 2)

        line("[5절 5 · 6항] 학습 (시험 사람 봉인 상태)")
        t = time.time()
        tr = train_all(A_main, gen, 0, R, cells)
        family_main = tr["계열관문"]["ver.2계열_argmax허용"]
        stage["학습"] = round(time.time() - t, 2)
        t = time.time()
        gate_shuffle(tr[DET_V2], gates)
        gate_determinism(tr[DET_V2], A_main, R, gates)
        stage["G3_G4"] = round(time.time() - t, 2)
        line("[동결] ver.2 번들 저장 (봉인 해제 전)")
        model_sha = None
        if tr[DET_V2].get("판정불가"):
            say("  ver.2가 판정불가라 번들을 저장하지 않는다.")
        else:
            model_sha = save_bundle(tr[DET_V2], out_model, rep121["sha256"])
        A_sens, cells_s, tr_s = None, None, None
        if red is not None:
            A_sens = {**base_accs, **red}
            cells_s = cell_status(A_sens, red, "민감도")
            t = time.time()
            tr_s = train_all(A_sens, red, 1, R, cells_s, family_main)
            stage["민감도학습"] = round(time.time() - t, 2)
        g2_train = {"학습표본_시험사람_교집합": sum(len(d["humans"] & set(test_hums)) for d in
                                           [tr[DET_V2], tr[DET_CTRL], *tr["LOMO"].values()]
                                           + ([tr_s[DET_V2], tr_s[DET_CTRL], *tr_s["LOMO"].values()] if tr_s else []))}
        check(g2_train["학습표본_시험사람_교집합"] == 0, "시험 사람이 학습 표본에 있다(G2)")

        line("[봉인 해제] 시험 사람 234를 계정 사전에 넣는다 (ver.2 번들 sha256 기록 뒤)")
        label_use("봉인 해제: 시험 사람 234")
        A_main.update(sealed)
        CTX.Wh_test = boot_counts((1,), [0] * len(test_hums), R)
        t = time.time()
        res = evaluate(A_main, gen, tr, cells, 0, R)
        line("[7절] 예측 판정 (본)")
        preds = judge_predictions(res, tr)
        stage["시험"] = round(time.time() - t, 2)
        sens = {"준비": sens_info}
        if tr_s is not None:
            A_sens.update(sealed)
            t = time.time()
            res_s = evaluate(A_sens, red, tr_s, cells_s, 1, R)
            line("[7절] 예측 판정 (민감도: 106명 슬롯 제외판, 본 판정을 바꾸지 않는다)")
            preds_s = judge_predictions(res_s, tr_s)
            sens.update({"칸판정_4절": cells_s, "생존표": survival_table(red),
                         "학습": {DET_V2: tr_s[DET_V2]["summary"], DET_CTRL: tr_s[DET_CTRL]["summary"],
                                "LOMO": {s: d["summary"] for s, d in tr_s["LOMO"].items()},
                                "계열관문": tr_s["계열관문"]},
                         "시험": res_s, "예측대조": preds_s})
            stage["민감도시험"] = round(time.time() - t, 2)
        else:
            say("\n  ■ 민감도(5절 9항)는 실행불가로 기록한다. 사유는 JSON 민감도.준비에 있다.")

        rows_all = res["ver1적용"] + [r for r in res["LOMO"]] + [res["보조"]]
        gates["G2_누설"] = {"통과": True, **g2_train,
                          "설명": "학습 함수 · 시험 함수 안 check()로 학습 사람 ∩ 시험 사람 = ∅, 학습 · 시험 "
                                  "페르소나 교집합 = ∅, 학습 봇 = 학습 쪽, 기준 행 ∩ ver.1 학습 = ∅를 확인했다."}
        gates["G5_4절"] = {"칸판정": cells, "판정불가_행수": sum(1 for r in rows_all if not r["판정가능"]),
                         "계급별n<100_행수": sum(1 for r in rows_all if not r["계급별n≥100"]),
                         "규칙": decision("D13"), "통과": True}
        results = {
            "표본": {"12-1적재": rep121, "생존표": surv, "칸판정_4절": cells,
                   "시험사람": len(test_hums), "학습사람": len(train_hums), "기준행": len(base134)},
            "ver2학습": tr[DET_V2]["summary"], "대조학습": tr[DET_CTRL]["summary"],
            "LOMO학습": {s: d["summary"] for s, d in tr["LOMO"].items()},
            "계열관문": tr["계열관문"],
            "학습규모": {"주석": decision("D23"),
                     "ver.2(4모델)": tr[DET_V2]["summary"].get("학습페르소나수"),
                     "대조": tr[DET_CTRL]["summary"].get("학습페르소나수"),
                     "하나빼기": {s: d["summary"].get("학습페르소나수") for s, d in tr["LOMO"].items()},
                     "사람풀": {d["tag"]: d["summary"].get("사람풀") for d in
                             [tr[DET_V2], tr[DET_CTRL], *tr["LOMO"].values()]
                             + ([tr_s[DET_V2], tr_s[DET_CTRL], *tr_s["LOMO"].values()] if tr_s else [])}},
            "ver2학습_OOF점수": ({t_: dict(zip(tr[DET_V2]["ids"], map(float, s)))
                              for t_, s in tr[DET_V2]["oof_sel"].items()} if not tr[DET_V2].get("판정불가") else None),
            "시험": res, "예측대조": preds, "민감도": sens,
        }
        digest = hashlib.sha256(json.dumps(jsonable(results), sort_keys=True, ensure_ascii=False)
                                .encode("utf-8")).hexdigest()
        out = {
            "설정": {
                "사전선언": "12_OpenRouter생성_사전선언_뼈대.md v3.2 5절 4~7항 · 9항, 7절 P12-3~P12-5, 4절 판정불가",
                "모드": mode, "시드": SEED, "부트스트랩": R, "캘리퍼": CALIPER, "비중격자": WEIGHT_GRID,
                "천장": CEILING, "판정불가_쌍문턱": N_MIN, "구현결정": IMPLEMENTATION_DECISIONS,
                "입력경로_12-1": in121,
                "입력_sha256": {**sha, "12-1": rep121["sha256"]}, "동결": {k: freeze.get(k) for k in
                                                                       ("동결시각", "11_정본모델.joblib")},
                "스크립트_sha256": sha256_file(SCRIPT_PATH), "11모듈_sha256": sha["11_판별기.py"],
                "버전": {"python": platform.python_version(), "numpy": np.__version__,
                       "scikit-learn": sklearn.__version__, "scipy": scipy.__version__,
                       "joblib": joblib.__version__},
                "라벨사용": "매칭 집단 · 학습 · 문턱 · AUC · 부트스트랩 · 라벨 뒤섞기 · 4절 칸 매칭",
                "검토주석": REVIEW_NOTES,
            },
            "관문": gates,
            "ver2번들": ({"파일": os.path.basename(out_model), "sha256": model_sha, "위치비중": tr[DET_V2]["w"]}
                       if model_sha else {"판정불가": True, "사유": tr[DET_V2].get("사유")}),
            **results,
            "결과_digest": digest,
            "소요초_단계별": stage, "소요초": round(time.time() - t0, 2),
            "실행기록": {"sys.flags.optimize": int(sys.flags.optimize), "__debug__": bool(__debug__),
                     "시작": started, "끝": datetime.now().astimezone().isoformat(),
                     "python_실행파일": sys.executable},
        }
        write_json(out_json, out)
        line("끝")
        say(f"  관문 G0~G5 통과 · 결과_digest {digest}")
        say(f"  저장 {out_json}\n       {out_model} (sha256 {model_sha})")
        say(f"  단계별 소요초 {stage} · 전체 {time.time() - t0:.1f}초")
    except Exception as e:     # 관문 실패와 그 밖 예외 모두 중단 JSON을 남긴다(D21)
        kind = "관문" if isinstance(e, GateError) else type(e).__name__
        tb = traceback.format_exc()
        say(f"\n■ 중단({kind}): {e}\n{tb}")
        write_json(out_json, {"중단": str(e), "종류": kind, "추적": tb, "관문": gates,
                              "소요초": round(time.time() - t0, 2)})
        sys.stdout.flush()
        sys.exit(1)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
