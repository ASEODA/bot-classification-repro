"""고정된 연구 수치 계산. 원 함수의 계산 순서·시드·반올림 규칙을 유지한다."""
import csv
import hashlib
import json
import math
import os
import random
import re
import statistics
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import rankdata, mannwhitneyu, false_discovery_control
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
WORK = RESULTS / ".work"
BOTSIM_RAW = WORK / "botsim"
UD_DIR = WORK / "ud-ewt"
FOX8_DB = WORK / "fox8.sqlite"
STANZA_DIR = WORK / "models" / "stanza"
TABLE = {k: RESULTS / "features" / (k + ".csv") for k in
         ("botsim", "comments", "politics", "fox8", "fox8_trunc")}

SEED = 20260926
MATCH_SEED_BOTSIM = 20260827
CALIPER = 0.10
DELTA_NOTABLE = 0.147
MIN_DOCS = 10
MAX_DOCS = 200
LANG_TARGET = "en"
META_COLS = ["문서수", "문장수", "토큰수", "토큰수_구두점제외"]
BLOCKS_B = {"F": ("F",), "M": ("M형태", "M품사"), "R": ("R",)}
RKEYS = ["문장당_토큰수", "구두점_비율", "문장길이_변동계수"]
RATE_DIGITS = 6
MIN_SENTENCES_CV = 5
N_PERM = 10_000
CAP = 5
REL_TOL = 1e-12
PROPOSAL_WEIGHTS = (0.5, 0.5)
NAN = float("nan")
MIN_CHARS = 20
SELF_REVEAL = re.compile(
    r"(as an ai language model"
    r"|i'?m sorry,? but (i cannot|as an ai)"
    r"|i cannot (comply|fulfill|browse)"
    r"|openai'?s? (content )?polic)", re.I)
RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
RE_URL = re.compile(r"(https?://\S+|www\.\S+)")
RE_MENTION = re.compile(r"@\w+")
RE_WS = re.compile(r"\s+")

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def say(*args):
    print(*args, flush=True)


def line(title=""):
    say("\n" + "=" * 74)
    if title:
        say(title)
        say("=" * 74)


def label_use(where):
    """라벨을 쓰는 지점마다 같은 꼴의 마커를 찍는다."""
    say(f"  [라벨 사용] {where}")


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _inside_code(path):
    p = Path(path).resolve()
    if RESULTS not in p.parents:
        raise PermissionError(f"results/ 밖 쓰기 금지: {p}")
    return p


