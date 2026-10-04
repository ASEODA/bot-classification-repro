"""집단 차이·세 통제·집단 동질성. 판별 특성 선택에는 결과를 사용하지 않는다."""
import math
from collections import Counter
import numpy as np
import common as C
FAMILIES = ("F", "M형태", "M품사", "R")

def load(name):
    ids, info, order, X = C.read_table(C.TABLE[name])
    return {"ids": ids, "info": info, "order": order, "X": X, "row": {u: i for i, u in enumerate(ids)},
            "labels": dict(zip(ids, info["라벨"]))}


def keys_of(order):
    return {f: [k for b, k in order if b == f] for f in FAMILIES}


def compare(T, labels, ids=None):
    ids = sorted(ids if ids is not None else T["ids"])
    rows_b = [T["row"][u] for u in ids if labels[u] == "bot"]
    rows_h = [T["row"][u] for u in ids if labels[u] == "human"]
    col = {bk: j for j, bk in enumerate(T["order"])}
    keys = keys_of(T["order"])
    result = {}
    for fam in FAMILIES:
        rows = {}
        for k in keys[fam]:
            j = col[(fam, k)]
            x = C.col_values(T["X"], j, rows_b)
            y = C.col_values(T["X"], j, rows_h)
            row = C.mw(x, y)
            sx, sy = C.summary(x), C.summary(y)
            row.update({'봇_n': len(x), '사람_n': len(y), '결측': len(ids) - len(x) - len(y),
                        '봇_중앙': sx['중앙'], '사람_중앙': sy['중앙'],
                        '봇_IQR': sx['IQR'], '사람_IQR': sy['IQR'],
                        'IQR비': sx['IQR'] / sy['IQR'] if sy['IQR'] and sx['IQR'] is not None else None})
            rows[k] = row
        qs = C.bh([v['p'] if v['p'] is not None else 1.0 for v in rows.values()])
        for row, q in zip(rows.values(), qs):
            row['q'] = q if row['p'] is not None else None
            row['주목'] = row['p'] is not None and q <= .05 and abs(row['델타']) >= C.DELTA_NOTABLE
        result[fam] = rows
    return result


def add_reference(result, baseline):
    for fam, rows in result.items():
        for key, row in rows.items():
            ref = baseline[fam][key]
            d, b = row['델타'], ref['델타']
            row['기준선_델타'] = b
            row['기준선_주목'] = ref['주목']
            row['델타변화'] = d - b if d is not None and b is not None else None
            row['효과유지'] = bool(ref['주목'] and d is not None and b * d > 0 and abs(d) >= C.DELTA_NOTABLE)
            if not ref['주목']:
                status = '신규주목' if row['주목'] else '기준선비주목'
            elif d is None:
                status = '검정불가'
            elif b * d < 0:
                status = '방향역전'
            elif abs(d) < C.DELTA_NOTABLE:
                status = '효과문턱미달'
            else:
                status = '효과유지'
            row['효과판정'] = status


def punct_check(rows):
    a, b = rows['M품사']['PUNCT'], rows['R']['구두점_비율']
    C.check(a['U'] == b['U'] and a['델타'] == b['델타'], 'PUNCT 단조변환 순위 불일치')


def summarize(rows):
    return {f: {'자질수': len(rs), '주목': sum(x['주목'] for x in rs.values()),
                '기준선주목': sum(x.get('기준선_주목', False) for x in rs.values()),
                '효과유지': sum(x.get('효과유지', False) for x in rs.values()),
                '판정': dict(Counter(x.get('효과판정', '기준선') for x in rs.values()))} for f, rs in rows.items()}


def matched_matrix(T, pairs):
    ids = [b for b, _, _ in pairs] + [h for _, h, _ in pairs]
    return ids, T["X"][[T["row"][u] for u in ids]]


def fox8_pairs(T, human_filter=None):
    """봇·사람 ID를 정렬한 뒤 비구두점 토큰 수의 로그값으로 매칭한다. 캘리퍼 0.10, 시드 20260926."""
    labels = T["labels"]
    src = dict(zip(T["ids"], T["info"].get("자료원", [None] * len(T["ids"]))))
    pool_bot = sorted(u for u in T["ids"] if labels[u] == "bot")
    pool_hum = sorted(u for u in T["ids"] if labels[u] == "human" and (human_filter is None or src[u] == human_filter))
    tok = dict(zip(T["ids"], T["info"]["토큰수_구두점제외"]))
    logd = {u: math.log(tok[u]) for u in pool_bot + pool_hum}
    pairs, unmatched, used = C.caliper_match(pool_bot, pool_hum, logd, C.CALIPER, C.SEED)
    return pairs, unmatched, used, pool_bot, pool_hum


def run():
    B = load("botsim")
    labels = B["labels"]
    base = compare(B, labels)
    punct_check(base)
    bots = sorted(u for u in B["ids"] if labels[u] == "bot")
    humans = sorted(u for u in B["ids"] if labels[u] == "human")
    tok = dict(zip(B["ids"], B["info"]["토큰수_구두점제외"]))
    logs = {u: math.log(t) for u, t in tok.items() if t > 0}
    pairs, _, _ = C.caliper_match(bots, humans, logs, C.CALIPER, C.MATCH_SEED_BOTSIM)
    C.check(len(pairs) == 512, "BotSim 매칭 512쌍 불일치")
    mids = sorted({u for b, h, _ in pairs for u in (b, h)})
    controls = {"분량매칭": compare(B, labels, mids)}
    samples = {"전체": dict(Counter(labels.values())), "분량매칭": {"bot":512, "human":512}}
    for name, table in (("댓글한정", "comments"), ("politics한정", "politics")):
        T = load(table)
        controls[name] = compare(T, labels)
        samples[name] = dict(Counter(T["labels"].values()))
    for rows in controls.values():
        add_reference(rows, base)
        punct_check(rows)
    hom = {}
    for name, T, ps in (("BotSim", B, pairs), ("fox8", load("fox8"), None)):
        if ps is None:
            ps = fox8_pairs(T)[0]
        ids, X = matched_matrix(T, ps)
        hom[name] = C.homogeneity(X, T["order"], len(ps), math.ceil(len(ps)/2), ids=ids)
        hom[name]["쌍수"] = len(ps)
        C.say(name, "동질성 비율:", {b:round(r["비율"],6) for b,r in hom[name]["블록별"].items()})
    out = {"전체기준선":base, "통제":controls, "표본":samples, "매칭쌍":pairs,
           "요약":{k:summarize(v) for k,v in controls.items()}, "동질성":hom}
    C.write_json(C.RESULTS / "analysis.json", out)
    return out
