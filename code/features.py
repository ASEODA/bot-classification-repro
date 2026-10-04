"""BotSim·fox8 원문에서 계정별 FMR 특성을 추출한다. 생성 모델 API는 호출하지 않는다."""
import csv
import hashlib
import json
import re
import sqlite3
import statistics
import time
import urllib.parse
from collections import Counter
import numpy as np
import common as C
from common import say, line, label_use
TRUNC_TAIL = re.compile(r"\S*\u2026$")


def full_botsim_corpus():
    """적격 계정 문서, 서브레딧 정보, 댓글 한정 코퍼스를 구성한다."""
    import langid
    data = C.read_json(C.BOTSIM_RAW / "user_post_comment.json")
    cand, cand_sub = {}, {}
    for uid, u in data.items():
        items = []
        for p in (u.get("posts") or []):
            items.append((str(p.get("posts") or ""), str(p.get("created_utc") or ""), p.get("subreddit")))
        for block in ("comment_1", "comment_2"):
            for c in (u.get(block) or []):
                items.append((str(c.get("comment_body") or ""), str(c.get("created_utc") or ""),
                              c.get("subreddit")))
        if not items:
            continue
        rows = []
        for text, ts, sub in items:
            cleaned, _, _ = C.clean_doc(text)
            if cleaned is not None:
                rows.append((str(ts or ""), cleaned, sub))
        rows.sort(key=lambda r: r[0])            # 시각 오름차순으로 안정 정렬한다.
        if len(rows) > C.MAX_DOCS:
            rows = rows[-C.MAX_DOCS:]
        if len(rows) >= C.MIN_DOCS:
            cand[uid] = [c for _, c, _ in rows]
            cand_sub[uid] = [s for _, _, s in rows]
    eligible = {}
    for uid, docs in cand.items():
        if langid.classify(" ".join(docs))[0] == C.LANG_TARGET:
            eligible[uid] = docs
    subs = {u: cand_sub[u] for u in eligible}
    # comment_1·comment_2에 한정하여 적격 규칙을 다시 적용한다.
    comments = {}
    for uid in sorted(eligible):
        u = data[uid]
        rows = []
        for block in ("comment_1", "comment_2"):
            for c in (u.get(block) or []):
                cleaned, _, _ = C.clean_doc(str(c.get("comment_body") or ""))
                if cleaned is not None:
                    rows.append((str(c.get("created_utc") or ""), cleaned))
        rows.sort(key=lambda r: r[0])
        if len(rows) > C.MAX_DOCS:
            rows = rows[-C.MAX_DOCS:]
        if len(rows) >= C.MIN_DOCS and langid.classify(" ".join(c for _, c in rows))[0] == C.LANG_TARGET:
            comments[uid] = [c for _, c in rows]
    label_use("Users.csv character_setting: 봇 · 사람 라벨(적격 판정에는 쓰지 않음)")
    labels = {}
    with open(C.BOTSIM_RAW / "Users.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels[row["user_id"]] = "bot" if (row.get("character_setting") or "").strip() else "human"
    return eligible, subs, comments, {u: labels.get(u, "라벨없음") for u in eligible}


def full_funcwords():
    """UD EWT에서 빈도 5 이상이고 닫힌 품사로 쓰인 비율이 50% 이상인 형태를 선택한다."""
    closed = {"ADP", "AUX", "CCONJ", "SCONJ", "DET", "PRON", "PART"}
    counts = {}
    for name in ("en_ewt-ud-train.conllu", "en_ewt-ud-dev.conllu", "en_ewt-ud-test.conllu"):
        with open(C.UD_DIR / name, encoding="utf-8") as f:
            for ln in f:
                ln = ln.rstrip("\n")
                if not ln or ln.startswith("#"):
                    continue
                cols = ln.split("\t")
                if len(cols) < 4 or "-" in cols[0] or "." in cols[0]:
                    continue
                word = cols[1].lower().strip()
                if word:
                    counts.setdefault(word, Counter())[cols[3]] += 1
    out = []
    for word, pc in counts.items():
        total = sum(pc.values())
        if total < 5:
            continue
        if sum(n for p, n in pc.items() if p in closed) / total < 0.50:
            continue
        out.append(word)
    return sorted(out)


def full_fox8_corpus():
    """리트윗을 제외하고 정제한 뒤 계정별 최근 200건 중 10건 이상을 요구하고 langid로 영어를 선정한다."""
    import heapq
    import langid
    conn = sqlite3.connect("file:" + urllib.parse.quote(str(C.FOX8_DB)) + "?mode=ro", uri=True)
    heaps, seq = {}, 0
    for uid, created, text, is_reply in conn.execute(
            "SELECT user_id, created_at, text, is_reply FROM tweets WHERE is_retweet = 0"):
        if not uid:
            continue
        cleaned, _, _ = C.clean_doc(text)
        if cleaned is None:
            continue
        s = (created or "")[:4]
        yr = s if len(s) == 4 and s.isdigit() else "?"
        item = (1 if yr == "?" else 0, created or "", seq, cleaned, f"{yr}|{1 if is_reply else 0}")
        seq += 1
        h = heaps.setdefault(uid, [])
        if len(h) < C.MAX_DOCS:
            heapq.heappush(h, item)
        else:
            heapq.heappushpop(h, item)
    labels_all = dict(conn.execute("SELECT user_id, label FROM users"))
    conn.close()
    work = {}
    for uid in sorted(heaps):
        items = sorted(heaps[uid])
        docs = [(c, k) for _, _, _, c, k in items]
        if len(docs) >= C.MIN_DOCS and langid.classify(" ".join(c for c, _ in docs))[0] == C.LANG_TARGET:
            work[uid] = docs
    return work, {u: labels_all[u] for u in work}


def doc_counts(doc, words, key=None):
    """파싱된 문서 하나의 문장·토큰·기능어·품사·형태론 특성을 센다."""
    a = {"문서수": 1, "문장수": 0, "토큰수": 0, "토큰수_구두점제외": 0,
         "기능어": Counter(), "UPOS": Counter(), "자질": Counter(), "문장길이": [], "버킷": key}
    for sent in doc.sentences:
        length = 0
        a["문장수"] += 1
        for w in sent.words:
            a["토큰수"] += 1
            a["UPOS"][w.upos] += 1
            if w.upos != "PUNCT":
                length += 1
                a["토큰수_구두점제외"] += 1
            surface = C.normalize_apostrophe(w.text.lower())
            if surface in words:
                a["기능어"][surface] += 1
            for feature in (w.feats or "").split("|"):
                if feature:
                    a["자질"][feature] += 1
        a["문장길이"].append(length)
    return a


def combine(rows, with_buckets=False):
    a = {k: sum(x[k] for x in rows) for k in C.META_COLS}
    for k in ("기능어", "UPOS", "자질"):
        c = Counter()
        for x in rows:
            c.update(x[k])
        a[k] = dict(c)
    a["문장길이"] = [v for x in rows for v in x["문장길이"]]
    if with_buckets:
        b = {}
        for x in rows:
            v = b.setdefault(x["버킷"], [0, 0, 0, 0])
            v[0] += 1; v[1] += x["문장수"]; v[2] += x["토큰수"]; v[3] += x["토큰수_구두점제외"]
        a["버킷별"] = {k: b[k] for k in sorted(b)}
        a["구두점토큰수"] = a["토큰수"] - a["토큰수_구두점제외"]
    assert len(a["문장길이"]) == a["문장수"] and sum(a["문장길이"]) == a["토큰수_구두점제외"]
    assert a["UPOS"].get("PUNCT", 0) == a["토큰수"] - a["토큰수_구두점제외"]
    return a


class ParseCache:
    """재개 가능한 추출을 위해 계정별 문서 카운트를 results/.work/parse_cache.sqlite에 저장한다."""

    def __init__(self):
        C.WORK.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(C.WORK / "parse_cache.sqlite")
        self.conn.execute("CREATE TABLE IF NOT EXISTS acct (corpus TEXT, uid TEXT, fp TEXT, docs TEXT, "
                          "PRIMARY KEY (corpus, uid))")

    def get(self, corpus, uid, fp):
        r = self.conn.execute("SELECT fp, docs FROM acct WHERE corpus=? AND uid=?", (corpus, uid)).fetchone()
        if r and r[0] == fp:
            return json.loads(r[1])
        return None

    def put(self, corpus, uid, fp, docs):
        self.conn.execute("INSERT OR REPLACE INTO acct VALUES (?,?,?,?)",
                          (corpus, uid, fp, json.dumps(docs, ensure_ascii=False)))
        self.conn.commit()


def full_parse(limit):
    import stanza
    import torch
    C.check(stanza.__version__ == "1.14.0", "stanza 1.14.0 필요")
    line("[full] 1/5 BotSim 적격 · 댓글 코퍼스 · 02 기능어 목록 (원문)")
    t = time.time()
    eligible, subs, comment_docs, labels = full_botsim_corpus()
    raw_words = full_funcwords()
    words, h = C.funcword_list(raw_words)
    say(f"  적격 {len(eligible):,} · 댓글 한정 {len(comment_docs):,} · 목록 {len(raw_words)} → {len(words)} ({h}) · "
        f"{time.time() - t:.0f}초")
    line("[full] 2/5 fox8 재선정 (원문 sqlite)")
    t = time.time()
    fox_work, fox_labels = full_fox8_corpus()
    say(f"  fox8 적격 {len(fox_work):,} · 라벨 {dict(Counter(fox_labels.values()))} · {time.time() - t:.0f}초")
    torch.manual_seed(C.SEED)
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos", use_gpu=False, verbose=False,
                          download_method=None, dir=str(C.STANZA_DIR))
    wset = set(words)
    cache = ParseCache()

    def run(corpus, uid, docs, keys=None, reuse=None):
        fp = hashlib.sha256(json.dumps([docs, keys], ensure_ascii=False).encode()).hexdigest()
        got = cache.get(corpus, uid, fp)
        if got is None:
            pending = [d for d in dict.fromkeys(docs) if not (reuse and d in reuse)] if reuse is not None else docs
            parsed = nlp.bulk_process(pending) if pending else []
            if reuse is not None:
                new = {d: doc_counts(p, wset) for d, p in zip(pending, parsed)}
                got = [reuse[d] if d in reuse else new[d] for d in docs]
            else:
                got = [doc_counts(p, wset, keys[i] if keys else None) for i, p in enumerate(parsed)]
            cache.put(corpus, uid, fp, got)
        return got

    line("[full] 3/5 BotSim 파싱 (계정 단위 bulk_process, 04 · 04-1)")
    ids = sorted(eligible)[:limit] if limit else sorted(eligible)
    botsim, politics, per_doc = {}, {}, {}
    t = time.time()
    for i, u in enumerate(ids, 1):
        rows = run("botsim", u, eligible[u])
        per_doc[u] = {d: r for d, r in zip(eligible[u], rows)}
        botsim[u] = combine(rows)
        pol = [r for r, s in zip(rows, subs[u]) if s == "politics"]
        if len(pol) >= 10:
            politics[u] = combine(pol)
        if i % 100 == 0 or i == len(ids):
            say(f"    {i:,}/{len(ids):,} 계정 · {time.time() - t:.0f}초")
    line("[full] 4/5 댓글 한정 파싱 (같은 글은 3단계 결과 재사용, 나머지는 계정 단위 bulk)")
    comments = {}
    for u in [u for u in sorted(comment_docs) if u in botsim]:
        rows = run("comments", u, comment_docs[u], reuse={d: r for d, r in per_doc[u].items()})
        comments[u] = combine(rows)
    line("[full] 5/5 fox8 파싱 (계정 단위 bulk_process)")
    fids = sorted(fox_work)[:limit] if limit else sorted(fox_work)
    fox8 = {}
    t = time.time()
    for i, u in enumerate(fids, 1):
        docs = [c for c, _ in fox_work[u]]
        keys = [k for _, k in fox_work[u]]
        fox8[u] = {"라벨": fox_labels[u], **combine(run("fox8", u, docs, keys), with_buckets=True)}
        if i % 100 == 0 or i == len(fids):
            say(f"    {i:,}/{len(fids):,} 계정 · {time.time() - t:.0f}초")
    return {"botsim": botsim, "labels": labels, "raw_words": raw_words, "comments": comments,
            "politics": politics, "fox8": fox8, "fox8_labels": {u: fox_labels[u] for u in fox8},
            "_full_sets": {"적격": sorted(eligible), "댓글": sorted(comment_docs), "fox8": sorted(fox_work),
                           "politics_후보": sorted(u for u in eligible
                                                  if sum(s == "politics" for s in subs[u]) >= 10)}}


