from typing import Dict, List, Tuple

import pandas as pd

AXIS_LABELS = ["Jump Height", "Triple Ext", "Elasticity", "Loading", "Braking"]

METRIC_TO_AXIS = {
    "jump_height": "Jump Height",
    "peak_power_bm": "Triple Ext",
    "rsi_modified": "Elasticity",
    "ecc_peak_power_bm": "Loading",
    "ecc_dec_rfd_bm": "Braking",
}


def compute_percentiles(df: pd.DataFrame, mapping: Dict[str, str]):
    n = len(df)
    if n == 0:
        raise ValueError("No athlete rows found in CSV.")

    athlete_col = mapping["athlete_name"]
    records: List[dict] = []
    wide_records: List[dict] = []

    percentiles_by_metric: Dict[str, pd.Series] = {}
    for metric_key, axis_label in METRIC_TO_AXIS.items():
        col = mapping[metric_key]
        ranks = df[col].rank(method="average", ascending=True)
        percent = ranks / n
        percentiles_by_metric[axis_label] = percent

    for idx, row in df.iterrows():
        athlete_name = row[athlete_col]
        wide_row = {"athlete_name": athlete_name}
        for axis_label, series in percentiles_by_metric.items():
            percentile = float(series.iloc[idx])
            wide_row[f"{axis_label} percentile"] = percentile
            records.append(
                {
                    "athlete_name": athlete_name,
                    "metric_key": axis_label,
                    "raw_value": float(row[mapping[_axis_to_metric(axis_label)]]),
                    "percentile_0_1": percentile,
                }
            )
        wide_records.append(wide_row)

    long_df = pd.DataFrame(records)
    wide_df = pd.DataFrame(wide_records)
    return long_df, wide_df


def _axis_to_metric(axis_label: str) -> str:
    for key, label in METRIC_TO_AXIS.items():
        if label == axis_label:
            return key
    raise KeyError(axis_label)
