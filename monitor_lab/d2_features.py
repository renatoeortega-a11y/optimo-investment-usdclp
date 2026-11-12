"""Funciones D2 vigentes extraídas sin cambiar fórmulas; no depende del repositorio de investigación."""
from __future__ import annotations
import math,bisect
from bisect import bisect_left
from datetime import date,timedelta
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from types import SimpleNamespace
import numpy as np
END=date(2024,12,31)
def numeric(x):
 return float(x) if isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x) else None


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    ticker: str
    unit: str
    kind: str

CORE = (
    FeatureSpec("dxy", "DXY Curncy", "nivel_indice", "positive"),
    FeatureSpec("cobre_lme", "LMCADS03 Comdty", "USD_tonelada", "positive"),
    FeatureSpec("oro", "XAU Curncy", "USD_onza_troy", "positive"),
    FeatureSpec("usdbrl", "USDBRL Curncy", "BRL_USD", "positive"),
    FeatureSpec("usdmxn", "USDMXN Curncy", "MXN_USD", "positive"),
    FeatureSpec("spx", "SPX Index", "puntos_indice", "positive"),
    FeatureSpec("vix", "VIX Index", "porcentaje_anual", "nonnegative"),
    FeatureSpec("treasury_2y", "USGG2YR Index", "porcentaje_anual", "rate"),
    FeatureSpec("treasury_10y", "USGG10YR Index", "porcentaje_anual", "rate"),
    FeatureSpec("tpm", "CHOVCHOV Index", "porcentaje_anual_nominal", "rate"),
    FeatureSpec("ndf_implicito_1m", "CHNI1M Curncy", "porcentaje_anual", "rate"),
    FeatureSpec("vol_clp_1m", "USDCLPV1M Curncy", "porcentaje_anual", "nonnegative"),
)


def finite_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    return numeric(value)

def value_valid(value: object, spec: FeatureSpec) -> bool:
    v = finite_number(value)
    if v is None:
        return False
    if spec.kind == "positive":
        return v > 0
    if spec.kind == "nonnegative":
        return v >= 0
    return True



NYSE={
2019:'01-01 01-21 02-18 04-19 05-27 07-04 09-02 11-28 12-25',
2020:'01-01 01-20 02-17 04-10 05-25 07-03 09-07 11-26 12-25',
2021:'01-01 01-18 02-15 04-02 05-31 07-05 09-06 11-25 12-24',
2022:'01-17 02-21 04-15 05-30 06-20 07-04 09-05 11-24 12-26',
2023:'01-02 01-16 02-20 04-07 05-29 06-19 07-04 09-04 11-23 12-25',
2024:'01-01 01-15 02-19 03-29 05-27 06-19 07-04 09-02 11-28 12-25'}

LME={2023:'05-01 05-08 05-29 08-28 12-25 12-26',2024:'01-01 03-29 04-01 05-06 05-27 08-26 12-25 12-26'}

BRAZIL_2024='02-12 02-13 03-29 04-21 05-01 05-30 09-07 10-12 11-02 11-15 11-20 12-25'

POLICY={
'dxy':(0,'BGN/global OTC; no equiparar spot al futuro DX','17:00 America/New_York declarada','bgn;ice'),
'cobre_lme':(6,'LME business days; cobertura documental parcial desde mayo 2023','Londres: campo de cierre exacto pendiente','lme;lme_update;lme_prices'),
'oro':(0,'Spot OTC global; no equiparar XAU BGN a fixing LBMA o futuros','17:00 America/New_York declarada','bgn;bfix'),
'usdbrl':(5,'Regional BGN onshore; calendario bancario/B3 solo indicio, 2024','America/Sao_Paulo: hora histórica no certificada','brazil;b3;bgn'),
'usdmxn':(0,'OTC BGN global; FIX Banxico es otra referencia','17:00 America/New_York declarada','bgn;banxico'),
'spx':(4,'Acciones US/índice SPX; calendario NYSE 2019–2024','16:00 America/New_York; 13:00 sesiones reducidas','nyse19;nyse22;nyse24;sp'),
'vix':(4,'Cboe SPX options; calendario NYSE usado SOLO como proxy','16:15 America/New_York declarada; histórico pendiente','vix;nyse19;nyse22'),
'treasury_2y':(0,'Generic Bloomberg OTC; SIFMA es recomendación, no cierre obligatorio','17:00 America/New_York declarada','sifma;sifma_limit'),
'treasury_10y':(0,'Generic Bloomberg OTC; no usar calendario de acciones','17:00 America/New_York declarada','sifma;sifma_limit'),
'tpm':(0,'Tasa administrada: vigencia por anuncio, no cotización de bolsa','Comunicado RPM desde 18:00 America/Santiago','tpm'),
'ndf_implicito_1m':(0,'NDF OTC: calendario del contribuidor y fixing por certificar','17:00 America/New_York declarada','bgn;bfix'),
'vol_clp_1m':(0,'Vol implícita OTC: calendario/contribuidores por certificar','17:00 America/New_York declarada','bgn')}

