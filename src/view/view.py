import base64
import io
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, no_update
import dash_bootstrap_components as dbc
from src.view.theme import UNB_THEME
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
                        dbc.Col(html.Img(src="/assets/logo.png", height="48px"), className="me-3"),
                        dbc.Col(
                            [
                                html.H5("Otimização de Localização", className="navbar-brand-text mb-0"),
                                html.Small("Universidade de Brasília", className="navbar-subtext")
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
    className="navbar-custom mb-32 py-3 shadow-sm"
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
    className="mb-32"
)

# 3. Tab 1 Content (Input)

# Upload Card
upload_card = dbc.Card(
    [
        dbc.CardHeader(
            "Carregar Arquivo",
            className="card-header-custom"
        ),
        dbc.CardBody(
            [
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.Div("📂", style={"fontSize": "2rem", "marginBottom": "8px"}),
                        html.Span('Arraste e solte ou ', style={"color": UNB_THEME['UNB_GRAY_DARK']}),
                        html.A('Selecione', className="fw-bold text-decoration-underline", style={"color": UNB_THEME['UNB_BLUE']})
                    ]),
                    className="upload-box",
                    multiple=False,
                    accept='.xlsx'
                )
            ],
            className="card-body-custom"
        ),
    ],
    className="card-custom h-100"
)

# Add Data Card
add_data_card = dbc.Card(
    [
        dbc.CardHeader(
            "Adicionar Dados",
            className="card-header-custom"
        ),
        dbc.CardBody(
            [
                html.P("Adicione uma nova linha à planilha carregada.", className="text-muted small mb-16"),
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
                        "Adicionar Linha",
                        id='btn-add-row',
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
                html.P("Baixe a planilha com os novos dados adicionados.", className="text-muted small mb-16"),
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
                            className="text-center mt-48"
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
        dbc.ModalBody(id="modal-body-content", children="Ocorreu um erro."),
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
                    dbc.Col(add_data_card, width=12, className="mb-24"),
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
            className="px-4 pb-48"
        )
    ],
    style={
        'backgroundColor': UNB_THEME['UNB_GRAY_LIGHT'],
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
        return html.H3('Configuração do Modelo (Placeholder)', className="text-center mt-48 text-muted")
    elif active_tab == 'tab-results':
        return html.H3('Resultados (Placeholder)', className="text-center mt-48 text-muted")
    return html.Div()

# 1. Upload & Add Row -> Update Store
@app.callback(
    Output('stored-data', 'data'),
    Output('error-modal', 'is_open'),
    Output('modal-body-content', 'children'),
    [Input('upload-data', 'contents'),
     Input('btn-add-row', 'n_clicks'),
     Input('close-modal', 'n_clicks')],
    [State('upload-data', 'filename'),
     State('stored-data', 'data'),
     State('input-nome', 'value'),
     State('input-idade', 'value'),
     State('error-modal', 'is_open')]
)
def update_store(contents, n_add, n_close, filename, stored_data, name_val, age_val, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Close Modal
    if trigger_id == 'close-modal':
        return no_update, False, no_update

    # Upload Data
    if trigger_id == 'upload-data':
        if contents is None:
            return no_update, no_update, no_update

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if filename.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(decoded))
                return df.to_json(date_format='iso', orient='split'), False, no_update
            else:
                return no_update, True, "O arquivo deve ser um Excel (.xlsx)."
        except Exception as e:
            print(f"Error processing file: {e}")
            return no_update, True, "Erro ao processar o arquivo. Verifique se é um Excel válido."

    # Add Row
    if trigger_id == 'btn-add-row':
        if not stored_data:
            return no_update, True, "Por favor, carregue um arquivo Excel primeiro."

        if not name_val or not age_val:
             return no_update, True, "Preencha os campos Nome e Idade para adicionar."

        try:
            df = pd.read_json(io.StringIO(stored_data), orient='split')

            # Create a new row dictionary
            new_row_data = {'Nome': name_val, 'Idade': age_val}

            # Create a DataFrame for the new row
            # If the original DF doesn't have these columns, they will be added.
            # If the original DF has other columns, they will be NaN for this row unless filled.
            new_row_df = pd.DataFrame([new_row_data])

            # Concatenate
            df = pd.concat([df, new_row_df], ignore_index=True)

            return df.to_json(date_format='iso', orient='split'), False, no_update
        except Exception as e:
            print(f"Error adding row: {e}")
            return no_update, True, f"Erro ao adicionar linha: {str(e)}"

    return no_update, no_update, no_update


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
            className="text-center mt-48"
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
                'color': UNB_THEME['UNB_GRAY_DARK']
            },
            style_header={
                'backgroundColor': '#F8F9FA',
                'color': UNB_THEME['UNB_BLUE'],
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
    return dcc.send_data_frame(df.to_excel, "dados_unb_editados.xlsx", index=False)


def view():
    app.run(debug=True)
