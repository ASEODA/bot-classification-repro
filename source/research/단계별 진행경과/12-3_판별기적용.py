#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""저장된 OpenRouter 측정 자료에 고정 BotSim 판별기를 적용한다. API 호출·새 생성·모형 재학습 없음. 실행은 저장소 run.sh를 사용한다."""

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
from datetime import datetime

sys.dont_write_bytecode = True

import joblib
import numpy as np
import scipy
import sklearn
from scipy.spatial.distance import cdist
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score, roc_curve


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ════════════════════════════════════════════════════════════════════════
# [경로]
# ════════════════════════════════════════════════════════════════════════
SCRIPT_PATH = nfc(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPT_PATH)
ROOT = os.path.dirname(HERE)
PREP_DIR = os.path.join(HERE, "12_OpenRouter생성_준비")
SPLIT_JSON = os.path.join(PREP_DIR, "분할.json")
MODEL_TABLE_JSON = os.path.join(PREP_DIR, "모델ID표.json")
FREEZE_JSON = os.path.join(PREP_DIR, "동결.json")
PY11 = os.path.join(HERE, "11_판별기.py")
J11 = os.path.join(HERE, "11_판별기.json")
BUNDLE11 = os.path.join(HERE, "11_판별기_모델.joblib")
PY10 = os.path.join(HERE, "10_동질성검정.py")
FUNCWORDS_JSON = os.path.join(HERE, "02_기능어목록.json")
DECL_MD = os.path.join(HERE, "12_OpenRouter생성_사전선언_뼈대.md")
SUMMARY121 = os.path.join(HERE, "12-1_생성댓글파싱_요약.json")
DATA_DIR = nfc(os.path.expanduser("~/DM_LAB_data/12_OpenRouter"))
ACC130 = os.path.join(DATA_DIR, "13-0_계정사전.json")
ACC121 = os.path.join(DATA_DIR, "12-1_계정사전.json")
SOURCES = {"11": PY11, "10": PY10}
OUT_BASE = "12_판별기적용"
OUT_JSON = os.path.join(HERE, f"{OUT_BASE}.json")
OUT_MD = os.path.join(HERE, f"{OUT_BASE}.md")
OUT_LOG = os.path.join(HERE, f"{OUT_BASE}_출력.log")
OUT_ABORT = os.path.join(HERE, f"{OUT_BASE}_중단.json")
OUT_ABORT_LOG = os.path.join(HERE, f"{OUT_BASE}_중단_출력.log")
PARTIAL = ".partial"
INPUT_FILES = [SPLIT_JSON, MODEL_TABLE_JSON, FREEZE_JSON, PY11, J11, BUNDLE11, PY10, FUNCWORDS_JSON,
               DECL_MD, SUMMARY121, ACC130, ACC121]

# ════════════════════════════════════════════════════════════════════════
# [설정] 사전선언 값. 결과를 보고 바꾸지 않는다.
# ════════════════════════════════════════════════════════════════════════
MODEL_REGEN = "openai/gpt-4o-mini"
SLOTS = ("MODEL_SLOT_1", "MODEL_SLOT_2", "MODEL_SLOT_3", "MODEL_SLOT_4")
MIN_DOCS = 10                   # 01 규칙
N_TEST_HUMANS, N_NEW_TEST, N_REGEN_TEST = 234, 252, 254
CELL_RANGE = (62, 64)           # 칸마다 시험 쪽 새 모델 계정 수(설계)
P123_AUC = 0.85                 # P12-3
P124_LO = -0.02                 # P12-4
# 부트스트랩 열쇠(보관 12-3 D19와 같음): 시험 사람 (1,), 칸 k (2, 0, k), 재생성 (2, 0, 5), 합동 (2, 0, 7)
KEY_HUMANS = (1,)
KEY_CELL = {slot: (2, 0, k) for k, slot in enumerate(SLOTS, start=1)}
KEY_REGEN, KEY_POOLED = (2, 0, 5), (2, 0, 7)
BATCH_POOLED, BATCH_REGEN = "합동: 새 모델 4칸 시험 쪽", "재생성 gpt-4o-mini 시험 쪽"

# 뼈대 7절 원문(관문 A가 뼈대 파일과 글자 대조).
PRED_TEXT = {
    "P12-3": "새 모델 4칸 합동에서 제안 AUC ≥ 0.85.",
    "P12-4": "제안 − 위치 차의 95% 하한 ≥ −0.02(밀도가 위치를 깎지 않는다).",
}

