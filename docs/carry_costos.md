# Carry, caja, costos e incertidumbre

No cambia el modelo, las 97 características, probabilidades, calibración ni posiciones. Este documento registra una estimación económica fundamentada; no reproduce un evaluador oficial no disponible.

## Fuentes y tiempo

Única fuente numérica: Excel oficial con SHA-256 obligatorio, valores hasta 2024-12-31. `CLICP Index|PX_LAST` es nivel del Índice Cámara Promedio, no tasa; `FEDL01 Index|PX_LAST` es tasa efectiva overnight USD en % anual. Su publicación es posterior a su fecha económica. Ninguna se usa para formar señales ni elegir modelos.

Por intervalo observado [t,s), C=CLICP(s)/CLICP(t)-1: devengo CLP realizado, sin volver a multiplicarlo por días ni sumar TPM. El cálculo estricto exige extremos positivos auténticos y falla si faltan. El cociente incorpora días calendario, fines de semana y feriados. Se conservan variaciones negativas de fuente, sin corregirlas silenciosamente.

**Ajuste contable de cobertura, registrado antes de obtener métricas:** el cálculo estricto falló por extremos CLICP ausentes. No se eliminan jornadas ni se asigna interés cero. En la versión estimada se requiere `--allow-clp-interpolation`: si un extremo d falta, se toma I(d)=I(a)*(I(b)/I(a))^((d-a)/(b-a)) entre observaciones auténticas a<d<b, separadas como máximo siete días calendario y ambas hasta 2024. No se extrapola. Esta asignación uniforme del devengo logarítmico dentro de una brecha es una aproximación ex post, no una observación Bloomberg ni disponibilidad ex ante. No modifica el Excel, D2, la política de imputación de predictores ni las señales. Su efecto en carry cuando cambia q dentro de una brecha es una fuente de incertidumbre adicional. El cálculo estricto rechaza extremos ausentes; la aproximación requiere una opción explícita. `reproduce` ejecuta esta versión estimada declarada; el comando `carry` sin la opción conserva el control estricto.

Para USD se recorre cada día calendario d de [t,s), usando el último FEDL01 de fecha económica <=d; U=producto(1+FEDL01(d)/100/360)-1. Fines de semana/ausencias usan la última observación anterior como aproximación explícita. No se usa la tasa de s ni se retropropagan publicaciones. Más de siete días de antigüedad falla. Base ACT/360 y capitalización diaria son supuestos de esta estimación, no parámetros oficiales confirmados. Se registra cobertura y antigüedad sin publicar tasas individuales. Es contabilidad realizada ex post: FEDL01 de t no era necesariamente conocido al decidir en t. No se reutiliza esa información en la señal. CLICP(s) también es ex post.

