# -*- coding: utf-8 -*-
"""
Lares - Download dos dados abertos do SP156
===========================================
Baixa os quatro trimestres de 2025 das solicitações do SP156 (Prefeitura de
São Paulo, licença CC0). Os arquivos brutos ficam fora do git.

Fonte:  https://dados.prefeitura.sp.gov.br/dataset/dados-do-sp156
Uso:    python pipeline/baixar_dados.py
Saída:  data/sp156/*.csv
"""
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "data" / "sp156"
BASE = ("https://dados.prefeitura.sp.gov.br/dataset/0aecfa2b-aa3a-40d4-8183-0d4351b7fd0a"
        "/resource")
ARQUIVOS = {
    "sp156_2025_t1.csv": f"{BASE}/7c5aeb58-2cad-40ba-9e9e-af1c17cc5070/download/arquivo-final-1-trim-25.csv",
    "sp156_2025_t2.csv": f"{BASE}/f5df7f4a-d614-4f85-b4a0-263ec9370cd9/download/arquivo-final-2-trim-25.csv",
    "sp156_2025_t3.csv": f"{BASE}/3b1d2648-d586-40c8-819c-24fbb8005343/download/arquivo-final-3-trim-25.csv",
    "sp156_2025_t4.csv": f"{BASE}/d3a98097-8128-45d4-b8fe-21874b81c971/download/arquivo-final-4-trim-25.csv",
}


def main() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    for nome, url in ARQUIVOS.items():
        destino = PASTA / nome
        if destino.exists():
            print(f"{nome}: já existe, pulando")
            continue
        print(f"{nome}: baixando...")
        urllib.request.urlretrieve(url, destino)
        print(f"{nome}: {destino.stat().st_size / 1_048_576:.1f} MB")


if __name__ == "__main__":
    main()
