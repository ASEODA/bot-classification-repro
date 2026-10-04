"""작은 손계산·분할·학습/평가 분리 회귀 검사. 원자료/네트워크 불필요."""
import unittest
import numpy as np
from sklearn.metrics import roc_auc_score
import common as C
import evaluation as E


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


if __name__=="__main__":
    unittest.main()
