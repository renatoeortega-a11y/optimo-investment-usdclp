"""Fixtures económicas SINTÉTICAS, nunca se mezclan con el backtest real."""
import hashlib,json,math,zipfile
from datetime import date,timedelta
from pathlib import Path
from xml.sax.saxutils import escape
from .common import sha
from .snapshot import PREDICTORS
def col(i):
 s=''
 while i:i,r=divmod(i-1,26);s=chr(65+r)+s
 return s
def create(path,end=date(2026,11,11),count=400,malformed_future=False):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);ds=[];d=end
 while len(ds)<count:
  if d.weekday()<5:ds.append(d)
  d-=timedelta(days=1)
 ds=sorted(ds);headers=['FECHA']+sorted(PREDICTORS);rows=['<row>'+''.join(f'<c r="{col(k+1)}1" t="inlineStr"><is><t>{escape(h)}</t></is></c>' for k,h in enumerate(headers))+'</row>']
 for j,d in enumerate(ds,2):
  cells=[f'<c r="A{j}" t="str"><v>{d}</v></c>']
  for k,h in enumerate(headers[1:],2):
   base=800 if h.startswith('USDCLP Curncy') else 4 if any(t in h for t in ('USGG','CHOV','CHNI')) else 20 if any(t in h for t in ('VIX','V1M')) else 100
   v=base*(1+.001*math.sin(j*.23+k)+.0001*j)
   cells.append(f'<c r="{col(k)}{j}"><v>{v}</v></c>')
  rows.append('<row>'+''.join(cells)+'</row>')
 if malformed_future:rows.append(f'<row><c r="A9999" t="str"><v>2026-11-13</v></c><c r="B9999" t="s"><v>999999999</v></c></row>')
 with zipfile.ZipFile(path,'w') as z:
  z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="datos" r:id="r1"/></sheets></workbook>');z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>');z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join(rows)+'</sheetData></worksheet>')
 manifest=dict(source_id='SYNTHETIC_FIXTURE',snapshot_sha256=sha(path),schema_sha256=hashlib.sha256(json.dumps(headers,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),snapshot_as_of=str(end),synthetic=True,daily_feed_certified=False,publication_times_certified=False)
 target=path.with_suffix('.json');target.write_text(json.dumps(manifest,indent=2),encoding='utf-8');return target
