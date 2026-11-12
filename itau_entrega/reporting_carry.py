"""Lectura de agregados compartibles: nunca abre Excel ni predicciones."""
from .reporting import rows,table,validation_metrics
import numpy as np

def plots():
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(2,2,figsize=(14,9));colors={'ExtraTrees_E2010':'#2e86de','buy':'#e67e22','cash_zero':'#839192'}
 for policy,color in colors.items():
  rs=[r for r in rows('carry_curva_bloques.csv') if r['policy']==policy and r['cost_bps']=='1']
  axes[0,0].plot([0,1,2],[1]+[float(r['wealth']) for r in rs],marker='o',linestyle='None',label={'ExtraTrees_E2010':'Estrategia','buy':'Comprar USD','cash_zero':'Caja CLP'}[policy],color=color)
 axes[0,0].set(title='Patrimonio al cierre de cada bloque, costo 1 pb',xticks=[0,1,2],xticklabels=['Inicial','2019–2021','2022–2024'],ylabel='Capital inicial = 1');axes[0,0].legend(fontsize=8)
 rs=[r for r in rows('carry_totales.csv') if r['cost_bps']=='1']
 axes[0,1].bar([{'ExtraTrees_E2010':'Estrategia','buy':'Comprar USD','cash_zero':'Caja CLP'}[r['policy']] for r in rs],[100*float(r['max_drawdown']) for r in rs],color=list(colors.values()));axes[0,1].set(title='Máximo drawdown compuesto, agregado',ylabel='% de patrimonio')
 es=rows('exposiciones_agregadas.csv');axes[1,0].bar([int(r['position']) for r in es],[int(r['days']) for r in es],color='#2e86de');axes[1,0].set(title='Posiciones originales, sin cambios',xlabel='Posición',ylabel='Jornadas',xticks=[-1,0,1])
 for policy,color in colors.items():
  rs=[r for r in rows('carry_totales.csv') if r['policy']==policy];axes[1,1].plot([int(r['cost_bps']) for r in rs],[100*float(r['net_compounded']) for r in rs],marker='o',label={'ExtraTrees_E2010':'Estrategia','buy':'Comprar USD','cash_zero':'Caja CLP'}[policy],color=color)
 axes[1,1].set(title='Retorno total estimado y sensibilidad a costos',xlabel='Costo hipotético (pb/unidad de rotación)',ylabel='Retorno compuesto (%)');axes[1,1].legend(fontsize=8)
 for ax in axes.flat:ax.grid(alpha=.2)
 fig.suptitle('Carry CLICP/FEDL01 estimado — estimación propia; puntos agregados, sin trayectoria diaria',fontsize=12);fig.tight_layout();return fig
