import time
import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import time
import locale
from streamlit_js_eval import streamlit_js_eval

############## CONFIG ##############

# Set locale for number formatting
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Set page config
st.set_page_config(
    page_title='Chegada de Turistas no Rio de Janeiro',
    page_icon='🌴',
    layout='wide',
    initial_sidebar_state='auto'
)

############## SESSION STATE FUNCTION ##############

if 'data' not in st.session_state:
    st.session_state.data = None

if 'current_view' not in st.session_state:
    st.session_state.current_view = 0

if 'current_explore_view' not in st.session_state:
    st.session_state.current_explore_view = 'Explorador'

if 'styles' not in st.session_state:
    st.session_state.styles = {
        'apply': False,
        'bg_color': '',
        'text_color': '',
        'font_family': 'default'
    }


############## UTIL FUNCTIONS ##############

def format_number(number):
    # Convert to number if necessary
    if isinstance(number, str):
        number = int(number)
    return locale.format_string('%d', number, grouping=True)


############## DATA FUNCTIONS ##############

@st.cache_data
def get_csv_content(csv_file):
    df = pd.read_csv(csv_file)
    return df.to_csv(index=False)


def get_data():
    return st.session_state.data


def set_data(data):
    # Make sure Ano is a string
    if data is not None and 'Ano' in data.columns:
        data['Ano'] = data['Ano'].astype(str)
    st.session_state.data = data


def get_available_views():
    return ['Upload dos Dados', 'Explorar', 'Customizar', 'Sobre']


def get_current_view():
    current_view = st.session_state.current_view
    return current_view or get_available_views()[0]


def get_current_view_index():
    return get_available_views().index(get_current_view())


def set_current_view(view):
    st.session_state.current_view = view


def get_available_explore_views():
    return ['Explorador', 'Editor']


def get_current_explore_view():
    current_explore_view = st.session_state.current_explore_view
    return current_explore_view or get_available_explore_views()[0]


def get_current_explore_view_index():
    return get_available_explore_views().index(get_current_explore_view())


############## CUSTOMIZATION FUNCTIONS ##############

def apply_customizations():
    # Ignore if customizations are not set
    if not any(st.session_state.styles['bg_color'] or st.session_state.styles['text_color']):
        return

    # Ignore if apply is not set
    if not st.session_state.styles['apply']:
        return

    # Apply the custom colors to the dashboard live
    if st.session_state.styles['font_family'] == 'default':
        st.markdown(f"""
        <style>
        #root, .main {{
            background-color: {st.session_state.styles['bg_color']};
            color: {st.session_state.styles['text_color']};
        }}
        h1,h2,h3,h4,h5,h6,p {{
            color: {st.session_state.styles['text_color']} !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <style>
        #root, .main {{
            background-color: {st.session_state.styles['bg_color']};
            font-family: {st.session_state.styles['font_family']};
        }}
        h1,h2,h3,h4,h5,h6,p {{
            color: {st.session_state.styles['text_color']} !important;
            font-family: {st.session_state.styles['font_family']};
        }}
        </style>
        """, unsafe_allow_html=True)

    # Adjust brightness if the background are different from default
    if st.session_state.styles['bg_color'] != '#ffffff':
        st.markdown(f"""
        <style>
        .stSidebar, header[data-testid="stHeader"] {{
            background-color: {st.session_state.styles['bg_color']};
            font-family: {st.session_state.styles['font_family']};
        }}
        .stSidebar, header[data-testid="stHeader"] {{
            filter: brightness(0.9);
        }}
        </style>
        """, unsafe_allow_html=True)


############## PLOTS & GRAPHS ##############

def plot_line_visitors_by_year(data, col=st):
    # Group by year
    data = data.groupby('Ano').sum().reset_index()

    # Plot the total number of tourists by year
    fig = px.line(data, x='Ano', y='Total', title='Total de Turistas por Ano',
                  labels={'Ano': 'Ano', 'Total': 'Total de Turistas'},
                  template='plotly_dark',
                  markers=True
                  )
    col.plotly_chart(fig, use_container_width=True)


def plot_bar_visitors_by_country(data, col=st):
    # Group by country
    data = data.groupby('País').sum().reset_index()

    # Plot the total number of tourists by country
    fig = px.bar(data, x='País', y='Total', title='Total de Turistas por País',
                 labels={'País': 'País', 'Total': 'Total de Turistas'},
                 template='plotly_dark',
                 )
    st.plotly_chart(fig, use_container_width=True)


