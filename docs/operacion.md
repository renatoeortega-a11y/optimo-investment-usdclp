> Para uso diario sencillo: [predict](prediccion_diaria.md), con Excel, fecha y posición anterior. Las referencias a registros independientes de este documento corresponden exclusivamente a la ruta estricta opcional. El modo local no requiere aprobaciones individuales y no certifica procedencia.

# Preparación e inferencia

Modelo vigente: Extra Trees D2 E2010, profundidad6,120 árboles, hoja mínima20, max_features=sqrt, semilla20261109, temperatura1. Entrenamiento final:4.105 pares con etiquetas conocidas hasta 2026-11-06. No nueva selección ni recalibración. SHA256 esperado:5f2394a58a1c85bff494fd7e8cb3f58887b6d57f404db92aa9d30ba08a77a052.

Preparar una vez con `python -m itau_entrega fit-deployment --excel data/raw/base_usdclp_actualizada.xlsx --cutoff 2026-11-06 --output artifacts/deployment_final.joblib`. Fuente de preparación fija SHAa198a2357332685b784fddd852dea242f59e90046dedd9709a3429ae9f6134ee. El comando rechaza sobrescrituras, fuentes no autorizadas y otro corte. Conservar el manifiesto privado generado junto al artefacto. Si no coincide el hash, revisar el entorno, no eludir el control.

Ruta estricta opcional: usar `python -m monitor_lab live-signal --snapshot runtime/snapshots/mercado.xlsx --manifest runtime/manifiestos/mercado.json --model artifacts/deployment_final.joblib --decision 2026-11-12 --previous-position 0 --session-confirmed --output outputs/live_signal_PRIVADA.json`. Sustituir fecha y posición real. Nunca ejecutar preparación como parte del job diario.

Requiere hoja datos y campos fuente definidos en contrato_datos.md. El proveedor certifica procedencia, fecha y disponibilidad; un responsable independiente registra la aprobación del manifiesto en runtime/approved_manifests.json. Hash nuevo requiere aprobación nueva. No incluir aprobaciones ni snapshots en Git.

El manifiesto declara source_id, snapshot_sha256, schema_sha256, snapshot_as_of, synthetic=false y daily_feed_certified=true. El registro independiente contiene approvals con payload_sha256, manifest_file_sha256, source_id, schema_sha256, scope=inference_only_2026 y daily_feed_certified=true. Payload SHA: JSON sort_keys=True, separators=(',',':'), ensure_ascii=True, UTF8. Schema SHA: lista de encabezados en orden, JSON ensure_ascii=False, separators=(',',':'), UTF8. Los hashes de archivos corresponden a sus bytes. No inventar ni reutilizar aprobaciones de otro snapshot.

La ruta sólo predice decisiones2026 hasta la fecha corriente en America/Santiago. Descarta datos posteriores al corte antes de decodificar valores. Rechaza estructura inválida, duplicados, calendario desordenado, hash/procedencia no aprobados y fechas futuras declaradas. Snapshot desactualizado o sesión no confirmada producen NO_ORDER. Las máscaras/edades y transformaciones usan historia auténtica; el codificador no se ajusta.

Salida: tres probabilidades, fecha/corte, posición objetivo y transición desde la posición previa. NO_ORDER conserva posición, target_position=null y delta0. Modelo erróneo o datos inválidos impiden una orden. No hay envío automático, evaluación, entrenamiento ni recalibración en live-signal. Extensión fuera2026 requiere revisión del contrato.

Con Excel se reconstruyen modelo y backtest; sin datos se ejecuta notebook de agregados. Tests funcionales y demo requieren modelo privado. El fixture anual2024 se obtiene de reproduce histórico. Feed, aprobación externa, sesión y adaptador de ejecución son configuraciones del laboratorio y no pueden deducirse del Excel.

Las métricas del notebook corresponden al protocolo histórico; no evalúan el ajuste final2026. Carry/costos permanecen separados de inferencia. Todos los artefactos, observaciones y salidas individuales permanecen privados.
