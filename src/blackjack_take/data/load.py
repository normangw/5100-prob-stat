"""Load NGCB workbook sheets into tidy (month, area, value) frames."""
import pandas as pd

from blackjack_take import config


def load_sheet(sheet: str, path=config.RAW_XLSX) -> pd.DataFrame:
    """Return long frame [month, area, value] for one sheet.

    Handles the workbook quirks: title row above the header, '#DIV/0!' strings, empty
    trailing rows, and a mostly-empty 'Bal. of Clark' header split across rows 2-3.
    """
    raw = pd.read_excel(path, sheet_name=sheet, header=config.HEADER_ROW - 1)
    raw = raw.rename(columns=lambda c: str(c).strip())
    raw = raw.rename(columns={"County": "Bal. of Clark County"})
    raw["Month"] = pd.to_datetime(raw["Month"], errors="coerce")
    raw = raw.dropna(subset=["Month"])
    value_cols = [c for c in raw.columns if c in config.AREAS]
    long = raw.melt(id_vars="Month", value_vars=value_cols, var_name="area", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")  # '#DIV/0!' -> NaN
    long = long.rename(columns={"Month": "month"})
    return long[(long["month"] >= config.START) & (long["month"] <= config.END)].reset_index(
        drop=True
    )


def load_take(path=config.RAW_XLSX) -> pd.DataFrame:
    """Win per game per day by area, using the series named in config."""
    return load_sheet(config.WIN_PER_UNIT_PER_DAY_SHEET, path)
