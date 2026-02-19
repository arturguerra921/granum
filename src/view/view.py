import base64
import io
import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, no_update
import dash_bootstrap_components as dbc
from src.view.theme import UNB_THEME
import dash

# --- Data Loading ---
try:
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'data')
    MUNICIPIOS_PATH = os.path.join(DATA_DIR, 'municipios.csv')
    ESTADOS_PATH = os.path.join(DATA_DIR, 'estados.csv')

    df_municipios = pd.read_csv(MUNICIPIOS_PATH, encoding='utf-8-sig')
    df_estados = pd.read_csv(ESTADOS_PATH, encoding='utf-8-sig')

    # Merge to get UF
    df_merged = pd.merge(df_municipios, df_estados[['codigo_uf', 'uf']], on='codigo_uf', how='left')

    # Create "Cidade - UF" column
    df_merged['cidade_uf'] = df_merged['nome'] + ' - ' + df_merged['uf']

    # Create options for dropdown
    CITY_OPTIONS = sorted(df_merged['cidade_uf'].unique().tolist())

    # Create lookup dictionary
    # Drop duplicates to ensure unique keys (though City-UF should be unique for municipalities)
    df_unique = df_merged.drop_duplicates(subset=['cidade_uf'])
    CITY_LOOKUP = df_unique.set_index('cidade_uf')[['latitude', 'longitude']].to_dict('index')

except Exception as e:
    print(f"Error loading geographical data: {e}")
    CITY_OPTIONS = []
    CITY_LOOKUP = {}


# Initialize app with Bootstrap theme and suppress callback exceptions
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Granum"

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
                                html.Div([
                                    dbc.Label("Produto", className="fw-bold small me-2"),
                                    html.I(className="bi bi-question-circle-fill text-muted", id="help-produto", style={"cursor": "help", "fontSize": "0.9rem"}),
                                    dbc.Tooltip(
                                        "Nome do produto a ser transportado (ex: Soja, Milho). O sistema sugerirá produtos já cadastrados.",
                                        target="help-produto",
                                    ),
                                ], className="d-flex align-items-center mb-1"),
                                dbc.Input(id="input-produto", type="text", placeholder="Ex: Arroz", list="list-suggested-products", className="mb-16"),
                                html.Datalist(id="list-suggested-products", children=[])
                            ],
                            width=6
                        ),
                        dbc.Col(
                            [
                                html.Div([
                                    dbc.Label("Peso (Kg)", className="fw-bold small me-2"),
                                    html.I(className="bi bi-question-circle-fill text-muted", id="help-peso", style={"cursor": "help", "fontSize": "0.9rem"}),
                                    dbc.Tooltip(
                                        "Peso total da carga em quilogramas.",
                                        target="help-peso",
                                    ),
                                ], className="d-flex align-items-center mb-1"),
                                dbc.Input(id="input-peso", type="number", placeholder="Ex: 100", className="mb-16")
                            ],
                            width=6
                        ),
                        dbc.Col(
                            [
                                html.Div([
                                    dbc.Label("Cidade", className="fw-bold small me-2"),
                                    html.I(className="bi bi-question-circle-fill text-muted", id="help-cidade", style={"cursor": "help", "fontSize": "0.9rem"}),
                                    dbc.Tooltip(
                                        "Selecione a cidade de origem/destino. Digite para filtrar as opções.",
                                        target="help-cidade",
                                    ),
                                ], className="d-flex align-items-center mb-1"),
                                dcc.Dropdown(
                                    id="input-cidade",
                                    options=[],
                                    placeholder="Selecione a cidade...",
                                    className="mb-16",
                                    searchable=True
                                )
                            ],
                            width=12
                        ),
                        dbc.Col(
                            [
                                html.Div([
                                    dbc.Label("Latitude", className="fw-bold small me-2"),
                                    html.I(className="bi bi-question-circle-fill text-muted", id="help-lat", style={"cursor": "help", "fontSize": "0.9rem"}),
                                    dbc.Tooltip(
                                        "Coordenada de latitude. Preenchida automaticamente ao selecionar a cidade.",
                                        target="help-lat",
                                    ),
                                ], className="d-flex align-items-center mb-1"),
                                dbc.Input(id="input-lat", type="number", placeholder="Lat", className="mb-16", disabled=True)
                            ],
                            width=5
                        ),
                        dbc.Col(
                            [
                                html.Div([
                                    dbc.Label("Longitude", className="fw-bold small me-2"),
                                    html.I(className="bi bi-question-circle-fill text-muted", id="help-lon", style={"cursor": "help", "fontSize": "0.9rem"}),
                                    dbc.Tooltip(
                                        "Coordenada de longitude. Preenchida automaticamente ao selecionar a cidade.",
                                        target="help-lon",
                                    ),
                                ], className="d-flex align-items-center mb-1"),
                                dbc.Input(id="input-lon", type="number", placeholder="Lon", className="mb-16", disabled=True)
                            ],
                            width=5
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Editar", className="fw-bold small", style={"visibility": "hidden"}),
                                dbc.Button("🔒", id="btn-manual-edit", color="secondary", className="d-flex align-items-center justify-content-center w-100", n_clicks=0, title="Editar Lat/Long manualmente")
                            ],
                            width=2
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
    initial_df = pd.DataFrame(columns=["Produto", "Peso (Kg)", "Cidade", "Latitude", "Longitude"])

    # Metrics Section
    metrics_section = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.I(className="bi bi-box-seam-fill fs-1 me-3", style={"color": UNB_THEME['UNB_BLUE']}),
                                    html.Div(
                                        [
                                            html.H6("Total Peso (Kg)", className="text-muted small text-uppercase fw-bold mb-1"),
                                            html.H3(id="metric-total-weight", children="0.00", className="mb-0", style={"color": UNB_THEME['UNB_BLUE']})
                                        ]
                                    )
                                ],
                                className="d-flex align-items-center justify-content-center py-2"
                            )
                        ],
                        className="p-3"
                    ),
                    className="shadow-sm border-0 h-100",
                    style={"backgroundColor": "#f8f9fa", "borderRadius": "12px"}
                ),
                width=6
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.I(className="bi bi-tags-fill fs-1 me-3", style={"color": UNB_THEME['UNB_GREEN']}),
                                    html.Div(
                                        [
                                            html.H6("Produtos Diferentes", className="text-muted small text-uppercase fw-bold mb-1"),
                                            html.H3(id="metric-unique-products", children="0", className="mb-0", style={"color": UNB_THEME['UNB_GREEN']})
                                        ]
                                    )
                                ],
                                className="d-flex align-items-center justify-content-center py-2"
                            )
                        ],
                        className="p-3"
                    ),
                    className="shadow-sm border-0 h-100",
                    style={"backgroundColor": "#f8f9fa", "borderRadius": "12px"}
                ),
                width=6
            ),
        ],
        className="mt-auto pt-3 g-3" # Push to bottom
    )

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
                                columns=[{'name': i, 'id': i, 'deletable': False, 'renamable': False} for i in initial_df.columns],
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
                        ], className="h-100"),
                        color="primary"
                    ),
                    metrics_section
                ],
                className="card-body-custom d-flex flex-column"
            ),
        ],
        className="card-custom h-100",
        style={"minHeight": "600px"} # Increased min-height to ensure space
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
initial_df = pd.DataFrame(columns=["Produto", "Peso (Kg)", "Cidade", "Latitude", "Longitude"])

