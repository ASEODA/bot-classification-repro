"""댓글 통제용 원문 선택. 기존 09-2의 정제/선택 규칙만 분리했다."""

import functools


import json


import os


import re


import time

import unicodedata

from collections import Counter

print = functools.partial(print, flush=True)

HERE = os.path.dirname(os.path.abspath(__file__))

ROOT = os.path.dirname(HERE)   # 연구주제/ : 원본데이터와 보관 폴더가 여기 있다

BASE = f"{ROOT}/1. 원본데이터"

BOTSIM_DIR = f"{BASE}/2. BotSim Data/BotSim-24-Dataset"

POSTS_JSON = f"{BOTSIM_DIR}/user_post_comment.json"   # 원본 — 장르를 가르려면 여기까지 내려가야 한다

MIN_CHARS = 20          # [01에서 가져옴] 정제 후 20자 미만 문서는 버린다

MIN_DOCS = 10           # [01에서 가져옴] 적격 문서가 10건 미만인 계정은 제외

MAX_DOCS = 200          # [01에서 가져옴] 계정당 최근 200건까지만 사용

LANG_TARGET = "en"      # [01에서 가져옴] 계정 단위 langid 판정이 이 언어여야 통과

SELF_REVEAL = re.compile(
    r"(as an ai language model"
    r"|i'?m sorry,? but (i cannot|as an ai)"
    r"|i cannot (comply|fulfill|browse)"
    r"|openai'?s? (content )?polic)", re.I)

RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")      # [01에서 가져옴]

RE_URL = re.compile(r"(https?://\S+|www\.\S+)")       # [01에서 가져옴]

RE_MENTION = re.compile(r"@\w+")                      # [01에서 가져옴]

RE_WS = re.compile(r"\s+")                            # [01에서 가져옴]

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
