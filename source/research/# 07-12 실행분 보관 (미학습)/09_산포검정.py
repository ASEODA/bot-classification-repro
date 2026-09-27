#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
09_산포검정.py
────────────────────────────────────────────────────────────────────────────
목적
    06·07·08은 전부 위치(순위) 검정이었다. "봇이 더 쓰나 덜 쓰나"만 물었다.
    09는 축을 바꾼다 — "봇끼리 서로 얼마나 닮았나"를 잰다.

    이 축을 따로 재는 이유는 실측치에 있다. 총 기능어 사용률의 IQR이
    봇 0.0392 · 사람 0.0877 로 사람 쪽이 2.24배 넓다. 같은 자료에서 위치
    신호(총사용률 δ = −0.130)보다 큰 숫자다. **큰 쪽 신호가 지금까지 쓴
    방법 밖에 있다.** U 검정과 Cliff's δ는 원리적으로 이 차이를 못 본다.
    09는 그 방법 밖의 신호를 안으로 들여온다.

위치와 산포는 무엇이 다른가
    두 반의 키를 재서 평균이 똑같이 나왔다고 하자. 위치 검정은 여기서
    "차이 없음"을 내놓고 할 일을 마친다. 그런데 한 반은 전원이 172cm 언저리에
    몰려 있고 다른 반은 150부터 195까지 흩어져 있을 수 있다. 두 반은 전혀
    다른 반이다. 위치 검정은 이 차이를 **못 재는 것이 아니라 애초에 안 본다** —
    순위만 보기 때문에, 값이 가운데로 몰렸는지 양 끝으로 벌어졌는지는
    순위 어디에도 안 남는다.

        키(cm)   A반 = [171, 172, 172, 173]      중앙 172   IQR 1
                 B반 = [150, 168, 176, 195]      중앙 172   IQR 27
        A반과 B반을 U 검정에 넣으면 δ ≈ 0 이 나온다. "차이 없다"는 뜻이
        아니라 "위치 차이가 없다"는 뜻이고, 실제 차이는 전부 산포에 있다.

    봇 연구에서 이 구분이 왜 중요한가. "봇은 이 단어를 더 쓴다"는 위치
    주장이고, "봇은 서로 비슷하게 쓴다"는 산포 주장이다. 자동 생성의 흔적을
    찾는다면 뒤쪽이 더 곧바른 주장이다 — 같은 프롬프트·같은 모델에서 나온
    글은 서로 닮을 이유가 있지만, 사람은 서로 닮을 이유가 없다.

이 진단이 못 하는 것 — 한계를 먼저 적는다
    · **쌍거리에는 p값을 안 붙인다.** [4/6]이 내는 13만 쌍의 거리는 서로
      독립이 아니다. 계정 하나가 511개 쌍에 동시에 들어가므로, 그 계정이
      특이하면 511개 쌍이 한꺼번에 움직인다. 독립이 아닌 자료에 U 검정을
      걸면 표본이 13만인 것처럼 계산되어 어떤 차이든 유의해진다. 그래서
      쌍거리는 기술통계로만 보고하고, 검정은 **계정당 값 하나**로 줄인
      뒤에 건다(계정별 거리 중앙값 512 대 512).
    · **L1 거리는 눈금에 끌려다닌다.** 두 계정의 172차원 사용률 벡터가
      멀다는 것은 문체가 다르다는 뜻일 수도 있고, 그저 총사용률 자체가
      큰 계정이라 모든 성분이 함께 큰 것일 수도 있다. 총사용률 중앙값이
      봇 0.416 · 사람 0.425 로 사람 쪽이 조금 높으므로, 사람 쪽 거리가 큰
      데에는 눈금 몫이 조금 섞여 있다. 그 몫을 떼어 내지 않았다.
    · **매칭 표본은 분포의 양 끝이 깎인 표본이다.** 08의 캘리퍼 밖으로
      밀려난 계정은 '짝이 없을 만큼 길거나 짧은' 계정이라 무작위가 아니다.
      끝이 깎이면 산포는 그것만으로도 줄어든다 — 다만 양쪽 무더기가 같은
      방식으로 깎이므로 두 무더기의 비교 자체는 성립한다.
    · **주장 범위.** BotSim 봇 646계정은 하나의 프레임워크·하나의 모델
      (GPT-4o-mini)·하나의 시간창에서 나왔다. 여기서 나온 동질성은 "봇"의
      성질이 아니라 "이 배포 계열"의 성질이다. 사전선언 09-4가 이 제한을
      미리 못 박아 두었고, [6/6] 끝에서 화면에 그대로 다시 찍는다.

무엇을 따르나
    07-12_사전선언.md 의 「09 — 산포·동질성 검정」 절을 그대로 구현한다.

        방법 1  산포 비교 — 총사용률과 주요 자질에서 그룹별 IQR·MAD를 내고
                Brown-Forsythe 검정(중앙값 기준 절대편차의 U 검정으로 구현 —
                표준 라이브러리만)으로 산포 차이를 검정한다.
        방법 2  쌍거리 분포 — 08의 매칭 표본에서 172차원 사용률 벡터의
                계정쌍 L1 거리를 그룹 내로 나눠 분포 비교.
        방법 3  단어별 IQR 비 — 172종 각각에서 사람 IQR ÷ 봇 IQR.
        방법 4  주장 범위 제한 — "봇은 서로 닮았다"가 아니라 "한 배포 계열은
                서로 닮았다"로 쓴다.
        예측 5개  아래 PREDICTIONS 상수에 그대로 박아 두고 [6/6]이 자동으로
                  대조한다. 빗나가도 지우지 않고 화면과 JSON에 남긴다.

    문턱(q ≤ 0.05, |δ| ≥ 0.147)도 분모 규칙도 06·07·08과 같은 값을 쓴다.
    검정 대상은 총사용률(가족 밖 단독) + F 172종 + 형태자질 58종 + UPOS
    17종이고, 세 가족에 각각 별도로 BH를 건다. 매칭은 다시 계산하지 않고
    08이 저장한 쌍 목록을 그대로 읽는다 — 같은 시드라도 코드가 한 줄
    달라지면 다른 쌍이 나오고, 그러면 08과 09가 다른 표본을 두고 같은
    이름으로 이야기하게 된다.

실행 · 선행 조건
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 -u 09_산포검정.py
    필요 패키지 없음. 표준 라이브러리만 쓴다(03~08과 같은 무의존 원칙).
    같은 폴더에 05_사용률검수.json · 04_기능어측정.json · 06_비교결과.json ·
    07_형태자질비교.json · 08_분모통제.json · 01_적격계정.json 이 모두
    있어야 한다. 하나라도 없으면 아무것도 하지 않고 끝낸다.
    [4/6]의 쌍거리 계산이 13만 쌍 × 2무더기 × 172차원이라 계산 대목 중에서는
    가장 무겁지만 몇 초면 끝난다. 실제로 시간을 쓰는 곳은 01(23MB)을 비롯한
    입력 파일 적재다. 전체가 1분 안쪽이다.

산출
    09_산포검정.json
        설정(방법·한계·사슬 5중 확인·매칭 쌍 수·사전 예측 5개 대조) ·
        총사용률_산포(전체표본·매칭표본) · F블록_산포 · 형태자질_산포 ·
        UPOS_산포 · 쌍거리(봇·사람·계정별 요약 검정) · IQR비
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
RATES_JSON = f"{HERE}/05_사용률검수.json"        # 05 — 사용률·분모·총사용률
MEASURE_JSON = f"{HERE}/04_기능어측정.json"      # 04 — 자질·UPOS·토큰수
COMPARE_JSON = f"{HERE}/06_비교결과.json"        # 06 — F 블록 위치 기준선
FEATURE_JSON = f"{HERE}/07_형태자질비교.json"    # 07 — M 블록 위치 기준선
CONTROL_JSON = f"{HERE}/08_분모통제.json"        # 08 — 매칭 쌍 목록(재계산 금지)
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"       # 01 — "라벨" 키만 꺼낸다
OUT_JSON = f"{HERE}/09_산포검정.json"            # 산출물

GROUP1, GROUP2 = "bot", "human"
# 06·07·08과 같은 순서로 고정한다. U와 δ는 모두 '그룹1 기준'이라 이 순서가
# 뒤집히면 부호가 통째로 반대가 되고 앞 단계와의 대조가 전부 어긋난다.
# 산포 검정에서 부호의 뜻은 위치 검정과 다르므로 여기 한 번 더 적는다:
#   δ > 0  →  봇의 절대편차가 크다  =  봇이 더 흩어져 있다
#   δ < 0  →  봇의 절대편차가 작다  =  봇이 더 뭉쳐 있다

Q_ALPHA = 0.05          # BH 보정 후 유의 판정 문턱 (06·07·08과 같은 값)
DELTA_NOTABLE = 0.147   # '주목'의 효과크기 하한 (관례적 small 경계, 앞 단계와 같음)
SPARSE_FRAC = 0.10      # 출현 계정이 전체의 이 비율 미만이면 '희소' 표시

RATE_DIGITS = 6         # 비율·IQR·MAD 저장 자릿수 (04·05·07·08과 같은 눈금)
STAT_DIGITS = 4         # U·z·δ 저장 자릿수
SIG_DIGITS = 6          # p·q는 유효숫자로 자른다 — 아래 sig() 참조

DENOM_AXIS = "축내부합"              # 분모 = 그 계정의 해당 축 총 출현수
DENOM_TOKEN = "토큰수_구두점제외"     # 분모 = 그 계정의 구두점 제외 토큰수

# 앞 단계 로그에 찍힌 값. 어긋나면 알리기만 하고 계속 돈다 — 이 값으로
# 항목을 고르거나 버리지 않는다(사전선언: 사후 문턱 도입 금지).
EXPECT_WORDS = 172
EXPECT_FEATURES = 58
EXPECT_UPOS = 17
EXPECT_PAIRS = 512

TOP_SHOW = 20           # 산포 표에 몇 줄을 띄울 것인가
BALANCE_TOL = 1e-6      # 08이 저장한 분모 분포와 다시 센 값의 허용 오차

# ── 판정 규칙 상수 ──────────────────────────────────────────────
# 아래 넷은 사전선언 09의 문구에 숫자·표본이 명시되지 않아 이 스크립트를
# 쓰면서 정했다. 결과를 보기 전에 정했고 실행 후에 고치지 않는다(결정 0-1).
PRED1_SAMPLE = "매칭표본"
# 예측 1(총사용률 산포)의 판정 표본. 08의 분모 통제를 통과한 산포인지가
# 09의 핵심이므로 매칭 표본을 주 결과로 삼는다. 전체 표본 결과도 나란히
# 찍고, 두 표본의 방향이 어긋나면 그 사실을 판정문에 적는다.

PRED4_SAMPLE = "전체표본"
# 예측 4(위치 대 산포)의 판정 표본. 견주는 상대인 06의 위치 δ가 전체 표본
# (봇 646 · 사람 1,223)에서 나온 값이라, 산포 δ도 같은 표본 것을 써야
# 같은 자를 대는 것이 된다. 매칭 표본 산포 δ는 참고로 함께 찍는다.

PRED3_BASE = "전체172종"
# 예측 3(단어별 IQR 비)의 분모. 사전선언 문구가 "172종 중 과반"이므로
# 172를 분모로 둔다. 봇 IQR이 0이라 '비'가 정의되지 않는 단어도 '어느 쪽
# IQR이 큰가'는 정의되므로(나눗셈만 불성립이다) 판정에서 빠지지 않는다.
# 계산 가능한 항목만을 분모로 한 비율도 함께 찍는다.

PRED5_AXES = ("Tense", "Number", "Gender")
# 예측 5의 "07에서 큰 δ를 낸 축". 사전선언이 이름을 그대로 적어 두었다.
# 판정은 (가) 그 세 축의 07 주목 자질 전부에서 매칭 표본 δ < 0 이고
# q ≤ 0.05, (나) 형태자질 가족의 검정 가능 항목 과반에서 δ < 0 — 둘 다면
# 적중, 하나만이면 부분 적중, 둘 다 아니면 빗나감으로 한다.

# ── 자가검증 고정 예제 (1) 통계 ─────────────────────────────────
# 06·07·08의 SELF_CHECK_* 를 그대로 가져왔다. [08에서 가져옴]
# 손계산 과정은 self_check_stats()의 docstring에 있다.
#   (설명, A(=그룹1), B(=그룹2), 기대 U_A, 기대 δ, 기대 σ²)
SELF_CHECK_U = [
    ("완전 분리", [1, 2, 3], [4, 5, 6], 0.0, -1.0, 5.25),
    ("동점 포함", [1, 1, 2], [1, 2, 2], 3.0, -1.0 / 3.0, 4.05),
]
SELF_CHECK_BH_P = [0.01, 0.02, 0.03, 0.04]
SELF_CHECK_BH_Q = [0.04, 0.04, 0.04, 0.04]
SELF_CHECK_TOL = 1e-9

# ── 자가검증 고정 예제 (2) Brown-Forsythe ───────────────────────
# 09에서 새로 들어온 기계라 새로 만든 예제다. 손계산은 self_check_bf()의
# docstring에 있고, 아래 기대값은 그 손계산에서 온 상수다.
#   예제 A: 산포 0 대 산포 큼 — 위치는 같고 산포만 다른 가장 깨끗한 경우
SELF_CHECK_BF_A1 = [10, 10, 10, 10]
SELF_CHECK_BF_B1 = [7, 9, 11, 13]
SELF_CHECK_BF_EXP_U1 = 0.0
SELF_CHECK_BF_EXP_D1 = -1.0
SELF_CHECK_BF_EXP_VAR1 = 72.0 / 7.0
#   예제 B: 위치 누설 — 공통 중앙값을 쓰면 부호가 뒤집히는 경우
SELF_CHECK_BF_A2 = [0, 0, 0]
SELF_CHECK_BF_B2 = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
SELF_CHECK_BF_EXP_D2_GROUP = -1.0     # 그룹별 중앙값 — 봇이 뭉쳐 있음
SELF_CHECK_BF_EXP_D2_COMMON = 1.0     # 공통 중앙값 — 정반대로 찍힌다

