#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
05_사용률검수.py
────────────────────────────────────────────────────────────────────────────
목적
    04가 센 원카운트를 계정별 '사용률'로 바꾸고, 그 분포를 사람 눈으로
    검수한다. 봇과 사람을 비교하지 않는다. 어떤 계정도, 어떤 단어도
    버리지 않는다.

왜 검수와 비교를 갈라 놓나
    분포를 처음 보는 순간이 이 파이프라인에서 가장 위험한 자리다. 봇과
    사람이 함께 칠해진 히스토그램을 먼저 만나면 튀는 계정을 빼거나 분모를
    바꿔 보고 싶어진다. 한 번 손을 대면 그 조정이 결과를 얼마나 움직였는지
    아무도 되짚지 못한다.
    그래서 05는 라벨 없이 전체 분포만 본다. 여기서 "이상하다"고 판단한 것은
    봇/사람 어느 쪽에도 유리할 수 없다 — 어느 쪽인지 모르는 채로 판단했기
    때문이다. 라벨은 06에서 처음 연다(사전선언 결정 4). 같은 이유로 이상치를
    '표시만' 한다. 제외 기준을 여기서 새로 만들면 자유도가 늘고 "왜 하필 그
    값이냐"는 방어 부담이 생긴다(결정 2).

무엇을 따르나
    05-06_사전선언.md (2026-08-25 확정)를 그대로 구현한다.
        결정 1  사용률 분모 = 토큰수_구두점제외
        결정 2  희귀 단어·이상치 계정은 기록만, 제외 없음
        결정 4  05 검수(라벨 미사용) / 06 비교(라벨 개봉) 분리
    결과를 보고 이 결정을 바꾸지 않는다. 바꿔야 한다면 사전선언 말미의
    「변경 이력」에 사유와 일시를 먼저 적고 변경 전 결과도 함께 보고한다.

무엇을 보는가 (사전선언의 검수 항목 4가지 — 모두 기록용이다)
    1. 총 기능어 사용률 분포 — 요약통계와 히스토그램. 상식적인가
    2. 계정당 분모(구두점 제외 토큰수) 분포 — 분모가 작은 계정 주의
    3. 단어별 출현 계정 수 — 희소성 표. 06 해석 때 참고 자료가 된다
    4. 이상치 계정 플래그와 그 원문 표본 — 눈으로 보되 제외하지 않는다

실행
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 -u 05_사용률검수.py
    필요 패키지 없음. 표준 라이브러리만 쓴다(03·04와 같은 무의존 원칙).
    하는 일이 나눗셈과 정렬뿐이라 이 기계에서 몇 초면 끝난다.

선행 조건
    같은 폴더에 04_기능어측정.json 이 있어야 한다. 없으면 아무것도 하지
    않고 끝낸다. 01_적격계정.json 은 [4]의 이상치 원문 눈검수에만 쓴다 —
    없으면 그 표본 출력만 건너뛰고 나머지는 그대로 돈다. 01을 열 때도
    "계정" 키만 꺼내고 라벨이 든 나머지는 즉시 버린다(04와 같은 del 규율).

산출
    05_사용률검수.json   계정별 사용률 + 검수 요약. 06번의 입력.