def pie_chart_visitors_by_medium(data, col=st):
    # Make a pie chart comparing the percentage of tourists by air and sea
    total_air = data['Aérea'].sum()
    total_sea = data['Marítima'].sum()
    fig = px.pie(
        names=['Aérea', 'Marítima'],
        values=[total_air, total_sea],
        labels={'value': 'Total de Turistas'},
        title='Porcentagem de Turistas por Meio de Transporte'
    )
    col.plotly_chart(fig, use_container_width=True)


def plot_3d_globe_with_tourists_by_country(data, col=st):
    # Get coordinates for each country from the CSV file
    csv_content = pd.read_csv('./data/02_processed/country_coordinates.csv')
    df_lat_lon = pd.DataFrame(csv_content)
    df_lat_lon = df_lat_lon.rename(columns={'Country': 'País'})

    # Sum the number of tourists by country keeping only the columns we need
    data = data.groupby('País').sum().reset_index()
    data = data[['País', 'Aérea', 'Marítima']]

    # Merge the data with the coordinates
    data = pd.merge(data, df_lat_lon, on='País', how='left')

    # Drop rows with missing values
    data = data.dropna(subset=['Latitude', 'Longitude'])

    # Add an offset for the "Marítima" bars to avoid overlap
    data['Longitude_offset'] = data['Longitude'] + \
        2  # Adjust the offset value as needed

    # Adjust elevation_scale scale based on the number of tourists
    air_elevation_scale = 9 if data['Aérea'].mean() > 9000 else 160
    sea_elevation_scale = 9 if data['Aérea'].mean() > 10000 else 160

    # Create a ColumnLayer for the Aérea (Air) data
    air_column_layer = pdk.Layer(
        'ColumnLayer',
        data,
        get_position='[Longitude, Latitude]',
        get_elevation='Aérea',  # Column height based on air tourist data
        elevation_scale=air_elevation_scale,
        get_fill_color=[255, 0, 0],
        radius=100000,
        pickable=True,
        elevation_range=[0, 3000],
        extruded=True,
        auto_highlight=True
    )

    # Create a ColumnLayer for the Marítima (Sea) data with an offset
    sea_column_layer = pdk.Layer(
        'ColumnLayer',
        data,
        get_position='[Longitude_offset, Latitude]',
        get_elevation='Marítima',
        elevation_scale=sea_elevation_scale,
        get_fill_color=[0, 0, 255],
        radius=100000,
        pickable=True,
        elevation_range=[0, 3000],
        extruded=True,
        auto_highlight=True
    )

    # Create the deck with an orbital view for a globe-like appearance
    view_state = pdk.ViewState(
        latitude=0,
        longitude=0,
        zoom=1,
        pitch=45,
        bearing=0
    )

    # Create the deck with the two column layers, text layer, and orbital view
    r = pdk.Deck(
        layers=[air_column_layer, sea_column_layer],
        initial_view_state=view_state,
        map_provider='mapbox',
        map_style='mapbox://styles/mapbox/light-v9',
        tooltip={"text": "{País}\n{Aérea} Aérea / {Marítima} Marítima"},
    )

    # Write the title with simulated legends
    col.write("""
              **Chegada de Turistas por País**   
              Aérea (Vermelho) / Marítima (Azul)
        """)

    # Plot the 3D globe with the 3D bars and labels
    col.pydeck_chart(r)

############## VIEWS ##############


### DATA UPLOAD ###
def view_download_processed_csv():
    st.write('### Download dos Dados Processados')
    st.write('''Faça o download do arquivo CSV com os dados processados da planilha
             **"Chegada de turistas pelo Município do Rio de Janeiro, por vias de acesso, segundo continentes e países de residência permanente entre 2006-2019"**.''')

    with st.spinner('Carregando Dados...'):
        csv_content = get_csv_content(
            "./data/02_processed/total_continentes.csv")

        st.download_button(
            label="Download do CSV Normalizado",
            data=csv_content,
            file_name='total_continentes.csv',
            mime='text/csv',
            use_container_width=True,
            type='primary'
        )


