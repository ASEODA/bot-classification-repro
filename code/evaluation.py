"""2026-10-01 확인 실험: 학습 눈금 kNN10 + 로지스틱, 1:1 순위 결합."""
import operator
import time
from collections import Counter
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.metrics import roc_auc_score
import common as C
EXP = 17
SEED_W = 20260101
SPLIT_SEED = 20260101
N_BOOT = 2000
N_EXTRA = 4
LEVELS = (50, 25, 10, 5)
SEEDS = (0, 1, 2)
SRC_EXPECT = {"botometer-feedback":116, "gilani-17":87, "midterm-2018":137, "varol-icwsm":109}
DIFFS = {"S−L":("S","L"), "S_eval−L":("S_eval","L"), "S−S_eval":("S","S_eval")}
OPS = {"<=": operator.le, ">=": operator.ge, ">": operator.gt}


def make_split(ids, info):
    lab, src = info["라벨"], info["자료원"]
    groups = {"bot": sorted(u for u, l in zip(ids, lab) if l == "bot")}
    for s in sorted({s for l, s in zip(lab, src) if l == "human"}):
        groups[s] = sorted(u for u, l, ss in zip(ids, lab, src) if l == "human" and ss == s)
    rng = np.random.default_rng(SPLIT_SEED)
    dev, conf, counts = [], [], {}
    for g in ["bot"] + sorted(k for k in groups if k != "bot"):
        u = groups[g]
        perm = rng.permutation(len(u))
        h = len(u) // 2
        dev += [u[i] for i in perm[:h]]
        conf += [u[i] for i in perm[h:]]
        counts[g] = {"전체": len(u), "개발": h, "확인": len(u) - h}
    return sorted(dev), sorted(conf), counts


def counterfactual(X, y, rng, side):
    bi, hi = np.where(y == 1)[0], np.where(y == 0)[0]
    mb, mh = np.nanmedian(X[bi], 0), np.nanmedian(X[hi], 0)
    Xc = X.copy()
    if side == "bot":       # 봇 = 봇 중앙값 + 사람 잔차
        donors = hi[rng.integers(0, len(hi), size=len(bi))]
        Xc[bi] = mb[None, :] + (X[donors] - mh[None, :])
    else:                   # 사람 = 사람 중앙값 + 봇 잔차
        donors = bi[rng.integers(0, len(bi), size=len(hi))]
        Xc[hi] = mh[None, :] + (X[donors] - mb[None, :])
    return Xc


def ci3(pt, dist):
    lo, hi = C.ci95(dist)
    return [float(pt), lo, hi]

def locremove(X, y):
    bi, hi = np.where(y == 1)[0], np.where(y == 0)[0]
    mb, mh = np.nanmedian(X[bi], 0), np.nanmedian(X[hi], 0)
    Xc = X.copy()
    Xc[bi] = mh[None, :] + (X[bi] - mb[None, :])
    return Xc


def spread(P, y):
    out = {}
    for g, nm in ((1, "봇"), (0, "사람")):
        Q = P[y == g]
        D = cdist(Q, Q, metric="cityblock") / Q.shape[1]
        np.fill_diagonal(D, np.inf)
        out[nm] = {"P_SD_중앙": float(np.median(Q.std(0))), "집단안_kNN10_중앙": float(np.median(np.sort(D, 1)[:, 9]))}
    return out

def declared_scores(X, b, prep):
    P = C.apply_prep(prep, X)
    L = b["model"].predict_proba(P)[:, 1]
    n, d = P.shape
    D = cdist(P, P, metric="cityblock") / d
    np.fill_diagonal(D, np.inf)
    idx = np.argsort(D, axis=1, kind="stable")[:, :10]
    G = -np.take_along_axis(D, idx, 1)[:, 9]
    sc = {"L": L, "G": G, "S": C.rank_mean(L, G)}
    try:
        ge = C.density(X, (10,))[0][10]
        sc["G_eval"], sc["S_eval"] = ge, C.rank_mean(L, ge)
        why = None
    except AssertionError as ex:          # 보고만 하는 행. 계산 불가면 그 행만 비운다.
        why = str(ex)
    return sc, P, why


def boots(key, nb, nh):
    Wh = C.boot_counts((EXP, *key, 1), [0] * nh, N_BOOT)
    Wb = C.boot_counts((EXP, *key, 2), [0] * nb, N_BOOT)
    return Wb, Wh


