"""BotSim 매칭 512쌍으로 5겹 교차검증 후 전체 학습한다. fox8 라벨은 사용하지 않는다."""
import warnings
import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import common as C


def fit(X, y, rows):
    prep = C.fit_prep(X[rows], rows)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model = LogisticRegression(C=1.0, l1_ratio=0.0, fit_intercept=True,
                                   class_weight=None, solver="lbfgs", max_iter=1000)
        model.fit(C.apply_prep(prep, X[rows]), y[rows])
    return {"model":model, "prep":prep}


def run(analysis):
    all_ids, info, order, Xall = C.read_table(C.TABLE["botsim"])
    pos = {u:i for i,u in enumerate(all_ids)}
    pairs = analysis["매칭쌍"]
    ids = [u for b,h,_ in pairs for u in (b,h)]
    rows = np.array([pos[u] for u in ids])
    X = Xall[rows]
    y = np.array([int(info["라벨"][i] == "bot") for i in rows])
    units = [(2*i, 2*i+1) for i in range(len(pairs))]
    assignment = C.make_folds(units, y, 5, np.random.default_rng(C.SEED))
    folds = np.array([assignment[i] for i in range(len(ids))])
    oof = np.full(len(ids), np.nan)
    for f in range(5):
        tr, va = np.where(folds != f)[0], np.where(folds == f)[0]
        fitted = fit(X,y,tr)
        C.check(not set(fitted["prep"]["fitted_on"]) & set(va), "학습/평가 겹침")
        oof[va] = fitted["model"].predict_proba(C.apply_prep(fitted["prep"],X[va]))[:,1]
    bundle = fit(X,y,np.arange(len(ids)))
    bundle.update({"train_ids":ids, "feature_order":order})
    out = {"ids":ids, "folds":folds, "oof":oof, "auc":float(roc_auc_score(y,oof)),
           "coef":bundle["model"].coef_[0], "intercept":float(bundle["model"].intercept_[0])}
    C.write_json(C.RESULTS / "training.json", out)
    joblib.dump(bundle, C.RESULTS / "model.joblib")
    C.say("BotSim 로지스틱 OOF AUC:", out["auc"])
    return bundle
