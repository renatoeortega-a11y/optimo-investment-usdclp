# Anexo metodológico y registro de descartes

Esta entrega no oculta el ensayo y error ni convierte el mejor resultado observado en evidencia independiente. El código ejecutable no importa las fases de investigación; sus identificadores se conservan como antecedentes de linaje. Las tablas agregadas incluidas permiten examinar la evidencia sin acceder al repositorio de investigación. No se incluyen PDF de terceros ni tablas individuales.

| Línea | Qué se investigó | Conclusión para la entrega |
|---|---|---|
| Fase3 revision2 | D1/D2/D3, lineales, árboles, SVM, boosting, PCA | Sin ventaja robusta; primera revisión retirada por frontera temporal; conservar revisión corregida |
| Fase4A revision1 | NDF chileno, swaps–Treasury, cobre/EM, estrés e interacciones | Sin incremento robusto; no confundir CHNI con China ni spreads con carry |
| Fases5/5B | Retorno, magnitud, riesgo; benchmarks congelados y dinámicos | Ventaja inicial de magnitud no se mantuvo ante referencias dinámicas; no aporta dirección automática |
| Fase5C | Expanding frente rolling3/5 y ablations por familias | Rolling no demostró superioridad; quitar tasas ayudó magnitud, no prueba para dirección |
| Fase5D-A/B | Historia anterior a2010; E2005/R9/R14 | Más historia no mejoró robustamente dirección; magnitud con Holm0,108 |
| V0–V4 | Quitar tasas/niveles/EM o sustituir por spreads | No justifica cambiar D2 |
| Fase6 |12combinaciones Cat/LGBM/XGB/HistGB/SVM/ElasticNet con D2/V2 | Ningún modelo superó robustamente ET y Laplace; Cat finalmente sí ejecutó, a diferencia del bloqueo histórico de Fase3 |
| Fase4B/7 | Selectividad, consenso, riesgo y abstención; A/B/C con soporte común | Ninguna continuidad robusta; no habilitó±3 |
| Piloto científico | Soberano×estrés, shock residual×EM, cobre negativo×VIX | Soberano excluido por soporte; otras dos interacciones sin mejora robusta |
| Fase8 | ElasticNet con interacciones, desequilibrio CLP y Huber r/sigma | Ningún tratamiento mejoró su control; normalización perjudicó esta especificación |
| Fase9 H9.1 | Etiqueta de movimiento relevante0,5sigma20 | No superó climatología; no comparar LL con objetivo original |
| Pooling fijo |75%ET+25%Cat frente a75%ET+25%Laplace | Ligera mejora probabilística descriptiva, sin ventaja ajustada; economía peor; mantener ET |

Linaje documental del proyecto de investigación: Fase5C (`docs/analisis_fase5c.md`), Fase5D-B (`docs/analisis_fase5d_b.md`) y Fase6 (`docs/analisis_fase6.md`). Estos nombres identifican los informes de origen, no archivos necesarios de esta entrega. La evidencia pública correspondiente está en [comparaciones de metodología](../reports/comparaciones_metodologia.csv), [ventanas](../reports/investigacion_ventanas.csv) y [Fase6](../reports/investigacion_fase6.csv). Los resultados disponibles de las fases posteriores, pilotos, H9.1 y pooling se conservan en las tablas de este repositorio, sin depender de informes externos.

La corrección de multiplicidad y bootstrap por bloques reducen discrecionalidad estadística, pero no eliminan el sesgo acumulado de reutilizar2019–2024. No se construyó un test nuevo abriendo2025–2026 para confirmar al seleccionado.


## Evidencia cuantitativa y justificación de la selección

Para revisión autónoma, [matriz_experimentos.csv](../reports/matriz_experimentos.csv) contiene las métricas globales disponibles de Fase6, Fase8, H9.1 y pooling, sin matrices de confusión ni datos por jornada. reports/investigacion_fase6.csv conserva validación interna, contrastes ET/Laplace e intervalos; investigacion_ventanas.csv contiene contrastes expanding/rolling; investigacion_retorno.csv e investigacion_magnitud.csv conservan el objetivo separado de Fase5. Los nombres source son referencias de procedencia histórica, no dependencias necesarias del ejecutable. Los resultados históricos económicos son SPOT, sin atribuirles el nuevo carry de esta evaluación.

