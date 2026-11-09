# -*- coding: utf-8 -*-
"""
Lares - Avaliação do modelo de prazo
====================================
Compara o modelo com o baseline (mediana de dias por categoria) no mesmo
conjunto de teste do treinamento, por categoria, e mostra como o prazo
estimado muda conforme o distrito.

Uso:    python pipeline/avaliacao_modelo.py
Saída:  docs/AVALIACAO_PRAZO.md
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error

from treinamento_modelo import dividir

RAIZ = Path(__file__).resolve().parent.parent
DATASET = RAIZ / "data" / "sp156_prazos.csv"
ARTEFATO = RAIZ / "servico_ia" / "modelo" / "modelo_prazo.joblib"
SAIDA = RAIZ / "docs" / "AVALIACAO_PRAZO.md"
TOLERANCIA_DIAS = 7


def tabela(df: pd.DataFrame) -> str:
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |",
              "| " + " | ".join("---" for _ in df.columns) + " |"]
    linhas += ["| " + " | ".join(map(str, valores)) + " |" for valores in df.itertuples(index=False)]
    return "\n".join(linhas)


def main() -> None:
    df = pd.read_csv(DATASET)
    artefato = joblib.load(ARTEFATO)
    modelo = artefato["modelo"]
    _, X_te, _, y_te = dividir(df)

    previsto = pd.Series(modelo.predict(X_te), index=X_te.index)
    baseline = X_te["categoria"].map(artefato["mediana_categoria"])

    por_categoria = []
    for categoria, grupo in X_te.groupby("categoria"):
        reais = y_te[grupo.index]
        por_categoria.append({
            "Categoria": categoria,
            "Amostras de teste": len(grupo),
            "MAE modelo (dias)": round(mean_absolute_error(reais, previsto[grupo.index]), 1),
            "MAE baseline (dias)": round(mean_absolute_error(reais, baseline[grupo.index]), 1),
            f"Acerto em até {TOLERANCIA_DIAS} dias": f"{((reais - previsto[grupo.index]).abs() <= TOLERANCIA_DIAS).mean():.0%}",
        })

    mae_modelo = mean_absolute_error(y_te, previsto)
    mae_baseline = mean_absolute_error(y_te, baseline)
    dentro = ((y_te - previsto).abs() <= TOLERANCIA_DIAS).mean()

    distritos = df["distrito"].value_counts().index[:3].tolist()
    exemplos = []
    for categoria in artefato["categorias"]:
        linha = {"Categoria": categoria}
        for distrito in distritos:
            entrada = pd.DataFrame([{"categoria": categoria, "distrito": distrito, "mes": 11}])
            linha[distrito] = max(1, round(float(modelo.predict(entrada)[0])))
        exemplos.append(linha)

    relatorio = f"""# Avaliação do modelo de prazo

Gerado por `pipeline/avaliacao_modelo.py` com os dados do SP156 de 2025
(solicitações finalizadas de zeladoria, de 0 a 365 dias).

## Resultado geral

| Métrica | Valor |
| --- | --- |
| Amostras de treino | {artefato['metricas']['amostras_treino']:,} |
| Amostras de teste | {len(X_te):,} |
| MAE do modelo | {mae_modelo:.2f} dias |
| MAE do baseline (mediana por categoria) | {mae_baseline:.2f} dias |
| Ganho sobre o baseline | {(1 - mae_modelo / mae_baseline):.0%} |
| Acerto em até {TOLERANCIA_DIAS} dias | {dentro:.0%} |

## Por categoria

{tabela(pd.DataFrame(por_categoria))}

## Mesmo problema, distritos diferentes (abertura em novembro)

Prazo estimado, em dias, nos três distritos com mais solicitações:

{tabela(pd.DataFrame(exemplos))}

## Limitações

- O modelo só conhece o que o SP156 registra: categoria, distrito e data. Não vê a gravidade
  descrita pelo cidadão nem a fila atual de cada equipe.
- O bairro digitado no app só é usado quando tem o mesmo nome de um distrito oficial; senão,
  o modelo estima só com a categoria e o mês.
- O mapeamento dos serviços do SP156 para as categorias do Lares é por palavra-chave
  (ver `data/mapeamento_servicos.csv`).
- Os dados são de São Paulo; em outra cidade, o modelo precisaria ser treinado de novo.
"""
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(relatorio, encoding="utf-8")
    print(f"MAE modelo {mae_modelo:.2f} | baseline {mae_baseline:.2f} | em até {TOLERANCIA_DIAS} dias: {dentro:.0%}")
    print(f"Salvo: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
