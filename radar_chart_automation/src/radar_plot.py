"""Radar chart rendering with polygon grid rings (not circular)."""

from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

AXIS_LABELS = ["Jump Height", "Triple Ext", "Elasticity", "Loading", "Braking"]


def build_radar_figure(athlete_name: str, date_to_values: Dict[str, List[float]]):
    fig = plt.figure(figsize=(8.5, 11))
    gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[3.2, 1.55], hspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    table_ax = fig.add_subplot(gs[1, 0])
    ax.set_aspect("equal")
    ax.axis("off")
    table_ax.axis("off")

    n_axes = len(AXIS_LABELS)
    angles = _axis_angles(n_axes)

    ring_levels = [0, 25, 50, 75, 100]
    _draw_polygon_grid(ax, angles, ring_levels)
    _draw_axis_labels(ax, angles)

    colors = plt.cm.tab10.colors
    date_colors = {}
    for idx, (date_label, values) in enumerate(date_to_values.items()):
        color = colors[idx % len(colors)]
        date_colors[date_label] = color
        points = _values_to_points(values, angles)
        ax.plot(points[:, 0], points[:, 1], color=color, linewidth=2, label=date_label)
        ax.fill(points[:, 0], points[:, 1], color=color, alpha=0.15)

    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)

    fig.text(0.5, 0.965, athlete_name, ha="center", va="center", fontsize=18)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=2, frameon=False)
    _draw_percentile_table(table_ax, date_to_values, date_colors)

    fig.subplots_adjust(top=0.92, bottom=0.07, left=0.06, right=0.94)
    return fig


def _axis_angles(n_axes: int) -> np.ndarray:
    base = np.linspace(0, 2 * np.pi, n_axes, endpoint=False)
    return np.pi / 2 - base


def _values_to_points(values: List[float], angles: np.ndarray) -> np.ndarray:
    scaled = np.array(values, dtype=float) / 100.0
    x = scaled * np.cos(angles)
    y = scaled * np.sin(angles)
    points = np.column_stack([x, y])
    return np.vstack([points, points[0]])


def _draw_polygon_grid(ax, angles: np.ndarray, ring_levels: List[int]) -> None:
    for level in ring_levels:
        radius = level / 100.0
        x = radius * np.cos(angles)
        y = radius * np.sin(angles)
        x = np.append(x, x[0])
        y = np.append(y, y[0])
        ax.plot(x, y, color="#cccccc", linewidth=1)

    for angle in angles:
        ax.plot([0, np.cos(angle)], [0, np.sin(angle)], color="#e0e0e0", linewidth=1)

    for level in ring_levels:
        radius = level / 100.0
        ax.text(0, radius, f"{level}%", ha="center", va="bottom", fontsize=9, color="#555555")


def _draw_axis_labels(ax, angles: np.ndarray) -> None:
    label_radius = 1.12
    for angle, label in zip(angles, AXIS_LABELS):
        x = label_radius * np.cos(angle)
        y = label_radius * np.sin(angle)
        alignment = "center"
        if x < -0.1:
            alignment = "right"
        elif x > 0.1:
            alignment = "left"
        ax.text(x, y, label, ha=alignment, va="center", fontsize=11)


def _draw_percentile_table(table_ax, date_to_values: Dict[str, List[float]], date_colors) -> None:
    col_labels = ["Date", *AXIS_LABELS]
    cell_text = []
    row_meta = []
    previous_values = None

    for date_label, values in date_to_values.items():
        cell_text.append([date_label, *[_format_percentile(v) for v in values]])
        row_meta.append(("date", date_label, values))

        if previous_values is not None:
            deltas = [curr - prev for curr, prev in zip(values, previous_values)]
            cell_text.append(["Delta", *[_format_delta(v) for v in deltas]])
            row_meta.append(("delta", date_label, deltas))
        previous_values = values

    col_widths = [0.20, 0.16, 0.16, 0.16, 0.16, 0.16]
    table = table_ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.35)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#d0d0d0")
        if row == 0:
            cell.set_facecolor("#f2f4f7")
            cell.get_text().set_fontweight("bold")

    for idx, meta in enumerate(row_meta, start=1):
        row_type, date_label, values = meta
        if row_type == "date":
            color = date_colors.get(date_label, "#222222")
            for col in range(len(col_labels)):
                table[(idx, col)].set_facecolor("#ffffff")
                table[(idx, col)].get_text().set_color(color)
                if col == 0:
                    table[(idx, col)].get_text().set_fontweight("bold")
        else:
            for col in range(len(col_labels)):
                table[(idx, col)].set_facecolor("#f7f7f7")
                if col == 0:
                    table[(idx, col)].get_text().set_fontweight("bold")
                    table[(idx, col)].get_text().set_color("#444444")
                    continue
                delta_value = values[col - 1]
                table[(idx, col)].get_text().set_color(_delta_color(delta_value))


def _format_percentile(value: float) -> str:
    rounded = round(float(value), 1)
    if rounded.is_integer():
        return f"{int(rounded)}%"
    return f"{rounded:.1f}%"


def _format_delta(value: float) -> str:
    rounded = round(float(value), 1)
    if rounded.is_integer():
        return f"{int(rounded):+d}"
    return f"{rounded:+.1f}"


def _delta_color(delta_value: float) -> str:
    if delta_value > 0:
        return "#1b7f3a"
    if delta_value < 0:
        return "#b42318"
    return "#555555"
