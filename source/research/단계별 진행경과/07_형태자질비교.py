#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
07_형태자질비교.py
────────────────────────────────────────────────────────────────────────────
목적
    06이 단어 하나하나로 잡아낸 차이를, 단어를 거치지 않고 문법 형태로 직접
    잰다. 04가 이미 계정마다 저장해 둔 형태 자질 58종(Tense=Past, Person=3,
    Mood=Imp …)과 품사 17종(NOUN, VERB, DET …)에 라벨을 붙여 두 무더기로
    나누고, 06과 똑같은 저울로 견준다. 재파싱은 없다 — 04의 숫자를 나누기만
    한다.

왜 M 블록을 지금 하나
    봉인된 분석 라인의 「변경 26 치명 1」이 이 파일의 출발점이다. 06의 δ 상위
    단어들이 만든 점수의 94%를 `was` 하나가 설명했고, 그 지문의 실체는
    "과거시제 3인칭 서사를 쓰지 않는다"는 한 축이라는 진단이 이미 적혀 있다.
    그런데 06은 그 진단을 확인할 수 없다. 06이 재는 것은 `was`라는 철자의
    빈도이지 과거시제라는 문법 범주가 아니기 때문이다.

    단어로 문법을 재면 두 가지가 섞인다. was가 적다는 것은 (ㄱ) 과거시제를
    덜 고른다는 뜻일 수도 있고, (ㄴ) 과거시제는 똑같이 쓰되 was 대신 were·
    had·did 같은 다른 철자로 쓴다는 뜻일 수도 있다. 어휘 선택과 문법 선택이
    한 숫자에 겹쳐 있다. 형태 자질은 그 겹침을 걷어낸다 — Tense=Past는
    was·were·had·walked·said를 한데 묶은 값이라 철자가 무엇이든 상관없다.

    그래서 07은 06의 되풀이가 아니라 06에 대한 시험이다. 자질 층위에서
    같은 방향이 더 크게 나오면 06이 잡은 것은 문법 현상이고, 자질 층위에서
    사라지면 06이 잡은 것은 특정 낱말의 습관이다. 둘은 논문에서 전혀 다른
    주장이 된다. 이 갈림길을 fox8까지 끌고 가지 않고 여기서 가른다.

무엇을 따르나
    07-12_사전선언.md (2026-08-27 확정)의 「07 — M 블록」 절을 그대로 구현한다.
    결정 하나하나가 코드의 상수와 함수로 박혀 있다.

        결정 0-1  라벨 개봉 이후의 규율
                  06에서 라벨을 열었으므로 07은 "라벨을 아는 상태"에서
                  수행된다. 01~05를 지켜 준 봉인이 여기에는 없다. 그 자리를
                  사전등록이 대신한다 — 스크립트를 쓰기 전에 예측을 적어
                  두고, 빗나가도 그대로 보고한다. 아래 PREDICTIONS 상수가
                  그 약속의 코드판이다.

        07 분모 규칙   대립값이 둘 이상인 축의 자질은 그 축의 총 출현수로
                       나누고, 대립값이 하나뿐인 자질과 UPOS 17종은
                       토큰수_구두점제외로 나눈다. 분모 0은 결측이다.
                       최소 문턱은 두지 않는다(문턱을 두면 새 자유도가 생긴다).
                       전체 토큰 기준 비율도 보조로 저장하되 판정에 쓰지 않는다.

        07 비교 방법   06과 완전히 동일하다. Mann-Whitney U(양측·동점 보정·
                       연속성 보정) + Cliff's δ(그룹1 = bot) + BH FDR q = 0.05.
                       주목 = q ≤ 0.05 그리고 |δ| ≥ 0.147.
                       두 가족(형태자질 58종 / UPOS 17종)에 각각 따로 보정한다.

        07 희소 표시   출현 계정이 전체의 10% 미만이면 표시만 하고 빼지 않는다.

    결과가 약하다고 방법을 바꾸지 않는다. 바꿔야 한다면 사전선언 말미의
    「변경 이력」에 사유와 일시를 먼저 적고, 변경 전 결과도 함께 보고한다.

실행
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 -u 07_형태자질비교.py
    필요 패키지 없음. 표준 라이브러리만 쓴다(03·04·05·06과 같은 무의존 원칙).
    04의 자질·품사 수치를 나누고 정렬할 뿐이라 몇 초면 끝난다.

선행 조건
    같은 폴더에 04_기능어측정.json 과 01_적격계정.json 이 있어야 한다.
    04가 없으면 아무것도 하지 않고 끝낸다. 01에서는 "라벨" 키 하나만 꺼내고
    나머지는 즉시 버린다(06과 같은 del 규율 — 07이 원문을 볼 일은 없다).
    07-12_사전선언.md 의 07 절을 먼저 읽고 시작하는 것이 원래 순서다.

산출
    07_형태자질비교.json
        설정(분모 규칙·04 승계·사전 예측 대조 결과) · 축분류 ·
        형태자질 58종 · UPOS 17종 · 주목자질 목록 · 보조_전체토큰기준
