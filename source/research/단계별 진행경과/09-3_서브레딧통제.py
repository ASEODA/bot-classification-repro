#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
09-3_서브레딧통제.py
────────────────────────────────────────────────────────────────────────────
목적
    06·07이 잡은 봇/사람의 문체 차이가 '서브레딧 화법의 차이'였을 가능성을
    끊는다. 두 집단을 같은 서브레딧 안에 세워 놓고 다시 견준다.

무엇이 문제였나
    01의 자료에서 사람 문서의 63.5%가 r/politics에서 왔고, 봇은 31.5%였다.
    같은 뉴스 계열이라도 정치 토론방과 국제뉴스방은 화법이 다르다. 정치방은
    1인칭·과거형 서사와 인용이 많고, 뉴스방은 제목 옮기기와 짧은 논평이 많다.
    그러면 06이 잡은 "봇은 was·he를 덜 쓴다"가 봇의 문체가 아니라 '봇이 있던
    방의 화법'일 수 있다. 이것은 계정을 더 모아도, 검정을 더 세게 걸어도
    사라지지 않는 종류의 위협이다 — 비교 조건 자체가 어긋나 있기 때문이다.

어떻게 끊는가
    한 방만 남긴다. 두 집단의 문서 가운데 subreddit == "politics" 인 것만
    골라 사용률을 다시 만들고, 06·07과 똑같은 자로 다시 잰다. 남은 차이는
    적어도 '어느 방에 있었나'로는 설명되지 않는다.
        표본 A(판정용)  politics 문서만. 그 안에서 문서 10건 이상인 계정.
        표본 B(보조)    news + worldnews 문서만. 같은 규칙. 나란히 적기만 한다.

무엇으로 판정하나
    표본이 줄면 q는 저절로 커진다(계정 1,869 → 1,000 언저리). 그래서 보관된
    13-19 사전선언의 14항(현 09-3)은 q 조건을 걸지 않고 **|δ| ≥ 0.147 유지 여부와 방향**으로 판정한다.
    09-2의 교훈이다 — 표본이 줄어드는 재검정에서 q를 문턱으로 쓰면 "표본이 줄어
    유의하지 않아졌다"를 "차이가 사라졌다"로 잘못 읽는다.
    판정 대상은 06·07의 머리 10종:
        we · must · our · was · he            (06 기능어)
        Tense=Past · Number=Sing · Gender=Neut · Gender=Masc · Gender=Fem (07 자질)

무엇을 따르나
    보관된 13-19_사전선언.md 「14 서브레딧 통제」(현 09-3)를 그대로 구현한다. 검정·δ·BH는
    06_봇사람비교.py에서, 축 내부 비율과 결측 규칙은 07_형태자질비교.py에서
    ast로 소스를 그대로 떠 왔다(아래 [승계] 절). 손으로 옮겨 적지 않은 이유는
    통계 구현이 단계마다 조금씩 달라지는 것 — "같은 자로 쟀다"는 주장을
    무너뜨리는 가장 흔한 경로 — 를 코드로 막기 위해서다.
    문턱(0.05 · 0.147)도, 검정도, 예측도 결과를 보고 바꾸지 않는다.

라벨
    이 파일은 라벨을 읽는다. 04-1은 읽지 않았다. 어디서 읽는지는 [1/9]의
    load_labels() 한 자리뿐이고, 화면에도 그 사실을 찍는다(보관된 13-19 사전선언의 공통 원칙
    「라벨 규율」).

실행
        python3 -u 09-3_서브레딧통제.py
    필요 패키지 없음. 표준 라이브러리만 쓴다. 파싱을 다시 하지 않고 04-1이
    저장해 둔 서브레딧별 카운트만 다시 나누므로 몇 초면 끝난다.

선행 조건
    같은 폴더에 04-1_확장재파싱.json · 01_적격계정.json · 05_사용률검수.json ·
    06_비교결과.json · 07_형태자질비교.json 이 있어야 한다.

산출
    09-3_서브레딧통제.json 표본 A·B의 총사용률·기능어 172·자질 58·UPOS 17 결과
                           + 머리 10종 대조표 + 예측 P14-1~P14-4 판정
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
HERE = os.path.dirname(os.path.abspath(__file__))
EXPAND_JSON = f"{HERE}/04-1_확장재파싱.json"      # 04-1 산출물 — 서브레딧별 카운트
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"        # 01 산출물 — "라벨" 키만 꺼낸다
RATES_JSON = f"{HERE}/05_사용률검수.json"         # 05 산출물 — 172종 목록·해시
COMPARE_PY = f"{HERE}/06_봇사람비교.py"           # 통계 함수의 원본
COMPARE_JSON = f"{HERE}/06_비교결과.json"         # 머리 5종 δ 기준값
FEATURE_PY = f"{HERE}/07_형태자질비교.py"         # 축내부비율·결측 규칙의 원본
FEATURE_JSON = f"{HERE}/07_형태자질비교.json"     # 머리 5종 δ 기준값
OUT_JSON = f"{HERE}/09-3_서브레딧통제.json"       # 산출물

GROUP1, GROUP2 = "bot", "human"
# 06·07과 같은 순서로 못 박는다. U와 δ는 그룹1 기준이라 이 줄이 뒤집히면
# 표 전체의 부호가 반대가 된다.
#   δ > 0  →  봇이 높음        δ < 0  →  봇이 낮음

Q_ALPHA = 0.05          # BH 보정 후 유의 판정 문턱 (06·07과 같다)
DELTA_NOTABLE = 0.147   # '주목'의 효과크기 하한 (관례적 small 경계, 06·07과 같다)
SPARSE_FRAC = 0.10      # 출현 계정이 표본의 이 비율 미만이면 '희소' 표시
TOP_SHOW = 15           # 주목 표에 몇 줄을 띄울 것인가

RATE_DIGITS = 6         # 사용률·중앙값 저장 자릿수
STAT_DIGITS = 6         # U·z·δ 저장 자릿수 (명세 §1 「실수는 소수 6자리」)
SIG_DIGITS = 6          # p·q는 유효숫자로 자른다 — 06의 sig()가 참조한다

DENOM_AXIS = "축내부합"               # 07의 상수 — 분모 = 그 계정의 해당 축 총 출현수
DENOM_TOKEN = "토큰수_구두점제외"      # 07의 상수 — 분모 = 구두점 제외 토큰수

# ── 표본 정의 (보관된 13-19 사전선언의 14항(현 09-3)) ──────────────────
SAMPLE_A = ("A(politics)", ("politics",))
SAMPLE_B = ("B(news+worldnews)", ("news", "worldnews"))
MIN_DOCS = 10           # 01의 적격 기준과 같은 수. 그 서브셋 안에서 다시 건다.
# 서브레딧 이름은 정확히 일치하는 것만 센다. 04-1의 관찰에는 "polotics"(2건),
# "internationalnews"(66건) 같은 변형 이름이 있지만, 그것을 politics로 묶을지
# 말지를 지금 정하면 결과를 보고 표본을 고르는 셈이 된다. 사전선언이 적은 것은
# subreddit == "politics" 이므로 글자 그대로 따른다.

# ── 06·07에서 AST로 복사해 온 함수들 ────────────────────────────
# 매 실행마다 원본과 사본을 각각 ast로 다시 떠서 해시를 맞춘다. 사본을 한 글자
# 라도 손대면 그 자리에서 걸린다. 04-1이 쓴 것과 같은 장치다.
COPIED_06_CORE = ["normal_cdf", "ranks_with_ties", "mann_whitney",
                  "bh_qvalues", "quartiles", "sig", "direction_of"]
COPIED_06_CORE_HASH = "b3de6ef352db03a1"   # 04-1이 승계한 것과 같은 해시여야 한다
COPIED_06_EXTRA = ["word_vector", "compare_total", "compare_words"]
COPIED_06_EXTRA_HASH = "a80276eb1af97220"
COPIED_07 = ["build_axis_map", "axis_of", "denom_kind_of", "compute_ratios",
             "compute_upos_ratios", "defined_values", "compare_family", "rnd"]
COPIED_07_HASH = "4f9d41e2e8262c18"

# ── 자가검증 고정 예제 (1) — 06의 세 예제 ────────────────────────
# 손계산은 06_봇사람비교.py의 self_check() docstring에 그대로 있다.
SELF_CHECK_U = [
    ("완전 분리", [1, 2, 3], [4, 5, 6], 0.0, -1.0, 5.25),
    ("동점 포함", [1, 1, 2], [1, 2, 2], 3.0, -1.0 / 3.0, 4.05),
]
SELF_CHECK_BH_P = [0.01, 0.02, 0.03, 0.04]
SELF_CHECK_BH_Q = [0.04, 0.04, 0.04, 0.04]
SELF_CHECK_TOL = 1e-9

# ── 자가검증 고정 예제 (2) — 09-3의 규칙 두 가지 ───────────────────
# 예제 ㉮ 서브레딧 필터와 적격 판정. 손계산은 self_check_sample()에 적어 두었다.
SELF_CHECK_DOCS = {
    "갑": {"politics": 12, "news": 5},
    "을": {"politics": 9, "news": 6, "worldnews": 7},
    "병": {"worldnews": 20},
    "정": {"politics": 10},
}
SELF_CHECK_ELIGIBLE_A = ["갑", "정"]        # politics ≥ 10  (정은 경계값 10)
SELF_CHECK_ELIGIBLE_B = ["을", "병"]        # news+worldnews ≥ 10

