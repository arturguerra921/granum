import os
import io
import base64
import pandas as pd
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from src.view.theme import UNB_THEME

def get_tab_costs_layout():
    # Card 1: Manage Storage Tariff
    storage_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Tarifa de Armazenagem", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-storage-costs", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Valores para armazenamento de cada produto. Atualizações na tabela serão salvas automaticamente.",
                        target="help-storage-costs",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button("Adicionar Linha", id="btn-add-storage-row", color="primary", className="w-100 mb-2"),
                                    dcc.Upload(
                                        id='upload-storage-csv',
                                        children=html.Div([
                                            html.Div("📂", style={"fontSize": "2rem", "marginBottom": "8px"}),
                                            html.Span('Arraste e solte ou ', style={"color": UNB_THEME['UNB_GRAY_DARK']}),
                                            html.A('Selecione', className="fw-bold text-decoration-underline", style={"color": UNB_THEME['UNB_BLUE']}),
                                            html.Div("Formatos: .csv", className="text-muted small mt-2")
                                        ]),
                                        className="upload-box mb-3",
                                        multiple=False,
                                        accept='.csv'
                                    ),
                                    dbc.Button("Baixar CSV", id="btn-download-storage", color="success", className="w-100 mb-2"),
                                    dcc.Download(id="download-storage-csv")
                                ],
                                width=12, lg=3, className="mb-3 mb-lg-0"
                            ),
                            dbc.Col(
                                [
                                    dbc.Spinner(
                                        html.Div(id='table-storage-container', children=[
                                            dash_table.DataTable(
                                                id='table-costs-storage',
                                                data=[],
                                                columns=[
                                                    {'name': 'Produto', 'id': 'Produto'},
                                                    {'name': 'Armazenar Público', 'id': 'Armazenar_Publico'},
                                                    {'name': 'Armazenar Privado', 'id': 'Armazenar_Privado'}
                                                ],
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
                                ],
                                width=12, lg=9
                            )
                        ]
                    )
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom mb-4"
    )

    # Card 2: Manage Freight Cost
    freight_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div([
                    html.Span("Valor do Frete", className="me-2"),
                    html.I(className="bi bi-question-circle-fill text-muted", id="help-freight-costs", style={"cursor": "help", "fontSize": "0.9rem"}),
                    dbc.Tooltip(
                        "Valores de frete por tonelada e km para cada estado. Atualizações na tabela serão salvas automaticamente.",
                        target="help-freight-costs",
                        placement="right"
                    ),
                ], className="d-flex align-items-center"),
                className="card-header-custom"
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button("Adicionar Linha", id="btn-add-freight-row", color="primary", className="w-100 mb-2"),
                                    dcc.Upload(
                                        id='upload-freight-csv',
                                        children=html.Div([
                                            html.Div("📂", style={"fontSize": "2rem", "marginBottom": "8px"}),
                                            html.Span('Arraste e solte ou ', style={"color": UNB_THEME['UNB_GRAY_DARK']}),
                                            html.A('Selecione', className="fw-bold text-decoration-underline", style={"color": UNB_THEME['UNB_BLUE']}),
                                            html.Div("Formatos: .csv", className="text-muted small mt-2")
                                        ]),
                                        className="upload-box mb-3",
                                        multiple=False,
                                        accept='.csv'
                                    ),
                                    dbc.Button("Baixar CSV", id="btn-download-freight", color="success", className="w-100 mb-2"),
                                    dcc.Download(id="download-freight-csv")
                                ],
                                width=12, lg=3, className="mb-3 mb-lg-0"
                            ),
                            dbc.Col(
                                [
                                    dbc.Spinner(
                                        html.Div(id='table-freight-container', children=[
                                            dash_table.DataTable(
                                                id='table-costs-freight',
                                                data=[],
                                                columns=[
                                                    {'name': 'Estado', 'id': 'Estado'},
                                                    {'name': 'Frete (R$/ton.km)', 'id': 'Frete Tonelada Km'}
                                                ],
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
                                ],
                                width=12, lg=9
                            )
                        ]
                    )
                ],
                className="card-body-custom"
            ),
        ],
        className="card-custom h-100"
    )

    return html.Div([
        storage_card,
        freight_card
    ])
