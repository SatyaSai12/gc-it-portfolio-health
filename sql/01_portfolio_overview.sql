-- 01_portfolio_overview.sql
-- Size of the reported portfolio in each sessional paper.
SELECT
    report_year,
    COUNT(*)                                        AS projects,
    COUNT(DISTINCT department)                      AS departments,
    ROUND(SUM(budget) / 1e9, 2)                     AS total_budget_bn,
    ROUND(AVG(budget) / 1e6, 1)                     AS avg_budget_m,
    SUM(budget >= 100000000)                        AS projects_over_100m,
    SUM(due_date IS NULL)                           AS projects_without_a_due_date
FROM snapshots
GROUP BY report_year
ORDER BY report_year;