# 예제 ㉯ 서브셋 분모 · 축 내부 비율 · 결측. 두 계정의 politics 블록만 있다고 하자.
SELF_CHECK_BLOCKS = {
    "갑": {"문서수": 12, "토큰수_구두점제외": 20,
          "기능어": {"the": 4, "we": 1},
          "자질": {"Tense=Past": 3, "Tense=Pres": 1, "Voice=Pass": 2},
          "UPOS": {"DET": 4, "NOUN": 10, "PUNCT": 3}},
    "을": {"문서수": 10, "토큰수_구두점제외": 10,
          "기능어": {"the": 1},
          "자질": {"Number=Sing": 5},
          "UPOS": {"NOUN": 8}},
}
#  (계정, 항목, 기대값, 설명)
SELF_CHECK_RATE = [
    ("갑", "총사용률", 0.25, "기능어 4+1=5회 ÷ 구두점 제외 20토큰"),
    ("을", "총사용률", 0.10, "기능어 1회 ÷ 10토큰"),
    ("갑", "the", 0.20, "4 ÷ 20"),
    ("갑", "must", 0.00, "한 번도 안 썼다 — 없는 키는 0회이지 결측이 아니다"),
]
SELF_CHECK_FEAT = [
    ("갑", "Tense=Past", 0.75, "Tense 축이 대립값 2종(Past·Pres) → 축내부 3/(3+1)"),
    ("을", "Tense=Past", None, "Tense 축이 아예 없다 → 분모 0 → 결측"),
    ("갑", "Voice=Pass", 0.10, "Voice는 값이 Pass뿐 → 토큰 분모 2/20"),
    ("을", "Voice=Pass", 0.00, "분자가 0인 것이지 분모가 0인 것이 아니다"),
    ("을", "Number=Sing", 0.50, "Number도 값이 Sing뿐 → 토큰 분모 5/10"),
]
SELF_CHECK_UPOS = [
    ("갑", "DET", 0.20, "4 ÷ 20"),
    ("갑", "PUNCT", 0.15, "3 ÷ 20 — 분모가 구두점을 뺀 수라 눈금이 다르다(07 주석)"),
    ("을", "DET", 0.00, "안 나온 품사는 0회"),
]

# ── 판정 대상: 06·07의 머리 10종 (보관된 13-19 사전선언의 14항(현 09-3)) ──
# (이름, 가족)  가족 F = 06 기능어, M = 07 형태자질
HEAD10 = [("we", "F"), ("must", "F"), ("our", "F"), ("was", "F"), ("he", "F"),
          ("Tense=Past", "M"), ("Number=Sing", "M"), ("Gender=Neut", "M"),
          ("Gender=Masc", "M"), ("Gender=Fem", "M")]

# ── 사전 예측 (보관된 13-19_사전선언 「14 서브레딧 통제」(현 09-3)의 네 항목) ─
# 이 상수가 사전등록의 실체다. 결과를 보기 전에 문서에 확정된 문장이고,
# [8/9]가 실제 수치와 자동으로 대조한다. 빗나간 것도 그대로 남긴다.
PREDICTIONS = [
    {"번호": "P14-1",
     "서술": "머리 10종 전부 |δ| ≥ 0.147 유지, 방향 뒤집힘 0",
     "근거": ["무너지면 그 항목은 서브레딧 화법이었다는 뜻이며",
             "06·07 해석에서 철회한다."]},
    {"번호": "P14-2",
     "서술": "총사용률 위치 δ의 부호가 음수(봇이 낮음)로 유지된다",
     "근거": ["06의 총사용률 δ = −0.130. 부호만 본다."]},
    {"번호": "P14-3",
     "서술": "총사용률 사분위 폭 비(봇 IQR ÷ 사람 IQR)가 1 미만으로 유지된다",
     "근거": ["옛 산포검정(보관)이 잡은 '봇의 뭉침'이 같은 방 안에서도 남는가."]},
    {"번호": "P14-4",
     "서술": "politics 표본의 봇 생존율이 사람 생존율보다 낮다",
     "근거": ["봇의 politics 비중이 작으므로. 예측이라기보다",
             "표본 성격의 기록이다."]},
]

# 표 머리글. 한글은 터미널에서 두 칸을 차지해 f-string의 자리맞춤이 어긋난다.
# 06·07과 같은 방식으로 공백을 손으로 세어 맞춰 두었다. 값 서식과 짝이므로
# 한쪽만 고치지 말 것.
TABLE_HEAD = ("      항목" + " " * 15 + "δ  방향" + " " * 14 + "q"
              + " " * 4 + "봇중앙" + " " * 2 + "사람중앙" + " " * 2 + "유효n")
HEAD10_HEAD = ("      항목            06·07 δ    표본A δ       변화   판정"
               "        표본B δ")


def line(title=""):
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다. 04·04-1·05~07·09-1·09-2와 옛 산포검정·IRA 대조·
    fox8 전이(보관)의 같은 함수를 그대로 가져왔다.

    임시 파일에 먼저 쓰고 이름을 바꿔치기한다(os.replace). 쓰는 도중에 창을
    닫으면 파일이 반쯤 잘린 채 남는다. 이름 바꾸기는 쪼개지지 않는 연산이라,
    어느 시점에 멈춰도 파일은 '이전 것' 아니면 '새 것'이다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


# ════════════════════════════════════════════════════════════════════════
# [승계 1] 06에서 AST로 복사한 통계 함수 — 아래 7개는 06의 소스 그대로다
# ════════════════════════════════════════════════════════════════════════
# 손으로 옮겨 적지 않았다. ast 모듈로 06_봇사람비교.py를 파싱해 함수 정의의
# 소스 조각을 그대로 떠 왔고, 실행할 때마다 verify_copied()가 원본과 사본을
# 다시 떠서 해시를 맞춘다. 04-1이 승계한 해시와 같아야 사슬이 이어진 것이다.
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


# ════════════════════════════════════════════════════════════════════════
# [승계 2] 06의 비교 절차 세 개 — 기능어 172종을 06과 글자까지 같게 돌린다
# ════════════════════════════════════════════════════════════════════════
# 검정 함수만 같고 그 함수를 부르는 절차가 다르면 "06과 같은 자"라는 말이
# 반쪽이 된다. word_vector의 .get(w, 0.0) 하나만 빠져도 결과가 통째로 뒤집힌다
# (그 함수의 주석이 경고하는 바로 그 사고다). 그래서 절차까지 통째로 떠 왔다.
def word_vector(uids, rates, word):
    """
    한 단어에 대해, 주어진 계정들의 사용률을 순서대로 늘어놓는다.

    ■ 여기가 이 파일에서 가장 틀리기 쉬운 한 줄이다. ■
    05는 사용률을 '희소 저장'했다 — 한 번도 안 쓴 단어는 그 계정의 "사용률"
    사전에 아예 키가 없다. 04부터 이어온 방식이고, 172종을 계정마다 다 적으면
    대부분이 0인 표가 되기 때문이다.

    그래서 .get(word, 0.0) 의 기본값 0.0이 반드시 있어야 한다. 없는 키를
    건너뛰면 "그 단어를 한 번도 안 쓴 계정"이 통째로 표본에서 사라진다.
    그러면 무더기 크기가 단어마다 제멋대로 달라지고, 남은 것은 그 단어를 쓴
    계정들끼리의 비교가 된다. 정작 재려던 것 — "봇이 이 단어를 덜 쓴다" —
    의 '덜 쓴다'가 바로 그 사라진 0들이다. 결과 전체가 뒤집힌다.
    """
    return [rates[u]["사용률"].get(word, 0.0) for u in uids]


def compare_total(bot_ids, human_ids, rates):
    """총 기능어 사용률 1건을 비교한다. BH 가족 밖의 단독 검정이다."""
    v1 = [rates[u]["총사용률"] for u in bot_ids]
    v2 = [rates[u]["총사용률"] for u in human_ids]
    res = mann_whitney(v1, v2)
    return res, v1, v2


def compare_words(words, bot_ids, human_ids, rates, presence):
    """
    단어 172종을 하나씩 비교하고, 172개의 p값에 BH 보정을 건다.

    반환은 |δ| 내림차순으로 정렬된 (단어, 결과) 목록이다. 사전선언이 주 결과로
    지목한 것이 '유의 단어의 개수'가 아니라 'δ가 큰 단어와 그 방향'이라,
    화면도 파일도 큰 것부터 보이는 순서로 둔다.
    """
    rows = []
    for w in words:
        v1 = word_vector(bot_ids, rates, w)      # ← 없는 키는 0.0으로 채워진다
        v2 = word_vector(human_ids, rates, w)
        r = mann_whitney(v1, v2)
        r["방향"] = direction_of(r["델타"])
        r["봇_중앙"] = statistics.median(v1)
        r["사람_중앙"] = statistics.median(v2)
        r["출현계정수"] = presence.get(w, 0)
        rows.append((w, r))

    qs = bh_qvalues([r["p"] for _, r in rows])
    for (w, r), q in zip(rows, qs):
        r["q"] = q
        r["유의"] = q <= Q_ALPHA
        r["주목"] = r["유의"] and abs(r["델타"]) >= DELTA_NOTABLE

    rows.sort(key=lambda kv: -abs(kv[1]["델타"]))
    return rows