"""

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
MEASURE_JSON = f"{HERE}/04_기능어측정.json"      # 04 산출물 — 자질·UPOS·토큰수
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"       # 01 산출물 — "라벨" 키만 꺼낸다
OUT_JSON = f"{HERE}/07_형태자질비교.json"        # 산출물

GROUP1, GROUP2 = "bot", "human"
# 06과 같은 순서로 고정한다. U와 δ는 모두 '그룹1 기준'이라 이 순서가 뒤집히면
# 부호가 통째로 반대가 되고, 06과의 대조가 전부 어긋난다.
#   δ > 0  →  봇이 높음
#   δ < 0  →  봇이 낮음

Q_ALPHA = 0.05          # BH 보정 후 유의 판정 문턱 (사전선언: q = 0.05, 06과 동일)
DELTA_NOTABLE = 0.147   # '주목'의 효과크기 하한 (관례적 small 경계, 06과 동일)
SPARSE_FRAC = 0.10      # 출현 계정이 전체의 이 비율 미만이면 '희소' 표시
TOP_SHOW = 25           # 형태자질 주목 표에 몇 줄을 띄울 것인가
MISSING_SHOW = 12       # 결측이 많은 자질을 몇 줄이나 볼 것인가

RATE_DIGITS = 6         # 비율·중앙값 저장 자릿수 (04·05와 같은 눈금)
STAT_DIGITS = 4         # U·z·δ 저장 자릿수
SIG_DIGITS = 6          # p·q는 유효숫자로 자른다 — 아래 sig() 참조

# 04 로그에 찍힌 종수. 어긋나면 알리기만 하고 계속 돈다 — 이 값으로 자질을
# 고르거나 버리지 않는다(사전선언: 사후 문턱 도입 금지). 04가 다른 실행분으로
# 바뀌었는지 눈치채기 위한 표지일 뿐이다.
EXPECT_FEATURES = 58
EXPECT_UPOS = 17

DENOM_AXIS = "축내부합"              # 분모 = 그 계정의 해당 축 총 출현수
DENOM_TOKEN = "토큰수_구두점제외"     # 분모 = 그 계정의 구두점 제외 토큰수

# ── 자가검증 고정 예제 (1) 통계 ─────────────────────────────────
# 06의 SELF_CHECK_* 를 그대로 가져왔다. 손계산 과정은 self_check_stats()의
# docstring에 적혀 있고, 기대값은 그 손계산에서 온 상수다.
#   (설명, A(=그룹1), B(=그룹2), 기대 U_A, 기대 δ, 기대 σ²)
SELF_CHECK_U = [
    ("완전 분리", [1, 2, 3], [4, 5, 6], 0.0, -1.0, 5.25),
    ("동점 포함", [1, 1, 2], [1, 2, 2], 3.0, -1.0 / 3.0, 4.05),
]
SELF_CHECK_BH_P = [0.01, 0.02, 0.03, 0.04]
SELF_CHECK_BH_Q = [0.04, 0.04, 0.04, 0.04]
SELF_CHECK_TOL = 1e-9

# ── 자가검증 고정 예제 (2) 분모 규칙 ────────────────────────────
# 07에서 새로 들어온 규칙이라 새로 만든 예제다. 인공 계정 세 개로 축 판별과
# 분모 선택과 결측 처리를 한꺼번에 건다. 손계산은 self_check_denominator()의
# docstring에 있다.
#
# 이 인공 자료에서 Tense 축은 값이 둘(Past·Pres)이라 축 내부 비율을 쓰고,
# Voice 축은 값이 하나(Pass)뿐이라 토큰수를 쓴다. 축 판별을 하드코딩하지 않고
# 자료에서 유도한다는 것이 이 예제로 확인된다.
SELF_CHECK_ACCOUNTS = {
    "가": {"토큰수_구두점제외": 20,
           "자질": {"Tense=Past": 3, "Tense=Pres": 1, "Voice=Pass": 2},
           "UPOS": {"VERB": 4}},
    "나": {"토큰수_구두점제외": 10,
           "자질": {"Tense=Pres": 4, "Voice=Pass": 1},
           "UPOS": {"VERB": 4}},
    "다": {"토큰수_구두점제외": 5,
           "자질": {"Voice=Pass": 1},
           "UPOS": {"NOUN": 3}},
}
SELF_CHECK_AXES = {"Tense": 2, "Voice": 1}      # 축 이름 → 기대 값 종수
#   (계정, 자질, 기대 축내부비율, 기대 전체토큰비율, 설명)
SELF_CHECK_RATIO = [
    ("가", "Tense=Past", 0.75, 0.15,
     "시제 넷 중 셋이 과거 → 0.75. 전체 20토큰으로 나누면 0.15로 전혀 다른 값"),
    ("가", "Tense=Pres", 0.25, 0.05, "같은 계정의 나머지 한 몫"),
    ("가", "Voice=Pass", 0.10, 0.10,
     "Voice는 대립값이 하나뿐이라 분모가 토큰수 → 두 값이 같아진다"),
    ("나", "Tense=Past", 0.00, 0.00,
     "시제는 넷 다 현재. 축이 나왔으므로 결측이 아니라 0이다"),
    ("다", "Tense=Past", None, 0.00,
     "Tense 축이 한 번도 안 나왔다 → 분모 0 → 결측(None)"),
    ("다", "Voice=Pass", 0.20, 0.20, "토큰 5개 중 1회"),
]

# ── 사전 예측 (07-12_사전선언 「07 — M 블록」의 다섯 항목) ──────
# 이 상수가 사전등록의 실체다. 여기 적힌 부호는 결과를 보기 전에 문서에
# 확정된 것이고, 아래 [6/6]이 실제 δ와 자동으로 대조한다. 빗나간 예측을
# 조용히 지우거나 문구를 고치면 사전등록이 아무 의미가 없어진다 — 빗나간
# 것도 그대로 화면과 JSON에 남긴다.
#
# "근거"는 화면 폭에 맞춰 미리 끊어 둔 줄의 목록이다. 자동 줄바꿈을 쓰지 않는
# 것은 이 파일의 다른 표들과 같은 이유다 — 한글은 터미널에서 두 칸을 차지해
# 글자 수로 자르면 폭이 맞지 않는다. JSON에는 한 줄로 이어 붙여 담는다.
PRED_REF_WAS = -0.718       # 06_비교결과의 was δ. 예측 1의 대조 기준이다.
PREDICTIONS = [
    {"번호": 1,
     "서술": "Tense=Past 비율에서 봇이 낮다 (δ < 0)",
     "가족": "형태자질",
     "검사": [("Tense=Past", "<")],
     "근거": ["치명 1이 지목한 축('과거시제 3인칭 서사를 쓰지 않는다')이므로",
             "성립해야 한다. |δ|가 06의 was(−0.718)보다 크면 자질이 단어보다",
             "깨끗한 측정임을 뜻한다."]},
    {"번호": 2,
     "서술": "Person=3 비율에서 봇이 낮고, Person=1 비율에서도 봇이 낮다",
     "가족": "형태자질",
     "검사": [("Person=3", "<"), ("Person=1", "<")],
     "근거": ["06의 he(−0.699)·i(−0.576)와 방향이 같아야 한다."]},
    {"번호": 3,
     "서술": "Mood=Imp(명령법)과 Voice=Pass에서 봇이 높다",
     "가족": "형태자질",
     "검사": [("Mood=Imp", ">"), ("Voice=Pass", ">")],
     "근거": ["캠페인·격식 산문의 표지로 예상한다.",
             "근거는 06의 must(+0.824)·while(+0.785)."]},
    {"번호": 4,
     "서술": "UPOS에서 봇이 DET·ADP를 높게, PRON·VERB를 낮게 쓴다",
     "가족": "UPOS",
     "검사": [("DET", ">"), ("ADP", ">"), ("PRON", "<"), ("VERB", "<")],
     "근거": ["06의 the(+0.603)·of(+0.524)·i(−0.576)와 정합해야 한다."]},
]
# 예측 5는 다른 넷과 성격이 다르다. 새로운 부호를 예측하는 것이 아니라
# 1·2의 결과에 걸린 조건부 지시라, 검사 목록 대신 [6/6]의 마지막 블록이
# 직접 판정한다.
PRED5_LINES = ["위 1·2가 성립하지 않으면, 06의 단어별 결과는 형태 층위가 아니라",
               "어휘 층위의 현상이라는 뜻이므로 해석을 전면 재검토한다"]
PRED5_TEXT = " ".join(PRED5_LINES)

# 표 머리글. 한글은 터미널에서 두 칸을 차지해 f-string의 자리맞춤({:<13})이
# 어긋난다. 그래서 06과 같은 방식으로 공백을 손으로 세어 맞춰 두었다.
# 아래 print_feature_table()의 값 서식과 짝이므로 한쪽만 고치지 말 것.
# 값 한 줄이 차지하는 칸(1부터):
#   1-6 들여쓰기 · 7-19 자질 · 20-26 δ · 29-37 방향(한글 4자+공백=9칸)
#   40-47 q · 50-57 봇중앙 · 60-67 사람중앙 · 70-74 유효n
# (δ·≤·≥는 폭이 모호한 글자다. CJK 설정 터미널에서는 두 칸으로 보여 머리글이
#  한 칸씩 밀릴 수 있다. 값 정렬 자체는 영향받지 않는다.)
TABLE_HEAD = ("      자질" + " " * 15 + "δ  방향" + " " * 14 + "q"
              + " " * 4 + "봇중앙" + " " * 2 + "사람중앙" + " " * 2 + "유효n")


def line(title=""):
    """구분선 한 줄. 06의 같은 함수를 그대로 가져왔다."""
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다. 04·05·06의 같은 함수를 그대로 가져왔다.

    임시 파일에 먼저 쓰고 이름을 바꿔치기한다(os.replace). 쓰는 도중에 창을
    닫으면 파일이 반쯤 잘린 채 남는다. 이름 바꾸기는 쪼개지지 않는 연산이라,
    어느 시점에 멈춰도 파일은 '이전 것' 아니면 '새 것'이다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def sig(x, digits=SIG_DIGITS):
    """
    p·q를 유효숫자 기준으로 자른다. 06에서 그대로 가져왔다.

    소수 자릿수로 반올림하면(round(p, 6)) 3e-40 같은 값이 통째로 0이 된다.
    유효숫자로 자르면 크기를 잃지 않으면서 파일이 짧아진다.
    """
    if x == 0.0:
        return 0.0
    return float(f"{x:.{digits}g}")


def rnd(x, digits):
    """None을 그대로 통과시키는 round. 검정 불가 자질의 칸이 None이라 필요하다."""
    return None if x is None else round(x, digits)


# ════════════════════════════════════════════════════════════════════════
# [통계] U 검정 · Cliff's δ · BH 보정
# ────────────────────────────────────────────────────────────────────────
# 아래 네 함수(normal_cdf · ranks_with_ties · mann_whitney · bh_qvalues)는
# 06_봇사람비교.py 에서 한 글자도 고치지 않고 가져온 것이다. 06에서 이미
# 손계산 예제와 scipy 대조를 통과한 코드라 다시 짜면 잃을 것만 있다.
# 사전선언이 "비교 방법은 06과 완전히 동일하다"고 못 박은 것을, 같은 절차를
# 다시 구현하는 것이 아니라 같은 코드를 그대로 쓰는 것으로 지킨다.
# 상세한 유도와 주석은 06 원본에 있다 — 여기서는 요약만 남긴다.
# ════════════════════════════════════════════════════════════════════════
def normal_cdf(x):
    """
    표준정규분포의 누적확률 Φ(x). [06에서 가져옴]

    math.erf 로 Φ(x) = ½(1 + erf(x/√2)). |x|가 8을 넘으면 배정도 실수의
    바닥에 닿아 p가 0.0으로 찍힌다 — "차이가 없을 확률이 0"이 아니라 "이
    계산으로는 더 작은 값을 구분할 수 없다"는 뜻이다.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def ranks_with_ties(values):
    """
    오름차순 순위. 같은 값끼리는 자리 번호를 나눠 갖는다. [06에서 가져옴]

    평균 순위를 쓰는 덕에 Cliff's δ의 동점 ½ 규칙이 따로 코드를 쓰지 않고도
    저절로 맞는다. 07의 자료에서도 동점은 지배적이다 — 대립값이 두셋뿐인 축의
    비율은 0.0·0.5·1.0 같은 값에 계정이 무더기로 겹쳐 앉는다. 짧은 계정일수록
    심하다(Mood 축이 두 번 나온 계정의 Mood=Imp 비율은 0, ½, 1 셋 중 하나다).

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
    Mann-Whitney U 검정(양측)과 Cliff's δ. 그룹1 기준. [06에서 가져옴]

        R1  = 그룹1이 가져간 순위의 합
        U1  = R1 − n1(n1+1)/2            (그룹1이 이긴 쌍의 수, 동점은 ½)
        δ   = 2·U1/(n1·n2) − 1           (Cliff's δ, −1 … +1)
        σ²  = (n1·n2/12)·[(N+1) − Σ(t³−t)/(N(N−1))]      (동점 보정 분산)
        z   = (U1 − n1·n2/2 − c)/σ       (c = ±0.5 연속성 보정)
        p   = 2·(1 − Φ(|z|))             (양측)

    σ² ≤ 0 이면 두 무더기의 값이 전부 같다는 뜻이라 δ = 0, z = 0, p = 1.0.
    07에서는 이 자리가 06보다 흔하다 — 예를 들어 어느 계정에서도 나오지 않은
    자질이나, 모든 계정에서 비율이 정확히 1.0인 자질(그 축에 대립값이 사실상
    하나뿐인 경우)이 여기로 온다.
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
    Benjamini-Hochberg FDR 보정. [06에서 가져옴]

        p를 오름차순으로 늘어놓고,  q_(i) = min_{j ≥ i} ( p_(j) · m / j )

    뒤에서부터 최솟값을 끌고 오는 min이 q를 단조 증가로 만든다. 1.0을 넘으면
    1.0으로 자른다.

    07에서 이 함수는 두 번 따로 불린다 — 형태자질 가족과 UPOS 가족에 각각
    걸어야 하기 때문이다(사전선언: "두 가족에 각각 별도로 BH 보정"). 둘을
    한 가족으로 묶으면 m이 75가 되어 UPOS 쪽 문턱이 자질 58종의 사정에 따라
    흔들린다. 애초에 다른 것을 재는 두 목록이라 가족을 나누는 편이 맞다.
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


def direction_of(delta):
    """δ의 부호를 말로 옮긴다. [06에서 가져옴] 그룹1 = 봇으로 고정되어야 뜻이 맞다."""
    if delta > 0:
        return "봇이 높음"
    if delta < 0:
        return "봇이 낮음"
    return "차이 없음"


# ════════════════════════════════════════════════════════════════════════
# [1] 입력 적재
# ════════════════════════════════════════════════════════════════════════
def load_measurement():
    """
    04 산출물에서 "설정"과 "계정"을 가져온다.

    04 파일에는 라벨이 애초에 들어 있지 않다(04가 읽지 않았으므로). 라벨을
    조심해야 하는 파일은 01뿐이고, 그쪽은 아래 load_labels()에서 "라벨" 키
    하나만 열어 본다.
    """
    data = json.load(open(MEASURE_JSON, encoding="utf-8"))
    return data["설정"], data["계정"]


def inherit_fingerprint(conf):
    """
    04의 기능어 지문(해시·종수)과 실행일을 07 산출물에 그대로 옮겨 적는다.

    07은 기능어를 세지 않는데 왜 기능어 해시를 베껴 두나. 이 해시는 07이 쓰는
    수치의 출처가 아니라 04 실행분의 신분증이기 때문이다. 05가 04에서 받아
    06에게 넘겼고, 07이 같은 값을 적으면 05·06·07이 같은 04 파일을 읽었다는
    사실이 파일만 열어 봐도 확인된다. 04를 다시 돌려 자질 종수가 58에서 60이
    되었는데 옛 06 결과와 새 07 결과를 나란히 놓는 사고를, 이 한 줄이 막는다.
    측정-검수-비교가 한 줄로 이어져 있다는 증거이기도 하다.
    """
    return {"기능어_해시": conf.get("기능어_해시"),
            "기능어_개수": conf.get("기능어_개수"),
            "04_실행일": conf.get("실행일")}


def load_labels():
    """
    01에서 "라벨" 키 하나만 꺼낸다. 06의 같은 함수를 그대로 가져왔다.

    del data 는 이 함수의 이름표를 지우는 것이고, 붙들고 있던 라벨 사전만
    남는다. 원문("계정")·언어판정·깔때기 통계는 그 자리에서 회수된다.
    07이 원문을 다시 들여다볼 일은 없고, 안 쓰는 23MB를 메모리에 이고 있을
    이유도 없다. 06에서 이미 라벨을 열었으니 이제 숨길 것은 없지만, 필요한
    것 하나만 들고 나오는 규율 자체는 그대로 지킨다.
    """
    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    labels = data.get("라벨") or {}
    del data
    return labels


def split_by_label(accounts, labels):
    """
    04의 계정을 라벨에 따라 두 무더기로 가른다. 06의 같은 함수와 대상만 다르다.

    라벨이 없거나 값이 bot/human이 아닌 계정은 비교에서 빠진다. 사전선언
    결정 2가 금지한 '분석적 제외'가 아니라 대응할 짝이 없는 것이다 — 어느
    무더기에 넣을지 알 수 없으면 비교 자체가 성립하지 않는다.
    01이 1,869계정 전원에 라벨을 달아 두었으므로 실제로는 나올 일이 아니다.
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
# [2] 축 판별과 비율 계산 — 사전선언 07의 분모 규칙
# ════════════════════════════════════════════════════════════════════════
def build_axis_map(accounts):
    """
    자료 전체를 훑어 축마다 어떤 값들이 나타나는지 모은다.

    UD 형태 자질의 키는 언제나 "축=값" 꼴이다(Tense=Past, PronType=Rel).
    "="를 기준으로 앞이 축, 뒤가 값이다.

    ■ 왜 축 목록을 손으로 적지 않고 자료에서 뽑는가 ■
    사전선언의 분모 규칙은 "대립값이 2개 이상인 축"과 "대립값이 하나뿐인 자질"을
    가른다. 그 판정을 상수로 박아 두면(예: Voice는 언제나 토큰수 분모) 자료가
    바뀌는 순간 규칙이 조용히 틀린다. fox8이나 IRA에 Voice=Act가 한 번이라도
    나오면 Voice는 그 자료에서 대립 축이 되고, 그때도 여전히 토큰수로 나누고
    있으면 07과 12가 서로 다른 눈금을 쓰게 된다. 자료에서 유도하면 규칙이
    자료를 따라간다 — 사전선언에 적힌 것은 축 이름 목록이 아니라 규칙 자체다.

    판정 범위는 '계정 하나'가 아니라 '자료 전체'다. 어떤 계정에 Tense=Past만
    나왔다고 해서 그 계정에서 Tense가 단일값 축이 되면, 같은 자질의 분모가
    계정마다 달라져 비교가 불가능해진다.

    반환: {축 이름: 정렬된 값 목록}
    """
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


