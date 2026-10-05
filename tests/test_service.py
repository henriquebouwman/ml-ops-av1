"""Testes do endpoint POST /extract, chamando o app BentoML em processo (sem subir servidor)."""

import io

import pytest
from PIL import Image, ImageFilter
from starlette.testclient import TestClient

from extractor import ollama_pronto
from service import LeituraMedidor

FOTO_BOA = "examples/example02.jpg"


@pytest.fixture(scope="module")
def cliente():
    with TestClient(LeituraMedidor.to_asgi()) as c:
        yield c


def enviar(cliente, conteudo: bytes, nome: str = "foto.jpg"):
    return cliente.post("/extract", files={"image": (nome, conteudo)})


@pytest.mark.skipif(not ollama_pronto(), reason="Ollama fora do ar ou modelo não baixado")
def test_foto_boa_extrai_leitura(cliente):
    with open(FOTO_BOA, "rb") as f:
        resposta = enviar(cliente, f.read())

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "OK"
    assert corpo["consumo"] == 1385
    assert corpo["confianca"]["geral"] > 0


def test_foto_ruim_devolve_ilegivel(cliente):
    # A mesma foto boa, desfocada até o display ficar ilegível.
    borrada = Image.open(FOTO_BOA).filter(ImageFilter.GaussianBlur(4))
    buffer = io.BytesIO()
    borrada.save(buffer, format="JPEG")

    resposta = enviar(cliente, buffer.getvalue())

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ILEGIVEL"
    assert corpo["numero_medidor"] is None
    assert corpo["funcao"] is None
    assert corpo["consumo"] is None
    assert corpo["confianca"]["geral"] == 0


def test_entrada_invalida_devolve_400(cliente):
    resposta = enviar(cliente, b"isto nao e uma imagem", nome="falsa.jpg")

    assert resposta.status_code == 400
    assert "não é uma imagem válida" in resposta.text