# ════════════════════════════════════════════════════════════════════════
# [승계 3] 07에서 AST로 복사한 분모·결측·가족검정 절차
# ════════════════════════════════════════════════════════════════════════
# 축 내부 비율이냐 토큰 비율이냐를 가르는 규칙, 분모 0을 결측으로 두는 규칙,
# 결측을 걷어 낸 뒤 한쪽이 비면 BH 가족에서 빼는 규칙까지 07의 소스 그대로다.
# 이 세 가지는 보관된 13-19 사전선언의 14항(현 09-3)이 "07 규칙 그대로"라고 지정한 부분이다.
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


def rnd(x, digits):
    """None을 그대로 통과시키는 round. 검정 불가 자질의 칸이 None이라 필요하다."""
    return None if x is None else round(x, digits)


def verify_copied(names, want_hash, src_path):
    """
    원본과 이 파일의 사본이 글자까지 같은지 확인한다.

    ast로 두 파일에서 같은 이름의 함수 정의 소스를 떠서, names 순서로 이어
    붙인 뒤 sha256 앞 16자를 비교한다. 주석 한 줄만 달라져도 해시가 달라지므로
    "06·07에서 가져왔다"는 말이 사실인지 매 실행 확인된다.

    반환: (통과 여부, 원본 해시, 사본 해시)
    """
    def extract(path):
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        segs = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                segs[node.name] = ast.get_source_segment(src, node)
        if set(segs) != set(names):
            return None
        blob = "\n\n\n".join(segs[n] for n in names)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    h_src = extract(src_path)
    h_copy = extract(os.path.abspath(__file__))
    ok = (h_src is not None and h_src == h_copy == want_hash)
    return ok, h_src, h_copy


# ════════════════════════════════════════════════════════════════════════
# [1] 입력 적재와 라벨 개봉
# ════════════════════════════════════════════════════════════════════════
def load_expand():
    """04-1 산출물에서 설정·관찰·계정을 가져온다. 라벨은 여기 없다."""
    data = json.load(open(EXPAND_JSON, encoding="utf-8"))
    return data["설정"], data.get("관찰", {}), data["계정"]


def load_labels():
    """
    ■ 이 파일에서 라벨을 읽는 유일한 자리다. ■

    01에서 "라벨" 키 하나만 꺼내고 원문·언어판정·깔때기 통계는 즉시 버린다.
    04-1은 이 키를 한 번도 읽지 않았다(04-1 설정의 「라벨_사용」에 그렇게 적혀
    있다). 서브레딧을 복원하고 표면형을 세는 일은 어느 계정이 봇인지 몰라도
    되는 일이었고, 실제로 모르는 채로 했다. 09-3은 그렇게 굳어진 카운트에
    이름표를 붙이기만 한다 — 여기서 무엇을 고르지는 않는다.
    """
    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    labels = data.get("라벨") or {}
    del data                    # 원문·언어판정 등 나머지는 여기서 버린다
    return labels


def load_word_list():
    """05의 희소성표에서 기능어 172종의 이름을 가져온다(06과 같은 목록)."""
    data = json.load(open(RATES_JSON, encoding="utf-8"))
    conf, review = data["설정"], data["검수요약"]
    words = sorted(review.get("희소성표", {}))
    del data
    return conf.get("04승계", {}), words


def load_reference_deltas():
    """
    06·07 JSON에서 머리 10종의 δ를 읽어 온다. 판정의 기준선이다.

    상수로 베껴 적지 않는다. 베껴 적으면 어느 쪽이 진짜인지 두 곳을 대조해야
    하고, 그 대조를 사람이 잊는 순간 기준선이 조용히 틀어진다.
    """
    d6 = json.load(open(COMPARE_JSON, encoding="utf-8"))
    d7 = json.load(open(FEATURE_JSON, encoding="utf-8"))
    ref = {}
    for name, fam in HEAD10:
        if fam == "F":
            ref[name] = d6["단어별"][name]["델타"]
        else:
            ref[name] = d7["형태자질"][name]["델타"]
    total6 = d6["총사용률_비교"]
    feat_keys = sorted(d7["형태자질"])
    upos_keys = sorted(d7["UPOS"])
    return ref, total6, feat_keys, upos_keys


def split_by_label(uids, labels):
    """
    계정을 라벨에 따라 두 무더기로 가른다. 06의 같은 함수와 뜻이 같다.

    라벨이 없거나 bot/human이 아닌 계정은 비교에서 빠진다. 어느 무더기에
    넣을지 알 수 없으면 비교 자체가 성립하지 않기 때문이며, 01이 1,869계정
    전원에 라벨을 달아 두었으므로 실제로는 나올 일이 아니다.
    """
    bot, human, other = [], [], []
    for uid in sorted(uids):
        lab = labels.get(uid)
        if lab == GROUP1:
            bot.append(uid)
        elif lab == GROUP2:
            human.append(uid)
        else:
            other.append(uid)
    return bot, human, other


# ════════════════════════════════════════════════════════════════════════
# [2] 표본 구성 — 한 서브레딧 안으로 들어간다
# ════════════════════════════════════════════════════════════════════════
def merge_blocks(account, subs):
    """
    04-1이 저장한 서브레딧별 블록에서 지정한 방들만 골라 하나로 합친다.

    표본 A는 방이 하나(politics)라 합칠 것이 없지만, 표본 B는 news와
    worldnews 두 방을 더한다. 더하는 방식은 '카운트끼리 더하기'다 — 문서수·
    문장수·토큰수는 그냥 합이고, 기능어·UPOS·자질 사전은 같은 키끼리 더한다.

    비율을 먼저 내고 평균 내지 않는 이유: 뉴스방에 문서 2건, 월드뉴스방에
    200건을 쓴 계정에서 두 방의 비율을 반반 섞으면 2건짜리가 200건짜리와
    같은 무게를 갖는다. 카운트를 더한 뒤 한 번 나누면 그 계정이 실제로 쓴
    글의 비중대로 섞인다 — 05가 계정 하나를 통째로 나눈 것과 같은 눈금이다.

    해당 방의 블록이 하나도 없으면 None을 돌려준다(그 계정은 이 표본에 없다).
    """
    blocks = [account["서브레딧별"][s] for s in subs if s in account["서브레딧별"]]
    if not blocks:
        return None
    merged = {"문서수": 0, "문장수": 0, "토큰수": 0, "토큰수_구두점제외": 0,
              "기능어": {}, "UPOS": {}, "자질": {}}
    for b in blocks:
        for k in ("문서수", "문장수", "토큰수", "토큰수_구두점제외"):
            merged[k] += b.get(k, 0)
        for fld in ("기능어", "UPOS", "자질"):
            for k, n in b.get(fld, {}).items():
                merged[fld][k] = merged[fld].get(k, 0) + n
    return merged


def build_sample(accounts, subs):
    """
    표본 하나를 만든다. 반환은 (적격 계정 블록, 탈락 사유별 개수).

    적격 기준은 그 서브셋 안에서 문서 10건 이상이다. 01이 계정 전체에 걸었던
    기준과 같은 수를 같은 뜻으로 다시 건다 — "이 방에서 이 사람이 어떻게
    쓰는가"를 재려면 이 방에서 쓴 글이 그만큼은 있어야 한다.

    문턱을 결과를 보고 정하지 않았다는 것이 여기서 중요하다. 10은 01이 이미
    쓰던 수이고 보관된 13-19 사전선언의 14항(현 09-3)이 "01과 같이"라고 못 박은 수다.
    """
    kept, dropped = {}, {"방없음": 0, "문서부족": 0}
    for uid, a in accounts.items():
        m = merge_blocks(a, subs)
        if m is None:
            dropped["방없음"] += 1
            continue
        if m["문서수"] < MIN_DOCS:
            dropped["문서부족"] += 1
            continue
        kept[uid] = m
    return kept, dropped


def build_rates(sample, words):
    """
    표본 블록에서 05와 같은 꼴의 사용률 사전을 만든다.

    분모는 그 서브셋의 토큰수_구두점제외다(05의 「분모_정의」를 서브셋에
    그대로 옮긴 것). 계정 전체의 분모를 쓰면 politics에서 쓴 the의 횟수를
    다른 방까지 포함한 토큰으로 나누게 되어, politics를 조금만 쓴 계정의
    사용률이 통째로 눌린다.

    저장은 05와 같이 희소하게 한다 — 0회인 단어는 키를 만들지 않는다.
    06에서 복사해 온 word_vector()가 .get(w, 0.0)으로 0을 채우므로 그래야
    맞는다(그 함수의 주석 참고).

    분모가 0인 계정은 나눗셈이 성립하지 않아 표본에서 뺀다. 05가 분모 0을
    따로 세어 둔 것과 같은 처리이며, 문서 10건 이상인 계정에서 토큰이 하나도
    없을 수는 없으므로 실제로는 비어 있어야 한다.
    """
    rates, zero = {}, []
    presence = {w: 0 for w in words}
    for uid in sorted(sample):
        a = sample[uid]
        denom = a["토큰수_구두점제외"]
        if denom == 0:
            zero.append(uid)
            continue
        fw = a["기능어"]
        row = {}
        for w in words:
            n = fw.get(w, 0)
            if n:
                presence[w] += 1
                row[w] = n / denom
        rates[uid] = {"총사용률": sum(fw.get(w, 0) for w in words) / denom,
                      "분모": denom, "사용률": row}
    return rates, presence, zero


