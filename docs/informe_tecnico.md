# Estrategia USD/CLP — Optimo Investment

Renato Ortega y Benjamín Mundaca.

La estrategia utiliza un único Extra Trees triclase con97 características D2. La posición se obtiene mediante argmax, sin ensemble ni umbral de confianza. En las1.524 jornadas históricas produjo−1/+1. Las familias predictoras cubren historiaUSD/CLP, dólar global, commodities, monedas emergentes, tasas y riesgo/renta variable.

El backtest2019–2024 usa entrenamiento expansivo desde2010, reajuste anual, selección y calibración temporales y purga known<decision. Accuracy53,35%, log loss0,726980 y Brier0,505391. Frente a Laplace dinámica, DM p=0,313: no se demuestra superioridad robusta. El período se reutilizó en investigaciones; evidencia exploratoria, no confirmación independiente.

Se investigaron modelos lineales, árboles, boosting, SVM, distintas ventanas y representaciones, mecanismos económicos, objetivos de retorno/magnitud, ensembles y políticas selectivas. No se encontró evidencia suficiente para promover un reemplazo. La elección de Extra Trees es una decisión operativa sustentada en un pipeline reproducible, no una prueba de dominancia general. El anexo y la matriz conservan resultados negativos y alternativas con mejoras descriptivas inciertas.

La simulación opera al cierre: predictores hasta la jornada anterior, señal antes de t, rebalanceo de referencia en PX_LAST(t), horizonte al siguiente cierre auténtico elegible. NO_ORDER conserva posición. La implementación real exige compatibilidad del monitor con esta convención.

A1pb por unidad de rotación, el retorno total compuesto histórico estimado es65,87%, frente66,10% de comprarUSD y34,97% de cajaCLP. Volatilidad14,46%, Sharpe sobre caja0,309 y DD−26,77%;461órdenes y920unidades de rotación. CLICP se trata como índice y FEDL01 como tasa porcentual ACT/360; financiación simétrica y costos hipotéticos. Los IC económicos incluyen cero. No es puntaje oficial ni rentabilidad ejecutable certificada.

El modelo operativo se ajustó posteriormente con4.105 pares conocidos hasta 2026-11-06, con parámetros previamente fijados y temperatura1. Las97variables y su orden se conservan. Durante el monitoreo no se entrenan ni recalibran parámetros. **Las métricas anteriores pertenecen al backtest y no al modelo de despliegue.** El ajuste final no constituye evaluación nueva2026.

Los datos y modelos aprendidos permanecen fuera de Git. Persisten limitaciones de disponibilidad point-in-time, calendarios, feed certificado, ejecución real, extremosCLICP estimados y convenciones exactas del evaluador. MIT cubre sólo código propio.
