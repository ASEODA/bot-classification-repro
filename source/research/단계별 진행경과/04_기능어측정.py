#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
04_기능어측정.py
────────────────────────────────────────────────────────────────────────────
목적
    적격 계정 1,869개가 "어떻게 말하는가"를 계정마다 한 벌씩 세어 저장한다.
    세기만 한다. 봇과 사람을 비교하지 않고, 비율도 만들지 않는다.

왜 세기와 비교를 갈라 놓나
    측정과 해석을 한 파일에 섞으면, 결과가 마음에 들지 않을 때 측정 쪽을
    손보고 싶어진다. 세는 규칙을 먼저 확정해 저장해 두면 그 유혹이 차단된다.
    이 파일은 라벨을 보지 않으므로, 여기서 나온 수치는 봇/사람 어느 쪽에도
    유리하게 조정될 수 없다. 비교는 05번이 이 파일을 읽어서 한다.

무엇을 세는가 (계정마다 한 벌)
    문서수 · 문장수 · 토큰수(구두점 포함 / 제외)
    기능어 목록의 출현 횟수        ← 이 연구의 주 측정치 (정규화 후 172종)
    UPOS 분포                      ← 품사 구성
    형태 자질 분포(Tense=Past 등)  ← 시제·인칭·태를 다룰 M 블록의 원재료

    파싱은 비싸다(문서 11만 건). 한 번 지나갈 때 쓸 만한 것을 다 주워 둔다.
    나중에 자질 하나가 더 필요해졌다고 전량을 다시 파싱하는 일이 없도록.

