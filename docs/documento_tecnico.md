# Pipeline de Dados com IoT, Docker, PostgreSQL e Streamlit

**Disruptive Architectures: IoT, Big Data e IA**
Processamento, armazenamento e visualização de leituras históricas de temperatura

- **Aluno:** Lucas Queiroz
- **Curso / turma / professor(a) / RA:** [PREENCHER]
- **Data:** São Paulo, 14 de outubro de 2026
- **Repositório:** https://github.com/lucasouqueiroz/iot-temperature-pipeline
- **Vídeo pitch:** [PREENCHER: link do YouTube]

---

## Sumário

1. Contextualização do projeto
2. Arquitetura e tecnologias
3. Base de dados
4. Passos realizados
5. Views SQL
6. Dashboard no Streamlit
7. Resultados e principais insights
8. Aplicações práticas em ambiente real
9. Limitações e melhorias futuras
10. Conclusão
11. Links da entrega

---

## 1. Contextualização do projeto

Dispositivos de Internet das Coisas (IoT) geram continuamente grandes volumes de leituras de sensores. Quando esses registros ficam apenas em arquivos soltos, torna-se difícil consultá-los, validar sua qualidade e transformá-los em informação útil para decisões. O problema tratado neste trabalho é: como organizar um fluxo simples, reproduzível e confiável que receba leituras de temperatura, as valide, as armazene em um banco de dados relacional e as apresente de forma visual?

A proposta é um pipeline de dados em lote. Um arquivo CSV com leituras de temperatura é lido por um script Python, validado e carregado em um banco PostgreSQL executado em um contêiner Docker. Sobre a tabela carregada foram criadas três views SQL, que alimentam um dashboard interativo construído com Streamlit e Plotly.

O projeto atende à proposta da disciplina de integrar conceitos de IoT, Big Data e automação com ferramentas modernas de ingestão, armazenamento e análise. Trata-se de uma análise histórica em lote: não há ligação com sensores em tempo real, streaming nem modelo de inteligência artificial, itens que não eram exigidos pelo desafio prático.

## 2. Arquitetura e tecnologias

O fluxo de dados segue as etapas abaixo:

```text
CSV (Kaggle)  ->  Python/pandas (validação e deduplicação)  ->  SQLAlchemy/psycopg2
     ->  PostgreSQL 16 em contêiner Docker  ->  3 views SQL  ->  Streamlit + Plotly
```

| Tecnologia | Papel no projeto |
|---|---|
| Python e pandas | Leitura do CSV, validação, tratamento de tipos e remoção de duplicatas exatas |
| SQLAlchemy e psycopg2 | Conexão com o PostgreSQL e inserção dos dados |
| PostgreSQL 16 | Armazenamento relacional das leituras e criação das views |
| Docker e Docker Compose | Execução reprodutível do banco em contêiner, com volume persistente e verificação de saúde |
| Streamlit e Plotly | Dashboard web interativo com indicadores e gráficos |
| Git e GitHub | Controle de versão e publicação do código, da documentação e das evidências |
| unittest | Cinco testes unitários da etapa de validação e normalização |

O repositório foi organizado em pastas: `src` (scripts de ingestão e dashboard), `sql` (views), `tests` (testes unitários), `data` (CSV local, não versionado) e `docs` (documentação e capturas de tela).

## 3. Base de dados

Foi utilizado o conjunto de dados público "Temperature Readings: IoT Devices", disponível no Kaggle (autor atulanandjha): https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices. O arquivo possui cinco colunas, convertidas para o modelo do projeto conforme a tabela:

| Coluna original | Coluna no banco | Interpretação |
|---|---|---|
| `id` | `source_id` | Identificador da leitura |
| `room_id/id` | `room` | Sala ou local informado |
| `noted_date` | `reading_at` | Data e hora (formato dia-mês-ano hora:minuto) |
| `temp` | `temperature` | Valor numérico da temperatura |
| `out/in` | `direction` | Classificação In ou Out |
| (derivada) | `device_id` | Combinação de sala + classificação (ex.: "Room Admin / In") |

