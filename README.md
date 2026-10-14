# Pipeline de Dados IoT — Temperature Readings

Pipeline de dados para processar leituras de temperatura de dispositivos IoT, armazená-las em PostgreSQL executado via Docker e visualizá-las em um dashboard Streamlit.

## Tecnologias

- Python
- Pandas
- SQLAlchemy
- PostgreSQL
- Docker Compose
- Streamlit
- Plotly
- Git e GitHub

## Estrutura

```text
.
├── data/
│   └── IOT-temp.csv          # CSV baixado do Kaggle (não versionado)
├── docs/
│   └── screenshots/          # Capturas do dashboard
├── sql/
│   └── views.sql             # Views analíticas no PostgreSQL
├── src/
│   ├── ingest.py             # Leitura, tratamento e carga no PostgreSQL
│   └── dashboard.py          # Dashboard Streamlit
├── .env.example
├── docker-compose.yml
└── requirements.txt
```

## Dataset

- Nome: **Temperature Readings: IoT Devices**
- Fonte: <https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices>

Baixe o arquivo CSV e salve-o como:

```text
data/IOT-temp.csv
```

O arquivo não é versionado neste repositório.

## Como executar

### 1. Clonar o repositório

```bash
git clone https://github.com/lucasouqueiroz/iot-temperature-pipeline.git
cd iot-temperature-pipeline
```

### 2. Criar o ambiente virtual

```bash
python -m venv .venv
```

Ativação no Windows:

```powershell
.venv\Scripts\activate
```

Ativação no Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Ajuste a senha do PostgreSQL em `.env`, se necessário.

### 5. Subir o PostgreSQL

```bash
docker compose up -d
```

Verifique se o contêiner está ativo:

```bash
docker ps
```

### 6. Criar as views

```bash
python src/ingest.py
```

O script cria a tabela `temperature_readings`, processa o CSV e executa o arquivo `sql/views.sql`.

### 7. Abrir o dashboard

```bash
streamlit run src/dashboard.py
```

Acesse o endereço exibido no terminal, normalmente:

```text
http://localhost:8501
```

## Views SQL

### `avg_temp_por_dispositivo`

Calcula a temperatura média por dispositivo.

```sql
CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
SELECT
    device_id,
    ROUND(AVG(temperature)::numeric, 2) AS avg_temp,
    COUNT(*) AS total_leituras
FROM temperature_readings
GROUP BY device_id;
```

### `leituras_por_hora`

Contabiliza as leituras registradas em cada hora do dia.

```sql
CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT
    EXTRACT(HOUR FROM reading_at)::int AS hora,
    COUNT(*) AS contagem
FROM temperature_readings
GROUP BY EXTRACT(HOUR FROM reading_at)
ORDER BY hora;
```

### `temp_max_min_por_dia`

Apresenta as temperaturas máxima e mínima por dia.

```sql
CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT
    DATE(reading_at) AS data,
    MAX(temperature) AS temp_max,
    MIN(temperature) AS temp_min
FROM temperature_readings
GROUP BY DATE(reading_at)
ORDER BY data;
```

## Dashboard

O dashboard apresenta:

- Média de temperatura por dispositivo;
- Volume de leituras por hora;
- Temperaturas máxima e mínima por dia.

Adicione as capturas de tela em `docs/screenshots/` e referencie-as aqui.

## Comandos Git utilizados

```bash
git clone https://github.com/lucasouqueiroz/iot-temperature-pipeline.git
git status
git add .
git commit -m "Mensagem descritiva do ajuste"
git push origin main
git pull origin main
```

## Possíveis insights

- Identificação de dispositivos com temperatura média fora do padrão;
- Detecção de horários com maior volume de leituras;
- Acompanhamento de variações diárias de temperatura;
- Suporte a alertas quando a temperatura ultrapassar limites operacionais.
