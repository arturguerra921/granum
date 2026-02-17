import base64
import io
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from src.view.theme import GOV_THEME

# Initialize app with Bootstrap theme
# We suppress callback exceptions because tabs render content dynamically
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# --- Layout ---

# Custom Styles for specific government colors override
# We can inject this as a style block or use inline styles.
# Since we want to be clean, let's use inline styles for the main container elements.

# Header using Navbar
header = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Using a Row to align logo and text if we had a logo. For now just text.
                dbc.Row(
                    dbc.Col(dbc.NavbarBrand("Otimização de Localização - Governo Federal", class_name="ms-2")),
                    align="center",
                    class_name="g-0",
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
        ]
    ),
    color=GOV_THEME['PRIMARY'],
    dark=True,
    className="mb-4",
)

# Tabs
tabs = dbc.Tabs(
    [
        dbc.Tab(label="Entrada de Dados", tab_id="tab-input"),
        dbc.Tab(label="Configuração do Modelo", tab_id="tab-config"),
        dbc.Tab(label="Resultados", tab_id="tab-results"),
    ],
    id="main-tabs",
    active_tab="tab-input",
    class_name="mb-4" # Margin bottom
)

# Content Container
content_container = html.Div(id="tabs-content")

app.layout = html.Div(
    [
        header,
        dbc.Container(
            [
                tabs,
                content_container
            ],
            fluid=True
        )
    ],
    style={'fontFamily': "'Verdana', sans-serif", 'backgroundColor': '#f8f9fa', 'minHeight': '100vh'}
)

# --- Tab 1 Layout Components ---

# Upload Card
upload_card = dbc.Card(
    [
        dbc.CardHeader("Upload de Dados", style={"backgroundColor": GOV_THEME['SECONDARY'], "color": "white"}),
        dbc.CardBody(
            [
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Arraste e solte ou ',
                        html.A('Selecione')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'borderColor': GOV_THEME['PRIMARY'],
                        'cursor': 'pointer'
                    },
                    multiple=False,
                    accept='.xlsx'
                ),
                html.Div(className="d-grid gap-2 mt-3", children=[
                    dbc.Button("Validar Dados", id='btn-validate', color="primary", style={"backgroundColor": GOV_THEME['PRIMARY']}),
                    dbc.Button("Limpar", id='btn-clear', color="secondary", outline=True),
                ])
            ]
        ),
    ],
    className="mb-4 shadow-sm"
)

# Data Table Card
data_table_card = dbc.Card(
    [
        dbc.CardHeader("Visualização dos Dados", style={"backgroundColor": GOV_THEME['SECONDARY'], "color": "white"}),
        dbc.CardBody(
            [
                dbc.Spinner(
                    html.Div(id='table-container', children=[
                        dash_table.DataTable(
                            id='data-preview-table',
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left',
                                'fontFamily': "'Verdana', sans-serif"
                            },
                            style_header={
                                'backgroundColor': GOV_THEME['PRIMARY'],
                                'color': 'white',
                                'fontWeight': 'bold'
                            },
                            data=[],
                            columns=[]
                        )
                    ]),
                    color="primary"
                )
            ]
        ),
    ],
    className="mb-4 shadow-sm"
)

tab1_layout = dbc.Row(
    [
        dbc.Col(upload_card, width=12, md=4, lg=3),
        dbc.Col(data_table_card, width=12, md=8, lg=9),
    ]
)


# --- Callbacks ---

@app.callback(
    Output('tabs-content', 'children'),
    Input('main-tabs', 'active_tab')
)
def render_content(active_tab):
    if active_tab == 'tab-input':
        return tab1_layout
    elif active_tab == 'tab-config':
        return html.H3('Configuração do Modelo (Placeholder)', className="text-center mt-5")
    elif active_tab == 'tab-results':
        return html.H3('Resultados (Placeholder)', className="text-center mt-5")
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
            print(f"File {filename} is not an .xlsx file")
            return [], []
    except Exception as e:
        print(e)
        return [], []

def view():
    app.run(debug=True)
