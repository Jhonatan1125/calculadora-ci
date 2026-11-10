import pytest

from config import CONFIG, cargar_config


def test_ambiente_por_defecto(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert cargar_config()[0] == "desarrollo"


def test_ambiente_desconocido(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(ValueError):
        cargar_config()


def test_bases_de_datos_independientes():
    bases = [c["base_datos"] for c in CONFIG.values()]
    assert len(bases) == len(set(bases))


def test_produccion_sin_depuracion():
    assert CONFIG["produccion"]["depuracion"] is False
