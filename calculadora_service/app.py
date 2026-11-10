import os
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# URL del Contenedor 2 usando el NOMBRE DEL SERVICIO en la red de Docker (nunca localhost ni IP fija)
HISTORIAL_SERVICE_URL = os.environ.get("HISTORIAL_SERVICE_URL", "http://historial-api:5001")
HISTORIAL_API_KEY = os.environ.get("HISTORIAL_API_KEY", "")
APP_PORT = int(os.environ.get("APP_PORT", "8000"))


def ejecutar_operacion(operacion: str, a: float, b: float) -> float:
    if operacion == "sumar":
        return a + b
    if operacion == "restar":
        return a - b
    if operacion == "multiplicar":
        return a * b
    if operacion == "dividir":
        if b == 0:
            raise ValueError("No se puede dividir por cero")
        return a / b
    if operacion == "potencia":
        return a ** b
    raise ValueError(f"Operacion no soportada: {operacion}")


@app.get("/health")
def health():
    return jsonify({
        "servicio": "calculadora-api",
        "estado": "ok",
        "historial_service_url": HISTORIAL_SERVICE_URL,
    }), 200


@app.post("/calcular")
def calcular():
    datos = request.get_json(silent=True) or {}
    operacion = datos.get("operacion")
    try:
        a = float(datos.get("a"))
        b = float(datos.get("b"))
        resultado = ejecutar_operacion(operacion, a, b)
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    # IDA: Enviar el cálculo al Contenedor 2 (historial-api) usando el nombre del servicio Docker
    registro_guardado = None
    try:
        respuesta = requests.post(
            f"{HISTORIAL_SERVICE_URL}/registros",
            json={
                "operacion": operacion,
                "a": a,
                "b": b,
                "resultado": resultado,
            },
            headers={"X-API-Key": HISTORIAL_API_KEY},
            timeout=5,
        )
        respuesta.raise_for_status()
        registro_guardado = respuesta.json()
    except requests.RequestException as exc:
        return jsonify({
            "error": "Fallo la comunicacion con el servicio historial-api",
            "detalle": str(exc),
        }), 502

    return jsonify({
        "operacion": operacion,
        "a": a,
        "b": b,
        "resultado": resultado,
        "guardado_en_historial_api": registro_guardado,
    }), 201


@app.get("/historial")
def obtener_historial():
    # VUELTA: Consultar los cálculos guardados en el Contenedor 2 (historial-api) por nombre de servicio
    try:
        respuesta = requests.get(
            f"{HISTORIAL_SERVICE_URL}/registros",
            headers={"X-API-Key": HISTORIAL_API_KEY},
            timeout=5,
        )
        respuesta.raise_for_status()
        return jsonify({
            "origen": HISTORIAL_SERVICE_URL,
            "datos": respuesta.json(),
        }), 200
    except requests.RequestException as exc:
        return jsonify({
            "error": "No fue posible leer el historial desde historial-api",
            "detalle": str(exc),
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
