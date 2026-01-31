from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

NAME_COLUMN_CANDIDATES = [
    "about",
    "athlete",
    "athlete name",
    "full name",
    "name",
    "player",
]

METRIC_COLUMNS = {
    "jump_height": ["jump height (in)", "jump height", "jump ht (in)", "jump ht"],
    "peak_power_bm": ["peak power/bm", "peak power / bm", "peak power per bm"],
    "rsi_modified": ["rsi-modified", "rsi modified", "rsimodified", "rsi mod"],
    "ecc_peak_power_bm": [
        "eccentric peak power/bm",
        "eccentric peak power / bm",
        "ecc peak power/bm",
        "ecc peak power / bm",
    ],
    "ecc_dec_rfd_bm": [
        "eccentric deceleration rfd/bm",
        "eccentric deceleration rfd / bm",
        "ecc deceleration rfd/bm",
        "ecc decel rfd/bm",
    ],
}

REQUIRED_KEYS = ["athlete_name"] + list(METRIC_COLUMNS.keys())


@dataclass
class ColumnMappingResult:
    mapping: Dict[str, str]
    missing_keys: List[str]


class ColumnMappingNeeded(Exception):
    def __init__(self, columns, missing_keys, suggested_mapping):
        super().__init__("Column mapping required")
        self.columns = columns
        self.missing_keys = missing_keys
        self.suggested_mapping = suggested_mapping


def _match_column(columns, candidates):
    lower_map = {c.lower().strip(): c for c in columns}
    for candidate in candidates:
        key = candidate.lower().strip()
        if key in lower_map:
            return lower_map[key]
    return None


def detect_column_mapping(columns) -> ColumnMappingResult:
    mapping: Dict[str, str] = {}
    missing = []
    name_column = _match_column(columns, NAME_COLUMN_CANDIDATES)
    if name_column:
        mapping["athlete_name"] = name_column
    else:
        missing.append("athlete_name")

    for key, candidates in METRIC_COLUMNS.items():
        col = _match_column(columns, candidates)
        if col:
            mapping[key] = col
        else:
            missing.append(key)

    return ColumnMappingResult(mapping=mapping, missing_keys=missing)


def load_csv(path: str, mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if mapping:
        missing = [key for key in REQUIRED_KEYS if key not in mapping]
        if missing:
            raise ColumnMappingNeeded(df.columns.tolist(), missing, mapping)
    else:
        result = detect_column_mapping(df.columns)
        mapping = result.mapping
        if result.missing_keys:
            raise ColumnMappingNeeded(df.columns.tolist(), result.missing_keys, mapping)

    return df, mapping


def validate_required_metrics(df: pd.DataFrame, mapping: Dict[str, str]) -> None:
    errors = []
    for key, col in mapping.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
            continue
        if key == "athlete_name":
            if df[col].isna().any():
                errors.append(f"Missing athlete name values in column: {col}")
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.isna().any():
            errors.append(f"Non-numeric or missing values in column: {col}")
        else:
            df[col] = numeric
    if errors:
        raise ValueError("; ".join(errors))