def in_dates(d, mapping): return d.strftime('%m-%d') in mapping.get(d.year,'').split()

def closed(feature,d,proxy=False):
    if feature=='spx': return d.weekday()>=5 or in_dates(d,NYSE)
    if feature=='cobre_lme': return d.weekday()>=5 or in_dates(d,LME)
    if proxy and feature=='vix': return d.weekday()>=5 or in_dates(d,NYSE)
    if proxy and feature=='usdbrl': return d.weekday()>=5 or (d.year==2024 and d.strftime('%m-%d') in BRAZIL_2024.split())
    return False

cal=SimpleNamespace(closed=closed)

@lru_cache(maxsize=None)
def candidate_closed(name,d):
    # Exclusión preventiva, no nueva certificación de Bloomberg.
    extra=(d.year==2022 and d.strftime('%m-%d') in '04-15 04-18 05-02 06-02 06-03 08-29 12-26 12-27'.split()) or (d.year==2023 and d.strftime('%m-%d') in '01-02 04-07 04-10'.split())
    return cal.closed(name,d,proxy=True) or (name=='cobre_lme' and extra)

calendars=SimpleNamespace(POLICY=POLICY,closed=closed)
previous=SimpleNamespace(candidate_closed=candidate_closed)

LOG = {'dxy', 'cobre_lme', 'oro', 'usdbrl', 'usdmxn', 'spx',
       'hg_comex', 'bcom', 'eurusd', 'usdjpy'}

class OfficialSeries(dict):
    """Índice inmutable de fechas; los valores auténticos nunca se reemplazan."""
    def __init__(self, values):
        super().__init__(values)
        self.dates = {n: tuple(sorted(v)) for n,v in values.items()}

def change(n, current, anchor):
    return 100 * math.log(current / anchor) if n in LOG else current - anchor

def documented_closed(n, d):
    return (n == 'spx' and calendars.closed(n, d)) or (
        n == 'cobre_lme' and previous.candidate_closed(n, d))

def last_authentic(series, n, d, hidden=None):
    hidden = hidden or {}
    # Nunca se consulta si existen registros futuros para elegir la observación.
    dates = series.dates[n] if isinstance(series,OfficialSeries) else sorted(series[n])
    j = bisect.bisect_left(dates,d)-1
    while j>=0 and dates[j] in hidden.get(n,set()):
        j-=1
    return dates[j] if j>=0 else None

def calendar_value(series, n, d):
    if d in series[n]:
        return d, series[n][d]
    a = last_authentic(series, n, d)
    cap = calendars.POLICY[n][0]
    if a is None or not cap or (d - a).days > cap:
        return None
    middle = [a + timedelta(days=j) for j in range(1, (d-a).days+1)
              if (a + timedelta(days=j)).weekday() < 5]
    if middle and all(documented_closed(n, t) for t in middle):
        return a, series[n][a]
    return None

def previous_weekday(d):
    t=d-timedelta(days=1)
    while t.weekday()>4:t-=timedelta(days=1)
    return t

def feature_cutoff(d,scenario):
    if scenario not in ('conservador_fecha','contemporaneo_experimental'):raise ValueError('Escenario desconocido')
    return previous_weekday(d) if scenario=='conservador_fecha' else d

