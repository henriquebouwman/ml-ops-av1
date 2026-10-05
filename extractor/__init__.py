"""Extração da leitura do medidor: checa nitidez, chama o modelo, limpa os campos
e calcula a confiança."""

import time

from PIL import Image

from extractor.confianca import calcular_confianca
from extractor.modelo import OLLAMA_MODEL, chamar_modelo, limpar_campos, ollama_pronto
from extractor.nitidez import imagem_nitida

__all__ = ["extrair", "ollama_pronto"]


def extrair(imagem: Image.Image) -> dict:
    inicio = time.perf_counter()
    if imagem_nitida(imagem):
        bruto = chamar_modelo(imagem)
    else:
        bruto = {}  # foto lisa ou desfocada demais: nem chama o modelo
    campos = limpar_campos(bruto)
    confianca = calcular_confianca(campos, bruto.get("confianca") or {})
    # Sem nenhum campo lido, a foto é tratada como sem display legível.
    status = "ILEGIVEL" if all(v is None for v in campos.values()) else "OK"
    return {
        **campos,
        "confianca": confianca,
        "status": status,
        "modelo": OLLAMA_MODEL,
        "tempo_ms": round((time.perf_counter() - inicio) * 1000),
    }
