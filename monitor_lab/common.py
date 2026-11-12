"""Contrato de publicaciÃ³n: sÃ³lo inferencia; no depende de registros de evaluaciÃ³n."""
import hashlib,json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
CONFIG_PATH=ROOT/'config/monitor_operativo.json'
EXPECTED_CONFIG_SHA256='8133e2bd85ed3c36e42829816c38e0ae0423160992607ab3986cb43ef5c5f475'
CONFIG=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def operational_today():return datetime.now(ZoneInfo(CONFIG['clock_timezone'])).date()
def verify_registration():
 # Nombre conservado para compatibilidad de tests; verifica contrato del motor,
 # no abre logs, manifiestos o protocolos del estudio2026.
 if sha(CONFIG_PATH)!=EXPECTED_CONFIG_SHA256:raise ValueError('Contrato del motor alterado; requiere revisiÃ³n de versiÃ³n')
 if sha(ROOT/'config/features.json')!=CONFIG['feature_order_sha256']:raise ValueError('Orden D2 alterado')
 return dict(model_sha256=CONFIG['frozen_model_sha256'],features_sha256=CONFIG['feature_order_sha256'],contract_sha256=EXPECTED_CONFIG_SHA256,scope='inference_only_2026')
