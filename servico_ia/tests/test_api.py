# -*- coding: utf-8 -*-
"""
Testes da API do serviço de IA — Lares
======================================
Valida o contrato do endpoint POST /triagem (o que a API Java
consome), o fallback quando o LLM não responde, a validação de entrada e
a autenticação por X-API-Key.

Executar:  pytest -v
"""
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
