# -*- coding: utf-8 -*-
"""
Testes das regras de fallback — Lares
=====================================
Categoria por palavra-chave, prioridade por termos de risco e de baixo
impacto, e o comportamento com relatos sem relação com zeladoria.

Executar:  pytest -v
"""
import pytest

from regras import classificar_por_regras
from texto import normalizar


def test_normalizar_tira_acento_caixa_e_espacos_extras():
    assert normalizar("  Calçada   QUEBRADA ") == "calcada quebrada"


# --------------------------------------------------------------------------
# Categoria
# --------------------------------------------------------------------------

@pytest.mark.parametrize("descricao, categoria", [
    ("Tem uma cratera no meio da avenida", "BURACO"),
    ("asfalto todo esburacado na minha rua", "BURACO"),
    ("poste apagado faz uma semana", "ILUMINACAO"),
    ("a lâmpada fica piscando a noite toda", "ILUMINACAO"),
    ("lixo acumulado na esquina", "LIXO"),
    ("o caminhão de coleta não passou", "LIXO"),
    ("calçada toda quebrada", "CALCADA"),
    ("não tem rampa para cadeirante", "CALCADA"),
    ("galho quebrado pendurado no ponto de ônibus", "ARVORE"),
    ("preciso de poda na árvore da frente", "ARVORE"),
    ("semáforo apagado no cruzamento", "SINALIZACAO"),
    ("farol quebrado na avenida", "SINALIZACAO"),
])
def test_categoria_por_palavra_chave(descricao, categoria):
    assert classificar_por_regras(descricao).categoria == categoria


def test_empate_segue_a_ordem_do_dicionario():
    # "raiz" (ARVORE) e "calcada" (CALCADA): CALCADA vem antes no dicionário
    assert classificar_por_regras("a raiz levantou a calçada").categoria == "CALCADA"


def test_sem_palavra_chave_vira_outros_com_confianca_baixa():
    resultado = classificar_por_regras("quero pedir uma pizza")
    assert resultado.categoria == "OUTROS"
    assert resultado.prioridade == "BAIXA"
    assert resultado.confianca == 0.2


def test_origem_e_sempre_fallback():
    assert classificar_por_regras("buraco na rua").origem == "fallback"


# --------------------------------------------------------------------------
# Prioridade
# --------------------------------------------------------------------------

def test_termo_de_risco_sobe_para_alta():
    assert classificar_por_regras("árvore caiu em cima da fiação").prioridade == "ALTA"


def test_termo_de_baixo_impacto_desce_para_baixa():
    assert classificar_por_regras("buraquinho pequeno, nada urgente").prioridade == "BAIXA"


def test_sem_termos_fica_media():
    assert classificar_por_regras("lâmpada do poste queimada").prioridade == "MEDIA"


def test_termos_de_risco_e_de_baixo_impacto_se_anulam():
    assert classificar_por_regras("pichação no muro da escola").prioridade == "MEDIA"


def test_termo_casa_so_no_inicio_da_palavra():
    # "fio" (risco) não pode casar com "desafio"
    assert classificar_por_regras("buraco na rua, um desafio passar").prioridade == "MEDIA"
