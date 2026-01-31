# Radar Chart Automation

Cross-platform desktop app for generating athlete radar charts from Teamworks AMS CSV exports (force plate CMJ summary).

## How to use
1. Run the app.
2. Click **Select CSV(s)** and choose one or more Teamworks exports (one test date per CSV).
3. Enter a **Run title** (optional). Leave blank to use the first filename.
4. (Optional) check **Export PNGs**.
5. Click **Run**. The status box shows progress and any errors.
6. Click **Open output folder** after completion.

Outputs are stored in:
`~/Documents/RadarChartAutomation/Runs/<run_folder_name>/`

## Project structure
```
radar_chart_automation/
  app.py
  src/
    io.py
    percentiles.py
    radar_plot.py
    run_manager.py
    utils.py
  assets/
  tests/
  requirements.txt
  radar_chart_automation.spec
```

## Output folders
Each run creates:
- `01_raw_input/` (copies of selected CSVs)
- `02_percentiles/` (long + wide percentile CSVs)
- `03_outputs/` (PDF and optional PNGs)
- `logs/` (run log)

## Percentile logic
- Percentiles are computed per test date, per metric, across all athletes in that CSV.
- Excel-like percent rank: `rank(value, ascending=True, average ties) / N`.

## Build and run
### Local run (dev)
```
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
python app.py
```

## Build (macOS .app)
```
pyinstaller --noconfirm radar_chart_automation.spec
```
Output: `dist/RadarChartAutomation.app`

## Build (Windows .exe)
```
pyinstaller --noconfirm radar_chart_automation.spec
```
Output: `dist/RadarChartAutomation/RadarChartAutomation.exe`

### PyInstaller (Windows)
```
pyinstaller radar_chart_automation.spec
```
Output: `dist/RadarChartAutomation/RadarChartAutomation.exe`

### PyInstaller (macOS)
```
pyinstaller radar_chart_automation.spec
```
Output: `dist/RadarChartAutomation/RadarChartAutomation.app`

Optional icon:
- Add an `.ico` (Windows) or `.icns` (macOS) and update `radar_chart_automation.spec` with `icon=...` in `EXE()`.

## Testing
```
pytest
```

## Notes
- If the app cannot auto-detect the athlete name or metric columns, a mapping dialog will appear.
- If a date is not found in the CSV or filename, the app will prompt for a date label.
