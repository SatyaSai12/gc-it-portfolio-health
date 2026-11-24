"""Run the SQL in sql/01-07, save each result to outputs/, and draw the charts.

Usage:
    python src/load.py
    python src/analyze.py
"""
import re
import sqlite3
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "gc_it.db"
OUT = ROOT / "outputs"
CHARTS = OUT / "charts"

BLUE, GREY = "#2a78d6", "#a8a6a0"
RAG = {"Red": "#d23f31", "Amber": "#e8a33a", "Green": "#3c9a5f"}
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "text.parse_math": False,        # "$10M-$100M" is money, not a formula
})


def statements(path: Path) -> list[str]:
    text = re.sub(r"--[^\n]*", "", path.read_text())
    return [s.strip() for s in text.split(";") if s.strip()]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(CHARTS / name, dpi=160)
    plt.close(fig)


def chart_slip(con):
    df = pd.read_sql_query("SELECT slip_years FROM project_variance", con)
    med = df.slip_years.median()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    bins = np.arange(-3, 9.5, 0.5)
    ax.hist(df.slip_years.clip(-3, 9), bins=bins, color=BLUE, edgecolor=SURFACE, linewidth=1.5)
    ax.axvline(0, color=INK_2, linewidth=1)
    ax.axvline(med, color=INK, linewidth=1.2, linestyle="--")
    ax.text(med + 0.1, ax.get_ylim()[1] * 0.92, f"median {med:.1f} years later", fontsize=9, color=INK)
    ax.text(-2.9, ax.get_ylim()[1] * 0.92, "finished\nearlier", fontsize=8.5, color=INK_2, va="top")
    ax.set_xlabel("Change in reported completion date, first report to latest (years)")
    ax.set_ylabel("Projects")
    ax.grid(axis="x", visible=False)
    ax.set_title(f"{(df.slip_years > 0).mean():.0%} of re-reported projects moved their finish date later")
    save(fig, "01_schedule_slip.png")


def chart_budget(con):
    df = pd.read_sql_query("SELECT budget_change_pct FROM project_variance", con)
    edges = [-np.inf, -0.05, 10, 30, 100, np.inf]
    labels = ["Went down", "0-10%\nup", "10-30%\nup", "30-100%\nup", "More than\ndoubled"]
    counts = pd.cut(df.budget_change_pct, edges, labels=labels, right=False).value_counts().reindex(labels)
    colors = [RAG["Green"], RAG["Green"], RAG["Amber"], RAG["Red"], RAG["Red"]]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(labels, counts.values, color=colors, width=0.6)
    for i, v in enumerate(counts.values):
        ax.text(i, v + 1, str(v), ha="center", fontsize=9.5, color=INK)
    ax.set_ylabel("Projects")
    ax.grid(axis="x", visible=False)
    doubled = counts["More than\ndoubled"] / counts.sum()
    ax.set_title(f"Budget change from first report to latest: {doubled:.0%} more than doubled")
    ax.text(0, -0.28, "Colour = cost RAG band: under 10% green, 10-30% amber, 30%+ red",
            transform=ax.transAxes, fontsize=8.5, color=INK_2)
    save(fig, "02_budget_change.png")


def chart_rag(con):
    df = pd.read_sql_query("SELECT cost_rag, schedule_rag, COUNT(*) n FROM project_rag GROUP BY 1, 2", con)
    order = ["Green", "Amber", "Red"]
    grid = df.pivot(index="cost_rag", columns="schedule_rag", values="n").reindex(index=order[::-1], columns=order).fillna(0)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for i, c in enumerate(grid.index):
        for j, s in enumerate(grid.columns):
            overall = "Red" if "Red" in (c, s) else ("Amber" if "Amber" in (c, s) else "Green")
            ax.add_patch(plt.Rectangle((j, i), 0.96, 0.96, color=RAG[overall], alpha=0.18 + 0.6 * grid.loc[c, s] / grid.values.max()))
            ax.text(j + 0.48, i + 0.48, f"{int(grid.loc[c, s])}", ha="center", va="center", fontsize=14, fontweight="bold", color=INK)
    ax.set_xlim(0, 3); ax.set_ylim(0, 3)
    ax.set_xticks([0.48, 1.48, 2.48], ["Green\n(< 3 months)", "Amber\n(3-12 months)", "Red\n(> 1 year)"])
    ax.set_yticks([0.48, 1.48, 2.48], ["Red\n(30%+)", "Amber\n(10-30%)", "Green\n(< 10%)"])
    ax.set_xlabel("Schedule slip")
    ax.set_ylabel("Budget growth")
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    total = int(grid.values.sum())
    red = int(grid.loc["Red"].sum() + grid["Red"].sum() - grid.loc["Red", "Red"])
    ax.set_title(f"{red} of {total} projects are Red on cost, schedule or both")
    save(fig, "03_rag_matrix.png")


