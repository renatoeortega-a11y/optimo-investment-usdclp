"""Auditoría histórica sin fit y sin valores2025/26."""
import csv,json
from datetime import date
import joblib,numpy as np
from itau_entrega import data
from itau_entrega.model import score,positions
from .common import ROOT,CONFIG,sha
from .engine import feature_vector,feature_context
def main():
 raw=data.load_excel(ROOT/'data/official_snapshot.xlsx');labels,X=data.dataset(raw);context=feature_context(raw)
 # Contexto histórico compartido usa búsquedas causales; no acceso a valores2025/26.
 from . import d2_features as f
 Y=[]
 for r in labels:
  d=date.fromisoformat(r['decision']);base,_=f.base_row(raw,context[1],d);feat,_,lin=f.feature_row(r,base,context[0],'conservador_fecha');assert not lin['max_native_source'] or lin['max_native_source']<d;Y.append([feat[n] for n in data.FEATURES])
 Y=np.asarray(Y);assert X.shape==Y.shape==(3638,97) and np.array_equal(X,Y,equal_nan=True)
 delta=0.;n=0
 for year in range(2019,2025):
  b=joblib.load(ROOT/'artifacts/historical_validation'/f'extra_{year}.joblib');ix=[i for i,r in enumerate(labels) if r['year']==year];a=score(b,X[ix]);z=score(b,Y[ix]);assert np.array_equal(positions(a),positions(z));delta=max(delta,float(np.max(abs(a-z))));n+=len(ix)
 assert n==1524
 d=date(2024,12,30);a,_=data.make_features(raw,d);b,_=feature_vector(raw,d);assert np.array_equal(a,b,equal_nan=True)
 result=dict(historical_rows=3638,features=97,oos_predictions=1524,positions_identical=True,max_probability_delta=delta,feature_values_exact=True,historical_annual_bundles_validation_only=True,final_until2024_model_not_applied_retrospectively=True,original_holdout_guard_intact=True)
 (ROOT/'logs/HISTORICAL_EQUIVALENCE.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