# ════════════════════════════════════════════════════════════════════════
# [자가검증] 검정 기계와 09-3의 규칙을 각각 고정 예제로 건다
# ════════════════════════════════════════════════════════════════════════
def self_check_stats():
    """
    06에서 복사해 온 U·δ·BH가 손계산과 맞는지 본다. 06의 세 예제 그대로다.

    왜 복사해 왔는데도 또 보나. 복사가 잘못될 수 있어서가 아니라, 이 파일이
    쓰는 상수(SIG_DIGITS 같은 것)나 파이썬 판본이 달라져 같은 소스가 다른
    답을 낼 수 있어서다. 해시 대조는 '글자가 같은가'를 보고, 이 예제는
    '답이 같은가'를 본다. 둘은 다른 질문이다.

    ── 예제 1. 완전 분리 ─────────────────────────────────────
        A(그룹1) = [1, 2, 3],  B(그룹2) = [4, 5, 6]
        순위 1 2 3 4 5 6, R_A = 6, U_A = 6 − 3·4/2 = 0
        δ = 2·0/9 − 1 = −1.0,  σ² = (9/12)·7 = 5.25
    ── 예제 2. 동점 포함 ─────────────────────────────────────
        A = [1, 1, 2],  B = [1, 2, 2]
        1은 평균 순위 2, 2는 평균 순위 5 → R_A = 2+2+5 = 9, U_A = 3.0
        δ = 6/9 − 1 = −1/3,  Σ(t³−t) = 24+24 = 48
        σ² = (9/12)·(7 − 48/30) = 0.75 × 5.4 = 4.05  (동점이 폭을 좁힌다)
    ── 예제 3. BH 보정 ───────────────────────────────────────
        p = [0.01, 0.02, 0.03, 0.04] → p_(i)·4/i 가 넷 다 0.04 → q 전부 0.04
    """
    print("\n  ── (1) 검정 기계 — 06의 세 예제 ──")
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


def self_check_sample():
    """
    09-3이 새로 만든 규칙 두 가지를 손으로 푼 예제로 건다.

    ── 예제 ㉮ 서브레딧 필터와 적격 판정 ──────────────────────
    네 계정의 방별 문서수가 이렇다고 하자.
        갑  politics 12 · news 5
        을  politics  9 · news 6 · worldnews 7
        병  worldnews 20
        정  politics 10
    표본 A는 politics 문서 10건 이상이다.
        갑 12 ≥ 10 → 적격 · 을 9 < 10 → 탈락 · 병 politics 방 자체가 없음
        정 10 ≥ 10 → 적격 (경계값이다. '이상'이므로 들어온다)
        → 표본 A = [갑, 정]
    표본 B는 news + worldnews 를 더한 수가 10건 이상이다.
        갑 5 → 탈락 · 을 6+7 = 13 → 적격 · 병 20 → 적격 · 정 두 방 없음
        → 표본 B = [을, 병]
    갑과 을이 표본을 맞바꾸는 것이 이 예제의 요점이다. 같은 계정이 방마다
    다른 표본에 들어가고, 어느 표본에도 못 들어가는 계정이 생긴다.

    ── 예제 ㉯ 서브셋 분모 · 축 내부 비율 · 결측 ───────────────
    두 계정의 politics 블록만 있다고 하자.
        갑  구두점 제외 20토큰 · 기능어 the 4 · we 1
            자질 Tense=Past 3 · Tense=Pres 1 · Voice=Pass 2
            품사 DET 4 · NOUN 10 · PUNCT 3
        을  구두점 제외 10토큰 · 기능어 the 1 · 자질 Number=Sing 5 · 품사 NOUN 8
    사용률(분모는 그 서브셋의 구두점 제외 토큰수)
        갑 총사용률 (4+1)/20 = 0.25 · the 4/20 = 0.20 · must 0/20 = 0.00
        을 총사용률 1/10 = 0.10
        must는 한 번도 안 나왔지만 결측이 아니라 0이다. 안 쓴 것도 자료다.
    축 판별(자료 전체 기준 — 07 규칙)
        Tense = {Past, Pres} → 대립값 2종 → 축내부합 분모
        Voice = {Pass} · Number = {Sing} → 대립값 1종 → 토큰 분모
    비율
        갑 Tense=Past  3/(3+1) = 0.75   "시제를 표시할 때 과거를 얼마나 고르나"
        을 Tense=Past  Tense 축이 0회 → 0/0 → 결측(None)
           분자가 0인 것과 분모가 0인 것은 전혀 다른 사건이다. 앞은 "안 골랐다"는
           정보이고, 뒤는 "잴 거리가 없다"는 뜻이다.
        갑 Voice=Pass  2/20 = 0.10 · 을 Voice=Pass  0/10 = 0.00
        을 Number=Sing 5/10 = 0.50 · 갑 Number=Sing 0/20 = 0.00
        갑 DET 4/20 = 0.20 · PUNCT 3/20 = 0.15 · 을 DET 0/10 = 0.00
    """
    ok = True

    print("\n  ── (2) 서브레딧 필터와 적격 판정 ──")
    toy = {uid: {"서브레딧별": {s: {"문서수": n, "문장수": 0, "토큰수": 0,
                                "토큰수_구두점제외": 0, "기능어": {},
                                "UPOS": {}, "자질": {}}
                            for s, n in docs.items()}}
           for uid, docs in SELF_CHECK_DOCS.items()}
    for label, subs, expect in (("표본 A(politics)", SAMPLE_A[1], SELF_CHECK_ELIGIBLE_A),
                                ("표본 B(news+worldnews)", SAMPLE_B[1], SELF_CHECK_ELIGIBLE_B)):
        kept, dropped = build_sample(toy, subs)
        got = sorted(kept)
        good = got == sorted(expect)
        ok = ok and good
        print(f"    {label}  (문서 {MIN_DOCS}건 이상)")
        print(f"      기대 {expect} · 실제 {got}  {'통과' if good else '실패'}")
        print(f"      탈락 사유  방없음 {dropped['방없음']} · "
              f"문서부족 {dropped['문서부족']}")

    print("\n  ── (3) 서브셋 분모 · 축 내부 비율 · 결측 ──")
    words = ["the", "we", "must"]
    rates, presence, zero = build_rates(SELF_CHECK_BLOCKS, words)
    for uid, item, expect, why in SELF_CHECK_RATE:
        actual = (rates[uid]["총사용률"] if item == "총사용률"
                  else rates[uid]["사용률"].get(item, 0.0))
        good = abs(actual - expect) <= SELF_CHECK_TOL
        ok = ok and good
        print(f"    {uid} {item:<8} 기대 {expect:>5.3f} · 실제 {actual:>5.3f} "
              f"{'통과' if good else '실패'}   {why}")

    axis_map = build_axis_map(SELF_CHECK_BLOCKS)
    feat_keys = ["Tense=Past", "Voice=Pass", "Number=Sing"]
    print(f"    축 판별  " + " · ".join(
        f"{ax}={{{','.join(vs)}}}→{denom_kind_of(ax + '=' + vs[0], axis_map)}"
        for ax, vs in sorted(axis_map.items())))
    ratios, _aux, _pres = compute_ratios(SELF_CHECK_BLOCKS, feat_keys, axis_map)
    for uid, key, expect, why in SELF_CHECK_FEAT:
        actual = ratios[uid][key]
        if expect is None:
            good = actual is None
            shown = " 결측 "
        else:
            good = actual is not None and abs(actual - expect) <= SELF_CHECK_TOL
            shown = f"{actual:>5.3f}"
        ok = ok and good
        exp_shown = " 결측 " if expect is None else f"{expect:>5.3f}"
        print(f"    {uid} {key:<12} 기대 {exp_shown} · 실제 {shown} "
              f"{'통과' if good else '실패'}   {why}")

    upos_keys = ["DET", "PUNCT", "NOUN"]
    uratios, _p = compute_upos_ratios(SELF_CHECK_BLOCKS, upos_keys)
    for uid, key, expect, why in SELF_CHECK_UPOS:
        actual = uratios[uid][key]
        good = actual is not None and abs(actual - expect) <= SELF_CHECK_TOL
        ok = ok and good
        print(f"    {uid} {key:<12} 기대 {expect:>5.3f} · 실제 {actual:>5.3f} "
              f"{'통과' if good else '실패'}   {why}")
    return ok


