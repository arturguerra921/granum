from dash import dcc, html
import dash_bootstrap_components as dbc
from src.view.theme import UNB_THEME

def get_valhalla_tab_layout():
    # Calculation Card
    calc_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Cálculo de Matriz de Distâncias", className="me-2"),
                    html.I(className="bi bi-info-circle-fill text-muted", title="Calcula a matriz de distâncias entre Origens e Armazéns usando Valhalla.")
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    html.P("Clique abaixo para iniciar o cálculo da matriz de distâncias. Isso pode levar alguns minutos dependendo do número de origens e destinos.", className="text-muted small mb-3"),
                    html.Div(
                        [
                            dbc.Button(
                                [html.I(className="bi bi-calculator me-2"), "Calcular Matriz"],
                                id="btn-calculate-matrix",
                                color="primary",
                                className="w-100 mb-3",
                                style={"backgroundColor": UNB_THEME['UNB_BLUE'], "borderColor": UNB_THEME['UNB_BLUE']}
                            ),
                        ],
                        className="d-grid gap-2"
                    ),
                    html.Div(id="valhalla-status", className="text-center text-muted small mt-2", style={"minHeight": "20px"})
                ],
                className="card-body-custom p-3"
            )
        ],
        className="card-custom mb-3 h-100"
    )

    # Results Card (Map)
    map_card = dbc.Card(
        [
            dbc.CardHeader("Mapa de Rotas (Origem -> Destino Mais Distante)", className="card-header-custom"),
            dbc.CardBody(
                [
                    dbc.Spinner(
                        dcc.Graph(
                            id="valhalla-map",
                            style={"height": "600px"},
                            config={'displayModeBar': True}
                        ),
                        color="primary"
                    )
                ],
                className="card-body-custom p-0" # Remove padding for map to extend edge-to-edge
            )
        ],
        className="card-custom h-100"
    )

    return html.Div([
        dbc.Row(
            [
                dbc.Col(calc_card, width=12, lg=3, className="mb-3"),
                dbc.Col(map_card, width=12, lg=9, className="mb-3")
            ],
            className="h-100"
        ),
        # Hidden store for results
        dcc.Store(id="valhalla-results-store"),
    ])
