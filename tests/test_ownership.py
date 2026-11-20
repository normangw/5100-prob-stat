import pandas as pd

from blackjack_take.data.ownership import owner_at, validate_ownership


def _df(rows):
    d = pd.DataFrame(rows, columns=["property", "area", "parent_company", "start", "end", "source"])
    d["start"], d["end"] = pd.to_datetime(d["start"]), pd.to_datetime(d["end"])
    return d


def test_valid_table_has_no_problems_and_owner_lookup_works():
    d = _df(
        [
            ("A", "Las Vegas Strip", "X", "1995-01-01", "2004-12-01", "s"),
            ("A", "Las Vegas Strip", "Y", "2005-01-01", None, "s"),
        ]
    )
    assert validate_ownership(d) == []
    assert owner_at(d, "2000-06-01")["parent_company"].tolist() == ["X"]
    assert owner_at(d, "2010-01-01")["parent_company"].tolist() == ["Y"]


def test_flags_parent_area_overlap_and_unknown_area():
    d = _df(
        [
            ("A", "Clark County", "X", "1995-01-01", "2005-12-01", "s"),
            ("A", "Nowhere", "Y", "2005-06-01", None, "s"),
        ]
    )
    msgs = " ".join(validate_ownership(d))
    assert "use leaf areas" in msgs and "unknown areas" in msgs and "overlapping" in msgs
