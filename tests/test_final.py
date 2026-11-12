import unittest
import numpy as np
from itau_entrega.contrastes import dm_hac,bootstrap
from itau_entrega import runtime,model
class FinalTests(unittest.TestCase):
 def test_dm_antisymmetry(self):
  d=np.sin(np.arange(200))*.001+.0001;a=dm_hac(d);b=dm_hac(-d);self.assertAlmostEqual(a['statistic'],-b['statistic']);self.assertAlmostEqual(a['p'],b['p'])
 def test_degenerate_dm_not_fabricated(self):self.assertIsNone(dm_hac(np.zeros(100))['p'])
 def test_bootstrap_zero(self):
  r=bootstrap(np.zeros(100));self.assertEqual(r['lo'],0);self.assertEqual(r['hi'],0);self.assertEqual(r['p'],1)
 def test_same_buy_reference(self):
  r=np.linspace(-.01,.01,100);np.testing.assert_equal(np.ones(100)*r,r)
 def test_unexpected_neutral_does_not_order_liquidation(self):
  self.assertEqual(runtime.transition(1,dict(status='policy_review_required',position=0))['position_after'],1)
 def test_original_argmax(self):np.testing.assert_equal(model.positions([[.51,.01,.48],[.45,.01,.54]]),[-1,1])
