"""Excel oficial: filtra fecha ANTES de decodificar cualquier valor económico."""
import hashlib,json,math,re,zipfile
import xml.etree.ElementTree as ET
from datetime import date,timedelta
from pathlib import Path
import numpy as np
from . import legacy_features as f
ROOT=Path(__file__).resolve().parents[1]
SHA='a198a2357332685b784fddd852dea242f59e90046dedd9709a3429ae9f6134ee'
END=date(2024,12,31);M='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
FEATURES=json.loads((ROOT/'config/features.json').read_text(encoding='utf-8'))
WANTED={t+'|PX_LAST' for t in f.TICKERS.values()}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def number(cell,strings):
 if cell.get('t')=='inlineStr':return ''.join(z.text or '' for z in cell.findall('.//'+M+'t'))
 v=cell.find(M+'v')
 if v is None or v.text is None:return None
 if cell.get('t')=='s':return strings[int(v.text)]
 if cell.get('t') in ('str','e'):return v.text
 try:return float(v.text)
 except ValueError:return v.text
def asdate(v):
 if isinstance(v,(float,int)):return date(1899,12,30)+timedelta(days=int(v))
 try:return date.fromisoformat(str(v)[:10])
 except ValueError:return None
class Strings:
 def __init__(self,nodes):self.nodes=nodes;self.cache={}
 def __getitem__(self,k):
  if k not in self.cache:self.cache[k]=''.join(x.text or '' for x in self.nodes[k].findall('.//'+M+'t'))
  return self.cache[k]
def guarded_rows(stream,strings,cutoff=END):
 if cutoff>END:raise ValueError('Reservado: no se autoriza decodificar 2025–2026')
 headers=None;last=None
 for _,row in ET.iterparse(stream,events=('end',)):
  if row.tag!=M+'row':continue
  cells={re.match('[A-Z]+',z.get('r')).group():z for z in row.findall(M+'c')}
  if headers is None:headers={k:str(number(z,strings)) for k,z in cells.items()}
  else:
   d=asdate(number(cells['A'],strings)) if 'A' in cells else None
   if d is not None and d<=cutoff:
    if last is not None and d<=last:raise ValueError('Fechas duplicadas/desordenadas')
    last=d
    yield d,{headers[k]:number(z,strings) for k,z in cells.items() if k!='A' and headers.get(k) in WANTED}
  row.clear()
def load_excel(path,cutoff=END):
 path=Path(path)
 if sha(path)!=SHA:raise ValueError('El Excel no coincide con la fuente oficial activa')
 with zipfile.ZipFile(path) as z:
  strings=Strings(list(ET.fromstring(z.read('xl/sharedStrings.xml')))) if 'xl/sharedStrings.xml' in z.namelist() else []
  rel={a.get('Id'):a.get('Target') for a in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  target=next(rel[sh.get(REL+'id')] for sh in ET.fromstring(z.read('xl/workbook.xml')).findall('.//'+M+'sheet') if sh.get('name')=='datos')
  member=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  with z.open(member) as stream:rows=dict(guarded_rows(stream,strings,cutoff))
 return rows
def make_features(raw,decision):
 if decision>END:raise ValueError('Reservado: decisión posterior a2024')
 # No se consulta si el cierre de la decisión o el siguiente resultado existen.
 cut=f.previous_weekday(decision);native={d:r for d,r in raw.items() if d<=cut};series=f.native(native)
 values={s.name:{d:float(row[s.ticker+'|PX_LAST']) for d,row in native.items() if f.value_valid(row.get(s.ticker+'|PX_LAST'),s)} for s in f.CORE}
 core=f.OfficialSeries(values);base,_=f.base_row(native,core,decision)
 # La función histórica exige un target nominal posterior; no se lee su precio.
 target=decision+timedelta(days=1)
 if target>END:raise ValueError('La última decisión elegible requiere horizonte dentro de2024')
 feats,_,line=f.feature_row(dict(decision=str(decision),target=str(target)),base,series,'conservador_fecha')
 assert not line['max_native_source'] or line['max_native_source']<=cut<decision
 return np.array([feats[n] for n in FEATURES]),line
def dataset(raw):
 dates=sorted(raw);columns={'USDCLP Curncy|PX_LAST':[raw[d].get('USDCLP Curncy|PX_LAST') for d in dates]}
 cal,blocked=f.observed_calendar(columns,dates)
 labels=f.build_targets(cal,blocked,f.Config(first_target=date(2010,1,1)))
 labels=[dict(decision=str(r['decision_date']),target=str(r['target_date']),known=str(r['target_known_date']),year=r['target_date'].year,ret=r['return_next'],truth=r['direction_next']) for r in labels if r['target_pair_eligible'] and r['decision_date']>=date(2010,1,1)]
 # ÍNDICE histórico compartido; mismos resultados que make_features(), evita reconstrucción por fila.
 series=f.native(raw);values={s.name:{d:float(row[s.ticker+'|PX_LAST']) for d,row in raw.items() if f.value_valid(row.get(s.ticker+'|PX_LAST'),s)} for s in f.CORE};core=f.OfficialSeries(values);X=[]
 for r in labels:
  d=date.fromisoformat(r['decision']);base,_=f.base_row(raw,core,d);feat,_,line=f.feature_row(r,base,series,'conservador_fecha');X.append([feat[n] for n in FEATURES])
 return labels,np.array(X)
