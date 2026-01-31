import os
import re
from datetime import datetime
from typing import Optional

from dateutil import parser

DATE_COLUMN_CANDIDATES = [
    "date",
    "test date",
    "session date",
]


def sanitize_filename(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_") or "output"


def sanitize_title(value: str) -> str:
    return sanitize_filename(value)


def parse_date_label(value: str) -> Optional[str]:
    if not value:
        return None
    try:
        parsed = parser.parse(str(value), fuzzy=True)
    except (ValueError, TypeError):
        return None
    return parsed.strftime("%Y-%m-%d")


def infer_date_from_filename(filename: str) -> Optional[str]:
    stem = os.path.splitext(os.path.basename(filename))[0]
    return parse_date_label(stem)


def pick_date_column(columns):
    lower_map = {c.lower().strip(): c for c in columns}
    for candidate in DATE_COLUMN_CANDIDATES:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def extract_date_label_from_column(df, column_name: str) -> Optional[str]:
    if column_name not in df.columns:
        return None
    series = df[column_name].dropna()
    if series.empty:
        return None
    sample = series.iloc[0]
    return parse_date_label(sample)


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d_%H%M%S")
