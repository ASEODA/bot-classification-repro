#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
08_R블록.py
────────────────────────────────────────────────────────────────────────────
목적
    지문의 셋째 블록 R(리듬·구두점)을 처음으로 검정한다. 06은 낱말(F 블록),
    07은 형태자질(M 블록)을 봤다. 남은 R은 "문장을 얼마나 길게 끊는가,
    구두점을 얼마나 찍는가, 그 길이가 얼마나 고른가"다. 낱말을 하나도 보지
    않고 글의 리듬만으로 봇과 사람이 갈리는지를 묻는다.

무엇을 재는가 (보관된 13-19 사전선언의 「16 R 블록」(현 08) 그대로, 3종 · BH 집합 1)
    ① 문장당 토큰수     = 토큰수_구두점제외 ÷ 문장수
    ② 구두점 비율       = (토큰수 − 토큰수_구두점제외) ÷ 토큰수
    ③ 문장 길이 변동계수 = 문장 길이 목록의 표준편차 ÷ 평균
                          (문장 5개 미만 계정은 결측)
    셋 다 계정 하나에 값 하나다. 04·04-1이 이미 세어 둔 수를 나누기만 하며
    새 파싱은 없다.

왜 이 셋인가 · 무엇을 일부러 뺐나
    문서 길이와 계정 총량은 R에 넣지 않는다(보관된 13-19 사전선언의 16항(현 08)이 정한 '제외 자질').
    그 둘은 09-1이 분량 혼입으로 지목한 축이라, 리듬을 재는 척하면서 실은
    "누가 더 많이 썼나"를 재게 된다. ①은 분자와 분모가 같은 계정 안에서
    나뉘고, ②는 비율이며, ③은 평균으로 나눈 무단위 값이라 셋 다 총량이
    커져도 저절로 커지지 않는다. 그것이 이 셋만 남긴 이유다.

입력을 둘에서 가져오는 이유
    ①②의 재료(문장수·토큰수·토큰수_구두점제외)는 04에도 04-1에도 있다.
    ③의 재료(문장 길이 목록)는 04-1에만 있다. 그래서 04-1을 주 입력으로 쓰되,
    04와 계정별로 대조해 두 파일이 같은 자료를 말하는지 먼저 확인한다
    (아래 [3/7] 정합 관문). 04-1은 이미 자기 정합 관문을 통과했지만, 이
    파일이 쓰는 세 수치에 대해서는 이 파일이 다시 확인한다 — 앞 단계가
    통과했다는 말을 믿고 넘어가는 것이 사슬이 끊기는 가장 흔한 자리다.

라벨을 어디서 여는가
    ■ 이 파일은 라벨을 읽는다. ■ 04-1은 읽지 않았고(04와 같은 규율),
    09-3·02-1·08과 옛 17~19(보관)는 읽는다.
    아래 [1/7]의 '라벨 개봉' 블록이 그 지점이다.
    ①②③의 계산에는 라벨이 한 번도 들어가지 않는다 — 계정별 값을 전부
    만든 뒤에 이름표를 붙여 두 무더기로 가른다.

무엇을 따르나
    보관된 13-19_사전선언.md (2026-08-31 확정)의 「16 R 블록」(현 08).
    통계는 06_봇사람비교.py의 함수를 ast로 복사해 그대로 쓴다(문턱 0.05·
    0.147도 06·07과 같다). 결측 규칙은 07을 따른다 — 분모가 성립하지 않는
    칸은 그 자질의 검정에서만 빠지고, 계정이 통째로 빠지지 않는다.
    결과가 약하게 나왔다고 다른 자를 대지 않는다.

실행
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 -u 08_R블록.py
    표준 라이브러리만 쓴다. 계정 1,869개 × 자질 3종이라 몇 초면 끝난다.

선행 조건
    같은 폴더에 04-1_확장재파싱.json · 04_기능어측정.json · 01_적격계정.json ·
    05_사용률검수.json · 06_봇사람비교.py 가 있어야 한다.

산출
    08_R블록.json    자질 3종의 U·z·p·q·δ·방향 + 사분위 요약과 IQR 비
                     + 사전 예측 P16-1~P16-4 대조
