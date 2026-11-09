# -*- coding: utf-8 -*-
"""
Lares - Categorias e prioridades da triagem
===========================================
Mesma lista do seed da API Java (tabela LARES_CATEGORIA). O código é o que o
serviço devolve à API Java; a descrição entra no prompt do LLM; o prazo padrão
é usado enquanto não existe modelo de prazo treinado.
"""
from __future__ import annotations

from dataclasses import dataclass

CATEGORIAS = {
    "BURACO": {
        "nome": "Buraco na via",
        "descricao": "buraco, cratera ou asfalto danificado na rua",
        "prazo_padrao_dias": 15,
    },
    "ILUMINACAO": {
        "nome": "Iluminação pública",
        "descricao": "poste apagado, lâmpada queimada ou piscando, rua sem iluminação",
        "prazo_padrao_dias": 7,
    },
    "LIXO": {
        "nome": "Lixo e entulho",
        "descricao": "lixo acumulado, entulho, descarte irregular, coleta que não passou",
        "prazo_padrao_dias": 5,
    },
    "CALCADA": {
        "nome": "Calçada danificada",
        "descricao": "calçada quebrada, desnivelada ou obstruída, falta de rampa ou acessibilidade",
        "prazo_padrao_dias": 30,
    },
    "ARVORE": {
        "nome": "Árvore e poda",
        "descricao": "árvore caída ou com risco de queda, galhos quebrados, pedido de poda",
        "prazo_padrao_dias": 20,
    },
    "SINALIZACAO": {
        "nome": "Sinalização de trânsito",
        "descricao": "semáforo apagado ou com defeito, placa caída ou torta, faixa de pedestre apagada",
        "prazo_padrao_dias": 10,
    },
    "OUTROS": {
        "nome": "Outros",
        "descricao": "qualquer outro problema urbano, ou relato sem relação com zeladoria",
        "prazo_padrao_dias": 30,
    },
}

CODIGOS = tuple(CATEGORIAS)
PRIORIDADES = ("BAIXA", "MEDIA", "ALTA")


@dataclass(frozen=True)
class Classificacao:
    """Resultado da triagem de uma ocorrência (pelo LLM ou pelas regras)."""
    categoria: str
    prioridade: str
    confianca: float
    origem: str  # "llm" ou "fallback"
    justificativa: str = ""