네 가지 판단 — 근거는 해당 코드 옆에 다시 적어 두었다
    1. 기능어는 '표면형'으로 센다. 품사 조건을 걸지 않는다.
    2. 아포스트로피는 곧은 것(')으로 통일해 센다. 굽은 것(’)이 원문의 37%다.
       첫 전량 측정이 이 문제를 드러내 이 규칙이 추가됐다([타이포그래피] 참조).
    3. 원카운트만 저장한다. 나눗셈(사용률)은 05번에서 한다.
    4. 라벨(봇/사람)은 읽지도, 저장하지도 않는다.

실행
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 -u 04_기능어측정.py
    필요 패키지: stanza  (03에서 확인 완료)

    이 기계 실측으로 계정 전체가 대략 1시간 안팎이다.
    (03이 잰 순차 처리는 173ms/문서 = 5.3시간이었다. 아래 [bulk 처리] 참조)

    오래 걸리는 작업이라 100계정마다 중간 저장한다.
    중간에 창을 닫아도 다시 실행하면 끝난 계정을 건너뛰고 이어서 한다.

선행 조건
    같은 폴더에 01_적격계정.json, 02_기능어목록.json 이 있어야 한다.
    영어 모델은 03에서 이미 내려받았다고 본다(여기서 다시 받지 않는다 —
    네트워크가 끊긴 자리에서도 돌아간다).

산출
    04_기능어측정.json       계정별 원카운트. 05번의 입력.
    04_기능어측정_진행.json  중간 저장 파일. 전부 끝나면 지운다.
"""

import functools
import hashlib
import json
import os
import platform
import time
from collections import Counter

# 진행 표시가 즉시 화면에 찍히게 한다.
# 파이썬은 출력을 버퍼에 모았다가 한꺼번에 내보내는 것이 기본이라, 한 시간짜리
# 작업에서는 "멈춘 것처럼" 보인다. 아래 한 줄로 이 파일의 모든 print가 즉시 나온다.
# (터미널에서 돌린다면 python3 -u 로 실행해도 같은 효과다)
print = functools.partial(print, flush=True)


# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더를 기준으로 잡는다 — 연구 폴더를 통째로 옮겨도 깨지지 않는다.
HERE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"          # 01 산출물 — "계정" 키만 쓴다
FUNCWORDS_JSON = f"{HERE}/02_기능어목록.json"        # 02 산출물 — "기능어" 키만 쓴다
OUT_JSON = f"{HERE}/04_기능어측정.json"              # 최종 산출물
PROGRESS_JSON = f"{HERE}/04_기능어측정_진행.json"    # 중간 저장(완료 시 삭제)

CHECKPOINT_EVERY = 100
# 100계정마다 중간 저장한다.
# 값을 키우면 저장 부담이 줄고 중단 시 잃는 작업이 늘어난다. 100계정이면
# 이 기계에서 3분 남짓이라, 최악의 경우에도 3분치만 다시 하면 된다.

WARMUP_ACCOUNTS = 20
# 처음 20계정을 끝낸 시점의 실측 속도로 전체 소요 시간을 추정해 알려준다.
# 03 [E]가 착수 전에 규모를 재 두었던 것과 같은 취지다. 다만 여기서는
# 이미 시작한 작업이므로, "지금 이 실행이 언제 끝나는지"를 알려주는 쪽이다.

# ── 자가검증용 문장 ─────────────────────────────────────────────
# 03 [C]에서 쓴 문장 그대로다. 기대값도 그때의 출력에서 읽은 것이다.
#   I do n't think they 've seen it , and it is n't mine .
#     → n't 두 번(don't, isn't) · 've 한 번(they've)
SELF_CHECK_TEXT = "I don't think they've seen it, and it isn't mine."
# 같은 문장의 굽은 아포스트로피(’)판도 한 벌 검사한다 — 아래 [타이포그래피] 참조.
SELF_CHECK_TEXT_CURLY = "I don’t think they’ve seen it, and it isn’t mine."
# 두 문장을 합친 기대값. 정규화가 작동해야 굽은 쪽도 곧은 키로 모인다.
SELF_CHECK_EXPECT = {"n't": 4, "'ve": 2}


# ════════════════════════════════════════════════════════════════════════
# [타이포그래피] 아포스트로피 정규화 — 곧은 것과 굽은 것
# ════════════════════════════════════════════════════════════════════════
def normalize_apostrophe(s):
    """
    굽은 아포스트로피(’, U+2019)를 곧은 것(', U+0027)으로 바꾼다.

    왜 필요한가 — 첫 전량 측정(2026-08-23)이 스스로 드러낸 문제다.
    측정 요약의 상위 20에 's(41,381회)와 ’s(24,845회)가 따로 올라왔다.
    같은 말이 글자 모양 때문에 두 칸에 나뉜 것이다. 원문을 전수로 세어 보니
    아포스트로피의 37%가 굽은 쪽이었다(40,103 / 106,968).

    더 나쁜 쪽은 조용히 사라진 경우다. 02 목록에는 굽은 변종이 n’t와 ’s만
    있다 — UD 코퍼스에서 빈도 5를 넘은 것만 살아남은, 자의적인 절단선이다.
    그래서 they’ve의 ’ve, it’ll의 ’ll, we’re의 ’re, I’m의 ’m, you’d의 ’d는
    목록의 어느 항목과도 일치하지 않아 0으로 세어졌다. 오류 메시지는 없었다.

    고치지 않으면 안 되는 이유: 글자 모양은 쓴 도구를 따라간다. 굽은
    따옴표는 iOS 자판·워드프로세서, 그리고 LLM 출력이 즐겨 쓴다. 도구가
    라벨(봇/사람)과 상관될 수 있으므로, 타이포그래피를 방치하면 "봇이
    축약형을 덜 쓴다"처럼 보이는 가짜 신호를 만들 수 있다.

    범위는 U+2019 하나다. 유사 문자를 원문에서 전수 조사한 결과 —
    U+2018(‘) 3,453회는 여는 따옴표 용법(n‘t 꼴 1회뿐), U+02BC·U+02BB 0회,
    U+00B4 17회 — 정규화할 이유가 없다.

    토큰과 02 목록 '양쪽에' 같은 정규화를 적용한다. 잣대가 하나여야 한다.
    """
    return s.replace("’", "'")


def line(title=""):
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


def fmt_dur(sec):
    """초를 사람이 읽는 단위로 바꾼다."""
    if sec < 90:
        return f"{sec:.0f}초"
    if sec < 5400:
        return f"{sec / 60:.1f}분"
    return f"{sec / 3600:.2f}시간"


def write_json(path, obj, indent=None):
    """
    JSON을 안전하게 쓴다.

    임시 파일에 먼저 쓰고 나서 이름을 바꿔치기한다(os.replace).
    중간 저장 파일을 쓰는 도중에 창을 닫으면 파일이 반쯤 잘린 채 남고,
    다음 실행에서 그 파일을 읽다 깨진다. 이름 바꾸기는 쪼개지지 않는
    연산이라, 어느 시점에 멈춰도 파일은 '이전 것' 아니면 '새 것'이다.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


# ════════════════════════════════════════════════════════════════════════
# [1] 입력 적재 — 여기서 라벨을 읽지 않는다
# ════════════════════════════════════════════════════════════════════════
def load_inputs():
    """
    01에서 계정별 문서를, 02에서 기능어 목록을 가져온다.

    01 파일 안에는 "라벨"(봇/사람) 키가 함께 들어 있다. 이 단계에서는
    "계정" 키만 꺼내고 나머지는 즉시 버린다(del). 규율을 말로만 두지 않고
    코드로 박아 두는 것이다 — 라벨이 담긴 객체 자체가 메모리에 남지 않으면
    실수로 참조할 수도 없다.

    왜 이렇게까지 하나: 측정 단계에서 라벨을 한 번이라도 보면, 그 뒤로는
    "봇이 잘 잡히는 쪽으로 규칙을 고르지 않았다"는 것을 증명할 방법이 없다.
    01이 적격 판정에 라벨을 쓰지 않은 것과 같은 이유다.
    """
    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    accounts = data["계정"]          # ← 01에서 꺼내는 것은 이 키 하나뿐이다
    del data                          # 라벨이 든 나머지는 여기서 버린다

    funcwords = json.load(open(FUNCWORDS_JSON, encoding="utf-8"))["기능어"]
    # 02 목록에도 토큰과 같은 정규화를 적용한다. 굽은 변종(n’t·’s·’)이 곧은
    # 항목과 합쳐져 174종이 172종이 된다. [타이포그래피] 참조.
    funcwords = sorted({normalize_apostrophe(w) for w in funcwords})
    return accounts, funcwords


def input_fingerprint(accounts, funcwords):
    """
    입력이 무엇이었는지 짧게 요약한 지문을 만든다.

    쓸모: 중간 저장 파일을 이어받을 때 "그때의 입력과 지금의 입력이 같은가"를
    확인한다. 02를 다시 돌려 목록이 174종에서 180종으로 바뀌었는데 앞의
    900계정 결과를 그대로 이어 붙이면, 한 파일 안에 기준이 다른 수치가
    섞인다. 눈으로는 절대 못 잡는 종류의 오염이다.
    """
    h = hashlib.sha256("\n".join(funcwords).encode("utf-8")).hexdigest()[:16]
    return {
        "기능어_해시": h,
        "기능어_개수": len(funcwords),
        "정규화": "아포스트로피 U+2019→U+0027",   # 세는 규칙도 지문의 일부다
        "계정수": len(accounts),
        "문서수": sum(len(v) for v in accounts.values()),
    }


# ════════════════════════════════════════════════════════════════════════
# [2] 파이프라인 — 03에서 감사한 것과 같은 구성
# ════════════════════════════════════════════════════════════════════════
def build_pipeline():
    """
    03이 감사한 그 파이프라인을 그대로 만든다.

        processors="tokenize,pos" · use_gpu=False

    한 글자라도 다르게 만들면 03의 감사 결과("봇 글과 사람 글에서 파서가
    비슷하게 작동한다")가 이 측정에 적용되지 않는다. 감사한 도구와 측정에
    쓴 도구가 같아야 감사가 의미를 갖는다.

    stanza.download를 부르지 않는다. 03이 이미 모델을 ~/stanza_resources에
    받아 두었고, download는 매번 인터넷으로 목록 파일을 확인하러 나간다.
    """
    import stanza
    print("[준비] 파이프라인 생성 중...")
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos",
                          verbose=False, use_gpu=False)
    print("[준비] 완료")
    return nlp


# ════════════════════════════════════════════════════════════════════════
# [3] 계정 하나를 재는 함수 — 이 파일의 심장
# ════════════════════════════════════════════════════════════════════════
def measure_account(nlp, docs, funcword_set):
    """
    한 계정의 문서 전부를 파싱해 원카운트 한 벌을 만든다.

    ── bulk 처리로 파싱한다 ────────────────────────────────────────
    문서를 하나씩 nlp(text)로 넘기면 03 실측 173ms/문서, 전량 5.3시간이다.
    느린 이유는 계산량이 아니라 호출 비용이다 — 문서마다 신경망을 한 번씩
    깨워 아주 작은 입력을 밀어 넣는다. bulk_process는 문서 목록을 받아
    내부에서 묶어 처리하므로 그 비용이 분산된다(이 기계 실측 34ms/문서).

    문서 경계는 그대로 보존된다. 입력 문서 N건에 결과 Document도 N개가
    1:1로 돌아온다(작성 시 stanza 1.14.0에서 확인). 계정 단위로 묶는 이유도
    여기 있다 — 계정당 10~200건이라 묶음 크기로 적당하고, 계정 경계에서
    끊기니 중간 저장 지점과도 자연스럽게 맞는다.

    ── 기능어는 '표면형'으로 센다 ──────────────────────────────────
    소문자로 바꾸고 아포스트로피를 정규화한 표면형이 02의 목록(같은 정규화
    적용, 172종)에 있으면 센다. 그 자리에서 파서가 붙인 품사는 보지 않는다.

    왜 품사 조건을 걸지 않나. 두 가지다.
      · 저자 판별 연구의 오랜 관행이 표면형 빈도다. 같은 방식으로 재야
        선행 연구 수치와 견줄 수 있다.
      · 더 중요한 이유 — 03 [D]가 걱정한 것이 "봇 글과 사람 글에서 파서
        오류율이 다르면 어쩌나"였다. 품사를 조건으로 걸면 그 오류가
        측정치에 그대로 들어온다. 표면형만 보면 파서에게 맡기는 일이
        토큰 나누기 하나로 줄어드는데, 토큰화는 품사 태깅보다 훨씬 안정적인
        부분이다(그리고 그 토큰화가 제대로 되는지는 아래 self_check가 본다).

    대안이었던 "닫힌 어류로 태그됐을 때만 센다"를 이 이유로 기각했다.

    ── 원카운트만 저장한다 ────────────────────────────────────────
    사용률(= 횟수 / 총 토큰)을 여기서 계산하지 않는다. 분모를 무엇으로 할지는
    아직 정해지지 않은 문제다 — 구두점을 포함한 토큰수인지, 뺀 것인지,
    문서당 평균을 먼저 낼 것인지. 원카운트와 분모 후보를 모두 저장해 두면
    05에서 어떤 정규화든 다시 해 볼 수 있다. 반대로 비율만 저장하면 되돌릴 수 없다.

    반환값의 카운트는 0을 담지 않는다(희소 저장). 174종을 계정마다 다 적으면
    대부분이 0인 표가 되고 파일만 커진다. 없는 키 = 0으로 읽으면 된다.
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


# ════════════════════════════════════════════════════════════════════════
# [4] 자가검증 — 측정에 들어가기 전 매번 확인한다
# ════════════════════════════════════════════════════════════════════════
def self_check(nlp, funcword_set):
    """
    02의 목록과 stanza의 토큰화가 서로 맞물리는지 확인한다.

    왜 매 실행마다 보나. 02 목록은 UD 분해형 규약을 따른다 — 목록에 don't가
    아니라 do와 n't가 따로 들어 있다. 이 규약은 stanza가 실제로 축약형을
    쪼개 줄 때만 맞는다. 만약 어떤 이유로 쪼개지 않게 되면(모델 교체, 버전
    변경, 파이프라인 구성 실수) don't는 목록의 어느 항목과도 일치하지 않아
    조용히 0으로 세어진다. 오류 메시지는 나오지 않는다. 부정 표현이 통째로
    사라진 표를 가지고 몇 시간을 돌린 뒤에야 알게 된다.

    검사는 본 측정과 똑같은 함수(measure_account)를 부른다. 검사만 통과하고
    본 측정은 다른 경로로 가는 일이 없게 하려는 것이다.

    통과하면 True, 아니면 화면에 원인을 적고 False.
    """
    line("[자가검증] 축약형이 기능어로 잡히는가 — 곧은 것과 굽은 것 모두")
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

    if not ok:
        print()
        print("■ 중단 — 자가검증 실패")
        print("  02 기능어 목록과 stanza 토큰화가 어긋나 있습니다.")
        print("  짚어 볼 곳:")
        print("   · stanza 버전이나 영어 모델이 03 실행 때와 달라졌는가")
        print("     (03_설치확인_기록.json의 '환경' 항목과 대조)")
        print("   · 02_기능어목록.json이 분해형이 아닌 목록으로 바뀌었는가")
        print("   · 아포스트로피 정규화(normalize_apostrophe)가 토큰과 목록")
        print("     양쪽에 똑같이 적용되고 있는가")
        print("   · 파이프라인 구성(tokenize,pos)이 바뀌었는가")
        print("  이 상태로 측정하면 부정 표현(n't)이 통째로 빠진 표가 나옵니다.")
        print("  원인을 잡은 뒤 다시 실행하십시오.")
    return ok


# ════════════════════════════════════════════════════════════════════════
# [5] 중간 저장 / 이어서 하기
# ════════════════════════════════════════════════════════════════════════
def load_progress():
    """중간 저장 파일이 있으면 읽어 준다. 없으면 None."""
    if not os.path.exists(PROGRESS_JSON):
        return None
    return json.load(open(PROGRESS_JSON, encoding="utf-8"))


def save_progress(done, fingerprint, elapsed_total):
    """
    지금까지 끝낸 계정을 통째로 저장한다.

    끝난 계정만 담고 남은 계정 목록은 담지 않는다. 다음 실행이 01을 다시
    읽어 "저장된 것에 없는 계정"을 남은 일로 계산하므로, 목록을 두 벌
    관리하다 어긋나는 일이 없다.

    들여쓰기 없이 쓴다 — 이 파일은 수십 번 다시 쓰이는 작업용이다.
    """
    write_json(PROGRESS_JSON, {
        "안내": "04번의 중간 저장 파일입니다. 측정이 끝나면 자동으로 지워집니다.",
        "지문": fingerprint,
        "완료계정수": len(done),
        "누적소요초": round(elapsed_total, 1),
        "저장시각": time.strftime("%Y-%m-%d %H:%M:%S"),
        "계정": done,
    })


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 74)
    print("계정별 기능어·품사·형태자질 측정  (측정만 한다 — 비교는 05번)")
    print("=" * 74)

    # ── 이미 끝난 작업인가 ──────────────────────────────────────
    if os.path.exists(OUT_JSON):
        prev = json.load(open(OUT_JSON, encoding="utf-8"))
        print("최종 산출물이 이미 있습니다. 아무것도 하지 않고 끝냅니다.")
        print(f"  파일   {OUT_JSON}")
        print(f"  크기   {os.path.getsize(OUT_JSON):,} bytes")
        print(f"  실행일 {prev.get('설정', {}).get('실행일', '?')}")
        print(f"  계정   {len(prev.get('계정', {})):,}개")
        print()
        print("  다시 측정하려면 이 파일을 다른 이름으로 옮기거나 지운 뒤 실행하십시오.")
        print("  (덮어쓰기를 막아 둔 것은, 한 시간짜리 측정 결과를 실수로 날리는 일이")
        print("   생각보다 자주 일어나기 때문입니다)")
        return

    # ── 입력 ────────────────────────────────────────────────────
    print("\n[1/5] 입력 적재")
    accounts, funcwords = load_inputs()
    funcword_set = set(funcwords)
    fp = input_fingerprint(accounts, funcwords)
    print(f"      계정 {fp['계정수']:,}개 · 문서 {fp['문서수']:,}건 (01)")
    print(f"      기능어 {fp['기능어_개수']}종 (02)")
    print("      라벨(봇/사람)은 읽지 않았습니다 — 측정이 끝날 때까지 쓰지 않습니다.")

    # ── 도구 ────────────────────────────────────────────────────
    print("\n[2/5] 파이프라인 준비")
    nlp = build_pipeline()

    # bulk 처리 API 확인. 이 스크립트가 5시간이 아니라 1시간인 이유가 여기 있다.
    if not hasattr(nlp, "bulk_process"):
        print()
        print("■ 중단 — 이 stanza 버전에는 bulk_process가 없습니다.")
        print("  작성 시점(stanza 1.14.0)에는 존재를 확인했습니다.")
        print("  대안: measure_account의 nlp.bulk_process(docs) 자리를")
        print("        nlp([stanza.Document([], text=d) for d in docs]) 로 바꾸면")
        print("        같은 효과를 냅니다(문서 목록을 한 번에 넘기는 방식).")
        return

    # ── 자가검증 ────────────────────────────────────────────────
    print("\n[3/5] 자가검증")
    if not self_check(nlp, funcword_set):
        return

    # ── 이어서 할 것 정리 ───────────────────────────────────────
    print("\n[4/5] 진행 상황 확인")
    done, prev_sec = {}, 0.0
    prog = load_progress()
    if prog:
        if prog.get("지문") != fp:
            print("■ 중단 — 중간 저장 파일과 지금의 입력이 다릅니다.")
            print(f"  저장 당시: {prog.get('지문')}")
            print(f"  지금:      {fp}")
            print("  01이나 02를 다시 돌려 입력이 바뀐 것으로 보입니다.")
            print("  기준이 다른 수치를 이어 붙이면 한 파일 안에 서로 다른 잣대가")
            print("  섞이고, 나중에 눈으로는 찾을 수 없습니다.")
            print(f"  → {PROGRESS_JSON} 을(를) 지우고 처음부터 다시 실행하십시오.")
            return
        done = prog["계정"]
        prev_sec = prog.get("누적소요초", 0.0)
        print(f"      중간 저장을 찾았습니다 — 완료 {len(done):,}계정 "
              f"(그때까지 {fmt_dur(prev_sec)})")
        print("      끝난 계정은 건너뛰고 이어서 합니다.")
    else:
        print("      중간 저장 없음. 처음부터 시작합니다.")

    # 계정 순서를 uid 오름차순으로 고정한다.
    # 실행할 때마다 순서가 달라지면 "몇 번째까지 했다"는 말이 뜻을 잃고,
    # 중간 저장을 이어받은 결과가 실행 순서에 따라 달라질 여지가 생긴다.
    todo = [uid for uid in sorted(accounts) if uid not in done]
    todo_docs = sum(len(accounts[uid]) for uid in todo)
    print(f"      남은 계정 {len(todo):,}개 · 문서 {todo_docs:,}건")

    if not todo:
        print("      남은 계정이 없습니다. 최종본만 정리합니다.")

    # ── 본 측정 ─────────────────────────────────────────────────
    print("\n[5/5] 측정 시작")
    print(f"      {CHECKPOINT_EVERY}계정마다 중간 저장합니다. 창을 닫아도 됩니다.")
    n_total = fp["계정수"]
    t_run = time.time()
    docs_run = 0

    for i, uid in enumerate(todo, 1):
        docs = accounts[uid]
        done[uid] = measure_account(nlp, docs, funcword_set)
        docs_run += len(docs)

        # 처음 WARMUP_ACCOUNTS 계정의 실측 속도로 이 실행의 끝을 추정한다.
        # 계정당 문서 수가 10~200건으로 제각각이라 '계정당 평균'으로 환산하면
        # 큰 계정이 몰린 구간에서 크게 빗나간다. 문서당 속도로 환산한다.
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
            print(f"         (03이 잰 순차 처리는 173 ms/문서였다. "
                  f"묶음 처리로 몇 배가 줄었는지 보라)")
            print()

        if i % CHECKPOINT_EVERY == 0:
            el = time.time() - t_run
            save_progress(done, fp, prev_sec + el)
            per_doc = el / docs_run
            left = (todo_docs - docs_run) * per_doc
            print(f"      {len(done):,}/{n_total:,} 계정 · "
                  f"경과 {fmt_dur(el)} · 잔여 추정 {fmt_dur(left)} · 저장 완료")

    run_sec = time.time() - t_run
    total_sec = prev_sec + run_sec
    print(f"      {len(done):,}/{n_total:,} 계정 완료 · 이번 실행 {fmt_dur(run_sec)}")

    # ── 최종 저장 ───────────────────────────────────────────────
    import stanza
    import torch

    scale = {
        "계정수": len(done),
        "문서수": sum(a["문서수"] for a in done.values()),
        "문장수": sum(a["문장수"] for a in done.values()),
        "토큰수": sum(a["토큰수"] for a in done.values()),
        "토큰수_구두점제외": sum(a["토큰수_구두점제외"] for a in done.values()),
    }
    out = {
        "설정": {
            "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.machine()}",
            "stanza": stanza.__version__,
            "torch": torch.__version__,
            "파이프라인": "tokenize,pos (use_gpu=False, bulk_process 계정 단위)",
            "기능어_출처": os.path.basename(FUNCWORDS_JSON),
            "기능어_개수": fp["기능어_개수"],
            "기능어_비고": "02 원본 174종이 아포스트로피 정규화로 172종이 됨(n’t·’s·’가 곧은 항목과 병합)",
            "기능어_해시": fp["기능어_해시"],
            "카운트_기준": "소문자+아포스트로피 정규화(’→') 표면형이 같은 정규화를 거친 기능어 목록에 있으면 1회. 품사 조건 없음.",
            "저장값": "원카운트. 비율·정규화는 05번에서 계산한다.",
            "라벨_사용": "없음. 01의 '라벨' 키를 읽지 않았다.",
            "처리규모": scale,
            "총소요초": round(total_sec, 1),
        },
        # uid 오름차순으로 담는다 — 다시 돌려도 파일 순서가 같아야 비교가 쉽다.
        "계정": {uid: done[uid] for uid in sorted(done)},
    }
    write_json(OUT_JSON, out, indent=1)
    if os.path.exists(PROGRESS_JSON):
        os.remove(PROGRESS_JSON)   # 최종본이 생겼으므로 중간 저장은 역할이 끝났다

    # ── 요약 (전체 합계 — 라벨 구분 없음) ───────────────────────
    fw_all, upos_all, feats_all = Counter(), Counter(), Counter()
    for a in done.values():
        fw_all.update(a["기능어"])
        upos_all.update(a["UPOS"])
        feats_all.update(a["자질"])
    fw_tokens = sum(fw_all.values())

    line("측정 요약 — 전체 합계 (봇/사람 구분 없음)")
    print(f"  계정                {scale['계정수']:>12,}")
    print(f"  문서                {scale['문서수']:>12,}")
    print(f"  문장                {scale['문장수']:>12,}")
    print(f"  토큰(구두점 포함)    {scale['토큰수']:>12,}")
    print(f"  토큰(구두점 제외)    {scale['토큰수_구두점제외']:>12,}")
    print(f"  기능어 토큰          {fw_tokens:>12,}   "
          f"전체 토큰의 {fw_tokens / scale['토큰수']:.1%}")
    print(f"  계정당 평균 토큰      {scale['토큰수'] / scale['계정수']:>12,.0f}")
    print(f"  나타난 기능어 종류    {len(fw_all):>12,} / {fp['기능어_개수']}종")

    print("\n  기능어 상위 20 (전체 합계)")
    top = fw_all.most_common(20)
    for k in range(0, len(top), 5):
        print("    " + "   ".join(f"{w}:{n:,}" for w, n in top[k:k + 5]))

    print("\n  UPOS 분포")
    for pos, n in upos_all.most_common():
        print(f"    {pos:<8}{n:>12,}  {n / scale['토큰수']:>6.1%}")

    print("\n  형태 자질 상위 15")
    for kv, n in feats_all.most_common(15):
        print(f"    {kv:<22}{n:>12,}")

    # ── 눈으로 검수할 것 ────────────────────────────────────────
    line("확인 항목")
    print("  아래를 직접 보고 나서 05번으로 넘어가십시오.")
    print("   1. 기능어 상위가 the/to/i/and/of 같은 상식적인 단어인가.")
    print("      엉뚱한 단어가 위에 있으면 토큰화나 목록을 의심하라.")
    print("   2. n't·'ve·'s 같은 분해형이 상위 목록에 실제로 보이는가.")
    print("      자가검증은 통과했어도 실제 데이터에서 0에 가깝다면 이상한 것이다.")
    print("   3. 기능어 비율이 상식적인 자리에 있는가.")
    print("      03 감사 표본의 닫힌 어류 비율은 사람 42%·봇 39%였다. 기준이")
    print("      달라(그쪽은 품사, 이쪽은 표면형 목록) 같을 수는 없지만,")
    print("      자릿수가 아예 다르면 어딘가 잘못된 것이다.")
    print("   4. 나타난 기능어 종류가 목록 종수(172)에 크게 못 미치지 않는가.")
    print("      한 번도 안 나온 단어가 많다면 05의 비교에서 잡음이 된다.")

    line("다음 단계")
    print("  05는 이 파일을 읽어 분포부터 눈으로 검수한다.")
    print("  계정별 기능어 사용률이 어떻게 퍼져 있는지, 이상치가 있는지,")
    print("  거의 안 쓰이는 단어가 얼마나 되는지를 먼저 본다.")
    print("  봇/사람 비교는 그 검수를 마친 뒤에 시작한다 — 라벨은 그때")
    print("  01에서 처음 꺼낸다.")
    print()
    print(f"  저장 완료: {OUT_JSON}")
    print(f"             {os.path.getsize(OUT_JSON):,} bytes · "
          f"총 소요 {fmt_dur(total_sec)}")


if __name__ == "__main__":
    main()