def evaluate(sc, y, Wb, Wh):
    bidx, hidx = np.where(y == 1)[0], np.where(y == 0)[0]
    pt, ds = {}, {}
    for k, v in sc.items():
        pt[k], ds[k] = C.auc_boot(v, bidx, hidx, Wb, Wh)
    auc = {k: ci3(pt[k], ds[k]) for k in sc}
    diff = {nm: ci3(pt[a] - pt[c], ds[a] - ds[c]) for nm, (a, c) in DIFFS.items() if a in pt and c in pt}
    return {"AUC": auc, "차": diff}, pt, ds


def run_set(key, code, name, X, y, uids, conf_set, b, prep, worlds):
    t0 = time.time()
    assert set(uids) <= conf_set, "확인 절반 밖 계정"
    nb, nh = int((y == 1).sum()), int((y == 0).sum())
    Wb, Wh = boots(key, nb, nh)
    res = {"집합": name, "부트스트랩열쇠": {"사람": [EXP, *key, 1], "봇": [EXP, *key, 2]}, "n_봇": nb, "n_사람": nh}
    sc0, P0, why = declared_scores(X, b, prep)
    res["W0"], pt0, ds0 = evaluate(sc0, y, Wb, Wh)
    if why:
        res["G_eval_계산불가"] = {"W0": why}
    if worlds:
        res["세계열쇠"] = {"W2": [SEED_W, EXP, code, 2], "W3": [SEED_W, EXP, code, 1],
                       "W2_추가": [[SEED_W, EXP, code, 2, e] for e in range(1, N_EXTRA + 1)]}
        WX = {"W1": locremove(X, y),
              "W2": counterfactual(X, y, np.random.default_rng([SEED_W, EXP, code, 2]), "human"),
              "W3": counterfactual(X, y, np.random.default_rng([SEED_W, EXP, code, 1]), "bot")}
        res["산포"] = {"W0": spread(P0, y)}
        pts, dss = {"W0": pt0}, {"W0": ds0}
        for w, Xw in WX.items():
            sc, P, why = declared_scores(Xw, b, prep)
            res[w], pts[w], dss[w] = evaluate(sc, y, Wb, Wh)
            res["산포"][w] = spread(P, y)
            if why:
                res.setdefault("G_eval_계산불가", {})[w] = why
        res["G_W0−W2"] = ci3(pts["W0"]["G"] - pts["W2"]["G"], dss["W0"]["G"] - dss["W2"]["G"])
        d0 = (pts["W0"]["S"] - pts["W0"]["L"], dss["W0"]["S"] - dss["W0"]["L"])
        d3 = (pts["W3"]["S"] - pts["W3"]["L"], dss["W3"]["S"] - dss["W3"]["L"])
        res["W3_Δ−Δcf"] = ci3(d0[0] - d3[0], d0[1] - d3[1])
        ext = []
        for e in range(1, N_EXTRA + 1):
            Xe = counterfactual(X, y, np.random.default_rng([SEED_W, EXP, code, 2, e]), "human")
            sc, P, _ = declared_scores(Xe, b, prep)
            gA = float(roc_auc_score(y, sc["G"]))
            ext.append({"e": e, "L": float(roc_auc_score(y, sc["L"])), "G": gA,
                        "S": float(roc_auc_score(y, sc["S"])), "G_W0−W2": pts["W0"]["G"] - gA, "산포": spread(P, y)})
        res["W2_추가추출"] = ext
        res["관문"] = gates(res)
    res["소요초"] = round(time.time() - t0, 1)
    return res


def test(v, op, thr):
    raw, rnd = OPS[op](v, thr), OPS[op](round(v, 3), thr)
    sym = {"<=": "≤", ">=": "≥", ">": ">"}[op]
    return {"값": float(v), "조건": f"{sym} {thr:.3f}", "통과": bool(raw and rnd), "반올림_엇갈림": bool(raw != rnd)}


