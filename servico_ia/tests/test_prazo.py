# -*- coding: utf-8 -*-
"""
Testes da estimativa de prazo — Lares
=====================================
Sem modelo treinado, vale o prazo padrão da categoria. Com modelo, o prazo
vem da regressão; um artefato pequeno é treinado aqui mesmo, com dados
sintéticos, para não depender do SP156 nos testes.

Executar:  pytest -v
"""
from datetime import date

import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

import prazo
from prazo import encontrar_distrito, estimar_prazo


@pytest.fixture
def artefato():
    linhas = []
    for mes in range(1, 13):
        for _ in range(5):
            linhas.append({"categoria": "BURACO", "distrito": "VILA MARIANA", "mes": mes, "dias": 10})
            linhas.append({"categoria": "BURACO", "distrito": "GRAJAU", "mes": mes, "dias": 40})
            linhas.append({"categoria": "LIXO", "distrito": "VILA MARIANA", "mes": mes, "dias": 3})
    df = pd.DataFrame(linhas)
    pre = ColumnTransformer(
        [("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
          ["categoria", "distrito"])],
        remainder="passthrough",
    )
    modelo = Pipeline([("pre", pre),
                       ("reg", HistGradientBoostingRegressor(loss="absolute_error",
                                                             categorical_features=[0, 1],
                                                             random_state=42))])
    modelo.fit(df[["categoria", "distrito", "mes"]], df["dias"])
    return {"modelo": modelo, "categorias": ["BURACO", "LIXO"],
            "distritos": ["GRAJAU", "VILA MARIANA"], "mediana_categoria": {}, "metricas": {}}


# --------------------------------------------------------------------------
# Bairro → distrito
# --------------------------------------------------------------------------

def test_bairro_casa_com_distrito_sem_acento_e_sem_caixa():
    assert encontrar_distrito("Grajaú", ["GRAJAU", "MOEMA"]) == "GRAJAU"


def test_bairro_que_nao_e_distrito_fica_sem_correspondencia():
    assert encontrar_distrito("Vila Madalena", ["GRAJAU", "MOEMA"]) is None


def test_bairro_vazio_fica_sem_correspondencia():
    assert encontrar_distrito(None, ["GRAJAU"]) is None


# --------------------------------------------------------------------------
# Estimativa
# --------------------------------------------------------------------------

def test_sem_modelo_usa_o_prazo_padrao_da_categoria(monkeypatch):
    monkeypatch.setattr(prazo, "ARTEFATO", None)
    assert estimar_prazo("ILUMINACAO", "Moema") == 7
    assert estimar_prazo("OUTROS", None) == 30


def test_com_modelo_o_prazo_depende_do_distrito(artefato):
    hoje = date(2026, 11, 9)
    vila_mariana = estimar_prazo("BURACO", "Vila Mariana", hoje, artefato)
    grajau = estimar_prazo("BURACO", "Grajaú", hoje, artefato)
    assert vila_mariana < grajau


def test_bairro_desconhecido_ainda_gera_prazo(artefato):
    assert estimar_prazo("BURACO", "Jardins", date(2026, 11, 9), artefato) >= 1


def test_categoria_fora_do_treino_usa_o_prazo_padrao(artefato):
    assert estimar_prazo("ARVORE", "Vila Mariana", date(2026, 11, 9), artefato) == 20


def test_prazo_nunca_e_menor_que_um_dia(artefato):
    artefato["modelo"] = type("Zero", (), {"predict": lambda self, x: [0.2]})()
    assert estimar_prazo("LIXO", "Vila Mariana", date(2026, 11, 9), artefato) == 1