def axis_of(key):
    """자질 키에서 축 이름만 떼어 낸다. "="가 없으면 키 전체가 축이다."""
    return key.split("=", 1)[0]


def denom_kind_of(key, axis_map):
    """
    이 자질에 어떤 분모를 쓸지 정한다. 사전선언 07의 표를 그대로 옮긴 것이다.

        대립값 ≥ 2  →  그 계정의 해당 축 총 출현수      (DENOM_AXIS)
        대립값 = 1  →  그 계정의 토큰수_구두점제외      (DENOM_TOKEN)

    ■ 두 분모가 무엇을 다르게 재는가 (이 파일에서 가장 중요한 구분) ■
    Tense=Past 를 놓고 보자. 어떤 계정이 시제 표시를 400번 했고 그중 300번이
    과거라 하자. 그리고 그 계정의 전체 토큰은 2,000개다.
        축 내부 비율   300 / 400  = 0.75   "시제를 표시할 때 과거를 얼마나 고르나"
        전체 토큰 비율 300 / 2000 = 0.15   "글 전체에서 과거형이 얼마나 나오나"
    두 번째 값은 동사를 얼마나 쓰는지에 통째로 끌려다닌다. 명사구 위주로 짧게
    쓰는 계정은 과거만 골라 쓰더라도 0.15가 0.05로 떨어진다. 그러면 우리가
    "과거시제를 덜 고른다"고 읽은 것이 실은 "동사 자체를 덜 쓴다"였던 셈이 된다.
    치명 1이 지목한 것은 앞의 선택이지 뒤의 사용량이 아니므로, 판정은 축 내부
    비율로 한다. 뒤의 값도 버리지 않고 보조로 저장하되 판정에는 쓰지 않는다.

    Voice=Pass 처럼 대립값이 하나뿐인 자질에는 이 구분이 성립하지 않는다.
    분모가 될 축 합계가 곧 자기 자신이라 비율이 언제나 1.0이 되어 버린다.
    그래서 F 블록(기능어)과 같은 눈금인 토큰수_구두점제외를 쓴다.
    """
    return DENOM_AXIS if len(axis_map.get(axis_of(key), [""])) >= 2 else DENOM_TOKEN


def compute_ratios(accounts, keys, axis_map):
    """
    계정마다 자질 58종의 비율을 낸다. 반환은 (판정용, 보조용, 출현계정수).

    ■ 없는 키는 0회다 — 결측이 아니다 ■
    04는 희소 저장을 한다. 그 계정에서 한 번도 안 나온 자질은 "자질" 사전에
    키가 아예 없다. 여기서 그 계정을 건너뛰면 06의 word_vector()가 경고한 것과
    똑같은 사고가 난다 — "그 자질을 안 쓴 계정"이 통째로 표본에서 사라지고,
    정작 재려던 '덜 쓴다'가 그 사라진 0들이다.
    그래서 count 는 .get(key, 0) 으로 0을 채우고, 결측 판정은 오로지 분모로만
    한다. 분자가 0인 것과 분모가 0인 것은 전혀 다른 사건이다:
        Tense=Past 0회, Tense=Pres 12회  →  0 / 12 = 0.0    (값이 있다)
        Tense 축 자체가 0회              →  0 / 0  = 결측   (나눗셈 불성립)
    앞은 "시제를 쓰면서 과거를 한 번도 안 골랐다"는 정보이고, 뒤는 "잴 거리가
    없다"는 뜻이다. 앞을 결측으로 처리하면 신호를 통째로 버리게 된다.

    분모 0은 결측(None)으로 두고 그 자질의 검정에서만 빠진다. 분석적 제외가
    아니라 나눗셈 불성립이며, 05의 분모 0 처리와 같은 성격이다(사전선언 07).
    최소 문턱은 두지 않는다 — 분모가 2인 계정도 그대로 들어간다. 문턱을 두면
    "왜 하필 그 값이냐"는 새 자유도가 생긴다(결정 2와 같은 논리).
    """
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


def compute_upos_ratios(accounts, keys):
    """
    품사 17종의 비율. 분모는 언제나 토큰수_구두점제외다(사전선언 07).

    품사에는 '축'이 없다 — 모든 토큰이 정확히 하나의 UPOS를 갖기 때문에 17종의
    합이 곧 전체 토큰이다. 그래서 축 내부 비율과 전체 토큰 비율이 애초에 같은
    값이고, 보조값을 따로 저장할 것도 없다. 다만 04의 토큰수_구두점제외는
    PUNCT를 뺀 수이고 UPOS 사전에는 PUNCT가 그대로 남아 있어, PUNCT의 비율만은
    1보다 큰 쪽으로 뜨는 것이 아니라 '구두점을 뺀 말 토큰 대비 구두점 수'라는
    다른 뜻의 값이 된다. 구두점 습관은 R 블록(리듬)이 다룰 신호라 여기서
    해석하지 않는다 — 표에는 그대로 두되 그 줄만은 눈금이 다르다고 읽는다.
    """
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


