import os

CONFIG = {
    "desarrollo": {"base_datos": "dev.db", "depuracion": True},
    "pruebas": {"base_datos": "test.db", "depuracion": True},
    "produccion": {"base_datos": "prod.db", "depuracion": False},
}


def cargar_config():
    ambiente = os.environ.get("APP_ENV", "desarrollo")
    if ambiente not in CONFIG:
        raise ValueError(f"Ambiente desconocido: {ambiente}")
    return ambiente, CONFIG[ambiente]
