#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
02_기능어목록_생성.py
────────────────────────────────────────────────────────────────────────────
목적
    이 연구에서 쓸 "영어 기능어 목록"을 만든다.
    단, 사람이 임의로 고르지 않는다. 공개된 표준 자료에서 기계적으로 추출한다.

왜 이렇게 하나 — 배경
    영어에는 한국의 국립국어원 같은 국가 언어 규범 기관이 없다. 그래서 "공인
    기능어 목록"이라는 것 자체가 존재하지 않고, 논문마다 목록이 다르다.
    출처 없는 목록을 쓰면 "그 목록은 누가 정한 것이냐"에 답할 수 없다.

    대신 영어 기능어는 목록이 아니라 **문법 범주**로 정의된다.
    새 단어가 거의 생기지 않는 품사(닫힌 어류, closed class)가 곧 기능어다.
      - 전치사, 조동사, 접속사, 한정사, 대명사, 불변화사
    반대로 명사·동사·형용사·부사는 새 단어가 계속 생긴다(열린 어류).

    Universal Dependencies(UD)는 이 구분을 국제 표준 품사 태그로 명시하고,
    사람이 직접 주석을 단 코퍼스(트리뱅크)를 공개한다.
    이 파일은 그 트리뱅크에서 닫힌 어류 단어를 그대로 긁어온다.
    → 목록의 출처가 "우리"가 아니라 "UD 표준 + 사람 주석 코퍼스"가 된다.

자료
    UD English Web Treebank (EWT)
    웹 텍스트(블로그·뉴스그룹·이메일·리뷰·Q&A)에 사람이 품사를 단 코퍼스.
    장르가 SNS 텍스트와 가까워 이 연구에 적합하다.
    https://github.com/UniversalDependencies/UD_English-EWT

    ※ 통계 모델(품사 태거)을 쓰지 않는 이유:
       태거는 추정치이고 버전마다 결과가 달라진다. 트리뱅크는 사람이 단 정답
       주석이라 재현성이 더 높고, 별도 패키지 설치도 필요 없다.

실행
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 02_기능어목록_생성.py
    필요 패키지: 없음 (표준 라이브러리만 사용)

    처음 실행하면 코퍼스 파일 3개(약 19MB)를 내려받아 캐시 폴더에 저장한다.
    두 번째부터는 캐시를 쓰므로 네트워크가 필요 없다.

산출
    02_기능어목록.json  — 단어 목록 + 출처 정보 + 각 단어의 품사 근거
    화면에는 품사별로 어떤 단어가 뽑혔는지 전부 출력한다(눈으로 검수용).
"""

import json
import os
import urllib.request
from collections import Counter, defaultdict

# ════════════════════════════════════════════════════════════════════════
# [경로]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더를 기준으로 잡는다 — 연구 폴더를 통째로 옮겨도 깨지지 않는다.
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = f"{HERE}/02_UD캐시"          # 내려받은 코퍼스 원본을 두는 곳
OUT_JSON = f"{HERE}/02_기능어목록.json"   # 이 스크립트의 산출물

# UD English-EWT 원본 파일 3종(학습/검증/평가 분할).
# 우리는 학습용으로 쓰는 게 아니라 단어 목록을 뽑는 게 목적이므로 셋 다 합쳐 쓴다.
UD_BASE = "https://raw.githubusercontent.com/UniversalDependencies/UD_English-EWT/master"
UD_FILES = ["en_ewt-ud-train.conllu", "en_ewt-ud-dev.conllu", "en_ewt-ud-test.conllu"]


# ════════════════════════════════════════════════════════════════════════
# [설정] 판단 기준 — 이 3개가 목록을 결정한다
# ════════════════════════════════════════════════════════════════════════

CLOSED_CLASS = {
    "ADP",    # 전치사·후치사   in, on, of, at, to(전치사), with ...
    "AUX",    # 조동사          is, was, have, will, can, must ...
    "CCONJ",  # 등위접속사      and, but, or ...
    "SCONJ",  # 종속접속사      if, because, although, while ...
    "DET",    # 한정사          the, a, this, some, every ...
    "PRON",   # 대명사          i, you, he, it, they, who, myself ...
    "PART",   # 불변화사        not, n't, to(부정사 표지), 's(소유격) ...
}
# UD가 닫힌 어류로 분류하는 품사는 위 7개에 NUM(수사)이 더 있다.
# NUM은 일부러 뺐다. 숫자는 주제에 따라 크게 달라지고(가격·연도·통계),
# 이 연구의 목표가 "주제와 무관한 특성"이라 주제 의존 요소를 미리 배제한다.

MIN_FREQ = 5
# 트리뱅크 안에서 이 횟수 미만으로만 나온 단어는 버린다.
# 이유: 오탈자, 특이한 축약, 외국어 조각이 한두 번 섞여 들어오는 것을 거른다.
# 값이 클수록 목록이 짧고 안정적이며, 작을수록 길고 잡음이 는다.

DOMINANT_RATIO = 0.50
# 한 단어가 여러 품사로 쓰일 때의 판단 기준.
# 예: "like"는 동사(VERB)로도 전치사(ADP)로도 쓰인다. "that"은 대명사·한정사·접속사다.
# 그 단어가 쓰인 전체 횟수 중 닫힌 어류로 태그된 비율이 이 값 이상이어야 채택한다.
# 0.50 = "주로 기능어로 쓰이는 단어만 넣는다"는 뜻.
# (이 기준이 없으면 "like" 같은 단어가 들어와 내용어가 섞인다)


# ════════════════════════════════════════════════════════════════════════
# [1단계] 코퍼스 내려받기 (최초 1회)
# ════════════════════════════════════════════════════════════════════════
def ensure_corpus():
    """UD 코퍼스 파일이 캐시에 없으면 내려받는다. 있으면 그대로 쓴다."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    paths = []
    for fname in UD_FILES:
        path = f"{CACHE_DIR}/{fname}"
        if os.path.exists(path):
            print(f"      캐시 사용: {fname} ({os.path.getsize(path):,} bytes)")
        else:
            url = f"{UD_BASE}/{fname}"
            print(f"      내려받는 중: {fname} ...", end=" ", flush=True)
            urllib.request.urlretrieve(url, path)
            print(f"완료 ({os.path.getsize(path):,} bytes)")
        paths.append(path)
    return paths


