"""특성 계산, 분할, 학습·평가 분리의 단위검사. 네트워크와 원자료는 필요하지 않다."""
import copy
import gzip
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from sklearn.metrics import roc_auc_score
import common as C
import evaluation as E
import prepare_data as P


class CoreTests(unittest.TestCase):
    def test_clean_text(self):
        text,_,_=C.clean_doc("This is a sufficiently long example sentence. https://example.org @example")
        self.assertNotIn("https",text)
        self.assertNotIn("@example",text)

    def test_rank_ties(self):
        L=np.array([.9,.2,.7,.7,.1]); G=np.array([1.5,-2,3,0,-2])
        np.testing.assert_allclose(C.rank_mean(L,G),[.875,.1875,.8125,.5625,.0625])

    def test_train_only_transform(self):
        train=np.array([[0.,0.],[1.,2.],[2.,np.nan]])
        p=C.fit_prep(train,np.array([0,1,2]))
        xp=[v.copy() for v in p["xp"]]
        np.testing.assert_array_equal(p["median"],[1,1])
        value=np.array([[100.,np.nan]])
        one=C.apply_prep(p,value)[0]
        batch=C.apply_prep(p,np.vstack([value,[-100,1000]]))[0]
        np.testing.assert_array_equal(one,batch)
        for before,after in zip(xp,p["xp"]): np.testing.assert_array_equal(before,after)

    def test_m_denominators(self):
        a={"자질":{"Tense=Past":3,"Tense=Pres":7,"Voice=Pass":2},"토큰수_구두점제외":20}
        keys=["Tense=Past","Tense=Pres","Voice=Pass"]
        axis={"Tense":["Past","Pres"],"Voice":["Pass"]}
        np.testing.assert_allclose(C.m_ratios(a,keys,axis),[.3,.7,.1])
        a["자질"]={"Voice=Pass":2}
        self.assertEqual(C.m_ratios(a,keys,axis),[None,None,.1])

    def test_rhythm(self):
        a={"토큰수":30,"토큰수_구두점제외":20,"문장수":5,"문장길이":[4]*5}
        np.testing.assert_allclose(C.rhythm(a),[4,1/3,0])
        a.update({"토큰수":24,"토큰수_구두점제외":16,"문장수":4,"문장길이":[4]*4})
        self.assertIsNone(C.rhythm(a)[2])

    def test_pair_folds(self):
        units=[(2*i,2*i+1) for i in range(20)]
        y=np.tile([1,0],20)
        folds=C.make_folds(units,y,5,np.random.default_rng(C.SEED))
        for b,h in units: self.assertEqual(folds[b],folds[h])
        self.assertEqual(set(folds),set(range(40)))

    def test_knn_self_exclusion_and_no_labels(self):
        class Model:
            def predict_proba(self,P): return np.column_stack([1-P[:,0],P[:,0]])
        X=np.arange(12.,dtype=float).reshape(-1,1)
        prep=C.fit_prep(X,np.arange(12))
        s,P,_=E.declared_scores(X,{"model":Model()},prep)
        np.testing.assert_allclose(s["G"],[ -sorted(abs(v-X[:,0])/11)[10] for v in X[:,0]])
        np.testing.assert_array_equal(s["S"],C.rank_mean(s["L"],s["G"]))

    def test_auc_ties_bootstrap(self):
        s=np.array([.2,.5,.5,.8]); y=np.array([0,0,1,1])
        W=C.boot_counts((17,501,1),[0,0],20)
        p,dist=C.auc_boot(s,np.array([2,3]),np.array([0,1]),W,W)
        self.assertEqual(p,roc_auc_score(y,s))
        self.assertTrue(((dist>=0)&(dist<=1)).all())


class DataPreparationTests(unittest.TestCase):
    def sample(self, generated=False):
        settings={"실행":{"folder":"/private/work"}, "시드":20260926,
                  "파이프라인":{"모델경로":{"pos":"/private/cache/resources/en/pos/model.pt"}},
                  "정제규칙":{"MIN_DOCS":10, "출처":"archived selection code"},
                  "입력":{"Users.csv":{"경로":"/private/work/Users.csv", "sha256":"0"*64}}}
        if generated:
            settings.update({"모델ID표":{"표":{"MODEL_SLOT_1":"example/model"}, "결정":"selection record"},
                             "시각규칙":{}, "복사":{"변형_이름표":{}}, "변형_이름표":{}})
        return {"설정":settings, "계정":{"u":{"tokens":17,"values":[0.25,None],
                                                    "text":"Source text /private/work is not metadata."}}}

    def test_public_metadata_preserves_measurements(self):
        for generated in (False,True):
            original=self.sample(generated)
            result=P.public_openrouter(copy.deepcopy(original))
            self.assertEqual(result["계정"],original["계정"])
            self.assertEqual(result["설정"]["시드"],20260926)
            self.assertNotIn("실행",result["설정"])
            self.assertEqual(result["설정"]["파이프라인"]["모델경로"]["pos"],"en/pos/model.pt")
            self.assertEqual(result["설정"]["입력"]["botsim_users"],"0"*64)
            if generated:
                self.assertEqual(result["설정"]["모델ID표"]["표"],original["설정"]["모델ID표"]["표"])

    def test_public_metadata_is_idempotent(self):
        for generated in (False,True):
            once=P.public_openrouter(self.sample(generated))
            self.assertEqual(P.public_openrouter(copy.deepcopy(once)),once)

    def test_public_metadata_archive_is_deterministic(self):
        original=self.sample()
        payload=json.dumps(original).encode()
        with tempfile.TemporaryDirectory() as tmp:
            paths=[Path(tmp)/name for name in ("a.gz","b.gz")]
            for path in paths: P.gzip_openrouter(io.BytesIO(payload),path)
            self.assertEqual(paths[0].read_bytes(),paths[1].read_bytes())
            with gzip.open(paths[0],"rt") as f:
                self.assertEqual(json.load(f)["계정"],original["계정"])

    def test_anonymous_download_requires_local_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"data").mkdir()
            (root/"data/manifest.json").write_text(json.dumps({"files":{"data/raw/botsim.zip":"0"*64}}))
            with patch.object(P,"ROOT",root), patch.object(P,"URL","https://anonymous.example/release/"), \
                    patch.object(P.urllib.request,"urlopen") as request:
                with self.assertRaisesRegex(RuntimeError,"익명 미러"):
                    P.ensure()
                request.assert_not_called()


    def test_model_archive_preserves_files_without_local_headers(self):
        payload=b"model weights"
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"source.tar.gz"
            info=tarfile.TarInfo("models/stanza/model.pt")
            info.size=len(payload)
            info.uid,info.gid,info.uname,info.gname,info.mtime=123,456,"local-user","local-group",12345
            info.pax_headers={"comment":"local execution"}
            with tarfile.open(src,"w:gz") as archive:
                archive.addfile(info,io.BytesIO(payload))
            outputs=[Path(tmp)/name for name in ("a.tar.gz","b.tar.gz")]
            for path in outputs:P.prepare_models(src,path)
            self.assertEqual(outputs[0].read_bytes(),outputs[1].read_bytes())
            with tarfile.open(outputs[0]) as archive:
                member=archive.getmembers()[0]
                self.assertEqual(archive.extractfile(member).read(),payload)
                self.assertEqual((member.uid,member.gid,member.uname,member.gname,member.mtime),(0,0,"","",0))
                self.assertEqual(member.pax_headers,{})


if __name__=="__main__":
    unittest.main()
