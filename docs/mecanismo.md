# Convención de ejecución

Optimo Investment define una estrategia simulada **al cierre**, sin decisiones intradía ni dólar observado.

1. Para jornada t se forma D2 con fuentes admisibles hasta `previous_weekday(t)`. Los valores posteriores se descartan antes de decodificarlos; el cierre de t no es predictor.
2. La señal se calcula antes del cierre de t con el codificador y Extra Trees congelados. Orden de clases: baja, cero y alza. Argmax original, sin ensemble, nuevos umbrales ni ±3.
3. Entrada/rebalanceo de referencia: `USDCLP Curncy|PX_LAST(t)`. Horizonte: siguiente cierre auténtico elegible s; `r=S(s)/S(t)-1`.
4. Cambio propuesto: `q_nueva-q_previa`; reversión de+1a−1 rota2unidades. La posición previa debe ser la vigente, no reiniciarse cada día.
5. NO_ORDER conserva la exposición previa, con delta0. No representa liquidación. Inputs inválidos provocan rechazo; sin salida válida no debe transmitirse ninguna orden.

El histórico produjo 1.524 posiciones −1/+1. La política triclase admite también una posición objetivo 0 cuando gana esa clase por argmax: pasar de −1/+1 a 0 cierra la exposición USD y permanece en CLP; de 0 a 0 mantiene caja. Una posición válida 0 no es NO_ORDER. NO_ORDER se reserva para los bloqueos operativos y de datos. Las ausencias se codifican con los parámetros guardados; no se rellenan nuevos instrumentos ni se inventan feriados. Se requiere confirmación externa de sesión y el sistema rechaza fines de semana.

PX_LAST es referencia de simulación, no garantía de ejecución negociable. La activación requiere compatibilidad del monitor con calendario, horario, precio y posición real. Esto no cambia la elección de cierre a cierre. El programa no transmite órdenes.

El retorno total estimado es `C+q[r+(1+r)U-C]-costos`; caja CLP, financiación y devengoUSD se aplican de forma idéntica a estrategia y benchmarks. La contabilidad es ex post y nunca informa las señales. El libro económico debe usar posiciones efectivamente mantenidas; NO_ORDER no crea una operación.


## Referencias y contrastes de las bases

Las bases, página 2 (paso 2 y sección 4), permiten posición cero y la definen como permanecer en pesos ganando la tasa local. Nombran comprar siempre, no operar nunca y exposición constante uno. Bajo esta implementación, comprar USD y mantener q=+1 son económicamente equivalentes: mismo nocional proporcional, financiación USD/CLP, entrada y liquidación terminal y costos sólo por cambios de posición. No se suponen cierres/reaperturas diarios adicionales no definidos por las bases. Ambas etiquetas corresponden al benchmark buy, no a dos pruebas independientes. No operar corresponde a cash_zero, con q=0 y remuneración CLICP; no tiene retorno total cero. Las bases no definen una tercera estrategia distinta en ese pasaje. El esqueleto/evaluador oficial podría precisar otras convenciones; no se inventa una tercera serie.

El test publicado en reports/diebold_mariano.csv compara calidad probabilística triclase con Laplace dinámica (p=0,313), no rentabilidad contra caja. Los intervalos económicos de reports/carry_bootstrap.csv comparan las dos referencias económicas distintas en costos 0/1/5 pb, con bootstrap pareado por bloques y Holm. Todos incluyen cero. Estos contrastes están ejecutados y publicados, sin evidencia de superioridad robusta; no se afirma que un contraste no significativo no se haya realizado ni que el evaluador oficial esté replicado exactamente.
