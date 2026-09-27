#!/usr/bin/env python3
"""14 사전선언 실행. 네트워크 없이 새 산출물만 쓰며 독립 프로세스 2회 검증한다."""

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import joblib
import numpy as np
import scipy
from scipy.spatial.distance import cdist
from scipy.stats import rankdata
import sklearn
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

HERE = Path(__file__).resolve().parent
DATA = Path("/Users/son/DM_LAB_data/12_OpenRouter")
PYTHON = "/Users/son/.claude/venvs/audio-transcribe/bin/python"
SEED = 20260926
N_BOOT = 2000
KS = (5, 10, 20)
FIELDS = ("기능어", "UPOS", "자질", "문장길이", "토큰수", "토큰수_구두점제외", "문장수", "구두점토큰수")
SCORES = ("위치", "밀도(k=10)", "위치+밀도", "밀도(k=5)", "밀도(k=20)")
CAVEAT = "단일 봇넷; 봇 글 98.3%가 2023년, 사람은 2020년 이전(연도 단독 AUC 1.000); 답글 비율 AUC 0.851"
FILES = {
    "사전선언": HERE / "14_이웃밀도_사전선언.md",
    "자질함수": HERE / "10_동질성검정.py",
    "11검산": HERE / "11_판별기.py",
    "축지도번들": HERE / "11_판별기_모델.joblib",
    "기능어": HERE / "02_기능어목록.json",
    "fox8자질": HERE / "13-1_fox8재파싱.json",
    "fox8위치": HERE / "13_fox8전이.json",
    "시험위치": HERE / "12_판별기v2.json",
    "BotSim위치": HERE / "11_판별기.json",
    "생성계정": DATA / "12-1_계정사전.json",
    "댓글계정": DATA / "13-0_계정사전.json",
    "13문턱규칙": HERE / "13_fox8전이.py",
    "13서술규칙": HERE / "13_fox8전이_사전선언.md",
    "13단서": HERE / "13_fox8전이.md",
}


def log(message):
    print(message, file=sys.stderr, flush=True)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def read_json(key):
    return json.loads(FILES[key].read_text(encoding="utf-8"))


def import_path(key, name):
    spec = importlib.util.spec_from_file_location(name, FILES[key])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ranks(values):
    return (rankdata(values, method="average", axis=0) - 1.0) / (len(values) - 1.0)


def density(matrix, ks):
    check(matrix.ndim == 2 and len(matrix) > max(ks), "행렬 크기 또는 k 오류")
    check(not np.isinf(matrix).any(), "자질에 무한값 존재")
    check(not np.isnan(matrix).all(axis=0).any(), "열 전체 결측: 사전선언의 중앙값을 정의할 수 없음")
    medians = np.nanmedian(matrix, axis=0)
    imputed = np.where(np.isnan(matrix), medians, matrix)
    percentiles = ranks(imputed)
    distances = cdist(percentiles, percentiles, metric="cityblock") / matrix.shape[1]
    np.fill_diagonal(distances, np.inf)
    ordered = np.partition(distances, [k - 1 for k in ks], axis=1)
    scores = {k: -ordered[:, k - 1] for k in ks}
    return scores, medians, percentiles, distances


def combine(position, density_scores):
    # 밀도 순위는 원래 채점 묶음 전체. 위치 순위만 관측 가능한 계정에서 계산한다.
    available = np.isfinite(position)
    result = np.full(len(position), np.nan)
    result[available] = (ranks(position[available]) + ranks(density_scores)[available]) / 2.0
    return result