"""

import ast
import hashlib
import json
import math
import os
import platform
import statistics
import time


# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더를 기준으로 잡는다 — 연구 폴더를 통째로 옮겨도 깨지지 않는다.
HERE = os.path.dirname(os.path.abspath(__file__))
REPARSE_JSON = f"{HERE}/04-1_확장재파싱.json"    # 04-1 산출물 — 주 입력(문장 길이 목록)
MEASURE_JSON = f"{HERE}/04_기능어측정.json"      # 04 산출물 — 교차 확인용
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"       # 01 산출물 — "라벨" 키만 꺼낸다
RATES_JSON = f"{HERE}/05_사용률검수.json"        # 05 산출물 — 기능어 해시 승계용
COMPARE_PY = f"{HERE}/06_봇사람비교.py"          # 06 원본 — 통계 함수의 출처
OUT_JSON = f"{HERE}/08_R블록.json"               # 산출물

GROUP1, GROUP2 = "bot", "human"
# 06·07과 같은 순서로 고정한다. U와 δ는 모두 '그룹1 기준'이라 이 순서가
# 뒤집히면 부호가 통째로 반대가 되고, 06·07과의 대조가 전부 어긋난다.
#   δ > 0  →  봇이 높음
#   δ < 0  →  봇이 낮음

Q_ALPHA = 0.05          # BH 보정 후 유의 판정 문턱 (사전선언: q = 0.05, 06·07과 동일)
DELTA_NOTABLE = 0.147   # '주목'의 효과크기 하한 (관례적 small 경계, 06·07과 동일)
MIN_SENTENCES_CV = 5    # 변동계수를 낼 최소 문장 수 (보관된 13-19 사전선언의 16항(현 08): 5개 미만은 결측)

RATE_DIGITS = 6         # 비율·중앙값 저장 자릿수 (04·05·07과 같은 눈금)
STAT_DIGITS = 4         # U·z·δ 저장 자릿수
SIG_DIGITS = 6          # p·q는 유효숫자로 자른다 — 06에서 복사한 sig()가 쓴다

# 승계 해시. 04-1이 05에서 읽어 적어 둔 값과 같아야 한다.
FUNCWORD_HASH = "382b68572f03bc23"      # 기능어 172종 목록의 해시(사전선언 값)

# ── 06에서 AST로 복사해 온 함수들 ───────────────────────────────
# 아래 [승계] 절이 실행할 때마다 06의 원본과 이 파일의 사본을 각각 ast로 다시
# 떠서 해시를 맞춰 본다. 사본을 손대면 그 자리에서 걸린다. 04-1이 쓴 것과 같은
# 일곱 개, 같은 순서, 같은 해시다.
COPIED_NAMES = ["normal_cdf", "ranks_with_ties", "mann_whitney",
                "bh_qvalues", "quartiles", "sig", "direction_of"]
COPIED_HASH = "b3de6ef352db03a1"    # 위 7개 소스를 이 순서로 이은 sha256 앞 16자

# ── 자질 정의 (보관된 13-19 사전선언의 16항(현 08) 그대로) ──────────────
# 키 · 화면 이름 · 단위 · 정의 문장. 이 순서로 표에 찍고 JSON에 담는다.
# BH 집합은 이 셋이다(m = 3).
FEATURES = [
    ("문장당_토큰수", "문장당 토큰수", "토큰/문장",
     "토큰수_구두점제외 ÷ 문장수"),
    ("구두점_비율", "구두점 비율", "비율",
     "(토큰수 − 토큰수_구두점제외) ÷ 토큰수"),
    ("문장길이_변동계수", "문장길이 변동계수", "무단위",
     f"문장 길이 목록의 표본표준편차 ÷ 평균 (문장 {MIN_SENTENCES_CV}개 미만은 결측)"),
]
FEATURE_KEYS = [k for k, _, _, _ in FEATURES]

# ── 자가검증 고정 예제 (1) 통계 ─────────────────────────────────
# 06의 SELF_CHECK_* 를 그대로 가져왔다. 손계산 과정은 06_봇사람비교.py의
# self_check() docstring에 있고, 기대값은 그 손계산에서 온 상수다.
#   (설명, A(=그룹1), B(=그룹2), 기대 U_A, 기대 δ, 기대 σ²)
SELF_CHECK_U = [
    ("완전 분리", [1, 2, 3], [4, 5, 6], 0.0, -1.0, 5.25),
    ("동점 포함", [1, 1, 2], [1, 2, 2], 3.0, -1.0 / 3.0, 4.05),
]
SELF_CHECK_BH_P = [0.01, 0.02, 0.03, 0.04]
SELF_CHECK_BH_Q = [0.04, 0.04, 0.04, 0.04]
SELF_CHECK_TOL = 1e-9

# ── 자가검증 고정 예제 (2) R 블록의 분모·결측 규칙 ──────────────
# 08에서 새로 들어온 규칙이라 새로 만든 예제다. 인공 계정 네 개로 세 자질의
# 나눗셈과 결측 판정을 한꺼번에 건다. 손계산은 self_check_features()의
# docstring에 있다. 네 계정 모두 sum(문장길이) = 토큰수_구두점제외 가 되도록
# 만들어 두었다 — 실제 자료가 지켜야 하는 관계이기도 하다([3/7]에서 검사).
SELF_CHECK_ACCOUNTS = {
    "가": {"토큰수": 100, "토큰수_구두점제외": 90, "문장수": 10,
           "문장길이": [9] * 10},
    "나": {"토큰수": 12, "토큰수_구두점제외": 10, "문장수": 4,
           "문장길이": [1, 2, 3, 4]},
    "다": {"토큰수": 0, "토큰수_구두점제외": 0, "문장수": 0,
           "문장길이": []},
    "라": {"토큰수": 25, "토큰수_구두점제외": 20, "문장수": 5,
           "문장길이": [2, 4, 4, 4, 6]},
}
#   (계정, 자질, 기대값 — None은 결측, 설명)
SELF_CHECK_FEATURE = [
    ("가", "문장당_토큰수", 9.0, "90 ÷ 10. 열 문장이 다 아홉 토큰"),
    ("가", "구두점_비율", 0.10, "구두점 = 100 − 90 = 10, 10 ÷ 100"),
    ("가", "문장길이_변동계수", 0.0, "길이가 전부 같다 → 표준편차 0 → CV 0"),
    ("나", "문장당_토큰수", 2.5, "10 ÷ 4"),
    ("나", "구두점_비율", 2.0 / 12.0, "구두점 2개 ÷ 전체 12"),
    ("나", "문장길이_변동계수", None, "문장이 4개뿐 → 5개 미만이라 결측"),
    ("다", "문장당_토큰수", None, "문장수 0 → 분모 0 → 결측"),
    ("다", "구두점_비율", None, "토큰수 0 → 분모 0 → 결측"),
    ("다", "문장길이_변동계수", None, "문장 목록이 비어 있음 → 결측"),
    ("라", "문장당_토큰수", 4.0, "20 ÷ 5"),
    ("라", "구두점_비율", 0.20, "구두점 5개 ÷ 전체 25"),
    ("라", "문장길이_변동계수", math.sqrt(2.0) / 4.0,
     "평균 4, 편차 −2·0·0·0·+2 → 제곱합 8, ÷(5−1)=2, √2 ≈ 1.4142 → ÷4"),
]
# 결측이 그 자질의 검정에서만 빠지는지(계정이 통째로 빠지지 않는지) 확인한다.
#   자질 → (기대 유효 계정 수, 기대 결측 계정 수)   ※ 위 인공 계정 4개 기준
SELF_CHECK_DEFINED = {
    "문장당_토큰수": (3, 1),
    "구두점_비율": (3, 1),
    "문장길이_변동계수": (2, 2),
}
# ── 자가검증 고정 예제 (3) 사분위 폭 비 ─────────────────────────
# 산포 판정(P16-4)이 쓰는 나눗셈을 따로 건다. 손계산은 self_check_iqr()에 있다.
SELF_CHECK_IQR_BOT = [1, 2, 3, 4]
SELF_CHECK_IQR_HUMAN = [0, 2, 4, 6]
SELF_CHECK_IQR_EXPECT = (1.5, 3.0, 0.5)     # (봇 IQR, 사람 IQR, 봇÷사람)

# ── 사전 예측 (보관된 13-19_사전선언 「16 R 블록」(현 08)의 네 항목) ──
# 이 상수가 사전등록의 실체다. 여기 적힌 부호는 결과를 보기 전에 문서에
# 확정된 것이고, 아래 [7/7]이 실제 δ와 자동으로 대조한다. 빗나간 예측을
# 조용히 지우거나 문구를 고치면 사전등록이 아무 의미가 없어진다 — 빗나간
# 것도 그대로 화면과 JSON에 남긴다.
#
# "근거"는 화면 폭에 맞춰 미리 끊어 둔 줄의 목록이다. 자동 줄바꿈을 쓰지
# 않는 것은 이 파일의 다른 표들과 같은 이유다 — 한글은 터미널에서 두 칸을
# 차지해 글자 수로 자르면 폭이 맞지 않는다. JSON에는 한 줄로 이어 담는다.
PREDICTIONS = [
    {"번호": "P16-1",
     "서술": "문장당 토큰수: 봇이 낮다 (δ < 0)",
     "종류": "부호",
     "검사": [("문장당_토큰수", "<")],
     "근거": ["03 감사 표본에서 봇 17.0 vs 사람 19.6 토큰이었다.",
             "그 표본은 계정 몇 개를 눈으로 본 것이라 전수에서도 같은",
             "방향인지는 여기서 처음 확인한다."]},
    {"번호": "P16-2",
     "서술": "구두점 비율: 봇이 낮다 (δ < 0)",
     "종류": "부호",
     "검사": [("구두점_비율", "<")],
     "근거": ["07의 UPOS PUNCT가 δ = −0.176 이었다. 그것은 구두점을",
             "'구두점 제외 토큰수'로 나눈 값이고, 여기 ②는 '전체 토큰수'로",
             "나눈다. 분모가 달라도 같은 부호가 나와야 한다 —",
             "07의 값을 x라 하면 여기 ②는 x/(1+x)이고, 이 함수가 순증가라",
             "순위가 하나도 바뀌지 않기 때문이다."]},
    {"번호": "P16-3",
     "서술": "문장 길이 변동계수: 봇이 낮다 (δ < 0)",
     "종류": "부호",
     "검사": [("문장길이_변동계수", "<")],
     "근거": ["옛 산포검정(보관)이 잡은 '뭉침'의 연장이다. 봇 계정들이",
             "사용률에서 서로 닮아 있었다면 문장 길이도 고르게 쓸 것이라고",
             "보았다. 이 예측만 다른 셋과 성격이 다르다 — 위치가 아니라 계정",
             "'안'의 산포를 재는 자질이라, 빗나가도 ①②와 모순되지 않는다."]},
    {"번호": "P16-4",
     "서술": "세 자질의 사분위 폭 비(봇 IQR ÷ 사람 IQR)가 모두 1 미만",
     "종류": "IQR비",
     "검사": [(k, "<1") for k in FEATURE_KEYS],
     "근거": ["옛 산포검정(보관)의 뭉침이 R 블록에서도 나타나는지를 본다.",
             "1 미만이면 봇 계정들끼리의 폭이 사람보다 좁다는 뜻이다.",
             "이것은 위치(δ)와 독립이다 — 중앙값이 같아도 폭은 다를 수 있다."]},
]

# 03·07에서 가져온 대조 기준. 화면에 나란히 찍어 R 블록의 크기를 가늠하게 한다.
# 아래 셋은 07_형태자질비교.json 의 UPOS PUNCT 칸에 적힌 값이다(분모는
# 토큰수_구두점제외). ②는 같은 분자를 '전체 토큰수'로 나눈 것이라, 두 값은
# 계정마다 x ↦ x/(1+x) 로 이어져 있다. 이 함수는 x > 0 에서 순증가라 순위를
# 하나도 바꾸지 않는다 — 그러므로 U·z·p·δ가 07과 '똑같이' 나와야 한다.
# 비슷하게가 아니라 똑같이다. 어긋나면 어느 한쪽의 분모 처리가 틀린 것이라,
# 아래 [7/7]에서 그 일치를 직접 확인한다.
REF_PUNCT_DELTA = -0.1758       # 07 UPOS PUNCT의 δ
REF_PUNCT_U = 325579.0          # 07 UPOS PUNCT의 U
REF_PUNCT_Z = -6.2591           # 07 UPOS PUNCT의 z
REF_AUDIT_BOT = 17.0            # 03 감사 표본의 봇 문장당 토큰수
REF_AUDIT_HUMAN = 19.6          # 03 감사 표본의 사람 문장당 토큰수

# 표 머리글. 한글은 터미널에서 두 칸을 차지해 f-string의 자리맞춤이 어긋난다.
# 그래서 06·07과 같은 방식으로 공백을 손으로 세어 맞춰 두었다.
# 아래 print_feature_table()의 값 서식과 짝이므로 한쪽만 고치지 말 것.
TABLE_HEAD = ("      자질" + " " * 17 + "δ  방향" + " " * 14 + "q"
              + " " * 5 + "봇중앙" + " " * 3 + "사람중앙" + " " * 2 + "유효n")


def line(title=""):
    """구분선 한 줄. 06의 같은 함수를 그대로 가져왔다."""
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다. 04·04-1·05·06·07의 같은 함수를 그대로 가져왔다.

    임시 파일에 먼저 쓰고 이름을 바꿔치기한다(os.replace). 쓰는 도중에 창을
    닫으면 파일이 반쯤 잘린 채 남는다. 이름 바꾸기는 쪼개지지 않는 연산이라,
    어느 시점에 멈춰도 파일은 '이전 것' 아니면 '새 것'이다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def rnd(x, digits):
    """None을 견디는 반올림. 07의 같은 함수를 그대로 가져왔다."""
    return None if x is None else round(x, digits)


# ════════════════════════════════════════════════════════════════════════
# [승계] 06에서 AST로 복사한 통계 함수 — 아래 7개는 06의 소스 그대로다
# ════════════════════════════════════════════════════════════════════════
# 손으로 옮겨 적지 않았다. ast 모듈로 06_봇사람비교.py를 파싱해 함수 정의의
# 소스 조각을 그대로 떠 왔고, 실행할 때마다 verify_copied_functions()가
# 06의 원본과 이 파일의 사본을 다시 떠서 해시를 맞춘다. 통계 구현이 단계마다
# 조금씩 달라지는 것 — 같은 자로 재고 있다는 주장을 무너뜨리는 가장 흔한
# 경로 — 를 코드로 막아 두는 것이다. 04-1이 쓴 것과 같은 사본이다.
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


def verify_copied_functions():
    """
    06의 원본과 이 파일의 사본이 글자까지 같은지 확인한다.

    ast로 두 파일에서 같은 이름의 함수 정의 소스를 떠서, COPIED_NAMES 순서로
    이어 붙인 뒤 sha256 앞 16자를 비교한다. 주석 한 줄만 달라져도 해시가
    달라지므로, "06에서 가져왔다"는 말이 사실인지 매 실행 확인된다.

    반환: (통과 여부, 06 해시, 사본 해시)
    """
    def extract(path):
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        segs = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in COPIED_NAMES:
                segs[node.name] = ast.get_source_segment(src, node)
        if set(segs) != set(COPIED_NAMES):
            return None
        blob = "\n\n\n".join(segs[n] for n in COPIED_NAMES)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    h_src = extract(COMPARE_PY)
    h_copy = extract(os.path.abspath(__file__))
    ok = (h_src is not None and h_src == h_copy == COPIED_HASH)
    return ok, h_src, h_copy


# ════════════════════════════════════════════════════════════════════════
# [1] 입력 적재와 라벨 개봉
# ════════════════════════════════════════════════════════════════════════
def load_reparse():
    """04-1에서 설정과 계정을 가져온다. 라벨은 04-1에 없다."""
    data = json.load(open(REPARSE_JSON, encoding="utf-8"))
    return data["설정"], data["계정"]


def load_measure():
    """
    04에서 설정과 계정을 가져온다. 정합 관문의 대조 상대다.

    04는 4.7MB다. 여기서 쓰는 것은 계정별 세 수치(문장수·토큰수·
    토큰수_구두점제외)뿐이지만, 대조를 하려면 원본을 그대로 읽어야 한다.
    """
    data = json.load(open(MEASURE_JSON, encoding="utf-8"))
    return data["설정"], data["계정"]


def load_funcword_hash():
    """
    05에서 기능어 목록 해시 하나만 꺼낸다.

    08은 기능어를 한 낱말도 쓰지 않는다(R 블록은 리듬만 본다). 그런데도 이
    해시를 읽는 이유는 사슬을 잇기 위해서다 — 02가 만든 목록으로 04가 세고,
    05가 나누고, 06·07이 비교하고, 04-1이 다시 파싱한 그 자료 위에 08이
    올라앉아 있다는 사실을 로그에 남긴다. 값이 다르면 다른 실행분의 자료를
    섞어 쓰고 있다는 뜻이다.
    """
    data = json.load(open(RATES_JSON, encoding="utf-8"))
    h = (data.get("설정", {}).get("04승계", {}) or {}).get("기능어_해시")
    del data
    return h


def load_labels():
    """
    01에서 "라벨" 키 하나만 꺼낸다. 06·07의 같은 함수와 같은 규율이다.

    01은 23MB다. 원문·언어판정·깔때기 통계는 이 파일이 볼 일이 없으므로
    라벨만 들고 나오고 나머지는 그 자리에서 버린다.
    """
    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    labels = data.get("라벨") or {}
    del data                    # 원문("계정")·언어판정 등 나머지는 여기서 버린다
    return labels


def split_by_label(accounts, labels):
    """
    계정을 라벨에 따라 두 무더기로 가른다. 06·07의 같은 함수를 따른다.

    라벨이 없거나 bot/human이 아닌 계정은 비교에서 빠진다. 사전선언이 금지한
    '분석적 제외'가 아니라 대응할 짝이 없는 것이다 — 어느 무더기에 넣을지
    모르면 비교 자체가 성립하지 않는다. 01이 1,869계정 전원에 라벨을 달아
    두었으므로 실제로는 나올 일이 아니다. 나온다면 01을 의심해야 한다.
    """
    bot, human, missing, invalid = [], [], [], []
    for uid in sorted(accounts):
        lab = labels.get(uid)
        if lab is None:
            missing.append(uid)
        elif lab == GROUP1:
            bot.append(uid)
        elif lab == GROUP2:
            human.append(uid)
        else:
            invalid.append(uid)
    return bot, human, missing, invalid


# ════════════════════════════════════════════════════════════════════════
# [2] 자질 계산 — 나눗셈 셋과 결측 규칙
# ════════════════════════════════════════════════════════════════════════
def coef_variation(lengths, min_n=MIN_SENTENCES_CV):
    """
    문장 길이 목록의 변동계수. 표준편차 ÷ 평균이다.

    ■ 왜 변동계수이고 표준편차가 아닌가 ■
    표준편차만 보면 "문장이 원래 긴 사람"이 자동으로 커진다. 평균 20토큰인
    사람의 편차 5와 평균 10토큰인 사람의 편차 5는 고르기가 전혀 다르다.
    평균으로 나누면 길이의 단위가 사라져, 남는 것은 '평균 대비 얼마나
    흔들리는가'뿐이다. 09-1이 경계한 분량 혼입을 이 자질에서 막는 장치이기도
    하다.

    ■ 결측 규칙 (보관된 13-19 사전선언의 16항(현 08)) ■
    문장이 5개 미만이면 결측이다. 표준편차는 표본이 작을수록 요동이 커서,
    문장 두세 개짜리 계정의 CV는 '그 계정의 리듬'이 아니라 우연이다. 다섯
    이라는 숫자는 사전선언에 못 박은 값이고 결과를 보고 조정하지 않는다.
    평균이 0인 경우(모든 문장이 구두점뿐이라 길이가 전부 0)도 나눗셈이
    성립하지 않아 결측이다.

    ■ 표본표준편차를 쓴다 (n−1) ■
    사전선언은 "표준편차"라고만 적었다. 모표준편차(n으로 나눔)와 표본
    표준편차(n−1로 나눔) 중 후자를 쓴다. 계정마다 문장 수가 다르므로 두
    정의의 비는 √(n/(n−1))로 계정마다 달라 순위가 조금 흔들릴 수 있다.
    그래서 이 선택을 로그와 JSON에 명시하고, 모표준편차로 바꿨을 때의 δ도
    참고로 함께 적는다(판정에는 쓰지 않는다). 정의가 애매한 자리를 조용히
    지나가지 않기 위한 기록이다.
    """
    n = len(lengths)
    if n < min_n:
        return None
    mean = sum(lengths) / n
    if mean <= 0:
        return None
    return statistics.stdev(lengths) / mean


def coef_variation_pop(lengths, min_n=MIN_SENTENCES_CV):
    """모표준편차(n으로 나눔) 판(版). 참고값 전용 — 판정에 쓰지 않는다."""
    n = len(lengths)
    if n < min_n:
        return None
    mean = sum(lengths) / n
    if mean <= 0:
        return None
    return statistics.pstdev(lengths) / mean


def compute_features(accounts):
    """
    계정별로 자질 3종을 낸다. 라벨은 아직 붙이지 않는다.

    ■ 분모가 0이면 결측(None)이다 ■
    07이 세운 규칙을 그대로 따른다. 결측은 '값이 0'과 다르다. 문장이 0개인
    계정의 문장당 토큰수는 0이 아니라 '잴 수 없음'이고, 0으로 채우면 그
    계정이 "문장이 아주 짧다"는 자료로 둔갑한다. 결측은 그 자질의 검정에서만
    빠지고 다른 자질에는 그대로 들어간다 — 계정이 통째로 빠지는 것이 아니다.
    (01의 적격 기준이 문서 10건 이상이라 실제로 분모 0은 나오지 않는다.
     그래도 규칙을 코드에 남겨 둔다. 나오지 않는다는 것은 확인의 결과이지
     전제가 아니다.)

    반환: {uid: {자질키: 값 또는 None}}
    """
    out = {}
    for uid, a in accounts.items():
        tok = a["토큰수"]
        tok_np = a["토큰수_구두점제외"]
        n_sent = a["문장수"]
        lengths = a["문장길이"]

        row = {}
        # ① 문장당 토큰수 — 분모는 문장수
        row["문장당_토큰수"] = (tok_np / n_sent) if n_sent > 0 else None
        # ② 구두점 비율 — 분모는 전체 토큰수(구두점을 포함한 쪽이다)
        row["구두점_비율"] = ((tok - tok_np) / tok) if tok > 0 else None
        # ③ 문장 길이 변동계수 — 문장 5개 미만은 결측
        row["문장길이_변동계수"] = coef_variation(lengths)
        out[uid] = row
    return out


def compute_cv_pop(accounts):
    """③의 모표준편차 판을 따로 낸다. 참고값 전용."""
    return {uid: coef_variation_pop(a["문장길이"]) for uid, a in accounts.items()}


# ════════════════════════════════════════════════════════════════════════
# [자가검증] 통계 기계 · 자질 규칙 · 사분위 폭 비를 각각 고정 예제로 건다
# ════════════════════════════════════════════════════════════════════════
def self_check_stats():
    """
    06에서 복사한 U·δ·BH를 06의 세 고정 예제로 확인한다.

    손계산은 06_봇사람비교.py의 self_check() docstring에 그대로 있다.
        예제 1 완전 분리  A=[1,2,3] B=[4,5,6] → U=0, δ=−1, σ²=5.25
        예제 2 동점 포함  A=[1,1,2] B=[1,2,2] → U=3, δ=−1/3, σ²=4.05
        예제 3 BH 보정    p=[.01,.02,.03,.04] → q 전부 0.04
    소스 해시가 맞아도 실행 결과를 다시 보는 이유는, 해시가 맞는 것과 이
    파이썬에서 같은 값이 나오는 것은 다른 문제이기 때문이다.
    """
    print("\n  ── (1) 통계 기계 — 06의 고정 예제 세 가지 ──")
    ok = True
    for name, a, b, exp_u, exp_d, exp_var in SELF_CHECK_U:
        got = mann_whitney(a, b)
        print(f"    {name}  A={a}  B={b}")
        for label, actual, expect in (("U", got["U"], exp_u),
                                      ("δ", got["델타"], exp_d),
                                      ("σ²", got["시그마제곱"], exp_var)):
            good = abs(actual - expect) <= SELF_CHECK_TOL
            ok = ok and good
            print(f"      {label} 기대 {expect:>8.4f} · 실제 {actual:>8.4f} "
                  f"{'통과' if good else '실패'}")

    got_q = bh_qvalues(SELF_CHECK_BH_P)
    good = all(abs(g - e) <= SELF_CHECK_TOL
               for g, e in zip(got_q, SELF_CHECK_BH_Q))
    ok = ok and good
    print(f"    BH 보정  p={SELF_CHECK_BH_P}")
    print(f"      기대 q={SELF_CHECK_BH_Q}")
    print(f"      실제 q={[round(v, 4) for v in got_q]}  "
          f"{'통과' if good else '실패'}")
    return ok


def self_check_features():
    """
    R 블록의 나눗셈 셋과 결측 규칙을 인공 계정 넷으로 확인한다.

    ── 계정 가 ── 토큰 100 · 구두점제외 90 · 문장 10 · 길이 [9]×10
        ① 90 ÷ 10 = 9.0
        ② (100 − 90) ÷ 100 = 0.10
        ③ 길이가 전부 9라 표준편차 0 → CV = 0 ÷ 9 = 0.0
           (결측이 아니다. 잴 수 있었고, 잰 값이 0이다.)

    ── 계정 나 ── 토큰 12 · 구두점제외 10 · 문장 4 · 길이 [1,2,3,4]
        ① 10 ÷ 4 = 2.5
        ② (12 − 10) ÷ 12 = 0.166666…
        ③ 문장이 4개 → 5개 미만이라 결측. ①②는 멀쩡히 살아 있다.
           이 한 줄이 "결측은 칸 하나이지 계정 전체가 아니다"를 건다.

    ── 계정 다 ── 토큰 0 · 구두점제외 0 · 문장 0 · 길이 []
        ①②③ 모두 분모가 0이라 결측. 0.0으로 채우지 않는다.

    ── 계정 라 ── 토큰 25 · 구두점제외 20 · 문장 5 · 길이 [2,4,4,4,6]
        ① 20 ÷ 5 = 4.0
        ② (25 − 20) ÷ 25 = 0.20
        ③ 평균 = 20 ÷ 5 = 4. 편차 −2, 0, 0, 0, +2 → 제곱합 8.
           표본분산 = 8 ÷ (5 − 1) = 2 → 표준편차 √2 ≈ 1.414214
           CV = 1.414214 ÷ 4 = 0.353553
           문장이 딱 5개다 — 결측 문턱의 경계가 '미만'임을 여기서 건다.

    ── 결측 셈 ── 네 계정에서 유효/결측이 자질마다 달라야 한다.
        ① 3 / 1     ② 3 / 1     ③ 2 / 2
    """
    print("\n  ── (2) 자질 규칙 — 손으로 푼 인공 계정 넷 ──")
    ok = True
    feats = compute_features(SELF_CHECK_ACCOUNTS)
    print("      계정  자질                   기대        실제  판정")
    for uid, key, expect, why in SELF_CHECK_FEATURE:
        got = feats[uid][key]
        if expect is None or got is None:
            good = (expect is None and got is None)
        else:
            good = abs(got - expect) <= 1e-12
        ok = ok and good
        print(f"      {uid}    {key:<18}{_fmt_val(expect):>10}"
              f"{_fmt_val(got):>12}  {'통과' if good else '실패'}")
        print(f"            └ {why}")

    print("\n      결측이 그 자질에서만 빠지는가 (계정이 통째로 빠지면 안 된다)")
    uids = list(SELF_CHECK_ACCOUNTS)
    for key, (exp_def, exp_miss) in SELF_CHECK_DEFINED.items():
        vals = defined_values(uids, feats, key)
        n_miss = len(uids) - len(vals)
        good = (len(vals) == exp_def and n_miss == exp_miss)
        ok = ok and good
        print(f"        {key:<18} 유효 {len(vals)}/{exp_def} · "
              f"결측 {n_miss}/{exp_miss}  {'통과' if good else '실패'}")
    return ok


def self_check_iqr():
    """
    사분위 폭 비를 손으로 푼 예제로 확인한다. P16-4가 이 나눗셈에 걸린다.

        봇   = [1, 2, 3, 4]
        사람 = [0, 2, 4, 6]
    사분위는 05·06·옛 산포검정(보관)과 같은 method="inclusive"다. n = 4일 때 자리는
    (n−1)·p = 3p 로 잡히므로
        봇 Q1 = 0.75번째 → 1 + 0.75×(2−1) = 1.75
        봇 Q3 = 2.25번째 → 3 + 0.25×(4−3) = 3.25   → IQR = 1.50
        사람 Q1 = 1.5,  Q3 = 4.5                    → IQR = 3.00
        폭 비(봇 ÷ 사람) = 1.5 ÷ 3.0 = 0.5

    중앙값은 둘 다 2.5·3.0 언저리로 비슷한데 폭은 두 배 차이가 난다.
    위치(δ)와 산포(IQR 비)가 서로 다른 것을 잰다는 사실을 이 예제가 보여 준다.
    """
    print("\n  ── (3) 사분위 폭 비 — P16-4가 쓰는 나눗셈 ──")
    exp_b, exp_h, exp_r = SELF_CHECK_IQR_EXPECT
    qb = quartiles([float(v) for v in SELF_CHECK_IQR_BOT])
    qh = quartiles([float(v) for v in SELF_CHECK_IQR_HUMAN])
    ib = qb["Q3"] - qb["Q1"]
    ih = qh["Q3"] - qh["Q1"]
    ratio = ib / ih
    ok = (abs(ib - exp_b) <= SELF_CHECK_TOL
          and abs(ih - exp_h) <= SELF_CHECK_TOL
          and abs(ratio - exp_r) <= SELF_CHECK_TOL)
    print(f"    봇   {SELF_CHECK_IQR_BOT}  Q1={qb['Q1']:.3f} Q3={qb['Q3']:.3f}"
          f"  IQR={ib:.3f} (기대 {exp_b})")
    print(f"    사람 {SELF_CHECK_IQR_HUMAN}  Q1={qh['Q1']:.3f} "
          f"Q3={qh['Q3']:.3f}  IQR={ih:.3f} (기대 {exp_h})")
    print(f"    폭 비 = {ratio:.3f} (기대 {exp_r})  {'통과' if ok else '실패'}")
    return ok


def _fmt_val(v):
    """자가검증 표에서 결측을 눈에 띄게 찍는다. 07의 _fmt()와 같은 뜻이다."""
    return "결측" if v is None else f"{v:.6f}"


def self_check(hash_ok, h_src, h_copy):
    """
    세 관문을 차례로 건다. 하나라도 실패하면 본 계산에 들어가지 않는다.

    반환: (통과 여부, 관문별 결과 사전). 사전은 JSON의 설정.자가검증에
    그대로 들어간다 — "통과했다"를 손으로 적어 넣지 않고 실제 결과를 싣는다.
    """
    line("[자가검증] 세 관문 — 통계 기계 · 자질 규칙 · 사분위 폭 비")
    print(f"  06에서 복사한 함수: {', '.join(COPIED_NAMES)}")
    print(f"  06 원본 해시 {h_src}  ·  이 파일 사본 해시 {h_copy}")
    print(f"  선언된 해시 {COPIED_HASH}   {'일치' if hash_ok else '불일치'}")
    if not hash_ok:
        print("  ■ 06의 통계 함수와 이 파일의 사본이 다릅니다. 같은 자로 재고")
        print("    있다는 전제가 깨졌으므로 본 계산에 들어가지 않습니다.")

    ok1 = self_check_stats()
    ok2 = self_check_features()
    ok3 = self_check_iqr()
    ok = hash_ok and ok1 and ok2 and ok3

    print()
    if ok:
        print("  세 관문 모두 통과. 본 계산으로 들어간다.")
    else:
        print("  ■ 중단 — 자가검증 실패. 위에서 '실패'가 찍힌 줄을 먼저 보십시오.")
        print("    본 계산에 들어가지 않고 끝냅니다. 관문을 우회하지 마십시오.")
    detail = {
        "함수해시": hash_ok, "통계기계": ok1, "자질규칙": ok2, "사분위폭비": ok3,
        "통과": ok,
        "예제": ("06의 세 고정 예제(완전 분리·동점 포함·BH) + 08의 인공 계정 "
               "넷(자질 12칸·결측 셈 3줄) + 사분위 폭 비 1줄"),
    }
    return ok, detail


# ════════════════════════════════════════════════════════════════════════
# [3] 정합 관문 — 04-1과 04가 같은 자료를 말하는가
# ════════════════════════════════════════════════════════════════════════
def consistency_gate(re_acc, ms_acc, ms_conf):
    """
    이 파일이 쓰는 세 수치를 04-1과 04에서 각각 꺼내 계정별로 맞춰 본다.

    무엇을 보는가.
      (a) 계정 집합이 같은가 (양쪽 1,869개, 아이디까지)
      (b) 계정별 문장수 · 토큰수 · 토큰수_구두점제외 가 전부 같은가
      (c) 세 수치의 전체 합계가 04 설정의 처리규모와 같은가
      (d) 04-1에만 있는 문장 길이 목록이 그 계정의 다른 수치와 앞뒤가 맞는가
          — len(문장길이) == 문장수 · sum(문장길이) == 토큰수_구두점제외

    (d)가 이 관문의 값어치다. (a)(b)(c)는 04-1이 이미 통과했다고 적어 둔
    것이고, (d)는 08이 처음 쓰는 자료(문장 길이 목록)가 그 통과한 수치와
    같은 파싱에서 나왔는지를 묻는다. 목록이 어긋나 있으면 ③ 변동계수는
    ①과 다른 자료를 재는 셈이 된다.

    불일치가 있어도 계산은 계속하되(보관된 13-19 사전선언의 13항(현 04-1)이 정한 처리 원칙), 설정에 실패를
    기록하고 화면에 첫 세 건을 띄운다.
    """
    res = {"계정집합": {}, "계정별": {}, "합계": {}, "문장길이_정합": {}}

    a_ids, b_ids = set(re_acc), set(ms_acc)
    res["계정집합"] = {"13": len(a_ids), "04": len(b_ids),
                   "일치": a_ids == b_ids,
                   "13에만": sorted(a_ids - b_ids)[:3],
                   "04에만": sorted(b_ids - a_ids)[:3]}

    keys = ["문장수", "토큰수", "토큰수_구두점제외"]
    mismatch, examples = 0, []
    for uid in sorted(a_ids & b_ids):
        x, y = re_acc[uid], ms_acc[uid]
        diff = {k: (x[k], y[k]) for k in keys if x[k] != y[k]}
        if diff:
            mismatch += 1
            if len(examples) < 3:
                examples.append({"계정": uid, "차이": {k: {"13": v[0], "04": v[1]}
                                                  for k, v in diff.items()}})
    res["계정별"] = {"대조계정수": len(a_ids & b_ids),
                  "일치계정수": len(a_ids & b_ids) - mismatch,
                  "불일치계정수": mismatch, "불일치예시": examples,
                  "대조항목": keys}

    scale = ms_conf.get("처리규모", {})
    for k in keys:
        s13 = sum(re_acc[u][k] for u in re_acc)
        s04 = scale.get(k)
        res["합계"][k] = {"13": s13, "04설정": s04, "일치": s13 == s04}

    bad_len, bad_sum, len_ex = 0, 0, []
    for uid in sorted(re_acc):
        a = re_acc[uid]
        L = a["문장길이"]
        e1 = len(L) != a["문장수"]
        e2 = sum(L) != a["토큰수_구두점제외"]
        bad_len += e1
        bad_sum += e2
        if (e1 or e2) and len(len_ex) < 3:
            len_ex.append({"계정": uid, "len(문장길이)": len(L),
                           "문장수": a["문장수"], "sum(문장길이)": sum(L),
                           "토큰수_구두점제외": a["토큰수_구두점제외"]})
    res["문장길이_정합"] = {"길이불일치계정수": bad_len, "합불일치계정수": bad_sum,
                      "불일치예시": len_ex,
                      "규칙": "len(문장길이) == 문장수 · sum(문장길이) == 토큰수_구두점제외"}

    res["통과"] = (res["계정집합"]["일치"]
                 and mismatch == 0
                 and all(v["일치"] for v in res["합계"].values())
                 and bad_len == 0 and bad_sum == 0)
    return res


def print_gate(res):
    """정합 관문의 결과를 화면에 푼다."""
    cs = res["계정집합"]
    print(f"      (a) 계정 집합    04-1 {cs['13']:,}개 · 04 {cs['04']:,}개  "
          f"→ {'같은 집합' if cs['일치'] else '■ 다르다'}")
    if not cs["일치"]:
        print(f"          04-1에만 {cs['13에만']} · 04에만 {cs['04에만']}")

    ca = res["계정별"]
    print(f"      (b) 계정별 세 수치  일치 {ca['일치계정수']:,} · "
          f"불일치 {ca['불일치계정수']:,}  (대조 {ca['대조계정수']:,}계정)")
    print(f"          대조 항목: {' · '.join(ca['대조항목'])}")
    for ex in ca["불일치예시"]:
        print(f"          ■ {ex['계정']}  {ex['차이']}")

    print("      (c) 전체 합계")
    for k, v in res["합계"].items():
        mark = "일치" if v["일치"] else "■ 불일치"
        s04 = "없음" if v["04설정"] is None else f"{v['04설정']:,}"
        print(f"          {k:<16} 04-1 {v['13']:>11,}   04 {s04:>11}   {mark}")

    sl = res["문장길이_정합"]
    print(f"      (d) 문장 길이 목록  길이 불일치 {sl['길이불일치계정수']:,}계정 · "
          f"합 불일치 {sl['합불일치계정수']:,}계정")
    print(f"          {sl['규칙']}")
    for ex in sl["불일치예시"]:
        print(f"          ■ {ex}")

    print()
    if res["통과"]:
        print("      네 검사 모두 통과. 04-1의 문장 길이 목록은 04가 센 토큰을")
        print("      문장 단위로 쪼갠 것과 정확히 같다 — ③ 변동계수가 ①②와")
        print("      같은 자료를 재고 있다는 뜻이다.")
    else:
        print("      ■ 정합 관문 불통과. 계산은 계속하되 설정에 기록한다.")
        print("        보관된 13-19 사전선언의 13항(현 04-1) 원칙에 따라, 어긋나는 수치는")
        print("        04를 정본으로 삼아야 한다. 위 (b)(c)의 불일치를 먼저 해명하십시오.")


# ════════════════════════════════════════════════════════════════════════
# [4·5] 비교 — 자질 3종을 검정하고 BH를 건다(가족 크기 3)
# ════════════════════════════════════════════════════════════════════════
def defined_values(uids, feats, key):
    """
    결측(None)을 뺀 값만 순서대로 늘어놓는다. 07의 같은 함수를 그대로 따른다.

    결측은 그 자질의 검정에서만 빠진다. 계정이 통째로 빠지는 것이 아니라
    칸 하나가 빠지는 것이라, 같은 계정이 ①에는 들어가고 ③에는 빠질 수 있다.
    그래서 유효 계정 수가 자질마다 다르고, 아래 표에 그 수를 한 칸 내주었다.
    """
    out = []
    for u in uids:
        v = feats[u][key]
        if v is not None:
            out.append(v)
    return out


def compare_features(bot_ids, human_ids, feats):
    """
    자질 3종을 검정하고, 세 개의 p에 BH 보정을 건다.

    ■ 가족이 셋뿐이라는 것의 뜻 ■
    06은 172종, 07은 58·17종이 한 가족이었다. 여기는 셋이다. BH는 m이 작을
    수록 덜 가혹해서, m=3이면 가장 작은 p가 살아남을 문턱이 0.05 × 1/3 =
    0.0167 이다(가장 큰 p는 0.05 그대로). 가족을 작게 잡아 유리해진 것이
    아니라, 사전선언이 R 블록의 자질을 셋으로 미리 못 박았기 때문에 셋이다.
    자질을 더 만들어 넣었다면 문턱이 조여졌을 것이고, 지금 와서 빼면 느슨해
    진다 — 어느 쪽도 하지 않는다.

    반환: |δ| 내림차순으로 정렬된 (자질키, 결과) 목록
    """
    n_all = len(bot_ids) + len(human_ids)
    rows = []
    for key, name, unit, defn in FEATURES:
        v1 = defined_values(bot_ids, feats, key)
        v2 = defined_values(human_ids, feats, key)
        r = {"이름": name, "단위": unit, "정의": defn,
             "봇_유효n": len(v1), "사람_유효n": len(v2),
             "결측계정수": n_all - len(v1) - len(v2)}
        if not v1 or not v2:
            # 한쪽 무더기가 통째로 비었다. 견줄 것이 없다.
            r.update({"검정가능": False, "U": None, "z": None, "p": None,
                      "q": None, "델타": None, "방향": "검정 불가",
                      "봇_중앙": None, "사람_중앙": None,
                      "유의": False, "주목": False,
                      "봇_요약": None, "사람_요약": None,
                      "봇_IQR": None, "사람_IQR": None, "IQR비": None})
        else:
            res = mann_whitney(v1, v2)
            qb, qh = quartiles(v1), quartiles(v2)
            ib, ih = qb["Q3"] - qb["Q1"], qh["Q3"] - qh["Q1"]
            r.update({"검정가능": True, "U": res["U"], "z": res["z"],
                      "p": res["p"], "델타": res["델타"],
                      "방향": direction_of(res["델타"]),
                      "봇_중앙": statistics.median(v1),
                      "사람_중앙": statistics.median(v2),
                      "봇_요약": qb, "사람_요약": qh,
                      "봇_IQR": ib, "사람_IQR": ih,
                      # 사람 IQR이 0이면 나눗셈이 성립하지 않아 None이다.
                      # '무한대'가 아니라 '잴 수 없음'으로 둔다(옛 산포검정(보관)과 같은 처리).
                      "IQR비": (ib / ih) if ih > 0 else None})
        rows.append((key, r))

    testable = [(k, r) for k, r in rows if r["검정가능"]]
    qs = bh_qvalues([r["p"] for _, r in testable])
    for (k, r), q in zip(testable, qs):
        r["q"] = q
        r["유의"] = q <= Q_ALPHA
        r["주목"] = r["유의"] and abs(r["델타"]) >= DELTA_NOTABLE

    # 검정 불가는 |δ|를 −1로 쳐서 맨 뒤로 보낸다(δ의 하한이 −1이라 겹치지 않는다).
    rows.sort(key=lambda kv: -(abs(kv[1]["델타"]) if kv[1]["검정가능"] else -1.0))
    return rows, len(testable)


def print_feature_table(rows):
    """자질 표를 |δ| 내림차순으로 띄운다. 셋뿐이라 전부 띄운다."""
    print(TABLE_HEAD)
    for k, r in rows:
        if not r["검정가능"]:
            print(f"      {r['이름']:<15}{'':>7}  검정 불가  "
                  f"(유효 봇 {r['봇_유효n']:,} · 사람 {r['사람_유효n']:,})")
            continue
        n_eff = r["봇_유효n"] + r["사람_유효n"]
        # 단위가 자질마다 달라 %로 찍을 수 없다. 소수 네 자리로 통일한다.
        print(f"      {r['이름']:<15}{r['델타']:>+7.3f}  {r['방향']}  "
              f"{r['q']:>8.4f}  {r['봇_중앙']:>9.4f}  {r['사람_중앙']:>9.4f}"
              f"  {n_eff:>5,}")
    print("      (중앙값의 단위 — 문장당 토큰수는 토큰/문장, 구두점 비율은")
    print("       비율(0.10 = 10%), 변동계수는 무단위다. 세 줄의 세로 비교는")
    print("       뜻이 없다. 가로로, 봇 대 사람으로만 읽어라.)")
    if any(r["검정가능"] and r["q"] == 0.0 for _, r in rows):
        print("      (q가 0.0000으로 찍힌 줄은 정규근사와 배정도 실수의 바닥이다.")
        print("       '틀릴 확률이 0'이 아니라 더 작은 값을 구분할 수 없다는 뜻이다.")
        print("       어차피 그 언저리면 어떤 문턱으로도 유의다 — 판단은 δ로 한다.)")


def print_dispersion_table(rows):
    """사분위 폭 비를 띄운다. P16-4가 이 표에 걸린다."""
    print("\n      산포 — 사분위 폭(Q3 − Q1)과 그 비")
    print("      자질" + " " * 15 + "봇 IQR" + " " * 4 + "사람 IQR"
          + " " * 4 + "폭 비(봇÷사람)")
    for k, r in rows:
        if r["IQR비"] is None:
            print(f"      {r['이름']:<15}{'—':>10}{'—':>12}{'  잴 수 없음':>16}")
            continue
        print(f"      {r['이름']:<15}{r['봇_IQR']:>10.4f}{r['사람_IQR']:>12.4f}"
              f"{r['IQR비']:>14.3f}")
    print("      폭 비가 1보다 작으면 봇 계정들끼리의 폭이 사람보다 좁다는 뜻이다.")
    print("      위치를 재는 δ와 다른 것을 잰다 — 중앙값이 같아도 폭은 다를 수 있다.")


# ════════════════════════════════════════════════════════════════════════
# [6] 사전 예측 대조
# ════════════════════════════════════════════════════════════════════════
def lookup(rows, key):
    """자질 목록에서 하나를 찾는다. 없으면 None."""
    for k, r in rows:
        if k == key:
            return r
    return None


def check_prediction(pred, rows):
    """
    예측 하나를 실제 결과와 대조한다. 07의 같은 함수와 같은 규칙이다.

    부호(또는 P16-4의 '1 미만')만 본다. 사전선언에 적힌 것이 "δ < 0"이지
    "q ≤ 0.05 이면서 δ < 0"이 아니기 때문이다. 결과를 보고 판정 기준을 조이는
    것이야말로 사전등록이 막으려는 일이다. 다만 표에는 q를 나란히 찍어,
    방향이 맞았더라도 통계적으로 뒷받침되는지를 읽는 사람이 함께 보게 한다.

    자질이 없거나 검정 불가면 '판정불가'다. 적중으로도 빗나감으로도 치지 않는다.
    """
    items, verdicts = [], []
    for key, want in pred["검사"]:
        r = lookup(rows, key)
        if r is None or not r["검정가능"]:
            v = "판정불가"
            items.append({"자질": key, "기대": ("δ " + want + " 0") if want in "<>"
                          else "IQR비 < 1", "값": None, "q": None, "판정": v,
                          "사유": "자료에 없음" if r is None else "한쪽 무더기가 빔"})
            verdicts.append(v)
            continue

        if want == "<1":
            val = r["IQR비"]
            if val is None:
                v = "판정불가"
                items.append({"자질": key, "기대": "IQR비 < 1", "값": None,
                              "q": None, "판정": v, "사유": "사람 IQR이 0이라 나눗셈 불성립"})
                verdicts.append(v)
                continue
            hit = val < 1.0
            v = "적중" if hit else "빗나감"
            items.append({"자질": key, "기대": "IQR비 < 1",
                          "값": round(val, STAT_DIGITS), "q": sig(r["q"]),
                          "판정": v, "주목": r["주목"]})
        else:
            d = r["델타"]
            hit = (d < 0) if want == "<" else (d > 0)
            v = "적중" if hit else "빗나감"
            items.append({"자질": key, "기대": f"δ {want} 0",
                          "값": round(d, STAT_DIGITS), "q": sig(r["q"]),
                          "판정": v, "주목": r["주목"]})
        verdicts.append(v)

    if all(x == "적중" for x in verdicts):
        overall = "적중"
    elif any(x == "판정불가" for x in verdicts):
        overall = "일부 판정불가"
    else:
        overall = "빗나감"
    return {"번호": pred["번호"], "서술": pred["서술"], "종류": pred["종류"],
            "근거": " ".join(pred["근거"]), "항목": items, "판정": overall}


def print_prediction_block(results, rows):
    """예측 대조 결과를 표로 찍는다. 빗나간 것도 그대로 남긴다."""
    line("사전 예측 대조 — 보관된 13-19_사전선언 「16 R 블록」(현 08)")
    print("  아래 부호는 결과를 보기 전에 문서에 확정된 것이다. 빗나간 예측도")
    print("  지우거나 고치지 않고 그대로 싣는다 — 그것이 사전등록의 요점이다.")
    print("  판정은 부호만 본다(q 조건을 걸지 않는다). q는 옆에 함께 찍어,")
    print("  방향이 맞은 것이 통계적으로도 뒷받침되는지를 사람이 읽게 한다.")

    for res in results:
        print()
        print(f"      {res['번호']}  {res['서술']}")
        print("              자질                 기대        실제         q  판정")
        for it in res["항목"]:
            name = it["자질"]
            if it["값"] is None:
                print(f"              {name:<18}{it['기대']:>9}{'—':>12}"
                      f"{'—':>10}  판정불가  ({it.get('사유', '')})")
            else:
                qtxt = "—" if it["q"] is None else f"{it['q']:.4f}"
                # δ는 부호가 판정의 전부라 +/−를 붙이고, IQR 비는 양수뿐이라
                # 붙이지 않는다. '+0.433'으로 찍힌 폭 비를 δ로 잘못 읽는 일을
                # 막으려는 것이다.
                vtxt = (f"{it['값']:.3f}" if it["기대"].startswith("IQR")
                        else f"{it['값']:+.3f}")
                print(f"              {name:<18}{it['기대']:>9}"
                      f"{vtxt:>12}{qtxt:>10}  {it['판정']}")
        print(f"        → {res['번호']} : {res['판정']}")
        src = next(p for p in PREDICTIONS if p["번호"] == res["번호"])
        print("          근거로 적어 둔 것:")
        for ln in src["근거"]:
            print(f"            {ln}")

        # P16-1·P16-2에는 앞 단계의 실측치를 나란히 붙여 크기를 가늠하게 한다.
        if res["번호"] == "P16-1":
            r = lookup(rows, "문장당_토큰수")
            if r and r["검정가능"]:
                print(f"\n          03 감사 표본  봇 {REF_AUDIT_BOT} vs "
                      f"사람 {REF_AUDIT_HUMAN} 토큰/문장")
                print(f"          08 전수 중앙값  봇 {r['봇_중앙']:.2f} vs "
                      f"사람 {r['사람_중앙']:.2f} 토큰/문장")
                print("          감사 표본은 계정 몇 개를 눈으로 본 것이었다. 전수에서")
                print("          같은 방향이면 그 인상이 자료로 확인된 것이고, 반대면")
                print("          감사 표본이 우연히 치우쳤던 것이다.")
        if res["번호"] == "P16-2":
            r = lookup(rows, "구두점_비율")
            if r and r["검정가능"]:
                same = (abs(round(r["델타"], 4) - REF_PUNCT_DELTA) <= 1e-9
                        and abs(r["U"] - REF_PUNCT_U) <= 1e-6
                        and abs(round(r["z"], 4) - REF_PUNCT_Z) <= 1e-9)
                print(f"\n          07 UPOS PUNCT   U = {REF_PUNCT_U:>10,.1f}  "
                      f"z = {REF_PUNCT_Z:>7.4f}  δ = {REF_PUNCT_DELTA:+.4f}")
                print(f"          08 구두점 비율   U = {r['U']:>10,.1f}  "
                      f"z = {r['z']:>7.4f}  δ = {r['델타']:+.4f}")
                print(f"          → {'세 값이 모두 같다' if same else '■ 값이 다르다'}")
                if same:
                    print("          우연이 아니다. 07은 구두점을 '구두점 제외 토큰수'로,")
                    print("          08은 '전체 토큰수'로 나눈다. 계정마다 두 값은")
                    print("          x ↦ x/(1+x) 로 이어져 있고 이 함수는 순증가라")
                    print("          순위를 하나도 바꾸지 않는다. 순위 검정이므로 U·z·δ가")
                    print("          똑같이 나오는 것이 정상이고, 지금 그렇다 — 두 파일의")
                    print("          분모 처리가 서로 맞다는 뜻이다. 중앙값만 다르다")
                    print(f"          (07 봇 0.1113 · 08 봇 {r['봇_중앙']:.4f}). 분모가")
                    print("          다르니 크기는 달라야 하고, 순서는 같아야 한다.")
                else:
                    print("          ■ 순증가 변환이므로 같아야 하는 값들이 다르다.")
                    print("            둘 중 하나의 분모 처리를 의심해야 한다.")
                print("          q는 다르다 — 07은 17종 가족의 BH, 08은 3종 가족의 BH다.")

    hits = sum(1 for r in results if r["판정"] == "적중")
    miss = sum(1 for r in results if r["판정"] == "빗나감")
    undecided = len(results) - hits - miss
    print()
    print(f"      네 예측 중 적중 {hits} · 빗나감 {miss} · 판정불가 {undecided}")
    return {"적중": hits, "빗나감": miss, "판정불가": undecided}


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    print("=" * 74)
    print("08 R 블록 — 문장 길이 · 구두점 · 리듬의 고르기  (라벨을 읽는다)")
    print("=" * 74)
    print("지문의 셋째 블록을 처음 검정한다. 낱말(06)도 형태(07)도 보지 않고,")
    print("글을 어떻게 끊고 어떻게 찍는지만 본다. 새 파싱은 없다 — 04와 04-1이")
    print("이미 센 수를 나누기만 한다.")

    # ── [1] 입력과 라벨 ─────────────────────────────────────────
    print("\n[1/7] 입력 적재와 라벨 개봉")
    for path, who in ((REPARSE_JSON, "04-1_확장재파싱.py"),
                      (MEASURE_JSON, "04_기능어측정.py"),
                      (ACCOUNTS_JSON, "01_botsim_적격검열.py"),
                      (RATES_JSON, "05_사용률검수.py"),
                      (COMPARE_PY, "06_봇사람비교.py")):
        if not os.path.exists(path):
            print(f"      {path} 이(가) 없습니다.")
            print(f"      {who} 를 먼저 실행하십시오. 아무것도 하지 않고 끝냅니다.")
            return

    re_conf, re_acc = load_reparse()
    ms_conf, ms_acc = load_measure()
    print(f"      04-1 계정 {len(re_acc):,}개 (실행일 {re_conf.get('실행일', '?')})")
    print(f"      04 계정 {len(ms_acc):,}개 (실행일 {ms_conf.get('실행일', '?')})")

    h05 = load_funcword_hash()
    h13 = (re_conf.get("승계해시", {}) or {}).get("기능어172")
    chain_ok = (h05 == h13 == FUNCWORD_HASH)
    print(f"      기능어 172종 해시 — 05 {h05} · 04-1 {h13} · "
          f"선언 {FUNCWORD_HASH}")
    print(f"      사슬 {'이어짐' if chain_ok else '■ 끊김'}. 08은 기능어를 한 낱말도")
    print("      쓰지 않지만, 같은 자료 위에 서 있다는 것을 이 해시로 남긴다.")

    labels = load_labels()
    bot_ids, human_ids, missing, invalid = split_by_label(re_acc, labels)

    line("라벨 개봉")
    print("  ■ 여기서 라벨을 읽는다. ■  01_적격계정.json 의 '라벨' 키다.")
    print("  04-1은 이 키를 읽지 않았고(04와 같은 규율), 09-3·02-1·08과")
    print("  옛 17~19(보관)는 읽는다.")
    print("  다만 위 [1]까지 온 수치 — 문장수·토큰수·문장 길이 목록 — 는")
    print("  전부 라벨을 모르는 채로 만들어진 값이다. 아래 [4]의 자질 계산도")
    print("  계정별로 먼저 끝내고, 그다음에 이름표를 붙여 두 무더기로 가른다.")
    print()
    print(f"  봇   {len(bot_ids):>6,}계정")
    print(f"  사람 {len(human_ids):>6,}계정")
    if missing or invalid:
        print()
        print(f"  ※ 라벨 없음 {len(missing):,}계정 · "
              f"bot/human 이 아닌 값 {len(invalid):,}계정")
        print("    어느 무더기에도 넣을 수 없어 비교에서 빠집니다. '분석적 제외'가")
        print("    아니라 대응할 짝이 없는 것입니다. 01을 확인하십시오.")
    if not bot_ids or not human_ids:
        print("\n■ 중단 — 한쪽 무더기가 비어 있어 비교가 성립하지 않습니다.")
        return

    # ── [2] 자가검증 ────────────────────────────────────────────
    print("\n[2/7] 자가검증 — 관문을 통과하지 못하면 본 계산에 들어가지 않는다")
    hash_ok, h_src, h_copy = verify_copied_functions()
    ok_check, check_detail = self_check(hash_ok, h_src, h_copy)
    if not ok_check:
        return

    # ── [3] 정합 관문 ───────────────────────────────────────────
    print("\n[3/7] 정합 관문 — 04-1과 04가 같은 자료를 말하는가")
    gate = consistency_gate(re_acc, ms_acc, ms_conf)
    print_gate(gate)

    # ── [4] 자질 계산 ───────────────────────────────────────────
    print("\n[4/7] 자질 3종 계산 (계정별 · 라벨 없이)")
    feats = compute_features(re_acc)
    for key, name, unit, defn in FEATURES:
        n_miss = sum(1 for u in feats if feats[u][key] is None)
        print(f"      {name:<15} = {defn}")
        print(f"      {'':<15}   단위 {unit} · 결측 {n_miss:,}계정 "
              f"/ {len(feats):,}")
    short = sum(1 for u in re_acc if len(re_acc[u]["문장길이"]) < MIN_SENTENCES_CV)
    print(f"\n      문장 {MIN_SENTENCES_CV}개 미만 계정 {short:,}개 — "
          "③의 결측은 여기서만 나온다.")
    print("      결측은 그 자질의 검정에서만 빠지고 다른 자질에는 그대로 들어간다")
    print("      (07의 규칙). 계정이 통째로 빠지는 것이 아니다.")

    # ── [5] 비교 ────────────────────────────────────────────────
    print(f"\n[5/7] 비교 (그룹1 = {GROUP1}, 그룹2 = {GROUP2} · BH 가족 크기 3)")
    rows, n_family = compare_features(bot_ids, human_ids, feats)
    print_feature_table(rows)

    sig_n = sum(1 for _, r in rows if r["유의"])
    notable = [(k, r) for k, r in rows if r["주목"]]
    up = sum(1 for _, r in notable if r["델타"] > 0)
    down = sum(1 for _, r in notable if r["델타"] < 0)
    print(f"\n      BH 가족 크기                         {n_family:>4}종 / 3종")
    print(f"      유의 (q ≤ {Q_ALPHA})                        {sig_n:>4}종")
    print(f"      주목 (q ≤ {Q_ALPHA} 그리고 |δ| ≥ {DELTA_NOTABLE})     "
          f"{len(notable):>4}종")
    print(f"        봇이 높음                            {up:>4}종")
    print(f"        봇이 낮음                            {down:>4}종")

    # ── [6] 산포 ────────────────────────────────────────────────
    print("\n[6/7] 산포 — 사분위 폭 비 (P16-4)")
    print_dispersion_table(rows)

    # 정의 모호성 참고값 — 판정 밖이다.
    cv_pop = compute_cv_pop(re_acc)
    v1 = [cv_pop[u] for u in bot_ids if cv_pop[u] is not None]
    v2 = [cv_pop[u] for u in human_ids if cv_pop[u] is not None]
    ref = mann_whitney(v1, v2) if (v1 and v2) else None
    cv_row = lookup(rows, "문장길이_변동계수")
    if ref and cv_row and cv_row["검정가능"]:
        print("\n      ── 판단이 필요했던 지점 (판정에 쓰지 않는 참고값) ──")
        print("      사전선언은 ③을 '표준편차 ÷ 평균'이라고만 적었다. 표본")
        print("      표준편차(n−1)를 썼고, 그것이 위 표의 값이다. 모표준편차(n)로")
        print(f"      바꾸면 δ = {ref['델타']:+.4f} 로, 위의 "
              f"{cv_row['델타']:+.4f} 와 견주면 차이가")
        print(f"      {abs(ref['델타'] - cv_row['델타']):.4f} 이다. 두 정의의 비는")
        print("      √(n/(n−1))이라 계정마다 조금씩 달라 순위가 흔들릴 수 있어")
        print("      함께 적어 둔다. 판정은 위의 표본표준편차 값으로만 한다.")

    # ── [7] 예측 대조와 저장 ────────────────────────────────────
    print("\n[7/7] 사전 예측 대조와 저장")
    results = [check_prediction(p, rows) for p in PREDICTIONS]
    tally = print_prediction_block(results, rows)

    method = (
        "R 블록 자질 3종을 계정 단위로 계산해 Mann-Whitney U 검정(양측)으로 "
        "비교했다. 동점은 평균 순위, 정규근사 분산에 동점 보정 항 "
        "Σ(t³−t)/(N(N−1)), z에 연속성 보정 0.5 — 06의 구현을 ast로 복사해 썼다. "
        "효과크기는 Cliff's δ = 2U/(n1·n2) − 1 (그룹1 = bot 기준). "
        f"다중비교는 Benjamini-Hochberg FDR, q = {Q_ALPHA} (자질 3종이 한 가족). "
        f"주목 = q ≤ {Q_ALPHA} 그리고 |δ| ≥ {DELTA_NOTABLE}. "
        f"결측은 분모 0 또는 문장 {MIN_SENTENCES_CV}개 미만이며 그 자질의 "
        "검정에서만 뺐다(07의 규칙 — 분석적 제외가 아니다). "
        "산포는 사분위 폭(Q3 − Q1, method=inclusive)의 봇 ÷ 사람 비. "
        "보관된 13-19_사전선언 「16 R 블록」(현 08)."
    )
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.machine()}",
            "방법": method,
            "입력파일": {"13": os.path.basename(REPARSE_JSON),
                     "04_교차확인": os.path.basename(MEASURE_JSON),
                     "01_라벨": os.path.basename(ACCOUNTS_JSON),
                     "05_해시": os.path.basename(RATES_JSON),
                     "06_통계함수": os.path.basename(COMPARE_PY)},
            "승계해시": {"기능어172": FUNCWORD_HASH,
                     "05가_적어_둔_값": h05, "13이_적어_둔_값": h13,
                     "사슬일치": chain_ok,
                     "06_통계함수": COPIED_HASH,
                     "06_원본_해시": h_src, "사본_해시": h_copy,
                     "복사한_함수": COPIED_NAMES},
            "라벨_사용": ("있음. 01의 '라벨' 키를 [1/7]에서 열었다. "
                      "자질 계산은 그 전에 계정별로 끝냈다."),
            "그룹1": GROUP1, "그룹2": GROUP2,
            "n_bot": len(bot_ids), "n_human": len(human_ids),
            "라벨결측": len(missing) + len(invalid),
            "자가검증": dict(check_detail,
                          비고="세 관문을 모두 통과해야 이 파일이 여기까지 온다."),
            "정합관문": gate,
            "총소요초": None,        # 아래에서 채운다
        },
        "자질별": {
            k: {
                "이름": r["이름"], "단위": r["단위"], "정의": r["정의"],
                "검정가능": r["검정가능"],
                "U": rnd(r["U"], STAT_DIGITS),
                "z": rnd(r["z"], STAT_DIGITS),
                "p": None if r["p"] is None else sig(r["p"]),
                "q": None if r["q"] is None else sig(r["q"]),
                "델타": rnd(r["델타"], STAT_DIGITS),
                "방향": r["방향"],
                "봇_중앙": rnd(r["봇_중앙"], RATE_DIGITS),
                "사람_중앙": rnd(r["사람_중앙"], RATE_DIGITS),
                "봇_요약": None if r["봇_요약"] is None else
                        {kk: round(vv, RATE_DIGITS) for kk, vv in r["봇_요약"].items()},
                "사람_요약": None if r["사람_요약"] is None else
                         {kk: round(vv, RATE_DIGITS) for kk, vv in r["사람_요약"].items()},
                "봇_IQR": rnd(r["봇_IQR"], RATE_DIGITS),
                "사람_IQR": rnd(r["사람_IQR"], RATE_DIGITS),
                "IQR비": rnd(r["IQR비"], RATE_DIGITS),
                "봇_유효n": r["봇_유효n"], "사람_유효n": r["사람_유효n"],
                "결측계정수": r["결측계정수"],
                "유의": r["유의"], "주목": r["주목"],
            }
            for k, r in rows
        },
        "관찰": {
            f"문장_{MIN_SENTENCES_CV}개미만_계정수": short,
            "자질별_결측계정수": {k: sum(1 for u in feats if feats[u][k] is None)
                          for k in FEATURE_KEYS},
            "BH가족크기": n_family,
        },
        "정의모호성_참고": {
            "쟁점": "보관된 13-19 사전선언의 16항(현 08) ③은 '표준편차'라고만 적혀 있다.",
            "채택": "표본표준편차(n−1). 위 자질별의 값이 이것이다.",
            "참고_모표준편차_델타": None if ref is None else round(ref["델타"], STAT_DIGITS),
            "비고": "판정에 쓰지 않는다. 정의가 애매한 자리를 기록으로 남긴 것이다.",
        },
        "예측대조": results,
        "예측집계": tally,
    }
    out["설정"]["총소요초"] = round(time.time() - t0, 1)
    write_json(OUT_JSON, out, indent=1)
    print(f"\n      {OUT_JSON}")
    print(f"      {os.path.getsize(OUT_JSON):,} bytes · "
          f"소요 {out['설정']['총소요초']}초")

    # ── 눈으로 검수할 것 ────────────────────────────────────────
    line("확인 항목")
    print("  아래를 직접 보고 나서 결과를 쓰십시오.")
    print("   1. 세 자질의 방향이 하나의 이야기를 이루는가. 문장이 짧고, 구두점을")
    print("      덜 찍고, 길이가 고르다면 '짧고 단조로운 리듬'이라는 한 그림이다.")
    print("      방향이 제각각이면 셋을 묶어 R 블록이라 부를 근거가 약해진다.")
    print("   2. ①과 ③이 서로 독립인지 의심하라. 문장이 짧으면 길이의 폭도 좁아")
    print("      보이기 쉽다(바닥이 0이라 아래로 퍼질 자리가 없다). ③의 δ가 ①과")
    print("      같은 방향으로 크게 나왔다면, 그것이 '고르다'인지 '짧다의 부산물'")
    print("      인지는 이 표가 답하지 못한다. 평균으로 나눈 무단위 값이라는 것이")
    print("      방어이기는 하나 완전하지는 않다.")
    print("   3. ②의 부호를 07의 PUNCT와 맞춰 보라. 분모가 다른 두 값이라 크기는")
    print("      달라도 부호는 같아야 한다. 어긋나면 어느 한쪽의 분모 처리가 틀렸다.")
    print("   4. 산포(IQR 비)와 위치(δ)를 섞어 읽지 말라. 폭 비가 1보다 작다는 것은")
    print("      '봇이 서로 닮았다'이지 '봇이 낮다'가 아니다. 옛 산포검정(보관)이")
    print("      잡은 뭉침이 R 블록에서도 보이는지를 묻는 별개의 물음이다.")
    print("   5. 여기서 결론을 내지 말라. R 블록이 BotSim에서 갈린다는 것은 필요")
    print("      조건일 뿐이다. 같은 방향이 fox8에서도 나오는지는")
    print("      옛 19 fox8 재검증(보관)이 보고, 서브레딧 화법의 부산물인지는")
    print("      09-3이 본다.")
    print()
    print("  이 다섯은 스크립트가 대신 판정할 수 없는 것들이다. δ와 q를 뽑는")
    print("  일까지가 코드의 몫이고, 그 숫자가 무슨 이야기인지는 사람이 읽는다.")
    print("  방법은 사전선언에 미리 못 박혀 있다 — 결과가 약하다고 자질을 더")
    print("  만들거나 문턱을 옮기는 순간, 이 표는 아무것도 증명하지 못한다.")


if __name__ == "__main__":
    main()
