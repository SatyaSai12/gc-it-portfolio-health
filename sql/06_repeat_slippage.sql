-- 06_repeat_slippage.sql
-- For projects in all three reports: if a project slipped between 2016 and 2019,
-- how likely was it to slip again between 2019 and 2022?
WITH three AS (
    SELECT
        unique_id,
        MAX(CASE WHEN report_year = 2016 THEN due_date END) AS due_2016,
        MAX(CASE WHEN report_year = 2019 THEN due_date END) AS due_2019,
        MAX(CASE WHEN report_year = 2022 THEN due_date END) AS due_2022
    FROM snapshots
    GROUP BY unique_id
    HAVING COUNT(*) = 3
),
moves AS (
    SELECT unique_id,
           CASE WHEN due_2019 > due_2016 THEN 'Slipped 2016-2019' ELSE 'Held or improved 2016-2019' END AS first_period,
           CASE WHEN due_2022 > due_2019 THEN 1 ELSE 0 END                                                AS slipped_again
    FROM three
    WHERE due_2016 IS NOT NULL AND due_2019 IS NOT NULL AND due_2022 IS NOT NULL
)
SELECT
    first_period,
    COUNT(*)                                  AS projects,
    SUM(slipped_again)                        AS slipped_2019_2022,
    ROUND(100.0 * AVG(slipped_again), 1)      AS pct_slipped_2019_2022
FROM moves
GROUP BY first_period
ORDER BY first_period DESC;
