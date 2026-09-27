#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
04-1_확장재파싱.py
────────────────────────────────────────────────────────────────────────────
목적
    04가 저장하지 않은 세 가지를 계정마다 확보한다.
        ① 서브레딧별 카운트      — 09-3(politics 한정 재검정)의 재료
        ② 변형 목록 후보 표면형  — 02-1(임계값 민감도)의 재료
        ③ 문장 길이 목록과 's의 품사별 카운트 — 08(R 블록)·옛 17 s분리(보관)의 재료
    새로 재는 것이 아니라, 04가 한 번 지나가며 버렸던 정보를 같은 길로 다시
    지나가며 줍는 일이다. 그래서 이름이 '재파싱'이다.

왜 04를 고치지 않고 새 파일을 만드나
    04·05·06·07은 이미 결과를 냈고, 그 결과로 사전선언 두 벌이 쓰였다.
    측정 파일을 뒤늦게 고치면 앞의 산출물이 어느 판으로 나온 것인지 아무도
    말할 수 없게 된다. 보관된 13-19 사전선언의 첫 줄이 "01~07의 산출물은 한 글자도
    바꾸지 않는다"인 이유다. 04-1은 04를 읽지도 고치지도 않고 원본에서 다시
    시작하되, 끝에서 04와 숫자가 같은지를 검사한다(아래 [정합 관문]).

라벨 규율 — 이 파일은 라벨을 읽지 않는다
    04와 같다. 01_적격계정.json 에서 "계정" 키만 꺼내고 "라벨"이 든 나머지는
    즉시 버린다(del). 04-1이 서브레딧을 붙이고 표면형을 세는 판단에 봇/사람이
    한 번도 개입하지 않았다는 사실이, 09-3·02-1·08과 옛 17~19(보관)가 그 값으로
    비교를 할 수 있는 근거다. 라벨은 뒤 단계(09-3·02-1·08)에서 연다.

무엇을 어떻게 하나 (네 가지 판단)
    1. 서브레딧은 '복원'한다.
       01_적격계정.json에는 정제된 문서 문자열만 있고 그 글이 어느 서브레딧에
       올라간 것인지가 없다. 원본 user_post_comment.json을 01과 똑같은 순서로
       (적재 → clean_doc → 시각 정렬 → 200건 상한) 다시 처리하되, 이번에는
       각 문서에 subreddit을 함께 실어 나른다. 그리고 그렇게 만든 문서 목록이
       01의 목록과 순서·내용까지 같은지 계정마다 대조한다. 어긋나는 계정은
       서브레딧을 '미상'으로 두고 개수를 기록한다(보관된 13-19 사전선언의 13항(현 04-1)).

    2. 파싱에 넣는 문서는 01의 문자열 그대로다.
       복원이 일치한 계정에서도 파서에 넘기는 것은 01 JSON의 문자열이다.
       서브레딧은 위치(몇 번째 문서인가)로만 갖다 붙인다. 이렇게 해야 04가
       파서에 넣은 것과 글자 하나까지 같은 입력이 되고, 뒤의 정합 관문이
       '입력이 같은가'가 아니라 '파서가 같은 답을 내는가'만 묻게 된다.

    3. 표면형은 02의 변형 목록 9개의 합집합만 센다.
       02-1이 (빈도 {3,5,10}) × (닫힌비율 {0.4,0.5,0.6}) 아홉 목록으로 재검정을
       한다. 아홉 벌을 따로 세면 파싱을 아홉 번 해야 하므로, 합집합 U를 한 번
       세어 두고 02-1이 목록별로 골라 쓰게 한다. U에 없는 표면형은 세지 않는다
       — 전체 어휘를 다 담으면 파일이 수십 배가 되고, 02-1이 쓸 일도 없다.

    4. 원카운트만 저장한다. 04와 같은 원칙이다.
       사용률(나눗셈)은 09-3·02-1·08과 옛 17 s분리(보관)가 각자의 분모 규칙으로 계산한다.
       04-1은 분자와 분모 후보를 모아 두기만 한다.

정합 관문 — 이 파일의 성패는 여기서 갈린다
    보관된 13-19 사전선언의 13항(현 04-1)이 미리 못 박은 다섯 합계와
    계정별 172종 카운트가 04와 전부 같아야 한다.
        문서 110,057 · 문장 242,251 · 토큰 4,214,937
        구두점 제외 3,756,059 · 기능어 토큰 1,550,348
        계정별 172종 카운트가 1,869계정 전부 동일
    같으면 04-1의 확장 재료를 04와 한 표에 놓고 써도 된다는 뜻이고, 다르면
    파서가 04 실행 때와 다르게 작동하고 있다는 뜻이다. 어긋나도 저장은
    마치되 설정.정합관문에 실패를 적고, 이후 단계는 04를 정본으로 삼는다.

실행
    터미널에서:
        python3 -u 04-1_확장재파싱.py
    시험 실행(앞의 N계정만, 별도 파일로):
        python3 -u 04-1_확장재파싱.py 20
    필요 패키지: stanza (04와 같은 1.14.0). 그 밖에는 표준 라이브러리만 쓴다.

    1,869계정 110,057문서라 45~60분이 걸린다. 100계정마다 중간 저장하므로
    창을 닫아도 다음 실행이 이어서 한다.

산출
    04-1_확장재파싱.json      계정별 확장 카운트. 09-3·02-1·08과 옛 17 s분리(보관)의 입력.
    04-1_확장재파싱_진행.json 중간 저장 파일. 전부 끝나면 지운다.
"""

import ast
import functools
import hashlib
import importlib.util
import json
import math
import os
import platform
import statistics
import sys
import time
from collections import Counter

# 진행 표시가 즉시 화면에 찍히게 한다(04와 같은 이유 — 한 시간짜리 작업이
# 버퍼에 갇히면 멈춘 것처럼 보인다).
print = functools.partial(print, flush=True)


# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                          # 연구주제/ (원본 데이터·UD 캐시가 있는 곳)
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"            # "계정" 키만 쓴다
CENSOR_PY = f"{HERE}/01_botsim_적격검열.py"           # 정제 함수를 그대로 빌려 쓴다
FUNCLIST_PY = f"{HERE}/02_기능어목록_생성.py"          # 변형 목록 생성 절차
FUNCWORDS_JSON = f"{HERE}/02_기능어목록.json"          # 기준선 172종 대조용
UD_CACHE = f"{ROOT}/02_UD캐시"                        # 02가 받아 둔 UD EWT
MEASURE_JSON = f"{HERE}/04_기능어측정.json"            # 정합 관문 대조 상대
RATES_JSON = f"{HERE}/05_사용률검수.json"              # 해시 사슬 승계
COMPARE_PY = f"{HERE}/06_봇사람비교.py"                # 통계 함수의 원본
RAW_JSON = (f"{ROOT}/1. 원본데이터/2. BotSim Data/BotSim-24-Dataset"
            f"/user_post_comment.json")               # 서브레딧이 있는 원본

OUT_JSON = f"{HERE}/04-1_확장재파싱.json"
PROGRESS_JSON = f"{HERE}/04-1_확장재파싱_진행.json"

CHECKPOINT_EVERY = 100      # 04와 같은 간격으로 중간 저장한다
WARMUP_ACCOUNTS = 20        # 처음 20계정의 실측 속도로 끝나는 시각을 추정한다

# ── 02 변형 목록의 격자 (보관된 13-19 사전선언의 15항(현 02-1)) ───────────
VARIANT_FREQS = (3, 5, 10)          # MIN_FREQ 후보
VARIANT_RATIOS = (0.4, 0.5, 0.6)    # DOMINANT_RATIO 후보
BASELINE_FREQ, BASELINE_RATIO = 5, 0.50     # 02가 쓴 기준선 — 172종이 나와야 한다

# ── 해시 사슬 (사전선언 공통) ───────────────────────────────────
EXPECTED_FW_HASH = "382b68572f03bc23"   # 05 JSON의 설정에 적힌 기능어 172종 해시

# ── 04가 남긴 다섯 합계 (보관된 13-19 사전선언의 13항(현 04-1)이 미리 못 박은 값) ──
GATE_TOTALS = {
    "문서수": 110057,
    "문장수": 242251,
    "토큰수": 4214937,
    "토큰수_구두점제외": 3756059,
    "기능어토큰": 1550348,
}
GATE_ACCOUNTS = 1869

# ── 06에서 AST로 복사해 온 함수들 ───────────────────────────────
# 아래 [승계] 절이 실행할 때마다 06의 원본과 이 파일의 사본을 각각 ast로 다시
# 떠서 해시를 맞춰 본다. 사본을 손대면 그 자리에서 걸린다.
COPIED_NAMES = ["normal_cdf", "ranks_with_ties", "mann_whitney",
                "bh_qvalues", "quartiles", "sig", "direction_of"]
COPIED_HASH = "b3de6ef352db03a1"    # 위 7개 소스를 이 순서로 이은 sha256 앞 16자
SIG_DIGITS = 6          # 06의 sig()가 참조하는 상수 — 06과 같은 값이다

# ── 자가검증 고정 예제 ───────────────────────────────────────────
# (1) 06의 세 예제. 손계산은 06_봇사람비교.py의 self_check() docstring에 있다.
SELF_CHECK_U = [
    ("완전 분리", [1, 2, 3], [4, 5, 6], 0.0, -1.0, 5.25),
    ("동점 포함", [1, 1, 2], [1, 2, 2], 3.0, -1.0 / 3.0, 4.05),
]
SELF_CHECK_BH_P = [0.01, 0.02, 0.03, 0.04]
SELF_CHECK_BH_Q = [0.04, 0.04, 0.04, 0.04]
SELF_CHECK_TOL = 1e-9

# (2) 04의 토큰화 예제. 축약형이 분해되고 굽은 아포스트로피가 정규화돼야
#     아래 기대값이 나온다. 04와 같은 잣대로 세고 있는지 보는 관문이다.
SELF_CHECK_TEXT = "I don't think they've seen it, and it isn't mine."
SELF_CHECK_TEXT_CURLY = "I don’t think they’ve seen it, and it isn’t mine."
SELF_CHECK_EXPECT = {"n't": 4, "'ve": 2}

RATE_DIGITS = 6         # 실수 저장 자릿수 (사전선언 공통 규약: 소수 6자리)
UNKNOWN_SUB = "미상"     # 01 목록과 복원이 어긋난 계정의 서브레딧 표시


def line(title=""):
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def fmt_dur(sec):
    """초를 사람이 읽는 단위로 바꾼다(04와 같다)."""
    if sec < 90:
        return f"{sec:.0f}초"
    if sec < 5400:
        return f"{sec / 60:.1f}분"
    return f"{sec / 3600:.2f}시간"


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다(04·05·06의 같은 함수).

    임시 파일에 먼저 쓰고 이름을 바꿔치기한다(os.replace). 쓰는 도중에 멈춰도
    파일은 '이전 것' 아니면 '새 것'이지, 반쯤 잘린 것이 되지 않는다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def load_module(path, name):
    """
    파일 경로로 모듈을 불러온다.

    01·02의 파일 이름에는 숫자와 한글이 들어 있어 import 문으로는 부를 수
    없다(모듈 이름 규칙에 어긋난다). 그래서 경로로 직접 적재한다. 정제 규칙을
    베껴 쓰지 않고 원본 함수를 그대로 부르기 위한 우회다 — 베끼는 순간
    01과 04-1이 서로 다른 규칙을 갖게 될 여지가 생긴다.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def normalize_apostrophe(s):
    """
    굽은 아포스트로피(’ U+2019)를 곧은 것(' U+0027)으로 바꾼다. 04와 같다.

    원문 아포스트로피의 37%가 굽은 쪽이고, 글자 모양은 쓴 도구를 따라간다.
    도구가 라벨과 상관될 수 있으므로 정규화하지 않으면 "봇이 축약형을 덜
    쓴다"는 가짜 신호가 생긴다. 토큰과 목록 양쪽에 똑같이 건다.
    """
    return s.replace("’", "'")