app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [
                tabs,
                content_container,
                dcc.Store(id='stored-data', data=initial_df.to_json(date_format='iso', orient='split')),
                dcc.Store(id='metrics-store', data={'weight': 0, 'count': 0}),
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

# 1. City Dropdown Options (Server-side filtering)
@app.callback(
    Output("input-cidade", "options"),
    Input("input-cidade", "search_value"),
    State("input-cidade", "value")
)
def update_city_options(search_value, value):
    if not search_value:
        # If no search term, show the selected value (if any) or nothing (or top few)
        if value:
            return [{'label': value, 'value': value}]
        return []

    # Filter options based on search term
    filtered = [
        {'label': c, 'value': c}
        for c in CITY_OPTIONS
        if search_value.lower() in c.lower()
    ]

    # Limit results for performance
    filtered = filtered[:50]

    # Ensure current value is present
    if value:
        # Check if value is already in filtered
        if not any(f['value'] == value for f in filtered):
            filtered.insert(0, {'label': value, 'value': value})

    return filtered

# 2. City Selection -> Auto-fill Lat/Lon
@app.callback(
    [Output('input-lat', 'value'),
     Output('input-lon', 'value')],
    Input('input-cidade', 'value'),
    prevent_initial_call=True
)
def update_lat_lon(city_value):
    if not city_value or city_value not in CITY_LOOKUP:
        return no_update, no_update

    data = CITY_LOOKUP[city_value]
    return data['latitude'], data['longitude']

# 2. Manual Edit Toggle
@app.callback(
    [Output('input-lat', 'disabled'),
     Output('input-lon', 'disabled'),
     Output('btn-manual-edit', 'children')],
    Input('btn-manual-edit', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_manual_edit(n_clicks):
    if n_clicks % 2 == 1:
        return False, False, "🔓" # Enable
    return True, True, "🔒" # Disable

# 3. Upload & Add Row -> Update Store
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
     State('input-produto', 'value'),
     State('input-peso', 'value'),
     State('input-cidade', 'value'),
     State('input-lat', 'value'),
     State('input-lon', 'value'),
     State('error-modal', 'is_open'),
     State('editable-table', 'data')]
)
def update_store(contents, n_add, timestamp, n_close, filename, stored_data,
                 prod_val, peso_val, cidade_val, lat_val, lon_val,
                 is_open, table_data):
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
                # Ensure columns match expectations, or just allow loose structure but warn?
                # For now, let's just load it. If columns mismatch, the table will show them but might look weird.
                # Ideally we align with expected columns.
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
             df = pd.DataFrame(columns=["Produto", "Peso (Kg)", "Cidade", "Latitude", "Longitude"])

        if not prod_val or not peso_val or not cidade_val:
             return no_update, True, "Preencha Produto, Peso e Cidade para adicionar."

        try:
            new_row_data = {
                'Produto': prod_val,
                'Peso (Kg)': peso_val,
                'Cidade': cidade_val,
                'Latitude': lat_val,
                'Longitude': lon_val
            }
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
@app.callback(
    Output('editable-table', 'data'),
    Output('editable-table', 'columns'),
    [Input('stored-data', 'data'),
     Input('main-tabs', 'active_tab')]
)
def update_table_view(stored_data, active_tab):
    if active_tab != 'tab-input':
        return no_update, no_update

    if stored_data is None:
        return no_update, no_update

    try:
        df = pd.read_json(io.StringIO(stored_data), orient='split')
        columns = [{'name': i, 'id': i, 'deletable': False, 'renamable': False} for i in df.columns]
        return df.to_dict('records'), columns
    except Exception as e:
        print(f"Error rendering table: {e}")
        return no_update, no_update

# 2.1 Update Metrics Store
@app.callback(
    Output('metrics-store', 'data'),
    Input('stored-data', 'data')
)
def update_metrics(stored_data):
    if stored_data is None:
        return {'weight': 0, 'count': 0}

    try:
        df = pd.read_json(io.StringIO(stored_data), orient='split')

        total_weight = 0
        unique_products = 0

        if not df.empty:
            if "Peso (Kg)" in df.columns:
                total_weight = pd.to_numeric(df["Peso (Kg)"], errors='coerce').fillna(0).sum()

            if "Produto" in df.columns:
                unique_products = df["Produto"].nunique()

        return {'weight': float(total_weight), 'count': int(unique_products)}
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return {'weight': 0, 'count': 0}

# 2.2 Product Suggestions (Datalist)
@app.callback(
    Output('list-suggested-products', 'children'),
    Input('stored-data', 'data')
)
def update_product_suggestions(stored_data):
    if stored_data is None:
        return []

    try:
        df = pd.read_json(io.StringIO(stored_data), orient='split')
        if "Produto" in df.columns:
            # Get unique products, drop None/NaN, sort
            products = sorted(df["Produto"].dropna().unique().astype(str).tolist())
            return [html.Option(value=p) for p in products]
        return []
    except Exception as e:
        print(f"Error updating product suggestions: {e}")
        return []

# Client-side callback for animating metrics
app.clientside_callback(
    """
    function(data) {
        if (!data) return window.dash_clientside.no_update;

        const animate = (id, endValue, isFloat) => {
            const el = document.getElementById(id);
            if (!el) return;

            // Get current value (stripped of formatting) or default to 0
            let startValue = parseFloat(el.innerText.replace(/,/g, '')) || 0;
            const duration = 1000; // 1 second
            const startTime = performance.now();

            const step = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // Ease out cubic
                const ease = 1 - Math.pow(1 - progress, 3);

                const current = startValue + (endValue - startValue) * ease;

                if (isFloat) {
                    el.innerText = current.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                } else {
                    el.innerText = Math.round(current).toString();
                }

                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                     // Ensure final value is exact
                    if (isFloat) {
                        el.innerText = endValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    } else {
                        el.innerText = endValue.toString();
                    }
                }
            };

            requestAnimationFrame(step);
        };

        animate('metric-total-weight', data.weight, true);
        animate('metric-unique-products', data.count, false);

        return window.dash_clientside.no_update;
    }
    """,
    Output('metric-total-weight', 'id'), # Dummy output
    Input('metrics-store', 'data')
)

# 3. Download
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn-download", "n_clicks"),
    State('stored-data', 'data'),
    prevent_initial_call=True,
)
def download_data(n_clicks, stored_data):
    if not n_clicks:
        return no_update

    if not stored_data:
        return no_update

    df = pd.read_json(io.StringIO(stored_data), orient='split')
    return dcc.send_data_frame(df.to_excel, "dados_unb_editados.xlsx", index=False)


def view():
    app.run(debug=True)
