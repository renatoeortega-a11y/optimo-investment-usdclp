# Optimo Investment — USD/CLP Quantitative Strategy

**Torneo Data Science en Finanzas: ¿Sube o baja el dólar mañana?** · Banco Itaú y FEN, Universidad de Chile.

Renato Ortega — rortegal@fen.uchile.cl · Benjamín Mundaca — bmundacam@fen.uchile.cl.

## Estrategia

Un clasificador **Extra Trees** estima probabilidades de baja, retorno exactamente cero y alza del USD/CLP. D2 contiene **97 características** de historia cambiaria, dólar global, commodities, monedas emergentes, tasas y riesgo/renta variable. La posición se obtiene mediante argmax; no se combinan modelos ni se aplican umbrales de confianza o apalancamiento. En el backtest hubo únicamente posiciones −1/+1.

La elección responde a una implementación auditada y reproducible y a la ausencia de evidencia suficiente para reemplazarla con las alternativas investigadas. No implica superioridad estadística general. [Informe técnico](docs/informe_tecnico.md) · [Investigación y descartes](docs/investigacion.md).

## Tres etapas distintas

| Etapa | Alcance |
|---|---|
| Backtest 2019–2024 | Entrenamiento expansivo desde 2010, selección y calibración temporales y reajuste anual. 1.524 jornadas externas. |
| Preparación del modelo operativo | 4.105 pares elegibles desde 2010, con etiquetas conocidas hasta **2026-11-06**. Parámetros seleccionados previamente y temperatura 1, sin nueva búsqueda ni recalibración. |
| Monitoreo | Nuevos datos se utilizan exclusivamente como predictores. Árboles, codificador y calibración permanecen congelados. |

Las métricas siguientes pertenecen al **backtest histórico**, no al modelo final ajustado hasta noviembre de 2026.

## Ejecución al cierre

Optimo Investment define una simulación **cierre a cierre**: información admisible hasta la jornada anterior; señal antes del cierre de t; rebalanceo de referencia a `USDCLP Curncy|PX_LAST(t)`; salida al siguiente cierre auténtico elegible s. Retorno spot: `S(s)/S(t) − 1`. El cambio propuesto es `q_nueva − q_previa`. `NO_ORDER` conserva la posición previa.

PX_LAST es una referencia de simulación. La ejecución real requiere compatibilidad con el precio, calendario y horario del monitor. El programa propone posiciones; no envía órdenes. [Mecanismo](docs/mecanismo.md).

## Resultados históricos

| Costo hipotético por unidad de rotación | Estrategia | Comprar USD | Caja CLP |
|---|---:|---:|---:|
| 0 pb | 81,86% | 66,14% | 34,97% |
| 1 pb | 65,87% | 66,10% | 34,97% |
| 5 pb | 14,79% | 65,97% | 34,97% |

Retornos totales compuestos estimados, con carry CLICP/FEDL01. A 1 pb: volatilidad anualizada 14,46%, Sharpe de exceso sobre caja 0,309, máximo drawdown −26,77%, 461 órdenes y rotación de 920 unidades. Accuracy direccional 53,35%; log loss triclase 0,72698. DM frente a Laplace: p=0,313. No se demuestra superioridad predictiva ni económica robusta.

CLICP se utiliza como índice de devengo; FEDL01 como porcentaje anual ACT/360. Se incluye caja CLP sin duplicar su remuneración. Hay extremos CLICP estimados y supuestos de financiación simétrica. Los costos son escenarios hipotéticos, **no puntaje neto oficial**. [Carry y costos](docs/carry_costos.md) · [Notebook](entrega.ipynb).

## Instalación y datos

Se requiere acceso al repositorio privado y al Excel oficial por canal autorizado. Referencia comprobada: Windows, Python 3.12.10. No se redistribuyen datos Bloomberg ni modelos aprendidos.

```powershell
git clone https://github.com/renatoeortega-a11y/optimo-investment-usdclp.git
cd optimo-investment-usdclp
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Colocar el Excel original en `data/raw/base_usdclp_actualizada.xlsx`. Su SHA-256 es `a198a2357332685b784fddd852dea242f59e90046dedd9709a3429ae9f6134ee`.

## Preparación inicial: una sola vez

```powershell
.\.venv\Scripts\python.exe -B -m itau_entrega fit-deployment --excel data/raw/base_usdclp_actualizada.xlsx --cutoff 2026-11-06 --output artifacts/deployment_final.joblib
Get-FileHash artifacts/deployment_final.joblib -Algorithm SHA256
```

Hash esperado: `5f2394a58a1c85bff494fd7e8cb3f58887b6d57f404db92aa9d30ba08a77a052`. El corte es fijo; el comando rechaza otros cortes y sobrescrituras. Conservar privadamente el artefacto y su manifiesto. Si el hash difiere, detener la activación y revisar el entorno.

## Inferencia diaria: sin entrenamiento

El laboratorio proporciona el snapshot actualizado, su manifiesto y la aprobación externa de procedencia y disponibilidad. [Contrato de datos](docs/contrato_datos.md) · [Operación](docs/operacion.md).

```powershell
.\.venv\Scripts\python.exe -B -m monitor_lab live-signal --snapshot runtime/snapshots/mercado.xlsx --manifest runtime/manifiestos/mercado.json --model artifacts/deployment_final.joblib --decision 2026-11-12 --previous-position 0 --session-confirmed --output outputs/live_signal_PRIVADA.json
```

Actualizar fecha, posición real previa, snapshot y aprobación cada jornada. La salida contiene probabilidades, posición y rebalanceo propuesto. Ausencias admitidas siguen el codificador congelado; columnas estructurales ausentes o contratos inválidos producen rechazo. Sin sesión confirmada o con snapshot desactualizado, `NO_ORDER` conserva la exposición.

## Backtest, notebook y pruebas

```powershell
.\.venv\Scripts\python.exe -B -m itau_entrega reproduce --excel data/raw/base_usdclp_actualizada.xlsx --output outputs/reproduccion
.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute entrega.ipynb --output entrega_ejecutada.ipynb --output-dir outputs
Copy-Item outputs/reproduccion/models/extra_2024.joblib artifacts/annual_2024_validation_only.joblib
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m monitor_lab synthetic-demo
```

`reproduce` reajusta únicamente los modelos históricos del protocolo 2019–2024; no cambia el artefacto de despliegue. Los 101 tests completos requieren el modelo definitivo y el fixture anual 2024 indicado. Notebook de agregados: funciona sin Excel ni modelos. La demo es exclusivamente sintética y requiere el artefacto preparado.

## Estructura y límites

Código en `itau_entrega/` y `monitor_lab/`; parámetros en `config/`; tests en `tests/`; tablas agregadas del notebook en `reports/`; documentación en `docs/`. Excel, artefactos, snapshots y salidas individuales permanecen fuera de Git.

2019–2024 fue reutilizado en investigación: evidencia exploratoria, no confirmatoria. El ajuste final no constituye una nueva evaluación independiente. Faltan certificación del feed, aprobación de snapshots, calendario y compatibilidad operativa del monitor. MIT cubre únicamente código propio, sin otorgar derechos sobre Bloomberg ni materiales de terceros.
