import base64
import io
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, no_update
import dash_bootstrap_components as dbc
from src.view.theme import GOV_THEME
import dash

# Initialize app with Bootstrap theme and suppress callback exceptions
# external_stylesheets includes the custom.css automatically because it's in the assets folder
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# --- Layout Components ---

# 1. Navbar / Header
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/logo.png", height="50px"), className="me-3"),
                        dbc.Col(
                            [
                                html.H5("Otimização de Localização", className="navbar-brand-text mb-0"),
                                html.Small("Governo Federal", className="navbar-subtext")
                            ],
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
        ],
        fluid=True
    ),
    className="navbar-custom mb-4 py-3 shadow-sm"
)

# 2. Tabs
tabs = dbc.Tabs(
    [
        dbc.Tab(label="Entrada de Dados", tab_id="tab-input", label_class_name="px-4"),
        dbc.Tab(label="Configuração do Modelo", tab_id="tab-config", label_class_name="px-4"),
        dbc.Tab(label="Resultados", tab_id="tab-results", label_class_name="px-4"),
    ],
    id="main-tabs",
    active_tab="tab-input",
    className="mb-4"
)

# 3. Tab 1 Content (Input)

# Upload Card
upload_card = dbc.Card(
    [
        dbc.CardHeader(
            "Carregar e Validar",
            className="card-header-custom"
        ),
        dbc.CardBody(
            [
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.Div("📂", style={"fontSize": "2rem", "marginBottom": "8px"}),
                        html.Span('Arraste e solte ou ', style={"color": "#6c757d"}),
                        html.A('Selecione', className="fw-bold text-decoration-underline", style={"color": GOV_THEME['AZUL_ATLANTICO']})
                    ]),
                    className="upload-box mb-24",
                    multiple=False,
                    accept='.xlsx'
                ),
                html.Div(className="d-grid gap-2", children=[
                    dbc.Button(
                        "Validar Dados",
                        id='btn-validate',
                        className="btn-primary-custom"
                    ),
                    dbc.Button(
                        "Limpar",
                        id='btn-clear',
                        outline=True,
                        className="btn-outline-secondary-custom"
                    ),
                ])
            ],
            className="card-body-custom"
        ),
    ],
    className="card-custom h-100"
)

# Enrichment Card (New Feature)
enrich_card = dbc.Card(
    [
        dbc.CardHeader(
            "Enriquecer Dados",
            className="card-header-custom"
        ),
        dbc.CardBody(
            [
                html.P("Adicione colunas padronizadas a todas as linhas da planilha carregada.", className="text-muted small mb-16"),
                dbc.Row([
                    dbc.Col(
                        [
                            dbc.Label("Nome", className="fw-bold small"),
                            dbc.Input(id="input-nome", type="text", placeholder="Ex: João Silva", className="mb-16")
                        ],
                        width=12
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Idade", className="fw-bold small"),
                            dbc.Input(id="input-idade", type="number", placeholder="Ex: 30", className="mb-24")
                        ],
                        width=12
                    ),
                ]),
                html.Div(className="d-grid", children=[
                    dbc.Button(
                        "Adicionar Colunas",
                        id='btn-add-columns',
                        className="btn-primary-custom"
                    ),
                ])
            ],
            className="card-body-custom"
        ),
    ],
    className="card-custom h-100"
)

# Download Card
download_card = dbc.Card(
    [
        dbc.CardHeader(
            "Exportar",
            className="card-header-custom"
        ),
        dbc.CardBody(
            [
                html.P("Baixe a planilha com as novas colunas adicionadas.", className="text-muted small mb-16"),
                 html.Div(className="d-grid", children=[
                    dbc.Button(
                        "Baixar Planilha Editada",
                        id='btn-download',
                        className="btn-success-custom"
                    ),
                ])
            ],
            className="card-body-custom"
        ),
    ],
    className="card-custom h-100"
)


# Data Table Card
data_table_card = dbc.Card(
    [
        dbc.CardHeader(
            "Visualização dos Dados",
            className="card-header-custom"
        ),
        dbc.CardBody(
            [
                dbc.Spinner(
                    html.Div(id='table-container', children=[
                        # Placeholder text will appear here
                         html.Div(
                            [
                                html.H5("Nenhum dado carregado", className="text-muted"),
                                html.P("Faça o upload de uma planilha Excel para visualizar os dados aqui.", className="text-muted small")
                            ],
                            className="text-center mt-5"
                        )
                    ]),
                    color="primary"
                )
            ],
            className="card-body-custom"
        ),
    ],
    className="card-custom h-100",
    style={"minHeight": "400px"}
)

