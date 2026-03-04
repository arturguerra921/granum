from dash import html, dcc
import dash_bootstrap_components as dbc
from src.view.theme import UNB_THEME

def get_tab_model_config_layout():
    # Card Config
    config_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Execução do Modelo Matemático", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-model-config", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Otimiza a alocação de produtos para os armazéns disponíveis baseando-se na distância e capacidade.",
                        target="help-model-config",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    html.P("Certifique-se de que preencheu os dados em todas as abas anteriores antes de executar.", className="text-muted small mb-3"),
                    dbc.Button("Rodar Modelo", id="btn-run-model", color="primary", className="w-100 mb-3"),
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom mb-3"
    )

    # Output Card
    output_card = dbc.Card(
        [
            dbc.CardHeader(
                "Saída do Console",
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    html.Pre(
                        id="model-output-text",
                        children="Aguardando execução do modelo...",
                        style={
                            "backgroundColor": "#1E1E1E",
                            "color": "#D4D4D4",
                            "padding": "15px",
                            "borderRadius": "8px",
                            "height": "600px",
                            "overflowY": "auto",
                            "fontFamily": "monospace",
                            "fontSize": "0.85rem",
                            "whiteSpace": "pre-wrap"
                        }
                    )
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom h-100"
    )

    # Loading Modal
    loading_modal = dbc.Modal(
        [
            dbc.ModalBody(
                [
                    html.Div(
                        [
                            dbc.Spinner(color="primary", spinner_style={"width": "3rem", "height": "3rem"}),
                            html.H5("Otimizando alocação...", className="mt-4"),
                            html.P("Isso pode levar alguns minutos. Por favor, aguarde.", className="text-muted text-center mt-2"),
                            dbc.Button("Interromper Modelo", id="btn-cancel-model", color="danger", className="mt-4 w-50", disabled=True)
                        ],
                        className="d-flex flex-column align-items-center justify-content-center p-5"
                    )
                ]
            )
        ],
        id="modal-model-running",
        is_open=False,
        backdrop="static", # Prevent closing by clicking outside
        keyboard=False, # Prevent closing with ESC key
        centered=True,
    )

    return html.Div([
        dbc.Row(
            [
                dbc.Col([
                    config_card
                ], width=12, lg=3, className="mb-24"),
                dbc.Col([
                    output_card
                ], width=12, lg=9, className="mb-24"),
            ]
        ),
        loading_modal
    ])
