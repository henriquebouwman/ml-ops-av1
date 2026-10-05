"""Chamada ao modelo visual servido pelo Ollama: prompt, formato da saída e parsing."""

import base64
import io
import json
import os

import httpx
from PIL import Image

OLLAMA_URL = os.environ.get("OLLAMA_URL") or "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL") or "qwen2.5vl:3b"
LADO_MAXIMO = 1024  # px; imagens maiores são reduzidas para limitar o tempo de inferência
TIMEOUT_S = 120

# Sem valores de exemplo no prompt: no teste inicial o modelo copiava o exemplo como resposta.
PROMPT = (
    "Esta é a foto de um medidor de energia elétrica. Extraia:\n"
    "- numero_medidor: o número de série do medidor, impresso na etiqueta ou no corpo "
    "(geralmente perto do código de barras). Só dígitos.\n"
    "- funcao: o código do registrador mostrado no display digital, em dígitos pequenos "
    "ao lado da leitura. Medidores de ponteiro ou de roletes (ciclométricos) não têm "
    "função: use null.\n"
    "- consumo: a leitura principal em kWh, exatamente os dígitos do display, sem "
    "acrescentar ponto decimal que não esteja visível.\n"
    "- confianca: para cada campo, um número de 0 a 1 dizendo o quanto você tem certeza.\n"
    "Use null em qualquer campo que não esteja legível. Não invente valores."
)

# JSON schema: o Ollama restringe a saída do modelo a este formato.
SCHEMA = {
    "type": "object",
    "properties": {
        "numero_medidor": {"type": ["string", "null"]},
        "funcao": {"type": ["string", "null"]},
        "consumo": {"type": ["number", "null"]},
        "confianca": {
            "type": "object",
            "properties": {
                "numero_medidor": {"type": "number"},
                "funcao": {"type": "number"},
                "consumo": {"type": "number"},
            },
            "required": ["numero_medidor", "funcao", "consumo"],
        },
    },
    "required": ["numero_medidor", "funcao", "consumo", "confianca"],
}


def chamar_modelo(imagem: Image.Image) -> dict:
    """Envia a imagem ao Ollama e devolve o JSON gerado pelo modelo, já como dict."""
    imagem = imagem.convert("RGB")
    imagem.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG")

    corpo = {
        "model": OLLAMA_MODEL,
        "prompt": PROMPT,
        "images": [base64.b64encode(buffer.getvalue()).decode()],
        "format": SCHEMA,
        "stream": False,
        "options": {"temperature": 0},
    }
    resposta = httpx.post(f"{OLLAMA_URL}/api/generate", json=corpo, timeout=TIMEOUT_S)
    resposta.raise_for_status()
    return json.loads(resposta.json()["response"])


def _texto(valor) -> str | None:
    """Texto vazio ou o modelo escrevendo "null" por extenso viram None."""
    texto = (valor or "").replace(" ", "")
    return None if texto.lower() in ("", "null", "none") else texto


def limpar_campos(bruto: dict) -> dict:
    """Normaliza os três campos extraídos pelo modelo."""
    return {
        "numero_medidor": _texto(bruto.get("numero_medidor")),
        "funcao": _texto(bruto.get("funcao")),
        "consumo": bruto.get("consumo"),
    }


def ollama_pronto() -> bool:
    """True se o Ollama responde e o modelo configurado já está baixado."""
    try:
        tags = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2).json()
    except httpx.HTTPError:
        return False
    return any(m["name"] == OLLAMA_MODEL for m in tags.get("models", []))
