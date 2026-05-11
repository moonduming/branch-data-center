-- 修复 perf_indicator_rule_post_profit 中被过度转义的 SQL 模板
-- 背景：
-- 旧版 insert_perf_indicator_rule_post_profit_seed.sql 把模板中的单引号多转义了一层，
-- 造成库里保存成类似：
--   DATA_DT = ''{data_dt}''
--   CCY_CD IN (''156'', ''B02'')
-- 定时任务 render 后会变成：
--   DATA_DT = ''2025-12-02''
--   CCY_CD IN (''156'', ''B02'')
-- 进而触发 MySQL 1064。
--
-- 该脚本只修复“明显是旧脏数据”的记录：
-- 通过识别 ''{data_dt}'' / ''{org_id}'' / ''156'' 这些特征定位。

START TRANSACTION;

UPDATE perf_indicator_rule_post_profit
SET
    point_sql_template = CASE
        WHEN point_sql_template IS NOT NULL THEN REPLACE(point_sql_template, CONCAT(CHAR(39), CHAR(39)), CHAR(39))
        ELSE point_sql_template
    END,
    daily_avg_sql_template = CASE
        WHEN daily_avg_sql_template IS NOT NULL THEN REPLACE(daily_avg_sql_template, CONCAT(CHAR(39), CHAR(39)), CHAR(39))
        ELSE daily_avg_sql_template
    END
WHERE
    INSTR(COALESCE(point_sql_template, ''), CONCAT(CHAR(39), CHAR(39), '{data_dt}', CHAR(39), CHAR(39))) > 0
    OR INSTR(COALESCE(point_sql_template, ''), CONCAT(CHAR(39), CHAR(39), '{org_id}', CHAR(39), CHAR(39))) > 0
    OR INSTR(COALESCE(point_sql_template, ''), CONCAT(CHAR(39), CHAR(39), '156', CHAR(39), CHAR(39))) > 0
    OR INSTR(COALESCE(daily_avg_sql_template, ''), CONCAT(CHAR(39), CHAR(39), '{data_dt}', CHAR(39), CHAR(39))) > 0
    OR INSTR(COALESCE(daily_avg_sql_template, ''), CONCAT(CHAR(39), CHAR(39), '{org_id}', CHAR(39), CHAR(39))) > 0
    OR INSTR(COALESCE(daily_avg_sql_template, ''), CONCAT(CHAR(39), CHAR(39), '156', CHAR(39), CHAR(39))) > 0;

COMMIT;

-- 可选验证：
-- SELECT id, indicator_id
-- FROM perf_indicator_rule_post_profit
-- WHERE point_sql_template LIKE '%''''{data_dt}''''%'
--    OR point_sql_template LIKE '%''''156''''%'
--    OR daily_avg_sql_template LIKE '%''''{data_dt}''''%'
--    OR daily_avg_sql_template LIKE '%''''156''''%';
