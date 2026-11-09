# -*- coding: utf-8 -*-
"""
Lares - Serviço de IA (Python/FastAPI)
======================================
Serviço stateless, sem acesso a banco. Recebe da API Java a
descrição e o bairro de uma ocorrência e devolve a triagem:
  1) categoria e prioridade, pelo LLM (OpenAI) ou, se ele falhar, pelas
     regras de palavra-chave;
  2) prazo estimado de atendimento, pelo modelo treinado com o SP156.

Autenticação: quando a variável LARES_IA_API_KEY está definida, POST
/triagem exige o header X-API-Key com o mesmo valor. Sem a variável
(execução local), o endpoint fica aberto. GET /health é sempre público.

Configuração: arquivo .env nesta pasta (ver .env.example).

Execução local:
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field

load_dotenv(Path(__file__).parent / ".env")

from classificador import classificar_com_llm  # noqa: E402
from prazo import ARTEFATO, estimar_prazo  # noqa: E402
from regras import classificar_por_regras  # noqa: E402

app = FastAPI(
    title="Lares - Serviço de IA",
    description="Triagem de ocorrências de zeladoria: categoria, prioridade e prazo estimado",
    version="1.0.0",
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False,
                              description="Chave compartilhada com a API Java")


def exigir_chave(chave: Optional[str] = Security(api_key_header)) -> None:
    """Valida o X-API-Key quando o serviço roda com LARES_IA_API_KEY."""
    esperada = os.getenv("LARES_IA_API_KEY")
    if not esperada:
        return
    if chave is None or not secrets.compare_digest(chave, esperada):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail="X-API-Key ausente ou inválida")


class TriagemRequest(BaseModel):
    """Payload enviado pela API Java ao registrar uma ocorrência."""
    model_config = ConfigDict(str_strip_whitespace=True)

    descricao: str = Field(..., min_length=1, max_length=500,
                           description="LARES_OCORRENCIA.descricao")
    bairro: Optional[str] = Field(None, max_length=80,
                                  description="LARES_OCORRENCIA.bairro")


class TriagemResponse(BaseModel):
    """Contrato combinado com a API Java (JSON em camelCase)."""
    model_config = ConfigDict(populate_by_name=True)

    categoria: str = Field(..., description="Código de LARES_CATEGORIA")
    prioridade: Literal["BAIXA", "MEDIA", "ALTA"]
    confianca: float = Field(..., ge=0, le=1)
    prazo_estimado_dias: int = Field(..., alias="prazoEstimadoDias", ge=1)
    origem: Literal["llm", "fallback"]


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_configurado": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "modelo_prazo": "treinado" if ARTEFATO else "prazo_padrao",
        "metricas_modelo": ARTEFATO["metricas"] if ARTEFATO else None,
    }


@app.post("/triagem", response_model=TriagemResponse, dependencies=[Depends(exigir_chave)])
def triagem(req: TriagemRequest) -> TriagemResponse:
    classificacao = (classificar_com_llm(req.descricao, req.bairro)
                     or classificar_por_regras(req.descricao))
    return TriagemResponse(
        categoria=classificacao.categoria,
        prioridade=classificacao.prioridade,
        confianca=classificacao.confianca,
        prazo_estimado_dias=estimar_prazo(classificacao.categoria, req.bairro),
        origem=classificacao.origem,
    )