# ════════════════════════════════════════════════════════════════════════
# [자가검증] 통계 기계와 분모 규칙을 각각 고정 예제로 건다
# ════════════════════════════════════════════════════════════════════════
def self_check_stats():
    """
    U·δ·BH 구현을 손으로 푼 예제와 맞춘다. 06의 self_check()를 그대로 가져왔다.

    06에서 이미 통과한 코드를 왜 또 거는가. 이 파일이 06을 import 하는 것이
    아니라 복사해 왔기 때문이다. 복사 과정에서 부호 하나가 바뀌어도 코드는
    멀쩡히 돌고 그럴듯한 p값이 나온다. 순위 검정은 틀려도 조용하다.

    ── 예제 1. 완전 분리 ─────────────────────────────────────
        A(그룹1) = [1, 2, 3],  B(그룹2) = [4, 5, 6]
        순위 1 2 3 4 5 6, R_A = 6, n1 = n2 = 3.
        U_A = 6 − 3·4/2 = 0            (A가 이긴 쌍이 하나도 없다)
        δ   = 2·0/9 − 1 = −1.0
        σ²  = (9/12)·[(6+1) − 0] = 5.25

    ── 예제 2. 동점 포함 ─────────────────────────────────────
        A(그룹1) = [1, 1, 2],  B(그룹2) = [1, 2, 2]
        1이 자리 1·2·3을 나눠 평균 순위 2, 2가 자리 4·5·6을 나눠 평균 순위 5.
        A의 순위 2, 2, 5 → R_A = 9,  U_A = 9 − 6 = 3.0
        δ   = 2·3/9 − 1 = −1/3 ≈ −0.3333
        σ²  = 동점 묶음 t=3 둘 → Σ(t³−t) = 48
              (9/12)·[7 − 48/30] = 0.75 × 5.4 = 4.05
        예제 1의 5.25보다 작다 — 동점 보정 항을 빠뜨리면 여기서 걸린다.

    ── 예제 3. BH 보정 ───────────────────────────────────────
        p = [0.01, 0.02, 0.03, 0.04], m = 4 → p_(i)·m/i 가 넷 다 0.04
        q = [0.04, 0.04, 0.04, 0.04]

    통과하면 True, 아니면 화면에 원인을 적고 False.
    """
    print("\n  ── (1) 통계 기계 — U · δ · BH ──")
    ok = True

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
        print(f"    (참고: z = {got['z']:.4f}, 양측 p = {got['p']:.4f})")

    got_q = bh_qvalues(SELF_CHECK_BH_P)
    good = all(abs(g - e) <= SELF_CHECK_TOL
               for g, e in zip(got_q, SELF_CHECK_BH_Q))
    ok = ok and good
    print(f"  BH 보정  p={SELF_CHECK_BH_P}")
    print(f"    기대 q={SELF_CHECK_BH_Q}")
    print(f"    실제 q={[round(v, 4) for v in got_q]}  "
          f"{'통과' if good else '실패'}")
    return ok


def self_check_denominator():
    """
    분모 규칙을 인공 계정 세 개로 건다. 07에서 새로 들어온 검사다.

    왜 따로 거는가. 분모는 07이 06에 더한 유일한 새 계산이고, 틀려도 조용한
    종류의 계산이다. 축 합계 대신 토큰수로 나눠도 0과 1 사이의 그럴듯한 값이
    나오고, δ도 q도 멀쩡히 나온다. 표를 며칠 들여다본 뒤에야 "이 숫자가 왜
    이렇게 작지"에서 알아챈다. 값 몇 개를 손으로 미리 풀어 두는 편이 훨씬 싸다.

    ── 인공 자료 ─────────────────────────────────────────────
        계정 가  토큰 20  {Tense=Past:3, Tense=Pres:1, Voice=Pass:2}
        계정 나  토큰 10  {Tense=Pres:4, Voice=Pass:1}
        계정 다  토큰  5  {Voice=Pass:1}

    ── 검사 1. 축 판별이 자료에서 유도되는가 ─────────────────
        Tense 축에 나타난 값 = {Past, Pres} → 2종 → 대립 축 → 축 내부 분모
        Voice 축에 나타난 값 = {Pass}       → 1종 → 단일값  → 토큰수 분모
        축 이름을 코드에 적어 두지 않았다는 것이 여기서 확인된다.

    ── 검사 2. 축 내부 비율과 전체 토큰 비율이 다르다 ────────
        계정 가의 Tense 축 합계 = 3 + 1 = 4
            축 내부   Tense=Past = 3 / 4  = 0.75
            전체 토큰 Tense=Past = 3 / 20 = 0.15
        같은 계정, 같은 자질인데 값이 다섯 배 차이 난다. 앞은 "시제를 표시한
        네 번 중 세 번을 과거로 골랐다"이고, 뒤는 "스무 토큰 중 세 개가
        과거형이었다"이다. 07이 판정에 쓰는 것은 앞이다.
            Tense=Pres 는 나머지 한 몫이라 0.25 / 0.05.

    ── 검사 3. 단일값 축은 두 값이 같다 ──────────────────────
        계정 가의 Voice=Pass = 2 / 20 = 0.10 (분모가 토큰수이므로 보조값과 동일)
        계정 다의 Voice=Pass = 1 / 5  = 0.20
        분모 규칙이 뒤바뀌면 이 줄만 멀쩡히 통과하고 Tense 줄이 깨진다 —
        그래서 두 종류를 한 표에 같이 넣어 두었다.

    ── 검사 4. 분자 0과 분모 0을 가른다 ──────────────────────
        계정 나의 Tense=Past = 0 / 4 = 0.0     (시제를 넷 다 현재로 골랐다)
        계정 다의 Tense=Past = 0 / 0 = 결측    (Tense 축이 아예 없다)
        앞을 결측으로 처리하면 "과거를 안 쓴다"는 신호가 통째로 사라진다.
        07이 재려는 것이 바로 그 0들이므로, 이 두 줄의 구분이 결과를 가른다.

    통과하면 True, 아니면 화면에 원인을 적고 False.
    """
    print("\n  ── (2) 분모 규칙 — 축 판별 · 축내부 비율 · 결측 ──")
    ok = True

    axis_map = build_axis_map(SELF_CHECK_ACCOUNTS)
    print("  축 판별 (자료에서 유도한 값 종수)")
    for ax, expect_k in sorted(SELF_CHECK_AXES.items()):
        got_vals = axis_map.get(ax, [])
        good = len(got_vals) == expect_k
        ok = ok and good
        kind = DENOM_AXIS if len(got_vals) >= 2 else DENOM_TOKEN
        print(f"    {ax:<8} 기대 {expect_k}종 · 실제 {len(got_vals)}종 "
              f"{sorted(got_vals)}  → 분모 {kind}  "
              f"{'통과' if good else '실패'}")

    keys = sorted({k for a in SELF_CHECK_ACCOUNTS.values() for k in a["자질"]})
    ratios, aux, _ = compute_ratios(SELF_CHECK_ACCOUNTS, keys, axis_map)

    print("\n  비율 계산 (판정용 = 축내부 · 보조 = 전체토큰)")
    print("    계정  자질            판정용            보조")
    for uid, key, exp_main, exp_aux, why in SELF_CHECK_RATIO:
        got_main, got_aux = ratios[uid][key], aux[uid][key]
        good = _close(got_main, exp_main) and _close(got_aux, exp_aux)
        ok = ok and good
        print(f"    {uid}    {key:<14}"
              f"기대 {_fmt(exp_main)} 실제 {_fmt(got_main)}   "
              f"기대 {_fmt(exp_aux)} 실제 {_fmt(got_aux)}  "
              f"{'통과' if good else '실패'}")
        print(f"          {why}")

    return ok


def _close(got, expect):
    """기대값이 None(결측)인 칸까지 함께 비교한다."""
    if expect is None or got is None:
        return got is expect
    return abs(got - expect) <= SELF_CHECK_TOL


def _fmt(v):
    """자가검증 표에서 결측을 눈에 띄게 찍는다."""
    return " 결측 " if v is None else f"{v:>5.3f}"


def self_check():
    """두 자가검증을 차례로 걸고, 하나라도 어긋나면 본 비교를 시작하지 않는다."""
    line("[자가검증] 검정 기계와 분모 규칙을 고정 예제로 건다")
    ok_stats = self_check_stats()
    ok_denom = self_check_denominator()
    if ok_stats and ok_denom:
        print("\n  두 검사 모두 통과했다. 본 비교로 들어간다.")
        return True

    print()
    print("■ 중단 — 자가검증 실패")
    print("  본 비교를 시작하지 않습니다. 이 상태로 돌리면 틀린 표가 조용히 나옵니다.")
    if not ok_stats:
        print("  통계 쪽에서 짚어 볼 곳:")
        print("   · ranks_with_ties 의 평균 순위 — 자리 번호가 1부터인가")
        print("   · U1 = R1 − n1(n1+1)/2 에서 n1이 그룹1의 크기가 맞는가")
        print("   · 분산의 동점 보정 항 Σ(t³−t)/(N(N−1)) 의 부호와 분모")
        print("   · bh_qvalues 의 누적 min 방향 — 큰 p부터 거꾸로 훑는가")
        print("   (이 넷은 06에서 그대로 옮겨 온 코드다. 06 원본과 대조하라.)")
    if not ok_denom:
        print("  분모 쪽에서 짚어 볼 곳:")
        print("   · build_axis_map 이 '축=값'을 '=' 앞뒤로 제대로 가르는가")
        print("   · denom_kind_of 의 경계가 '값 종수 ≥ 2'가 맞는가")
        print("   · compute_ratios 에서 축 합계(axis_total)를 그 계정 안에서만")
        print("     더하고 있는가 — 전체 자료의 합계를 쓰면 값이 전부 작아진다")
        print("   · 분자 0(0/n)과 분모 0(n/0)을 가르고 있는가")
    return False