**Observação importante:** a base não traz um identificador explícito de sensor físico. Por isso, o campo `device_id` foi derivado da combinação entre a sala e a classificação In/Out e deve ser entendido como um grupo de leitura, e não como a comprovação de dois dispositivos físicos distintos. O nome técnico foi mantido por compatibilidade com o exemplo do enunciado e com as views. Também não foi atribuído fuso horário às datas, pois ele não é informado no arquivo.

## 4. Passos realizados

### 4.1 Configuração do ambiente e do Git

O desenvolvimento foi feito no Windows com VS Code, Python 3.11 e ambiente virtual (venv). O Git foi instalado e o repositório público foi criado no GitHub e clonado para a máquina local. Os commits seguintes foram realizados pelo próprio aluno, a partir do VS Code. As dependências do projeto foram instaladas com pip a partir do arquivo `requirements.txt` (pandas, SQLAlchemy, psycopg2-binary, Streamlit, Plotly e python-dotenv).

As credenciais do banco ficam em um arquivo `.env` local, ignorado pelo Git. O repositório contém apenas o modelo `.env.example`, sem senha real.

### 4.2 Criação do contêiner PostgreSQL no Docker

O banco foi definido em um arquivo `docker-compose.yml`, com imagem `postgres:16`, contêiner chamado `postgres-iot`, volume persistente, porta publicada somente na interface local (`127.0.0.1:5432`) e verificação de saúde (healthcheck). Para o Docker Desktop funcionar no Windows foi necessário concluir a instalação do WSL 2, pré-requisito do mecanismo Linux. O contêiner foi iniciado com:

```powershell
docker compose up -d --wait
docker compose ps
```

O resultado foi o contêiner `postgres-iot` com status "healthy".

**[docker.png]**
*Figura 1 – Docker Desktop com o projeto iot-temperature-pipeline em execução*

**[execucao-pipeline.png]**
*Figura 2 – Terminal: contêiner PostgreSQL saudável, carga confirmada e inicialização do Streamlit*

### 4.3 Leitura, validação e inserção dos dados

O script `src/ingest.py` lê o CSV (separado por vírgulas) e executa as seguintes verificações antes de gravar no banco: presença das colunas obrigatórias; ausência de campos nulos ou vazios; conversão estrita de datas no formato dia-mês-ano hora:minuto; temperaturas numéricas e finitas; classificação restrita a In ou Out; e inexistência de um mesmo identificador com valores conflitantes. Apenas duplicatas exatas são removidas, sem imputação de valores nem descarte arbitrário de temperaturas extremas.

A carga é feita por meio do SQLAlchemy, em uma única transação que reúne: o bloqueio de concorrência, a substituição integral da tabela `temperature_readings` (DELETE seguido de inserção), a criação das views e a conferência das quantidades. Se a contagem da tabela divergir das somas das views, a transação é revertida. A tabela possui índice único em `source_id` e índice em `reading_at`. Por substituir a tabela, a carga não acumula registros quando executada novamente e deve ser usada apenas no banco dedicado ao projeto.

Resultado da execução: 97.606 registros no arquivo original, uma duplicata exata removida e 97.605 leituras únicas, no período de 28/07/2018 07:06 a 08/12/2018 09:30. O script confirmou a carga e a consistência das contagens.

| Etapa | Resultado observado |
|---|---|
| Registros originais | 97.606 |
| Duplicatas exatas removidas | 1 |
| Leituras únicas carregadas | 97.605 |
| Período | 28/07/2018 07:06 a 08/12/2018 09:30 |
| Conferência pelo script | Contagens da tabela e das views validadas |

### 4.4 Testes e recarga

Foram implementados cinco testes unitários da etapa de normalização: normalização correta de colunas e datas, remoção de duplicatas exatas, rejeição de identificador conflitante, rejeição de classificação inválida e rejeição de coluna ausente. Todos foram aprovados (`Ran 5 tests`, `OK`). Em seguida, a ingestão foi executada uma segunda vez e manteve 97.605 leituras, confirmando que a recarga não acumula registros.

