"""Paquete reproducible por lista permitida; no distribuye datos ni modelos."""
import hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXED=('.gitattributes','.gitignore','README.md','requirements.txt','LICENSE','entrega.ipynb','exportar.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def files():
 chosen=[ROOT/n for n in FIXED]
 for folder,pattern in [('docs','*.md'),('itau_entrega','*.py'),('monitor_lab','*.py'),('tests','*.py'),('config','*.json'),('reports','*.csv'),('reports','*.json')]:chosen+=sorted((ROOT/folder).glob(pattern))
 return sorted(set(chosen))
def export(destination,require_executed=True):
 chosen=files()
 for p in chosen:
  text=p.read_text(encoding='utf-8')
  assert not re.search(r'[A-Z]:[/\\]Users[/\\]|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20}|github_pat_[A-Za-z0-9_]{20}',text),p.name
  if p.suffix=='.ipynb':
   code=[c for c in json.loads(text)['cells'] if c['cell_type']=='code'];assert len(code)==6
   if require_executed:assert all(c.get('execution_count') is not None and not any(o.get('output_type')=='error' for o in c.get('outputs',[])) for c in code)
 manifest=dict(files={p.relative_to(ROOT).as_posix():sha(p) for p in chosen},notebook_executed=require_executed,source_data_distributed=False,trained_models_distributed=False,individual_predictions_distributed=False)
 m=ROOT/'MANIFIESTO_ENTREGA.json';m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');chosen.append(m)
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
  for p in chosen:z.write(p,p.relative_to(ROOT).as_posix())
 return dict(files=len(chosen),zip_sha256=sha(destination))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(export(a.output)))