# ════════════════════════════════════════════════════════════════════════
# [비교] 한 가족을 통째로 검정하고 BH를 건다
# ════════════════════════════════════════════════════════════════════════
def defined_values(uids, ratios, key):
    """
    결측(None)을 뺀 값만 순서대로 늘어놓는다.

    결측은 그 자질의 검정에서만 빠진다. 계정이 통째로 빠지는 것이 아니라
    칸 하나가 빠지는 것이라, 같은 계정이 Tense 검정에는 들어가고 Mood 검정에는
    빠질 수 있다. 그래서 유효 계정 수가 자질마다 다르고, 아래 표에 그 수를
    한 칸 내주었다. 유효 수가 뚝 떨어진 자질은 남은 계정들이 어떤 계정인지를
    먼저 물어야 한다 — 그 축을 쓴 계정만 남은 것이므로 이미 한 번 걸러진
    표본이다.
    """
    out = []
    for u in uids:
        v = ratios[u][key]
        if v is not None:
            out.append(v)
    return out


def compare_family(keys, bot_ids, human_ids, ratios, presence,
                   sparse_cut, kinds=None):
    """
    한 가족(형태자질 58종 또는 UPOS 17종)을 통째로 검정하고 BH를 건다.

    ■ BH 가족에서 검정 불가 자질을 빼는 이유 ■
    결측을 걷어 낸 뒤 한쪽 무더기가 비면 U를 계산할 수 없다. p가 없는 항목을
    BH에 넣을 방법이 없으므로(m만 부풀린다) 가족에서 뺀다. 뺀 개수는 화면과
    JSON에 그대로 적는다 — m이 58이 아니라 56이었다는 사실은 q값의 뜻을
    바꾸므로 숨기면 안 된다. 이것은 사후 문턱이 아니다. 문턱은 "값이 있는데
    작아서 버리는 것"이고, 여기는 값 자체가 없다.

    반환은 |δ| 내림차순으로 정렬된 (자질, 결과) 목록이다. 검정 불가 항목은
    δ가 없으므로 맨 뒤로 보낸다. 사전선언이 주 결과로 지목한 것이 '유의 개수'가
    아니라 'δ가 큰 자질과 그 방향'이라, 화면도 파일도 큰 것부터 보이는 순서로 둔다.
    """
    n_all = len(bot_ids) + len(human_ids)
    rows = []
    for k in keys:
        v1 = defined_values(bot_ids, ratios, k)
        v2 = defined_values(human_ids, ratios, k)
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
            # 한쪽 무더기가 통째로 비었다. 견줄 것이 없다.
            r.update({"검정가능": False, "U": None, "z": None, "p": None,
                      "q": None, "델타": None, "방향": "검정 불가",
                      "봇_중앙": None, "사람_중앙": None,
                      "유의": False, "주목": False})
        else:
            res = mann_whitney(v1, v2)
            r.update({"검정가능": True, "U": res["U"], "z": res["z"],
                      "p": res["p"], "델타": res["델타"],
                      "방향": direction_of(res["델타"]),
                      "봇_중앙": statistics.median(v1),
                      "사람_중앙": statistics.median(v2)})
        rows.append((k, r))

    testable = [(k, r) for k, r in rows if r["검정가능"]]
    qs = bh_qvalues([r["p"] for _, r in testable])
    for (k, r), q in zip(testable, qs):
        r["q"] = q
        r["유의"] = q <= Q_ALPHA
        r["주목"] = r["유의"] and abs(r["델타"]) >= DELTA_NOTABLE

    # 검정 불가는 |δ|를 −1로 쳐서 맨 뒤로 보낸다(실제 δ의 하한은 −1이므로 겹치지 않는다).
    rows.sort(key=lambda kv: -(abs(kv[1]["델타"]) if kv[1]["검정가능"] else -1.0))
    return rows, len(testable)


def print_feature_table(rows, title, limit=None):
    """자질 표를 |δ| 내림차순으로 띄운다. limit이 None이면 전부 띄운다."""
    shown = rows if limit is None else rows[:limit]
    if not shown:
        print("\n      띄울 줄이 없습니다.")
        return
    print(f"\n      {title}")
    print(TABLE_HEAD)
    for k, r in shown:
        if not r["검정가능"]:
            print(f"      {k:<13}{'':>7}  검정 불가  "
                  f"(유효 봇 {r['봇_유효n']:,} · 사람 {r['사람_유효n']:,})")
            continue
        mark = "  희소" if r["희소"] else ""
        n_eff = r["봇_유효n"] + r["사람_유효n"]
        print(f"      {k:<13}{r['델타']:>+7.3f}  {r['방향']}  {r['q']:>8.4f}"
              f"  {r['봇_중앙']:>8.3%}  {r['사람_중앙']:>8.3%}"
              f"  {n_eff:>5,}{mark}")


def family_summary(rows, n_family, sparse_cut, n_all, label):
    """가족 하나의 요약을 찍는다. 06의 유의/주목 집계 블록과 같은 서식이다."""
    sig_n = sum(1 for _, r in rows if r["유의"])
    notable = [(k, r) for k, r in rows if r["주목"]]
    up = sum(1 for _, r in notable if r["델타"] > 0)
    down = sum(1 for _, r in notable if r["델타"] < 0)
    sparse_n = sum(1 for _, r in notable if r["희소"])
    untestable = sum(1 for _, r in rows if not r["검정가능"])

    # 아래 줄들의 공백도 손으로 맞춘 것이다(숫자가 49번째 칸에서 끝난다).
    print(f"\n      BH 가족 크기                         {n_family:>4}종 "
          f"/ {len(rows)}종 ({label})")
    if untestable:
        print(f"        검정 불가로 가족에서 빠짐           {untestable:>4}종")
    print(f"      유의 (q ≤ {Q_ALPHA})                        "
          f"{sig_n:>4}종")
    print(f"      주목 (q ≤ {Q_ALPHA} 그리고 |δ| ≥ {DELTA_NOTABLE})     "
          f"{len(notable):>4}종")
    print(f"        봇이 높음                            {up:>4}종")
    print(f"        봇이 낮음                            {down:>4}종")
    print(f"        그중 희소 표시                       {sparse_n:>4}종")
    print(f"        (희소 = 그 자질이 나온 계정이 {sparse_cut:,}개 미만 — "
          f"전체 {n_all:,}계정의 {SPARSE_FRAC:.0%})")
    return notable


# ════════════════════════════════════════════════════════════════════════
# [6] 사전 예측 대조 — 이 파일의 핵심
# ════════════════════════════════════════════════════════════════════════
def lookup(rows, key):
    """가족 목록에서 자질 하나를 찾는다. 없으면 None."""
    for k, r in rows:
        if k == key:
            return r
    return None


def check_prediction(pred, feat_rows, upos_rows):
    """
    예측 하나를 실제 결과와 대조한다.

    판정은 '부호'만 본다. 사전선언에 적힌 것이 "δ < 0", "δ > 0" 이지 "q ≤ 0.05
    이면서 δ < 0" 이 아니기 때문이다. 결과를 보고 판정 기준을 조이는 것이야말로
    사전등록이 막으려는 일이다. 다만 표에는 q를 나란히 찍어, 방향이 맞았더라도
    통계적으로 뒷받침되는지를 읽는 사람이 함께 보게 한다.

    자질이 자료에 없거나 검정 불가면 '판정불가'다. 적중으로도 빗나감으로도
    치지 않되, 예측 5의 조건 판정에서는 "성립하지 않음"으로 다룬다 —
    성립을 확인하지 못한 것은 성립이 아니다.
    """
    rows = feat_rows if pred["가족"] == "형태자질" else upos_rows
    items, verdicts = [], []
    for key, want in pred["검사"]:
        r = lookup(rows, key)
        if r is None:
            v = "판정불가"
            item = {"자질": key, "기대": f"δ {want} 0", "델타": None,
                    "q": None, "판정": v, "사유": "자료에 없는 자질"}
        elif not r["검정가능"]:
            v = "판정불가"
            item = {"자질": key, "기대": f"δ {want} 0", "델타": None,
                    "q": None, "판정": v, "사유": "결측 처리 후 한쪽 무더기가 빔"}
        else:
            d = r["델타"]
            hit = (d < 0) if want == "<" else (d > 0)
            v = "적중" if hit else "빗나감"
            item = {"자질": key, "기대": f"δ {want} 0", "델타": round(d, STAT_DIGITS),
                    "q": sig(r["q"]), "판정": v,
                    "주목": r["주목"], "희소": r["희소"]}
        items.append(item)
        verdicts.append(v)

    if all(v == "적중" for v in verdicts):
        overall = "적중"
    elif any(v == "판정불가" for v in verdicts):
        overall = "일부 판정불가"
    else:
        overall = "빗나감"
    return {"번호": pred["번호"], "서술": pred["서술"], "가족": pred["가족"],
            "근거": " ".join(pred["근거"]),      # 화면용 여러 줄을 한 줄로 이어 담는다
            "항목": items, "판정": overall}


