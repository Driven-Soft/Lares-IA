# -*- coding: utf-8 -*-
"""
Lares - Treinamento do modelo de prazo de atendimento
=====================================================
Regressão do número de dias até a finalização de uma solicitação, a partir
da categoria, do distrito e do mês de abertura (dados do SP156).

Modelo: HistGradientBoostingRegressor com perda absoluta (otimiza o erro
absoluto médio, o que é robusto aos poucos casos que demoram muito) e
categoria e distrito como features categóricas nativas. Com os mesmos
hiperparâmetros, o suporte nativo errou 1 dia a menos que o one-hot (MAE de
16,6 contra 17,5), porque aprende melhor a combinação categoria × distrito.
Baseline: a mediana de dias de cada categoria. O modelo só vale a pena se
errar menos que o baseline.

Distrito fora do treino (bairro que não bate com um distrito) é codificado
como -1, que o modelo trata como valor ausente.

Executado offline. O artefato (joblib) é embarcado no serviço de IA
(servico_ia/), que só faz inferência.

Uso:    python pipeline/treinamento_modelo.py
Saída:  servico_ia/modelo/modelo_prazo.joblib
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

SEED = 42
RAIZ = Path(__file__).resolve().parent.parent
DATASET = RAIZ / "data" / "sp156_prazos.csv"
SAIDA = RAIZ / "servico_ia" / "modelo" / "modelo_prazo.joblib"
FEATURES_CAT = ["categoria", "distrito"]
FEATURES_NUM = ["mes"]
ALVO = "dias"


def dividir(df: pd.DataFrame):
    """Mesma divisão treino/teste usada na avaliação."""
    X = df[FEATURES_CAT + FEATURES_NUM]
    y = df[ALVO]
    return train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=df["categoria"])


def main() -> None:
    df = pd.read_csv(DATASET)
    X_tr, X_te, y_tr, y_te = dividir(df)
    print(f"Treino: {len(X_tr):,} | Teste: {len(X_te):,}")

    pre = ColumnTransformer(
        [("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
          FEATURES_CAT)],
        remainder="passthrough",
    )
    modelo = Pipeline([
        ("pre", pre),
        ("reg", HistGradientBoostingRegressor(loss="absolute_error", categorical_features=[0, 1],
                                              max_iter=600, max_leaf_nodes=63,
                                              learning_rate=0.1, random_state=SEED)),
    ])
    modelo.fit(X_tr, y_tr)
    mae_modelo = mean_absolute_error(y_te, modelo.predict(X_te))

    mediana_categoria = y_tr.groupby(X_tr["categoria"]).median()
    previsto_baseline = X_te["categoria"].map(mediana_categoria).fillna(y_tr.median())
    mae_baseline = mean_absolute_error(y_te, previsto_baseline)

    print(f"MAE do modelo:   {mae_modelo:.2f} dias")
    print(f"MAE do baseline: {mae_baseline:.2f} dias (mediana por categoria)")

    artefato = {
        "modelo": modelo,
        "categorias": sorted(df["categoria"].unique()),
        "distritos": sorted(df["distrito"].unique()),
        "mediana_categoria": mediana_categoria.round(1).to_dict(),
        "metricas": {
            "mae_modelo_dias": round(mae_modelo, 2),
            "mae_baseline_dias": round(mae_baseline, 2),
            "amostras_treino": len(X_tr),
            "amostras_teste": len(X_te),
        },
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefato, SAIDA, compress=3)
    print(f"Salvo: {SAIDA.relative_to(RAIZ)} ({SAIDA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
