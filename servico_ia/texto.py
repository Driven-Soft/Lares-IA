# -*- coding: utf-8 -*-
"""
Lares - Normalização de texto
=============================
Deixa textos comparáveis: minúsculas, sem acento e com espaços simples.
Usada nas regras de palavra-chave, no casamento bairro → distrito e no
mapeamento dos serviços do SP156.
"""
from __future__ import annotations

import re
import unicodedata


def normalizar(texto: str | None) -> str:
    """Ex.: "  Calçada   QUEBRADA " → "calcada quebrada"."""
    if not texto:
        return ""
    decomposto = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()