# Error Modal
error_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Atenção"), close_button=True),
        dbc.ModalBody("Por favor, carregue um arquivo Excel primeiro antes de adicionar colunas."),
        dbc.ModalFooter(
            dbc.Button("Fechar", id="close-modal", className="ms-auto", n_clicks=0)
        ),
    ],
    id="error-modal",
    is_open=False,
)

tab1_layout = html.Div([
    dbc.Row(
        [
            dbc.Col([
                dbc.Row([
                    dbc.Col(upload_card, width=12, className="mb-24"),
                    dbc.Col(enrich_card, width=12, className="mb-24"),
                    dbc.Col(download_card, width=12, className="mb-24")
                ])
            ], width=12, lg=3),

            dbc.Col(data_table_card, width=12, lg=9, className="mb-24"),
        ]
    ),
    error_modal,
    dcc.Store(id='stored-data'),
    dcc.Download(id='download-dataframe-xlsx')
])

# --- App Layout Assembly ---

content_container = html.Div(id="tabs-content")

app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [
                tabs,
                content_container
            ],
            fluid=True,
            className="px-4 pb-5"
        )
    ],
    style={
        'backgroundColor': '#F4F6F8',
        'minHeight': '100vh'
    }
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
        return html.H3('Configuração do Modelo (Placeholder)', className="text-center mt-5 text-muted")
    elif active_tab == 'tab-results':
        return html.H3('Resultados (Placeholder)', className="text-center mt-5 text-muted")
    return html.Div()

# 1. Upload & Clear -> Update Store
@app.callback(
    Output('stored-data', 'data'),
    Output('error-modal', 'is_open'),
    [Input('upload-data', 'contents'),
     Input('btn-clear', 'n_clicks'),
     Input('btn-add-columns', 'n_clicks'),
     Input('close-modal', 'n_clicks')],
    [State('upload-data', 'filename'),
     State('stored-data', 'data'),
     State('input-nome', 'value'),
     State('input-idade', 'value'),
     State('error-modal', 'is_open')]
)
def update_store(contents, n_clear, n_add, n_close, filename, stored_data, name_val, age_val, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Close Modal
    if trigger_id == 'close-modal':
        return no_update, False

    # Clear Data
    if trigger_id == 'btn-clear':
        return None, False

    # Upload Data
    if trigger_id == 'upload-data':
        if contents is None:
            return no_update, no_update

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if filename.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(decoded))
                return df.to_json(date_format='iso', orient='split'), False
            else:
                # Ideally show error for wrong file type, but keeping simple for now
                return no_update, False
        except Exception as e:
            print(f"Error processing file: {e}")
            return no_update, False

    # Add Columns
    if trigger_id == 'btn-add-columns':
        if not stored_data:
            return no_update, True # Open error modal

        try:
            df = pd.read_json(io.StringIO(stored_data), orient='split')

            # Add new columns with provided values
            if name_val:
                df['Nome'] = name_val
            if age_val:
                df['Idade'] = age_val

            return df.to_json(date_format='iso', orient='split'), False
        except Exception as e:
            print(f"Error adding columns: {e}")
            return no_update, False

    return no_update, no_update


# 2. Store -> Render Table
@app.callback(
    Output('table-container', 'children'),
    Input('stored-data', 'data')
)
def render_table(stored_data):
    if stored_data is None:
        return html.Div(
            [
                html.H5("Nenhum dado carregado", className="text-muted"),
                html.P("Faça o upload de uma planilha Excel para visualizar os dados aqui.", className="text-muted small")
            ],
            className="text-center mt-5"
        )

    try:
        df = pd.read_json(io.StringIO(stored_data), orient='split')

        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=10,
            style_table={'overflowX': 'auto', 'borderRadius': '8px', 'border': '1px solid #dee2e6'},
            style_cell={
                'textAlign': 'left',
                'fontFamily': "'Roboto', sans-serif",
                'padding': '12px',
                'fontSize': '0.9rem',
                'color': '#495057'
            },
            style_header={
                'backgroundColor': '#F8F9FA',
                'color': '#3C3C3C',
                'fontWeight': 'bold',
                'border': 'none',
                'padding': '12px',
                'borderBottom': '2px solid #DEE2E6'
            },
            style_data={
                'borderBottom': '1px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )
    except Exception as e:
        return html.Div(f"Erro ao renderizar tabela: {e}")

# 3. Download
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn-download", "n_clicks"),
    State('stored-data', 'data'),
    prevent_initial_call=True,
)
def download_data(n_clicks, stored_data):
    if not stored_data:
        return no_update

    df = pd.read_json(io.StringIO(stored_data), orient='split')
    return dcc.send_data_frame(df.to_excel, "dados_editados.xlsx", index=False)


def view():
    app.run(debug=True)
