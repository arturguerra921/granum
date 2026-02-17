import base64
import io
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, no_update, ctx
import dash_bootstrap_components as dbc
from src.view.theme import GOV_THEME
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
                        dbc.Col(html.Img(src="assets/logo.png", height="60px"), className="me-3"),
                        dbc.Col(
                            [
                                html.H4("Otimização de Localização", className="mb-0 text-white", style={"fontWeight": "bold"}),
                                html.Small("Governo Federal", className="text-warning", style={"fontWeight": "bold"})
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
    color=GOV_THEME['AZUL_ATLANTICO'],
    dark=True,
    className="mb-4 shadow-sm py-3"
)

# 2. Tabs
tabs = dbc.Tabs(
    [
        dbc.Tab(label="Entrada de Dados", tab_id="tab-input", label_style={"fontWeight": "600"}),
        dbc.Tab(label="Configuração do Modelo", tab_id="tab-config", label_style={"fontWeight": "600"}),
        dbc.Tab(label="Resultados", tab_id="tab-results", label_style={"fontWeight": "600"}),
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
            "Carregar Arquivo",
            className="text-white fw-bold border-0 pt-3",
            style={"backgroundColor": GOV_THEME['AZUL_ATLANTICO']}
        ),
        dbc.CardBody(
            [
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.Div("📂", style={"fontSize": "2rem", "marginBottom": "10px"}),
                        html.Span('Arraste e solte ou ', style={"color": "#6c757d"}),
                        html.A('Selecione', className="fw-bold text-decoration-underline", style={"color": GOV_THEME['AZUL_ATLANTICO']})
                    ]),
                    style={
                        'width': '100%',
                        'height': '120px',
                        'lineHeight': '1.5',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '10px',
                        'textAlign': 'center',
                        'borderColor': GOV_THEME['AZUL_ATLANTICO'],
                        'backgroundColor': '#F8F9FA',
                        'display': 'flex',
                        'flexDirection': 'column',
                        'justifyContent': 'center',
                        'alignItems': 'center',
                        'cursor': 'pointer',
                    },
                    multiple=False,
                    accept='.xlsx'
                ),
                html.Div(className="d-grid gap-2 mt-3", children=[
                    dbc.Button(
                        "Limpar Dados",
                        id='btn-clear',
                        outline=True,
                        color="secondary",
                        size="sm"
                    ),
                ])
            ]
        ),
    ],
    className="shadow-sm border-0 mb-4",
    style={"borderRadius": "10px"}
)

# New Data Entry Card
new_data_card = dbc.Card(
    [
        dbc.CardHeader(
            "Adicionar Dados",
            className="text-white fw-bold border-0 pt-3",
            style={"backgroundColor": GOV_THEME['AZUL_ATLANTICO']}
        ),
        dbc.CardBody(
            [
                dbc.Row([
                    dbc.Col(dbc.Input(id="input-name", placeholder="Nome", type="text"), className="mb-2"),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Input(id="input-age", placeholder="Idade", type="number"), className="mb-2"),
                ]),
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                            "Adicionar Linha",
                            id="btn-add-row",
                            color="success",
                            className="w-100 fw-bold",
                            style={"backgroundColor": GOV_THEME['VERDE_AMAZONIA'], "border": "none"}
                        )
                    )
                ])
            ]
        )
    ],
    className="shadow-sm border-0 mb-4",
    style={"borderRadius": "10px"}
)

# Data Table Card
data_table_card = dbc.Card(
    [
        dbc.CardHeader(
            dbc.Row([
                dbc.Col("Visualização dos Dados", className="text-white fw-bold pt-1"),
                dbc.Col(
                    dbc.Button(
                        "⬇ Baixar Excel",
                        id="btn-download",
                        color="light",
                        size="sm",
                        className="fw-bold",
                        style={"color": GOV_THEME['AZUL_ATLANTICO']}
                    ),
                    width="auto",
                    className="text-end"
                )
            ]),
            className="border-0",
            style={"backgroundColor": GOV_THEME['AZUL_ATLANTICO']}
        ),
        dbc.CardBody(
            [
                dbc.Spinner(
                    html.Div(id='table-container', children=[
                        html.P("Nenhum dado carregado.", className="text-muted text-center mt-5")
                    ]),
                    color="primary"
                )
            ]
        ),
    ],
    className="shadow-sm border-0 h-100",
    style={"borderRadius": "10px", "minHeight": "400px"}
)

