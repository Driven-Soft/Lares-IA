# Avaliação do modelo de prazo

Gerado por `pipeline/avaliacao_modelo.py` com os dados do SP156 de 2025
(solicitações finalizadas de zeladoria, de 0 a 365 dias).

## Resultado geral

| Métrica | Valor |
| --- | --- |
| Amostras de treino | 340,812 |
| Amostras de teste | 85,204 |
| MAE do modelo | 16.55 dias |
| MAE do baseline (mediana por categoria) | 18.23 dias |
| Ganho sobre o baseline | 9% |
| Acerto em até 7 dias | 69% |

## Por categoria

| Categoria | Amostras de teste | MAE modelo (dias) | MAE baseline (dias) | Acerto em até 7 dias |
| --- | --- | --- | --- | --- |
| ARVORE | 18125 | 45.8 | 52.1 | 22% |
| BURACO | 22654 | 12.7 | 13.5 | 64% |
| CALCADA | 1675 | 54.9 | 56.3 | 12% |
| LIXO | 41227 | 3.8 | 3.9 | 98% |
| SINALIZACAO | 1523 | 29.3 | 30.3 | 26% |

## Mesmo problema, distritos diferentes (abertura em novembro)

Prazo estimado, em dias, nos três distritos com mais solicitações:

| Categoria | JABAQUARA | CAPAO REDONDO | ITAQUERA |
| --- | --- | --- | --- |
| ARVORE | 6 | 29 | 79 |
| BURACO | 4 | 7 | 5 |
| CALCADA | 11 | 26 | 40 |
| LIXO | 1 | 1 | 2 |
| SINALIZACAO | 19 | 10 | 25 |

## Limitações

- O modelo só conhece o que o SP156 registra: categoria, distrito e data. Não vê a gravidade
  descrita pelo cidadão nem a fila atual de cada equipe.
- O bairro digitado no app só é usado quando tem o mesmo nome de um distrito oficial; senão,
  o modelo estima só com a categoria e o mês.
- O mapeamento dos serviços do SP156 para as categorias do Lares é por palavra-chave
  (ver `data/mapeamento_servicos.csv`).
- Os dados são de São Paulo; em outra cidade, o modelo precisaria ser treinado de novo.
