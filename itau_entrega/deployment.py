"""Preparación preentrega autorizada. No evaluación ni selección de parámetros."""
import hashlib,json,re,zipfile,platform
import xml.etree.ElementTree as ET
from datetime import date,timedelta
from pathlib import Path
from types import SimpleNamespace
from importlib.metadata import version
import joblib,numpy as np
from threadpoolctl import threadpool_limits
from . import data,model,legacy_features as historical
from monitor_lab import d2_features as f

ROOT=Path(__file__).resolve().parents[1]
FIXED_CUTOFF='2026-11-06'

def validate_cutoff(cutoff):
 if cutoff!=FIXED_CUTOFF:raise ValueError('Corte autorizado fijo: '+FIXED_CUTOFF)
 return date.fromisoformat(cutoff)

def authorized_rows(stream,strings,cutoff):
 """Descarta celdas económicas posteriores al corte ANTES de decodificarlas."""
 validate_cutoff(str(cutoff));headers=None;last=None
 for _,row in ET.iterparse(stream,events=('end',)):
  if row.tag!=data.M+'row':continue
  cells={re.match('[A-Z]+',z.get('r')).group():z for z in row.findall(data.M+'c')}
  if headers is None:
   headers={k:str(data.number(z,strings)) for k,z in cells.items()}
   if not data.WANTED<=set(headers.values()):raise ValueError('Faltan columnas D2')
  else:
   d=data.asdate(data.number(cells['A'],strings)) if 'A' in cells else None
   if d is not None and d<=cutoff:
    if last is not None and d<=last:raise ValueError('Fechas duplicadas/desordenadas')
    last=d
    yield d,{headers[k]:data.number(z,strings) for k,z in cells.items() if headers.get(k) in data.WANTED}
  row.clear()

def load_authorized(path,cutoff):
 cutoff=validate_cutoff(cutoff)
 if data.sha(path)!=data.SHA:raise ValueError('Fuente de preparación no autorizada')
 with zipfile.ZipFile(path) as z:
  strings=data.Strings(list(ET.fromstring(z.read('xl/sharedStrings.xml')))) if 'xl/sharedStrings.xml' in z.namelist() else []
  rel={e.get('Id'):e.get('Target') for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  target=next(rel[e.get(data.REL+'id')] for e in ET.fromstring(z.read('xl/workbook.xml')).findall('.//'+data.M+'sheet') if e.get('name')=='datos')
  member=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  with z.open(member) as stream:return dict(authorized_rows(stream,strings,cutoff))

def training_dataset(raw,cutoff):
 end=validate_cutoff(cutoff);raw={d:r for d,r in raw.items() if d<=end};dates=sorted(raw)
 cal,blocked=historical.observed_calendar({'USDCLP Curncy|PX_LAST':[raw[d].get('USDCLP Curncy|PX_LAST') for d in dates]},dates)
 # Mismas reglas de pares; autorización explícita limitada a preparación.
 cfg=SimpleNamespace(first_target=date(2010,1,1),development_cutoff=end,max_unverified_gap_days=7)
 targets=historical.build_targets(cal,blocked,cfg)
 labels=[dict(decision=str(r['decision_date']),target=str(r['target_date']),known=str(r['target_known_date']),truth=r['direction_next']) for r in targets if r['target_pair_eligible'] and r['decision_date']>=date(2010,1,1)]
 series=f.native(raw);values={s.name:{d:float(r[s.ticker+'|PX_LAST']) for d,r in raw.items() if f.value_valid(r.get(s.ticker+'|PX_LAST'),s)} for s in f.CORE};core=f.OfficialSeries(values);X=[]
 for r in labels:
  d=date.fromisoformat(r['decision']);base,_=f.base_row(raw,core,d);feat,_,line=f.feature_row(r,base,series,'conservador_fecha')
  assert not line['max_native_source'] or line['max_native_source']<d
  X.append([feat[n] for n in data.FEATURES])
 assert labels and max(r['known'] for r in labels)<=cutoff
 return labels,np.asarray(X)

def fit_deployment(excel,cutoff,output):
 end=validate_cutoff(cutoff);out=Path(output)
 if out.exists() or out.with_suffix('.manifest.json').exists():raise ValueError('No sobrescribir artefactos: use ruta nueva')
 cfg=json.loads((ROOT/'config/deployment_fijo.json').read_text(encoding='utf-8'))
 assert cfg['cutoff']==cutoff and cfg['depth']==6 and cfg['temperature']==1.0
 labels,X=training_dataset(load_authorized(excel,cutoff),cutoff)
 with threadpool_limits(limits=2):trained=model.Model(cfg['depth'],X,np.array([r['truth'] for r in labels]))
 bundle=dict(model=trained,temperature=1.0,year=2026,first_permitted_decision=str(end+timedelta(days=1)),last_train_known=max(r['known'] for r in labels),n_train=len(labels),n_cal=0,depth=6,features=97,seed=model.SEED,source_sha256=data.SHA,training_cutoff=cutoff,feature_names=data.FEATURES,class_order=model.CLASSES.tolist(),dependencies={k:version(k) for k in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')},python_version=platform.python_version(),deployment_status='fixed_pre_delivery_training; no_2026_evaluation',calibration_origin='temperature1 frozen from pre2025 model; not refitted')
 out.parent.mkdir(parents=True,exist_ok=True);joblib.dump(bundle,out)
 manifest={k:v for k,v in bundle.items() if k!='model'};manifest['sha256']=data.sha(out);manifest['configuration_sha256']=data.sha(ROOT/'config/deployment_fijo.json');manifest['feature_order_sha256']=data.sha(ROOT/'config/features.json')
 out.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 return dict(status='frozen_deployment_prepared',cutoff=cutoff,last_train_known=bundle['last_train_known'],n_train=len(labels),model_sha256=manifest['sha256'],no_evaluation=True)
