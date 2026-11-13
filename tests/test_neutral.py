import tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from itau_entrega.runtime import transition
from monitor_lab.engine import live_signal
from monitor_lab.predict import predict
from monitor_lab.fixtures import create
from monitor_lab.common import ROOT

class NeutralTests(unittest.TestCase):
 def test_all_nine_transitions(self):
  for prev in [-1,0,1]:
   for target in [-1,0,1]:
    with self.subTest(previous=prev,target=target):
     t=transition(prev,dict(status='historical_signal_only',position=target))
     self.assertEqual(t['target_position'],target);self.assertEqual(t['order_delta'],target-prev);self.assertEqual(t['position_after'],target);self.assertEqual(t['turnover_units'],abs(target-prev));self.assertEqual(t['action'],'HOLD' if prev==target else 'REBALANCE_AT_CONFIRMED_CLOSE')
 def test_argmax_three_targets_through_both_routes(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'SYNTHETIC.xlsx';manifest=create(path)
   for target,probs in [(-1,[.8,.1,.1]),(0,[.1,.8,.1]),(1,[.1,.1,.8])]:
    for prev in [-1,0,1]:
     with self.subTest(previous=prev,target=target),patch('monitor_lab.engine.score',return_value=np.array([probs])):
      a=live_signal(path,manifest,ROOT/'artifacts/deployment_final.joblib','2026-11-12',prev,True)
      b=predict(path,'2026-11-12',prev)
      self.assertEqual(a['position'],target);self.assertEqual(b['position'],target);self.assertEqual(a['transition'],b['transition']);self.assertEqual(b['transition']['target_position'],target);self.assertNotEqual(b['transition']['action'],'NO_ORDER')
 def test_blocking_zero_is_not_neutral_order(self):
  for prev in [-1,0,1]:
   for status in ['stale_snapshot','session_unconfirmed','insufficient_history','no_information']:
    t=transition(prev,dict(status=status,position=0));self.assertEqual(t['action'],'NO_ORDER');self.assertIsNone(t['target_position']);self.assertEqual(t['position_after'],prev);self.assertEqual(t['order_delta'],0)
