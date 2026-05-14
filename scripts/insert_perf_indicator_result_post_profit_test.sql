-- 个人业绩看板分润结果测试数据
-- 使用方式：
-- 1. 确保 perf_indicator、perf_indicator_result_post_profit 表已存在
-- 2. 执行本脚本，写入 2026-05-12、2026-05-13 两天的个人看板测试数据
-- 3. 员工编号来源：scripts/人员团队.xlsx
--
-- 说明：
-- - 数据覆盖三个条线机构员工，便于联调 employee_no + org_id 过滤
-- - 发展转型类指标（2-7）同时生成 day_avg(metric_value) 与 point_in_time(metric_value_2)
-- - 其余叶子指标仅生成 point_in_time，保持和现有机构看板测试口径一致
-- - 使用 REPLACE INTO，支持重复执行

REPLACE INTO `perf_indicator_result_post_profit`
(
    `data_dt`,
    `indicator_id`,
    `org_id`,
    `employee_no`,
    `employee_name`,
    `metric_value`,
    `metric_value_2`,
    `calc_status`,
    `error_msg`,
    `extra_json`
)
SELECT
    dt.data_dt,
    ind.indicator_id,
    emp.org_id,
    emp.employee_no,
    emp.employee_name,
    CASE
        WHEN ind.has_metric_value = 1
            THEN ROUND(1000000 + ind.indicator_id * 9700 + emp.emp_idx * 2900 - dt.day_offset * 1100, 4)
        ELSE NULL
    END AS metric_value,
    ROUND(2000000 + ind.indicator_id * 13100 + emp.emp_idx * 3100 - dt.day_offset * 1700, 4) AS metric_value_2,
    '01' AS calc_status,
    NULL AS error_msg,
    NULL AS extra_json
FROM (
    SELECT 0 AS day_offset, DATE('2026-05-13') AS data_dt
    UNION ALL
    SELECT 1, DATE('2026-05-12')
) AS dt
CROSS JOIN (
    SELECT 2 AS indicator_id, 1 AS has_metric_value
    UNION ALL SELECT 3, 1
    UNION ALL SELECT 4, 1
    UNION ALL SELECT 5, 1
    UNION ALL SELECT 6, 1
    UNION ALL SELECT 7, 1
    UNION ALL SELECT 9, 0
    UNION ALL SELECT 10, 0
    UNION ALL SELECT 11, 0
    UNION ALL SELECT 12, 0
    UNION ALL SELECT 13, 0
    UNION ALL SELECT 14, 0
    UNION ALL SELECT 15, 0
    UNION ALL SELECT 16, 0
    UNION ALL SELECT 17, 0
    UNION ALL SELECT 18, 0
    UNION ALL SELECT 19, 0
    UNION ALL SELECT 21, 0
    UNION ALL SELECT 22, 0
    UNION ALL SELECT 23, 0
    UNION ALL SELECT 24, 0
    UNION ALL SELECT 25, 0
    UNION ALL SELECT 26, 0
) AS ind
CROSS JOIN (
    SELECT '44030001' AS org_id, 'HS0000832' AS employee_no, '夏力' AS employee_name, 1 AS emp_idx
    UNION ALL
    SELECT '44030004', 'HS0020867', '蓝珍秀', 2
    UNION ALL
    SELECT '44030005', 'HS0020935', '李艳芬', 3
) AS emp;
