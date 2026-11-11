# -*- coding: utf-8 -*-
"""
Testes da API do serviço de IA — Lares
======================================
Valida o contrato do endpoint POST /triagem (o que a API Java
consome), o fallback quando o LLM não responde, a validação de entrada e
a autenticação por X-API-Key.

Executar:  pytest -v
"""
import logging

from fastapi.testclient import TestClient

import main
from categorias import CODIGOS, Classificacao

client = TestClient(main.app)

BURACO = {"descricao": "Buraco enorme na frente da escola, carro já furou pneu",
          "bairro": "Vila Mariana"}


def triar(**overrides):
    return client.post("/triagem", json={**BURACO, **overrides})


# --------------------------------------------------------------------------
# Health check
# --------------------------------------------------------------------------

def test_health_responde_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm_configurado"] is False


def _linha_de_acesso(caminho):
    """Registro no formato do log de acesso do uvicorn."""
    return logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
                             ("10.0.0.1:5000", "GET", caminho, "1.1", 200), None)


def test_log_de_acesso_ignora_o_health_check():
    filtro = main.SemHealthCheck()
    assert filtro.filter(_linha_de_acesso("/health")) is False
    assert filtro.filter(_linha_de_acesso("/health?x=1")) is False


def test_log_de_acesso_mantem_as_outras_rotas():
    filtro = main.SemHealthCheck()
    assert filtro.filter(_linha_de_acesso("/triagem")) is True
    assert filtro.filter(_linha_de_acesso("/")) is True


def test_raiz_redireciona_para_o_swagger():
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/docs"


# --------------------------------------------------------------------------
# Contrato da resposta
# --------------------------------------------------------------------------

class TestContrato:
    def test_resposta_tem_exatamente_os_campos_combinados(self):
        body = triar().json()
        assert set(body) == {"categoria", "prioridade", "confianca",
                             "prazoEstimadoDias", "origem"}

    def test_valores_estao_nos_dominios_combinados(self):
        body = triar().json()
        assert body["categoria"] in CODIGOS
        assert body["prioridade"] in {"BAIXA", "MEDIA", "ALTA"}
        assert 0 <= body["confianca"] <= 1
        assert body["prazoEstimadoDias"] >= 1

    def test_bairro_e_opcional(self):
        r = client.post("/triagem", json={"descricao": BURACO["descricao"]})
        assert r.status_code == 200


# --------------------------------------------------------------------------
# LLM e fallback
# --------------------------------------------------------------------------

class TestOrigem:
    def test_sem_chave_da_openai_usa_as_regras(self):
        body = triar().json()
        assert body["origem"] == "fallback"
        assert body["categoria"] == "BURACO"
        assert body["prioridade"] == "ALTA"

    def test_quando_o_llm_responde_a_origem_e_llm(self, monkeypatch):
        resposta = Classificacao(categoria="ILUMINACAO", prioridade="MEDIA",
                                 confianca=0.91, origem="llm")
        monkeypatch.setattr(main, "classificar_com_llm", lambda descricao, bairro: resposta)
        body = triar().json()
        assert body["origem"] == "llm"
        assert body["categoria"] == "ILUMINACAO"
        assert body["confianca"] == 0.91

    def test_quando_o_llm_falha_a_origem_e_fallback(self, monkeypatch):
        monkeypatch.setattr(main, "classificar_com_llm", lambda descricao, bairro: None)
        assert triar().json()["origem"] == "fallback"


# --------------------------------------------------------------------------
# Validação de entrada
# --------------------------------------------------------------------------

class TestValidacao:
    def test_descricao_vazia_retorna_422(self):
        assert triar(descricao="").status_code == 422

    def test_descricao_so_com_espacos_retorna_422(self):
        assert triar(descricao="    ").status_code == 422

    def test_descricao_acima_de_500_caracteres_retorna_422(self):
        assert triar(descricao="a" * 501).status_code == 422

    def test_descricao_com_500_caracteres_e_aceita(self):
        assert triar(descricao="buraco " + "a" * 493).status_code == 200

    def test_sem_descricao_retorna_422(self):
        assert client.post("/triagem", json={"bairro": "Moema"}).status_code == 422


# --------------------------------------------------------------------------
# Autenticação
# --------------------------------------------------------------------------

class TestAutenticacao:
    def test_sem_chave_configurada_o_endpoint_fica_aberto(self):
        assert triar().status_code == 200

    def test_com_chave_configurada_exige_o_header(self, monkeypatch):
        monkeypatch.setenv("LARES_IA_API_KEY", "segredo-de-teste")
        assert triar().status_code == 401

    def test_chave_errada_retorna_401(self, monkeypatch):
        monkeypatch.setenv("LARES_IA_API_KEY", "segredo-de-teste")
        r = client.post("/triagem", json=BURACO, headers={"X-API-Key": "outra"})
        assert r.status_code == 401

    def test_chave_certa_retorna_200(self, monkeypatch):
        monkeypatch.setenv("LARES_IA_API_KEY", "segredo-de-teste")
        r = client.post("/triagem", json=BURACO, headers={"X-API-Key": "segredo-de-teste"})
        assert r.status_code == 200

    def test_health_continua_publico_com_chave_configurada(self, monkeypatch):
        monkeypatch.setenv("LARES_IA_API_KEY", "segredo-de-teste")
        assert client.get("/health").status_code == 200
