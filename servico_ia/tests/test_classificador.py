# -*- coding: utf-8 -*-
"""
Testes da classificação pelo LLM — Lares
========================================
A chamada à OpenAI é substituída por um cliente falso: os testes cobrem a
leitura da resposta, a validação e a queda para o fallback, sem rede.

Executar:  pytest -v
"""
import json
from types import SimpleNamespace

import pytest

import classificador
from classificador import classificar_com_llm


def _resposta(conteudo):
    mensagem = SimpleNamespace(content=conteudo)
    return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)])


class ClienteFalso:
    """Imita OpenAI(...).chat.completions.create e guarda a última chamada."""

    def __init__(self, conteudo=None, erro=None):
        self.conteudo = conteudo
        self.erro = erro
        self.chamada = None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.chamada = kwargs
        if self.erro:
            raise self.erro
        return _resposta(self.conteudo)


@pytest.fixture
def com_chave(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")


def _usar_cliente(monkeypatch, cliente):
    monkeypatch.setattr(classificador, "OpenAI", lambda **kwargs: cliente)


VALIDA = json.dumps({"categoria": "ARVORE", "prioridade": "ALTA",
                     "confianca": 0.934, "justificativa": "Árvore caída na fiação."})


def test_sem_chave_nao_chama_o_llm(monkeypatch):
    cliente = ClienteFalso(VALIDA)
    _usar_cliente(monkeypatch, cliente)
    assert classificar_com_llm("árvore caiu") is None
    assert cliente.chamada is None


def test_resposta_valida_vira_classificacao(monkeypatch, com_chave):
    _usar_cliente(monkeypatch, ClienteFalso(VALIDA))
    resultado = classificar_com_llm("árvore caiu na fiação", "Jabaquara")
    assert resultado.categoria == "ARVORE"
    assert resultado.prioridade == "ALTA"
    assert resultado.confianca == 0.93
    assert resultado.origem == "llm"


def test_envia_o_relato_como_mensagem_do_usuario_e_pede_json(monkeypatch, com_chave):
    cliente = ClienteFalso(VALIDA)
    _usar_cliente(monkeypatch, cliente)
    classificar_com_llm("árvore caiu", "Jabaquara")
    mensagens = cliente.chamada["messages"]
    assert mensagens[0]["role"] == "system"
    assert mensagens[1] == {"role": "user", "content": "Bairro: Jabaquara\nRelato: árvore caiu"}
    assert cliente.chamada["response_format"]["type"] == "json_schema"
    assert cliente.chamada["temperature"] == 0


def test_usa_o_modelo_da_variavel_de_ambiente(monkeypatch, com_chave):
    monkeypatch.setenv("OPENAI_MODEL", "modelo-de-teste")
    cliente = ClienteFalso(VALIDA)
    _usar_cliente(monkeypatch, cliente)
    classificar_com_llm("árvore caiu")
    assert cliente.chamada["model"] == "modelo-de-teste"


@pytest.mark.parametrize("conteudo", [
    "isto não é json",
    "",
    None,
    json.dumps({"categoria": "ENCHENTE", "prioridade": "ALTA",
                "confianca": 0.9, "justificativa": "x"}),
    json.dumps({"categoria": "BURACO", "prioridade": "URGENTE",
                "confianca": 0.9, "justificativa": "x"}),
    json.dumps({"categoria": "BURACO", "prioridade": "ALTA",
                "confianca": 1.7, "justificativa": "x"}),
])
def test_resposta_invalida_devolve_none(monkeypatch, com_chave, conteudo):
    _usar_cliente(monkeypatch, ClienteFalso(conteudo))
    assert classificar_com_llm("buraco na rua") is None


def test_erro_da_api_devolve_none(monkeypatch, com_chave):
    _usar_cliente(monkeypatch, ClienteFalso(erro=TimeoutError("demorou")))
    assert classificar_com_llm("buraco na rua") is None


def test_prompt_lista_todas_as_categorias():
    for codigo in ("BURACO", "ILUMINACAO", "LIXO", "CALCADA", "ARVORE", "SINALIZACAO", "OUTROS"):
        assert f"- {codigo}:" in classificador.PROMPT_SISTEMA
