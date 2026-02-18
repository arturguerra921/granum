import base64
import io
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, no_update
import dash_bootstrap_components as dbc
from src.view.theme import UNB_THEME
import dash

# Initialize app with Bootstrap theme and suppress callback exceptions
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
# Defined as a function to ensure fresh instances if needed, though Dash handles ID reuse fine
def get_tab1_layout():
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
    # Initial Empty DataFrame
    initial_df = pd.DataFrame(columns=["Nome", "Idade"])

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
                            dash_table.DataTable(
                                id='editable-table',
                                data=initial_df.to_dict('records'), # Initially empty
                                columns=[{'name': i, 'id': i, 'deletable': True, 'renamable': True} for i in initial_df.columns],
                                editable=True,
                                row_deletable=True,
                                page_size=10,
                                style_table={'overflowX': 'auto', 'borderRadius': '8px', 'border': f"1px solid {UNB_THEME['BORDER_LIGHT']}"},
                                style_cell={
                                    'textAlign': 'left',
                                    'fontFamily': "'Roboto', sans-serif",
                                    'padding': '12px',
                                    'fontSize': '0.9rem',
                                    'color': UNB_THEME['UNB_GRAY_DARK']
                                },
                                style_header={
                                    'backgroundColor': '#F8F9FA', # Standard light gray header background
                                    'color': UNB_THEME['UNB_BLUE'],
                                    'fontWeight': 'bold',
                                    'border': 'none',
                                    'padding': '12px',
                                    'borderBottom': f"2px solid {UNB_THEME['BORDER_LIGHT']}"
                                },
                                style_data={
                                    'borderBottom': f"1px solid {UNB_THEME['BORDER_LIGHT']}"
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': '#f8f9fa'
                                    }
                                ]
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

    return html.Div([
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
        error_modal
    ])

# --- App Layout Assembly ---

content_container = html.Div(id="tabs-content")
initial_df = pd.DataFrame(columns=["Nome", "Idade"])

app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [
                tabs,
                content_container,
                dcc.Store(id='stored-data', data=initial_df.to_json(date_format='iso', orient='split')),
                dcc.Download(id='download-dataframe-xlsx')
            ],
            fluid=True,
            className="px-4 pb-48"
        )
    ],
    style={
        'backgroundColor': UNB_THEME['APP_BACKGROUND'],
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
        return get_tab1_layout()
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
     Input('editable-table', 'data_timestamp'), # Track edits via timestamp
     Input('close-modal', 'n_clicks')],
    [State('upload-data', 'filename'),
     State('stored-data', 'data'),
     State('input-nome', 'value'),
     State('input-idade', 'value'),
     State('error-modal', 'is_open'),
     State('editable-table', 'data')]
)
def update_store(contents, n_add, timestamp, n_close, filename, stored_data, name_val, age_val, is_open, table_data):
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
        if stored_data:
             df = pd.read_json(io.StringIO(stored_data), orient='split')
        else:
             df = pd.DataFrame(columns=["Nome", "Idade"])

        if not name_val or not age_val:
             return no_update, True, "Preencha os campos Nome e Idade para adicionar."

        try:
            new_row_data = {'Nome': name_val, 'Idade': age_val}
            new_row_df = pd.DataFrame([new_row_data])
            df = pd.concat([df, new_row_df], ignore_index=True)
            return df.to_json(date_format='iso', orient='split'), False, no_update
        except Exception as e:
            print(f"Error adding row: {e}")
            return no_update, True, f"Erro ao adicionar linha: {str(e)}"

    # Table Edited (Manual Data Entry)
    if trigger_id == 'editable-table':
        try:
            # Reconstruct DF from table data
            if table_data is None:
                return no_update, no_update, no_update

            df = pd.DataFrame(table_data)
            # Ensure proper JSON structure for store
            return df.to_json(date_format='iso', orient='split'), False, no_update
        except Exception as e:
            print(f"Error updating store from table edit: {e}")
            return no_update, no_update, no_update

    return no_update, no_update, no_update


# 2. Store -> Render Table (Update Table Data)
# Explicitly including active_tab in Inputs to force re-evaluation if needed
# But primarily, the Input is stored-data.
# We need to make sure this callback fires when the component is created.
# Without prevent_initial_call=True (default False), it SHOULD fire on layout render.
@app.callback(
    Output('editable-table', 'data'),
    Output('editable-table', 'columns'),
    [Input('stored-data', 'data'),
     Input('main-tabs', 'active_tab')] # Add this to force trigger on tab switch
)
def update_table_view(stored_data, active_tab):
    if active_tab != 'tab-input':
        return no_update, no_update

    if stored_data is None:
        return no_update, no_update

    try:
        df = pd.read_json(io.StringIO(stored_data), orient='split')
        columns = [{'name': i, 'id': i, 'deletable': True, 'renamable': True} for i in df.columns]
        return df.to_dict('records'), columns
    except Exception as e:
        print(f"Error rendering table: {e}")
        return no_update, no_update

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
