"""Estimación contable CLP/USD, separada de las señales congeladas."""
import csv,json,math,re,zipfile
from datetime import date,timedelta
from pathlib import Path
from bisect import bisect_right
import xml.etree.ElementTree as ET
import numpy as np
from . import data
from .runtime import write_csv

def bootstrap(delta,block=10,reps=1999):
 d=np.asarray(delta,float);n=len(d);rng=np.random.default_rng(20261112);means=[]
 for _ in range(reps):
  starts=rng.integers(0,n,size=(n+block-1)//block);idx=((starts[:,None]+np.arange(block))%n).ravel()[:n];means.append(d[idx].mean())
 samples=np.asarray(means);centered=samples-d.mean()
 return dict(n=n,block=block,reps=reps,delta=float(d.mean()),lo=float(np.quantile(samples,.025)),hi=float(np.quantile(samples,.975)),p=float((np.sum(abs(centered)>=abs(d.mean()))+1)/(reps+1)))

FIELDS={'CLICP Index|PX_LAST','FEDL01 Index|PX_LAST'}
def load_funding(path):
 if data.sha(path)!=data.SHA:raise ValueError('Hash de fuente oficial incorrecto')
 rows={}
 with zipfile.ZipFile(path) as z:
  strings=data.Strings(list(ET.fromstring(z.read('xl/sharedStrings.xml')))) if 'xl/sharedStrings.xml' in z.namelist() else []
  rel={x.get('Id'):x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  target=next(rel[x.get(data.REL+'id')] for x in ET.fromstring(z.read('xl/workbook.xml')).findall('.//'+data.M+'sheet') if x.get('name')=='datos')
  member=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  headers=None;last=None
  with z.open(member) as stream:
   for _,node in ET.iterparse(stream,events=('end',)):
    if node.tag!=data.M+'row':continue
    cells={re.match('[A-Z]+',x.get('r')).group():x for x in node.findall(data.M+'c')}
    if headers is None:
     headers={k:str(data.number(x,strings)) for k,x in cells.items()};assert FIELDS<=set(headers.values()),'Campos de financiación ausentes'
    else:
     d=data.asdate(data.number(cells['A'],strings)) if 'A' in cells else None
     if d is not None and d<=data.END:
      if last is not None and d<=last:raise ValueError('Calendario duplicado/desordenado')
      last=d
      rows[d]={headers[k]:data.number(x,strings) for k,x in cells.items() if headers.get(k) in FIELDS}
    node.clear()
 return rows

def valid(x):return isinstance(x,(float,int)) and math.isfinite(x)
def factors(rows,intervals,allow_clp_interpolation=False,clp_endpoint_method='log_linear'):
 if clp_endpoint_method not in ('log_linear','previous_native','next_native'):raise ValueError('Método contable no registrado')
 cl={d:float(r['CLICP Index|PX_LAST']) for d,r in rows.items() if valid(r.get('CLICP Index|PX_LAST')) and r['CLICP Index|PX_LAST']>0}
 us={d:float(r['FEDL01 Index|PX_LAST']) for d,r in rows.items() if valid(r.get('FEDL01 Index|PX_LAST'))}
 if not all(-10<=v<=100 for v in us.values()):raise ValueError('FEDL01 incompatible con porcentaje anual')
 dates=sorted(us);cldates=sorted(cl);C=[];U=[];durations=[];ages=[];estimated=set()
 def index_at(d):
  if d in cl:return cl[d]
  if not allow_clp_interpolation:raise ValueError('Extremos CLICP auténticos requeridos; no interpolar sin opción explícita')
  j=bisect_right(cldates,d)-1
  if j<0 or j+1>=len(cldates):raise ValueError('No extrapolar índice ni abrir período reservado')
  a,b=cldates[j:j+2]
  if b>data.END or (b-a).days>7:raise ValueError('Extremo CLICP no acotado en siete días de desarrollo')
  estimated.add(d)
  if clp_endpoint_method=='previous_native':return cl[a]
  if clp_endpoint_method=='next_native':return cl[b]
  return cl[a]*(cl[b]/cl[a])**((d-a).days/(b-a).days)
 for t,s in intervals:
  if not t<s<=data.END:raise ValueError('Intervalo fuera del desarrollo autorizado')
  C.append(index_at(s)/index_at(t)-1);growth=1.;d=t
  while d<s:
   j=bisect_right(dates,d)-1
   if j<0 or (d-dates[j]).days>7:raise ValueError('FEDL01 sin cobertura causal económica suficiente')
   ages.append((d-dates[j]).days);growth*=1+us[dates[j]]/100/360;d+=timedelta(days=1)
  U.append(growth-1);durations.append((s-t).days)
 affected=sum(t in estimated or s in estimated for t,s in intervals)
 return np.array(C),np.array(U),np.array(durations),dict(n_intervals=len(intervals),calendar_days=sum(durations),clp_endpoint_estimates_required=bool(estimated),clp_unique_endpoints=len({d for pair in intervals for d in pair}),clp_unique_estimated_endpoints=len(estimated),clp_estimated_endpoint_appearances=sum(t in estimated for t,s in intervals)+sum(s in estimated for t,s in intervals),clp_intervals_affected=affected,clp_endpoint_method=clp_endpoint_method,clp_estimation='bounded between native index observations, max gap seven calendar days; '+clp_endpoint_method if estimated else 'none',usd_calendar_day_coverage=1.,max_usd_age_calendar_days=max(ages),usd_lagged_calendar_days=sum(a>0 for a in ages),clp_negative_intervals_suppressed='not disclosed if small; preserved unchanged',first_clp_year=min(cl).year,last_clp_year=max(cl).year,first_usd_year=min(us).year,last_usd_year=max(us).year,official=False)

def ledger(ret,q,clp,usd,cost_bps=0):
 r,q,c,u=map(lambda x:np.asarray(x,dtype=float),(ret,q,clp,usd))
 if not len(r) or not (r.shape==q.shape==c.shape==u.shape) or not all(np.isfinite(x).all() for x in (r,q,c,u)):raise ValueError('Vectores contables inválidos')
 if not set(q)<={-1,0,1} or cost_bps<0 or np.any(c<=-1) or np.any(u<=-1):raise ValueError('Posición/factores inválidos')
 turn=np.abs(np.diff(np.r_[0.,q]));turn[-1]+=abs(q[-1]);cost=turn*cost_bps/10000
 spot=q*r;carry=q*((1+r)*u-c);excess=spot+carry-cost;total=c+excess
 if np.any(1+total<=0):raise ValueError('Capital no positivo: no componer')
 wealth=np.r_[1.,np.cumprod(1+total)];cashwealth=np.r_[1.,np.cumprod(1+c)]
 return dict(spot=spot,base_cash=c,clp_financing=-q*c,usd_income=q*(1+r)*u,carry=carry,cost=cost,turnover=turn,excess=excess,total=total,wealth=wealth,cashwealth=cashwealth)

def metrics(l,q,days):
 q=np.asarray(q);x=l['excess'];r=l['total'];w=l['wealth'];draw=w/np.maximum.accumulate(w)-1;active=q!=0;sd=x.std(ddof=1)
 return dict(n=len(q),net_compounded=float(w[-1]-1),wealth_final=float(w[-1]),cash_compounded=float(l['cashwealth'][-1]-1),relative_to_cash=float(w[-1]/l['cashwealth'][-1]-1),excess_synthetic_compounded=float(np.prod(1+x)-1),net_cagr_calendar=float(w[-1]**(365/sum(days))-1),vol_annual=float(r.std(ddof=1)*np.sqrt(252)),sharpe_excess_cash=float(x.mean()/sd*np.sqrt(252)) if sd>0 else None,max_drawdown=float(draw.min()),hit_excess_exposed=float(np.mean(x[active]>0)) if active.any() else None,hit_total=float(np.mean(r>0)),exposed_days=int(active.sum()),turnover=float(l['turnover'].sum()),orders=int(np.count_nonzero(np.diff(np.r_[0,q]))+(q[-1]!=0)),mean_exposure=float(q.mean()),mean_absolute_exposure=float(abs(q).mean()),spot_sum=float(l['spot'].sum()),base_cash_sum=float(l['base_cash'].sum()),clp_financing_sum=float(l['clp_financing'].sum()),usd_income_sum=float(l['usd_income'].sum()),carry_sum=float(l['carry'].sum()),cost_sum=float(l['cost'].sum()),excess_sum=float(x.sum()),total_sum=float(r.sum()),official=False)

def evaluate(excel,predictions,output,allow_clp_interpolation=False):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 with Path(predictions).open(encoding='utf-8-sig') as f:records=list(csv.DictReader(f))
 if len(records)!=1524:raise ValueError('Soporte distinto de 1524')
 intervals=[(date.fromisoformat(r['decision']),date.fromisoformat(r['target'])) for r in records]
 if any(a[1]!=b[0] for a,b in zip(intervals,intervals[1:])):raise ValueError('Huecos fuera del soporte: no inventar devengo')
 q=np.array([int(r['position']) for r in records]);ret=np.array([float(r['ret']) for r in records]);years=np.array([s.year for t,s in intervals])
 if not set(q)=={-1,1}:raise ValueError('Posiciones diferentes del comportamiento congelado')
 P=np.array([[float(r[k]) for k in ('p_down','p_flat','p_up')] for r in records])
 if not np.allclose(P.sum(axis=1),1) or (P<0).any() or not np.array_equal(np.array([-1,0,1])[P.argmax(axis=1)],q):raise ValueError('Probabilidades/argmax desalineados')
 funding=load_funding(excel)
 C,U,days,coverage=factors(funding,intervals,allow_clp_interpolation)
 policies={'ExtraTrees_E2010':q,'buy':np.ones(len(q)),'cash_zero':np.zeros(len(q))};summary=[];curve=[];ledgers={}
 for name,pos in policies.items():
  for cost in (0,1,5):
   l=ledger(ret,pos,C,U,cost);ledgers[name,cost]=l;row=dict(policy=name,cost_bps=cost,**metrics(l,pos,days))
   if name!='ExtraTrees_E2010':row.update(hit_excess_exposed=None,hit_total=None)
   summary.append(row)
   for period,mask in [('2019-2021',years<=2021),('2022-2024',years>=2022)]:
    assert mask.sum()>=100 and np.sum(q[mask]!=1)>=100
    end=np.flatnonzero(mask)[-1]+1
    curve.append(dict(policy=name,cost_bps=cost,period=period,n=int(mask.sum()),wealth=float(l['wealth'][end]),cashwealth=float(l['cashwealth'][end])))
   # Sólo outputs privados pueden contener las observaciones y la curva diaria.
   write_csv(output/f'ledger_{name}_{cost}_PRIVADO.csv',[dict(decision=str(t),target=str(s),position=float(pos[j]),clp=C[j],usd=U[j],total=l['total'][j],excess=l['excess'][j],wealth=l['wealth'][j+1]) for j,(t,s) in enumerate(intervals)])
 contrasts=[]
 for ref in ('buy','cash_zero'):
  for cost in (0,1,5):contrasts.append(dict(id='ExtraTrees_E2010',reference=ref,cost_bps=cost,**bootstrap(ledgers['ExtraTrees_E2010',cost]['excess']-ledgers[ref,cost]['excess'])))
 last=0.
 for j,row in enumerate(sorted(contrasts,key=lambda r:r['p'])):last=max(last,min(1.,(len(contrasts)-j)*row['p']));row['p_holm']=last
 write_csv(output/'carry_totales.csv',summary);write_csv(output/'carry_curva_bloques.csv',curve);write_csv(output/'carry_bootstrap.csv',contrasts)
 # Sensibilidad contable autorizada: nunca cambia muestra, q, r, U o costos.
 sensitivity=[]
 for method in ('log_linear','previous_native','next_native'):
  cc,uu,dd,_=factors(funding,intervals,allow_clp_interpolation,method)
  assert np.array_equal(U,uu) and np.array_equal(days,dd)
  for name,pos in policies.items():
   for cost in (0,1,5):
    mm=metrics(ledger(ret,pos,cc,U,cost),pos,days);base=next(x for x in summary if x['policy']==name and x['cost_bps']==cost)
    sensitivity.append(dict(method=method,policy=name,cost_bps=cost,n=len(ret),net_compounded=mm['net_compounded'],delta_net_compounded=mm['net_compounded']-base['net_compounded'],sharpe_excess_cash=mm['sharpe_excess_cash'],max_drawdown=mm['max_drawdown'],carry_sum=mm['carry_sum'],positions_unchanged=True))
 write_csv(output/'carry_sensibilidad.csv',sensitivity)
 coverage.update(source_sha256=data.SHA,predictions_sha256=data.sha(predictions),positions_unchanged=True,three_original_classes=True,day_basis_usd=360,usd_percent_divisor=100,accounting='self-financed proportional capital; ex-post carry; estimated non-official',bootstrap_seed=20261112)
 (output/'carry_cobertura.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
 return summary,curve,contrasts,coverage
