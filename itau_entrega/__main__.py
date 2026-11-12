import argparse,json
from pathlib import Path
from . import runtime
def main():
 p=argparse.ArgumentParser(description='Entrega USD/CLP; no órdenes reales; reservado sellado');sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('demo')
 a=sub.add_parser('fit-deployment');a.add_argument('--excel',required=True);a.add_argument('--cutoff',required=True);a.add_argument('--output',required=True)
 a=sub.add_parser('carry');a.add_argument('--excel',required=True);a.add_argument('--predictions',required=True);a.add_argument('--output',required=True);a.add_argument('--allow-clp-interpolation',action='store_true')
 for name in ('validate','reproduce','fit-final'):
  a=sub.add_parser(name);a.add_argument('--excel',required=True)
  if name!='validate':a.add_argument('--output',default='outputs/reproduccion' if name=='reproduce' else 'outputs/model_final.joblib')
 a=sub.add_parser('signal');a.add_argument('--excel',required=True);a.add_argument('--model',required=True);a.add_argument('--decision',required=True);a.add_argument('--previous-position',type=int,choices=[-3,-1,0,1,3],required=True);a.add_argument('--session-confirmed',action='store_true');a.add_argument('--output',default='outputs/signal_PRIVADA.json')
 args=p.parse_args()
 if args.command=='fit-deployment':
  from .deployment import fit_deployment
  result=fit_deployment(args.excel,args.cutoff,args.output)
 elif args.command=='carry':
  from .carry import evaluate
  summary,_,_,_=evaluate(args.excel,args.predictions,args.output,args.allow_clp_interpolation);result=dict(status='estimated_carry_completed',official=False,aggregates=summary)
 elif args.command=='demo':result=runtime.demo()
 elif args.command=='validate':
  labels,X=runtime.prepare(args.excel);result=dict(source_sha256=runtime.SHA,rows=len(labels),features=X.shape[1],last_label=max(r['known'] for r in labels),reserved_sealed=True)
 elif args.command=='reproduce':
  records=runtime.reproduce(args.excel,args.output);result=dict(external_n=len(records),output=args.output,private_predictions=True)
 elif args.command=='fit-final':result=runtime.fit_final(args.excel,args.output)
 else:
  result=runtime.signal(args.excel,args.model,args.decision,args.session_confirmed);result['transition']=runtime.transition(args.previous_position,result);path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError) as error:
  print(json.dumps(dict(status='invalid_input',error=str(error)),ensure_ascii=False));raise SystemExit(2)