def write_json(path, obj, indent=1):
    p = _inside_code(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(jsonable(obj), f, ensure_ascii=False, indent=indent, allow_nan=False)
    os.replace(tmp, p)


def write_text(path, text):
    p = _inside_code(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def jsonable(o):
    """numpy 값을 파이썬 값으로. NaN · inf는 None."""
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return [jsonable(v) for v in o.tolist()]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        x = float(o)
        return None if (math.isnan(x) or math.isinf(x)) else x
    return o


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def normalize_apostrophe(s):
    """[04] 굽은 아포스트로피(U+2019)를 곧은 것으로. 토큰과 목록 양쪽에 건다."""
    return s.replace("’", "'")


def funcword_list(raw_words):
    """[04 · 10] 02 목록 174종 → 정규화 · 정렬 172종, 해시 앞 16자."""
    words = sorted({normalize_apostrophe(w) for w in raw_words})
    h = hashlib.sha256("\n".join(words).encode("utf-8")).hexdigest()[:16]
    return words, h


def axis_of(key):
    return key.split("=", 1)[0]


def build_axis_map(accounts):
    """[07] 자료 전체(라벨 없음)에서 축별 값 종류를 모은다."""
    axis_values = {}
    for a in accounts.values():
        for key in a.get("자질", {}):
            axis, sep, val = key.partition("=")
            if not sep:
                axis, val = key, ""
            axis_values.setdefault(axis, set()).add(val)
    return {ax: sorted(vs) for ax, vs in axis_values.items()}


def f_rates(a, keys):
    """[05 · 11] 기능어 카운트 / 토큰수_구두점제외, 6자리 반올림. 없는 키는 0회."""
    w = a["토큰수_구두점제외"]
    return [round(a["기능어"].get(k, 0) / w, RATE_DIGITS) if w else None for k in keys]


def m_ratios(a, keys, axis_map):
    """[07 · 11] 대립값 2 이상 축은 축 내부 합, 1개면 토큰수_구두점제외. 분모 0은 결측."""
    feats = a.get("자질", {})
    denom_tok = a.get("토큰수_구두점제외", 0)
    axis_total = {}
    for k, n in feats.items():
        axis_total[axis_of(k)] = axis_total.get(axis_of(k), 0) + n
    row = []
    for k in keys:
        cnt = feats.get(k, 0)
        if len(axis_map.get(axis_of(k), [""])) >= 2:
            d = axis_total.get(axis_of(k), 0)
        else:
            d = denom_tok
        row.append(None if d == 0 else cnt / d)
    return row


def upos_ratios(a, keys):
    """[07 · 11] 품사 카운트 / 토큰수_구두점제외."""
    pos = a.get("UPOS", {})
    d = a.get("토큰수_구두점제외", 0)
    return [None if d == 0 else pos.get(k, 0) / d for k in keys]


def rhythm(a):
    """[08 · 11] 문장당 토큰수, 구두점 비율, 변동계수(표본표준편차, 문장 5개 미만 결측)."""
    tok, tok_np, n_sent = a["토큰수"], a["토큰수_구두점제외"], a["문장수"]
    lengths = a["문장길이"]
    assert len(lengths) == n_sent and sum(lengths) == tok_np, "문장길이 정합 실패"
    r1 = tok_np / n_sent if n_sent > 0 else None
    r2 = (tok - tok_np) / tok if tok > 0 else None
    r3 = None
    if n_sent >= MIN_SENTENCES_CV:
        mean = sum(lengths) / n_sent
        if mean > 0:
            r3 = statistics.stdev(lengths) / mean
    return [r1, r2, r3]


def build_matrix(accounts, ids, keys, axis_map):
    """[11] (len(ids) x 250) 행렬. 결측 NaN. 열 순서 F · M형태 · M품사 · R."""
    rows = []
    for u in ids:
        a = accounts[u]
        rows.append(f_rates(a, keys["F"]) + m_ratios(a, keys["M형태"], axis_map)
                    + upos_ratios(a, keys["M품사"]) + rhythm(a))
    return np.array([[NAN if v is None else v for v in r] for r in rows], dtype=float)


def feature_keys(accounts, function_words):
    """자질 250 키. F = 정규화 기능어 172, M형태 · M품사 = 1,869계정 전체 키 합집합 정렬(07과 같음)."""
    return {"F": list(function_words),
            "M형태": sorted({k for a in accounts.values() for k in a.get("자질", {})}),
            "M품사": sorted({k for a in accounts.values() for k in a.get("UPOS", {})}),
            "R": list(RKEYS)}


def feature_order(keys):
    return [(b, k) for b in ("F", "M형태", "M품사", "R") for k in keys[b]]


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, (float, np.floating)):
        return "" if math.isnan(v) else repr(float(v))
    return str(v)


def write_table(path, ids, info_cols, info, order, X):
    """ids 행, info_cols(라벨 · 메타) 열 + 자질 250 열."""
    p = _inside_code(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uid"] + info_cols + [f"{b}|{k}" for b, k in order])
        for i, u in enumerate(ids):
            w.writerow([u] + [_cell(info[u][c]) for c in info_cols] + [_cell(v) for v in X[i]])


def read_table(path):
    """반환: ids, info(열 이름 → 값 목록), order, X."""
    with open(path, encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        head = next(r)
        feat_start = next(i for i, h in enumerate(head) if "|" in h)
        info_cols = head[1:feat_start]
        order = [tuple(h.split("|", 1)) for h in head[feat_start:]]
        ids, info, rows = [], {c: [] for c in info_cols}, []
        for row in r:
            ids.append(row[0])
            for c, v in zip(info_cols, row[1:feat_start]):
                info[c].append(v)
            rows.append([float(v) if v != "" else NAN for v in row[feat_start:]])
    X = np.array(rows, dtype=float)
    for c in info_cols:
        vals = info[c]
        try:
            info[c] = [int(v) for v in vals]
        except ValueError:
            try:
                info[c] = [float(v) if v != "" else None for v in vals]
            except ValueError:
                pass
    return ids, info, order, X


def bh(ps):
    m = len(ps)
    order = sorted(range(m), key=ps.__getitem__)
    qs, running = [1.0] * m, 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, ps[i] * m / rank)
        qs[i] = running
    if ps:
        assert np.allclose(qs, false_discovery_control(np.asarray(ps, dtype=float), method='bh'),
                           rtol=1e-12, atol=1e-15)
    return qs


def mw(x, y):
    """순위 · 동점 보정은 독립 계산, SciPy p값과 전 항목 교차 검산. 델타 = 봇 - 사람 Cliff δ."""
    if not x or not y:
        return {'U': None, 'p': None, '델타': None, 'z': None}
    nx, ny = len(x), len(y)
    n = nx + ny
    indexed = sorted([(v, 0) for v in x] + [(v, 1) for v in y])
    rank_sum, tie_sum, i = 0.0, 0.0, 0
    while i < n:
        j = i + 1
        while j < n and indexed[j][0] == indexed[i][0]:
            j += 1
        rank_sum += ((i + 1 + j) / 2) * sum(group == 0 for _, group in indexed[i:j])
        t = j - i
        tie_sum += t ** 3 - t
        i = j
    u = rank_sum - nx * (nx + 1) / 2
    variance = nx * ny / 12 * ((n + 1) - tie_sum / (n * (n - 1)))
    difference = u - nx * ny / 2
    if variance > 0:
        zabs = max(0.0, abs(difference) - 0.5) / math.sqrt(variance)
        z = math.copysign(zabs, difference)
        p = math.erfc(zabs / math.sqrt(2))
    else:
        z, p = 0.0, 1.0
    chk = mannwhitneyu(x, y, alternative='two-sided', method='asymptotic', use_continuity=True)
    assert u == chk.statistic
    assert math.isclose(p, chk.pvalue, rel_tol=1e-9, abs_tol=1e-300), (p, chk.pvalue)
    return {'U': u, 'p': p, '델타': 2 * u / (nx * ny) - 1, 'z': z}


def summary(values):
    if not values:
        return {'Q1': None, '중앙': None, 'Q3': None, 'IQR': None}
    if len(values) == 1:
        q1 = med = q3 = values[0]
    else:
        q1, med, q3 = statistics.quantiles(values, n=4, method='inclusive')
    return {'Q1': q1, '중앙': med, 'Q3': q3, 'IQR': q3 - q1}


def col_values(X, j, rows):
    """행 번호 rows 의 j열 값 가운데 결측이 아닌 것(파이썬 float)."""
    v = X[rows, j]
    return [float(t) for t in v[~np.isnan(v)]]


def caliper_match(bot_ids, human_ids, logd, caliper, seed):
    """log 분모 차 +-caliper 이내 봇:사람 1:1 그리디. 봇 순서는 시드 고정 난수로 섞는다.
    거리가 같으면 human_ids 앞쪽이 이긴다. 반환: (쌍 [(봇, 사람, 거리)], 탈락 봇, 쓰인 사람)."""
    rng = random.Random(seed)
    order = list(bot_ids)
    rng.shuffle(order)
    used = set()
    pairs = []
    unmatched_bots = []
    for b in order:
        lb = logd[b]
        best, best_gap = None, None
        for h in human_ids:
            if h in used:
                continue
            gap = abs(logd[h] - lb)
            if gap > caliper:
                continue
            if best_gap is None or gap < best_gap:
                best, best_gap = h, gap
        if best is None:
            unmatched_bots.append(b)
        else:
            used.add(best)
            pairs.append((b, best, best_gap))
    return pairs, unmatched_bots, used


def nanmedian_cols(M):
    out = np.full(M.shape[1], np.nan)
    for j in range(M.shape[1]):
        v = M[:, j]
        v = v[~np.isnan(v)]
        if v.size:
            out[j] = np.median(v)
    return out


def nanmean_cols(M):
    out = np.full(M.shape[1], np.nan)
    for j in range(M.shape[1]):
        v = M[:, j]
        v = v[~np.isnan(v)]
        if v.size:
            out[j] = np.mean(v)
    return out


def centers(X, is_bot):
    """[라벨 사용 지점] 집단별 원값 중앙값."""
    return nanmedian_cols(X[is_bot]), nanmedian_cols(X[~is_bot])


def residuals(X, is_bot, c_bot, c_hum):
    C = np.where(is_bot[:, None], c_bot[None, :], c_hum[None, :])
    return X - C


def residual_scale(R):
    """척도 s_j = 전 계정 |r| 중앙값. 0이면 평균, 평균도 0 또는 정의 2개 미만이면 자질 제외."""
    A = np.abs(R)
    med, mean = nanmedian_cols(A), nanmean_cols(A)
    n_def = (~np.isnan(A)).sum(axis=0)
    s = np.full(R.shape[1], np.nan)
    kind = []
    for j in range(R.shape[1]):
        if n_def[j] < 2:
            kind.append("제외_정의2미만")
        elif med[j] > 0:
            s[j] = med[j]
            kind.append("중앙값")
        elif mean[j] > 0:
            s[j] = mean[j]
            kind.append("평균")
        else:
            kind.append("제외_0")
    return s, kind


def scaled_residuals(R, s):
    with np.errstate(invalid="ignore"):
        return np.minimum(np.abs(R) / s[None, :], CAP)


def block_distances(Z):
    used = (~np.isnan(Z)).sum(axis=1)
    with np.errstate(invalid="ignore"):
        d = np.nansum(Z, axis=1) / np.where(used > 0, used, np.nan)
    return d, used


def ratio_of(d_bot, d_hum):
    """비율 = 사람 거리 중앙값 / 봇 거리 중앙값. 1보다 크면 봇이 더 좁다."""
    return float(np.median(d_hum)) / float(np.median(d_bot))


def perm_ratios(d_bot, d_hum, swaps):
    b = np.where(swaps, d_hum[None, :], d_bot[None, :])
    h = np.where(swaps, d_bot[None, :], d_hum[None, :])
    return np.median(h, axis=1) / np.median(b, axis=1)


def p_values(obs, perm):
    perm = np.asarray(perm, dtype=float)
    ge = int(np.sum(perm >= obs * (1 - REL_TOL)))
    lo = abs(math.log(obs))
    ge2 = int(np.sum(np.abs(np.log(perm)) >= lo * (1 - REL_TOL)))
    n = perm.size
    return (ge + 1) / (n + 1), (ge2 + 1) / (n + 1), ge, ge2


def five(v):
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if v.size == 0:
        return {"n": 0}
    q1, q2, q3 = np.percentile(v, [25, 50, 75])
    return {"n": int(v.size), "최소": float(v.min()), "Q1": float(q1), "중앙": float(q2),
            "Q3": float(q3), "최대": float(v.max()), "평균": float(v.mean())}


def block_split(order):
    """자질 순서 → 동질성 세 블록(F · M · R)의 열 번호."""
    blocks_of = np.array([b for b, _ in order])
    return {B: np.where(np.isin(blocks_of, parts))[0] for B, parts in BLOCKS_B.items()}


def homogeneity(Xm, order, n_pairs, sparse_min, seed=SEED, n_perm=N_PERM, ids=None):
    """10 v1.3 전 절차. Xm 행 = 쌍 순서대로 봇 n 전부 → 사람 n 전부.
    반환 사전: 블록별 비율 · p · 거리 · 척도 요약, 희소 제외 민감도."""
    cols = block_split(order)
    names = [k for _, k in order]
    is_bot = np.array([True] * n_pairs + [False] * n_pairs)
    rng = np.random.default_rng(seed)
    swaps = rng.random((n_perm, n_pairs)) < 0.5           # 세 블록 · 민감도 공유 (10 결정 G)
    res, sens = {}, {}
    for B in ("F", "M", "R"):
        Xb = Xm[:, cols[B]]
        keys_b = [names[j] for j in cols[B]]
        cb, ch = centers(Xb, is_bot)
        R = residuals(Xb, is_bot, cb, ch)
        s, kind = residual_scale(R)
        Z = scaled_residuals(R, s)
        d, used = block_distances(Z)
        check(not np.isnan(d).any(), f"{B} 블록 거리 결측")
        d_bot, d_hum = d[:n_pairs], d[n_pairs:]
        check(np.median(d_bot) > 0, f"{B} 블록 봇 거리 중앙값 0")
        r = ratio_of(d_bot, d_hum)
        pr = perm_ratios(d_bot, d_hum, swaps)
        p1, p2, ge, ge2 = p_values(r, pr)
        qs = np.percentile(pr, [2.5, 50, 97.5])
        res[B] = {"자질수": len(keys_b), "비율": r, "p_단측": p1, "p_양측": p2, "관측이상_횟수": ge,
                  "봇_거리": five(d_bot), "사람_거리": five(d_hum),
                  "척도_종류별_수": {k: kind.count(k) for k in ("중앙값", "평균", "제외_0", "제외_정의2미만")},
                  "결측칸": int(np.isnan(Xb).sum()),
                  "순열분포": {"Q2.5": float(qs[0]), "중앙": float(qs[1]), "Q97.5": float(qs[2]),
                           "최대": float(pr.max())}}
        if ids is not None:
            res[B]["계정별_거리"] = {"봇": dict(zip(ids[:n_pairs], map(float, d_bot))),
                                "사람": dict(zip(ids[n_pairs:], map(float, d_hum)))}
        # 희소 제외 민감도 (10 결정 O): 원값 0 계정이 한 집단에서 sparse_min 이상인 자질을 뺀다.
        zero = (Xb == 0)
        zb, zh = zero[is_bot].sum(axis=0), zero[~is_bot].sum(axis=0)
        drop = (zb >= sparse_min) | (zh >= sparse_min)
        keep = ~drop
        ds, _ = block_distances(Z[:, keep])
        check(not np.isnan(ds).any(), f"민감도 {B} 블록 거리 결측")
        sb, sh = ds[:n_pairs], ds[n_pairs:]
        rs = ratio_of(sb, sh)
        prs = perm_ratios(sb, sh, swaps)
        ps1, ps2, gs, _ = p_values(rs, prs)
        sens[B] = {"문턱": sparse_min, "제외_자질수": int(drop.sum()), "남은_자질수": int(keep.sum()),
                   "제외_자질": [keys_b[j] for j in range(len(keys_b)) if drop[j]],
                   "비율": rs, "p_단측": ps1, "p_양측": ps2, "관측이상_횟수": gs}
    return {"블록별": res, "민감도_희소제외": sens, "교환행렬_digest": hashlib.sha256(swaps.tobytes()).hexdigest()}


def fit_prep(Xtr, fitted_on):
    """학습 행만으로 자질별 백분위 함수(xp, fp)와 원값 중앙값."""
    d = Xtr.shape[1]
    xp, fp, med = [], [], np.empty(d)
    for j in range(d):
        v = Xtr[:, j]
        v = v[~np.isnan(v)]
        assert v.size > 0, f"{j}번 자질이 학습 fold에서 전부 결측"
        med[j] = np.median(v)
        uniq = np.unique(v)
        if v.size == 1 or uniq.size == 1:
            xp.append(uniq.copy())
            fp.append(np.array([0.5]))
            continue
        r = rankdata(v, method="average")
        p = (r - 1.0) / (v.size - 1.0)
        order = np.argsort(v, kind="mergesort")
        vs, ps = v[order], p[order]
        first = np.concatenate(([True], vs[1:] != vs[:-1]))
        xp.append(vs[first].copy())
        fp.append(ps[first].copy())
    return {"xp": xp, "fp": fp, "median": med, "fitted_on": np.asarray(fitted_on).copy()}


def apply_prep(prep, X):
    Xf = np.where(np.isnan(X), prep["median"][None, :], X)
    P = np.empty_like(Xf)
    for j in range(X.shape[1]):
        P[:, j] = np.clip(np.interp(Xf[:, j], prep["xp"][j], prep["fp"][j]), 0.0, 1.0)
    return P


def make_folds(units, y, k, rng):
    """단위(쌍) 묶음으로 k겹. 단위의 라벨 구성으로 층화. 반환: 행 번호 → fold."""
    kinds = {}
    for ui, u in enumerate(units):
        kinds.setdefault(tuple(sorted(int(y[i]) for i in u)), []).append(ui)
    assign = {}
    for kind in sorted(kinds):
        idx = np.array(kinds[kind])
        perm = idx[rng.permutation(idx.size)]
        for f, chunk in enumerate(np.array_split(perm, k)):
            for ui in chunk:
                for i in units[ui]:
                    assign[int(i)] = f
    return assign


def ranks(values):
    return (rankdata(values, method="average", axis=0) - 1.0) / (len(values) - 1.0)


def density(matrix, ks):
    """[14 · 11] 묶음 안 열 중앙값 대치 → 묶음 안 백분위 → L1 평균 거리 → k번째 이웃 거리의 음수. 라벨 없음."""
    check(matrix.ndim == 2 and len(matrix) > max(ks), "행렬 크기 또는 k 오류")
    check(not np.isinf(matrix).any(), "자질에 무한값 존재")
    check(not np.isnan(matrix).all(axis=0).any(), "열 전체 결측")
    medians = np.nanmedian(matrix, axis=0)
    imputed = np.where(np.isnan(matrix), medians, matrix)
    percentiles = ranks(imputed)
    distances = cdist(percentiles, percentiles, metric="cityblock") / matrix.shape[1]
    np.fill_diagonal(distances, np.inf)
    ordered = np.partition(distances, [k - 1 for k in ks], axis=1)
    scores = {k: -ordered[:, k - 1] for k in ks}
    return scores, medians, percentiles, distances


def rank_mean(s_pos, s_dens):
    """제안(결합) 점수: 묶음 안 평균 순위 1:1 평균 r, 점수 = (r - 1)/(n - 1)."""
    n = len(s_pos)
    assert n == len(s_dens) and n >= 2
    w_pos, w_dens = PROPOSAL_WEIGHTS
    r = w_pos * rankdata(s_pos, method="average") + w_dens * rankdata(s_dens, method="average")
    return (r - 1.0) / (n - 1.0)


def boot_counts(key, strata, R):
    """부트스트랩 재추출 행렬 (R x 단위 수). 시드 [20260926, 열쇠...]."""
    rng = np.random.default_rng([SEED, *key])
    strata = np.asarray(strata)
    W = np.zeros((R, len(strata)))
    for s in sorted(set(strata.tolist())):
        idx = np.where(strata == s)[0]
        W[:, idx] = rng.multinomial(idx.size, np.full(idx.size, 1.0 / idx.size), size=R)
    return W


def cmp_matrix(sb, sh):
    return (sb[:, None] > sh[None, :]).astype(float) + 0.5 * (sb[:, None] == sh[None, :])


def boot_auc(C, Wb, Wh):
    return ((Wb @ C) * Wh).sum(axis=1) / (Wb.sum(axis=1) * Wh.sum(axis=1))


def ci95(dist):
    lo, hi = np.percentile(dist, [2.5, 97.5])
    return [float(lo), float(hi)]


def auc_boot(s, bidx, hidx, Wb, Wh):
    C = cmp_matrix(s[bidx], s[hidx])
    pt = float(C.mean())
    ref = roc_auc_score(np.r_[np.ones(len(bidx)), np.zeros(len(hidx))], np.r_[s[bidx], s[hidx]])
    check(abs(pt - ref) < 1e-12, "비교 행렬 AUC != roc_auc_score")
    return pt, boot_auc(C, Wb, Wh)


def clean_doc(text):
    """1) 자기폭로 문장 절제 2) URL · 멘션 제거 3) 20자 검사. 반환 (정제문, 탈락사유, 절제여부)."""
    if not text:
        return None, "빈 문자열", False
    t = unicodedata.normalize("NFC", str(text))
    excised = False
    if SELF_REVEAL.search(t):
        sents = RE_SENT_SPLIT.split(t)
        kept = [s for s in sents if s.strip() and not SELF_REVEAL.search(s)]
        t = " ".join(kept)
        excised = True
        if not t.strip():
            return None, "자기폭로 절제 후 내용 없음", True
    t = RE_URL.sub(" ", t)
    t = RE_MENTION.sub(" ", t)
    t = RE_WS.sub(" ", t).strip()
    if len(t) < MIN_CHARS:
        reason = ("자기폭로 절제 후 " if excised else "") + f"{MIN_CHARS}자 미만"
        return None, reason, excised
    return t, None, excised


def fox8_sources(db_path=FOX8_DB):
    """fox8 users 표의 dataset 열(사람 자료원). 같은 ID가 여러 출처면 마지막 출처(DATA.md)."""
    import sqlite3
    import urllib.parse
    conn = sqlite3.connect("file:" + urllib.parse.quote(str(db_path)) + "?mode=ro", uri=True)
    try:
        return {u: (lab, ds) for u, lab, ds in conn.execute("SELECT user_id, label, dataset FROM users")}
    finally:
        conn.close()
