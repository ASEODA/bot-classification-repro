#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
09-2_게시물유형통제.py
────────────────────────────────────────────────────────────────────────────
목적
    01은 게시글 제목(posts)과 댓글(comment_1·comment_2)을 구분 없이 합쳤다.
    01 코드의 주석이 그 근거를 이렇게 적어 두었다 — "문체는 글의 종류가 아니라
    쓴 주체에 붙는 성질이라고 보기 때문". 09-2는 그 가정을 검사한다.

    방법은 하나뿐이다. **댓글만으로 코퍼스를 다시 만들고, 04부터 07까지를
    그 코퍼스 위에서 다시 돌린다.** 제목을 빼고도 06·07의 신호가 남으면 그
    신호는 문체다. 사라지면 그것은 문체가 아니라 글의 종류였다.

왜 장르가 교란인가 — 제목은 다른 문법으로 쓰인다
    뉴스 제목은 이렇게 생겼다.

        "Iraqi Kurds silent as Israel escalates"

    관사가 없다(the Iraqi Kurds가 아니다). be동사가 없다(are silent이 아니다).
    제목은 지면을 아끼려고 관사·조동사·연결어를 **구조적으로** 지운다. 즉
    제목을 쓰는 계정은 기능어 사용률이 낮게 나오는데, 그것은 그 사람이
    기능어를 안 쓰는 사람이라서가 아니라 제목이라는 형식이 그렇기 때문이다.

    그리고 이 자료에서 제목은 한쪽에 더 많다(2026-08-27 직접 집계).

        봇   제목 17,616건 (37.1%) · 평균 122자
        사람 제목 32,833건 (42.1%) · 평균  85자
        제목만 쓰는 계정 — 사람 39 · 봇 0

    사람 쪽에 제목이 5.0%p 더 많고, 사람 제목은 봇 제목보다 37자 짧다.
    39개 계정은 아예 제목만 쓴다. 그러면 06이 낸 "사람이 기능어를 적게 쓴다"
    (총사용률 δ = −0.130, 봇이 낮음 → 사람 쪽 꼬리가 아래로 길다)의 일부는
    문체가 아니라 **글의 종류**다. 05가 라벨 없이 발견해 둔 '헤드라인 투'
    계정이 그 반례를 미리 적어 둔 것이었다.

이 진단이 못 하는 것 — 한계를 먼저 적는다
    · **제목 한정 분석은 하지 않는다.** 제목은 문형이 특수해 기능어 사용률의
      뜻 자체가 달라지고(위의 관사 생략), 제목만으로 적격인 계정이 39개
      전원 사람이라 비교가 성립하지 않는다. 보관된 07-12 사전선언의 10-3항(현 09-2)이 그렇게 못 박았다.
      대신 장르 구성비를 계정 수준 변수로 기록해 라벨과의 상관만 보고한다.
    · **09-2는 표본이 줄어든 비교다.** 댓글이 10건에 못 미쳐 탈락하는 계정이
      생기고, 그 탈락은 무작위가 아니다(제목만 쓰는 39계정은 전원 사람이다).
      그래서 06·07과 09-2의 차이에는 '장르를 뺀 몫'과 '표본이 달라진 몫'이
      섞여 있다. 이 파일은 둘을 분리하지 못한다 — 탈락 계정의 라벨 분포를
      숫자로 내는 것까지가 할 수 있는 전부다.
    · **09-2는 매칭 표본이 아니다.** 09-1이 맞춘 분모 균형은 여기 없다. 그래서
      산포 대조는 옛 산포검정(보관)의 **전체 표본** 값과 견주는 것이 맞고, 옛 산포검정(보관)이 매칭
      표본에서만 낸 값(계정별 거리 δ = −0.9064)에는 짝이 되는 전체 표본
      값이 아예 없다. [7/8]이 이 사실을 화면에 다시 찍는다.
    · **눈금이 바뀔 수 있다.** 07의 축 판별은 자료에서 유도한다. 자료가
      바뀌면 축 목록도 따라 바뀌고, 그러면 분모가 조용히 달라진 값을 07과
      견주게 된다. [5/8]이 07의 축분류와 대조해 다르면 경고를 찍는다.
    · **라벨을 아는 상태에서 수행된다.** 06에서 라벨을 열었으므로 그 뒤 단계(보관된 07-12 사전선언이 다룬 단계)에는
      봉인이라는 보호막이 없다(보관된 07-12 사전선언의 결정 0-1). 그 자리를 사전등록이
      대신한다 — 아래 PREDICTIONS 다섯은 09-2를 돌리기 전에 문서에 확정된
      것이고, [8/8]이 자동으로 대조한다. 빗나가도 지우지 않는다.

무엇을 따르나
    보관된 07-12_사전선언.md 의 「10 — 장르 통제 재측정」 절(현 09-2)을 그대로 구현한다.

        방법 1  댓글 한정 코퍼스를 만든다. 01과 **완전히 같은 규칙**
                (URL·멘션 제거, 자기폭로 문장 절제, MIN_CHARS=20,
                 MAX_DOCS=200, MIN_DOCS=10, 계정 단위 langid 영어 판정)을
                적용하되 입력에서 posts를 뺀다.
        방법 2  04와 같은 파이프라인(tokenize,pos · bulk_process 계정 단위)
                으로 재파싱하고, 05·06·07의 로직을 그대로 써서 F·형태자질·
                UPOS를 다시 낸다. 세 가족에 각각 별도로 BH.
        방법 3  제목 한정 분석은 하지 않는다. 장르 구성비만 계정 수준
                변수로 기록해 라벨과의 상관을 본다.
        방법 4  06·07 기준선과 항목별로 대조한다. 판정 형식은 09-1과 같다 —
                유지 / 무너짐 / 방향 뒤집힘 / 신규.
        방법 5  탈락 계정은 기록만 하고 앞 단계 결과를 수정하지 않는다.

    문턱(q ≤ 0.05, |δ| ≥ 0.147)도 분모 규칙도 06·07·09-1·옛 산포검정(보관)과 같은 값을 쓴다.
    결과가 약하다고 방법을 바꾸지 않는다(보관된 07-12 사전선언의 결정 0-1).

