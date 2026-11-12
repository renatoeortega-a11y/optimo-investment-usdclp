import json,subprocess,sys,tempfile,unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from monitor_lab.common import ROOT,verify_registration
from monitor_lab.snapshot import load_fields,PREDICTORS
from monitor_lab.engine import live_signal
from monitor_lab.fixtures import create

class IntegrationMonitorTests(unittest.TestCase):
 def test_evaluation_module_not_shipped(self):self.assertFalse((ROOT/'monitor_lab/evaluate.py').exists())
 def test_extended_funding_reader_not_shipped(self):self.assertFalse((ROOT/'monitor_lab/funding.py').exists())
 def test_eval_command_rejected(self):
  r=subprocess.run([sys.executable,'-B','-m','monitor_lab','evaluate-2026'],cwd=ROOT,capture_output=True);self.assertEqual(r.returncode,2)
 def test_training_command_rejected(self):
  r=subprocess.run([sys.executable,'-B','-m','monitor_lab','fit-final'],cwd=ROOT,capture_output=True);self.assertEqual(r.returncode,2)
 def test_no_private_preregistration_dependency(self):
  with patch('monitor_lab.common.read',side_effect=AssertionError('private registry unavailable')):self.assertEqual(verify_registration()['scope'],'inference_only_2026')
 def test_unsupported_reader_roles_rejected_before_open(self):
  for role in ('labels_2026','training','funding_realized_2026'):
   with self.assertRaises(ValueError):load_fields('missing.xlsx',date(2026,11,11),PREDICTORS,{},role=role)
 def test_unknown_approval_fails_closed(self):
  from monitor_lab.snapshot import approval
  self.assertIsNone(approval({'source_id':'unapproved'}))
 def test_future_manifest_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   x=Path(td)/'SYNTHETIC.xlsx';m=create(x);obj=json.loads(m.read_text());obj['snapshot_as_of']='2026-11-13';m.write_text(json.dumps(obj))
   with patch('monitor_lab.common.operational_today',return_value=date(2026,11,12)):
    with self.assertRaises(ValueError):live_signal(x,m,ROOT/'artifacts/deployment_final.joblib','2026-11-12',1,True)
 def test_clock_advances_without_reopening_evaluation(self):
  with tempfile.TemporaryDirectory() as td:
   x=Path(td)/'SYNTHETIC.xlsx';m=create(x,end=date(2026,11,12))
   with patch('monitor_lab.common.operational_today',return_value=date(2026,11,13)):
    r=live_signal(x,m,ROOT/'artifacts/deployment_final.joblib','2026-11-13',0,True)
   self.assertEqual(r['status'],'synthetic_signal_only');self.assertEqual(r['mode'],'inference_only_2026');self.assertFalse(r['real_order_authorized'])
 def test_future_decision_rejected_before_snapshot(self):
  with patch('monitor_lab.common.operational_today',return_value=date(2026,11,12)):
   with tempfile.TemporaryDirectory() as td:
    m=Path(td)/'manifest.json';m.write_text(json.dumps({'synthetic':True}))
    with self.assertRaises(ValueError):live_signal('missing.xlsx',m,'missing.joblib','2026-11-13',0,True)
 def test_manifest_missing_fields_is_clear_error(self):
  from monitor_lab.snapshot import validate_manifest
  with self.assertRaisesRegex(ValueError,'ausente'):validate_manifest({'synthetic':True})
 def test_manifest_boolean_strings_are_rejected(self):
  from monitor_lab.snapshot import validate_manifest
  with tempfile.TemporaryDirectory() as td:
   x=Path(td)/'SYNTHETIC.xlsx';m=create(x);obj=json.loads(m.read_text());obj['synthetic']='false'
   with self.assertRaisesRegex(ValueError,'booleanos'):validate_manifest(obj)
 def test_duplicate_predictor_header_is_rejected(self):
  import zipfile,hashlib
  from monitor_lab.common import sha
  with tempfile.TemporaryDirectory() as td:
   x=Path(td)/'SYNTHETIC.xlsx';m=create(x);obj=json.loads(m.read_text());y=Path(td)/'DUPLICATE_SYNTHETIC.xlsx'
   with zipfile.ZipFile(x) as zin,zipfile.ZipFile(y,'w') as zout:
    for name in zin.namelist():
     content=zin.read(name)
     if name.endswith('sheet1.xml'):content=content.decode().replace('</row>','<c r="T1" t="inlineStr"><is><t>DXY Curncy|PX_LAST</t></is></c></row>',1).encode()
     zout.writestr(name,content)
   obj['snapshot_sha256']=sha(y);obj['schema_sha256']=hashlib.sha256(json.dumps(['FECHA']+sorted(PREDICTORS)+['DXY Curncy|PX_LAST'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
   with self.assertRaisesRegex(ValueError,'duplicadas'):load_fields(y,date(2026,11,11),PREDICTORS,obj)