def self_check():
    """세 관문을 차례로 걸고, 하나라도 실패하면 본 계산을 시작하지 않는다."""
    line("[자가검증] 손으로 푼 예제와 맞춰 본다 — 실패하면 여기서 끝낸다")
    ok1 = self_check_stats()
    ok2 = self_check_sample()
    ok = ok1 and ok2
    if not ok:
        print()
        print("■ 중단 — 자가검증 실패")
        print("  본 계산을 시작하지 않습니다. 짚어 볼 곳:")
        print("   · 검정 실패 → 06에서 복사한 소스가 손상됐는지 해시 대조를 먼저 보라")
        print("   · 필터 실패 → build_sample의 '이상' 부등호(>=)와 방 이름 대소문자")
        print("   · 비율 실패 → build_rates의 분모가 서브셋의 토큰수인지,")
        print("     compute_ratios의 축 판별이 자료 전체에서 유도되는지")
        print("  이 상태로 돌리면 틀린 표가 조용히 나옵니다.")
    else:
        print("\n  세 관문 모두 통과. 본 계산으로 들어간다.")
    return ok


# ════════════════════════════════════════════════════════════════════════
# [3] 표본 하나를 통째로 검정한다
# ════════════════════════════════════════════════════════════════════════
def iqr_of(values):
    """사분위 폭. quartiles()는 06에서 복사해 온 것이고 05와 같은 정의다."""
    q = quartiles(values)
    return q, q["Q3"] - q["Q1"]


def run_sample(name, subs, accounts, labels, words, feat_keys, upos_keys,
               label_total):
    """
    표본 하나를 만들고 네 가지 비교를 돌린다.

        총사용률 1건    BH 가족 밖의 단독 검정 (06과 같다)
        기능어 172종    BH 가족 1
        형태자질 58종   BH 가족 2 (축 내부 비율 · 07 규칙)
        UPOS 17종       BH 가족 3 (토큰 분모)

    세 가족을 따로 보정한다. 서로 다른 m에서 나온 q라 세 표의 q를 한 줄에
    세워 비교하면 안 된다(07의 같은 경고).
    """
    print(f"\n  ── 표본 {name} — 서브레딧 {' + '.join(subs)} ──")
    sample, dropped = build_sample(accounts, subs)
    bot_ids, human_ids, other = split_by_label(sample, labels)
    n_all = len(bot_ids) + len(human_ids)

    surv = {}
    for lab, ids in ((GROUP1, bot_ids), (GROUP2, human_ids)):
        base = label_total[lab]
        surv[lab] = {"적격": len(ids), "전체": base,
                     "생존율": len(ids) / base if base else None}
    print(f"    적격 계정 {len(sample):,}  (탈락 — 방없음 {dropped['방없음']:,} · "
          f"문서부족 {dropped['문서부족']:,})")
    print(f"    봇   {len(bot_ids):>5,} / {label_total[GROUP1]:,}"
          f"   생존율 {surv[GROUP1]['생존율']:.1%}")
    print(f"    사람 {len(human_ids):>5,} / {label_total[GROUP2]:,}"
          f"   생존율 {surv[GROUP2]['생존율']:.1%}")
    print("    생존율 = 이 방에서 문서 10건 이상을 쓴 계정의 비율이다. 낮다는 것은")
    print("    그 집단이 이 방을 덜 썼다는 뜻이고, 표본이 그만큼 그 집단의 일부만")
    print("    대표한다는 뜻이기도 하다. 아래 결과를 읽을 때 함께 봐야 할 수치다.")
    if other:
        print(f"    ※ 라벨이 bot/human이 아닌 계정 {len(other):,}개는 비교에서 빠졌다.")
    if not bot_ids or not human_ids:
        print("    ■ 한쪽 무더기가 비어 비교가 성립하지 않는다. 이 표본은 건너뛴다.")
        return None

    # ── 사용률 ──────────────────────────────────────────────
    rates, presence, zero = build_rates(sample, words)
    if zero:
        print(f"    ※ 분모(구두점 제외 토큰수)가 0인 계정 {len(zero)}개를 뺐다 — "
              "나눗셈 불성립.")
        bot_ids = [u for u in bot_ids if u in rates]
        human_ids = [u for u in human_ids if u in rates]
        n_all = len(bot_ids) + len(human_ids)
    sparse_cut = int(n_all * SPARSE_FRAC)

    # ── 총사용률 (단독) ─────────────────────────────────────
    total, tv1, tv2 = compare_total(bot_ids, human_ids, rates)
    total["방향"] = direction_of(total["델타"])
    q_bot, iqr_bot = iqr_of(tv1)
    q_hum, iqr_hum = iqr_of(tv2)
    iqr_ratio = (iqr_bot / iqr_hum) if iqr_hum else None
    print(f"\n    총 기능어 사용률 (BH 가족 밖 단독 검정)")
    print(" " * 19 + "Q1" + " " * 6 + "중앙" + " " * 8 + "Q3" + " " * 7 + "IQR")
    print(f"      봇    {q_bot['Q1']:>7.2%}   {q_bot['중앙']:>7.2%}   "
          f"{q_bot['Q3']:>7.2%}   {iqr_bot:>7.2%}   (n={len(tv1):,})")
    print(f"      사람  {q_hum['Q1']:>7.2%}   {q_hum['중앙']:>7.2%}   "
          f"{q_hum['Q3']:>7.2%}   {iqr_hum:>7.2%}   (n={len(tv2):,})")
    print(f"      δ = {total['델타']:+.3f} → {total['방향']}   "
          f"z = {total['z']:.3f}   양측 p = {total['p']:.3g}")
    if iqr_ratio is not None:
        print(f"      사분위 폭 비 (봇 ÷ 사람) = {iqr_ratio:.3f}")
        print("      1보다 작으면 봇 쪽이 더 좁게 뭉쳐 있다는 뜻이다 — 옛 산포검정(보관)이")
        print("      잡은 '봇의 뭉침'이 같은 방 안에서도 남는지를 보는 수치다.")

    # ── 기능어 172종 ────────────────────────────────────────
    frows = compare_words(words, bot_ids, human_ids, rates, presence)
    f_notable = summarize_family(frows, len(words), sparse_cut, n_all,
                                 f"기능어 {len(words)}종", key_name="단어")

    # ── 형태자질 58종 · UPOS 17종 ───────────────────────────
    axis_map = build_axis_map(sample)
    kinds = {k: denom_kind_of(k, axis_map) for k in feat_keys}
    ratios, aux, fpresence = compute_ratios(sample, feat_keys, axis_map)
    # 분모 0으로 뺀 계정은 비율 표에서도 빼 준다 — 검정에 들어가는 계정 목록이
    # 세 가족에서 같아야 표를 나란히 읽을 수 있다.
    mrows, m_family = compare_family(feat_keys, bot_ids, human_ids, ratios,
                                     fpresence, sparse_cut, kinds)
    m_notable = summarize_family(mrows, m_family, sparse_cut, n_all,
                                 f"형태자질 {len(feat_keys)}종", key_name="자질")

    uratios, upresence = compute_upos_ratios(sample, upos_keys)
    urows, u_family = compare_family(upos_keys, bot_ids, human_ids, uratios,
                                     upresence, sparse_cut)
    u_notable = summarize_family(urows, u_family, sparse_cut, n_all,
                                 f"UPOS {len(upos_keys)}종", key_name="품사")

    return {"이름": name, "서브레딧": list(subs),
            "n_bot": len(bot_ids), "n_human": len(human_ids),
            "적격계정수": len(sample), "탈락": dropped, "생존율": surv,
            "분모0계정": zero, "희소기준": sparse_cut,
            "총사용률": total, "총사용률_봇요약": q_bot, "총사용률_사람요약": q_hum,
            "IQR": {"봇": iqr_bot, "사람": iqr_hum, "비": iqr_ratio},
            "기능어_행": frows, "형태자질_행": mrows, "UPOS_행": urows,
            "BH가족": {"기능어": len(words), "형태자질": m_family,
                     "UPOS": u_family},
            "주목": {"기능어": [w for w, _ in f_notable],
                   "형태자질": [k for k, _ in m_notable],
                   "UPOS": [k for k, _ in u_notable]},
            "축분류": {ax: {"값목록": vs, "분모종류": denom_kind_of(ax + "=" + vs[0],
                                                          axis_map)}
                    for ax, vs in sorted(axis_map.items())}}


def summarize_family(rows, n_family, sparse_cut, n_all, label, key_name="항목"):
    """가족 하나의 요약과 |δ| 상위 표를 찍는다. 06·07의 같은 블록과 한 서식이다."""
    testable = [(k, r) for k, r in rows if r.get("검정가능", True)]
    sig_n = sum(1 for _, r in rows if r.get("유의"))
    notable = [(k, r) for k, r in rows if r.get("주목")]
    up = sum(1 for _, r in notable if r["델타"] > 0)
    down = sum(1 for _, r in notable if r["델타"] < 0)
    sparse_n = sum(1 for _, r in notable
                   if r.get("희소", r.get("출현계정수", 0) < sparse_cut))

    print(f"\n    [{label}]  BH 가족 {n_family}종")
    if len(testable) != len(rows):
        print(f"      검정 불가로 가족에서 빠짐 {len(rows) - len(testable)}종")
    print(f"      유의 (q ≤ {Q_ALPHA})  {sig_n:>4}종   "
          f"주목 (그리고 |δ| ≥ {DELTA_NOTABLE})  {len(notable):>4}종"
          f"   (봇 높음 {up} · 봇 낮음 {down} · 희소 {sparse_n})")

    shown = notable[:TOP_SHOW]
    if shown:
        print(f"      |δ| 상위 {len(shown)}종")
        print(TABLE_HEAD)
        for k, r in shown:
            mark = "  희소" if r.get("희소",
                                   r.get("출현계정수", 0) < sparse_cut) else ""
            n_eff = r.get("봇_유효n", 0) + r.get("사람_유효n", 0) or n_all
            print(f"      {k:<13}{r['델타']:>+7.3f}  {r['방향']}  {r['q']:>8.4f}"
                  f"  {r['봇_중앙']:>8.3%}  {r['사람_중앙']:>8.3%}"
                  f"  {n_eff:>5,}{mark}")
    else:
        print("      주목 항목 없음.")
    return notable


