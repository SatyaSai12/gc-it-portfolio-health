"""Load the three sessional-paper snapshots into SQLite.

Each CSV is one report the Government of Canada tabled in Parliament, listing
every IT project over $1 million with its total budget and estimated completion
date (2016, 2019, 2022). A project that appears in more than one report can be
compared with itself over time.

Usage:
    python src/load.py        # creates data/gc_it.db
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "gc_it.db"


def clean(year: int) -> pd.DataFrame:
    df = pd.read_csv(RAW / f"gc-it-projects-{year}.csv")
    out = pd.DataFrame({
        "unique_id": df.uniqueId,
        "dept_acronym": df.deptAcronym,
        "department": df.department,
        "project_name": df.projectName.str.strip(),
        "report_year": year,
        "as_of_date": pd.to_datetime(df.asOfDate, format="mixed").dt.strftime("%Y-%m-%d"),
        # "$4,800,000" -> 4800000
        "budget": pd.to_numeric(df.totalBudget.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce"),
        # Mostly "March 31, 2024"; a few are fiscal years like "2023-24" and cannot be parsed to a day -> NULL
        "due_date": pd.to_datetime(df.estimatedCompletionDate, errors="coerce", format="mixed").dt.strftime("%Y-%m-%d"),
    })
    return out


def main() -> None:
    snaps = pd.concat([clean(y) for y in (2016, 2019, 2022)], ignore_index=True)
    DB.unlink(missing_ok=True)
    with sqlite3.connect(DB) as con:
        snaps.to_sql("snapshots", con, index=False)
        con.executescript((ROOT / "sql" / "00_views.sql").read_text())
        for year, n in con.execute("SELECT report_year, COUNT(*) FROM snapshots GROUP BY 1"):
            print(f"{year}: {n} projects")
        n = con.execute("SELECT COUNT(*) FROM project_variance").fetchone()[0]
        print(f"tracked across 2+ reports: {n}")


if __name__ == "__main__":
    main()