| Investigación | Propósito y evidencia | Motivo de no reemplazo |
|---|---|---|
| Logística/ElasticNet, RF, Extra Trees, D1/D2/D3/PCA (Fase3 revision2) | Comparar lineales, árboles y representación causal; primera versión retirada por frontera temporal | No hay ganador confirmatorio; no presentar revisión1 inválida |
| Fase6: CatBoost, XGBoost, LightGBM, HistGB, SVC-RBF y logística ElasticNet, D2/V2 | 12 combinaciones; selección temporal por LL; ver tabla con todas las métricas e IC | Ninguna ventaja ajustada robusta ET/Laplace; CatBoost sí ejecutó aquí pese al bloqueo previo de Fase3 |
| Ventanas Fase5C | ET dirección LL expanding0,72698 / rolling5 0,73145 / rolling3 0,73239 | No prueba universal de superioridad expanding; preferir referencia estable auditada |
| Fase5D-B | E2005 vs E2010 y R14/R9; ET magnitud MSE −2,465%, Holm0,108 | Más historia no confirma mejor dirección; concentración2022–2023, no reemplazo automático |
| Familias D2 / V0–V4 / spreads | 97 columnas, tasas18, USDCLP12, dólar11, commodities21, EM16, riesgo19. Eliminar tasas ayudó magnitud rolling5 (MSE−2,42%, Holm0,015) | No trasladar conclusión de magnitud a dirección; sustituir/agregar spreads no dio mejora robusta |
| Fase5/5B: retorno y magnitud | RF retorno R²OOS cercano0,205% en Fase5, no robusto. ET magnitud inicialmente mejoró MSE7,88% sobre media expansiva y5% sobre media60 | Comparación inicial con benchmarks congelados; ventaja no persistió al actualizar referencias; magnitud no aporta signo automáticamente |
| Riesgo y cuantiles | EWMA, vol60, GARCH, residuos cuadrados y cuantiles; riesgo no es dirección | Mejoras de riesgo no acreditaron política neta superior; sin promover±3 |
| Fase4A y piloto | NDF chileno, curvas swap/Treasury, cobre/EM y estrés. Soberano escaso no sustituido por swaps | Interacciones residuales/EM y cobre/VIX no mejoraron robustamente; soporte limita soberano |
| Fase8 A/B/C | A interacciones regularizadas deltaLL+0,00100579; B residuos deltaLL+0,00012140; Holm0,867 ambos. C normalizado aumenta MSE16,99%, p0,0015 | Tratamientos no mejoran sus controles; C se mide en escala original, no comparar objetivos distintos |
| H9.1 | Banda fija0,5sigma20; LL nuevo1,090016 vs climatología1,088961, p0,5325 | El objetivo cambió; no comparar LL directamente con0,72698; no evidencia de anticipación útil de eventos |
| Pooling fijo | P0 LL0,72698044; 75%ET+25%Cat LL0,72662090; 75%ET+25%Laplace LL0,72699013; Holm1 | Mejora descriptiva incierta, no Cat incremental robusto; a1pb spot P1=0,24374 frente P0=0,33485 |
| Fase7 A/B/C, soporte1014 (2021–24) | A spot−1pb0,200821; B0,149601; C0,093128. B−A y C−A Holm0,839 | Menos exposición/rotación no compensó oportunidades perdidas; no cambiar argmax ni habilitar±3 |

Fase7 B usó mediana causal de confianza con al menos300 OOS anteriores; C esperanza aproximada previamente autorizada, no probabilidad convertida arbitrariamente en magnitud. Comparar sólo soporte común, no contra A completo2019–24. Las filas de Fase7 publicadas son totales de soporte grande; se omiten subestratos raros.

La elección de Extra Trees no resulta de una prueba de que domine a todas las alternativas. Es una decisión operativa/provisional, apoyada en representación y pipeline auditados, funcionamiento repetido y ausencia de evidencia suficiente para promover los tratamientos registrados. Otros modelos pueden tener mejores pérdidas descriptivas. La reutilización de2019–2024 y multiplicidad impiden convertir el mejor resultado retrospectivo en estimación imparcial. No se usó el holdout para resolver esta incertidumbre. El carry estimado sólo se añade al modelo elegido y benchmarks: no es un nuevo ranking retrospectivo de estrategias.


## Preparación operativa

El ajuste final utiliza 4.105 pares con etiquetas conocidas hasta 2026-11-06. No es una evaluación adicional: las métricas históricas pertenecen al protocolo 2019–2024. No se utilizaron resultados de la evaluación experimental de 2026 para modificar parámetros.
