#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
02-1_임계값민감도.py
────────────────────────────────────────────────────────────────────────────
목적
    06이 찾아낸 94종의 주목 단어가 '기능어 목록을 어떻게 골랐느냐'에 기대고
    있는 것은 아닌지 확인한다. 02는 기능어를 두 문턱으로 뽑았다 — UD
    English-EWT에서 빈도 5회 이상이고, 닫힌 어류로 태그된 비율이 0.5 이상.
    둘 다 관례적인 값이고, 다르게 잡을 이유도 그만큼 있었다. 그 선택이
    결과를 만들었다면 06의 172종·94종은 목록을 손보는 것만으로 흔들린다.

왜 이 검사가 필요한가
    기능어 목록은 이 파이프라인에서 사람이 손댄 몇 안 되는 자리 중 하나다.
    02는 라벨을 보기 전에 목록을 확정했으므로 결과를 보고 고른 것은 아니다.
    그러나 '결과를 보고 고르지 않았다'와 '어떻게 골라도 같은 결과가 난다'는
    다른 말이다. 앞의 것은 공정성이고 뒤의 것은 강건성이다. 02-1이 재는 것은
    뒤쪽이다.

무엇을 하는가
    04-1이 만들어 둔 아홉 벌의 변형 목록 — (빈도 3·5·10) × (닫힌비율
    0.4·0.5·0.6) — 을 그대로 가져와, 목록마다 06과 똑같은 F 비교를 다시
    돌린다. 계정별 사용률은 04-1의 표면형 카운터와 구두점 제외 토큰수로 새로
    만들고, U·δ·BH는 06의 함수를 AST로 복사해 쓴다. 변형마다 BH 가족은
    그 목록의 크기다(보관된 13-19 사전선언의 15항(현 02-1)).

    여기서 δ 자체는 목록에 따라 변하지 않는다는 점을 미리 알아 두는 편이
    좋다. 한 단어의 사용률은 그 단어의 횟수를 구두점 제외 토큰수로 나눈
    값이고, 두 수 모두 어느 목록에 들었는지와 무관하다. 목록이 바꾸는 것은
    ① 어떤 단어가 표에 오르는가 ② BH 가족이 몇 종인가, 이 둘뿐이다. 그래서
    이 단계가 실제로 묻는 것은 "δ가 흔들리는가"가 아니라 "문턱을 옮기면
    다른 단어가 들어오고 그 바람에 판정이 달라지는가"다.

무엇을 따르나
    보관된 13-19_사전선언.md 「15 기능어 목록 임계값 민감도」(현 02-1)를 그대로 구현한다.
    문턱(q ≤ 0.05, |δ| ≥ 0.147)은 06 그대로 두고 바꾸지 않는다. 사전선언에
    없는 검정은 하나도 더 돌리지 않는다.

라벨을 어디서 읽나
    ■ 이 파일은 01_적격계정.json 의 "라벨" 키를 읽는다. ■
    04-1은 라벨을 읽지 않았다(04와 같은 규율). 02-1은 봇·사람을 갈라야 비교가
    성립하므로 라벨을 연다. 다만 여는 자리를 load_labels() 한 곳으로 묶고,
    그 밖에서는 라벨이 든 객체를 들고 다니지 않는다.

실행
    cd "연구주제/단계별 진행경과" && python3 -u 02-1_임계값민감도.py
    표준 라이브러리만 쓴다. 검정은 정렬과 사칙연산뿐이라 몇 초면 끝난다.

선행 조건
    같은 폴더에 04-1_확장재파싱.json · 01_적격계정.json · 05_사용률검수.json ·
    06_비교결과.json 이 있어야 한다. 04-1이 정합 관문을 통과했는지도 여기서
    확인한다 — 통과하지 못한 04-1 위에서 02-1을 돌리면 아무 뜻이 없다.

산출
    02-1_임계값민감도.json    변형 아홉 벌의 단어별 U·z·p·q·δ + 요약 + 예측 판정
    02-1_임계값민감도_출력.log  이 화면 그대로