실행 · 선행 조건
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 -u 09-2_게시물유형통제.py
    필요 패키지: langid(01과 같은 판정 도구) · stanza(04와 같은 파이프라인).

    상위 폴더(연구주제/)에 1. 원본데이터/2. BotSim Data/BotSim-24-Dataset/
    user_post_comment.json, 같은 폴더에 01_적격계정.json · 02_기능어목록.json ·
    04_기능어측정.json · 05_사용률검수.json · 06_비교결과.json ·
    07_형태자질비교.json, 보관 폴더(# 07-12 실행분 보관 (미학습)/)에
    옛 산포검정(보관) 산출물 09_산포검정.json 이 모두 있어야 한다.
    하나라도 없으면 아무것도 하지 않고 끝낸다.

    ■ 이 스크립트는 실제로 재파싱을 한다. 이 기계에서 약 30분이다. ■
    04가 문서 110,057건을 25 ms/문서로 45.9분에 끝냈고, 댓글 한정 코퍼스는
    그보다 작다. 100계정마다 중간 저장하므로 창을 닫아도 되고, 다시 실행하면
    끝난 계정을 건너뛰고 이어서 한다. 최종본이 이미 있으면 아무것도 하지
    않고 끝낸다(04와 같은 덮어쓰기 방지).

산출
    09-2_게시물유형통제.json · 09-2_게시물유형통제_출력.log
    09-2_게시물유형통제_진행.json (중간 저장 파일. 전부 끝나면 지운다)
"""

import functools
import hashlib
import json
import math
import os
import platform
import re
import statistics
import time
import unicodedata
from collections import Counter

# 진행 표시가 즉시 화면에 찍히게 한다. [04에서 가져옴]
# 30분짜리 작업에서 출력이 버퍼에 갇히면 "멈춘 것처럼" 보인다.
print = functools.partial(print, flush=True)


# ════════════════════════════════════════════════════════════════════════
# [경로]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더를 기준으로 잡는다 — 연구 폴더를 통째로 옮겨도 깨지지 않는다.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # 연구주제/ : 원본데이터와 보관 폴더가 여기 있다
BASE = f"{ROOT}/1. 원본데이터"
BOTSIM_DIR = f"{BASE}/2. BotSim Data/BotSim-24-Dataset"
POSTS_JSON = f"{BOTSIM_DIR}/user_post_comment.json"   # 원본 — 장르를 가르려면 여기까지 내려가야 한다
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"            # 01 — 적격 계정 목록 + 라벨
FUNCWORDS_JSON = f"{HERE}/02_기능어목록.json"         # 02 — 기능어 172종
MEASURE_JSON = f"{HERE}/04_기능어측정.json"           # 04 — 지문(해시)과 규모 대조
RATES_JSON = f"{HERE}/05_사용률검수.json"             # 05 — 희소성표·이상치 하한
COMPARE_JSON = f"{HERE}/06_비교결과.json"             # 06 — F 블록 위치 기준선
FEATURE_JSON = f"{HERE}/07_형태자질비교.json"         # 07 — M·UPOS 위치 기준선, 축분류
DISPERSION_JSON = f"{ROOT}/# 07-12 실행분 보관 (미학습)/09_산포검정.json"   # 옛 산포검정(보관) — 산포 기준선
OUT_JSON = f"{HERE}/09-2_게시물유형통제.json"         # 산출물
PROGRESS_JSON = f"{HERE}/09-2_게시물유형통제_진행.json"   # 중간 저장(완료 시 삭제)


# ════════════════════════════════════════════════════════════════════════
# [설정 1] 01의 적격 판정 규칙 — 한 글자도 바꾸지 않는다
# ────────────────────────────────────────────────────────────────────────
# ■ 왜 01의 필터를 그대로 써야 하나 ■
# 09-2가 재는 것은 "제목을 빼면 무엇이 달라지는가" 하나뿐이다. 그런데 필터를
# 조금이라도 손대면(예: MIN_CHARS를 15로 내려 탈락 계정을 줄이면) 06·07과
# 09-2의 차이에 '장르를 뺀 몫'과 '필터를 바꾼 몫'이 섞여 들어오고, 그 둘은
# 결과만 보고는 절대 갈라지지 않는다. 통제 실험에서 한 번에 하나만 바꾸는
# 것과 같은 이야기다. 그래서 아래 상수·정규식은 01_botsim_적격검열.py 에서
# 복사해 온 것이고, 바뀐 것은 입력에서 posts를 뺀다는 것 하나뿐이다.
#
# 01이 이 값들을 왜 이렇게 정했는지(20자·10건·200건의 근거)는 01의 주석에
# 그대로 있다. 여기서 다시 논증하지 않는다 — 다시 논증하면 다시 정할 여지가
# 생기고, 그 여지가 바로 막으려는 것이다.
# ════════════════════════════════════════════════════════════════════════
MIN_CHARS = 20          # [01에서 가져옴] 정제 후 20자 미만 문서는 버린다
MIN_DOCS = 10           # [01에서 가져옴] 적격 문서가 10건 미만인 계정은 제외
MAX_DOCS = 200          # [01에서 가져옴] 계정당 최근 200건까지만 사용
LANG_TARGET = "en"      # [01에서 가져옴] 계정 단위 langid 판정이 이 언어여야 통과

# 자기폭로 문구 — 문서를 버리지 않고 그 문장만 도려낸다. [01에서 가져옴]
SELF_REVEAL = re.compile(
    r"(as an ai language model"
    r"|i'?m sorry,? but (i cannot|as an ai)"
    r"|i cannot (comply|fulfill|browse)"
    r"|openai'?s? (content )?polic)", re.I)

RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")      # [01에서 가져옴]
RE_URL = re.compile(r"(https?://\S+|www\.\S+)")       # [01에서 가져옴]
RE_MENTION = re.compile(r"@\w+")                      # [01에서 가져옴]
RE_WS = re.compile(r"\s+")                            # [01에서 가져옴]


# ════════════════════════════════════════════════════════════════════════
# [설정 2] 04의 측정 규칙 — 역시 한 글자도 바꾸지 않는다
# ════════════════════════════════════════════════════════════════════════
CHECKPOINT_EVERY = 100  # [04에서 가져옴] 100계정마다 중간 저장
WARMUP_ACCOUNTS = 20    # [04에서 가져옴] 처음 20계정의 실측 속도로 끝을 추정한다

# 04의 자가검증 문장과 기대값. 곧은 아포스트로피판과 굽은 판을 함께 건다.
SELF_CHECK_TEXT = "I don't think they've seen it, and it isn't mine."
SELF_CHECK_TEXT_CURLY = "I don’t think they’ve seen it, and it isn’t mine."
SELF_CHECK_EXPECT = {"n't": 4, "'ve": 2}


# ════════════════════════════════════════════════════════════════════════
# [설정 3] 06·07·09-1·옛 산포검정(보관)과 같은 판정 눈금
# ════════════════════════════════════════════════════════════════════════
GROUP1, GROUP2 = "bot", "human"
# 06·07·09-1·옛 산포검정(보관)과 같은 순서로 고정한다. U와 δ는 모두 '그룹1 기준'이라 이 순서가
# 뒤집히면 부호가 통째로 반대가 되고 앞 단계와의 대조가 전부 어긋난다.

Q_ALPHA = 0.05          # BH 보정 후 유의 판정 문턱 (06·07·09-1·옛 산포검정(보관)과 같은 값)
DELTA_NOTABLE = 0.147   # '주목'의 효과크기 하한 (관례적 small 경계, 앞 단계와 같음)
SPARSE_FRAC = 0.10      # 출현 계정이 전체의 이 비율 미만이면 '희소' 표시

RATE_DIGITS = 6         # 비율·중앙값 저장 자릿수 (04·05·07·09-1·옛 산포검정(보관)과 같은 눈금)
STAT_DIGITS = 4         # U·z·δ 저장 자릿수
SIG_DIGITS = 6          # p·q는 유효숫자로 자른다 — 아래 sig() 참조

DENOM_AXIS = "축내부합"              # 분모 = 그 계정의 해당 축 총 출현수
DENOM_TOKEN = "토큰수_구두점제외"     # 분모 = 그 계정의 구두점 제외 토큰수

TOP_SHOW = 25           # 대조 표에 몇 줄을 띄울 것인가

# 앞 단계 로그에 찍힌 값. 어긋나면 알리기만 하고 계속 돈다 — 이 값으로
# 항목을 고르거나 버리지 않는다(사전선언: 사후 문턱 도입 금지).
EXPECT_ELIGIBLE = 1869
EXPECT_WORDS = 172
EXPECT_FEATURES = 58
EXPECT_UPOS = 17

# 04가 실제로 걸린 시간. [4/8]의 예상 시간을 사람이 검증할 수 있게 적어 둔다.
REF_MS_PER_DOC = 25.0
REF_04_DOCS = 110057
REF_04_MINUTES = 45.9


# ════════════════════════════════════════════════════════════════════════
# [설정 4] 보관된 07-12 사전선언의 10항(현 09-2) 실측 장르 표 — 재현되는지 대조한다
# ────────────────────────────────────────────────────────────────────────
# 보관된 07-12 사전선언의 10항(현 09-2)에 실린 표를 상수로 박아 두고, 이 스크립트가 원본에서 다시 센
# 값과 맞춰 본다. 왜 맞춰 보나 — 사전선언의 표가 이 스크립트와 다른 기준으로
# 세어진 것이라면, 09-2의 모든 전제("사람 쪽에 제목이 5%p 더 많다")가 근거를
# 잃는다. 그런데 화면에는 아무 이상도 안 찍힌다. 표를 다시 세는 데 몇 초면
# 되므로 매번 센다.
#
# ■ 세는 기준 ■ (이 한 줄이 표를 재현할 수 있느냐를 가른다)
#   대상  = 01이 적격으로 판정한 1,869계정
#   단위  = 원본 항목 하나(posts의 한 줄, comment_1·comment_2의 한 줄)
#   포함  = 텍스트가 공백을 걷어 내고도 비어 있지 않은 항목
#   제외  = 없음 — 01의 20자 필터도, 200건 상한도 여기서는 걸지 않는다
# 즉 이 표는 "01의 필터를 통과한 글"이 아니라 "적격 계정이 쓴 글 전부"의
# 장르 구성이다. 필터 뒤의 구성은 [2/8]이 따로 낸다.
# ════════════════════════════════════════════════════════════════════════
EXPECT_GENRE = {
    "bot": {"제목수": 17616, "제목비율": 0.371, "제목평균글자": 122,
            "댓글수": 29908, "댓글비율": 0.629, "댓글평균글자": 261},
    "human": {"제목수": 32833, "제목비율": 0.421, "제목평균글자": 85,
              "댓글수": 45245, "댓글비율": 0.579, "댓글평균글자": 302},
}
EXPECT_TITLE_ONLY = {"bot": 0, "human": 39}
GENRE_TOL_RATIO = 0.001     # 비율은 소수 셋째 자리까지 실린 값이다
GENRE_TOL_CHARS = 1.0       # 평균 글자는 정수로 반올림돼 실렸다(84.5 → 85)


def line(title=""):
    """구분선 한 줄. [옛 산포검정(보관)에서 가져옴]"""
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다. [04·옛 산포검정(보관)에서 가져옴]

    임시 파일에 먼저 쓰고 이름을 바꿔치기한다(os.replace). 중간 저장 파일을
    쓰는 도중에 창을 닫으면 파일이 반쯤 잘린 채 남고, 다음 실행에서 그 파일을
    읽다 깨진다. 이름 바꾸기는 쪼개지지 않는 연산이라, 어느 시점에 멈춰도
    파일은 '이전 것' 아니면 '새 것'이다. 30분짜리 작업에서 이것이 있고
    없고는 크다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def sig(x, digits=SIG_DIGITS):
    """
    p·q를 유효숫자 기준으로 자른다. [옛 산포검정(보관)에서 가져옴]

    소수 자릿수로 반올림하면(round(p, 6)) 3e-40 같은 값이 통째로 0이 된다.
    유효숫자로 자르면 크기를 잃지 않으면서 파일이 짧아진다.
    """
    if x is None:
        return None
    if x == 0.0:
        return 0.0
    return float(f"{x:.{digits}g}")


def rnd(x, digits):
    """None을 그대로 통과시키는 round. [옛 산포검정(보관)에서 가져옴] 검정 불가 칸이 None이라 필요하다."""
    return None if x is None else round(x, digits)


def fmt_dur(sec):
    """초를 사람이 읽는 단위로 바꾼다. [04에서 가져옴]"""
    if sec < 90:
        return f"{sec:.0f}초"
    if sec < 5400:
        return f"{sec / 60:.1f}분"
    return f"{sec / 3600:.2f}시간"


def quartiles(values):
    """
    중앙값과 사분위수 한 벌. [옛 산포검정(보관)에서 가져옴] 값이 둘 미만이면 사분위가 성립하지 않는다.

    method="inclusive"는 가진 자료가 모집단 전체일 때 쓰는 정의다(05·06·09-1·옛 산포검정(보관)과 같다).
    """
    if len(values) < 2:
        m = values[0] if values else 0.0
        return {"Q1": m, "중앙": m, "Q3": m}
    q1, med, q3 = statistics.quantiles(sorted(values), n=4, method="inclusive")
    return {"Q1": q1, "중앙": med, "Q3": q3}


def five_number(values):
    """최소·Q1·중앙·Q3·최대 한 벌. [옛 산포검정(보관)에서 가져옴]"""
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
# direction_of)는 보관된 09_산포검정.py 에서 한 글자도 고치지 않고 가져왔고, 옛 산포검정(보관)은
# 09-1에서, 09-1은 07에서, 07은 06에서 가져왔다. 06에서 손계산 예제를 통과한
# 코드라 다시 짜면 잃을 것만 있다. [3/8]이 같은 예제를 다시 건다.
# ════════════════════════════════════════════════════════════════════════
def normal_cdf(x):
    """
    표준정규분포의 누적확률 Φ(x). [옛 산포검정(보관)에서 가져옴]

    math.erf 로 Φ(x) = ½(1 + erf(x/√2)). |x|가 8을 넘으면 배정도 실수의
    바닥에 닿아 p가 0.0으로 찍힌다 — "차이가 없을 확률이 0"이 아니라 "이
    계산으로는 더 작은 값을 구분할 수 없다"는 뜻이다.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def ranks_with_ties(values):
    """
    오름차순 순위. 같은 값끼리는 자리 번호를 나눠 갖는다. [옛 산포검정(보관)에서 가져옴]

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
    Mann-Whitney U 검정(양측)과 Cliff's δ. 그룹1 기준. [옛 산포검정(보관)에서 가져옴]

        R1  = 그룹1이 가져간 순위의 합
        U1  = R1 − n1(n1+1)/2            (그룹1이 이긴 쌍의 수, 동점은 ½)
        δ   = 2·U1/(n1·n2) − 1           (Cliff's δ, −1 … +1)
        σ²  = (n1·n2/12)·[(N+1) − Σ(t³−t)/(N(N−1))]      (동점 보정 분산)
        z   = (U1 − n1·n2/2 − c)/σ       (c = ±0.5 연속성 보정)
        p   = 2·(1 − Φ(|z|))             (양측)

    σ² ≤ 0 이면 두 무더기의 값이 전부 같다는 뜻이라 δ = 0, z = 0, p = 1.0.
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
    Benjamini-Hochberg FDR 보정. [옛 산포검정(보관)에서 가져옴]

        p를 오름차순으로 늘어놓고,  q_(i) = min_{j ≥ i} ( p_(j) · m / j )

    09-2에서도 세 번 따로 불린다 — F 172종, 형태자질, UPOS에 각각 걸어야 하기
    때문이다. 총사용률 1건과 제목비율 1건은 가족 밖 단독이라 이 함수를 거치지
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
    """δ의 부호를 말로 옮긴다. [옛 산포검정(보관)에서 가져옴] 위치 검정용 문구다(06·07과 같다)."""
    if delta > 0:
        return "봇이 높음"
    if delta < 0:
        return "봇이 낮음"
    return "차이 없음"


def direction_disp(delta):
    """
    산포 검정용 문구. [옛 산포검정(보관)에서 가져옴]

    같은 δ라도 순위를 매긴 대상이 값이 아니라 절대편차라 뜻이 다르다.
    δ < 0 이면 봇의 절대편차가 작다 = 봇이 더 뭉쳐 있다. 위치 δ와 한 표에
    섞어 읽지 말 것.
    """
    if delta > 0:
        return "봇이 더 흩어짐"
    if delta < 0:
        return "봇이 더 뭉침"
    return "차이 없음"


# ════════════════════════════════════════════════════════════════════════
# [사전 예측] 보관된 07-12_사전선언 「10」(현 09-2)의 예측 다섯
# ────────────────────────────────────────────────────────────────────────
# 이 상수가 사전등록의 실체다. 여기 적힌 것은 결과를 보기 전에 문서에 확정된
# 것이고, [8/8]이 실제 수치와 자동으로 대조한다. 빗나간 예측을 조용히 지우거나
# 문구를 고치면 사전등록이 아무 의미가 없어진다.
#
# "근거"·"판정규칙"은 화면 폭에 맞춰 미리 끊어 둔 줄의 목록이다. 자동 줄바꿈을
# 쓰지 않는 것은 09-1·옛 산포검정(보관)과 같은 이유다 — 한글은 터미널에서 두 칸을 차지해 글자
# 수로 자르면 폭이 맞지 않는다. JSON에는 한 줄로 이어 담는다.
# ════════════════════════════════════════════════════════════════════════

# 예측 1이 지목한 '머리'. 사전선언 문구는 "we·must·our·was·he와 Tense=Past·
# Number=Sing·Gender 계열"이다. 앞의 다섯은 06의 δ 상위 다섯 단어이고,
# 뒤의 셋은 07의 δ 상위 축이다.
#
# ■ Gender 계열을 어떻게 세는가 ■
# 사전선언이 "Gender 계열"이라고만 적어 항목 수가 펼치기 나름이다. 이 파일은
# **07에서 주목이었던 Gender 축 자질 전부**를 넣는다(자료로 정해지는 값이라
# 여기서 고를 여지가 없다). 판정은 어느 쪽으로 세든 같다 — "전부 유지면
# 적중"이므로 Gender를 한 항목으로 묶든 둘로 펼치든 조건이 동일하다.
# 화면에는 펼친 목록과 축 단위 개수를 함께 찍는다.
PRED1_WORDS = ("we", "must", "our", "was", "he")
PRED1_FEATS = ("Tense=Past", "Number=Sing")
PRED1_AXIS = "Gender"

PREDICTIONS = [
    {"번호": 1,
     "축": "머리 유지",
     "서술": "we·must·our·was·he와 Tense=Past·Number=Sing·Gender 계열은 "
           "댓글 한정에서도 |δ| ≥ 0.147 을 유지한다",
     "판정규칙": ["위에 지정한 항목이 **전부** |δ| ≥ 0.147 을 유지하면 적중.",
               "하나라도 문턱 아래로 떨어지거나 방향이 뒤집히면 빗나감이다.",
               "'몇 개 이상'으로 느슨하게 잡지 않는다 — 그런 문턱은 결과를",
               "본 뒤에만 정할 수 있는 종류다(09-1 예측 1과 같은 규율).",
               "Gender 계열은 07에서 주목이었던 그 축의 자질 전부를 넣는다.",
               "판정은 09-1과 같은 형식으로 한다 — 유지 / 무너짐 / 뒤집힘."],
     "근거": ["무너지면 그 신호는 문체가 아니라 장르 혼합비였다는 뜻이고,",
             "06·07의 해석을 철회해야 한다. 보관된 07-12 사전선언의 10-1항(현 09-2)이 그렇게 적었다.",
             "09-2에서 가장 무거운 예측이며, 나머지 넷은 이 하나를 읽는",
             "보조 자료다."]},
    {"번호": 2,
     "축": "총사용률 위치",
     "서술": "총사용률 위치 δ가 더 음수 쪽으로 이동한다 (현재 06에서 −0.130)",
     "판정규칙": ["09-2의 총사용률 위치 δ가 06의 값보다 작으면(더 음수) 적중.",
               "06의 δ는 06_비교결과.json 에서 읽어 온다 — 하드코딩하지",
               "않는다. 06을 다시 돌리면 값이 바뀔 수 있고, 그때 이 판정도",
               "함께 바뀌어야 한다(옛 산포검정(보관)의 예측 4와 같은 규율).",
               "이동 폭은 판정에 넣지 않는다. 사전선언이 방향만 적었다."],
     "근거": ["제목은 기능어를 적게 쓰는 문형이고 그 제목이 사람 쪽에 5.0%p",
             "더 많았다. 제목을 빼면 사람의 총사용률이 올라가고, 봇 기준인",
             "δ는 그만큼 더 음수 쪽으로 간다. 이 예측이 빗나가면 장르 구성비",
             "차이가 총사용률에 미치는 영향이 예상과 반대라는 뜻이므로,",
             "09-2 전체의 전제를 다시 봐야 한다."]},
    {"번호": 3,
     "축": "왼쪽 꼬리",
     "서술": "총사용률 분포의 왼쪽 꼬리가 짧아진다 "
           "(05가 표시한 하한 이상치 172계정이 줄어든다)",
     "판정규칙": ["05의 이상치 하한을 그대로 쓴다(05_사용률검수.json 에서",
               "읽어 온다 — 새 경계를 만들면 자유도가 는다).",
               "판정은 **같은 계정들** 안에서 한다. 09-2에서 살아남은 계정만",
               "골라, 그 계정들의 05 값과 09-2 값에서 각각 하한 미만 개수를",
               "세고 09-2 쪽이 더 적으면 적중.",
               "표본이 줄어든 것과 꼬리가 짧아진 것을 갈라 놓기 위한",
               "규칙이다. 05 전체 1,869계정 기준 수도 함께 찍는다."],
     "근거": ["05가 라벨 없이 남긴 관찰 — 총사용률이 낮은 쪽 꼬리는 뉴스",
             "제목을 그대로 공유하는 '헤드라인 투' 계정들이었다. 제목을",
             "빼면 그 계정들의 사용률이 올라가 꼬리가 걷힌다.",
             "05의 관찰이 라벨 개봉 전 기록이라 이 대조는 사후 변명이 아니다."]},
    {"번호": 4,
     "축": "산포",
     "서술": "옛 산포검정(보관)이 낸 동질성 신호는 게시물 유형 통제 후에도 유지된다",
     "판정규칙": ["(가) 총사용률 Brown-Forsythe 에서 δ < 0 이고 q ≤ 0.05",
               "(나) 계정별 거리 요약 검정에서 δ < 0 이고 p ≤ 0.05",
               "둘 다면 적중, 하나만이면 부분 적중, 둘 다 아니면 빗나감.",
               "크기 비교(옛 산포검정(보관)의 |δ|보다 큰가 작은가)는 판정에 넣지 않는다 —",
               "표본이 달라 크기를 곧바로 견줄 수 없기 때문이다. 대신",
               "옛 산포검정(보관)의 값과 나란히 찍어 사람이 읽게 한다."],
     "근거": ["유지되지 않으면 옛 산포검정(보관)의 동질성은 '봇이 댓글만 쓴다'의 부산물이었다는",
             "뜻이다(봇은 제목만 쓰는 계정이 0이고 제목 비율도 더 낮다).",
             "그렇다면 옛 산포검정(보관)이 잡은 것은 봇의 성질이 아니라 장르 구성의 균질성이다."]},
    {"번호": 5,
     "축": "탈락 계정",
     "서술": "댓글이 MIN_DOCS 미만이 되어 탈락한 계정은 사람 쪽에 편중된다",
     "판정규칙": ["탈락 무더기의 봇 비율 ÷ 전체 봇 비율(= 편중 배수)이 1.0",
               "미만이면 적중. 1.0이면 라벨과 무관하게 섞여 있다는 뜻이고,",
               "1.0 미만이면 사람 쪽으로 몰려 있다는 뜻이다(09-1의 교차표와",
               "같은 읽는 법).",
               "탈락 계정 수가 0이면 판정불가로 적는다."],
     "근거": ["제목만 쓰는 39계정이 전원 사람이므로 최소한 그 39개는 반드시",
             "탈락한다. 예측이라기보다 산술에 가깝고, 그래서 이 예측이",
             "빗나가면 코퍼스 구축 코드를 먼저 의심해야 한다 — 다섯 예측 중",
             "유일하게 '검산' 성격을 갖는 항목이다."]},
]

# 보관된 07-12 사전선언의 10-1항(현 09-2)이 못 박은 문장. [8/8] 끝에서 화면에 그대로 찍는다.
HEAD_RULE = ('머리가 무너지면 그 신호는 문체가 아니라 장르 혼합비였다는 뜻이고, '
             '06·07의 해석을 철회해야 한다.')


# ════════════════════════════════════════════════════════════════════════
# [타이포그래피] 아포스트로피 정규화 — 곧은 것과 굽은 것
# ════════════════════════════════════════════════════════════════════════
def normalize_apostrophe(s):
    """
    굽은 아포스트로피(’, U+2019)를 곧은 것(', U+0027)으로 바꾼다. [04에서 가져옴]

    04의 첫 전량 측정이 스스로 드러낸 문제다 — 's(41,381회)와 ’s(24,845회)가
    따로 올라왔고, 원문 아포스트로피의 37%가 굽은 쪽이었다. 굽은 따옴표는
    iOS 자판·워드프로세서·LLM 출력이 즐겨 쓰므로 도구가 라벨과 상관될 수
    있고, 방치하면 "봇이 축약형을 덜 쓴다"처럼 보이는 가짜 신호를 만든다.

    토큰과 02 목록 '양쪽에' 같은 정규화를 적용한다. 잣대가 하나여야 한다.
    04의 함수를 그대로 가져온 이유가 여기 있다 — 04와 09-2의 카운트를 같은
    표에 놓으려면 세는 규칙이 한 글자도 달라선 안 된다.
    """
    return s.replace("’", "'")


# ════════════════════════════════════════════════════════════════════════
# [1] 장르 집계 — 원본에서 제목과 댓글을 갈라 센다
# ════════════════════════════════════════════════════════════════════════
def load_raw_split(eligible):
    """
    원본 JSON을 {계정ID: {"제목": [(글, 시각), ...], "댓글": [...]}}로 펼친다.

    ■ 01의 load_raw와 무엇이 다른가 ■
    01은 posts와 comment_1·comment_2를 한 통에 부었다("문체는 글의 종류가
    아니라 쓴 주체에 붙는 성질"). 09-2는 바로 그 합치기를 검사하는 파일이므로
    합치지 않고 갈라 담는다. 항목을 읽어 오는 방법·필드 이름·문자열 변환은
    01과 한 글자도 다르지 않다 — 다르면 09-2가 세는 글과 01이 세던 글이
    달라진다.

    eligible 에 든 계정만 담는다. 09-2는 01의 적격 판정을 출발점으로 삼기
    때문이다(보관된 07-12 사전선언의 10-1항(현 09-2): 댓글 한정으로 '다시' 거른다).
    """
    data = json.load(open(POSTS_JSON, encoding="utf-8"))
    raw = {}
    for uid, u in data.items():
        if uid not in eligible:
            continue
        titles, comments = [], []
        for p in (u.get("posts") or []):
            titles.append((str(p.get("posts") or ""),
                           str(p.get("created_utc") or "")))
        for block in ("comment_1", "comment_2"):
            for c in (u.get(block) or []):
                comments.append((str(c.get("comment_body") or ""),
                                 str(c.get("created_utc") or "")))
        raw[uid] = {"제목": titles, "댓글": comments}
    del data
    return raw


def genre_census(raw, labels):
    """
    라벨별 장르 구성을 센다. 보관된 07-12 사전선언의 10항(현 09-2) 실측표를 재현하는 것이 목적이다.

    세는 기준은 [설정 4]의 주석에 적어 두었다 — 적격 계정의 원본 항목 중
    공백을 걷어 내고도 비어 있지 않은 것 전부다. 01의 20자 필터도 200건
    상한도 여기서는 걸지 않는다.

    왜 필터 전 숫자를 보나. 장르 구성은 '이 계정이 무엇을 쓰는 사람인가'의
    성질이고, 필터는 그 뒤에 오는 우리 쪽 결정이다. 필터 뒤 숫자로 장르를
    말하면 "제목이 짧아 20자 필터에 더 많이 걸린다"는 우리 결정의 효과가
    장르 구성으로 둔갑한다. 필터 뒤 구성은 [2/8]이 따로 낸다.

    반환: (라벨별 집계, 계정별 제목비율, 제목만 쓰는 계정 수)
    """
    agg = {GROUP1: Counter(), GROUP2: Counter()}
    title_ratio = {}
    title_only = Counter()
    no_label = []

    for uid, blocks in raw.items():
        lab = labels.get(uid)
        if lab not in (GROUP1, GROUP2):
            no_label.append(uid)
            continue
        titles = [t for t, _ in blocks["제목"] if t.strip()]
        comments = [t for t, _ in blocks["댓글"] if t.strip()]
        agg[lab]["제목수"] += len(titles)
        agg[lab]["댓글수"] += len(comments)
        agg[lab]["제목글자"] += sum(len(t) for t in titles)
        agg[lab]["댓글글자"] += sum(len(t) for t in comments)
        total = len(titles) + len(comments)
        # 글이 하나도 없는 계정은 01의 적격 기준상 나올 수 없다. 나온다면
        # 01과 원본이 어긋난 것이므로 비율을 만들지 않고 결측으로 둔다.
        title_ratio[uid] = (len(titles) / total) if total else None
        if titles and not comments:
            title_only[lab] += 1

    out = {}
    for lab in (GROUP1, GROUP2):
        a = agg[lab]
        total = a["제목수"] + a["댓글수"]
        out[lab] = {
            "제목수": a["제목수"],
            "댓글수": a["댓글수"],
            "합": total,
            "제목비율": (a["제목수"] / total) if total else None,
            "댓글비율": (a["댓글수"] / total) if total else None,
            "제목평균글자": (a["제목글자"] / a["제목수"]) if a["제목수"] else None,
            "댓글평균글자": (a["댓글글자"] / a["댓글수"]) if a["댓글수"] else None,
            "제목만쓰는계정": title_only[lab],
        }
    return out, title_ratio, dict(title_only), no_label


def compare_to_declared(census, title_only):
    """
    다시 센 장르 표를 보관된 07-12 사전선언의 10항(현 09-2) 실측표와 맞춰 본다.

    어긋나는 칸을 목록으로 돌려준다. 어긋나도 중단하지 않는다 — 09-2의 계산은
    사전선언의 표가 아니라 이 스크립트가 다시 센 값으로 하므로, 표가 틀렸다면
    그것은 사전선언 쪽을 고쳐야 할 일이지 계산을 멈출 일이 아니다. 다만
    "전제가 흔들렸다"는 사실은 화면과 JSON에 크게 남는다.
    """
    bad = []
    for lab in (GROUP1, GROUP2):
        want, got = EXPECT_GENRE[lab], census[lab]
        for key in ("제목수", "댓글수"):
            if got[key] != want[key]:
                bad.append(f"{lab}·{key}: 다시 셈 {got[key]:,} ≠ 사전선언 {want[key]:,}")
        for key in ("제목비율", "댓글비율"):
            g, w = got[key], want[key]
            if g is None or abs(g - w) > GENRE_TOL_RATIO:
                bad.append(f"{lab}·{key}: 다시 셈 {g} ≠ 사전선언 {w}")
        for key in ("제목평균글자", "댓글평균글자"):
            g, w = got[key], want[key]
            if g is None or abs(g - w) > GENRE_TOL_CHARS:
                bad.append(f"{lab}·{key}: 다시 셈 {g} ≠ 사전선언 {w}")
        if title_only.get(lab, 0) != EXPECT_TITLE_ONLY[lab]:
            bad.append(f"{lab}·제목만쓰는계정: 다시 셈 "
                       f"{title_only.get(lab, 0)} ≠ 사전선언 {EXPECT_TITLE_ONLY[lab]}")
    return bad


def print_genre_table(census):
    """장르 구성 표. 라벨 두 줄이면 되므로 공백을 손으로 맞춰 두었다."""
    print("\n      라벨별 장르 구성 (적격 계정의 원본 항목 · 비어 있지 않은 것)")
    print("        라벨     제목수   비율  평균자      댓글수   비율  평균자")
    for lab, name in ((GROUP1, "봇   "), (GROUP2, "사람 ")):
        c = census[lab]
        print(f"        {name}{c['제목수']:>9,}{c['제목비율']:>7.1%}"
              f"{c['제목평균글자']:>8.1f}{c['댓글수']:>12,}"
              f"{c['댓글비율']:>7.1%}{c['댓글평균글자']:>8.1f}")
    gap = census[GROUP2]["제목비율"] - census[GROUP1]["제목비율"]
    print(f"\n        제목 비율 차 (사람 − 봇)   {gap:+.1%}p")
    print(f"        제목만 쓰는 계정   봇 {census[GROUP1]['제목만쓰는계정']:,} · "
          f"사람 {census[GROUP2]['제목만쓰는계정']:,}")


# ════════════════════════════════════════════════════════════════════════
# [2] 댓글 한정 코퍼스 — 01의 규칙을 그대로, 입력에서 posts만 뺀다
# ════════════════════════════════════════════════════════════════════════
def clean_doc(text):
    """
    글 1건을 정제한다. [01에서 한 글자도 고치지 않고 가져옴]

    통과하면 (정제 문자열, None, 절제여부), 탈락하면 (None, 사유, 절제여부).

    순서가 중요하다.
      1) 자기폭로 문장 절제 — 남은 문장으로 계속 진행
      2) URL·멘션 제거
      3) 길이 검사 — 절제 뒤의 길이로 판정해야 정확하다
    URL을 먼저 지우고 길이를 재야, 링크만 잔뜩 붙은 짧은 글이 '긴 글'로
    위장되지 않는다.
    """
    if not text:
        return None, "빈 문자열", False
    t = unicodedata.normalize("NFC", str(text))

    # (1) 자기폭로 문장만 도려내기
    excised = False
    if SELF_REVEAL.search(t):
        sents = RE_SENT_SPLIT.split(t)
        kept = [s for s in sents if s.strip() and not SELF_REVEAL.search(s)]
        t = " ".join(kept)
        excised = True
        if not t.strip():
            return None, "자기폭로 절제 후 내용 없음", True

    # (2) 링크·멘션 제거 — 문체가 아니라 행동의 흔적
    t = RE_URL.sub(" ", t)
    t = RE_MENTION.sub(" ", t)
    t = RE_WS.sub(" ", t).strip()

    # (3) 길이 검사
    if len(t) < MIN_CHARS:
        reason = ("자기폭로 절제 후 " if excised else "") + f"{MIN_CHARS}자 미만"
        return None, reason, excised
    return t, None, excised


def build_comment_corpus(raw, labels):
    """
    댓글만으로 계정을 다시 구성하고, 01과 같은 순서로 같은 필터를 건다.

    ■ 01과 다른 것은 딱 하나 ■
    01의 build_accounts는 posts와 comment_1·comment_2를 합친 목록을 받았다.
    여기는 comment_1·comment_2만 받는다. 그 뒤의 모든 단계 — 정제, 시각
    오름차순 정렬, 최근 MAX_DOCS건 절삭, MIN_DOCS건 미만 계정 탈락, 계정의
    글 전체를 합쳐 langid로 언어 판정 — 는 01과 같은 순서, 같은 값이다.

    ■ 왜 langid를 다시 돌리나 ■
    01에서 en으로 판정된 계정이라도 그 판정은 '제목 + 댓글'을 합친 텍스트에
    대한 것이었다. 댓글만 남기면 판정 대상 텍스트가 달라지므로 판정도 다시
    해야 한다. 01의 결과를 그대로 물려받으면 "01의 필터를 그대로 적용했다"는
    말이 거짓이 된다 — 마지막 단계만 옛 답을 베낀 것이기 때문이다.

    ■ 단계별 탈락을 라벨별로 세는 이유 ■
    01은 깔때기를 라벨 없이 냈다(그때는 라벨을 몰랐다). 09-2는 라벨을 아는
    상태이므로 각 단계가 어느 쪽을 더 많이 깎았는지 볼 수 있고, 봐야 한다.
    예측 5가 정확히 그것을 묻는다.

    반환: (계정별 문서 목록, 깔때기, 계정별 언어 판정)
    """
    import langid

    drop_reasons = Counter()            # 사유별 문서 탈락(전체)
    drop_by_label = {}                  # 사유별 문서 탈락(라벨별)
    n_docs_in = Counter()               # 라벨별 원본 댓글 수
    n_docs_trimmed = Counter()          # 라벨별 200건 상한 절삭 수
    n_excised = Counter()
    n_excised_kept = Counter()
    short_accounts = Counter()          # MIN_DOCS 미만으로 탈락한 계정(라벨별)
    lang_dropped = Counter()            # 비영어 판정으로 탈락한 계정(라벨별)
    kept_accounts = Counter()           # 최종 적격 계정(라벨별)
    dropped_uids = {"문서부족": [], "비영어": []}

    def note_drop(lab, reason):
        drop_reasons[reason] += 1
        drop_by_label.setdefault(reason, Counter())[lab] += 1

    # ── 2-1. 문서 정제 + 계정 구성 (01의 3-1과 같은 순서) ────────
    candidates = {}
    for uid in sorted(raw):
        lab = labels.get(uid, "라벨없음")
        rows = []
        for text, ts in raw[uid]["댓글"]:
            n_docs_in[lab] += 1
            cleaned, reason, excised = clean_doc(text)
            if excised:
                n_excised[lab] += 1
            if cleaned is None:
                note_drop(lab, reason)
                continue
            if excised:
                n_excised_kept[lab] += 1
            rows.append((str(ts or ""), cleaned))

        rows.sort(key=lambda r: r[0])          # 시각 오름차순 [01과 같음]
        if len(rows) > MAX_DOCS:
            n_docs_trimmed[lab] += len(rows) - MAX_DOCS
            rows = rows[-MAX_DOCS:]            # 최근분만 [01과 같음]
        if len(rows) >= MIN_DOCS:
            candidates[uid] = [c for _, c in rows]
        else:
            short_accounts[lab] += 1
            dropped_uids["문서부족"].append(uid)

    # ── 2-2. 계정 단위 언어 판정 (01의 3-2와 같음) ──────────────
    print(f"      계정 {len(candidates):,}개 언어 판정 중...", end=" ", flush=True)
    t0 = time.time()
    accounts, lang_info = {}, {}
    lang_counter = Counter()
    for uid in sorted(candidates):
        docs = candidates[uid]
        lab = labels.get(uid, "라벨없음")
        joined = " ".join(docs)
        lang, score = langid.classify(joined)
        lang_info[uid] = {"lang": lang, "score": round(float(score), 1),
                          "chars": len(joined)}
        lang_counter[lang] += 1
        if lang == LANG_TARGET:
            accounts[uid] = docs
            kept_accounts[lab] += 1
        else:
            lang_dropped[lab] += 1
            dropped_uids["비영어"].append(uid)
    print(f"{time.time() - t0:.1f}초")

    funnel = {
        "대상_계정수": len(raw),
        "원본_댓글수": dict(n_docs_in),
        "문서_탈락사유": dict(drop_reasons),
        "문서_탈락사유_라벨별": {k: dict(v) for k, v in drop_by_label.items()},
        "상한초과_절삭문서수": dict(n_docs_trimmed),
        "문서부족_탈락계정수": dict(short_accounts),
        "언어판정_대상계정수": len(candidates),
        "언어별_계정수": dict(lang_counter.most_common()),
        "비영어_탈락계정수": dict(lang_dropped),
        "적격_계정수": dict(kept_accounts),
        "적격_계정합": len(accounts),
        "적격_문서수": sum(len(v) for v in accounts.values()),
        "자기폭로_절제문서수": dict(n_excised),
        "자기폭로_절제후_생존문서수": dict(n_excised_kept),
        "탈락계정목록": dropped_uids,
    }
    return accounts, funnel, lang_info


def print_funnel(funnel, labels, n_start):
    """
    댓글 한정 깔때기를 라벨별로 띄운다. 01의 깔때기와 같은 순서로 읽힌다.

    01은 이 표를 라벨 없이 냈다. 09-2는 라벨을 아는 상태라 두 열로 낼 수 있고,
    각 단계가 어느 쪽을 더 깎았는지가 여기서 보인다.
    """
    def row(name, d):
        b, h = d.get(GROUP1, 0), d.get(GROUP2, 0)
        print(f"        {name:<26}{b:>9,}{h:>10,}{b + h:>10,}")

    print("\n      댓글 한정 깔때기 (01과 같은 규칙 · 입력에서 posts만 뺐다)")
    print("        단계                             봇      사람       합")
    row("원본 댓글 항목", funnel["원본_댓글수"])
    for reason in sorted(funnel["문서_탈락사유_라벨별"]):
        row(f"  탈락 · {reason}", funnel["문서_탈락사유_라벨별"][reason])
    row(f"  {MAX_DOCS}건 상한 절삭", funnel["상한초과_절삭문서수"])
    print("        " + "─" * 55)
    row(f"문서 {MIN_DOCS}건 미만 탈락 계정", funnel["문서부족_탈락계정수"])
    row("비영어 판정 탈락 계정", funnel["비영어_탈락계정수"])
    row("댓글 한정 적격 계정", funnel["적격_계정수"])

    kept = funnel["적격_계정수"]
    n_kept = kept.get(GROUP1, 0) + kept.get(GROUP2, 0)
    print(f"\n        01 적격 {n_start:,}계정 → 댓글 한정 적격 {n_kept:,}계정 "
          f"({n_kept / n_start:.1%} 생존)")
    print(f"        적격 문서 {funnel['적격_문서수']:,}건")
    print("\n        ※ 문서 탈락 수는 '건' 단위이고 계정 탈락 수는 '개' 단위다.")
    print("          두 줄을 더하지 말 것 — 단위가 다르다.")


def dropped_label_split(eligible, kept, labels):
    """
    댓글 한정에서 탈락한 계정의 라벨 분포와 편중 배수를 낸다. 예측 5가 쓴다.

    편중 배수 = (탈락 무더기의 봇 비율) ÷ (01 적격 전체의 봇 비율). [09-1에서 가져옴]
    1.0이면 라벨과 무관하게 탈락했다는 뜻이고, 1.0 미만이면 사람 쪽으로
    몰려 있다는 뜻이다. 원비율만 찍으면 "19.4%가 봇"이 많은 건지 적은 건지
    읽는 사람이 매번 암산해야 한다.
    """
    dropped = [u for u in eligible if u not in kept]
    n_bot_all = sum(1 for u in eligible if labels.get(u) == GROUP1)
    n_hum_all = sum(1 for u in eligible if labels.get(u) == GROUP2)
    base = n_bot_all / (n_bot_all + n_hum_all) if (n_bot_all + n_hum_all) else None

    nb = sum(1 for u in dropped if labels.get(u) == GROUP1)
    nh = sum(1 for u in dropped if labels.get(u) == GROUP2)
    n = nb + nh
    rate = (nb / n) if n else None
    return {
        "탈락계정수": len(dropped),
        "탈락_봇": nb,
        "탈락_사람": nh,
        "탈락_봇비율": rate,
        "전체_봇비율": base,
        "편중배수": (rate / base) if (rate is not None and base) else None,
        "봇에서_탈락한_비율": (nb / n_bot_all) if n_bot_all else None,
        "사람에서_탈락한_비율": (nh / n_hum_all) if n_hum_all else None,
        "탈락계정목록": dropped,
    }


# ════════════════════════════════════════════════════════════════════════
# [3] 파이프라인과 측정 — 04와 똑같이
# ════════════════════════════════════════════════════════════════════════
def build_pipeline():
    """
    04가 만든 그 파이프라인을 그대로 만든다. [04에서 가져옴]

        processors="tokenize,pos" · use_gpu=False

    한 글자라도 다르게 만들면 03의 감사 결과("봇 글과 사람 글에서 파서가
    비슷하게 작동한다")가 이 측정에 적용되지 않는다. 그리고 09-2의 수치를
    04의 수치와 나란히 놓을 수도 없게 된다 — 두 표의 차이에 '장르를 뺀 몫'과
    '파서 구성이 달라진 몫'이 섞이기 때문이다. 09-2가 재려는 것은 앞의 하나뿐이다.

    stanza.download를 부르지 않는다. 03이 이미 모델을 ~/stanza_resources에
    받아 두었고, download는 매번 인터넷으로 목록 파일을 확인하러 나간다.
    """
    import stanza
    print("      파이프라인 생성 중...", end=" ", flush=True)
    t0 = time.time()
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos",
                          verbose=False, use_gpu=False)
    print(f"{time.time() - t0:.1f}초")
    return nlp


def measure_account(nlp, docs, funcword_set):
    """
    한 계정의 문서 전부를 파싱해 원카운트 한 벌을 만든다. [04에서 가져옴]

    ── bulk 처리로 파싱한다 ────────────────────────────────────────
    문서를 하나씩 nlp(text)로 넘기면 03 실측 173 ms/문서다. bulk_process는
    문서 목록을 받아 내부에서 묶어 처리하므로 호출 비용이 분산된다(04 실측
    25 ms/문서). 문서 경계는 보존된다 — 입력 N건에 Document도 N개다.

    ── 기능어는 '표면형'으로 센다 ──────────────────────────────────
    소문자로 바꾸고 아포스트로피를 정규화한 표면형이 02의 목록(같은 정규화
    적용, 172종)에 있으면 센다. 그 자리에서 파서가 붙인 품사는 보지 않는다.
    품사를 조건으로 걸면 파서 오류율의 라벨 간 차이가 측정치에 그대로
    들어오는데, 03 [D]가 걱정한 것이 정확히 그것이었다.

    ── 원카운트만 저장한다 ────────────────────────────────────────
    사용률(= 횟수 / 총 토큰)은 [5/8]에서 05의 분모 규칙으로 계산한다.
    반환값의 카운트는 0을 담지 않는다(희소 저장). 없는 키 = 0으로 읽으면 된다.
    """
    parsed = nlp.bulk_process(docs)

    n_sent = 0
    n_tok = 0          # 구두점 포함
    n_tok_nopunct = 0  # 구두점 제외
    fw = Counter()     # 기능어 표면형
    upos = Counter()   # 품사
    feats = Counter()  # 형태 자질("Tense=Past" 같은 키=값 하나하나)

    for doc in parsed:
        for sent in doc.sentences:
            n_sent += 1
            for w in sent.words:
                n_tok += 1
                upos[w.upos] += 1
                if w.upos != "PUNCT":
                    n_tok_nopunct += 1

                surface = normalize_apostrophe(w.text.lower())
                if surface in funcword_set:
                    fw[surface] += 1

                # feats는 "Mood=Ind|Number=Sing|Tense=Pres" 처럼 막대로 이어진
                # 문자열이다. 막대로 끊어 "키=값" 단위로 센다. 통짜로 세면
                # 조합이 수백 가지로 흩어져 아무것도 비교할 수 없다.
                if w.feats:
                    for kv in w.feats.split("|"):
                        feats[kv] += 1

    return {
        "문서수": len(docs),
        "문장수": n_sent,
        "토큰수": n_tok,
        "토큰수_구두점제외": n_tok_nopunct,
        "기능어": dict(fw.most_common()),
        "UPOS": dict(upos.most_common()),
        "자질": dict(feats.most_common()),
    }


def input_fingerprint(accounts, funcwords):
    """
    입력이 무엇이었는지 짧게 요약한 지문을 만든다. [04에서 가져옴]

    쓸모: 중간 저장 파일을 이어받을 때 "그때의 입력과 지금의 입력이 같은가"를
    확인한다. 코퍼스 구축 코드를 한 줄 고쳐 계정이 1,436개에서 1,441개가
    됐는데 앞의 900계정 결과를 그대로 이어 붙이면, 한 파일 안에 기준이 다른
    수치가 섞인다. 눈으로는 절대 못 잡는 종류의 오염이다.

    "코퍼스" 항목이 04의 지문에 없던 칸이다. 09-2의 중간 저장 파일과 04의
    중간 저장 파일은 이름이 달라 섞일 일이 없지만, 지문만 보고도 어느 쪽
    작업인지 알 수 있게 적어 둔다.
    """
    h = hashlib.sha256("\n".join(funcwords).encode("utf-8")).hexdigest()[:16]
    return {
        "코퍼스": "댓글 한정(comment_1·comment_2만, posts 제외)",
        "기능어_해시": h,
        "기능어_개수": len(funcwords),
        "정규화": "아포스트로피 U+2019→U+0027",   # 세는 규칙도 지문의 일부다
        "계정수": len(accounts),
        "문서수": sum(len(v) for v in accounts.values()),
    }


def self_check_contraction(nlp, funcword_set):
    """
    02의 목록과 stanza의 토큰화가 서로 맞물리는지 확인한다. [04에서 가져옴]

    왜 매 실행마다 보나. 02 목록은 UD 분해형 규약을 따른다 — 목록에 don't가
    아니라 do와 n't가 따로 들어 있다. 이 규약은 stanza가 실제로 축약형을
    쪼개 줄 때만 맞는다. 쪼개지 않게 되면(모델 교체, 버전 변경, 파이프라인
    구성 실수) don't는 목록의 어느 항목과도 일치하지 않아 조용히 0으로
    세어진다. 오류 메시지는 나오지 않는다. 부정 표현이 통째로 사라진 표를
    가지고 30분을 돌린 뒤에야 알게 된다.

    검사는 본 측정과 똑같은 함수(measure_account)를 부른다. 검사만 통과하고
    본 측정은 다른 경로로 가는 일이 없게 하려는 것이다.
    """
    print("\n  ── (2) 축약형이 기능어로 잡히는가 — 곧은 것과 굽은 것 모두 ──")
    print(f'  입력 1 (곧은 \'): "{SELF_CHECK_TEXT}"')
    print(f'  입력 2 (굽은 ’): "{SELF_CHECK_TEXT_CURLY}"')
    print("  03 [C] 문장과 그 굽은 아포스트로피판이다. 분해(do+n't)와")
    print("  정규화(’→')가 함께 작동해야 아래 기대값이 나온다.")

    got = measure_account(nlp, [SELF_CHECK_TEXT, SELF_CHECK_TEXT_CURLY],
                          funcword_set)
    counts = got["기능어"]

    ok = True
    for word, expect in SELF_CHECK_EXPECT.items():
        actual = counts.get(word, 0)
        mark = "통과" if actual == expect else "실패"
        if actual != expect:
            ok = False
        print(f"  {word:<6} 기대 {expect}회 · 실제 {actual}회   {mark}")
    print(f"  (이 문장에서 잡힌 기능어 전체: {counts})")
    return ok


# ── 자가검증 고정 예제 (통계) ───────────────────────────────────
# 06·07·09-1·옛 산포검정(보관)의 SELF_CHECK_* 를 그대로 가져왔다. 손계산 과정은
# self_check_stats()의 docstring에 있다.
#   (설명, A(=그룹1), B(=그룹2), 기대 U_A, 기대 δ, 기대 σ²)
SELF_CHECK_U = [
    ("완전 분리", [1, 2, 3], [4, 5, 6], 0.0, -1.0, 5.25),
    ("동점 포함", [1, 1, 2], [1, 2, 2], 3.0, -1.0 / 3.0, 4.05),
]
SELF_CHECK_BH_P = [0.01, 0.02, 0.03, 0.04]
SELF_CHECK_BH_Q = [0.04, 0.04, 0.04, 0.04]
SELF_CHECK_TOL = 1e-9


def self_check_stats():
    """
    U·δ·BH 구현을 손으로 푼 예제와 맞춘다. [옛 산포검정(보관)의 self_check_stats 그대로]

    06·07·09-1·옛 산포검정(보관)에서 이미 통과한 코드를 왜 또 거는가. 이 파일이 앞 단계를 import
    하는 것이 아니라 복사해 왔기 때문이다. 복사 과정에서 부호 하나가 바뀌어도
    코드는 멀쩡히 돌고 그럴듯한 p값이 나온다. 순위 검정은 틀려도 조용하다.

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


def self_check(nlp, funcword_set):
    """
    두 자가검증을 차례로 걸고, 하나라도 어긋나면 파싱을 시작하지 않는다.

    순서에 뜻이 있다. 통계 기계를 먼저 거는 것은 파이프라인 없이도 되기
    때문이고, 축약형 검사를 뒤에 두는 것은 nlp가 필요하기 때문이다. 둘 다
    통과해야 30분짜리 파싱으로 들어간다 — 30분을 돌린 뒤에 부정 표현이
    통째로 빠진 표를 발견하는 것보다 여기서 2초 쓰는 편이 훨씬 싸다.
    """
    ok_stats = self_check_stats()
    ok_tok = self_check_contraction(nlp, funcword_set)
    if ok_stats and ok_tok:
        print("\n  두 검사 모두 통과했다. 파싱으로 들어간다.")
        return True

    print()
    print("■ 중단 — 자가검증 실패")
    print("  파싱을 시작하지 않습니다. 이 상태로 돌리면 틀린 표가 조용히 나옵니다.")
    if not ok_stats:
        print("  통계 쪽에서 짚어 볼 곳:")
        print("   · ranks_with_ties 의 평균 순위 — 자리 번호가 1부터인가")
        print("   · U1 = R1 − n1(n1+1)/2 에서 n1이 그룹1의 크기가 맞는가")
        print("   · 분산의 동점 보정 항 Σ(t³−t)/(N(N−1)) 의 부호와 분모")
        print("   · bh_qvalues 의 누적 min 방향 — 큰 p부터 거꾸로 훑는가")
        print("   (이 넷은 06→07→09-1→옛 산포검정(보관)→09-2로 그대로 옮겨 온 코드다. 06 원본과 대조하라.)")
    if not ok_tok:
        print("  토큰화 쪽에서 짚어 볼 곳:")
        print("   · stanza 버전이나 영어 모델이 03·04 실행 때와 달라졌는가")
        print("     (03_설치확인_기록.json·04_기능어측정.json의 '설정'과 대조)")
        print("   · 02_기능어목록.json이 분해형이 아닌 목록으로 바뀌었는가")
        print("   · normalize_apostrophe 가 토큰과 목록 양쪽에 똑같이 걸리는가")
        print("   · 파이프라인 구성(tokenize,pos)이 바뀌었는가")
    return False


# ════════════════════════════════════════════════════════════════════════
# [4] 중간 저장 / 이어서 하기 — 04의 방식 그대로
# ════════════════════════════════════════════════════════════════════════
def load_progress():
    """중간 저장 파일이 있으면 읽어 준다. 없으면 None. [04에서 가져옴]"""
    if not os.path.exists(PROGRESS_JSON):
        return None
    return json.load(open(PROGRESS_JSON, encoding="utf-8"))


def save_progress(done, fingerprint, elapsed_total):
    """
    지금까지 끝낸 계정을 통째로 저장한다. [04에서 가져옴]

    끝난 계정만 담고 남은 계정 목록은 담지 않는다. 다음 실행이 코퍼스를 다시
    지어 "저장된 것에 없는 계정"을 남은 일로 계산하므로, 목록을 두 벌
    관리하다 어긋나는 일이 없다. 코퍼스를 다시 짓는 데 드는 시간(원본 적재 +
    langid)은 1분 남짓이라 이어받기의 이득을 해치지 않는다.

    들여쓰기 없이 쓴다 — 이 파일은 수십 번 다시 쓰이는 작업용이다.
    """
    write_json(PROGRESS_JSON, {
        "안내": "09-2번의 중간 저장 파일입니다. 측정이 끝나면 자동으로 지워집니다.",
        "지문": fingerprint,
        "완료계정수": len(done),
        "누적소요초": round(elapsed_total, 1),
        "저장시각": time.strftime("%Y-%m-%d %H:%M:%S"),
        "계정": done,
    })


def run_measurement(nlp, accounts, funcword_set, fp):
    """
    계정을 하나씩 파싱해 카운트한다. 여기가 30분이다.

    04의 [5/5]와 같은 구조다 — uid 오름차순 고정, 처음 WARMUP_ACCOUNTS
    계정의 실측 속도로 이 실행의 끝을 추정, CHECKPOINT_EVERY 계정마다 중간
    저장. 계정당 문서 수가 10~200건으로 제각각이라 '계정당 평균'으로 환산하면
    큰 계정이 몰린 구간에서 크게 빗나가므로 문서당 속도로 환산한다.

    반환: (계정별 측정치, 이번 실행 소요초, 누적 소요초). 이어받기 실패 시 None.
    """
    done, prev_sec = {}, 0.0
    prog = load_progress()
    if prog:
        if prog.get("지문") != fp:
            print("■ 중단 — 중간 저장 파일과 지금의 입력이 다릅니다.")
            print(f"  저장 당시: {prog.get('지문')}")
            print(f"  지금:      {fp}")
            print("  01·02가 다시 돌았거나 코퍼스 구축 코드가 바뀐 것으로 보입니다.")
            print("  기준이 다른 수치를 이어 붙이면 한 파일 안에 서로 다른 잣대가")
            print("  섞이고, 나중에 눈으로는 찾을 수 없습니다.")
            print(f"  → {PROGRESS_JSON} 을(를) 지우고 처음부터 다시 실행하십시오.")
            return None
        done = prog["계정"]
        prev_sec = prog.get("누적소요초", 0.0)
        print(f"      중간 저장을 찾았습니다 — 완료 {len(done):,}계정 "
              f"(그때까지 {fmt_dur(prev_sec)})")
        print("      끝난 계정은 건너뛰고 이어서 합니다.")
    else:
        print("      중간 저장 없음. 처음부터 시작합니다.")

    # 계정 순서를 uid 오름차순으로 고정한다. 실행할 때마다 순서가 달라지면
    # "몇 번째까지 했다"는 말이 뜻을 잃는다.
    todo = [uid for uid in sorted(accounts) if uid not in done]
    todo_docs = sum(len(accounts[uid]) for uid in todo)
    n_total = fp["계정수"]
    print(f"      남은 계정 {len(todo):,}개 · 문서 {todo_docs:,}건")
    if todo_docs:
        print(f"      04 실측 {REF_MS_PER_DOC:.0f} ms/문서로 어림하면 "
              f"{fmt_dur(todo_docs * REF_MS_PER_DOC / 1000)}입니다.")
        print(f"      (04는 문서 {REF_04_DOCS:,}건에 {REF_04_MINUTES}분이 걸렸다. "
              "아래 실측으로 다시 잡는다.)")
    if not todo:
        print("      남은 계정이 없습니다. 저장된 측정치로 바로 넘어갑니다.")
        return done, 0.0, prev_sec

    print(f"      {CHECKPOINT_EVERY}계정마다 중간 저장합니다. 창을 닫아도 됩니다.")
    t_run = time.time()
    docs_run = 0

    for i, uid in enumerate(todo, 1):
        docs = accounts[uid]
        done[uid] = measure_account(nlp, docs, funcword_set)
        docs_run += len(docs)

        if i == WARMUP_ACCOUNTS:
            el = time.time() - t_run
            per_doc = el / docs_run
            left = (todo_docs - docs_run) * per_doc
            print()
            print(f"      ── 속도 실측 (처음 {WARMUP_ACCOUNTS}계정) ──")
            print(f"         문서 {docs_run:,}건 · {el:.1f}초 "
                  f"→ {per_doc * 1000:.0f} ms/문서")
            print(f"         남은 문서 {todo_docs - docs_run:,}건 "
                  f"→ 예상 {fmt_dur(left)}")
            print(f"         (04는 {REF_MS_PER_DOC:.0f} ms/문서였다. 크게 다르면 "
                  "다른 기계이거나 다른 구성이다.)")
            print()

        if i % CHECKPOINT_EVERY == 0:
            el = time.time() - t_run
            save_progress(done, fp, prev_sec + el)
            per_doc = el / docs_run
            left = (todo_docs - docs_run) * per_doc
            print(f"      {len(done):,}/{n_total:,} 계정 · "
                  f"경과 {fmt_dur(el)} · 잔여 추정 {fmt_dur(left)} · 저장 완료")

    run_sec = time.time() - t_run
    print(f"      {len(done):,}/{n_total:,} 계정 완료 · "
          f"이번 실행 {fmt_dur(run_sec)}")
    return done, run_sec, prev_sec + run_sec


# ════════════════════════════════════════════════════════════════════════
# [5-가] 사용률 — 05의 분모 규칙 (사전선언 05-06 결정 1)
# ════════════════════════════════════════════════════════════════════════
def compute_rates(measures):
    """
    계정마다 단어별 사용률과 총 사용률을 낸다. [05에서 가져옴]

    분모는 토큰수_구두점제외 하나로 고정이다(05-06 사전선언 결정 1). 구두점
    습관은 R 블록이 다룰 신호라 F 블록과 섞지 않는다.

    희소 저장은 04·05의 방식을 그대로 잇는다 — 0회인 단어는 담지 않는다.
    없는 키 = 0으로 읽으면 되고, 아래 word_vector()가 그 규약을 지킨다.

    분모가 0인 계정은 사용률을 정의할 수 없어 따로 빼서 알린다. 결정 2가
    금지한 '분석적 제외'가 아니라 나눗셈이 성립하지 않는 것뿐이다.
    """
    rates, undefined = {}, []
    for uid in sorted(measures):
        a = measures[uid]
        denom = a["토큰수_구두점제외"]
        if denom == 0:
            undefined.append(uid)
            continue
        counts = a["기능어"]
        rates[uid] = {
            "총사용률": round(sum(counts.values()) / denom, RATE_DIGITS),
            "분모": denom,
            "사용률": {w: round(n / denom, RATE_DIGITS)
                     for w, n in counts.items()},
        }
    return rates, undefined


def word_vector(uids, rates, word):
    """
    한 단어에 대해, 주어진 계정들의 사용률을 순서대로 늘어놓는다. [06·09-1·옛 산포검정(보관)에서 가져옴]

    ■ 여기가 F 블록에서 가장 틀리기 쉬운 한 줄이다. ■
    사용률은 '희소 저장'이라 한 번도 안 쓴 단어는 그 계정의 사전에 아예 키가
    없다. 그래서 .get(word, 0.0) 의 기본값 0.0이 반드시 있어야 한다. 없는
    키를 건너뛰면 "그 단어를 한 번도 안 쓴 계정"이 통째로 표본에서 사라지고,
    정작 재려던 '덜 쓴다'가 바로 그 사라진 0들이다. 결과 전체가 뒤집힌다.
    """
    return [rates[u]["사용률"].get(word, 0.0) for u in uids]


def word_presence(uids, rates, words):
    """주어진 표본 안에서 각 단어를 한 번이라도 쓴 계정 수. [옛 산포검정(보관)에서 가져옴]"""
    out = {w: 0 for w in words}
    for u in uids:
        used = rates[u]["사용률"]
        for w in words:
            if used.get(w, 0.0) > 0:
                out[w] += 1
    return out


# ════════════════════════════════════════════════════════════════════════
# [5-나] 분모 규칙 — 07의 축 판별 블록을 통째로 가져온다
# ────────────────────────────────────────────────────────────────────────
# build_axis_map · axis_of · denom_kind_of · compute_ratios ·
# compute_upos_ratios · defined_values 는 07_형태자질비교.py 에서 한 글자도
# 고치지 않고 가져왔다(09-1·옛 산포검정(보관)도 같은 코드를 쓴다). 09-2가 07과 같은 눈금을
# 써야 "07이 전체 글에서 본 것과 09-2가 댓글에서 보는 것"을 같은 자리에 놓을
# 수 있다. 분모 규칙을 손대면 그 대조가 성립하지 않는다.
#
# ■ 다만 축 목록은 자료에서 다시 유도한다 ■
# 07이 축을 하드코딩하지 않고 자료에서 유도한 것은 "자료가 바뀌면 규칙이
# 따라간다"는 설계였다. 09-2는 자료가 바뀐 경우이므로 그 설계대로 다시 유도한다.
# 그런데 그러면 눈금이 조용히 달라질 수 있다 — 예를 들어 어떤 축의 값이
# 댓글에서 하나로 줄면 분모가 '축 내부 합'에서 '토큰수'로 바뀐다. 그래서
# [5/8]이 07의 축분류와 대조해 다르면 경고를 찍는다. 규칙은 따라가되,
# 눈금이 바뀐 사실은 반드시 드러나야 한다.
# ════════════════════════════════════════════════════════════════════════
def build_axis_map(measures):
    """
    자료 전체를 훑어 축마다 어떤 값들이 나타나는지 모은다. [07에서 가져옴]

    07과 같이 **라벨이 붙은 계정 전부**를 넘긴다. 한쪽 무더기에서만 유도하면
    축의 값 종수가 달라져 분모가 조용히 바뀐다.

    반환: {축 이름: 정렬된 값 목록}
    """
    axis_values = {}
    for a in measures.values():
        for key in a.get("자질", {}):
            axis, sep, val = key.partition("=")
            if not sep:
                axis, val = key, ""
            axis_values.setdefault(axis, set()).add(val)
    return {ax: sorted(vs) for ax, vs in axis_values.items()}


def axis_of(key):
    """자질 키에서 축 이름만 떼어 낸다. [07에서 가져옴] "="가 없으면 키 전체가 축이다."""
    return key.split("=", 1)[0]


def denom_kind_of(key, axis_map):
    """
    이 자질에 어떤 분모를 쓸지 정한다. [07에서 가져옴] 보관된 07-12 사전선언의 07항 표 그대로다.

        대립값 ≥ 2  →  그 계정의 해당 축 총 출현수      (DENOM_AXIS)
        대립값 = 1  →  그 계정의 토큰수_구두점제외      (DENOM_TOKEN)
    """
    return DENOM_AXIS if len(axis_map.get(axis_of(key), [""])) >= 2 else DENOM_TOKEN


def compute_ratios(measures, keys, axis_map):
    """
    계정마다 자질 비율을 낸다. [07에서 가져옴] 반환은 (판정용, 보조용, 출현계정수).

    없는 키는 0회다 — 결측이 아니다. 결측 판정은 오로지 분모로만 한다.
        Tense=Past 0회, Tense=Pres 12회  →  0 / 12 = 0.0    (값이 있다)
        Tense 축 자체가 0회              →  0 / 0  = 결측   (나눗셈 불성립)
    """
    kinds = {k: denom_kind_of(k, axis_map) for k in keys}
    ratios, aux, presence = {}, {}, {k: 0 for k in keys}

    for uid in sorted(measures):
        a = measures[uid]
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


def compute_upos_ratios(measures, keys):
    """
    품사 비율. [07에서 가져옴] 분모는 언제나 토큰수_구두점제외다(보관된 07-12 사전선언의 07항).

    PUNCT 줄만은 분모가 구두점을 뺀 수인데 분자는 구두점 수라 '말 토큰 대비
    구두점'이라는 다른 뜻의 값이 된다. 07·09-1·옛 산포검정(보관)이 그랬듯 09-2도 그 줄을
    해석하지 않는다.
    """
    ratios, presence = {}, {k: 0 for k in keys}
    for uid in sorted(measures):
        a = measures[uid]
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
    결측(None)을 뺀 값만 순서대로 늘어놓는다. [07에서 가져옴]

    결측은 그 자질의 검정에서만 빠진다. 계정이 통째로 빠지는 것이 아니라
    칸 하나가 빠지는 것이라, 같은 계정이 Tense 검정에는 들어가고 Mood 검정에는
    빠질 수 있다. 그래서 유효 계정 수가 자질마다 다르고, 표에 그 수를 싣는다.
    """
    out = []
    for u in uids:
        v = ratios[u][key]
        if v is not None:
            out.append(v)
    return out


def compare_axis_map(axis_map, base_axes):
    """
    09-2가 유도한 축과 07의 축분류를 대조한다. 눈금이 바뀌었는지를 보는 자리다.

    07 JSON의 "축분류"는 {축: {값종수, 값목록, 분모종류, 자질수}} 꼴이다.
    세 가지를 본다.
        · 07에 있던 축이 09-2에서 사라졌는가 (그 축의 자질이 댓글에 안 나온 것)
        · 09-2에 새로 생긴 축이 있는가
        · 남은 축에서 값 목록이 달라졌는가 — 특히 **분모 종류가 바뀐 축**

    분모 종류가 바뀐 축이 가장 위험하다. 07에서는 축 내부 비율이던 자질이
    09-2에서는 토큰수 대비 비율이 되면, 같은 이름의 두 δ가 서로 다른 것을
    재고 있는데 표에서는 나란히 놓인다. 그래서 따로 세어 크게 찍는다.

    반환: (기록용 사전, 분모 종류가 바뀐 축 목록)
    """
    now = {ax: sorted(vals) for ax, vals in axis_map.items()}
    before = {ax: list(info.get("값목록") or [])
              for ax, info in (base_axes or {}).items()}

    gone = sorted(set(before) - set(now))
    added = sorted(set(now) - set(before))
    changed, denom_changed = [], []
    for ax in sorted(set(now) & set(before)):
        if now[ax] != before[ax]:
            changed.append({"축": ax, "07값": before[ax], "10값": now[ax]})
        kind_before = DENOM_AXIS if len(before[ax]) >= 2 else DENOM_TOKEN
        kind_now = DENOM_AXIS if len(now[ax]) >= 2 else DENOM_TOKEN
        if kind_before != kind_now:
            denom_changed.append({"축": ax, "07분모": kind_before,
                                  "10분모": kind_now})
    return {
        "07축수": len(before), "10축수": len(now),
        "사라진축": gone, "새로생긴축": added,
        "값목록이_달라진축": changed,
        "분모종류가_바뀐축": denom_changed,
        "동일": not (gone or added or changed),
    }, denom_changed


# ════════════════════════════════════════════════════════════════════════
# [5-다] 비교 — 07의 compare_family를 getter로 일반화한 것
# ════════════════════════════════════════════════════════════════════════
def compare_family(keys, bot_ids, human_ids, getter, presence, sparse_cut,
                   kinds=None):
    """
    한 가족을 통째로 검정하고 BH를 건다. [07의 compare_family에 옛 산포검정(보관)의 getter 방식을 붙임]

    계산은 07과 한 글자도 다르지 않다. 달라진 것은 값을 꺼내는 방법을 밖에서
    넣어 준다는 것뿐이다 — F 블록은 사용률에서(word_vector), M·UPOS는 07의
    분모 규칙으로 만든 비율에서(defined_values) 꺼낸다. 옛 산포검정(보관)이 bf_family를
    그렇게 만든 것과 같은 이유다. 꺼내는 방법이 셋인데 검정을 세 벌 적어 두면
    언젠가 한 벌만 고치게 된다.

    ■ BH 가족에서 검정 불가 항목을 빼는 이유 ■
    한쪽 무더기가 비면 U를 계산할 수 없다. p가 없는 항목을 BH에 넣을 방법이
    없으므로(m만 부풀린다) 가족에서 뺀다. 뺀 개수는 화면과 JSON에 그대로
    적는다 — m이 58이 아니라 56이었다는 사실은 q값의 뜻을 바꾸므로 숨기면
    안 된다. 이것은 사후 문턱이 아니다. 문턱은 "값이 있는데 작아서 버리는
    것"이고, 여기는 값 자체가 없다.

    반환: (|δ| 내림차순 (키, 결과) 목록, 검정 가능 항목 수)
    """
    n_all = len(bot_ids) + len(human_ids)
    rows = []
    for k in keys:
        v1 = getter(bot_ids, k)
        v2 = getter(human_ids, k)
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

    # 검정 불가는 |δ|를 −1로 쳐서 맨 뒤로 보낸다(δ의 하한이 −1이라 겹치지 않는다).
    rows.sort(key=lambda kv: -(abs(kv[1]["델타"]) if kv[1]["검정가능"] else -1.0))
    return rows, len(testable)


def family_summary(rows, n_family, sparse_cut, n_all, label):
    """가족 하나의 요약을 찍는다. [07의 family_summary 그대로]"""
    sig_n = sum(1 for _, r in rows if r["유의"])
    notable = [(k, r) for k, r in rows if r["주목"]]
    up = sum(1 for _, r in notable if r["델타"] > 0)
    down = sum(1 for _, r in notable if r["델타"] < 0)
    sparse_n = sum(1 for _, r in notable if r["희소"])
    untestable = sum(1 for _, r in rows if not r["검정가능"])

    # 아래 줄들의 공백도 손으로 맞춘 것이다(숫자가 49번째 칸에서 끝난다).
    print(f"\n      [{label}] BH 가족 크기                  {n_family:>4}종 "
          f"/ {len(rows)}종")
    if untestable:
        print(f"        검정 불가로 가족에서 빠짐           {untestable:>4}종")
    print(f"        유의 (q ≤ {Q_ALPHA})                      "
          f"{sig_n:>4}종")
    print(f"        주목 (q ≤ {Q_ALPHA} 그리고 |δ| ≥ {DELTA_NOTABLE})   "
          f"{len(notable):>4}종")
    print(f"          봇이 높음                          {up:>4}종")
    print(f"          봇이 낮음                          {down:>4}종")
    print(f"          그중 희소 표시                     {sparse_n:>4}종")
    print(f"        (희소 = 그 항목이 나온 계정이 {sparse_cut:,}개 미만 — "
          f"댓글 한정 {n_all:,}계정의 {SPARSE_FRAC:.0%})")
    return {
        "가족크기": n_family,
        "대상종수": len(rows),
        "검정불가": untestable,
        "유의": sig_n,
        "주목": len(notable),
        "봇이높음": up,
        "봇이낮음": down,
        "희소포함": sparse_n,
        "주목목록": [k for k, _ in notable],
    }


# ════════════════════════════════════════════════════════════════════════
# [6] 기준선 대조 — 09-1의 crosswalk 블록을 그대로 (판정 형식이 같아야 한다)
# ════════════════════════════════════════════════════════════════════════
def crosswalk_head(base_label):
    """대조 표의 머리글. [09-1에서 가져옴] base_label 은 "06" 또는 "07"."""
    return ("      항목" + " " * 11 + f"{base_label} δ" + " " * 2 + "09-2 δ"
            + " " * 6 + "Δδ" + " " * 9 + "q  판정")


def crosswalk(rows, baseline):
    """
    09-2의 한 가족 결과에 앞 단계(06 또는 07)의 δ를 나란히 붙인다. [09-1에서 가져옴]

    ■ 각 칸의 뜻 ■
        앞델타   06 또는 07이 전체 글에서 낸 δ
        델타     09-2가 댓글 한정에서 낸 δ
        변화량   09-2 − 앞 (부호 있는 값. 방향까지 읽으려면 부호가 필요하다)
        앞주목   앞 단계에서 q ≤ 0.05 이면서 |δ| ≥ 0.147 이었는가
        주목     09-2에서 같은 두 조건을 넘었는가
        유지     09-2에서 |δ| ≥ 0.147 인가
        뒤집힘   부호가 반대로 갔는가

    ■ 유지와 주목을 왜 따로 두나 ■ [09-1의 논리를 그대로 잇는다]
    보관된 07-12 사전선언의 10-1항(현 09-2)이 "댓글 한정에서도 |δ| ≥ 0.147 을 유지한다"라고만 적었지
    q 조건을 붙이지 않았다. 붙이면 안 되는 이유가 있다 — 댓글 한정으로
    표본이 줄어 q는 그것만으로도 커진다. q까지 걸면 '표본이 작아진 것'을
    '신호가 사라진 것'으로 오독하게 된다. 그래서 판정은 δ 문턱으로 하고,
    q는 참고 칸으로 나란히 둔다. 09-2에서 새로 문턱을 넘은 항목(신규)도 같은
    이유로 결론에 올리지 않는다 — 09-2는 진단이지 발견이 아니다.

    ■ 뒤집힘의 무게 ■
    부호가 반대로 간 항목은 |δ|가 커도 살아남은 것이 아니다. 앞 단계에서
    "봇이 높다"였던 것이 "봇이 낮다"가 되었다면 그 항목에 대해 우리가 아는
    것은 아무것도 없다. 다만 판정 칸의 '뒤집힘'은 앞 단계나 09-2 중 한 번이라도
    주목이었던 항목에만 붙인다 — δ가 +0.01에서 −0.02로 간 것도 부호로는
    반전이지만 애초에 아무 방향도 주장한 적이 없어 반전이라 부를 것이 없다.
    """
    out = []
    for k, r in rows:
        b = (baseline or {}).get(k) or {}
        d_old = b.get("델타")
        prior_notable = bool(b.get("주목"))
        d_new = r["델타"] if r["검정가능"] else None

        if d_old is None or d_new is None:
            change = None
            flip = None
            hold = None
            verdict = "검정불가"
        else:
            change = d_new - d_old
            flip = (d_old > 0 > d_new) or (d_old < 0 < d_new)
            hold = abs(d_new) >= DELTA_NOTABLE
            if flip and (prior_notable or r["주목"]):
                verdict = "뒤집힘"
            elif prior_notable:
                verdict = "유지" if hold else "무너짐"
            elif r["주목"]:
                verdict = "신규"
            else:
                verdict = "미주목"

        out.append((k, {
            "앞델타": d_old,
            "델타": d_new,
            "변화량": change,
            "q": r.get("q"),
            "방향": r.get("방향"),
            "앞주목": prior_notable,
            "주목": bool(r.get("주목")),
            "유지": hold,
            "뒤집힘": flip,
            "판정": verdict,
            "봇_유효n": r.get("봇_유효n"),
            "사람_유효n": r.get("사람_유효n"),
            "출현계정수": r.get("출현계정수"),
            "희소": bool(r.get("희소")),
        }))
    return out


def print_crosswalk(cross, base_label, title, limit=None):
    """대조 표를 띄운다. [09-1에서 가져옴] 앞 단계와 09-2를 한 줄에 놓는다."""
    shown = cross if limit is None else cross[:limit]
    if not shown:
        print("\n      띄울 줄이 없습니다.")
        return
    print(f"\n      {title}")
    print(crosswalk_head(base_label))
    for k, c in shown:
        if c["델타"] is None or c["앞델타"] is None:
            reason = "09-2 검정불가" if c["델타"] is None else "앞 단계에 없음"
            print(f"      {k:<12}{'—':>7}{'—':>8}{'—':>8}{'—':>10}  {reason}")
            continue
        mark = "  희소" if c["희소"] else ""
        print(f"      {k:<12}{c['앞델타']:>+7.3f}{c['델타']:>+8.3f}"
              f"{c['변화량']:>+8.3f}{c['q']:>10.4f}  {c['판정']}{mark}")


def mean_abs_change(cross, only_prior_notable=True):
    """
    가족의 평균 |Δδ|. [09-1에서 가져옴]

    only_prior_notable=True 면 앞 단계에서 주목이던 항목만 센다. 결론에 실린
    것이 그 항목들이고, δ가 0 근처였던 항목은 애초에 흔들릴 여지가 없어
    평균을 가족 크기 쪽으로 끌어당기기만 한다.
    """
    vals = []
    for _, c in cross:
        if c["변화량"] is None:
            continue
        if only_prior_notable and not c["앞주목"]:
            continue
        vals.append(abs(c["변화량"]))
    if not vals:
        return None, 0
    return statistics.mean(vals), len(vals)


def family_verdict(cross, label):
    """
    한 가족의 판정을 집계해 찍는다. [09-1의 family_verdict 그대로]

    반환은 JSON에 그대로 담을 요약 사전이다.
    """
    prior = [(k, c) for k, c in cross if c["앞주목"]]
    held = [(k, c) for k, c in prior if c["유지"] and not c["뒤집힘"]]
    fallen = [(k, c) for k, c in prior if c["유지"] is False and not c["뒤집힘"]]
    flipped = [(k, c) for k, c in prior if c["뒤집힘"]]
    flipped_noise = [(k, c) for k, c in cross
                     if c["뒤집힘"] and not c["앞주목"] and not c["주목"]]
    new_notable = [(k, c) for k, c in cross if c["판정"] == "신규"]
    untestable = [(k, c) for k, c in cross if c["델타"] is None]

    mean_prior, n_prior = mean_abs_change(cross, only_prior_notable=True)
    mean_all, n_all_ch = mean_abs_change(cross, only_prior_notable=False)

    print(f"\n      [{label}] 앞 단계 주목 {len(prior)}종에 대한 판정")
    print(f"        |δ| ≥ {DELTA_NOTABLE} 유지               "
          f"{len(held):>4}종")
    print(f"        문턱 아래로 떨어짐 (무너짐)         {len(fallen):>4}종")
    print(f"        방향 뒤집힘                         {len(flipped):>4}종"
          f"{'   ← 결론에서 빼야 한다' if flipped else ''}")
    if flipped_noise:
        print(f"        (참고) 양쪽 다 무주목인 항목의 부호 반전"
              f" {len(flipped_noise):>3}종")
        print("               δ가 0 근처에서 흔들린 것이라 방향을 주장한 적이")
        print("               없다. 위 뒤집힘 수에 넣지 않았다.")
    if new_notable:
        print(f"        09-2에서 새로 문턱을 넘음 (신규)    "
              f"{len(new_notable):>4}종")
        print("               09-2는 진단이라 결론에 올리지 않는다.")
    if untestable:
        print(f"        09-2에서 검정 불가                  "
              f"{len(untestable):>4}종")
    if mean_prior is not None:
        print(f"        평균 |Δδ| (앞 주목 {n_prior}종 한정)      "
              f"{mean_prior:>7.4f}")
    if mean_all is not None:
        print(f"        평균 |Δδ| (가족 전체 {n_all_ch}종)        "
              f"{mean_all:>7.4f}   (참고)")

    return {
        "앞주목수": len(prior),
        "유지": len(held),
        "무너짐": len(fallen),
        "뒤집힘": len(flipped),
        "신규": len(new_notable),
        "검정불가": len(untestable),
        "평균절대변화_앞주목한정": rnd(mean_prior, STAT_DIGITS),
        "평균절대변화_전체": rnd(mean_all, STAT_DIGITS),
        "유지목록": [k for k, _ in held],
        "무너짐목록": [k for k, _ in fallen],
        "뒤집힘목록": [k for k, _ in flipped],
        "무주목_부호반전수": len(flipped_noise),
    }


# ════════════════════════════════════════════════════════════════════════
# [7] 산포 — 옛 산포검정(보관)의 Brown-Forsythe와 쌍거리를 그대로
# ════════════════════════════════════════════════════════════════════════
def iqr_of(values):
    """사분위 범위 Q3 − Q1. [옛 산포검정(보관)에서 가져옴] 값이 둘 미만이면 0.0."""
    if len(values) < 2:
        return 0.0
    q = quartiles(values)
    return q["Q3"] - q["Q1"]


def abs_deviations(values):
    """
    그 무더기의 **자기 중앙값**에서 잰 절대편차. [옛 산포검정(보관)에서 가져옴] Brown-Forsythe의 재료다.

    ■ 왜 그룹별 중앙값인가 ■
    두 무더기를 합친 공통 중앙값을 쓰면, 위치가 다른 무더기는 그것만으로
    편차가 커진다. 그러면 표에는 '산포가 크다'로 찍히지만 실제로 잰 것은
    '위치가 다르다'다. 각 무더기에서 자기 중앙값을 빼면 두 무더기가 같은
    자리로 옮겨진 뒤 흩어짐만 남는다.

    반환된 편차들의 중앙값이 곧 그 무더기의 MAD다.
    """
    med = statistics.median(values)
    return [abs(v - med) for v in values], med


def brown_forsythe(v1, v2):
    """
    두 무더기의 산포를 견준다. 그룹1(=봇) 기준. [옛 산포검정(보관)에서 가져옴]

        1. 각 무더기에서 그 무더기의 중앙값을 뺀 절대편차를 만든다.
        2. 두 절대편차 무더기를 Mann-Whitney U로 견주고 Cliff's δ를 낸다.
        3. δ < 0  →  봇의 절대편차가 작다  =  봇이 더 뭉쳐 있다.

    IQR·MAD·중앙값을 함께 담아 돌려준다. 검정이 "어느 쪽이 넓은가"만
    말한다면 IQR·MAD는 "얼마나 넓은가"를 말한다. 둘 다 있어야 읽힌다.
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
        "델타": res["델타"], "방향": direction_disp(res["델타"]),
        "봇_중앙": m1, "사람_중앙": m2,
        "봇_IQR": iqr1, "사람_IQR": iqr2,
        "봇_MAD": statistics.median(d1), "사람_MAD": statistics.median(d2),
        # 비는 언제나 사람 ÷ 봇이다. 1보다 크면 사람이 넓다 = 봇이 뭉쳐 있다.
        # 봇 IQR이 0이면 나눗셈이 성립하지 않아 None — '무한대'가 아니라
        # '이 자료로는 비를 말할 수 없다'로 읽어야 한다.
        "IQR비": (iqr2 / iqr1) if iqr1 > 0 else None,
        "MAD비": (statistics.median(d2) / statistics.median(d1))
                if statistics.median(d1) > 0 else None,
        "봇_유효n": len(v1), "사람_유효n": len(v2),
    }