# ════════════════════════════════════════════════════════════════════════
# [승계] 06에서 AST로 복사한 통계 함수 — 아래 7개는 06의 소스 그대로다
# ════════════════════════════════════════════════════════════════════════
# 손으로 옮겨 적지 않았다. ast 모듈로 06_봇사람비교.py를 파싱해 함수 정의의
# 소스 조각을 그대로 떠 왔고, 실행할 때마다 verify_copied_functions()가
# 06의 원본과 이 파일의 사본을 다시 떠서 해시를 맞춘다. 통계 구현이 단계마다
# 조금씩 달라지는 것 — 같은 자로 재고 있다는 주장을 무너뜨리는 가장 흔한
# 경로 — 를 코드로 막아 두는 것이다.
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
# [1] 입력 적재 — 라벨은 읽지 않는다
# ════════════════════════════════════════════════════════════════════════
def load_accounts():
    """
    01에서 "계정" 키만 꺼낸다. 라벨이 든 나머지는 즉시 버린다.

    04가 했던 것과 같은 일이다. 규율을 말로만 두지 않고 코드로 박아 두면,
    라벨이 담긴 객체 자체가 메모리에 남지 않아 실수로 참조할 수도 없다.
    """
    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    accounts = data["계정"]
    del data
    return accounts


def load_inherited_hash():
    """05 JSON에서 기능어 해시를 읽어 온다(해시 사슬 승계)."""
    conf = json.load(open(RATES_JSON, encoding="utf-8"))["설정"]
    return conf.get("04승계", {}), conf.get("실행일")


# ════════════════════════════════════════════════════════════════════════
# [2] 02 변형 목록 아홉 벌과 합집합
# ════════════════════════════════════════════════════════════════════════
def build_variant_lists(m02):
    """
    02의 절차를 그대로 써서 (빈도 3·5·10) × (닫힌비율 0.4·0.5·0.6) 아홉 벌을 만든다.

    02가 하는 일은 셋뿐이다 — UD English-EWT에서 (단어, 품사) 쌍을 세고,
    빈도가 문턱 미만이면 버리고, 그 단어가 닫힌 어류로 태그된 비율이 문턱
    미만이면 버린다. 여기서는 02의 read_conllu()와 CLOSED_CLASS를 그대로
    부르고 두 문턱만 갈아 끼운다. 선별 논리를 베껴 쓰지 않으므로 02와
    04-1이 다른 규칙을 갖게 될 여지가 없다.

    각 목록에는 04와 같은 아포스트로피 정규화를 건다. 정규화 뒤 중복이
    합쳐지므로(n’t → n't) 목록이 몇 종 줄어든다 — 02 원본 174종이 172종이
    됐던 것과 같은 일이다.

    반환: {"f5_r0.50": [단어…], …}  (키는 사람이 읽을 수 있는 이름)
    """
    paths = [f"{UD_CACHE}/{f}" for f in m02.UD_FILES]
    for p in paths:
        if not os.path.exists(p):
            raise FileNotFoundError(p)
    counts, n_tokens = m02.read_conllu(paths)

    lists = {}
    for freq in VARIANT_FREQS:
        for ratio in VARIANT_RATIOS:
            picked = set()
            for word, pos_counter in counts.items():
                total = sum(pos_counter.values())
                if total < freq:                       # 기준 1 — 최소 빈도
                    continue
                closed = sum(n for pos, n in pos_counter.items()
                             if pos in m02.CLOSED_CLASS)
                if closed / total < ratio:             # 기준 2 — 닫힌 어류 비율
                    continue
                picked.add(normalize_apostrophe(word))
            lists[f"f{freq}_r{ratio:.2f}"] = sorted(picked)
    return lists, n_tokens, len(counts)


def list_hash(words):
    """목록 하나의 지문. 06·04가 쓴 방식과 같다(줄바꿈으로 이어 sha256 앞 16자)."""
    return hashlib.sha256("\n".join(words).encode("utf-8")).hexdigest()[:16]


# ════════════════════════════════════════════════════════════════════════
# [3] 서브레딧 복원 — 01과 같은 순서로 원본을 다시 처리한다
# ════════════════════════════════════════════════════════════════════════
def rebuild_docs(user, m01, max_docs=None):
    """
    원본의 계정 한 덩어리에서 (정제 문서, 서브레딧) 목록을 만든다.

    01의 build_accounts()가 하던 일을 그대로 하되 subreddit을 함께 들고 간다.
    순서가 중요하다 — 01과 한 단계라도 어긋나면 문서 목록이 달라지고, 그러면
    서브레딧이 엉뚱한 문서에 붙는다.

        1) posts → comment_1 → comment_2 순으로 펼친다
           (01의 load_raw가 이 순서다. 같은 시각의 글이 여럿일 때 파이썬의
            정렬이 안정적이라 이 순서가 그대로 남는다 — 순서를 바꾸면
            동점 시각에서 목록이 달라진다)
        2) 01의 clean_doc()을 그대로 부른다(자기폭로 문장 절제 → URL·멘션
           제거 → 20자 검사). 함수를 빌려 오므로 규칙이 어긋날 수 없다.
        3) 작성 시각 문자열 오름차순으로 정렬한다
        4) 200건(01의 MAX_DOCS)을 넘으면 뒤쪽 200건만 남긴다 = 최근분

    max_docs를 인자로 둔 것은 자가검증에서 작은 상한(2건)으로 절삭 규칙을
    시험하기 위해서다. 본 계산에서는 01의 MAX_DOCS를 그대로 쓴다.
    """
    if max_docs is None:
        max_docs = m01.MAX_DOCS

    items = []
    for p in (user.get("posts") or []):
        items.append((str(p.get("posts") or ""),
                      str(p.get("created_utc") or ""),
                      p.get("subreddit")))
    for block in ("comment_1", "comment_2"):
        for c in (user.get(block) or []):
            items.append((str(c.get("comment_body") or ""),
                          str(c.get("created_utc") or ""),
                          c.get("subreddit")))

    rows = []
    for text, ts, sub in items:
        cleaned, _reason, _excised = m01.clean_doc(text)
        if cleaned is None:
            continue
        rows.append((str(ts or ""), cleaned, sub))

    rows.sort(key=lambda r: r[0])
    if len(rows) > max_docs:
        rows = rows[-max_docs:]
    return [(c, s) for _, c, s in rows]


