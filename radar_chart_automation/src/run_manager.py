import os
from dataclasses import dataclass
from datetime import datetime

from .utils import sanitize_title


@dataclass
class RunPaths:
    base: str
    raw_input: str
    percentiles: str
    outputs: str
    logs: str


def create_run_folder(run_title: str, default_title: str | None = None) -> RunPaths:
    home = os.path.expanduser("~")
    base_dir = os.path.join(home, "Documents", "RadarChartAutomation", "Runs")
    if run_title:
        run_folder = sanitize_title(run_title)
    else:
        date_stamp = datetime.now().strftime("%m-%d-%y")
        title = sanitize_title(default_title or "run")
        run_folder = f"{date_stamp}__{title}"
    base = os.path.join(base_dir, run_folder)

    raw_input = os.path.join(base, "01_raw_input")
    percentiles = os.path.join(base, "02_percentiles")
    outputs = os.path.join(base, "03_outputs")
    logs = os.path.join(base, "logs")

    for path in [raw_input, percentiles, outputs, logs]:
        os.makedirs(path, exist_ok=True)

    return RunPaths(base=base, raw_input=raw_input, percentiles=percentiles, outputs=outputs, logs=logs)