IMPLEMENTATION_DECISIONS = [
    "D1 적용: 11 번들을 11 score_bundle 복사본으로 채점한다. 위치 = 번들 로지스틱(번들 원값 중앙값 대치 → 번들 "
    "백분위 함수), 기준선 = 번들 랜덤 포레스트, 밀도 = 채점 묶음 안 대치 · 백분위 · 10번째 이웃 거리의 음수(번들 k), "
    "제안 = 묶음 안 순위 1:1 평균. 번들은 다시 배우지 않는다. 자질 정의(기능어 172 · 형태 58 · 품사 17 · 리듬 3, "
    "축 지도)도 번들 값을 쓴다.",
    "D2 채점 묶음 여섯: 칸 넷(칸의 시험 쪽 새 모델 계정 + 시험 사람 234), 합동(새 모델 4칸 시험 쪽 252 + 234), "
    "재생성(gpt-4o-mini 재생성 시험 쪽 254 + 234). 묶음마다 밀도 · 제안을 새로 매긴다. 매칭하지 않는다.",
    "D3 표본: 12-1 계정 가운데 쪽 = 시험이고 생성모델 ≠ openai/gpt-4o-mini인 계정(집단 새모델) 252, 칸은 '칸' 필드, "
    "생성 모델 = 모델ID표의 칸 모델(관문). 재생성 = 쪽 시험 · 생성모델 = openai/gpt-4o-mini(집단 재생성) 254. "
    "시험 사람 = 분할.json 역할표에서 역할에 '시험'이 든 uid 234 = 13-0의 사람 · 봉인 · 역할 시험. 문서 10건 이상 · "
    "라벨 · 문장길이 정합 · 적격은 관문으로만 본다(걸러내지 않는다). 봇 · 사람 목록은 uid 정렬.",
    "D4 부트스트랩(보관 12-3 D6 · D19와 같은 열쇠): 봇과 사람을 따로 계정 단위 복원 추출한다(np.random.default_rng("
    "[20260926, 열쇠…]).multinomial, 2,000회). 시험 사람 234의 재추출 행렬 하나(열쇠 (1,))를 모든 묶음이 공유한다. "
    "봇 열쇠: 칸 k (2, 0, k) 한 층, 재생성 (2, 0, 5) 층 = 페르소나 배정 칸의 모델, 합동 (2, 0, 7) 층 = 생성 모델. "
    "같은 묶음의 모든 도구가 같은 재추출을 쓴다(짝지은 부트스트랩). 점수는 재추출마다 다시 계산하지 않는다(밀도 · 제안 "
    "순위 포함). 구간 = np.percentile 2.5 · 97.5. 점추정 AUC는 roc_auc_score와 대조한다.",
    "D5 문턱: 위치 · 제안의 번들 문턱(BotSim 내부)으로 낸 균형정확도 · 탐지율 · 오탐률 · 순도 · 봇 표시 비율은 기술값이다. "
    "제안 문턱은 묶음 안 정규화 순위 위의 값이라 뜻이 바뀐다. 판정에 쓰지 않는다.",
    "D6 예측: P12-3 = 합동 묶음 제안 AUC(점추정) ≥ 0.85. P12-4 = 합동 묶음 제안 − 위치 AUC 차의 짝지은 부트스트랩 "
    "95% 하한 ≥ −0.02. 두 AUC가 모두 0.999 이상이면 천장 동률로 판정불가.",
    "D7 입력 사슬: 번들은 sha256을 11 JSON 기록과 대조한 뒤에만 연다(pickle). 11_판별기.py sha256 = 11 JSON 스크립트_sha256. "
    "번들 계수 250 · 절편 · 문턱 = 11 JSON(비트 단위), 자질 순서 = 11 JSON. 기능어: 02 목록의 U+2019를 U+0027로 바꿔 중복을 "
    "뺀 172 = 번들 function_words = 번들 F 열, 해시 382b68572f03bc23. 분할 · 13-0 · 모델ID표 sha256 = 동결.json. 12-1 "
    "sha256 = 12-1_생성댓글파싱_요약.json 산출.sha256, 12-1 설정.관문통과 = true.",
    "D8 AST 동일: 12-3 func_ast 규칙(docstring을 뺀 ast.dump)으로 11 정본 · 10 소스와 대조한다. 한국어 문서 규칙에 따라 "
    "복사 함수 docstring의 줄표만 쌍점으로 바꿨다.",
    "D9 결정성: 같은 프로세스에서 여섯 묶음 평가를 한 번 더 하고 결과(계정별 점수 · AUC · 재추출 분포)의 canonical "
    "sha256이 같은지 본다. 프로세스 사이는 JSON 결과_digest로 대조한다.",
]


# ════════════════════════════════════════════════════════════════════════
# [복사한 상수] 11 정본에서 옮겼다(관문 A가 AST 대조)
# ════════════════════════════════════════════════════════════════════════
SEED = 20260926
N_BOOT = 2000
CEILING = 0.999
NAN = float("nan")
FPR_TARGETS = (0.05, 0.10)
FUNCWORD_HASH = "382b68572f03bc23"
BLOCK_SIZES = {"F": 172, "M형태": 58, "M품사": 17, "R": 3}
MIN_SENTENCES_CV = 5          # 08과 같은 값. 문장 5개 미만은 변동계수 결측
RATE_DIGITS = 6               # 05와 같은 값. F 사용률 반올림 자릿수
ROW_POS = "위치"
ROW_DENS = "밀도"
ROW_PROP = "제안"
ROW_BASE = "기준선"
TOOLS = (ROW_POS, ROW_DENS, ROW_PROP, ROW_BASE)
PROPOSAL_WEIGHTS = (0.5, 0.5)   # 위치 순위 : 밀도 순위 = 1:1 고정. BotSim 결과로 바꾸지 않는다
DH_X = np.array([[0, 0], [0, 1], [1, 0], [1, 2], [2, NAN], [2, 2]], dtype=float)
DH_K = 2
DH_KDIST = np.array([1, 2, 2, 2, 2, 1]) / 5.0
DH_POS = np.arange(6.0)
DH_PROP = np.array([9, 5, 7, 9, 11, 19]) / 20.0
RK_POS = np.array([0.9, 0.2, 0.7, 0.7, 0.1])
RK_DENS = np.array([1.5, -2.0, 3.0, 0.0, -2.0])
RK_EXPECT = [0.875, 0.1875, 0.8125, 0.5625, 0.0625]
COPY_CONSTS = {k: "11" for k in ("SEED", "N_BOOT", "CEILING", "NAN", "FPR_TARGETS", "FUNCWORD_HASH", "BLOCK_SIZES",
                                  "MIN_SENTENCES_CV", "RATE_DIGITS", "ROW_POS", "ROW_DENS", "ROW_PROP", "ROW_BASE",
                                  "TOOLS", "PROPOSAL_WEIGHTS", "DH_X", "DH_K", "DH_KDIST", "DH_POS", "DH_PROP",
                                  "RK_POS", "RK_DENS", "RK_EXPECT")}
COPY_FUNCS = {**{k: "11" for k in ("say", "line", "label_use", "sha256_file", "check", "canonical", "digest",
                                    "func_ast", "jsonable", "axis_of", "f_rates", "m_ratios", "upos_ratios",
                                    "rhythm", "build_matrix", "apply_prep", "sigmoid", "rates_at",
                                    "balanced_accuracy", "choose_threshold", "tpr_at_fpr", "metrics", "ranks",
                                    "density", "rank_mean", "score_bundle", "boot_counts", "cmp_matrix",
                                    "boot_auc", "ci95", "auc_boot", "paired_diff", "close")},
              "normalize_apostrophe": "10"}

