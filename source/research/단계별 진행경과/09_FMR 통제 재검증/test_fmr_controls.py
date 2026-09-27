"""손계산·독립 구현·조건 분리·라벨 비개입 회귀 테스트."""
import sys
sys.dont_write_bytecode = True
import math
import random
import statistics
import unittest
from types import SimpleNamespace
from fmr_prepare_measure import combine, doc_counts, differences, module, STEP
from fmr_controls import bh, mw, rhythm, vectors, paired_sign, FAMILIES, RKEYS


def fake_doc(sentences):
    return SimpleNamespace(sentences=[SimpleNamespace(words=[SimpleNamespace(text=t,upos=p,feats=f)
                                 for t,p,f in sentence]) for sentence in sentences])


class FMRTests(unittest.TestCase):
    def test_u_and_ties(self):
        for x,y,u,d in [([1,2,3],[4,5,6],0,-1),([1,1,2],[1,2,2],3,-1/3),([0,0],[0,0],2,0)]:
            r=mw(x,y)
            self.assertEqual(r['U'],u)
            self.assertAlmostEqual(r['델타'],d)
        self.assertEqual(mw([0,0],[0,0])['p'],1)

    def test_tail_is_not_zero(self):
        r=mw(list(range(100)),list(range(200,400)))
        self.assertGreater(r['p'],0)
        self.assertLess(r['p'],1e-20)

    def test_random_rank_crosscheck(self):
        rng=random.Random(20260920)
        for _ in range(200):
            x=[rng.randrange(12) for _ in range(rng.randrange(1,50))]
            y=[rng.randrange(12) for _ in range(rng.randrange(1,50))]
            r=mw(x,y)
            brute=sum((a>b)-(a<b) for a in x for b in y)/(len(x)*len(y))
            self.assertAlmostEqual(r['델타'],brute)
            rev=mw(y,x)
            self.assertAlmostEqual(r['p'],rev['p'])
            self.assertAlmostEqual(r['델타'],-rev['델타'])

    def test_bh(self):
        self.assertEqual(bh([.01,.02,.03,.04]),[.04]*4)
        self.assertEqual(bh([]),[])
        self.assertEqual(bh([1,1]),[1,1])
        self.assertEqual(bh([.001,1]),[.002,1])

    def test_missing(self):
        self.assertIsNone(mw([], [1])['p'])
        empty={'문장수':0,'토큰수':0,'토큰수_구두점제외':0,'문장길이':[]}
        self.assertTrue(all(v is None for v in rhythm(empty).values()))
        four={'문장수':4,'토큰수':8,'토큰수_구두점제외':8,'문장길이':[2]*4}
        self.assertIsNone(rhythm(four)[RKEYS[2]])
        five={'문장수':5,'토큰수':10,'토큰수_구두점제외':10,'문장길이':[2]*5}
        self.assertEqual(rhythm(five)[RKEYS[2]],0)

    def test_cv_example(self):
        a={'문장수':5,'토큰수':25,'토큰수_구두점제외':20,'문장길이':[2,4,4,4,6]}
        r=rhythm(a)
        self.assertEqual(r[RKEYS[0]],4)
        self.assertEqual(r[RKEYS[1]],.2)
        self.assertAlmostEqual(r[RKEYS[2]],math.sqrt(2)/4)
        a['문장길이']=[1,2,2,2,3];a['토큰수_구두점제외']=10
        self.assertAlmostEqual(rhythm(a)[RKEYS[2]],r[RKEYS[2]])

    def test_apostrophe_and_punctuation(self):
        doc=fake_doc([[('we','PRON','Person=1'),('’ve','AUX',None),('won','VERB','Tense=Past'),('!','PUNCT',None)]])
        a=doc_counts(doc,{'we',"'ve"})
        self.assertEqual(a['기능어'],{'we':1,"'ve":1})
        self.assertEqual(a['토큰수'],4)
        self.assertEqual(a['토큰수_구두점제외'],3)
        self.assertEqual(a['문장길이'],[3])
        self.assertEqual(a['자질'],{'Person=1':1,'Tense=Past':1})

    def test_duplicates_are_not_dropped_in_aggregation(self):
        a=doc_counts(fake_doc([[('we','PRON',None),('.','PUNCT',None)]]),{'we'})
        r=combine([a,a,a])
        self.assertEqual(r['문서수'],3)
        self.assertEqual(r['기능어']['we'],3)
        self.assertEqual(r['문장길이'],[1,1,1])
        self.assertFalse(differences(r,r))

    def test_restriction_not_reusing_full_rhythm(self):
        short=doc_counts(fake_doc([[('a','DET',None),('.','PUNCT',None)]]),{'a'})
        long=doc_counts(fake_doc([[('a','DET',None)]*9+[('.','PUNCT',None)]]),{'a'})
        full=combine([short,long]);restricted=combine([short])
        self.assertEqual(rhythm(full)[RKEYS[0]],5)
        self.assertEqual(rhythm(restricted)[RKEYS[0]],1)

    def test_fixed_morph_denominator_zero_vs_missing(self):
        m=module(STEP/'07_형태자질비교.py','test07')
        a={'u':{'자질':{'Tense=Pres':4},'토큰수_구두점제외':10},
           'v':{'자질':{},'토큰수_구두점제외':10}}
        r,_,_=m.compute_ratios(a,['Tense=Past'],{'Tense':['Past','Pres']})
        self.assertEqual(r['u']['Tense=Past'],0)
        self.assertIsNone(r['v']['Tense=Past'])

    def test_matching(self):
        m=module(STEP/'09-1_분량통제.py','test08')
        logs={u:math.log(v) for u,v in {'b1':100,'b2':1000,'b3':103,'h1':105,'h2':900,'h3':1100,'h4':10000,'h5':1050}.items()}
        a=m.caliper_match(['b1','b2','b3'],['h1','h2','h3','h4','h5'],logs,.1,20260827)
        b=m.caliper_match(['b1','b2','b3'],['h1','h2','h3','h4','h5'],logs,.1,20260827)
        self.assertEqual(a,b)
        pairs,unmatched,used=a
        self.assertEqual(len(used),len(pairs))
        self.assertTrue(all(g<=.1 for _,_,g in pairs))

    def test_sign_test_uses_pairs_and_omits_ties(self):
        vec={f:{'b1':{'x':2},'h1':{'x':1},'b2':{'x':1},'h2':{'x':1}} for f in FAMILIES}
        keys={f:['x'] for f in FAMILIES}
        r=paired_sign(vec,keys,[('b1','h1',0),('b2','h2',0)])['F']['x']
        self.assertEqual((r['양의차이'],r['음의차이'],r['동점']),(1,0,1))
        self.assertEqual(r['p'],1)


if __name__=='__main__':
    unittest.main(verbosity=2)