def hand_gate():
    # 손계산 상수. A..F의 두 열은 각각 0, 1, 2가 두 번씩 있다.
    # 결측 E2의 관측 중앙값은 1. 두 열 평균순위는 1.5, 3.5, 5.5.
    # 백분위는 .1, .5, .9. L1 평균 거리는 아래 정수 행렬 / 5.
    x = np.array([[0, 0], [0, 1], [1, 0], [1, 2], [2, np.nan], [2, 2]], dtype=float)
    expected_p = np.array([[1, 1], [1, 5], [5, 1], [5, 9], [9, 5], [9, 9]]) / 10.0
    expected_d = np.array([[0, 1, 1, 3, 3, 4], [1, 0, 2, 2, 2, 3],
                           [1, 2, 0, 2, 2, 3], [3, 2, 2, 0, 2, 1],
                           [3, 2, 2, 2, 0, 1], [4, 3, 3, 1, 1, 0]]) / 5.0
    expected_k = np.array([1, 2, 2, 2, 2, 1]) / 5.0
    expected_dr = np.array([9, 3, 3, 3, 3, 9]) / 10.0
    expected_combined = np.array([9, 5, 7, 9, 11, 19]) / 20.0
    s, med, p, d = density(x, (2,))
    check(np.isinf(np.diag(d)).all(), "손 예제: 자기 자신 제외 실패")
    np.fill_diagonal(d, 0.0)
    actual = [med, p, d, -s[2], ranks(s[2]), combine(np.arange(6.0), s[2])]
    expected = [[1.0, 1.0], expected_p, expected_d, expected_k, expected_dr, expected_combined]
    for got, want in zip(actual, expected):
        np.testing.assert_allclose(got, want, rtol=0, atol=1e-12)
    log("손 예제 통과: 6x2, k=2, 거리 행렬/5, k거리=[.2,.4,.4,.4,.4,.2], 합성=[.45,.25,.35,.45,.55,.95]")
    names = ("중앙값", "백분위", "거리", "k번째거리", "밀도순위", "순위평균")
    return {"통과": True, "k": 2, "허용오차": 1e-12,
            "손계산": {n: np.asarray(v).tolist() for n, v in zip(names, expected)},
            "실제": {n: v.tolist() for n, v in zip(names, actual)}}


def source_gate():
    source = Path(__file__).read_text(encoding="utf-8")
    marker = "[" + "라벨 사용" + "]"
    tree = ast.parse(source)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            lines = source.splitlines()[node.lineno - 1:node.end_lineno]
            for i, line in enumerate(lines, node.lineno):
                if marker in line:
                    found[node.name] = i
            for child in ast.walk(node):
                if isinstance(child, ast.Subscript) and isinstance(child.slice, ast.Constant) and child.slice.value == "라벨":
                    check(node.name in ("evaluate_auc", "adapt_fox"), "평가 외 라벨 접근")
    check(source.count(marker) == 2 and set(found) == {"evaluate_auc", "adapt_fox"}, "마커 위치 오류")
    check(all(chr(c) not in source for c in (0x2013, 0x2014)), "금지 문자 포함")
    # 13 D가 사용하는 함수와 11 원본이 실제로 같은지 코드 본문을 대조한다.
    bodies = []
    for key in ("11검산", "13문턱규칙"):
        parsed = ast.parse(FILES[key].read_text(encoding="utf-8"))
        fun = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == "choose_threshold")
        bodies.append(ast.dump(ast.Module(body=fun.body[1:], type_ignores=[]), include_attributes=False))
    check(bodies[0] == bodies[1], "11과 13 D의 문턱 선택 규칙 불일치")
    return {"통과": True, "마커_함수별행": found, "직접라벨접근_평가두함수만": True, "13D_문턱함수_11과동일": True}


def build_features(accounts, order, axis_map, f10, f11):
    ids = sorted(accounts)
    # 자질 함수로 라벨, 집단, 역할, 모델 정보를 전달하지 않는다.
    pure = {u: {k: accounts[u][k] for k in FIELDS} for u in ids}
    keys = {block: [key for b, key in order if b == block] for block in ("F", "M형태", "M품사", "R")}
    rates, undefined = f10.compute_rates(pure)
    check(not undefined, "기능어 사용률 분모 0")
    morph, _, _ = f10.compute_ratios(pure, keys["M형태"], axis_map)
    upos, _ = f10.compute_upos_ratios(pure, keys["M품사"])
    rhythm = f10.compute_features(pure)
    blocks = {"F": {u: rates[u]["사용률"] for u in ids}, "M형태": morph, "M품사": upos, "R": rhythm}
    matrix = np.array([[blocks[b][u].get(k, 0.0) if b == "F" else blocks[b][u][k]
                        for b, k in order] for u in ids], dtype=float)
    ref = f11.build_matrix(pure, ids, keys, axis_map)
    check(matrix.shape == (len(ids), 250), "250자질 불일치")
    check(np.array_equal(matrix, ref, equal_nan=True), "10 함수와 11 자질 행렬 불일치")
    return ids, matrix