# ── 손 예제 A (13 손 예제와 같은 값): 계정 6개 × 자질 3개, 고정 분위 변환 · 클립 · 위치 점수 ──
#   f1  xp = (.1, .2, .4)  fp = (0, .5, 1)   중앙값 .2
#   f2  xp = (1, 3)        fp = (0, 1)       중앙값 2
#   f3  xp = (5,)          fp = (.5,)        중앙값 5   (한 점뿐 → 무엇이 와도 .5)
#   A1 (.15, 2, 7) → (.25, .5, .5) · A2 (.3, 0, 5) → (.75, 0, .5) · A3 (.05, 4, 결측) → (0, 1, .5)
#   A4 (.9, 결측, 1) → (1, .5, .5) · A5 (결측, 1.5, 5) → (.5, .25, .5) · A6 (.2, 3, 9) → (.5, 1, .5)
#   w = ln3 · (4, −4, 2), 절편 −ln3 → z/ln3 = 4(p1 − p2) = −1 · 3 · −4 · 2 · 1 · −2
#   점수 3^k/(1+3^k) = 1/4 · 27/28 · 1/82 · 9/10 · 3/4 · 1/10
#   봇 {1/4, 27/28, 3/4} 대 사람 {1/82, 9/10, 1/10}: 비교 행렬 AUC 7/9. 봇 가중 (1,1,1) · 사람 가중 (0,2,1)이면 5/9
HAND_PREP = {"xp": [np.array([0.1, 0.2, 0.4]), np.array([1.0, 3.0]), np.array([5.0])],
             "fp": [np.array([0.0, 0.5, 1.0]), np.array([0.0, 1.0]), np.array([0.5])],
             "median": np.array([0.2, 2.0, 5.0])}
HAND_X = np.array([[0.15, 2.0, 7.0], [0.30, 0.0, 5.0], [0.05, 4.0, NAN],
                   [0.90, NAN, 1.0], [NAN, 1.5, 5.0], [0.20, 3.0, 9.0]])
HAND_P = np.array([[0.25, 0.5, 0.5], [0.75, 0.0, 0.5], [0.0, 1.0, 0.5],
                   [1.0, 0.5, 0.5], [0.5, 0.25, 0.5], [0.5, 1.0, 0.5]])
HAND_W = math.log(3) * np.array([4.0, -4.0, 2.0])
HAND_B = -math.log(3)
HAND_SCORE = [1 / 4, 27 / 28, 1 / 82, 9 / 10, 3 / 4, 1 / 10]
HAND_Y = np.array([1, 1, 0, 0, 1, 0])
HAND_TOL = 1e-9


# ════════════════════════════════════════════════════════════════════════
# [도구] 이 파일 고유
# ════════════════════════════════════════════════════════════════════════
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


RUN = types.SimpleNamespace(tee=None, gates={})


