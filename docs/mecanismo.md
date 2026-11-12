# Convención de ejecución

Optimo Investment define una estrategia simulada **al cierre**, sin decisiones intradía ni dólar observado.

1. Para jornada t se forma D2 con fuentes admisibles hasta `previous_weekday(t)`. Los valores posteriores se descartan antes de decodificarlos; el cierre de t no es predictor.
2. La señal se calcula antes del cierre de t con el codificador y Extra Trees congelados. Orden de clases: baja, cero y alza. Argmax original, sin ensemble, nuevos umbrales ni ±3.
3. Entrada/rebalanceo de referencia: `USDCLP Curncy|PX_LAST(t)`. Horizonte: siguiente cierre auténtico elegible s; `r=S(s)/S(t)-1`.
4. Cambio propuesto: `q_nueva-q_previa`; reversión de+1a−1 rota2unidades. La posición previa debe ser la vigente, no reiniciarse cada día.
5. NO_ORDER conserva la exposición previa, con delta0. No representa liquidación. Inputs inválidos provocan rechazo; sin salida válida no debe transmitirse ninguna orden.

El histórico produjo1.524posiciones−1/+1. Un argmax neutral no observado se deriva a revisión/NO_ORDER según la salvaguarda existente. Las ausencias se codifican con los parámetros guardados; no se rellenan nuevos instrumentos ni se inventan feriados. Se requiere confirmación externa de sesión y el sistema rechaza fines de semana.

PX_LAST es referencia de simulación, no garantía de ejecución negociable. La activación requiere compatibilidad del monitor con calendario, horario, precio y posición real. Esto no cambia la elección de cierre a cierre. El programa no transmite órdenes.

El retorno total estimado es `C+q[r+(1+r)U-C]-costos`; caja CLP, financiación y devengoUSD se aplican de forma idéntica a estrategia y benchmarks. La contabilidad es ex post y nunca informa las señales. El libro económico debe usar posiciones efectivamente mantenidas; NO_ORDER no crea una operación.
