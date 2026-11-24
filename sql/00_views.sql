-- 00_views.sql
-- project_variance: one row per project that appears in at least two reports,
-- comparing its FIRST reported budget and completion date (the baseline)
-- with its LATEST reported ones.

DROP VIEW IF EXISTS ranked_snapshots;
CREATE VIEW ranked_snapshots AS
SELECT
    s.*,
    ROW_NUMBER() OVER (PARTITION BY unique_id ORDER BY report_year ASC)  AS first_rank,
    ROW_NUMBER() OVER (PARTITION BY unique_id ORDER BY report_year DESC) AS last_rank,
    COUNT(*)     OVER (PARTITION BY unique_id)                           AS times_reported
FROM snapshots s;

DROP VIEW IF EXISTS project_variance;
CREATE VIEW project_variance AS
SELECT
    f.unique_id,
    f.department,
    l.project_name,
    f.times_reported,
    f.report_year                                   AS baseline_year,
    l.report_year                                   AS latest_year,
    l.as_of_date                                    AS latest_as_of,
    f.budget                                        AS baseline_budget,
    l.budget                                        AS latest_budget,
    f.due_date                                      AS baseline_due,
    l.due_date                                      AS latest_due,

    -- Cost variance: growth over the baseline budget, in %
    ROUND(100.0 * (l.budget - f.budget) / f.budget, 1)               AS budget_change_pct,

    -- Schedule variance: how far the finish date moved, in years (positive = later)
    ROUND((julianday(l.due_date) - julianday(f.due_date)) / 365.25, 2) AS slip_years,

    -- Size band on the baseline budget
    CASE
        WHEN f.budget <  10000000  THEN '1. Under $10M'
        WHEN f.budget < 100000000  THEN '2. $10M-$100M'
        ELSE                            '3. Over $100M'
    END                                                              AS size_band
FROM ranked_snapshots f
JOIN ranked_snapshots l
  ON l.unique_id = f.unique_id AND l.last_rank = 1
WHERE f.first_rank = 1
  AND f.times_reported >= 2
  AND f.budget IS NOT NULL AND l.budget IS NOT NULL
  AND f.due_date IS NOT NULL AND l.due_date IS NOT NULL;

-- RAG rating. Thresholds:
--   Cost:     under 10% growth = Green, 10-30% = Amber, 30%+ = Red
--             (the bands the US Federal IT Dashboard uses for cost variance)
--   Schedule: under 3 months = Green, 3-12 months = Amber, over 12 months = Red
--   Overall:  the worse of the two
DROP VIEW IF EXISTS project_rag;
CREATE VIEW project_rag AS
SELECT
    v.*,
    CASE WHEN budget_change_pct < 10 THEN 'Green' WHEN budget_change_pct < 30 THEN 'Amber' ELSE 'Red' END AS cost_rag,
    CASE WHEN slip_years < 0.25      THEN 'Green' WHEN slip_years <= 1       THEN 'Amber' ELSE 'Red' END AS schedule_rag,
    CASE
        WHEN budget_change_pct >= 30 OR slip_years > 1     THEN 'Red'
        WHEN budget_change_pct >= 10 OR slip_years >= 0.25 THEN 'Amber'
        ELSE 'Green'
    END                                                                                              AS overall_rag
FROM project_variance v;
