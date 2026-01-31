import os
import shutil
import sys
import traceback
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from src import io, percentiles, radar_plot, run_manager, utils

APP_VERSION = "1.0.0"


class RadarChartApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Radar Chart Automation")
        self.geometry("720x560")

        self.selected_files = []
        self.last_run_folder = None

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(frame, text="Radar Chart Automation", font=("TkDefaultFont", 16, "bold"))
        title_label.pack(anchor=tk.W)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(12, 4))

        self.select_button = ttk.Button(button_frame, text="Select CSV(s)", command=self.select_files)
        self.select_button.pack(side=tk.LEFT)

        self.run_button = ttk.Button(button_frame, text="Run", command=self.run_processing)
        self.run_button.pack(side=tk.LEFT, padx=(8, 0))

        self.open_button = ttk.Button(button_frame, text="Open output folder", command=self.open_output_folder)
        self.open_button.pack(side=tk.LEFT, padx=(8, 0))
        self.open_button.state(["disabled"])

        run_title_frame = ttk.Frame(frame)
        run_title_frame.pack(fill=tk.X, pady=(8, 4))
        ttk.Label(run_title_frame, text="Run title (optional)").pack(side=tk.LEFT)
        self.run_title_entry = ttk.Entry(run_title_frame)
        self.run_title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.run_title_entry.insert(0, "e.g. January 2026 Testing")
        self.run_title_entry.bind("<FocusIn>", self._clear_placeholder)

        self.export_png_var = tk.BooleanVar(value=False)
        self.export_png_check = ttk.Checkbutton(
            frame, text="Export PNGs", variable=self.export_png_var
        )
        self.export_png_check.pack(anchor=tk.W, pady=(4, 8))

        self.status_area = ScrolledText(frame, height=18, wrap=tk.WORD, state=tk.DISABLED)
        self.status_area.pack(fill=tk.BOTH, expand=True)

    def _clear_placeholder(self, event):
        if self.run_title_entry.get().startswith("e.g."):
            self.run_title_entry.delete(0, tk.END)

    def log_status(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_area.config(state=tk.NORMAL)
        self.status_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_area.see(tk.END)
        self.status_area.config(state=tk.DISABLED)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select Teamworks CSV exports",
            filetypes=[("CSV Files", "*.csv")],
        )
        if files:
            self.selected_files = list(files)
            self.log_status(f"Selected {len(files)} file(s).")

    def open_output_folder(self):
        if not self.last_run_folder:
            return
        path = self.last_run_folder
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f"open '{path}'")
            else:
                os.system(f"xdg-open '{path}'")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open folder: {exc}")

    def _setup_logger(self, log_path: str):
        import logging

        logger = logging.getLogger("radar_chart_automation")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def run_processing(self):
        if not self.selected_files:
            messagebox.showerror("Missing files", "Please select one or more CSV files.")
            return

        run_title_input = self.run_title_entry.get().strip()
        user_provided_title = run_title_input and not run_title_input.startswith("e.g.")
        default_title = os.path.splitext(os.path.basename(self.selected_files[0]))[0]

        run_paths = run_manager.create_run_folder(
            run_title_input if user_provided_title else "",
            default_title=default_title,
        )
        log_path = os.path.join(run_paths.logs, "run.log")
        logger = self._setup_logger(log_path)
        logger.info("Radar Chart Automation v%s", APP_VERSION)
        logger.info("Selected CSVs: %s", ", ".join(self.selected_files))

        self.log_status("Copying input files...")
        for path in self.selected_files:
            shutil.copy2(path, run_paths.raw_input)

        long_frames = []
        wide_frames = []
        date_labels = []
        athlete_date_values = {}

        try:
            for path in self.selected_files:
                df, mapping = self._load_with_mapping(path)
                logger.info("Column mapping for %s: %s", path, mapping)
                io.validate_required_metrics(df, mapping)

                date_label = self._determine_date_label(df, path)
                if not date_label:
                    raise ValueError(f"No date label resolved for {os.path.basename(path)}")

                date_labels.append(date_label)
                logger.info("Date label for %s: %s", path, date_label)

                long_df, wide_df = percentiles.compute_percentiles(df, mapping)
                long_df["test_date_label"] = date_label
                wide_df["test_date_label"] = date_label

                long_frames.append(long_df)
                wide_frames.append(wide_df)

                for _, row in wide_df.iterrows():
                    athlete = row["athlete_name"]
                    values = [
                        row["Jump Height percentile"],
                        row["Triple Ext percentile"],
                        row["Elasticity percentile"],
                        row["Loading percentile"],
                        row["Braking percentile"],
                    ]
                    values = [float(v) * 100 for v in values]
                    athlete_date_values.setdefault(athlete, {})[date_label] = values

                logger.info("Processed %s athletes for %s", len(wide_df), date_label)

            long_all = pd.concat(long_frames, ignore_index=True)
            wide_all = pd.concat(wide_frames, ignore_index=True)

            long_all.to_csv(os.path.join(run_paths.percentiles, "percentiles_long.csv"), index=False)
            wide_all.to_csv(os.path.join(run_paths.percentiles, "percentiles_wide.csv"), index=False)

            self.log_status("Building PDF charts...")
            pdf_name = f"{os.path.basename(run_paths.base)}__radars.pdf"
            pdf_path = os.path.join(run_paths.outputs, pdf_name)

            with PdfPages(pdf_path) as pdf:
                for athlete, date_map in athlete_date_values.items():
                    ordered_map = {label: date_map[label] for label in date_labels if label in date_map}
                    fig = radar_plot.build_radar_figure(athlete, ordered_map)
                    pdf.savefig(fig)
                    if self.export_png_var.get():
                        png_dir = os.path.join(run_paths.outputs, "png")
                        os.makedirs(png_dir, exist_ok=True)
                        filename = utils.sanitize_filename(athlete) + ".png"
                        fig.savefig(os.path.join(png_dir, filename), dpi=150)
                    plt_close(fig)

            self.last_run_folder = run_paths.base
            self.open_button.state(["!disabled"])
            self.log_status("Run complete.")
            self.log_status(f"Output folder: {run_paths.base}")
        except Exception as exc:
            logger.error("Run failed: %s", exc)
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", str(exc))
            self.log_status(f"Error: {exc}")

    def _load_with_mapping(self, path: str):
        try:
            return io.load_csv(path)
        except io.ColumnMappingNeeded as exc:
            mapping = self._prompt_column_mapping(exc.columns, exc.suggested_mapping)
            if not mapping:
                raise ValueError("Column mapping was cancelled.")
            df, mapping = io.load_csv(path, mapping)
            return df, mapping

    def _prompt_column_mapping(self, columns, suggested_mapping):
        required = io.REQUIRED_KEYS
        mapping = dict(suggested_mapping)

        dialog = tk.Toplevel(self)
        dialog.title("Map columns")
        dialog.grab_set()

        ttk.Label(dialog, text="Select the correct CSV columns for each required field.").pack(
            padx=12, pady=(12, 8)
        )

        combo_vars = {}
        for key in required:
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.X, padx=12, pady=4)
            label = ttk.Label(frame, text=key.replace("_", " ").title())
            label.pack(side=tk.LEFT)
            var = tk.StringVar(value=mapping.get(key, ""))
            combo = ttk.Combobox(frame, textvariable=var, values=columns, state="readonly")
            combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            combo_vars[key] = var

        result = {"mapping": None}

        def on_ok():
            chosen = {key: var.get() for key, var in combo_vars.items() if var.get()}
            if len(chosen) < len(required):
                messagebox.showerror("Missing selection", "Please choose a column for every field.")
                return
            result["mapping"] = chosen
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=12)
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=8)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT)

        self.wait_window(dialog)
        return result["mapping"]

    def _determine_date_label(self, df, path: str):
        date_column = utils.pick_date_column(df.columns)
        date_label = None
        if date_column:
            date_label = utils.extract_date_label_from_column(df, date_column)
        if not date_label:
            date_label = utils.infer_date_from_filename(path)
        if not date_label:
            prompt = f"Enter a date label for {os.path.basename(path)} (e.g. 2026-01-31):"
            date_label = simpledialog.askstring("Date label", prompt, parent=self)
            if date_label:
                date_label = utils.parse_date_label(date_label) or date_label.strip()
        return date_label


def plt_close(fig):
    import matplotlib.pyplot as plt

    plt.close(fig)


if __name__ == "__main__":
    app = RadarChartApp()
    app.mainloop()