def fox8_caveat_cols(a):
    """연도·답글 버킷에서 연도 중앙값·최댓값, 답글 비율, 2023년 문서 수를 요약한다."""
    years, replies = Counter(), 0
    for key, counts in a["버킷별"].items():
        year, reply = key.split("|")
        years[year] += counts[0]
        if reply == "1":
            replies += counts[0]
    ys = []
    for yv, c in years.items():
        ys += [int(yv)] * int(c)
    return {"연도_중앙값": float(statistics.median(ys)), "연도_최대": max(int(k) for k in years),
            "답글비율": replies / a["문서수"], "문서수_2023": int(years.get("2023", 0))}


def strip_trunc(t):
    """끝의 줄임표(U+2026)와 그 앞에 공백 없이 붙은 잘린 낱말을 한 번 제거한다."""
    if t.endswith("\u2026"):
        return TRUNC_TAIL.sub("", t).rstrip(), True
    return t, False


def fox8_trunc(G, cache, limit=None):
    """선정된 문서는 유지하면서 잘린 끝부분을 제거한 뒤 Stanza 특성을 다시 추출한다."""
    import stanza
    import torch
    line("[fox8 절단] 1/3 문서 재선정 및 추출 캐시 대조")
    t = time.time()
    work, labels = full_fox8_corpus()
    old = cache["fox8"]
    if limit:
        work = {u: work[u] for u in sorted(work)[:limit]}
    same_docs = all(len(work[u]) == old[u]["문서수"]
                    and Counter(k for _, k in work[u]) == Counter({k: v[0] for k, v in old[u]["버킷별"].items()})
                    for u in work) if set(work) == set(old) else False
    G.add("재선정 계정·문서 수·버킷별 문서 수와 추출 캐시 대조", "동일 기록", len(work), same_docs)
    C.check(same_docs, "재선정 문서와 추출 캐시가 다르다")
    stats = {}
    new_docs = {}
    for u in sorted(work):
        rows = []
        for text, key in work[u]:
            s2, cut = strip_trunc(text)
            st = stats.setdefault(labels[u], Counter())
            st["문서"] += 1
            st["절단"] += int(cut)
            st["빈문서"] += int(cut and not s2)
            rows.append((s2, key))
        new_docs[u] = rows
    summ = {lab: {**dict(c), "절단비율": c["절단"] / c["문서"]} for lab, c in stats.items()}
    say(f"  재선정 {time.time() - t:.0f}초 · 절단 꼬리 문서: " +
        " · ".join(f"{lab} {v['절단']:,}/{v['문서']:,} ({100 * v['절단비율']:.1f}%, 빈 문서 {v['빈문서']})"
                   for lab, v in sorted(summ.items())))
    line("[fox8 절단] 2/3 Stanza 재측정 (계정 단위 bulk_process, 중단 뒤 재개)")
    C.check(stanza.__version__ == "1.14.0", "stanza 1.14.0 필요")
    words, _ = C.funcword_list(cache["raw_words"])
    wset = set(words)
    torch.manual_seed(C.SEED)
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos", use_gpu=False, verbose=False,
                          download_method=None, dir=str(C.STANZA_DIR))
    pc = ParseCache()
    fox, t = {}, time.time()
    ids = sorted(new_docs)
    for i, u in enumerate(ids, 1):
        docs = [d for d, _ in new_docs[u]]
        keys = [k for _, k in new_docs[u]]
        fp = hashlib.sha256(json.dumps([docs, keys], ensure_ascii=False).encode()).hexdigest()
        got = pc.get("fox8_trunc", u, fp)
        if got is None:
            live = [d for d in docs if d]
            parsed = iter(nlp.bulk_process(live)) if live else iter(())
            got = []
            for d, k in zip(docs, keys):
                if d:
                    got.append(doc_counts(next(parsed), wset, k))
                else:
                    got.append({"문서수": 1, "문장수": 0, "토큰수": 0, "토큰수_구두점제외": 0, "기능어": {},
                                "UPOS": {}, "자질": {}, "문장길이": [], "버킷": k})
            pc.put("fox8_trunc", u, fp, got)
        fox[u] = {"라벨": labels[u], **combine(got, with_buckets=True)}
        if i % 100 == 0 or i == len(ids):
            say(f"    {i:,}/{len(ids):,} 계정 · {time.time() - t:.0f}초")
    return fox, summ