"""

import ast
import hashlib
import json
import math
import os
import platform
import statistics
import sys
import time


# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
HERE = os.path.dirname(os.path.abspath(__file__))
EXT_JSON = f"{HERE}/04-1_확장재파싱.json"        # 주 입력 — 표면형 카운터·변형 목록
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"       # "라벨" 키만 꺼낸다
RATES_JSON = f"{HERE}/05_사용률검수.json"        # 사용률 규칙·해시 사슬
COMPARE_JSON = f"{HERE}/06_비교결과.json"        # 정합 관문 대조 상대
COMPARE_PY = f"{HERE}/06_봇사람비교.py"          # 통계 함수의 원본

OUT_JSON = f"{HERE}/02-1_임계값민감도.json"

GROUP1, GROUP2 = "bot", "human"
# 06과 같은 순서로 못 박는다. δ > 0 이면 봇이 높음, δ < 0 이면 봇이 낮음.
# 이 두 줄이 뒤집히면 아홉 표의 부호가 통째로 반대가 된다.

Q_ALPHA = 0.05          # BH 보정 후 유의 문턱 — 06 그대로
DELTA_NOTABLE = 0.147   # 주목 단어의 효과크기 하한 — 06 그대로
SPARSE_FRAC = 0.10      # 출현 계정이 이 비율 미만이면 '희소' 표시 — 06 그대로

RATE_DIGITS = 6         # 사용률 저장·비교 자릿수 — 05가 쓴 눈금이다(아래 설명)
STAT_DIGITS = 4         # U·z·δ 저장 자릿수 — 06과 같다
SIG_DIGITS = 6          # p·q는 유효숫자로 자른다 — 06의 sig()가 참조한다

# ── 보관된 13-19 사전선언의 15항(현 02-1)이 지목한 머리 낱말 다섯 ─────────
HEAD5 = ("we", "must", "our", "was", "he")

# ── 예측의 문턱 (보관된 13-19 사전선언의 15항(현 02-1) 그대로) ────────────
NOTABLE_BAND = (0.40, 0.70)   # P15-2 주목 비율이 들어야 할 구간
SIZE_TOL = 0.20               # P15-3 같은 빈도 안에서 허용되는 크기 변동

# ── 해시 사슬 (사전선언 공통) ───────────────────────────────────
EXPECTED_FW_HASH = "382b68572f03bc23"   # 기능어 172종 해시 — 05가 적어 둔 값
# 이 해시는 기준선 변형(f5_r0.50)의 목록 해시와도 같아야 한다. 04-1이 02의
# 절차로 다시 만든 목록이 02의 원본과 글자까지 같다는 뜻이 되기 때문이다.

# ── 06에서 AST로 복사해 온 함수들 ───────────────────────────────
COPIED_NAMES = ["normal_cdf", "ranks_with_ties", "mann_whitney",
                "bh_qvalues", "quartiles", "sig", "direction_of"]
COPIED_HASH = "b3de6ef352db03a1"    # 위 7개 소스를 이 순서로 이은 sha256 앞 16자
# 04-1이 적어 둔 값과 같다. 같은 함수를 같은 순서로 떴으니 같아야 한다.

# ── 자가검증 고정 예제 ───────────────────────────────────────────
# (1) 06의 세 예제. 손계산은 06_봇사람비교.py의 self_check() docstring에 있다.
SELF_CHECK_U = [
    ("완전 분리", [1, 2, 3], [4, 5, 6], 0.0, -1.0, 5.25),
    ("동점 포함", [1, 1, 2], [1, 2, 2], 3.0, -1.0 / 3.0, 4.05),
]
SELF_CHECK_BH_P = [0.01, 0.02, 0.03, 0.04]
SELF_CHECK_BH_Q = [0.04, 0.04, 0.04, 0.04]
SELF_CHECK_TOL = 1e-9

# (2) 02-1의 사용률 규칙 예제 — 분모·희소 저장·반올림 세 가지를 한꺼번에 본다.
#     계정 X  분모 400, {"we": 12, "the": 33}
#            we  = 12/400 = 0.03        the = 33/400 = 0.0825
#            must는 카운터에 키가 없다  → 0.0 (쓰지 않은 것이지 결측이 아니다)
#     계정 Y  분모 3, {"we": 1}   → 1/3 = 0.333333… → 여섯 자리로 0.333333
#     계정 Z  분모 7, {"we": 2}   → 2/7 = 0.285714… → 여섯 자리로 0.285714
GATE2_ACCOUNTS = {
    "X": {"토큰수_구두점제외": 400, "표면형_합집합": {"we": 12, "the": 33}},
    "Y": {"토큰수_구두점제외": 3, "표면형_합집합": {"we": 1}},
    "Z": {"토큰수_구두점제외": 7, "표면형_합집합": {"we": 2}},
}
GATE2_EXPECT = {
    ("X", "we"): 0.03, ("X", "the"): 0.0825, ("X", "must"): 0.0,
    ("Y", "we"): 0.333333, ("Z", "we"): 0.285714,
}

# (3) BH 가족 크기 규칙 예제 — 가족이 '목록 크기'라는 것을 눈으로 확인한다.
#     봇 세 계정의 we 사용률 0.01 0.02 0.03, 사람 세 계정 0.04 0.05 0.06.
#     06의 예제 1과 같은 모양이라 U = 0, δ = −1 이 나와야 한다.
#     목록에는 어느 계정에도 없는 단어 "zzz"를 하나 끼워 둔다 — 두 무더기가
#     모두 0이라 분산이 0이고, 06의 규칙대로 δ = 0, p = 1.0 자리로 간다.
#     그래도 목록에 든 이상 BH 가족에는 들어가므로 m = 2 다.
GATE3_BOT = {"b1": {"토큰수_구두점제외": 100, "표면형_합집합": {"we": 1}},
             "b2": {"토큰수_구두점제외": 100, "표면형_합집합": {"we": 2}},
             "b3": {"토큰수_구두점제외": 100, "표면형_합집합": {"we": 3}}}
GATE3_HUMAN = {"h1": {"토큰수_구두점제외": 100, "표면형_합집합": {"we": 4}},
               "h2": {"토큰수_구두점제외": 100, "표면형_합집합": {"we": 5}},
               "h3": {"토큰수_구두점제외": 100, "표면형_합집합": {"we": 6}}}
GATE3_LIST = ["we", "zzz"]


def line(title=""):
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다(04·05·06·04-1의 같은 함수).

    임시 파일에 먼저 쓰고 이름을 바꿔치기한다(os.replace). 쓰는 도중에 멈춰도
    파일은 '이전 것' 아니면 '새 것'이지, 반쯤 잘린 것이 되지 않는다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def list_hash(words):
    """목록 하나의 지문. 04-1·02가 쓴 방식과 같다(줄바꿈으로 이어 sha256 앞 16자)."""
    return hashlib.sha256("\n".join(words).encode("utf-8")).hexdigest()[:16]


# ════════════════════════════════════════════════════════════════════════
# [승계] 06에서 AST로 복사한 통계 함수 — 아래 7개는 06의 소스 그대로다
# ════════════════════════════════════════════════════════════════════════
# 손으로 옮겨 적지 않았다. ast 모듈로 06_봇사람비교.py를 파싱해 함수 정의의
# 소스 조각을 그대로 떠 왔고, 실행할 때마다 verify_copied_functions()가 06의
# 원본과 이 파일의 사본을 다시 떠서 해시를 맞춘다. 04-1도 같은 일곱 함수를 같은
# 순서로 떠 두었으므로 세 파일(06·04-1·02-1)의 해시가 모두 b3de6ef352db03a1 이다.
# 이 셋이 어긋나면 "같은 자로 재고 있다"는 주장이 그 자리에서 무너진다.
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
    06의 원본과 이 파일의 사본이 글자까지 같은지 확인한다(04-1과 같은 방식).

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
def load_extended():
    """04-1 산출물을 통째로 가져온다 — 설정·변형목록·합집합·관찰·계정."""
    return json.load(open(EXT_JSON, encoding="utf-8"))


def load_labels():
    """
    01에서 "라벨" 키 하나만 꺼낸다. 06의 같은 함수와 같은 규율이다.

    ■ 라벨을 여는 자리는 이 함수 하나다. ■ 04-1은 이 키를 읽지 않았고, 02-1은
    봇·사람을 갈라야 하므로 읽는다. 원문("계정")·언어판정·깔때기 통계는
    필요 없으므로 그 자리에서 버린다 — 23MB를 이고 다닐 이유도 없고, 없는
    것은 실수로 참조할 수도 없다.
    """
    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    labels = data.get("라벨") or {}
    del data
    return labels


def load_rate_rules():
    """05 JSON의 설정에서 분모 정의와 승계 해시를 읽어 온다."""
    conf = json.load(open(RATES_JSON, encoding="utf-8"))["설정"]
    return {"05_실행일": conf.get("실행일"),
            "분모_정의": conf.get("분모_정의"),
            "04승계": conf.get("04승계", {})}


def split_by_label(uids, labels):
    """
    계정을 라벨에 따라 두 무더기로 가른다(06의 split_by_label과 같은 규칙).

    라벨이 없거나 bot/human이 아닌 계정은 비교에서 빠진다. 사전선언 결정 2가
    금지한 '분석적 제외'가 아니라 대응할 짝이 없는 것이다. 01이 1,869계정
    전원에 라벨을 달아 두었으므로 실제로는 나올 일이 아니다.
    """
    bot, human, missing, invalid = [], [], [], []
    for uid in sorted(uids):
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
# [2] 사용률 — 05와 같은 분모, 05와 같은 눈금
# ════════════════════════════════════════════════════════════════════════
def build_rates(accounts):
    """
    계정별 표면형 사용률을 만든다.

        사용률(w) = 그 계정에서 w가 나온 횟수 ÷ 그 계정의 구두점 제외 토큰수

    분모를 왜 구두점 제외로 잡나. 05가 그렇게 잡았고(사전선언 결정 1), 02-1은
    06과 견주기 위한 단계라 같은 분모를 써야 한다. 구두점을 분모에 넣으면
    "구두점을 적게 찍는 계정"이 모든 기능어에서 높게 나온다 — 기능어 신호와
    구두점 습관이 뒤섞인다.

    ■ 왜 여섯 자리로 반올림하나 ■
    05가 사용률을 소수 여섯 자리로 저장했고 06은 그 값을 읽어 순위를 매겼다.
    여기서 반올림 없이 원 실수를 쓰면 05에서 같은 값으로 뭉쳤던 계정 쌍이
    갈라지면서 동점 묶음이 달라지고, 순위 검정의 δ가 소수 넷째 자리에서
    어긋난다(실측 172종 중 7종에서 0.0001 차이). 문턱을 옮기지는 않지만
    "기준선은 06과 같은 수가 나와야 한다"는 정합 관문이 그 자리에서 흔들린다.
    05의 눈금을 그대로 쓰는 것이 05·06과 같은 자를 쓴다는 뜻이므로 여기서도
    RATE_DIGITS = 6 으로 자른다. 이것은 방법의 변경이 아니라 05 규칙의 승계다.

    희소 저장은 04-1이 이미 하고 있다 — 한 번도 안 쓴 표면형은 그 계정의
    카운터에 키가 아예 없다. 그래서 아래 word_vector()의 기본값 0.0이
    반드시 있어야 한다. 06의 같은 자리에 붙어 있던 경고와 같은 이야기다.
    """
    rates = {}
    for uid, a in accounts.items():
        denom = a["토큰수_구두점제외"]
        if denom <= 0:
            rates[uid] = {}
            continue
        rates[uid] = {w: round(n / denom, RATE_DIGITS)
                      for w, n in a["표면형_합집합"].items()}
    return rates


def word_vector(uids, rates, word):
    """
    한 단어에 대해, 주어진 계정들의 사용률을 순서대로 늘어놓는다.

    ■ 06에서 가장 틀리기 쉬운 한 줄이라고 적혀 있던 그 줄이다. ■
    .get(word, 0.0) 의 기본값 0.0이 반드시 있어야 한다. 없는 키를 건너뛰면
    "그 단어를 한 번도 안 쓴 계정"이 통째로 표본에서 사라지고, 남는 것은
    그 단어를 쓴 계정들끼리의 비교가 된다. 정작 재려던 '덜 쓴다'가 바로
    그 사라진 0들이다.
    """
    return [rates[u].get(word, 0.0) for u in uids]


def presence_count(uids, rates, word):
    """이 단어가 한 번이라도 나온 계정의 수. 06의 '출현계정수'와 같은 뜻이다."""
    return sum(1 for u in uids if rates[u].get(word, 0.0) > 0.0)


# ════════════════════════════════════════════════════════════════════════
# [3] 한 벌의 목록에 대한 F 비교 — 06과 같은 절차
# ════════════════════════════════════════════════════════════════════════
def compare_list(words, bot_ids, human_ids, rates):
    """
    목록 하나를 받아 단어별로 U·δ를 내고, 그 목록 크기를 가족으로 BH를 건다.

    ■ 가족의 크기가 목록의 크기다 ■ — 보관된 13-19 사전선언의 15항(현 02-1)이 그렇게 못 박았다.
    변형마다 목록이 155종에서 191종까지 오가므로 가족도 함께 움직인다.
    가족을 172로 고정해 두면 목록이 작은 변형에서 부당하게 가혹해지고,
    목록이 큰 변형에서는 관대해진다. 문턱을 옮기는 것이 아니라, 문턱이
    적용되는 단위를 목록에 맞추는 것이다.

    어느 계정에서도 나오지 않은 단어도 가족에 넣는다. 두 무더기가 모두 0이면
    mann_whitney가 분산 0을 만나 δ = 0, p = 1.0 을 돌려주는데(06의 규칙),
    그 자리를 빼 버리면 가족 크기가 목록 크기와 달라진다. 검정이 성립하지
    않는 것과 가족에서 빠지는 것은 다른 일이다.

    반환: {단어: 결과 사전} — |δ| 내림차순이 아니라 목록 순서를 유지한다.
          (표를 띄울 때만 정렬한다. JSON은 사전이라 순서가 뜻을 갖지 않는다.)
    """
    out = {}
    for w in words:
        v1 = word_vector(bot_ids, rates, w)
        v2 = word_vector(human_ids, rates, w)
        r = mann_whitney(v1, v2)
        r["방향"] = direction_of(r["델타"])
        r["봇_중앙"] = statistics.median(v1)
        r["사람_중앙"] = statistics.median(v2)
        r["출현계정수"] = (presence_count(bot_ids, rates, w)
                       + presence_count(human_ids, rates, w))
        out[w] = r

    qs = bh_qvalues([out[w]["p"] for w in words])
    for w, q in zip(words, qs):
        out[w]["q"] = q
        out[w]["유의"] = q <= Q_ALPHA
        out[w]["주목"] = out[w]["유의"] and abs(out[w]["델타"]) >= DELTA_NOTABLE
    return out


def pack_word(r, sparse_cut):
    """JSON에 넣을 모양으로 자릿수를 맞춘다. 06이 저장한 눈금과 같다."""
    return {
        "U": round(r["U"], 1),
        "z": round(r["z"], STAT_DIGITS),
        "p": sig(r["p"]),
        "q": sig(r["q"]),
        "델타": round(r["델타"], STAT_DIGITS),
        "방향": r["방향"],
        "봇_중앙": round(r["봇_중앙"], RATE_DIGITS),
        "사람_중앙": round(r["사람_중앙"], RATE_DIGITS),
        "출현계정수": r["출현계정수"],
        "희소": r["출현계정수"] < sparse_cut,
        "유의": r["유의"],
        "주목": r["주목"],
    }


# ════════════════════════════════════════════════════════════════════════
# [자가검증] 세 관문 — 하나라도 실패하면 본 계산에 들어가지 않는다
# ════════════════════════════════════════════════════════════════════════
def gate_1_statistics():
    """
    관문 1 — 06에서 복사한 U·δ·BH가 손계산과 맞는가.

    06의 self_check()가 쓰던 세 예제 그대로다. 손계산은 06의 docstring에 있다.
        예제 1 완전 분리  A=[1,2,3] B=[4,5,6] → U_A=0, δ=−1, σ²=5.25
        예제 2 동점 포함  A=[1,1,2] B=[1,2,2] → U_A=3, δ=−1/3, σ²=4.05
        예제 3 BH        p=[.01,.02,.03,.04] → q=[.04,.04,.04,.04]
    """
    print("\n  ── 관문 1. 06의 통계 함수 (완전 분리 · 동점 포함 · BH) ──")
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


def gate_2_rates():
    """
    관문 2 — 사용률 규칙(손으로 푼 예제). 분모·희소 저장·반올림 셋을 함께 본다.

        계정 X  분모 400, {"we": 12, "the": 33}
            we   = 12 / 400 = 0.03
            the  = 33 / 400 = 0.0825
            must → 카운터에 키가 없다. 0.0 이어야 한다.
                   여기서 키를 건너뛰면 그 계정이 표본에서 사라진다.
        계정 Y  분모 3, {"we": 1}  → 1/3 = 0.3333333… → 0.333333 (여섯 자리)
        계정 Z  분모 7, {"we": 2}  → 2/7 = 0.2857142… → 0.285714 (여섯 자리)

    Y와 Z를 넣은 이유는 반올림이 실제로 걸리는지 보기 위해서다. 05가 여섯
    자리로 저장했으므로 02-1도 여섯 자리로 잘라야 06과 같은 순위가 나온다.
    """
    print("\n  ── 관문 2. 사용률 규칙 (분모 · 희소 저장 · 여섯 자리) ──")
    rates = build_rates(GATE2_ACCOUNTS)
    ok = True
    for (uid, w), expect in GATE2_EXPECT.items():
        actual = rates[uid].get(w, 0.0)
        good = abs(actual - expect) <= SELF_CHECK_TOL
        ok = ok and good
        note = "  ← 카운터에 없는 단어" if w not in GATE2_ACCOUNTS[uid]["표면형_합집합"] else ""
        print(f"    {uid}·{w:<5} 기대 {expect:>10.6f} · 실제 {actual:>10.6f} "
              f"{'통과' if good else '실패'}{note}")
    vec = word_vector(["X", "Y", "Z"], rates, "we")
    good = vec == [0.03, 0.333333, 0.285714]
    ok = ok and good
    print(f"    벡터 we  기대 [0.03, 0.333333, 0.285714]")
    print(f"             실제 {vec}  {'통과' if good else '실패'}")
    vec2 = word_vector(["X", "Y", "Z"], rates, "must")
    good = vec2 == [0.0, 0.0, 0.0] and len(vec2) == 3
    ok = ok and good
    print(f"    벡터 must 기대 [0.0, 0.0, 0.0] (세 자리가 다 남아야 한다)")
    print(f"             실제 {vec2}  {'통과' if good else '실패'}")
    return ok


def gate_3_family():
    """
    관문 3 — BH 가족의 크기가 '목록 크기'인가(손으로 푼 예제).

    봇 세 계정의 we 사용률이 0.01·0.02·0.03, 사람 세 계정이 0.04·0.05·0.06
    이다. 분모를 100으로 맞춰 두었으니 카운트 1,2,3 / 4,5,6 이 그대로
    사용률이 된다. 이 배치는 06의 예제 1과 같은 모양이라
        U = 0,  δ = −1.0
    이 나와야 한다. z = (0 − 4.5 + 0.5) / √5.25 = −4 / 2.291288 = −1.745743,
    양측 p = 2(1 − Φ(1.745743)) ≈ 0.08085.

    목록에는 어느 계정에도 없는 단어 "zzz"를 끼워 두었다. 두 무더기가 모두
    0.0이라 분산이 0이고, 06의 규칙대로 δ = 0, p = 1.0 자리로 간다. 그래도
    목록에 든 이상 가족에는 들어가므로 m = 2 다.

    m = 2 일 때 BH는
        q(we)  = min(1.0, p_we × 2 / 1) = 2 p_we ≈ 0.16170
        q(zzz) = min(1.0, 1.0 × 2 / 2)  = 1.0
    이다. 만약 가족을 목록 크기가 아니라 172로 고정했다면
        q(we) = min(1.0, p_we × 172 / 1) = 1.0
    이 되어 주목 단어가 하나도 남지 않는다. 아래에서 그 반사실을 나란히
    찍어 두는 이유가 그것이다 — 가족 크기를 잘못 잡으면 표가 조용히 빈다.
    """
    print("\n  ── 관문 3. BH 가족 = 목록 크기 (손으로 푼 예제) ──")
    fake = dict(GATE3_BOT)
    fake.update(GATE3_HUMAN)
    rates = build_rates(fake)
    ok = True

    v1 = word_vector(sorted(GATE3_BOT), rates, "we")
    v2 = word_vector(sorted(GATE3_HUMAN), rates, "we")
    good = (v1 == [0.01, 0.02, 0.03] and v2 == [0.04, 0.05, 0.06])
    ok = ok and good
    print(f"    사용률 봇 {v1} · 사람 {v2}  {'통과' if good else '실패'}")

    res = compare_list(GATE3_LIST, sorted(GATE3_BOT), sorted(GATE3_HUMAN), rates)
    for w, key, expect in (("we", "U", 0.0), ("we", "델타", -1.0),
                           ("zzz", "델타", 0.0), ("zzz", "p", 1.0)):
        actual = res[w][key]
        good = abs(actual - expect) <= SELF_CHECK_TOL
        ok = ok and good
        print(f"    {w:<4}{key:<4} 기대 {expect:>8.4f} · 실제 {actual:>8.4f} "
              f"{'통과' if good else '실패'}")

    p_we = res["we"]["p"]
    good = abs(res["we"]["q"] - min(1.0, 2.0 * p_we)) <= SELF_CHECK_TOL
    ok = ok and good
    print(f"    가족 m = len(목록) = {len(GATE3_LIST)}")
    print(f"      p(we) = {p_we:.6f}")
    print(f"      q(we) 기대 2·p = {min(1.0, 2.0 * p_we):.6f} · "
          f"실제 {res['we']['q']:.6f}  {'통과' if good else '실패'}")
    good = abs(res["zzz"]["q"] - 1.0) <= SELF_CHECK_TOL
    ok = ok and good
    print(f"      q(zzz) 기대 1.000000 · 실제 {res['zzz']['q']:.6f}  "
          f"{'통과' if good else '실패'}")
    counterfactual = min(1.0, p_we * 172 / 1)
    print(f"      (반사실: 가족을 172로 고정했다면 q(we) = {counterfactual:.6f} —")
    print(f"       가족을 잘못 잡으면 이렇게 표가 조용히 빈다.)")

    # 주목 판정도 함께 본다. δ = −1.0 은 문턱 0.147을 한참 넘지만, 세 계정씩
    # 여섯 개로는 q가 0.05에 닿지 못한다. 그래서 둘 다 주목이 아니어야 한다 —
    # "δ가 크면 주목"이 아니라 "q와 δ를 함께 넘어야 주목"이라는 규칙이
    # 코드에 제대로 들어가 있는지 여기서 확인된다.
    good = (res["we"]["주목"] is False and res["zzz"]["주목"] is False
            and res["we"]["유의"] is False)
    ok = ok and good
    print(f"    주목 판정  we={res['we']['주목']} · zzz={res['zzz']['주목']}  "
          f"{'통과' if good else '실패'}")
    print(f"      we 는 δ = −1.0 으로 문턱 {DELTA_NOTABLE} 을 한참 넘지만")
    print(f"      q = {res['we']['q']:.4f} 라 유의가 아니고, 따라서 주목도 아니다.")
    print("      세 계정씩으로는 완전 분리여도 유의에 닿지 못한다 — 순위 검정의")
    print("      표본 하한이다. 두 조건을 함께 걸고 있는지가 여기서 확인된다.")
    return ok


def self_check():
    """세 관문을 차례로 지난다. 하나라도 실패하면 본 계산을 시작하지 않는다."""
    line("[자가검증] 세 관문 — 통계 함수 · 사용률 규칙 · BH 가족 크기")
    print("  06이 04의 토큰화를 먼저 확인하고 본 계산에 들어갔던 것과 같은 자리다.")
    print("  순위 검정과 다중비교 보정은 틀려도 조용하다 — 가족 크기를 하나만")
    print("  잘못 잡아도 코드는 멀쩡히 돌고 그럴듯한 표가 나온다. 손으로 풀 수")
    print("  있는 자료로 기계를 먼저 통과시키는 편이 훨씬 싸다.")
    ok1 = gate_1_statistics()
    ok2 = gate_2_rates()
    ok3 = gate_3_family()
    ok = ok1 and ok2 and ok3
    print()
    print(f"  관문 1 통계 함수 {'통과' if ok1 else '실패'} · "
          f"관문 2 사용률 규칙 {'통과' if ok2 else '실패'} · "
          f"관문 3 BH 가족 {'통과' if ok3 else '실패'}")
    if not ok:
        print()
        print("■ 중단 — 자가검증 실패. 본 계산을 시작하지 않습니다.")
        print("  짚어 볼 곳:")
        print("   · build_rates 의 분모가 토큰수_구두점제외가 맞는가")
        print("   · word_vector 의 .get(word, 0.0) 기본값이 살아 있는가")
        print("   · compare_list 가 bh_qvalues 에 넘기는 목록 길이")
        print("   · 06 원본 함수를 손댄 흔적이 있는가(위 [승계] 해시)")
    return ok


# ════════════════════════════════════════════════════════════════════════
# [표] 화면 서식
# ════════════════════════════════════════════════════════════════════════
# 한글은 터미널에서 두 칸을 차지해 f-string의 자리맞춤이 어긋난다. 06·07이
# 그랬듯 머리글의 공백을 손으로 세어 맞춰 두었다. 값 서식과 짝이므로 한쪽만
# 고치지 말 것. (CJK 설정이 아닌 터미널에서는 한 칸씩 밀려 보일 수 있다.)
SUMMARY_HEAD = ("      변형" + " " * 8 + "빈도" + "   비율" + "   크기"
                + "   172겹침" + "  추가" + "  빠짐" + "   주목" + "  주목비율")


def print_summary_table(rows):
    """변형 아홉 벌의 크기·겹침·주목을 한 표로 띄운다."""
    print(SUMMARY_HEAD)
    for r in rows:
        mark = "  ← 기준선" if r["기준선인가"] else ""
        print(f"      {r['이름']:<12}{r['빈도문턱']:>4}{r['비율문턱']:>7.2f}"
              f"{r['크기']:>7}{r['기준선172와_겹침']:>12}"
              f"{r['추가_종수']:>6}{r['빠짐_종수']:>6}"
              f"{r['주목종수']:>7}{r['주목비율']:>10.3f}{mark}")


def print_head5_table(rows):
    """머리 5종이 아홉 목록에 남아 있는지를 격자로 띄운다."""
    print("      변형" + " " * 8 + "".join(f"{w:>10}" for w in HEAD5))
    for r in rows:
        cells = []
        for w in HEAD5:
            cells.append(f"{'포함' if r['머리5종'][w]['포함'] else '없음':>8}")
        print(f"      {r['이름']:<12}" + "".join(cells))


# ════════════════════════════════════════════════════════════════════════
# [정합 관문] 기준선 변형이 06과 같은 수를 내는가
# ════════════════════════════════════════════════════════════════════════
def consistency_gate(baseline_res, six_words):
    """
    기준선 변형(f5_r0.50)의 172종이 06_비교결과.json과 글자까지 같은지 본다.

    같아야 하는 이유. 기준선 변형은 02가 실제로 쓴 문턱(5 / 0.50)이고, 그
    목록의 해시는 06이 쓴 172종의 해시와 같다. 사용률의 분자는 04-1이 다시
    센 표면형 카운트, 분모는 04-1의 구두점 제외 토큰수인데, 04-1은 이미 04와
    다섯 합계와 계정별 172종 카운트가 전부 같다는 것을 확인했다. 그러니
    05→06 경로로 얻은 δ와 04-1→02-1 경로로 얻은 δ는 같은 수여야 한다.

    이 관문이 하는 일은 02-1의 계산을 검사하는 것이 아니라 '두 경로가 같은
    곳에 닿는가'를 검사하는 것이다. 어긋나면 02-1의 아홉 표 전체를 06과 나란히
    놓을 수 없다 — 변형 여덟 벌이 기준선과 다른 것인지, 경로가 다른 것인지
    구분할 수 없기 때문이다.

    반환: (일치 종수, 불일치 목록[(단어, 항목, 06값, 02-1값)…])
    """
    same, diffs = 0, []
    for w, r in sorted(baseline_res.items()):
        old = six_words.get(w)
        if old is None:
            diffs.append((w, "06에 없음", None, round(r["델타"], STAT_DIGITS)))
            continue
        bad = []
        if abs(round(r["델타"], STAT_DIGITS) - old["델타"]) > 1e-9:
            bad.append(("델타", old["델타"], round(r["델타"], STAT_DIGITS)))
        if abs(round(r["U"], 1) - old["U"]) > 1e-6:
            bad.append(("U", old["U"], round(r["U"], 1)))
        if r["주목"] != old["주목"]:
            bad.append(("주목", old["주목"], r["주목"]))
        if r["방향"] != old["방향"]:
            bad.append(("방향", old["방향"], r["방향"]))
        if bad:
            for item, o, n in bad:
                diffs.append((w, item, o, n))
        else:
            same += 1
    return same, diffs


# ════════════════════════════════════════════════════════════════════════
# [예측] 보관된 13-19 사전선언의 15항(현 02-1)의 P15-1 ~ P15-3 을 기계로 판정한다
# ════════════════════════════════════════════════════════════════════════
def judge_predictions(rows):
    """
    사전선언에 적힌 문장을 그대로 문턱으로 옮겨 적중·빗나감을 가린다.

    판정은 문장 단위 전부-아니면-빗나감이다(07과 같다). "9개 변형 모두에서"
    라고 적혀 있으면 한 칸이라도 어긋나는 순간 빗나감이고, 어긋난 칸의
    이름을 그대로 적는다. 결과가 마음에 들지 않는다고 문턱을 손보지 않는다.
    """
    verdicts = []

    # ── P15-1 ────────────────────────────────────────────────
    # "9개 변형 모두에서 06 머리 낱말 5종(we·must·our·was·he)이 목록에 남고
    #  |δ| ≥ 0.147 을 유지한다."
    bad = []
    for r in rows:
        for w in HEAD5:
            cell = r["머리5종"][w]
            if not cell["포함"]:
                bad.append(f"{w}/{r['이름']}(목록에 없음)")
            elif abs(cell["델타"]) < DELTA_NOTABLE:
                bad.append(f"{w}/{r['이름']}(|δ|={abs(cell['델타']):.3f})")
    verdicts.append({
        "번호": "P15-1",
        "기대": "9변형 × 머리 5종 = 45칸 모두 목록에 있고 |δ| ≥ 0.147",
        "실제": (f"45칸 중 {45 - len(bad)}칸 충족"
                if bad else "45칸 모두 충족"),
        "판정": "빗나감" if bad else "적중",
        "어긋난칸": bad,
    })

    # ── P15-2 ────────────────────────────────────────────────
    # "주목 비율(주목 종수 ÷ 목록 크기)이 모든 변형에서 0.40~0.70 안에 있다."
    lo, hi = NOTABLE_BAND
    out = [f"{r['이름']}({r['주목비율']:.3f})"
           for r in rows if not (lo <= r["주목비율"] <= hi)]
    got = [r["주목비율"] for r in rows]
    verdicts.append({
        "번호": "P15-2",
        "기대": f"아홉 변형의 주목 비율이 모두 {lo:.2f}~{hi:.2f} 안",
        "실제": f"최소 {min(got):.3f} · 최대 {max(got):.3f}",
        "판정": "빗나감" if out else "적중",
        "어긋난칸": out,
    })

    # ── P15-3 ────────────────────────────────────────────────
    # "목록 크기는 빈도 임계값에 주로 반응하고(3 > 5 > 10), 비율 임계값에는
    #  덜 반응한다(같은 빈도에서 크기 변동 20% 이내)."
    by = {(r["빈도문턱"], r["비율문턱"]): r["크기"] for r in rows}
    freqs = sorted({r["빈도문턱"] for r in rows})
    ratios = sorted({r["비율문턱"] for r in rows})
    bad3 = []
    for ratio in ratios:                       # 앞 절 — 빈도에 반응하는가
        seq = [by[(f, ratio)] for f in freqs]
        if not all(a > b for a, b in zip(seq, seq[1:])):
            bad3.append(f"비율 {ratio:.2f}에서 크기 {seq} — 3 > 5 > 10 이 아니다")
    spreads = {}
    for freq in freqs:                          # 뒤 절 — 비율에는 덜 반응하는가
        seq = [by[(freq, r)] for r in ratios]
        spread = (max(seq) - min(seq)) / max(seq)
        spreads[freq] = spread
        if spread > SIZE_TOL:
            bad3.append(f"빈도 {freq}에서 크기 변동 {spread:.1%} — {SIZE_TOL:.0%} 초과")
    verdicts.append({
        "번호": "P15-3",
        "기대": (f"모든 비율에서 크기 f3 > f5 > f10, 그리고 같은 빈도 안의 "
                f"크기 변동이 {SIZE_TOL:.0%} 이내"),
        "실제": ("빈도 반응 " + " · ".join(
                    f"r{r:.2f}:{[by[(f, r)] for f in freqs]}" for r in ratios)
                + " / 비율 변동 " + " · ".join(
                    f"f{f}:{spreads[f]:.1%}" for f in freqs)),
        "판정": "빗나감" if bad3 else "적중",
        "어긋난칸": bad3,
    })
    return verdicts


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    t_all = time.time()

    print("=" * 74)
    print("02-1 임계값 민감도 — 기능어 목록을 아홉 가지로 바꿔 06을 다시 돌린다")
    print("=" * 74)
    print("02의 두 문턱(빈도 5 · 닫힌비율 0.50)은 관례적인 선택이었다. 그 선택이")
    print("06의 94종을 만든 것인지, 아니면 어떻게 골라도 같은 결과가 나오는지를")
    print("여기서 가린다. 보관된 13-19 사전선언의 15항(현 02-1)의 방법을 그대로 구현하고, 문턱(q ≤ 0.05,")
    print("|δ| ≥ 0.147)은 06 그대로 둔다.")

    for path in (EXT_JSON, ACCOUNTS_JSON, RATES_JSON, COMPARE_JSON, COMPARE_PY):
        if not os.path.exists(path):
            print(f"\n■ 중단 — {os.path.basename(path)} 이(가) 없습니다.")
            return

    # ── [1/8] 입력과 라벨 ───────────────────────────────────────
    print("\n[1/8] 입력 적재 · 해시 사슬 · 라벨 개봉")
    ext = load_extended()
    ext_conf = ext["설정"]
    accounts = ext["계정"]
    variants = ext["변형목록"]
    union = ext["합집합"]
    print(f"      04-1 산출물  계정 {len(accounts):,}개 · 변형 {len(variants)}벌 · "
          f"합집합 {union['크기']}종 (실행일 {ext_conf.get('실행일', '?')})")

    gate13 = ext_conf.get("정합관문", {})
    if not gate13.get("통과"):
        print("\n■ 중단 — 04-1이 정합 관문을 통과하지 못한 상태입니다.")
        print("  보관된 13-19 사전선언의 13항(현 04-1)은 그럴 경우 04를 정본으로 삼으라고 적어 두었습니다.")
        print("  04-1의 표면형 카운터 위에서 02-1을 돌리는 것은 뜻이 없습니다.")
        return
    print(f"      04-1 정합 관문  통과 — 다섯 합계 일치, 계정별 172종 "
          f"{gate13.get('계정별172종_일치계정수'):,}계정 전부 일치")
    print("      04-1의 카운트가 04와 같다는 뜻이다. 그래서 02-1의 사용률은 05·06이")
    print("      쓴 것과 같은 분자·분모에서 나온다.")

    rules = load_rate_rules()
    fw = rules["04승계"]
    base_key = None
    for k, v in variants.items():
        if v.get("기준선인가"):
            base_key = k
    print(f"\n      ── 해시 사슬 ──")
    print(f"      05가 적어 둔 기능어 172종 해시   {fw.get('기능어_해시')}")
    print(f"      사전선언이 못 박은 값             {EXPECTED_FW_HASH}")
    print(f"      04-1이 다시 만든 기준선({base_key}) 해시  "
          f"{variants[base_key]['해시']}")
    chain_ok = (fw.get("기능어_해시") == EXPECTED_FW_HASH
                == variants[base_key]["해시"])
    print(f"      → {'세 값이 같다. 사슬이 이어져 있다.' if chain_ok else '어긋난다.'}")
    if not chain_ok:
        print("\n■ 중단 — 해시 사슬이 끊겼습니다. 02·05·04-1 중 어느 것이 달라졌습니다.")
        return
    print(f"      05의 분모 정의  {rules['분모_정의']}")

    copy_ok, h_src, h_copy = verify_copied_functions()
    print(f"\n      ── 06에서 복사한 통계 함수 ──")
    print(f"      {', '.join(COPIED_NAMES)}")
    print(f"      06 원본 해시 {h_src} · 이 파일 사본 {h_copy} · "
          f"기대 {COPIED_HASH}")
    print(f"      → {'같다. 같은 자로 잰다.' if copy_ok else '어긋난다.'}")
    if not copy_ok:
        print("\n■ 중단 — 통계 함수 사본이 06 원본과 다릅니다. 계산을 시작하지 않습니다.")
        return

    labels = load_labels()
    bot_ids, human_ids, missing, invalid = split_by_label(accounts, labels)
    line("라벨 개봉")
    print("  ■ 이 파일이 01_적격계정.json 의 '라벨' 키를 읽는다. ■")
    print("  04-1은 이 키를 읽지 않았다 — 서브레딧을 복원하고 표면형을 세는 동안")
    print("  어느 계정이 봇인지 몰랐다. 02-1은 두 무더기를 갈라야 비교가 성립하므로")
    print("  여기서 연다. 읽는 자리는 load_labels() 한 곳뿐이고, 목록을 고르는")
    print("  일(04-1이 이미 끝냈다)에는 라벨이 닿지 않았다. 아홉 벌의 목록은 어느")
    print("  것도 결과를 보고 만들어진 것이 아니다 — 그것이 이 민감도 검사가")
    print("  뜻을 갖는 조건이다.")
    print()
    print(f"  봇   {len(bot_ids):>6,}계정")
    print(f"  사람 {len(human_ids):>6,}계정")
    if missing or invalid:
        print(f"\n  ※ 라벨 없음 {len(missing):,} · bot/human 아님 {len(invalid):,}")
        print("    어느 무더기에도 넣을 수 없어 빠집니다. 01을 확인하십시오.")
    if not bot_ids or not human_ids:
        print("\n■ 중단 — 한쪽 무더기가 비어 비교가 성립하지 않습니다.")
        return

    # ── [2/8] 자가검증 ──────────────────────────────────────────
    print("\n[2/8] 자가검증")
    if not self_check():
        return

    # ── [3/8] 변형 목록 점검 ────────────────────────────────────
    print("\n[3/8] 변형 목록 아홉 벌 점검 — 04-1이 만든 것을 그대로 쓴다")
    print("      02-1은 목록을 새로 만들지 않는다. 04-1이 02의 read_conllu()와")
    print("      CLOSED_CLASS를 그대로 불러 만들어 둔 아홉 벌을 읽어 쓴다.")
    print("      여기서는 그 목록이 저장된 뒤 바뀌지 않았는지만 확인한다 —")
    print("      해시를 다시 계산해 04-1이 적어 둔 값과 맞춰 본다.")
    union_set = set(union["목록"])
    baseline_words = list(variants[base_key]["목록"])
    baseline_set = set(baseline_words)
    list_ok = True
    for k in sorted(variants):
        v = variants[k]
        recomputed = list_hash(v["목록"])
        good = (recomputed == v["해시"]) and set(v["목록"]) <= union_set
        list_ok = list_ok and good
        if not good:
            print(f"      {k}  해시 {v['해시']} vs 재계산 {recomputed}  "
                  f"합집합포함 {set(v['목록']) <= union_set}  ← 어긋남")
    print(f"      아홉 벌 모두 해시 일치, 모두 합집합 {union['크기']}종 안: "
          f"{'예' if list_ok else '아니오'}")
    if not list_ok:
        print("\n■ 중단 — 변형 목록이 04-1이 저장한 것과 다릅니다.")
        return
    print("      합집합 안에 있어야 하는 이유: 04-1은 합집합에 든 표면형만 셌다.")
    print("      목록에 합집합 밖 단어가 있으면 그 단어의 카운트가 통째로 0이 되어")
    print("      '아무도 안 쓴 단어'로 잘못 잡힌다.")

    # ── [4/8] 사용률 ────────────────────────────────────────────
    print("\n[4/8] 계정별 사용률 만들기 (05와 같은 분모 · 05와 같은 여섯 자리)")
    rates = build_rates(accounts)
    denom_total = sum(a["토큰수_구두점제외"] for a in accounts.values())
    surf_total = sum(sum(a["표면형_합집합"].values()) for a in accounts.values())
    print(f"      분모 합계 {denom_total:,} (구두점 제외 토큰수)")
    print(f"      합집합 표면형 토큰 {surf_total:,} — "
          f"전체의 {surf_total / denom_total:.1%}")
    print("      사용률은 계정 안에서만 계산한다. 계정마다 분모가 다르므로")
    print("      긴 계정과 짧은 계정을 같은 자로 견줄 수 있다(05 결정 1).")
    print("      여섯 자리로 자르는 이유는 05가 그 눈금으로 저장했고 06이 그")
    print("      값으로 순위를 매겼기 때문이다. 눈금이 다르면 동점 묶음이 달라져")
    print("      δ가 소수 넷째 자리에서 어긋난다 — 아래 [6/8]이 그것을 잡는다.")

    # ── [5/8] 변형별 비교 ───────────────────────────────────────
    print(f"\n[5/8] 변형별 F 비교 (그룹1 = {GROUP1}, 그룹2 = {GROUP2})")
    sparse_cut = int(len(accounts) * SPARSE_FRAC)
    rows = []
    all_results = {}
    for k in sorted(variants, key=lambda s: (int(s.split("_")[0][1:]),
                                             float(s.split("r")[1]))):
        v = variants[k]
        words = list(v["목록"])
        res = compare_list(words, bot_ids, human_ids, rates)
        all_results[k] = res

        notable = [w for w in words if res[w]["주목"]]
        added = sorted(set(words) - baseline_set)
        removed = sorted(baseline_set - set(words))
        row = {
            "이름": k,
            "빈도문턱": v["빈도문턱"],
            "비율문턱": v["비율문턱"],
            "크기": len(words),
            "해시": v["해시"],
            "기준선인가": bool(v.get("기준선인가")),
            "기준선172와_겹침": v["기준선172와_겹침"],
            "추가_종수": len(added),
            "빠짐_종수": len(removed),
            "추가_단어": added,
            "빠짐_단어": removed,
            "유의종수": sum(1 for w in words if res[w]["유의"]),
            "주목종수": len(notable),
            "주목비율": round(len(notable) / len(words), 6),
            "봇높음": sum(1 for w in notable if res[w]["델타"] > 0),
            "봇낮음": sum(1 for w in notable if res[w]["델타"] < 0),
            "추가단어중_주목": sum(1 for w in added if res[w]["주목"]),
            "머리5종": {w: ({"포함": True,
                          "델타": round(res[w]["델타"], STAT_DIGITS),
                          "q": sig(res[w]["q"]),
                          "주목": res[w]["주목"]}
                         if w in res else
                         {"포함": False, "델타": None, "q": None, "주목": False})
                     for w in HEAD5},
            "단어별": {w: pack_word(res[w], sparse_cut) for w in words},
        }
        rows.append(row)

    print_summary_table(rows)
    print()
    print("      읽는 법 — '추가'는 기준선 172종에 없던 단어가 몇 종 들어왔는가,")
    print("      '빠짐'은 172종 중 몇 종이 떨어져 나갔는가다. '주목'은 그 목록")
    print("      안에서 q ≤ 0.05 이면서 |δ| ≥ 0.147 인 단어의 수이고, 주목 비율은")
    print("      그것을 목록 크기로 나눈 값이다. BH 가족은 변형마다 그 목록의")
    print("      크기이므로, 목록이 커지면 같은 p라도 q가 조금 커진다.")
    print()
    for r in rows:
        if r["추가_종수"]:
            head = ", ".join(r["추가_단어"][:12])
            more = f" 외 {r['추가_종수'] - 12}종" if r["추가_종수"] > 12 else ""
            print(f"      {r['이름']:<12} 추가 {r['추가_종수']:>2}종 중 주목 "
                  f"{r['추가단어중_주목']:>2}종 — {head}{more}")
        if r["빠짐_종수"]:
            print(f"      {r['이름']:<12} 빠짐 {r['빠짐_종수']:>2}종 — "
                  f"{', '.join(r['빠짐_단어'][:12])}")

    line("머리 5종은 아홉 목록에 다 남아 있는가")
    print("  보관된 13-19 사전선언의 15항(현 02-1)이 지목한 다섯 낱말이다. 06에서 |δ| 상위에 있던 것들이고,")
    print("  목록이 흔들리면 이들이 먼저 빠질 것이라고 보았다.")
    print()
    print_head5_table(rows)
    print()
    base_row = [r for r in rows if r["기준선인가"]][0]
    for w in HEAD5:
        cell = base_row["머리5종"][w]
        print(f"      {w:<6} δ = {cell['델타']:+.4f}  "
              f"(06의 값과 같아야 한다 — [6/8]에서 확인)")
    qmax = max(r["머리5종"][w]["q"] for r in rows for w in HEAD5
               if r["머리5종"][w]["q"] is not None)
    print(f"\n      아홉 변형 × 다섯 낱말의 q 최댓값 = {qmax:.3g}")
    print("      0.0은 정규근사와 배정도 실수의 바닥이다 — '차이가 없을 확률이")
    print("      0'이 아니라 더 작은 값을 구분할 수 없다는 뜻이다. 가족이 155종")
    print("      이든 191종이든 이 다섯은 문턱 근처에 얼씬도 하지 않는다.")
    print()
    print("      ■ δ가 아홉 변형에서 똑같이 나오는 것은 우연이 아니다 ■")
    print("      한 낱말의 사용률은 그 낱말의 횟수를 구두점 제외 토큰수로 나눈")
    print("      값이다. 두 수 모두 '그 낱말이 어느 목록에 들었는가'와 아무 상관이")
    print("      없다. 그래서 δ는 목록을 바꿔도 그대로다. 목록이 바꾸는 것은 두")
    print("      가지뿐이다 — 어떤 낱말이 표에 오르는가, 그리고 BH 가족이 몇")
    print("      종인가. 이 단계가 실제로 묻는 것은 '문턱을 옮기면 다른 낱말이")
    print("      들어오고 그 바람에 판정이 달라지는가'이지 'δ가 흔들리는가'가")
    print("      아니다. 이 점을 적어 두지 않으면 아홉 줄이 같은 것을 보고")
    print("      '아홉 번 재현했다'고 읽기 쉽다 — 재현이 아니라 같은 수다.")

    # ── [6/8] 정합 관문 ─────────────────────────────────────────
    print("\n[6/8] 정합 관문 — 기준선 변형이 06과 같은 수를 내는가")
    six = json.load(open(COMPARE_JSON, encoding="utf-8"))
    six_words = six["단어별"]
    same, diffs = consistency_gate(all_results[base_key], six_words)
    print(f"      기준선 {base_key} · 172종 · 06_비교결과.json 과 대조")
    print(f"      δ·U·방향·주목이 모두 같은 단어  {same} / "
          f"{len(all_results[base_key])}종")
    if diffs:
        print(f"      불일치 {len(diffs)}건 — 앞 3건:")
        for w, item, o, n in diffs[:3]:
            print(f"        {w:<10} {item:<6} 06={o}  02-1={n}")
        print("      ※ 두 경로가 다른 곳에 닿았습니다. 아홉 표를 06과 나란히")
        print("        놓을 수 없습니다 — 사전선언대로 06을 정본으로 삼고, 이")
        print("        불일치를 결과에 그대로 실으십시오.")
    else:
        print("      불일치 0건.")
        print("      05→06 경로(05가 저장한 사용률)와 04-1→02-1 경로(04-1이 다시 센")
        print("      표면형 카운트)가 같은 δ에 닿았다. 두 경로는 파싱을 따로")
        print("      돌렸고 중간 저장 형식도 다르다. 그런데도 172종의 U가 소수점")
        print("      아래까지 같다는 것은, 02-1이 06과 같은 자를 쓰고 있다는 뜻이다.")
    six_notable = sum(1 for w, r in six_words.items() if r["주목"])
    print(f"\n      06이 센 주목 단어 {six_notable}종 · "
          f"02-1의 기준선 {base_row['주목종수']}종 "
          f"{'(같다)' if six_notable == base_row['주목종수'] else '(다르다)'}")

    # ── [7/8] 저장 ──────────────────────────────────────────────
    print("\n[7/8] 저장")
    verdicts = judge_predictions(rows)
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.machine()}",
            "방법": ("04-1의 표면형 카운터로 계정별 사용률을 만들고(분모 = 구두점 "
                   "제외 토큰수, 05와 같은 여섯 자리), 아홉 변형 목록마다 06과 "
                   "같은 Mann-Whitney U + Cliff's δ 비교를 돌렸다. BH 가족은 "
                   "변형마다 그 목록의 크기다(보관된 13-19 사전선언의 15항(현 02-1)). 문턱은 06 그대로 "
                   "q ≤ 0.05, |δ| ≥ 0.147. 추가 검정은 없다."),
            "그룹1": GROUP1,
            "그룹2": GROUP2,
            "n_bot": len(bot_ids),
            "n_human": len(human_ids),
            "라벨결측": len(missing) + len(invalid),
            "입력파일": {
                "13": os.path.basename(EXT_JSON),
                "01_라벨": os.path.basename(ACCOUNTS_JSON),
                "05_규칙": os.path.basename(RATES_JSON),
                "06_대조": os.path.basename(COMPARE_JSON),
                "06_통계함수": os.path.basename(COMPARE_PY),
            },
            "승계해시": {
                "기능어172": EXPECTED_FW_HASH,
                "05가_적어_둔_값": fw.get("기능어_해시"),
                "13의_기준선목록": variants[base_key]["해시"],
                "06_통계함수": h_copy,
                "복사한_함수": COPIED_NAMES,
                "변형목록": {k: variants[k]["해시"] for k in sorted(variants)},
            },
            "라벨_사용": ("있음. 01_적격계정.json 의 '라벨' 키를 load_labels()"
                       "에서 한 번 읽는다. 04-1은 읽지 않았다."),
            "사용률_규칙": {
                "분모": "계정별 토큰수_구두점제외 (04-1 합계 필드 = 04와 같다)",
                "분자": "04-1의 표면형_합집합 카운트",
                "자릿수": RATE_DIGITS,
                "자릿수_이유": ("05가 여섯 자리로 저장했고 06이 그 값으로 순위를 "
                            "매겼다. 반올림하지 않으면 동점 묶음이 달라져 172종 "
                            "중 7종에서 δ가 0.0001 어긋난다."),
                "희소저장": "카운터에 없는 표면형은 0.0으로 채운다(06과 같다)",
            },
            "13_정합관문": {"통과": True,
                        "계정별172종_일치계정수":
                            gate13.get("계정별172종_일치계정수")},
            "자가검증": {"관문1_통계함수": True, "관문2_사용률규칙": True,
                     "관문3_BH가족크기": True},
            "정합관문": {
                "기준선": base_key,
                "대조": "06_비교결과.json 단어별 172종의 δ·U·방향·주목",
                "일치종수": same,
                "불일치건수": len(diffs),
                "불일치예시": [{"단어": w, "항목": i, "06": o, "15": n}
                          for w, i, o, n in diffs[:3]],
                "통과": len(diffs) == 0,
            },
            "문턱": {"q": Q_ALPHA, "델타": DELTA_NOTABLE,
                   "희소기준": f"출현 계정 {sparse_cut}개 미만"},
        },
        "변형별": {r["이름"]: r for r in rows},
        "머리5종_추적": {
            w: {r["이름"]: r["머리5종"][w] for r in rows} for w in HEAD5
        },
        "요약표": [{k: r[k] for k in
                  ("이름", "빈도문턱", "비율문턱", "크기", "해시",
                   "기준선인가", "기준선172와_겹침", "추가_종수", "빠짐_종수",
                   "유의종수", "주목종수", "주목비율", "봇높음", "봇낮음",
                   "추가단어중_주목")} for r in rows],
        "예측판정": verdicts,
    }
    write_json(OUT_JSON, out, indent=1)
    print(f"      {OUT_JSON}")
    print(f"      {os.path.getsize(OUT_JSON):,} bytes")

    # ── [8/8] 예측 대조 ─────────────────────────────────────────
    print("\n[8/8] 사전 예측 대조")
    line("사전 예측 대조 — 보관된 13-19_사전선언 「15」(현 02-1)")
    print("  판정은 문장 단위 전부-아니면-빗나감이다(07과 같다). '9개 변형 모두'")
    print("  라고 적힌 예측은 한 칸이라도 어긋나면 빗나감이고, 어긋난 칸의 이름을")
    print("  그대로 적는다. 빗나간 예측도 지우지 않는다.")
    print()
    print("  번호     판정      서술")
    texts = {
        "P15-1": "9개 변형 모두에서 머리 낱말 5종(we·must·our·was·he)이 목록에 남고 |δ| ≥ 0.147 유지",
        "P15-2": "주목 비율(주목 종수 ÷ 목록 크기)이 모든 변형에서 0.40~0.70 안",
        "P15-3": "목록 크기는 빈도에 주로 반응(3 > 5 > 10), 비율에는 덜 반응(같은 빈도에서 변동 20% 이내)",
    }
    for v in verdicts:
        print(f"  {v['번호']:<8} {v['판정']:<8}  {texts[v['번호']]}")
    print()
    for v in verdicts:
        print(f"  {v['번호']}  기대: {v['기대']}")
        print(f"         실제: {v['실제']}")
        if v["어긋난칸"]:
            print(f"         어긋난 칸: {', '.join(v['어긋난칸'][:8])}")
    hit = sum(1 for v in verdicts if v["판정"] == "적중")
    miss = sum(1 for v in verdicts if v["판정"] == "빗나감")
    na = len(verdicts) - hit - miss
    print(f"\n  적중 {hit} · 빗나감 {miss} · 판정불가 {na}  (전부 {len(verdicts)})")

    line("확인 항목")
    print("  아래를 직접 보고 나서 결과를 쓰십시오.")
    print("   1. [5/8]의 δ 표에서 아홉 줄이 같은 수를 내는 것을 '아홉 번")
    print("      재현했다'로 읽지 말 것. 사용률의 분자와 분모가 목록과")
    print("      무관하므로 δ는 애초에 같은 수다. 이 단계가 답한 것은")
    print("      '문턱을 옮겨도 같은 낱말이 목록에 남는가'이지 '값이")
    print("      안정한가'가 아니다.")
    print("   2. 그러면 이 검사는 무엇을 배제했나. 두 가지다 — 06의 머리")
    print("      낱말이 문턱 5/0.50 에서만 목록에 드는 경계 낱말이었을")
    print("      가능성, 그리고 목록을 넓히면 주목 비율이 급락해 94종이")
    print("      '고른 것치고 많다'가 될 가능성. [3/8]과 [5/8]의 표가")
    print("      그 둘을 각각 막는다.")
    print("   3. 빈도 3으로 내리면 UD에서 서너 번밖에 안 나온 낱말이")
    print("      들어온다. 그중 몇 종이 주목으로 잡히는지를 [5/8] 아래의")
    print("      '추가 … 중 주목' 줄에서 보라. 그 낱말들이 BotSim 코퍼스")
    print("      에서도 희소하다면 δ가 커도 몇 계정의 우연이다 — JSON의")
    print("      '희소' 표시를 함께 보라.")
    print("   4. 아홉 변형은 모두 같은 UD English-EWT 에서 나왔다. 목록")
    print("      생성의 자의성 중 '문턱'만 흔든 것이고, '어느 코퍼스로")
    print("      닫힌 어류를 판정하는가'는 흔들지 않았다. 02-1이 배제한")
    print("      위협의 범위를 그만큼으로 적으라.")
    print("   5. [6/8]의 정합 관문이 0건이어야 아홉 표를 06과 같은 지면에")
    print("      놓을 수 있다. 한 건이라도 남았다면 그 원인을 밝히기 전에는")
    print("      02-1의 표를 06의 연장으로 인용하지 말 것.")

    print(f"\n  실행 시간 {time.time() - t_all:.1f}초")


if __name__ == "__main__":
    main()
