"""Interfaz de archivos locales. Inferencia únicamente sobre el motor congelado."""
import csv,hashlib,hmac,json,os,re,zipfile,math
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET
from itau_entrega import data
from itau_entrega.runtime import transition
from .common import ROOT,CONFIG,sha,read,verify_registration
from . import common
from .snapshot import load_fields,PREDICTORS
from .engine import frozen_bundle,from_raw,feature_context
from . import d2_features as f

def inspect_excel(path,cutoff):
 headers=None;last=None;eligible=None
 with zipfile.ZipFile(path) as z:
  strings=data.Strings(list(ET.fromstring(z.read('xl/sharedStrings.xml')))) if 'xl/sharedStrings.xml' in z.namelist() else []
  rel={e.get('Id'):e.get('Target') for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  sheets=[e for e in ET.fromstring(z.read('xl/workbook.xml')).findall('.//'+data.M+'sheet') if e.get('name')=='datos']
  if len(sheets)!=1:raise ValueError('Se requiere exactamente una hoja llamada datos')
  target=rel[sheets[0].get(data.REL+'id')];member=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  with z.open(member) as stream:
   for _,row in ET.iterparse(stream,events=('end',)):
    if row.tag!=data.M+'row':continue
    cells={re.match('[A-Z]+',e.get('r')).group():e for e in row.findall(data.M+'c')}
    if headers is None:
     headers=[str(data.number(e,strings)) for e in cells.values()]
     missing=sorted(PREDICTORS-set(headers))
     if missing:raise ValueError('Faltan columnas requeridas: '+', '.join(missing))
     if any(headers.count(k)!=1 for k in PREDICTORS):raise ValueError('Columnas predictoras duplicadas')
    elif cells:
     d=data.asdate(data.number(cells['A'],strings)) if 'A' in cells else None
     if d is None:raise ValueError('Fila sin fecha válida')
     if last is not None and d<=last:raise ValueError('Fechas duplicadas o desordenadas')
     last=d
     if d<=cutoff:eligible=d
    row.clear()
 if headers is None or eligible is None:raise ValueError('No hay historia anterior a la decisión')
 return dict(source_id='user_provided_excel',snapshot_sha256=sha(path),schema_sha256=hashlib.sha256(json.dumps(headers,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),snapshot_as_of=str(eligible),synthetic=False,daily_feed_certified=False),str(last)

def channel_certificate(path,metadata,trust_path):
 """Verificación criptográfica de canal; una ruta de archivo no prueba origen."""
 if not Path(trust_path).exists():raise ValueError('Fuente certificada sin configuración de confianza')
 cfg=read(trust_path)
 if cfg.get('enabled') is not True or cfg.get('algorithm')!='HMAC-SHA256':raise ValueError('Canal certificado no habilitado')
 if not isinstance(cfg.get('source_id'),str) or not cfg['source_id'].strip():raise ValueError('Identificador de fuente certificada ausente')
 key=os.environ.get(cfg.get('key_env',''))
 if not key or len(key.encode())<32:raise ValueError('Clave de canal ausente o demasiado corta')
 signature_path=Path(str(path)+'.signature.json')
 if not signature_path.exists():raise ValueError('Falta firma del proveedor para este Excel')
 envelope=read(signature_path);payload=envelope.get('payload',{});signature=envelope.get('signature','')
 message=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
 expected=hmac.new(key.encode(),message,hashlib.sha256).hexdigest()
 if not isinstance(signature,str) or not hmac.compare_digest(expected,signature):raise ValueError('Firma del canal inválida')
 if payload.get('source_id')!=cfg.get('source_id') or payload.get('schema_sha256')!=cfg.get('schema_sha256') or payload.get('schema_sha256')!=metadata['schema_sha256'] or payload.get('snapshot_sha256')!=metadata['snapshot_sha256']:raise ValueError('Fuente, esquema o archivo no autorizado por el canal')
 if payload.get('daily_feed_certified') is not True:raise ValueError('El proveedor no certificó el feed')
 asof=date.fromisoformat(payload['snapshot_as_of'])
 if asof>common.operational_today():raise ValueError('Certificación con fecha futura')
 return payload

def predict(excel,decision,previous_position,mode='local',trust_path=None,session_unconfirmed=False,csv_output=False):
 verify_registration();d=date.fromisoformat(decision)
 if d.year!=CONFIG['supported_year'] or d>common.operational_today():raise ValueError('Fecha fuera del año operativo o posterior al reloj de Chile')
 if previous_position not in (-1,0,1):raise ValueError('La posición anterior debe ser -1, 0 o +1')
 if mode not in ('local','certified'):raise ValueError('Modo inválido')
 cfg=read(ROOT/'config/predict_interface.json');model=ROOT/cfg['model_path']
 if not model.is_file():raise ValueError('Falta el modelo congelado. Complete una sola vez la preparación fit-deployment indicada en README; predict nunca entrena.')
 before=sha(model);bundle=frozen_bundle(model)
 if decision<bundle['first_permitted_decision']:raise ValueError('El modelo aún no estaba disponible para esa decisión')
 cut=f.previous_weekday(d)
 try:meta,last_date=inspect_excel(excel,cut)
 except (zipfile.BadZipFile,ET.ParseError,KeyError,StopIteration,OverflowError) as error:raise ValueError('Excel inválido: revise formato XLSX, hoja datos y fechas') from error
 certificate=channel_certificate(excel,meta,trust_path or ROOT/'runtime/source_trust.json') if mode=='certified' else None
 raw=load_fields(excel,cut,PREDICTORS,meta,access_mode='user_provided')
 for row in raw.values():
  for name,value in row.items():
   if value is None or (isinstance(value,str) and (value.startswith('#') or value=='N/A')):continue
   if not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Valor no numérico o no finito en columna '+name)
 # Mismos filtros nativos y tratamiento de NaN que D2; no se imputan valores nuevos.
 series,_=feature_context(raw);ds,_=f.histories(series,'usdclp',cut)
 reason=None;status=None
 if d.weekday()>4 or session_unconfirmed or (certificate is not None and certificate.get('session_confirmed') is not True):status='session_unconfirmed';reason='Sesión no confirmada; se conserva la posición anterior.'
 elif not ds or ds[-1]<cut or date.fromisoformat(meta['snapshot_as_of'])<cut or (certificate is not None and date.fromisoformat(certificate['snapshot_as_of'])<cut):
  status='stale_snapshot';last=str(ds[-1]) if ds else 'ninguna fecha válida'
  reason=f'El archivo solo contiene USD/CLP admisible hasta {last}. Para generar la señal del {decision} se necesita información hasta {cut}. No se supone que una ausencia sea feriado.'
 elif len(ds)<cfg['minimum_usdclp_observations']:status='insufficient_history';reason='Se necesitan al menos 21 observaciones auténticas USD/CLP para los 20 retornos históricos de D2.'
 if status:result=dict(status=status,position=0,p_down=None,p_flat=None,p_up=None,executed=False)
 else:result=from_raw(raw,d,bundle)
 result['transition']=transition(previous_position,result)
 if result['status']=='historical_signal_only':result['status']='local_signal_ready' if mode=='local' else 'certified_signal_ready'
 result.update(decision=decision,feature_cutoff=str(cut),max_information_used=result.get('max_source'),reason=reason,mode=mode,provenance='user_provided_not_externally_certified' if certificate is None else 'verified_channel_signature',externally_certified=certificate is not None,session_basis='weekday_simulation_requested_by_user' if certificate is None else 'signed_provider_session',real_order_authorized=False,executed=False,model_sha256=before,metadata=meta,snapshot_last_date=last_date)
 if certificate is not None:result['certificate_payload_sha256']=hashlib.sha256(json.dumps(certificate,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
 if sha(excel)!=meta['snapshot_sha256']:raise ValueError('El Excel cambió durante la ejecución; no se emite señal')
 if sha(model)!=before:raise ValueError('El artefacto cambió durante la ejecución')
 out=ROOT/cfg['output_directory'];out.mkdir(parents=True,exist_ok=True)
 key=f"{decision}_{meta['snapshot_sha256'][:16]}_{previous_position}_{mode}"
 key+='_'+hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()[:12]
 # Idempotente: mismo insumo/estado produce mismo contenido. No se guarda una posición como ejecutada.
 (out/(key+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 if csv_output:
  record={k:result.get(k) for k in ['decision','feature_cutoff','p_down','p_flat','p_up','status','mode','externally_certified']};record.update(result['transition'])
  with (out/(key+'.csv')).open('w',encoding='utf-8',newline='') as stream:
   w=csv.DictWriter(stream,fieldnames=list(record));w.writeheader();w.writerow(record)
 return result