def write_out(path, obj):
    """임시 파일에 쓰고 fsync 뒤 이름을 바꾼다. 이 폴더 밖에는 쓰지 않는다."""
    check(os.path.dirname(os.path.abspath(path)) == HERE, f"산출 폴더 밖 쓰기 금지: {path}")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(jsonable(obj), f, ensure_ascii=False, indent=1, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def stop(msg):
    """관문 실패 또는 예외. 정본 산출은 만들지 않고 중단 기록만 남긴다."""
    say(f"\n■ 중단 : {msg}")
    write_out(OUT_ABORT, {"중단": msg, "관문": RUN.gates, "시각": datetime.now().astimezone().isoformat()})
    for p in (OUT_JSON, OUT_MD):
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


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ════════════════════════════════════════════════════════════════════════
# [복사한 함수] 11 정본(11_판별기.py)과 10(10_동질성검정.py)에서 옮겼다. 관문 A가 AST를 대조한다.
# ════════════════════════════════════════════════════════════════════════
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


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


def normalize_apostrophe(s):
    """
    굽은 아포스트로피(’, U+2019)를 곧은 것(', U+0027)으로 바꾼다. [10_동질성검정.py]
    02 목록과 번들 기능어의 대조에만 쓴다(14와 같은 규칙: 174 → 172).
    """
    return s.replace("’", "'")


def axis_of(key):
    return key.split("=", 1)[0]


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


def apply_prep(prep, X):
    """결측을 학습 원값 중앙값으로 채운 뒤 백분위 함수에 통과. 범위 밖은 0 · 1로 자른다."""
    Xf = np.where(np.isnan(X), prep["median"][None, :], X)
    P = np.empty_like(Xf)
    for j in range(X.shape[1]):
        P[:, j] = np.clip(np.interp(Xf[:, j], prep["xp"][j], prep["fp"][j]), 0.0, 1.0)
    return P


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
        점수 = (r̄ − 1) ÷ (n − 1)   → [0, 1].
    """
    n = len(s_pos)
    assert n == len(s_dens) and n >= 2
    w_pos, w_dens = PROPOSAL_WEIGHTS
    r = w_pos * rankdata(s_pos, method="average") + w_dens * rankdata(s_dens, method="average")
    return (r - 1.0) / (n - 1.0)


def score_bundle(b, X):
    """
    고정 모델 번들 한 벌로 채점 묶음 X(원값, 계정 × 250, 결측 NaN)를 채점한다. 라벨은 받지 않는다.
        위치 = 번들 로지스틱 · 기준선 = 번들 랜덤 포레스트 · 밀도 = 묶음 안 k번째 이웃 거리의 음수 ·
        제안 = 묶음 안 순위 1:1 평균. 참고 k는 '밀도(k=…)'로 함께 돌려준다.
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


def close(a, b, tol=HAND_TOL):
    return abs(float(a) - float(b)) <= tol


# ════════════════════════════════════════════════════════════════════════
# [관문 A] 복사 AST · 뼈대 원문 · 손 예제
# ════════════════════════════════════════════════════════════════════════
def gate_copies():
    me = open(SCRIPT_PATH, encoding="utf-8").read()
    my_tree = ast.parse(me)
    top_funcs = [n.name for n in my_tree.body if isinstance(n, ast.FunctionDef)]
    my_assign = {n.targets[0].id: n for n in my_tree.body
                 if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
    srcs = {k: open(p, encoding="utf-8").read() for k, p in SOURCES.items()}
    trees = {k: ast.parse(t) for k, t in srcs.items()}
    res = {"함수": {}, "상수": {}}
    for name, k in COPY_FUNCS.items():
        a, b = func_ast(me, name), func_ast(srcs[k], name)
        ok = a is not None and a == b and top_funcs.count(name) == 1
        res["함수"][name] = {"원본": os.path.basename(SOURCES[k]), "AST일치": ok}
        if not ok:
            say(f"      ■ 함수 {name} ← {os.path.basename(SOURCES[k])} 불일치")
    for name, k in COPY_CONSTS.items():
        node = None
        for n in trees[k].body:
            if (isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                    and n.targets[0].id == name):
                node = n
        mine = my_assign.get(name)
        ok = node is not None and mine is not None and ast.dump(node.value) == ast.dump(mine.value)
        res["상수"][name] = {"원본": os.path.basename(SOURCES[k]), "AST일치": ok}
        if not ok:
            say(f"      ■ 상수 {name} ← {os.path.basename(SOURCES[k])} 불일치")
    n_f = sum(r["AST일치"] for r in res["함수"].values())
    n_c = sum(r["AST일치"] for r in res["상수"].values())
    say(f"      함수 {n_f}/{len(COPY_FUNCS)} · 상수 {n_c}/{len(COPY_CONSTS)} AST 일치 "
        f"(11_판별기.py {sum(1 for v in COPY_FUNCS.values() if v == '11')}개 · 10_동질성검정.py 1개)")
    res["원본_sha256"] = {k: sha256_file(p) for k, p in SOURCES.items()}
    return res, all(r["AST일치"] for g in ("함수", "상수") for r in res[g].values())


def gate_decl_text():
    txt = open(DECL_MD, encoding="utf-8").read()
    rows = {k: f"- **{k}**: {v}" in txt for k, v in PRED_TEXT.items()}
    rows["5절 4항 판별기 적용(12-3)"] = "4. **판별기 적용(12-3)**:" in txt
    for k, v in rows.items():
        say(f"      {k:<26} {'원문 일치' if v else '■ 원문과 다름'}")
    return {"항목": rows, "뼈대_sha256": sha256_file(DECL_MD)}, all(rows.values())


def gate_hand():
    """고정 분위 변환 · 클립 · 위치 점수 · 비교 행렬 AUC · 가중 재추출 AUC · 밀도 · 순위 평균."""
    fails = []
    P = apply_prep(HAND_PREP, HAND_X)
    if not np.allclose(P, HAND_P, rtol=0.0, atol=HAND_TOL):
        fails.append(f"분위 {P.tolist()}")
    s = sigmoid(HAND_B + P @ HAND_W)
    if not all(close(a, b) for a, b in zip(s, HAND_SCORE)):
        fails.append(f"점수 {s.tolist()}")
    C = cmp_matrix(s[HAND_Y == 1], s[HAND_Y == 0])
    b1 = boot_auc(C, np.array([[1.0, 1.0, 1.0]]), np.array([[0.0, 2.0, 1.0]]))
    if not (close(C.mean(), 7 / 9) and close(b1[0], 5 / 9)):
        fails.append(f"AUC {C.mean()} {b1}")
    d, _, _, _ = density(DH_X, (DH_K,))
    if not (np.allclose(-d[DH_K], DH_KDIST, rtol=0.0, atol=1e-12)
            and np.allclose(rank_mean(DH_POS, d[DH_K]), DH_PROP, rtol=0.0, atol=1e-12)):
        fails.append(f"밀도 {d}")
    if not all(close(a, b) for a, b in zip(rank_mean(RK_POS, RK_DENS), RK_EXPECT)):
        fails.append("동점 순위 평균")
    say(f"      분위 변환 18칸 · 위치 점수 6개 · AUC 7/9 · 가중 재추출 5/9 · 밀도 k번째 거리 · 제안 · "
        f"동점 순위 평균: {'통과' if not fails else '■ 실패 ' + str(fails)}")
    return {"실패": fails, "계산_점수": s.tolist(), "통과": not fails}, not fails


# ════════════════════════════════════════════════════════════════════════
# [관문 B] 입력 사슬
# ════════════════════════════════════════════════════════════════════════
def gate_inputs():
    j11 = load_json(J11)
    freeze = load_json(FREEZE_JSON)
    sha = {os.path.relpath(p, ROOT) if p.startswith(ROOT) else p: sha256_file(p) for p in INPUT_FILES}
    s_b = sha256_file(BUNDLE11)
    rows = {"11 번들 sha256 = 11 JSON 고정모델.파일_sha256": s_b == j11["고정모델"]["파일_sha256"],
            "11_판별기.py sha256 = 11 JSON 스크립트_sha256": sha256_file(PY11) == j11["설정"]["스크립트_sha256"],
            "11 JSON 관문 전부 통과": all(j11["관문_요약"].values()),
            "분할.json = 동결": sha256_file(SPLIT_JSON) == freeze["분할.json"],
            "13-0_계정사전.json = 동결": sha256_file(ACC130) == freeze["13-0_계정사전.json"],
            "모델ID표.json = 동결": sha256_file(MODEL_TABLE_JSON) == freeze["모델ID표.json"]}
    for k, v in rows.items():
        say(f"      {k:<46} {'같음' if v else '■ 다름'}")
    check(all(rows.values()), "입력 사슬이 끊겼다(번들 · 11 정본 · 동결 해시 가운데 다른 것이 있다). 번들을 열지 않는다.")
    # 번들은 11_판별기.py가 이 폴더에 쓴 자체 산출물이다. sha256을 11 JSON 기록과 방금 대조했다(pickle).
    b = joblib.load(BUNDLE11)
    order = [list(x) for x in b["feature_order"]]
    coef11 = j11["고정모델"]["계수"]
    words02 = sorted({normalize_apostrophe(w) for w in load_json(FUNCWORDS_JSON)["기능어"]})
    fw = list(b["function_words"])
    h = hashlib.sha256("\n".join(fw).encode("utf-8")).hexdigest()[:16]
    rows2 = {"자질순서 = 11 JSON": order == j11["자질"]["순서"],
             "계수250 비트일치 = 11 JSON": len(b["coef"]) == 250 and all(
                 float(b["coef"][j]) == coef11[f"{bb}|{k}"] for j, (bb, k) in enumerate(order)),
             "절편 비트일치 = 11 JSON": float(b["intercept"]) == j11["고정모델"]["절편"],
             "문턱(위치 · 제안) = 11 JSON": dict(b["thresholds"]) == j11["고정모델"]["문턱"],
             "밀도 k = 10, 참고 5 · 20": b["density_k"] == 10 and list(b["density_ks"]) == [5, 10, 20],
             "제안 비중 (0.5, 0.5)": tuple(b["proposal_weights"]) == PROPOSAL_WEIGHTS,
             "블록 크기 172 · 58 · 17 · 3": {bb: sum(1 for x, _ in order if x == bb) for bb in BLOCK_SIZES} == BLOCK_SIZES,
             "기능어 172 = 02 정규화 = 번들 F 열": words02 == fw == [k for bb, k in order if bb == "F"] and len(fw) == 172,
             "기능어 해시 382b": h == FUNCWORD_HASH == b["funcword_hash"]}
    for k, v in rows2.items():
        say(f"      {k:<46} {'같음' if v else '■ 다름'}")
    check(all(rows2.values()), "번들이 11 JSON 또는 02 목록과 맞지 않는다.")
    return j11, b, {"항목": {**rows, **rows2}, "번들_sha256": s_b, "입력_sha256": sha, "통과": True}


# ════════════════════════════════════════════════════════════════════════
# [표본] 12-1 시험 쪽 · 봉인 시험 사람
# ════════════════════════════════════════════════════════════════════════
def build_samples(bundle):
    d121 = load_json(ACC121)
    conf = d121.get("설정") or {}
    summ = load_json(SUMMARY121)
    sha121 = sha256_file(ACC121)
    rows = {"12-1 설정.관문통과 = true": conf.get("관문통과") is True,
            "12-1 smoke · 시험입력 아님": not conf.get("smoke") and not conf.get("시험입력"),
            "12-1 sha256 = 12-1 요약 산출.sha256": (summ.get("산출") or {}).get("sha256") == sha121}
    gen = d121["계정"]
    del d121
    a130 = load_json(ACC130)
    check(a130["설정"].get("관문통과") is True, "13-0 계정사전 관문통과가 true가 아니다")
    A130 = a130["계정"]
    split = load_json(SPLIT_JSON)["분할"]
    slot_model = load_json(MODEL_TABLE_JSON)["표"]
    rows["모델ID표 칸 넷"] = tuple(sorted(slot_model)) == SLOTS
    test_split = sorted(r["uid"] for r in split["사람"]["역할표"] if "시험" in r["역할"])
    test_130 = sorted(u for u, a in A130.items() if a["집단"] == "사람" and a.get("봉인") is True
                      and "시험" in a.get("역할", []))
    rows[f"시험 사람 {N_TEST_HUMANS} = 분할 역할 '시험' = 13-0 사람 · 봉인 · 시험"] = (
        test_split == test_130 and len(test_split) == N_TEST_HUMANS)
    rows["시험 사람 ∩ 11 학습 계정 = ∅"] = not (set(test_split) & set(bundle["train_ids"]))
    new = sorted(u for u, a in gen.items() if a.get("쪽") == "시험" and a.get("생성모델") != MODEL_REGEN)
    regen = sorted(u for u, a in gen.items() if a.get("쪽") == "시험" and a.get("생성모델") == MODEL_REGEN)
    rows[f"새 모델 시험 쪽 {N_NEW_TEST} (집단 새모델)"] = (len(new) == N_NEW_TEST
                                                   and all(gen[u]["집단"] == "새모델" for u in new))
    rows[f"재생성 시험 쪽 {N_REGEN_TEST} (집단 재생성)"] = (len(regen) == N_REGEN_TEST
                                                     and all(gen[u]["집단"] == "재생성" for u in regen))
    cells = {slot: sorted(u for u in new if gen[u]["칸"] == slot) for slot in SLOTS}
    rows["칸 넷의 합 = 새 모델 252"] = sum(len(v) for v in cells.values()) == len(new)
    rows["칸마다 62~64 계정"] = all(CELL_RANGE[0] <= len(v) <= CELL_RANGE[1] for v in cells.values())
    rows["새 모델 생성모델 = 모델ID표 칸 모델"] = all(gen[u]["생성모델"] == slot_model[s] for s, v in cells.items()
                                              for u in v)
    bots = new + regen
    rows["봇 라벨 bot · 사람 라벨 human"] = (all(gen[u].get("라벨") == "bot" for u in bots)
                                         and all(A130[u].get("라벨") == "human" for u in test_split))
    rows["문서 10건 이상 · 적격 false 없음"] = all(gen[u]["문서수"] >= MIN_DOCS and gen[u].get("적격") is not False
                                            for u in bots) and all(A130[u]["문서수"] >= MIN_DOCS for u in test_split)
    rows["문장길이 정합(개수 = 문장수, 합 = 토큰수_구두점제외)"] = all(
        len(x["문장길이"]) == x["문장수"] and sum(x["문장길이"]) == x["토큰수_구두점제외"]
        for x in [gen[u] for u in bots] + [A130[u] for u in test_split])
    rows["페르소나 중복 없음(집단 안)"] = all(len({gen[u]["페르소나id"] for u in g}) == len(g) for g in (new, regen))
    rows["봇 ∩ 사람 = ∅"] = not (set(bots) & set(test_split))
    for k, v in rows.items():
        say(f"      {k:<52} {'통과' if v else '■ 실패'}")
    check(all(rows.values()), "표본 구성이 사전선언 · 입력 사슬과 다르다.")
    accs = {**{u: gen[u] for u in bots}, **{u: A130[u] for u in test_split}}
    strata_regen = [slot_model[gen[u]["모델슬롯"]] for u in regen]
    say(f"      칸별 계정: " + " · ".join(f"{s} {slot_model[s]} {len(v)}" for s, v in cells.items())
        + f" · 재생성 {len(regen)} · 시험 사람 {len(test_split)}")
    return accs, {"new": new, "regen": regen, "cells": cells, "humans": test_split, "strata_regen": strata_regen,
                  "slot_model": slot_model, "model_of": {u: gen[u]["생성모델"] for u in bots}}, {
        "항목": rows, "12-1_sha256": sha121, "통과": True,
        "칸별_계정수": {s: len(v) for s, v in cells.items()}, "재생성": len(regen), "시험사람": len(test_split)}


# ════════════════════════════════════════════════════════════════════════
# [적용] 묶음 하나 = (봇 목록, 사람 234). 네 도구 · AUC · 구간 · 짝지은 차 · 기술 문턱
# ════════════════════════════════════════════════════════════════════════
def purity(conf):
    """문턱 위 봇 순도 = TP/(TP+FP), 문턱 아래 사람 순도 = TN/(TN+FN). 분모 0이면 None."""
    tp, fn, fp, tn = conf["TP"], conf["FN"], conf["FP"], conf["TN"]
    return {"문턱위_봇순도": (tp / (tp + fp)) if (tp + fp) else None,
            "문턱아래_사람순도": (tn / (tn + fn)) if (tn + fn) else None}


def eval_batch(name, accs, bots, hums, strata, key, bundle, Wh, keys):
    """[라벨 사용] 채점 묶음 = bots + hums. 라벨은 AUC · 부트스트랩 층 · 기술 문턱 지표에만 쓴다."""
    X = build_matrix(accs, bots + hums, keys, bundle["axis_map"])
    nb, nh = len(bots), len(hums)
    y = np.array([1] * nb + [0] * nh)
    s, P = score_bundle(bundle, X)
    manual = sigmoid(bundle["intercept"] + P @ np.asarray(bundle["coef"]))
    dmax = float(np.max(np.abs(manual - s[ROW_POS])))
    check(dmax < 1e-12, f"{name}: 위치 점수가 번들 손 공식과 다르다({dmax})")
    Wb = boot_counts(key, strata, N_BOOT)
    bidx, hidx = np.arange(nb), np.arange(nb, nb + nh)
    tools, dist = {}, {}
    for t, sc in s.items():
        pt, d = auc_boot(sc, bidx, hidx, Wb, Wh)
        dist[t] = d
        row = {"AUC": pt, "CI95": ci95(d),
               **{f"탐지율@오탐{int(round(tg * 100))}%": tpr_at_fpr(sc, y, tg) for tg in FPR_TARGETS}}
        if t in bundle["thresholds"]:
            thr = bundle["thresholds"][t]
            m = metrics(sc, y, thr)
            m.update(purity(m["혼동"]))
            m["문턱"] = thr
            m["봇표시비율"] = float(np.mean(sc >= thr))
            row["자체문턱_기술"] = m
        tools[t] = row
    diffs = {"제안-위치": paired_diff(tools[ROW_PROP]["AUC"], dist[ROW_PROP], tools[ROW_POS]["AUC"], dist[ROW_POS]),
             "밀도-위치": paired_diff(tools[ROW_DENS]["AUC"], dist[ROW_DENS], tools[ROW_POS]["AUC"], dist[ROW_POS])}
    n_missing = int(np.isnan(X).sum())
    out = {"묶음": name, "n_봇": nb, "n_사람": nh, "결측칸": n_missing, "위치_손공식_최대차": dmax,
           "부트스트랩": {"봇_열쇠": list(key), "사람_열쇠": list(KEY_HUMANS), "봇_층": sorted(set(map(str, strata)))},
           "도구": tools, "짝지은차": diffs,
           "계정별점수": {u: {t: float(sc[i]) for t, sc in s.items()} for i, u in enumerate(bots + hums)}}
    p, q, dn, bs = (tools[t] for t in (ROW_POS, ROW_PROP, ROW_DENS, ROW_BASE))
    dd = diffs["제안-위치"]
    say(f"  {name:<44} 봇 {nb:>3} · 위치 {p['AUC']:.4f} [{p['CI95'][0]:.4f}, {p['CI95'][1]:.4f}] · 밀도 "
        f"{dn['AUC']:.4f} [{dn['CI95'][0]:.4f}, {dn['CI95'][1]:.4f}] · 제안 {q['AUC']:.4f} "
        f"[{q['CI95'][0]:.4f}, {q['CI95'][1]:.4f}] · 기준선 {bs['AUC']:.4f} · 제안−위치 {dd['차']:+.4f} "
        f"[{dd['CI95'][0]:+.4f}, {dd['CI95'][1]:+.4f}]")
    return out, dist


def evaluate_all(accs, S, bundle, keys, verbose=True):
    """[라벨 사용] 묶음 여섯. 시험 사람 재추출 행렬 하나를 모든 묶음이 공유한다(D4)."""
    if verbose:
        label_use("시험 봇 · 시험 사람 라벨로 AUC · 부트스트랩 층 · 기술 문턱 지표")
    hums = S["humans"]
    Wh = boot_counts(KEY_HUMANS, [0] * len(hums), N_BOOT)
    res, dists = {}, {}
    old = sys.stdout
    if not verbose:
        sys.stdout = open(os.devnull, "w")
    try:
        for slot in SLOTS:
            m = S["slot_model"][slot]
            bots = S["cells"][slot]
            name = f"칸 {slot} {m}"
            res[name], dists[name] = eval_batch(name, accs, bots, hums, [m] * len(bots), KEY_CELL[slot],
                                                bundle, Wh, keys)
        res[BATCH_POOLED], dists[BATCH_POOLED] = eval_batch(
            BATCH_POOLED, accs, S["new"], hums, [S["model_of"][u] for u in S["new"]], KEY_POOLED, bundle, Wh, keys)
        res[BATCH_REGEN], dists[BATCH_REGEN] = eval_batch(
            BATCH_REGEN, accs, S["regen"], hums, S["strata_regen"], KEY_REGEN, bundle, Wh, keys)
    finally:
        if not verbose:
            sys.stdout.close()
            sys.stdout = old
    return res, dists


def judge(res):
    """P12-3 · P12-4 기계 판정(D6). 판정 표본 = 합동 묶음."""
    pooled = res[BATCH_POOLED]
    a = pooled["도구"][ROW_PROP]["AUC"]
    d = pooled["짝지은차"]["제안-위치"]
    out = [{"번호": "P12-3", "서술": PRED_TEXT["P12-3"], "판정": "적중" if a >= P123_AUC else "빗나감",
            "관측": f"합동 제안 AUC {a:.6f} (기준 ≥ {P123_AUC})"}]
    if d["천장동률"]:
        v = "판정불가"
    else:
        v = "적중" if d["CI95"][0] >= P124_LO else "빗나감"
    out.append({"번호": "P12-4", "서술": PRED_TEXT["P12-4"], "판정": v,
                "관측": f"합동 제안 − 위치 {d['차']:+.6f} [{d['CI95'][0]:+.6f}, {d['CI95'][1]:+.6f}]의 하한 "
                        f"≥ {P124_LO}{' (천장 동률)' if d['천장동률'] else ''}"})
    return out


# ════════════════════════════════════════════════════════════════════════
# [Markdown]
# ════════════════════════════════════════════════════════════════════════
def f4(x, sign=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "없음"
    return f"{x:+.4f}" if sign else f"{x:.4f}"


def ci(r, sign=False):
    return f"{f4(r['AUC'] if 'AUC' in r else r['차'], sign)} [{f4(r['CI95'][0], sign)}, {f4(r['CI95'][1], sign)}]"


def write_markdown(out):
    today = datetime.now().strftime("%Y-%m-%d")
    res = out["적용"]
    L = ["---", 'title: "12_판별기적용"', 'rating: "☆☆☆☆☆"', 'aliases: ["12-3 결과표", "OpenRouter 판별기 적용"]',
         'status: "[[🚦refining]]"', 'MOC: "[[📚 203 Research]]"', 'type: "[[🔖 Experiment]]"',
         'index: "[[🏷️ misc]]"', "tags:", '  - "#category/001_연구방법론"', '  - "#봇탐지"', '  - "#문체분석"',
         'access: "[[🔒 private]]"', 'author: "[[👤손제홍]]"',
         f'source: "12-3_판별기적용.py 자동 산출(스크립트 sha256 {out["설정"]["스크립트_sha256"][:16]}, '
         f'결과_digest {out["결과_digest"][:16]})"',
         'source_url: ""', f'creation_date: "{today}"', f'modification_date: "{today}"', "---", "",
         "# 12-3 판별기 적용 : OpenRouter 시험 쪽", "",
         "> [!warning] 판정 문장은 연구자가 쓴다",
         "> 이 파일은 12-3_판별기적용.py가 만든 수치와 규칙 판정이다.", "",
         "> [!caution] 범위",
         "> BotSim 공개 코드를 재구성한 댓글 생성 조건, 댓글 한정 계정, Reddit 2023~24 사람 고정 안의 값이다. "
         "11 판별기는 BotSim 매칭 1,024계정(전체 글)으로 학습했고 여기서 다시 배우지 않는다. 칸은 62~64 페르소나라 "
         "구간이 넓다.", "",
         "## 표 1. 네 도구 AUC (묶음별)", "",
         f"채점 묶음 = 봇 목록 + 봉인 시험 사람 {out['표본']['시험사람']}. 밀도 · 제안은 묶음마다 새로 매긴다. "
         f"AUC 구간 = 계정 부트스트랩 {N_BOOT:,}회 95%(봇 · 사람 층별, 같은 묶음 안 도구끼리 짝지음).", "",
         "| 묶음 | 봇 | 위치 | 밀도(k=10) | 제안 | 기준선 | 제안 − 위치 | 밀도 − 위치 |",
         "|---|---|---|---|---|---|---|---|"]
    for name, r in res.items():
        t = r["도구"]
        L.append(f"| {name} | {r['n_봇']} | {ci(t[ROW_POS])} | {ci(t[ROW_DENS])} | {ci(t[ROW_PROP])} | "
                 f"{ci(t[ROW_BASE])} | {ci(r['짝지은차']['제안-위치'], True)} | {ci(r['짝지은차']['밀도-위치'], True)} |")
    L += ["", "## 표 2. 밀도 참고 k (판정에 쓰지 않음)", "", "| 묶음 | 밀도(k=5) | 밀도(k=10) | 밀도(k=20) |",
          "|---|---|---|---|"]
    for name, r in res.items():
        t = r["도구"]
        L.append(f"| {name} | {ci(t['밀도(k=5)'])} | {ci(t[ROW_DENS])} | {ci(t['밀도(k=20)'])} |")
    L += ["", "## 표 3. 번들 문턱(BotSim 내부)으로 낸 기술 지표", "",
          "판정에 쓰지 않는다. 제안 문턱은 묶음 안 정규화 순위 위의 값이라 봇 표시 비율이 묶음 구성에 따라 정해진다.", "",
          "| 묶음 | 도구 | 문턱 | 봇 표시 비율 | 균형정확도 | 탐지율 | 오탐률 | 위 봇 순도 | 아래 사람 순도 | 탐지@오탐5% | 탐지@오탐10% |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in res.items():
        for tool in (ROW_POS, ROW_PROP):
            m = r["도구"][tool]["자체문턱_기술"]
            L.append(f"| {name} | {tool} | {m['문턱']:.6g} | {f4(m['봇표시비율'])} | {f4(m['균형정확도'])} | "
                     f"{f4(m['봇탐지율'])} | {f4(m['사람오탐률'])} | {f4(m['문턱위_봇순도'])} | "
                     f"{f4(m['문턱아래_사람순도'])} | {f4(m['탐지율@오탐5%'])} | {f4(m['탐지율@오탐10%'])} |")
    L += ["", "## 예측 대조 (빗나가도 지우지 않는다)", ""]
    for p in out["예측대조"]:
        L.append(f"- **{p['번호']}** [{p['판정']}] {p['서술']}")
        L.append(f"\t- {p['관측']}")
    L += ["", "## 관문", ""]
    for k, v in out["관문_요약"].items():
        L.append(f"- {k}: {'통과' if v else '실패'}")
    L += ["", f"결과_digest `{out['결과_digest']}`", ""]
    txt = "\n".join(L)
    check(chr(0x2014) not in txt and chr(0x2013) not in txt, "Markdown에 줄표 · 반각 대시")
    with open(OUT_MD + PARTIAL, "w", encoding="utf-8") as f:
        f.write(txt)


# ════════════════════════════════════════════════════════════════════════
# [본 계산]
# ════════════════════════════════════════════════════════════════════════
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="12-3 판별기 적용 (뼈대 5절 4항, 마감판)")
    ap.add_argument("--overwrite", action="store_true", help="이미 있는 산출(.json · .md · _출력.log)을 덮어쓴다")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if sys.flags.optimize:
        sys.exit("python -O로는 실행하지 않습니다(assert가 꺼진다). -O 없이 다시 실행하십시오.")
    have = [os.path.basename(p) for p in (OUT_JSON, OUT_MD, OUT_LOG) if os.path.exists(p)]
    if have and not args.overwrite:
        sys.exit(f"산출이 이미 있습니다: {have}. 덮어쓰려면 --overwrite를 붙이십시오.")
    for p in INPUT_FILES:
        if not os.path.exists(p):
            sys.exit(f"입력이 없습니다: {p}")
    t0 = time.time()
    started = datetime.now().astimezone().isoformat()
    stage, gates = {}, RUN.gates
    RUN.tee = Tee(OUT_LOG + PARTIAL)
    sys.stdout = RUN.tee
    say("=" * 74)
    say("12-3 판별기 적용: 11 판별기(위치 · 밀도 · 제안 · 기준선)를 OpenRouter 시험 쪽에 적용  (라벨을 읽는다)")
    say("=" * 74)
    say(f"실행 {started} · python {platform.python_version()} · numpy {np.__version__} · scikit-learn "
        f"{sklearn.__version__} · scipy {scipy.__version__} · joblib {joblib.__version__} · 부트스트랩 {N_BOOT:,}")
    hashes_before = {p: sha256_file(p) for p in INPUT_FILES}

    t = time.time()
    line("[1/5] 관문 A : 복사 AST 대조 · 뼈대 예측 원문 · 손 예제")
    c_res, c_ok = gate_copies()
    gates["A_복사대조"] = {**c_res, "통과": c_ok}
    check(c_ok, "복사한 함수 · 상수가 원본 소스와 다르다.")
    d_res, d_ok = gate_decl_text()
    gates["A_뼈대원문"] = {**d_res, "통과": d_ok}
    check(d_ok, "예측 문장이 뼈대 원문과 다르다.")
    h_res, h_ok = gate_hand()
    gates["A_손예제"] = h_res
    check(h_ok, "손 예제가 손계산과 맞지 않는다.")
    stage["관문A"] = round(time.time() - t, 2)

    t = time.time()
    line("[2/5] 관문 B : 입력 사슬 (번들 sha256은 열기 전에 대조)")
    j11, bundle, b_res = gate_inputs()
    gates["B_입력사슬"] = b_res
    keys = {bb: [k for x, k in bundle["feature_order"] if x == bb] for bb in BLOCK_SIZES}
    stage["관문B"] = round(time.time() - t, 2)

    t = time.time()
    line("[3/5] 표본 : 시험 쪽 새 모델 252 (칸 넷) · 재생성 254 · 봉인 시험 사람 234")
    label_use("표본 구성 확인: 12-1 · 13-0의 집단 · 역할 · 라벨 필드(계산에는 쓰지 않음)")
    accs, S, s_res = build_samples(bundle)
    gates["C_표본"] = s_res
    stage["표본"] = round(time.time() - t, 2)

    t = time.time()
    line("[4/5] 적용 : 묶음 여섯 × 네 도구 · AUC와 95% 구간 · 짝지은 차 · 결정성 · 예측")
    res, dists = evaluate_all(accs, S, bundle, keys)
    res2, dists2 = evaluate_all(accs, S, bundle, keys, verbose=False)
    dg1 = digest(jsonable({"적용": res, "분포": {k: {t_: v.tolist() for t_, v in d.items()} for k, d in dists.items()}}))
    dg2 = digest(jsonable({"적용": res2, "분포": {k: {t_: v.tolist() for t_, v in d.items()} for k, d in dists2.items()}}))
    say(f"  결정성(같은 프로세스 재계산) digest {dg1[:16]}… · {dg2[:16]}… → {'같음' if dg1 == dg2 else '■ 다름'}")
    gates["D_결정성"] = {"digest": [dg1, dg2], "통과": dg1 == dg2}
    check(dg1 == dg2, "같은 프로세스 안 재계산이 비트 단위로 같지 않다.")
    preds = judge(res)
    for p in preds:
        say(f"  {p['번호']} [{p['판정']}] {p['서술']}\n        관측: {p['관측']}")
    ok_same = {p: sha256_file(p) for p in INPUT_FILES} == hashes_before
    say(f"  입력 {len(INPUT_FILES)}개 sha256 실행 전후 동일: {ok_same}")
    gates["D_입력불변"] = {"통과": ok_same}
    check(ok_same, "실행 중 입력 파일이 바뀌었다.")
    stage["적용"] = round(time.time() - t, 2)

    line("[5/5] 저장")
    results = {"관문_요약": {k: bool(v.get("통과")) for k, v in gates.items()},
               "표본": s_res, "적용": res, "예측대조": preds}
    out = {
        "설정": {
            "사전선언": "12_OpenRouter생성_사전선언_뼈대.md 5절 4항 · 7절 P12-3 · P12-4 (마감판 2026-09-27)",
            "실행시각": started, "시드": SEED, "부트스트랩": N_BOOT, "천장": CEILING,
            "번들": {"파일": os.path.basename(BUNDLE11), "sha256": b_res["번들_sha256"],
                     "문턱": dict(bundle["thresholds"]), "밀도_k": bundle["density_k"],
                     "밀도_ks": list(bundle["density_ks"])},
            "구현결정": IMPLEMENTATION_DECISIONS, "사전예측": PRED_TEXT,
            "입력_sha256": {os.path.relpath(p, ROOT) if p.startswith(ROOT) else p: v for p, v in hashes_before.items()},
            "스크립트_sha256": sha256_file(SCRIPT_PATH),
            "버전": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                     "scikit-learn": sklearn.__version__, "joblib": joblib.__version__},
            "라벨사용": "표본 구성 확인(집단 · 역할 필드), AUC · 부트스트랩 층 · 기술 문턱 지표. 밀도는 라벨을 쓰지 않는다",
        },
        "관문": gates,
        **results,
    }
    out["결과_digest"] = digest(jsonable(results))
    out["소요초_단계별"] = stage
    out["소요초"] = round(time.time() - t0, 2)
    out["실행기록"] = {"sys.flags.optimize": int(sys.flags.optimize), "__debug__": bool(__debug__),
                   "시작": started, "끝": datetime.now().astimezone().isoformat(), "python_실행파일": sys.executable}
    write_out(OUT_JSON + PARTIAL, out)
    write_markdown(out)
    say(f"  결과_digest {out['결과_digest']}")
    say(f"  단계별 소요초 {stage} · 전체 {time.time() - t0:.1f}초")
    sys.stdout.flush()
    RUN.tee.f.close()
    sys.stdout = RUN.tee.out
    for p in (OUT_JSON, OUT_MD, OUT_LOG):
        os.replace(p + PARTIAL, p)
    print(f"정본 이름으로 바꿈: {', '.join(os.path.basename(p) for p in (OUT_JSON, OUT_MD, OUT_LOG))}")
    return out


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except AssertionError as e:      # check()가 던진 관문 실패
        if RUN.tee is None:
            raise
        stop(f"관문(check) 실패: {e}")
    except Exception:
        if RUN.tee is None:
            raise
        stop("예외: " + traceback.format_exc())