def restore_subreddits(accounts, raw, m01):
    """
    계정마다 복원 결과를 01의 문서 목록과 대조하고 서브레딧 배열을 만든다.

    ■ 대조에 통과한 계정에서도, 파서에 넘기는 문서는 01의 문자열이다. ■
    복원본이 아니라 01 본을 쓴다. 두 목록이 같다고 확인했으니 어느 쪽을 써도
    같지만, 04가 파서에 넣은 것과 '같은 객체 경로'로 들어가야 뒤의 정합
    관문이 입력 차이가 아니라 파서 차이만 묻게 된다.

    어긋난 계정은 서브레딧 전부를 '미상'으로 둔다. 문서 목록이 다르면 몇
    번째 문서에 어느 서브레딧이 붙는지 알 수 없고, 반쯤 맞은 배열을 넘기면
    09-3이 politics 문서를 잘못 세게 된다. 개수를 세어 로그에 남긴다
    (보관된 13-19 사전선언의 13항(현 04-1): "불일치 계정은 서브레딧 미상").

    반환: (uid → 서브레딧 리스트, 일치 계정 수, 불일치 계정 목록[:상세])
    """
    subs_by_uid = {}
    n_match = 0
    mismatches = []
    for uid in sorted(accounts):
        docs01 = accounts[uid]
        user = raw.get(uid)
        if user is None:
            mismatches.append((uid, "원본에 계정이 없음", len(docs01), 0))
            subs_by_uid[uid] = [UNKNOWN_SUB] * len(docs01)
            continue
        rebuilt = rebuild_docs(user, m01)
        if [d for d, _ in rebuilt] == docs01:
            n_match += 1
            subs_by_uid[uid] = [str(s) if s else UNKNOWN_SUB for _, s in rebuilt]
        else:
            mismatches.append((uid, "문서 목록 불일치", len(docs01), len(rebuilt)))
            subs_by_uid[uid] = [UNKNOWN_SUB] * len(docs01)
    return subs_by_uid, n_match, mismatches


# ════════════════════════════════════════════════════════════════════════
# [4] 파이프라인 — 04가 쓴 것과 같은 구성이어야 한다
# ════════════════════════════════════════════════════════════════════════
def build_pipeline():
    """
    04와 글자까지 같은 파이프라인을 만든다.

        processors="tokenize,pos" · use_gpu=False · 계정 단위 bulk_process

    한 글자라도 다르면 정합 관문이 04와 어긋날 것이고, 어긋난 원인이 파서
    구성 때문인지 다른 무엇 때문인지 가릴 수 없게 된다.
    """
    import stanza
    print("      파이프라인 생성 중...")
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos",
                          verbose=False, use_gpu=False, download_method=None)
    print("      완료")
    return nlp


# ════════════════════════════════════════════════════════════════════════
# [5] 계정 하나를 재는 함수 — 이 파일의 심장
# ════════════════════════════════════════════════════════════════════════
def aggregate(parsed, subs, funcword_set, union_set):
    """
    파싱 결과 한 계정분을 받아 확장 카운트 한 벌을 만든다.

    parsed 는 문서 객체의 목록이고, 각 문서는 .sentences → .words →
    (.text, .upos, .feats) 를 갖는다. stanza의 Document가 그 모양이고,
    자가검증은 같은 모양의 아주 작은 가짜 객체를 넣는다. 집계 규칙을 파서
    없이도 손으로 검사할 수 있게 하려는 것이다 — 파서를 부르는 검사는
    "파서가 이렇게 태그했으니 이렇게 나온다"가 되어 손계산이 성립하지 않는다.

    subs 는 문서와 같은 길이의 서브레딧 이름 배열이다. 문서 i의 모든 문장·
    토큰이 subs[i]에 쌓인다.

    ── 세는 것 ────────────────────────────────────────────────
    서브레딧별 : 문서수 · 문장수 · 토큰수 · 토큰수_구두점제외 ·
                 기능어 172종 · UPOS · 형태자질   (09-3이 쓴다)
    표면형_합집합 : 변형 목록 합집합 U에 든 표면형의 횟수. 서브레딧을 나누지
                 않는다 — 02-1은 계정 단위로만 보기 때문이다. 파일 크기가
                 서브레딧 수만큼 불어나는 것도 막는다.
    s_분리     : 표면형이 "'s"인 토큰을 UPOS별로 센다. PART=소유격(dog's),
                 AUX/VERB=축약(it's). 06의 's(+0.799)가 두 가지를 한 칸에
                 섞어 놓아 해석이 막혔던 것을 옛 17 s분리(보관)가 푼다.
    문장길이   : 문장마다 구두점을 뺀 토큰수. 08의 변동계수 재료다.
                 이 목록의 길이는 반드시 문장수와 같아야 한다(아래 검산).

    ── 04와 같아야 하는 것 ────────────────────────────────────
    합계 필드(문서수·문장수·토큰수·토큰수_구두점제외·기능어)는 04의
    measure_account()와 같은 규칙으로 센다. 구두점 판정은 UPOS PUNCT,
    기능어는 소문자+아포스트로피 정규화 표면형이 172종 목록에 있으면 1회,
    품사 조건은 걸지 않는다. 정합 관문이 이 필드들을 04와 맞춰 본다.

    카운트는 0을 담지 않는다(희소 저장). 04·05가 쓴 방식 그대로다.
    """
    per_sub = {}
    fw_all = Counter()          # 계정 합계 기능어(04 대조용)
    union_all = Counter()       # 변형 목록 합집합 표면형
    s_split = Counter()         # "'s"의 UPOS별
    sent_lens = []
    n_sent = n_tok = n_nopunct = 0

    for i, doc in enumerate(parsed):
        sub = subs[i] if i < len(subs) else UNKNOWN_SUB
        bucket = per_sub.get(sub)
        if bucket is None:
            bucket = per_sub[sub] = {
                "문서수": 0, "문장수": 0, "토큰수": 0, "토큰수_구두점제외": 0,
                "기능어": Counter(), "UPOS": Counter(), "자질": Counter(),
            }
        bucket["문서수"] += 1

        for sent in doc.sentences:
            n_sent += 1
            bucket["문장수"] += 1
            sent_len = 0
            for w in sent.words:
                n_tok += 1
                bucket["토큰수"] += 1
                bucket["UPOS"][w.upos] += 1
                if w.upos != "PUNCT":
                    n_nopunct += 1
                    bucket["토큰수_구두점제외"] += 1
                    sent_len += 1

                surface = normalize_apostrophe(w.text.lower())
                if surface in funcword_set:
                    fw_all[surface] += 1
                    bucket["기능어"][surface] += 1
                if surface in union_set:
                    union_all[surface] += 1
                if surface == "'s":
                    key = w.upos if w.upos in ("PART", "AUX", "VERB") else "기타"
                    s_split[key] += 1

                if w.feats:
                    for kv in w.feats.split("|"):
                        bucket["자질"][kv] += 1
            sent_lens.append(sent_len)

    return {
        "문서수": len(parsed),
        "문장수": n_sent,
        "토큰수": n_tok,
        "토큰수_구두점제외": n_nopunct,
        "기능어": dict(fw_all.most_common()),
        "서브레딧별": {
            sub: {
                "문서수": b["문서수"],
                "문장수": b["문장수"],
                "토큰수": b["토큰수"],
                "토큰수_구두점제외": b["토큰수_구두점제외"],
                "기능어": dict(b["기능어"].most_common()),
                "UPOS": dict(b["UPOS"].most_common()),
                "자질": dict(b["자질"].most_common()),
            }
            for sub, b in sorted(per_sub.items())
        },
        "표면형_합집합": dict(union_all.most_common()),
        "s_분리": {k: s_split.get(k, 0) for k in ("PART", "AUX", "VERB", "기타")},
        "문장길이": sent_lens,
    }


def measure_account(nlp, docs, subs, funcword_set, union_set):
    """계정 하나를 04와 같은 방식(계정 단위 bulk_process)으로 파싱해 집계한다."""
    parsed = nlp.bulk_process(docs)
    return aggregate(parsed, subs, funcword_set, union_set)


