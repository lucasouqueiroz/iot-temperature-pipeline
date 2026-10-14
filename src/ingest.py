"""Pipeline de ingestão do dataset IoT de temperatura.

Lê o CSV, normaliza os dados, cria a tabela no PostgreSQL e executa as views SQL.
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

CSV_PATH = BASE_DIR / os.getenv("CSV_PATH", "data/IOT-temp.csv")

DB_USER = os.getenv("POSTGRES_USER", "iot_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "iot_password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "iot_db")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def read_csv_flexible(path: Path) -> pd.DataFrame:
    """Lê o CSV tentando identificar automaticamente o delimitador."""
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {path}. "
            "Baixe o dataset do Kaggle e salve-o em data/IOT-temp.csv."
        )

    return pd.read_csv(path, sep=None, engine="python", on_bad_lines="skip")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes de colunas e tipos essenciais."""
    df = df.copy()
    df.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    ]

    column_aliases = {
        "device_id": ["device_id", "id", "roomid", "room_id"],
        "room": ["room", "roomid", "room_id"],
        "note": ["note", "noted"],
        "reading_at": ["reading_at", "date", "datetime", "datetemp"],
        "temperature": ["temperature", "temp", "tempout", "temp_out"],
        "direction": ["direction", "in", "out"],
    }

    renamed = {}
    for target, candidates in column_aliases.items():
        for candidate in candidates:
            if candidate in df.columns and target not in renamed.values():
                renamed[candidate] = target
                break

    df = df.rename(columns=renamed)

    required = {"device_id", "reading_at", "temperature"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes após normalização: {missing}. "
            f"Colunas encontradas: {list(df.columns)}"
        )

    df["reading_at"] = pd.to_datetime(df["reading_at"], errors="coerce", dayfirst=True)
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

    df = df.dropna(subset=["reading_at", "temperature"])
    df["device_id"] = df["device_id"].astype(str)

    return df


def create_table(engine) -> None:
    """Cria a tabela principal, se ela ainda não existir."""
    ddl = """
    CREATE TABLE IF NOT EXISTS temperature_readings (
        id SERIAL PRIMARY KEY,
        device_id TEXT NOT NULL,
        room TEXT,
        note TEXT,
        reading_at TIMESTAMP NOT NULL,
        temperature NUMERIC NOT NULL,
        direction TEXT
    );
    """
    with engine.begin() as connection:
        connection.execute(text(ddl))


def create_views(engine) -> None:
    """Executa o script SQL com as views analíticas."""
    views_path = BASE_DIR / "sql" / "views.sql"
    with engine.begin() as connection:
        connection.execute(text(views_path.read_text(encoding="utf-8")))


def main() -> None:
    engine = create_engine(DATABASE_URL)

    print(f"Lendo arquivo: {CSV_PATH}")
    raw_df = read_csv_flexible(CSV_PATH)
    print(f"Linhas lidas: {len(raw_df)}")
    print(f"Colunas detectadas: {list(raw_df.columns)}")

    df = normalize_columns(raw_df)
    print(f"Linhas válidas após tratamento: {len(df)}")

    create_table(engine)
    df.to_sql(
        "temperature_readings",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    create_views(engine)
    print("Carga concluída e views criadas com sucesso.")


if __name__ == "__main__":
    main()