Documentación primaria: [reglamento ICP de CBF, anexo 5.1](https://cbf.cl/wp-content/uploads/2019/12/CBF17041s-Reglamento-ICP-y-ICP-Real.pdf), [EFFR de New York Fed](https://www.newyorkfed.org/markets/reference-rates/effr.html). Sólo se consultan definiciones; no se descargan series numéricas externas. La metodología histórica de EFFR cambió; no se reconstruyen vintages ni se certifica que FEDL01 sea tasa negociable por el equipo.

## Capital y financiación

Capital inicial W=1 CLP normalizado. Al inicio de cada intervalo q unidades de exposición USD por unidad de capital, q pertenece a -1,0,+1. La exposición no cambia por los escenarios de costos.

Con r=S(s)/S(t)-1:

- Spot: q*r.
- Caja base: C.
- Financiación CLP de la exposición: -q*C.
- Devengo USD convertido a CLP: q*(1+r)*U.
- Carry diferencial: q*((1+r)*U-C).
- Costo hipotético: c/10000 * |q-q_previa|, añadiendo cierre terminal |q_final|.
- Exceso sobre caja por intervalo: X=q*r+q*((1+r)*U-C)-costo.
- Retorno total sobre capital: R=C+X=(1-q)*C+q*((1+r)*(1+U)-1)-costo.

Así q=0 gana C; q=+1 gana el activo USD con su interés, sin cobrar además caja CLP; q=-1 mantiene dos unidades de caja CLP y financia una unidad USD. Se suponen tasas simétricas de inversión/financiación, sin spreads de préstamo, margen, haircuts, deslizamiento ni impacto. La componente cruzada r*U se conserva. Es una cartera sintética, no promesa de financiación real.

Patrimonio reinvertido W(s)=W(t)*(1+R). Neto acumulado=producto(1+R)-1. Las sumas spot/carry/costos sobre nocional fijo se muestran sólo como descomposición aditiva, no como contribuciones sumables al retorno compuesto. Se informa por separado producto(1+X)-1 (exceso reinvertido sintético) y riqueza relativa W/W_caja-1; no se confunden. La rotación/costo se mantiene en cambios de q objetivo para preservar la convención histórica; no incluye negociación monetaria adicional para redimensionar una posición constante al variar el patrimonio, relevante sobre todo en cortos. No se afirma que el costo simulado sea el costo completo de replicación.

Si hay huecos entre intervalos evaluados se detiene el cálculo: no se inventa exposición ni devengo en jornadas fuera del soporte. Costos 0/1/5 pb por unidad de cambio de exposición, imputados al intervalo de decisión; salida final al último intervalo. La rotación se define en unidades de exposición objetivo, no en órdenes USD ni en rebalanceo monetario continuo.

## Métricas y comparación

Mismas jornadas para estrategia, comprar +1 y caja q=0. Comprar siempre y exposición constante +1 son una única referencia. Volatilidad: desviación de R por intervalo por sqrt(252), etiquetada como convención de sesiones (intervalos con distinta duración). Sharpe: media de X / sd(X) * sqrt(252), referencia caja, no tasa libre de riesgo cero. Drawdown sobre patrimonio compuesto. CAGR descriptivo usando días naturales efectivamente cubiertos/365, no una suma anualizada. Hit rate económico: X>0 entre intervalos expuestos; hit rate total R>0 por separado. Para referencias se suprimen tasas de acierto que puedan revelar clases raras mediante cruces con publicaciones anteriores.

Bootstrap circular pareado sobre diferencias de X, bloques de diez observaciones, 1999 réplicas, semilla 20261112; IC95% de diferencia media por intervalo y p bilateral centrado. Holm para estrategia frente a comprar/caja en tres costos: familia de seis contrastes. No es un IC del retorno compuesto ni elimina selección acumulada. No se selecciona costo, modelo o política mediante estos resultados.

Publicación: totales n>=100 y curva de patrimonio sólo en dos bloques grandes 2019–2021/2022–2024. Se guardan cálculos por intervalo únicamente en outputs privados. Se conserva el soporte común y las supresiones previas; no se publican curvas diarias reconstruibles.


## Número exacto y sensibilidad de extremos CLICP

En el soporte principal de 1.524 intervalos consecutivos hay **1.525 extremos únicos**. **30 extremos únicos** no tienen nivel CLICP auténtico y se estiman; aparecen **60 veces** como extremo inicial/final y afectan **54 intervalos**. No son 60 fechas diferentes. Se publica este conteo global de disponibilidad a petición expresa; no se publican fechas, valores ni métricas del subgrupo de54. Todas las métricas de sensibilidad usan las mismas1.524 jornadas, probabilidades y posiciones.

Se conserva `log_linear` como escenario principal. Dos sensibilidades desplazan mecánicamente el devengo dentro de cada brecha: `previous_native` usa en el extremo faltante el índice auténtico anterior; `next_native` usa el posterior. Ambos sólo entre extremos auténticos separados <=7días y hasta2024, sin extrapolar. Son escenarios contables ex post de asignación temporal, no nuevas cotizaciones, pronósticos, reglas de señal ni cotas matemáticas universales del error. No se selecciona el escenario más rentable. USD, costos, muestra y estrategia permanecen fijos.

| Método, costo1pb | Retorno compuesto estrategia | Diferencia frente principal (puntos porcentuales) | Sharpe exceso sobre caja | DD compuesto |
|---|---:|---:|---:|---:|
| log_linear | 65.873273% | +0.000000 | 0.308601 | -26.768812% |
| previous_native | 67.152371% | +1.279098 | 0.317417 | -26.775832% |
| next_native | 65.351333% | -0.521939 | 0.304920 | -26.775983% |

Las27filas de reports/carry_sensibilidad.csv cubren3métodos×3políticas×3costos. Comprar y caja no cambian su patrimonio final en esta sensibilidad: USD no depende de C y la caja telescopa entre extremos auténticos globales. Las diferencias de estrategia son incertidumbre de asignación temporal, no evidencia de alfa. La dependencia de esta aproximación es material respecto de la pequeña diferencia frente a comprar a1pb.



## Alcance

Estas cifras pertenecen al backtest 2019–2024. El modelo operativo usa el corte fijo2026-11-06 y no hereda esas métricas como evaluación propia. La inferencia no calcula etiquetas ni contabilidad futura. Véase [mecanismo](mecanismo.md).