# ════════════════════════════════════════════════════════════════════════
# [6] 자가검증 관문 — 네 가지를 통과해야 본 계산에 들어간다
# ════════════════════════════════════════════════════════════════════════
class _낱말:
    """자가검증용 가짜 토큰. stanza Word가 갖는 세 속성만 흉내 낸다."""
    def __init__(self, text, upos, feats=None):
        self.text, self.upos, self.feats = text, upos, feats


class _문장:
    def __init__(self, words):
        self.words = words


class _문서:
    def __init__(self, sentences):
        self.sentences = sentences


def gate_1_statistics():
    """
    관문 1 — 06에서 복사한 U·δ·BH가 손계산과 맞는가.

    06의 self_check()가 쓰던 세 예제 그대로다. 손계산은 06의 docstring에 있다.
        예제 1 완전 분리  A=[1,2,3] B=[4,5,6] → U_A=0, δ=−1, σ²=5.25
        예제 2 동점 포함  A=[1,1,2] B=[1,2,2] → U_A=3, δ=−1/3, σ²=4.05
        예제 3 BH        p=[.01,.02,.03,.04] → q=[.04,.04,.04,.04]
    04-1은 검정을 돌리지 않지만, 09-3·02-1·08과 옛 17~19(보관)가 쓸 함수가 이 파일에 사본으로 들어와
    있으므로 사본이 원본과 같은 답을 내는지 여기서 확인해 둔다.
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


def gate_2_restore(m01):
    """
    관문 2 — 서브레딧 복원 규칙(손으로 푼 예제).

    가짜 계정 하나를 만들어 rebuild_docs()에 넣는다. 원본 항목은 다섯이고,
    셋만 살아남아야 한다.

        posts   "Short."                              시각 300  politics
                → 정제 후 6자. 20자 미만이라 탈락.
        posts   "Politics is the art of the possible today."  시각 200  politics
                → 41자. 통과.
        posts   "see https://example.com/aaa…"        시각 050  politics
                → URL을 지우면 "see" 3자. 탈락.
                  ■ URL을 먼저 지우고 길이를 재는 순서가 여기서 드러난다.
                    순서가 반대면 이 글이 '긴 글'로 위장해 살아남는다.
        comment_1 "This news comment is long enough to survive."  시각 100  news
                → 통과.
        comment_2 "Worldnews comment body that is quite long here." 시각 400  worldnews
                → 통과.

    시각 오름차순으로 정렬하면 100(news) · 200(politics) · 400(worldnews).
    posts를 먼저 펼쳤어도 정렬이 끝나면 comment_1의 글이 맨 앞에 온다.

    상한 절삭도 같은 자료로 시험한다. 상한을 2로 두면 뒤쪽 둘만 남아야 한다
        → 200(politics) · 400(worldnews).
    '뒤쪽'을 남기는 것은 최근 글을 쓴다는 뜻이다(01의 MAX_DOCS 주석).
    """
    print("\n  ── 관문 2. 서브레딧 복원 — 정제·정렬·상한 (손계산 예제) ──")
    user = {
        "posts": [
            {"posts": "Short.", "created_utc": "300", "subreddit": "politics"},
            {"posts": "Politics is the art of the possible today.",
             "created_utc": "200", "subreddit": "politics"},
            {"posts": "see https://example.com/aaaaaaaaaaaaaaaaaaaaaa",
             "created_utc": "050", "subreddit": "politics"},
        ],
        "comment_1": [
            {"comment_body": "This news comment is long enough to survive.",
             "created_utc": "100", "subreddit": "news"},
        ],
        "comment_2": [
            {"comment_body": "Worldnews comment body that is quite long here.",
             "created_utc": "400", "subreddit": "worldnews"},
        ],
    }
    expect_subs = ["news", "politics", "worldnews"]
    expect_head = ["This news comment", "Politics is the", "Worldnews comment body"]

    got = rebuild_docs(user, m01)
    got_subs = [s for _, s in got]
    got_head = [" ".join(d.split()[:3]) for d, _ in got]
    ok1 = (got_subs == expect_subs and got_head == expect_head)
    print(f"    기대 순서 {expect_subs}")
    print(f"    실제 순서 {got_subs}   {'통과' if ok1 else '실패'}")
    print(f"    실제 문서 머리 {got_head}")

    got2 = rebuild_docs(user, m01, max_docs=2)
    got2_subs = [s for _, s in got2]
    ok2 = got2_subs == ["politics", "worldnews"]
    print(f"    상한 2건 — 기대 ['politics', 'worldnews'] · "
          f"실제 {got2_subs}   {'통과' if ok2 else '실패'}")
    return ok1 and ok2


def gate_3_aggregate(funcword_set, union_set):
    """
    관문 3 — 집계 규칙(손으로 푼 예제). 파서를 부르지 않는다.

    가짜 문서 둘을 만든다. 품사와 표면형을 우리가 정해 넣으므로 기대값이
    손으로 나온다.

      문서 0 (politics)
        문장 1  It/PRON  's/PART  dog/NOUN  ./PUNCT      → 구두점 제외 3
        문장 2  He/PRON  's/AUX(Tense=Pres|Number=Sing)  here/ADV  !/PUNCT
                                                          → 구두점 제외 3
      문서 1 (news)
        문장 1  We/PRON  must/AUX  go/VERB               → 구두점 제외 3

    기대값
        합계        문서 2 · 문장 3 · 토큰 11 · 구두점 제외 9
        politics    문서 1 · 문장 2 · 토큰 8 · 구두점 제외 6
                    기능어 it 1 · 's 2 · he 1
                    UPOS PRON 2 · PART 1 · AUX 1 · NOUN 1 · ADV 1 · PUNCT 2
                    자질 Tense=Pres 1 · Number=Sing 1
        news        문서 1 · 문장 1 · 토큰 3 · 구두점 제외 3
                    기능어 we 1 · must 1
        s_분리      PART 1 · AUX 1 · VERB 0 · 기타 0
                    ■ 06의 's(+0.799)가 이 두 칸을 한데 묶고 있었다.
        문장길이    [3, 3, 3]   — 길이가 3이어야 한다(문장수와 같다)

    대문자 It/He/We가 소문자 키로 모이는지도 이 예제가 함께 본다.
    """
    print("\n  ── 관문 3. 집계 규칙 — 서브레딧·문장길이·'s 분리 (손계산 예제) ──")
    for w in ("it", "'s", "he", "we", "must"):
        if w not in funcword_set:
            print(f"    ■ 예제가 쓰는 낱말 {w!r} 이(가) 172종 목록에 없습니다.")
            return False

    docs = [
        _문서([
            _문장([_낱말("It", "PRON"), _낱말("'s", "PART"),
                   _낱말("dog", "NOUN"), _낱말(".", "PUNCT")]),
            _문장([_낱말("He", "PRON"),
                   _낱말("'s", "AUX", "Tense=Pres|Number=Sing"),
                   _낱말("here", "ADV"), _낱말("!", "PUNCT")]),
        ]),
        _문서([
            _문장([_낱말("We", "PRON"), _낱말("must", "AUX"),
                   _낱말("go", "VERB")]),
        ]),
    ]
    got = aggregate(docs, ["politics", "news"], funcword_set, union_set)

    checks = [
        ("합계 문서수", got["문서수"], 2),
        ("합계 문장수", got["문장수"], 3),
        ("합계 토큰수", got["토큰수"], 11),
        ("합계 구두점제외", got["토큰수_구두점제외"], 9),
        ("politics 문장수", got["서브레딧별"]["politics"]["문장수"], 2),
        ("politics 구두점제외", got["서브레딧별"]["politics"]["토큰수_구두점제외"], 6),
        ("politics 기능어 's", got["서브레딧별"]["politics"]["기능어"].get("'s", 0), 2),
        ("politics 기능어 it", got["서브레딧별"]["politics"]["기능어"].get("it", 0), 1),
        ("politics UPOS PUNCT", got["서브레딧별"]["politics"]["UPOS"].get("PUNCT", 0), 2),
        ("politics 자질 Tense=Pres",
         got["서브레딧별"]["politics"]["자질"].get("Tense=Pres", 0), 1),
        ("news 문서수", got["서브레딧별"]["news"]["문서수"], 1),
        ("news 기능어 must", got["서브레딧별"]["news"]["기능어"].get("must", 0), 1),
        ("s_분리 PART", got["s_분리"]["PART"], 1),
        ("s_분리 AUX", got["s_분리"]["AUX"], 1),
        ("s_분리 VERB", got["s_분리"]["VERB"], 0),
        ("합집합 표면형 we", got["표면형_합집합"].get("we", 0), 1),
    ]
    ok = True
    for name, actual, expect in checks:
        good = actual == expect
        ok = ok and good
        print(f"    {name:<22} 기대 {expect:>3} · 실제 {actual:>3}  "
              f"{'통과' if good else '실패'}")
    good = got["문장길이"] == [3, 3, 3]
    ok = ok and good
    print(f"    {'문장길이':<22} 기대 [3, 3, 3] · 실제 {got['문장길이']}  "
          f"{'통과' if good else '실패'}")
    good = len(got["문장길이"]) == got["문장수"]
    ok = ok and good
    print(f"    {'문장길이 개수 = 문장수':<20} {'통과' if good else '실패'}")
    return ok


def gate_4_tokenizer(nlp, funcword_set, union_set):
    """
    관문 4 — 파서가 04와 같은 잣대로 자르는가.

    04의 자가검증 문장 두 벌(곧은 아포스트로피판과 굽은 판)을 본 계산과
    똑같은 경로(bulk_process → aggregate)로 통과시킨다. 기대값은 04가 쓰던
    상수 그대로 n't 4회 · 've 2회다.

    이 관문이 막는 것: 축약형이 분해되지 않거나(don't가 통짜로 남거나)
    굽은 아포스트로피가 정규화되지 않으면, 목록의 어느 항목과도 일치하지
    않아 조용히 0으로 세어진다. 오류 메시지는 나오지 않는다. 04가 겪은
    일이라 그 문장을 그대로 물려받았다.
    """
    print("\n  ── 관문 4. 파서 토큰화 — 04의 자가검증 문장 그대로 ──")
    print(f'    입력 1 (곧은 \'): "{SELF_CHECK_TEXT}"')
    print(f'    입력 2 (굽은 ’): "{SELF_CHECK_TEXT_CURLY}"')
    got = measure_account(nlp, [SELF_CHECK_TEXT, SELF_CHECK_TEXT_CURLY],
                          ["politics", "politics"], funcword_set, union_set)
    counts = got["기능어"]
    ok = True
    for word, expect in SELF_CHECK_EXPECT.items():
        actual = counts.get(word, 0)
        good = actual == expect
        ok = ok and good
        print(f"    {word:<6} 기대 {expect}회 · 실제 {actual}회   "
              f"{'통과' if good else '실패'}")
    print(f"    (이 문장에서 잡힌 기능어 전체: {counts})")
    return ok


# ════════════════════════════════════════════════════════════════════════
# [7] 중간 저장 / 이어서 하기
# ════════════════════════════════════════════════════════════════════════
def load_progress(path):
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_progress(path, done, fingerprint, elapsed_total):
    """
    끝낸 계정을 통째로 저장한다(04와 같은 방식).

    끝난 것만 담고 남은 목록은 담지 않는다. 다음 실행이 01을 다시 읽어
    "저장된 것에 없는 계정"을 남은 일로 계산하므로 목록을 두 벌 관리하다
    어긋날 일이 없다. 지문이 다르면 이어받지 않는다 — 기준이 다른 수치가
    한 파일에 섞이면 눈으로는 절대 못 잡는다.
    """
    write_json(path, {
        "안내": "04-1번의 중간 저장 파일입니다. 재파싱이 끝나면 자동으로 지워집니다.",
        "지문": fingerprint,
        "완료계정수": len(done),
        "누적소요초": round(elapsed_total, 1),
        "저장시각": time.strftime("%Y-%m-%d %H:%M:%S"),
        "계정": done,
    })


# ════════════════════════════════════════════════════════════════════════
# [8] 정합 관문 — 04와 숫자가 같은가
# ════════════════════════════════════════════════════════════════════════
def consistency_gate(done, pilot):
    """
    보관된 13-19 사전선언의 13항(현 04-1)이 미리 못 박은 관문을 실행한다.

        (가) 다섯 합계가 04와 같은가 — 문서·문장·토큰·구두점 제외·기능어 토큰
        (나) 계정별 172종 카운트가 04와 전 계정 동일한가

    (나)가 이 단계의 성패다. 합계는 계정 사이의 오차가 상쇄돼 우연히 맞을 수
    있지만, 1,869계정 × 172종이 모두 같으려면 파서가 04 실행 때와 똑같이
    작동하는 수밖에 없다. 04의 계정별 스칼라(문서·문장·토큰)도 함께 맞춰
    본다 — 어긋났을 때 원인이 토큰화인지 품사인지 가르는 데 쓴다.

    어긋나도 저장은 마친다. 보관된 13-19 사전선언의 13항(현 04-1): "하나라도 어긋나면 원인을
    로그에 적고, 이후 단계는 13 값이 아니라 04 값을 정본으로 삼는다."(인용문의 13 = 현 04-1)
    """
    ref = json.load(open(MEASURE_JSON, encoding="utf-8"))
    ref_scale = ref["설정"]["처리규모"]
    ref_acc = ref["계정"]

    got_totals = {
        "문서수": sum(a["문서수"] for a in done.values()),
        "문장수": sum(a["문장수"] for a in done.values()),
        "토큰수": sum(a["토큰수"] for a in done.values()),
        "토큰수_구두점제외": sum(a["토큰수_구두점제외"] for a in done.values()),
        "기능어토큰": sum(sum(a["기능어"].values()) for a in done.values()),
    }
    if pilot:
        # 시험 실행은 계정 일부만 돌린다. 사전선언의 다섯 합계는 전량 기준이라
        # 그대로 비교할 수 없으므로, 같은 계정들의 04 값을 더해 기준을 만든다.
        ref_totals = {
            "문서수": sum(ref_acc[u]["문서수"] for u in done),
            "문장수": sum(ref_acc[u]["문장수"] for u in done),
            "토큰수": sum(ref_acc[u]["토큰수"] for u in done),
            "토큰수_구두점제외": sum(ref_acc[u]["토큰수_구두점제외"] for u in done),
            "기능어토큰": sum(sum(ref_acc[u]["기능어"].values()) for u in done),
        }
        기준설명 = f"시험 {len(done)}계정의 04 합계"
    else:
        ref_totals = dict(GATE_TOTALS)
        ref_totals_from_file = {
            "문서수": ref_scale["문서수"], "문장수": ref_scale["문장수"],
            "토큰수": ref_scale["토큰수"],
            "토큰수_구두점제외": ref_scale["토큰수_구두점제외"],
        }
        # 사전선언에 적힌 값과 04 파일의 값이 서로 다르면 그 자체가 사고다.
        for k, v in ref_totals_from_file.items():
            if ref_totals[k] != v:
                print(f"    ■ 사전선언의 {k}({ref_totals[k]:,})와 04 파일의 값"
                      f"({v:,})이 다릅니다. 04 파일을 정본으로 읽습니다.")
                ref_totals[k] = v
        기준설명 = "보관된 13-19 사전선언의 13항(현 04-1)의 다섯 합계(= 04 처리규모)"

    총계일치 = True
    rows = []
    for k in ("문서수", "문장수", "토큰수", "토큰수_구두점제외", "기능어토큰"):
        same = got_totals[k] == ref_totals[k]
        총계일치 = 총계일치 and same
        rows.append((k, ref_totals[k], got_totals[k], same))

    # ── 계정별 172종 ────────────────────────────────────────────
    n_same = 0
    diffs = []
    scalar_diffs = []
    for uid in sorted(done):
        r = ref_acc.get(uid)
        if r is None:
            diffs.append((uid, "04에 계정이 없음", None, None))
            continue
        if done[uid]["기능어"] == r["기능어"]:
            n_same += 1
        else:
            mine, theirs = done[uid]["기능어"], r["기능어"]
            keys = sorted(set(mine) | set(theirs))
            first = [(w, theirs.get(w, 0), mine.get(w, 0))
                     for w in keys if mine.get(w, 0) != theirs.get(w, 0)]
            diffs.append((uid, "172종 카운트 불일치", len(first), first[:5]))
        for f in ("문서수", "문장수", "토큰수", "토큰수_구두점제외"):
            if done[uid][f] != r[f]:
                scalar_diffs.append((uid, f, r[f], done[uid][f]))

    return {
        "기준": 기준설명,
        "합계표": rows,
        "합계일치": 총계일치,
        "계정일치수": n_same,
        "계정불일치수": len(diffs),
        "불일치예시": diffs[:3],
        "스칼라불일치": scalar_diffs[:10],
        "스칼라불일치수": len(scalar_diffs),
        "통과": 총계일치 and not diffs and not scalar_diffs,
    }


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    t_all = time.time()

    # 시험 실행 — 앞의 N계정만 돌리고 별도 파일에 쓴다.
    # 45분짜리 본 계산에 들어가기 전에 파이프라인 전체(복원 → 파싱 → 정합
    # 관문 → 저장)가 끝까지 도는지 20계정으로 먼저 확인하기 위한 것이다.
    pilot = 0
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        pilot = int(sys.argv[1])
    out_json = OUT_JSON if not pilot else OUT_JSON.replace(".json", "_시험.json")
    prog_json = (PROGRESS_JSON if not pilot
                 else PROGRESS_JSON.replace(".json", "_시험.json"))

    print("=" * 74)
    print("04-1 확장 재파싱 — 서브레딧·표면형·문장 통계 (라벨을 읽지 않는다)")
    print("=" * 74)
    if pilot:
        print(f"※ 시험 실행 — 앞의 {pilot}계정만 돌립니다. 산출물은 별도 파일입니다.")
        print(f"  {os.path.basename(out_json)}")
    else:
        print("보관된 13-19 사전선언의 13항(현 04-1)의 방법을 그대로 구현한다. 04를 읽지도 고치지도 않고")
        print("원본에서 다시 시작하되, 끝에서 04와 숫자가 같은지 검사한다.")

    if os.path.exists(out_json) and not pilot:
        prev = json.load(open(out_json, encoding="utf-8"))
        print("\n최종 산출물이 이미 있습니다. 아무것도 하지 않고 끝냅니다.")
        print(f"  파일   {out_json}")
        print(f"  실행일 {prev.get('설정', {}).get('실행일', '?')}")
        print("  다시 돌리려면 이 파일을 다른 이름으로 옮기거나 지운 뒤 실행하십시오.")
        return

    # ── [1/8] 입력 ──────────────────────────────────────────────
    print("\n[1/8] 입력 적재 — 라벨은 열지 않는다")
    accounts = load_accounts()
    print(f"      01 적격 계정 {len(accounts):,}개 · "
          f"문서 {sum(len(v) for v in accounts.values()):,}건")
    print("      01 파일에서 꺼낸 것은 '계정' 키 하나뿐이다. '라벨'이 든 나머지는")
    print("      그 자리에서 버렸다(del). 04가 했던 것과 같다 — 서브레딧을 붙이고")
    print("      표면형을 세는 판단에 봇/사람이 한 번도 개입하지 않았다는 사실이,")
    print("      09-3·02-1·08과 옛 17~19(보관)가 이 값으로 비교를 할 수 있는 근거다. 라벨은 뒤 단계(09-3·02-1·08)에서 연다.")

    inherit, rates_date = load_inherited_hash()
    fw_hash_05 = inherit.get("기능어_해시")
    print(f"\n      해시 사슬 승계 — 05 JSON(실행일 {rates_date})의 기능어 해시")
    print(f"        {fw_hash_05}  ({inherit.get('기능어_개수')}종)")
    if fw_hash_05 != EXPECTED_FW_HASH:
        print(f"      ■ 중단 — 사전선언이 적어 둔 해시({EXPECTED_FW_HASH})와 다릅니다.")
        print("        02가 다시 돌아 목록이 바뀐 것으로 보입니다. 같은 잣대가")
        print("        아니면 04·05·06과 04-1의 숫자를 한 표에 놓을 수 없습니다.")
        return
    print("      사전선언의 값과 같다. 02→04→05→04-1로 사슬이 이어졌다.")

    # ── [2/8] 06 함수 승계 ──────────────────────────────────────
    print("\n[2/8] 06 통계 함수 승계 확인 (ast로 원본과 사본을 다시 떠서 대조)")
    ok_copy, h_src, h_copy = verify_copied_functions()
    print(f"      06에서 복사한 함수: {', '.join(COPIED_NAMES)}")
    print(f"      06 원본 해시 {h_src}   이 파일 사본 해시 {h_copy}")
    print(f"      선언된 해시 {COPIED_HASH}   {'일치' if ok_copy else '불일치'}")
    if not ok_copy:
        print("      ■ 중단 — 06의 통계 함수와 이 파일의 사본이 다릅니다.")
        print("        04-1·09-3·02-1·08과 옛 17~19(보관)가 06과 같은 자로 잰다는 전제가 깨집니다.")
        return
    print("      손으로 옮겨 적지 않았다는 것이 매 실행 확인된다. 06의 U·δ·BH가")
    print("      단계마다 조금씩 달라지는 일 — 같은 자로 잰다는 주장을 무너뜨리는")
    print("      가장 흔한 경로 — 을 코드로 막아 둔 것이다.")

    # ── [3/8] 02 변형 목록 ──────────────────────────────────────
    print("\n[3/8] 02 변형 목록 아홉 벌과 합집합 (02-1이 쓸 재료)")
    m02 = load_module(FUNCLIST_PY, "m02_funclist")
    print(f"      02의 read_conllu()와 CLOSED_CLASS를 그대로 부른다.")
    print(f"      UD 캐시 {UD_CACHE}")
    variants, ud_tokens, ud_types = build_variant_lists(m02)
    print(f"      UD English-EWT 토큰 {ud_tokens:,}개 · 단어형 {ud_types:,}종")

    base_key = f"f{BASELINE_FREQ}_r{BASELINE_RATIO:.2f}"
    base_list = variants[base_key]
    base_hash = list_hash(base_list)
    print(f"\n      기준선 {base_key} → {len(base_list)}종 · 해시 {base_hash}")
    if base_hash != EXPECTED_FW_HASH:
        print(f"      ■ 중단 — 기준선(5/0.50)이 04·05의 172종과 다릅니다.")
        print(f"        기대 {EXPECTED_FW_HASH} · 실제 {base_hash}")
        print("        02의 절차를 그대로 썼는데 다른 목록이 나왔다면, UD 캐시가")
        print("        바뀌었거나 정규화가 어긋난 것입니다. 원인을 잡기 전에는")
        print("        나머지 여덟 벌도 믿을 수 없습니다.")
        return
    print("      02가 만든 172종과 글자까지 같다. 아홉 벌 중 하나가 기준선이므로,")
    print("      이 대조가 통과하면 나머지 여덟 벌도 같은 절차로 나온 것이다.")

    base_set = set(base_list)
    union = sorted(set().union(*[set(v) for v in variants.values()]))
    union_set = set(union)
    union_hash = list_hash(union)

    print("\n      목록      크기   172와 겹침   해시")
    for key in sorted(variants, key=lambda k: (int(k.split("_")[0][1:]), k)):
        v = variants[key]
        mark = "  ← 기준선" if key == base_key else ""
        print(f"      {key:<10}{len(v):>4}   {len(set(v) & base_set):>8}   "
              f"{list_hash(v)}{mark}")
    print(f"      합집합 U  {len(union):>4}   {len(union_set & base_set):>8}   "
          f"{union_hash}")
    print("\n      아홉 벌을 따로 세면 파싱을 아홉 번 해야 한다. 합집합을 한 번")
    print("      세어 두면 02-1이 목록별로 골라 쓸 수 있다. U에 없는 표면형은")
    print("      세지 않는다 — 전체 어휘를 담으면 파일만 커지고 쓸 일이 없다.")

    # ── [4/8] 서브레딧 복원 ─────────────────────────────────────
    print("\n[4/8] 서브레딧 복원 — 원본을 01과 같은 순서로 다시 처리한다")
    m01 = load_module(CENSOR_PY, "m01_censor")
    print(f"      01의 clean_doc()·MAX_DOCS를 그대로 빌려 쓴다 "
          f"(MIN_CHARS={m01.MIN_CHARS} · MAX_DOCS={m01.MAX_DOCS})")
    print(f"      원본 적재 중... {os.path.basename(RAW_JSON)}")
    t0 = time.time()
    raw = json.load(open(RAW_JSON, encoding="utf-8"))
    print(f"      원본 계정 {len(raw):,}개 ({time.time() - t0:.1f}초)")
    print("      계정별 대조 중...")
    t0 = time.time()
    subs_by_uid, n_match, mismatches = restore_subreddits(accounts, raw, m01)
    del raw                       # 78MB — 대조가 끝났으면 들고 있을 이유가 없다
    print(f"      일치 {n_match:,}계정 · 불일치 {len(mismatches):,}계정 "
          f"({time.time() - t0:.1f}초)")
    if mismatches:
        print("      불일치 예시 (최대 3건) — 이 계정들은 서브레딧을 '미상'으로 둔다")
        for uid, why, n01, nre in mismatches[:3]:
            print(f"        {uid:<14} {why} (01 {n01}건 · 복원 {nre}건)")
        print("      문서 목록이 다르면 몇 번째 문서에 어느 서브레딧이 붙는지 알 수")
        print("      없다. 반쯤 맞은 배열을 넘기면 09-3이 politics 문서를 잘못 센다.")
    else:
        print("      전 계정에서 순서·내용이 완전히 일치했다. 01이 만든 문서 목록을")
        print("      원본에서 그대로 재현할 수 있다는 뜻이고, 따라서 i번째 문서에")
        print("      i번째 서브레딧을 붙이는 일이 안전하다.")

    sub_docs = Counter()
    for uid in accounts:
        sub_docs.update(subs_by_uid[uid])
    print(f"\n      복원된 서브레딧 {len(sub_docs)}종 (문서 수 기준)")
    for s, n in sub_docs.most_common():
        print(f"        {s:<20}{n:>8,}   {n / sum(sub_docs.values()):>6.1%}")

    # ── [5/8] 파이프라인 ────────────────────────────────────────
    print("\n[5/8] 파이프라인 준비 — 04와 같은 구성이어야 한다")
    nlp = build_pipeline()
    if not hasattr(nlp, "bulk_process"):
        print("      ■ 중단 — 이 stanza 버전에는 bulk_process가 없습니다.")
        return

    # ── [6/8] 자가검증 ──────────────────────────────────────────
    print("\n[6/8] 자가검증 관문 — 넷 다 통과해야 본 계산에 들어간다")
    funcword_set = base_set
    gates = [
        ("관문 1 통계", gate_1_statistics()),
        ("관문 2 복원", gate_2_restore(m01)),
        ("관문 3 집계", gate_3_aggregate(funcword_set, union_set)),
        ("관문 4 토큰화", gate_4_tokenizer(nlp, funcword_set, union_set)),
    ]
    print()
    for name, ok in gates:
        print(f"      {name}  {'통과' if ok else '실패'}")
    if not all(ok for _, ok in gates):
        print()
        print("■ 중단 — 자가검증 실패. 본 계산을 시작하지 않습니다.")
        print("  짚어 볼 곳:")
        print("   · 관문 1이 걸렸다면 06 사본이 손상된 것이다([2/8]도 함께 볼 것)")
        print("   · 관문 2가 걸렸다면 01의 clean_doc 또는 정렬·상한 순서가 바뀌었다")
        print("   · 관문 3이 걸렸다면 aggregate의 서브레딧 배분·구두점 판정·'s 분기")
        print("   · 관문 4가 걸렸다면 stanza 버전이나 영어 모델이 04 때와 다르다")
        print("  이 상태로 45분을 돌리면 틀린 표가 조용히 나옵니다.")
        return
    print("      네 관문을 다 지났다. 앞의 둘은 검정과 복원 규칙을, 뒤의 둘은")
    print("      집계 규칙과 파서를 각각 손계산·고정 기대값과 맞춘 것이다.")

    # ── [7/8] 본 계산 ───────────────────────────────────────────
    print("\n[7/8] 확장 재파싱")
    uids_all = sorted(accounts)
    if pilot:
        uids_all = uids_all[:pilot]
    fp = {
        "기능어_해시": base_hash,
        "합집합_해시": union_hash,
        "합집합_크기": len(union),
        "계정수": len(uids_all),
        "문서수": sum(len(accounts[u]) for u in uids_all),
        "서브레딧_일치계정수": n_match,
    }

    done, prev_sec = {}, 0.0
    prog = load_progress(prog_json)
    if prog:
        if prog.get("지문") != fp:
            print("      ■ 중단 — 중간 저장 파일과 지금의 입력이 다릅니다.")
            print(f"        저장 당시: {prog.get('지문')}")
            print(f"        지금:      {fp}")
            print(f"        → {prog_json} 을(를) 지우고 처음부터 다시 실행하십시오.")
            return
        done = prog["계정"]
        prev_sec = prog.get("누적소요초", 0.0)
        print(f"      중간 저장을 찾았습니다 — 완료 {len(done):,}계정 "
              f"(그때까지 {fmt_dur(prev_sec)}). 이어서 합니다.")
    else:
        print("      중간 저장 없음. 처음부터 시작합니다.")

    todo = [u for u in uids_all if u not in done]
    todo_docs = sum(len(accounts[u]) for u in todo)
    print(f"      남은 계정 {len(todo):,}개 · 문서 {todo_docs:,}건")
    print(f"      {CHECKPOINT_EVERY}계정마다 중간 저장합니다. 창을 닫아도 됩니다.")

    t_run = time.time()
    docs_run = 0
    for i, uid in enumerate(todo, 1):
        docs = accounts[uid]
        done[uid] = measure_account(nlp, docs, subs_by_uid[uid],
                                    funcword_set, union_set)
        docs_run += len(docs)

        if i == WARMUP_ACCOUNTS and todo_docs > docs_run:
            el = time.time() - t_run
            per_doc = el / docs_run
            print()
            print(f"      ── 속도 실측 (처음 {WARMUP_ACCOUNTS}계정) ──")
            print(f"         문서 {docs_run:,}건 · {el:.1f}초 "
                  f"→ {per_doc * 1000:.0f} ms/문서")
            print(f"         남은 문서 {todo_docs - docs_run:,}건 "
                  f"→ 예상 {fmt_dur((todo_docs - docs_run) * per_doc)}")
            print()

        if i % CHECKPOINT_EVERY == 0:
            el = time.time() - t_run
            save_progress(prog_json, done, fp, prev_sec + el)
            per_doc = el / docs_run
            print(f"      {len(done):,}/{len(uids_all):,} 계정 · "
                  f"경과 {fmt_dur(el)} · 잔여 추정 "
                  f"{fmt_dur((todo_docs - docs_run) * per_doc)} · 저장 완료")

    run_sec = time.time() - t_run
    total_sec = prev_sec + run_sec
    print(f"      {len(done):,}/{len(uids_all):,} 계정 완료 · "
          f"이번 실행 {fmt_dur(run_sec)}")

    # 문장길이 목록의 길이가 문장수와 같은지 전 계정에서 다시 본다.
    # 관문 3이 가짜 자료로 본 것을 실제 자료에서도 확인하는 검산이다.
    bad_len = [u for u in done if len(done[u]["문장길이"]) != done[u]["문장수"]]
    print(f"      검산 — 문장길이 목록의 길이 = 문장수 : "
          f"{'전 계정 일치' if not bad_len else f'{len(bad_len)}계정 불일치'}")

    # ── [8/8] 정합 관문과 저장 ──────────────────────────────────
    print("\n[8/8] 정합 관문 — 04와 숫자가 같은가")
    gate = consistency_gate(done, pilot)
    print(f"      기준: {gate['기준']}")
    print("      항목                    04(기준)        04-1(이번)   판정")
    for k, ref_v, got_v, same in gate["합계표"]:
        print(f"      {k:<16}{ref_v:>14,}{got_v:>18,}   "
              f"{'일치' if same else '불일치'}")
    print(f"\n      계정별 172종 카운트 — 일치 {gate['계정일치수']:,}계정 · "
          f"불일치 {gate['계정불일치수']:,}계정")
    if gate["불일치예시"]:
        print("      첫 불일치 3건")
        for uid, why, n, sample in gate["불일치예시"]:
            print(f"        {uid:<14} {why} (다른 낱말 {n}종)")
            for w, ref_v, got_v in (sample or []):
                print(f"           {w:<10} 04 {ref_v:>6,}  →  04-1 {got_v:>6,}")
    if gate["스칼라불일치수"]:
        print(f"      계정별 문서·문장·토큰 불일치 {gate['스칼라불일치수']:,}건 (최대 10건)")
        for uid, f, ref_v, got_v in gate["스칼라불일치"]:
            print(f"        {uid:<14} {f:<16} 04 {ref_v:>8,}  →  04-1 {got_v:>8,}")

    print()
    if gate["통과"]:
        print("      ■ 정합 관문 통과 — 04-1의 확장 재료를 04와 한 표에 놓고 써도 된다.")
        print("        합계는 계정 사이 오차가 상쇄돼 우연히 맞을 수 있지만, 계정별")
        print("        172종이 전부 같으려면 파서가 04 실행 때와 똑같이 작동하는")
        print("        수밖에 없다. 이 관문이 이 단계의 성패다.")
    else:
        print("      ■ 정합 관문 실패 — 사전선언에 따라 저장은 마치되, 이후 단계는")
        print("        04-1 값이 아니라 04 값을 정본으로 삼는다. 04-1이 새로 낸 재료")
        print("        (서브레딧·표면형·문장길이·'s 분리)는 04에 없으므로 쓸 수밖에")
        print("        없지만, 04와 겹치는 필드는 04를 쓴다.")

    # ── 관찰 (보관된 13-19 사전선언의 13항(현 04-1)이 기록하라고 한 것) ───
    kinds = Counter(len(done[u]["서브레딧별"]) for u in done)
    unknown_accounts = [u for u in done if UNKNOWN_SUB in done[u]["서브레딧별"]]
    s_total = Counter()
    for u in done:
        s_total.update(done[u]["s_분리"])
    sent_all = [n for u in done for n in done[u]["문장길이"]]

    line("관찰 — 보관된 13-19 사전선언의 13항(현 04-1)이 기록하라고 한 것")
    print(f"  서브레딧 미상 계정            {len(unknown_accounts):>6,}계정")
    print("  계정당 서브레딧 종류 수 분포")
    for k in sorted(kinds):
        print(f"    {k}종  {kinds[k]:>6,}계정   {kinds[k] / len(done):>6.1%}")
    print(f"\n  's 표면형의 품사 갈래 (전 계정 합) — 옛 17 s분리(보관)가 둘로 나눈다")
    for k in ("PART", "AUX", "VERB", "기타"):
        tag = {"PART": "소유격 dog's", "AUX": "축약 it's",
               "VERB": "축약(본동사 태그)", "기타": "그 밖"}[k]
        print(f"    {k:<6}{s_total.get(k, 0):>10,}   {tag}")
    print(f"\n  문장 {len(sent_all):,}개의 구두점 제외 길이")
    if sent_all:
        q = quartiles(sent_all)
        print(f"    Q1 {q['Q1']:.1f} · 중앙 {q['중앙']:.1f} · Q3 {q['Q3']:.1f} · "
              f"평균 {statistics.fmean(sent_all):.2f}")
        print("    08이 이 목록에서 문장당 토큰수와 변동계수를 만든다.")

    # ── 저장 ────────────────────────────────────────────────────
    import stanza
    import torch

    # 변형 목록 아홉 벌을 파일에 적을 모양으로 정리한다. 02-1이 이 블록만 읽으면
    # 목록을 다시 만들지 않고도 같은 아홉 벌을 쓸 수 있다(해시로 확인 가능).
    variant_block = {}
    for key in sorted(variants, key=lambda k: (int(k.split("_")[0][1:]), k)):
        v = variants[key]
        variant_block[key] = {
            "빈도문턱": int(key.split("_")[0][1:]),
            "비율문턱": float(key.split("_r")[1]),
            "크기": len(v),
            "해시": list_hash(v),
            "기준선172와_겹침": len(set(v) & base_set),
            "기준선인가": key == base_key,
            "목록": v,
        }

    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.machine()}",
            "stanza": stanza.__version__,
            "torch": torch.__version__,
            "파이프라인": "tokenize,pos (use_gpu=False, bulk_process 계정 단위) — 04와 같다",
            "입력파일": {
                "01": os.path.basename(ACCOUNTS_JSON),
                "01_정제함수": os.path.basename(CENSOR_PY),
                "02_절차": os.path.basename(FUNCLIST_PY),
                "04_대조": os.path.basename(MEASURE_JSON),
                "05_해시": os.path.basename(RATES_JSON),
                "06_통계함수": os.path.basename(COMPARE_PY),
                "원본": "1. 원본데이터/2. BotSim Data/BotSim-24-Dataset/user_post_comment.json",
            },
            "승계해시": {
                "기능어172": base_hash,
                "05가_적어_둔_값": fw_hash_05,
                "사전선언_값": EXPECTED_FW_HASH,
                "06_통계함수": h_src,
                "복사한_함수": COPIED_NAMES,
            },
            "라벨_사용": "없음. 01의 '라벨' 키를 읽지 않았다. 라벨은 뒤 단계(09-3·02-1·08)에서 연다.",
            "시험실행": bool(pilot),
            "처리규모": {
                "계정수": len(done),
                "문서수": sum(a["문서수"] for a in done.values()),
                "문장수": sum(a["문장수"] for a in done.values()),
                "토큰수": sum(a["토큰수"] for a in done.values()),
                "토큰수_구두점제외": sum(a["토큰수_구두점제외"] for a in done.values()),
                "기능어토큰": sum(sum(a["기능어"].values()) for a in done.values()),
            },
            "서브레딧복원": {
                "일치계정수": n_match,
                "불일치계정수": len(mismatches),
                "불일치예시": [{"계정": u, "사유": w, "01문서수": a, "복원문서수": b}
                            for u, w, a, b in mismatches[:20]],
                "규칙": "01의 load_raw 순서 → clean_doc → 시각 오름차순 → "
                      f"{m01.MAX_DOCS}건 상한. 불일치 계정의 서브레딧은 '{UNKNOWN_SUB}'.",
            },
            "정합관문": {
                "기준": gate["기준"],
                "합계": {k: {"04": r, "13": g, "일치": s}
                       for k, r, g, s in gate["합계표"]},
                "합계일치": gate["합계일치"],
                "계정별172종_일치계정수": gate["계정일치수"],
                "계정별172종_불일치계정수": gate["계정불일치수"],
                "계정별스칼라_불일치건수": gate["스칼라불일치수"],
                "통과": gate["통과"],
                "불통과시_처리": "보관된 13-19 사전선언의 13항(현 04-1) — 이후 단계는 04를 정본으로 삼는다.",
            },
            "총소요초": round(total_sec, 1),
        },
        "변형목록": variant_block,
        "합집합": {
            "크기": len(union),
            "해시": union_hash,
            "설명": "아홉 변형 목록의 합집합. 계정별 표면형_합집합은 여기 든 것만 센다.",
            "목록": union,
        },
        "관찰": {
            "서브레딧별_문서수": dict(sub_docs.most_common()),
            "계정당_서브레딧종류수": {str(k): kinds[k] for k in sorted(kinds)},
            "서브레딧미상_계정수": len(unknown_accounts),
            "s_분리_합계": dict(s_total),
            "문장길이_요약": ({k: round(v, RATE_DIGITS)
                          for k, v in quartiles(sent_all).items()}
                         if sent_all else {}),
        },
        "계정": {uid: done[uid] for uid in sorted(done)},
    }
    write_json(out_json, out, indent=1)
    if os.path.exists(prog_json):
        os.remove(prog_json)
    print(f"\n      저장 완료: {out_json}")
    print(f"                 {os.path.getsize(out_json):,} bytes · "
          f"총 소요 {fmt_dur(total_sec)}")

    # ── 사전 예측 대조 ──────────────────────────────────────────
    line("사전 예측 대조 — 보관된 13-19 사전선언")
    print("  P번호        기대                                실제        판정")
    print("  (없음)       보관된 13-19 사전선언의 13항(현 04-1)은 '예측 없음 (측정 단계)'라고 적었다.")
    print("               04-1은 재료를 만드는 단계이고, 검정도 라벨도 없다.")
    print("               예측은 뒤 단계(09-3의 P14-1~4 등)에서 붙는다.")
    print()
    print("  대신 보관된 13-19 사전선언의 13항(현 04-1)이 기록하라고 지정한 두 관찰과 정합 관문:")
    print(f"    관찰 ① 서브레딧 미상 계정 수      {len(unknown_accounts):,}계정")
    print(f"    관찰 ② 계정당 서브레딧 종류 수    "
          f"{', '.join(f'{k}종 {kinds[k]:,}계정' for k in sorted(kinds))}")
    print(f"    정합 관문 (다섯 합계)             "
          f"{'일치' if gate['합계일치'] else '불일치'}")
    print(f"    정합 관문 (계정별 172종)          "
          f"{gate['계정일치수']:,}/{len(done):,}계정 일치")
    print(f"    → 04-1 종합                      "
          f"{'통과' if gate['통과'] else '실패'}")

    # ── 확인 항목 ───────────────────────────────────────────────
    line("확인 항목")
    print("  아래를 직접 보고 나서 09-3으로 넘어가십시오.")
    print("   1. 정합 관문이 계정별 172종까지 전부 일치했는가. 합계만 맞고 계정별이")
    print("      어긋났다면 파서가 04 때와 다르게 작동한 것이고, 09-3·02-1·08과 옛 17 s분리(보관)가 04와")
    print("      비교 가능하다는 전제가 깨진다. 이 경우 사전선언대로 04를 정본으로")
    print("      삼되, 04-1이 새로 낸 재료를 쓰는 단계에서는 그 사실을 함께 적어야 한다.")
    print("   2. 서브레딧 복원의 불일치 계정 수가 0인가. 0이 아니라면 그 계정들은")
    print("      09-3의 politics 표본에서 통째로 빠진다(서브레딧 미상). 빠진 계정이")
    print("      한쪽 라벨에 몰려 있으면 09-3의 표본이 기울 수 있다 — 09-3이 라벨을 연")
    print("      뒤에 확인할 일이지만, 여기서 개수를 먼저 봐 두라.")
    print("   3. 서브레딧 분포가 상식적인가. politics가 절반쯤이고 news·worldnews가")
    print("      그다음이어야 한다(BotSim이 뉴스·정치 서브레딧에서 수집된 자료다).")
    print("      철자가 다른 변종(internationalnews·InternationNews 같은)이 보이면")
    print("      09-3이 그것을 합칠지 말지를 정해야 한다 — 사전선언은 politics 하나만")
    print("      쓰라고 했으므로 판정 표본에는 영향이 없다.")
    print("   4. 's의 품사 갈래가 한쪽으로 쏠려 있지 않은가. PART와 AUX가 둘 다")
    print("      의미 있는 양이어야 옛 17 s분리(보관)가 둘을 갈라 볼 값어치가 있다. 한쪽이 거의")
    print("      0이면 06의 's(+0.799)는 사실상 다른 한쪽 하나였다는 뜻이다.")
    print("   5. 합집합 U의 크기가 172보다 조금 큰가(191 언저리). 크게 벌어지면")
    print("      빈도 3 목록이 잡음을 잔뜩 들여온 것이고, 02-1의 민감도 해석에서")
    print("      그 목록을 따로 봐야 한다.")
    print()
    print(f"  전체 소요 {fmt_dur(time.time() - t_all)}")
    print("  다음 단계: 09-3_서브레딧통제.py — 여기서 라벨을 처음 연다.")


if __name__ == "__main__":
    main()