# ════════════════════════════════════════════════════════════════════════
# [4] 머리 10종 대조 — 06·07의 δ 옆에 표본 A의 δ를 세운다
# ════════════════════════════════════════════════════════════════════════
def lookup(rows, key):
    """가족 목록에서 항목 하나를 찾는다. 없으면 None."""
    for k, r in rows:
        if k == key:
            return r
    return None


def head10_table(ref, res_a, res_b):
    """
    머리 10종을 06·07의 δ와 나란히 적고 유지/무너짐/뒤집힘을 판정한다.

    판정 규칙(보관된 13-19 사전선언의 14항(현 09-3) — 결과를 보고 만든 것이 아니다):
        유지    |δ_A| ≥ 0.147 이고 부호가 06·07과 같다
        뒤집힘  부호가 06·07과 반대다 (크기와 무관하게 해석이 바뀐다)
        무너짐  부호는 같은데 |δ_A| < 0.147 이다
        판정불가 결측 처리 후 한쪽 무더기가 비어 δ가 없다
    q는 걸지 않는다. 표본이 1,869에서 1,000 언저리로 줄었으니 q는 그만큼
    커지는 것이 정상이고, 그것을 '차이가 사라졌다'로 읽으면 안 된다(09-2의 교훈).
    """
    out = []
    for name, fam in HEAD10:
        rows_a = res_a["기능어_행"] if fam == "F" else res_a["형태자질_행"]
        ra = lookup(rows_a, name)
        rb = None
        if res_b:
            rows_b = res_b["기능어_행"] if fam == "F" else res_b["형태자질_행"]
            rb = lookup(rows_b, name)
        d0 = ref[name]
        if ra is None or ra.get("델타") is None or not ra.get("검정가능", True):
            out.append({"항목": name, "가족": fam, "기준δ": d0, "표본Aδ": None,
                        "표본Bδ": None, "변화": None, "판정": "판정불가"})
            continue
        d1 = ra["델타"]
        same_sign = (d0 > 0 and d1 > 0) or (d0 < 0 and d1 < 0)
        if not same_sign:
            verdict = "뒤집힘"
        elif abs(d1) >= DELTA_NOTABLE:
            verdict = "유지"
        else:
            verdict = "무너짐"
        db = None
        if rb is not None and rb.get("델타") is not None:
            db = rb["델타"]
        out.append({"항목": name, "가족": fam, "기준δ": d0, "표본Aδ": d1,
                    "표본Bδ": db, "변화": d1 - d0, "판정": verdict,
                    "q_A": ra.get("q")})
    return out


def print_head10(table):
    print("\n      06·07이 잡은 머리 10종을 politics 안에서 다시 잰 결과다.")
    print("      기준 δ는 06_비교결과.json·07_형태자질비교.json에서 그대로 읽어 왔다.")
    print(HEAD10_HEAD)
    for r in table:
        if r["표본Aδ"] is None:
            print(f"      {r['항목']:<14}{r['기준δ']:>+9.3f}"
                  f"{'—':>11}{'—':>11}   판정불가")
            continue
        b = f"{r['표본Bδ']:>+9.3f}" if r["표본Bδ"] is not None else f"{'—':>9}"
        print(f"      {r['항목']:<14}{r['기준δ']:>+9.3f}{r['표본Aδ']:>+11.3f}"
              f"{r['변화']:>+11.3f}   {r['판정']:<6}   {b}")
    print("\n      유지  = |δ| ≥ 0.147 이고 부호가 같다 — 방을 통제해도 남는 차이다.")
    print("      무너짐 = 부호는 같은데 효과가 small 경계 밑으로 내려갔다.")
    print("      뒤집힘 = 부호가 반대다 — 06·07의 해석을 그 항목에 대해 철회한다.")
    print("      표본 B는 보조다. 판정에 넣지 않고 방향이 같은지만 곁눈질한다.")


# ════════════════════════════════════════════════════════════════════════
# [5] 사전 예측 대조 — 이 파일의 핵심
# ════════════════════════════════════════════════════════════════════════
def check_predictions(table, res_a):
    """
    P14-1 ~ P14-4를 실제 수치와 대조한다. 판정은 문장 단위 전부-아니면-빗나감이다
    (보관된 13-19 사전선언의 공통 원칙 「판정 규칙」, 07과 같다).
    """
    results = []

    # P14-1 — 머리 10종 전부 유지, 뒤집힘 0
    kept = [r for r in table if r["판정"] == "유지"]
    broken = [r for r in table if r["판정"] == "무너짐"]
    flipped = [r for r in table if r["판정"] == "뒤집힘"]
    undec = [r for r in table if r["판정"] == "판정불가"]
    if undec:
        v1 = "일부 판정불가"
    elif len(kept) == len(table):
        v1 = "적중"
    else:
        v1 = "빗나감"
    results.append({"번호": "P14-1", "판정": v1,
                    "기대": "머리 10종 전부 |δ| ≥ 0.147 유지 · 뒤집힘 0",
                    "실제": f"유지 {len(kept)} · 무너짐 {len(broken)} · "
                          f"뒤집힘 {len(flipped)} · 판정불가 {len(undec)}",
                    "무너진항목": [r["항목"] for r in broken],
                    "뒤집힌항목": [r["항목"] for r in flipped]})

    # P14-2 — 총사용률 δ < 0
    d = res_a["총사용률"]["델타"]
    v2 = "적중" if d < 0 else "빗나감"
    results.append({"번호": "P14-2", "판정": v2,
                    "기대": "총사용률 δ < 0 (봇이 낮음)",
                    "실제": f"δ = {d:+.4f} ({direction_of(d)})"})

    # P14-3 — IQR 비 < 1
    ratio = res_a["IQR"]["비"]
    if ratio is None:
        v3 = "판정불가"
        real3 = "사람 IQR이 0이라 비를 낼 수 없다"
    else:
        v3 = "적중" if ratio < 1.0 else "빗나감"
        real3 = f"봇 IQR {res_a['IQR']['봇']:.4%} ÷ 사람 IQR " \
                f"{res_a['IQR']['사람']:.4%} = {ratio:.4f}"
    results.append({"번호": "P14-3", "판정": v3,
                    "기대": "총사용률 사분위 폭 비(봇 ÷ 사람) < 1", "실제": real3})

    # P14-4 — 봇 생존율 < 사람 생존율
    sb = res_a["생존율"][GROUP1]["생존율"]
    sh = res_a["생존율"][GROUP2]["생존율"]
    v4 = "적중" if sb < sh else "빗나감"
    results.append({"번호": "P14-4", "판정": v4,
                    "기대": "politics 표본의 봇 생존율 < 사람 생존율",
                    "실제": f"봇 {sb:.1%} ({res_a['생존율'][GROUP1]['적격']:,}/"
                          f"{res_a['생존율'][GROUP1]['전체']:,}) · "
                          f"사람 {sh:.1%} ({res_a['생존율'][GROUP2]['적격']:,}/"
                          f"{res_a['생존율'][GROUP2]['전체']:,})"})
    return results


def print_predictions(results):
    print("\n      보관된 13-19_사전선언 「14 서브레딧 통제」(현 09-3)의 예측 넷을")
    print("      실제와 대조한다.")
    print("      아래 문장들은 결과를 보기 전에 확정된 것이다. 빗나간 예측도 지우거나")
    print("      고치지 않고 그대로 싣는다 — 그것이 사전등록의 요점이다.")
    for res in results:
        src = next(p for p in PREDICTIONS if p["번호"] == res["번호"])
        print()
        print(f"      {res['번호']}  {src['서술']}")
        print(f"        기대  {res['기대']}")
        print(f"        실제  {res['실제']}")
        print(f"        → {res['판정']}")
        for ln in src["근거"]:
            print(f"          {ln}")
        if res["번호"] == "P14-1" and (res.get("무너진항목") or res.get("뒤집힌항목")):
            print()
            print("        ■ 사전선언이 미리 적어 둔 처분이 발동한다.")
            if res.get("무너진항목"):
                print(f"          무너진 항목: {', '.join(res['무너진항목'])}")
            if res.get("뒤집힌항목"):
                print(f"          뒤집힌 항목: {', '.join(res['뒤집힌항목'])}")
            print("          '무너지면 그 항목은 서브레딧 화법이었다는 뜻이며 06·07")
            print("          해석에서 철회한다' — 지금 와서 문구를 고치는 것이 아니라")
            print("          그 약속을 실행하는 것이다. 해당 항목은 봇의 문체 지문이")
            print("          아니라 봇이 있던 방의 화법으로 다시 적어야 한다.")


