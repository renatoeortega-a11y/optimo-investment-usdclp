import io,json,unittest
from unittest.mock import patch
from datetime import date
import numpy as np
from itau_entrega import data,model,runtime,accounting

class DeliveryTests(unittest.TestCase):
 def test_97_features(self):self.assertEqual(len(data.FEATURES),97);self.assertEqual(len(set(data.FEATURES)),97)
 def test_no_cache_import(self):
  import ast
  for path in (data.ROOT/'itau_entrega').glob('*.py'):
   for n in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
    if isinstance(n,ast.ImportFrom):self.assertFalse((n.module or '').startswith(('research','src')))
 def test_allowed_positions(self):np.testing.assert_equal(model.positions([[.7,.1,.2],[.2,.6,.2],[.1,.1,.8]]),[-1,0,1])
 def test_bad_probability_sum(self):
  with self.assertRaises(ValueError):model.positions([[.1,.1,.1]])
 def test_negative_probabilities(self):
  with self.assertRaises(ValueError):model.positions([[-.1,.1,1.]])
 def test_all_legal_exposures_supported_by_accounting(self):self.assertEqual(len(accounting.ledger(np.zeros(5),[-3,-1,0,1,3])['spot']),5)
 def test_sealed_signal_before_any_load(self):
  with patch.object(runtime,'load_excel',side_effect=AssertionError),patch.object(runtime.joblib,'load',side_effect=AssertionError):self.assertEqual(runtime.signal('missing','missing','2026-11-13',True)['status'],'sealed_period')
 def test_unconfirmed_session_abstains(self):self.assertEqual(runtime.signal('missing','missing','2024-11-13')['position'],0)
 def test_weekend_abstains(self):self.assertEqual(runtime.signal('missing','missing','2024-11-16',True)['position'],0)
 def test_closed_day_does_not_liquidate_existing_position(self):self.assertEqual(runtime.transition(1,{'status':'session_unconfirmed','position':0}),dict(action='NO_ORDER',previous_position=1,target_position=None,order_delta=0,turnover_units=0,position_after=1))
 def test_signal_reversal_transition(self):self.assertEqual(runtime.transition(-1,{'status':'historical_signal_only','position':1})['turnover_units'],2)
 def test_cost_units(self):
  x=accounting.ledger([.01,-.01],[1,-1],1);self.assertAlmostEqual(x['cost'].sum(),.0004);self.assertAlmostEqual(x['spot'].sum(),.02)
 def test_flip_is_two_turnover_units(self):np.testing.assert_equal(accounting.ledger([0,0],[1,-1])['turnover'],[1,3])
 def test_operation_count_includes_liquidation(self):self.assertEqual(accounting.stats([.01,-.01],[1,-1])['total_orders'],3)
 def test_no_carry_is_not_zero(self):
  x=accounting.stats([.01,.02],[1,1]);self.assertIsNone(x['carry_sum']);self.assertIsNone(x['total_net_sum'])
 def test_shared_reference_hits_suppressed(self):
  import csv
  with (data.ROOT/'reports/trading_totales.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
  for r in rows:
   if r['policy'] in ('buy','zero'):self.assertEqual(r['direction_accuracy'],'');self.assertEqual(r['win_rate_exposed_spot'],'')
 def test_feature_future_perturbation(self):
  raw={date(2024,1,5):{t+'|PX_LAST':100. for t in data.f.TICKERS.values()}};old,_=data.make_features(raw,date(2024,1,8));raw[date(2024,1,8)]={k:999. for k in raw[date(2024,1,5)]};new,_=data.make_features(raw,date(2024,1,8));np.testing.assert_equal(old,new)
 def test_model_not_available_yet(self):
  with patch.object(runtime.joblib,'load',return_value={'first_permitted_decision':'2025-01-01'}),patch.object(runtime,'load_excel',side_effect=AssertionError):self.assertEqual(runtime.signal('not_read','trusted_local','2024-12-30',True)['status'],'model_not_yet_available')
 def test_long_pays_positive_differential(self):self.assertAlmostEqual(accounting.ledger([0],[1],days=[3],annual_clp=.06,annual_usd=.04,day_count=360)['carry'][0],-.02*3/360)
 def test_short_receives_differential(self):self.assertGreater(accounting.ledger([0],[-1],days=[1],annual_clp=.06,annual_usd=.04,day_count=360)['carry'][0],0)
 def test_cash_not_assumed_zero(self):
  x=accounting.ledger([0],[0],days=[1],annual_clp=.06,annual_usd=.04,day_count=360);self.assertGreater(x['total_net'][0],0)
 def test_incomplete_carry_rejected(self):
  with self.assertRaises(ValueError):accounting.ledger([0],[1],annual_clp=.06)
 def test_model_encoding_does_not_fit_test(self):
  enc=model.Encoding().fit(np.array([[1.,np.nan],[3.,2.]]));before=enc.mean.copy();z=enc.transform(np.array([[1e6,np.nan]]));np.testing.assert_equal(before,enc.mean);self.assertEqual(z.shape,(1,4))
 def test_grids_frozen(self):self.assertEqual(model.GRID,(4,6));self.assertEqual(model.TEMPS,(.75,1,1.5,2));self.assertEqual(model.SEED,20261109)
 def xml(self,when):return ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>fecha</t></is></c><c r="B1" t="inlineStr"><is><t>USDCLP Curncy|PX_LAST</t></is></c></row><row r="2"><c r="A2" t="str"><v>'+when+'</v></c><c r="B2"><v>777</v></c></row></sheetData></worksheet>').encode()
 def test_future_never_decoded(self):
  original=data.number
  def guard(cell,strings):
   if cell.get('r')=='B2':raise AssertionError('Future decoded')
   return original(cell,strings)
  with patch.object(data,'number',side_effect=guard):self.assertEqual(list(data.guarded_rows(io.BytesIO(self.xml('2025-01-01')),[])),[])
 def test_decision_close_not_read_for_signal(self):
  original=data.number
  def guard(cell,strings):
   if cell.get('r')=='B2':raise AssertionError('Unknown decision close decoded')
   return original(cell,strings)
  with patch.object(data,'number',side_effect=guard):self.assertEqual(list(data.guarded_rows(io.BytesIO(self.xml('2024-01-03')),[],date(2024,1,2))),[])
 def test_synthetic_smoke(self):
  result=runtime.demo();self.assertTrue(result['positions_valid']);self.assertEqual(result['source'],'SYNTHETIC_ONLY_NOT_BACKTEST');self.assertIsNotNone(result['metrics']['total_net_sum'])
if __name__=='__main__':unittest.main()
