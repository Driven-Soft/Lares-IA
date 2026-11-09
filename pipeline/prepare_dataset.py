# -*- coding: utf-8 -*-
"""
Lares - Preparação do dataset de prazos do SP156
================================================
Transforma as solicitações brutas do SP156 no dataset de treino do modelo
de prazo:
  1) lê os CSVs trimestrais (detecta separador e encoding);
  2) mantém só as solicitações finalizadas;
  3) mapeia o serviço do SP156 para uma das categorias do Lares por lista
     de termos (o que não é zeladoria fica de fora);
  4) calcula os dias entre a abertura e a finalização (0 a 365 dias).

O SP156 não traz o texto da reclamação nem o bairro: as features possíveis
são a categoria, o distrito e a data.

Uso:    python pipeline/prepare_dataset.py
Saída:  data/sp156_prazos.csv          (categoria, distrito, mes, dias)
        data/mapeamento_servicos.csv   (serviço do SP156 → categoria, com contagem)
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "servico_ia"))
from texto import normalizar  # noqa: E402

PASTA = RAIZ / "data" / "sp156"
SAIDA = RAIZ / "data" / "sp156_prazos.csv"
SAIDA_MAPEAMENTO = RAIZ / "data" / "mapeamento_servicos.csv"
DIAS_MAXIMO = 365

# Nome da coluna no SP156 (normalizado) → nome usado aqui. O dicionário de
# dados chama o status de "Status da Solicitação", mas os CSVs de 2025 trazem
# só "Status"; os dois nomes são aceitos.
COLUNAS = {
    "data de abertura": "abertura",
    "data de finalizacao": "finalizacao",
    "servico": "servico",
    "status": "status",
    "status da solicitacao": "status",
    "distrito": "distrito",
}

# Serviço do SP156 → categoria do Lares. Só entram os serviços que são um
# problema de zeladoria relatado pelo cidadão: ficam de fora pedidos de
# instalação, autorizações, denúncias de terceiros e serviços em área
# particular. O SP156 de 2025 não tem iluminação pública (atendida por outro
# canal da prefeitura); para ILUMINACAO e OUTROS vale o prazo padrão.
MAPA_CATEGORIAS = [
    # (categoria, o serviço precisa ter um destes termos, e nenhum destes)
    ("ARVORE", ("arvore",), ("area interna", "denunciar", "plantio", "mudas")),
    ("BURACO", ("tapa-buraco", "paralelepipedo", "nivelamento de vias"), ()),
    ("CALCADA", ("calcada",), ("sugerir construcao", "calcadao", "plantio")),
    ("LIXO", ("entulho", "coleta de lixo domiciliar", "falta de varricao",
              "sacos de varricao", "lixeiras publicas"),
     ("cacamba irregular", "flagrante", "conteiner")),
    ("SINALIZACAO", ("sinalizacao horizontal apagada", "placas de transito",
                     "placa com nome de rua", "manutencao de semaforos"), ("instalacao",)),
    ("ILUMINACAO", ("iluminacao publica", "lampada"), ()),
]


def categoria_do_servico(servico: str) -> str | None:
    texto = normalizar(servico)
    for categoria, incluir, excluir in MAPA_CATEGORIAS:
        if any(t in texto for t in incluir) and not any(t in texto for t in excluir):
            return categoria
    return None


def ler_csv(caminho: Path) -> pd.DataFrame:
    with open(caminho, "rb") as arquivo:
        primeira_linha = arquivo.readline()
    sep = ";" if primeira_linha.count(b";") >= primeira_linha.count(b",") else ","

    def usar(coluna: str) -> bool:
        return normalizar(coluna) in COLUNAS

    for encoding in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(caminho, sep=sep, encoding=encoding, usecols=usar, dtype=str)
            break
        except UnicodeDecodeError:
            continue
    df = df.rename(columns=lambda c: COLUNAS[normalizar(c)])
    faltando = set(COLUNAS.values()) - set(df.columns)
    if faltando:
        raise SystemExit(f"{caminho.name}: colunas não encontradas: {sorted(faltando)}")
    return df


def main() -> None:
    arquivos = sorted(PASTA.glob("*.csv"))
    if not arquivos:
        raise SystemExit("Nenhum CSV em data/sp156. Rode antes: python pipeline/baixar_dados.py")

    df = pd.concat([ler_csv(caminho) for caminho in arquivos], ignore_index=True)
    print(f"Solicitações lidas: {len(df):,}")

    df = df[df["status"].map(normalizar).str.contains("finaliz", na=False)]
    print(f"Finalizadas: {len(df):,}")

    df["categoria"] = df["servico"].map(categoria_do_servico)
    df = df.dropna(subset=["categoria"])
    print(f"De zeladoria (mapeadas para o Lares): {len(df):,}")

    abertura = pd.to_datetime(df["abertura"], format="mixed", dayfirst=True, errors="coerce")
    finalizacao = pd.to_datetime(df["finalizacao"], format="mixed", dayfirst=True, errors="coerce")
    df["dias"] = ((finalizacao - abertura).dt.total_seconds() / 86_400).round(2)
    df["mes"] = abertura.dt.month
    df["distrito"] = df["distrito"].str.strip()
    df = df.dropna(subset=["dias", "mes", "distrito"])
    df = df[(df["dias"] >= 0) & (df["dias"] <= DIAS_MAXIMO) & (df["distrito"] != "")]
    df["mes"] = df["mes"].astype(int)
    print(f"Com datas e distrito válidos (0 a {DIAS_MAXIMO} dias): {len(df):,}")

    mapeamento = (df.groupby(["categoria", "servico"]).size()
                  .rename("quantidade").reset_index()
                  .sort_values(["categoria", "quantidade"], ascending=[True, False]))
    mapeamento.to_csv(SAIDA_MAPEAMENTO, index=False)

    df[["categoria", "distrito", "mes", "dias"]].to_csv(SAIDA, index=False)

    resumo = df.groupby("categoria")["dias"].agg(["count", "median", "mean"]).round(1)
    print("\nPor categoria (dias até a finalização):")
    print(resumo.to_string())
    print(f"\nDistritos: {df['distrito'].nunique()}")
    print(f"Salvo: {SAIDA.relative_to(RAIZ)} e {SAIDA_MAPEAMENTO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
