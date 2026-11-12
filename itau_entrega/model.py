"""Extra Trees D2 E2010 exactamente como Fase5C: misma grilla, semilla y calibración."""
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import log_loss
CLASSES=np.array([-1,0,1]);GRID=(4,6);TEMPS=(.75,1.,1.5,2.);SEED=20261109
class Encoding:
 def fit(self,X):
  count=np.isfinite(X).sum(axis=0);self.mean=np.divide(np.nansum(X,axis=0),count,out=np.zeros(X.shape[1]),where=count>0);z=X-self.mean
  scale=np.sqrt(np.divide(np.nansum(z*z,axis=0),count,out=np.ones(X.shape[1]),where=count>0));self.scale=np.where(scale>1e-10,scale,1.);return self
 def transform(self,X):return np.column_stack([np.where(np.isfinite(X),(X-self.mean)/self.scale,0.),~np.isfinite(X)])
def temperature(P,t):
 z=np.exp(np.log(np.clip(P,1e-12,1))/t);return z/z.sum(axis=1,keepdims=True)
class Model:
 def __init__(self,depth,X,y):
  self.encoding=Encoding().fit(X);self.estimator=ExtraTreesClassifier(n_estimators=120,max_depth=int(depth),min_samples_leaf=20,max_features='sqrt',n_jobs=2,random_state=SEED).fit(self.encoding.transform(X),y)
 def score(self,X):
  raw=self.estimator.predict_proba(self.encoding.transform(X));P=np.full((len(X),3),1e-12)
  for j,c in enumerate(self.estimator.classes_):P[:,int(c)+1]=raw[:,j]
  return P/P.sum(axis=1,keepdims=True)
def boundary(labels,Y):return min((r['decision'] for r in labels if r['year']==Y),default=f'{Y}-01-01')
def splits(labels,Y,final_boundary=None):
 ds=np.array([r['decision'] for r in labels]);known=np.array([r['known'] for r in labels]);years=np.array([r['year'] for r in labels]);base=ds>='2010-01-01';end=final_boundary or boundary(labels,Y)
 def train(v):return np.flatnonzero(base&(years<v)&(known<(end if v==Y else boundary(labels,v))))
 tr=train(Y);te=np.flatnonzero(years==Y);it=train(Y-2);va=np.flatnonzero(base&(years==Y-2)&(known<boundary(labels,Y-1)));ct=train(Y-1);cal=np.flatnonzero(base&(years==Y-1)&(known<end))
 for aa,bb in ((it,va),(ct,cal),(va,cal)):
  assert len(aa)>=100 and len(bb)>=100 and max(labels[i]['known'] for i in aa)<min(labels[i]['decision'] for i in bb)
 assert max(labels[i]['known'] for i in tr)<end and max(labels[i]['known'] for i in cal)<end
 return tr,te,it,va,ct,cal
def fit_annual(labels,X,Y,final_boundary=None):
 tr,te,it,va,ct,cal=splits(labels,Y,final_boundary);y=np.array([r['truth'] for r in labels]);trials=[]
 for depth in GRID:
  P=Model(depth,X[it],y[it]).score(X[va]);trials.append((log_loss(y[va],P,labels=CLASSES),depth))
 depth=min(trials)[1];cm=Model(depth,X[ct],y[ct]);cp=cm.score(X[cal]);t=min((log_loss(y[cal],temperature(cp,t),labels=CLASSES),t) for t in TEMPS)[1]
 final=Model(depth,X[tr],y[tr]);return dict(model=final,temperature=t,year=Y,first_permitted_decision=final_boundary or boundary(labels,Y),last_train_known=max(labels[i]['known'] for i in tr),n_train=len(tr),n_cal=len(cal),depth=depth,features=97,seed=SEED),te
def score(bundle,X):return temperature(bundle['model'].score(X),bundle['temperature'])
def positions(P):
 P=np.asarray(P)
 if P.ndim!=2 or P.shape[1]!=3 or not np.isfinite(P).all() or (P<0).any() or not np.allclose(P.sum(axis=1),1):raise ValueError('Probabilidades inválidas')
 return CLASSES[P.argmax(axis=1)]
