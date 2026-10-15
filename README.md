# Pipeline de temperaturas IoT

Projeto academico de Disruptive Architectures: IoT, Big Data e IA. Ingestao em lote de leituras historicas, validacao, armazenamento PostgreSQL no Docker e visualizacao Streamlit/Plotly. Nao implementa IA, streaming nem conexao com sensores em tempo real: esses componentes nao sao exigidos no desafio pratico.

## Arquitetura e arquivos

CSV Kaggle → pandas (validacao e deduplicacao) → SQLAlchemy/psycopg2 → PostgreSQL → tres views SQL → Streamlit/Plotly.

- src/ingest.py: validacao e carga integral transacional.
- src/dashboard.py: tres visualizacoes, indicadores e exportacao de agregados.
- sql/views.sql: consultas analiticas.
- tests/test_ingest.py: testes unitarios sem banco.
- data/: CSV local, nao versionado.
- docs/: checklist, roteiro e evidencias a adicionar.

## Fonte e semantica

Temperature Readings: IoT Devices: https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices

Baixe o CSV para data/IOT-temp.csv. Respeite os termos da fonte antes de redistribuir a base. Colunas: id, room_id/id, noted_date, temp, out/in. id identifica uma leitura, nao um sensor. device_id e um campo derivado de sala + In/Out por compatibilidade com as views; nao conta dispositivos fisicos. Datas sao interpretadas estritamente como dia-mes-ano hora:minuto, sem inventar fuso horario.

## Execucao no Windows / PowerShell

Use Python 3.11 ou 3.12, Git e Docker Desktop em execucao, com Docker Compose disponivel.

```powershell
git clone https://github.com/lucasouqueiroz/iot-temperature-pipeline.git
cd iot-temperature-pipeline
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se ja clonou, salve suas alteracoes e execute git pull --ff-only em vez de clonar outra vez. Edite .env e defina POSTGRES_PASSWORD; nunca publique esse arquivo. A senha do exemplo e apenas demonstrativa. Coloque o CSV em data/IOT-temp.csv. Os comandos abaixo dispensam ativacao do venv e alteracao da politica do PowerShell.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe src/ingest.py --validate-only
docker compose up -d --wait
.\.venv\Scripts\python.exe src/ingest.py
.\.venv\Scripts\python.exe -m streamlit run src/dashboard.py
```

Abra http://localhost:8501. Apos nova carga, clique em Atualizar dados. Linux/macOS: substitua .\.venv\Scripts\python.exe por .venv/bin/python.

## Qualidade e seguranca da carga

A validacao rejeita campos nulos/vazios, datas invalidas, temperaturas nao finitas, classificacoes fora de In/Out e IDs conflitantes. Remove apenas duplicatas exatas. Nao imputa valores nem elimina temperaturas extremas arbitrariamente.

ATENCAO: a carga substitui integralmente temperature_readings neste banco dedicado. DELETE, insercao, criacao das views e verificacao de contagens ocorrem na mesma transacao; falhas revertem a operacao. Reexecutar nao acumula leituras. Nao aponte este projeto para tabelas de producao. source_id tem indice unico; reading_at tem indice para consultas futuras. Um bloqueio transacional serializa cargas simultaneas.

## Views e interpretacao

1. avg_temp_por_dispositivo: media e quantidade por grupo sala/classificacao. Identifica diferencas entre grupos, nao necessariamente sensores.
2. leituras_por_hora: soma por hora do dia em todo o periodo. Mede volume de coleta, nao taxa de falhas nem temperatura media por hora.
3. temp_max_min_por_dia: extremos diarios combinando grupos. Mostra variacao observada; isoladamente nao comprova defeito ou causa ambiental.

As contagens das duas primeiras views devem coincidir com a tabela. Nao compare uma media simples das medias de grupos com a media geral: tamanhos dos grupos diferem.

## Resultados do CSV fornecido

Analise direta do arquivo anexado durante o desenvolvimento (ainda nao e evidencia de execucao no PostgreSQL local): 97.606 linhas originais; uma duplicata exata; 97.605 leituras unicas; periodo de 28/07/2018 07:06 a 08/12/2018 09:30.

Apos deduplicacao: In tem 20.345 leituras, media aproximada 30,45 e faixa 21–41; Out tem 77.260 leituras, media aproximada 36,27 e faixa 24–51. A diferenca observada das medias e aproximadamente 5,81. Nao e uma comparacao pareada por instante: horarios e volumes de amostragem podem diferir.

Uso pratico: explorar diferencas entre classificacoes, horarios de coleta e extremos para apoiar investigacoes. Limites de alerta devem ser definidos pelo contexto real; o projeto nao afirma anomalias somente com base nesses numeros.

## Validacao local e evidencias

Execute a ingestao duas vezes; ambas devem informar 97.605 leituras para este CSV. O script verifica automaticamente a tabela e as somas das views antes de confirmar a transacao. Para conferir manualmente:

```powershell
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) FROM temperature_readings;"'
```

Salve prints reais em docs/screenshots/: visao geral, medias, horas e extremos diarios. Adicione as imagens ao README somente apos gera-las. Nao ha screenshots nem PDF final incluidos nesta etapa. Consulte docs/entrega.md.

## Diagnostico

- Arquivo ausente: confirme data/IOT-temp.csv e CSV_PATH.
- Banco indisponivel: docker compose ps e docker compose logs postgres.
- Porta ocupada: altere POSTGRES_PORT no .env e recrie o servico com docker compose up -d --wait.
- Senha alterada com volume existente: a variavel de inicializacao nao muda automaticamente a senha ja gravada no banco; use a senha original ou altere-a via SQL. Nao apague volumes sem aceitar perder os dados.
- Parar sem apagar dados: docker compose down.
- Dependencias: confirme o interpretador do venv e execute pip check com esse interpretador.

## Git e autoria

```powershell
git status
git add src docs README.md
git commit -m "Valida pipeline local e adiciona evidencias"
git push origin main
git pull --ff-only
```

O repositorio foi inicialmente criado remotamente; git init e usado para iniciar um repositorio novo e nao deve ser executado novamente para este clone. Documente somente comandos realmente utilizados. Verifique user.name e user.email antes de seus commits. Nao use git add -f para incluir .env ou CSV.

## Estado de validacao

Tratamento do CSV verificado durante o desenvolvimento. Testes unitarios incluidos para execucao local. Integracao PostgreSQL/Docker e renderizacao do dashboard precisam ser comprovadas no ambiente do aluno; nao sao declaradas aprovadas antecipadamente.
