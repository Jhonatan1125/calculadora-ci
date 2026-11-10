import json
import os
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)

HISTORIAL_PORT = int(os.environ.get("HISTORIAL_PORT", "5001"))
HISTORIAL_DATA_FILE = Path(os.environ.get("HISTORIAL_DATA_FILE", "/data/historial.json"))
HISTORIAL_API_KEY = os.environ.get("HISTORIAL_API_KEY", "")


def verificar_api_key() -> bool:
    if not HISTORIAL_API_KEY:
        return False
    return request.headers.get("X-API-Key") == HISTORIAL_API_KEY


def leer_registros() -> list:
    if not HISTORIAL_DATA_FILE.exists():
        return []
    try:
        contenido = HISTORIAL_DATA_FILE.read_text(encoding="utf-8")
        return json.loads(contenido)
    except (json.JSONDecodeError, OSError):
        return []


def guardar_registros(registros: list) -> None:
    HISTORIAL_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORIAL_DATA_FILE.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@app.get("/health")
def health():
    return jsonify({
        "servicio": "historial-api",
        "estado": "ok",
        "archivo_datos": str(HISTORIAL_DATA_FILE),
    }), 200


@app.post("/registros")
def crear_registro():
    if not verificar_api_key():
        return jsonify({"error": "No autorizado: API Key invalida"}), 401

    datos = request.get_json(silent=True) or {}
    registros = leer_registros()
    nuevo_registro = {
        "id": len(registros) + 1,
        "operacion": datos.get("operacion"),
        "a": datos.get("a"),
        "b": datos.get("b"),
        "resultado": datos.get("resultado"),
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
    }
    registros.append(nuevo_registro)
    guardar_registros(registros)
    return jsonify(nuevo_registro), 201


@app.get("/registros")
def listar_registros():
    if not verificar_api_key():
        return jsonify({"error": "No autorizado: API Key invalida"}), 401

    registros = leer_registros()
    return jsonify({
        "total": len(registros),
        "registros": registros,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=HISTORIAL_PORT)