def evaluate_auc(name, accounts, ids, scores, expected_counts):
    log(f"[라벨 사용] AUC: {name}, 층별 계정 bootstrap {N_BOOT}회, seed={SEED}" + ("; " + CAVEAT if name == "fox8" else ""))
    y = np.array([{"bot": 1, "human": 0}[accounts[u]["라벨"]] for u in ids])
    counts = {"봇": int(y.sum()), "사람": int((y == 0).sum())}
    check((counts["봇"], counts["사람"]) == expected_counts, "고정 표본수 불일치")

    def bootstrap(index, names):
        labels = y[index]
        matrix = np.column_stack([scores[n][index] for n in names])
        b, h = np.flatnonzero(labels == 1), np.flatnonzero(labels == 0)
        check(len(b) > 0 and len(h) > 0 and np.isfinite(matrix).all(), "AUC 입력 오류")
        n_b, n_h = len(b), len(h)
        point = (rankdata(matrix, method="average", axis=0)[b].sum(axis=0) - n_b * (n_b + 1) / 2) / (n_b * n_h)
        for j in range(len(names)):
            check(abs(point[j] - roc_auc_score(labels, matrix[:, j])) < 1e-12, "AUC sklearn 검산 실패")
        rng = np.random.default_rng(SEED)
        draws = np.empty((N_BOOT, len(names)))
        # 같은 재추출 계정을 모든 점수에 적용한다. 원래 묶음의 점수는 고정한다.
        for r in range(N_BOOT):
            sample = np.r_[rng.choice(b, n_b, replace=True), rng.choice(h, n_h, replace=True)]
            ranked = rankdata(matrix[sample], method="average", axis=0)
            draws[r] = (ranked[:n_b].sum(axis=0) - n_b * (n_b + 1) / 2) / (n_b * n_h)
        metrics = {n: {"AUC": float(point[j]), "CI95": np.quantile(draws[:, j], [0.025, 0.975]).tolist(),
                       "n": len(index), "봇": n_b, "사람": n_h} for j, n in enumerate(names)}
        return metrics, draws

    full = np.arange(len(ids))
    common = np.flatnonzero(np.isfinite(scores["위치"]))
    if len(common) == len(ids):
        metrics, draws = bootstrap(full, SCORES)
        paired_metrics = metrics
        draw_names = SCORES
    else:
        metrics, _ = bootstrap(full, ("밀도(k=10)", "밀도(k=5)", "밀도(k=20)"))
        draw_names = ("위치", "밀도(k=10)", "위치+밀도")
        paired_metrics, draws = bootstrap(common, draw_names)
        metrics.update({n: paired_metrics[n] for n in ("위치", "위치+밀도")})
    diffs = {}
    for target, title in (("위치+밀도", "위치+밀도-위치"), ("밀도(k=10)", "밀도-위치")):
        delta = draws[:, draw_names.index(target)] - draws[:, draw_names.index("위치")]
        lo, hi = np.quantile(delta, [0.025, 0.975])
        diffs[title] = {"차": paired_metrics[target]["AUC"] - paired_metrics["위치"]["AUC"],
                        "CI95": [float(lo), float(hi)], "n": len(common),
                        "0포함": bool(lo <= 0 <= hi), "양수구간": bool(lo > 0)}
    return {"표본": counts, "AUC": metrics, "짝지은차": diffs,
            "위치가용_공통표본AUC": {n: paired_metrics[n] for n in ("위치", "밀도(k=10)", "위치+밀도")}}