def dense_vectors(uids, rates, words):
    """
    계정마다 172차원 사용률 벡터를 만든다. [옛 산포검정(보관)에서 가져옴] 희소 저장을 조밀하게 편다.

    없는 키는 0.0이다 — word_vector()와 같은 규율이고 같은 이유다. 안 쓴
    단어를 빠뜨리면 벡터의 길이가 계정마다 달라져 거리를 잴 수 없다.
    """
    return [[rates[u]["사용률"].get(w, 0.0) for w in words] for u in uids]


def within_group_distances(vecs):
    """
    한 무더기 안의 모든 계정쌍 L1 거리. [옛 산포검정(보관)에서 가져옴] n개면 n(n−1)/2 쌍이다.

        L1(a, b) = Σ_j |a_j − b_j|          (172개 성분의 절대차 합)

    ■ 왜 L1인가 ■
    유클리드(L2)는 큰 성분 하나에 제곱으로 끌려간다. 172종 중 the·of·to
    같은 몇 단어가 사용률의 대부분을 차지하므로, L2를 쓰면 사실상 그 몇
    단어의 거리가 된다. L1은 모든 성분을 같은 무게로 더한다.

    ■ 반환 ■ (모든 쌍 거리 목록, 계정별 거리 목록)

    ■ 속도 ■ 옛 산포검정(보관)은 512계정(130,816쌍)이었지만 09-2는 매칭 표본이 아니라 훨씬
    크다. 사람 무더기가 900계정이면 40만 쌍이고, 172성분을 곱하면 7천만 번의
    뺄셈이다. 몇십 초가 걸릴 수 있어 [7/8]이 미리 규모를 찍고 시간을 잰다.
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
    """다섯 숫자 각각의 사람 ÷ 봇 비. [옛 산포검정(보관)에서 가져옴]"""
    out = {}
    for key in ("최소", "Q1", "중앙", "Q3", "최대"):
        b, h = bot_five.get(key), hum_five.get(key)
        out[key] = (h / b) if (b not in (None, 0) and h is not None) else None
    return out


def pack_disp(r):
    """산포 결과 한 칸을 JSON에 담을 꼴로 바꾼다. [옛 산포검정(보관)의 pack_one에서 가져옴]"""
    if r is None or not r.get("검정가능"):
        return {"검정가능": False, "델타": None, "q": None, "방향": "검정 불가"}
    return {
        "검정가능": True,
        "U": rnd(r["U"], 1), "z": rnd(r["z"], STAT_DIGITS),
        "p": sig(r["p"]), "q": sig(r.get("q", r["p"])),
        "델타": rnd(r["델타"], STAT_DIGITS), "방향": r["방향"],
        "봇_중앙": rnd(r["봇_중앙"], RATE_DIGITS),
        "사람_중앙": rnd(r["사람_중앙"], RATE_DIGITS),
        "봇_IQR": rnd(r["봇_IQR"], RATE_DIGITS),
        "사람_IQR": rnd(r["사람_IQR"], RATE_DIGITS),
        "봇_MAD": rnd(r["봇_MAD"], RATE_DIGITS),
        "사람_MAD": rnd(r["사람_MAD"], RATE_DIGITS),
        "IQR비": rnd(r["IQR비"], STAT_DIGITS),
        "MAD비": rnd(r["MAD비"], STAT_DIGITS),
        "봇_유효n": r["봇_유효n"], "사람_유효n": r["사람_유효n"],
    }


def pack_cross(cross, base_label):
    """
    한 가족의 대조 결과를 JSON에 담을 꼴로 바꾼다. [09-1에서 가져옴] |δ| 내림차순 유지.

    앞 단계의 δ를 같은 줄에 실어 둔다. 09-2를 읽는 사람이 가장 먼저 물을 것이
    "전체 글에서 컸던 항목이 댓글에서도 큰가"이기 때문이다.
    """
    return {
        k: {
            f"{base_label}델타": c["앞델타"],
            f"{base_label}주목": c["앞주목"],
            "델타": rnd(c["델타"], STAT_DIGITS),
            "변화량": rnd(c["변화량"], STAT_DIGITS),
            "q": sig(c["q"]),
            "방향": c["방향"],
            "주목": c["주목"],
            "유지": c["유지"],
            "뒤집힘": c["뒤집힘"],
            "판정": c["판정"],
            "봇_유효n": c["봇_유효n"],
            "사람_유효n": c["사람_유효n"],
            "출현계정수": c["출현계정수"],
            "희소": c["희소"],
        }
        for k, c in cross
    }


# ════════════════════════════════════════════════════════════════════════
# [사슬] 다섯 파일이 같은 04에서 나왔는가
# ════════════════════════════════════════════════════════════════════════
def chain_fingerprints(conf04, conf05, conf06, conf07, conf09):
    """
    04의 기능어 지문을 승계하고, 05·06·07·옛 산포검정(보관)이 적어 둔 값과 대조한다.
    [옛 산포검정(보관)의 chain_fingerprints에서 09-1 자리를 옛 산포검정(보관)으로 바꿔 그대로 씀]

    이 해시는 09-2가 쓰는 수치의 출처가 아니라 **04 실행분의 신분증**이다.
    09-2에서 이 확인이 갖는 뜻은 앞 단계와 조금 다르다. 09-2는 04의 카운트를
    읽지 않고 **새로 파싱한다**. 그런데도 04의 지문을 보는 이유는, 09-2가
    대조할 기준선(06의 δ, 07의 δ, 옛 산포검정(보관)의 산포 δ)이 전부 04에서 나온 값이기
    때문이다. 기준선들이 서로 다른 04에서 나왔다면 09-2는 어긋난 자들 사이에서
    비교를 하게 되고, 화면에는 아무 이상도 안 찍힌다. 그래서 중단이다.

    저장 자리가 파일마다 다르므로 각각 다른 경로로 꺼낸다.
        05 : 설정 → 04승계 → 기능어_해시
        06 : 설정 → 05승계 → 04승계 → 기능어_해시
        07 : 설정 → 04승계 → 기능어_해시
        옛 산포검정(보관) : 설정 → 사슬확인 → 기능어_해시

    반환: (기록용 사전, 모두 일치하는가)
    """
    h04 = conf04.get("기능어_해시")
    h05 = (conf05.get("04승계") or {}).get("기능어_해시")
    h06 = ((conf06.get("05승계") or {}).get("04승계") or {}).get("기능어_해시")
    h07 = (conf07.get("04승계") or {}).get("기능어_해시")
    chain09 = conf09.get("사슬확인") or {}
    h09 = chain09.get("기능어_해시")
    seen = [h04, h05, h06, h07, h09]
    agree = all(h is not None for h in seen) and len(set(seen)) == 1
    record = {
        "기능어_해시": h04,
        "기능어_개수": conf04.get("기능어_개수"),
        "04_실행일": conf04.get("실행일"),
        "05_실행일": conf05.get("실행일"),
        "06_실행일": conf06.get("실행일"),
        "07_실행일": conf07.get("실행일"),
        "09_실행일": conf09.get("실행일"),
        "05가_적어둔_해시": h05,
        "06이_적어둔_해시": h06,
        "07이_적어둔_해시": h07,
        "09가_적어둔_해시": h09,
        "09의_자체판정": chain09.get("일치"),
        "일치": agree,
    }
    return record, agree


# ════════════════════════════════════════════════════════════════════════
# [8] 사전 예측 대조
# ════════════════════════════════════════════════════════════════════════
def print_prediction_header():
    """[8/8]의 머리말. 사전등록이 무엇을 막는지 매번 다시 적는다. [옛 산포검정(보관)에서 가져옴]"""
    print("\n      보관된 07-12 사전선언의 10항(현 09-2) 예측 다섯을 실제 결과와 대조한다.")
    print("      아래 예측은 09-2를 돌리기 전에 문서에 확정된 것이다. 빗나간 예측도")
    print("      지우거나 고치지 않고 그대로 싣는다 — 06에서 라벨을 연 이상")
    print("      이 파이프라인에 남은 보호막은 사전등록뿐이다.")


def print_pred_meta(pred):
    """예측 하나의 서술·판정규칙·근거를 미리 끊어 둔 줄 그대로 찍는다. [09-1·옛 산포검정(보관)에서 가져옴]"""
    print()
    print(f"      예측 {pred['번호']}  {pred['서술']}")
    print(f"        [{pred['축']}]")
    print("        판정 규칙으로 적어 둔 것:")
    for ln in pred["판정규칙"]:
        print(f"          {ln}")
    print("        근거로 적어 둔 것:")
    for ln in pred["근거"]:
        print(f"          {ln}")


def pred1_items(base_feats):
    """
    예측 1이 판정할 항목 목록을 만든다. (가족, 키) 쌍의 목록.

    Gender 계열은 07에서 주목이었던 그 축의 자질 전부다. 자료로 정해지는
    값이라 여기서 고를 여지가 없다 — 상수에 이름을 박아 두면 07이 다시 돌아
    주목 목록이 달라졌을 때 옛 이름을 계속 보게 된다.
    """
    items = [("F", w) for w in PRED1_WORDS]
    items += [("M", k) for k in PRED1_FEATS]
    gender = sorted(k for k, v in (base_feats or {}).items()
                    if axis_of(k) == PRED1_AXIS and v.get("주목"))
    items += [("M", k) for k in gender]
    return items, gender


def check_pred1(f_cross, m_cross, base_feats):
    """
    예측 1 — 머리가 댓글 한정에서도 |δ| ≥ 0.147 을 유지하는가.

    지정 항목이 **전부** 유지여야 적중이다. 하나라도 무너지거나 뒤집히면
    빗나감으로 적는다. 판정은 crosswalk이 이미 낸 칸을 읽기만 한다 — 같은
    판정을 두 곳에서 계산하면 언젠가 둘이 어긋난다.
    """
    fmap, mmap = dict(f_cross), dict(m_cross)
    items, gender = pred1_items(base_feats)
    rows = []
    for family, key in items:
        c = (fmap if family == "F" else mmap).get(key)
        if c is None or c["델타"] is None:
            rows.append({"가족": family, "항목": key, "앞델타": None,
                         "델타": None, "판정": "검정불가"})
            continue
        rows.append({"가족": family, "항목": key,
                     "앞델타": c["앞델타"], "델타": rnd(c["델타"], STAT_DIGITS),
                     "변화량": rnd(c["변화량"], STAT_DIGITS),
                     "q": sig(c["q"]), "판정": c["판정"]})
    hit = bool(rows) and all(r["판정"] == "유지" for r in rows)
    return {
        "지정항목수": len(rows),
        "Gender계열": gender,
        "축단위_개수": len(PRED1_WORDS) + len(PRED1_FEATS)
                   + (1 if gender else 0),
        "항목": rows,
        "유지수": sum(1 for r in rows if r["판정"] == "유지"),
        "무너짐수": sum(1 for r in rows if r["판정"] == "무너짐"),
        "뒤집힘수": sum(1 for r in rows if r["판정"] == "뒤집힘"),
        "판정": "적중" if hit else "빗나감",
    }


def check_pred2(total10, loc06):
    """
    예측 2 — 총사용률 위치 δ가 더 음수 쪽으로 갔는가.

    06의 δ는 06_비교결과.json 에서 읽어 온다. 하드코딩하면 06을 다시 돌려
    값이 바뀌어도 이 판정은 옛 숫자를 계속 쓴다(옛 산포검정(보관)의 예측 4와 같은 규율).
    """
    d06 = (loc06 or {}).get("델타")
    if total10 is None or d06 is None:
        return {"판정": "판정불가", "사유": "06의 총사용률 δ 또는 09-2의 값이 없음"}
    d10 = total10["델타"]
    return {
        "06델타": d06,
        "06출처": "06_비교결과.json → 총사용률_비교 → 델타 (읽어 옴)",
        "10델타": rnd(d10, STAT_DIGITS),
        "이동": rnd(d10 - d06, STAT_DIGITS),
        "10q": sig(total10["p"]),
        "q비고": "단독 검정이라 q = p (m = 1 에서 BH는 항등).",
        "판정": "적중" if d10 < d06 else "빗나감",
    }


def check_pred3(cut, rates10, rates05, survivors):
    """
    예측 3 — 총사용률 분포의 왼쪽 꼬리가 짧아졌는가.

    ■ 왜 '같은 계정들' 안에서 세나 ■
    09-2에서 계정이 1,869개에서 줄었으므로 하한 미만 계정 수를 그냥 견주면
    '꼬리가 짧아진 것'과 '표본이 작아진 것'이 섞인다. 살아남은 계정만 골라
    그들의 05 값과 09-2 값에서 각각 세면 그 섞임이 없어진다 — 같은 계정을
    두 번 재어 견주는 것이므로 표본 크기가 같다.

    05 전체 1,869계정 기준 수도 함께 담는다. 사전선언이 "172계정"이라고
    적은 그 숫자와 대조할 수 있어야 하기 때문이다.
    """
    if cut is None:
        return {"판정": "판정불가", "사유": "05의 이상치 하한이 없음"}
    all05 = sum(1 for u, r in rates05.items() if r["총사용률"] < cut)
    same05 = sum(1 for u in survivors
                 if u in rates05 and rates05[u]["총사용률"] < cut)
    same10 = sum(1 for u in survivors if rates10[u]["총사용률"] < cut)
    n = len(survivors)
    return {
        "하한": cut,
        "하한_출처": "05_사용률검수.json → 검수요약 → 이상치_하한 (읽어 옴)",
        "05전체_미만계정": all05,
        "05전체_계정수": len(rates05),
        "생존계정수": n,
        "생존계정_05기준_미만": same05,
        "생존계정_10기준_미만": same10,
        "생존계정_05기준_비율": rnd(same05 / n, 4) if n else None,
        "생존계정_10기준_비율": rnd(same10 / n, 4) if n else None,
        "줄어든_계정수": same05 - same10,
        "판정": "적중" if same10 < same05 else "빗나감",
    }


def check_pred4(total_disp, acct_test, base09_total, base09_dist):
    """
    예측 4 — 옛 산포검정(보관)이 낸 동질성 신호가 게시물 유형 통제 후에도 유지되는가.

    (가) 총사용률 Brown-Forsythe 에서 δ < 0 이고 q ≤ 0.05
    (나) 계정별 거리 요약 검정에서 δ < 0 이고 p ≤ 0.05
    둘 다면 적중, 하나만이면 부분 적중, 둘 다 아니면 빗나감.

    ■ 크기 비교를 판정에 넣지 않는 이유 ■
    옛 산포검정(보관)의 계정별 거리 δ(−0.9064)는 **매칭 표본**에서 나온 값이고 09-2는 매칭
    표본이 아니다. 그리고 그룹 내 거리는 무더기 크기에 따라 분포가 달라진다.
    두 값을 크기로 견주면 표본이 다른 것을 비교하게 되므로 방향과 유의성만
    판정에 쓰고, 크기는 나란히 찍어 사람이 읽게 한다.
    """
    a_ok = (total_disp is not None and total_disp["델타"] < 0
            and total_disp["p"] <= Q_ALPHA)
    b_ok = (acct_test is not None and acct_test["델타"] < 0
            and acct_test["p"] <= Q_ALPHA)
    if a_ok and b_ok:
        verdict = "적중"
    elif a_ok or b_ok:
        verdict = "부분 적중"
    else:
        verdict = "빗나감"
    return {
        "총사용률_산포_델타": rnd(total_disp["델타"], STAT_DIGITS)
                       if total_disp else None,
        "총사용률_산포_q": sig(total_disp["p"]) if total_disp else None,
        "총사용률_IQR비": rnd(total_disp["IQR비"], STAT_DIGITS)
                     if total_disp else None,
        "09_총사용률_산포_델타_전체표본": base09_total.get("델타"),
        "09_총사용률_IQR비_전체표본": base09_total.get("IQR비"),
        "계정별거리_델타": rnd(acct_test["델타"], STAT_DIGITS)
                    if acct_test else None,
        "계정별거리_q": sig(acct_test["p"]) if acct_test else None,
        "09_계정별거리_델타_매칭표본": base09_dist.get("델타"),
        "가_총사용률": a_ok,
        "나_계정별거리": b_ok,
        "표본_비고": "09-2는 매칭 표본이 아니다. 총사용률 산포는 옛 산포검정(보관)의 전체 표본 "
                 "값과 견주는 것이 맞고, 계정별 거리는 옛 산포검정(보관)이 매칭 표본에서만 "
                 "냈으므로 짝이 되는 전체 표본 값이 없다. 방향과 유의성만 "
                 "판정에 쓰고 크기는 참고로 싣는다.",
        "판정": verdict,
    }


def check_pred5(drop):
    """
    예측 5 — 탈락 계정이 사람 쪽에 편중되는가.

    편중 배수 = 탈락 무더기의 봇 비율 ÷ 01 적격 전체의 봇 비율.
    1.0 미만이면 사람 쪽으로 몰려 있다는 뜻이다.
    """
    if not drop["탈락계정수"]:
        return {"판정": "판정불가", "사유": "탈락한 계정이 없음"}
    ratio = drop["편중배수"]
    return {
        "탈락계정수": drop["탈락계정수"],
        "탈락_봇": drop["탈락_봇"],
        "탈락_사람": drop["탈락_사람"],
        "탈락_봇비율": rnd(drop["탈락_봇비율"], 4),
        "전체_봇비율": rnd(drop["전체_봇비율"], 4),
        "편중배수": rnd(ratio, 4),
        "봇에서_탈락한_비율": rnd(drop["봇에서_탈락한_비율"], 4),
        "사람에서_탈락한_비율": rnd(drop["사람에서_탈락한_비율"], 4),
        "판정": "적중" if (ratio is not None and ratio < 1.0) else "빗나감",
    }


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 74)
    print("게시물 유형 통제 재측정  (09-2 — 제목을 빼고도 06·07의 신호가 남는가)")
    print("=" * 74)

    # ── 이미 끝난 작업인가 ──────────────────────────────────────
    # [04에서 가져옴] 30분짜리 측정 결과를 실수로 날리는 일은 생각보다 자주
    # 일어난다. 최종본이 있으면 손대지 않는다.
    if os.path.exists(OUT_JSON):
        prev = json.load(open(OUT_JSON, encoding="utf-8"))
        print("최종 산출물이 이미 있습니다. 아무것도 하지 않고 끝냅니다.")
        print(f"  파일   {OUT_JSON}")
        print(f"  크기   {os.path.getsize(OUT_JSON):,} bytes")
        print(f"  실행일 {prev.get('설정', {}).get('실행일', '?')}")
        print(f"  계정   {len(prev.get('계정', {})):,}개")
        print()
        print("  다시 측정하려면 이 파일을 다른 이름으로 옮기거나 지운 뒤 실행하십시오.")
        return

    # ══════════════════════════════════════════════════════════════
    # [1/8] 입력 적재와 장르 집계
    # ══════════════════════════════════════════════════════════════
    print("\n[1/8] 입력 적재와 장르 집계")
    need = [(POSTS_JSON, "BotSim 원본"),
            (ACCOUNTS_JSON, "01_botsim_적격검열.py"),
            (FUNCWORDS_JSON, "02_기능어목록_생성.py"),
            (MEASURE_JSON, "04_기능어측정.py"),
            (RATES_JSON, "05_사용률검수.py"),
            (COMPARE_JSON, "06_봇사람비교.py"),
            (FEATURE_JSON, "07_형태자질비교.py"),
            (DISPERSION_JSON, "# 07-12 실행분 보관 (미학습)/09_산포검정.py")]
    missing_files = [(p, s) for p, s in need if not os.path.exists(p)]
    if missing_files:
        for p, s in missing_files:
            print(f"      {p} 이(가) 없습니다.  ({s})")
        print()
        print("      09-2는 원본과 앞 단계 산출물 위에서만 성립합니다. 원본이 없으면")
        print("      제목과 댓글을 가를 수 없고, 06·07·옛 산포검정(보관)이 없으면 무엇과 견줄지가")
        print("      없습니다. 아무것도 하지 않고 끝냅니다.")
        return

    try:
        import langid  # noqa: F401  — 있는지만 확인한다
    except ImportError:
        print("      langid 를 불러올 수 없습니다.")
        print("      01이 계정 단위 언어 판정에 쓴 그 도구이고, 09-2는 01과 같은")
        print("      규칙을 써야 하므로 대체할 수 없습니다.  pip install langid")
        return

    d01 = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    eligible = set(d01["계정"])
    labels = dict(d01.get("라벨") or {})
    del d01      # 원문("계정")·언어판정·깔때기는 여기서 버린다. 09-2가 쓸 일이 없다.

    funcwords = json.load(open(FUNCWORDS_JSON, encoding="utf-8"))["기능어"]
    # 02 목록에도 토큰과 같은 정규화를 적용한다(04와 같음). 굽은 변종이 곧은
    # 항목과 합쳐져 174종이 172종이 된다.
    funcwords = sorted({normalize_apostrophe(w) for w in funcwords})
    funcword_set = set(funcwords)

    d04 = json.load(open(MEASURE_JSON, encoding="utf-8"))
    conf04 = d04["설정"]
    scale04 = conf04.get("처리규모", {})
    del d04      # 04의 계정별 카운트는 쓰지 않는다 — 09-2는 새로 파싱한다.

    d05 = json.load(open(RATES_JSON, encoding="utf-8"))
    rates05 = d05["계정"]
    review05 = d05["검수요약"]
    conf05 = d05["설정"]
    d06 = json.load(open(COMPARE_JSON, encoding="utf-8"))
    d07 = json.load(open(FEATURE_JSON, encoding="utf-8"))
    d09 = json.load(open(DISPERSION_JSON, encoding="utf-8"))

    base_words = d06["단어별"]
    base_feats = d07["형태자질"]
    base_upos = d07["UPOS"]
    base_axes = d07.get("축분류") or {}
    loc06_total = d06.get("총사용률_비교") or {}
    disp09_total = (d09.get("총사용률_산포") or {}).get("전체표본") or {}
    disp09_dist = ((d09.get("쌍거리") or {}).get("계정별요약검정")) or {}

    print(f"      01 적격     계정 {len(eligible):,}개 · 라벨 {len(labels):,}개")
    print(f"      02 기능어   {len(funcwords)}종 (아포스트로피 정규화 후)")
    print(f"      04 기준     계정 {scale04.get('계정수', '?'):,}개 · "
          f"문서 {scale04.get('문서수', 0):,}건 "
          f"(실행일 {conf04.get('실행일', '?')})")
    print(f"      05 사용률   계정 {len(rates05):,}개 · "
          f"이상치 하한 {review05.get('이상치_하한')}")
    print(f"      06 기준선   단어 {len(base_words):,}종 · "
          f"총사용률 위치 δ = {loc06_total.get('델타')}")
    print(f"      07 기준선   형태자질 {len(base_feats):,}종 · "
          f"UPOS {len(base_upos):,}종 · 축 {len(base_axes)}개")
    print(f"      옛 산포검정(보관) 기준선  총사용률 산포 δ = {disp09_total.get('델타')} (전체표본) · "
          f"계정별 거리 δ = {disp09_dist.get('델타')} (매칭표본)")

    if len(eligible) != EXPECT_ELIGIBLE:
        print(f"\n      ※ 01 적격 계정이 {EXPECT_ELIGIBLE:,}개가 아닙니다. 01이 다시")
        print("        돌았을 수 있습니다. 계산은 계속하지만 보관된 07-12 사전선언의 10항(현 09-2) 실측표와")
        print("        대조가 어긋날 것입니다(아래에서 확인됩니다).")

    # ── 사슬 무결성 ─────────────────────────────────────────────
    chain, chain_ok = chain_fingerprints(conf04, conf05, d06["설정"],
                                         d07["설정"], d09["설정"])
    line("사슬 무결성 — 기준선들이 같은 04에서 나왔는가")
    print("  09-2는 04의 카운트를 읽지 않는다. 새로 파싱한다. 그런데도 04의 지문을")
    print("  보는 이유는, 09-2가 대조할 기준선 셋(06의 δ · 07의 δ · 옛 산포검정(보관)의 산포 δ)이")
    print("  전부 04에서 나온 값이기 때문이다. 기준선들이 서로 다른 04에서 나왔다면")
    print("  09-2는 어긋난 자들 사이에서 비교를 하게 되고, 화면에는 아무 이상도")
    print("  안 찍힌다. 그래서 어긋나면 경고가 아니라 중단이다.")
    print()
    print(f"  04 기능어 해시            {chain['기능어_해시']}  "
          f"({chain['기능어_개수']}종)")
    print(f"  05가 적어 둔 해시         {chain['05가_적어둔_해시']}")
    print(f"  06이 적어 둔 해시         {chain['06이_적어둔_해시']}")
    print(f"  07이 적어 둔 해시         {chain['07이_적어둔_해시']}")
    print(f"  옛 산포검정(보관)이 적어 둔 해시 {chain['09가_적어둔_해시']}")
    if not chain_ok:
        print()
        print("■ 중단 — 사슬이 끊어졌습니다.")
        print("  다섯 파일이 같은 04 실행분에서 나오지 않았습니다.")
        print("  04부터 다시 돌려 05·06·07·옛 산포검정(보관)을 새로 만든 뒤 09-2를 실행하십시오.")
        return
    print("  다섯 값이 같다. 같은 04에서 나온 파일들이다.")
    print()
    print(f"  ※ 09-2가 지금 만드는 기능어 목록의 해시는 "
          f"{hashlib.sha256(chr(10).join(funcwords).encode('utf-8')).hexdigest()[:16]}")
    print("    이다. 위 04 해시와 같아야 09-2의 카운트와 04의 카운트를 같은 표에")
    print("    놓을 수 있다(같지 않으면 아래 지문 대조에서 다시 걸린다).")

    # ── 라벨 규율 ───────────────────────────────────────────────
    line("라벨 — 09-2는 라벨을 아는 상태에서 수행된다")
    print("  01~05를 지켜 준 봉인은 06에서 이미 열렸다. 09-2에는 그 보호막이 없다.")
    print("  봉인 대신 사전등록이 그 자리를 대신한다(보관된 07-12 사전선언의 결정 0-1).")
    print()
    print("  09-2가 라벨을 쓰는 곳은 둘이다 — 아래 장르 집계와, [5/8] 이후의 비교다.")
    print("  코퍼스를 짓는 [2/8]은 라벨을 보지 않는다. 01이 그랬듯 적격 판정에")
    print("  라벨이 끼어들면 '봇이 잘 남는 쪽으로 필터를 골랐다'를 방어할 수 없다.")
    print("  깔때기를 라벨별로 세는 것은 판정이 끝난 뒤의 집계일 뿐이다.")
    print()
    n_bot_all = sum(1 for u in eligible if labels.get(u) == GROUP1)
    n_hum_all = sum(1 for u in eligible if labels.get(u) == GROUP2)
    print(f"  01 적격 계정   봇 {n_bot_all:,} · 사람 {n_hum_all:,}")

    # ── 장르 집계 ───────────────────────────────────────────────
    print("\n      원본 적재 중 (제목과 댓글을 갈라 담는다)...", end=" ", flush=True)
    t0 = time.time()
    raw = load_raw_split(eligible)
    print(f"{time.time() - t0:.1f}초  · 계정 {len(raw):,}개")
    if len(raw) != len(eligible):
        print(f"      ※ 01 적격 {len(eligible):,}계정 중 {len(raw):,}개만 원본에서")
        print("        찾았습니다. 01과 원본이 어긋난 것이므로 확인이 필요합니다.")

    census, title_ratio, title_only, no_label = genre_census(raw, labels)
    print_genre_table(census)
    if no_label:
        print(f"\n        ※ 라벨이 bot/human이 아닌 계정 {len(no_label):,}개는 집계에서")
        print("          빠졌습니다. 01의 적격 계정에는 전원 라벨이 있어야 합니다.")

    genre_mismatch = compare_to_declared(census, title_only)
    print("\n      ── 보관된 07-12 사전선언의 10항(현 09-2) 실측표와 대조 ──")
    print("      (세는 기준: 적격 계정의 원본 항목 중 공백을 걷어 내고도 비어")
    print("       있지 않은 것 전부. 01의 20자 필터도 200건 상한도 걸지 않는다.)")
    if not genre_mismatch:
        print("      일치한다. 보관된 07-12 사전선언의 10항(현 09-2)이 전제로 삼은 장르 구성이 재현되었다.")
        print("      → '사람 쪽에 제목이 5.0%p 더 많고 제목만 쓰는 계정 39개가")
        print("         전원 사람'이라는 09-2의 출발점은 이 스크립트가 다시 센")
        print("         숫자로도 성립한다.")
    else:
        print(f"      ■ 어긋나는 칸이 {len(genre_mismatch)}개 있습니다.")
        for msg in genre_mismatch[:12]:
            print(f"        {msg}")
        if len(genre_mismatch) > 12:
            print(f"        … 이 밖에 {len(genre_mismatch) - 12}건")
        print("      계산은 계속합니다 — 09-2는 사전선언의 표가 아니라 방금 다시 센")
        print("      값으로 계산하기 때문입니다. 다만 보관된 07-12 사전선언의 10항(현 09-2) 전제 문장이")
        print("      흔들렸다는 뜻이므로, 결과를 쓰기 전에 어느 쪽이 맞는지")
        print("      확인하고 사전선언의 「변경 이력」에 적으십시오.")

    # ── 계정 수준 장르 변수 ─────────────────────────────────────
    line("계정 수준 장르 변수 — 장르 구성비 자체가 라벨과 얼마나 상관되는가")
    print("  보관된 07-12 사전선언의 10-3항(현 09-2)이 제목 한정 분석을 금지하는 대신 요구한 것이다.")
    print("  계정마다 '쓴 글 중 제목의 비율'을 하나의 수로 만들고, 그 수가 봇과")
    print("  사람에서 얼마나 다른지를 06과 같은 검정으로 잰다. 이 δ가 크면")
    print("  06·07이 잡은 문체 차이의 일부가 장르 구성비 차이일 수 있다는 뜻이고,")
    print("  0에 가까우면 장르 혼합비는 라벨과 무관하다는 뜻이다.")

    tr_bot = [title_ratio[u] for u in sorted(title_ratio)
              if labels.get(u) == GROUP1 and title_ratio[u] is not None]
    tr_hum = [title_ratio[u] for u in sorted(title_ratio)
              if labels.get(u) == GROUP2 and title_ratio[u] is not None]
    tr_five_bot, tr_five_hum = five_number(tr_bot), five_number(tr_hum)
    print("\n      계정별 제목 비율의 다섯 숫자 (09-1·옛 산포검정(보관)이 쓰는 그 다섯이다)")
    print("        무더기     계정      최소       Q1      중앙       Q3      최대")
    for name, s in (("봇      ", tr_five_bot), ("사람    ", tr_five_hum)):
        if s["n"] == 0:
            print(f"        {name}{0:>7,}   (비어 있음)")
            continue
        print(f"        {name}{s['n']:>7,}{s['최소']:>10.3f}{s['Q1']:>9.3f}"
              f"{s['중앙']:>10.3f}{s['Q3']:>9.3f}{s['최대']:>10.3f}")

    tr_test = mann_whitney(tr_bot, tr_hum) if (tr_bot and tr_hum) else None
    if tr_test is not None:
        tr_test["방향"] = direction_of(tr_test["델타"])
        print(f"\n        U = {tr_test['U']:,.1f}   z = {tr_test['z']:.3f}   "
              f"양측 p = {tr_test['p']:.3g}")
        print(f"        δ = {tr_test['델타']:+.4f}  →  {tr_test['방향']}"
              f"   (여기서 '높음'은 제목 비율이 높다는 뜻이다)")
        print("        (단독 검정이라 q = p 로 읽는다. m = 1 에서 BH는 항등.)")
        if abs(tr_test["델타"]) >= DELTA_NOTABLE:
            print(f"\n        |δ| 가 주목 문턱({DELTA_NOTABLE})을 넘는다. 장르 구성비가")
            print("        라벨과 상관된다는 뜻이므로, 06·07의 δ에는 문체 몫과")
            print("        장르 몫이 섞여 있을 수 있다. [6/8]의 대조가 그 섞임을")
            print("        푸는 자리다.")
        else:
            print(f"\n        |δ| 가 주목 문턱({DELTA_NOTABLE})에 못 미친다. 장르 구성비")
            print("        자체는 라벨과 크게 상관되지 않는다는 뜻이다. 그래도")
            print("        제목만 쓰는 계정이 한쪽에만 39개 있다는 사실은 남는다 —")
            print("        평균적 구성비가 비슷해도 꼬리는 한쪽에 있을 수 있다.")

    # ══════════════════════════════════════════════════════════════
    # [2/8] 댓글 한정 코퍼스 구축
    # ══════════════════════════════════════════════════════════════
    print("\n[2/8] 댓글 한정 코퍼스 구축 (01의 규칙 그대로 · 입력에서 posts 제외)")
    print("      01의 필터를 한 글자도 바꾸지 않는다. 바꾸면 06·07과 09-2의 차이에")
    print("      '장르를 뺀 몫'과 '필터를 바꾼 몫'이 섞이고, 그 둘은 결과만 보고는")
    print("      절대 갈라지지 않는다. 통제 실험에서 한 번에 하나만 바꾸는 것과")
    print("      같은 이야기다.")
    print(f"      기준: {MIN_CHARS}자 이상 · 자기폭로 문장 절제 · 최근 {MAX_DOCS}건 · "
          f"{MIN_DOCS}건 이상 · langid {LANG_TARGET}")
    print()

    corpus, funnel, lang_info = build_comment_corpus(raw, labels)
    del raw      # 원본은 여기까지만 쓴다. 23MB를 이고 30분을 돌 이유가 없다.
    print_funnel(funnel, labels, len(eligible))

    if not corpus:
        print("\n■ 중단 — 댓글 한정으로 남은 계정이 없습니다.")
        return

    drop = dropped_label_split(eligible, corpus, labels)
    print("\n      탈락 계정의 라벨 분포 (예측 5의 판정 자료)")
    print(f"        탈락 {drop['탈락계정수']:,}계정 = "
          f"봇 {drop['탈락_봇']:,} + 사람 {drop['탈락_사람']:,}")
    if drop["탈락_봇비율"] is not None:
        print(f"        탈락 무더기의 봇 비율 {drop['탈락_봇비율']:.1%} · "
              f"01 적격 전체 {drop['전체_봇비율']:.1%}")
        print(f"        편중 배수 {drop['편중배수']:.2f}배   "
              "(1.0 = 라벨과 무관 · 1.0 미만 = 사람 쪽 편중)")
        print(f"        봇의 {drop['봇에서_탈락한_비율']:.1%}가 탈락 · "
              f"사람의 {drop['사람에서_탈락한_비율']:.1%}가 탈락")
    print("\n        ※ 탈락 계정은 기록만 하고 06·07의 결과를 수정하지 않는다")
    print("          (보관된 07-12 사전선언의 10-5항(현 09-2)). 09-2는 진단이지 대체가 아니다.")

    # ══════════════════════════════════════════════════════════════
    # [3/8] 자가검증
    # ══════════════════════════════════════════════════════════════
    print("\n[3/8] 자가검증 — 검정 기계와 토큰화를 고정 예제로 건다")
    nlp = build_pipeline()
    if not hasattr(nlp, "bulk_process"):
        print()
        print("■ 중단 — 이 stanza 버전에는 bulk_process가 없습니다.")
        print("  04는 stanza 1.14.0에서 이 API로 25 ms/문서를 냈습니다.")
        print("  대안: measure_account의 nlp.bulk_process(docs) 자리를")
        print("        nlp([stanza.Document([], text=d) for d in docs]) 로 바꾸면")
        print("        같은 효과를 냅니다(문서 목록을 한 번에 넘기는 방식).")
        return
    if not self_check(nlp, funcword_set):
        return

    # ══════════════════════════════════════════════════════════════
    # [4/8] 파싱과 카운트 — 여기가 30분이다
    # ══════════════════════════════════════════════════════════════
    print("\n[4/8] 파싱과 카운트 (04와 같은 파이프라인 · bulk_process 계정 단위)")
    fp = input_fingerprint(corpus, funcwords)
    print(f"      계정 {fp['계정수']:,}개 · 문서 {fp['문서수']:,}건")
    print(f"      04는 계정 {scale04.get('계정수', 0):,}개 · "
          f"문서 {scale04.get('문서수', 0):,}건이었다 — "
          f"문서 기준 {fp['문서수'] / max(scale04.get('문서수', 1), 1):.0%}")
    print()

    got = run_measurement(nlp, corpus, funcword_set, fp)
    if got is None:
        return
    measures, run_sec, total_sec = got
    del nlp      # 파싱이 끝났다. 모델을 이고 있을 이유가 없다.

    scale10 = {
        "계정수": len(measures),
        "문서수": sum(a["문서수"] for a in measures.values()),
        "문장수": sum(a["문장수"] for a in measures.values()),
        "토큰수": sum(a["토큰수"] for a in measures.values()),
        "토큰수_구두점제외": sum(a["토큰수_구두점제외"] for a in measures.values()),
    }
    print(f"\n      재파싱 규모   문서 {scale10['문서수']:,}건 · "
          f"문장 {scale10['문장수']:,}개 · 토큰 {scale10['토큰수']:,}개")
    print(f"      04 대비        토큰 {scale10['토큰수'] / max(scale04.get('토큰수', 1), 1):.0%} · "
          f"총 소요 {fmt_dur(total_sec)} (04는 {REF_04_MINUTES}분)")

    # ══════════════════════════════════════════════════════════════
    # [5/8] 비율과 비교
    # ══════════════════════════════════════════════════════════════
    print("\n[5/8] 비율과 비교 (05의 분모 규칙 · 07의 축 내부 비율 · 06과 같은 검정)")

    rates10, undefined = compute_rates(measures)
    if undefined:
        print(f"      ※ 분모가 0인 계정 {len(undefined)}개는 사용률을 정의할 수 없어")
        print("        통계에서 빠집니다(분석적 제외가 아니라 나눗셈 불성립).")

    bot_ids = [u for u in sorted(rates10) if labels.get(u) == GROUP1]
    hum_ids = [u for u in sorted(rates10) if labels.get(u) == GROUP2]
    n_all = len(bot_ids) + len(hum_ids)
    sparse_cut = int(n_all * SPARSE_FRAC)
    print(f"      비교 대상   봇 {len(bot_ids):,} · 사람 {len(hum_ids):,}  "
          f"(합 {n_all:,})")
    if not bot_ids or not hum_ids:
        print("\n■ 중단 — 한쪽 무더기가 비어 있어 비교가 성립하지 않습니다.")
        return

    # ── 총사용률 (가족 밖 단독 검정) ────────────────────────────
    tot_bot = [rates10[u]["총사용률"] for u in bot_ids]
    tot_hum = [rates10[u]["총사용률"] for u in hum_ids]
    total10 = mann_whitney(tot_bot, tot_hum)
    total10["방향"] = direction_of(total10["델타"])
    q_bot, q_hum = quartiles(tot_bot), quartiles(tot_hum)

    print("\n      ── 총 기능어 사용률 (1건 — BH 가족 밖 단독 검정) ──")
    print(" " * 17 + "Q1" + " " * 6 + "중앙" + " " * 8 + "Q3")
    print(f"      봇    {q_bot['Q1']:>7.2%}   {q_bot['중앙']:>7.2%}   "
          f"{q_bot['Q3']:>7.2%}   (n={len(tot_bot):,})")
    print(f"      사람  {q_hum['Q1']:>7.2%}   {q_hum['중앙']:>7.2%}   "
          f"{q_hum['Q3']:>7.2%}   (n={len(tot_hum):,})")
    print(f"\n      U = {total10['U']:,.1f}   z = {total10['z']:.3f}   "
          f"양측 p = {total10['p']:.3g}")
    print(f"      δ = {total10['델타']:+.4f}  →  {total10['방향']}"
          f"      (06은 {loc06_total.get('델타')})")

    # ── F 블록 ──────────────────────────────────────────────────
    # 비교 대상 단어는 05의 희소성표 순서를 그대로 쓴다(06과 같은 목록이어야
    # 항목이 줄 단위로 맞는다). 댓글 한정에서 한 번도 안 나온 단어도 그대로
    # 둔다 — word_vector가 0.0으로 채우므로 검정은 성립하고, 목록을 줄이면
    # 06과 견줄 항목이 사라진다.
    words = sorted(review05.get("희소성표", {}))
    if len(words) != EXPECT_WORDS:
        print(f"\n      ※ 05 희소성표의 단어가 {EXPECT_WORDS}종이 아닙니다"
              f"({len(words)}종). 계산은 계속합니다.")
    presence_w = word_presence(bot_ids + hum_ids, rates10, words)

    def word_getter(uids, key):
        return word_vector(uids, rates10, key)

    f_rows, f_m = compare_family(words, bot_ids, hum_ids, word_getter,
                                 presence_w, sparse_cut)

    # ── 형태자질 · UPOS ─────────────────────────────────────────
    sub = {u: measures[u] for u in (bot_ids + hum_ids)}
    axis_map = build_axis_map(sub)
    feat_keys = sorted({k for a in sub.values() for k in a.get("자질", {})})
    upos_keys = sorted({k for a in sub.values() for k in a.get("UPOS", {})})
    kinds = {k: denom_kind_of(k, axis_map) for k in feat_keys}
    ratios, aux_ratios, presence_f = compute_ratios(sub, feat_keys, axis_map)
    upos_ratios, presence_u = compute_upos_ratios(sub, upos_keys)
    del sub, aux_ratios     # 보조 비율은 07이 판정에 쓰지 않았고 09-2도 안 쓴다

    def feat_getter(uids, key):
        return defined_values(uids, ratios, key)

    def upos_getter(uids, key):
        return defined_values(uids, upos_ratios, key)

    m_rows, m_m = compare_family(feat_keys, bot_ids, hum_ids, feat_getter,
                                 presence_f, sparse_cut, kinds)
    u_rows, u_m = compare_family(upos_keys, bot_ids, hum_ids, upos_getter,
                                 presence_u, sparse_cut)

    n_axis = sum(1 for k in feat_keys if kinds[k] == DENOM_AXIS)
    print(f"\n      가족 1 F블록 {len(words)}종 · 가족 2 형태자질 "
          f"{len(feat_keys)}종(축 내부 분모 {n_axis}종) · "
          f"가족 3 UPOS {len(upos_keys)}종")
    print(f"      BH 가족 크기   F {f_m}종 · 형태자질 {m_m}종 · UPOS {u_m}종")
    print("      세 가족에 각각 따로 보정했다. 서로 다른 m에서 나온 q이므로")
    print("      세 표의 q를 한 줄로 세워 비교하면 안 된다(07·09-1·옛 산포검정(보관)과 같은 규율).")

    # ── 축 목록 대조 — 눈금이 바뀌었는가 ────────────────────────
    axis_report, denom_changed = compare_axis_map(axis_map, base_axes)
    line("축 목록 대조 — 눈금이 바뀌지 않았는가")
    print("  07은 축을 하드코딩하지 않고 자료에서 유도했다. '자료가 바뀌면 규칙이")
    print("  따라간다'는 설계이고, 09-2는 자료가 바뀐 경우이므로 그 설계대로 다시")
    print("  유도했다. 다만 눈금이 바뀐 사실은 반드시 드러나야 한다 — 어떤 축의")
    print("  값이 댓글에서 하나로 줄면 분모가 '축 내부 합'에서 '토큰수'로 조용히")
    print("  바뀌고, 그러면 같은 이름의 두 δ가 서로 다른 것을 재게 된다.")
    print()
    print(f"  07 축 {axis_report['07축수']}개 · 09-2 축 {axis_report['10축수']}개")
    print(f"  형태자질 종수  07 {len(base_feats)}종 → 09-2 {len(feat_keys)}종")
    print(f"  UPOS 종수      07 {len(base_upos)}종 → 09-2 {len(upos_keys)}종")
    if axis_report["동일"]:
        print("\n  축 목록과 값 목록이 07과 완전히 같다. 눈금이 그대로다.")
    else:
        print()
        print("  ■ 경고 — 축 목록이 07과 다릅니다.")
        if axis_report["사라진축"]:
            print(f"    07에 있었으나 09-2에 없는 축 {len(axis_report['사라진축'])}개: "
                  f"{', '.join(axis_report['사라진축'])}")
        if axis_report["새로생긴축"]:
            print(f"    09-2에 새로 생긴 축 {len(axis_report['새로생긴축'])}개: "
                  f"{', '.join(axis_report['새로생긴축'])}")
        for ch in axis_report["값목록이_달라진축"][:10]:
            print(f"    {ch['축']}  07 {ch['07값']} → 09-2 {ch['10값']}")
        if len(axis_report["값목록이_달라진축"]) > 10:
            print(f"    … 이 밖에 {len(axis_report['값목록이_달라진축']) - 10}개 축")
        print()
        print("    값 목록만 달라진 축은 분모의 '내용'이 달라진 것이고, 아래")
        print("    분모 종류가 바뀐 축은 분모의 '정의'가 달라진 것이다. 뒤쪽이")
        print("    훨씬 무겁다.")
    if denom_changed:
        print()
        print(f"  ■■ 분모 종류가 바뀐 축 {len(denom_changed)}개 — 가장 무거운 경고")
        for ch in denom_changed:
            print(f"     {ch['축']}  07 {ch['07분모']} → 09-2 {ch['10분모']}")
        print("     이 축의 자질은 07의 δ와 09-2의 δ가 서로 다른 눈금에서 나온")
        print("     값이다. [6/8] 표에서 나란히 놓이지만 '유지/무너짐' 판정을")
        print("     그대로 읽으면 안 된다. 해석에서 따로 떼어 다루라.")
    else:
        print("\n  분모 종류가 바뀐 축은 없다. 07과 같은 눈금으로 잰 값이다.")

    f_sum = family_summary(f_rows, f_m, sparse_cut, n_all, "F 블록")
    m_sum = family_summary(m_rows, m_m, sparse_cut, n_all, "형태자질")
    u_sum = family_summary(u_rows, u_m, sparse_cut, n_all, "UPOS")

    # ══════════════════════════════════════════════════════════════
    # [6/8] 기준선 대조
    # ══════════════════════════════════════════════════════════════
    print("\n[6/8] 기준선 대조 (06·07과 항목별로 · 판정 형식은 09-1과 같다)")
    print("      유지  = 앞 단계에서 주목이었고 09-2에서도 |δ| ≥ 0.147")
    print("      무너짐 = 앞 단계에서 주목이었으나 09-2에서 문턱 아래로 떨어짐")
    print("      뒤집힘 = 방향이 반대로 감 — 그 항목에 대해 우리가 아는 것은 없다")
    print("      신규  = 09-2에서 새로 문턱을 넘음 (09-2는 진단이라 결론에 올리지 않는다)")

    f_cross = crosswalk(f_rows, base_words)
    m_cross = crosswalk(m_rows, base_feats)
    u_cross = crosswalk(u_rows, base_upos)

    print_crosswalk(f_cross, "06",
                    f"F 블록 {len(words)}종 중 |09-2 δ| 상위 "
                    f"{min(TOP_SHOW, len(f_cross))}종", TOP_SHOW)
    f_verd = family_verdict(f_cross, "F 블록")

    print_crosswalk(m_cross, "07",
                    f"형태자질 {len(m_cross)}종 중 |09-2 δ| 상위 "
                    f"{min(TOP_SHOW, len(m_cross))}종", TOP_SHOW)
    m_verd = family_verdict(m_cross, "형태자질")

    print_crosswalk(u_cross, "07", f"UPOS {len(u_cross)}종 전부 (|09-2 δ| 내림차순)")
    u_verd = family_verdict(u_cross, "UPOS")
    print("\n      PUNCT 줄만은 눈금이 다르다(분모는 구두점 제외 토큰수인데")
    print("      분자는 구두점 수다). 07·09-1·옛 산포검정(보관)이 그랬듯 여기서도 해석하지 않는다.")

    # ── 총사용률 위치 δ 대조 ────────────────────────────────────
    line("총사용률 위치 δ — 06과 대조 (예측 2의 판정 자료)")
    d06_total = loc06_total.get("델타")
    if d06_total is None:
        print("  06_비교결과.json 에 총사용률 δ가 없다. 대조할 수 없다.")
    else:
        print(f"  06 (전체 글, 봇 {n_bot_all:,} · 사람 {n_hum_all:,})   "
              f"δ = {d06_total:+.4f}")
    print(f"  09-2 (댓글 한정, 봇 {len(bot_ids):,} · 사람 {len(hum_ids):,})   "
          f"δ = {total10['델타']:+.4f}")
    if d06_total is not None:
        shift = total10["델타"] - d06_total
        print(f"  이동 Δδ = {shift:+.4f}   "
              f"({'더 음수 쪽' if shift < 0 else '더 양수 쪽'}으로 갔다)")
        print()
        print("  읽는 법: δ는 봇 기준이다. 제목은 기능어를 적게 쓰는 문형이고 그")
        print("  제목이 사람 쪽에 더 많았으므로, 제목을 빼면 사람의 총사용률이")
        print("  올라가고 δ는 더 음수 쪽으로 가야 한다. 그것이 예측 2다.")

    # ── 왼쪽 꼬리 ───────────────────────────────────────────────
    cut = review05.get("이상치_하한")
    line("총사용률 분포의 왼쪽 꼬리 — 05의 하한 이상치가 줄었는가 (예측 3)")
    print("  05는 라벨을 모르는 상태에서 총사용률이 중앙값 − 3×MAD 아래인 계정을")
    print("  표시해 두었다. 그 계정들의 원문이 뉴스 제목을 그대로 공유하는")
    print("  '헤드라인 투'였다는 것이 05의 관찰이다. 제목을 빼면 그 꼬리가")
    print("  걷혀야 한다. 05의 경계를 그대로 쓴다 — 새 경계를 만들면 자유도가 는다.")
    tail = check_pred3(cut, rates10, rates05, sorted(rates10))
    if tail["판정"] != "판정불가":
        print()
        print(f"  하한 {tail['하한']}  (05_사용률검수.json 에서 읽어 옴)")
        print(f"  05 전체 {tail['05전체_계정수']:,}계정 중 하한 미만  "
              f"{tail['05전체_미만계정']:,}계정")
        print()
        print(f"  ── 같은 계정들 안에서 견준다 (생존 {tail['생존계정수']:,}계정) ──")
        print(f"     05 값 기준 하한 미만   {tail['생존계정_05기준_미만']:>5,}계정  "
              f"({tail['생존계정_05기준_비율']:.1%})")
        print(f"     09-2 값 기준 하한 미만 {tail['생존계정_10기준_미만']:>5,}계정  "
              f"({tail['생존계정_10기준_비율']:.1%})")
        print(f"     줄어든 계정            {tail['줄어든_계정수']:>+5,}계정"
              "   (양수면 꼬리가 짧아진 것)")
        print()
        print("     같은 계정을 두 번 재어 견주므로 '표본이 작아진 몫'이 섞이지")
        print("     않는다. 05 전체 기준 숫자는 사전선언이 적은 172계정과 대조하는")
        print("     용도로만 함께 싣는다.")

    # ══════════════════════════════════════════════════════════════
    # [7/8] 산포 재검정 (예측 4용)
    # ══════════════════════════════════════════════════════════════
    print("\n[7/8] 산포 재검정 — 옛 산포검정(보관)의 동질성이 게시물 유형 통제 후에도 남는가")
    print("      Brown-Forsythe: 각 무더기에서 그 무더기의 중앙값을 뺀 절대편차를")
    print("      만들고, 그 절대편차를 두 무더기 간 U 검정에 넣는다. 공통 중앙값을")
    print("      쓰지 않는 것이 요점이다 — 쓰면 위치 차이가 산포 차이로 새어 든다.")
    print("      δ < 0 이면 봇의 절대편차가 작다 = 봇이 더 뭉쳐 있다.")

    line("■ 무엇과 견주는가 — 표본이 다르다는 사실을 먼저 적는다 ■")
    print("  09-2는 **매칭 표본이 아니다.** 09-1이 맞춘 분모 균형이 여기에는 없다.")
    print("  그래서 총사용률 산포는 옛 산포검정(보관)의 **전체 표본** 값과 견주는 것이 맞다.")
    print()
    # 옛 산포검정(보관)의 표본 크기도 하드코딩하지 않고 보관된 09_산포검정.json 에서 읽는다. 09-1·옛 산포검정(보관)이 다시
    # 돌아 매칭 쌍 수가 달라져도 화면이 옛 숫자를 계속 찍는 일이 없게 한다.
    n09_bot = (disp09_total.get("봇_유효n") or n_bot_all)
    n09_hum = (disp09_total.get("사람_유효n") or n_hum_all)
    n09_pair = ((disp09_dist.get("봇_요약") or {}).get("n"))
    print(f"    옛 산포검정(보관) 총사용률 산포 δ (전체 표본, 봇 {n09_bot:,} · 사람 {n09_hum:,})"
          f"   {disp09_total.get('델타')}")
    print(f"    옛 산포검정(보관) 계정별 거리 δ  (매칭 표본, 봇·사람 각 "
          f"{n09_pair if n09_pair is not None else '?'})"
          f"        {disp09_dist.get('델타')}")
    print()
    print("  계정별 거리는 사정이 다르다. 옛 산포검정(보관)은 그 검정을 **매칭 표본에서만**")
    print("  냈으므로 짝이 되는 전체 표본 값이 아예 없다. 아래 09-2의 값은 옛 산포검정(보관)의")
    print("  매칭 표본 값과 나란히 놓이지만, 표본이 달라 크기를 곧바로 견줄 수")
    print("  없다. 그룹 내 거리는 무더기 크기에 따라 분포 자체가 달라지기")
    print("  때문이다. 그래서 예측 4의 판정에는 **방향과 유의성만** 쓴다.")

    disp_total = brown_forsythe(tot_bot, tot_hum)
    print("\n      ── 총 기능어 사용률의 산포 (댓글 한정) ──")
    print("        무더기      IQR       MAD   IQR비(사람÷봇)")
    if disp_total is None:
        print("        (검정 불가)")
    else:
        ratio = "—" if disp_total["IQR비"] is None else f"{disp_total['IQR비']:.2f}배"
        print(f"        봇   {disp_total['봇_IQR']:>9.4f}{disp_total['봇_MAD']:>10.4f}")
        print(f"        사람 {disp_total['사람_IQR']:>9.4f}"
              f"{disp_total['사람_MAD']:>10.4f}       {ratio}")
        print(f"\n        n = 봇 {disp_total['봇_유효n']:,} · "
              f"사람 {disp_total['사람_유효n']:,}")
        print(f"        U = {disp_total['U']:,.1f}   z = {disp_total['z']:.3f}   "
              f"양측 p = {disp_total['p']:.3g}")
        print(f"        δ = {disp_total['델타']:+.4f}  →  {disp_total['방향']}")
        print(f"        (옛 산포검정(보관) 전체 표본은 δ = {disp09_total.get('델타')} · "
              f"IQR비 {disp09_total.get('IQR비')}배였다)")
        print("        (단독 검정이라 q = p 로 읽는다. m = 1 에서 BH는 항등.)")

    # ── 계정별 거리 ─────────────────────────────────────────────
    nb, nh = len(bot_ids), len(hum_ids)
    pairs_b, pairs_h = nb * (nb - 1) // 2, nh * (nh - 1) // 2
    print(f"\n      ── 그룹 내 쌍거리 ({len(words)}차원 사용률 벡터의 L1) ──")
    print(f"      봇 {nb:,}계정 → {pairs_b:,}쌍 · 사람 {nh:,}계정 → {pairs_h:,}쌍")

    # 한 무더기에 계정이 하나뿐이면 그 안에 쌍이 없어 거리를 잴 수 없다.
    # 실제 자료에서는 나올 수 없는 경우지만, 여기서 예외가 나면 방금 끝낸
    # 30분짜리 파싱이 저장도 못 된 채 날아간다. 그래서 막아 둔다.
    if nb < 2 or nh < 2:
        # 한 무더기에 계정이 하나뿐이면 그 안에 쌍이 없다. 실제 자료에서는
        # 나올 수 없는 경우지만, 여기서 예외가 나면 방금 끝낸 30분짜리
        # 파싱이 저장도 못 된 채 날아간다. 그래서 막아 둔다.
        print("      ■ 한 무더기의 계정이 2개 미만이라 그룹 내 쌍이 없습니다.")
        print("        쌍거리와 계정별 거리 검정을 건너뜁니다. 예측 4의 (나)는")
        print("        값이 없으므로 미통과로 셉니다 — 문턱을 느슨하게 바꾸지")
        print("        않는다는 규율이 여기에도 적용됩니다. JSON의 계정별거리검정")
        print("        칸에는 '검정가능: false'가 남습니다.")
        bot_five = hum_five = five_number([])
        dist_ratio = distance_ratio_table(bot_five, hum_five)
        bot_med, hum_med, acct = [], [], None
        acct_bot_five = acct_hum_five = five_number([])
    else:
        print("      계산 중...", end=" ", flush=True)
        t0 = time.time()
        bot_vecs = dense_vectors(bot_ids, rates10, words)
        hum_vecs = dense_vectors(hum_ids, rates10, words)
        bot_dists, bot_per = within_group_distances(bot_vecs)
        hum_dists, hum_per = within_group_distances(hum_vecs)
        del bot_vecs, hum_vecs
        print(f"{time.time() - t0:.1f}초")

        bot_five = five_number(bot_dists)
        hum_five = five_number(hum_dists)
        dist_ratio = distance_ratio_table(bot_five, hum_five)
        del bot_dists, hum_dists

        print("\n        무더기         쌍수      최소       Q1      중앙"
              "       Q3      최대")
        for label_txt, s in (("봇-봇      ", bot_five), ("사람-사람  ", hum_five)):
            print(f"        {label_txt}{s['n']:>9,}{s['최소']:>10.4f}"
                  f"{s['Q1']:>9.4f}{s['중앙']:>10.4f}"
                  f"{s['Q3']:>9.4f}{s['최대']:>10.4f}")
        print("        비(사람÷봇)  "
              + " · ".join(
                  f"{k} {dist_ratio[k]:.2f}배" if dist_ratio[k] is not None
                  else f"{k} —" for k in ("최소", "Q1", "중앙", "Q3", "최대")))

        print("\n      ■ 여기에 p값을 붙이지 않는 이유 ■ [옛 산포검정(보관)에서 그대로]")
        print(f"      위 쌍들은 서로 독립이 아니다. 봇 계정 하나가 {nb - 1:,}개 쌍에,")
        print(f"      사람 계정 하나가 {nh - 1:,}개 쌍에 동시에 들어간다. 이런 자료에")
        print("      U 검정을 걸면 표본이 수십만인 것처럼 계산되어 어떤 사소한 차이든")
        print("      유의해진다. 그래서 기술통계로만 읽고, 검정은 계정당 값 하나로")
        print("      줄인 뒤에 건다 — 그러면 계정 수가 곧 표본 수가 된다.")
        print("      ※ 옛 산포검정(보관)의 매칭 표본은 두 무더기의 계정 수가 같아 쌍 수도 같았다.")
        print("        09-2는 무더기 크기가 다르므로 쌍 수도 다르다. 다섯 숫자는")
        print("        크기에 무관한 요약이라 비교는 성립하지만, 이 비대칭을 알고")
        print("        읽으라.")

        bot_med = [statistics.median(v) for v in bot_per]
        hum_med = [statistics.median(v) for v in hum_per]
        del bot_per, hum_per
        acct = mann_whitney(bot_med, hum_med)
        acct["방향"] = direction_disp(acct["델타"])
        acct_bot_five = five_number(bot_med)
        acct_hum_five = five_number(hum_med)

        print("\n      계정별 요약 — '같은 무더기 안 다른 계정들과의 거리 중앙값'")
        print("        무더기       계정      최소       Q1      중앙"
              "       Q3      최대")
        for label_txt, s in (("봇        ", acct_bot_five),
                             ("사람      ", acct_hum_five)):
            print(f"        {label_txt}{s['n']:>7,}{s['최소']:>10.4f}"
                  f"{s['Q1']:>9.4f}{s['중앙']:>10.4f}"
                  f"{s['Q3']:>9.4f}{s['최대']:>10.4f}")
        print(f"\n        U = {acct['U']:,.1f}   z = {acct['z']:.3f}   "
              f"양측 p = {acct['p']:.3g}")
        print(f"        δ = {acct['델타']:+.4f}  →  {acct['방향']}")
        print(f"        (옛 산포검정(보관) 매칭 표본은 δ = {disp09_dist.get('델타')}였다 — "
              "표본이 달라 크기는 견주지 않는다)")
        print("        (단독 검정이라 q = p 로 읽는다. 이 검정을 판정에 쓴다.)")
        if (acct["델타"] < 0) != (hum_five["중앙"] > bot_five["중앙"]):
            print("\n      ※ 기술통계와 계정별 요약 검정의 방향이 어긋난다. 어느")
            print("        한쪽을 고르지 말고 왜 어긋나는지부터 확인하라 — 한 계정이")
            print("        여러 쌍에 들어가는 구조가 만든 차이일 수 있다.")

    # ══════════════════════════════════════════════════════════════
    # [8/8] 사전 예측 대조
    # ══════════════════════════════════════════════════════════════
    print("\n[8/8] 사전 예측 대조")
    print_prediction_header()

    r1 = check_pred1(f_cross, m_cross, base_feats)
    print_pred_meta(PREDICTIONS[0])
    print(f"        지정 항목 {r1['지정항목수']}종 "
          f"(축 단위로 세면 {r1['축단위_개수']}항목 — Gender 계열이 "
          f"{len(r1['Gender계열'])}종이다)")
    print("        항목            앞 δ  09-2 δ      Δδ  판정")
    for it in r1["항목"]:
        if it["델타"] is None:
            print(f"        {it['항목']:<14}{'—':>7}{'—':>8}{'—':>8}  검정불가")
            continue
        print(f"        {it['항목']:<14}{it['앞델타']:>+7.3f}{it['델타']:>+8.3f}"
              f"{it['변화량']:>+8.3f}  {it['판정']}")
    print(f"          유지 {r1['유지수']} · 무너짐 {r1['무너짐수']} · "
          f"뒤집힘 {r1['뒤집힘수']}")
    print(f"        → 예측 1 : {r1['판정']}")
    if r1["판정"] == "빗나감":
        print("          ■ 머리가 무너졌다. 보관된 07-12 사전선언의 10-1항(현 09-2)이 적어 둔 대로,")
        print("            그 신호는 문체가 아니라 장르 혼합비였다는 뜻이고")
        print("            06·07의 해석을 철회해야 한다. 결과를 본 뒤에 정하는")
        print("            것이 아니라 미리 적어 둔 약속을 실행하는 것이다.")

    r2 = check_pred2(total10, loc06_total)
    print_pred_meta(PREDICTIONS[1])
    if r2["판정"] == "판정불가":
        print(f"        → 예측 2 : 판정불가  ({r2.get('사유', '')})")
    else:
        print(f"        06 δ = {r2['06델타']:+.4f}  →  09-2 δ = {r2['10델타']:+.4f}"
              f"   (이동 {r2['이동']:+.4f})")
        print(f"        → 예측 2 : {r2['판정']}")

    r3 = tail
    print_pred_meta(PREDICTIONS[2])
    if r3["판정"] == "판정불가":
        print(f"        → 예측 3 : 판정불가  ({r3.get('사유', '')})")
    else:
        print(f"        생존 {r3['생존계정수']:,}계정에서 하한({r3['하한']}) 미만  "
              f"05 값 {r3['생존계정_05기준_미만']:,} → "
              f"09-2 값 {r3['생존계정_10기준_미만']:,}")
        print(f"        05 전체 {r3['05전체_계정수']:,}계정 기준으로는 "
              f"{r3['05전체_미만계정']:,}계정 (사전선언은 172라 적었다)")
        print(f"        → 예측 3 : {r3['판정']}")

    r4 = check_pred4(disp_total, acct, disp09_total, disp09_dist)
    print_pred_meta(PREDICTIONS[3])
    print(f"        (가) 총사용률 산포   δ = {r4['총사용률_산포_델타']} · "
          f"q = {r4['총사용률_산포_q']}   → {'통과' if r4['가_총사용률'] else '미통과'}")
    print(f"             옛 산포검정(보관) 전체 표본  δ = {r4['09_총사용률_산포_델타_전체표본']}")
    print(f"        (나) 계정별 거리     δ = {r4['계정별거리_델타']} · "
          f"q = {r4['계정별거리_q']}   → {'통과' if r4['나_계정별거리'] else '미통과'}")
    print(f"             옛 산포검정(보관) 매칭 표본  δ = {r4['09_계정별거리_델타_매칭표본']}"
          "   (표본이 달라 크기는 견주지 않는다)")
    print(f"        → 예측 4 : {r4['판정']}")
    if r4["판정"] == "빗나감":
        print("          ■ 옛 산포검정(보관)의 동질성이 게시물 유형 통제 후에 사라졌다. 그렇다면 그")
        print("            동질성은 '봇이 댓글만 쓴다'의 부산물이었다는 뜻이고,")
        print("            옛 산포검정(보관)이 잡은 것은 봇의 성질이 아니라 장르 구성의")
        print("            균질성이다. 옛 산포검정(보관)의 결론을 그렇게 고쳐 써야 한다.")

    r5 = check_pred5(drop)
    print_pred_meta(PREDICTIONS[4])
    if r5["판정"] == "판정불가":
        print(f"        → 예측 5 : 판정불가  ({r5.get('사유', '')})")
    else:
        print(f"        탈락 {r5['탈락계정수']:,}계정 = 봇 {r5['탈락_봇']:,} + "
              f"사람 {r5['탈락_사람']:,}")
        print(f"        탈락 무더기 봇 비율 {r5['탈락_봇비율']:.1%} ÷ "
              f"전체 봇 비율 {r5['전체_봇비율']:.1%} = 편중 배수 "
              f"{r5['편중배수']:.2f}배")
        print(f"        → 예측 5 : {r5['판정']}")
        if r5["판정"] == "빗나감":
            print("          ■ 이 예측은 다섯 중 유일하게 '검산' 성격을 갖는다.")
            print("            제목만 쓰는 39계정이 전원 사람이므로 최소한 그")
            print("            39개는 반드시 탈락해야 한다. 빗나갔다면 코퍼스")
            print("            구축 코드를 먼저 의심하라.")

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
    print("      빗나간 것을 지우지 않는다. 보관된 07-12 사전선언의 10항(현 09-2)을 쓸 때 무엇을 예상했고")
    print("      자료가 무엇을 돌려주었는지가 나란히 남아야 한다.")
    print()
    print(f"      {HEAD_RULE}")

    # ══════════════════════════════════════════════════════════════
    # 저장
    # ══════════════════════════════════════════════════════════════
    line("저장")
    # 총사용률·제목비율·계정별 거리는 가족 밖 단독 검정이라 BH를 거치지 않는다.
    # m = 1 에서 BH는 항등사상이므로 q = p 다. 저장 칸을 비워 두면 읽는 사람이
    # "보정을 빠뜨렸나"를 매번 되묻게 되므로 같은 값을 q 자리에 명시해 둔다.
    method = (
        "01_botsim_적격검열.py 의 적격 판정 규칙(URL·멘션 제거, 자기폭로 문장 "
        f"절제, MIN_CHARS={MIN_CHARS}, MAX_DOCS={MAX_DOCS}, MIN_DOCS={MIN_DOCS}, "
        f"계정 단위 langid 판정 {LANG_TARGET})을 한 글자도 바꾸지 않고 그대로 "
        "적용하되, 입력에서 posts(게시글 제목)를 빼고 comment_1·comment_2만 "
        "썼다. 대상은 01이 적격으로 판정한 계정이다. 그 코퍼스를 04와 같은 "
        "파이프라인(stanza tokenize,pos · use_gpu=False · bulk_process 계정 "
        "단위)으로 재파싱하고, 05의 분모 규칙(토큰수_구두점제외)으로 F 사용률을, "
        "07의 분모 규칙(대립값 2 이상인 축은 축 내부 합, 하나뿐이면 "
        "토큰수_구두점제외)으로 형태자질을, 토큰수_구두점제외로 UPOS를 냈다. "
        "축 판별은 07과 같이 하드코딩하지 않고 댓글 한정 자료에서 다시 "
        "유도했으며, 07의 축분류와 대조해 차이를 기록했다. 검정은 06과 동일한 "
        "Mann-Whitney U(양측·동점 보정·연속성 보정) + Cliff's δ(그룹1 = bot), "
        f"다중비교는 Benjamini-Hochberg FDR q = {Q_ALPHA}를 세 가족(F {len(words)}종 · "
        f"형태자질 {len(feat_keys)}종 · UPOS {len(upos_keys)}종)에 각각 별도로 "
        f"걸었다. 주목 = q ≤ {Q_ALPHA} 그리고 |δ| ≥ {DELTA_NOTABLE}. 기준선 대조 "
        "판정은 09-1과 같은 형식(유지 / 무너짐 / 방향 뒤집힘 / 신규)이며, 판정에는 "
        "δ 문턱만 쓰고 q는 참고로 둔다(표본이 줄어 q는 그것만으로도 커진다). "
        "산포는 옛 산포검정(보관)과 같은 Brown-Forsythe(그룹별 중앙값 기준 절대편차의 U 검정)와 "
        "계정별 거리 요약 검정으로 다시 냈다. 보관된 07-12 사전선언의 10항(현 09-2)."
    )
    limits = (
        "09-2는 표본이 줄어든 비교다. 댓글이 MIN_DOCS 미만이 되어 탈락한 계정이 "
        f"{drop['탈락계정수']:,}개 있고 그 탈락은 무작위가 아니다(제목만 쓰는 "
        "39계정이 전원 사람이다). 따라서 06·07과 09-2의 차이에는 '장르를 뺀 몫'과 "
        "'표본이 달라진 몫'이 섞여 있으며 이 파일은 둘을 분리하지 못한다 — "
        "탈락 계정의 라벨 분포를 숫자로 내는 것까지가 전부다. "
        "제목 한정 분석은 하지 않았다(보관된 07-12 사전선언의 10-3항(현 09-2)): 제목은 관사·조동사를 "
        "구조적으로 생략해 기능어 사용률의 뜻 자체가 달라지고, 제목만으로 "
        "적격인 계정이 39개 전원 사람이라 비교가 성립하지 않는다. "
        "09-2는 매칭 표본이 아니므로 09-1이 맞춘 분모 균형이 없다 — 산포 대조는 "
        "옛 산포검정(보관)의 전체 표본 값과 견주는 것이 맞고, 옛 산포검정(보관)이 매칭 표본에서만 낸 계정별 "
        "거리에는 짝이 되는 전체 표본 값이 아예 없어 방향과 유의성만 판정에 "
        "썼다. 그룹 내 거리는 무더기 크기에 따라 분포가 달라지는데 09-2의 두 "
        "무더기는 크기가 다르다. 축 목록을 자료에서 다시 유도했으므로 눈금이 "
        "07과 달라졌을 수 있으며, 분모 종류가 바뀐 축의 자질은 07의 δ와 09-2의 "
        "δ가 서로 다른 눈금에서 나온 값이다(위 축대조 항목 참조). "
        "그리고 09-2는 라벨을 아는 상태에서 수행되었다(보관된 07-12 사전선언의 결정 0-1) — "
        "봉인 대신 사전등록이 그 자리를 대신한다."
    )
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.machine()}",
            "방법": method,
            "한계": limits,
            "그룹1": GROUP1,
            "그룹2": GROUP2,
            "n_bot": len(bot_ids),
            "n_human": len(hum_ids),
            "라벨_사용": "09-2는 라벨을 아는 상태에서 수행된다(보관된 07-12 사전선언의 결정 "
                      "0-1). 다만 코퍼스를 짓는 단계는 라벨을 보지 않는다 — "
                      "01이 그랬듯 적격 판정에 라벨이 끼어들면 방어할 수 없다.",
            "01규칙_승계": {
                "MIN_CHARS": MIN_CHARS, "MIN_DOCS": MIN_DOCS,
                "MAX_DOCS": MAX_DOCS, "LANG_TARGET": LANG_TARGET,
                "언어판정도구": "langid.py (Lui & Baldwin, ACL 2012)",
                "판정단위": "계정(댓글 전체 결합)",
                "비고": "01_botsim_적격검열.py 의 값과 정규식을 그대로 썼다. "
                       "바뀐 것은 입력에서 posts를 뺀다는 것 하나뿐이다.",
            },
            "파이프라인": "tokenize,pos (use_gpu=False, bulk_process 계정 단위) "
                     "— 04와 같은 구성. stanza.download는 부르지 않았다.",
            "기능어_개수": len(funcwords),
            "기능어_해시": fp["기능어_해시"],
            "카운트_기준": "소문자+아포스트로피 정규화(’→') 표면형이 같은 정규화를 "
                      "거친 기능어 목록에 있으면 1회. 품사 조건 없음(04와 같음).",
            "재파싱규모": scale10,
            "04규모_대조": scale04,
            "총소요초": round(total_sec, 1),
            "이번실행초": round(run_sec, 1),
            "BH가족": {"F블록": f_m, "형태자질": m_m, "UPOS": u_m,
                     "비고": "세 가족에 각각 별도로 보정했다. 서로 다른 m에서 "
                            "나온 q이므로 세 표의 q를 한 줄로 세워 비교하면 "
                            "안 된다. 총사용률·제목비율·계정별 거리는 가족 밖 "
                            "단독이라 q = p 다(m = 1 에서 BH는 항등)."},
            "희소기준": f"출현 계정이 {sparse_cut:,}개 미만"
                     f"(댓글 한정 {n_all:,}계정의 {SPARSE_FRAC:.0%}). "
                     "표시만 하고 제외하지 않는다.",
            "판정규칙_상수": {
                "주목문턱": DELTA_NOTABLE,
                "q문턱": Q_ALPHA,
                "예측1_지정단어": list(PRED1_WORDS),
                "예측1_지정자질": list(PRED1_FEATS),
                "예측1_지정축": PRED1_AXIS,
                "예측1_Gender계열": r1["Gender계열"],
                "비고": "예측 1의 Gender 계열은 07에서 주목이었던 그 축의 자질 "
                      "전부다(자료로 정해지는 값이라 고를 여지가 없다). 판정은 "
                      "'전부 유지면 적중'이라 Gender를 한 항목으로 묶든 펼치든 "
                      "조건이 같다. 예측 3의 '같은 계정들 안에서 센다'는 규칙과 "
                      "예측 4의 '방향·유의성만 쓴다'는 규칙은 사전선언 문구에 "
                      "명시되지 않아 이 스크립트를 쓰면서(결과를 보기 전에) "
                      "정했다. 실행 후에 고치지 않는다.",
            },
            "사슬확인": chain,
            "축대조": axis_report,
            "가족요약": {"F블록": f_sum, "형태자질": m_sum, "UPOS": u_sum},
            "가족판정": {"F블록": f_verd, "형태자질": m_verd, "UPOS": u_verd},
            "사전예측결과": pred_results,
        },
        "장르구성": {
            "세는기준": "01이 적격으로 판정한 계정의 원본 항목 중, 텍스트가 공백을 "
                    "걷어 내고도 비어 있지 않은 것 전부. 01의 20자 필터도 200건 "
                    "상한도 걸지 않았다 — 장르 구성은 계정의 성질이고 필터는 "
                    "그 뒤에 오는 우리 쪽 결정이라, 필터 뒤 숫자로 장르를 말하면 "
                    "'제목이 짧아 20자 필터에 더 걸린다'는 우리 결정의 효과가 "
                    "장르 구성으로 둔갑한다.",
            "라벨별": {lab: {k: (rnd(v, 4) if isinstance(v, float) else v)
                          for k, v in c.items()}
                    for lab, c in census.items()},
            "제목만쓰는계정": title_only,
            "사전선언_실측표": EXPECT_GENRE,
            "사전선언_제목만": EXPECT_TITLE_ONLY,
            "사전선언과_어긋난칸": genre_mismatch,
            "사전선언과_일치": not genre_mismatch,
            "계정수준_제목비율": {
                "정의": "계정마다 (제목 수) ÷ (제목 수 + 댓글 수). 보관된 07-12 사전선언의 10-3항(현 09-2)이 "
                      "제목 한정 분석 대신 요구한 계정 수준 장르 변수다.",
                "봇_다섯숫자": {k: rnd(v, RATE_DIGITS)
                          for k, v in tr_five_bot.items()},
                "사람_다섯숫자": {k: rnd(v, RATE_DIGITS)
                           for k, v in tr_five_hum.items()},
                "U": rnd(tr_test["U"], 1) if tr_test else None,
                "z": rnd(tr_test["z"], STAT_DIGITS) if tr_test else None,
                "p": sig(tr_test["p"]) if tr_test else None,
                "q": sig(tr_test["p"]) if tr_test else None,
                "q비고": "단독 검정이라 q = p (m = 1 에서 BH는 항등).",
                "델타": rnd(tr_test["델타"], STAT_DIGITS) if tr_test else None,
                "방향": tr_test["방향"] if tr_test else None,
                "주목": bool(tr_test and tr_test["p"] <= Q_ALPHA
                          and abs(tr_test["델타"]) >= DELTA_NOTABLE),
                "계정별": {u: rnd(v, RATE_DIGITS)
                        for u, v in sorted(title_ratio.items())},
            },
        },
        "코퍼스": {
            "정의": "01의 적격 판정 규칙을 그대로 적용하되 입력에서 posts를 뺀 "
                  "댓글 한정 코퍼스.",
            "01적격_계정수": len(eligible),
            "살아남은_계정수": funnel["적격_계정합"],
            "살아남은_라벨별": funnel["적격_계정수"],
            "생존율": rnd(funnel["적격_계정합"] / len(eligible), 4)
                   if eligible else None,
            "문서수": funnel["적격_문서수"],
            "필터별_탈락": {
                "문서_탈락사유": funnel["문서_탈락사유"],
                "문서_탈락사유_라벨별": funnel["문서_탈락사유_라벨별"],
                "상한초과_절삭문서수": funnel["상한초과_절삭문서수"],
                "문서부족_탈락계정수": funnel["문서부족_탈락계정수"],
                "언어판정_대상계정수": funnel["언어판정_대상계정수"],
                "언어별_계정수": funnel["언어별_계정수"],
                "비영어_탈락계정수": funnel["비영어_탈락계정수"],
                "자기폭로_절제문서수": funnel["자기폭로_절제문서수"],
                "자기폭로_절제후_생존문서수": funnel["자기폭로_절제후_생존문서수"],
            },
            "탈락_라벨분포": {k: v for k, v in drop.items()
                        if k != "탈락계정목록"},
            "탈락계정목록": drop["탈락계정목록"],
            "탈락계정_사유별": funnel["탈락계정목록"],
            "언어판정": lang_info,
            "분모0계정": undefined,
        },
        "F블록": pack_cross(f_cross, "06"),
        "형태자질": pack_cross(m_cross, "07"),
        "UPOS": pack_cross(u_cross, "07"),
        "총사용률": {
            "10": {
                "U": rnd(total10["U"], 1), "z": rnd(total10["z"], STAT_DIGITS),
                "p": sig(total10["p"]), "q": sig(total10["p"]),
                "q비고": "가족 밖 단독 검정이라 q = p (m = 1 에서 BH는 항등).",
                "델타": rnd(total10["델타"], STAT_DIGITS),
                "방향": total10["방향"],
                "봇_요약": {k: rnd(v, RATE_DIGITS) for k, v in q_bot.items()},
                "사람_요약": {k: rnd(v, RATE_DIGITS) for k, v in q_hum.items()},
            },
            "06대조": {
                "06델타": d06_total,
                "06출처": "06_비교결과.json → 총사용률_비교 (읽어 옴)",
                "이동": rnd(total10["델타"] - d06_total, STAT_DIGITS)
                     if d06_total is not None else None,
            },
            "왼쪽꼬리": tail,
        },
        "산포": {
            "정의": "옛 산포검정(보관)과 같은 Brown-Forsythe(그룹별 중앙값 기준 절대편차의 U "
                  "검정)와 계정별 거리 요약 검정을 댓글 한정 표본에서 다시 냈다. "
                  "δ < 0 이면 봇의 절대편차가 작다 = 봇이 더 뭉쳐 있다. 06·07·09-1의 "
                  "위치 δ와 뜻이 다르므로 한 표에 섞어 읽지 말 것.",
            "표본_비고": "09-2는 매칭 표본이 아니다. 총사용률 산포는 옛 산포검정(보관)의 전체 표본 "
                     "값과 견주는 것이 맞고, 계정별 거리는 옛 산포검정(보관)이 매칭 표본에서만 "
                     "냈으므로 짝이 되는 전체 표본 값이 없다.",
            "총사용률_산포": pack_disp(disp_total),
            "09_총사용률_산포_전체표본": disp09_total,
            "쌍거리": {
                "정의": f"댓글 한정 표본에서 {len(words)}차원 사용률 벡터의 그룹 내 "
                      f"계정쌍 L1 거리. 봇 {nb:,}계정 → {pairs_b:,}쌍 · "
                      f"사람 {nh:,}계정 → {pairs_h:,}쌍.",
                "봇": {k: rnd(v, RATE_DIGITS) for k, v in bot_five.items()},
                "사람": {k: rnd(v, RATE_DIGITS) for k, v in hum_five.items()},
                "비_사람나누기봇": {k: rnd(v, STAT_DIGITS)
                            for k, v in dist_ratio.items()},
                "검정_안_함": "쌍은 서로 독립이 아니다(한 계정이 수백 개 쌍에 동시에 "
                         "들어간다). p를 붙이면 어떤 차이든 유의해지므로 "
                         "기술통계로만 보고한다.",
                "무더기크기_비대칭": "옛 산포검정(보관)의 매칭 표본은 두 무더기가 512로 같아 쌍 수도 "
                             "같았다. 09-2는 무더기 크기가 달라 쌍 수도 다르다. "
                             "다섯 숫자는 크기에 무관한 요약이라 비교는 "
                             "성립하지만 이 비대칭을 알고 읽어야 한다.",
            },
            "계정별거리검정": {
                "정의": "계정마다 '같은 무더기 안 다른 계정들과의 거리 중앙값'을 "
                      "구해 계정당 값 하나로 줄였다. 계정 수가 곧 표본 수가 되어 "
                      "독립성이 회복된다. 판정에는 이 검정을 쓴다.",
                "검정가능": acct is not None,
                "U": rnd(acct["U"], 1) if acct else None,
                "z": rnd(acct["z"], STAT_DIGITS) if acct else None,
                "p": sig(acct["p"]) if acct else None,
                "q": sig(acct["p"]) if acct else None,
                "q비고": "단독 검정이라 q = p (m = 1 에서 BH는 항등).",
                "델타": rnd(acct["델타"], STAT_DIGITS) if acct else None,
                "방향": acct["방향"] if acct else "검정 불가",
                "봇_요약": {k: rnd(v, RATE_DIGITS)
                        for k, v in acct_bot_five.items()},
                "사람_요약": {k: rnd(v, RATE_DIGITS)
                         for k, v in acct_hum_five.items()},
                "09_매칭표본": disp09_dist,
                "계정별_중앙값": {
                    "봇": {u: round(v, RATE_DIGITS)
                         for u, v in zip(bot_ids, bot_med)},
                    "사람": {u: round(v, RATE_DIGITS)
                          for u, v in zip(hum_ids, hum_med)},
                },
            },
        },
        # 04와 같은 꼴로 계정별 원카운트를 함께 담는다. 명세가 요구한 여덟 블록에
        # 더해 둔 것이고, 이유는 하나다 — 이 파일이 30분짜리 재파싱의 유일한
        # 산출물이다. 중간 저장 파일은 끝나면 지워지므로, 여기에 담지 않으면
        # 뒤에 자질 하나를 더 보고 싶어졌을 때 30분을 다시 써야 한다. 04가
        # "한 번 지나갈 때 쓸 만한 것을 다 주워 둔다"고 한 것과 같은 취지다.
        "계정": {uid: measures[uid] for uid in sorted(measures)},
    }
    write_json(OUT_JSON, out, indent=1)
    if os.path.exists(PROGRESS_JSON):
        os.remove(PROGRESS_JSON)   # 최종본이 생겼으므로 중간 저장은 역할이 끝났다
    print(f"      {OUT_JSON}")
    print(f"      {os.path.getsize(OUT_JSON):,} bytes · 총 소요 {fmt_dur(total_sec)}")

    # ── 눈으로 검수할 것 ────────────────────────────────────────
    line("확인 항목")
    print("  아래를 직접 보고 나서 다음 단계(09-3)로 넘어가십시오.")
    print("   1. 머리가 유지됐는가. [8/8] 예측 1이 09-2의 존재 이유다. we·must·")
    print("      our·was·he와 Tense=Past·Number=Sing·Gender 계열이 댓글 한정에서도")
    print("      |δ| ≥ 0.147 을 유지하면 그 신호는 문체다. 무너졌다면 그것은")
    print("      장르 혼합비였다는 뜻이고, 보관된 07-12 사전선언의 10-1항(현 09-2)이 적어 둔 대로 06·07의")
    print("      해석을 철회해야 한다. 일부만 유지됐다면 어느 항목이 남았는지가")
    print("      곧 주장의 범위다 — 남은 것만으로 다시 쓰라.")
    print("   2. 총사용률 δ가 예측대로 움직였는가. 제목이 사람 쪽에 5.0%p 더")
    print("      많았으므로 제목을 빼면 δ는 더 음수 쪽으로 가야 한다. 반대로")
    print("      갔다면 장르 구성비가 총사용률에 미치는 영향이 예상과 반대라는")
    print("      뜻이고, 09-2 전체의 전제를 다시 봐야 한다.")
    print("   3. 왼쪽 꼬리가 짧아졌는가. 05가 라벨 없이 '헤드라인 투'라고 적어 둔")
    print("      계정들이 제목을 빼면 정상 범위로 돌아와야 한다. 돌아오지 않았다면")
    print("      그 계정들의 낮은 사용률은 제목 탓이 아니라 다른 무엇 탓이고,")
    print("      05의 원문 관찰을 다시 읽어야 한다.")
    print("   4. 산포 신호가 장르와 무관한가. 옛 산포검정(보관)의 동질성(봇끼리 닮았다)이 댓글")
    print("      한정에서도 남으면 그것은 봇의 성질이다. 사라지면 '봇이 댓글만")
    print("      쓴다'의 부산물이었다는 뜻이다 — 봇은 제목만 쓰는 계정이 0개고")
    print("      제목 비율도 더 낮다. 옛 산포검정(보관)의 결론 문장을 그렇게 고쳐 써야 한다.")
    print("   5. 축 목록이 07과 같은가. 다르면 눈금이 바뀐 것이다. 특히 분모")
    print("      종류가 바뀐 축의 자질은 07의 δ와 09-2의 δ가 서로 다른 것을 재고")
    print("      있는데 표에서는 나란히 놓인다. [5/8]의 축 대조를 먼저 보고,")
    print("      바뀐 축이 있으면 그 자질들의 '유지/무너짐' 판정을 그대로 읽지")
    print("      말고 해석에서 따로 떼어 다루라.")
    print()
    print("  이 다섯은 스크립트가 대신 판정할 수 없는 것들이다. δ와 q를 뽑는")
    print("  일까지가 코드의 몫이고, 그 숫자가 무슨 이야기인지는 사람이 읽는다.")
    print("  그리고 09-2는 진단이지 대체가 아니다 — 탈락한 계정을 기록만 하고")
    print("  06·07의 결과를 수정하지 않은 것이 그 뜻이다(보관된 07-12 사전선언의 10-5항(현 09-2)).")


if __name__ == "__main__":
    main()
