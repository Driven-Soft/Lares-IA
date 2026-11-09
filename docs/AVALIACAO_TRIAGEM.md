# Avaliação da triagem

Gerado por `pipeline/avaliacao_triagem.py` com 28 descrições rotuladas
(`data/triagem_rotulada.csv`).

## Resultado

| Métrica | LLM (gpt-4.1-mini) | Regras (fallback) |
| --- | --- | --- |
| Acurácia da categoria | 100% | 96% |
| F1 macro da categoria | 1.00 | 0.96 |
| Acurácia da prioridade | 93% | 82% |
| Chamadas que falharam | 0 | — |
| Tempo médio por chamada | 1.04 s | — |

## Matriz de confusão do LLM (categoria)

| Esperado ↓ / Previsto → | BURACO | ILUMINACAO | LIXO | CALCADA | ARVORE | SINALIZACAO | OUTROS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **BURACO** | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| **ILUMINACAO** | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| **LIXO** | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| **CALCADA** | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| **ARVORE** | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| **SINALIZACAO** | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| **OUTROS** | 0 | 0 | 0 | 0 | 0 | 0 | 4 |

## Onde o LLM errou

| Descrição | Esperado | Previsto | Justificativa do LLM |
| --- | --- | --- | --- |
| sofá velho abandonado na rua | LIXO / BAIXA | LIXO / MEDIA | Sofá abandonado caracteriza descarte irregular de lixo na via pública. |
| placa de pare caida na esquina | SINALIZACAO / ALTA | SINALIZACAO / MEDIA | Placa de pare caída é problema de sinalização que atrapalha o trânsito. |

## Matriz de confusão das regras (categoria)

| Esperado ↓ / Previsto → | BURACO | ILUMINACAO | LIXO | CALCADA | ARVORE | SINALIZACAO | OUTROS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **BURACO** | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| **ILUMINACAO** | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| **LIXO** | 0 | 0 | 3 | 0 | 0 | 0 | 1 |
| **CALCADA** | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| **ARVORE** | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| **SINALIZACAO** | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| **OUTROS** | 0 | 0 | 0 | 0 | 0 | 0 | 4 |

## Casos de falha (chamando a API)

| Caso | HTTP | Categoria | Prioridade | Origem |
| --- | --- | --- | --- | --- |
| Texto vazio | 422 | — | — | — |
| Texto acima de 500 caracteres | 422 | — | — | — |
| Pedido sem relação | 200 | OUTROS | BAIXA | llm |
| Texto ofensivo | 200 | OUTROS | BAIXA | llm |
| Tentativa de manipular o prompt | 200 | OUTROS | BAIXA | llm |
| LLM indisponível (chave inválida) | 200 | ILUMINACAO | MEDIA | fallback |

## Limitações

- A `confianca` vem do próprio LLM: é uma autoavaliação, não uma probabilidade calibrada.
- O LLM pode errar a categoria em relatos ambíguos (ex.: raiz de árvore quebrando a calçada);
  o gestor pode corrigir a categoria no app.
- As regras de fallback só reconhecem as palavras-chave da lista; relatos sem elas viram OUTROS.
- O serviço depende da OpenAI: sem ela, a triagem continua, mas com a qualidade das regras.
