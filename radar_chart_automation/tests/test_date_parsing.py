from src import utils


def test_parse_date_label():
    assert utils.parse_date_label("2026-01-31") == "2026-01-31"
    assert utils.parse_date_label("Jan 31, 2026") == "2026-01-31"


def test_infer_from_filename():
    assert utils.infer_date_from_filename("cmj_2026-01-31.csv") == "2026-01-31"
