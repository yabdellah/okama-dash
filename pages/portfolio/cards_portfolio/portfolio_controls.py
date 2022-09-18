import re
from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import html, dcc, callback, ALL, MATCH

import pandas as pd
from dash.exceptions import PreventUpdate

from common import settings as settings, inflation as inflation
from common.create_link import create_link
from common.html_elements.copy_link_div import create_copy_link_div
from common.parse_query import get_tickers_list
from common.symbols import get_symbols
from common import cache
from pages.compare.cards_compare.eng.al_tooltips_options_txt import (
    al_options_tooltip_inflation,
    al_options_tooltip_cagr,
    al_options_window,
)

app = dash.get_app()
cache.init_app(app.server)
options = get_symbols()

today_str = pd.Timestamp.today().strftime("%Y-%m")


def card_controls(
    tickers: Optional[list],
    first_date: Optional[str],
    last_date: Optional[str],
    ccy: Optional[str],
):
    # tickers_list = get_tickers_list(tickers)
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Investment Portfolio", className="card-title"),
                html.Div(
                    [
                        html.Label("Tickers & Weights"),
                        html.Div(id='dynamic-container', children=[]),
                        dbc.Button("Add Asset", id="dynamic-add-filter", n_clicks=0),
                    ],
                ),
                html.Div(
                    [
                        html.Label("Base currency"),
                        dcc.Dropdown(
                            options=inflation.get_currency_list(),
                            value=ccy if ccy else "USD",
                            multi=False,
                            placeholder="Select a base currency",
                            id="pf-base-currency",
                        ),
                    ],
                ),
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("First Date"),
                                        dbc.Input(
                                            id="pf-first-date",
                                            value=first_date if first_date else "2000-01",
                                            type="text",
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Last Date"),
                                        dbc.Input(
                                            id="pf-last-date",
                                            value=last_date if last_date else today_str,
                                            type="text",
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ]
                                ),
                            ]
                        ),
                        dbc.Row(
                            # copy link to clipboard button
                            create_copy_link_div(
                                location_id="pf-url",
                                hidden_div_with_url_id="pf-show-url",
                                button_id="pf-copy-link-button",
                                card_name="asset list",
                            ),
                        ),
                        dbc.Row(html.H5(children="Options")),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Plot:",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="pf-info-plot",
                                                ),
                                            ]
                                        ),
                                        dbc.RadioItems(
                                            options=[
                                                {"label": "Wealth Index", "value": "wealth"},
                                                {"label": "Rolling Cagr", "value": "cagr"},
                                                {"label": "Rolling Real Cagr", "value": "real_cagr"},
                                            ],
                                            value="wealth",
                                            id="pf-plot-option",
                                        ),
                                        dbc.Tooltip(
                                            al_options_tooltip_cagr,
                                            target="pf-info-plot",
                                        ),
                                    ],
                                    lg=4,
                                    md=4,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Include Inflation",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="pf-info-inflation",
                                                ),
                                            ]
                                        ),
                                        dbc.Switch(
                                            label="",
                                            value=False,
                                            id="pf-inflation-switch",
                                        ),
                                        dbc.Tooltip(
                                            al_options_tooltip_inflation,
                                            target="pf-info-inflation",
                                        ),
                                    ],
                                    lg=4,
                                    md=4,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Rolling Window",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="pf-info-rolling",
                                                ),
                                            ]
                                        ),
                                        dbc.Input(
                                            type="number",
                                            min=1,
                                            value=2,
                                            id="pf-rolling-window",
                                        ),
                                        dbc.FormText("Format: number of years (≥ 1)"),
                                        dbc.Tooltip(
                                            al_options_window,
                                            target="pf-info-rolling",
                                        ),
                                    ],
                                    lg=4,
                                    md=4,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                            ]
                        ),
                    ]
                ),
                html.Div(
                    [
                        dbc.Button(
                            children="Calculate",
                            id="pf-submit-button",
                            n_clicks=0,
                            color="primary",
                        ),
                    ],
                    style={"text-align": "center"},
                    className="p-3",
                ),
            ]
        ),
        class_name="mb-3",
    )
    return card


@callback(
    Output(component_id="pf-rolling-window", component_property="disabled"),
    Input(component_id="pf-plot-option", component_property="value"),
)
def update_rolling_input(plot_options: str):
    return plot_options == "wealth"


@callback(
    Output(component_id="pf-inflation-switch", component_property="value"),
    Output(component_id="pf-inflation-switch", component_property="disabled"),
    Input(component_id="pf-plot-option", component_property="value"),
    State(component_id="pf-inflation-switch", component_property="value"),
)
def update_inflation_switch(plot_options: str, inflation_switch_value):
    """
    Change inflation-switch value and disabled state.

    It should be "ON" and "Disabled" if "Real CAGR" chart selected.
    """
    if plot_options == "real_cagr":
        return True, True
    else:
        return inflation_switch_value, False


# @callback(
#     Output("pf-show-url", "children"),
#     Input("pf-url", "href"),
#     Input("pf-symbols-list", "value"),  # get selected tickers
#     Input("pf-base-currency", "value"),
#     Input("pf-first-date", "value"),
#     Input("pf-last-date", "value"),
# )
# def update_link_pf(href: str, tickers_list: Optional[list], ccy: str, first_date: str, last_date: str):
#     return create_link(ccy, first_date, href, last_date, tickers_list)


# ----------------------- Pattern Matching Callbacks -------------------------------------------
@app.callback(
    Output('dynamic-container', 'children'),
    Input('dynamic-add-filter', 'n_clicks'),
    State('dynamic-container', 'children'))
def display_dropdowns(n_clicks, children):
    new_row = dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id={
                    'type': 'pf-dynamic-dropdown',
                    'index': n_clicks
                },
                placeholder="Select an assets",
            ),
        ),
        dbc.Col(
            dbc.Input(
                id={
                    'type': 'pf-dynamic-input',
                    'index': n_clicks
                },
                placeholder="Input a weight",
            )
        )

    ])
    children.append(new_row)
    return children


@app.callback(
    Output({'type': 'pf-dynamic-dropdown', 'index': MATCH}, "options"),
    Input({'type': 'pf-dynamic-dropdown', 'index': MATCH}, "search_value"),
)
def optimize_search_al(search_value):
    if not search_value:
        raise PreventUpdate
    return [o for o in options if re.match(search_value, o, re.IGNORECASE)]

# @app.callback(
#     Output('dynamic-output', 'children'),
#     Input({'type': 'pf-dynamic-input', 'index': ALL}, 'value'),
# )
# def calculate_weights_sum(values):
#     return sum(float(x) for x in values if x)
#
#
# @app.callback(
#     Output('weights-list', 'children'),
#     Input({'type': 'pf-dynamic-input', 'index': ALL}, 'value'),
# )
# def get_weights_list(values):
#     return values
#
#
# @app.callback(
#     Output('assets-list', 'children'),
#     Input({'type': 'pf-dynamic-dropdown', 'index': ALL}, 'value'),
# )
# def get_assets_list(values):
#     return values
