import re

from fastapi.testclient import TestClient

from app import app
from rag.generation import NOT_FOUND_MESSAGE

client = TestClient(app)


def _normalizar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", texto)


NOT_FOUND_NORMALIZADO = _normalizar_espacos(NOT_FOUND_MESSAGE)


def perguntar(pergunta: str) -> str:
    response = client.post("/perguntar", json={"pergunta": pergunta})
    assert response.status_code == 200
    return _normalizar_espacos(response.json()["resposta"])


def test_reembolso():
    resposta = perguntar("Depois que um reembolso é aprovado, quanto tempo demora para eu receber o dinheiro de volta?")
    assert NOT_FOUND_NORMALIZADO not in resposta
    assert "dias úteis" in resposta.lower()


def test_pagamento():
    resposta = perguntar("Quais formas de pagamento a BimBam Buy aceita?")
    assert NOT_FOUND_NORMALIZADO not in resposta
    assert "pix" in resposta.lower() or "cartão" in resposta.lower()


def test_envio_formulacao_padrao():
    resposta = perguntar("Quais são os prazos de entrega dos pedidos?")
    assert NOT_FOUND_NORMALIZADO not in resposta
    assert "dias úteis" in resposta.lower()


def test_envio_formulacao_alternativa_1():
    resposta = perguntar("Quanto tempo demora para meu pedido chegar?")
    assert NOT_FOUND_NORMALIZADO not in resposta
    assert "dias úteis" in resposta.lower()


def test_envio_formulacao_alternativa_2():
    resposta = perguntar("Meu pedido está atrasado, o que fazer?")
    assert NOT_FOUND_NORMALIZADO not in resposta
    resposta_lower = resposta.lower()
    assert "rastre" in resposta_lower or "operador" in resposta_lower or "entrega" in resposta_lower


def test_afiliados():
    resposta = perguntar("Como funciona o programa de afiliados da BimBam Buy?")
    assert NOT_FOUND_NORMALIZADO not in resposta
    assert "comiss" in resposta.lower()


def test_garantia():
    resposta = perguntar("O que acontece quando eu abro um chamado de garantia por um produto com defeito?")
    assert NOT_FOUND_NORMALIZADO not in resposta
    assert "garantia" in resposta.lower() or "diagnóstico" in resposta.lower()


def test_pergunta_fora_de_escopo():
    resposta = perguntar("Qual é a capital da Mongólia?")
    assert NOT_FOUND_NORMALIZADO in resposta
