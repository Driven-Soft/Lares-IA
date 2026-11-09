# -*- coding: utf-8 -*-
"""Configuração comum dos testes do serviço de IA."""
import pytest


@pytest.fixture(autouse=True)
def sem_chaves(monkeypatch):
    """Os testes nunca chamam a OpenAI e rodam com o endpoint aberto, mesmo
    que o .env da máquina tenha as chaves; os testes de autenticação e do
    LLM configuram o que precisam por conta."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LARES_IA_API_KEY", raising=False)
