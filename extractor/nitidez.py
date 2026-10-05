"""Checagem determinística de nitidez, feita antes de chamar o modelo.

Uma foto lisa ou muito desfocada quase não tem bordas; nesses casos o modelo
inventa números em vez de devolver null, então a foto é marcada ILEGIVEL aqui."""

from PIL import Image, ImageFilter, ImageStat

# Calibrado só nas imagens de examples/ (nítidas: 616 a 4336; lisa/borradas: 60 a 157).
LIMIAR_NITIDEZ = 300


def nitidez(imagem: Image.Image) -> float:
    """Variância do filtro de bordas na imagem em tons de cinza."""
    cinza = imagem.convert("L")
    cinza.thumbnail((1024, 1024))
    return ImageStat.Stat(cinza.filter(ImageFilter.FIND_EDGES)).var[0]


def imagem_nitida(imagem: Image.Image) -> bool:
    return nitidez(imagem) >= LIMIAR_NITIDEZ
