"""Inferencia descriptiva reproducible, sin elegir modelos o políticas."""
import numpy as np
from scipy.stats import t as student_t
from .accounting import ledger

def dm_hac(delta,lag=10):
 d=np.asarray(delta,float);n=len(d);z=d-d.mean();longrun=float(z@z/n)
 for k in range(1,min(lag,n-1)+1):longrun+=2*(1-k/(lag+1))*float(z[k:]@z[:-k]/n)
 if longrun<=0:return dict(n=n,lag=lag,horizon=1,delta=float(d.mean()),statistic=None,p=None,reason='Varianza HAC no positiva')
 # Harvey-Leybourne-Newbold h=1; referencia t(n-1), contraste bilateral.
 statistic=float(d.mean()/np.sqrt(longrun/n)*np.sqrt((n-1)/n))
 return dict(n=n,lag=lag,horizon=1,delta=float(d.mean()),statistic=statistic,p=float(2*student_t.sf(abs(statistic),df=n-1)),method='DM HAC Bartlett; HLN h1; t n-1; exploratory')

def bootstrap(delta,block=10,reps=1999):
 d=np.asarray(delta,float);n=len(d);rng=np.random.default_rng(20261111);means=[]
 for _ in range(reps):
  starts=rng.integers(0,n,size=(n+block-1)//block);idx=((starts[:,None]+np.arange(block))%n).ravel()[:n];means.append(d[idx].mean())
 samples=np.asarray(means);centered=samples-d.mean();pv=(np.sum(abs(centered)>=abs(d.mean()))+1)/(reps+1)
 return dict(n=n,block=block,reps=reps,delta=float(d.mean()),lo=float(np.quantile(samples,.025)),hi=float(np.quantile(samples,.975)),p=float(pv))

def summarize(records,labels):
 ret=np.array([r['ret'] for r in records]);q=np.array([r['position'] for r in records]);P=np.array([[r[k] for k in ('p_down','p_flat','p_up')] for r in records]);y=np.array([r['truth'] for r in records]);prior=[]
 for r in records:
  h=[z['truth'] for z in labels if z['known']<r['decision']];c=np.array([h.count(k)+1 for k in (-1,0,1)],float);prior.append(c/c.sum())
 B=np.array(prior);loss=-np.log(P[np.arange(len(y)),y+1]);base=-np.log(B[np.arange(len(y)),y+1]);dm=[dict(id='ExtraTrees',reference='Laplace_dynamic',metric='triclase_logloss',**dm_hac(loss-base))]
 rows=[]
 for reference,qq in [('buy',np.ones(len(q))),('zero',np.zeros(len(q)))]:
  for cost in (0,1,5):rows.append(dict(id='ExtraTrees',reference=reference,cost_bps=cost,**bootstrap(ledger(ret,q,cost)['spot_less_cost']-ledger(ret,qq,cost)['spot_less_cost'])))
 # Familia económica6. No confundir con prueba de rentabilidad neta oficial.
 ordered=sorted(rows,key=lambda z:z['p']);last=0
 for j,r in enumerate(ordered):last=max(last,min(1,(len(rows)-j)*r['p']));r['p_holm']=last
 return dm,rows