# ════════════════════════════════════════════════════════════════════════
# [2단계] 품사 주석 읽기
# ════════════════════════════════════════════════════════════════════════
def read_conllu(paths):
    """
    CoNLL-U 형식 파일에서 (단어, 품사) 쌍을 모두 꺼낸다.

    CoNLL-U는 한 줄에 한 단어를 두고 탭으로 열을 나눈 형식이다.
        1열 = 번호, 2열 = 단어 표면형, 4열 = UD 품사(UPOS)
    빈 줄은 문장 경계, #으로 시작하는 줄은 주석이라 건너뛴다.
    번호에 '-'나 '.'이 들어간 줄은 복합어 분해 정보라 중복 계산을 피하려 건너뛴다.
      (예: "don't"가 1-2번으로 묶이고 1=do, 2=n't로 따로 나온다)
    """
    counts = defaultdict(Counter)   # {단어: Counter({품사: 횟수})}
    n_tokens = 0
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                cols = line.split("\t")
                if len(cols) < 4:
                    continue
                idx, form, _lemma, upos = cols[0], cols[1], cols[2], cols[3]
                if "-" in idx or "." in idx:      # 복합어 묶음 줄 건너뛰기
                    continue
                word = form.lower().strip()
                if not word:
                    continue
                counts[word][upos] += 1
                n_tokens += 1
    return counts, n_tokens