# ════════════════════════════════════════════════════════════════════════
# [저장] JSON 한 벌
# ════════════════════════════════════════════════════════════════════════
def pack_rows(rows):
    """가족 하나를 JSON에 담을 꼴로 바꾼다. |δ| 내림차순 순서를 그대로 유지한다."""
    out = {}
    for k, r in rows:
        item = {
            "U": rnd(r.get("U"), STAT_DIGITS),
            "z": rnd(r.get("z"), STAT_DIGITS),
            "p": None if r.get("p") is None else sig(r["p"]),
            "q": None if r.get("q") is None else sig(r["q"]),
            "델타": rnd(r.get("델타"), STAT_DIGITS),
            "방향": r.get("방향"),
            "봇_중앙": rnd(r.get("봇_중앙"), RATE_DIGITS),
            "사람_중앙": rnd(r.get("사람_중앙"), RATE_DIGITS),
            "유의": bool(r.get("유의")),
            "주목": bool(r.get("주목")),
        }
        for extra in ("축", "분모종류", "검정가능", "봇_유효n", "사람_유효n",
                      "결측계정수", "출현계정수", "희소"):
            if extra in r:
                item[extra] = r[extra]
        out[k] = item
    return out


def pack_sample(res):
    """표본 하나를 JSON에 담을 꼴로 바꾼다."""
    if res is None:
        return None
    t = res["총사용률"]
    return {
        "이름": res["이름"], "서브레딧": res["서브레딧"],
        "적격계정수": res["적격계정수"], "탈락": res["탈락"],
        "n_bot": res["n_bot"], "n_human": res["n_human"],
        "생존율": {k: {"적격": v["적격"], "전체": v["전체"],
                    "생존율": rnd(v["생존율"], RATE_DIGITS)}
                 for k, v in res["생존율"].items()},
        "분모0계정": res["분모0계정"],
        "희소기준": res["희소기준"],
        "총사용률_비교": {
            "U": rnd(t["U"], STAT_DIGITS), "z": rnd(t["z"], STAT_DIGITS),
            "p": sig(t["p"]), "델타": rnd(t["델타"], STAT_DIGITS),
            "방향": t["방향"],
            "봇_요약": {k: rnd(v, RATE_DIGITS)
                     for k, v in res["총사용률_봇요약"].items()},
            "사람_요약": {k: rnd(v, RATE_DIGITS)
                      for k, v in res["총사용률_사람요약"].items()},
            "IQR": {k: rnd(v, RATE_DIGITS) for k, v in res["IQR"].items()},
            "비고": "BH 가족 밖의 단독 검정이다 — 세 가족의 q 계산에 넣지 않았다.",
        },
        "BH가족": res["BH가족"],
        "주목": res["주목"],
        "축분류": res["축분류"],
        "기능어": pack_rows(res["기능어_행"]),
        "형태자질": pack_rows(res["형태자질_행"]),
        "UPOS": pack_rows(res["UPOS_행"]),
    }


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    print("=" * 74)
    print("서브레딧 통제 — 같은 방 안에서 봇과 사람을 다시 견준다")
    print("=" * 74)

    # ── [1/9] 입력 ──────────────────────────────────────────────
    print("\n[1/9] 입력 적재")
    for path in (EXPAND_JSON, ACCOUNTS_JSON, RATES_JSON, COMPARE_JSON,
                 FEATURE_JSON, COMPARE_PY, FEATURE_PY):
        if not os.path.exists(path):
            print(f"      {path} 이(가) 없습니다. 아무것도 하지 않고 끝냅니다.")
            return
    conf13, obs13, accounts = load_expand()
    fw, words = load_word_list()
    ref, total6, feat_keys, upos_keys = load_reference_deltas()
    print(f"      04-1_확장재파싱.json  계정 {len(accounts):,}개 "
          f"(실행일 {conf13.get('실행일', '?')})")
    print(f"      기능어 {len(words)}종 · 형태자질 {len(feat_keys)}종 · "
          f"UPOS {len(upos_keys)}종")

    gate = conf13.get("정합관문", {})
    print(f"\n      04-1의 정합 관문  {'통과' if gate.get('통과') else '불통과'}"
          f"   (합계 일치 {gate.get('합계일치')} · "
          f"계정별 172종 일치 {gate.get('계정별172종_일치계정수')}계정 / "
          f"불일치 {gate.get('계정별172종_불일치계정수')}계정)")
    if gate.get("통과"):
        print("      04-1의 카운트가 04와 전 계정 일치했다. 04를 다시 열어 대조할")
        print("      필요가 없으므로 서브레딧별 카운트를 그대로 쓴다.")
    else:
        print("      ■ 04-1의 관문이 불통과다. 보관된 13-19 사전선언의 13항(현 04-1)에")
        print("        따라 이후 단계는 04를 정본으로 삼아야 한다. 서브레딧별 분해는")
        print("        04에 없는 정보이므로 이 결과는 '04-1이 옳다는 가정 위에서만'")
        print("        읽어야 한다.")

    print(f"\n      승계 해시  기능어 {fw.get('기능어_개수')}종 · "
          f"{fw.get('기능어_해시')}")
    print(f"      04-1이 적어 둔 승계 해시  {conf13.get('승계해시', {}).get('기능어172')}")
    print("      02가 만든 목록으로 04가 세고, 05가 나누고, 06이 비교하고,")
    print("      04-1이 서브레딧별로 다시 세고, 09-3이 그 안에서 다시 나눈다. 같은")
    print("      해시가 이 파일들에 이어져 있으면 사슬이 끊기지 않은 것이다.")

    labels = load_labels()
    line("라벨 개봉")
    print("  ■ 여기서 라벨을 읽는다. ■  04-1은 이 키를 한 번도 열지 않았다.")
    print("  서브레딧을 복원하고 토큰을 세는 일에는 어느 계정이 봇인지 알 필요가")
    print("  없었고, 실제로 모르는 채로 했다. 09-3은 그렇게 굳어진 카운트를 방별로")
    print("  나누기만 한다 — 이 파일에서 표본을 고르는 기준(방 이름·문서 10건)은")
    print("  사전선언에 미리 적힌 것이고, 라벨을 보고 정한 것이 아니다.")
    all_bot, all_human, all_other = split_by_label(accounts, labels)
    label_total = {GROUP1: len(all_bot), GROUP2: len(all_human)}
    print(f"\n  전체  봇 {len(all_bot):,}계정 · 사람 {len(all_human):,}계정")
    if all_other:
        print(f"  ※ 라벨이 bot/human이 아닌 계정 {len(all_other):,}개")

    # 위협의 크기를 먼저 적어 둔다 — 이 파일이 왜 필요한지의 근거다.
    share = {}
    for lab, ids in ((GROUP1, all_bot), (GROUP2, all_human)):
        tot = sum(accounts[u]["문서수"] for u in ids)
        pol = sum(accounts[u]["서브레딧별"].get("politics", {}).get("문서수", 0)
                  for u in ids)
        share[lab] = {"문서수": tot, "politics": pol,
                      "비중": pol / tot if tot else None}
    print(f"\n  politics 문서 비중  봇 {share[GROUP1]['비중']:.1%} "
          f"({share[GROUP1]['politics']:,}/{share[GROUP1]['문서수']:,}) · "
          f"사람 {share[GROUP2]['비중']:.1%} "
          f"({share[GROUP2]['politics']:,}/{share[GROUP2]['문서수']:,})")
    print("  이 두 수의 차이가 09-3이 겨냥하는 위협 자체다. 두 집단이 애초에 다른")
    print("  방에서 글을 썼다면, 06·07이 잡은 것이 문체인지 방인지 구별할 수 없다.")

    # ── [2/9] 승계 확인 ─────────────────────────────────────────
    print("\n[2/9] 06·07 함수 승계 확인 (ast로 원본과 사본을 다시 떠서 대조)")
    all_ok = True
    for names, want, src, tag in (
            (COPIED_06_CORE, COPIED_06_CORE_HASH, COMPARE_PY, "06 통계 7개"),
            (COPIED_06_EXTRA, COPIED_06_EXTRA_HASH, COMPARE_PY, "06 비교절차 3개"),
            (COPIED_07, COPIED_07_HASH, FEATURE_PY, "07 분모·결측·가족 8개")):
        ok, h_src, h_copy = verify_copied(names, want, src)
        all_ok = all_ok and ok
        print(f"      {tag:<18} 원본 {h_src} · 사본 {h_copy} · 기대 {want}  "
              f"{'통과' if ok else '실패'}")
        print(f"        {', '.join(names)}")
    if not all_ok:
        print("\n■ 중단 — 복사한 소스가 원본과 다릅니다. 본 계산을 시작하지 않습니다.")
        return
    print("      06의 통계 7개 해시는 04-1이 승계한 것과 같은 값이어야 한다.")

    # ── [3/9] 자가검증 ──────────────────────────────────────────
    print("\n[3/9] 자가검증")
    if not self_check():
        return

    # ── [4/9]·[5/9] 표본 A·B ────────────────────────────────────
    print("\n[4/9] 표본 A — 판정용")
    res_a = run_sample(SAMPLE_A[0], SAMPLE_A[1], accounts, labels, words,
                       feat_keys, upos_keys, label_total)
    if res_a is None:
        print("■ 중단 — 표본 A가 성립하지 않습니다.")
        return

    print("\n[5/9] 표본 B — 보조 (판정에 쓰지 않는다)")
    res_b = run_sample(SAMPLE_B[0], SAMPLE_B[1], accounts, labels, words,
                       feat_keys, upos_keys, label_total)

    # ── [6/9] 머리 10종 대조 ────────────────────────────────────
    print("\n[6/9] 머리 10종 대조 — 06·07의 δ 옆에 표본 A의 δ를 세운다")
    table = head10_table(ref, res_a, res_b)
    print_head10(table)

    # ── [7/9] 축분류 대조 ───────────────────────────────────────
    print("\n[7/9] 축 판별이 07과 같은가")
    d7conf = json.load(open(FEATURE_JSON, encoding="utf-8"))["축분류"]
    diff = []
    for ax, info in res_a["축분류"].items():
        want = d7conf.get(ax, {}).get("분모종류")
        if want and want != info["분모종류"]:
            diff.append((ax, want, info["분모종류"]))
    print(f"      07의 축 {len(d7conf)}개 · 표본 A의 축 {len(res_a['축분류'])}개")
    if diff:
        print("      ※ 분모 종류가 달라진 축이 있다 — 표본에서 어떤 대립값이 사라져")
        print("        단일값 축이 된 경우다. 07의 규칙은 '자료에서 유도한다'이므로")
        print("        규칙을 어긴 것이 아니라 규칙이 자료를 따라간 것이다. 다만 그")
        print("        자질의 δ는 07과 같은 눈금이 아니므로 아래에 적어 둔다.")
        for ax, w, g in diff:
            print(f"        {ax}  07 {w} → 표본A {g}")
    else:
        print("      모든 축의 분모 종류가 07과 같다. 같은 눈금으로 잰 것이다.")

    # ── [8/9] 사전 예측 대조 ────────────────────────────────────
    line("[8/9] 사전 예측 대조")
    preds = check_predictions(table, res_a)
    print_predictions(preds)

    # ── [9/9] 저장 ──────────────────────────────────────────────
    print("\n[9/9] 저장")
    elapsed = time.time() - t0
    method = (
        "04-1이 저장한 서브레딧별 카운트에서 지정한 방의 문서만 합쳐 사용률을 "
        "다시 만들고, 06·07과 같은 검정을 다시 돌렸다. Mann-Whitney U(양측, "
        "동점 평균 순위 · 동점 보정 분산 · 연속성 보정 0.5) · Cliff's δ "
        "(그룹1 = bot 기준) · Benjamini-Hochberg FDR. 기능어 172종 · 형태자질 "
        "58종 · UPOS 17종을 각각 별개의 BH 가족으로 두고 따로 보정했다. "
        "총사용률 1건은 가족 밖 단독 검정이다. 형태자질의 분모는 07 규칙 "
        "(대립값 2종 이상인 축은 축 내부 합, 아니면 구두점 제외 토큰수)이고 "
        "분모 0은 결측으로 두어 그 자질의 검정에서만 뺐다. 검정·분모·결측 "
        "구현은 06·07에서 ast로 소스를 그대로 떠 왔다(해시 대조 통과). "
        f"주목 = q ≤ {Q_ALPHA} 그리고 |δ| ≥ {DELTA_NOTABLE}. "
        "머리 10종의 판정만은 q를 걸지 않고 |δ| 유지 여부와 방향으로 했다 — "
        "표본이 줄면 q가 커지는 것이 정상이기 때문이다(보관된 13-19 사전선언의 14항(현 09-3))."
    )
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "방법": method,
            "그룹1": GROUP1, "그룹2": GROUP2,
            "입력파일": {
                "13": os.path.basename(EXPAND_JSON),
                "01_라벨": os.path.basename(ACCOUNTS_JSON),
                "05_목록해시": os.path.basename(RATES_JSON),
                "06_기준δ": os.path.basename(COMPARE_JSON),
                "07_기준δ": "07_형태자질비교.json",
                "06_통계원본": os.path.basename(COMPARE_PY),
                "07_분모원본": "07_형태자질비교.py",
            },
            "승계해시": {
                "기능어172": fw.get("기능어_해시"),
                "13이_적어둔_값": conf13.get("승계해시", {}).get("기능어172"),
                "06_통계7개": COPIED_06_CORE_HASH,
                "06_비교절차3개": COPIED_06_EXTRA_HASH,
                "07_분모결측8개": COPIED_07_HASH,
                "복사한_함수": {"06_통계": COPIED_06_CORE,
                            "06_절차": COPIED_06_EXTRA,
                            "07_분모결측": COPIED_07},
            },
            "라벨_사용": "있음. 01의 '라벨' 키를 load_labels() 한 자리에서 읽었다. "
                      "04-1은 읽지 않았다.",
            "13_정합관문": {"통과": gate.get("통과"),
                        "합계일치": gate.get("합계일치"),
                        "계정별172종_일치계정수": gate.get("계정별172종_일치계정수"),
                        "계정별172종_불일치계정수": gate.get("계정별172종_불일치계정수")},
            "표본정의": {"A": {"서브레딧": list(SAMPLE_A[1]), "역할": "판정용",
                          "적격": f"그 방 문서 {MIN_DOCS}건 이상"},
                     "B": {"서브레딧": list(SAMPLE_B[1]), "역할": "보조",
                           "적격": f"두 방 합 {MIN_DOCS}건 이상"}},
            "판정규칙": f"머리 10종은 |δ| ≥ {DELTA_NOTABLE} 유지와 방향으로만 "
                     "판정한다. q 조건은 걸지 않는다(표본 축소, 보관된 13-19 사전선언의 14항(현 09-3)).",
            "저장자릿수": {"비율": RATE_DIGITS, "통계": STAT_DIGITS,
                       "p·q": f"유효숫자 {SIG_DIGITS}자리"},
            "총소요초": round(elapsed, 1),
        },
        "전체_politics비중": {k: {"문서수": v["문서수"], "politics": v["politics"],
                             "비중": rnd(v["비중"], RATE_DIGITS)}
                         for k, v in share.items()},
        "기준δ": {"머리10종": {k: v for k, v in ref.items()},
                "06_총사용률": total6},
        "표본A": pack_sample(res_a),
        "표본B": pack_sample(res_b),
        "머리10종_대조": [{**r,
                      "기준δ": rnd(r["기준δ"], STAT_DIGITS),
                      "표본Aδ": rnd(r["표본Aδ"], STAT_DIGITS),
                      "표본Bδ": rnd(r["표본Bδ"], STAT_DIGITS),
                      "변화": rnd(r["변화"], STAT_DIGITS),
                      "q_A": None if r.get("q_A") is None else sig(r["q_A"])}
                     for r in table],
        "예측판정": preds,
    }
    write_json(OUT_JSON, out, indent=1)
    print(f"      {OUT_JSON}")
    print(f"      {os.path.getsize(OUT_JSON):,} bytes")
    print(f"      총 소요 {elapsed:.1f}초")

    # ── 눈으로 검수할 것 ────────────────────────────────────────
    line("확인 항목")
    print("  아래를 직접 보고 나서 결과를 쓰십시오.")
    print("   1. 머리 10종 중 무너지거나 뒤집힌 항목이 있으면, 그 항목을 06·07")
    print("      해석에서 실제로 빼라. 사전선언에 그렇게 적어 두었다. 표만 싣고")
    print("      본문은 그대로 두는 것이 가장 흔한 배신이다.")
    print("   2. 생존율을 함께 보라. 봇의 politics 생존율이 크게 낮다면, 표본 A의")
    print("      봇은 '정치방에 자주 쓰는 봇'만 남은 것이다. 방은 통제했지만 그")
    print("      대가로 봇의 일부만 남았다 — 남은 차이가 봇 전체의 성질인지는 이")
    print("      표가 답하지 못한다. 무엇을 통제하면 무엇이 좁아지는지의 교환이다.")
    print("   3. 표본 B(news+worldnews)의 δ가 표본 A와 방향이 다르면, 그 항목은")
    print("      방마다 다르게 움직이는 것이다. 두 표본에서 같은 방향으로 크게")
    print("      남은 항목만이 '방과 무관한 문체'라고 부를 자격이 있다.")
    print("   4. δ가 06·07보다 오히려 커진 항목이 있는지 보라. 방을 맞추자 신호가")
    print("      선명해졌다는 뜻이고, 06·07에서는 방의 혼합이 오히려 차이를 흐리고")
    print("      있었다는 말이 된다. 그런 항목은 본문에서 앞자리에 세울 만하다.")
    print("   5. 축 판별이 07과 달라진 축이 있으면 그 자질의 δ를 07과 나란히 읽지")
    print("      말라. 분모가 다르면 같은 이름의 다른 수치다.")
    print()
    print("  이 다섯은 스크립트가 대신 판정할 수 없는 것들이다. 수치를 뽑는")
    print("  일까지가 코드의 몫이고, 무엇을 철회할지는 사람이 정한다.")


if __name__ == "__main__":
    main()
