"""CLI sólo inferencia. No hay entrenamiento, evaluación ni recalibración."""
import argparse,json,sys,hashlib
from pathlib import Path
from .common import ROOT
def main():
 p=argparse.ArgumentParser(description='Optimo Investment: inferencia congelada, sin órdenes reales');s=p.add_subparsers(dest='command',required=True)
 a=s.add_parser('live-signal');a.add_argument('--snapshot',required=True);a.add_argument('--manifest',required=True);a.add_argument('--decision',required=True);a.add_argument('--previous-position',type=int,choices=[-1,0,1],required=True);a.add_argument('--session-confirmed',action='store_true');a.add_argument('--model',default=str(ROOT/'artifacts/deployment_final.joblib'));a.add_argument('--output',required=True)
 a=s.add_parser('synthetic-demo');a.add_argument('--output',default=str(ROOT/'results/synthetic'))
 a=s.add_parser('predict');a.add_argument('--excel',required=True);a.add_argument('--decision',required=True);a.add_argument('--previous-position',type=int,choices=[-1,0,1],required=True);a.add_argument('--mode',choices=['local','certified'],default='local');a.add_argument('--trust-config');a.add_argument('--session-unconfirmed',action='store_true');a.add_argument('--csv',action='store_true');a.add_argument('--json',action='store_true')
 args=p.parse_args()
 from .engine import live_signal
 if args.command=='predict':
  from .predict import predict
  result=predict(args.excel,args.decision,args.previous_position,args.mode,args.trust_config,args.session_unconfirmed,args.csv)
  if not args.json:
   print('USD/CLP | Decisión:',result['decision'],'| Información utilizada hasta:',result['max_information_used'] or 'sin nueva señal')
   print('Procedencia:', 'firma de canal verificada' if result['externally_certified'] else 'archivo del usuario; NO certificado externamente')
   if result['p_down'] is not None:print('Probabilidad de baja: {:.2%} | Estabilidad: {:.2%} | Alza: {:.2%}'.format(result['p_down'],result['p_flat'],result['p_up']))
   t=result['transition'];print('Posición anterior:',t['previous_position'],'| Objetivo:',t['target_position'],'| Rebalanceo:',t['order_delta'],'| Acción:',t['action'])
   print('Estado:',result['status'])
   if result['reason']:print(result['reason'])
   print('Propuesta, NO orden real. Registro JSON privado en outputs/predict/.')
 elif args.command=='synthetic-demo':
  from .fixtures import create
  out=Path(args.output);out.mkdir(parents=True,exist_ok=True);snapshot=out/'SYNTHETIC.xlsx';manifest=create(snapshot);result=live_signal(snapshot,manifest,ROOT/'artifacts/deployment_final.joblib','2026-11-12',1,True);(out/'signal_SYNTHETIC.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 else:
  result=live_signal(args.snapshot,args.manifest,args.model,args.decision,args.previous_position,args.session_confirmed);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf-8')
 if args.command!='predict' or args.json:print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 try:main()
 except (ValueError,OSError) as e:
  failure=dict(status='rejected',reason=str(e),executed=False,real_order_authorized=False)
  if len(sys.argv)>1 and sys.argv[1]=='predict':
   out=ROOT/'outputs/predict';out.mkdir(parents=True,exist_ok=True);key=hashlib.sha256(json.dumps(dict(error=failure,arguments=sys.argv[2:]),sort_keys=True).encode()).hexdigest()[:20];(out/('rejected_'+key+'.json')).write_text(json.dumps(failure,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps(failure,ensure_ascii=False));raise SystemExit(2)
