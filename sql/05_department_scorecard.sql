-- 05_department_scorecard.sql
-- Departments with at least 6 tracked projects, ranked by median schedule slip.
WITH ranked AS (
    SELECT department, slip_years, budget_change_pct, overall_rag,
           ROW_NUMBER() OVER (PARTITION BY department ORDER BY slip_years)        AS rn_s,
           ROW_NUMBER() OVER (PARTITION BY department ORDER BY budget_change_pct) AS rn_b,
           COUNT(*)     OVER (PARTITION BY department)                           AS cnt
    FROM project_rag
)
SELECT
    department,
    MAX(cnt)                                                                         AS tracked_projects,
    ROUND(AVG(CASE WHEN rn_s IN ((cnt+1)/2, (cnt+2)/2) THEN slip_years END), 2)        AS median_slip_years,
    ROUND(AVG(CASE WHEN rn_b IN ((cnt+1)/2, (cnt+2)/2) THEN budget_change_pct END), 1) AS median_budget_change_pct,
    ROUND(100.0 * AVG(overall_rag = 'Red'), 1)                                       AS pct_red
FROM ranked
GROUP BY department
HAVING MAX(cnt) >= 6
ORDER BY median_slip_years DESC;