# ── 사전 예측 (07-12_사전선언 「09」의 예측 다섯) ────────────────
# 이 상수가 사전등록의 실체다. 여기 적힌 것은 결과를 보기 전에 문서에
# 확정된 것이고, [6/6]이 실제 수치와 자동으로 대조한다. 빗나간 예측을
# 조용히 지우거나 문구를 고치면 사전등록이 아무 의미가 없어진다.
#
# "근거"·"판정규칙"은 화면 폭에 맞춰 미리 끊어 둔 줄의 목록이다. 자동
# 줄바꿈을 쓰지 않는 것은 08과 같은 이유다 — 한글은 터미널에서 두 칸을
# 차지해 글자 수로 자르면 폭이 맞지 않는다. JSON에는 한 줄로 이어 담는다.
PREDICTIONS = [
    {"번호": 1,
     "축": "총사용률",
     "서술": "총사용률 산포에서 사람의 산포가 유의하게 크다 (q ≤ 0.05, δ < 0)",
     "판정규칙": ["매칭 표본의 Brown-Forsythe 결과가 δ < 0 이고 q ≤ 0.05 이면 적중.",
               "총사용률은 가족 밖 단독 검정이라 보정할 형제가 없다 — m = 1 에서",
               "BH는 항등사상이므로 q = p 로 읽는다(06의 관례와 같다).",
               "전체 표본 결과도 나란히 찍고, 두 표본의 방향이 어긋나면 그",
               "사실을 판정문에 적는다."],
     "근거": ["실측 IQR이 봇 0.0392 · 사람 0.0877 로 사람 쪽이 2.24배 넓다.",
             "이 관찰이 우연이 아님을 검정으로 확인하는 것이 예측 1이다.",
             "IQR은 사분위 두 점만 보는 요약이라 그 사이가 어떻게 채워졌는지는",
             "못 본다. 절대편차 전체를 순위로 견주면 그 안쪽까지 본다."]},
    {"번호": 2,
     "축": "쌍거리",
     "서술": "그룹 내 L1 거리가 사람끼리 더 멀다. 매칭 표본에서도 유지된다",
     "판정규칙": ["계정별 거리 중앙값(512 대 512)의 U 검정에서 δ < 0 이고",
               "p ≤ 0.05 이면 적중. 13만 쌍의 거리 자체에는 검정을 걸지 않는다 —",
               "쌍이 서로 독립이 아니라 p가 무의미해지기 때문이다.",
               "쌍거리 기술통계(중앙값 비)의 방향도 함께 찍고, 두 방향이",
               "어긋나면 그 사실을 판정문에 적는다."],
     "근거": ["동질성은 '한 계정이 어떤 값을 갖나'가 아니라 '계정들이 서로",
             "얼마나 떨어져 있나'의 성질이다. 거리는 그것을 직접 잰다.",
             "IQR·MAD가 항목마다 따로 보는 것을 172차원에서 한꺼번에 본다."]},
    {"번호": 3,
     "축": "단어별 IQR 비",
     "서술": "172종 중 과반에서 사람 IQR이 크다",
     "판정규칙": ["매칭 표본에서 사람 IQR > 봇 IQR 인 단어가 172종 중 87종",
               "이상이면 적중. 봇 IQR이 0이라 '비'가 정의되지 않는 단어도",
               "'어느 쪽이 큰가'는 정의되므로 분모에서 빼지 않는다.",
               "비의 분포는 계산 가능한 항목으로만 내고 그 수를 따로 적는다."],
     "근거": ["산포 차이가 총사용률이라는 합계 하나에만 있는지, 172개 성분에",
             "고루 퍼져 있는지를 가른다. 합계에만 있다면 그것은 '길이를 맞추는",
             "습관'일 수 있지만, 성분마다 퍼져 있다면 단어 선택 자체가 서로",
             "닮았다는 뜻이다."]},
    {"번호": 4,
     "축": "위치 대 산포",
     "서술": "총사용률에서 산포 신호의 |δ|가 위치 신호(−0.130)보다 크다",
     "판정규칙": ["전체 표본의 산포 δ와 06이 같은 표본에서 낸 위치 δ를 견준다.",
               "|산포 δ| > |위치 δ| 이면 적중. 위치 δ는 06_비교결과.json 의",
               "총사용률_비교에서 읽어 온다(하드코딩하지 않는다 — 06을 다시",
               "돌리면 값이 바뀔 수 있고, 그때 이 판정도 함께 바뀌어야 한다).",
               "매칭 표본의 산포 δ는 참고로 함께 찍는다."],
     "근거": ["이것이 09의 존재 이유다. 산포 신호가 위치 신호보다 크다면",
             "06·07·08이 쓴 방법이 큰 쪽을 놓치고 있었다는 뜻이다.",
             "작다면 '큰 쪽 신호가 방법 밖에 있다'는 09의 전제가 틀린 것이므로",
             "09의 비중을 낮춘다 — 사전선언이 그렇게 적어 두었다."]},
    {"번호": 5,
     "축": "형태자질",
     "서술": "형태자질에서도 봇의 산포가 작다. 특히 Tense·Number·Gender 축에서",
     "판정규칙": ["(가) 07에서 주목이었던 Tense·Number·Gender 계열 자질 전부에서",
               "     매칭 표본 δ < 0 이고 q ≤ 0.05 이면 축 부분 적중.",
               "(나) 형태자질 가족의 검정 가능 항목 과반에서 δ < 0 이면",
               "     가족 부분 적중.",
               "둘 다면 적중, 하나만이면 부분 적중, 둘 다 아니면 빗나감."],
     "근거": ["성립하지 않으면 동질성은 어휘 층위에만 있는 현상이다.",
             "어휘 층위에만 있으면 주장이 '이 봇들은 같은 단어를 쓴다'로 좁아지고,",
             "형태 층위까지 가면 '같은 문법을 고른다'가 된다. 후자가 프롬프트·",
             "모델 공유의 흔적으로 훨씬 곧바르다."]},
]

# 사전선언 09-4가 못 박은 문장. [6/6] 끝에서 화면에 그대로 찍는다.
CLAIM_LIMIT = ('정직한 주장은 "봇은 서로 닮았다"가 아니라 '
               '"한 배포 계열은 서로 닮았다"이다.')


