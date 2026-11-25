"""Create time-evolution and phase SVG plots from test_ode CSV files.

Run from the build directory: python ../demos/plotmassspring.py
Only Python's standard library is required.
"""

import csv
from html import escape
from pathlib import Path


WIDTH = 1000
LEFT, RIGHT = 100, 960
PANEL_HEIGHT = 190
PANEL_TOPS = tuple(90 + 220 * i for i in range(5))
HEIGHT = PANEL_TOPS[-1] + PANEL_HEIGHT + 30
COLORS = {"x": "#2366bd", "v": "#d35c35", "phase": "#2366bd"}
METHODS = (
    ("Exact", "exact"),
    ("Explicit Euler", "euler"),
    ("Improved Euler (midpoint)", "improved"),
    ("Implicit Euler", "implicit"),
    ("Crank–Nicolson", "cn"),
)


def polyline(points, color, dashed=False):
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    dash = ' stroke-dasharray="6 4"' if dashed else ""
    return (
        f'<polyline points="{coords}" fill="none" stroke="{color}"'
        f' stroke-width="1.8"{dash}/>'
    )


def label(x, y, value, size=15, color="#273140"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial,sans-serif"'
        f' font-size="{size}" fill="{color}">{escape(str(value))}</text>'
    )


def frame(title, panels):
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"'
        f' viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="white"/>',
        label(LEFT, 38, title, 22),
    ]
    for top, (name, content, scale) in zip(PANEL_TOPS, panels):
        body.extend(
            [
                f'<rect x="{LEFT}" y="{top}" width="{RIGHT-LEFT}"'
                f' height="{PANEL_HEIGHT}" fill="#fafbfc" stroke="#aeb8c4"/>',
                label(LEFT + 10, top + 24, name, 16),
                label(RIGHT - 175, top + 24, f"scale ±{scale:.3g}", 13),
                content,
            ]
        )
    body.append("</svg>")
    return "\n".join(body) + "\n"


def plot_time(rows, path):
    max_t = rows[-1]["t"]
    panels = []
    stride = max(1, len(rows) // 1600)
    sampled = rows[::stride]
    if sampled[-1] is not rows[-1]:
        sampled.append(rows[-1])
    for name, key in METHODS:
        top = PANEL_TOPS[len(panels)]
        scale = max(1.0, *(abs(row[f"{key}_{axis}"]) for row in rows for axis in ("x", "v")))

        def points(axis):
            return [
                (
                    LEFT + (RIGHT - LEFT) * row["t"] / max_t,
                    top + PANEL_HEIGHT / 2
                    - (PANEL_HEIGHT / 2 - 12) * row[f"{key}_{axis}"] / scale,
                )
                for row in sampled
            ]

        content = (
            polyline(points("x"), COLORS["x"])
            + polyline(points("v"), COLORS["v"])
            + label(RIGHT - 65, top + PANEL_HEIGHT - 10, "time t", 12)
        )
        panels.append((name, content, scale))
    title = f"Time evolution — T={max_t:.3f} (blue: position, orange: velocity)"
    path.write_text(frame(title, panels), encoding="utf-8")


def plot_phase(rows, path):
    panels = []
    stride = max(1, len(rows) // 1600)
    sampled = rows[::stride]
    if sampled[-1] is not rows[-1]:
        sampled.append(rows[-1])
    for name, key in METHODS:
        top = PANEL_TOPS[len(panels)]
        scale = max(1.0, *(abs(row[f"{key}_{axis}"]) for row in rows for axis in ("x", "v")))
        center_x = (LEFT + RIGHT) / 2
        center_y = top + PANEL_HEIGHT / 2
        radius = PANEL_HEIGHT / 2 - 12
        points = [
            (
                center_x + radius * row[f"{key}_x"] / scale,
                center_y - radius * row[f"{key}_v"] / scale,
            )
            for row in sampled
        ]
        guide = [
            (center_x + radius * row["exact_x"] / scale,
             center_y - radius * row["exact_v"] / scale)
            for row in sampled
        ]
        content = (
            f'<line x1="{LEFT}" y1="{center_y}" x2="{RIGHT}" y2="{center_y}"'
            ' stroke="#d6dce3"/>'
            + polyline(guide, "#919ba7", dashed=True)
            + polyline(points, COLORS["phase"])
            + label(center_x + radius + 12, center_y + 5, "position x", 12)
            + label(center_x + 8, top + 42, "velocity v", 12)
        )
        panels.append((name, content, scale))
    title = f"Phase portrait — T={rows[-1]['t']:.3f} (gray dashed: exact)"
    path.write_text(frame(title, panels), encoding="utf-8")


def main():
    files = sorted(Path(".").glob("massspring_T*_h*.csv"))
    if not files:
        raise SystemExit("No massspring CSV files found; run test_ode in this directory first.")
    for file in files:
        with file.open(newline="", encoding="utf-8") as source:
            rows = [
                {key: float(value) for key, value in row.items()}
                for row in csv.DictReader(source)
            ]
        plot_time(rows, file.with_name(file.stem + "_time.svg"))
        plot_phase(rows, file.with_name(file.stem + "_phase.svg"))
    print(f"Created {2 * len(files)} SVG plots from {len(files)} datasets.")


if __name__ == "__main__":
    main()