def print_prediction_block(results):
    """예측 대조 결과를 표로 찍는다. 빗나간 것도 그대로 남긴다."""
    print("\n      사전선언 07의 예측 다섯 가지를 실제 결과와 대조한다.")
    print("      아래 부호는 결과를 보기 전에 문서에 확정된 것이다. 빗나간 예측도")
    print("      지우거나 고치지 않고 그대로 싣는다 — 그것이 사전등록의 요점이고,")
    print("      06에서 라벨을 연 이상 이 파이프라인에 남은 유일한 보호막이다.")

    for res in results:
        print()
        print(f"      예측 {res['번호']}  {res['서술']}   [{res['가족']}]")
        print("              자질            기대     실제 δ         q  판정")
        for it in res["항목"]:
            if it["델타"] is None:
                print(f"              {it['자질']:<14}{it['기대']:>7}"
                      f"{'—':>11}{'—':>10}  판정불가  ({it.get('사유', '')})")
            else:
                tail = "  희소" if it.get("희소") else ""
                print(f"              {it['자질']:<14}{it['기대']:>7}"
                      f"{it['델타']:>+11.3f}{it['q']:>10.4f}  {it['판정']}{tail}")
        print(f"        → 예측 {res['번호']} : {res['판정']}")
        # 근거는 PREDICTIONS 원본에서 다시 꺼낸다 — 결과 사전에는 JSON용으로
        # 한 줄로 이어 붙인 것이 들어 있어 화면 폭을 넘긴다.
        src = next(p for p in PREDICTIONS if p["번호"] == res["번호"])
        print("          근거로 적어 둔 것:")
        for ln in src["근거"]:
            print(f"            {ln}")

        # 예측 1에만 붙는 대조 — 자질이 단어보다 깨끗한 측정인가.
        if res["번호"] == 1 and res["항목"] and res["항목"][0]["델타"] is not None:
            d = res["항목"][0]["델타"]
            print(f"\n          06의 was  δ = {PRED_REF_WAS:+.3f}  (|δ| = "
                  f"{abs(PRED_REF_WAS):.3f})")
            print(f"          07의 Tense=Past  δ = {d:+.3f}  (|δ| = {abs(d):.3f})")
            if abs(d) > abs(PRED_REF_WAS):
                print("          자질 쪽이 더 크다 → 과거시제라는 문법 범주가 was라는")
                print("          철자보다 두 무더기를 더 잘 가른다. 06이 잡은 것은 낱말")
                print("          습관이 아니라 문법 선택이었다고 읽을 근거가 된다.")
            else:
                print("          자질 쪽이 더 작다 → was 하나가 Tense=Past 전체보다 잘")
                print("          가른다는 뜻이다. 과거시제를 통째로 묶으면 신호가 옅어지므로,")
                print("          06이 잡은 것은 '과거시제를 덜 쓴다'가 아니라 was를 부르는")
                print("          특정 문형(3인칭 서사·개인 회상)의 부재일 수 있다.")
                print("          치명 1의 진단과 어긋나지 않으나, 형태 층위로 옮겨 적을")
                print("          근거는 되지 못한다.")

    # ── 예측 5 — 1·2에 걸린 조건부 지시 ─────────────────────
    p1 = next((r for r in results if r["번호"] == 1), None)
    p2 = next((r for r in results if r["번호"] == 2), None)
    hit1 = bool(p1 and p1["판정"] == "적중")
    hit2 = bool(p2 and p2["판정"] == "적중")
    print()
    print(f"      예측 5  {PRED5_LINES[0]}")
    for ln in PRED5_LINES[1:]:
        print(f"              {ln}")
    print(f"              예측 1 {'성립' if hit1 else '불성립'} · "
          f"예측 2 {'성립' if hit2 else '불성립'}")
    if hit1 and hit2:
        print("        → 조건에 걸리지 않는다. 06의 결과는 형태 층위에서도 같은")
        print("          방향으로 재현된다 — 어휘 층위만의 현상이 아니라는 뜻이다.")
        print("          다만 이것으로 결론이 서는 것은 아니다. 08(분모 통제)과")
        print("          09(산포)를 지나야 한다.")
        verdict5 = "조건 미발동 (1·2 모두 성립)"
    else:
        print()
        print("        ■ 경고 — 예측 5의 조건이 발동했다.")
        print("          1·2가 성립하지 않았다는 것은, 06의 단어별 결과가 형태")
        print("          층위의 현상이 아니라 어휘 층위의 현상이라는 뜻이다.")
        print("          과거시제를 덜 고르는 것이 아니라 was라는 낱말을 덜 쓰는")
        print("          것이고, 3인칭을 덜 쓰는 것이 아니라 he를 덜 쓰는 것이다.")
        print()
        print("          해석을 전면 재검토해야 한다. 구체적으로:")
        print("           · '과거시제 3인칭 서사를 쓰지 않는다'는 치명 1의 요약은")
        print("             이 자료에서 형태 증거를 얻지 못했다. 원고에 그대로 쓸 수 없다.")
        print("           · 06의 δ 상위 단어들은 문법 범주가 아니라 주제·레지스터의")
        print("             표지일 가능성이 커진다. 08·09가 그 가능성을 직접 겨눈다.")
        print("           · fox8 전이(12)에서 방향이 맞아도 같은 낱말이 맞은 것이지")
        print("             같은 문법이 맞은 것이 아니다. 주장 범위를 그렇게 좁혀야 한다.")
        print("          이 경고는 예측이 빗나갔을 때 무엇을 할지 미리 적어 둔 것이다.")
        print("          지금 와서 문구를 고치는 것이 아니라, 그 약속을 실행하는 것이다.")
        verdict5 = "조건 발동 (해석 전면 재검토)"

    return {"번호": 5, "서술": PRED5_TEXT, "가족": "메타",
            "근거": "예측 1·2의 성립 여부에 걸린 조건부 지시",
            "항목": [{"자질": "예측1", "판정": "성립" if hit1 else "불성립"},
                   {"자질": "예측2", "판정": "성립" if hit2 else "불성립"}],
            "판정": verdict5}