def line(title=""):
    """구분선 한 줄. [08에서 가져옴]"""
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다. [08에서 가져옴]

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
    p·q를 유효숫자 기준으로 자른다. [08에서 가져옴]

    소수 자릿수로 반올림하면(round(p, 6)) 3e-40 같은 값이 통째로 0이 된다.
    유효숫자로 자르면 크기를 잃지 않으면서 파일이 짧아진다.
    """
    if x is None:
        return None
    if x == 0.0:
        return 0.0
    return float(f"{x:.{digits}g}")


def rnd(x, digits):
    """None을 그대로 통과시키는 round. [08에서 가져옴] 검정 불가 칸이 None이라 필요하다."""
    return None if x is None else round(x, digits)


def quartiles(values):
    """
    중앙값과 사분위수 한 벌. [08에서 가져옴] 값이 둘 미만이면 사분위가 성립하지 않는다.

    method="inclusive"는 가진 자료가 모집단 전체일 때 쓰는 정의다(05·06·08과 같다).
    09에서는 IQR = Q3 − Q1 의 재료이기도 하다.
    """
    if len(values) < 2:
        m = values[0] if values else 0.0
        return {"Q1": m, "중앙": m, "Q3": m}
    q1, med, q3 = statistics.quantiles(sorted(values), n=4, method="inclusive")
    return {"Q1": q1, "중앙": med, "Q3": q3}


def five_number(values):
    """최소·Q1·중앙·Q3·최대 한 벌. [08에서 가져옴]"""
    if not values:
        return {"n": 0, "최소": None, "Q1": None, "중앙": None,
                "Q3": None, "최대": None}
    q = quartiles(values)
    return {"n": len(values), "최소": min(values), "Q1": q["Q1"],
            "중앙": q["중앙"], "Q3": q["Q3"], "최대": max(values)}


# ════════════════════════════════════════════════════════════════════════
# [통계] U 검정 · Cliff's δ · BH 보정
# ────────────────────────────────────────────────────────────────────────
# 아래 다섯 함수(normal_cdf · ranks_with_ties · mann_whitney · bh_qvalues ·
# direction_of)는 08_분모통제.py 에서 한 글자도 고치지 않고 가져온 것이고,
# 08은 07에서, 07은 06에서 가져왔다. 06에서 손계산 예제와 scipy 대조를
# 통과한 코드라 다시 짜면 잃을 것만 있다.
#
# 09가 이 기계를 쓰는 방식만 다르다. 06·07·08은 **값**을 순위 매겼고,
# 09는 **절대편차**를 순위 매긴다. 기계는 같고 넣는 재료가 다르다.
# 그것이 Brown-Forsythe의 전부다 — 새 분포표도, 새 근사도 필요 없다.
# ════════════════════════════════════════════════════════════════════════
def normal_cdf(x):
    """
    표준정규분포의 누적확률 Φ(x). [08에서 가져옴]

    math.erf 로 Φ(x) = ½(1 + erf(x/√2)). |x|가 8을 넘으면 배정도 실수의
    바닥에 닿아 p가 0.0으로 찍힌다 — "차이가 없을 확률이 0"이 아니라 "이
    계산으로는 더 작은 값을 구분할 수 없다"는 뜻이다.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def ranks_with_ties(values):
    """
    오름차순 순위. 같은 값끼리는 자리 번호를 나눠 갖는다. [08에서 가져옴]

    09에서 동점은 06·07·08보다 더 지배적이다. 절대편차는 원래 값보다
    동점이 많이 생긴다 — 중앙값 위아래로 같은 거리에 있는 두 값이 같은
    편차가 되기 때문이다(9와 11은 중앙값 10에서 둘 다 편차 1). 동점 보정이
    없으면 분산이 부풀려져 p가 실제보다 커진다. 그래서 이 함수가 09에서
    특히 중요하다.

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
        avg = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        if j > i:
            ties.append(j - i + 1)
        i = j + 1
    return ranks, ties


def mann_whitney(group1, group2):
    """
    Mann-Whitney U 검정(양측)과 Cliff's δ. 그룹1 기준. [08에서 가져옴]

        R1  = 그룹1이 가져간 순위의 합
        U1  = R1 − n1(n1+1)/2            (그룹1이 이긴 쌍의 수, 동점은 ½)
        δ   = 2·U1/(n1·n2) − 1           (Cliff's δ, −1 … +1)
        σ²  = (n1·n2/12)·[(N+1) − Σ(t³−t)/(N(N−1))]      (동점 보정 분산)
        z   = (U1 − n1·n2/2 − c)/σ       (c = ±0.5 연속성 보정)
        p   = 2·(1 − Φ(|z|))             (양측)

    σ² ≤ 0 이면 두 무더기의 값이 전부 같다는 뜻이라 δ = 0, z = 0, p = 1.0.
    09에서 이 경우가 실제로 나온다 — 어떤 단어를 양쪽 무더기 전원이 한 번도
    안 썼으면 값도 편차도 전부 0이다. 그때 "산포 차이 없음"은 옳은 답이다.
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
    Benjamini-Hochberg FDR 보정. [08에서 가져옴]

        p를 오름차순으로 늘어놓고,  q_(i) = min_{j ≥ i} ( p_(j) · m / j )

    09에서도 세 번 따로 불린다 — F 172종, 형태자질 58종, UPOS 17종에 각각
    걸어야 하기 때문이다. 총사용률 1건은 가족 밖 단독이라 이 함수를 거치지
    않는다(m = 1 이면 BH는 항등사상이므로 q = p 다).
    """
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    q = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        idx = order[rank - 1]
        val = pvals[idx] * m / rank
        if val < running:
            running = val
        q[idx] = min(1.0, running)
    return q


def direction_of(delta):
    """
    δ의 부호를 말로 옮긴다. [08에서 가져옴 · 09에서 문구만 산포용으로 바꿈]

    ■ 문구를 바꾼 이유 ■
    06~08에서 "봇이 높음"은 '봇이 그 단어를 더 쓴다'는 뜻이었다. 09에서
    순위를 매기는 대상은 값이 아니라 절대편차라, 같은 문구를 그대로 쓰면
    "봇이 높음"이 '봇이 더 쓴다'로 읽힌다. 실제 뜻은 '봇이 더 흩어져 있다'다.
    부호의 뜻이 다르므로 이름표도 달라야 한다. 계산은 한 글자도 안 바꿨다.
    """
    if delta > 0:
        return "봇이 더 흩어짐"
    if delta < 0:
        return "봇이 더 뭉침"
    return "차이 없음"


# ════════════════════════════════════════════════════════════════════════
# [분모 규칙] 축 판별과 비율 계산 — 08에서 통째로 가져온 블록
# ────────────────────────────────────────────────────────────────────────
# build_axis_map · axis_of · denom_kind_of · compute_ratios ·
# compute_upos_ratios · defined_values 는 08_분모통제.py 에서 한 글자도
# 고치지 않고 가져왔다(08은 07에서 가져왔다). 09가 07·08과 같은 눈금을
# 써야 "07이 위치에서 본 것과 09가 산포에서 보는 것"을 같은 자리에 놓을
# 수 있다. 분모 규칙을 손대면 그 대조가 성립하지 않는다.
# ════════════════════════════════════════════════════════════════════════
def build_axis_map(accounts):
    """
    자료 전체를 훑어 축마다 어떤 값들이 나타나는지 모은다. [08에서 가져옴]

    09도 08과 같이 **매칭 표본이 아니라 라벨이 붙은 전체 계정**을 넘긴다.
    매칭 표본에서만 축을 유도하면 어떤 축의 값이 하나로 줄어들어 분모가
    축 합계에서 토큰수로 조용히 바뀔 수 있고, 그러면 07·08과 다른 눈금으로
    잰 값을 07·08과 견주게 된다.

    반환: {축 이름: 정렬된 값 목록}
    """
    axis_values = {}
    for a in accounts.values():
        for key in a.get("자질", {}):
            axis, sep, val = key.partition("=")
            if not sep:
                axis, val = key, ""
            axis_values.setdefault(axis, set()).add(val)
    return {ax: sorted(vs) for ax, vs in axis_values.items()}


def axis_of(key):
    """자질 키에서 축 이름만 떼어 낸다. [08에서 가져옴] "="가 없으면 키 전체가 축이다."""
    return key.split("=", 1)[0]


def denom_kind_of(key, axis_map):
    """
    이 자질에 어떤 분모를 쓸지 정한다. [08에서 가져옴] 사전선언 07의 표 그대로다.

        대립값 ≥ 2  →  그 계정의 해당 축 총 출현수      (DENOM_AXIS)
        대립값 = 1  →  그 계정의 토큰수_구두점제외      (DENOM_TOKEN)
    """
    return DENOM_AXIS if len(axis_map.get(axis_of(key), [""])) >= 2 else DENOM_TOKEN


def compute_ratios(accounts, keys, axis_map):
    """
    계정마다 자질 비율을 낸다. [08에서 가져옴] 반환은 (판정용, 보조용, 출현계정수).

    없는 키는 0회다 — 결측이 아니다. 결측 판정은 오로지 분모로만 한다.
        Tense=Past 0회, Tense=Pres 12회  →  0 / 12 = 0.0    (값이 있다)
        Tense 축 자체가 0회              →  0 / 0  = 결측   (나눗셈 불성립)

    이 규율을 09에서도 그대로 지키는 것이 중요하다. 0.0을 결측으로 잘못
    처리하면 '그 자질을 아예 안 쓰는 계정'이 통째로 빠지는데, 그런 계정이
    한 무더기에 몰려 있으면 바로 그 몰림이 산포의 실체다.
    """
    kinds = {k: denom_kind_of(k, axis_map) for k in keys}
    ratios, aux, presence = {}, {}, {k: 0 for k in keys}

    for uid in sorted(accounts):
        a = accounts[uid]
        feats = a.get("자질", {})
        denom_tok = a.get("토큰수_구두점제외", 0)

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
            arow[k] = None if denom_tok == 0 else cnt / denom_tok
        ratios[uid] = row
        aux[uid] = arow
    return ratios, aux, presence


def compute_upos_ratios(accounts, keys):
    """
    품사 비율. [08에서 가져옴] 분모는 언제나 토큰수_구두점제외다(사전선언 07).

    PUNCT 줄만은 분모가 구두점을 뺀 수인데 분자는 구두점 수라 '말 토큰 대비
    구두점'이라는 다른 뜻의 값이 된다. 07·08이 그랬듯 09도 그 줄을 해석하지
    않는다.
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
    결측(None)을 뺀 값만 순서대로 늘어놓는다. [08에서 가져옴]

    결측은 그 자질의 검정에서만 빠진다. 계정이 통째로 빠지는 것이 아니라
    칸 하나가 빠지는 것이라, 같은 계정이 Tense 검정에는 들어가고 Mood
    검정에는 빠질 수 있다. 07·08과 똑같은 처리다.

    ■ 산포 검정에서 이 처리가 갖는 뜻 ■
    결측을 뺀 뒤 남은 값들로 그 무더기의 중앙값을 내고, 그 중앙값에서
    편차를 잰다. 결측 계정이 한 무더기에 몰려 있으면 그 무더기의 산포는
    '그 자질을 쓰는 계정들만의 산포'가 된다. 그래서 유효 n이 크게 줄어든
    자질은 표에서 그 점을 보고 읽어야 한다 — 유효 n을 항상 함께 싣는 이유다.
    """
    out = []
    for u in uids:
        v = ratios[u][key]
        if v is not None:
            out.append(v)
    return out


def word_vector(uids, rates, word):
    """
    한 단어에 대해, 주어진 계정들의 사용률을 순서대로 늘어놓는다. [08에서 가져옴]

    ■ 여기가 F 블록에서 가장 틀리기 쉬운 한 줄이다. ■
    05는 사용률을 '희소 저장'했다 — 한 번도 안 쓴 단어는 그 계정의 "사용률"
    사전에 아예 키가 없다. 그래서 .get(word, 0.0) 의 기본값 0.0이 반드시
    있어야 한다. 없는 키를 건너뛰면 "그 단어를 한 번도 안 쓴 계정"이 통째로
    표본에서 사라진다.

    09에서 이 0들은 산포 그 자체다. 절반 넘는 계정이 0인 단어에서 그
    무더기의 중앙값은 0이고, 편차는 곧 '0에서 얼마나 떨어졌나'가 된다.
    0을 빠뜨리면 그 단어의 산포는 '쓴 사람들끼리의 산포'로 조용히 바뀐다.
    """
    return [rates[u]["사용률"].get(word, 0.0) for u in uids]


def word_presence(uids, rates, words):
    """주어진 표본 안에서 각 단어를 한 번이라도 쓴 계정 수. [08에서 가져옴]"""
    out = {w: 0 for w in words}
    for u in uids:
        used = rates[u]["사용률"]
        for w in words:
            if used.get(w, 0.0) > 0:
                out[w] += 1
    return out


def load_labels():
    """
    01에서 "라벨" 키 하나만 꺼낸다. [08에서 가져옴]

    del data 는 이 함수의 이름표를 지우는 것이고, 붙들고 있던 라벨 사전만
    남는다. 원문("계정")·언어판정·깔때기 통계는 그 자리에서 회수된다.
    06에서 이미 라벨을 열었으니 이제 숨길 것은 없지만, 필요한 것 하나만
    들고 나오는 규율 자체는 그대로 지킨다.
    """
    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    labels = data.get("라벨") or {}
    del data
    return labels


# ════════════════════════════════════════════════════════════════════════
# [산포] Brown-Forsythe — 09가 새로 들이는 기계
# ════════════════════════════════════════════════════════════════════════
def iqr_of(values):
    """
    사분위 범위 Q3 − Q1. 값이 둘 미만이면 0.0.

    IQR을 산포의 요약으로 쓰는 이유는 05·06과 같다 — 표준편차는 꼬리 한
    계정에 통째로 끌려다니는데, 이 자료에는 총사용률이 극단인 계정이
    188개나 있다(05가 라벨 없이 기록해 둔 이상치). 사분위는 그런 계정이
    몇 개 있든 자리만 차지하고 값을 밀지 못한다.
    """
    if len(values) < 2:
        return 0.0
    q = quartiles(values)
    return q["Q3"] - q["Q1"]


def abs_deviations(values):
    """
    그 무더기의 **자기 중앙값**에서 잰 절대편차. Brown-Forsythe의 재료다.

    ■ 왜 그룹별 중앙값인가 — 09에서 가장 중요한 한 줄 ■
    두 무더기를 합친 공통 중앙값을 쓰면, 위치가 다른 무더기는 그것만으로
    편차가 커진다. 중앙값이 저쪽에 있으니 이쪽 값은 전부 멀어지는 것이다.
    그러면 표에는 '산포가 크다'로 찍히지만 실제로 잰 것은 '위치가 다르다'다.
    위치 차이가 산포 차이로 새어 들어온다.

    각 무더기에서 자기 중앙값을 빼면 두 무더기가 같은 자리로 옮겨진 뒤
    흩어짐만 남는다. 이것이 Levene 검정의 중앙값판인 Brown-Forsythe이고,
    평균 대신 중앙값을 쓰는 것은 치우친 분포와 이상치에 견디기 위해서다.
    그 절대편차를 t 검정이 아니라 순위 검정(U)에 넣는 것이 이 파이프라인의
    선택이다 — 정규성 가정을 하나 더 얹지 않으려는 것이고, 06부터 써 온
    무의존·강건 원칙과도 맞는다.

    self_check_bf()의 예제 B가 이 차이를 숫자로 보여 준다. 같은 자료에서
    그룹별 중앙값은 δ = −1.0, 공통 중앙값은 δ = +1.0 — 부호가 통째로
    뒤집힌다.

    ■ MAD와의 관계 ■
    반환된 편차들의 중앙값이 곧 그 무더기의 MAD다. 즉 Brown-Forsythe는
    "MAD를 숫자 하나로 요약해 눈으로 견주는" 대신 "편차 전체를 순위로
    견주는" 검정이다. 그래서 MAD를 따로 계산하지 않고 여기서 함께 얻는다.
    """
    med = statistics.median(values)
    return [abs(v - med) for v in values], med


def brown_forsythe(v1, v2):
    """
    두 무더기의 산포를 견준다. 그룹1(=봇) 기준.

        1. 각 무더기에서 그 무더기의 중앙값을 뺀 절대편차를 만든다.
        2. 두 절대편차 무더기를 Mann-Whitney U(양측·동점 보정·연속성 보정)로
           견주고 Cliff's δ를 낸다.
        3. δ < 0  →  봇의 절대편차가 작다  =  봇이 더 뭉쳐 있다.

    IQR·MAD·중앙값을 함께 담아 돌려준다. 검정이 "어느 쪽이 넓은가"만
    말한다면 IQR·MAD는 "얼마나 넓은가"를 말한다. 둘 다 있어야 읽힌다 —
    표본이 크면 아주 작은 산포 차이도 유의해지고, 그때 필요한 것이
    "IQR 비가 2.24배"처럼 크기를 말하는 숫자다.

    한쪽이 비면 None을 돌려준다(검정 불가).
    """
    if not v1 or not v2:
        return None
    d1, m1 = abs_deviations(v1)
    d2, m2 = abs_deviations(v2)
    res = mann_whitney(d1, d2)
    iqr1, iqr2 = iqr_of(v1), iqr_of(v2)
    return {
        "검정가능": True,
        "U": res["U"], "z": res["z"], "p": res["p"],
        "델타": res["델타"], "방향": direction_of(res["델타"]),
        "봇_중앙": m1, "사람_중앙": m2,
        "봇_IQR": iqr1, "사람_IQR": iqr2,
        # MAD = 절대편차의 중앙값. abs_deviations()의 docstring을 보라.
        "봇_MAD": statistics.median(d1), "사람_MAD": statistics.median(d2),
        # 비는 언제나 사람 ÷ 봇이다. 1보다 크면 사람이 넓다 = 봇이 뭉쳐 있다.
        # 봇 IQR이 0이면 나눗셈이 성립하지 않아 None — '무한대'가 아니라
        # '이 자료로는 비를 말할 수 없다'로 읽어야 한다. 그 수를 따로 센다.
        "IQR비": (iqr2 / iqr1) if iqr1 > 0 else None,
        "MAD비": (statistics.median(d2) / statistics.median(d1))
                if statistics.median(d1) > 0 else None,
        "봇_유효n": len(v1), "사람_유효n": len(v2),
    }


def bf_untestable(n_bot, n_hum):
    """검정 불가 칸 한 벌. compare 계열이 돌려주는 사전과 모양을 맞춘다."""
    return {"검정가능": False, "U": None, "z": None, "p": None, "q": None,
            "델타": None, "방향": "검정 불가",
            "봇_중앙": None, "사람_중앙": None,
            "봇_IQR": None, "사람_IQR": None,
            "봇_MAD": None, "사람_MAD": None,
            "IQR비": None, "MAD비": None,
            "봇_유효n": n_bot, "사람_유효n": n_hum,
            "유의": False, "주목": False}


def bf_family(keys, bot_ids, human_ids, getter, presence, sparse_cut,
              kinds=None):
    """
    한 가족을 통째로 산포 검정하고 BH를 건다. 08의 compare_family와 같은 뼈대다.

    getter(uids, key) 가 그 무더기의 값 목록을 돌려준다. F 블록은 05의
    사용률에서, M 블록은 07의 분모 규칙으로 만든 비율에서 꺼내므로 꺼내는
    방법만 바꿔 끼운다. 검정 자체는 한 가지다.

    BH 가족에서 검정 불가 항목을 빼는 이유는 08과 같다 — p가 없는 항목을
    BH에 넣을 방법이 없고(m만 부풀린다), 이것은 사후 문턱이 아니라 값이
    아예 없는 칸의 처리다.

    반환: (|δ| 내림차순 (키, 결과) 목록, 검정 가능 항목 수)
    """
    n_all = len(bot_ids) + len(human_ids)
    rows = []
    for k in keys:
        v1 = getter(bot_ids, k)
        v2 = getter(human_ids, k)
        r = bf_untestable(len(v1), len(v2)) if (not v1 or not v2) \
            else brown_forsythe(v1, v2)
        r["축"] = axis_of(k)
        r["분모종류"] = (kinds or {}).get(k, DENOM_TOKEN)
        r["결측계정수"] = n_all - len(v1) - len(v2)
        r["출현계정수"] = presence.get(k, 0)
        r["희소"] = presence.get(k, 0) < sparse_cut
        rows.append((k, r))

    testable = [(k, r) for k, r in rows if r["검정가능"]]
    qs = bh_qvalues([r["p"] for _, r in testable])
    for (k, r), q in zip(testable, qs):
        r["q"] = q
        r["유의"] = q <= Q_ALPHA
        r["주목"] = r["유의"] and abs(r["델타"]) >= DELTA_NOTABLE

    # 검정 불가는 |δ|를 −1로 쳐서 맨 뒤로 보낸다(δ의 하한이 −1이므로 겹치지 않는다).
    rows.sort(key=lambda kv: -(abs(kv[1]["델타"]) if kv[1]["검정가능"] else -1.0))
    return rows, len(testable)


def merge_samples(full_rows, matched_rows):
    """
    전체 표본 결과와 매칭 표본 결과를 항목별로 한 줄에 묶는다.

    매칭 표본이 주 결과다(사전선언 08이 세운 분모 통제를 통과한 산포인지가
    09의 핵심이다). 전체 표본은 '매칭으로 무엇이 달라졌는가'를 보이기 위해
    나란히 둔다. Δ는 매칭 − 전체이며, 부호를 살려 둬야 어느 쪽으로
    움직였는지 읽힌다.

    반환: |매칭 δ| 내림차순 (키, 묶음) 목록
    """
    full = dict(full_rows)
    out = []
    for k, m in matched_rows:
        f = full.get(k) or bf_untestable(0, 0)
        df, dm = f.get("델타"), m.get("델타")
        out.append((k, {
            "전체": f, "매칭": m,
            "변화량": None if (df is None or dm is None) else dm - df,
            "부호일치": None if (df is None or dm is None)
                     else (df < 0) == (dm < 0),
        }))
    out.sort(key=lambda kv: -(abs(kv[1]["매칭"]["델타"])
                              if kv[1]["매칭"]["검정가능"] else -1.0))
    return out


# ════════════════════════════════════════════════════════════════════════
# [쌍거리] 172차원 사용률 벡터의 그룹 내 L1 거리
# ════════════════════════════════════════════════════════════════════════
def dense_vectors(uids, rates, words):
    """
    계정마다 172차원 사용률 벡터를 만든다. 05의 희소 저장을 조밀하게 편다.

    없는 키는 0.0이다 — word_vector()와 같은 규율이고 같은 이유다. 안 쓴
    단어를 빠뜨리면 벡터의 길이가 계정마다 달라져 거리를 잴 수 없다.
    단어 순서는 sorted(희소성표)로 고정한다. 순서가 달라져도 L1 거리는
    같지만(합은 순서에 무관하다), 고정해 두면 같은 코드가 같은 순서를
    쓴다는 것이 보장되어 디버깅이 쉬워진다.
    """
    return [[rates[u]["사용률"].get(w, 0.0) for w in words] for u in uids]


def within_group_distances(vecs):
    """
    한 무더기 안의 모든 계정쌍 L1 거리. n개면 n(n−1)/2 쌍이다.

        L1(a, b) = Σ_j |a_j − b_j|          (172개 성분의 절대차 합)

    ■ 왜 L1인가 ■
    유클리드(L2)는 큰 성분 하나에 제곱으로 끌려간다. 172종 중 the·of·to
    같은 몇 단어가 사용률의 대부분을 차지하므로, L2를 쓰면 사실상 그 몇
    단어의 거리가 된다. L1은 모든 성분을 같은 무게로 더해 '두 계정의
    기능어 프로필이 전체적으로 얼마나 다른가'에 가깝다.

    ■ 반환 ■
    (모든 쌍 거리 목록, 계정별 거리 목록)
    계정별 목록은 [4/6]의 '계정당 값 하나'를 만드는 재료다. 각 계정은
    자기가 낀 n−1개 거리를 갖는다.

    ■ 속도 ■
    512계정이면 130,816쌍 × 172성분 = 약 2,250만 번의 뺄셈이다. 안쪽을
    sum(...)의 생성식으로 쓴 것은 파이썬 반복문보다 몇 배 빠르기 때문이고,
    그 이상은 표준 라이브러리만 쓴다는 원칙 안에서 할 수 있는 것이 없다.
    """
    n = len(vecs)
    dists = []
    per = [[] for _ in range(n)]
    for i in range(n - 1):
        vi = vecs[i]
        pi = per[i]
        for j in range(i + 1, n):
            d = sum(abs(a - b) for a, b in zip(vi, vecs[j]))
            dists.append(d)
            pi.append(d)
            per[j].append(d)
    return dists, per


def distance_ratio_table(bot_five, hum_five):
    """다섯 숫자 각각의 사람 ÷ 봇 비. 어느 구간에서 벌어지는지를 보인다."""
    out = {}
    for key in ("최소", "Q1", "중앙", "Q3", "최대"):
        b, h = bot_five.get(key), hum_five.get(key)
        out[key] = (h / b) if (b not in (None, 0) and h is not None) else None
    return out


# ════════════════════════════════════════════════════════════════════════
# [자가검증] 통계 기계와 Brown-Forsythe를 각각 고정 예제로 건다
# ════════════════════════════════════════════════════════════════════════
def self_check_stats():
    """
    U·δ·BH 구현을 손으로 푼 예제와 맞춘다. [08의 self_check_stats 그대로]

    06·07·08에서 이미 통과한 코드를 왜 또 거는가. 이 파일이 앞 단계를
    import 하는 것이 아니라 복사해 왔기 때문이다. 복사 과정에서 부호 하나가
    바뀌어도 코드는 멀쩡히 돌고 그럴듯한 p값이 나온다. 순위 검정은 틀려도
    조용하다.

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

    got_q = bh_qvalues(SELF_CHECK_BH_P)
    good = all(abs(g - e) <= SELF_CHECK_TOL
               for g, e in zip(got_q, SELF_CHECK_BH_Q))
    ok = ok and good
    print(f"  BH 보정  p={SELF_CHECK_BH_P}")
    print(f"    기대 q={SELF_CHECK_BH_Q}")
    print(f"    실제 q={[round(v, 4) for v in got_q]}  "
          f"{'통과' if good else '실패'}")
    return ok


def self_check_bf():
    """
    Brown-Forsythe를 손으로 푼 두 예제와 맞춘다. 09에서 새로 들어온 검사다.

    왜 따로 거는가. 산포 검정은 틀려도 조용한 종류다. 중앙값을 잘못 빼도
    편차는 나오고, 부호를 반대로 써도 δ는 −1과 +1 사이의 그럴듯한 값이
    찍힌다. "봇이 뭉쳐 있다"와 "봇이 흩어져 있다"는 정반대 결론인데
    화면에서는 부호 하나 차이다.

    ── 예제 A. 위치는 같고 산포만 다른 경우 ──────────────────
        A(그룹1) = [10, 10, 10, 10]      B(그룹2) = [7, 9, 11, 13]

        중앙값      A = 10
                    B = (11 + 9)/2 = 10          ← 위치가 정확히 같다
        절대편차    A = [0, 0, 0, 0]
                    B = [3, 1, 1, 3]

        이 절대편차를 U 검정에 넣는다. A는 전부 0이고 B는 전부 0보다 크므로
        A가 이긴 쌍이 하나도 없다.
            합친 값을 정렬하면 0,0,0,0,1,1,3,3
            0 넷이 자리 1·2·3·4를 나눠 평균 순위 2.5
            1 둘이 자리 5·6을 나눠 평균 순위 5.5
            3 둘이 자리 7·8을 나눠 평균 순위 7.5
            R_A = 4 × 2.5 = 10,  U_A = 10 − 4·5/2 = 0
            δ   = 2·0/16 − 1 = −1.0            ← 봇(A)이 완전히 뭉쳐 있음
            σ²  = 동점 묶음 t = 4, 2, 2 → Σ(t³−t) = 60 + 6 + 6 = 72
                  (16/12)·[(8+1) − 72/(8·7)] = (4/3)·(9 − 9/7)
                                             = (4/3)·(54/7) = 72/7 ≈ 10.2857

        위치가 같으므로 이 −1.0은 순수하게 산포만 잡은 값이다. 위치 검정을
        같은 자료에 걸면 δ = 0 이 나온다 — 두 방법이 서로 다른 것을 본다는
        사실이 이 한 예제에 다 들어 있다.

    ── 예제 B. 공통 중앙값을 쓰면 부호가 뒤집힌다 ────────────
        A(그룹1) = [0, 0, 0]
        B(그룹2) = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

        (가) 그룹별 중앙값 — 이 파일이 쓰는 방식
             중앙값   A = 0,  B = (14+15)/2 = 14.5
             절대편차 A = [0, 0, 0]
                      B = [4.5, 3.5, 2.5, 1.5, 0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
             A는 전부 0, B는 전부 0 초과 → U_A = 0
             δ = 2·0/(3·10) − 1 = −1.0        ← 봇(A)이 뭉쳐 있음 (사실이다)

        (나) 공통 중앙값 — 쓰면 안 되는 방식
             합친 13개를 정렬하면 0,0,0,10,11,…,19 이고 가운데(7번째)는 13.
             절대편차 A = [13, 13, 13]
                      B = [3, 2, 1, 0, 1, 2, 3, 4, 5, 6]
             A의 편차 13은 B의 최대 6보다 크다 → A가 모든 쌍을 이긴다
             U_A = 3·10 = 30,  δ = 2·30/30 − 1 = +1.0
                                              ← 봇이 흩어져 있다? 정반대다

        A는 세 값이 전부 같아 산포가 0인데도 (나)는 "가장 흩어진 무더기"로
        찍는다. A가 B에서 멀리 떨어져 있다는 사실, 즉 **위치 차이가 산포로
        새어 들어온** 것이다. 이 검사는 그 새는 구멍이 막혀 있는지를 본다.

    통과하면 True, 아니면 화면에 원인을 적고 False.
    """
    print("\n  ── (2) Brown-Forsythe — 절대편차 · 그룹별 중앙값 ──")
    ok = True

    got = brown_forsythe(SELF_CHECK_BF_A1, SELF_CHECK_BF_B1)
    print(f"  예제 A  A={SELF_CHECK_BF_A1}  B={SELF_CHECK_BF_B1}")
    print(f"          중앙값 A={got['봇_중앙']:g} · B={got['사람_중앙']:g}"
          "   (위치가 같다 — 남는 것은 산포뿐)")
    print("          절대편차 A=[0, 0, 0, 0] · B=[3, 1, 1, 3]")
    for label, actual, expect in (("U", got["U"], SELF_CHECK_BF_EXP_U1),
                                  ("δ", got["델타"], SELF_CHECK_BF_EXP_D1)):
        good = abs(actual - expect) <= SELF_CHECK_TOL
        ok = ok and good
        print(f"    {label} 기대 {expect:>8.4f} · 실제 {actual:>8.4f} "
              f"{'통과' if good else '실패'}")
    # σ²는 brown_forsythe()가 돌려주지 않으므로 편차를 직접 넣어 확인한다.
    dev_a, _ = abs_deviations(SELF_CHECK_BF_A1)
    dev_b, _ = abs_deviations(SELF_CHECK_BF_B1)
    var = mann_whitney(dev_a, dev_b)["시그마제곱"]
    good = abs(var - SELF_CHECK_BF_EXP_VAR1) <= 1e-9
    ok = ok and good
    print(f"    σ² 기대 {SELF_CHECK_BF_EXP_VAR1:>8.4f} · 실제 {var:>8.4f} "
          f"{'통과' if good else '실패'}")
    # 같은 자료에 위치 검정을 걸면 무엇이 나오는지 나란히 보인다.
    loc = mann_whitney(SELF_CHECK_BF_A1, SELF_CHECK_BF_B1)
    print(f"    (참고) 같은 자료의 위치 δ = {loc['델타']:+.4f} — 위치 검정은")
    print("           이 차이를 원리적으로 못 본다. 09가 필요한 이유다.")

    print(f"\n  예제 B  A={SELF_CHECK_BF_A2}")
    print(f"          B={SELF_CHECK_BF_B2}")
    got2 = brown_forsythe(SELF_CHECK_BF_A2, SELF_CHECK_BF_B2)
    good = abs(got2["델타"] - SELF_CHECK_BF_EXP_D2_GROUP) <= SELF_CHECK_TOL
    ok = ok and good
    print(f"    그룹별 중앙값 δ 기대 {SELF_CHECK_BF_EXP_D2_GROUP:>+7.4f} · "
          f"실제 {got2['델타']:>+7.4f} {'통과' if good else '실패'}")

    # 공통 중앙값판을 일부러 만들어 부호가 뒤집히는 것을 보인다. 이 값은
    # 본 계산에 쓰이지 않는다 — 쓰면 안 되는 방식이 무엇인지 보이려는 것이다.
    pooled_med = statistics.median(SELF_CHECK_BF_A2 + SELF_CHECK_BF_B2)
    wrong = mann_whitney([abs(v - pooled_med) for v in SELF_CHECK_BF_A2],
                         [abs(v - pooled_med) for v in SELF_CHECK_BF_B2])
    good = abs(wrong["델타"] - SELF_CHECK_BF_EXP_D2_COMMON) <= SELF_CHECK_TOL
    ok = ok and good
    print(f"    공통 중앙값 δ 기대 {SELF_CHECK_BF_EXP_D2_COMMON:>+7.4f} · "
          f"실제 {wrong['델타']:>+7.4f} {'통과' if good else '실패'}")
    print(f"      (공통 중앙값 = {pooled_med:g}. A는 세 값이 전부 같아 산포가")
    print("       0인데도 '가장 흩어진 무더기'로 찍힌다. 위치 차이가 산포로")
    print("       새어 들어온 것이고, 그래서 이 파일은 그룹별 중앙값을 쓴다.)")
    return ok


def self_check():
    """두 자가검증을 차례로 걸고, 하나라도 어긋나면 본 계산을 시작하지 않는다."""
    print("\n      자가검증 — 검정 기계와 산포 정의를 고정 예제로 건다")
    ok_stats = self_check_stats()
    ok_bf = self_check_bf()
    if ok_stats and ok_bf:
        print("\n  두 검사 모두 통과했다. 본 계산으로 들어간다.")
        return True

    print()
    print("■ 중단 — 자가검증 실패")
    print("  본 계산을 시작하지 않습니다. 이 상태로 돌리면 틀린 표가 조용히 나옵니다.")
    if not ok_stats:
        print("  통계 쪽에서 짚어 볼 곳:")
        print("   · ranks_with_ties 의 평균 순위 — 자리 번호가 1부터인가")
        print("   · U1 = R1 − n1(n1+1)/2 에서 n1이 그룹1의 크기가 맞는가")
        print("   · 분산의 동점 보정 항 Σ(t³−t)/(N(N−1)) 의 부호와 분모")
        print("   · bh_qvalues 의 누적 min 방향 — 큰 p부터 거꾸로 훑는가")
        print("   (이 넷은 06→07→08→09로 그대로 옮겨 온 코드다. 06 원본과 대조하라.)")
    if not ok_bf:
        print("  산포 쪽에서 짚어 볼 곳:")
        print("   · abs_deviations 가 **그 무더기의** 중앙값을 쓰는가 —")
        print("     합친 중앙값을 쓰면 위치 차이가 산포로 새어 들어온다")
        print("   · 편차에 절대값을 씌웠는가 (부호가 남으면 위치 검정이 된다)")
        print("   · brown_forsythe 가 그룹1에 봇을 넣고 있는가 — 순서가 바뀌면")
        print("     δ의 부호가 통째로 반대가 되고 '뭉침'과 '흩어짐'이 뒤바뀐다")
    return False


# ════════════════════════════════════════════════════════════════════════
# [1] 입력 적재 · 사슬 무결성 · 매칭 표본 복원
# ════════════════════════════════════════════════════════════════════════
def chain_fingerprints(conf04, conf05, conf06, conf07, conf08):
    """
    04의 기능어 지문을 승계하고, 05·06·07·08이 적어 둔 값과 대조한다.
    [08의 chain_fingerprints를 5중으로 넓힘 — 08은 넷을 봤고 09는 다섯을 본다]

    이 해시는 09가 쓰는 수치의 출처가 아니라 **04 실행분의 신분증**이다.
    05가 04에서 받아 적었고, 06은 05를 통해, 07은 04에서 직접, 08은 그 넷을
    대조한 결과를 자기 파일에 적어 두었다. 다섯 값이 같으면 지금 한 폴더에
    있는 파일들이 모두 같은 04에서 나왔다는 뜻이다.

    09에서 이 확인이 특히 중요한 이유가 있다. 09는 08이 저장한 **쌍 목록**을
    그대로 읽어 표본을 복원한다. 08이 옛 05로 만든 쌍이고 09가 새 05를
    읽으면, 같은 uid가 다른 분모·다른 사용률을 갖게 되어 "분모를 맞춘 표본"
    이라는 전제 자체가 거짓이 된다. 그런데 화면에는 아무 이상도 안 찍힌다.
    그래서 어긋나면 경고가 아니라 중단이다.

    저장 자리가 파일마다 다르므로 각각 다른 경로로 꺼낸다.
        05 : 설정 → 04승계 → 기능어_해시
        06 : 설정 → 05승계 → 04승계 → 기능어_해시
        07 : 설정 → 04승계 → 기능어_해시
        08 : 설정 → 사슬확인 → 기능어_해시

    반환: (기록용 사전, 모두 일치하는가)
    """
    h04 = conf04.get("기능어_해시")
    h05 = (conf05.get("04승계") or {}).get("기능어_해시")
    h06 = ((conf06.get("05승계") or {}).get("04승계") or {}).get("기능어_해시")
    h07 = (conf07.get("04승계") or {}).get("기능어_해시")
    chain08 = conf08.get("사슬확인") or {}
    h08 = chain08.get("기능어_해시")
    seen = [h04, h05, h06, h07, h08]
    agree = all(h is not None for h in seen) and len(set(seen)) == 1
    record = {
        "기능어_해시": h04,
        "기능어_개수": conf04.get("기능어_개수"),
        "04_실행일": conf04.get("실행일"),
        "05_실행일": conf05.get("실행일"),
        "06_실행일": conf06.get("실행일"),
        "07_실행일": conf07.get("실행일"),
        "08_실행일": conf08.get("실행일"),
        "05가_적어둔_해시": h05,
        "06이_적어둔_해시": h06,
        "07이_적어둔_해시": h07,
        "08이_적어둔_해시": h08,
        "08의_자체판정": chain08.get("일치"),
        "일치": agree,
    }
    return record, agree


def restore_pairs(pair_list, labels, rates, measures):
    """
    08이 저장한 쌍 목록으로 매칭 표본을 복원한다. **매칭을 다시 계산하지 않는다.**

    ■ 왜 다시 계산하지 않는가 ■
    08의 그리디 매칭은 시드로 섞은 봇의 순서에 결과가 달려 있다. 같은 시드를
    써도 후보를 훑는 순서나 동점 처리가 한 줄만 달라지면 다른 쌍이 나온다.
    그러면 08과 09가 서로 다른 512쌍을 두고 "매칭 표본"이라는 같은 이름으로
    이야기하게 되고, 그 차이는 어디에도 안 찍힌다. 08이 이미 uid를 적어
    두었으므로 읽어 쓰는 것이 옳다 — 재현이 아니라 승계다.

    ■ 무엇을 확인하나 ■
      1. 두 uid가 05와 04 양쪽에 다 있는가 (없으면 값을 꺼낼 수 없다)
      2. 앞의 uid가 라벨 bot, 뒤의 uid가 라벨 human 인가 (자리가 뒤바뀌면
         모든 δ의 부호가 반대가 된다 — 조용히 틀리는 종류다)
      3. 같은 계정이 두 번 쓰이지 않았는가 (1:1 매칭의 정의)

    반환: (봇 uid 목록, 사람 uid 목록, 문제 목록)
    """
    bots, hums, problems = [], [], []
    seen = set()
    for item in pair_list:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            problems.append(f"쌍의 꼴이 아님: {item!r}")
            continue
        b, h = item[0], item[1]
        for uid, want in ((b, GROUP1), (h, GROUP2)):
            if uid not in rates:
                problems.append(f"{uid} 가 05에 없음")
            elif uid not in measures:
                problems.append(f"{uid} 가 04에 없음")
            elif labels.get(uid) != want:
                problems.append(f"{uid} 의 라벨이 {labels.get(uid)!r} "
                                f"— {want} 자리에 있음")
            elif uid in seen:
                problems.append(f"{uid} 가 두 번 쓰임")
            else:
                seen.add(uid)
                continue
            break
        else:
            bots.append(b)
            hums.append(h)
    return bots, hums, problems


def check_balance(m_bot, m_hum, rates, stored):
    """
    복원한 표본의 분모 분포가 08이 적어 둔 것과 같은지 다시 센다.

    쌍 수만 맞춰 보고 넘어가면 '개수는 같은데 다른 계정들'인 경우를 못 잡는다.
    분모의 다섯 숫자가 08과 소수점까지 일치해야 같은 표본이다.

    반환: (다시 센 값, 08이 적어 둔 값, 일치 여부, 어긋난 칸 목록)
    """
    got = {"봇": five_number([rates[u]["분모"] for u in m_bot]),
           "사람": five_number([rates[u]["분모"] for u in m_hum])}
    want = {"봇": (stored or {}).get("봇") or {},
            "사람": (stored or {}).get("사람") or {}}
    bad = []
    for side in ("봇", "사람"):
        for key in ("n", "최소", "Q1", "중앙", "Q3", "최대"):
            a, b = got[side].get(key), want[side].get(key)
            if b is None:
                bad.append(f"{side}·{key}: 08에 값이 없음")
            elif a is None or abs(a - b) > BALANCE_TOL:
                bad.append(f"{side}·{key}: 09 {a} ≠ 08 {b}")
    return got, want, (not bad), bad


def print_denom_table(title, rows):
    """분모 분포 표. [08에서 가져옴] 매칭이 실제로 균형을 맞췄는지가 이 표에서 갈린다."""
    print(f"\n      {title}")
    print("        무더기         계정      최소       Q1      중앙"
          "       Q3      최대")
    for label, s in rows:
        if s["n"] == 0:
            print(f"        {label:<12}{0:>6,}   (비어 있음)")
            continue
        print(f"        {label:<12}{s['n']:>6,}{s['최소']:>10,.0f}"
              f"{s['Q1']:>9,.0f}{s['중앙']:>10,.0f}"
              f"{s['Q3']:>9,.0f}{s['최대']:>10,.0f}")


# ════════════════════════════════════════════════════════════════════════
# [표] 산포 결과를 화면에 띄운다
# ────────────────────────────────────────────────────────────────────────
# 한글은 터미널에서 두 칸을 차지해 f-string의 자리맞춤이 어긋난다. 그래서
# 06·07·08과 같은 방식으로 공백을 손으로 세어 맞춰 두었다. 아래 머리글과
# print_bf_rows()의 값 서식은 짝이므로 한쪽만 고치지 말 것.
# 값 한 줄이 차지하는 칸(1부터):
#   1-6 들여쓰기 · 7-21 항목 · 22-29 전체δ · 30-38 매칭δ · 39-47 Δ
#   48-57 q(매칭) · 58-65 IQR비 · 68- 판정
# (δ·Δ·≥는 폭이 모호한 글자다. CJK 설정 터미널에서는 두 칸으로 보여 머리글이
#  한 칸씩 밀릴 수 있다. 값 정렬 자체는 영향받지 않는다.)
# ════════════════════════════════════════════════════════════════════════
BF_HEAD = ("      항목" + " " * 13 + "전체δ" + " " * 4 + "매칭δ" + " " * 6
           + "Δδ" + " " * 8 + "q" + " " * 4 + "IQR비  판정")


def bf_verdict(pack):
    """한 항목의 판정 한 마디. 주목 여부와 방향, 두 표본의 부호 일치를 담는다."""
    m = pack["매칭"]
    if not m["검정가능"]:
        return "검정불가"
    tag = "주목" if m["주목"] else ("유의" if m["유의"] else "무주목")
    side = "봇뭉침" if m["델타"] < 0 else ("봇흩어짐" if m["델타"] > 0 else "동일")
    if pack["부호일치"] is False:
        return f"{tag}·{side}·부호바뀜"
    return f"{tag}·{side}"


def print_bf_rows(packs, title, limit=None):
    """산포 대조 표를 띄운다. 전체 표본과 매칭 표본을 한 줄에 놓는다."""
    shown = packs if limit is None else packs[:limit]
    if not shown:
        print("\n      띄울 줄이 없습니다.")
        return
    print(f"\n      {title}")
    print(BF_HEAD)
    for k, pack in shown:
        f, m = pack["전체"], pack["매칭"]
        if not m["검정가능"] or not f["검정가능"]:
            why = "매칭 표본에서 검정 불가" if not m["검정가능"] \
                else "전체 표본에서 검정 불가"
            print(f"      {k:<15}{'—':>8}{'—':>9}{'—':>9}{'—':>10}"
                  f"{'—':>8}  {why}")
            continue
        ratio = "     —" if m["IQR비"] is None else f"{m['IQR비']:>8.2f}"
        mark = "  희소" if m["희소"] else ""
        print(f"      {k:<15}{f['델타']:>+8.3f}{m['델타']:>+9.3f}"
              f"{pack['변화량']:>+9.3f}{m['q']:>10.4f}{ratio}  "
              f"{bf_verdict(pack)}{mark}")


def family_dispersion_summary(packs, label):
    """
    한 가족의 산포 결과를 집계해 찍는다. JSON에 그대로 담을 요약을 돌려준다.

    세는 것은 넷이다.
        검정 가능       BH 가족에 들어간 항목 수
        주목            q ≤ 0.05 이고 |δ| ≥ 0.147
        봇 뭉침 (δ<0)   방향이 예측대로인 항목 수
        부호 바뀜       전체 표본과 매칭 표본에서 δ의 부호가 다른 항목 수
                        — 분모를 맞췄더니 방향이 달라진 것이라 그 항목의
                        산포는 노출 비대칭의 산물이었을 수 있다
    """
    testable = [(k, p) for k, p in packs if p["매칭"]["검정가능"]]
    notable = [(k, p) for k, p in testable if p["매칭"]["주목"]]
    tight = [(k, p) for k, p in testable if p["매칭"]["델타"] < 0]
    tight_notable = [(k, p) for k, p in notable if p["매칭"]["델타"] < 0]
    flipped = [(k, p) for k, p in testable if p["부호일치"] is False]
    ratios = [p["매칭"]["IQR비"] for _, p in testable
              if p["매칭"]["IQR비"] is not None]

    print(f"\n      [{label}] 매칭 표본 기준 집계")
    print(f"        검정 가능                           {len(testable):>4}종")
    print(f"        주목 (q ≤ {Q_ALPHA} 이고 |δ| ≥ {DELTA_NOTABLE})     "
          f"{len(notable):>4}종")
    print(f"        봇이 더 뭉침 (δ < 0)                {len(tight):>4}종"
          f"   ← 예측 방향")
    print(f"          그중 주목                         "
          f"{len(tight_notable):>4}종")
    print(f"        전체 표본과 부호가 다름             {len(flipped):>4}종"
          + ("   ← 분모를 맞추니 방향이 바뀐 항목" if flipped else ""))
    if ratios:
        q = quartiles(ratios)
        print(f"        IQR 비(사람÷봇) 중앙 {q['중앙']:.2f}배  "
              f"(Q1 {q['Q1']:.2f} · Q3 {q['Q3']:.2f} · "
              f"계산 가능 {len(ratios)}종)")

    return {
        "검정가능": len(testable),
        "주목": len(notable),
        "봇뭉침": len(tight),
        "봇뭉침_주목": len(tight_notable),
        "부호다름": len(flipped),
        "부호다름목록": [k for k, _ in flipped],
        "주목목록": [k for k, _ in notable],
        "IQR비_계산가능": len(ratios),
        "IQR비_중앙": rnd(quartiles(ratios)["중앙"], STAT_DIGITS)
                   if ratios else None,
    }


# ════════════════════════════════════════════════════════════════════════
# [5] 항목별 IQR 비 — 산포 차이가 어디에 얼마나 퍼져 있나
# ════════════════════════════════════════════════════════════════════════
def iqr_ratio_report(packs, label, show_head=0):
    """
    한 가족의 항목별 IQR 비(사람 ÷ 봇)를 집계한다. 매칭 표본 값만 쓴다.

    ■ 봇 IQR이 0인 항목 ■
    그 단어를 절반 넘는 계정이 안 쓰면 Q1도 Q3도 0이 되어 IQR이 0이다.
    그러면 비는 나눗셈이 성립하지 않는다. '무한대'라고 적으면 안 된다 —
    무한히 큰 차이가 아니라 **이 자료로는 비를 말할 수 없다**는 뜻이다.
    그래서 비의 분포에서는 빼고 그 수를 따로 센다.

    다만 '어느 쪽 IQR이 큰가'는 봇 IQR이 0이어도 정해진다(0보다 크면 사람이
    크다). 비교는 성립하고 나눗셈만 불성립이므로, 예측 3의 판정에는 172종
    전부가 들어간다. 계산 가능한 항목만으로 낸 비율도 함께 찍어 두 숫자를
    나란히 볼 수 있게 한다.

    반환: JSON에 그대로 담을 사전
    """
    rows = [(k, p["매칭"]) for k, p in packs if p["매칭"]["검정가능"]]
    total = len(packs)
    ratios = [(k, r["IQR비"]) for k, r in rows if r["IQR비"] is not None]
    human_wide = [k for k, r in rows
                  if r["사람_IQR"] is not None and r["봇_IQR"] is not None
                  and r["사람_IQR"] > r["봇_IQR"]]
    bot_wide = [k for k, r in rows
                if r["사람_IQR"] is not None and r["봇_IQR"] is not None
                and r["봇_IQR"] > r["사람_IQR"]]
    tie = [k for k, r in rows
           if r["사람_IQR"] is not None and r["봇_IQR"] is not None
           and r["봇_IQR"] == r["사람_IQR"]]
    zero_bot = [k for k, r in rows if r["봇_IQR"] == 0]
    zero_both = [k for k, r in rows
                 if r["봇_IQR"] == 0 and r["사람_IQR"] == 0]

    print(f"\n      [{label}] 항목별 IQR 비 (사람 ÷ 봇 · 매칭 표본)")
    print(f"        대상 {total}종 중 검정 가능 {len(rows)}종")
    print(f"        비를 계산할 수 있는 항목            {len(ratios):>4}종")
    print(f"        봇 IQR = 0 이라 비가 정의 안 됨     {len(zero_bot):>4}종"
          f"   (그중 양쪽 다 0: {len(zero_both)}종)")
    print(f"        사람 IQR이 더 큼                    {len(human_wide):>4}종")
    print(f"        봇 IQR이 더 큼                      {len(bot_wide):>4}종")
    print(f"        같음                                {len(tie):>4}종")
    if ratios:
        vals = sorted(v for _, v in ratios)
        q = quartiles(vals)
        print(f"        비의 분포   최소 {min(vals):.2f} · Q1 {q['Q1']:.2f} · "
              f"중앙 {q['중앙']:.2f} · Q3 {q['Q3']:.2f} · 최대 {max(vals):.2f}")
        print("        (1보다 크면 사람이 넓다 = 봇이 뭉쳐 있다.)")
    if show_head and ratios:
        top = sorted(ratios, key=lambda kv: -kv[1])[:show_head]
        print(f"\n        비가 큰 항목 {len(top)}종 (봇이 가장 뭉친 쪽)")
        print("        항목              사람 IQR       봇 IQR      비")
        for k, v in top:
            r = dict(rows)[k]
            print(f"        {k:<16}{r['사람_IQR']:>11.6f}"
                  f"{r['봇_IQR']:>13.6f}{v:>8.2f}")

    return {
        "대상종수": total,
        "검정가능": len(rows),
        "비_계산가능": len(ratios),
        "봇IQR_0": len(zero_bot),
        "양쪽_0": len(zero_both),
        "사람이_큼": len(human_wide),
        "봇이_큼": len(bot_wide),
        "같음": len(tie),
        "사람이_큼_비율_전체기준": rnd(len(human_wide) / total, 4)
                            if total else None,
        "사람이_큼_비율_계산가능기준": rnd(
            sum(1 for _, v in ratios if v > 1.0) / len(ratios), 4)
            if ratios else None,
        "비_분포": {k: rnd(v, STAT_DIGITS) for k, v in
                 five_number([v for _, v in ratios]).items()}
                 if ratios else None,
        "항목별_비": {k: rnd(v, STAT_DIGITS) for k, v in ratios},
        "사람이_큼_목록": human_wide,
        "봇이_큼_목록": bot_wide,
    }


# ════════════════════════════════════════════════════════════════════════
# [6] 사전 예측 대조
# ════════════════════════════════════════════════════════════════════════
def print_prediction_header():
    """[6/6]의 머리말. 사전등록이 무엇을 막는지 매번 다시 적는다."""
    print("\n      사전선언 09의 예측 다섯을 실제 결과와 대조한다.")
    print("      아래 예측은 09를 돌리기 전에 문서에 확정된 것이다. 빗나간 예측도")
    print("      지우거나 고치지 않고 그대로 싣는다 — 06에서 라벨을 연 이상")
    print("      이 파이프라인에 남은 보호막은 사전등록뿐이다.")


def print_pred_meta(pred):
    """예측 하나의 서술·판정규칙·근거를 미리 끊어 둔 줄 그대로 찍는다. [08에서 가져옴]"""
    print()
    print(f"      예측 {pred['번호']}  {pred['서술']}")
    print(f"        [{pred['축']}]")
    print("        판정 규칙으로 적어 둔 것:")
    for ln in pred["판정규칙"]:
        print(f"          {ln}")
    print("        근거로 적어 둔 것:")
    for ln in pred["근거"]:
        print(f"          {ln}")


def check_pred1(total_full, total_matched):
    """
    예측 1 — 총사용률 산포에서 사람이 유의하게 넓은가.

    판정 표본은 매칭 표본이다(상수 PRED1_SAMPLE). 단독 검정이라 보정할
    형제가 없어 q = p 로 읽는다 — m = 1 에서 BH는 항등사상이다.
    """
    m, f = total_matched, total_full
    if m is None:
        return {"판정": "판정불가", "사유": "매칭 표본에서 검정 불가"}
    q = m["p"]                      # 단독 검정이므로 q = p
    hit = (m["델타"] < 0) and (q <= Q_ALPHA)
    same_side = (f is not None) and ((f["델타"] < 0) == (m["델타"] < 0))
    note = ""
    if f is not None and not same_side:
        note = ("전체 표본과 매칭 표본의 방향이 어긋난다 — "
                "판정은 매칭 표본으로 했으나 이 불일치를 함께 읽어야 한다.")
    return {
        "판정표본": PRED1_SAMPLE,
        "매칭_델타": rnd(m["델타"], STAT_DIGITS),
        "매칭_q": sig(q),
        "매칭_IQR비": rnd(m["IQR비"], STAT_DIGITS),
        "전체_델타": rnd(f["델타"], STAT_DIGITS) if f else None,
        "전체_q": sig(f["p"]) if f else None,
        "전체_IQR비": rnd(f["IQR비"], STAT_DIGITS) if f else None,
        "두표본_부호일치": same_side,
        "비고": note,
        "판정": "적중" if hit else "빗나감",
    }


def check_pred2(acct_test, bot_five, hum_five):
    """
    예측 2 — 그룹 내 거리가 사람끼리 더 먼가.

    판정은 계정별 거리 중앙값의 U 검정으로 한다(512 대 512). 13만 쌍의
    거리 자체에는 검정을 걸지 않는다 — 쌍이 서로 독립이 아니기 때문이다.
    기술통계(중앙값 비)의 방향도 함께 보고 두 방향이 어긋나면 적어 둔다.
    """
    if acct_test is None:
        return {"판정": "판정불가", "사유": "계정별 요약 검정을 만들 수 없음"}
    q = acct_test["p"]              # 단독 검정이므로 q = p
    hit = (acct_test["델타"] < 0) and (q <= Q_ALPHA)
    b_med, h_med = bot_five.get("중앙"), hum_five.get("중앙")
    desc_side = (h_med > b_med) if (b_med is not None and h_med is not None) \
        else None
    note = ""
    if desc_side is not None and desc_side != (acct_test["델타"] < 0):
        note = ("기술통계와 계정별 요약 검정의 방향이 어긋난다. "
                "판정은 검정으로 했으나 이 불일치가 먼저 설명되어야 한다.")
    return {
        "판정근거": "계정별 거리 중앙값의 U 검정 (독립성이 회복된 형태)",
        "델타": rnd(acct_test["델타"], STAT_DIGITS),
        "q": sig(q),
        "봇_거리중앙": rnd(b_med, RATE_DIGITS),
        "사람_거리중앙": rnd(h_med, RATE_DIGITS),
        "기술통계_방향_일치": None if desc_side is None
                       else desc_side == (acct_test["델타"] < 0),
        "비고": note,
        "판정": "적중" if hit else "빗나감",
    }


def check_pred3(f_iqr):
    """
    예측 3 — 172종 중 과반에서 사람 IQR이 큰가.

    분모는 172종 전체다(상수 PRED3_BASE). 봇 IQR이 0이라 비가 정의되지
    않는 단어도 '어느 쪽이 큰가'는 정해지므로 분모에서 빼지 않는다.
    """
    total = f_iqr["대상종수"]
    hit_n = f_iqr["사람이_큼"]
    need = total // 2 + 1
    return {
        "판정분모": PRED3_BASE,
        "대상종수": total,
        "사람이_큼": hit_n,
        "봇이_큼": f_iqr["봇이_큼"],
        "같음": f_iqr["같음"],
        "과반문턱": need,
        "비_계산가능": f_iqr["비_계산가능"],
        "계산가능기준_사람이큼비율": f_iqr["사람이_큼_비율_계산가능기준"],
        "판정": "적중" if hit_n >= need else "빗나감",
    }


def check_pred4(total_full, total_matched, loc):
    """
    예측 4 — 산포 신호가 위치 신호보다 큰가. **09의 존재 이유가 걸린 예측이다.**

    위치 δ는 06_비교결과.json 의 총사용률_비교에서 읽어 온다. 하드코딩하면
    06을 다시 돌려 값이 바뀌어도 이 판정은 옛 숫자를 계속 쓴다.

    판정 표본은 전체 표본이다(상수 PRED4_SAMPLE). 06의 위치 δ가 전체 표본
    (봇 646 · 사람 1,223)에서 나온 값이라 같은 표본끼리 견줘야 한다.
    매칭 표본의 산포 δ는 참고로 함께 담는다.
    """
    if total_full is None or loc is None or loc.get("델타") is None:
        return {"판정": "판정불가",
                "사유": "06의 총사용률 위치 δ 또는 전체 표본 산포 δ가 없음"}
    d_loc = abs(loc["델타"])
    d_disp = abs(total_full["델타"])
    return {
        "판정표본": PRED4_SAMPLE,
        "위치_델타": rnd(loc["델타"], STAT_DIGITS),
        "위치_출처": "06_비교결과.json → 총사용률_비교 → 델타 (읽어 옴)",
        "산포_델타_전체": rnd(total_full["델타"], STAT_DIGITS),
        "산포_델타_매칭": rnd(total_matched["델타"], STAT_DIGITS)
                     if total_matched else None,
        "절대값_위치": rnd(d_loc, STAT_DIGITS),
        "절대값_산포": rnd(d_disp, STAT_DIGITS),
        "배수": rnd(d_disp / d_loc, STAT_DIGITS) if d_loc else None,
        "판정": "적중" if d_disp > d_loc else "빗나감",
    }


def check_pred5(m_packs, base_feats, m_summary):
    """
    예측 5 — 형태자질에서도 봇의 산포가 작은가. 특히 Tense·Number·Gender에서.

    (가) 07에서 주목이었던 그 세 축의 자질 전부에서 매칭 표본 δ < 0 이고
         q ≤ 0.05 이면 축 부분 적중.
    (나) 형태자질 가족의 검정 가능 항목 과반에서 δ < 0 이면 가족 부분 적중.
    둘 다면 적중, 하나만이면 부분 적중, 둘 다 아니면 빗나감.

    ■ 축이 2값인 자질은 쌍으로 같은 값을 낸다 ■
    Tense 축의 값이 Past와 Pres 둘뿐이면 Pres 비율 = 1 − Past 비율이다.
    그러면 두 항목의 중앙값도 서로 1을 나눠 갖고, 절대편차는 **완전히
    같아진다**. 즉 Tense=Past와 Tense=Pres의 산포 δ는 같은 숫자다(위치
    δ가 부호만 반대인 것과 대조된다). (나)의 종수 세기에는 이 중복이
    들어 있으므로, 항목 수를 독립된 증거의 수로 읽으면 안 된다. 아래에서
    축 단위로도 함께 센다.
    """
    lookup = dict(m_packs)
    items = []
    for k, b in (base_feats or {}).items():
        if axis_of(k) not in PRED5_AXES or not b.get("주목"):
            continue
        pack = lookup.get(k)
        m = pack["매칭"] if pack else None
        if m is None or not m["검정가능"]:
            items.append({"자질": k, "07델타": b.get("델타"), "산포델타": None,
                          "q": None, "판정": "판정불가"})
            continue
        good = (m["델타"] < 0) and (m["q"] is not None and m["q"] <= Q_ALPHA)
        items.append({
            "자질": k,
            "07델타": b.get("델타"),
            "산포델타": rnd(m["델타"], STAT_DIGITS),
            "q": sig(m["q"]),
            "IQR비": rnd(m["IQR비"], STAT_DIGITS),
            "판정": "봇뭉침" if good else
                  ("봇흩어짐" if m["델타"] > 0 else "유의하지 않음"),
        })
    items.sort(key=lambda it: it["자질"])
    axis_hit = bool(items) and all(it["판정"] == "봇뭉침" for it in items)

    tight = m_summary["봇뭉침"]
    testable = m_summary["검정가능"]
    family_hit = testable > 0 and tight > testable / 2
    axes_seen = sorted({axis_of(it["자질"]) for it in items})

    if axis_hit and family_hit:
        overall = "적중"
    elif axis_hit or family_hit:
        overall = "부분 적중"
    else:
        overall = "빗나감"
    return {
        "축목록": list(PRED5_AXES),
        "확인한_축": axes_seen,
        "축항목": items,
        "축_부분적중": axis_hit,
        "가족_검정가능": testable,
        "가족_봇뭉침": tight,
        "가족_부분적중": family_hit,
        "비고": "축이 2값인 자질(Tense=Past와 Tense=Pres 등)은 절대편차가 "
              "완전히 같아 산포 δ가 동일하다. 가족의 종수 세기에 이 중복이 "
              "들어 있으므로 항목 수를 독립된 증거 수로 읽으면 안 된다.",
        "판정": overall,
    }


# ════════════════════════════════════════════════════════════════════════
# [저장] JSON 한 벌
# ════════════════════════════════════════════════════════════════════════
def pack_one(r):
    """검정 결과 한 칸을 JSON에 담을 꼴로 바꾼다."""
    if r is None or not r.get("검정가능"):
        return {"검정가능": False, "델타": None, "q": None, "방향": "검정 불가",
                "봇_IQR": None, "사람_IQR": None, "IQR비": None,
                "봇_유효n": r.get("봇_유효n") if r else None,
                "사람_유효n": r.get("사람_유효n") if r else None}
    return {
        "검정가능": True,
        "U": rnd(r["U"], 1), "z": rnd(r["z"], STAT_DIGITS),
        "p": sig(r["p"]), "q": sig(r.get("q")),
        "델타": rnd(r["델타"], STAT_DIGITS), "방향": r["방향"],
        "봇_중앙": rnd(r["봇_중앙"], RATE_DIGITS),
        "사람_중앙": rnd(r["사람_중앙"], RATE_DIGITS),
        "봇_IQR": rnd(r["봇_IQR"], RATE_DIGITS),
        "사람_IQR": rnd(r["사람_IQR"], RATE_DIGITS),
        "봇_MAD": rnd(r["봇_MAD"], RATE_DIGITS),
        "사람_MAD": rnd(r["사람_MAD"], RATE_DIGITS),
        "IQR비": rnd(r["IQR비"], STAT_DIGITS),
        "MAD비": rnd(r["MAD비"], STAT_DIGITS),
        "유의": bool(r.get("유의")), "주목": bool(r.get("주목")),
        "봇_유효n": r["봇_유효n"], "사람_유효n": r["사람_유효n"],
    }


def pack_family(packs, base, base_label):
    """
    한 가족의 산포 결과를 JSON에 담을 꼴로 바꾼다. |매칭 δ| 내림차순을 유지한다.

    앞 단계의 **위치** δ를 같은 줄에 실어 둔다. 09를 읽는 사람이 가장 먼저
    물을 것이 "위치에서 컸던 항목이 산포에서도 큰가"이기 때문이다. 이름표에
    단계 번호와 '위치'를 함께 박는다 — 같은 항목에 δ가 셋(위치·전체산포·
    매칭산포) 실리므로 이름이 흐릿하면 곧바로 헷갈린다.
    """
    out = {}
    for k, p in packs:
        b = (base or {}).get(k) or {}
        out[k] = {
            f"{base_label}위치델타": b.get("델타"),
            f"{base_label}위치주목": bool(b.get("주목")),
            "산포_전체표본": pack_one(p["전체"]),
            "산포_매칭표본": pack_one(p["매칭"]),
            "변화량": rnd(p["변화량"], STAT_DIGITS),
            "부호일치": p["부호일치"],
            "출현계정수": p["매칭"].get("출현계정수"),
            "희소": bool(p["매칭"].get("희소")),
            "분모종류": p["매칭"].get("분모종류"),
        }
    return out


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 74)
    print("산포·동질성 검정  (09 — 봇이 더 쓰나가 아니라 봇끼리 닮았나)")
    print("=" * 74)

    # ── [1] 입력 ────────────────────────────────────────────────
    print("\n[1/6] 입력 적재")
    need = [(RATES_JSON, "05_사용률검수.py"), (MEASURE_JSON, "04_기능어측정.py"),
            (COMPARE_JSON, "06_봇사람비교.py"), (FEATURE_JSON, "07_형태자질비교.py"),
            (CONTROL_JSON, "08_분모통제.py"), (ACCOUNTS_JSON, "01_botsim_적격검열.py")]
    missing_files = [(p, s) for p, s in need if not os.path.exists(p)]
    if missing_files:
        for p, s in missing_files:
            print(f"      {p} 이(가) 없습니다.  ({s} 를 먼저 실행하십시오)")
        print()
        print("      09는 앞 단계 산출물 위에서만 성립합니다. 특히 08이 없으면")
        print("      매칭 표본을 복원할 수 없고(다시 계산하지 않는 것이 규칙입니다),")
        print("      06이 없으면 예측 4의 위치 δ를 읽을 수 없습니다. 아무것도")
        print("      하지 않고 끝냅니다.")
        return

    d05 = json.load(open(RATES_JSON, encoding="utf-8"))
    d04 = json.load(open(MEASURE_JSON, encoding="utf-8"))
    d06 = json.load(open(COMPARE_JSON, encoding="utf-8"))
    d07 = json.load(open(FEATURE_JSON, encoding="utf-8"))
    d08 = json.load(open(CONTROL_JSON, encoding="utf-8"))

    rates = d05["계정"]
    summary05 = d05["검수요약"]
    measures = d04["계정"]
    base_words = d06["단어별"]
    base_feats = d07["형태자질"]
    base_upos = d07["UPOS"]
    loc_total = d06.get("총사용률_비교") or {}

    print(f"      05 사용률   계정 {len(rates):,}개 "
          f"(실행일 {d05['설정'].get('실행일', '?')})")
    print(f"      04 측정치   계정 {len(measures):,}개 "
          f"(실행일 {d04['설정'].get('실행일', '?')})")
    print(f"      06 기준선   단어 {len(base_words):,}종 · "
          f"총사용률 위치 δ = {loc_total.get('델타')}")
    print(f"      07 기준선   형태자질 {len(base_feats):,}종 · "
          f"UPOS {len(base_upos):,}종")
    print(f"      08 매칭     쌍 {d08['설정'].get('n_pair', '?')}개 "
          f"(실행일 {d08['설정'].get('실행일', '?')})")

    # ── 사슬 무결성 (5중) ───────────────────────────────────────
    chain, chain_ok = chain_fingerprints(d04["설정"], d05["설정"], d06["설정"],
                                         d07["설정"], d08["설정"])
    line("사슬 무결성 — 다섯 파일이 같은 04에서 나왔는가")
    print("  09는 08이 적어 둔 uid 목록으로 표본을 복원하고, 그 uid의 값을")
    print("  05에서 꺼낸다. 08이 옛 05로 만든 쌍인데 09가 새 05를 읽으면 같은")
    print("  uid가 다른 분모·다른 사용률을 갖게 되어 '분모를 맞춘 표본'이라는")
    print("  전제가 거짓이 된다. 화면에는 아무 이상도 안 찍힌다. 그래서 중단한다.")
    print()
    print(f"  04 기능어 해시            {chain['기능어_해시']}  "
          f"({chain['기능어_개수']}종)")
    print(f"  05가 적어 둔 해시         {chain['05가_적어둔_해시']}")
    print(f"  06이 적어 둔 해시         {chain['06이_적어둔_해시']}")
    print(f"  07이 적어 둔 해시         {chain['07이_적어둔_해시']}")
    print(f"  08이 적어 둔 해시         {chain['08이_적어둔_해시']}")
    if not chain_ok:
        print()
        print("■ 중단 — 사슬이 끊어졌습니다.")
        print("  다섯 파일이 같은 04 실행분에서 나오지 않았습니다.")
        print("  04부터 다시 돌려 05·06·07·08을 새로 만든 뒤 09를 실행하십시오.")
        return
    print("  다섯 값이 같다. 같은 04에서 나온 파일들이다.")

    # ── 라벨 · 전체 표본 ────────────────────────────────────────
    labels = load_labels()
    pool_bot, pool_hum, no_label, no_data = [], [], [], []
    for uid in sorted(rates):
        if uid not in measures:
            no_data.append(uid)
            continue
        lab = labels.get(uid)
        if lab == GROUP1:
            pool_bot.append(uid)
        elif lab == GROUP2:
            pool_hum.append(uid)
        else:
            no_label.append(uid)
    n_pool = len(pool_bot) + len(pool_hum)

    print(f"\n      라벨을 붙인 계정   봇 {len(pool_bot):,} · "
          f"사람 {len(pool_hum):,}  (합 {n_pool:,})  ← 전체 표본")
    if no_label:
        print(f"      ※ 라벨 없음/이상 {len(no_label):,}계정 — 어느 무더기에도")
        print("        넣을 수 없어 빠집니다(분석적 제외가 아닙니다).")
    if no_data:
        print(f"      ※ 05에는 있으나 04에 없는 계정 {len(no_data):,}개")
    if not pool_bot or not pool_hum:
        print("\n■ 중단 — 한쪽 무더기가 비어 있어 비교가 성립하지 않습니다.")
        return

    if len(base_words) != EXPECT_WORDS or len(base_feats) != EXPECT_FEATURES \
            or len(base_upos) != EXPECT_UPOS:
        print(f"\n      ※ 앞 단계 로그의 종수(단어 {EXPECT_WORDS} · "
              f"자질 {EXPECT_FEATURES} · UPOS {EXPECT_UPOS})와 다릅니다.")
        print("        계산은 계속합니다. 여기서 종수를 맞추려고 항목을 고르지는")
        print("        않습니다(사전선언: 사후 문턱 도입 금지).")

    # ── 매칭 표본 복원 ──────────────────────────────────────────
    line("매칭 표본 복원 — 08의 쌍을 읽는다. 다시 계산하지 않는다.")
    print("  08의 그리디 매칭은 시드로 섞은 순서에 결과가 달려 있어, 같은 시드를")
    print("  써도 코드가 한 줄 다르면 다른 쌍이 나온다. 그러면 08과 09가 서로")
    print("  다른 표본을 두고 '매칭 표본'이라는 같은 이름으로 이야기하게 된다.")
    print("  08이 uid를 적어 두었으므로 읽어 쓴다 — 재현이 아니라 승계다.")

    pair_list = (d08.get("매칭") or {}).get("쌍목록") or []
    m_bot, m_hum, problems = restore_pairs(pair_list, labels, rates, measures)
    n_pair = len(m_bot)
    print(f"\n      08이 적어 둔 쌍   {len(pair_list):,}개")
    print(f"      복원한 쌍         {n_pair:,}개  "
          f"(봇 {n_pair:,} + 사람 {n_pair:,} = 계정 {2 * n_pair:,}개)")
    if problems:
        print(f"\n■ 중단 — 쌍을 복원할 수 없습니다 ({len(problems)}건).")
        for msg in problems[:10]:
            print(f"        {msg}")
        if len(problems) > 10:
            print(f"        … 이 밖에 {len(problems) - 10}건")
        print("      08과 09가 같은 계정을 보고 있지 않다는 뜻입니다.")
        return
    if not m_bot:
        print("\n■ 중단 — 08의 쌍 목록이 비어 있습니다.")
        return
    if n_pair != EXPECT_PAIRS:
        print(f"      ※ 08 로그에 찍힌 쌍 수({EXPECT_PAIRS})와 다릅니다. 08이 다시")
        print("        돌았을 수 있습니다. 아래 분모 균형 확인으로 판단하십시오.")

    got_bal, want_bal, bal_ok, bal_bad = check_balance(
        m_bot, m_hum, rates, (d08["매칭"].get("분모분포") or {}).get("매칭후"))
    print_denom_table("복원한 표본의 분모(구두점 제외 토큰수) 분포",
                      [("봇 (매칭)", got_bal["봇"]), ("사람 (매칭)", got_bal["사람"])])
    ratio_after = (got_bal["봇"]["중앙"] / got_bal["사람"]["중앙"]
                   if got_bal["사람"]["중앙"] else None)
    print(f"\n      중앙값 비 (봇 ÷ 사람)   {ratio_after:.4f}배   "
          f"(08이 적어 둔 값 "
          f"{(d08['매칭'].get('분모분포') or {}).get('중앙값비_후')})")
    if not bal_ok:
        print("\n■ 중단 — 08이 적어 둔 분모 분포와 다시 센 값이 다릅니다.")
        for msg in bal_bad[:10]:
            print(f"        {msg}")
        print("      쌍의 개수가 같아도 다른 계정들이라는 뜻입니다. 08과 09가")
        print("      같은 05를 읽고 있는지부터 확인하십시오.")
        return
    print("      08이 적어 둔 다섯 숫자와 소수점까지 일치한다. 같은 표본이다.")

    # ── [2] 자가검증 ────────────────────────────────────────────
    print("\n[2/6] 자가검증")
    if not self_check():
        return

    # ── [3] Brown-Forsythe 산포 검정 ────────────────────────────
    print("\n[3/6] Brown-Forsythe 산포 검정 "
          f"(그룹1 = {GROUP1}, 그룹2 = {GROUP2})")
    print("      각 무더기에서 그 무더기의 중앙값을 뺀 절대편차를 만들고, 그")
    print("      절대편차를 두 무더기 간 U 검정에 넣는다. 공통 중앙값을 쓰지")
    print("      않는 것이 요점이다 — 공통 중앙값을 쓰면 위치 차이가 산포")
    print("      차이로 새어 들어와, 멀리 떨어져 있기만 한 무더기가 '넓다'로")
    print("      찍힌다([2/6]의 예제 B가 그 경우를 숫자로 보여 준다).")
    print("      δ < 0 이면 봇의 절대편차가 작다 = 봇이 더 뭉쳐 있다.")
    print("      전체 표본과 매칭 표본에서 각각 계산해 나란히 싣는다. 주 결과는")
    print("      매칭 표본이다 — 08의 분모 통제를 통과한 산포인지가 핵심이다.")

    # 총사용률 1건 — 가족 밖 단독 검정 (06의 관례와 같다)
    total_full = brown_forsythe(
        [rates[u]["총사용률"] for u in pool_bot],
        [rates[u]["총사용률"] for u in pool_hum])
    total_matched = brown_forsythe(
        [rates[u]["총사용률"] for u in m_bot],
        [rates[u]["총사용률"] for u in m_hum])

    # 아래 표의 공백도 손으로 센 것이다. 한글 라벨(전체·매칭·봇·사람)이
    # 터미널에서 두 칸씩 차지하므로 f-string의 자리맞춤이 안 통한다.
    # 두 값 줄이 같은 칸(22칸)에서 끝나도록 '봇'에는 세 칸, '사람'에는 한 칸을
    # 붙여 두었다. 한쪽만 고치면 표가 어긋난다.
    print("\n      ── 총 기능어 사용률 (1건 — BH 가족 밖 단독 검정) ──")
    print("        표본    무더기      IQR       MAD   IQR비(사람÷봇)")
    for label, r in (("전체", total_full), ("매칭", total_matched)):
        if r is None:
            print(f"        {label}     (검정 불가)")
            continue
        ratio = "—" if r["IQR비"] is None else f"{r['IQR비']:.2f}배"
        print(f"        {label}     봇   {r['봇_IQR']:>9.4f}"
              f"{r['봇_MAD']:>10.4f}")
        print(f"                 사람 {r['사람_IQR']:>9.4f}"
              f"{r['사람_MAD']:>10.4f}       {ratio}")
    for label, r in (("전체 표본", total_full), ("매칭 표본", total_matched)):
        if r is None:
            continue
        print(f"\n        {label}  n = 봇 {r['봇_유효n']:,} · "
              f"사람 {r['사람_유효n']:,}")
        print(f"          U = {r['U']:,.1f}   z = {r['z']:.3f}   "
              f"양측 p = {r['p']:.3g}")
        print(f"          δ = {r['델타']:+.4f}  →  {r['방향']}")
    print("\n        이 1건은 아래 세 가족의 BH에 넣지 않는다. 미리 재기로 정해 둔")
    print("        단독 비교라 '여러 번 찍어서 맞은 것'일 수 없기 때문이다.")
    print("        보정할 형제가 없으므로 q = p 로 읽는다(m = 1 에서 BH는 항등).")

    # ── F 블록 172종 (가족 1) ───────────────────────────────────
    words = sorted(summary05["희소성표"])
    presence_full = word_presence(pool_bot + pool_hum, rates, words)
    presence_match = word_presence(m_bot + m_hum, rates, words)
    cut_full = int(n_pool * SPARSE_FRAC)
    cut_match = int(2 * n_pair * SPARSE_FRAC)

    def word_getter(uids, key):
        return word_vector(uids, rates, key)

    f_full, f_m_full = bf_family(words, pool_bot, pool_hum, word_getter,
                                 presence_full, cut_full)
    f_match, f_m_match = bf_family(words, m_bot, m_hum, word_getter,
                                   presence_match, cut_match)
    f_packs = merge_samples(f_full, f_match)

    # ── 형태자질 58종 (가족 2) · UPOS 17종 (가족 3) ─────────────
    # 축 유도 범위는 08과 같이 '라벨 붙은 전체 계정'이다. 매칭 표본에서만
    # 유도하면 어떤 축의 값 종수가 줄어 분모가 조용히 바뀌고, 그러면 07·08과
    # 다른 눈금으로 잰 값을 07·08과 견주게 된다.
    pool_sub = {u: measures[u] for u in (pool_bot + pool_hum)}
    axis_map = build_axis_map(pool_sub)
    feat_keys = sorted({k for a in pool_sub.values() for k in a.get("자질", {})})
    upos_keys = sorted({k for a in pool_sub.values() for k in a.get("UPOS", {})})
    kinds = {k: denom_kind_of(k, axis_map) for k in feat_keys}

    ratios_full, _aux, feat_presence_full = compute_ratios(
        pool_sub, feat_keys, axis_map)
    upos_full, upos_presence_full = compute_upos_ratios(pool_sub, upos_keys)
    del pool_sub

    matched_sub = {u: measures[u] for u in (m_bot + m_hum)}
    ratios_match, _aux2, feat_presence_match = compute_ratios(
        matched_sub, feat_keys, axis_map)
    upos_match, upos_presence_match = compute_upos_ratios(matched_sub, upos_keys)
    del matched_sub

    def feat_getter_full(uids, key):
        return defined_values(uids, ratios_full, key)

    def feat_getter_match(uids, key):
        return defined_values(uids, ratios_match, key)

    def upos_getter_full(uids, key):
        return defined_values(uids, upos_full, key)

    def upos_getter_match(uids, key):
        return defined_values(uids, upos_match, key)

    mf_full, mf_m_full = bf_family(feat_keys, pool_bot, pool_hum,
                                   feat_getter_full, feat_presence_full,
                                   cut_full, kinds)
    mf_match, mf_m_match = bf_family(feat_keys, m_bot, m_hum,
                                     feat_getter_match, feat_presence_match,
                                     cut_match, kinds)
    m_packs = merge_samples(mf_full, mf_match)

    uu_full, uu_m_full = bf_family(upos_keys, pool_bot, pool_hum,
                                   upos_getter_full, upos_presence_full,
                                   cut_full)
    uu_match, uu_m_match = bf_family(upos_keys, m_bot, m_hum,
                                     upos_getter_match, upos_presence_match,
                                     cut_match)
    u_packs = merge_samples(uu_full, uu_match)

    n_axis = sum(1 for k in feat_keys if kinds[k] == DENOM_AXIS)
    print(f"\n      가족 1 F블록 {len(words)}종 · 가족 2 형태자질 "
          f"{len(feat_keys)}종(축 내부 분모 {n_axis}종) · "
          f"가족 3 UPOS {len(upos_keys)}종")
    print(f"      BH 가족 크기(매칭 표본)   F {f_m_match}종 · "
          f"형태자질 {mf_m_match}종 · UPOS {uu_m_match}종")
    # 두 표본의 가족 크기가 다를 수 있다. 매칭으로 계정이 줄면 어떤 항목의
    # 한쪽 무더기가 통째로 비어 검정 불가가 되기 때문이다. 크기가 다르면
    # 같은 항목의 q를 두 표본에서 견줄 때 그 사실을 알고 봐야 한다.
    print(f"      (전체 표본에서는  F {f_m_full}종 · 형태자질 {mf_m_full}종 · "
          f"UPOS {uu_m_full}종)")
    print("      세 가족에 각각 따로 보정했다. 서로 다른 m에서 나온 q이므로")
    print("      세 표의 q를 한 줄로 세워 비교하면 안 된다(07·08과 같은 규율).")
    print("      형태자질의 결측은 07·08과 같이 그 자질의 검정에서만 뺀다 —")
    print("      계정이 통째로 빠지는 것이 아니라 칸 하나가 빠진다.")

    print_bf_rows(f_packs, f"F 블록 {len(words)}종 중 |매칭 δ| 상위 "
                           f"{min(TOP_SHOW, len(f_packs))}종", TOP_SHOW)
    f_sum = family_dispersion_summary(f_packs, "F 블록")

    print_bf_rows(m_packs, f"형태자질 {len(m_packs)}종 중 |매칭 δ| 상위 "
                           f"{min(TOP_SHOW, len(m_packs))}종", TOP_SHOW)
    m_sum = family_dispersion_summary(m_packs, "형태자질")

    print_bf_rows(u_packs, f"UPOS {len(u_packs)}종 전부 (|매칭 δ| 내림차순)")
    u_sum = family_dispersion_summary(u_packs, "UPOS")
    print("\n      PUNCT 줄만은 눈금이 다르다(분모는 구두점 제외 토큰수인데")
    print("      분자는 구두점 수다). 07·08이 그랬듯 여기서도 해석하지 않는다.")
    print("\n      ※ 축이 정확히 2값인 자질은 짝끼리 산포 δ가 **같다**. Pres 비율이")
    print("        1 − Past 비율이면 중앙값에서의 거리가 완전히 같기 때문이다.")
    print("        위치 δ가 부호만 반대였던 것과 다르다. 종수를 독립된 증거의")
    print("        수로 읽지 말 것.")

    # ── [4] 그룹 내 쌍거리 분포 ─────────────────────────────────
    print("\n[4/6] 그룹 내 쌍거리 분포 (매칭 표본 · 172차원 사용률 벡터의 L1)")
    n_pairs_each = n_pair * (n_pair - 1) // 2
    print(f"      봇 {n_pair:,}계정과 사람 {n_pair:,}계정에서 각각 "
          f"{n_pair:,}×{n_pair - 1:,}/2 = {n_pairs_each:,}쌍의 거리를 잰다.")
    print("      두 무더기의 계정 수가 같으므로(08의 1:1 매칭) 쌍의 수도 같다 —")
    print("      한쪽이 크면 쌍 수가 제곱으로 늘어 분포 비교가 어긋난다.")
    print("      계산 대목 중에서는 가장 무겁지만 몇 초면 끝납니다.")

    t0 = time.time()
    bot_vecs = dense_vectors(m_bot, rates, words)
    hum_vecs = dense_vectors(m_hum, rates, words)
    bot_dists, bot_per = within_group_distances(bot_vecs)
    hum_dists, hum_per = within_group_distances(hum_vecs)
    elapsed = time.time() - t0
    del bot_vecs, hum_vecs
    print(f"      계산 완료 — {len(bot_dists):,} + {len(hum_dists):,}쌍, "
          f"{elapsed:.1f}초")

    bot_five = five_number(bot_dists)
    hum_five = five_number(hum_dists)
    dist_ratio = distance_ratio_table(bot_five, hum_five)

    # 라벨의 공백은 손으로 채운 것이다. "봇-봇"과 "사람-사람"은 글자 수가
    # 달라 f-string의 :<10 으로는 두 줄이 맞지 않는다(한글이 두 칸이라 글자
    # 수와 칸 수가 다르다). 아래 두 라벨은 각각 11칸으로 맞춰 두었다.
    print("\n      그룹 내 L1 거리 분포")
    print("        무더기         쌍수      최소       Q1      중앙"
          "       Q3      최대")
    for label, s in (("봇-봇      ", bot_five), ("사람-사람  ", hum_five)):
        print(f"        {label}{s['n']:>9,}{s['최소']:>10.4f}"
              f"{s['Q1']:>9.4f}{s['중앙']:>10.4f}"
              f"{s['Q3']:>9.4f}{s['최대']:>10.4f}")
    # 비는 자리맞춤을 포기하고 한 줄로 늘어놓는다. '배'가 붙는 칸과 안 붙는
    # 칸이 섞이면 어차피 열이 맞지 않는다.
    print("        비(사람÷봇)  "
          + " · ".join(
              f"{k} {dist_ratio[k]:.2f}배" if dist_ratio[k] is not None
              else f"{k} —" for k in ("최소", "Q1", "중앙", "Q3", "최대")))

    line("■ 여기에 p값을 붙이지 않는 이유 ■")
    print(f"  위 {n_pairs_each:,}쌍은 서로 독립이 아니다. 계정 하나가 "
          f"{n_pair - 1:,}개 쌍에 동시에")
    print(f"  들어가므로, 특이한 계정이 하나 있으면 {n_pair - 1:,}개 쌍이 "
          "한꺼번에 움직인다.")
    print(f"  이런 자료에 U 검정을 걸면 표본이 {n_pairs_each:,}인 것처럼 계산되어")
    print("  **어떤 사소한 차이든 유의해진다.** p는 작게 나오지만 그 작음은")
    print("  자료가 아니라 세는 방식이 만든 것이다.")
    print("  그래서 이 표는 기술통계로만 읽는다. 검정은 아래에서 계정당 값")
    print("  하나로 줄인 뒤에 건다 — 그러면 계정 수가 곧 표본 수가 되어")
    print(f"  독립성이 회복된다({n_pair:,} 대 {n_pair:,}).")

    bot_med = [statistics.median(v) for v in bot_per]
    hum_med = [statistics.median(v) for v in hum_per]
    del bot_per, hum_per
    acct = mann_whitney(bot_med, hum_med)
    acct["방향"] = direction_of(acct["델타"])
    acct_bot_five = five_number(bot_med)
    acct_hum_five = five_number(hum_med)

    print("\n      계정별 요약 — '같은 무더기 안 다른 계정들과의 거리 중앙값'")
    print("        무더기       계정      최소       Q1      중앙"
          "       Q3      최대")
    for label, s in (("봇        ", acct_bot_five), ("사람      ", acct_hum_five)):
        print(f"        {label}{s['n']:>7,}{s['최소']:>10.4f}"
              f"{s['Q1']:>9.4f}{s['중앙']:>10.4f}"
              f"{s['Q3']:>9.4f}{s['최대']:>10.4f}")
    print(f"\n        U = {acct['U']:,.1f}   z = {acct['z']:.3f}   "
          f"양측 p = {acct['p']:.3g}")
    print(f"        δ = {acct['델타']:+.4f}  →  {acct['방향']}")
    print("        (단독 검정이라 q = p 로 읽는다. 이 검정을 판정에 쓴다.)")
    if (acct["델타"] < 0) != (hum_five["중앙"] > bot_five["중앙"]):
        print("\n      ※ 기술통계와 계정별 요약 검정의 방향이 어긋난다. 쌍거리")
        print("        중앙값이 가리키는 쪽과 계정별 중앙값의 순위가 가리키는")
        print("        쪽이 다르다는 뜻이므로, 어느 한쪽을 고르지 말고 왜 어긋나는지")
        print("        부터 확인하라 — 한 계정이 여러 쌍에 들어가는 구조가 만든")
        print("        차이일 수 있다.")
    print("\n      ■ L1 거리의 한계 ■ 두 계정이 멀다는 것은 문체가 다르다는 뜻일")
    print("        수도 있고, 총사용률 자체가 큰 계정이라 모든 성분이 함께 큰")
    print("        것일 수도 있다. 그 몫을 떼어 내지 않았다. 총사용률 중앙값이")
    print("        두 무더기에서 얼마나 다른지를 [3/6] 표와 함께 읽어야 한다.")

    # ── [5] 항목별 IQR 비 ───────────────────────────────────────
    print("\n[5/6] 항목별 IQR 비 (사람 IQR ÷ 봇 IQR · 매칭 표본)")
    print("      [3/6]이 이미 항목마다 두 무더기의 IQR을 냈다. 여기서는 그 값을")
    print("      모아 분포로 본다 — 다시 계산하지 않는다(같은 값을 두 번 세는")
    print("      코드를 두면 언젠가 둘이 어긋난다).")
    f_iqr = iqr_ratio_report(f_packs, "F 블록 172종", show_head=10)
    m_iqr = iqr_ratio_report(m_packs, "형태자질 58종 (예측 5용)")

    # ── [6] 사전 예측 대조 ──────────────────────────────────────
    print("\n[6/6] 사전 예측 대조")
    print_prediction_header()

    r1 = check_pred1(total_full, total_matched)
    print_pred_meta(PREDICTIONS[0])
    if r1["판정"] == "판정불가":
        print(f"        → 예측 1 : 판정불가  ({r1.get('사유', '')})")
    else:
        # 전체 표본 쪽이 비는 경우는 한쪽 무더기가 통째로 없을 때뿐이고 그때는
        # 위에서 이미 중단한다. 그래도 마지막 단계에서 한 줄 때문에 긴 계산이
        # 통째로 날아가는 일은 막아 둔다.
        if r1["전체_델타"] is None:
            print("        전체 표본  검정 불가")
        else:
            print(f"        전체 표본  δ = {r1['전체_델타']:+.4f} · "
                  f"q = {r1['전체_q']:.3g} · IQR비 {r1['전체_IQR비']}배")
        print(f"        매칭 표본  δ = {r1['매칭_델타']:+.4f} · "
              f"q = {r1['매칭_q']:.3g} · IQR비 {r1['매칭_IQR비']}배"
              "   ← 판정에 쓰는 값")
        print(f"        → 예측 1 : {r1['판정']}")
        if r1["비고"]:
            print(f"          {r1['비고']}")

    r2 = check_pred2(acct, bot_five, hum_five)
    print_pred_meta(PREDICTIONS[1])
    if r2["판정"] == "판정불가":
        print(f"        → 예측 2 : 판정불가  ({r2.get('사유', '')})")
    else:
        print(f"        쌍거리 중앙값(기술통계)  봇 {r2['봇_거리중앙']} · "
              f"사람 {r2['사람_거리중앙']}")
        print(f"        계정별 요약 검정         δ = {r2['델타']:+.4f} · "
              f"q = {r2['q']:.3g}   ← 판정에 쓰는 값")
        print(f"        → 예측 2 : {r2['판정']}")
        if r2["비고"]:
            print(f"          {r2['비고']}")

    r3 = check_pred3(f_iqr)
    print_pred_meta(PREDICTIONS[2])
    print(f"        사람 IQR이 큰 단어  {r3['사람이_큼']}종 / "
          f"{r3['대상종수']}종   (과반 문턱 {r3['과반문턱']}종)")
    print(f"        봇 IQR이 큰 단어    {r3['봇이_큼']}종 · "
          f"같음 {r3['같음']}종")
    print(f"        비를 계산할 수 있었던 단어 {r3['비_계산가능']}종 — 그중 비가")
    print(f"        1을 넘는 비율 {r3['계산가능기준_사람이큼비율']}"
          "  (분모가 다르므로 위 숫자와 다르다)")
    print(f"        → 예측 3 : {r3['판정']}")

    r4 = check_pred4(total_full, total_matched, loc_total)
    print_pred_meta(PREDICTIONS[3])
    if r4["판정"] == "판정불가":
        print(f"        → 예측 4 : 판정불가  ({r4.get('사유', '')})")
    else:
        print(f"        위치 신호 (06, 전체 표본)   δ = {r4['위치_델타']:+.4f}"
              f"  →  |δ| = {r4['절대값_위치']:.4f}")
        print(f"        산포 신호 (09, 전체 표본)   δ = "
              f"{r4['산포_델타_전체']:+.4f}  →  |δ| = {r4['절대값_산포']:.4f}")
        if r4["배수"] is not None:
            print(f"        산포 ÷ 위치 = {r4['배수']:.2f}배")
        print(f"        (참고) 매칭 표본 산포 δ = {r4['산포_델타_매칭']}")
        print(f"        → 예측 4 : {r4['판정']}")
        if r4["판정"] == "빗나감":
            print("          ■ 산포 신호가 위치 신호보다 작다. '큰 쪽 신호가")
            print("            방법 밖에 있다'는 09의 전제가 틀린 것이므로,")
            print("            사전선언대로 09의 비중을 낮춘다. 결과를 본 뒤에")
            print("            비중을 정하는 것이 아니라 미리 적어 둔 약속을")
            print("            실행하는 것이다.")

    r5 = check_pred5(m_packs, base_feats, m_sum)
    print_pred_meta(PREDICTIONS[4])
    print(f"        (가) 07 주목 자질 중 {'·'.join(PRED5_AXES)} 계열 "
          f"{len(r5['축항목'])}종")
    if r5["축항목"]:
        print("        자질              07 위치δ   산포δ         q  판정")
        for it in r5["축항목"]:
            if it["산포델타"] is None:
                print(f"        {it['자질']:<16}"
                      f"{it['07델타'] if it['07델타'] is not None else '—':>10}"
                      f"{'—':>9}{'—':>10}  판정불가")
                continue
            print(f"        {it['자질']:<16}{it['07델타']:>+10.3f}"
                  f"{it['산포델타']:>+9.3f}{it['q']:>10.4f}  {it['판정']}")
    else:
        print("          해당 축에 07 주목 자질이 없다.")
    print(f"          축 부분 : {'적중' if r5['축_부분적중'] else '빗나감'}")
    print(f"        (나) 형태자질 가족 — 검정 가능 {r5['가족_검정가능']}종 중 "
          f"δ < 0 인 항목 {r5['가족_봇뭉침']}종")
    print(f"          가족 부분 : {'적중' if r5['가족_부분적중'] else '빗나감'}")
    print(f"        → 예측 5 : {r5['판정']}")
    print("          (축이 2값인 자질은 짝끼리 산포 δ가 같다. 위 종수에 그")
    print("           중복이 들어 있으므로 독립된 증거 수로 읽지 말 것.)")

    pred_results = []
    for pred, res in zip(PREDICTIONS, (r1, r2, r3, r4, r5)):
        pred_results.append({
            "번호": pred["번호"], "축": pred["축"], "서술": pred["서술"],
            "판정규칙": " ".join(pred["판정규칙"]),
            "근거": " ".join(pred["근거"]),
            "결과": res, "판정": res["판정"],
        })
    hit = sum(1 for r in pred_results if r["판정"] == "적중")
    part = sum(1 for r in pred_results if r["판정"] == "부분 적중")
    print()
    print(f"      요약 — 예측 5개 중 {hit}개 적중"
          + (f", {part}개 부분 적중" if part else "")
          + f", {len(pred_results) - hit - part}개 빗나감/판정불가")
    print("      빗나간 것을 지우지 않는다. 사전선언 09를 쓸 때 무엇을 예상했고")
    print("      자료가 무엇을 돌려주었는지가 나란히 남아야 한다.")

    # ── 주장 범위 제한 (사전선언 09-4) ──────────────────────────
    line("주장 범위 — 여기서 나온 동질성이 무엇의 성질인가")
    print("  BotSim 봇 646계정은 하나의 프레임워크·하나의 모델(GPT-4o-mini)·")
    print("  하나의 시간창에서 나왔다. 같은 프롬프트 틀에서 같은 모델이 같은")
    print("  시기에 만든 글이 서로 닮은 것은 놀랄 일이 아니다. 그것을 '봇 일반'의")
    print("  성질로 옮겨 적는 순간, 이 결과는 검증할 수 없는 주장이 된다.")
    print()
    print(f"  {CLAIM_LIMIT}")
    print()
    print("  원고에 이 문장을 그대로 쓴다. 다른 프레임워크·다른 모델·다른 시기의")
    print("  봇에서도 같은 동질성이 나오는지는 이 자료로 답할 수 없다.")

    # ── 저장 ────────────────────────────────────────────────────
    line("저장")
    # 총사용률은 가족 밖 단독 검정이라 BH를 거치지 않는다. m = 1 에서 BH는
    # 항등사상이므로 q = p 다. 저장 칸을 비워 두면 읽는 사람이 "보정을
    # 빠뜨렸나"를 매번 되묻게 되므로, 같은 값을 q 자리에 명시해 둔다.
    for r in (total_full, total_matched):
        if r is not None:
            r["q"] = r["p"]
            r["유의"] = r["p"] <= Q_ALPHA
            r["주목"] = r["유의"] and abs(r["델타"]) >= DELTA_NOTABLE

    method = (
        "Brown-Forsythe 산포 검정을 순위 검정으로 구현했다. 각 무더기에서 그 "
        "무더기의 중앙값을 뺀 절대편차를 만들고, 두 절대편차 무더기를 "
        "Mann-Whitney U(양측·동점 보정·연속성 보정)로 견주어 Cliff's δ를 "
        f"낸다(그룹1 = {GROUP1}). δ < 0 이면 봇의 절대편차가 작다 = 봇이 더 "
        "뭉쳐 있다. 공통 중앙값이 아니라 그룹별 중앙값을 쓰는 것이 요점이며, "
        "공통 중앙값을 쓰면 위치 차이가 산포 차이로 새어 들어온다. "
        f"대상은 총사용률(가족 밖 단독) + F 블록 {len(words)}종 + 형태자질 "
        f"{len(feat_keys)}종 + UPOS {len(upos_keys)}종이고, 세 가족에 각각 "
        f"별도로 BH FDR q = {Q_ALPHA}를 걸었다. 전체 표본(봇 {len(pool_bot)} · "
        f"사람 {len(pool_hum)})과 08의 매칭 표본(봇 {n_pair} · 사람 {n_pair})에서 "
        "각각 계산했으며 주 결과는 매칭 표본이다. 매칭은 다시 계산하지 않고 "
        "08_분모통제.json 의 쌍 목록을 그대로 읽어 복원했고, 복원한 표본의 "
        "분모 다섯 숫자가 08이 적어 둔 값과 일치함을 확인했다. 분모 규칙·"
        "결측 처리·희소 표시는 07·08과 같다. 쌍거리는 매칭 표본에서 172차원 "
        "사용률 벡터의 그룹 내 L1 거리이며, 기술통계로만 보고하고 검정은 "
        "계정별 거리 중앙값(512 대 512)으로 한다."
    )
    limits = (
        f"쌍거리 {n_pairs_each:,}쌍은 서로 독립이 아니다(한 계정이 "
        f"{n_pair - 1:,}개 쌍에 들어간다). "
        f"독립이 아닌 자료에 p를 붙이면 표본이 {n_pairs_each:,}인 것처럼 "
        "계산되어 어떤 차이든 "
        "유의해지므로 쌍거리에는 검정을 걸지 않았다. L1 거리는 총사용률 자체의 "
        "크기에 끌려다니며 그 몫을 떼어 내지 않았다. 매칭 표본은 캘리퍼 밖 "
        "계정이 빠진 표본이라 분포의 양 끝이 깎여 있고, 끝이 깎이면 산포는 "
        "그것만으로도 줄어든다(두 무더기가 같은 방식으로 깎이므로 비교 자체는 "
        "성립한다). 축이 2값인 형태자질은 짝끼리 산포 δ가 완전히 같으므로 "
        "종수를 독립된 증거 수로 읽으면 안 된다. 그리고 " + CLAIM_LIMIT +
        " BotSim 봇은 하나의 프레임워크·하나의 모델(GPT-4o-mini)·하나의 "
        "시간창에서 나왔다(사전선언 09-4)."
    )
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "방법": method,
            "한계": limits,
            "주장범위": CLAIM_LIMIT,
            "그룹1": GROUP1,
            "그룹2": GROUP2,
            "부호의_뜻": "δ < 0 = 봇의 절대편차가 작다 = 봇이 더 뭉쳐 있다. "
                     "06~08의 위치 δ와 뜻이 다르므로 한 표에 섞어 읽지 말 것.",
            "표본": {
                "전체표본": {"봇": len(pool_bot), "사람": len(pool_hum)},
                "매칭표본": {"쌍수": n_pair, "봇": n_pair, "사람": n_pair,
                         "출처": "08_분모통제.json 의 쌍 목록을 그대로 읽었다"
                               "(다시 계산하지 않았다)."},
                "주결과": "매칭표본",
            },
            "매칭쌍수": n_pair,
            "매칭_분모확인": {"09가_다시_센_값": got_bal,
                        "08이_적어둔_값": want_bal,
                        "일치": bal_ok},
            "BH가족": {"F블록": f_m_match, "형태자질": mf_m_match,
                     "UPOS": uu_m_match,
                     "비고": "매칭 표본 기준 검정 가능 항목 수. 세 가족에 각각 "
                            "별도로 보정했다. 총사용률 1건은 가족 밖 단독이라 "
                            "q = p 다(m = 1 에서 BH는 항등)."},
            "희소기준": f"매칭 표본 {2 * n_pair:,}계정의 {SPARSE_FRAC:.0%}인 "
                     f"{cut_match:,}계정 미만. 표시만 하고 제외하지 않는다.",
            "판정규칙_상수": {
                "주목문턱": DELTA_NOTABLE,
                "q문턱": Q_ALPHA,
                "예측1_판정표본": PRED1_SAMPLE,
                "예측3_판정분모": PRED3_BASE,
                "예측4_판정표본": PRED4_SAMPLE,
                "예측5_축": list(PRED5_AXES),
                "비고": "판정 표본과 분모는 사전선언 문구에 명시되지 않아 이 "
                      "스크립트를 쓰면서(결과를 보기 전에) 정했다. 실행 후에 "
                      "고치지 않는다.",
            },
            "사슬확인": chain,
            "사전예측결과": pred_results,
            "가족요약": {"F블록": f_sum, "형태자질": m_sum, "UPOS": u_sum},
        },
        "총사용률_산포": {
            "전체표본": pack_one(total_full),
            "매칭표본": pack_one(total_matched),
            "위치_대조": {
                "06위치델타": loc_total.get("델타"),
                "06위치p": loc_total.get("p"),
                "출처": "06_비교결과.json → 총사용률_비교 (읽어 옴)",
                "비고": "위치 δ와 산포 δ는 다른 것을 재는 값이다. 크기를 "
                      "견주는 것은 '어느 축의 신호가 더 큰가'를 묻기 위함이지 "
                      "둘을 같은 눈금으로 놓기 위함이 아니다.",
            },
            "가족밖_단독검정": True,
        },
        "F블록_산포": pack_family(f_packs, base_words, "06"),
        "형태자질_산포": pack_family(m_packs, base_feats, "07"),
        "UPOS_산포": pack_family(u_packs, base_upos, "07"),
        "쌍거리": {
            "정의": "매칭 표본에서 172차원 사용률 벡터의 그룹 내 계정쌍 L1 거리. "
                  f"각 무더기 {n_pair:,}계정 → {n_pairs_each:,}쌍.",
            "봇": {k: rnd(v, RATE_DIGITS) for k, v in bot_five.items()},
            "사람": {k: rnd(v, RATE_DIGITS) for k, v in hum_five.items()},
            "비_사람나누기봇": {k: rnd(v, STAT_DIGITS)
                        for k, v in dist_ratio.items()},
            "검정_안_함": f"쌍은 서로 독립이 아니다(한 계정이 {n_pair - 1:,}개 "
                     f"쌍에 동시에 들어간다). p를 붙이면 표본이 "
                     f"{n_pairs_each:,}인 것처럼 계산되어 어떤 차이든 "
                     "유의해지므로 기술통계로만 보고한다.",
            "계정별요약검정": {
                "정의": "계정마다 '같은 무더기 안 다른 계정들과의 거리 중앙값'을 "
                      "구해 계정당 값 하나로 줄였다. 계정 수가 곧 표본 수가 되어 "
                      "독립성이 회복된다. 판정에는 이 검정을 쓴다.",
                "U": rnd(acct["U"], 1), "z": rnd(acct["z"], STAT_DIGITS),
                "p": sig(acct["p"]), "q": sig(acct["p"]),
                "q비고": "단독 검정이라 q = p (m = 1 에서 BH는 항등).",
                "델타": rnd(acct["델타"], STAT_DIGITS), "방향": acct["방향"],
                "유의": acct["p"] <= Q_ALPHA,
                "주목": acct["p"] <= Q_ALPHA
                      and abs(acct["델타"]) >= DELTA_NOTABLE,
                "봇_요약": {k: rnd(v, RATE_DIGITS)
                        for k, v in acct_bot_five.items()},
                "사람_요약": {k: rnd(v, RATE_DIGITS)
                         for k, v in acct_hum_five.items()},
                "계정별_중앙값": {
                    "봇": {u: round(v, RATE_DIGITS)
                         for u, v in zip(m_bot, bot_med)},
                    "사람": {u: round(v, RATE_DIGITS)
                          for u, v in zip(m_hum, hum_med)},
                },
            },
            "한계": "L1 거리는 총사용률 자체의 크기에 끌려다닌다. 두 계정이 멀다는 "
                  "것이 문체 차이인지 분량 차이인지를 이 값만으로는 가를 수 없다.",
        },
        "IQR비": {
            "정의": "매칭 표본에서 사람 IQR ÷ 봇 IQR. 1보다 크면 사람이 넓다 = "
                  "봇이 뭉쳐 있다. 봇 IQR이 0이면 나눗셈이 성립하지 않아 결측이며 "
                  "('무한대'가 아니다) 그 수를 따로 센다. 다만 '어느 쪽이 큰가'는 "
                  "봇 IQR이 0이어도 정해지므로 종수 세기에서는 빠지지 않는다.",
            "F블록": f_iqr,
            "형태자질": m_iqr,
        },
    }
    write_json(OUT_JSON, out, indent=1)
    print(f"      {OUT_JSON}")
    print(f"      {os.path.getsize(OUT_JSON):,} bytes")

    # ── 눈으로 검수할 것 ────────────────────────────────────────
    line("확인 항목")
    print("  아래를 직접 보고 나서 10으로 넘어가십시오.")
    print("   1. 산포 신호가 위치 신호보다 큰가. [6/6] 예측 4가 09의 존재")
    print("      이유다. 총사용률에서 |산포 δ|가 |위치 δ|보다 크면 06·07·08이")
    print("      쓴 방법이 큰 쪽을 놓치고 있었다는 뜻이고, 원고의 주 결과가")
    print("      바뀐다. 작다면 사전선언대로 09의 비중을 낮춘다 — 결과를 보고")
    print("      정하는 것이 아니라 미리 적어 둔 약속을 지키는 것이다.")
    print("   2. 매칭 표본에서도 유지되는가. 전체 표본에서만 크고 매칭 표본에서")
    print("      무너진다면 그 산포는 '봇이 길게 쓴다'의 그림자다. 긴 글일수록")
    print("      사용률이 안정되므로(큰 수의 법칙) 분모가 큰 무더기는 그것만으로")
    print("      뭉쳐 보인다. [3/6]의 '전체 표본과 부호가 다름' 줄을 먼저 보라.")
    print("   3. 쌍거리 기술통계와 계정별 요약 검정이 같은 방향인가. 어긋나면")
    print("      어느 하나를 고르지 말고 왜 어긋나는지부터 확인하라. 13만 쌍의")
    print("      분포는 몇몇 계정이 통째로 밀어 올릴 수 있고, 계정별 중앙값은")
    print("      그 영향을 계정 하나 몫으로 줄인다. 두 숫자가 다른 것을 본다.")
    print("   4. 형태자질에서도 동질성이 보이는가. 어휘 층위(F 블록)에만 있으면")
    print("      주장은 '이 봇들은 같은 단어를 쓴다'로 좁아진다. 형태 층위까지")
    print("      가야 '같은 문법을 고른다'가 되고, 그것이 프롬프트·모델 공유의")
    print("      흔적으로 훨씬 곧바르다. 예측 5의 (가)와 (나)를 나눠 읽으라 —")
    print("      축이 2값인 자질은 짝끼리 δ가 같아 종수가 부풀려 보인다.")
    print("   5. 주장 범위를 반드시 제한할 것.")
    print(f"      {CLAIM_LIMIT}")
    print("      이 문장을 원고에 그대로 쓴다. 여기서 나온 동질성은 '봇'의")
    print("      성질이 아니라 '이 배포 계열'의 성질이며, 646계정이 하나의")
    print("      프레임워크·하나의 모델·하나의 시간창에서 나왔다는 사실이")
    print("      그 제한의 근거다. 11(IRA 대조)이 겨누는 자리가 바로 여기다.")
    print()
    print("  이 다섯은 스크립트가 대신 판정할 수 없는 것들이다. δ와 q를 뽑는")
    print("  일까지가 코드의 몫이고, 그 숫자가 무슨 이야기인지는 사람이 읽는다.")


if __name__ == "__main__":
    main()
