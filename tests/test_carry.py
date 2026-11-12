import unittest
from datetime import date
import numpy as np
from itau_entrega.carry import ledger,factors,metrics,bootstrap,load_funding

class CarryTests(unittest.TestCase):
 def test_zero_is_clp_cash(self):
  l=ledger([.02],[0],[.001],[.0005]);self.assertAlmostEqual(l['total'][0],.001);self.assertEqual(l['excess'][0],0)
 def test_long_no_double_clp(self):
  l=ledger([.02],[1],[.001],[.0005]);self.assertAlmostEqual(l['total'][0],1.02*1.0005-1);self.assertAlmostEqual(l['carry'][0],1.02*.0005-.001)
 def test_short_finances_usd_receives_two_clp(self):
  l=ledger([.02],[-1],[.001],[.0005]);self.assertAlmostEqual(l['total'][0],2*.001-(1.02*1.0005-1))
 def test_cost_entry_exit(self):
  l=ledger([0],[1],[0],[0],1);self.assertAlmostEqual(l['cost'][0],.0002)
 def test_compound_not_sum(self):
  l=ledger([.1,.1],[1,1],[0,0],[0,0]);self.assertAlmostEqual(l['wealth'][-1]-1,.21)
 def test_friday_monday_three_days(self):
  t=date(2024,1,5);s=date(2024,1,8);rows={t:{'CLICP Index|PX_LAST':100.,'FEDL01 Index|PX_LAST':3.6},s:{'CLICP Index|PX_LAST':100.03,'FEDL01 Index|PX_LAST':99.}}
  c,u,d,a=factors(rows,[(t,s)]);self.assertEqual(d[0],3);self.assertAlmostEqual(c[0],.0003);self.assertAlmostEqual(u[0],1.0001**3-1);self.assertEqual(a['max_usd_age_calendar_days'],2)
 def test_usd_percent_units(self):
  t=date(2024,1,2);s=date(2024,1,3);c,u,_,_=factors({t:{'CLICP Index|PX_LAST':100,'FEDL01 Index|PX_LAST':3.6},s:{'CLICP Index|PX_LAST':100.01}},[(t,s)]);self.assertAlmostEqual(u[0],.0001)
 def test_no_future_endpoint_rate(self):
  t=date(2024,1,2);s=date(2024,1,3)
  with self.assertRaises(ValueError):factors({t:{'CLICP Index|PX_LAST':100},s:{'CLICP Index|PX_LAST':100.01,'FEDL01 Index|PX_LAST':3.6}},[(t,s)])
 def test_missing_index_endpoint_fails(self):
  with self.assertRaises(ValueError):factors({date(2024,1,2):{'FEDL01 Index|PX_LAST':3.6}},[(date(2024,1,2),date(2024,1,3))])
 def test_explicit_bounded_index_estimate(self):
  a=date(2024,1,2);b=date(2024,1,4);m=date(2024,1,3);rows={a:{'CLICP Index|PX_LAST':100,'FEDL01 Index|PX_LAST':3.6},b:{'CLICP Index|PX_LAST':101}}
  c,_,_,info=factors(rows,[(a,m)],True);self.assertAlmostEqual(c[0],1.01**.5-1);self.assertTrue(info['clp_endpoint_estimates_required'])
 def test_interpolation_never_extrapolates(self):
  with self.assertRaises(ValueError):factors({date(2024,1,2):{'CLICP Index|PX_LAST':100,'FEDL01 Index|PX_LAST':3.6}},[(date(2024,1,2),date(2024,1,3))],True)
 def test_registered_endpoint_sensitivity(self):
  a=date(2024,1,2);b=date(2024,1,4);m=date(2024,1,3);rows={a:{'CLICP Index|PX_LAST':100,'FEDL01 Index|PX_LAST':3.6},b:{'CLICP Index|PX_LAST':101}}
  lo,_,_,info=factors(rows,[(a,m),(m,b)],True,'previous_native');hi,_,_,_=factors(rows,[(a,m),(m,b)],True,'next_native')
  np.testing.assert_allclose(lo,[0,.01]);np.testing.assert_allclose(hi,[.01,0]);self.assertEqual(info['clp_unique_estimated_endpoints'],1);self.assertEqual(info['clp_estimated_endpoint_appearances'],2);self.assertEqual(info['clp_intervals_affected'],2)
 def test_invalid_sensitivity_fails(self):
  with self.assertRaises(ValueError):factors({},[],True,'unregistered')
 def test_reserved_interval_fails(self):
  with self.assertRaises(ValueError):factors({},[(date(2024,12,31),date(2025,1,1))])
 def test_negative_source_accrual_preserved(self):
  l=ledger([0],[0],[-.00001],[0]);self.assertAlmostEqual(l['total'][0],-.00001)
 def test_drawdown_compounded(self):
  l=ledger([.1,-.1],[1,1],[0,0],[0,0]);self.assertAlmostEqual(metrics(l,np.ones(2),[1,1])['max_drawdown'],-.1)
 def test_decomposition(self):
  l=ledger([.01,-.02],[1,-1],[.001,.001],[.0005,.0005],1)
  np.testing.assert_allclose(l['total'],l['spot']+l['base_cash']+l['clp_financing']+l['usd_income']-l['cost'])
 def test_cash_cost_invariant(self):
  np.testing.assert_array_equal(ledger([.01],[0],[.001],[.0005],5)['total'],[.001])
 def test_no_leverage(self):
  with self.assertRaises(ValueError):ledger([0],[3],[0],[0])
 def test_bootstrap_zero(self):
  b=bootstrap(np.zeros(100),reps=49);self.assertEqual(b['lo'],0);self.assertEqual(b['hi'],0);self.assertEqual(b['p'],1)
 def test_funding_reader_filters_before_decode(self):
  import tempfile,zipfile
  from pathlib import Path
  from unittest.mock import patch
  from itau_entrega import data
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'synthetic.xlsx'
   with zipfile.ZipFile(p,'w') as z:
    z.writestr('xl/workbook.xml',f'<workbook xmlns="{data.M[1:-1]}" xmlns:r="{data.REL[1:-1]}"><sheets><sheet name="datos" r:id="r1"/></sheets></workbook>')
    z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
    z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{data.M[1:-1]}"><sheetData><row><c r="A1" t="inlineStr"><is><t>date</t></is></c><c r="B1" t="inlineStr"><is><t>CLICP Index|PX_LAST</t></is></c><c r="C1" t="inlineStr"><is><t>FEDL01 Index|PX_LAST</t></is></c></row><row><c r="A2" t="str"><v>2024-01-02</v></c><c r="B2"><v>100</v></c><c r="C2"><v>3.6</v></c></row><row><c r="A3" t="str"><v>2025-01-02</v></c><c r="B3" t="s"><v>999999</v></c><c r="C3" t="s"><v>999999</v></c></row></sheetData></worksheet>')
   with patch('itau_entrega.data.sha',return_value=data.SHA):r=load_funding(p)
   self.assertEqual(list(r),[date(2024,1,2)])
 def test_stale_fedl_fails(self):
  rows={date(2024,1,1):{'FEDL01 Index|PX_LAST':3.6},date(2024,1,10):{'CLICP Index|PX_LAST':100},date(2024,1,11):{'CLICP Index|PX_LAST':100.1}}
  with self.assertRaises(ValueError):factors(rows,[(date(2024,1,10),date(2024,1,11))])

if __name__=='__main__':unittest.main()
