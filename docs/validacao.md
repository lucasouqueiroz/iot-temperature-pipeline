# Registro de validação local

Data: 14/10/2026. Execução: Lucas Queiroz. Resultados registrados com base nos logs e capturas fornecidos pelo aluno, não em execução remota do assistente.

## Integração

PostgreSQL 16 iniciou saudável no Docker. A carga processou 97.606 linhas, removeu uma duplicata exata e confirmou 97.605 leituras únicas. O script verificou o total da tabela e as somas das views de médias e volume por hora. O Streamlit apresentou indicadores e três gráficos.

## Testes unitários

Comando: .\.venv\Scripts\python.exe -m unittest discover -s tests -v

Resultado: Ran 5 tests in 0.049s; OK.

- test_conflicting_id: aprovado.
- test_exact_duplicates: aprovado.
- test_invalid_direction: aprovado.
- test_missing_column: aprovado.
- test_normalization: aprovado.

## Recarga

Nova execução de src/ingest.py manteve 97.605 leituras. Confirma ausência de acúmulo na recarga observada. Não equivale a cobertura de todos os modos de falha.

## Evidências

- [Docker](screenshots/docker.png)
- [Indicadores e médias](screenshots/dashboard-medias.png)
- [Horas e extremos](screenshots/dashboard-horas-extremos.png)
- [Primeira execução](screenshots/execucao-pipeline.png)
- [Testes e segunda carga](screenshots/testes-e-recarga.png)

## Limites

Não foram executados testes de desempenho, concorrência ou injeção de falha para rollback. Transação e bloqueio foram verificados no código. Os grupos analíticos não são identificadores comprovados de sensores físicos. PDF e vídeo continuam pendentes.
