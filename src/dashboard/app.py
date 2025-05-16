import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Jurimetria - Assédio Moral",
    page_icon="⚖️",
    layout="wide"
)

# Título do dashboard
st.title("Análise Jurimétrica de Assédio Moral na Justiça do Trabalho")

# Carrega os dados processados
@st.cache_data
def load_data():
    data_path = Path(__file__).parent.parent.parent / "data" / "processed" / "processed_decisions.csv"
    return pd.read_csv(data_path)

try:
    df = load_data()
    
    # Sidebar com filtros
    st.sidebar.header("Filtros")
    
    # Filtro por tribunal
    tribunais = df['tribunal'].unique()
    tribunal_selecionado = st.sidebar.multiselect(
        "Selecione o(s) Tribunal(is)",
        tribunais,
        default=tribunais
    )
    
    # Filtro por período
    df['data_julgamento'] = pd.to_datetime(df['data_julgamento'])
    min_date = df['data_julgamento'].min()
    max_date = df['data_julgamento'].max()
    
    date_range = st.sidebar.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Aplica filtros
    mask = (df['tribunal'].isin(tribunal_selecionado)) & \
           (df['data_julgamento'].dt.date >= date_range[0]) & \
           (df['data_julgamento'].dt.date <= date_range[1])
    
    df_filtered = df[mask]
    
    # Layout em colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição por Tribunal")
        fig_tribunal = px.pie(
            df_filtered,
            names='tribunal',
            title='Decisões por Tribunal'
        )
        st.plotly_chart(fig_tribunal, use_container_width=True)
        
        st.subheader("Análise de Sentimento")
        fig_sentiment = px.histogram(
            df_filtered,
            x='sentiment_score',
            title='Distribuição do Sentimento das Decisões'
        )
        st.plotly_chart(fig_sentiment, use_container_width=True)
    
    with col2:
        st.subheader("Evolução Temporal")
        df_temporal = df_filtered.groupby(
            df_filtered['data_julgamento'].dt.to_period('M')
        ).size().reset_index()
        df_temporal.columns = ['data', 'quantidade']
        df_temporal['data'] = df_temporal['data'].astype(str)
        
        fig_temporal = px.line(
            df_temporal,
            x='data',
            y='quantidade',
            title='Evolução do Número de Decisões'
        )
        st.plotly_chart(fig_temporal, use_container_width=True)
        
        st.subheader("Estatísticas Gerais")
        st.metric("Total de Decisões", len(df_filtered))
        st.metric(
            "Média de Sentimento",
            f"{df_filtered['sentiment_score'].mean():.2f}"
        )
        st.metric(
            "Média de Palavras por Decisão",
            f"{df_filtered['word_count'].mean():.0f}"
        )
    
    # Tabela com dados detalhados
    st.subheader("Dados Detalhados")
    st.dataframe(
        df_filtered[[
            'tribunal',
            'data_julgamento',
            'relator',
            'sentiment_score',
            'word_count'
        ]].sort_values('data_julgamento', ascending=False)
    )

except FileNotFoundError:
    st.error("Arquivo de dados não encontrado. Execute primeiro o script de processamento.")
except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}") 