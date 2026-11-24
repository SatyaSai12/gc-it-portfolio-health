-- 07_watch_list.sql
-- Projects still in flight at the 2022 report (finish date after the report date)
-- and rated Red: the list a portfolio office would take to the next governance board.
SELECT
    project_name,
    department,
    ROUND(baseline_budget / 1e6, 1)   AS baseline_budget_m,
    ROUND(latest_budget / 1e6, 1)     AS latest_budget_m,
    budget_change_pct,
    baseline_due,
    latest_due,
    slip_years,
    cost_rag,
    schedule_rag
FROM project_rag
WHERE latest_year = 2022
  AND latest_due > latest_as_of
  AND overall_rag = 'Red'
ORDER BY latest_budget DESC
LIMIT 15;
