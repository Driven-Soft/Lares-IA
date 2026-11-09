# -*- coding: utf-8 -*-
"""
Lares - Estimativa do prazo de atendimento
==========================================
Usa o modelo treinado com os dados abertos do SP156
(pipeline/treinamento_modelo.py). Enquanto o modelo não existe, devolve o
prazo padrão da categoria, o mesmo do seed da API Java.

O app manda o bairro digitado pelo cidadão, e o SP156 usa os distritos
oficiais. O bairro só vira distrito quando o nome bate (sem acento e sem
diferenciar maiúsculas); senão, o modelo estima só com a categoria e o mês.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import joblib
import pandas as pd

from categorias import CATEGORIAS
from texto import normalizar

ARQUIVO_MODELO = Path(__file__).parent / "modelo" / "modelo_prazo.joblib"
DISTRITO_DESCONHECIDO = "DESCONHECIDO"


def carregar_artefato(caminho: Path = ARQUIVO_MODELO) -> dict | None:
    """Carrega o modelo treinado, ou None se ele ainda não foi gerado."""
    return joblib.load(caminho) if caminho.exists() else None


ARTEFATO = carregar_artefato()


def encontrar_distrito(bairro: str | None, distritos: list[str]) -> str | None:
    """Devolve o distrito do SP156 com o mesmo nome do bairro, se houver."""
    alvo = normalizar(bairro)
    if not alvo:
        return None
    for distrito in distritos:
        if normalizar(distrito) == alvo:
            return distrito
    return None


def estimar_prazo(categoria: str, bairro: str | None, hoje: date | None = None,
                  artefato: dict | None = None) -> int:
    """Prazo estimado, em dias inteiros (mínimo de 1 dia)."""
    artefato = artefato if artefato is not None else ARTEFATO
    padrao = CATEGORIAS[categoria]["prazo_padrao_dias"]
    if artefato is None or categoria not in artefato["categorias"]:
        return padrao

    distrito = encontrar_distrito(bairro, artefato["distritos"]) or DISTRITO_DESCONHECIDO
    mes = (hoje or date.today()).month
    entrada = pd.DataFrame([{"categoria": categoria, "distrito": distrito, "mes": mes}])
    dias = float(artefato["modelo"].predict(entrada)[0])
    return max(1, round(dias))
