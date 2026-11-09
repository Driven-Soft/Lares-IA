# -*- coding: utf-8 -*-
"""
Lares - Regras de fallback da triagem
=====================================
Classificação por palavra-chave, usada quando o LLM não responde (sem
chave, timeout, erro ou resposta inválida). É determinística e auditável:
a mesma descrição sempre gera a mesma categoria e a mesma prioridade.

Categoria: a que tiver mais palavras-chave no texto; no empate, vale a
ordem do dicionário. Sem nenhuma palavra-chave, a categoria é OUTROS.

Prioridade: parte de MEDIA, sobe para ALTA com termos de risco e desce
para BAIXA com termos de baixo impacto. Termos dos dois tipos ao mesmo
tempo se anulam (fica MEDIA). Relato sem relação com zeladoria e sem
termo de risco fica BAIXA.

Os termos são comparados no texto normalizado (sem acento, minúsculo) e
casam no início de palavra: "machuc" pega "machucou", mas "fio" não pega
"desafio".
"""
from __future__ import annotations

import re

from categorias import Classificacao
from texto import normalizar

PALAVRAS_CATEGORIA = {
    "SINALIZACAO": ("semaforo", "farol", "placa", "sinalizacao", "faixa de pedestre", "lombada"),
    "ILUMINACAO": ("poste", "lampada", "luz", "iluminacao", "rua escura", "escuridao", "breu"),
    "BURACO": ("buraco", "buraqu", "cratera", "asfalto", "esburacad", "pavimento"),
    "LIXO": ("lixo", "entulho", "descarte", "coleta", "lixeira", "cacamba", "residuo", "sujeira"),
    "CALCADA": ("calcada", "passeio", "rampa", "cadeirante", "acessibilidade", "desnivel"),
    "ARVORE": ("arvore", "galho", "poda", "tronco", "raiz"),
}

PALAVRAS_ALTA = (
    "risco", "perig", "acident", "caiu", "cair", "caind", "queda", "fio", "fiacao",
    "faisca", "choque", "crianca", "escola", "hospital", "idos", "machuc", "ferid",
    "alag", "cratera", "enorme", "batida", "atropel", "assalto", "rato",
)

PALAVRAS_BAIXA = (
    "pichacao", "pichad", "pintura", "estetic", "torta", "torto", "pequen",
    "buraquinho", "nada urgente", "desperdicio",
)

CONFIANCA_COM_PALAVRA = 0.5
CONFIANCA_SEM_PALAVRA = 0.2


def _contem(texto: str, termo: str) -> bool:
    return re.search(r"\b" + re.escape(termo), texto) is not None


def _prioridade(texto: str, categoria: str) -> str:
    alta = any(_contem(texto, termo) for termo in PALAVRAS_ALTA)
    baixa = any(_contem(texto, termo) for termo in PALAVRAS_BAIXA)
    if alta and not baixa:
        return "ALTA"
    if baixa and not alta:
        return "BAIXA"
    if categoria == "OUTROS" and not alta:
        return "BAIXA"
    return "MEDIA"


def classificar_por_regras(descricao: str) -> Classificacao:
    """Classifica a descrição só com palavras-chave."""
    texto = normalizar(descricao)
    pontos = {
        categoria: sum(1 for termo in termos if _contem(texto, termo))
        for categoria, termos in PALAVRAS_CATEGORIA.items()
    }
    categoria, maior = max(pontos.items(), key=lambda item: item[1])

    if maior == 0:
        categoria = "OUTROS"
        justificativa = "Nenhuma palavra-chave de zeladoria encontrada."
        confianca = CONFIANCA_SEM_PALAVRA
    else:
        justificativa = f"{maior} palavra(s)-chave da categoria {categoria}."
        confianca = CONFIANCA_COM_PALAVRA

    return Classificacao(
        categoria=categoria,
        prioridade=_prioridade(texto, categoria),
        confianca=confianca,
        origem="fallback",
        justificativa=justificativa,
    )
