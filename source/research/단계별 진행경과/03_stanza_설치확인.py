#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
03_stanza_설치확인.py
────────────────────────────────────────────────────────────────────────────
목적
    Stanza가 영어 텍스트를 UD 기준으로 제대로 분석하는지 눈으로 확인한다.
    아직 기능어 빈도를 세지 않는다. 측정 도구가 믿을 만한지부터 본다.

이 파일이 확인하는 것 5가지
    [A] 환경 기록      — 버전·날짜. 나중에 재현하려면 반드시 필요하다.
    [B] 표준 예문      — Stanza 공식 문서 예문. 출력 형식이 정상인지 확인.
    [C] 축약형 처리    — don't / they've 를 어떻게 쪼개는지. 우리 기능어 계산에 직결.
    [D] 실제 데이터 감사 — BotSim 게시글을 직접 파싱해 오류를 눈으로 찾는다.
    [E] 처리 속도      — 전체 데이터에 몇 시간 걸릴지 추정한다.

왜 [D]가 중요한가 (이 파일의 핵심)
    Stanza는 사람이 아니라 학습된 모델이다. 즉 틀린다.
    SNS 글은 짧고 문법이 깨져 있어 일반 파서에게 어려운 영역이다.
    만약 파서가 봇 글에서만 더 자주 틀린다면, 우리는 "봇의 문체"가 아니라
    "파서의 오류 패턴"을 측정하게 된다. 그러면 연구 전체가 무너진다.
    그래서 봇 10건·사람 10건을 나란히 놓고 직접 읽어봐야 한다.

    ※ 여기서 라벨(봇/사람)을 쓰는 것은 오직 표본을 고르기 위해서다.
      특징을 만들거나 고르는 데는 쓰지 않는다.

실행
    IDLE에서 열어 Run(F5), 또는 터미널에서:
        python3 03_stanza_설치확인.py
    필요 패키지: stanza  (설치됨 — pip install stanza)

    처음 실행하면 영어 모델을 내려받는다(수백 MB, 몇 분).
    받은 모델은 ~/stanza_resources 에 저장되고 다음부터는 재사용한다.

선행 조건
    [D] 구간은 01_적격계정.json 이 있어야 동작한다(01번 스크립트 산출물).
    없으면 [D]만 건너뛰고 나머지는 그대로 실행된다.