"""

import json
import os
import platform
import statistics
import time
from collections import Counter


# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더를 기준으로 잡는다 — 연구 폴더를 통째로 옮겨도 깨지지 않는다.
HERE = os.path.dirname(os.path.abspath(__file__))
MEASURE_JSON = f"{HERE}/04_기능어측정.json"      # 04 산출물 — 이 파일의 주 입력
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"       # 01 산출물 — "계정" 키만, [4]에서만
OUT_JSON = f"{HERE}/05_사용률검수.json"          # 산출물

RATE_DIGITS = 6
# 사용률을 소수 6자리로 저장한다. 계정 하나의 토큰이 수백~수만 규모라 단어
# 한 번의 출현이 1e-5 언저리다. 6자리면 그 한 번이 여전히 구분되면서 파일이
# 불필요하게 커지지 않는다.

HIST_BINS = 25          # 25구간이면 IDLE 창 한 화면에 들어오고, 봉우리가
HIST_WIDTH = 44         # 하나인지 둘인지는 이 해상도로 보인다.

MAD_K = 3.0
# 이상치 경계 = 중앙값 ± 3×MAD. 근거는 flag_outliers()의 설명을 보라.
# 결정 2에 따라 이 경계는 '표시'에만 쓰고 제외에는 쓰지 않는다.

SMALL_DENOM_SHOW = 5    # 분모가 가장 작은 계정 몇 개를 표로 볼 것인가
SPARSE_SHOW = 15        # 희소성 표에서 아래쪽(드문 단어) 몇 개를 볼 것인가
COMMON_SHOW = 5         # 같은 표에서 위쪽(흔한 단어) 몇 개를 볼 것인가

OUTLIER_SHOW = 20       # 원문 표본을 띄울 이상치 계정 수 상한
SAMPLE_DOCS = 2         # 계정당 몇 건을 보일 것인가
SAMPLE_CHARS = 200      # 한 건을 몇 글자까지 보일 것인가
# 눈검수는 "이게 정상 텍스트인가"만 가리면 된다. 전문을 다 띄우면 화면이
# 넘쳐 오히려 아무도 읽지 않는다. 200자면 문체가 드러나기에 충분하다.

# ── 04와 대조할 기댓값 ─────────────────────────────────────────
# 04 실행 로그(04_기능어측정_출력.log)에 찍힌 값이다.
#   기능어 토큰 1,550,348 / 전체 토큰 4,214,937 = 36.8%   (구두점 포함)
# 구두점을 뺀 분모(3,756,059)로 다시 나누면 약 41.3%다. 이 파일이 쓰는 분모가
# 후자이므로 두 값을 모두 재계산해 04와 맞는지 본다. 허용 오차 0.2%p는 위
# 기댓값이 소수 첫째 자리까지 반올림된 값이기 때문이다. 이보다 크게 벌어지면
# 04와 05가 서로 다른 것을 세고 있다는 뜻이다.
EXPECT_RATIO_PUNCT = 0.368
EXPECT_RATIO_NOPUNCT = 0.413
CHECK_TOL = 0.002

# 요약통계 라벨. 한글은 터미널에서 두 칸을 차지해 f-string의 자리맞춤({:<4})이
# 어긋난다. 그래서 라벨 뒤 공백을 손으로 맞춰 둔다.
STAT_LABELS = [("최소  ", "최소"), ("Q1    ", "Q1"), ("중앙  ", "중앙"),
               ("Q3    ", "Q3"), ("최대  ", "최대"), ("평균  ", "평균")]


def line(title=""):
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다. 04의 같은 함수를 그대로 가져왔다.

    임시 파일에 먼저 쓰고 이름을 바꿔치기한다(os.replace). 쓰는 도중에 창을
    닫으면 파일이 반쯤 잘린 채 남고 06이 그것을 읽다 깨진다. 이름 바꾸기는
    쪼개지지 않는 연산이라, 어느 시점에 멈춰도 파일은 '이전 것' 아니면
    '새 것'이다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def summarize(values):
    """최소·Q1·중앙·Q3·최대·평균을 한 벌 낸다."""
    vs = sorted(values)
    # method="inclusive"는 가진 자료가 모집단 전체일 때 쓰는 정의다. 여기서는
    # 1,869계정이 표본이 아니라 '적격 계정 전부'이므로 이쪽이 맞다.
    q1, med, q3 = statistics.quantiles(vs, n=4, method="inclusive")
    return {"개수": len(vs), "최소": vs[0], "Q1": q1, "중앙": med,
            "Q3": q3, "최대": vs[-1], "평균": statistics.fmean(vs)}


def print_stats(stats, fmt):
    """요약통계를 세로로 찍는다. fmt은 값 하나를 문자열로 바꾸는 함수."""
    for label, key in STAT_LABELS:
        print(f"      {label}{fmt(stats[key])}")


def rounded(stats, digits):
    """저장용으로 소수를 잘라 낸다. 개수 같은 정수는 그대로 둔다."""
    return {k: (round(v, digits) if isinstance(v, float) else v)
            for k, v in stats.items()}


# ════════════════════════════════════════════════════════════════════════
# [1] 입력 적재 — 04를 읽고 그 지문을 이어받는다
# ════════════════════════════════════════════════════════════════════════
def load_measurement():
    """
    04 산출물에서 "설정"과 "계정"을 가져온다.

    04 파일에는 라벨이 애초에 들어 있지 않다(04가 읽지 않았으므로). 그래서
    여기서는 del 할 것이 없다 — 라벨을 조심해야 하는 파일은 01뿐이고, 그쪽은
    [4]에서 한 번만, "계정" 키만 열어 본다.
    """
    data = json.load(open(MEASURE_JSON, encoding="utf-8"))
    return data["설정"], data["계정"]


def inherit_fingerprint(conf):
    """
    04의 기능어 지문(해시·종수)을 05 산출물에 그대로 옮겨 적는다.

    왜 베껴 두나. 06은 05 파일만 읽고 비교를 한다. 그런데 사용률이라는 숫자는
    "어떤 기능어 목록으로 센 것인가"를 모르면 뜻이 없다. 02를 다시 돌려
    목록이 172종에서 180종으로 바뀌면 옛 05 파일의 사용률과 새 06의 해석이
    조용히 어긋난다. 해시를 달고 다니면 그 어긋남이 눈에 보인다.
    측정-검수-비교가 한 줄로 이어져 있다는 증거이기도 하다.
    """
    return {"기능어_해시": conf.get("기능어_해시"),
            "기능어_개수": conf.get("기능어_개수")}


# ════════════════════════════════════════════════════════════════════════
# [2] 사용률 계산 — 사전선언 결정 1
# ════════════════════════════════════════════════════════════════════════
def compute_rates(accounts):
    """
    계정마다 단어별 사용률과 총 사용률을 낸다.

    분모는 토큰수_구두점제외 하나로 고정이다(결정 1). 구두점 습관은 R 블록
    (리듬)이 다룰 신호라 F 블록(기능어)과 섞지 않는다. 저자 판별 연구가 단어
    수를 분모로 쓰는 관행과도 맞고, 04가 이미 저장해 둔 값이라 다시 파싱할
    필요도 없다.

    희소 저장은 04의 방식을 그대로 잇는다 — 04에 없는 단어(=0회)는 여기서도
    담지 않는다. 172종을 계정마다 다 적으면 대부분이 0인 표가 되고 파일만
    커진다. 없는 키 = 0으로 읽으면 된다.

    분모가 0인 계정은 사용률을 정의할 수 없어 따로 빼서 알린다. 결정 2가
    금지한 '분석적 제외'가 아니라 나눗셈이 성립하지 않는 것뿐이다(01의 적격
    기준상 나올 일이 없다. 나온다면 01을 의심해야 한다).
    """
    rates, undefined = {}, []
    # uid 오름차순으로 담는다 — 다시 돌려도 파일 순서가 같아야 비교가 쉽다.
    for uid in sorted(accounts):
        a = accounts[uid]
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


def cross_check(accounts):
    """
    전 계정을 합산해 전체 기능어 비율을 다시 계산하고 04와 맞춰 본다.

    왜 필요한가. 05는 04의 숫자를 그대로 믿고 나눗셈만 한다. 04 파일을 잘못
    읽거나(키 이름 착각) 중간에 다른 버전이 끼어들어도 사용률은 여전히
    '그럴듯한' 값으로 나온다. 0.4 언저리의 숫자가 뜨면 사람은 그냥 통과시킨다.
    합계 비율을 04 로그와 대조하는 것이 그런 조용한 어긋남을 잡는 가장 싼
    방법이다. 포함 기준은 04 로그에 그대로 찍혀 있어 직접 비교가 되고, 제외
    기준은 이 파일이 실제로 쓰는 분모라 둘 다 낸다.
    """
    fw = sum(sum(a["기능어"].values()) for a in accounts.values())
    tok = sum(a["토큰수"] for a in accounts.values())
    nopunct = sum(a["토큰수_구두점제외"] for a in accounts.values())
    r_punct, r_nopunct = fw / tok, fw / nopunct
    ok = (abs(r_punct - EXPECT_RATIO_PUNCT) <= CHECK_TOL and
          abs(r_nopunct - EXPECT_RATIO_NOPUNCT) <= CHECK_TOL)
    return {"기능어토큰": fw, "토큰수": tok, "토큰수_구두점제외": nopunct,
            "비율_구두점포함": round(r_punct, 4),
            "비율_구두점제외": round(r_nopunct, 4),
            "기대_구두점포함": EXPECT_RATIO_PUNCT,
            "기대_구두점제외": EXPECT_RATIO_NOPUNCT,
            "허용오차": CHECK_TOL, "일치": ok}


# ════════════════════════════════════════════════════════════════════════
# [3] 분포 검수 — 눈으로 볼 것들
# ════════════════════════════════════════════════════════════════════════
def print_histogram(values):
    """
    사용률 분포를 ASCII 막대로 그린다.

    요약통계 여섯 줄로는 봉우리가 하나인지 둘인지, 어느 쪽으로 꼬리가 긴지
    알 수 없다. 분포의 모양은 그림으로만 보인다.
    """
    lo, hi = min(values), max(values)
    if hi <= lo:
        print("      모든 계정의 값이 같습니다 — 그릴 분포가 없습니다.")
        print("      정상적인 데이터에서 나올 모양이 아닙니다. 04를 의심하십시오.")
        return
    span = hi - lo
    counts = [0] * HIST_BINS
    for v in values:
        k = int((v - lo) / span * HIST_BINS)
        if k == HIST_BINS:      # 최대값은 마지막 칸에 넣는다(경계 처리)
            k = HIST_BINS - 1
        counts[k] += 1
    tallest = max(counts)
    for k, c in enumerate(counts):
        left = lo + span * k / HIST_BINS
        right = lo + span * (k + 1) / HIST_BINS
        bar = "#" * round(c / tallest * HIST_WIDTH)
        print(f"      {left:6.1%} ~{right:6.1%} |{bar:<{HIST_WIDTH}} {c:>5,}")


def print_denominator_block(rates, accounts, stat_denom):
    """분모 분포와, 분모가 가장 작은 계정 몇 개를 보여 준다."""
    print("\n  ── 분모(구두점 제외 토큰수) 분포 ──")
    print_stats(stat_denom, lambda v: f"{v:>12,.0f} 토큰")

    smallest = sorted(rates, key=lambda u: rates[u]["분모"])[:SMALL_DENOM_SHOW]
    print(f"\n      분모가 가장 작은 {SMALL_DENOM_SHOW}계정")
    print("        계정          분모      문서수   총사용률")
    for uid in smallest:
        print(f"        {uid[:12]:<12}{rates[uid]['분모']:>8,}"
              f"{accounts[uid]['문서수']:>10,}"
              f"{rates[uid]['총사용률']:>10.1%}")

    # 분모가 작으면 사용률이 출렁인다 — 그래서 분포의 양 끝에는 문체가 유별난
    # 계정보다 글이 적은 계정이 먼저 모인다. 아래 print는 그 사실을 화면에서도
    # 읽게 하려는 것이다(이 파일은 눈검수용이다).
    print("\n      ※ 분모가 작으면 사용률이 출렁인다. 200토큰짜리 계정에서는")
    print("        기능어 한 번의 차이가 0.5%p를 움직이고, 5,000토큰이면 같은")
    print("        한 번이 0.02%p다. 눈금이 25배 다르다. [4]의 이상치 목록에")
    print("        작은 분모가 몰려 있다면 문체가 아니라 표본 크기의 문제다.")


def word_presence(accounts):
    """
    단어마다 '몇 개 계정에서 한 번이라도 나왔는가'를 센다.

    희소성을 재는 이유: 1,869계정 중 12계정에서만 나온 단어는 06의 검정에서
    거의 전부 0인 두 무더기를 비교하게 된다. p값이 어떻게 나오든 해석할 것이
    없다. 미리 표로 남겨 두면 06의 결과표를 볼 때 "이 단어는 애초에 데이터가
    없었다"를 즉시 알 수 있다. 결정 2에 따라 걸러 내지는 않는다 — 기록만 한다.
    """
    seen = Counter()
    for a in accounts.values():
        for w, n in a["기능어"].items():
            if n:      # 04는 0을 담지 않지만, '출현'의 정의를 코드에 남겨 둔다
                seen[w] += 1
    return seen


def print_sparsity_block(presence, n_accounts, expected_words):
    """희소성 표를 화면에 요약한다. 전체는 JSON에 담긴다."""
    print(f"\n  ── 단어별 출현 계정 수 (전체 {n_accounts:,}계정 기준) ──")
    ordered = sorted(presence.items(), key=lambda kv: (kv[1], kv[0]))

    print(f"\n      가장 드문 {SPARSE_SHOW}개")
    for w, n in ordered[:SPARSE_SHOW]:
        print(f"        {w:<12}{n:>8,}계정{n / n_accounts:>9.1%}")
    print(f"\n      가장 흔한 {COMMON_SHOW}개")
    for w, n in reversed(ordered[-COMMON_SHOW:]):
        print(f"        {w:<12}{n:>8,}계정{n / n_accounts:>9.1%}")

    # 한 계정에서도 안 나온 단어는 04가 아예 저장하지 않았으므로 이 표에
    # 나타나지 않는다. 04 로그는 "나타난 기능어 종류 172 / 172종"이었다.
    missing = (expected_words or 0) - len(presence)
    print(f"\n      나타난 단어 {len(presence)}종 / 목록 {expected_words}종")
    if missing > 0:
        print(f"      ※ {missing}종은 어느 계정에서도 나오지 않았다. 06의 검정에서")
        print("        두 무더기가 모두 0이 되어 비교가 성립하지 않는다.")


# ════════════════════════════════════════════════════════════════════════
# [4] 이상치 플래그 — 사전선언 결정 2 (표시만, 제외 없음)
# ════════════════════════════════════════════════════════════════════════
def flag_outliers(totals):
    """
    총사용률이 중앙값 ± 3×MAD 밖인 계정을 표시한다.

    MAD(Median Absolute Deviation, 중앙값 절대편차)는 각 값이 중앙값에서
    얼마나 떨어졌는지(|x − 중앙값|)를 구한 뒤 그 거리들의 '중앙값'을 취한
    것이다. 평균 대신 중앙값을, 제곱 대신 절댓값을 쓰는 산포 척도다.

    왜 표준편차 대신 쓰나. 표준편차는 편차를 제곱해 평균하므로 극단값 하나가
    자기 몫보다 훨씬 크게 폭을 벌린다. 이상치를 찾겠다고 표준편차로 경계를
    그으면, 찾으려던 그 이상치가 경계를 밖으로 밀어내 스스로 정상 범위 안에
    들어앉는다(masking). 중앙값과 MAD는 절반 미만의 값이 아무리 극단으로
    가도 거의 움직이지 않아 이 함정에 빠지지 않는다.

    3×MAD는 얼마나 넓은 그물인가. 정규분포에서 MAD × 1.4826 = 표준편차인데
    그 환산 계수를 곱하지 않으므로, 3×MAD는 표준편차로 치면 약 2.0σ 폭이다.
    꽤 촘촘해서 정상 계정도 제법 걸린다. 그래도 상관없다 — 이 플래그는
    "통계적으로 이상하다"는 판정이 아니라 "눈으로 한 번 보라"는 표시이고,
    결정 2에 따라 걸린 계정을 제외하지 않기 때문이다.

    MAD가 0이면(절반 이상이 중앙값과 정확히 같으면) 경계가 한 점으로 무너져
    기준이 성립하지 않는다. 그때는 건너뛴다.
    """
    values = list(totals.values())
    med = statistics.median(values)
    mad = statistics.median([abs(v - med) for v in values])
    if mad == 0:
        return med, 0.0, None, None, []
    low, high = med - MAD_K * mad, med + MAD_K * mad
    # 낮은 쪽부터 늘어놓는다 — 표를 위에서 아래로 읽으면 분포의 양 끝이 순서대로 온다.
    flagged = sorted([u for u, v in totals.items() if v < low or v > high],
                     key=lambda u: totals[u])
    return med, mad, low, high, flagged


def print_outlier_table(flagged, rates, accounts):
    """플래그가 붙은 계정을 표로 보여 준다."""
    print(f"\n      플래그 {len(flagged):,}계정")
    print("        계정          총사용률      분모     문서수")
    for uid in flagged:
        print(f"        {uid[:12]:<12}{rates[uid]['총사용률']:>10.1%}"
              f"{rates[uid]['분모']:>10,}{accounts[uid]['문서수']:>10,}")


def show_outlier_texts(flagged, rates):
    """
    플래그가 붙은 계정의 원문을 몇 건 띄운다.

    숫자만 보고는 "사용률 58%"가 문체 때문인지 데이터가 깨진 탓인지 알 수
    없다. URL만 늘어놓은 글, 같은 문장이 반복된 글, 영어가 아닌 글이 섞이면
    사용률은 얼마든지 튄다. 04가 잡을 수 없는 문제라 사람이 읽어야 한다.

    05에서 01을 여는 자리는 여기 한 곳뿐이다. 04와 똑같이 "계정" 키만 꺼내고
    라벨이 든 나머지는 즉시 버린다(del). 규율을 말로만 두지 않고 코드로 박아
    두는 것이다 — 라벨이 담긴 객체가 메모리에 남지 않으면 실수로 참조할
    수도 없다.
    """
    if not os.path.exists(ACCOUNTS_JSON):
        print(f"\n      원문 표본 건너뜀 — "
              f"{os.path.basename(ACCOUNTS_JSON)} 이(가) 없습니다.")
        print("      플래그 목록은 그대로 저장됩니다. 원문 확인만 못 합니다.")
        return

    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    docs_by_uid = data["계정"]     # ← 01에서 꺼내는 것은 이 키 하나뿐이다
    del data                       # 라벨이 든 나머지는 여기서 버린다

    shown = flagged[:OUTLIER_SHOW]
    print(f"\n      원문 표본 — {len(shown)}계정 × 최대 {SAMPLE_DOCS}건 "
          f"× {SAMPLE_CHARS}자")
    print("      (라벨은 읽지 않았다. 어느 쪽 계정인지 모르는 채로 읽는 것이다)")
    for uid in shown:
        docs = docs_by_uid.get(uid, [])
        print(f"\n      ▶ {uid[:12]}…  총사용률 {rates[uid]['총사용률']:.1%} · "
              f"분모 {rates[uid]['분모']:,} 토큰 · 문서 {len(docs)}건")
        for k, doc in enumerate(docs[:SAMPLE_DOCS], 1):
            # 줄바꿈이 든 글이 화면 구조를 흐트러뜨린다. 공백을 한 칸으로 눌러 둔다.
            flat = " ".join(doc.split())
            tail = "…" if len(flat) > SAMPLE_CHARS else ""
            print(f"         {k}) {flat[:SAMPLE_CHARS]}{tail}")

    extra = len(flagged) - len(shown)
    if extra > 0:
        print(f"\n      … 이 밖에 {extra:,}계정이 더 플래그되었다(원문 생략).")
        print("        전체 목록은 05_사용률검수.json 의 검수요약.이상치 에 있다.")


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 74)
    print("계정별 기능어 사용률 검수  (검수만 한다 — 봇/사람 비교는 06번)")
    print("=" * 74)

    # ── [1] 입력 ────────────────────────────────────────────────
    print("\n[1/5] 입력 적재")
    if not os.path.exists(MEASURE_JSON):
        print(f"      {MEASURE_JSON} 이(가) 없습니다.")
        print("      04_기능어측정.py 를 먼저 실행하십시오. 아무것도 하지 않고 끝냅니다.")
        return

    conf, accounts = load_measurement()
    inherited = inherit_fingerprint(conf)
    print(f"      계정 {len(accounts):,}개 (04 산출물, 실행일 {conf.get('실행일', '?')})")
    print(f"      04 승계 — 기능어 {inherited['기능어_개수']}종 · "
          f"해시 {inherited['기능어_해시']}")
    print("      라벨(봇/사람)은 여전히 봉인 상태다. 06에서 처음 연다.")

    # ── [2] 사용률 ──────────────────────────────────────────────
    print("\n[2/5] 사용률 계산 (분모 = 토큰수_구두점제외, 사전선언 결정 1)")
    rates, undefined = compute_rates(accounts)
    print(f"      계정 {len(rates):,}개의 단어별·전체 사용률을 냈습니다.")
    if undefined:
        print(f"      ※ 분모가 0인 계정 {len(undefined)}개는 사용률을 정의할 수 없어")
        print("        통계에서 빠집니다(분석적 제외가 아니라 나눗셈 불성립).")
        print(f"        해당 계정: {', '.join(u[:12] for u in undefined[:10])}")
        print("        01의 적격 기준상 나올 일이 아닙니다. 01을 확인하십시오.")

    check = cross_check(accounts)
    print("\n      ── 04 대비 검산 ──")
    print(f"      기능어 토큰 합       {check['기능어토큰']:>12,}")
    print(f"      토큰수(구두점 포함)  {check['토큰수']:>12,}  → "
          f"{check['비율_구두점포함']:>6.1%}  (04 로그 {EXPECT_RATIO_PUNCT:.1%})")
    print(f"      토큰수(구두점 제외)  {check['토큰수_구두점제외']:>12,}  → "
          f"{check['비율_구두점제외']:>6.1%}  (기대 약 {EXPECT_RATIO_NOPUNCT:.1%})")
    if check["일치"]:
        print(f"      두 값 모두 기댓값과 {CHECK_TOL:.1%}p 안에서 일치합니다.")
    else:
        print("\n      ■ 경고 — 04 로그의 값과 어긋납니다.")
        print("        05는 04의 숫자를 나누기만 하므로, 합계가 다르다는 것은 읽은")
        print("        파일이 04 로그를 남긴 그 파일이 아니라는 뜻입니다. 짚어 볼 곳:")
        print("         · 04_기능어측정.json 이 다른 실행분으로 바뀌지 않았는가")
        print("           (설정.실행일과 04 로그의 저장 시각을 대조하라)")
        print("         · 기능어 목록이 172종에서 바뀌지 않았는가(위 해시 확인)")
        print("         · 이 스크립트의 기댓값 상수가 옛 로그를 가리키고 있지 않은가")
        print("        계산은 계속하지만, 원인을 잡기 전에는 06으로 넘어가지 마십시오.")

    # ── [3] 분포 검수 ───────────────────────────────────────────
    print("\n[3/5] 분포 검수")
    totals = {uid: r["총사용률"] for uid, r in rates.items()}
    stat_total = summarize(list(totals.values()))
    stat_denom = summarize([r["분모"] for r in rates.values()])

    line("총 기능어 사용률 분포")
    print_stats(stat_total, lambda v: f"{v:>8.1%}")
    print(f"\n      히스토그램 ({HIST_BINS}구간)")
    print_histogram(list(totals.values()))

    print_denominator_block(rates, accounts, stat_denom)

    presence = word_presence(accounts)
    print_sparsity_block(presence, len(rates), inherited["기능어_개수"])

    # ── [4] 이상치 ──────────────────────────────────────────────
    print("\n[4/5] 이상치 플래그 (표시만 — 제외하지 않는다, 사전선언 결정 2)")
    med, mad, low, high, flagged = flag_outliers(totals)
    print(f"      중앙값 {med:.1%} · MAD {mad:.4f}")
    if mad == 0:
        print("      MAD가 0이라 경계가 한 점으로 무너집니다. 판정을 건너뜁니다.")
        print("      절반 이상의 계정이 중앙값과 정확히 같다는 뜻이라, 정상적인")
        print("      데이터라면 나올 수 없는 모양입니다. 04를 먼저 의심하십시오.")
    elif flagged:
        print(f"      경계   {low:.1%} ~ {high:.1%}   (중앙값 ± {MAD_K:g}×MAD)")
        print_outlier_table(flagged, rates, accounts)
        show_outlier_texts(flagged, rates)
    else:
        print(f"      경계   {low:.1%} ~ {high:.1%}   (중앙값 ± {MAD_K:g}×MAD)")
        print("      경계 밖 계정이 없습니다. 분포가 상당히 조밀합니다.")

    # ── [5] 저장 ────────────────────────────────────────────────
    print("\n[5/5] 저장")
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "분모_정의": "토큰수_구두점제외 (04 저장값). 사전선언 결정 1.",
            "이상치_기준": f"총사용률이 중앙값 ± {MAD_K:g}×MAD 밖. "
                        "표시만 하고 제외하지 않는다(사전선언 결정 2).",
            "라벨_사용": "없음. 01은 이상치 원문 확인을 위해 '계정' 키만 읽고 "
                      "나머지는 즉시 폐기했다. 라벨은 06에서 처음 연다(결정 4).",
            "04승계": inherited,
            "검산결과": check,
        },
        "검수요약": {
            "총사용률_통계": rounded(stat_total, RATE_DIGITS),
            "분모_통계": rounded(stat_denom, 1),
            # 희소성 표는 드문 것부터 담는다 — 파일을 열자마자 위험한 단어가 보인다.
            "희소성표": {w: n for w, n in
                      sorted(presence.items(), key=lambda kv: (kv[1], kv[0]))},
            "이상치": flagged,
            "이상치_중앙값": round(med, RATE_DIGITS),
            "이상치_MAD": round(mad, RATE_DIGITS),
            "이상치_하한": round(low, RATE_DIGITS) if low is not None else None,
            "이상치_상한": round(high, RATE_DIGITS) if high is not None else None,
            "분모0계정": undefined,
        },
        "계정": rates,
    }
    write_json(OUT_JSON, out, indent=1)
    print(f"      {OUT_JSON}")
    print(f"      {os.path.getsize(OUT_JSON):,} bytes")

    # ── 눈으로 검수할 것 ────────────────────────────────────────
    line("확인 항목")
    print("  아래를 직접 보고 나서 06번으로 넘어가십시오.")
    print("   1. 총사용률 분포가 상식적인가 — 중심이 40% 언저리에 있어야 한다.")
    print("      영어 산문에서 기능어는 대략 열 단어 중 넷이다. 중앙값이 20%나")
    print("      60%에 가 있다면 분모나 목록 어느 한쪽이 잘못된 것이다.")
    print("   2. 희소 단어 목록을 확인하라. 몇 계정에서만 나온 단어가 몇 종인가.")
    print("      그 단어들은 06에서 p값이 어떻게 나오든 해석할 것이 없다.")
    print("   3. 이상치 계정의 원문이 정상 텍스트인가. URL만 늘어놓았거나, 같은")
    print("      문장이 반복되거나, 영어가 아닌 글이 섞여 있지 않은가. 깨진")
    print("      데이터라면 그 사실을 기록해 두라 — 여기서 빼지는 않는다.")
    print("   4. 분모가 가장 작은 계정들을 보라. 이들의 사용률은 한두 번의 우연으로")
    print("      크게 흔들린다. 06 결과에서 어느 쪽 끝에 몰리는지 다시 볼 값이다.")
    print("   5. 04 대비 검산이 일치했는가. 어긋났다면 원인을 잡기 전까지 06으로")
    print("      넘어가서는 안 된다 — 05의 모든 수치가 의심스러워진다.")
    print()
    print("  이 다섯은 스크립트가 대신 판정할 수 없는 것들이다. 숫자를 늘어놓는")
    print("  일까지가 코드의 몫이고, 그 숫자가 상식적인지는 사람이 본다. 판단을")
    print("  마친 뒤 06(비교)으로 넘어가라. 라벨(봇/사람)은 06에서 처음 연다 —")
    print("  여기까지 나온 모든 수치는 어느 계정이 봇인지 모르는 채로 만들어졌고,")
    print("  그 사실이 05가 어느 쪽에도 유리하게 조정되지 않았다는 증거다.")


if __name__ == "__main__":
    main()
