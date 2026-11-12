"""No fit, no calibración: sólo codificador/modelo/temperatura congelados."""
from datetime import date,timedelta
import joblib,numpy as np
from itau_entrega.data import FEATURES
from itau_entrega.model import score,positions
from itau_entrega.runtime import transition
from .common import CONFIG,ROOT,sha,read,verify_registration
from . import common
from .snapshot import load_fields,PREDICTORS,approval,validate_manifest
from . import d2_features as f

def feature_context(raw):
 series=f.native(raw);values={s.name:{d:float(r[s.ticker+'|PX_LAST']) for d,r in raw.items() if f.value_valid(r.get(s.ticker+'|PX_LAST'),s)} for s in f.CORE};return series,f.OfficialSeries(values)
def feature_vector(raw,decision,context=None):
 cut=f.previous_weekday(decision)
 if any(d>cut for d in raw):raw={d:r for d,r in raw.items() if d<=cut};context=None
 series,core=context or feature_context(raw);base,_=f.base_row(raw,core,decision)
 feats,_,line=f.feature_row(dict(decision=str(decision),target=str(decision+timedelta(days=1))),base,series,'conservador_fecha')
 assert not line['max_native_source'] or line['max_native_source']<=cut<decision
 return np.array([feats[n] for n in FEATURES]),line
def frozen_bundle(path):
 if sha(path)!=CONFIG['frozen_model_sha256']:raise ValueError('Modelo distinto del congelado')
 if sha(ROOT/'config/features.json')!=CONFIG['feature_order_sha256']:raise ValueError('Orden D2 alterado')
 b=joblib.load(path)
 if b.get('training_cutoff')!=CONFIG['training_cutoff'] or b['last_train_known']!=CONFIG['last_train_known'] or b['features']!=97 or b['depth']!=CONFIG['depth'] or b['temperature']!=CONFIG['temperature'] or b.get('feature_names')!=FEATURES or b.get('class_order')!=[-1,0,1]:raise ValueError('Estado del modelo incompatible')
 return b
def from_raw(raw,decision,bundle):
 if str(decision)<bundle['first_permitted_decision'] or bundle['last_train_known']>=str(decision):raise ValueError('Modelo todavía no disponible')
 raw={d:r for d,r in raw.items() if d<=f.previous_weekday(decision)};context=feature_context(raw);X,line=feature_vector(raw,decision,context);ds,_=f.histories(context[0],'usdclp',f.previous_weekday(decision))
 if not ds:return dict(status='no_information',position=0,executed=False,p_down=None,p_flat=None,p_up=None)
 # Orden fijo de suma al predecir: evita redondeos dependientes de hilos,
 # sin modificar árboles, parámetros ni codificador guardados.
 with joblib.parallel_backend('sequential'):P=score(bundle,X[None,:])[0]
 q=int(positions(P[None,:])[0]);result=dict(status='historical_signal_only' if q in (-1,1) else 'policy_review_required',position=q,p_down=float(P[0]),p_flat=float(P[1]),p_up=float(P[2]),decision=str(decision),feature_cutoff=str(line['cutoff']),max_source=str(line['max_native_source']),features=97,missing_features=int(np.isnan(X).sum()),availability_certified=False,executed=False)
 return result
def live_signal(excel,manifest_path,model,decision,previous_position,session_confirmed=False):
 verify_registration();manifest=read(manifest_path);d=date.fromisoformat(decision);cut=f.previous_weekday(d)
 if d.year!=CONFIG['supported_year'] or d>common.operational_today():raise ValueError('Decisión fuera de2026 o posterior al reloj de Chile')
 validate_manifest(manifest)
 approved=approval(manifest) if not manifest.get('synthetic') else None
 if not manifest.get('synthetic') and (approved is None or sha(manifest_path)!=approved['manifest_file_sha256']):raise ValueError('Manifiesto operativo nuevo no aprobado')
 base=dict(decision=decision,position=0,p_down=None,p_flat=None,p_up=None,executed=False)
 def no_order(status):
  r=dict(base,status=status);r['transition']=transition(previous_position,r);return r
 if d.weekday()>4 or not session_confirmed:return no_order('session_unconfirmed')
 asof=date.fromisoformat(manifest['snapshot_as_of'])
 if asof>common.operational_today():raise ValueError('Snapshot declara una fecha futura')
 if asof<cut:return no_order('stale_snapshot')
 if not manifest.get('synthetic') and not (manifest.get('daily_feed_certified') and approved.get('daily_feed_certified')):return no_order('uncertified_live_feed')
 raw=load_fields(excel,cut,PREDICTORS,manifest);result=from_raw(raw,d,frozen_bundle(model));result['transition']=transition(previous_position,result)
 result['synthetic']=bool(manifest.get('synthetic'));result['mode']='inference_only_2026';result['real_order_authorized']=False
 if result['status']=='historical_signal_only':result['status']='synthetic_signal_only' if result['synthetic'] else 'live_signal_ready'
 return result