tab1_layout = dbc.Row(
    [
        dbc.Col([upload_card, new_data_card], width=12, md=4, lg=3),
        dbc.Col(data_table_card, width=12, md=8, lg=9),
    ]
)

# --- App Layout Assembly ---

content_container = html.Div(id="tabs-content")
store = dcc.Store(id='stored-data')
download_component = dcc.Download(id="download-dataframe-xlsx")

app.layout = html.Div(
    [
        store,
        download_component,
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
        'fontFamily': "'Verdana', sans-serif",
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

# Callback to manage data store (Upload + Add Row + Clear)
@app.callback(
    Output('stored-data', 'data'),
    [Input('upload-data', 'contents'),
     Input('btn-add-row', 'n_clicks'),
     Input('btn-clear', 'n_clicks')],
    [State('upload-data', 'filename'),
     State('input-name', 'value'),
     State('input-age', 'value'),
     State('stored-data', 'data')]
)
def update_store(contents, n_add, n_clear, filename, name, age, current_data):
    trigger_id = ctx.triggered_id

    if trigger_id == 'btn-clear':
        return None

    if trigger_id == 'upload-data':
        if contents:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                if filename.endswith('.xlsx'):
                    df = pd.read_excel(io.BytesIO(decoded))
                    # Ensure columns exist if empty
                    if 'Name' not in df.columns: df['Name'] = []
                    if 'Age' not in df.columns: df['Age'] = []
                    return df.to_dict('records')
            except Exception as e:
                print(f"Error processing file: {e}")
                return no_update

    if trigger_id == 'btn-add-row':
        if name and age is not None:
            new_row = {'Name': name, 'Age': age} # Assuming columns are Name/Age as per request
            if current_data:
                df = pd.DataFrame(current_data)
                # If columns don't match, we align them or just append
                # For simplicity, assuming the uploaded excel matches or we are starting fresh
                new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                return new_df.to_dict('records')
            else:
                # Start fresh if no data exists
                return [new_row]

    return no_update

# Callback to update table from store
@app.callback(
    Output('table-container', 'children'),
    Input('stored-data', 'data')
)
def update_table(data):
    if not data:
        return html.Div(
            [
                html.H5("Nenhum dado carregado", className="text-muted"),
                html.P("Faça o upload de uma planilha ou adicione dados manualmente.", className="text-muted small")
            ],
            className="text-center mt-5"
        )

    df = pd.DataFrame(data)

    # Ensure columns are in a good order if possible, or just default
    cols = [{"name": i, "id": i} for i in df.columns]

    return dash_table.DataTable(
        data=data,
        columns=cols,
        page_size=10,
        style_table={'overflowX': 'auto', 'borderRadius': '8px', 'border': '1px solid #dee2e6'},
        style_cell={
            'textAlign': 'left',
            'fontFamily': "'Verdana', sans-serif",
            'padding': '12px',
            'fontSize': '0.9rem',
            'color': '#495057'
        },
        style_header={
            'backgroundColor': GOV_THEME['AZUL_ATLANTICO'],
            'color': 'white',
            'fontWeight': 'bold',
            'border': 'none',
            'padding': '12px'
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

# Callback to download data
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn-download", "n_clicks"),
    State("stored-data", "data"),
    prevent_initial_call=True,
)
def download_data(n_clicks, data):
    if not data:
        return no_update

    df = pd.DataFrame(data)
    return dcc.send_data_frame(df.to_excel, "dados_atualizados.xlsx", index=False)

def view():
    app.run(debug=True)
