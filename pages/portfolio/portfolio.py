import warnings

import dash
from dash import dash_table, callback, ALL, MATCH
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import okama as ok

import common.settings as settings
from common.mobile_screens import adopt_small_screens
from pages.portfolio.cards_portfolio.portfolio_controls import card_controls
from pages.portfolio.cards_portfolio.portfolio_info import card_assets_info
from pages.portfolio.cards_portfolio.pf_statistics_table import card_table
from pages.portfolio.cards_portfolio.pf_wealth_indexes_chart import card_graf_portfolio
import pages.compare.crisis.crisis_data as cr

warnings.simplefilter(action="ignore", category=FutureWarning)

dash.register_page(
    __name__,
    path="/portfolio",
    title="Investment Portfolio : okama",
    name="Investment Portfolio",
    description="Okama widget for Investment Portfolio analysis",
)


def layout(tickers=None, first_date=None, last_date=None, ccy=None, **kwargs):
    page = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(card_controls(tickers, first_date, last_date, ccy), lg=5),
                    dbc.Col(card_assets_info, lg=7),
                ]
            ),
            dbc.Row(dbc.Col(card_graf_portfolio, width=12), align="center"),
            dbc.Row(dbc.Col(card_table, width=12), align="center"),
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page


@callback(
    Output(component_id="pf-wealth-indexes", component_property="figure"),
    Output(component_id="pf-wealth-indexes", component_property="config"),
    Output(component_id="pf-describe-table", component_property="children"),
    # user screen info
    Input(component_id="store", component_property="data"),
    # main Inputs
    Input(component_id="pf-submit-button", component_property="n_clicks"),
    State({'type': 'pf-dynamic-dropdown', 'index': ALL}, 'value'),  # tickers
    State({'type': 'pf-dynamic-input', 'index': ALL}, 'value'),  # weights
    State(component_id="pf-base-currency", component_property="value"),
    State(component_id="pf-rebalancing-period", component_property="value"),
    State(component_id="pf-first-date", component_property="value"),
    State(component_id="pf-last-date", component_property="value"),
    # Options
    State(component_id="pf-plot-option", component_property="value"),
    State(component_id="pf-inflation-switch", component_property="value"),
    State(component_id="pf-rolling-window", component_property="value"),
    # Logarithmic scale button
    Input(component_id="pf-logarithmic-scale-switch", component_property="on"),
    prevent_initial_call=True,
)
def update_graf_portfolio(
    screen,
    n_clicks,
    assets: list,
    weights: list,
    ccy: str,
    rebalancing_period: str,
    fd_value: str,
    ld_value: str,
    # Options
    plot_type: str,
    inflation_on: bool,
    rolling_window: int,
    # Log scale
    log_on: bool,
):
    assets = [i for i in assets if i is not None]
    weights = [i / 100. for i in weights if i is not None]
    # symbols = assets if isinstance(assets, list) else [assets]
    pf_object = ok.Portfolio(
        assets=assets,
        weights=weights,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        rebalancing_period=rebalancing_period,
        inflation=inflation_on,
        symbol="PORTFOLIO.PF"
    )
    fig = get_pf_figure(pf_object, plot_type, inflation_on, rolling_window, log_on)
    # Change layout for mobile screens
    fig, config = adopt_small_screens(fig, screen)
    # PF statistics
    statistics_dash_table = get_pf_statistics_table(pf_object)
    return (fig,
            config,
            # info_table,
            # names_table,
            statistics_dash_table
            )


def get_pf_statistics_table(al_object):
    statistics_df = al_object.describe().iloc[:-4, :]
    # statistics_df = al_object.describe()
    # statistics_df.iloc[-4:, :] = statistics_df.iloc[-4:, :].applymap(str)
    statistics_dict = statistics_df.to_dict(orient="records")

    columns = [
        dict(id=i, name=i, type="numeric", format=dash_table.FormatTemplate.percentage(2))
        for i in statistics_df.columns
    ]
    return dash_table.DataTable(
        data=statistics_dict,
        columns=columns,
        style_table={"overflowX": "auto"},
    )


def get_pf_figure(pf_object: ok.Portfolio, plot_type: str, inflation_on: bool, rolling_window: int, log_scale: bool):
    titles = {
        "wealth": "Portfolio Wealth index",
        "cagr": f"Rolling CAGR (window={rolling_window} years)",
        "real_cagr": f"Rolling real CAGR (window={rolling_window} years)",
    }

    # Select Plot Type
    if plot_type == "wealth":
        df = pf_object.wealth_index_with_assets
    else:
        real = False if plot_type == "cagr" else True
        df = pf_object.get_rolling_cagr(window=rolling_window * settings.MONTHS_PER_YEAR, real=real)
    ind = df.index.to_timestamp("D")
    chart_first_date = ind[0]
    chart_last_date = ind[-1]
    # inflation must not be in the chart for "Real CAGR"
    plot_inflation_condition = inflation_on and plot_type != "real_cagr"

    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1] if plot_inflation_condition else df.columns,
        log_y=log_scale,
        title=titles[plot_type],
        # width=800,
        height=800,
    )
    # Plot Inflation
    if plot_inflation_condition:
        fig.add_trace(
            go.Scatter(
                x=ind,
                y=df.iloc[:, -1],
                mode="none",
                fill="tozeroy",
                fillcolor="rgba(226,150,65,0.5)",
                name="Inflation",
            )
        )
    # Plot Financial crisis historical data (sample)
    for crisis in cr.crisis_list:
        if (chart_first_date < crisis.first_date_dt) and (chart_last_date > crisis.last_date_dt):
            fig.add_vrect(
                x0=crisis.first_date,
                x1=crisis.last_date,
                annotation_text=crisis.name,
                annotation=dict(align="left", valign="top", textangle=-90),
                fillcolor="red",
                opacity=0.25,
                line_width=0,
            )
    # Plot x-axis slider
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        xaxis_title="Date",
        legend_title="Assets",
    )
    return fig