flex=SimpleNamespace(calendar_value=calendar_value,last_authentic=last_authentic,change=change)
old=SimpleNamespace(feature_cutoff=feature_cutoff,previous_weekday=previous_weekday,flex=flex,NAMES=tuple(s.name for s in CORE))

EXTRAS={'usdclp':'USDCLP Curncy','bcom':'BCOM Index','brent':'CO1 Comdty','wti':'CL1 Comdty','move':'MOVE Index','eurusd':'EURUSD Curncy'}

NAMES=list(s.name for s in CORE)+list(EXTRAS)

MOM=('usdclp','dxy','cobre_lme','usdbrl','usdmxn','spx')

def histories(series,n,cut):
    ds,vs=series[n];j=bisect.bisect_right(ds,cut)
    ds,vs=ds[max(0,j-90):j],vs[max(0,j-90):j]
    if not ds or (cut-ds[-1]).days>7:return [],np.array([])
    # Restrict to uninterrupted native sequence; no pretending long missing interval is daily.
    start=0
    for k in range(1,len(ds)):
        if (ds[k]-ds[k-1]).days>7:start=k
    return ds[start:],vs[start:]

def rsi(x,n=14):
    if len(x)<n+1:return np.nan
    d=np.diff(x[-n-1:]);gain=np.maximum(d,0).mean();loss=np.maximum(-d,0).mean()
    return 50. if gain==loss==0 else 100. if loss==0 else 100-100/(1+gain/loss)

def ema(x,n):
    z=float(x[0]);out=[]
    for v in x:z+=2/(n+1)*(v-z);out.append(z)
    return np.array(out)

def feature_row(label,base,series,scenario):
    d=date.fromisoformat(label['decision']);cut=old.feature_cutoff(d,scenario);prev=old.previous_weekday(cut)
    f={};groups={};sources=[]
    def put(name,v,group):f[name]=float(v);groups[name]=group
    hist={}
    for j,n in enumerate(NAMES):
        ds,v=histories(series,n,cut);hist[n]=(ds,v)
        if ds:sources.extend(ds)
        if j<12:
            level,change,age=base[j],base[12+j],base[48+j]
            imp=base[72+j]
        else:
            sd,sv=series[n];a=bisect.bisect_right(sd,cut)-1;b=bisect.bisect_right(sd,prev)-1
            # Additional current levels only authentic on cutoff: no new ffill policy.
            level=sv[a] if a>=0 and sd[a]==cut else np.nan
            previous=sv[b] if b>=0 and sd[b]==prev else np.nan
            change=(level-previous if n=='wti' else math.log(level/previous)) if np.isfinite(level) and np.isfinite(previous) and (n=='wti' or level>0 and previous>0) else np.nan
            age=(d-sd[a]).days if a>=0 else np.nan;imp=0
        put(n+'__level',level,'D1');put(n+'__change',change,'D1');put(n+'__age',age,'D1')
        if j<12:put(n+'__imputed',imp,'D1')
    put('tpm_minus_us2_proxy',f['tpm__level']-f['treasury_2y__level'],'D1')
    put('us10_minus_us2',f['treasury_10y__level']-f['treasury_2y__level'],'D1')
    for n in MOM:
        ds,v=hist[n]
        for w in (5,20):
            ok=len(v)>=w+1 and np.all(v[-w-1:]>0)
            put(n+f'__momentum_{w}',math.log(v[-1]/v[-w-1]) if ok else np.nan,'D2')
            put(n+f'__duration_{w}',(ds[-1]-ds[-w-1]).days if ok else np.nan,'D2')
    ds,v=hist['usdclp'];r=np.diff(np.log(v)) if len(v) else np.array([])
    for w in (5,20):put('usdclp__vol_'+str(w),np.std(r[-w:],ddof=1) if len(r)>=w else np.nan,'D2')
    for lag in (1,2):put('usdclp__lag_'+str(lag),r[-lag-1] if len(r)>lag else np.nan,'D2')
    put('usdclp__persistence5',np.sign(r[-5:]).mean() if len(r)>=5 else np.nan,'D2')
    for w in (5,20):put('usdclp__sma_dist'+str(w),v[-1]/v[-w:].mean()-1 if len(v)>=w else np.nan,'D3')
    for n in ('usdclp','dxy','spx'):put(n+'__rsi14',rsi(hist[n][1]),'D3')
    macd=ema(v,12)-ema(v,26) if len(v)>=35 else np.array([])
    put('usdclp__macd',macd[-1]/v[-1] if len(macd) else np.nan,'D3')
    put('usdclp__macd_hist',(macd-ema(macd,9))[-1]/v[-1] if len(macd) else np.nan,'D3')
    sd=np.std(v[-20:],ddof=1) if len(v)>=20 else np.nan
    put('usdclp__boll_z',(v[-1]-v[-20:].mean())/sd if sd>0 else np.nan,'D3')
    put('usdclp__boll_width',4*sd/v[-20:].mean() if len(v)>=20 else np.nan,'D3')
    sdret=f['usdclp__vol_20'];short=f['usdclp__vol_5']
    put('usdclp__zret20',(r[-1]-r[-20:].mean())/sdret if sdret>0 else np.nan,'D3')
    put('usdclp__vol_ratio',short/sdret if sdret>0 else np.nan,'D3')
    for n in ('dxy','cobre_lme'):
        dd,vv=hist[n];a=dict(zip(ds[1:],r));b=dict(zip(dd[1:],np.diff(np.log(vv)) if len(vv) else []))
        common=sorted(a.keys()&b.keys())[-20:]
        # Match starting as well as ending observation dates to avoid mismatched intervals.
        ap={ds[k]:ds[k-1] for k in range(1,len(ds))};bp={dd[k]:dd[k-1] for k in range(1,len(dd))}
        common=[t for t in common if ap[t]==bp[t]]
        corr=np.nan
        if len(common)==20:
            aa=np.array([a[t] for t in common]);bb=np.array([b[t] for t in common])
            if aa.std()>0 and bb.std()>0:corr=np.corrcoef(aa,bb)[0,1]
        put('usdclp__corr20_'+n,corr,'D3')
    assert all(t<=cut for t in sources) and cut<=d<date.fromisoformat(label['target'])
    vix=f['vix__level'];regime='alto' if vix>30 else 'bajo' if vix<20 else 'medio' if np.isfinite(vix) else 'sin_dato'
    return f,groups,dict(decision=d,cutoff=cut,max_native_source=max(sources) if sources else '',regime=regime,certified_timestamp=False)