"""

import json
import os
import platform
import sys
import time
import random

# ════════════════════════════════════════════════════════════════════════
# [경로·설정]
# ════════════════════════════════════════════════════════════════════════
# 이 파일이 있는 폴더를 기준으로 잡는다 — 연구 폴더를 통째로 옮겨도 깨지지 않는다.
HERE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_JSON = f"{HERE}/01_적격계정.json"   # 01번 산출물 (없으면 [D] 생략)
OUT_JSON = f"{HERE}/03_설치확인_기록.json"

SAMPLE_PER_LABEL = 10      # 감사 표본: 봇 10건 + 사람 10건
SEED = 20260817            # 표본 재현용 고정 시드

# UD가 닫힌 어류(기능어)로 분류하는 품사.
# 이 목록의 근거는 02번 스크립트와 동일하다. NUM은 우리 판단으로 제외한 상태.
CLOSED_CLASS = {"ADP", "AUX", "CCONJ", "SCONJ", "DET", "PRON", "PART"}


def line(title=""):
    print("\n" + "─" * 74)
    if title:
        print(title)
        print("─" * 74)


# ════════════════════════════════════════════════════════════════════════
# [A] 환경 기록
# ════════════════════════════════════════════════════════════════════════
def record_environment():
    """
    버전을 기록한다. 사소해 보이지만 재현성의 핵심이다.
    Stanza는 모델이 갱신되면 같은 문장에도 다른 품사를 줄 수 있다.
    나중에 "왜 수치가 달라졌지?"를 추적하려면 이 기록이 있어야 한다.
    """
    import stanza
    import torch
    env = {
        "실행일": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}",
        "stanza": stanza.__version__,
        "torch": torch.__version__,
        "모델저장경로": os.path.expanduser("~/stanza_resources"),
    }
    line("[A] 환경 기록")
    for k, v in env.items():
        print(f"  {k:<12} {v}")
    return env


# ════════════════════════════════════════════════════════════════════════
# 파이프라인 준비
# ════════════════════════════════════════════════════════════════════════
def build_pipeline():
    """
    영어 분석 파이프라인을 만든다.

    processors 설명:
      tokenize — 글을 문장으로, 문장을 단어로 나눈다.
      pos      — 각 단어에 UPOS(범용 품사)·XPOS(영어 전용 품사)·
                 feats(시제·인칭·태 등 형태 자질)를 붙인다.

    여기서는 이 둘만 쓴다. 의존구조(depparse)·개체명(ner)·표제어(lemma)는
    지금 단계에서 필요 없고, 붙이면 속도만 느려진다.
    (나중에 M 블록을 확장할 때 필요하면 그때 추가한다)

    'mwt'(복합 토큰 분해)는 일부러 넣지 않았다. 언어에 따라 없는 경우가 있어
    지정하면 오류가 날 수 있다. 영어 축약형이 실제로 어떻게 처리되는지는
    아래 [C]에서 직접 확인한다 — 추측하지 않고 출력으로 본다.
    """
    import stanza
    print("\n[모델 준비] 영어 모델을 확인/다운로드합니다 (최초 1회, 수백 MB)...")
    stanza.download("en", verbose=False)
    print("[모델 준비] 파이프라인 생성 중...")
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos",
                          verbose=False, use_gpu=False)
    print("[모델 준비] 완료")
    return nlp


def show_parse(nlp, text, label=""):
    """한 문장(또는 짧은 글)을 파싱해 표 형태로 출력한다."""
    if label:
        print(f"\n▶ {label}")
    print(f'  입력: "{text}"')
    doc = nlp(text)
    print(f"  {'단어':<14}{'UPOS':<8}{'XPOS':<7}{'닫힌어류':<9}자질")
    print("  " + "-" * 70)
    for sent in doc.sentences:
        for w in sent.words:
            mark = "●" if w.upos in CLOSED_CLASS else ""
            feats = w.feats if w.feats else "-"
            print(f"  {w.text:<14}{w.upos:<8}{str(w.xpos):<7}{mark:<9}{feats}")
    return doc


# ════════════════════════════════════════════════════════════════════════
# [D] 실제 데이터 감사
# ════════════════════════════════════════════════════════════════════════
def audit_real_data(nlp):
    """
    BotSim 실제 게시글을 파싱해 출력한다.
    파서가 우리 데이터에서 어떻게 작동하는지 눈으로 보는 것이 목적이다.

    볼 것:
      1. 문장 분리가 엉뚱하게 되지 않았는가 (마침표 없는 SNS 글에서 흔한 문제)
      2. 품사가 상식과 어긋나지 않는가
      3. 봇 글과 사람 글에서 오류 빈도가 다르지 않은가  ← 가장 중요
    """
    if not os.path.exists(ACCOUNTS_JSON):
        line("[D] 실제 데이터 감사 — 건너뜀")
        print(f"  {ACCOUNTS_JSON} 이(가) 없습니다.")
        print("  01_botsim_적격검열.py 를 먼저 실행하면 이 구간이 동작합니다.")
        return None

    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    accounts, labels = data["계정"], data["라벨"]

    # 라벨별로 계정을 나눈 뒤 각 10건씩 문서를 뽑는다.
    # (라벨은 표본 선정에만 쓴다 — 특징 추출·선택에는 절대 쓰지 않는다)
    rng = random.Random(SEED)
    picked = {}
    for lab in ("bot", "human"):
        uids = sorted([u for u in accounts if labels.get(u) == lab])
        rng.shuffle(uids)
        docs = []
        for uid in uids:
            if accounts[uid]:
                docs.append((uid, rng.choice(accounts[uid])))
            if len(docs) >= SAMPLE_PER_LABEL:
                break
        picked[lab] = docs

    line("[D] 실제 데이터 감사 — BotSim 게시글")
    print("  파서가 우리 데이터에서 제대로 작동하는지 직접 확인하십시오.")
    print("  특히 봇 글과 사람 글의 오류 빈도가 다른지 비교하십시오.")

    stats = {}
    for lab in ("human", "bot"):
        print(f"\n{'='*74}\n[{lab.upper()}] 표본 {len(picked[lab])}건\n{'='*74}")
        n_tok = n_closed = n_sent = 0
        for k, (uid, text) in enumerate(picked[lab], 1):
            doc = show_parse(nlp, text, label=f"{lab} 표본 {k}  (계정 {uid[:12]}…)")
            for s in doc.sentences:
                n_sent += 1
                for w in s.words:
                    n_tok += 1
                    if w.upos in CLOSED_CLASS:
                        n_closed += 1
        stats[lab] = {
            "표본수": len(picked[lab]),
            "문장수": n_sent,
            "토큰수": n_tok,
            "닫힌어류_토큰수": n_closed,
            "닫힌어류_비율": round(n_closed / n_tok, 4) if n_tok else None,
            "문장당_평균토큰": round(n_tok / n_sent, 2) if n_sent else None,
        }

    line("[D] 표본 요약 (본 측정 아님 — 감사용 참고치)")
    print(f"  {'':<8}{'문장':<8}{'토큰':<8}{'닫힌어류비율':<14}{'문장당토큰'}")
    for lab in ("human", "bot"):
        s = stats[lab]
        print(f"  {lab:<8}{s['문장수']:<8}{s['토큰수']:<8}"
              f"{str(s['닫힌어류_비율']):<14}{s['문장당_평균토큰']}")
    print("\n  ※ 표본 20건짜리 수치다. 결론을 내리는 값이 아니라,")
    print("     파싱이 양쪽에서 비슷하게 작동하는지 보는 눈금일 뿐이다.")
    return stats


# ════════════════════════════════════════════════════════════════════════
# [E] 처리 속도 측정
# ════════════════════════════════════════════════════════════════════════
def measure_speed(nlp):
    """
    전체 데이터를 파싱하는 데 얼마나 걸릴지 추정한다.
    규모를 모르고 착수하면 며칠짜리 작업에 발이 묶인다.
    """
    if not os.path.exists(ACCOUNTS_JSON):
        line("[E] 처리 속도 — 건너뜀 (01번 산출물 없음)")
        return None

    data = json.load(open(ACCOUNTS_JSON, encoding="utf-8"))
    accounts = data["계정"]
    all_docs = [d for docs in accounts.values() for d in docs]
    rng = random.Random(SEED)
    sample = rng.sample(all_docs, min(200, len(all_docs)))

    line("[E] 처리 속도 측정")
    print(f"  표본 {len(sample)}건 파싱 중...")
    t0 = time.time()
    for d in sample:
        nlp(d)
    elapsed = time.time() - t0

    per_doc = elapsed / len(sample)
    total = len(all_docs)
    est_sec = per_doc * total

    print(f"  소요       {elapsed:.1f}초 ({per_doc*1000:.0f} ms/문서)")
    print(f"  전체 문서   {total:,}건")
    print(f"  전체 예상   {est_sec/60:.1f}분  ({est_sec/3600:.2f}시간)")
    print("\n  ※ 참고: fox8은 계정당 최대 200건이라 문서 수가 훨씬 많다.")
    print("     이 속도로 환산해 미리 계산한 뒤 착수해야 한다.")
    return {"표본수": len(sample), "초당문서": round(1/per_doc, 2),
            "전체문서수": total, "예상소요_분": round(est_sec/60, 1)}


# ════════════════════════════════════════════════════════════════════════
# [실행]
# ════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 74)
    print("Stanza + UD 설치 확인 및 파서 감사")
    print("=" * 74)

    env = record_environment()
    nlp = build_pipeline()

    # ── [B] 표준 예문 ────────────────────────────────────────────
    line("[B] 표준 예문 — 출력 형식 확인")
    print("  Stanza 공식 문서가 쓰는 예문이다. 여기서 형식이 정상이어야 한다.")
    show_parse(nlp, "Barack Obama was born in Hawaii.")
    print("\n  읽는 법:")
    print("    was  → AUX(조동사) · Tense=Past(과거) · Person=3(3인칭)")
    print("    born → VERB(동사) · Voice=Pass(수동태)")
    print("    in   → ADP(전치사) ● 닫힌 어류")
    print("    Hawaii → PROPN(고유명사), 닫힌 어류 아님 = 내용어")

    # ── 연구용 예문 ──────────────────────────────────────────────
    line("[B-2] 연구용 예문 — 우리가 재려는 것이 실제로 나오는가")
    show_parse(nlp, "I was working in the office, but they did not agree with me.")
    print("\n  확인할 점: was/did에 Tense=Past가, I/they/me에 Person이 붙는가.")
    print("  이 자질들이 나중에 M 블록(시제·인칭·태)의 원재료가 된다.")

    # ── [C] 축약형 처리 ──────────────────────────────────────────
    line("[C] 축약형 처리 — 우리 기능어 계산에 직결되는 문제")
    print("  UD는 don't 를 do + n't 두 단어로 쪼개는 규정이다.")
    print("  실제로 그렇게 나오는지 확인한다. 쪼개진다면 우리 기능어 목록도")
    print("  통짜 축약형(don't)이 아니라 분해형(do, n't) 기준이어야 한다.")
    show_parse(nlp, "I don't think they've seen it, and it isn't mine.")

    # ── [D] 실제 데이터 ──────────────────────────────────────────
    stats = audit_real_data(nlp)

    # ── [E] 속도 ─────────────────────────────────────────────────
    speed = measure_speed(nlp)

    # ── 저장 ─────────────────────────────────────────────────────
    out = {"환경": env, "감사표본_요약": stats, "처리속도": speed,
           "닫힌어류_기준": sorted(CLOSED_CLASS), "표본시드": SEED}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    line("확인 항목")
    print("  아래를 직접 눈으로 판단한 뒤 다음 단계로 넘어가십시오.")
    print("   1. 표준 예문의 품사·자질이 정상인가")
    print("   2. 축약형이 쪼개지는가 (쪼개진다면 기능어 목록 기준을 맞춰야 함)")
    print("   3. 실제 게시글에서 문장 분리가 엉뚱하지 않은가")
    print("   4. 봇 글과 사람 글에서 오류 빈도가 비슷한가  ← 가장 중요")
    print("   5. 전체 파싱 소요 시간이 감당 가능한가")
    print(f"\n  기록 저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
