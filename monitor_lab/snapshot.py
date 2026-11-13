"""Lector exclusivamente predictivo; rechaza roles de etiquetas/financiación."""
import hashlib,json,re,zipfile
from datetime import date
import xml.etree.ElementTree as ET
from itau_entrega import data
from .common import CONFIG,ROOT,sha,read
from . import common

PREDICTORS=set(data.WANTED)
FUNDING={'CLICP Index|PX_LAST','FEDL01 Index|PX_LAST'}
def validate_manifest(manifest):
 if not isinstance(manifest,dict):raise ValueError('Manifiesto debe ser un objeto JSON')
 for key in ('source_id','snapshot_sha256','schema_sha256','snapshot_as_of','synthetic','daily_feed_certified'):
  if key not in manifest:raise ValueError('Campo de manifiesto ausente: '+key)
 for key in ('snapshot_sha256','schema_sha256'):
  if not isinstance(manifest[key],str) or not re.fullmatch('[0-9a-f]{64}',manifest[key]):raise ValueError('SHA256 inválido en manifiesto: '+key)
 if not isinstance(manifest['source_id'],str) or not manifest['source_id'].strip():raise ValueError('Procedencia source_id vacía')
 if type(manifest['synthetic']) is not bool or type(manifest['daily_feed_certified']) is not bool:raise ValueError('Indicadores del manifiesto deben ser booleanos')
 try:date.fromisoformat(manifest['snapshot_as_of'])
 except (ValueError,TypeError):raise ValueError('snapshot_as_of debe ser fecha ISO') from None
def approval(manifest):
 payload=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 registry=ROOT/'runtime/approved_manifests.json'
 if not registry.exists():return None
 entries=read(registry)['approvals']
 return next((e for e in entries if e.get('payload_sha256')==payload and e.get('scope')=='inference_only_2026' and e.get('source_id')==manifest.get('source_id') and e.get('schema_sha256')==manifest.get('schema_sha256')),None)
def load_fields(path,cutoff,fields,manifest,role='live_predictors',access_mode='strict'):
 if role!='live_predictors':raise ValueError('Ruta de integración: sólo predictores, sin acceso a etiquetas/evaluación/financiación')
 validate_manifest(manifest)
 if access_mode not in ('strict','user_provided'):raise ValueError('Modo de lectura desconocido')
 if access_mode=='user_provided' and (manifest['synthetic'] or manifest['daily_feed_certified']):raise ValueError('Un archivo local no puede autodeclarar certificación ni usar el modo sintético')
 if cutoff>common.operational_today():raise ValueError('Corte posterior al reloj operativo de Chile')
 if fields-PREDICTORS:raise ValueError('La ruta predictiva no lee financiación ni resultados')
 if sha(path)!=manifest['snapshot_sha256']:raise ValueError('Snapshot no coincide con manifiesto autorizado')
 if not manifest.get('synthetic') and access_mode=='strict':
  if approval(manifest) is None:raise ValueError('Manifiesto no aprobado por canal de control')
 rows={};last=None;last_date=None
 with zipfile.ZipFile(path) as z:
  strings=data.Strings(list(ET.fromstring(z.read('xl/sharedStrings.xml')))) if 'xl/sharedStrings.xml' in z.namelist() else []
  rel={e.get('Id'):e.get('Target') for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))};target=next(rel[e.get(data.REL+'id')] for e in ET.fromstring(z.read('xl/workbook.xml')).findall('.//'+data.M+'sheet') if e.get('name')=='datos');member=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  headers=None
  with z.open(member) as stream:
   for _,row in ET.iterparse(stream,events=('end',)):
    if row.tag!=data.M+'row':continue
    cells={re.match('[A-Z]+',e.get('r')).group():e for e in row.findall(data.M+'c')}
    if headers is None:
     headers={k:str(data.number(e,strings)) for k,e in cells.items()};schema=hashlib.sha256(json.dumps(list(headers.values()),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
     if schema!=manifest['schema_sha256']:raise ValueError('Esquema/orden de columnas no aprobado')
     if not fields<=set(headers.values()):raise ValueError('Columnas requeridas ausentes')
     if any(list(headers.values()).count(k)!=1 for k in fields):raise ValueError('Columnas predictoras duplicadas')
    else:
     d=data.asdate(data.number(cells['A'],strings)) if 'A' in cells else None
     if d is None and cells:raise ValueError('Fila sin fecha válida')
     if d is not None:
      if last_date is not None and d<=last_date:raise ValueError('Calendario duplicado/desordenado')
      last_date=d
     if d is not None and d<=cutoff:
      if last is not None and d<=last:raise ValueError('Fechas duplicadas/desordenadas')
      last=d
      rows[d]={headers[k]:data.number(e,strings) for k,e in cells.items() if headers.get(k) in fields}
    row.clear()
 return rows