Esses testes cobrem a etapa de transformação dos dados. Não foram realizados testes de desempenho, de concorrência nem de injeção de falhas para demonstrar experimentalmente a reversão da transação.

**[testes-e-recarga.png]**
*Figura 3 – Cinco testes unitários aprovados e segunda carga mantendo 97.605 leituras*

## 5. Views SQL

Foram criadas três views no PostgreSQL, conforme solicitado. O código completo está no arquivo `sql/views.sql` do repositório.

### 5.1 View `avg_temp_por_dispositivo`

```sql
CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
SELECT device_id,
       ROUND(AVG(temperature)::numeric, 2) AS avg_temp,
       COUNT(*) AS total_leituras
FROM temperature_readings
GROUP BY device_id;
```

**Propósito:** comparar a temperatura média e o volume de leituras entre os grupos de leitura (sala + classificação In/Out). Ela permite identificar rapidamente se um grupo opera em patamar térmico diferente de outro. Como os grupos têm tamanhos distintos, a média geral não deve ser calculada como média simples das médias dos grupos.

### 5.2 View `leituras_por_hora`

```sql
CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT EXTRACT(HOUR FROM reading_at)::int AS hora,
       COUNT(*) AS contagem
FROM temperature_readings
GROUP BY EXTRACT(HOUR FROM reading_at)
ORDER BY hora;
```

**Propósito:** mostrar como o volume de leituras se distribui pelas horas do dia (0 a 23), somando todo o período. Ela mede o volume de coleta, e não a temperatura nem a taxa de falhas. É útil para entender o comportamento da coleta e planejar rotinas de processamento ou monitoramento.

### 5.3 View `temp_max_min_por_dia`

```sql
CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT DATE(reading_at) AS data,
       MAX(temperature) AS temp_max,
       MIN(temperature) AS temp_min
FROM temperature_readings
GROUP BY DATE(reading_at)
ORDER BY data;
```

**Propósito:** acompanhar a variação diária da temperatura por meio dos valores máximo e mínimo de cada dia, combinando os grupos de leitura. Ela ajuda a observar tendências e dias com amplitude térmica elevada. No gráfico, a linha conecta apenas os dias que possuem registro; o dashboard indicou 86 dias com leituras, que não são necessariamente consecutivos.

## 6. Dashboard no Streamlit

O dashboard consulta diretamente as três views e apresenta indicadores e gráficos interativos construídos com Plotly. O botão "Atualizar dados" limpa o cache após uma nova carga, e a seção de dados agregados permite baixar os resultados em CSV. Um aviso na tela informa que o agrupamento sala + In/Out não representa um sensor físico identificado.

Indicadores exibidos na execução: 2 grupos de leitura, 97.605 leituras únicas e 86 dias com leituras.

### 6.1 Indicadores e média de temperatura por grupo

**[dashboard-medias.png]**
*Figura 4 – Indicadores e gráfico de média de temperatura por sala e classificação*

O gráfico de barras compara a média dos dois grupos: Room Admin / In (aproximadamente 30,45) e Room Admin / Out (aproximadamente 36,27).

### 6.2 Volume de leituras por hora e extremos diários

**[dashboard-horas-extremos.png]**
*Figura 5 – Volume de leituras por hora do dia e temperaturas máxima e mínima por dia*

O gráfico de linha por hora agrega todo o período e mostra a distribuição do volume de coleta ao longo do dia. O gráfico de temperaturas máxima e mínima por dia apresenta a evolução diária dos extremos ao longo dos meses registrados.

## 7. Resultados e principais insights

Após a deduplicação, a classificação das leituras apresentou o seguinte resumo:

| Classificação | Leituras | Média | Mínimo | Máximo |
|---|---:|---:|---:|---:|
| In | 20.345 | 30,45 | 21 | 41 |
| Out | 77.260 | 36,27 | 24 | 51 |

