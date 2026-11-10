from calculadora import potencia, restar, sumar


def test_sumar():
    assert sumar(2, 3) == 5


def test_restar():
    assert restar(5, 3) == 2


def test_potencia():
    assert potencia(2, 3) == 8