def adapt_fox(accounts, ids, scores, f11):
    log("[라벨 사용] fox8 문턱 적응: 5겹 층화, 4겹에서 BA 최대 문턱, 남은 1겹 평가; " + CAVEAT)
    y = np.array([{"bot": 1, "human": 0}[accounts[u]["라벨"]] for u in ids])
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    folds = list(splitter.split(np.zeros(len(y)), y))
    fold_ids = np.empty(len(y), dtype=int)
    for i, (_, test) in enumerate(folds):
        fold_ids[test] = i + 1
    result = {}
    for name in ("위치", "밀도(k=10)", "위치+밀도"):
        s = scores[name]
        rows = []
        for i, (train, test) in enumerate(folds):
            threshold, train_ba = f11.choose_threshold(s[train], y[train])
            pred, truth = s[test] >= threshold, y[test]
            tp = int(np.sum(pred & (truth == 1)))
            fp = int(np.sum(pred & (truth == 0)))
            tn = int(np.sum(~pred & (truth == 0)))
            fn = int(np.sum(~pred & (truth == 1)))
            rows.append({"fold": i + 1, "학습n": len(train), "평가n": len(test), "문턱": threshold,
                         "학습균형정확도": train_ba, "균형정확도": .5 * (tp / (tp + fn) + tn / (tn + fp)),
                         "위_봇순도": tp / (tp + fp) if tp + fp else None,
                         "아래_사람순도": tn / (tn + fn) if tn + fn else None,
                         "혼동": {"TP": tp, "FN": fn, "FP": fp, "TN": tn}})
        means, defined = {}, {}
        for key in ("균형정확도", "위_봇순도", "아래_사람순도"):
            values = [r[key] for r in rows if r[key] is not None]
            means[key] = float(np.mean(values)) if values else None
            defined[key] = len(values)
        result[name] = {"겹평균": means, "정의된겹수": defined, "fold별": rows}
    return {"점수별": result, "계정별fold": dict(zip(ids, fold_ids.tolist())), "단서": CAVEAT}


def predictions(batches):
    wording = dict(re.findall(r"^- \*\*(P14-[a-d])\*\*: (.+)$", FILES["사전선언"].read_text(encoding="utf-8"), re.M))
    check(set(wording) == {"P14-a", "P14-b", "P14-c", "P14-d"}, "사전선언 예측 4개 추출 실패")
    a = batches["fox8"]["AUC"]["밀도(k=10)"]["AUC"]
    b = batches["fox8"]["짝지은차"]["위치+밀도-위치"]["CI95"]
    c = batches["OpenRouter 시험"]["AUC"]["밀도(k=10)"]["AUC"]
    d = batches["BotSim"]["AUC"]["밀도(k=10)"]["AUC"]
    values = {"P14-a": (a >= .80, a), "P14-b": (b[0] <= 0 <= b[1] or b[0] > 0, b),
              "P14-c": (c >= .80, c), "P14-d": (d >= .90, d)}
    return {k: {"원문": wording[k], "판정": "적중" if ok else "빗나감", "판정값": value}
            for k, (ok, value) in values.items()}


