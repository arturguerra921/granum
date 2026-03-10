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
                            id="toggle-min-max-capacity",
                            value=False,
                            className="custom-switch mb-0 small"
                        ),
                        html.Label(
                            "Adicionar carga mínima e máxima",
                            htmlFor="toggle-min-max-capacity",
                            className="mb-0 mx-2 text-muted cursor-pointer small"
                        ),
                        html.I(className="bi bi-question-circle-fill text-muted", id="help-min-max", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
                        dbc.Tooltip(
                            "Ative para configurar capacidades diárias mínimas e máximas de recepção para os armazéns durante o período alocado.",
                            target="help-min-max",
                            placement="top"
                        )
                    ], className="mb-4 d-flex align-items-center justify-content-center"),

                    # Container for extra options (initially hidden)
                    html.Div(
                        id="container-min-max-options",
                        style={"display": "none"},
                        children=[
                            html.Hr(className="mt-2 mb-3"),

                            html.P([
                                html.I(className="bi bi-info-circle me-1"),
                                "Campos deixados em branco (sem valor numérico) não serão considerados no limite. Você não precisa preencher todos."
                            ], className="text-muted small mb-3 fst-italic", style={"fontSize": "0.8rem"}),

                            html.H6("Limites de Recepção do Armazém", className="fw-bold small text-primary-custom mb-3"),

                            # Linha 1: Recepção Mínima e Dias
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        dbc.Label("Recepção mínima diária (ton)", className="fw-bold small me-2 mb-0", style={"color": "#9ca3af"}),
                                        html.I(className="bi bi-question-circle-fill text-muted", id="help-carga-min", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
                                        dbc.Tooltip("A soma de todas as rotas chegando em um armazém deve ser pelo menos este valor diariamente.", target="help-carga-min")
                                    ], className="d-flex align-items-center mb-1"),
                                    dbc.Input(id="input-carga-min", type="number", min=0, placeholder="Ex: 10", className="mb-4")
                                ], width=6),
                                dbc.Col([
                                    html.Div([
                                        dbc.Label("Dias para alocação", className="fw-bold small me-2 mb-0", style={"color": "#9ca3af"}),
                                        html.I(className="bi bi-question-circle-fill text-muted", id="help-dias", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
                                        dbc.Tooltip("Quantidade de dias que multiplica as cargas diárias (mínima e máxima) de recepção do armazém, simulando mais de um dia de operação.", target="help-dias")
                                    ], className="d-flex align-items-center mb-1"),
                                    dbc.Input(id="input-dias-alocacao", type="number", min=1, placeholder="Ex: 5", className="mb-4")
                                ], width=6)
                            ]),

                            # Linha 2: Recepção Máxima e Switch
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        dbc.Label("Recepção máxima diária (ton)", className="fw-bold small me-2 mb-0", style={"color": "#9ca3af"}),
                                        html.I(className="bi bi-question-circle-fill text-muted", id="help-carga-max", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
                                        dbc.Tooltip("A soma de todas as rotas chegando em um armazém não pode ultrapassar este valor diariamente.", target="help-carga-max")
                                    ], className="d-flex align-items-center mb-1"),
                                    dbc.Input(id="input-carga-max", type="number", min=0, placeholder="Ex: 100", className="mb-4")
                                ], width=6),
                                dbc.Col([
                                    # Para o alinhamento perfeito
                                    html.Div([
                                        dbc.Label("Spacer", className="fw-bold small me-2 mb-0", style={"visibility": "hidden"}),
                                        html.I(className="bi bi-question-circle-fill", style={"visibility": "hidden", "fontSize": "var(--font-size-small)"})
                                    ], className="d-flex align-items-center mb-1"),
                                    html.Div([
                                        dbc.Switch(
                                            id="toggle-use-recepcao",
                                            value=False,
                                            className="custom-switch mb-0 small"
                                        ),
                                        html.Label(
                                            "Utilizar Cap. de Recepção",
                                            htmlFor="toggle-use-recepcao",
                                            className="mb-0 mx-2 text-muted cursor-pointer small",
                                            style={"whiteSpace": "nowrap"}
                                        ),
                                        html.I(className="bi bi-question-circle-fill text-muted", id="help-use-recepcao", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
                                        dbc.Tooltip(
                                            "Se ativado, utiliza a capacidade de recepção (t) dos armazéns cadastrados no banco de dados como recepção máxima diária.",
                                            target="help-use-recepcao",
                                            placement="top"
                                        )
                                    ], className="d-flex align-items-center mb-4", style={"height": "38px"})
                                ], width=6),
                            ]),

                            html.Hr(className="mt-2 mb-4"),

                            html.H6("Limites de Rota Individual (Frete)", className="fw-bold small text-primary-custom mb-3"),

                            # Linha 3: Carga mínima e máxima de frete
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        dbc.Label("Carga mínima de frete (ton)", className="fw-bold small me-2 mb-0", style={"color": "#9ca3af"}),
                                        html.I(className="bi bi-question-circle-fill text-muted", id="help-frete-min", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
                                        dbc.Tooltip("Valor mínimo que uma rota individual deve transportar. Rotas com carga menor que esta não existirão.", target="help-frete-min")
                                    ], className="d-flex align-items-center mb-1"),
                                    dbc.Input(id="input-frete-min", type="number", min=0, placeholder="Ex: 15", className="mb-4")
                                ], width=6),
                                dbc.Col([
                                    html.Div([
                                        dbc.Label("Carga máxima de frete (ton)", className="fw-bold small me-2 mb-0", style={"color": "#9ca3af"}),
                                        html.I(className="bi bi-question-circle-fill text-muted", id="help-frete-max", style={"cursor": "help", "fontSize": "var(--font-size-small)"}),
                                        dbc.Tooltip("Valor máximo que uma rota individual pode transportar. Nenhuma rota terá carga maior que esta.", target="help-frete-max")
                                    ], className="d-flex align-items-center mb-1"),
                                    dbc.Input(id="input-frete-max", type="number", min=0, placeholder="Ex: 50", className="mb-4")
                                ], width=6)
                            ]),

                            html.Hr(className="mt-0 mb-4")
                        ]
                    ),
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
                    dbc.Button("Rodar Modelo", id="btn-run-model", className="btn-primary-custom w-100 mb-3"),
                    dbc.Button("Baixar Log de Execução (.txt)", id="btn-download-log", className="btn-outline-secondary-custom w-100 mb-3", disabled=True),
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
