import pandas as pd

from src import percentiles


def test_percentiles_rank_n():
    df = pd.DataFrame(
        {
            "Name": ["A", "B", "C"],
            "Jump Height (in)": [10, 20, 30],
            "Peak Power/BM": [100, 200, 300],
            "RSI-Modified": [1, 2, 3],
            "Eccentric Peak Power/BM": [5, 6, 7],
            "Eccentric Deceleration RFD/BM": [9, 8, 7],
        }
    )
    mapping = {
        "athlete_name": "Name",
        "jump_height": "Jump Height (in)",
        "peak_power_bm": "Peak Power/BM",
        "rsi_modified": "RSI-Modified",
        "ecc_peak_power_bm": "Eccentric Peak Power/BM",
        "ecc_dec_rfd_bm": "Eccentric Deceleration RFD/BM",
    }

    long_df, wide_df = percentiles.compute_percentiles(df, mapping)

    assert wide_df.loc[0, "Jump Height percentile"] == 1 / 3
    assert wide_df.loc[1, "Jump Height percentile"] == 2 / 3
    assert wide_df.loc[2, "Jump Height percentile"] == 1.0
    assert len(long_df) == 15


def test_percentiles_ties_min_rank():
    df = pd.DataFrame(
        {
            "Name": ["A", "B", "C", "D"],
            "Jump Height (in)": [10, 20, 20, 40],
            "Peak Power/BM": [1, 2, 3, 4],
            "RSI-Modified": [1, 2, 3, 4],
            "Eccentric Peak Power/BM": [1, 2, 3, 4],
            "Eccentric Deceleration RFD/BM": [1, 2, 3, 4],
        }
    )
    mapping = {
        "athlete_name": "Name",
        "jump_height": "Jump Height (in)",
        "peak_power_bm": "Peak Power/BM",
        "rsi_modified": "RSI-Modified",
        "ecc_peak_power_bm": "Eccentric Peak Power/BM",
        "ecc_dec_rfd_bm": "Eccentric Deceleration RFD/BM",
    }

    long_df, wide_df = percentiles.compute_percentiles(df, mapping)
    assert wide_df.loc[0, "Jump Height percentile"] == 1 / 4
    assert wide_df.loc[1, "Jump Height percentile"] == 2 / 4
    assert wide_df.loc[2, "Jump Height percentile"] == 2 / 4
    assert wide_df.loc[3, "Jump Height percentile"] == 4 / 4