def view_data_upload():
    st.write('### Upload dos Dados')

    if get_data() is not None:
        st.success(
            '✅ Dados carregados com sucesso. Utilize o menu **Explorar** para explorar os dados.')

        # Adiciona um botão para limpar os dados
        st.write("")
        st.write("")
        st.write('##### Limpar Dados')
        st.write('Clique no botão abaixo para limpar os dados carregados.')
        if st.button('Limpar Dados', use_container_width=True):
            set_data(None)
            set_current_view('Upload dos Dados')
            # Retorna para a tela de upload
            with st.spinner('Atualizando...'):
                # Aguarda 1 segundo
                time.sleep(1)
                st.rerun()
        else:
            return get_data()

    st.write('Faça o upload do arquivo com os dados CSV obtidos acima.')
    uploaded_file = st.file_uploader(
        "Escolha um arquivo CSV", type=['csv'])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            # Checa se o arquivo possui a estrutura correta
            required_columns = ['País', 'Continente',
                                'Aérea', 'Marítima', 'Total', 'Ano']
            if all(col in df.columns for col in required_columns):
                set_data(df)
                st.success(
                    '✅ Arquivo carregado com sucesso. Utilize o menu lateral para explorar os dados.')
                st.rerun()
                return get_data()
        st.error('❌ Por favor, faça o upload de um arquivo CSV válido.')


### EXPLORE ###
def view_explore():
    st.title('🔍 Explorar')
    st.write('Selecione uma opção para visualizar os dados.')

    if get_data() is None:
        st.warning('⚠️ Faça o upload dos dados para explorar.')
        return

    explore_options = get_available_explore_views()
    current_explore_view = get_current_explore_view()
    explore_option = st.selectbox(
        'Opções de Visualização', explore_options, index=explore_options.index(current_explore_view))

    # Save the current explore view
    st.session_state.current_explore_view = explore_option

    # Show a loader while the data is being loaded
    with st.spinner('Carregando dados...'):
        data = get_data()

    # Explore the data
    if explore_option == 'Explorador':
        ##############################

        # Allow user to filter the displayed data
        st.write('###### Filtros')

        # Make a selection for selecting the continent
        col1, col2, col3 = st.columns(3)
        continent = col1.selectbox(
            'Continente', ['Todos'] + data['Continente'].unique().tolist())
        if continent != 'Todos':
            filtered_data = data[data['Continente'] == continent]
        else:
            filtered_data = data

        # Make a selection for selecting the country, should already be filtered by the continent
        # Sort by country name
        country = col2.selectbox(
            'País', ['Todos'] + filtered_data.sort_values(by='País', ascending=True)['País'].unique().tolist())
        if country != 'Todos':
            filtered_data = filtered_data[filtered_data['País'] == country]

        # Make a selection for selecting the with a multiselect picker
        # Make all years selected by default
        years = col3.multiselect(
            'Ano', filtered_data['Ano'].unique().tolist(), default=filtered_data['Ano'].unique().tolist())
        if years != filtered_data['Ano'].unique().tolist():
            filtered_data = filtered_data[filtered_data['Ano'].isin(years)]

        if filtered_data.empty:
            st.warning('⚠️ Nenhum dado encontrado com os filtros selecionados.')
            return
        else:
            st.dataframe(filtered_data, use_container_width=True)

        ##############################

        # Show the total number of tourists
        col1, col2, col3 = st.columns(3)
        total_tourists = format_number(filtered_data['Total'].sum())

        col1.metric(label='Total',
                    value=total_tourists, delta="Turistas no total")

        # Show the countries with the most tourists including all years
        most_tourists = filtered_data.groupby(
            'País').sum().nlargest(5, 'Total')
        col2.metric(label='País com mais Turistas',
                    value=str(most_tourists.index[0]), delta=format_number(int(most_tourists['Total'].iloc[0])))

        # Show the average number of tourists per year
        average_tourists = format_number(
            filtered_data['Total'].sum() / len(filtered_data['Ano'].unique()))
        col3.metric(label='Média',
                    value=average_tourists, delta="Turistas por ano")

        ##############################

        # Plot the total number of tourists by country
        plot_bar_visitors_by_country(filtered_data)

        # Plot the total number of tourists by year
        col1, col2 = st.columns(2)
        plot_line_visitors_by_year(filtered_data, col1)

        # Make a pie chart comparing the percentage of tourists by air and sea
        pie_chart_visitors_by_medium(filtered_data, col2)

        # Plot 3D world map with tourists by country
        plot_3d_globe_with_tourists_by_country(filtered_data)
    # Edit the data
    elif explore_option == 'Editor':
        ##############################

        # Allow user to filter the displayed data
        st.write('###### Editor')

        # Make a multiselect for selecting the columns to display
        columns = st.multiselect(
            'Colunas', data.columns.tolist(), default=get_data().columns.tolist())
        df = data[columns]

        # Allow user to filter the displayed data with a search_filter box
        search_filter = st.text_input('Filtrar Valores', '')
        if search_filter:
            df = df[df.astype(str).apply(
                lambda x: x.str.contains(search_filter, case=False, na=False)).any(axis=1)]

        # Show the data in a dataframe
        st.dataframe(df, use_container_width=True)

        # Permite ao usuário download do arquivo CSV
        st.write('##### Download dos dados filtrados')
        st.write(
            'Clique no botão abaixo para fazer o download do arquivo CSV filtrado com base nas suas seleções.')
        csv_content = df.to_csv(index=False)
        st.download_button(
            label="Download do CSV",
            data=csv_content,
            file_name='turistas_rio_de_janeiro.csv',
            mime='text/csv',
            use_container_width=True,
            type='primary'
        )


