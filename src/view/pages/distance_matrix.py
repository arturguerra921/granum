from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from src.view.theme import UNB_THEME

def get_tab_distance_matrix_layout():
    # Calculation Card
    calc_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Cálculo da Matriz de Distâncias", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-calc-matrix", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Calcula a distância rodoviária real entre cada cidade de origem (Entrada de Dados) e cada armazém (Armazéns).",
                        target="help-calc-matrix",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    html.P("Clique no botão abaixo para iniciar o cálculo. Isso pode levar alguns segundos dependendo da quantidade de dados.", className="text-muted small mb-3"),
                    dbc.Button("Calcular Matriz", id="btn-calc-matrix", color="primary", className="w-100 mb-2"),
                    html.Div(id="calc-status-message", className="text-center small mt-2")
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom mb-3"
    )

    # Export Card
    export_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Exportar Matriz", className="me-2"),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                     dbc.Button("Baixar Excel (.xlsx)", id="btn-download-matrix", color="success", className="w-100", disabled=True),
                     dcc.Download(id="download-matrix-xlsx")
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom"
    )

    # Matrix Table Card
    table_card = dbc.Card(
        [
            dbc.CardHeader(
                "Matriz de Distâncias (km)",
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    dbc.Spinner(
                        html.Div(id='table-matrix-container', children=[
                            dash_table.DataTable(
                                id='table-distance-matrix',
                                data=[],
                                columns=[],
                                page_size=15,
                                style_table={'overflowX': 'auto', 'borderRadius': '8px', 'border': f"1px solid {UNB_THEME['BORDER_LIGHT']}"},
                                style_cell={
                                    'textAlign': 'center',
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
                                    'borderBottom': f"2px solid {UNB_THEME['BORDER_LIGHT']}",
                                    'textAlign': 'center'
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
                    html.Div("Clique em uma célula da tabela para visualizar a rota no mapa abaixo.", className="text-muted small mt-2")
                ],
                className="card-body-custom d-flex flex-column"
            ),
        ],
        className="card-custom h-100 mb-3",
        style={"minHeight": "300px"} # Reduced min-height
    )

    # Map Card
    map_card = dbc.Card(
        [
            dbc.CardHeader(
                "Visualização da Rota",
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    dcc.Graph(
                        id="graph-route-map",
                        style={"height": "600px"}, # Increased height for better view
                        config={
                            "displayModeBar": True,
                            "scrollZoom": True,
                            "showAxisDragHandles": True,
                            "modeBarButtons.add": ['drawline', 'drawopenpath', 'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape']
                        }
                    )
                ],
                className="card-body-custom"
            )
        ],
        className="card-custom h-100"
    )

    return html.Div([
        dbc.Row(
            [
                dbc.Col([
                    calc_card,
                    export_card
                ], width=12, lg=3, className="mb-24"),
                dbc.Col([
                    table_card,
                    map_card
                ], width=12, lg=9, className="mb-24"),
            ]
        ),
    ])
