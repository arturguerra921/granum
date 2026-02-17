import base64
import io
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table
from src.view.theme import GOV_THEME

app = Dash(__name__, suppress_callback_exceptions=True)

# --- Layout ---

# Header
header = html.Div(
    [
        html.H1(
            "Otimização de Localização - Governo Federal",
            style={'color': GOV_THEME['BACKGROUND'], 'margin': 0, 'padding': '20px'}
        )
    ],
    style={'backgroundColor': GOV_THEME['PRIMARY']}
)

# Tabs
tabs = dcc.Tabs(
    id="main-tabs",
    value='tab-input',
    children=[
        dcc.Tab(label='Entrada de Dados', value='tab-input'),
        dcc.Tab(label='Configuração do Modelo', value='tab-config'),
        dcc.Tab(label='Resultados', value='tab-results'),
    ]
)

# Content Container
content_container = html.Div(id="tabs-content")

app.layout = html.Div([
    header,
    tabs,
    content_container
])

# --- Tab 1 Layout Components ---

upload_component = dcc.Upload(
    id='upload-data',
    children=html.Div([
        'Arraste e solte ou ',
        html.A('Selecione um Arquivo')
    ]),
    style={
        'width': '100%',
        'height': '60px',
        'lineHeight': '60px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin': '10px 0',
        'borderColor': GOV_THEME['PRIMARY']
    },
    multiple=False,
    accept='.xlsx'
)

controls_section = html.Div([
    html.Button("Validar Dados", id='btn-validate', style={'marginRight': '10px'}),
    html.Button("Limpar", id='btn-clear')
], style={'marginTop': '20px'})

left_sidebar = html.Div(
    [
        html.H3("Upload de Dados"),
        upload_component,
        controls_section
    ],
    style={
        'width': '30%',
        'padding': '20px',
        'borderRight': '1px solid #ccc',
        'boxSizing': 'border-box'
    }
)

right_area = html.Div(
    [
        html.H3("Visualização dos Dados"),
        dash_table.DataTable(
            id='data-preview-table',
            page_size=10,
            style_table={'overflowX': 'auto'},
            data=[],
            columns=[]
        )
    ],
    style={
        'width': '70%',
        'padding': '20px',
        'boxSizing': 'border-box'
    }
)

tab1_layout = html.Div(
    [left_sidebar, right_area],
    style={'display': 'flex', 'height': '100vh'}
)


# --- Callbacks ---

@app.callback(
    Output('tabs-content', 'children'),
    Input('main-tabs', 'value')
)
def render_content(tab):
    if tab == 'tab-input':
        return tab1_layout
    elif tab == 'tab-config':
        return html.H3('Configuração do Modelo (Placeholder)')
    elif tab == 'tab-results':
        return html.H3('Resultados (Placeholder)')
    return html.Div()

@app.callback(
    [Output('data-preview-table', 'data'),
     Output('data-preview-table', 'columns')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    if contents is None:
        return [], []

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(decoded))
            columns = [{'name': i, 'id': i} for i in df.columns]
            data = df.to_dict('records')
            return data, columns
        else:
            # In case of error or wrong file type, we might want to alert or return empty
            # For now returning empty with print
            print(f"File {filename} is not an .xlsx file")
            return [], []
    except Exception as e:
        print(e)
        return [], []

def view():
    app.run(debug=True)