### CUSTOMIZE ###
def view_customize():
    # Allow user to customize the dashboard colors
    st.title('🎨 Customizar Interface')
    st.write('Personalize o dashboard com suas cores preferidas.')

    bg_color = st.session_state.styles['bg_color']
    text_color = st.session_state.styles['text_color']
    font_family = st.session_state.styles['font_family']

    st.write('##### Cores')
    col1, col2 = st.columns(2)

    with col1:
        # Allow the user to pick a custom background color
        st.write('###### Cor de Fundo')
        bg_color = st.color_picker(
            'Escolha uma cor de fundo', bg_color or '#fafafa')
        st.write(f'Selecionada: {bg_color}')

    with col2:

        # Allow the user to pick a custom text color
        st.write('###### Cor do Texto')
        text_color = st.color_picker(
            'Escolha uma cor para o texto', text_color or '#444444')
        st.write(f'Selecionada: {text_color}')

    # Allow the user to pick a custom font family
    st.write('##### Tipografia')
    options = ['default', 'sans-serif', 'serif', 'monospace']
    index = options.index(font_family)
    font_family = st.selectbox(
        'Escolha uma fonte', options, index=index)
    st.write(f'Selecionada: {font_family}')

    # Show a toggle to apply the customizations
    st.write("")
    st.write('##### Aplicar Customizações')
    st.write(
        'Ative o botão abaixo para aplicar as customizações ao dashboard.')
    st.warning(
        '⚠️ Talvez seja necessário clicar duas vezes para ativar suas mudanças.')
    st.session_state.styles['apply'] = st.toggle(
        'Aplicar', st.session_state.styles['apply'])

    # Allow the user to reset the customizations
    st.write("")
    st.write('##### Resetar Sessão')
    st.write('Clique no botão abaixo para resetar sua sessão. Isso irá limpar os dados e as customizações!')
    if st.button('Resetar Sessão', use_container_width=True):
        with st.spinner('Resetando...'):
            time.sleep(2)
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

    # Apply background and text colors dynamically
    st.session_state.styles['bg_color'] = bg_color
    st.session_state.styles['text_color'] = text_color
    st.session_state.styles['font_family'] = font_family


### ABOUT ###
def view_about():
    st.title('✨ Sobre')
    st.write('''Este é um projeto de exemplo para demonstrar o uso do Streamlit para a criação de um dashboard interativo.
             O dashboard permite a visualização dos dados de chegada de turistas no Município do Rio de Janeiro, por meios de acesso, segundo continentes e países de residência.
             Para começar, faça o download dos dados processados e em seguida faça o upload do arquivo CSV para explorar os dados.''')
    st.write('### Fonte dos Dados')
    st.write('''Os dados utilizados neste projeto foram obtidos do portal de dados abertos do Município do Rio de Janeiro.
                O arquivo original pode ser encontrado [aqui](https://datario-pcrj.hub.arcgis.com/documents/665ce86a7a2e4c0fa523b7b7636513e0/about).''')
    st.write('### Sobre o Autor')
    st.write('''Este projeto foi criado Rafael Oliveira: https://github.com/RafaelOlivra/datario-streamlit-exploration''')


##############  DASHBOARD ##############
def get_sidebar(view_index=0):
    st.sidebar.title('Chegada de turistas pelo Município do Rio de Janeiro')
    st.sidebar.write('Selecione uma opção para visualizar os dados.')
    current_view = st.sidebar.radio(
        'Menu', get_available_views(), index=view_index)
    set_current_view(current_view)


def dashboard():
    ### SIDEBAR ###
    get_sidebar()

    ### DATA UPLOAD ###
    current_view = get_current_view()
    if current_view == 'Upload dos Dados':
        st.title('⬆️ Upload dos Dados')
        view_download_processed_csv()
        view_data_upload()
    ### EXPLORE ###
    elif current_view == 'Explorar':
        view_explore()
    ### CUSTOMIZE ###
    elif current_view == 'Customizar':
        view_customize()
     ### ABOUT ###
    elif current_view == 'Sobre':
        view_about()

    ### CUSTOMIZE COLORS ###
    apply_customizations()


if __name__ == '__main__':
    dashboard()
