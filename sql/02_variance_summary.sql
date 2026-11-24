-- 02_variance_summary.sql
-- Headline cost and schedule variance for projects reported more than once.
-- Median via window functions (SQLite has no MEDIAN()).

WITH ranked AS (
    SELECT
        slip_years, budget_change_pct,
        ROW_NUMBER() OVER (ORDER BY slip_years)        AS rn_slip,
        ROW_NUMBER() OVER (ORDER BY budget_change_pct) AS rn_budget,
        COUNT(*)     OVER ()                           AS cnt
    FROM project_variance
)
SELECT
    MAX(cnt)                                                                     AS tracked_projects,
    ROUND(100.0 * AVG(slip_years > 0), 1)                                        AS pct_finish_date_moved_later,
    ROUND(100.0 * AVG(slip_years > 1), 1)                                        AS pct_slipped_over_1_year,
    ROUND(AVG(CASE WHEN rn_slip IN ((cnt+1)/2, (cnt+2)/2) THEN slip_years END), 2) AS median_slip_years,
    ROUND(100.0 * AVG(budget_change_pct > 10), 1)                                AS pct_budget_up_over_10,
    ROUND(100.0 * AVG(budget_change_pct >= 30), 1)                               AS pct_budget_up_30_or_more,
    ROUND(100.0 * AVG(budget_change_pct < 0), 1)                                 AS pct_budget_down,
    ROUND(AVG(CASE WHEN rn_budget IN ((cnt+1)/2, (cnt+2)/2) THEN budget_change_pct END), 1) AS median_budget_change_pct
FROM ranked;

-- Combined budget of the tracked projects: baseline vs latest
SELECT
    ROUND(SUM(baseline_budget) / 1e9, 2)                                   AS baseline_total_bn,
    ROUND(SUM(latest_budget)   / 1e9, 2)                                   AS latest_total_bn,
    ROUND(100.0 * (SUM(latest_budget) - SUM(baseline_budget)) / SUM(baseline_budget), 1) AS growth_pct
FROM project_variance;
