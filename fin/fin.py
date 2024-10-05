import webbrowser
import os
from pathlib import Path
from datetime import datetime

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
STATEMENT = "/Users/areebbeigh/Downloads/statement.csv"
WITHDRAWALS = "Withdrawal Amt."
DEPOSITS = "Deposit Amt."
NARRATION = "Narration"
DATE = "Date"
CLOSING_BALANCE = "Closing Balance"
YM = "YM"
YM_STRF_FORMAT = "%Y %b"

df = pd.read_csv(STATEMENT)
df[DATE] = pd.to_datetime(df[DATE], format="%d/%m/%y")
df[YM] = df[DATE].dt.strftime(YM_STRF_FORMAT)
df[WITHDRAWALS] = df[WITHDRAWALS].fillna(0)
df[DEPOSITS] = df[DEPOSITS].fillna(0)


def debits_credits_per_month(df: pd.DataFrame):
    grouped = df.groupby(YM, sort=False).agg(
        total_debits=(WITHDRAWALS, "sum"),
        total_credits=(DEPOSITS, "sum"),
    )
    return grouped


def top_debits_per_month(df: pd.DataFrame, count: int = 5):
    cols = [YM, DATE, NARRATION, WITHDRAWALS]
    res = (
        df.groupby(YM, sort=False)[cols]
        .apply(lambda r: r.nlargest(count, WITHDRAWALS))
        .reset_index(drop=True)
    )
    res = res[cols][res[WITHDRAWALS] > 0]
    return res


def top_credits_per_month(df: pd.DataFrame, count: int = 5):
    cols = [YM, DATE, NARRATION, DEPOSITS]
    res = (
        df.groupby(YM, sort=False)[cols]
        .apply(lambda r: r.nlargest(count, DEPOSITS))
        .reset_index(drop=True)
    )
    res = res[cols][res[DEPOSITS] > 0]
    return res


def _ym_to_datetime(ym: str) -> datetime:
    return datetime.strptime(ym, YM_STRF_FORMAT)


def per_month_closing_balances(df: pd.DataFrame):
    res = (
        df.groupby(YM, sort=False)[[YM, DATE, CLOSING_BALANCE]]
        .apply(lambda r: r.tail(1))
        .reset_index(drop=True)
    )
    res.index = res[YM]
    res = res[[CLOSING_BALANCE]]
    return res


def savings_per_month(df: pd.DataFrame):
    txns = debits_credits_per_month(df)
    closing_balance = per_month_closing_balances(df)
    df_dict = {}
    prev_savings = None
    for ym, row in txns.iterrows():
        savings = row["total_credits"] - row["total_debits"]
        df_dict.setdefault(YM, []).append(ym)
        df_dict.setdefault("Savings", []).append(savings)

        if prev_savings is not None:
            savings_percentage = ((savings - prev_savings) / abs(prev_savings)) * 100
        else:
            savings_percentage = 0
        df_dict.setdefault("Savings %", []).append(savings_percentage)
        df_dict.setdefault(CLOSING_BALANCE, []).append(
            closing_balance.loc[ym][CLOSING_BALANCE]
        )

        prev_savings = savings
    return pd.DataFrame(df_dict)


funcs = [
    savings_per_month,
    debits_credits_per_month,
    top_credits_per_month,
    top_debits_per_month,
]
INCLUDE_INDEX = [debits_credits_per_month]
SECTION_TEMPLATE_FILE = BASE_DIR / "section-template.html"

with open(SECTION_TEMPLATE_FILE, "r") as f:
    section_template = f.read()

tables = []

for func in funcs:
    res: pd.DataFrame = func(df)
    html = res.to_html(
        index=func in INCLUDE_INDEX,
        classes="table table-striped table-hover table-bordered",
    )
    html = section_template.format(content=html, title=func.__name__)
    tables.append(html)

with open("template.html", "r") as f:
    html_template = f.read()

REPORT_HTML_FILE = BASE_DIR / "report.html"
print(f"Writing to {REPORT_HTML_FILE}")

report_html = html_template.format(content="\n".join(tables))
with open(REPORT_HTML_FILE, "w") as f:
    f.write(report_html)

webbrowser.open(f"file://{REPORT_HTML_FILE}")
