import json,tempfile,unittest
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch
import numpy as np
from itau_entrega import data
from monitor_lab.common import ROOT,CONFIG,verify_registration,read
from monitor_lab.snapshot import load_fields,PREDICTORS,FUNDING
from monitor_lab.engine import feature_vector,frozen_bundle,live_signal
from monitor_lab.fixtures import create

class MonitorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.path=Path(cls.tmp.name)/'SYNTHETIC.xlsx';cls.manifest=create(cls.path,malformed_future=True);cls.raw=load_fields(cls.path,date(2026,11,11),PREDICTORS,read(cls.manifest));cls.model=ROOT/'artifacts/deployment_final.joblib'
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_registration_immutable(self):verify_registration()
 def test_historical_guard_stays(self):
  with self.assertRaises(ValueError):data.load_excel(self.path,cutoff=date(2026,1,1))
 def test_original_feature_cutoff_stays(self):
  with self.assertRaises(ValueError):data.f.feature_cutoff(date(2026,1,2),'conservador_fecha')
 def test_exact_97_features(self):self.assertEqual(feature_vector(self.raw,date(2026,11,12))[0].shape,(97,))
 def test_future_values_never_affect_X(self):
  x,_=feature_vector(self.raw,date(2026,11,10));raw=dict(self.raw);raw[date(2026,11,10)]={k:1e100 for k in PREDICTORS};raw[date(2026,11,11)]={k:-1e100 for k in PREDICTORS};y,_=feature_vector(raw,date(2026,11,10));np.testing.assert_array_equal(x,y)
 def test_no_execution_close_used(self):
  x,_=feature_vector(self.raw,date(2026,11,12));raw=dict(self.raw);raw[date(2026,11,12)]={'USDCLP Curncy|PX_LAST':1e200};np.testing.assert_array_equal(x,feature_vector(raw,date(2026,11,12))[0])
 def test_filter_before_decode(self):self.assertNotIn(date(2026,11,13),self.raw)
 def test_model_fixed_at_authorized_cutoff(self):self.assertEqual(frozen_bundle(self.model)['last_train_known'],'2026-11-06')
 def test_hash_tamper_rejected(self):
  m=read(self.manifest);m['snapshot_sha256']='bad'
  with self.assertRaises(ValueError):load_fields(self.path,date(2026,11,11),PREDICTORS,m)
 def test_schema_rejected(self):
  m=read(self.manifest);m['schema_sha256']='bad'
  with self.assertRaises(ValueError):load_fields(self.path,date(2026,11,11),PREDICTORS,m)
 def test_predictor_cannot_read_carry(self):
  with self.assertRaises(ValueError):load_fields(self.path,date(2026,11,11),FUNDING,read(self.manifest))
 def test_valid_synthetic_inference_no_fit(self):
  with patch('itau_entrega.model.Model.__init__',side_effect=AssertionError('training forbidden')):r=live_signal(self.path,self.manifest,self.model,'2026-11-12',1,True)
  self.assertTrue(r['synthetic']);self.assertEqual(r['features'],97);self.assertTrue(r['max_source']<'2026-11-12');self.assertAlmostEqual(sum(r[k] for k in ('p_down','p_flat','p_up')),1);self.assertIn(r['position'],(-1,1));self.assertEqual(r['transition']['order_delta'],r['position']-1)
 def test_no_session_no_order(self):
  r=live_signal(self.path,self.manifest,self.model,'2026-11-12',1,False);self.assertEqual(r['transition']['action'],'NO_ORDER');self.assertEqual(r['transition']['position_after'],1)
 def test_weekend_no_order(self):
  r=live_signal(self.path,self.manifest,self.model,'2026-11-07',-1,True);self.assertEqual(r['status'],'session_unconfirmed')
 def test_stale_snapshot_no_order(self):
  p=Path(self.tmp.name)/'stale.json';m=read(self.manifest);m['snapshot_as_of']='2026-10-01';p.write_text(json.dumps(m));r=live_signal(self.path,p,self.model,'2026-11-12',1,True);self.assertEqual(r['status'],'stale_snapshot');self.assertEqual(r['transition']['position_after'],1)
 def test_no_2025_evaluation_route(self):
  with self.assertRaises(ValueError):live_signal(self.path,self.manifest,self.model,'2025-12-30',0,True)
 def test_no_future_asof_route(self):
  with self.assertRaises(ValueError):live_signal(self.path,self.manifest,self.model,'2027-01-01',0,True)
 def test_missing_values_encoded_not_new_imputation(self):
  raw={d:dict(r) for d,r in self.raw.items()};cut=date(2026,11,11);raw[cut]['DXY Curncy|PX_LAST']=None;v,_=feature_vector(raw,date(2026,11,12));self.assertTrue(np.isnan(v).any())
 def test_old_model_rejected(self):
  with self.assertRaises(ValueError):frozen_bundle(ROOT/'artifacts/annual_2024_validation_only.joblib')
 def test_climatology_known_strict(self):
  from monitor_lab.causal_counts import causal_counts
  h=[dict(known='2024-12-30',truth=-1)];o=[dict(known='2026-01-02',truth=1),dict(known='2026-01-05',truth=0)]
  np.testing.assert_array_equal(causal_counts(h,o,'2026-01-05'),[1,0,1])
 def test_climatology_rejects2025(self):
  from monitor_lab.causal_counts import causal_counts
  with self.assertRaises(ValueError):causal_counts([dict(known='2025-12-31',truth=1)],[],'2026-01-02')
 def test_labels_reader_does_not_return2025(self):
  with self.assertRaises(ValueError):load_fields(self.path,date(2026,11,11),{'USDCLP Curncy|PX_LAST'},read(self.manifest),role='labels_2026')
 def test_new_hash_allowed_only_with_separate_live_approval(self):
  m=read(self.manifest);m.update(synthetic=False,daily_feed_certified=True,source_id='SYNTHETIC_AUTHORITY_TEST_ONLY');p=Path(self.tmp.name)/'approved_synthetic_only.json';p.write_text(json.dumps(m));from monitor_lab.common import sha
  entry=dict(manifest_file_sha256=sha(p),daily_feed_certified=True)
  with patch('monitor_lab.engine.approval',return_value=entry),patch('monitor_lab.snapshot.approval',return_value=entry):r=live_signal(self.path,p,self.model,'2026-11-12',0,True)
  self.assertAlmostEqual(sum(r[k] for k in ('p_down','p_flat','p_up')),1)
  with self.assertRaises(ValueError):load_fields(self.path,date(2026,11,11),FUNDING,m,role='funding_realized_2026')
