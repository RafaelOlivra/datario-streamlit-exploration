import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import numpy as np


def grafico_evolucao_semanal_SP():
    # Carrega os dados do arquivo JSON
    df = pd.read_json(
        './data/02_processed/novos_casos_por_semanaepi_SP.json', orient='index')
    df = df.reset_index()
    df.columns = ['semanaEpi', 'casosNovos']

    # Mostra os dados num gráfico de barras usando o Streamlit
    st.write(f'## Evolução semanal de novos casos no estado de São Paulo')
    st.bar_chart(df, x='semanaEpi', y='casosNovos',
                 x_label="Semana Epidemiológica", y_label="Novos Casos")


def grafico_evolucao_semanal_SP_MG_RJ():
    # Carrega os dados do arquivo JSON

    # Demo JSON
    data = {
        "SP": {
            "2020-10-01": 100,
            "2020-10-08": 200,
            "2020-10-15": 300,
            "2020-10-22": 400
        },
        "MG": {
            "2020-10-01": 50,
            "2020-10-08": 100,
            "2020-10-15": 150,
            "2020-10-22": 1200
        },
        "RJ": {
            "2020-10-01": 75,
            "2020-10-08": 150,
            "2020-10-15": 225,
            "2020-10-22": 10
        }
    }

    df = pd.DataFrame(data)
    df = df.reset_index()
    df.columns = ['Data', 'SP', 'MG', 'RJ']
    df['Data'] = pd.to_datetime(df['Data'])

    # Show only month and year
    #df['Data'] = df['Data'].dt.strftime('%b-%y')

    st.write(df)

    # Mostra os dados num gráfico de áreas Streamlit
    st.write(f'## Evolução semanal de novos casos em SP, MG e RJ')
    st.area_chart(df, x='Data', x_label='Mês', y=[
                  'SP', 'MG', 'RJ'], y_label='Novos Casos')


def grafico_obitos_acumulados_BR():
    # Carrega os dados do arquivo JSON
    df = pd.read_json(
        './data/02_processed/obitos_acumulados_por_semanaepi_BR.json', orient='index')
    df = df.reset_index()
    df.columns = ['semanaEpi', 'obitosAcumulados']
    # Mostra os dados num gráfico de barras usando o Streamlit
    st.write(f'## Óbitos acumulados em todo o Brasil')
    st.line_chart(df, x='semanaEpi', y='obitosAcumulados',
                  x_label="Semana Epidemiológica", y_label="Óbitos Acumulados")


def dashboard():
    # 2. Gráfico de Barras com Streamlit:
    # Usando os dados de casos novos de COVID-19 por semana epidemiológica de notificação, crie um gráfico de barras em Streamlit que mostre a evolução semanal dos casos em um determinado estado. Indique o estado escolhido e explique sua escolha.
    grafico_evolucao_semanal_SP()

    # 3. Gráfico de Linha com Streamlit:
    # Crie um gráfico de linha utilizando Streamlit para representar o número de óbitos acumulados por COVID-19 ao longo das semanas epidemiológicas de notificação para todo o Brasil. Explique como a curva de óbitos acumulados pode ser interpretada.
    grafico_obitos_acumulados_BR()

    # 4. Gráfico de Área com Streamlit:
    # Utilizando os dados de casos acumulados por COVID-19, crie um gráfico de área em Streamlit para comparar a evolução dos casos em três estados diferentes. Explique as diferenças observadas entre os estados escolhidos.
    grafico_evolucao_semanal_SP_MG_RJ()


if __name__ == '__main__':
    dashboard()
