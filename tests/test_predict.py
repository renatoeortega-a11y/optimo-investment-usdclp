import json,tempfile,unittest,hmac,hashlib,os,zipfile
from pathlib import Path
from datetime import date
from unittest.mock import patch
from itau_entrega import model
from monitor_lab.common import ROOT,sha,read
from monitor_lab.predict import predict,inspect_excel
from monitor_lab.fixtures import create
from monitor_lab.engine import live_signal

class PredictTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'SYNTHETIC.xlsx';self.manifest=create(self.path);self.out=Path(self.tmp.name)/'output'
  import monitor_lab.predict as module
  old_read=module.read
  def cfg_read(p):
   r=old_read(p)
   if Path(p).name=='predict_interface.json':r['output_directory']=str(self.out)
   return r
  self.patcher=patch.object(module,'read',side_effect=cfg_read);self.patcher.start();self.addCleanup(self.patcher.stop)
 def run_predict(self,**kw):return predict(self.path,'2026-11-12',1,**kw)
 def sign(self):
  meta,_=inspect_excel(self.path,date(2026,11,11));key='fixture_test_secret_do_not_use_'*3;cfg=Path(self.tmp.name)/'trust.json'
  cfg.write_text(json.dumps(dict(enabled=True,algorithm='HMAC-SHA256',key_env='OPTIMO_TEST_KEY',source_id='fixture_provider',schema_sha256=meta['schema_sha256'])))
  payload=dict(meta,source_id='fixture_provider',daily_feed_certified=True,session_confirmed=True)
  signature=hmac.new(key.encode(),json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode(),hashlib.sha256).hexdigest()
  Path(str(self.path)+'.signature.json').write_text(json.dumps(dict(payload=payload,signature=signature)))
  return cfg,key
 def alter_xml(self,fn):
  with zipfile.ZipFile(self.path) as z:parts={n:z.read(n) for n in z.namelist()}
  parts['xl/worksheets/sheet1.xml']=fn(parts['xl/worksheets/sheet1.xml'].decode()).encode()
  with zipfile.ZipFile(self.path,'w') as z:
   for n,b in parts.items():z.writestr(n,b)
 def test_local_signal_no_certification(self):
  r=self.run_predict();self.assertEqual(r['status'],'local_signal_ready');self.assertFalse(r['externally_certified']);self.assertFalse(r['metadata']['daily_feed_certified']);self.assertFalse(r['real_order_authorized'])
 def test_local_matches_existing_strict_engine(self):
  a=self.run_predict();b=live_signal(self.path,self.manifest,ROOT/'artifacts/deployment_final.joblib','2026-11-12',1,True)
  for k in ['p_down','p_flat','p_up','transition']:self.assertEqual(a[k],b[k])
 def test_invalid_xlsx_clear_error(self):
  self.path.write_text('not an Excel')
  with self.assertRaisesRegex(ValueError,'Excel inválido'):self.run_predict()
 def test_no_fit_and_deterministic(self):
  before=sha(ROOT/'artifacts/deployment_final.joblib')
  with patch.object(model.Model,'__init__',side_effect=AssertionError('no fit')),patch.object(model.Encoding,'fit',side_effect=AssertionError('no fit')):a=self.run_predict();b=self.run_predict()
  self.assertEqual(a,b);self.assertEqual(before,sha(ROOT/'artifacts/deployment_final.joblib'))
 def test_daily_updates_leave_model_unchanged(self):
  before=sha(ROOT/'artifacts/deployment_final.joblib');create(self.path,end=date(2026,11,10),count=400);predict(self.path,'2026-11-11',1);create(self.path,end=date(2026,11,11),count=401);self.run_predict();self.assertEqual(before,sha(ROOT/'artifacts/deployment_final.joblib'))
 def test_future_rows_do_not_change_probabilities(self):
  a=self.run_predict();create(self.path,malformed_future=True);b=self.run_predict()
  for k in ['p_down','p_flat','p_up','transition']:self.assertEqual(a[k],b[k])
 def test_stale_no_order(self):
  create(self.path,end=date(2026,11,6));r=self.run_predict();self.assertEqual(r['transition']['action'],'NO_ORDER');self.assertEqual(r['transition']['position_after'],1);self.assertIn('2026-11-11',r['reason'])
 def test_weekend_no_order(self):
  r=predict(self.path,'2026-11-07',-1);self.assertEqual(r['transition']['position_after'],-1);self.assertEqual(r['status'],'session_unconfirmed')
 def test_unconfirmed_no_order(self):self.assertEqual(self.run_predict(session_unconfirmed=True)['transition']['position_after'],1)
 def test_certified_without_trust_rejected(self):
  with self.assertRaises(ValueError):self.run_predict(mode='certified',trust_path=self.path.with_suffix('.missing'))
 def test_certified_equivalent_to_local(self):
  cfg,key=self.sign();a=self.run_predict()
  with patch.dict(os.environ,OPTIMO_TEST_KEY=key):b=self.run_predict(mode='certified',trust_path=cfg)
  self.assertTrue(b['externally_certified'])
  for k in ['p_down','p_flat','p_up','transition']:self.assertEqual(a[k],b[k])
 def test_tampered_signature_rejected(self):
  cfg,key=self.sign();p=Path(str(self.path)+'.signature.json');obj=read(p);obj['signature']='0'*64;p.write_text(json.dumps(obj))
  with patch.dict(os.environ,OPTIMO_TEST_KEY=key):
   with self.assertRaises(ValueError):self.run_predict(mode='certified',trust_path=cfg)
 def test_certified_file_changed_rejected(self):
  cfg,key=self.sign();self.alter_xml(lambda x:x.replace('800','801',1))
  with patch.dict(os.environ,OPTIMO_TEST_KEY=key):
   with self.assertRaises(ValueError):self.run_predict(mode='certified',trust_path=cfg)
 def test_missing_column_rejected(self):
  self.alter_xml(lambda x:x.replace('USDCLP Curncy|PX_LAST','WRONG_FIELD'))
  with self.assertRaises(ValueError):self.run_predict()
 def test_duplicate_date_rejected(self):
  self.alter_xml(lambda x:x.replace('2026-11-11','2026-11-10'))
  with self.assertRaises(ValueError):self.run_predict()
 def test_disordered_date_rejected(self):
  self.alter_xml(lambda x:x.replace('2026-11-10','2020-01-01'))
  with self.assertRaises(ValueError):self.run_predict()
 def test_short_history_no_order(self):
  create(self.path,count=10);r=self.run_predict();self.assertEqual(r['status'],'insufficient_history');self.assertEqual(r['transition']['position_after'],1)
 def test_json_csv_automatic(self):
  r=self.run_predict(csv_output=True);self.assertEqual(len(list(self.out.glob('*.json'))),1);self.assertEqual(len(list(self.out.glob('*.csv'))),1);self.assertEqual(read(next(self.out.glob('*.json'))),r)
 def test_strict_mode_still_rejects_unapproved(self):
  m=read(self.manifest);m.update(synthetic=False,daily_feed_certified=False);self.manifest.write_text(json.dumps(m))
  with self.assertRaises(ValueError):live_signal(self.path,self.manifest,ROOT/'artifacts/deployment_final.joblib','2026-11-12',1,True)
 def test_numeric_invalid_rejected(self):
  self.alter_xml(lambda x:x.replace('<v>800','<v>INVALID',1))
  with self.assertRaises(ValueError):self.run_predict()
