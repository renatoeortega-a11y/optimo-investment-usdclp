"""Reproducción y señal operativa; no depende de caches del proyecto."""
import csv,json,joblib
from datetime import date
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from .data import END,SHA,ROOT,load_excel,dataset,make_features,f
from .model import fit_annual,score,positions
from .accounting import safe_summary,stats,ALLOWED

def write_csv(path,rows):
 rows=list(rows);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8',newline='') as stream:
  w=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def prepare(excel):return dataset(load_excel(excel))
def reproduce(excel,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);labels,X=prepare(excel);records=[]
 with threadpool_limits(limits=2):
  for Y in range(2019,2025):
   print(f'Reproducción anual {Y}: Extra Trees D2 E2010',flush=True);bundle,te=fit_annual(labels,X,Y);P=score(bundle,X[te]);q=positions(P)
   bundle.update(source_sha256=SHA,development_cutoff=str(END))
   (out/'models').mkdir(exist_ok=True);joblib.dump(bundle,out/'models'/f'extra_{Y}.joblib')
   for j,i in enumerate(te):records.append(dict(**labels[i],position=int(q[j]),p_down=float(P[j,0]),p_flat=float(P[j,1]),p_up=float(P[j,2])))
 assert len(records)==1524
 write_csv(out/'predicciones_PRIVADAS.csv',records)
 np.savez_compressed(out/'features_PRIVADAS.npz',D2=X)
 metrics,coarse,exposure=safe_summary(records);write_csv(out/'trading_totales.csv',metrics);write_csv(out/'curva_bloques.csv',coarse);write_csv(out/'exposiciones_agregadas.csv',exposure)
 (out/'linaje.json').write_text(json.dumps(dict(source_sha256=SHA,rows=len(labels),features=97,external_rows=1524,labels_cutoff=str(END),origin='2010-01-01',refit='annual',carry='not available: conventions pending',new_model_search=False),indent=2),encoding='utf-8')
 from .contrastes import summarize
 dm,boot=summarize(records,labels);write_csv(out/'diebold_mariano.csv',dm);write_csv(out/'bootstrap_economico.csv',boot)
 from .carry import evaluate
 evaluate(excel,out/'predicciones_PRIVADAS.csv',out/'carry',allow_clp_interpolation=True)
 return records
def fit_final(excel,out):
 """Ajuste operativo, no evaluación: sólo2010–2024, frontera nominal2025-01-01."""
 labels,X=prepare(excel)
 with threadpool_limits(limits=2):bundle,_=fit_annual(labels,X,2025,final_boundary='2025-01-01')
 bundle.update(source_sha256=SHA,development_cutoff=str(END),deployment_status='frozen; monitor convention and reserved authorization pending')
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);joblib.dump(bundle,out);return dict(trained_through=str(END),status=bundle['deployment_status'],n_train=bundle['n_train'])
def signal(excel,model_path,decision,session_confirmed=False):
 d=date.fromisoformat(decision);base=dict(decision=decision,position=0,p_down=None,p_flat=None,p_up=None,executed=False)
 # Antes de abrir Excel/modelo. No hay interruptor de CLI que abra2025–2026.
 if d>END:return dict(base,status='sealed_period',reason='No se autoriza usar2025–2026; requiere protocolo y autorización posteriores')
 if d.weekday()>4 or not session_confirmed:return dict(base,status='session_unconfirmed',reason='Confirmar jornada operable en calendario del monitor; no inferirla del cierre futuro')
 bundle=joblib.load(model_path) # Sólo artefactos locales de confianza.
 if decision<bundle['first_permitted_decision']:return dict(base,status='model_not_yet_available')
 if d==END:return dict(base,status='horizon_outside_development')
 if bundle.get('source_sha256')!=SHA:raise ValueError('Linaje de modelo no coincide con la fuente oficial')
 raw=load_excel(excel,cutoff=f.previous_weekday(d));X,lin=make_features(raw,d)
 if not lin['max_native_source'] or not f.histories(f.native(raw),'usdclp',f.previous_weekday(d))[0]:return dict(base,status='no_information')
 pp=score(bundle,X[None,:])[0];q=int(positions(pp[None,:])[0])
 if q not in (-1,1):return dict(base,status='policy_review_required',reason='Argmax neutral no observado en validación congelada; NO_ORDER, sin convertirlo en liquidación')
 return dict(base,status='historical_signal_only',position=q,p_down=float(pp[0]),p_flat=float(pp[1]),p_up=float(pp[2]),feature_cutoff=str(lin['cutoff']),availability_certified=False,execution='proposed close-to-next-observed-close; pending monitor confirmation')
def transition(previous,result):
 """Propuesta de orden; sin sesión/señal válida NO liquida una exposición ya existente."""
 if previous not in ALLOWED:raise ValueError('Posición previa inválida')
 if result['status']!='historical_signal_only':return dict(action='NO_ORDER',previous_position=previous,target_position=None,order_delta=0,turnover_units=0,position_after=previous)
 target=result['position'];delta=target-previous
 return dict(action='HOLD' if delta==0 else 'REBALANCE_AT_CONFIRMED_CLOSE',previous_position=previous,target_position=target,order_delta=delta,turnover_units=abs(delta),position_after=target)
def demo():
 rng=np.random.default_rng(20261112);dates=np.busday_offset(np.datetime64('2010-01-04'),np.arange(3900)).astype(str);labels=[]
 for d,t in zip(dates,dates[1:]):
  if t>'2024-12-31':break
  ret=float(rng.normal(0,.01));labels.append(dict(decision=d,target=t,known=t,year=int(t[:4]),ret=ret,truth=int(np.sign(ret))))
 X=rng.normal(size=(len(labels),97));X[::7,4]=np.nan
 with threadpool_limits(limits=2):bundle,te=fit_annual(labels,X,2024)
 P=score(bundle,X[te]);q=positions(P);r=np.array([labels[i]['ret'] for i in te]);days=np.array([(date.fromisoformat(labels[i]['target'])-date.fromisoformat(labels[i]['decision'])).days for i in te]);metrics=stats(r,q,1,days=days,annual_clp=.06,annual_usd=.04,day_count=360)
 return dict(source='SYNTHETIC_ONLY_NOT_BACKTEST',n=len(te),positions_valid=bool(set(q)<=set([-3,-1,0,1,3])),signal_example=int(q[-1]),fixture_carry='CLP6%,USD4%,ACT/360; synthetic explicit example, not official',metrics=metrics)
