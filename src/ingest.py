"""Carga integral, validada e transacional do CSV IoT."""
import argparse
import logging
import math
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / '.env')

def get_engine():
    password = os.getenv('POSTGRES_PASSWORD')
    if not password:
        raise ValueError('Configure POSTGRES_PASSWORD no arquivo .env')
    url = URL.create('postgresql+psycopg2', username=os.getenv('POSTGRES_USER', 'iot_user'), password=password, host=os.getenv('POSTGRES_HOST', 'localhost'), port=int(os.getenv('POSTGRES_PORT', '5432')), database=os.getenv('POSTGRES_DB', 'iot_db'))
    return create_engine(url, pool_pre_ping=True, connect_args={'connect_timeout': 10})

def normalize_columns(df):
    required = {'id', 'room_id/id', 'noted_date', 'temp', 'out/in'}
    if required - set(df.columns):
        raise ValueError(f'Colunas ausentes: {sorted(required - set(df.columns))}')
    df = df[list(sorted(required))].copy()
    if df.isna().any().any():
        raise ValueError('Campos nulos no CSV')
    for column in ['id', 'room_id/id', 'out/in']:
        df[column] = df[column].astype(str).str.strip()
        if df[column].eq('').any():
            raise ValueError(f'Campo vazio: {column}')
    df = df.drop_duplicates()
    if df['id'].duplicated().any():
        raise ValueError('Mesmo ID com valores conflitantes')
    result = df.rename(columns={'id': 'source_id', 'room_id/id': 'room', 'noted_date': 'reading_at', 'temp': 'temperature', 'out/in': 'direction'})
    result['reading_at'] = pd.to_datetime(result['reading_at'], format='%d-%m-%Y %H:%M', errors='raise')
    result['temperature'] = pd.to_numeric(result['temperature'], errors='raise')
    if not result['temperature'].map(math.isfinite).all():
        raise ValueError('Temperatura nao finita')
    if not result['direction'].isin(['In', 'Out']).all():
        raise ValueError('Classificacao diferente de In/Out')
    result['device_id'] = result['room'] + ' / ' + result['direction']
    if result.empty:
        raise ValueError('CSV sem leituras')
    return result[['source_id', 'device_id', 'room', 'reading_at', 'temperature', 'direction']]

def load_database(df, engine):
    # Altera somente a tabela dedicada a este projeto. DELETE e carga sao atomicos.
    with engine.begin() as connection:
        connection.execute(text('SELECT pg_advisory_xact_lock(704210)'))
        connection.execute(text('CREATE TABLE IF NOT EXISTS temperature_readings (id BIGSERIAL PRIMARY KEY, source_id TEXT, device_id TEXT NOT NULL, room TEXT, reading_at TIMESTAMP NOT NULL, temperature NUMERIC NOT NULL, direction TEXT)'))
        connection.execute(text('ALTER TABLE temperature_readings ADD COLUMN IF NOT EXISTS source_id TEXT'))
        connection.execute(text('DELETE FROM temperature_readings'))
        connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ux_iot_source ON temperature_readings(source_id)'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS ix_iot_reading_at ON temperature_readings(reading_at)'))
        df.to_sql('temperature_readings', connection, if_exists='append', index=False, method='multi', chunksize=1000)
        sql = (BASE_DIR / 'sql' / 'views.sql').read_text(encoding='utf-8')
        for statement in sql.split(';'):
            if statement.strip():
                connection.execute(text(statement))
        count = connection.execute(text('SELECT COUNT(*) FROM temperature_readings')).scalar_one()
        hourly = connection.execute(text('SELECT SUM(contagem) FROM leituras_por_hora')).scalar_one()
        grouped = connection.execute(text('SELECT SUM(total_leituras) FROM avg_temp_por_dispositivo')).scalar_one()
        if count != len(df) or hourly != count or grouped != count:
            raise ValueError('Contagens inconsistentes; carga sera revertida')
    return count

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true', help='Valida CSV sem acessar PostgreSQL')
    args = parser.parse_args()
    path = Path(os.getenv('CSV_PATH', 'data/IOT-temp.csv'))
    if not path.is_absolute():
        path = BASE_DIR / path
    raw = pd.read_csv(path, sep=',', encoding='utf-8-sig')
    df = normalize_columns(raw)
    logging.info('Originais=%s; unicas=%s; duplicatas exatas removidas=%s', len(raw), len(df), len(raw) - len(df))
    logging.info('Periodo: %s a %s', df.reading_at.min(), df.reading_at.max())
    logging.info('Resumo por classificacao:\n%s', df.groupby('direction').temperature.agg(['count', 'mean', 'min', 'max']).to_string())
    if not args.validate_only:
        engine = get_engine()
        try:
            count = load_database(df, engine)
            logging.info('Carga confirmada: %s leituras; views e contagens validadas.', count)
        finally:
            engine.dispose()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()
