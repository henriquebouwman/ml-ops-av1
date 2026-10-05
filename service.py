"""Serviço BentoML: valida a imagem recebida, chama o extrator e devolve a extração."""

from http import HTTPStatus
from pathlib import Path
from typing import Literal

import bentoml
import httpx
from bentoml.exceptions import BentoMLException, InvalidArgument, ServiceUnavailable
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from extractor import extrair, ollama_pronto


class Confianca(BaseModel):
    numero_medidor: float
    funcao: float
    consumo: float
    geral: float


class Extracao(BaseModel):
    numero_medidor: str | None
    funcao: str | None
    consumo: float | None
    confianca: Confianca
    status: Literal["OK", "ILEGIVEL"]
    modelo: str
    tempo_ms: int


@bentoml.service(name="leitura_medidor", traffic={"timeout": 180})
class LeituraMedidor:
    def __is_ready__(self) -> bool:
        # /readyz só responde 200 quando o Ollama está de pé com o modelo baixado.
        return ollama_pronto()

    @bentoml.api(route="/extract")
    def extract(self, image: Path) -> Extracao:
        """Recebe a foto do medidor (multipart, campo `image`) e devolve a extração."""
        try:
            imagem = Image.open(image)
            imagem.load()  # força a leitura completa: pega arquivos truncados
        except (UnidentifiedImageError, OSError):
            raise InvalidArgument(
                "O campo 'image' não é uma imagem válida. Envie um arquivo JPEG, PNG ou WebP."
            )

        try:
            return Extracao(**extrair(imagem))
        except httpx.HTTPError:
            raise ServiceUnavailable(
                "Modelo indisponível: confira se o Ollama está rodando (ollama serve)."
            )
        except ValueError:
            raise BentoMLException(
                "O modelo devolveu uma resposta fora do formato esperado.",
                error_code=HTTPStatus.BAD_GATEWAY,
            )