# ════════════════════════════════════════════════════════════════════════
# [3단계] 닫힌 어류 단어 선별
# ════════════════════════════════════════════════════════════════════════
def select_function_words(counts):
    """
    설정된 3개 기준(CLOSED_CLASS / MIN_FREQ / DOMINANT_RATIO)을 적용해
    기능어 목록을 만든다.

    반환:
      selected  {단어: {"총빈도":n, "닫힌어류비율":r, "대표품사":tag, "품사분포":{...}}}
      rejected  탈락 사유별 집계
    """
    selected = {}
    rejected = Counter()

    for word, pos_counter in counts.items():
        total = sum(pos_counter.values())

        # 기준 1 — 최소 빈도
        if total < MIN_FREQ:
            rejected["빈도 미달"] += 1
            continue

        # 기준 2 — 닫힌 어류 비율
        closed_n = sum(n for pos, n in pos_counter.items() if pos in CLOSED_CLASS)
        ratio = closed_n / total
        if ratio < DOMINANT_RATIO:
            # 닫힌 어류로 한 번도 안 쓰인 단어와, 가끔만 그렇게 쓰인 단어를 구분해 센다
            rejected["열린 어류 우세" if closed_n else "닫힌 어류 아님"] += 1
            continue

        # 대표 품사 = 닫힌 어류 중 가장 많이 태그된 것 (설명·검수용)
        closed_only = {pos: n for pos, n in pos_counter.items() if pos in CLOSED_CLASS}
        main_pos = max(closed_only, key=closed_only.get)

        selected[word] = {
            "총빈도": total,
            "닫힌어류비율": round(ratio, 3),
            "대표품사": main_pos,
            "품사분포": dict(pos_counter.most_common()),
        }

    return selected, rejected


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("기능어 목록 생성 — UD English Web Treebank 닫힌 어류 추출")
    print("=" * 70)
    print(f"기준: 품사 {sorted(CLOSED_CLASS)}")
    print(f"      최소 빈도 {MIN_FREQ}회 이상 / 닫힌 어류 비율 {DOMINANT_RATIO:.0%} 이상")
    print(f"      (NUM 수사는 주제 의존성 때문에 제외)")
    print()

    print("[1/3] 코퍼스 준비")
    paths = ensure_corpus()

    print("[2/3] 품사 주석 읽는 중...")
    counts, n_tokens = read_conllu(paths)
    print(f"      토큰 {n_tokens:,}개 / 단어형 {len(counts):,}종")

    print("[3/3] 닫힌 어류 선별 중...")
    selected, rejected = select_function_words(counts)

    # ── 탈락 집계 ───────────────────────────────────────────────
    print()
    print("─" * 70)
    print("선별 결과")
    print("─" * 70)
    for reason, n in rejected.most_common():
        print(f"  탈락 · {reason:<16} {n:>7,}종")
    print(f"  채택                    {len(selected):>7,}종")

    # ── 품사별 목록 전체 출력 (눈으로 검수하라고 전부 찍는다) ──
    by_pos = defaultdict(list)
    for word, info in selected.items():
        by_pos[info["대표품사"]].append((info["총빈도"], word))

    POS_KR = {
        "ADP": "전치사", "AUX": "조동사", "CCONJ": "등위접속사",
        "SCONJ": "종속접속사", "DET": "한정사", "PRON": "대명사",
        "PART": "불변화사",
    }
    print()
    print("─" * 70)
    print("채택된 단어 (품사별, 빈도순)")
    print("─" * 70)
    for pos in sorted(by_pos, key=lambda p: -len(by_pos[p])):
        words = [w for _, w in sorted(by_pos[pos], reverse=True)]
        print(f"\n[{pos} · {POS_KR.get(pos, pos)}] {len(words)}종")
        # 한 줄에 10개씩 끊어 출력
        for i in range(0, len(words), 10):
            print("  " + "  ".join(words[i:i + 10]))

    # ── 경계 사례 표시 ──────────────────────────────────────────
    # 닫힌 어류 비율이 애매한(0.5~0.8) 단어들. 기준을 바꾸면 들락날락하는 단어라
    # 따로 보여준다. 검수 시 여기를 먼저 보면 된다.
    borderline = sorted(
        ((info["닫힌어류비율"], w) for w, info in selected.items()
         if info["닫힌어류비율"] < 0.8),
        key=lambda x: x[0])
    if borderline:
        print()
        print("─" * 70)
        print(f"경계 사례 — 닫힌 어류 비율 80% 미만 ({len(borderline)}종)")
        print("기준(DOMINANT_RATIO)을 조금만 바꿔도 포함 여부가 뒤집히는 단어들이다.")
        print("─" * 70)
        for ratio, w in borderline:
            dist = selected[w]["품사분포"]
            top = ", ".join(f"{p}:{n}" for p, n in list(dist.items())[:4])
            print(f"  {w:<14} 닫힌비율 {ratio:.2f}  ({top})")

    # ── 저장 ────────────────────────────────────────────────────
    out = {
        "출처": {
            "코퍼스": "Universal Dependencies English Web Treebank (UD_English-EWT)",
            "주소": "https://github.com/UniversalDependencies/UD_English-EWT",
            "사용파일": UD_FILES,
            "주석": "사람이 직접 단 품사 주석(gold standard). 통계 태거 미사용.",
        },
        "기준": {
            "닫힌어류_품사": sorted(CLOSED_CLASS),
            "NUM_제외_사유": "숫자는 주제 의존적이라 '주제 무관 특성' 연구에 부적합",
            "최소빈도": MIN_FREQ,
            "닫힌어류_최소비율": DOMINANT_RATIO,
        },
        "집계": {
            "코퍼스_토큰수": n_tokens,
            "코퍼스_단어형수": len(counts),
            "채택_단어수": len(selected),
            "탈락_사유별": dict(rejected),
        },
        # 단어 목록. 다음 단계(기능어 빈도 측정)는 이 키만 쓰면 된다.
        "기능어": sorted(selected.keys()),
        # 각 단어가 왜 뽑혔는지의 근거. 검수·논문 부록용.
        "근거": selected,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print()
    print(f"저장 완료: {OUT_JSON}")
    print(f"기능어 {len(selected)}종. 다음 단계(03_기능어빈도)의 입력이다.")


if __name__ == "__main__":
    main()
