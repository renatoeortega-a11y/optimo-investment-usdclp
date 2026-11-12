"""CLI sólo inferencia. No hay entrenamiento, evaluación ni recalibración."""
import argparse,json
from pathlib import Path
from .common import ROOT
def main():
 p=argparse.ArgumentParser(description='Optimo Investment: inferencia congelada, sin órdenes reales');s=p.add_subparsers(dest='command',required=True)
 a=s.add_parser('live-signal');a.add_argument('--snapshot',required=True);a.add_argument('--manifest',required=True);a.add_argument('--decision',required=True);a.add_argument('--previous-position',type=int,choices=[-1,0,1],required=True);a.add_argument('--session-confirmed',action='store_true');a.add_argument('--model',default=str(ROOT/'artifacts/deployment_final.joblib'));a.add_argument('--output',required=True)
 a=s.add_parser('synthetic-demo');a.add_argument('--output',default=str(ROOT/'results/synthetic'))
 args=p.parse_args()
 from .engine import live_signal
 if args.command=='synthetic-demo':
  from .fixtures import create
  out=Path(args.output);out.mkdir(parents=True,exist_ok=True);snapshot=out/'SYNTHETIC.xlsx';manifest=create(snapshot);result=live_signal(snapshot,manifest,ROOT/'artifacts/deployment_final.joblib','2026-11-12',1,True);(out/'signal_SYNTHETIC.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 else:
  result=live_signal(args.snapshot,args.manifest,args.model,args.decision,args.previous_position,args.session_confirmed);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError) as e:print(json.dumps(dict(status='rejected',reason=str(e)),ensure_ascii=False));raise SystemExit(2)