def pipeline():
    # 사전선언을 항상 첫 분석 입력으로 읽는다.
    FILES["사전선언"].read_text(encoding="utf-8")
    hashes = {str(p): sha(p) for p in FILES.values()}
    gates = {"손예제": hand_gate(), "소스": source_gate()}
    f10, f11 = import_path("자질함수", "step10"), import_path("11검산", "step11")
    bundle = joblib.load(FILES["축지도번들"])
    order, axis_map = bundle["feature_order"], bundle["axis_map"]
    words = sorted({f10.normalize_apostrophe(w) for w in read_json("기능어")["기능어"]})
    check(words == bundle["function_words"] == [k for b, k in order if b == "F"], "고정 기능어 목록 불일치")
    check([sum(b == block for b, _ in order) for block in ("F", "M형태", "M품사", "R")] == [172, 58, 17, 3], "자질 블록 불일치")
    fox = read_json("fox8자질")["계정"]
    fox_positions = {u: r["ver.1"]["위치(전부)"] for u, r in read_json("fox8위치")["시험c_판별기전이"]["계정별"].items()}
    generated, original = read_json("생성계정")["계정"], read_json("댓글계정")["계정"]
    test_positions = read_json("시험위치")["시험"]["보조"]["점수"]["ver.1"]["위치(전부)"]
    new = {u: a for u, a in generated.items() if a["쪽"] == "시험" and a["생성모델"].split("/")[-1] != "gpt-4o-mini"}
    check(len(new) == 252 and all(a["집단"] == "새모델" for a in new.values()), "새 모델 시험 252계정 불일치")
    humans = {u: original[u] for u in test_positions if u in original}
    check(len(humans) == 234 and all(a["집단"] == "사람" and a["봉인"] is True and "시험" in a["역할"] for a in humans.values()), "봉인 시험 사람 234 불일치")
    check(not set(new) & set(humans), "시험 계정 중복")
    test = {**new, **humans}
    check(set(test) == set(test_positions) and len(test) == 486, "12-3 시험 UID 집합 불일치")
    botsim = {u: a for u, a in original.items() if a["집단"] == "원봇" or (a["집단"] == "사람" and "표a" in a.get("역할", []))}
    check(len(botsim) == 1144, "BotSim 1144 불일치")
    check(set(fox) == set(fox_positions) and len(fox) == 1991, "fox8 UID 불일치")
    bot_positions = read_json("BotSim위치")["OOF점수"]["위치(전부)"]
    pure_bot = {u: {k: a[k] for k in FIELDS} for u, a in botsim.items()}
    observed_axis = f10.build_axis_map(pure_bot)
    batches = {}
    adaptation = None
    batch_inputs = [("fox8", fox, fox_positions, (1094, 897)),
                    ("OpenRouter 시험", test, test_positions, (252, 234)),
                    ("BotSim", botsim, bot_positions, (504, 640))]
    for name, accounts, positions, expected in batch_inputs:
        ids, matrix = build_features(accounts, order, axis_map, f10, f11)
        ds, medians, percentiles, _ = density(matrix, KS)
        position = np.array([positions.get(u, np.nan) for u in ids], dtype=float)
        check(np.all((position[np.isfinite(position)] >= 0) & (position[np.isfinite(position)] <= 1)), "위치 확률 범위 오류")
        combined = combine(position, ds[10])
        scores = {"위치": position, "위치+밀도": combined, **{f"밀도(k={k})": ds[k] for k in KS}}
        result = evaluate_auc(name, accounts, ids, scores, expected)
        result.update({"n": len(ids), "위치점수_결측n": int(np.isnan(position).sum()),
                       "위치점수_결측uid": [u for u, p in zip(ids, position) if np.isnan(p)],
                       "자질_10과11_완전일치": True, "결측수_열별": np.isnan(matrix).sum(axis=0).tolist(),
                       "대치중앙값": medians.tolist(), "백분위_digest": digest(percentiles.tolist()),
                       "계정별점수": {u: {key: float(values[i]) if np.isfinite(values[i]) else None
                                        for key, values in scores.items()} for i, u in enumerate(ids)}})
        if name == "fox8":
            result["단서"] = CAVEAT
            adaptation = adapt_fox(accounts, ids, scores, f11)
        batches[name] = result
        log(f"자질 검산 통과: {name}, {len(ids)}x250, 위치 결측 {result['위치점수_결측n']}")
    check(hashes == {str(p): sha(p) for p in FILES.values()}, "실행 중 입력 변경")
    settings = {
        "k": 10, "참고k": [5, 20], "seed": SEED, "bootstrap": N_BOOT,
        "순위": "(rankdata(method=average)-1)/(n-1)", "거리": "250열 백분위 절대차의 평균",
        "결측": "묶음별 열 중앙값. 열 전체 결측이면 중단", "축지도출처": str(FILES["축지도번들"]),
        "축지도": axis_map, "BotSim댓글_관측축지도_번들과동일": observed_axis == axis_map,
        "자질순서": order, "기능어정규화": "02 목록 U+2019를 U+0027로 바꿔 중복 제거: 174 -> 172",
        "합성결측처리": "밀도 계산 및 밀도 순위는 원래 묶음 전체. 위치 순위는 점수가 있는 계정에서만 정규화. 합성과 두 짝지은 차이는 위치 가용 계정만 평가",
        "bootstrap규칙": "묶음/평가집합별 default_rng(20260926), 봇과 사람 각각 원래 수만큼 복원추출, 모든 점수 공통 추출. 고정 점수 AUC의 percentile 2.5%, 97.5%, 선형 보간. 점수 재계산 없음",
        "문턱규칙": "13 D와 같은 11 choose_threshold: 고유 점수 후보, 점수 >= 문턱, BA 최대, 1e-12 동점 중 가장 작은 후보. 5겹 비가중 평균, 순도 분모 0이면 결측",
        "라벨경계": "사전 지정 집단/역할/시험 UID로 묶음 구성. 점수 함수에는 8개 원자질 필드만 전달. 평가 라벨은 AUC와 fox8 문턱 적응만 접근",
        "버전": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__, "joblib": joblib.__version__},
        "python": sys.executable, "실행코드_sha256": sha(__file__),
        "스레드": os.environ.get("CODEX_THREAD_ID"), "창": os.environ.get("ORCA_PANE_KEY"),
        "요청창": "0ae08c15-8d9c-4f8f-bbb8-dd0e05b60206:36336566-d15a-44fc-9355-7b22cbe1483c",
        "실행경로": "새 Codex 스레드. Orca status: stale_bootstrap/reachable=false; terminal list: runtime_unavailable",
    }
    gates["입력불변"] = True
    return {"설정": settings, "입력_sha256": hashes, "관문": gates, "묶음": batches,
            "fox8_문턱적응": adaptation, "예측": predictions(batches),
            "사전선언이탈": [], "구현명시": [settings["합성결측처리"], settings["bootstrap규칙"]],
            "한계": ["같은 묶음에 닮은 봇이 여럿 있을 때만 작동한다. 단독 봇은 잡지 못한다(캠페인 탐지 목적).",
                     "사람도 좁은 게시판에서 서로 닮으면 밀도가 오를 수 있다.",
                     "계정 bootstrap 구간은 고정 묶음 점수의 불확실성만 나타낸다. 독립 캠페인이나 새 묶음의 일반화 구간이 아니다.",
                     "BotSim의 기존 OOF 위치 점수와 댓글 한정 자질의 밀도 점수를 합친 보조 결과다.", CAVEAT]}


