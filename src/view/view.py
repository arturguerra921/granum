import base64
import io
import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from src.view.theme import UNB_THEME
from src.logic.valhalla.client import ValhallaClient
import dash

# --- Data Loading ---
try:
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'data')
    MUNICIPIOS_PATH = os.path.join(DATA_DIR, 'municipios.csv')
    ESTADOS_PATH = os.path.join(DATA_DIR, 'estados.csv')
    BASE_ARMAZENS_PATH = os.path.join(DATA_DIR, 'Armazens_Credenciados_Habilitados_Base.csv')

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

# Initialize Valhalla Client
valhalla_client = ValhallaClient()

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
        dbc.Tab(label="Armazéns", tab_id="tab-armazens", label_class_name="px-4"),
        dbc.Tab(label="Produto e Armazéns", tab_id="tab-prod-armazens", label_class_name="px-4"),
        dbc.Tab(label="Matriz de Distâncias", tab_id="tab-matrix", label_class_name="px-4"),
        dbc.Tab(label="Configuração do Modelo", tab_id="tab-config", label_class_name="px-4"),
        dbc.Tab(label="Resultados", tab_id="tab-results", label_class_name="px-4"),
    ],
    id="main-tabs",
    active_tab="tab-input",
    className="mb-32"
)

# 3. Tab 1 Content (Input)
def get_tab1_layout():
    # Upload Card
    upload_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Carregar Arquivo", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-upload", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Caso já possua uma planilha pronta (Excel .xlsx ou CSV), carregue-a aqui. Se não tiver, você pode adicionar dados manualmente abaixo.",
                        target="help-upload",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.Div("📂", style={"fontSize": "2rem", "marginBottom": "8px"}),
                            html.Span('Arraste e solte ou ', style={"color": UNB_THEME['UNB_GRAY_DARK']}),
                            html.A('Selecione', className="fw-bold text-decoration-underline", style={"color": UNB_THEME['UNB_BLUE']}),
                            html.Div("Formatos: .xlsx, .csv", className="text-muted small mt-2")
                        ]),
                        className="upload-box",
                        multiple=False,
                        accept='.xlsx, .csv'
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
                html.Div([
                    html.Span("Adicionar Dados", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-add", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Inserção manual de dados. Cada inserção será adicionada como uma nova linha na tabela ao lado.",
                        target="help-add",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    html.P("Adicione uma nova linha à planilha carregada.", className="text-muted small mb-16"),
                    dbc.Row([
                        dbc.Col(
                            [
                                html.Div([
                                    dbc.Label("Produto", className="fw-bold small me-2 mb-0"),
                                    html.I(className="bi bi-question-circle-fill text-muted", id="help-produto", style={"cursor": "help", "fontSize": "0.9rem"}),
                                    dbc.Tooltip(
                                        "Nome do produto (ex: Soja, Milho). O sistema ajustará maiúsculas/minúsculas automaticamente e sugerirá produtos já cadastrados.",
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
                                    dbc.Label("Peso (Kg)", className="fw-bold small me-2 mb-0"),
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
                                    dbc.Label("Cidade", className="fw-bold small me-2 mb-0"),
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
                                    dbc.Label("Latitude", className="fw-bold small me-2 mb-0"),
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
                                    dbc.Label("Longitude", className="fw-bold small me-2 mb-0"),
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
                html.Div([
                    html.Span("Exportar", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-export", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Salvar a planilha para usos futuros. Não é necessário exportar para continuar usando as funcionalidades nesta sessão.",
                        target="help-export",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
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
    ])

# 4. Tab Armazéns Content
def get_tab_armazens_layout():
    # Card 1: Load
    card_load_restore = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Visualizar Base", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-load-base", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Tabela automaticamente mostrada ao lado. Essa forma foi utilizada para evitar que sempre precise fazer upload dos armazéns, guardando no próprio aplicativo.",
                        target="help-load-base",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    dbc.Button("Puxar da Base", id="btn-load-base", className="btn-primary-custom mb-2 w-100"),
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom mb-3"
    )

    # Card 2: Update and Save
    card_update_save = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Gerenciar Base", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-manage-base", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Essa função guardará a nova versão que será enviada para os futuros usos do aplicativo, substituindo a base que hoje é carregada automaticamente.",
                        target="help-manage-base",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    dbc.Button("Atualizar a Base", id="btn-update-base", color="info", className="w-100 mb-2 text-white", style={"backgroundColor": "#17a2b8", "borderColor": "#17a2b8"}),
                    # Upload Component (Initially Hidden)
                    html.Div(
                        id="upload-update-container",
                        children=[
                            dcc.Upload(
                                id='upload-update-base',
                                children=html.Div([
                                    html.Div("📂", style={"fontSize": "2rem", "marginBottom": "8px"}),
                                    html.Span('Arraste e solte ou ', style={"color": UNB_THEME['UNB_GRAY_DARK']}),
                                    html.A('Selecione', className="fw-bold text-decoration-underline", style={"color": UNB_THEME['UNB_BLUE']}),
                                    html.Div("Formatos: .csv", className="text-muted small mt-2")
                                ]),
                                className="upload-box",
                                multiple=False,
                                accept='.csv'
                            )
                        ],
                        style={"display": "none"}
                    ),

                    # Salvar na base (Initially Hidden)
                    dbc.Button("Salvar na Base", id="btn-save-base", className="btn-success-custom w-100 mt-4", style={"display": "none"}),
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom h-100"
    )

    # Metrics Section for Armazéns
    armazens_metrics_section = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.I(className="bi bi-building-fill fs-1 me-3", style={"color": UNB_THEME['UNB_BLUE']}),
                                    html.Div(
                                        [
                                            html.H6("Unidades Armazenadoras", className="text-muted small text-uppercase fw-bold mb-1"),
                                            html.H3(id="metric-armazens-count", children="0", className="mb-0", style={"color": UNB_THEME['UNB_BLUE']})
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
                                    html.I(className="bi bi-bank2 fs-1 me-3", style={"color": "#FFC107"}), # Warning/Yellow color
                                    html.Div(
                                        [
                                            html.H6("Unidades Armazenadoras Públicas", className="text-muted small text-uppercase fw-bold mb-1"),
                                            html.H3(id="metric-armazens-public", children="0", className="mb-0", style={"color": "#FFC107"})
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
                                    html.I(className="bi bi-buildings-fill fs-1 me-3", style={"color": "#6C757D"}), # Secondary/Gray color
                                    html.Div(
                                        [
                                            html.H6("Unidades Armazenadoras Privadas", className="text-muted small text-uppercase fw-bold mb-1"),
                                            html.H3(id="metric-armazens-private", children="0", className="mb-0", style={"color": "#6C757D"})
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
                                    html.I(className="bi bi-box-seam-fill fs-1 me-3", style={"color": UNB_THEME['UNB_GREEN']}),
                                    html.Div(
                                        [
                                            html.H6("Capacidade Estática (t)", className="text-muted small text-uppercase fw-bold mb-1"),
                                            html.H3(id="metric-armazens-capacity", children="0.00", className="mb-0", style={"color": UNB_THEME['UNB_GREEN']})
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
        className="mt-auto pt-3 g-3"
    )

    # Armazens Table Card
    armazens_table_card = dbc.Card(
        [
            dbc.CardHeader(
                "Tabela de Armazéns Credenciados",
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                     dbc.Spinner(
                        html.Div(id='table-armazens-container', children=[
                            dash_table.DataTable(
                                id='table-armazens',
                                data=[],
                                columns=[],
                                editable=False,
                                row_deletable=False,
                                filter_action='native',
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
                                    'backgroundColor': '#F8F9FA',
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
                    armazens_metrics_section
                ],
                className="card-body-custom d-flex flex-column"
            ),
        ],
        className="card-custom h-100",
        style={"minHeight": "600px"}
    )

    # Modals
    tutorial_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Como Atualizar a Base"), close_button=True),
            dbc.ModalBody(
                [
                    html.P("Siga os passos abaixo para atualizar a base de armazéns:"),
                    html.Ol([
                        html.Li([
                            "Acesse o link: ",
                            html.A("Consulta Conab", href="https://consultaweb.conab.gov.br/consultas/consultaArmazem.do?method=acaoCarregarConsulta", target="_blank")
                        ]),
                        html.Li("Marque apenas a opção 'Armazéns Credenciados'."),
                        html.Li("Deixe os outros campos em branco."),
                        html.Li("Preencha o código de segurança e clique em 'Consultar'."),
                        html.Li("No final da página de resultados, exporte ou salve a tabela como arquivo CSV."),
                        html.Li("Carregue o arquivo CSV na área que aparecerá após fechar esta janela.")
                    ]),
                    html.Img(src="/assets/data/Tutorial_Atualizar_Armazens.png", style={"width": "100%", "marginTop": "10px", "borderRadius": "8px", "border": "1px solid #ddd"})
                ]
            ),
            dbc.ModalFooter(
                dbc.Button("Entendi", id="close-modal-tutorial", className="ms-auto", n_clicks=0)
            ),
        ],
        id="modal-tutorial",
        size="lg",
        is_open=False,
    )

    confirm_save_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Confirmar Salvamento"), close_button=True),
            dbc.ModalBody("Atenção: Esta ação irá sobrescrever a base de dados original de forma irreversível. O aplicativo será reiniciado e todo seu progresso será perdido. Caso tenha feito trabalho na página de adição de produtos, volte e salve a planilha de produtos para fazer o upload novamente após a reinicialização."),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancelar", id="cancel-save", className="me-2", n_clicks=0),
                    dbc.Button("Confirmar e Salvar", id="confirm-save", color="danger", n_clicks=0),
                ]
            ),
        ],
        id="modal-confirm-save",
        is_open=False,
    )

    return html.Div([
        dbc.Row(
            [
                dbc.Col([
                    html.Div(card_load_restore, className="mb-3"),
                    html.Div(card_update_save, className="flex-grow-1 h-100")
                ], width=12, lg=3, className="mb-24 d-flex flex-column h-100"),
                dbc.Col(armazens_table_card, width=12, lg=9, className="mb-24"),
            ]
        ),
        tutorial_modal,
        confirm_save_modal
    ])

# 5. Tab Produto e Armazéns Content
def get_tab_prod_armazens_layout():
    # Table Card
    table_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Relação Produto x Tipo de Armazém", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-prod-armazens", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Selecione quais tipos de armazém podem armazenar cada produto. Clique na célula para marcar (☑) ou desmarcar (☐).",
                        target="help-prod-armazens",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    dbc.Spinner(
                        html.Div(id='table-prod-armazens-container', children=[
                            dash_table.DataTable(
                                id='table-prod-armazens',
                                data=[],
                                columns=[{'name': 'Produto', 'id': 'Produto'}], # Initial column
                                editable=False, # We handle clicks via active_cell
                                row_deletable=False,
                                page_size=15,
                                style_table={'overflowX': 'auto', 'borderRadius': '8px', 'border': f"1px solid {UNB_THEME['BORDER_LIGHT']}"},
                                style_cell={
                                    'textAlign': 'center',
                                    'fontFamily': "'Roboto', sans-serif",
                                    'padding': '12px',
                                    'fontSize': '0.9rem',
                                    'color': UNB_THEME['UNB_GRAY_DARK']
                                },
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'Produto'},
                                        'textAlign': 'left',
                                        'fontWeight': 'bold'
                                    }
                                ],
                                style_header={
                                    'backgroundColor': '#F8F9FA',
                                    'color': UNB_THEME['UNB_BLUE'],
                                    'fontWeight': 'bold',
                                    'border': 'none',
                                    'padding': '12px',
                                    'borderBottom': f"2px solid {UNB_THEME['BORDER_LIGHT']}",
                                    'textAlign': 'center'
                                },
                                style_data={
                                    'borderBottom': f"1px solid {UNB_THEME['BORDER_LIGHT']}",
                                    'cursor': 'pointer',
                                    'fontSize': '1.5rem', # Checkbox size
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': '#f8f9fa'
                                    },
                                    {
                                        'if': {'column_id': 'Produto'},
                                        'fontSize': '0.9rem' # Product name size
                                    }
                                ]
                            )
                        ], className="h-100"),
                        color="primary"
                    ),
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom h-100",
        style={"minHeight": "600px"}
    )

    # Missing Data Modal
    missing_data_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Atenção"), close_button=False),
            dbc.ModalBody(id="modal-missing-data-body", children="Faltam dados."),
            dbc.ModalFooter(
                dbc.Button("Confirmar", id="btn-confirm-missing-data", className="ms-auto", n_clicks=0)
            ),
        ],
        id="modal-missing-data",
        is_open=False,
        backdrop="static", # Prevent closing by clicking outside
        keyboard=False
    )

    return html.Div([
        dbc.Row(
            [
                dbc.Col(table_card, width=12, className="mb-24"),
            ]
        ),
        missing_data_modal
    ])

# 6. Tab Matrix Content
def get_tab_matrix_layout():
    control_card = dbc.Card(
        [
            dbc.CardHeader("Controle da Matriz", className="card-header-custom"),
            dbc.CardBody(
                [
                    html.P("Clique no botão abaixo para calcular a matriz de distâncias e visualizar as rotas para o armazém mais distante de cada origem.", className="text-muted small mb-3"),
                    dbc.Button("Calcular Matriz", id="btn-calc-matrix", className="btn-primary-custom w-100 mb-3"),
                    html.Div(id="matrix-status", className="text-muted small")
                ],
                className="card-body-custom"
            )
        ],
        className="card-custom h-100 mb-3"
    )

    map_card = dbc.Card(
        [
            dbc.CardHeader("Visualização das Rotas (Nó Mais Distante)", className="card-header-custom"),
            dbc.CardBody(
                dbc.Spinner(
                    dcc.Graph(id="matrix-map", style={"height": "600px"}),
                    color="primary"
                ),
                className="card-body-custom p-0" # No padding for map
            )
        ],
        className="card-custom h-100"
    )

    return html.Div([
        dbc.Row(
            [
                dbc.Col(control_card, width=12, lg=3),
                dbc.Col(map_card, width=12, lg=9),
            ]
        )
    ])


# Error Modal (Global)
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

# --- App Layout Assembly ---

# Pre-render all tab layouts to ensure IDs exist for callbacks
tab1_layout = get_tab1_layout()
tab2_layout = get_tab_armazens_layout()
tab_prod_armazens_layout = get_tab_prod_armazens_layout()
tab_matrix_layout = get_tab_matrix_layout()
tab3_layout = html.H3('Configuração do Modelo (Placeholder)', className="text-center mt-48 text-muted")
tab4_layout = html.H3('Resultados (Placeholder)', className="text-center mt-48 text-muted")

content_container = html.Div(
    [
        html.Div(id="tab-input-container", children=tab1_layout, style={"display": "block"}),
        html.Div(id="tab-armazens-container", children=tab2_layout, style={"display": "none"}),
        html.Div(id="tab-prod-armazens-container", children=tab_prod_armazens_layout, style={"display": "none"}),
        html.Div(id="tab-matrix-container", children=tab_matrix_layout, style={"display": "none"}),
        html.Div(id="tab-config-container", children=tab3_layout, style={"display": "none"}),
        html.Div(id="tab-results-container", children=tab4_layout, style={"display": "none"}),
    ],
    id="tabs-content"
)

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
                dcc.Store(id='store-armazens'), # New Store for Armazéns
                dcc.Store(id='store-prod-armazens'), # New Store for Prod x Armazens
                dcc.Store(id='store-matrix-routes'), # Store for map routes
                dcc.Download(id='download-dataframe-xlsx'),
                error_modal
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
    [Output("tab-input-container", "style"),
     Output("tab-armazens-container", "style"),
     Output("tab-prod-armazens-container", "style"),
     Output("tab-matrix-container", "style"),
     Output("tab-config-container", "style"),
     Output("tab-results-container", "style")],
    Input("main-tabs", "active_tab")
)
def render_content(active_tab):
    styles = [{"display": "none"}] * 6
    if active_tab == 'tab-input':
        styles[0] = {"display": "block"}
    elif active_tab == 'tab-armazens':
        styles[1] = {"display": "block"}
    elif active_tab == 'tab-prod-armazens':
        styles[2] = {"display": "block"}
    elif active_tab == 'tab-matrix':
        styles[3] = {"display": "block"}
    elif active_tab == 'tab-config':
        styles[4] = {"display": "block"}
    elif active_tab == 'tab-results':
        styles[5] = {"display": "block"}
    return styles

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
            elif filename.endswith('.csv'):
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            else:
                return no_update, True, "O arquivo deve ser Excel (.xlsx) ou CSV (.csv)."

            # Normalize "Produto" column if it exists
            if "Produto" in df.columns:
                 df["Produto"] = df["Produto"].fillna('').astype(str).str.title()

            return df.to_json(date_format='iso', orient='split'), False, no_update
        except Exception as e:
            print(f"Error processing file: {e}")
            return no_update, True, "Erro ao processar o arquivo. Verifique se é um arquivo válido."

    # Add Row
    if trigger_id == 'btn-add-row':
        if stored_data:
             df = pd.read_json(io.StringIO(stored_data), orient='split')
        else:
             df = pd.DataFrame(columns=["Produto", "Peso (Kg)", "Cidade", "Latitude", "Longitude"])

        if not prod_val or not peso_val or not cidade_val:
             return no_update, True, "Preencha Produto, Peso e Cidade para adicionar."

        try:
            # Normalize Product Name (Title Case)
            # Use title() which capitalizes first letter of each word
            prod_val_normalized = str(prod_val).title()

            new_row_data = {
                'Produto': prod_val_normalized,
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

            # Normalize "Produto" column on edit
            if "Produto" in df.columns:
                 df["Produto"] = df["Produto"].fillna('').astype(str).str.title()

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


# --- Armazéns Callbacks ---

# 4. Load Data to Store (and Handle Restore)
@app.callback(
    Output('store-armazens', 'data'),
    Output('error-modal', 'is_open', allow_duplicate=True),
    Output('modal-body-content', 'children', allow_duplicate=True),
    Output('btn-save-base', 'style'), # New output for Save button visibility
    [Input('main-tabs', 'active_tab'),
     Input('btn-load-base', 'n_clicks'),
     Input('upload-update-base', 'contents'),
     Input('table-armazens', 'data_timestamp')],
    [State('store-armazens', 'data'),
     State('table-armazens', 'data'),
     State('upload-update-base', 'filename')],
    prevent_initial_call=True
)
def manage_armazens_data(active_tab, n_load, upload_contents, timestamp,
                         stored_data, table_data, upload_filename):
    ctx = dash.callback_context
    if not ctx.triggered:
         # Initial Load if tab is active
        if active_tab == 'tab-armazens' and not stored_data:
             try:
                # Load CSV
                df = pd.read_csv(BASE_ARMAZENS_PATH, sep=';', encoding='iso-8859-1', skiprows=1, index_col=False)

                # Drop trailing empty column if exists
                if not df.empty and "Unnamed" in str(df.columns[-1]):
                    df = df.iloc[:, :-1]

                return df.to_json(date_format='iso', orient='split'), no_update, no_update, no_update
             except Exception:
                return no_update, no_update, no_update, no_update
        return no_update, no_update, no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Load from Base
    if trigger_id == 'main-tabs' and active_tab == 'tab-armazens':
        # Only load if store is empty to preserve session edits, or if we want to force reload?
        # Requirement: "load automatico". If user edited and switched tabs, we should probably keep edits.
        # But if it's the first load, we need data.
        if not stored_data:
            try:
                # Load CSV
                df = pd.read_csv(BASE_ARMAZENS_PATH, sep=';', encoding='iso-8859-1', skiprows=1, index_col=False)

                # Drop trailing empty column if exists
                if not df.empty and "Unnamed" in str(df.columns[-1]):
                    df = df.iloc[:, :-1]

                return df.to_json(date_format='iso', orient='split'), no_update, no_update, no_update
            except Exception:
                return no_update, no_update, no_update, no_update
        return no_update, no_update, no_update, no_update # Keep current state

    if trigger_id == 'btn-load-base':
        try:
            # Load CSV
            df = pd.read_csv(BASE_ARMAZENS_PATH, sep=';', encoding='iso-8859-1', skiprows=1, index_col=False)

            # Drop trailing empty column if exists
            if not df.empty and "Unnamed" in str(df.columns[-1]):
                df = df.iloc[:, :-1]

            return df.to_json(date_format='iso', orient='split'), no_update, no_update, no_update
        except Exception:
            return no_update, True, "Erro ao carregar a base de dados.", no_update

    # Update from Upload (CSV)
    if trigger_id == 'upload-update-base' and upload_contents:
        content_type, content_string = upload_contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            # Conab CSV Parsing Rules:
            # 1. Encoding: iso-8859-1
            # 2. Separator: ;
            # 3. Skip Rows: 1 (Header is on line 2, index 1)
            # 4. Trailing Delimiter: Drop last column

            # Decode using iso-8859-1
            decoded_str = decoded.decode('iso-8859-1')

            df = pd.read_csv(
                io.StringIO(decoded_str),
                sep=';',
                encoding='iso-8859-1',
                skiprows=1,
                index_col=False
            )

            # Drop the last column if it's completely empty (result of trailing delimiter)
            # The last column is usually 'Unnamed: X' due to the trailing delimiter
            if not df.empty:
                # Drop columns that are entirely null (fixes trailing delimiter issue)
                df = df.dropna(axis=1, how='all')

                # Also drop if the last column is explicitly unnamed (fallback)
                if not df.empty and "Unnamed" in str(df.columns[-1]):
                     df = df.iloc[:, :-1]

            if df is not None:
                return df.to_json(date_format='iso', orient='split'), no_update, no_update, {"display": "block"}
            else:
                return no_update, True, "Arquivo vazio ou inválido.", no_update

        except Exception as e:
            print(f"Error reconstruction: {e}")
            return no_update, True, f"Erro ao processar arquivo: {e}", no_update

    # Table Edits (should be disabled now but keeping fallback logic)
    if trigger_id == 'table-armazens':
        if table_data:
             df = pd.DataFrame(table_data)
             return df.to_json(date_format='iso', orient='split'), no_update, no_update, no_update
        return no_update, no_update, no_update, no_update

    return no_update, no_update, no_update, no_update

# 5. Render Armazéns Table and Metrics
@app.callback(
    Output('table-armazens', 'data'),
    Output('table-armazens', 'columns'),
    Output('metric-armazens-count', 'children'),
    Output('metric-armazens-capacity', 'children'),
    Output('metric-armazens-public', 'children'),
    Output('metric-armazens-private', 'children'),
    Input('store-armazens', 'data')
)
def update_armazens_table_view(stored_data):
    if not stored_data:
        return [], [], "0", "0.00", "0", "0"

    try:
        df = pd.read_json(io.StringIO(stored_data), orient='split')
        columns = [{'name': i, 'id': i, 'deletable': False, 'renamable': False} for i in df.columns]

        # Calculate Metrics
        count = len(df)

        # Try to find capacity column (case insensitive partial match)
        capacity = 0
        cap_col = next((c for c in df.columns if 'cap' in str(c).lower() or 'ton' in str(c).lower()), None)

        if cap_col:
            # Clean and convert to numeric
            try:
                # Force to string first to handle mixed types or already parsed floats
                series_str = df[cap_col].astype(str)

                # Check if it looks like Brazilian format (1.000,00)
                # Remove thousands separator (.) and replace decimal separator (,) with (.)
                series_clean = series_str.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)

                capacity = pd.to_numeric(series_clean, errors='coerce').sum()
            except:
                capacity = 0

        # Calculate Public vs Private
        # Requirement: Public = "Armazenador" == "COMPANHIA NACIONAL DE ABASTECIMENTO"
        # Private = All others
        public_count = 0
        private_count = 0

        armazenador_col = next((c for c in df.columns if 'armazenador' in str(c).lower()), None)
        if armazenador_col:
             public_mask = df[armazenador_col].astype(str).str.upper() == "COMPANHIA NACIONAL DE ABASTECIMENTO"
             public_count = public_mask.sum()
             private_count = len(df) - public_count

        # Format for display
        count_str = f"{count}"
        capacity_str = f"{capacity:,.2f}"
        public_str = f"{public_count}"
        private_str = f"{private_count}"

        return df.to_dict('records'), columns, count_str, capacity_str, public_str, private_str
    except Exception:
        return [], [], "0", "0.00", "0", "0"

# 6. Save Confirmation Modal
@app.callback(
    Output("modal-confirm-save", "is_open"),
    [Input("btn-save-base", "n_clicks"),
     Input("confirm-save", "n_clicks"),
     Input("cancel-save", "n_clicks")],
    [State("modal-confirm-save", "is_open"),
     State('store-armazens', 'data')]
)
def toggle_save_modal(n_save, n_confirm, n_cancel, is_open, stored_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "btn-save-base":
        return True

    if trigger_id == "cancel-save":
        return False

    if trigger_id == "confirm-save":
        # Execute Save
        if stored_data:
            try:
                df = pd.read_json(io.StringIO(stored_data), orient='split')
                # Save as CSV with header
                with open(BASE_ARMAZENS_PATH, 'w', encoding='iso-8859-1') as f:
                    f.write("Armazéns Credenciados e Habilitados\n")
                    df.to_csv(f, sep=';', index=False, lineterminator='\n')
            except Exception as e:
                print(f"Error saving: {e}")
        return False

    return is_open


# 8. Tutorial Modal and Upload Visibility
@app.callback(
    Output("modal-tutorial", "is_open"),
    Output("upload-update-container", "style"),
    [Input("btn-update-base", "n_clicks"),
     Input("close-modal-tutorial", "n_clicks")],
    [State("modal-tutorial", "is_open")]
)
def toggle_tutorial_modal(n_update, n_close, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, {"display": "none"}

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "btn-update-base":
        return True, {"display": "block"} # Open modal, SHOW upload

    if trigger_id == "close-modal-tutorial":
        return False, {"display": "block"} # Close modal, keep upload shown

    return is_open, {"display": "none"}

# 9. Validation for Tab Prod x Armazens
@app.callback(
    Output("modal-missing-data", "is_open"),
    Output("modal-missing-data-body", "children"),
    Input("main-tabs", "active_tab"),
    [State('stored-data', 'data'),
     State('store-armazens', 'data')]
)
def validate_tab_prod_armazens(active_tab, stored_data, stored_armazens):
    if active_tab != 'tab-prod-armazens':
        return False, no_update

    # Check Products
    has_prod = False
    if stored_data:
        try:
            df = pd.read_json(io.StringIO(stored_data), orient='split')
            if not df.empty and "Produto" in df.columns:
                has_prod = True
        except:
            pass

    # Check Armazens
    has_armazens = False
    if stored_armazens:
        try:
            df = pd.read_json(io.StringIO(stored_armazens), orient='split')
            if not df.empty:
                has_armazens = True
        except:
            pass

    if not has_prod and not has_armazens:
        return True, "Você precisa adicionar produtos na aba 'Entrada de Dados' e carregar a base na aba 'Armazéns' antes de prosseguir."
    elif not has_prod:
        return True, "Você precisa adicionar pelo menos um produto na aba 'Entrada de Dados' antes de prosseguir."
    elif not has_armazens:
        return True, "Você precisa carregar a base de dados na aba 'Armazéns' antes de prosseguir."

    return False, no_update

# 10. Redirection from Modal
@app.callback(
    Output("main-tabs", "active_tab"),
    Output("modal-missing-data", "is_open", allow_duplicate=True),
    Input("btn-confirm-missing-data", "n_clicks"),
    [State('stored-data', 'data'),
     State('store-armazens', 'data')],
    prevent_initial_call=True
)
def redirect_missing_data(n_clicks, stored_data, stored_armazens):
    if not n_clicks:
        return no_update, no_update

    # Check Products
    has_prod = False
    if stored_data:
        try:
            df = pd.read_json(io.StringIO(stored_data), orient='split')
            if not df.empty and "Produto" in df.columns:
                has_prod = True
        except:
            pass

    # Check Armazens
    has_armazens = False
    if stored_armazens:
        try:
            df = pd.read_json(io.StringIO(stored_armazens), orient='split')
            if not df.empty:
                has_armazens = True
        except:
            pass

    if not has_prod:
        return 'tab-input', False
    elif not has_armazens:
        return 'tab-armazens', False

    return no_update, False


# 11. Populate Product x Armazens Table and Sync Store
@app.callback(
    Output('store-prod-armazens', 'data'),
    Output('table-prod-armazens', 'data'),
    Output('table-prod-armazens', 'columns'),
    Input('main-tabs', 'active_tab'),
    Input('stored-data', 'data'),
    Input('store-armazens', 'data'),
    State('store-prod-armazens', 'data')
)
def update_prod_armazens_table(active_tab, stored_data, stored_armazens, stored_matrix):
    if active_tab != 'tab-prod-armazens':
        return no_update, no_update, no_update

    # 1. Get Unique Products
    products = []
    if stored_data:
        try:
            df_prod = pd.read_json(io.StringIO(stored_data), orient='split')
            if not df_prod.empty and "Produto" in df_prod.columns:
                products = sorted(df_prod["Produto"].dropna().unique().astype(str).tolist())
        except Exception as e:
            print(f"Error reading products: {e}")

    # 2. Get Unique Warehouse Types
    types = []
    if stored_armazens:
        try:
            df_arm = pd.read_json(io.StringIO(stored_armazens), orient='split')
            if not df_arm.empty and "Tipo" in df_arm.columns:
                types = sorted(df_arm["Tipo"].dropna().unique().astype(str).tolist())
        except Exception as e:
            print(f"Error reading types: {e}")

    if not products or not types:
        return no_update, [], []

    # 3. Load or Initialize Matrix
    try:
        if stored_matrix:
            df_matrix = pd.read_json(io.StringIO(stored_matrix), orient='split')
        else:
            df_matrix = pd.DataFrame(columns=['Produto'])
    except:
        df_matrix = pd.DataFrame(columns=['Produto'])

    # 4. Sync Logic
    # We want a DataFrame with rows = products, columns = ['Produto'] + types
    new_matrix = pd.DataFrame({'Produto': products})

    # For each type column, preserve existing values if possible
    for t in types:
        if t in df_matrix.columns:
            # Create lookup: Product -> Value for this type
            # We need to handle potential duplicates in df_matrix if something went wrong, but set_index should be fine if unique
            try:
                # Drop duplicates in old matrix just in case
                lookup = df_matrix.drop_duplicates(subset=['Produto']).set_index('Produto')[t].to_dict()
                new_matrix[t] = new_matrix['Produto'].map(lookup).fillna('☐')
            except:
                new_matrix[t] = '☐'
        else:
            new_matrix[t] = '☐'

    # 5. Prepare Output
    columns = [
        {'name': 'Produto', 'id': 'Produto', 'editable': False}
    ] + [
        {'name': t, 'id': t, 'editable': False} for t in types
    ]

    return new_matrix.to_json(date_format='iso', orient='split'), new_matrix.to_dict('records'), columns


# 12. Handle Checkbox Toggles
@app.callback(
    Output('store-prod-armazens', 'data', allow_duplicate=True),
    Output('table-prod-armazens', 'data', allow_duplicate=True),
    Output('table-prod-armazens', 'active_cell'),
    Input('table-prod-armazens', 'active_cell'),
    State('table-prod-armazens', 'data'),
    prevent_initial_call=True
)
def toggle_checkbox(active_cell, table_data):
    if not active_cell or not table_data:
        return no_update, no_update, no_update

    row_idx = active_cell['row']
    col_id = active_cell['column_id']

    # Ignore clicks on "Produto" column
    if col_id == 'Produto':
        return no_update, no_update, None

    try:
        df = pd.DataFrame(table_data)

        # Toggle Logic
        current_val = df.at[row_idx, col_id]
        if current_val == '☐':
            new_val = '☑'
        else:
            new_val = '☐'

        df.at[row_idx, col_id] = new_val

        return df.to_json(date_format='iso', orient='split'), df.to_dict('records'), None

    except Exception as e:
        print(f"Error toggling checkbox: {e}")
        return no_update, no_update, None

# 13. Calculate Matrix and Routes
@app.callback(
    Output("matrix-status", "children"),
    Output("store-matrix-routes", "data"),
    Input("btn-calc-matrix", "n_clicks"),
    State("stored-data", "data"), # Origins
    State("store-armazens", "data"), # Destinations
    prevent_initial_call=True
)
def calculate_matrix_logic(n_clicks, stored_input, stored_armazens):
    if not n_clicks:
        return no_update, no_update

    if not stored_input or not stored_armazens:
        return "Dados insuficientes (Origens ou Destinos faltando).", no_update

    try:
        # Load Data
        df_origins = pd.read_json(io.StringIO(stored_input), orient='split')
        df_dests = pd.read_json(io.StringIO(stored_armazens), orient='split')

        if df_origins.empty or df_dests.empty:
            return "Dados insuficientes.", no_update

        # Filter Valid Coords
        # We need unique locations from origins (many rows might be same city)
        # Drop duplicates by Lat/Lon
        origins_unique = df_origins.drop_duplicates(subset=['Latitude', 'Longitude'])

        # Prepare Locations for Valhalla
        origins_payload = []
        for _, row in origins_unique.iterrows():
            origins_payload.append({"lat": row['Latitude'], "lon": row['Longitude']})

        dests_payload = []
        # Keep track of indices to map back to warehouse info
        dest_mapping = []
        for i, row in df_dests.iterrows():
            # Assuming Lat/Lon columns exist in Armazens base
            # Standard Conab CSV usually has 'LATITUDE' and 'LONGITUDE' or similar
            # Let's try to find them case-insensitive
            lat_col = next((c for c in df_dests.columns if 'lat' in str(c).lower()), None)
            lon_col = next((c for c in df_dests.columns if 'lon' in str(c).lower()), None)

            if lat_col and lon_col:
                # Clean coords (replace comma with dot if string)
                try:
                    lat = float(str(row[lat_col]).replace(',', '.'))
                    lon = float(str(row[lon_col]).replace(',', '.'))
                    dests_payload.append({"lat": lat, "lon": lon})
                    dest_mapping.append(i)
                except:
                    continue

        if not origins_payload or not dests_payload:
            return "Coordenadas inválidas encontradas.", no_update

        # Call Matrix API
        # Warning: This might be heavy if N x M is large. Valhalla handles it well though.
        matrix = valhalla_client.get_matrix(origins_payload, dests_payload)

        if not matrix:
            return "Erro ao calcular matriz (Verifique se o Valhalla está rodando).", no_update

        # Process Results: Find Farthest for each Origin
        routes_data = [] # List of geometries to plot

        for i, row_distances in enumerate(matrix):
            # i corresponds to index in origins_payload / origins_unique

            # Find max distance index
            max_dist = -1
            max_idx = -1

            for j, dist in enumerate(row_distances):
                if dist is not None and dist > max_dist:
                    max_dist = dist
                    max_idx = j

            if max_idx != -1:
                # Get route geometry for this pair
                origin = origins_payload[i]
                destination = dests_payload[max_idx]

                route_info = valhalla_client.get_route(origin, destination)

                if route_info:
                    routes_data.append({
                        'origin': origin,
                        'destination': destination,
                        'geometry': route_info['geometry'], # List of [lat, lon]
                        'distance': route_info['distance']
                    })

        return f"Cálculo concluído. {len(routes_data)} rotas encontradas.", routes_data

    except Exception as e:
        print(f"Matrix Calc Error: {e}")
        return f"Erro: {str(e)}", no_update

# 14. Render Map
@app.callback(
    Output("matrix-map", "figure"),
    Input("store-matrix-routes", "data"),
    Input("main-tabs", "active_tab")
)
def update_map(routes_data, active_tab):
    if active_tab != 'tab-matrix':
        return no_update

    fig = go.Figure()

    # Base Map Style
    fig.update_layout(
        mapbox_style="open-street-map", # Free, no token needed
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False
    )

    if not routes_data:
        # Default center Brazil
        fig.update_layout(
            mapbox={
                'center': {'lat': -15.793889, 'lon': -47.882778},
                'zoom': 3
            }
        )
        return fig

    # Plot Routes
    lats = []
    lons = []

    # 1. Plot Lines (Routes)
    for route in routes_data:
        geo = route['geometry']
        # Unzip geometry
        r_lats, r_lons = zip(*geo)

        # Add trace for route
        fig.add_trace(go.Scattermapbox(
            mode="lines",
            lat=r_lats,
            lon=r_lons,
            line=dict(width=2, color='blue'),
            hoverinfo='none' # Performance
        ))

        lats.extend(r_lats)
        lons.extend(r_lons)

    # 2. Plot Endpoints (Origins and Destinations)
    # We can extract them from routes_data
    org_lats = [r['origin']['lat'] for r in routes_data]
    org_lons = [r['origin']['lon'] for r in routes_data]

    dest_lats = [r['destination']['lat'] for r in routes_data]
    dest_lons = [r['destination']['lon'] for r in routes_data]

    fig.add_trace(go.Scattermapbox(
        mode="markers",
        lat=org_lats,
        lon=org_lons,
        marker=dict(size=8, color='green'),
        name="Origem"
    ))

    fig.add_trace(go.Scattermapbox(
        mode="markers",
        lat=dest_lats,
        lon=dest_lons,
        marker=dict(size=8, color='red'),
        name="Destino (Mais Distante)"
    ))

    # Auto-center
    if lats and lons:
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        fig.update_layout(
            mapbox={
                'center': {'lat': center_lat, 'lon': center_lon},
                'zoom': 3
            }
        )

    return fig


def view():
    app.run(debug=True)
