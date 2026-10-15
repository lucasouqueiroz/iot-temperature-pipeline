"""Dashboard das views PostgreSQL; os grupos nao representam sensores fisicos."""
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text
from ingest import get_engine

st.set_page_config(page_title='Temperaturas IoT', layout='wide')
st.title('Monitoramento de temperaturas IoT')
st.caption('CSV Kaggle → Python → PostgreSQL no Docker → views SQL → Streamlit')
st.info('Sala + In/Out define um grupo de leitura, nao um sensor fisico identificado. Analise historica em lote, nao monitoramento em tempo real.')

@st.cache_resource
def database():
    return get_engine()

@st.cache_data(ttl=60)
def load_view(name):
    allowed = {'avg_temp_por_dispositivo', 'leituras_por_hora', 'temp_max_min_por_dia'}
    if name not in allowed:
        raise ValueError('View nao permitida')
    with database().connect() as connection:
        return pd.read_sql_query(text(f'SELECT * FROM {name}'), connection)

if st.sidebar.button('Atualizar dados'):
    st.cache_data.clear()

try:
    avg = load_view('avg_temp_por_dispositivo')
    hour = load_view('leituras_por_hora').sort_values('hora')
    daily = load_view('temp_max_min_por_dia').sort_values('data')
    if avg.empty or daily.empty:
        st.warning('Banco sem leituras. Execute python src/ingest.py.')
        st.stop()
    a, b, c = st.columns(3)
    a.metric('Grupos de leitura', len(avg))
    b.metric('Leituras unicas', f"{int(avg.total_leituras.sum()):,}")
    c.metric('Dias com leituras', len(daily))
    st.header('Media de temperatura por sala e classificacao')
    st.plotly_chart(px.bar(avg, x='device_id', y='avg_temp', color='device_id', labels={'device_id': 'Grupo de leitura', 'avg_temp': 'Temperatura media'}), use_container_width=True)
    st.header('Volume de leituras por hora do dia')
    st.caption('Agregacao por hora (0–23) de todo o periodo; nao e uma serie cronologica continua.')
    st.plotly_chart(px.line(hour, x='hora', y='contagem', markers=True, labels={'hora': 'Hora do dia', 'contagem': 'Leituras'}), use_container_width=True)
    st.header('Temperaturas maxima e minima por dia')
    st.plotly_chart(px.line(daily, x='data', y=['temp_max', 'temp_min'], labels={'data': 'Data', 'value': 'Temperatura', 'variable': 'Metrica'}), use_container_width=True)
    with st.expander('Dados agregados e exportacao'):
        for name, frame in [('medias', avg), ('horas', hour), ('dias', daily)]:
            st.dataframe(frame, use_container_width=True)
            st.download_button(f'Baixar {name}', frame.to_csv(index=False).encode('utf-8'), file_name=f'{name}.csv', mime='text/csv')
except Exception:
    st.error('Nao foi possivel consultar as views. Confira .env, saude do container e execute a ingestao. Consulte o terminal para detalhes locais.')
    import logging
    logging.exception('Falha ao consultar PostgreSQL')