- A classificação Out concentra cerca de 79% das leituras (77.260 de 97.605), enquanto In reúne cerca de 21%.
- A média de Out (36,27) é aproximadamente 5,81 maior que a de In (30,45), e a faixa de valores de Out também alcança patamares mais altos (máximo de 51 contra 41).
- Pelo gráfico de extremos diários, as temperaturas máximas se mantêm em patamar mais baixo no início do período e passam a níveis mais altos a partir de meados de setembro, como observado visualmente no dashboard.
- O volume de leituras por hora não é uniforme: no gráfico há um pico por volta das 14 horas e volumes menores em alguns horários da madrugada e da manhã. Esses valores foram lidos visualmente no gráfico e são aproximados.

**Cuidados na interpretação:** a diferença entre as médias é descritiva. Os grupos têm volumes e possivelmente horários de amostragem diferentes, e a comparação não é pareada por instante, portanto não se pode afirmar que a classificação seja a causa da diferença. Do mesmo modo, um volume menor de leituras em determinada hora não comprova, por si só, falha de coleta.

## 8. Aplicações práticas em ambiente real

- Monitoramento de ambientes sensíveis (salas de servidores, laboratórios, câmaras de armazenamento): comparar grupos de medição e acompanhar extremos diários para apoiar a investigação de desvios.
- Definição de limites de alerta: os extremos diários e as diferenças entre grupos ajudam a calibrar faixas de temperatura aceitáveis, que devem ser definidas conforme o contexto operacional.
- Planejamento da coleta e da infraestrutura: o perfil de volume por hora auxilia no dimensionamento de rotinas de ingestão e na análise da cobertura dos dados.
- Base para evolução arquitetural: a mesma estrutura pode receber ingestão incremental, orquestração das cargas e automação de relatórios.

## 9. Limitações e melhorias futuras

- A análise é histórica e em lote; não há dados em tempo real nem streaming.
- Não há identificador explícito de sensor físico no arquivo; os grupos são derivados de sala e classificação.
- O fuso horário das leituras não é informado.
- A carga substitui toda a tabela do projeto; em um cenário real seria adequada uma ingestão incremental com controle de versões dos dados.
- Os testes automatizados cobrem a transformação dos dados; não cobrem desempenho, concorrência nem falhas de infraestrutura.
- O projeto não implementa modelos de inteligência artificial. Como evolução, os dados poderiam alimentar detecção de anomalias e alertas automáticos.

## 10. Conclusão

O trabalho entregou um pipeline completo e reproduzível: um CSV real de leituras de temperatura foi validado em Python, armazenado em um PostgreSQL executado no Docker, consultado por três views SQL e apresentado em um dashboard interativo no Streamlit. A execução local foi comprovada pelas evidências deste documento: contêiner saudável, carga de 97.605 leituras únicas com conferência das contagens, cinco testes unitários aprovados e recarga sem acúmulo de registros.

Além do cumprimento técnico do desafio, o projeto destacou boas práticas de engenharia de dados: validação antes da carga, segredos fora do repositório, operações transacionais, documentação de limitações e interpretação cuidadosa dos resultados.

## 11. Links da entrega

| Item | Link |
|---|---|
| Repositório público no GitHub | https://github.com/lucasouqueiroz/iot-temperature-pipeline |
| Base de dados (Kaggle) | https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices |
| Vídeo pitch (até 4 minutos) | [PREENCHER: link do YouTube - público ou não listado] |

---

## Apêndice – Guia das fotos a anexar

Substitua cada marcação pela imagem correspondente e apague este apêndice antes de exportar o PDF.

| Marcação no texto | Seção | O que deve aparecer |
|---|---|---|
| **[docker.png]** | 4.2 | Tela do Docker Desktop com o contêiner do projeto em execução |
| **[execucao-pipeline.png]** | 4.2 | Terminal com docker compose, carga confirmada e Streamlit iniciado |
| **[testes-e-recarga.png]** | 4.4 | Cinco testes aprovados e segunda carga com 97.605 leituras |
| **[dashboard-medias.png]** | 6.1 | Indicadores e gráfico de médias por grupo |
| **[dashboard-horas-extremos.png]** | 6.2 | Gráficos de volume por hora e extremos diários |
