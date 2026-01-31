from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

AXIS_LABELS = ["Jump Height", "Triple Ext", "Elasticity", "Loading", "Braking"]


def build_radar_figure(athlete_name: str, date_to_values: Dict[str, List[float]]):
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.set_aspect("equal")
    ax.axis("off")

    n_axes = len(AXIS_LABELS)
    angles = _axis_angles(n_axes)

    ring_levels = [20, 40, 60, 80, 100]
    _draw_polygon_grid(ax, angles, ring_levels)
    _draw_axis_labels(ax, angles)

    colors = plt.cm.tab10.colors
    for idx, (date_label, values) in enumerate(date_to_values.items()):
        color = colors[idx % len(colors)]
        points = _values_to_points(values, angles)
        ax.plot(points[:, 0], points[:, 1], color=color, linewidth=2, label=date_label)
        ax.fill(points[:, 0], points[:, 1], color=color, alpha=0.15)

    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)

    # Keep title and legend close to the chart area.
    fig.text(0.5, 0.842, athlete_name, ha="center", va="center", fontsize=18)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.05), ncol=2, frameon=False)

    fig.subplots_adjust(top=0.9, bottom=0.12, left=0.12, right=0.88)
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