def gates(r):
    sp = r["산포"]
    sd = lambda w, g: sp[w][g]["P_SD_중앙"]
    nn = lambda w, g: sp[w][g]["집단안_kNN10_중앙"]
    m1_sd, m1_nn = abs(sd("W2", "봇") - sd("W2", "사람")), abs(nn("W2", "봇") - nn("W2", "사람"))
    m2_sd, L1 = abs(sd("W1", "봇") - sd("W0", "봇")), r["W1"]["AUC"]["L"]
    t_m1 = [test(m1_sd, "<=", 0.010), test(m1_nn, "<=", 0.010)]
    t_m2 = [test(m2_sd, "<=", 0.015), test(L1[0], "<=", 0.60), test(L1[2], "<=", 0.60)]
    M1 = {"SD차": m1_sd, "이웃차": m1_nn, "검사": t_m1,
          "엄격": all(t["통과"] for t in t_m1), "느슨": bool(m1_sd <= 0.010 and m1_nn <= 0.010)}
    M2 = {"봇SD변화": m2_sd, "W1_L_AUC": L1, "검사": t_m2,
          "엄격": all(t["통과"] for t in t_m2), "느슨": bool(m2_sd <= 0.015 and L1[0] <= 0.60)}
    gap = lambda f, w: f(w, "사람") - f(w, "봇")
    M3 = {"SD": 1 - gap(sd, "W3") / gap(sd, "W0"), "이웃": 1 - gap(nn, "W3") / gap(nn, "W0")}
    return {"M1": M1, "M2": M2, "M3": M3}


def run(bundle):
    ids, info, order, X = C.read_table(C.TABLE["fox8"])
    split = C.read_json(C.DATA / "records/split_fox8.json")
    dev, conf, _ = make_split(ids, info)
    C.check(dev == split["개발"] and conf == split["확인"], "fox8 고정 분할 불일치")
    C.check(not set(dev) & set(conf) and set(dev)|set(conf) == set(ids), "분할 중복/누락")
    C.check(order == bundle["feature_order"], "학습/외부 자료 자질 순서 불일치")
    pos = {u:i for i,u in enumerate(ids)}
    rows = np.array([pos[u] for u in conf])
    Xc = X[rows]
    y = np.array([int(info["라벨"][i] == "bot") for i in rows])
    src = np.array([info["자료원"][i] for i in rows])
    C.check(int(y.sum()) == 547 and len(y) == 996, "확인 집합 크기 불일치")
    C.check(dict(Counter(src[y==0])) == SRC_EXPECT, "사람 자료원 구성 불일치")
    tids, _, torder, TX = C.read_table(C.TABLE["fox8_trunc"])
    C.check(tids == ids and torder == order, "절단 제거 자료의 행/열 불일치")
    Xt = TX[rows]
    excluded = C.read_json(C.DATA / "records/excluded_fox8.json")["uids"]
    keep = ~np.isin(conf, excluded)
    C.check(len(excluded) == 686 and int((~keep).sum()) == 348, "문구 제외 계정 불일치")
    prep, confset = bundle["prep"], set(conf)
    uids = np.array(conf)
    out = {"집합":{}, "하위표집":{}}

    def evaluate_one(key, code, name, values, mask, worlds):
        r = run_set(key,code,name,values[mask],y[mask],uids[mask].tolist(),confset,bundle,prep,worlds)
        C.say(name, "L/G/S:", [round(r["W0"]["AUC"][s][0],6) for s in ("L","G","S")])
        return r

    all_rows = np.ones(len(y), dtype=bool)
    out["집합"]["501"] = evaluate_one((501,),501,"확인 절반 전체",Xc,all_rows,True)
    bot_uids = np.array(sorted(u for u,l in zip(conf,y) if l == 1))
    for p in LEVELS:
        out["하위표집"][f"{p}%"] = []
        nb = int(round(449*p/(100-p)))
        for seed in SEEDS:
            chosen = np.sort(np.random.default_rng([SEED_W,EXP,2,p,seed]).choice(bot_uids,nb,replace=False))
            mask = (y==0) | np.isin(uids,chosen)
            r = evaluate_one((600+p,seed),None,f"(A) 봇 {p}% 시드 {seed}",Xc,mask,False)
            r.update({"시드":seed,"뽑은봇":chosen.tolist()})
            out["하위표집"][f"{p}%"].append(r)
    for i,s in enumerate(sorted(SRC_EXPECT)):
        for code,mask,name in ((511+i,(y==1)|(src==s),f"(B) 봇 + {s}"),
                              (521+i,(y==1)|((y==0)&(src!=s)),f"(B) {s} 제외")):
            out["집합"][str(code)] = evaluate_one((code,),code,name,Xc,mask,False)
    out["집합"]["531"] = evaluate_one((531,),531,"(C) 절단 꼬리 제거 판",Xt,all_rows,True)
    out["집합"]["541"] = evaluate_one((541,),541,"(D) 문구 계정 제외",Xc,keep,True)
    C.write_json(C.RESULTS / "evaluation.json",out)
    return out
