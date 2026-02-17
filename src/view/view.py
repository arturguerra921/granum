import base64
import io
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, no_update
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
                        dbc.Col(html.Img(src="/assets/logo.png", height="60px"), className="me-3"),
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
# Using simple bootstrap tabs.
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
            className="bg-white text-primary fw-bold border-0 pt-3",
            style={"color": GOV_THEME['AZUL_ATLANTICO']}
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
                        'height': '150px',
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
                html.Div(className="d-grid gap-2 mt-4", children=[
                    dbc.Button(
                        "Validar Dados",
                        id='btn-validate',
                        className="fw-bold border-0",
                        style={"backgroundColor": GOV_THEME['VERDE_AMAZONIA']}
                    ),
                    dbc.Button(
                        "Limpar",
                        id='btn-clear',
                        outline=True,
                        color="secondary"
                    ),
                ])
            ]
        ),
    ],
    className="shadow-sm border-0 h-100",
    style={"borderRadius": "10px"}
)

# Data Table Card
data_table_card = dbc.Card(
    [
        dbc.CardHeader(
            "Visualização dos Dados",
            className="bg-white text-primary fw-bold border-0 pt-3",
            style={"color": GOV_THEME['AZUL_ATLANTICO']}
        ),
        dbc.CardBody(
            [
                dbc.Spinner(
                    html.Div(id='table-container', children=[
                        # Placeholder text will appear here
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
        dbc.Col(upload_card, width=12, md=4, lg=3, className="mb-4"),
        dbc.Col(data_table_card, width=12, md=8, lg=9, className="mb-4"),
    ]
)

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

@app.callback(
    Output('table-container', 'children'),
    [Input('upload-data', 'contents'),
     Input('btn-clear', 'n_clicks')],
    [State('upload-data', 'filename')]
)
def update_table(contents, n_clicks, filename):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default state
        return html.Div(
            [
                html.H5("Nenhum dado carregado", className="text-muted"),
                html.P("Faça o upload de uma planilha Excel para visualizar os dados aqui.", className="text-muted small")
            ],
            className="text-center mt-5"
        )

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'btn-clear':
        # Clear button pressed
        return html.Div(
            [
                html.H5("Nenhum dado carregado", className="text-muted"),
                html.P("Faça o upload de uma planilha Excel para visualizar os dados aqui.", className="text-muted small")
            ],
            className="text-center mt-5"
        )

    if contents is None:
         # Should catch cases where trigger is upload but contents are None (rare)
         return no_update

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(decoded))

            # Simple styling for the DataTable
            return dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
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
        else:
            return dbc.Alert("Erro: O arquivo deve ser um Excel (.xlsx).", color="danger")
    except Exception as e:
        print(f"Error processing file: {e}")
        return dbc.Alert("Ocorreu um erro ao processar o arquivo.", color="danger")

def view():
    app.run(debug=True)
