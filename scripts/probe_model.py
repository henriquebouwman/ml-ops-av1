"""Script descartável: roda o modelo visual do Ollama nas fotos de examples/
e imprime a resposta e o tempo de cada uma. Serve só para decidir o modelo."""

import base64
import io
import json
import sys
import time
from pathlib import Path

import httpx
from PIL import Image

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5vl:3b"

PROMPT = (
    "Esta é a foto de um medidor de energia elétrica. Extraia:\n"
    "- numero_medidor: o número de série impresso no corpo/etiqueta do medidor\n"
    "- funcao: o código do registrador exibido no display (ex.: 03, 1.8.0)\n"
    "- consumo: o valor numérico exibido no display (kWh)\n"
    "- confianca: de 0 a 1, o quanto você tem certeza de cada campo\n"
    "Use null para o que não estiver legível. Não invente valores."
)

# JSON schema: o Ollama restringe a saída do modelo a este formato
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

fotos = sorted(
    p for p in Path("examples").iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)
if not fotos:
    sys.exit("Nenhuma imagem em examples/")

for foto in fotos:
    # normaliza qualquer formato (png com alfa, webp...) para JPEG RGB
    buffer = io.BytesIO()
    Image.open(foto).convert("RGB").save(buffer, format="JPEG")
    corpo = {
        "model": MODELO,
        "prompt": PROMPT,
        "images": [base64.b64encode(buffer.getvalue()).decode()],
        "format": SCHEMA,
        "stream": False,
        "options": {"temperature": 0},
    }
    inicio = time.perf_counter()
    resposta = httpx.post(OLLAMA_URL, json=corpo, timeout=300).json()
    segundos = time.perf_counter() - inicio
    print(f"== {foto.name} ({segundos:.1f}s)")
    print(json.dumps(json.loads(resposta["response"]), ensure_ascii=False, indent=2))
