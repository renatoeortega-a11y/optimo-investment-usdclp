"""Helper puro de pruebas causales: no lee archivos, evalúa modelos ni ajusta parámetros."""
import numpy as np
def causal_counts(history,observed,decision):
 if any(h['known']>'2024-12-31' for h in history):raise ValueError('Benchmark no admite etiquetas2025 en prior')
 if any(h['known'][:4]!='2026' for h in observed):raise ValueError('La actualización sólo admite etiquetas2026')
 return np.array([sum(h['truth']==k for h in history)+sum(h['truth']==k and h['known']<decision for h in observed) for k in (-1,0,1)],float)
