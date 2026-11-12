# Reproducción y alcance de la evidencia

La representación histórica fue contrastada en 3.638 filas × 97 características, con igualdad exacta incluyendo NaN. Las 1.524 posiciones históricas coinciden; diferencia máxima de probabilidades 2,22e-16, tolerancia 1e-12. No hubo decisiones neutrales en ese backtest. Estos resultados describen equivalencia de implementación, no significancia económica.

El ajuste final utiliza 4.105 pares hasta 2026-11-06, sin nueva selección ni recalibración. Dos reproducciones previas obtuvieron bytes idénticos al SHA esperado. La preparación y la inferencia diaria tienen contratos separados. Las 101 pruebas cubren temporalidad, corte fijo, identidad, inferencia sin fit, actualización de snapshot, contabilidad y NO_ORDER.

Con Excel autorizado: reproduce genera modelos históricos, predicciones privadas y tablas; fit-deployment genera el artefacto final y su manifiesto privado. No se requieren caches de investigación. Los agregados compartidos permiten ejecutar el notebook sin Excel ni modelos. La demo y los tests funcionales necesitan el artefacto generado; el fixture de rechazo anual2024 se obtiene de outputs/reproduccion/models/extra_2024.joblib.

Los CSV científicos y económicos se conservan byte por byte respecto de la entrega de origen. Las cifras del notebook se leen de esos mismos CSV. El cambio visual de patrimonio elimina segmentos entre bloques: no cambia cifras ni períodos. Las fuentes de investigación referidas en el anexo son antecedentes opcionales; los ejecutables son autónomos.

Los resúmenes de riesgo y las métricas económicas no describen un puntaje oficial. Disponibilidad point-in-time, revisiones, calendarios históricos y financiación simétrica son limitaciones explícitas. La ejecución real requiere un feed certificado y compatibilidad del sistema de evaluación con la decisión de cierre a cierre.
