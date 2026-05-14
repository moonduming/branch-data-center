-- 分润指标规则日均 SQL
-- 说明：
-- 1. 本文件仅整理 daily_avg_sql_template，对应结果字段统一为 org_id, employee_no, employee_name, metric_value
-- 2. 当前仅整理 5 个存在日均值的指标，其余纯时点指标不需要日均 SQL
-- 3. 单位存款按 ORIG_ACCT_ID 分润，个人存款按 ECIF_CUST_ID 分润
-- 4. period_start 取 {data_dt} 所在年份 1 月 1 日，period_end 取当年 12 月 31 日

---- 日均单位存款-全口径存款
WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        a.BAL_YEAR_ACCUM AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history a
    CROSS JOIN params pm
    WHERE a.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND SUBSTR(a.MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND a.CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR RIGHT(a.MNG_ORG_ID, 8) = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ORIG_ACCT_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT
        pr.ORIG_ACCT_ID,
        pr.eff_date
    FROM prop_raw pr
    CROSS JOIN params pm
    WHERE pr.eff_date >= pm.period_start
),
all_starts AS (
    SELECT ORIG_ACCT_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    WHERE d.ORIG_ACCT_ID IS NULL
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    GROUP BY a.ORIG_ACCT_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ORIG_ACCT_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ORIG_ACCT_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ORIG_ACCT_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ORIG_ACCT_ID = p.ORIG_ACCT_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ORIG_ACCT_ID = lp.ORIG_ACCT_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ORIG_ACCT_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ORIG_ACCT_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ORIG_ACCT_ID = o.ORIG_ACCT_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ORIG_ACCT_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ORIG_ACCT_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum,
        d.exit_date
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ORIG_ACCT_ID = b.ORIG_ACCT_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
org_exit_snapshot AS (
    SELECT DISTINCT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        FIRST_VALUE(effective_accum) OVER (
            PARTITION BY ORIG_ACCT_ID, org_id, employee_no
            ORDER BY DATA_DT DESC
        ) AS frozen_accum
    FROM org_active_accum
),
org_min_eff_date AS (
    SELECT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        MIN(eff_date) AS min_eff_date
    FROM org_ownership_span
    GROUP BY ORIG_ACCT_ID, org_id, employee_no, employee_name
),
all_dates AS (
    SELECT DISTINCT DATA_DT FROM acct_daily_accum
),
org_full_dates AS (
    SELECT
        s.ORIG_ACCT_ID,
        s.org_id,
        s.employee_no,
        s.employee_name,
        d.DATA_DT
    FROM org_exit_snapshot s
    INNER JOIN org_min_eff_date m
        ON s.ORIG_ACCT_ID = m.ORIG_ACCT_ID
       AND s.org_id = m.org_id
       AND s.employee_no = m.employee_no
    INNER JOIN all_dates d
        ON d.DATA_DT >= m.min_eff_date
    CROSS JOIN params pm
    WHERE d.DATA_DT <= pm.period_end
),
org_daily_accum_final AS (
    SELECT
        f.ORIG_ACCT_ID,
        f.DATA_DT,
        f.org_id,
        f.employee_no,
        f.employee_name,
        COALESCE(a.effective_accum, s.frozen_accum) AS effective_accum
    FROM org_full_dates f
    LEFT JOIN org_active_accum a
        ON f.ORIG_ACCT_ID = a.ORIG_ACCT_ID
       AND f.org_id = a.org_id
       AND f.employee_no = a.employee_no
       AND f.DATA_DT = a.DATA_DT
    LEFT JOIN org_exit_snapshot s
        ON f.ORIG_ACCT_ID = s.ORIG_ACCT_ID
       AND f.org_id = s.org_id
       AND f.employee_no = s.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM all_dates
),
org_daily_contrib AS (
    SELECT
        e.org_id,
        e.employee_no,
        e.employee_name,
        e.DATA_DT,
        e.effective_accum / f.day_num AS daily_contrib
    FROM org_daily_accum_final e
    INNER JOIN daily_factor f ON e.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;

---- 日均单位存款-优质存款
WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        p1.ORIG_ACCT_ID,
        p1.DATA_DT,
        CASE
            WHEN p1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN p1.BAL_YEAR_ACCUM
            WHEN (p1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN p1.BAL_YEAR_ACCUM
            WHEN (p1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND p1.EXEC_RATE <= p4.PARA_SCOPE THEN p1.BAL_YEAR_ACCUM
            ELSE 0
        END AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history p1
    LEFT JOIN shenzhen_data.FDL_REFL_DIM_PARAMET_CONFIG p4
        ON (CASE
                WHEN SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 6) = ''L12001'' THEN ''CORP_DEP_RT''
                WHEN SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 6) = ''L11001'' THEN ''INDIV_DEP_RT''
                ELSE ''''
            END) = p4.DIM_CD
       AND p1.INT_ST_DT >= CAST(p4.PARA_ST_VAL AS DATE)
       AND p1.INT_ST_DT < CAST(p4.PARA_END_VAL AS DATE)
       AND (CASE WHEN CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) > 730 THEN ''3Y'' ELSE '''' END) = p4.PARA_CD
       AND p4.YEAR = SUBSTR(''{data_dt}'', 1, 4)
       AND p4.BIZ_TYPE_CD = ''B_DP_RT''
    CROSS JOIN params pm
    WHERE p1.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND p1.BASIS_CD IN (''D_100'')
      AND p1.CCY_CD IN (''156'', ''B02'')
      AND SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND (''{org_id}'' = '''' OR p1.ACCNT_ORG_ID = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ORIG_ACCT_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT ORIG_ACCT_ID, eff_date
    FROM prop_raw
    CROSS JOIN params pm
    WHERE eff_date >= pm.period_start
),
all_starts AS (
    SELECT ORIG_ACCT_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    WHERE d.ORIG_ACCT_ID IS NULL
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    GROUP BY a.ORIG_ACCT_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ORIG_ACCT_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ORIG_ACCT_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ORIG_ACCT_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ORIG_ACCT_ID = p.ORIG_ACCT_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ORIG_ACCT_ID = lp.ORIG_ACCT_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ORIG_ACCT_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ORIG_ACCT_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ORIG_ACCT_ID = o.ORIG_ACCT_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ORIG_ACCT_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ORIG_ACCT_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ORIG_ACCT_ID = b.ORIG_ACCT_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM (SELECT DISTINCT DATA_DT FROM acct_daily_accum) t
),
org_daily_contrib AS (
    SELECT
        a.org_id,
        a.employee_no,
        a.employee_name,
        a.DATA_DT,
        a.effective_accum / f.day_num AS daily_contrib
    FROM org_active_accum a
    INNER JOIN daily_factor f ON a.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;

---- 日均单位存款-活期存款
WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        a.BAL_YEAR_ACCUM AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history a
    CROSS JOIN params pm
    WHERE a.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND SUBSTR(a.MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND a.CCY_CD IN (''156'', ''B02'')
      AND a.FIX_CUR_FLG = ''0''
      AND (''{org_id}'' = '''' OR RIGHT(a.MNG_ORG_ID, 8) = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ORIG_ACCT_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT ORIG_ACCT_ID, eff_date
    FROM prop_raw
    CROSS JOIN params pm
    WHERE eff_date >= pm.period_start
),
all_starts AS (
    SELECT ORIG_ACCT_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    WHERE d.ORIG_ACCT_ID IS NULL
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    GROUP BY a.ORIG_ACCT_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ORIG_ACCT_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ORIG_ACCT_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ORIG_ACCT_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ORIG_ACCT_ID = p.ORIG_ACCT_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ORIG_ACCT_ID = lp.ORIG_ACCT_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ORIG_ACCT_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ORIG_ACCT_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ORIG_ACCT_ID = o.ORIG_ACCT_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ORIG_ACCT_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ORIG_ACCT_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ORIG_ACCT_ID = b.ORIG_ACCT_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM (SELECT DISTINCT DATA_DT FROM acct_daily_accum) t
),
org_daily_contrib AS (
    SELECT
        a.org_id,
        a.employee_no,
        a.employee_name,
        a.DATA_DT,
        a.effective_accum / f.day_num AS daily_contrib
    FROM org_active_accum a
    INNER JOIN daily_factor f ON a.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;

---- 日均个人存款-全口径存款
WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        a.ECIF_CUST_ID,
        a.DATA_DT,
        a.BAL_YEAR_ACCUM AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history a
    CROSS JOIN params pm
    WHERE a.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND SUBSTR(a.MNG_ACCNT_PROD_ID, 1, 4) = ''L110''
      AND a.CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR a.ACCNT_ORG_ID = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ECIF_CUST_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT ECIF_CUST_ID, eff_date
    FROM prop_raw
    CROSS JOIN params pm
    WHERE eff_date >= pm.period_start
),
all_starts AS (
    SELECT ECIF_CUST_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ECIF_CUST_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ECIF_CUST_ID FROM acct_daily_accum WHERE ECIF_CUST_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ECIF_CUST_ID = d.ECIF_CUST_ID
    WHERE d.ECIF_CUST_ID IS NULL
    UNION ALL
    SELECT a.ECIF_CUST_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ECIF_CUST_ID FROM acct_daily_accum WHERE ECIF_CUST_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ECIF_CUST_ID = d.ECIF_CUST_ID
    GROUP BY a.ECIF_CUST_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ECIF_CUST_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ECIF_CUST_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ECIF_CUST_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ECIF_CUST_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ECIF_CUST_ID = p.ECIF_CUST_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ECIF_CUST_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ECIF_CUST_ID = lp.ECIF_CUST_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ECIF_CUST_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ECIF_CUST_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ECIF_CUST_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ECIF_CUST_ID = o.ECIF_CUST_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ECIF_CUST_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ECIF_CUST_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ECIF_CUST_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ECIF_CUST_ID = b.ECIF_CUST_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM (SELECT DISTINCT DATA_DT FROM acct_daily_accum) t
),
org_daily_contrib AS (
    SELECT
        a.org_id,
        a.employee_no,
        a.employee_name,
        a.DATA_DT,
        a.effective_accum / f.day_num AS daily_contrib
    FROM org_active_accum a
    INNER JOIN daily_factor f ON a.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;

---- 日均个人存款-优质存款
WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        p1.ECIF_CUST_ID,
        p1.DATA_DT,
        CASE
            WHEN p1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN p1.BAL_YEAR_ACCUM
            WHEN (p1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN p1.BAL_YEAR_ACCUM
            WHEN (p1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND p1.EXEC_RATE <= p4.PARA_SCOPE THEN p1.BAL_YEAR_ACCUM
            ELSE 0
        END AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history p1
    LEFT JOIN shenzhen_data.FDL_REFL_DIM_PARAMET_CONFIG p4
        ON (CASE
                WHEN SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 6) = ''L12001'' THEN ''CORP_DEP_RT''
                WHEN SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 6) = ''L11001'' THEN ''INDIV_DEP_RT''
                ELSE ''''
            END) = p4.DIM_CD
       AND p1.INT_ST_DT >= CAST(p4.PARA_ST_VAL AS DATE)
       AND p1.INT_ST_DT < CAST(p4.PARA_END_VAL AS DATE)
       AND (CASE WHEN CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) > 730 THEN ''3Y'' ELSE '''' END) = p4.PARA_CD
       AND p4.YEAR = SUBSTR(''{data_dt}'', 1, 4)
       AND p4.BIZ_TYPE_CD = ''B_DP_RT''
    CROSS JOIN params pm
    WHERE p1.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND p1.BASIS_CD IN (''D_100'')
      AND p1.CCY_CD IN (''156'', ''B02'')
      AND SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 4) = ''L110''
      AND (''{org_id}'' = '''' OR p1.ACCNT_ORG_ID = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ECIF_CUST_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT ECIF_CUST_ID, eff_date
    FROM prop_raw
    CROSS JOIN params pm
    WHERE eff_date >= pm.period_start
),
all_starts AS (
    SELECT ECIF_CUST_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ECIF_CUST_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ECIF_CUST_ID FROM acct_daily_accum WHERE ECIF_CUST_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ECIF_CUST_ID = d.ECIF_CUST_ID
    WHERE d.ECIF_CUST_ID IS NULL
    UNION ALL
    SELECT a.ECIF_CUST_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ECIF_CUST_ID FROM acct_daily_accum WHERE ECIF_CUST_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ECIF_CUST_ID = d.ECIF_CUST_ID
    GROUP BY a.ECIF_CUST_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ECIF_CUST_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ECIF_CUST_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ECIF_CUST_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ECIF_CUST_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ECIF_CUST_ID = p.ECIF_CUST_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ECIF_CUST_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ECIF_CUST_ID = lp.ECIF_CUST_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ECIF_CUST_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ECIF_CUST_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ECIF_CUST_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ECIF_CUST_ID = o.ECIF_CUST_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ECIF_CUST_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ECIF_CUST_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ECIF_CUST_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ECIF_CUST_ID = b.ECIF_CUST_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM (SELECT DISTINCT DATA_DT FROM acct_daily_accum) t
),
org_daily_contrib AS (
    SELECT
        a.org_id,
        a.employee_no,
        a.employee_name,
        a.DATA_DT,
        a.effective_accum / f.day_num AS daily_contrib
    FROM org_active_accum a
    INNER JOIN daily_factor f ON a.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;
