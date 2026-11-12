import io,json,tempfile,unittest,inspect
from datetime import date
from pathlib import Path
from unittest.mock import patch
import numpy as np
from itau_entrega import deployment,model,data
from monitor_lab.common import ROOT,CONFIG,sha,read
from monitor_lab.engine import live_signal,feature_vector,frozen_bundle
from monitor_lab.snapshot import load_fields,PREDICTORS
from monitor_lab.fixtures import create

class DeploymentTests(unittest.TestCase):
 def test_fixed_cutoff(self):
  self.assertEqual(str(deployment.validate_cutoff('2026-11-06')),'2026-11-06')
  for c in ['2026-11-07','2024-12-31',None]:
   with self.assertRaises(ValueError):deployment.validate_cutoff(c)
 def test_historical_reader_remains_sealed(self):
  with self.assertRaises(ValueError):list(data.guarded_rows(io.BytesIO(b''),[],date(2026,11,6)))
 def test_future_training_cell_not_decoded(self):
  xml=f'<worksheet xmlns="{data.M[1:-1]}"><sheetData><row><c r="A1" t="str"><v>date</v></c><c r="B1" t="str"><v>USDCLP Curncy|PX_LAST</v></c></row><row><c r="A2" t="str"><v>2026-11-07</v></c><c r="B2" t="s"><v>999999</v></c></row></sheetData></worksheet>'
  with patch.object(data,'WANTED',{'USDCLP Curncy|PX_LAST'}):self.assertEqual(list(deployment.authorized_rows(io.BytesIO(xml.encode()),[],date(2026,11,6))),[])
 def test_no_overwrite_and_no_fit_on_invalid_cutoff(self):
  with patch.object(model,'Model',side_effect=AssertionError('fit prohibited')):
   with self.assertRaises(ValueError):deployment.fit_deployment('missing','2026-11-07','missing')
 def test_bundle_contract(self):
  b=frozen_bundle(ROOT/'artifacts/deployment_final.joblib');self.assertEqual(b['feature_names'],data.FEATURES);self.assertEqual(b['class_order'],[-1,0,1]);self.assertEqual(b['temperature'],1.0);self.assertEqual(b['n_cal'],0);self.assertEqual(b['training_cutoff'],'2026-11-06')
 def test_repeatability_and_no_training_in_live(self):
  p=ROOT/'artifacts/deployment_final.joblib';before=sha(p)
  with tempfile.TemporaryDirectory() as td:
   x=Path(td)/'SYNTHETIC.xlsx';m=create(x)
   with patch.object(model.Encoding,'fit',side_effect=AssertionError('encoder fit forbidden')),patch.object(model.Model,'__init__',side_effect=AssertionError('model fit forbidden')):
    a=live_signal(x,m,p,'2026-11-12',1,True);b=live_signal(x,m,p,'2026-11-12',1,True)
   self.assertEqual(a,b)
  self.assertEqual(before,sha(p))
 def test_future_rows_do_not_change_prediction(self):
  with tempfile.TemporaryDirectory() as td:
   x=Path(td)/'SYNTHETIC.xlsx';m=create(x,end=date(2026,11,11));a=live_signal(x,m,ROOT/'artifacts/deployment_final.joblib','2026-11-12',1,True)
   m=create(x,end=date(2026,11,11),malformed_future=True);b=live_signal(x,m,ROOT/'artifacts/deployment_final.joblib','2026-11-12',1,True)
   self.assertEqual(a,b)
 def test_daily_update_changes_features_not_model(self):
  p=ROOT/'artifacts/deployment_final.joblib';before=sha(p)
  with tempfile.TemporaryDirectory() as td:
   x=Path(td)/'SYNTHETIC.xlsx';m=create(x,end=date(2026,11,10));raw=load_fields(x,date(2026,11,10),PREDICTORS,read(m));a,_=feature_vector(raw,date(2026,11,11))
   m=create(x,end=date(2026,11,11),count=401);raw=load_fields(x,date(2026,11,11),PREDICTORS,read(m));b,_=feature_vector(raw,date(2026,11,12));self.assertFalse(np.array_equal(a,b,equal_nan=True))
   live_signal(x,m,p,'2026-11-12',1,True)
  self.assertEqual(before,sha(p))
 def test_preparation_not_exposed_in_live_cli(self):
  source=(ROOT/'monitor_lab/__main__.py').read_text();self.assertNotIn('fit-deployment',source);self.assertNotIn('deployment import',source)
 def test_training_pairs_respect_cutoff_and_causal_lineage(self):
  with tempfile.TemporaryDirectory() as td:
   x=Path(td)/'SYNTHETIC.xlsx';m=create(x,end=date(2026,11,11));raw=load_fields(x,date(2026,11,11),PREDICTORS,read(m));labels,X=deployment.training_dataset(raw,'2026-11-06')
   self.assertEqual(X.shape[1],97);self.assertLessEqual(max(r['known'] for r in labels),'2026-11-06');self.assertTrue(all(r['decision']<r['known'] for r in labels))
