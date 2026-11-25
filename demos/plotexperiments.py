"""Plot convergence and RC CSVs using only the Python standard library.
Run convergence and test_rc, then run this script from the output directory.
"""
import csv
import math
from pathlib import Path
from plotmassspring import frame, label, polyline, LEFT, RIGHT, PANEL_TOPS, PANEL_HEIGHT

COLORS = {"explicit": "#2366bd", "improved": "#d35c35",
          "implicit": "#368752", "crank_nicolson": "#9656ac"}


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def plot_convergence(path):
    rows = read_rows(path)
    xs = [math.log10(float(row["tau"])) for row in rows]
    ys = [math.log10(float(row["error"])) for row in rows]
    xmin, xmax = math.floor(min(xs)), math.ceil(max(xs))
    ymin, ymax = math.floor(min(ys)), math.ceil(max(ys))
    top, bottom = 80, 540

    def point(x, y):
        return (LEFT + (RIGHT-LEFT)*(x-xmin)/(xmax-xmin),
                bottom-(bottom-top)*(y-ymin)/(ymax-ymin))

    body = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620">',
            '<rect width="100%" height="100%" fill="white"/>',
            label(LEFT, 35, "Mass–spring convergence at T = 2π (log–log)", 22)]
    for x in range(xmin, xmax+1):
        px, _ = point(x, ymin)
        body += [f'<path d="M {px} {top} V {bottom}" stroke="#ddd"/>',
                 label(px-15, bottom+24, f"10^{x}", 13)]
    for y in range(ymin, ymax+1):
        _, py = point(xmin, y)
        body += [f'<path d="M {LEFT} {py} H {RIGHT}" stroke="#ddd"/>',
                 label(30, py+4, f"10^{y}", 13)]
    for index, (method, color) in enumerate(COLORS.items()):
        data = [row for row in rows if row["method"] == method]
        points = [point(math.log10(float(row["tau"])), math.log10(float(row["error"])))
                  for row in data]
        body += [polyline(points, color), label(LEFT+10, top+25+index*21, method, 15, color)]
        for px, py in points:
            body.append(f'<circle cx="{px}" cy="{py}" r="3" fill="{color}"/>')
    body += [label(450, 600, "time-step τ", 17), label(LEFT, 65, "Euclidean final-state error", 15), '</svg>']
    path.with_suffix(".svg").write_text("\n".join(body), encoding="utf-8")


def plot_rc(path):
    rows = [{key: float(value) for key, value in row.items()} for row in read_rows(path)]
    panels = []
    for key in ("exact", *COLORS):
        top = PANEL_TOPS[len(panels)]
        scale = max(1e-12, *(abs(row[key]) for row in rows), *(abs(row["exact"]) for row in rows))

        def points(column):
            return [(LEFT+(RIGHT-LEFT)*row["t"]/rows[-1]["t"],
                     top+PANEL_HEIGHT/2-(PANEL_HEIGHT/2-12)*row[column]/scale) for row in rows]

        content = (polyline(points("exact"), "#919ba7", dashed=True)
                   + polyline(points(key), COLORS.get(key, "#273140"))
                   + label(RIGHT-90, top+PANEL_HEIGHT-10, "time t [s]", 12))
        panels.append((key, content, scale))
    parameters = "R=1, C=1" if "_p0_" in path.stem else "R=100, C=10⁻⁶ (stiff)"
    tau = rows[1]["t"]-rows[0]["t"]
    title = f"RC capacitor voltage — {parameters}, τ={tau:g} (gray dashed: exact)"
    path.with_suffix(".svg").write_text(frame(title, panels), encoding="utf-8")


def main():
    convergence = Path("convergence.csv")
    rc_files = sorted(Path(".").glob("rc_p*_h*.csv"))
    if not convergence.exists() or not rc_files:
        raise SystemExit("Run convergence and test_rc in this directory first.")
    plot_convergence(convergence)
    for path in rc_files:
        plot_rc(path)
    print(f"Created convergence.svg and {len(rc_files)} RC plots.")


if __name__ == "__main__":
    main()
