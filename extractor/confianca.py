"""Confiança de cada campo = confiança declarada pelo modelo × fator de validação,
onde o fator é 1 se o valor passa na regra de formato, 0,5 se não passa e 0 se o
campo veio nulo; a confiança geral é a média dos três campos."""

import re

FATOR_INVALIDO = 0.5


def numero_medidor_valido(valor: str) -> bool:
    return re.fullmatch(r"\d{5,15}", valor) is not None


def funcao_valida(valor: str) -> bool:
    return re.fullmatch(r"\d{1,3}", valor) is not None


def consumo_valido(valor) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and valor >= 0


VALIDADORES = {
    "numero_medidor": numero_medidor_valido,
    "funcao": funcao_valida,
    "consumo": consumo_valido,
}


def calcular_confianca(campos: dict, declarada: dict) -> dict:
    confianca = {}
    for nome, validar in VALIDADORES.items():
        valor = campos[nome]
        modelo = min(max(float(declarada.get(nome) or 0), 0.0), 1.0)  # limita a [0, 1]
        if valor is None:
            fator = 0.0
        elif validar(valor):
            fator = 1.0
        else:
            fator = FATOR_INVALIDO
        confianca[nome] = round(modelo * fator, 2)
    confianca["geral"] = round(sum(confianca.values()) / len(VALIDADORES), 2)
    return confianca
