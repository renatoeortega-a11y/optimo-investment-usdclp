# Predicción diaria: interfaz sencilla y procedencia

## Preparación única

Instalar dependencias y generar `artifacts/deployment_final.joblib` con el Excel histórico y `fit-deployment --cutoff 2026-11-06`. La configuración `config/predict_interface.json` resuelve automáticamente la ruta. El motor exige SHA-256 `5f2394a58a1c85bff494fd7e8cb3f58887b6d57f404db92aa9d30ba08a77a052`; no basta con un archivo de nombre correcto. Árboles, codificador, temperatura, clases y orden de97variables siguen congelados. Actualizar el Excel nunca modifica ese artefacto.

## Uso local en tres pasos

1. Actualizar la hoja `datos` del Excel con campos y fechas del [contrato](contrato_datos.md), conservando la historia. No preparar un JSON ni calcular hashes.
2. Ejecutar `python -m monitor_lab predict --excel data/mercado_actualizado.xlsx --decision 2026-11-12 --previous-position 1`.
3. Leer las probabilidades y `transition`: posición previa, objetivo, delta y acción. Los JSON se guardan automáticamente en `outputs/predict/`; `--csv` genera además CSV. No son órdenes reales ni se actualiza automáticamente la posición vigente.

Fecha y posición siguen siendo obligatorias: hoy no implica sesión operable ni conocemos la cartera real. No se deduce posición desde una señal anterior, porque una propuesta podría no haberse ejecutado. El modo local trata la fecha hábil solicitada como escenario de simulación, **sin certificar sesión ni disponibilidad en tiempo real**. `--session-unconfirmed` solicita NO_ORDER si la sesión se sabe cerrada o no está confirmada. Los fines de semana siempre producen NO_ORDER. No se inventan feriados.

El corte es la jornada de semana anterior a la decisión, igual al motor vigente. Una ausencia en esa fecha no se convierte automáticamente en feriado. Si falta USD/CLP auténtico reciente, se conserva la posición y se explica qué fecha se necesita. Se exige un mínimo de21observaciones auténticas USD/CLP para sus20retornos; las ausencias de otras fuentes mantienen el codificador/NaN originales, con conteo de características ausentes. Este control de suficiencia del envoltorio no cambia D2 ni añade imputaciones.

Se inspeccionan encabezados y fechas sin decodificar valores económicos futuros. Se validan columnas, unicidad, orden, tipos numéricos y hash del archivo durante la lectura. Se calculan automáticamente SHA del Excel, esquema y corte; el JSON registra estos metadatos y el hash del modelo. Filas posteriores al corte no afectan las probabilidades. Repetir una entrada produce el mismo resultado; el identificador depende del resultado y conserva decisiones de validación distintas.

El modo local devuelve `externally_certified=false` y `provenance=user_provided_not_externally_certified`. No crea entradas en ningún registro de aprobaciones ni usa la etiqueta synthetic para eludir controles. Los ejemplos sintéticos son únicamente fixtures de prueba, no origen certificado real.

## Canal certificado opcional

`--mode certified` exige un mecanismo de confianza configurado por el laboratorio. Una carpeta o nombre de archivo no demuestra procedencia. Se admite firma HMAC-SHA256 del proveedor mediante clave compartida custodiada fuera de Git. Requiere que el sistema real del proveedor pueda emitir esa evidencia; no se presume que el feed actual lo haga.

Una vez, el responsable configura `runtime/source_trust.json` con `enabled:true`, `algorithm:"HMAC-SHA256"`, `source_id`, `schema_sha256` y `key_env` (nombre de variable de entorno que contiene una clave secreta de al menos32bytes). No guardar la clave en el JSON o repositorio. El transporte, los permisos del directorio y la custodia/rotación de esa clave son responsabilidades del laboratorio.

En cada actualización **el canal del proveedor**, no el evaluador manualmente, entrega `ARCHIVO.xlsx.signature.json`. Contiene `payload` y `signature`. El payload firmado incluye `source_id`, `snapshot_sha256`, `schema_sha256`, `snapshot_as_of`, `daily_feed_certified:true` y `session_confirmed:true` cuando la sesión está confirmada. Firma: HMAC-SHA256 de JSON canónico con `sort_keys=True`, `separators=(',',':')`, `ensure_ascii=True`, codificadoUTF-8. El esquema se calcula desde la lista ordenada de encabezados con `ensure_ascii=False`, `separators=(',',':')`, UTF-8. La interfaz comprueba bytes, fuente, esquema, vigencia, firma y declaración de sesión. No firma ni certifica por sí misma los archivos locales.

Comando: `python -m monitor_lab predict --excel data/mercado_actualizado.xlsx --decision 2026-11-12 --previous-position 1 --mode certified`. Puede indicarse `--trust-config` para otra configuración local.

La firma verifica procedencia bajo la clave configurada; no prueba por sí sola ausencia de revisiones o disponibilidad histórica point-in-time. Una clave comprometida invalida esa garantía. Si el proveedor no dispone de este contrato, usar modo local para reproducción o mantener la ruta estricta. No presentar un escenario local como operación certificada.

## Ruta estricta conservada

`live-signal` y el registro independiente de aprobaciones siguen disponibles, con sus controles previos. Son apropiados cuando el contrato exige aprobación por snapshot. No se eliminan ni se autogeneran aprobaciones para esa ruta. El modo firmado es una alternativa explícita de canal; local y certificado comparten lector causal, motor D2, modelo, argmax y función de transición. Con datos/estado elegibles equivalentes generan idénticas probabilidades.

## Límites

La ejecución sigue siendo cierre a cierre con PX_LAST como referencia de simulación. El envoltorio no calcula carry, etiquetas o métricas posteriores, no entrena y no envía órdenes. El contrato operativo continúa limitado a2026 y a fechas no posteriores al reloj de Chile. Datos, firmas, claves, logs, artefactos y señales individuales permanecen fuera de Git.
