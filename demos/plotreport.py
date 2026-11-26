"""Generate a curated set of documentation figures from the experiment CSVs.

Usage: python demos/plotreport.py --data-dir build --output-dir docs/pictures
Only Python's standard library is required. No ODE is re-integrated here:
all numerical curves come from CSVs produced by the C++ experiments.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from html import escape
import math
from pathlib import Path

METHODS = (
    ("Explicit Euler", "euler", "explicit", "#2366bd"),
    ("Improved Euler", "improved", "improved", "#d35c35"),
    ("Implicit Euler", "implicit", "implicit", "#368752"),
    ("Crank–Nicolson", "cn", "crank_nicolson", "#9656ac"),
)
STEP_COLORS = ("#2366bd", "#d35c35", "#368752")
EXACT_COLOR = "#626b75"


@dataclass
class Series:
    label: str
    x: list
    y: list
    color: str
    dashed: bool = False
    markers: bool = False


@dataclass
class Panel:
    title: str
    xlabel: str
    ylabel: str
    series: list
    logx: bool = False
    logy: bool = False
    xlim: tuple | None = None
    ylim: tuple | None = None
    equal: bool = False


def read_numeric(path):
    with path.open(newline="", encoding="utf-8") as source:
        rows = [{key: float(value) for key, value in row.items()}
                for row in csv.DictReader(source)]
    if len(rows) < 2 or any(not math.isfinite(value) for row in rows for value in row.values()):
        raise ValueError(f"Missing or non-finite data in {path}")
    if rows[0]["t"] != 0 or any(b["t"] <= a["t"] for a, b in zip(rows, rows[1:])):
        raise ValueError(f"Invalid time grid in {path}")
    return rows


def step_size(rows):
    return rows[-1]["t"] / (len(rows)-1)


def sample(series, limit=700):
    if len(series.x) != len(series.y) or not series.x:
        raise ValueError("A series must have matching, nonempty coordinates")
    stride = max(1, math.ceil((len(series.x)-1)/(limit-1)))
    indices = list(range(0, len(series.x), stride))
    if indices[-1] != len(series.x)-1:
        indices.append(len(series.x)-1)
    return [(series.x[i], series.y[i]) for i in indices]


def text(x, y, value, size=14, anchor="start", color="#273140"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
            f'font-family="Arial,sans-serif" font-size="{size}" fill="{color}">'
            f'{escape(str(value))}</text>')


def axis_limits(values, logarithmic, specified):
    if not values or any(not math.isfinite(v) for v in values):
        raise ValueError("Axis coordinates must be finite and nonempty")
    if logarithmic and any(v <= 0 for v in values):
        raise ValueError("Logarithmic coordinates must be positive")
    transform = math.log10 if logarithmic else float
    if specified is not None:
        low, high = map(transform, specified)
    else:
        low, high = min(map(transform, values)), max(map(transform, values))
        if logarithmic:
            low, high = math.floor(low), math.ceil(high)
        else:
            padding = 0.07 * (high-low) if high > low else max(abs(low)*0.05, 0.05)
            low, high = low-padding, high+padding
    if high <= low:
        high = low+1
    return low, high


def ticks(low, high, logarithmic):
    if logarithmic:
        first, last = math.ceil(low), math.floor(high)
        stride = max(1, math.ceil((last-first)/5))
        values = list(range(first, last+1, stride))
        if values and values[-1] != last:
            values.append(last)
        return [(v, f"1e{v}") for v in values]
    return [(low+(high-low)*i/4, f"{low+(high-low)*i/4:.3g}") for i in range(5)]


def render_panel(panel, x, y, width, height, index):
    left, top = x+90, y+45
    plot_width, plot_height = width-120, height-150
    if panel.equal:
        side = min(plot_width, plot_height)
        left += (plot_width-side)/2
        plot_width = plot_height = side
    bottom = top+plot_height
    xmin, xmax = axis_limits([v for s in panel.series for v in s.x], panel.logx, panel.xlim)
    ymin, ymax = axis_limits([v for s in panel.series for v in s.y], panel.logy, panel.ylim)

    def point(a, b):
        a = math.log10(a) if panel.logx else a
        b = math.log10(b) if panel.logy else b
        return (left+plot_width*(a-xmin)/(xmax-xmin),
                bottom-plot_height*(b-ymin)/(ymax-ymin))

    clip_id = f"panel-{index}"
    body = [text(x+width/2, y+22, panel.title, 17, "middle"),
            f'<defs><clipPath id="{clip_id}"><rect x="{left}" y="{top}" '
            f'width="{plot_width}" height="{plot_height}"/></clipPath></defs>']
    for value, label in ticks(xmin, xmax, panel.logx):
        px = left+plot_width*(value-xmin)/(xmax-xmin)
        body += [f'<path d="M {px:.2f} {top:.2f} V {bottom:.2f}" stroke="#e4e8ec"/>',
                 text(px, bottom+19, label, 12, "middle")]
    for value, label in ticks(ymin, ymax, panel.logy):
        py = bottom-plot_height*(value-ymin)/(ymax-ymin)
        body += [f'<path d="M {left:.2f} {py:.2f} H {left+plot_width:.2f}" stroke="#e4e8ec"/>',
                 text(left-9, py+4, label, 12, "end")]
    body += [f'<rect x="{left}" y="{top}" width="{plot_width}" '
             f'height="{plot_height}" fill="none" stroke="#8b959f"/>',
             text(left+plot_width/2, bottom+41, panel.xlabel, 14, "middle"),
             f'<text transform="translate({left-65:.2f},{top+plot_height/2:.2f}) rotate(-90)" '
             f'text-anchor="middle" font-family="Arial,sans-serif" font-size="14">'
             f'{escape(panel.ylabel)}</text>']
    body.append(f'<g clip-path="url(#{clip_id})">')
    for series in panel.series:
        points = [point(a, b) for a, b in sample(series)]
        coords = " ".join(f"{px:.2f},{py:.2f}" for px, py in points)
        dash = ' stroke-dasharray="6 4"' if series.dashed else ""
        body.append(f'<polyline points="{coords}" fill="none" stroke="{series.color}" '
                    f'stroke-width="2"{dash}/>')
        if series.markers:
            body.extend(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="2.7" fill="{series.color}"/>'
                        for px, py in points)
    body.append('</g>')
    for i, series in enumerate(panel.series):
        lx, ly = x+75+(i%2)*(width-120)/2, y+height-48+(i//2)*23
        dash = ' stroke-dasharray="6 4"' if series.dashed else ""
        body += [f'<path d="M {lx} {ly-4} h 24" stroke="{series.color}" stroke-width="2"{dash}/>',
                 text(lx+31, ly, series.label, 13)]
    return "\n".join(body)


def write_figure(path, title, subtitle, panels, columns=2):
    width = 1240 if columns == 2 else 980
    rows = math.ceil(len(panels)/columns)
    panel_width, panel_height = (width-40)/columns, 460
    height = 100+rows*panel_height+20
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img">',
            f'<title>{escape(title)}</title>', f'<desc>{escape(subtitle)}</desc>',
            '<rect width="100%" height="100%" fill="white"/>',
            text(width/2, 35, title, 25, "middle"), text(width/2, 65, subtitle, 15, "middle")]
    for i, panel in enumerate(panels):
        body.append(render_panel(panel, 20+(i%columns)*panel_width,
                                 90+(i//columns)*panel_height, panel_width, panel_height, i))
    body.append('</svg>')
    path.write_text("\n".join(body)+"\n", encoding="utf-8")


def exact_rc(times, rc):
    a = 100*math.pi*rc
    return [(math.cos(100*math.pi*t)+a*math.sin(100*math.pi*t)-math.exp(-t/rc))/(1+a*a)
            for t in times]


def grid(end, n=700):
    return [end*i/n for i in range(n+1)]


def mass_figures(data, output):
    short = [read_numeric(data/f"massspring_T0_h{i}.csv") for i in range(3)]
    long = [read_numeric(data/f"massspring_T1_h{i}.csv") for i in range(3)]
    panels = []
    for name, key, _, _ in METHODS:
        times = grid(short[0][-1]["t"])
        series = [Series("Exact", times, [math.cos(t) for t in times], EXACT_COLOR, dashed=True)]
        for rows, color in zip(short, STEP_COLORS):
            series.append(Series(f"τ={step_size(rows):.5g}", [r["t"] for r in rows],
                                 [r[f"{key}_x"] for r in rows], color))
        panels.append(Panel(name, "Time t", "Position x", series, xlim=(0,times[-1])))
    write_figure(output/"massspring_step_comparison.svg", "Mass–spring: changing the time step",
                 "T=4π, m=k=1, y(0)=(1,0). Actual steps shown; each method has its own vertical scale.", panels)

    panels = []
    rows = short[2]
    circle = grid(2*math.pi)
    for name, key, _, color in METHODS:
        series = [Series("Exact", [math.cos(t) for t in circle], [-math.sin(t) for t in circle],
                         EXACT_COLOR, dashed=True),
                  Series(name, [r[f"{key}_x"] for r in rows], [r[f"{key}_v"] for r in rows], color)]
        panels.append(Panel(name, "Position x", "Velocity v", series,
                            xlim=(-2,2), ylim=(-2,2), equal=True))
    write_figure(output/"massspring_phase_comparison.svg", "Mass–spring: phase portraits",
                 f"T=4π, τ={step_size(rows):.6g}. Identical axis ranges and equal aspect ratio in all panels.", panels)

    panels = []
    rows = long[0]
    times = grid(rows[-1]["t"])
    for name, key, _, color in METHODS:
        series = [Series("Exact", times, [math.cos(t) for t in times], EXACT_COLOR, dashed=True),
                  Series(name, [r["t"] for r in rows], [r[f"{key}_x"] for r in rows], color)]
        panels.append(Panel(name, "Time t", "Position x", series, xlim=(0,times[-1])))
    write_figure(output/"massspring_long_time.svg", "Mass–spring: long-time evolution",
                 f"T=40π (ten times longer), τ={step_size(rows):.6g}. Independent vertical scales.", panels)

    panels = []
    for name, key, _, _ in METHODS:
        series = [Series("Exact energy", [0,long[0][-1]["t"]], [1,1], EXACT_COLOR, dashed=True)]
        for rows, color in zip(long, STEP_COLORS):
            energy = [r[f"{key}_x"]**2+r[f"{key}_v"]**2 for r in rows]
            series.append(Series(f"τ={step_size(rows):.5g}", [r["t"] for r in rows], energy, color))
        logarithmic = key in ("euler", "implicit")
        panels.append(Panel(name, "Time t", "E(t)/E(0)"+(" (log scale)" if logarithmic else ""),
                            series, logy=logarithmic, xlim=(0,long[0][-1]["t"]),
                            ylim=(0.95,1.05) if key == "cn" else None))
    write_figure(output/"massspring_energy.svg", "Mass–spring: energy drift for different steps",
                 "T=40π. Euler panels use log energy; Crank–Nicolson uses a fixed range around 1.", panels)


def convergence_figure(data, output):
    with (data/"convergence.csv").open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    series = []
    for name, _, key, color in METHODS:
        selected = sorted((r for r in rows if r["method"] == key), key=lambda r: int(r["N"]))
        if [int(r["N"]) for r in selected] != [2**i for i in range(4,13)]:
            raise ValueError(f"Missing convergence grids for {name}")
        order = math.log2(float(selected[-2]["error"])/float(selected[-1]["error"]))
        series.append(Series(f"{name}: p={order:.4f}", [float(r["tau"]) for r in selected],
                             [float(r["error"]) for r in selected], color, markers=True))
    panel = Panel("All four methods", "Time step τ (log scale)", "Final Euclidean error (log scale)",
                  series, logx=True, logy=True)
    write_figure(output/"euler_convergence.svg", "Mass–spring: measured convergence order",
                 "T=2π, N=16,…,4096. Legends give p from the last refinement (2048 → 4096).", [panel], columns=1)


def rc_figures(data, output):
    nonstiff = [read_numeric(data/f"rc_p0_h{i}.csv") for i in range(4)]
    stiff = [read_numeric(data/f"rc_p1_h{i}.csv") for i in range(4)]
    panels = []
    for name, _, key, _ in METHODS:
        times = grid(nonstiff[0][-1]["t"])
        series = [Series("Exact", times, exact_rc(times,1), EXACT_COLOR, dashed=True)]
        for index, color in zip((0,1,3), STEP_COLORS):
            rows = nonstiff[index]
            series.append(Series(f"τ={step_size(rows):.5g}", [r["t"] for r in rows],
                                 [r[key] for r in rows], color))
        panels.append(Panel(name, "Time t [s]", "Capacitor voltage [V]", series, xlim=(0,times[-1])))
    write_figure(output/"rc_nonstiff_steps.svg", "RC circuit: accuracy with different steps",
                 "R=C=1, T=0.1 s (five forcing periods). Exact curves are sampled densely.", panels)

    panels = []
    for group, title in ((METHODS[:2], "Explicit methods"), (METHODS[2:], "Implicit methods")):
        series = []
        for name, _, key, color in group:
            steps = [step_size(rows) for rows in stiff]
            errors = [max(abs(r[key]-r["exact"]) for r in rows) for rows in stiff]
            pairs = sorted(zip(steps,errors))
            series.append(Series(name, [p[0] for p in pairs], [p[1] for p in pairs], color, markers=True))
        # A reference vertical line marks the real-axis explicit stability boundary.
        lowest = min(min(s.y) for s in series)
        highest = max(max(s.y) for s in series)
        series.append(Series("Explicit boundary τ=2RC", [0.0002,0.0002], [lowest,highest],
                             EXACT_COLOR, dashed=True))
        panels.append(Panel(title, "Time step τ [s] (log scale)", "Maximum nodal error [V] (log scale)",
                            series, logx=True, logy=True))
    write_figure(output/"rc_stiff_stability.svg", "Stiff RC circuit: stability versus accuracy",
                 "R=100, C=10⁻⁶, T=0.1 s. Maximum error over all nodes; different y scales in the two panels.", panels)

    panels = []
    end = 0.001
    times = grid(end)
    for name, _, key, _ in METHODS:
        series = [Series("Exact", times, exact_rc(times,0.0001), EXACT_COLOR, dashed=True)]
        for index, color in zip((2,3), STEP_COLORS):
            rows = [r for r in stiff[index] if r["t"] <= end+1e-14]
            series.append(Series(f"τ={step_size(stiff[index]):.5g}", [r["t"] for r in rows],
                                 [r[key] for r in rows], color, markers=True))
        panels.append(Panel(name, "Time t [s]", "Capacitor voltage [V]", series,
                            xlim=(0,end), ylim=(0,1.1)))
    write_figure(output/"rc_stiff_transient.svg", "Stiff RC circuit: resolving the fast transient",
                 "First 0.001 s (10RC). Numerical dots are actual C++ nodes, not extra simulated points.", panels)

    rows = [r for r in stiff[1] if r["t"] <= 0.02+1e-14]
    times = grid(0.02)
    series = [Series("Exact", times, exact_rc(times,0.0001), EXACT_COLOR, dashed=True)]
    for name, _, key, color in METHODS[2:]:
        series.append(Series(name, [r["t"] for r in rows], [r[key] for r in rows], color, markers=True))
    panel = Panel("Implicit Euler and Crank–Nicolson", "Time t [s]", "Capacitor voltage [V]", series,
                  xlim=(0,0.02))
    write_figure(output/"rc_stiff_coarse_step.svg", "Stiff RC circuit: a stable step can still be inaccurate",
                 "R=100, C=10⁻⁶, τ=0.001 s=10RC. One forcing period; numerical nodes explicitly marked.",
                 [panel], columns=1)


def generate(data, output):
    output.mkdir(parents=True, exist_ok=True)
    mass_figures(data,output)
    convergence_figure(data,output)
    rc_figures(data,output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("build"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/pictures"))
    args = parser.parse_args()
    generate(args.data_dir,args.output_dir)
    print(f"Generated 9 report SVGs in {args.output_dir}")


if __name__ == "__main__":
    main()