# ════════════════════════════════════════════════════════════════════════
# [저장] JSON 한 벌
# ════════════════════════════════════════════════════════════════════════
def pack_rows(rows):
    """가족 하나를 JSON에 담을 꼴로 바꾼다. |δ| 내림차순 순서를 그대로 유지한다."""
    return {
        k: {
            "축": r["축"],
            "분모종류": r["분모종류"],
            "검정가능": r["검정가능"],
            "U": rnd(r["U"], STAT_DIGITS),
            "z": rnd(r["z"], STAT_DIGITS),
            "p": None if r["p"] is None else sig(r["p"]),
            "q": None if r["q"] is None else sig(r["q"]),
            "델타": rnd(r["델타"], STAT_DIGITS),
            "방향": r["방향"],
            "봇_중앙": rnd(r["봇_중앙"], RATE_DIGITS),
            "사람_중앙": rnd(r["사람_중앙"], RATE_DIGITS),
            "봇_유효n": r["봇_유효n"],
            "사람_유효n": r["사람_유효n"],
            "결측계정수": r["결측계정수"],
            "출현계정수": r["출현계정수"],
            "희소": r["희소"],
            "유의": r["유의"],
            "주목": r["주목"],
        }
        for k, r in rows
    }


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 74)
    print("봇 / 사람 형태 자질·품사 비교  (M 블록 — 단어를 거치지 않고 문법을 잰다)")
    print("=" * 74)

    # ── [1] 입력 ────────────────────────────────────────────────
    print("\n[1/6] 입력 적재")
    if not os.path.exists(MEASURE_JSON):
        print(f"      {MEASURE_JSON} 이(가) 없습니다.")
        print("      04_기능어측정.py 를 먼저 실행하십시오. 07은 04가 저장해 둔")
        print("      자질·UPOS·토큰수를 나누기만 하므로 그 파일이 없으면 할 일이")
        print("      없습니다. 아무것도 하지 않고 끝냅니다.")
        return
    if not os.path.exists(ACCOUNTS_JSON):
        print(f"      {ACCOUNTS_JSON} 이(가) 없습니다.")
        print("      라벨이 여기에만 있어 비교를 할 수 없습니다. 끝냅니다.")
        return

    conf, accounts = load_measurement()
    inherited = inherit_fingerprint(conf)
    print(f"      계정 {len(accounts):,}개 (04 산출물, 실행일 "
          f"{inherited['04_실행일'] or '?'})")
    print(f"      04→07 승계 — 기능어 {inherited['기능어_개수']}종 · "
          f"해시 {inherited['기능어_해시']}")
    print("      07은 기능어를 세지 않는다. 이 해시는 04 실행분의 신분증이고,")
    print("      05·06이 적어 둔 값과 같으면 세 파일이 같은 04를 읽은 것이다.")

    labels = load_labels()
    bot_ids, human_ids, missing, invalid = split_by_label(accounts, labels)
    n_all = len(bot_ids) + len(human_ids)

    line("라벨 — 07은 라벨을 아는 상태에서 수행된다")
    print("  01~05를 지켜 준 봉인은 06에서 이미 열렸다. 07에는 그 보호막이 없다.")
    print("  봉인 대신 사전등록이 그 자리를 대신한다(07-12 사전선언 결정 0-1).")
    print()
    print("  무슨 뜻인가. 07의 분모 규칙도, 판정 문턱도, 아래 [6/6]이 대조할 예측")
    print("  다섯 개도 이 스크립트를 쓰기 전에 문서에 확정되었다. 결과를 본 뒤에")
    print("  고를 여지를 미리 없앤 것이다. 봉인은 '판단할 때 라벨을 몰랐다'로")
    print("  공정성을 증명했고, 사전등록은 '판단을 라벨보다 먼저 적어 두었다'로")
    print("  증명한다. 증명 방식이 다를 뿐 막으려는 것은 같다 — 여러 갈래로")
    print("  돌려 보고 마음에 드는 것만 보고하는 일이다.")
    print()
    print(f"  봇   {len(bot_ids):>6,}계정")
    print(f"  사람 {len(human_ids):>6,}계정")
    if missing or invalid:
        print()
        print(f"  ※ 라벨 없음 {len(missing):,}계정 · "
              f"bot/human 이 아닌 값 {len(invalid):,}계정")
        print("    이들은 어느 무더기에도 넣을 수 없어 비교에서 빠집니다. 결정 2가")
        print("    금지한 '분석적 제외'가 아니라 대응할 짝이 없는 것입니다.")
        for uid in (missing + invalid)[:10]:
            print(f"      {uid[:12]}  라벨={labels.get(uid)!r}")
    if not bot_ids or not human_ids:
        print("\n■ 중단 — 한쪽 무더기가 비어 있어 비교가 성립하지 않습니다.")
        return

    # ── [2] 자가검증 ────────────────────────────────────────────
    print("\n[2/6] 자가검증")
    if not self_check():
        return

    # ── [3] 비율 계산 ───────────────────────────────────────────
    print("\n[3/6] 비율 계산 (사전선언 07의 분모 규칙)")
    compared = bot_ids + human_ids
    sub = {u: accounts[u] for u in compared}   # 라벨이 붙은 계정만 대상으로 한다

    axis_map = build_axis_map(sub)
    feat_keys = sorted({k for a in sub.values() for k in a.get("자질", {})})
    upos_keys = sorted({k for a in sub.values() for k in a.get("UPOS", {})})
    kinds = {k: denom_kind_of(k, axis_map) for k in feat_keys}

    print(f"      형태 자질 {len(feat_keys)}종 · UPOS {len(upos_keys)}종 · "
          f"축 {len(axis_map)}개")
    if len(feat_keys) != EXPECT_FEATURES or len(upos_keys) != EXPECT_UPOS:
        print(f"      ※ 04 로그의 종수(자질 {EXPECT_FEATURES} · UPOS {EXPECT_UPOS})와")
        print("        다릅니다. 04가 다른 실행분으로 바뀌었을 수 있습니다. 계산은")
        print("        계속하지만 위 해시를 05·06과 대조해 보십시오. 여기서 종수를")
        print("        맞추려고 자질을 고르지는 않습니다(사후 문턱 도입 금지).")

    ratios, aux_ratios, presence = compute_ratios(sub, feat_keys, axis_map)
    upos_ratios, upos_presence = compute_upos_ratios(sub, upos_keys)

    line("축별 분류 — 어느 자질에 어떤 분모를 쓰는가")
    print("  대립값이 둘 이상이면 그 축의 총 출현수로 나눈다(선택의 문제를 잰다).")
    print("  하나뿐이면 토큰수_구두점제외로 나눈다(축 내부 비율이 정의되지 않는다).")
    print("  축 이름을 코드에 적어 두지 않고 자료에서 유도한 결과다 — 자료가")
    print("  바뀌면 이 표도 따라 바뀐다.")
    print()
    print("      축                값종수  적용 분모            자질수  값")
    n_axis_kind = {DENOM_AXIS: 0, DENOM_TOKEN: 0}
    for ax in sorted(axis_map):
        vals = axis_map[ax]
        kind = DENOM_AXIS if len(vals) >= 2 else DENOM_TOKEN
        n_feat = sum(1 for k in feat_keys if axis_of(k) == ax)
        n_axis_kind[kind] += n_feat
        shown = ",".join(vals)
        if len(shown) > 28:
            shown = shown[:27] + "…"
        print(f"      {ax:<18}{len(vals):>4}종  {kind:<18}{n_feat:>4}종  {shown}")
    print()
    print(f"      축 내부 합을 분모로 쓰는 자질   {n_axis_kind[DENOM_AXIS]:>4}종")
    print(f"      토큰수를 분모로 쓰는 자질       {n_axis_kind[DENOM_TOKEN]:>4}종")
    print(f"      UPOS(전부 토큰수 분모)          {len(upos_keys):>4}종")

    # 결측 집계 — 분모가 0이라 나눗셈이 성립하지 않은 칸이 얼마나 되는가.
    miss_count = {k: sum(1 for u in compared if ratios[u][k] is None)
                  for k in feat_keys}
    with_miss = sorted(((n, k) for k, n in miss_count.items() if n),
                       reverse=True)
    print(f"\n      결측(분모 0) 이 있는 자질 {len(with_miss)}종 / {len(feat_keys)}종")
    if with_miss:
        print(f"      결측이 많은 순 상위 {min(MISSING_SHOW, len(with_miss))}종")
        print("        자질            결측계정   비율")
        for n, k in with_miss[:MISSING_SHOW]:
            print(f"        {k:<16}{n:>6,}계정{n / n_all:>8.1%}")
        print("\n      결측은 그 축이 한 번도 안 나온 계정이다. 나눗셈이 성립하지")
        print("      않는 것이지 값이 작은 것이 아니다. 해당 자질의 검정에서만")
        print("      빠지며 다른 자질에는 그대로 들어간다. 결측이 절반을 넘는")
        print("      자질은 남은 계정이 이미 한 번 걸러진 표본이라, δ가 커도")
        print("      '그 축을 쓴 계정들 사이의 차이'로만 읽어야 한다.")

    sparse_cut = int(n_all * SPARSE_FRAC)

    # ── [4] 형태자질 ────────────────────────────────────────────
    print(f"\n[4/6] 형태 자질 비교 — BH 가족 1 (그룹1 = {GROUP1}, 그룹2 = {GROUP2})")
    feat_rows, feat_m = compare_family(feat_keys, bot_ids, human_ids,
                                       ratios, presence, sparse_cut, kinds)
    notable_feat = family_summary(feat_rows, feat_m, sparse_cut, n_all,
                                  "형태자질")
    if notable_feat:
        print_feature_table(notable_feat, f"주목 자질 {len(notable_feat)}종 중 "
                            f"|δ| 상위 {min(TOP_SHOW, len(notable_feat))}종",
                            TOP_SHOW)
        rest = len(notable_feat) - min(TOP_SHOW, len(notable_feat))
        if rest > 0:
            print(f"\n      … 이 밖에 {rest}종이 더 주목 목록에 있다(생략).")
            print("        전체는 07_형태자질비교.json 의 주목자질 에 같은 순서로 있다.")
    else:
        print("\n      주목 자질이 없습니다.")
        print("      q ≤ 0.05 와 |δ| ≥ 0.147 을 함께 넘은 자질이 하나도 없다는 뜻입니다.")
        print("      06에서 단어별로 94종이 걸렸는데 자질에서 하나도 안 걸린다면,")
        print("      그 차이가 문법 범주에 실려 있지 않다는 강한 신호입니다.")
    untested = [(k, r) for k, r in feat_rows if not r["검정가능"]]
    if untested:
        print(f"\n      검정 불가 {len(untested)}종 — BH 가족에서 빠진 자질")
        for k, r in untested:
            print(f"        {k:<16}유효 봇 {r['봇_유효n']:>5,} · "
                  f"사람 {r['사람_유효n']:>5,}")
        print("        결측을 걷어 내니 한쪽 무더기가 통째로 비었다. 견줄 것이 없어")
        print("        δ도 p도 내지 않았다. 값이 작아서 뺀 것이 아니라 값이 아예 없다.")
        print("        한쪽 라벨에서만 그 축이 나타난다는 사실 자체는 결과다 —")
        print("        검정으로는 잡히지 않으니 08에서 라벨과 교차해 다시 보라.")

    print(f"\n      '희소' = 이 자질이 나온 계정이 {sparse_cut:,}개 미만"
          f"(전체의 {SPARSE_FRAC:.0%}) 이라는 표시다.")
    print("      표시만 하고 빼지 않는다(사전선언 07). 두 무더기가 거의 다 0인")
    print("      상태에서 나온 δ라 값이 커도 몇 계정의 우연에 좌우된다.")

    # ── [5] UPOS ────────────────────────────────────────────────
    print("\n[5/6] UPOS 비교 — BH 가족 2 (별도 보정)")
    print("      형태자질과 다른 가족이다. q값을 따로 계산했으므로 위 표의 q와")
    print("      아래 표의 q는 서로 다른 m으로 나온 값이다. 한 표에 섞어 정렬하면")
    print("      안 된다(사전선언 07: 두 가족에 각각 별도로 BH 보정).")
    upos_rows, upos_m = compare_family(upos_keys, bot_ids, human_ids,
                                       upos_ratios, upos_presence, sparse_cut)
    notable_upos = family_summary(upos_rows, upos_m, sparse_cut, n_all, "UPOS")
    print_feature_table(upos_rows, f"UPOS {len(upos_rows)}종 전부 (|δ| 내림차순)")
    print("\n      PUNCT 줄만은 눈금이 다르다. 분모가 구두점을 뺀 토큰수인데 분자는")
    print("      구두점 수라, '말 토큰 대비 구두점'이라는 다른 뜻의 값이 된다.")
    print("      구두점 습관은 R 블록(리듬)이 다룰 신호다 — 여기서 해석하지 않는다.")

    # ── [6] 사전 예측 대조 ──────────────────────────────────────
    print("\n[6/6] 사전 예측 대조")
    pred_results = [check_prediction(p, feat_rows, upos_rows) for p in PREDICTIONS]
    pred5 = print_prediction_block(pred_results)
    pred_results.append(pred5)

    hit = sum(1 for r in pred_results[:-1] if r["판정"] == "적중")
    print()
    print(f"      요약 — 예측 4개 중 {hit}개 적중, "
          f"{len(pred_results) - 1 - hit}개 빗나감/판정불가")
    print(f"             예측 5 : {pred5['판정']}")

    # ── 저장 ────────────────────────────────────────────────────
    line("저장")
    method = (
        "자질·품사별 Mann-Whitney U 검정(양측). 동점은 평균 순위로 처리하고, "
        "정규근사 분산에 동점 보정 항 Σ(t³−t)/(N(N−1))을 넣었으며, "
        "z에 연속성 보정 0.5를 적용했다. "
        "효과크기는 Cliff's δ = 2U/(n1·n2) − 1 (그룹1 = bot 기준). "
        f"다중비교는 Benjamini-Hochberg FDR, q = {Q_ALPHA}. "
        f"형태자질 {feat_m}종과 UPOS {upos_m}종을 별개의 가족으로 두고 각각 "
        "따로 보정했다(검정 불가 항목은 p가 없어 가족에서 빠졌다). "
        f"주목 = q ≤ {Q_ALPHA} 그리고 |δ| ≥ {DELTA_NOTABLE}. "
        "구현은 06_봇사람비교.py 의 검정 함수를 그대로 가져왔다 — "
        "사전선언 07의 '06과 완전히 동일'을 같은 코드로 지켰다."
    )
    denom_rule = (
        "대립값이 2개 이상인 축의 자질은 그 계정의 해당 축 총 출현수로 나눈다 "
        "(예: Tense=Past ÷ (Tense=Past + Tense=Pres)). '시제를 표시한 것 중 "
        "과거를 얼마나 골랐나'를 재기 위함이며, 전체 토큰을 분모로 하면 "
        "'동사를 얼마나 쓰나'가 섞여 들어와 선택의 문제와 사용량의 문제가 "
        "뒤엉킨다. 대립값이 하나뿐인 자질과 UPOS 17종은 토큰수_구두점제외로 "
        "나눈다. 축 판별은 하드코딩하지 않고 자료 전체에서 유도했다. "
        "분모 0은 결측으로 두고 그 자질의 검정에서만 뺐다(분석적 제외가 아니라 "
        "나눗셈 불성립). 분모에 최소 문턱을 두지 않았다. 사전선언 07."
    )
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "방법": method,
            "분모규칙": denom_rule,
            "그룹1": GROUP1,
            "그룹2": GROUP2,
            "n_bot": len(bot_ids),
            "n_human": len(human_ids),
            "라벨결측": len(missing) + len(invalid),
            "라벨_사용": "07은 라벨을 아는 상태에서 수행된다. 봉인 대신 "
                      "사전등록이 그 자리를 대신한다(07-12 사전선언 결정 0-1).",
            "BH가족": {"형태자질": feat_m, "UPOS": upos_m,
                     "비고": "두 가족에 각각 별도로 보정했다. 서로 다른 m에서 "
                            "나온 q이므로 두 표의 q를 한 줄로 세워 비교하면 안 된다."},
            "희소기준": f"출현 계정이 {sparse_cut:,}개 미만"
                     f"(비교 대상 {n_all:,}계정의 {SPARSE_FRAC:.0%}). "
                     "표시만 하고 제외하지 않는다(사전선언 07).",
            "보조_전체토큰기준_비고":
                "모든 형태 자질을 토큰수_구두점제외로 나눈 값의 그룹별 중앙값이다. "
                "판정에 쓰지 않는다 — 참고 기록이다(사전선언 07). "
                "UPOS는 본 비율이 이미 이 눈금이라 따로 담지 않았다.",
            "04승계": inherited,
            "사전예측_대조": pred_results,
        },
        # 축 판별 결과. 분모 규칙이 어떻게 적용되었는지가 이 표에 다 들어 있다.
        "축분류": {
            ax: {"값종수": len(vals),
                 "값목록": vals,
                 "분모종류": DENOM_AXIS if len(vals) >= 2 else DENOM_TOKEN,
                 "자질수": sum(1 for k in feat_keys if axis_of(k) == ax)}
            for ax, vals in sorted(axis_map.items())
        },
        # 두 가족 모두 |δ| 내림차순. 파일을 열면 큰 것부터 보인다.
        "형태자질": pack_rows(feat_rows),
        "UPOS": pack_rows(upos_rows),
        # 주목 목록은 가족을 표시해 함께 담는다 — 화면에 띄운 순서 그대로다.
        "주목자질": (
            [{"가족": "형태자질", "자질": k, "델타": round(r["델타"], STAT_DIGITS),
              "방향": r["방향"], "q": sig(r["q"]), "희소": r["희소"]}
             for k, r in notable_feat]
            + [{"가족": "UPOS", "자질": k, "델타": round(r["델타"], STAT_DIGITS),
                "방향": r["방향"], "q": sig(r["q"]), "희소": r["희소"]}
               for k, r in notable_upos]
        ),
        # 판정 미사용. 전체 토큰을 분모로 했을 때의 중앙값만 남긴다.
        "보조_전체토큰기준": {
            k: {"봇_중앙": rnd(_median_defined(bot_ids, aux_ratios, k), RATE_DIGITS),
                "사람_중앙": rnd(_median_defined(human_ids, aux_ratios, k), RATE_DIGITS)}
            for k in feat_keys
        },
    }
    write_json(OUT_JSON, out, indent=1)
    print(f"      {OUT_JSON}")
    print(f"      {os.path.getsize(OUT_JSON):,} bytes")

    # ── 눈으로 검수할 것 ────────────────────────────────────────
    line("확인 항목")
    print("  아래를 직접 보고 나서 08로 넘어가십시오.")
    print("   1. 사전 예측이 몇 개 적중했고, 빗나간 것은 무엇을 뜻하는가. 적중은")
    print("      06의 결과가 문법 층위에서도 재현된다는 뜻이고, 빗나감은 06이 잡은")
    print("      것이 낱말 습관이었다는 뜻이다. 특히 예측 1(Tense=Past)과 2(Person)는")
    print("      치명 1의 진단을 직접 겨눈 것이라, 여기서 빗나가면 원고의 해석")
    print("      문단을 통째로 다시 써야 한다. 적중한 것만 골라 쓰지 말라 —")
    print("      다섯 개를 미리 적어 둔 이유가 그것이다.")
    print("   2. 자질의 |δ|가 06의 단어 |δ|보다 큰가. 크면 형태 쪽이 더 깨끗한")
    print("      측정이다 — 같은 문법을 여러 철자로 쓰는 사람들이 단어 표에서는")
    print("      흩어져 있다가 자질 표에서 한 줄로 모였다는 뜻이다. 작으면 반대다.")
    print("      묶었더니 신호가 옅어졌다면, 그 신호를 만든 것은 문법 범주가 아니라")
    print("      그 안의 특정 낱말이다. 06의 was(−0.718)를 기준선으로 삼아라.")
    print("   3. 결측이 많은 자질을 확인하라. 결측이 절반을 넘는 자질에서 나온 δ는")
    print("      '그 축을 쓴 계정들' 사이의 차이일 뿐이고, 그 계정들이 어느 라벨에")
    print("      몰려 있는지는 이 표가 답하지 않는다. 결측 자체가 신호일 수 있다 —")
    print("      '그 축을 아예 안 쓴다'는 것도 문체다. 08에서 다시 볼 값이다.")
    print("   4. UPOS 결과가 06의 단어 결과와 정합하는가. 06에서 the(+0.603)·")
    print("      of(+0.524)가 봇 쪽으로 높았으니 DET·ADP도 같은 방향이어야 하고,")
    print("      i(−0.576)·he(−0.699)가 낮았으니 PRON도 낮아야 한다. 어긋난다면")
    print("      둘 중 하나가 다른 것을 재고 있다는 뜻이다. 예를 들어 the는 높은데")
    print("      DET 전체는 낮다면, 봇이 늘리는 것은 한정사 일반이 아니라 정관사")
    print("      하나뿐이라는 말이 된다 — 훨씬 좁고 훨씬 덜 문법적인 주장이다.")
    print("   5. 여기서 결론을 내지 말라. 07은 06과 같은 자료를 다른 각도로 본")
    print("      것이고, 두 결과가 공유하는 약점 — 분모가 봇 쪽이 2.28배 크다는")
    print("      사실 — 은 아직 손대지 않았다. 08(분모 통제)과 09(산포)를 지나야")
    print("      한다. 특히 09가 겨누는 산포 신호는 위치 신호보다 크다고 이미")
    print("      확인되었다. 이 표만 보고 결론을 쓰면 큰 쪽을 놓친다.")
    print()
    print("  이 다섯은 스크립트가 대신 판정할 수 없는 것들이다. δ와 q를 뽑는")
    print("  일까지가 코드의 몫이고, 그 숫자가 무슨 이야기인지는 사람이 읽는다.")
    print("  방법과 예측은 사전선언에 미리 못 박혀 있다 — 결과를 보고 문턱이나")
    print("  분모를 손보는 순간, 라벨을 아는 상태에서 이 비교를 했다는 사실을")
    print("  방어할 근거가 사라진다.")


def _median_defined(uids, ratios, key):
    """보조값의 그룹별 중앙값. 결측은 빼고 센다. 값이 하나도 없으면 None."""
    vals = [ratios[u][key] for u in uids if ratios[u][key] is not None]
    return statistics.median(vals) if vals else None


if __name__ == "__main__":
    main()