def chart_size(df):
    d = df[df.size_band != "3. Over $100M"].copy()
    d["label"] = d.size_band.str[3:] + "\n(" + d.projects.astype(str) + " projects)"
    fig, ax = plt.subplots(figsize=(7, 3.3))
    ax.barh(d.label[::-1], d.median_slip_years[::-1], color=BLUE, height=0.5)
    for i, (v, p) in enumerate(zip(d.median_slip_years[::-1], d.pct_slipped_over_1_year[::-1])):
        ax.text(v + 0.05, i, f"{v:.1f} years median   ({p:.0f}% slipped over a year)", va="center", fontsize=9, color=INK_2)
    ax.set_xlim(0, d.median_slip_years.max() * 2.1)
    ax.set_xlabel("Median schedule slip (years)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Smaller projects slipped further than mid-size ones")
    ax.text(0, -0.3, "Projects over $100M (only 4 tracked) are left out: too few to compare.", transform=ax.transAxes, fontsize=8.5, color=INK_2)
    save(fig, "04_size_bands.png")


def chart_departments(df):
    d = df.sort_values("median_slip_years")
    short = d.department.str.replace("Innovation, Science and Economic Development Canada", "Innovation, Science & Econ. Dev.") \
                        .str.replace("Immigration, Refugees and Citizenship Canada", "Immigration, Refugees & Citizenship") \
                        .str.replace("Employment and Social Development Canada", "Employment & Social Development")
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.hlines(range(len(d)), 0, d.median_slip_years, color=GRID, linewidth=2)
    ax.scatter(d.median_slip_years, range(len(d)), color=BLUE, s=45, zorder=3)
    for i, (v, n) in enumerate(zip(d.median_slip_years, d.tracked_projects)):
        ax.text(v + 0.08, i, f"{v:.1f}  (n={n})", va="center", fontsize=8.5, color=INK_2)
    ax.set_yticks(range(len(d)), short)
    ax.set_xlim(0, d.median_slip_years.max() + 1)
    ax.set_xlabel("Median schedule slip (years)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Median slip by department (6+ tracked projects)")
    save(fig, "05_departments.png")


def main():
    if not DB.exists():
        raise SystemExit("data/gc_it.db not found. Run: python src/load.py")
    CHARTS.mkdir(parents=True, exist_ok=True)
    results = {}
    with sqlite3.connect(DB) as con:
        for path in sorted((ROOT / "sql").glob("0[1-9]_*.sql")):
            for n, stmt in enumerate(statements(path), start=1):
                name = path.stem if n == 1 else f"{path.stem}_part{n}"
                df = pd.read_sql_query(stmt, con)
                df.to_csv(OUT / f"{name}.csv", index=False)
                results[name] = df
                print(f"{name:<30} {len(df):>4} rows")
        pd.read_sql_query("SELECT * FROM project_rag ORDER BY overall_rag, slip_years DESC", con) \
          .to_csv(OUT / "project_rag_full.csv", index=False)
        chart_slip(con)
        chart_budget(con)
        chart_rag(con)
    chart_size(results["04_size_bands"])
    chart_departments(results["05_department_scorecard"])
    print("charts written to outputs/charts/")


if __name__ == "__main__":
    main()
