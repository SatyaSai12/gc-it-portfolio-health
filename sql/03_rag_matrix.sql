-- 03_rag_matrix.sql
-- How many projects fall in each cost x schedule RAG cell, plus the overall split.
SELECT cost_rag, schedule_rag, COUNT(*) AS projects
FROM project_rag
GROUP BY cost_rag, schedule_rag
ORDER BY cost_rag, schedule_rag;

SELECT overall_rag, COUNT(*) AS projects, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM project_rag
GROUP BY overall_rag
ORDER BY CASE overall_rag WHEN 'Red' THEN 1 WHEN 'Amber' THEN 2 ELSE 3 END;
