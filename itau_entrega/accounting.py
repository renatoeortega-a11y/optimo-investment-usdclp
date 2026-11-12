"""Contabilidad explícita. No fabrica carry ni puntajes oficiales."""
import numpy as np
ALLOWED={-3,-1,0,1,3}
def ledger(r,q,cost_bps=0,days=None,annual_clp=None,annual_usd=None,day_count=None):
 r=np.asarray(r,float);q=np.asarray(q,float)
 if len(r)!=len(q) or not np.isfinite(r).all() or not set(q)<=ALLOWED:raise ValueError('Retornos/posiciones inválidos')
 entry_change=abs(np.diff(np.r_[0.,q]));turn=entry_change.copy();turn[-1]+=abs(q[-1]);cost=turn*cost_bps/10000
 spot=q*r;out=dict(spot=spot,cost=cost,turnover=turn,spot_less_cost=spot-cost,carry=None,excess_net=None,total_net=None,official=False)
 if any(z is not None for z in (annual_clp,annual_usd,day_count)):
  if any(z is None for z in (annual_clp,annual_usd,day_count,days)):raise ValueError('Carry requiere tasas, días y base explícitos')
  if day_count not in (360,365):raise ValueError('Base de días no admitida')
  dt=np.asarray(days)/day_count;cl=np.asarray(annual_clp);us=np.asarray(annual_usd)
  carry=-q*(cl-us)*dt;out.update(carry=carry,excess_net=spot+carry-cost,total_net=cl*dt+spot+carry-cost)
 return out
def stats(r,q,cost_bps=0,**kwargs):
 q=np.asarray(q);r=np.asarray(r);l=ledger(r,q,cost_bps,**kwargs);net=l['spot_less_cost'];active=q!=0;sd=float(net.std(ddof=1));curve=np.r_[0,np.cumsum(net)]
 rebalances=int(np.sum(np.diff(np.r_[0,q])!=0));final_exit=int(q[-1]!=0)
 return dict(n=len(r),gross_spot_sum=float(l['spot'].sum()),cost_sum=float(l['cost'].sum()),spot_less_cost_sum=float(net.sum()),carry_sum=float(l['carry'].sum()) if l['carry'] is not None else None,excess_net_sum=float(l['excess_net'].sum()) if l['excess_net'] is not None else None,total_net_sum=float(l['total_net'].sum()) if l['total_net'] is not None else None,vol_annual_spot_less_cost=sd*np.sqrt(252),sharpe_spot_less_cost_rf0=float(net.mean()/sd*np.sqrt(252)) if sd>0 else None,max_drawdown_additive=float((curve-np.maximum.accumulate(curve)).min()),direction_accuracy=float(np.mean(np.sign(r)==q)),win_rate_exposed_spot=float(np.mean(l['spot'][active]>0)) if active.any() else None,exposed_days=int(active.sum()),rebalances_including_entry=rebalances,final_liquidation_orders=final_exit,total_orders=rebalances+final_exit,turnover=float(l['turnover'].sum()),mean_exposure=float(q.mean()),mean_absolute_exposure=float(abs(q).mean()),official_score=False)
def safe_summary(records):
 """Sólo totales. Curva por dos bloques disjuntos grandes; ninguna serie diaria exportada."""
 r=np.array([z['ret'] for z in records]);q=np.array([z['position'] for z in records]);years=np.array([z['year'] for z in records]);pol={'E2010_ExtraTrees':q,'buy':np.ones(len(q)),'zero':np.zeros(len(q))};metrics=[];curve=[]
 assert len(r)>=100
 for name,pos in pol.items():
  for cost in (0,1,5):
   row=dict(policy=name,cost_bps=cost,**stats(r,pos,cost))
   # Las referencias no son pronósticos de clase. Además, sus aciertos permitirían
   # deducir una clase nula pequeña al cruzarlos con referencias ya publicadas.
   if name in ('buy','zero'):row.update(direction_accuracy=None,win_rate_exposed_spot=None)
   metrics.append(row)
 for period,mask in (('2019-2021',years<=2021),('2022-2024',years>=2022)):
  assert mask.sum()>=100 and np.sum(q[mask]!=1)>=100,'No publicar curva que aísle pocos diferenciales'
  for name,pos in pol.items():
   for cost in (0,1,5):
    l=ledger(r,pos,cost);curve.append(dict(policy=name,cost_bps=cost,period=period,n=int(mask.sum()),spot_sum=float(l['spot'][mask].sum()),spot_less_cost_sum=float(l['spot_less_cost'][mask].sum())))
 # Coarse cohorts are a projection of the same stored predictions, not a new policy/backtest search.
 exposure=[dict(position=int(k),days=int(np.sum(q==k))) for k in sorted(ALLOWED)]
 assert all(z['days']==0 or z['days']>=100 for z in exposure),'Suprimir toda la distribución si existe exposición rara'
 return metrics,curve,exposure
