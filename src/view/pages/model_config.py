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
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-model-config", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
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
                    html.Div([
                        dbc.Switch(
                            id="toggle-detailed-log",
                            value=False,
                            className="custom-switch mb-0 small"
                        ),
                        html.Label(
                            "Detalhar log do modelo",
                            htmlFor="toggle-detailed-log",
                            className="mb-0 mx-2 text-muted cursor-pointer small"
                        ),
                        html.I(className="bi bi-question-circle-fill text-muted", id="help-detailed-log", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
                        dbc.Tooltip(
                            "Ativar esta opção incluirá a construção detalhada do modelo matemático (em Python) no log. No entanto, isso pode aumentar significativamente o tempo de resolução. Use esta opção apenas para depuração ou se você quiser entender como o modelo é construído.",
                            target="help-detailed-log",
                            placement="top"
                        )
                    ], className="mb-4 d-flex align-items-center justify-content-center"),
                    dbc.Button("Rodar Modelo", id="btn-run-model", color="none", className="btn-primary-custom w-100 mb-3"),
                    dbc.Button("Baixar Log de Execução (.txt)", id="btn-download-log", color="none", className="btn-outline-secondary-custom w-100 mb-3", disabled=True),
                    dcc.Download(id="download-model-log"),
                    html.Div(id="model-output-text", className="mt-3 text-center")
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom mb-3"
    )

    # Loading Modal
    loading_modal = dbc.Modal(
        [
            dbc.ModalBody(
                [
                    html.Div(
                        [
                            dbc.Spinner(spinner_class_name="text-primary-custom", spinner_style={"width": "3rem", "height": "3rem"}),
                            html.H5("Otimizando alocação...", className="mt-4"),
                            html.P("Isso pode levar alguns minutos. Por favor, aguarde.", className="text-muted text-center mt-2"),
                            dbc.Button("Interromper Modelo", id="btn-cancel-model", color="none", className="btn-danger-custom mt-4 w-50", disabled=True)
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
                ], width=12, md=8, lg=6, className="mb-24 mx-auto"),
            ],
            className="justify-content-center"
        ),
        loading_modal
    ])