def interval(row, field="AUC"):
    return f"{row[field]:.6f} [{row['CI95'][0]:.6f}, {row['CI95'][1]:.6f}]"


def markdown(out):
    lines = ["# 14 이웃 밀도 점수", "", "> fox8 결과는 환경 전이 또는 환경 의존성 반박으로 쓰지 않는다.",
             "> " + CAVEAT, "", "## 고정 방법", "",
             "250자질(F 172, M 58+17, R 3), 10 함수 경로 import, 11 번들의 자질 순서와 축 지도 사용. 10과 11 자질 행렬 완전 일치.",
             "묶음 내 열 중앙값 대치, 평균순위 백분위 (r-1)/(n-1), L1 평균 거리의 10번째 다른 이웃까지 거리의 음수. k=5,20은 참고이며 판정에 쓰지 않는다.",
             "합성은 위치와 k=10 밀도의 묶음 내 순위 백분위를 1:1 평균한다. 위치는 기존 ver.1 점수이며 새로 적합하지 않는다.",
             out["설정"]["합성결측처리"], out["설정"]["bootstrap규칙"], out["설정"]["문턱규칙"], "",
             "## AUC와 95% 구간", "", "| 묶음 | 점수 | n | AUC [95% CI] |", "|---|---|---:|---|"]
    for name, batch in out["묶음"].items():
        suffix = "[^fox8]" if name == "fox8" else ""
        for score in SCORES:
            row = batch["AUC"][score]
            lines.append(f"| {name}{suffix} | {score} | {row['n']} | {interval(row)} |")
    lines += ["", "## 짝지은 AUC 차", "", "| 묶음 | 차이 | 공통 n | 차 [95% CI] |", "|---|---|---:|---|"]
    for name, batch in out["묶음"].items():
        suffix = "[^fox8]" if name == "fox8" else ""
        for title, row in batch["짝지은차"].items():
            lines.append(f"| {name}{suffix} | {title} | {row['n']} | {interval(row, '차')} |")
    missing = out["묶음"]["BotSim"]["위치점수_결측n"]
    lines += ["", f"BotSim 위치 결측 {missing}계정. 밀도 단독 주 결과는 1,144계정, 위치·합성·두 차이는 {1144-missing}계정이다.",
              "", "## fox8 문턱 적응 (보조)", "", "순위·밀도는 전체 묶음에서 라벨 없이 고정하고 문턱만 4겹 라벨로 고른다.[^fox8]",
              "", "| 점수 | 5겹 평균 균형정확도 | 위 봇 순도 | 아래 사람 순도 |", "|---|---:|---:|---:|"]
    for name, data in out["fox8_문턱적응"]["점수별"].items():
        m = data["겹평균"]
        fmt = lambda v: "결측" if v is None else f"{v:.6f}"
        lines.append(f"| {name}[^fox8] | {fmt(m['균형정확도'])} | {fmt(m['위_봇순도'])} | {fmt(m['아래_사람순도'])} |")
    lines += ["", "| 점수 | 겹 | 학습 n | 평가 n | 문턱 | 균형정확도 | 위 봇 순도 | 아래 사람 순도 |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, data in out["fox8_문턱적응"]["점수별"].items():
        for row in data["fold별"]:
            lines.append(f"| {name}[^fox8] | {row['fold']} | {row['학습n']} | {row['평가n']} | {row['문턱']:.12g} | {fmt(row['균형정확도'])} | {fmt(row['위_봇순도'])} | {fmt(row['아래_사람순도'])} |")
    lines += ["", "## 예측: 원문과 기계 판정", "", "| 예측 | 사전선언 원문 | 판정값 | 판정 |", "|---|---|---|---|"]
    for key, row in out["예측"].items():
        suffix = "[^fox8]" if key in ("P14-a", "P14-b") else ""
        lines.append(f"| {key}{suffix} | {row['원문']} | {row['판정값']} | {row['판정']} |")
    lines += ["", "P14-b는 차이 구간이 0을 포함하거나 구간 전체가 양수이면 적중이다. 상한이 0보다 작을 때만 빗나감으로 판정한다.[^fox8]",
              "", "## 관문과 실행", "", "- 손 예제: 6계정 x 2자질, k=2. 중앙값, 백분위, 거리 행렬, k번째 거리, 밀도 순위, 합성을 고정 손계산 상수와 대조하여 통과.",
              "- 손계산 k번째 거리: [0.2, 0.4, 0.4, 0.4, 0.4, 0.2]. 합성: [0.45, 0.25, 0.35, 0.45, 0.55, 0.95].",
              "- 별도 Python 프로세스에서 전체 파이프라인 2회 실행. 계정별 점수, 전처리, 구간, 겹별 문턱, 예측, 입력 해시를 포함한 canonical JSON digest 일치.",
              f"- 결정성 digest: `{out['결정성']['digest'][0]}`",
              "- 소스 마커는 AUC 평가 함수와 fox8 문턱 적응 함수 각 1곳뿐이다. 로그도 같은 두 단계에서만 출력한다.",
              "- 평가 라벨 접근도 두 함수뿐이며 점수 함수에는 원자질 필드만 전달한다. 사전 지정 묶음 선택에는 집단·역할 메타데이터를 사용한다.",
              "- 입력 파일 실행 전후 sha256 일치. 기존 파일 보존 검증 통과. 네트워크 미사용. pyc 쓰기 비활성화.",
              f"- 실행: {out['설정']['실행경로']}. thread `{out['설정']['스레드']}`.",
              f"- 실행 코드 sha256: `{out['설정']['실행코드_sha256']}`", "", "## 입력 sha256", "", "| 입력 | sha256 |", "|---|---|"]
    for path, value in out["입력_sha256"].items():
        lines.append(f"| `{path}` | `{value}` |")
    lines += ["", "## 이탈과 한계", "", "- 분석 변경 없음. BotSim 위치 결측은 사용자 지시대로 공통 가용 계정에서만 위치·합성·짝지은 차이를 평가한다.",
              "- 결측 위치 순위를 임의 대치하지 않았다. 밀도 백분위의 기준 묶음은 축소하지 않았다."]
    lines += ["- " + item for item in out["한계"]]
    lines += ["", "성공 범위에서는 동질성을 라벨·중심 없이 판별에 쓰는 형태다. 사전 예측을 빗나간 범위는 그대로 후속 과제의 근거로 남긴다.",
              "", "[^fox8]: " + CAVEAT, ""]
    return "\n".join(lines)


def main():
    check(sys.executable == PYTHON, "지정 Python 인터프리터로 실행해야 함")
    outputs = [HERE / f"14_이웃밀도{s}" for s in (".json", ".md", "_출력.log")]
    check(not any(p.exists() for p in outputs), "기존 산출물 덮어쓰기 금지")
    baseline = {str(p): sha(p) for p in HERE.rglob("*") if p.is_file()}
    with outputs[2].open("x", encoding="utf-8") as logfile:
        def emit(text):
            print(text, flush=True)
            logfile.write(text + "\n")
            logfile.flush()

        emit("14 사전선언 실행: 새 Codex 스레드, 요청창 연결 실패(runtime_unavailable), 네트워크 미사용")
        runs, digests = [], []
        marker = "[" + "라벨 사용" + "]"
        for run in (1, 2):
            emit(f"전체 파이프라인 독립 프로세스 실행 {run}/2")
            process = subprocess.run([PYTHON, "-B", str(Path(__file__).resolve()), "--compute"],
                                     cwd=HERE, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                     capture_output=True, text=True, encoding="utf-8")
            emit(process.stderr.rstrip())
            check(process.returncode == 0, f"파이프라인 {run} 실패: {process.stdout[-1000:]}")
            marked = [line for line in process.stderr.splitlines() if marker in line]
            check(len(marked) == 4 and sum(line.startswith(marker + " AUC:") for line in marked) == 3
                  and sum(line.startswith(marker + " fox8 문턱 적응:") for line in marked) == 1, "로그 마커 경계 실패")
            result = json.loads(process.stdout)
            runs.append(result)
            digests.append(digest(result))
            emit(f"실행 {run} digest {digests[-1]}")
        check(digests[0] == digests[1], "2회 결정성 실패")
        out = runs[0]
        out["결정성"] = {"통과": True, "독립프로세스수": 2, "digest": digests,
                       "범위": "결정성 메타데이터를 추가하기 전 전체 파이프라인 반환 객체의 canonical JSON"}
        text_json = json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        text_md = markdown(out)
        for content in (text_json, text_md):
            check(marker not in content, "보고서의 평가 외 마커 금지")
            check(all(chr(c) not in content for c in (0x2013, 0x2014)), "산출물 금지 문자")
        # 새 파일만 배타적으로 생성한다. 기존 입력 또는 이전 산출물은 열지 않는다.
        with outputs[0].open("x", encoding="utf-8") as f:
            f.write(text_json)
        with outputs[1].open("x", encoding="utf-8") as f:
            f.write(text_md)
        check(all(Path(p).exists() and sha(p) == value for p, value in baseline.items()), "기존 파일 변경 발견")
        after = {str(p) for p in HERE.rglob("*") if p.is_file()}
        check(after - set(baseline) == {str(p) for p in outputs}, "허용 외 파일 생성")
        emit("관문 통과: 손 예제, 자질 10/11 일치, 독립 실행 digest 일치, 입력 불변, 기존 파일 보존, 마커 경계")
        for name, batch in out["묶음"].items():
            suffix = "; " + CAVEAT if name == "fox8" else ""
            for score in SCORES:
                emit(f"{name} {score}: {interval(batch['AUC'][score])}, n={batch['AUC'][score]['n']}" + suffix)
            for title, row in batch["짝지은차"].items():
                emit(f"{name} {title}: {interval(row, '차')}, n={row['n']}" + suffix)
        for key, row in out["예측"].items():
            emit(f"{key} {row['원문']} {row['판정']}, 값={row['판정값']}" + ("; " + CAVEAT if key in ("P14-a", "P14-b") else ""))
        for path, value in out["입력_sha256"].items():
            emit(f"입력 sha256 {path}: {value}")
        for p in [Path(__file__), *outputs[:2]]:
            emit(f"산출 sha256 {p.name}: {sha(p)}")
        emit("완료. 로그 자체의 sha256은 외부 최종 검증에서 계산한다.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--compute"]:
        print(canonical(pipeline()))
    else:
        check(not sys.argv[1:], "추가 분석 옵션은 허용하지 않음")
        main()