def native(data):
 # Exact Fase3 numeric filter, solely removes the historical 2009 lower bound.
 series={}
 for n,t in TICKERS.items():
  pairs=[]
  for d,row in sorted(data.items()):
   if d.weekday()>4:continue
   v=row.get(t+'|PX_LAST')
   if not finite(v):continue
   if n!='wti' and n not in ('tpm','treasury_2y','treasury_10y','ndf_implicito_1m') and v<=0:continue
   pairs.append((d,float(v)))
  series[n]=([d for d,v in pairs],np.array([v for d,v in pairs]))
 return series

def base_row(data,series,d):
 cut=old.feature_cutoff(d,'conservador_fecha');prev=old.previous_weekday(cut);f=defaultdict(list);lin=[]
 for n in old.NAMES:
  got=old.flex.calendar_value(series,n,cut);before=old.flex.calendar_value(series,n,prev)
  v=got[1] if got else np.nan;v0=before[1] if before else np.nan
  last=got[0] if got else old.flex.last_authentic(series,n,cut);older=old.flex.last_authentic(series,n,cut)
  f['level'].append(v);f['change'].append(old.flex.change(n,v,v0) if np.isfinite(v) and np.isfinite(v0) else np.nan)
  f['missing'].append(int(not np.isfinite(v)));f['change_missing'].append(int(not(np.isfinite(v) and np.isfinite(v0))))
  f['age'].append((d-last).days if last else np.nan);f['available_exact'].append(int(bool(got) and got[0]==cut));f['imputed'].append(0);f['interval'].append((cut-older).days if older else np.nan)
  lin.append(dict(decision=d,feature=n,cutoff=cut,source=got[0] if got else '',carried=bool(got and got[0]!=cut)))
 return [v for field in ('level','change','missing','change_missing','age','available_exact','imputed','interval') for v in f[field]],lin

TICKERS={s.name:s.ticker for s in CORE}|EXTRAS
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
