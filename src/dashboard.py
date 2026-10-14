"""Dashboard Streamlit para leituras de temperatura IoT."""

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("POSTGRES_USER", "iot_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "iot_password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "iot_db")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


@st.cache_data(ttl=300)
def load_data(view_name: str) -> pd.DataFrame:
    """Carrega dados de uma view do PostgreSQL."""
    engine = create_engine(DATABASE_URL)
    return pd.read_sql(f"SELECT * FROM {view_name}", engine)


st.set_page_config(page_title="Dashboard de Temperaturas IoT", layout="wide")
st.title("Dashboard de Temperaturas IoT")
st.caption("Pipeline com Python, PostgreSQL, Docker e Streamlit")

try:
    df_avg = load_data("avg_temp_por_dispositivo")
    df_hour = load_data("leituras_por_hora")
    df_daily = load_data("temp_max_min_por_dia")

    col1, col2, col3 = st.columns(3)
    col1.metric("Dispositivos", int(df_avg["device_id"].nunique()))
    col2.metric("Total de leituras", int(df_avg["total_leituras"].sum()))
    col3.metric("Dias analisados", int(df_daily["data"].nunique()))

    st.header("Média de temperatura por dispositivo")
    fig_avg = px.bar(
        df_avg.sort_values("avg_temp", ascending=False),
        x="device_id",
        y="avg_temp",
        color="avg_temp",
        labels={"device_id": "Dispositivo", "avg_temp": "Temperatura média"},
    )
    st.plotly_chart(fig_avg, use_container_width=True)

    st.header("Leituras por hora do dia")
    fig_hour = px.line(
        df_hour,
        x="hora",
        y="contagem",
        markers=True,
        labels={"hora": "Hora", "contagem": "Leituras"},
    )
    st.plotly_chart(fig_hour, use_container_width=True)

    st.header("Temperaturas máxima e mínima por dia")
    fig_daily = px.line(
        df_daily,
        x="data",
        y=["temp_max", "temp_min"],
        labels={"data": "Data", "value": "Temperatura", "variable": "Métrica"},
    )
    st.plotly_chart(fig_daily, use_container_width=True)

    with st.expander("Ver dados agregados"):
        st.subheader("Média por dispositivo")
        st.dataframe(df_avg)
        st.subheader("Leituras por hora")
        st.dataframe(df_hour)
        st.subheader("Máximas e mínimas por dia")
        st.dataframe(df_daily)

except Exception as error:
    st.error("Não foi possível carregar os dados do PostgreSQL.")
    st.exception(error)
    st.info(
        "Verifique se o Docker está ativo, execute `docker compose up -d` "
        "e rode `python src/ingest.py` antes de abrir o dashboard."
    )
