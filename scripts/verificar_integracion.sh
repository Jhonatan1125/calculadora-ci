#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${COMPOSE_PROJECT_NAME:-calculadora-ci-test}"
NETWORK_NAME="${PROJECT_NAME}_red-calculadora"

echo "=== Limpiando ejecuciones previas del proyecto ${PROJECT_NAME} ==="
docker compose -p "${PROJECT_NAME}" down -v --remove-orphans || true

echo "=== Levantando calculadora-api e historial-api con Docker Compose ==="
docker compose -p "${PROJECT_NAME}" up -d
docker compose -p "${PROJECT_NAME}" ps

echo "=== Verificando comunicacion entre contenedores en la red ${NETWORK_NAME} ==="
docker run --rm --network "${NETWORK_NAME}" python:3.13.2-slim python - <<'PY'
import json
import sys
import time
import urllib.error
import urllib.request


def request_json(url, method="GET", payload=None, headers=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


# 1. Esperar a que ambos servicios respondan /health por nombre de servicio DNS
ready = False
for intento in range(1, 26):
    try:
        s1, h1 = request_json("http://calculadora-api:8000/health")
        s2, h2 = request_json("http://historial-api:5001/health")
        if s1 == 200 and s2 == 200:
            print(f"[OK] Healthchecks listos en intento {intento}:")
            print("  calculadora-api:", json.dumps(h1))
            print("  historial-api:  ", json.dumps(h2))
            ready = True
            break
    except Exception as exc:
        print(f"Esperando servicios (intento {intento}/25): {exc}")
        time.sleep(1)

if not ready:
    print("[ERROR] Los contenedores no respondieron /health a tiempo.", file=sys.stderr)
    sys.exit(1)

# 2. Validar proteccion por API Key inyectada desde Jenkins Credentials
try:
    request_json("http://historial-api:5001/registros")
    print("[ERROR] historial-api permitio acceso sin X-API-Key.", file=sys.stderr)
    sys.exit(1)
except urllib.error.HTTPError as err:
    if err.code != 401:
        print(f"[ERROR] Se esperaba HTTP 401 sin API Key y llego HTTP {err.code}.", file=sys.stderr)
        sys.exit(1)
    print("[OK] Seguridad verificada: historial-api rechazo peticion sin X-API-Key (HTTP 401).")

# 3. IDA: calcular en calculadora-api y guardar en historial-api via http://historial-api:5001
status_ida, resp_ida = request_json(
    "http://calculadora-api:8000/calcular",
    method="POST",
    payload={"operacion": "sumar", "a": 15, "b": 25},
)
print("[IDA] Respuesta POST /calcular:", json.dumps(resp_ida, ensure_ascii=False))
assert status_ida == 201, f"HTTP esperado 201, recibido {status_ida}"
assert resp_ida.get("resultado") == 40.0, f"Resultado inesperado: {resp_ida}"
assert resp_ida.get("guardado_en_historial_api", {}).get("resultado") == 40.0

# 4. VUELTA: consultar historial desde calculadora-api leyendo historial-api por DNS interno
status_vuelta, resp_vuelta = request_json("http://calculadora-api:8000/historial")
print("[VUELTA] Respuesta GET /historial:", json.dumps(resp_vuelta, ensure_ascii=False))
assert status_vuelta == 200, f"HTTP esperado 200, recibido {status_vuelta}"
assert resp_vuelta.get("origen") == "http://historial-api:5001", f"Origen inesperado: {resp_vuelta}"
registros = resp_vuelta.get("datos", {}).get("registros", [])
assert len(registros) >= 1 and registros[-1].get("resultado") == 40.0, f"Registros inesperados: {registros}"

print("[OK] Comunicacion bidireccional por nombre de servicio (calculadora-api <-> historial-api) verificada.")
PY
