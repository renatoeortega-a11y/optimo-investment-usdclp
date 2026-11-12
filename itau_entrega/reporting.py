"""Sólo agregados seguros para el notebook compartible; no carga precios ni modelos privados."""
import csv,html,json
from pathlib import Path
import numpy as np
from .data import ROOT
def rows(name):
 with (ROOT/'reports'/name).open(encoding='utf-8') as stream:return list(csv.DictReader(stream))
def table(rs,columns):
 def value(v):
  if v in ('',None):return 'N/D'
  try:return f'{float(v):.6g}'
  except (ValueError,TypeError):return html.escape(str(v))
 return '<table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in columns)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+value(r.get(k))+'</td>' for k in columns)+'</tr>' for r in rs)+'</tbody></table>'
def validation_metrics():
 return [r for r in rows('metricas_modelos.csv') if r['id'] in ('E2010__extra_dir','baseline__laplace_dynamic') and r['axis']=='total' and r['version']=='cal' and r['view']=='three']
def trading():return rows('trading_totales.csv')
def plots():
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(2,2,figsize=(13,8));colors={'E2010_ExtraTrees':'#185a9d','buy':'#e18b25','zero':'#6a737d'}
 curve=rows('curva_bloques.csv')
 for policy,color in colors.items():
  r=[z for z in curve if z['policy']==policy and z['cost_bps']=='1'];vals=np.cumsum([float(z['spot_less_cost_sum']) for z in r]);axes[0,0].plot([0,1,2],np.r_[0,vals]*100,marker='o',label=policy,color=color)
 axes[0,0].set(xticks=[0,1,2],xticklabels=['Inicio','2019–2021','2022–2024'],ylabel='P&L aditivo/nocional (%)',title='Spot menos costo hipotético 1pb; carry no disponible');axes[0,0].legend(fontsize=8)
 metrics=[r for r in trading() if r['cost_bps']=='1'];axes[0,1].bar([r['policy'] for r in metrics],[float(r['max_drawdown_additive'])*100 for r in metrics],color=[colors[r['policy']] for r in metrics]);axes[0,1].set(title='Máximo drawdown agregado: spot menos 1pb',ylabel='P&L/nocional (%)')
 exposure=rows('exposiciones_agregadas.csv');axes[1,0].bar([int(r['position']) for r in exposure],[int(r['days']) for r in exposure],color='#185a9d');axes[1,0].set(title='Exposición de la estrategia — conteos totales',xlabel='Posición',ylabel='Jornadas')
 for policy,color in colors.items():
  rs=[z for z in trading() if z['policy']==policy];axes[1,1].plot([int(z['cost_bps']) for z in rs],[float(z['cost_sum'])*100 for z in rs],marker='o',color=color,label=policy)
 axes[1,1].set(title='Costos hipotéticos por unidad de rotación',xlabel='Costo (pb)',ylabel='Costo total/nocional (%)');axes[1,1].legend(fontsize=8)
 for ax in axes.flat:ax.grid(alpha=.2)
 fig.tight_layout();return fig