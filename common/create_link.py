def create_link(ccy, first_date, href, last_date, tickers_list):
    t_number = len(tickers_list)
    tickers_str = "".join(
        f"{ticker}," if i + 1 < t_number else ticker
        for i, ticker in enumerate(tickers_list)
    )

    reset_href = href.split("?")[0]
    new_url = f"{reset_href}?tickers={tickers_str}" if tickers_str else reset_href
    new_url += f"&ccy={ccy}"
    new_url += f"&first_date={first_date}"
    new_url += f"&last_date={last_date}"
    return new_url
