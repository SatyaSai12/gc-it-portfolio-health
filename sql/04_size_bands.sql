-- 04_size_bands.sql
-- Do bigger projects slip more? Variance by baseline budget band.
WITH ranked AS (
    SELECT size_band, slip_years, budget_change_pct,
           ROW_NUMBER() OVER (PARTITION BY size_band ORDER BY slip_years)        AS rn_s,
           ROW_NUMBER() OVER (PARTITION BY size_band ORDER BY budget_change_pct) AS rn_b,
           COUNT(*)     OVER (PARTITION BY size_band)                           AS cnt
    FROM project_variance
)
SELECT
    size_band,
    MAX(cnt)                                                                        AS projects,
    ROUND(AVG(CASE WHEN rn_s IN ((cnt+1)/2, (cnt+2)/2) THEN slip_years END), 2)        AS median_slip_years,
    ROUND(100.0 * AVG(slip_years > 1), 1)                                           AS pct_slipped_over_1_year,
    ROUND(AVG(CASE WHEN rn_b IN ((cnt+1)/2, (cnt+2)/2) THEN budget_change_pct END), 1) AS median_budget_change_pct,
    ROUND(100.0 * AVG(budget_change_pct >= 30), 1)                                  AS pct_budget_up_30_or_more
FROM ranked
GROUP BY size_band
ORDER BY size_band;
