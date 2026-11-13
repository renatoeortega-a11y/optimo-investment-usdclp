# Contrato diario de predictores — Optimo Investment

Archivo Excel versionado, hoja datos, fecha en primera columna y campos Ticker|PX_LAST. Debe incluir historia acumulada suficiente para90observaciones auténticas por fuente, anclas anteriores para edades y continuidad temporal. Una fila aislada no reconstruye D2. Se mantienen snapshots originales sin sobrescribir ni fusionar correcciones silenciosamente; no se descargan datos externos.

| Ticker exacto | Campo | Unidad/convención |
|---|---|---|
| USDCLP Curncy | PX_LAST | CLP por USD |
| DXY Curncy | PX_LAST | nivel índice dólar |
| LMCADS03 Comdty | PX_LAST | USD por tonelada cobre LME |
| XAU Curncy | PX_LAST | USD por onza troy |
| USDBRL Curncy | PX_LAST | BRL por USD |
| USDMXN Curncy | PX_LAST | MXN por USD |
| SPX Index | PX_LAST | puntos índice |
| VIX Index | PX_LAST | porcentaje de volatilidad |
| USGG2YR Index | PX_LAST | porcentaje anual, Treasury2Y |
| USGG10YR Index | PX_LAST | porcentaje anual, Treasury10Y |
| CHOVCHOV Index | PX_LAST | porcentaje anual, TPM Chile |
| CHNI1M Curncy | PX_LAST | porcentaje anual, tasa implícita NDF chileno; no China |
| USDCLPV1M Curncy | PX_LAST | porcentaje anual, volatilidad FX1M |
| BCOM Index | PX_LAST | nivel índice commodities |
| CO1 Comdty | PX_LAST | USD por barril, Brent |
| CL1 Comdty | PX_LAST | USD por barril, WTI; manejo histórico de niveles negativos preservado |
| MOVE Index | PX_LAST | nivel índice de volatilidad de tasas |
| EURUSD Curncy | PX_LAST | USD por EUR |


Valores ausentes en columnas presentes siguen NaN/máscaras; no rellenar series antes de su existencia ni inventar feriados. Columnas estructurales ausentes o calendario inválido rechazan el snapshot. No confundir CHNI con China.

En la ruta estricta opcional, el proveedor entrega manifiesto source_id, snapshot_sha256, schema_sha256, snapshot_as_of, synthetic=false, daily_feed_certified=true y evidencia de procedencia/disponibilidad. Un control independiente autoriza los hashes y scope=inference_only_2026 en runtime/approved_manifests.json; ver operacion.md. El servicio no confía sólo en la autodeclaración. Cada snapshot nuevo cambia su hash; nunca se impone el hash del Excel histórico a un feed diario.

Para decidir t se usa únicamente información hasta previous_weekday(t). El laboratorio debe certificar que llegó antes del instante de decisión. Se necesita posición previa vigente y confirmación de sesión, no una sesión inferida de precios futuros. Hora, precio negociable, calendario y manejo de revisiones deben acordarse con el monitor.

Para contabilidad posterior se requieren precios de ejecución/salida y CLICP/FEDL01 con convenciones aprobadas; no entran a esta ruta de inferencia. La caja y el carry se contabilizan según carry_costos.md. No se envían etiquetas, predicciones ni rendimientos diarios a GitHub. Todos los snapshots, manifiestos de control, modelos, logs y señales quedan privados en rutas ignoradas.

Para uso local, predict inspecciona el Excel y genera esos metadatos automáticamente, sin aprobación externa ni certificación de origen. El canal certificado puede usar firmas automatizadas según [predicción diaria](prediccion_diaria.md). No se modifican los campos, unidades, calendario o corte de información.
